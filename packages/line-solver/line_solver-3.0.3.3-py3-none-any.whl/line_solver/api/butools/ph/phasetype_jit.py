"""
JIT-compiled kernels for Phase-Type Distribution computations.

Provides Numba-accelerated versions of phase-type computational hotspots:
- Moment computation kernels
- Multi-point PDF/CDF summation
- Matrix-vector operations for PH distributions

Graceful fallback to pure Python if Numba is not available.

License: MIT (same as LINE)
"""

import numpy as np
from typing import Tuple

# Try to import Numba directly to avoid circular imports
try:
    from numba import njit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

    def njit(*args, **kwargs):
        """Decorator that does nothing if Numba is not available."""
        def decorator(func):
            return func
        if args and callable(args[0]):
            return args[0]
        return decorator

    def prange(*args, **kwargs):
        """Fallback for prange."""
        return range(*args)


if HAS_NUMBA:
    # =========================================================================
    # JIT-compiled versions
    # =========================================================================

    @njit(cache=True)
    def factorial_jit(n: int) -> float:
        """
        JIT-compiled factorial computation.

        Args:
            n: Non-negative integer

        Returns:
            n! as float
        """
        if n <= 1:
            return 1.0
        result = 1.0
        for i in range(2, n + 1):
            result *= i
        return result

    @njit(cache=True)
    def factorials_array_jit(n_max: int, output: np.ndarray) -> None:
        """
        JIT-compiled computation of factorials from 0 to n_max.

        Args:
            n_max: Maximum n to compute
            output: Output array (n_max + 1,)
        """
        output[0] = 1.0
        for i in range(1, n_max + 1):
            output[i] = output[i - 1] * i

    @njit(fastmath=True, cache=True)
    def sum_alpha_invA_power_jit(
        alpha: np.ndarray,
        invA_power: np.ndarray,
        n: int
    ) -> float:
        """
        JIT-compiled computation of sum(alpha * invA^k).

        Args:
            alpha: Initial distribution vector (1, n) or (n,)
            invA_power: Current power of inv(A) matrix (n, n)
            n: Matrix dimension

        Returns:
            Sum of element-wise product
        """
        result = 0.0
        for i in range(n):
            for j in range(n):
                result += alpha[j] * invA_power[j, i]
        return result

    @njit(fastmath=True, cache=True)
    def matmul_inplace_jit(
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        n: int
    ) -> None:
        """
        JIT-compiled matrix multiplication C = A @ B.

        Args:
            A: First matrix (n, n)
            B: Second matrix (n, n)
            C: Output matrix (n, n), modified in place
            n: Matrix dimension
        """
        for i in range(n):
            for j in range(n):
                s = 0.0
                for k in range(n):
                    s += A[i, k] * B[k, j]
                C[i, j] = s

    @njit(fastmath=True, cache=True)
    def moments_from_ph_jit(
        alpha: np.ndarray,
        invA: np.ndarray,
        n_phases: int,
        K: int,
        moments: np.ndarray
    ) -> None:
        """
        JIT-compiled computation of phase-type moments.

        Computes moments[k] = k! * sum(alpha * invA^k) for k = 1, ..., K.

        Args:
            alpha: Initial distribution (n_phases,)
            invA: Inverse of generator matrix (n_phases, n_phases)
            n_phases: Number of phases
            K: Number of moments to compute
            moments: Output array (K,)
        """
        # Work arrays for matrix powers
        invA_power = np.eye(n_phases)
        temp = np.zeros((n_phases, n_phases))

        factorial = 1.0
        for k in range(1, K + 1):
            factorial *= k

            # invA_power = invA_power @ invA
            for i in range(n_phases):
                for j in range(n_phases):
                    s = 0.0
                    for l in range(n_phases):
                        s += invA_power[i, l] * invA[l, j]
                    temp[i, j] = s

            for i in range(n_phases):
                for j in range(n_phases):
                    invA_power[i, j] = temp[i, j]

            # Compute sum(alpha * invA_power)
            s = 0.0
            for i in range(n_phases):
                row_sum = 0.0
                for j in range(n_phases):
                    row_sum += invA_power[i, j]
                s += alpha[i] * row_sum

            moments[k - 1] = factorial * s

    @njit(fastmath=True, cache=True)
    def pdf_sum_jit(
        alpha: np.ndarray,
        expAt: np.ndarray,
        neg_A: np.ndarray,
        n_phases: int
    ) -> float:
        """
        JIT-compiled PDF computation: sum(alpha * exp(A*t) * (-A)).

        Args:
            alpha: Initial distribution (n_phases,)
            expAt: Matrix exponential exp(A*t) (n_phases, n_phases)
            neg_A: Negative generator -A (n_phases, n_phases)
            n_phases: Number of phases

        Returns:
            PDF value at time t
        """
        # Compute alpha @ expAt @ neg_A, then sum
        # First: v = alpha @ expAt
        v = np.zeros(n_phases)
        for j in range(n_phases):
            s = 0.0
            for i in range(n_phases):
                s += alpha[i] * expAt[i, j]
            v[j] = s

        # Then: result = sum(v @ neg_A)
        result = 0.0
        for i in range(n_phases):
            for j in range(n_phases):
                result += v[i] * neg_A[i, j]

        return result

    @njit(fastmath=True, cache=True)
    def cdf_sum_jit(
        alpha: np.ndarray,
        expAt: np.ndarray,
        n_phases: int
    ) -> float:
        """
        JIT-compiled CDF computation: 1 - sum(alpha * exp(A*t)).

        Args:
            alpha: Initial distribution (n_phases,)
            expAt: Matrix exponential exp(A*t) (n_phases, n_phases)
            n_phases: Number of phases

        Returns:
            CDF value at time t
        """
        # Compute sum over all elements of alpha @ expAt
        s = 0.0
        for i in range(n_phases):
            row_sum = 0.0
            for j in range(n_phases):
                row_sum += expAt[i, j]
            s += alpha[i] * row_sum

        return 1.0 - s

    @njit(fastmath=True, cache=True)
    def multipoint_pdf_jit(
        alpha: np.ndarray,
        neg_A: np.ndarray,
        expAt_all: np.ndarray,
        n_phases: int,
        n_points: int,
        output: np.ndarray
    ) -> None:
        """
        JIT-compiled multi-point PDF computation.

        Args:
            alpha: Initial distribution (n_phases,)
            neg_A: Negative generator -A (n_phases, n_phases)
            expAt_all: Pre-computed exp(A*t) for all points (n_points, n_phases, n_phases)
            n_phases: Number of phases
            n_points: Number of time points
            output: Output PDF values (n_points,)
        """
        for p in range(n_points):
            # Extract exp(A*t) for this point
            result = 0.0
            for i in range(n_phases):
                v_i = 0.0
                for j in range(n_phases):
                    v_i += alpha[j] * expAt_all[p, j, i]
                for j in range(n_phases):
                    result += v_i * neg_A[i, j]
            output[p] = result

    @njit(fastmath=True, cache=True)
    def multipoint_cdf_jit(
        alpha: np.ndarray,
        expAt_all: np.ndarray,
        n_phases: int,
        n_points: int,
        output: np.ndarray
    ) -> None:
        """
        JIT-compiled multi-point CDF computation.

        Args:
            alpha: Initial distribution (n_phases,)
            expAt_all: Pre-computed exp(A*t) for all points (n_points, n_phases, n_phases)
            n_phases: Number of phases
            n_points: Number of time points
            output: Output CDF values (n_points,)
        """
        for p in range(n_points):
            s = 0.0
            for i in range(n_phases):
                row_sum = 0.0
                for j in range(n_phases):
                    row_sum += expAt_all[p, i, j]
                s += alpha[i] * row_sum
            output[p] = 1.0 - s

    @njit(fastmath=True, cache=True)
    def check_ph_representation_jit(
        alpha: np.ndarray,
        A: np.ndarray,
        n_phases: int,
        tol: float
    ) -> bool:
        """
        JIT-compiled check for valid PH representation.

        Checks:
        1. alpha sums to 1 (within tolerance)
        2. alpha elements are non-negative
        3. A diagonal elements are negative
        4. A off-diagonal elements are non-negative
        5. Row sums of A are non-positive

        Args:
            alpha: Initial distribution (n_phases,)
            A: Generator matrix (n_phases, n_phases)
            n_phases: Number of phases
            tol: Numerical tolerance

        Returns:
            True if valid PH representation
        """
        # Check alpha sums to 1
        alpha_sum = 0.0
        for i in range(n_phases):
            if alpha[i] < -tol:
                return False
            alpha_sum += alpha[i]

        if abs(alpha_sum - 1.0) > tol:
            return False

        # Check A structure
        for i in range(n_phases):
            # Diagonal should be negative
            if A[i, i] > tol:
                return False

            # Row sum should be non-positive
            row_sum = 0.0
            for j in range(n_phases):
                row_sum += A[i, j]
                # Off-diagonal should be non-negative
                if i != j and A[i, j] < -tol:
                    return False

            if row_sum > tol:
                return False

        return True

    @njit(fastmath=True, cache=True)
    def scale_matrix_jit(
        A: np.ndarray,
        scale: float,
        n: int,
        output: np.ndarray
    ) -> None:
        """
        JIT-compiled matrix scaling: output = A * scale.

        Args:
            A: Input matrix (n, n)
            scale: Scaling factor
            n: Matrix dimension
            output: Output matrix (n, n)
        """
        for i in range(n):
            for j in range(n):
                output[i, j] = A[i, j] * scale

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def factorial_jit(n: int) -> float:
        """Pure Python factorial."""
        from math import factorial
        return float(factorial(n))

    def factorials_array_jit(n_max: int, output: np.ndarray) -> None:
        """Pure Python factorials array."""
        from math import factorial
        for i in range(n_max + 1):
            output[i] = float(factorial(i))

    def sum_alpha_invA_power_jit(
        alpha: np.ndarray,
        invA_power: np.ndarray,
        n: int
    ) -> float:
        """Pure Python sum(alpha * invA_power)."""
        return float(np.sum(alpha @ invA_power))

    def matmul_inplace_jit(
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        n: int
    ) -> None:
        """Pure Python matrix multiplication."""
        np.copyto(C, A @ B)

    def moments_from_ph_jit(
        alpha: np.ndarray,
        invA: np.ndarray,
        n_phases: int,
        K: int,
        moments: np.ndarray
    ) -> None:
        """Pure Python moments computation."""
        from math import factorial
        invA_power = np.eye(n_phases)

        for k in range(1, K + 1):
            invA_power = invA_power @ invA
            moments[k - 1] = factorial(k) * np.sum(alpha @ invA_power)

    def pdf_sum_jit(
        alpha: np.ndarray,
        expAt: np.ndarray,
        neg_A: np.ndarray,
        n_phases: int
    ) -> float:
        """Pure Python PDF computation."""
        return float(np.sum(alpha @ expAt @ neg_A))

    def cdf_sum_jit(
        alpha: np.ndarray,
        expAt: np.ndarray,
        n_phases: int
    ) -> float:
        """Pure Python CDF computation."""
        return float(1.0 - np.sum(alpha @ expAt))

    def multipoint_pdf_jit(
        alpha: np.ndarray,
        neg_A: np.ndarray,
        expAt_all: np.ndarray,
        n_phases: int,
        n_points: int,
        output: np.ndarray
    ) -> None:
        """Pure Python multi-point PDF."""
        for p in range(n_points):
            output[p] = np.sum(alpha @ expAt_all[p] @ neg_A)

    def multipoint_cdf_jit(
        alpha: np.ndarray,
        expAt_all: np.ndarray,
        n_phases: int,
        n_points: int,
        output: np.ndarray
    ) -> None:
        """Pure Python multi-point CDF."""
        for p in range(n_points):
            output[p] = 1.0 - np.sum(alpha @ expAt_all[p])

    def check_ph_representation_jit(
        alpha: np.ndarray,
        A: np.ndarray,
        n_phases: int,
        tol: float
    ) -> bool:
        """Pure Python PH representation check."""
        # Check alpha
        if np.any(alpha < -tol):
            return False
        if abs(np.sum(alpha) - 1.0) > tol:
            return False

        # Check A diagonal
        if np.any(np.diag(A) > tol):
            return False

        # Check A off-diagonal
        off_diag = A - np.diag(np.diag(A))
        if np.any(off_diag < -tol):
            return False

        # Check row sums
        if np.any(np.sum(A, axis=1) > tol):
            return False

        return True

    def scale_matrix_jit(
        A: np.ndarray,
        scale: float,
        n: int,
        output: np.ndarray
    ) -> None:
        """Pure Python matrix scaling."""
        np.copyto(output, A * scale)


__all__ = [
    'HAS_NUMBA',
    'factorial_jit',
    'factorials_array_jit',
    'sum_alpha_invA_power_jit',
    'matmul_inplace_jit',
    'moments_from_ph_jit',
    'pdf_sum_jit',
    'cdf_sum_jit',
    'multipoint_pdf_jit',
    'multipoint_cdf_jit',
    'check_ph_representation_jit',
    'scale_matrix_jit',
]
