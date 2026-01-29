"""
JIT-compiled kernels for Stationary Moment Computation (SMC) / QBD processes.

Provides Numba-accelerated versions of QBD computational hotspots:
- Matrix iteration loops for fundamental matrices
- Convergence checking with matrix norms
- Stationary distribution computation
- Logarithmic reduction inner loops

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

    @njit(fastmath=True, cache=True)
    def matrix_inf_norm_jit(A: np.ndarray, m: int) -> float:
        """
        JIT-compiled infinity norm computation (max row sum of abs).

        Args:
            A: Matrix (m, m)
            m: Matrix dimension

        Returns:
            Infinity norm of A
        """
        max_sum = 0.0
        for i in range(m):
            row_sum = 0.0
            for j in range(m):
                row_sum += abs(A[i, j])
            if row_sum > max_sum:
                max_sum = row_sum
        return max_sum

    @njit(fastmath=True, cache=True)
    def matmul_jit(A: np.ndarray, B: np.ndarray, C: np.ndarray, m: int) -> None:
        """
        JIT-compiled matrix multiplication C = A @ B.

        Args:
            A: First matrix (m, m)
            B: Second matrix (m, m)
            C: Output matrix (m, m), modified in place
            m: Matrix dimension
        """
        for i in range(m):
            for j in range(m):
                s = 0.0
                for k in range(m):
                    s += A[i, k] * B[k, j]
                C[i, j] = s

    @njit(fastmath=True, cache=True)
    def matmul_add_jit(
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        m: int
    ) -> None:
        """
        JIT-compiled matrix multiply-add: C += A @ B.

        Args:
            A: First matrix (m, m)
            B: Second matrix (m, m)
            C: Output matrix (m, m), modified in place
            m: Matrix dimension
        """
        for i in range(m):
            for j in range(m):
                s = 0.0
                for k in range(m):
                    s += A[i, k] * B[k, j]
                C[i, j] += s

    @njit(fastmath=True, cache=True)
    def lr_step_lstar_jit(
        BF: np.ndarray,
        BB: np.ndarray,
        Lstar: np.ndarray,
        temp: np.ndarray,
        m: int
    ) -> None:
        """
        JIT-compiled computation of Lstar = BF @ BB + BB @ BF.

        Args:
            BF: BF matrix (m, m)
            BB: BB matrix (m, m)
            Lstar: Output matrix (m, m)
            temp: Temporary matrix (m, m)
            m: Matrix dimension
        """
        # BF @ BB
        for i in range(m):
            for j in range(m):
                s = 0.0
                for k in range(m):
                    s += BF[i, k] * BB[k, j]
                Lstar[i, j] = s

        # BB @ BF
        for i in range(m):
            for j in range(m):
                s = 0.0
                for k in range(m):
                    s += BB[i, k] * BF[k, j]
                temp[i, j] = s

        # Add
        for i in range(m):
            for j in range(m):
                Lstar[i, j] += temp[i, j]

    @njit(fastmath=True, cache=True)
    def lr_step_squares_jit(
        BF: np.ndarray,
        BB: np.ndarray,
        Fstar: np.ndarray,
        Bstar: np.ndarray,
        m: int
    ) -> None:
        """
        JIT-compiled computation of Fstar = BF @ BF and Bstar = BB @ BB.

        Args:
            BF: BF matrix (m, m)
            BB: BB matrix (m, m)
            Fstar: Output BF^2 (m, m)
            Bstar: Output BB^2 (m, m)
            m: Matrix dimension
        """
        # BF @ BF
        for i in range(m):
            for j in range(m):
                s = 0.0
                for k in range(m):
                    s += BF[i, k] * BF[k, j]
                Fstar[i, j] = s

        # BB @ BB
        for i in range(m):
            for j in range(m):
                s = 0.0
                for k in range(m):
                    s += BB[i, k] * BB[k, j]
                Bstar[i, j] = s

    @njit(fastmath=True, cache=True)
    def stationary_dist_loop_jit(
        pi0: np.ndarray,
        R: np.ndarray,
        K: int,
        m: int,
        output: np.ndarray
    ) -> None:
        """
        JIT-compiled stationary distribution computation up to level K.

        Computes pi_k = pi_{k-1} @ R for k = 1, ..., K.

        Args:
            pi0: Initial distribution (1, m)
            R: Matrix parameter (m, m)
            K: Maximum level
            m: Matrix dimension
            output: Output array ((K+1)*m,)
        """
        # Copy pi0 to output
        for j in range(m):
            output[j] = pi0[0, j]

        # Iteratively compute pi_k = pi_{k-1} @ R
        pix = np.zeros(m)
        for j in range(m):
            pix[j] = pi0[0, j]

        for k in range(1, K + 1):
            # pix = pix @ R
            new_pix = np.zeros(m)
            for j in range(m):
                s = 0.0
                for i in range(m):
                    s += pix[i] * R[i, j]
                new_pix[j] = s

            # Copy to output and update pix
            for j in range(m):
                output[k * m + j] = new_pix[j]
                pix[j] = new_pix[j]

    @njit(fastmath=True, cache=True)
    def scale_and_add_identity_jit(
        A: np.ndarray,
        scale: float,
        m: int,
        output: np.ndarray
    ) -> None:
        """
        JIT-compiled computation of output = A / scale + I.

        Args:
            A: Input matrix (m, m)
            scale: Scaling factor
            m: Matrix dimension
            output: Output matrix (m, m)
        """
        inv_scale = 1.0 / scale
        for i in range(m):
            for j in range(m):
                if i == j:
                    output[i, j] = A[i, j] * inv_scale + 1.0
                else:
                    output[i, j] = A[i, j] * inv_scale

    @njit(fastmath=True, cache=True)
    def scale_matrix_inplace_jit(
        A: np.ndarray,
        scale: float,
        m: int
    ) -> None:
        """
        JIT-compiled in-place matrix scaling: A = A / scale.

        Args:
            A: Matrix to scale (m, m), modified in place
            scale: Scaling factor
            m: Matrix dimension
        """
        inv_scale = 1.0 / scale
        for i in range(m):
            for j in range(m):
                A[i, j] *= inv_scale

    @njit(fastmath=True, cache=True)
    def compute_drift_jit(
        theta: np.ndarray,
        B: np.ndarray,
        F: np.ndarray,
        m: int
    ) -> float:
        """
        JIT-compiled drift computation: theta @ sum(B, 1) - theta @ sum(F, 1).

        Args:
            theta: Stationary distribution (m,)
            B: Backward matrix (m, m)
            F: Forward matrix (m, m)
            m: Matrix dimension

        Returns:
            Drift value
        """
        B_row_sums = np.zeros(m)
        F_row_sums = np.zeros(m)

        for i in range(m):
            for j in range(m):
                B_row_sums[i] += B[i, j]
                F_row_sums[i] += F[i, j]

        drift = 0.0
        for i in range(m):
            drift += theta[i] * (B_row_sums[i] - F_row_sums[i])

        return drift

    @njit(fastmath=True, cache=True)
    def apply_shift_transient_jit(
        F: np.ndarray,
        L: np.ndarray,
        theta: np.ndarray,
        B: np.ndarray,
        m: int
    ) -> None:
        """
        JIT-compiled shift technique for transient case.

        Modifies F = F - ones @ (theta @ F) and L = L + ones @ (theta @ B).

        Args:
            F: Forward matrix (m, m), modified
            L: Local matrix (m, m), modified
            theta: Stationary distribution (m,)
            B: Backward matrix (m, m)
            m: Matrix dimension
        """
        # Compute theta @ F
        thetaF = np.zeros(m)
        for j in range(m):
            s = 0.0
            for i in range(m):
                s += theta[i] * F[i, j]
            thetaF[j] = s

        # Compute theta @ B
        thetaB = np.zeros(m)
        for j in range(m):
            s = 0.0
            for i in range(m):
                s += theta[i] * B[i, j]
            thetaB[j] = s

        # Apply shifts
        for i in range(m):
            for j in range(m):
                F[i, j] -= thetaF[j]
                L[i, j] += thetaB[j]

    @njit(fastmath=True, cache=True)
    def apply_shift_recurrent_jit(
        B: np.ndarray,
        L: np.ndarray,
        F: np.ndarray,
        m: int
    ) -> None:
        """
        JIT-compiled shift technique for positive recurrent case.

        Uses uniform distribution uT = ones / m.

        Args:
            B: Backward matrix (m, m), modified
            L: Local matrix (m, m), modified
            F: Forward matrix (m, m)
            m: Matrix dimension
        """
        uT_val = 1.0 / m

        # Compute row sums
        B_row_sums = np.zeros(m)
        F_row_sums = np.zeros(m)
        for i in range(m):
            for j in range(m):
                B_row_sums[i] += B[i, j]
                F_row_sums[i] += F[i, j]

        # Apply shifts: B = B - sum(B,1) @ uT, L = L + sum(F,1) @ uT
        for i in range(m):
            for j in range(m):
                B[i, j] -= B_row_sums[i] * uT_val
                L[i, j] += F_row_sums[i] * uT_val

    @njit(cache=True)
    def check_convergence_jit(BB: np.ndarray, BF: np.ndarray, m: int, tol: float) -> bool:
        """
        JIT-compiled convergence check: min(norm(BB), norm(BF)) < tol.

        Args:
            BB: BB matrix (m, m)
            BF: BF matrix (m, m)
            m: Matrix dimension
            tol: Convergence tolerance

        Returns:
            True if converged
        """
        norm_BB = matrix_inf_norm_jit(BB, m)
        norm_BF = matrix_inf_norm_jit(BF, m)
        return min(norm_BB, norm_BF) < tol

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def matrix_inf_norm_jit(A: np.ndarray, m: int) -> float:
        """Pure Python infinity norm."""
        return float(np.linalg.norm(A, np.inf))

    def matmul_jit(A: np.ndarray, B: np.ndarray, C: np.ndarray, m: int) -> None:
        """Pure Python matrix multiplication."""
        np.copyto(C, A @ B)

    def matmul_add_jit(A: np.ndarray, B: np.ndarray, C: np.ndarray, m: int) -> None:
        """Pure Python matrix multiply-add."""
        C += A @ B

    def lr_step_lstar_jit(
        BF: np.ndarray,
        BB: np.ndarray,
        Lstar: np.ndarray,
        temp: np.ndarray,
        m: int
    ) -> None:
        """Pure Python Lstar computation."""
        np.copyto(Lstar, BF @ BB + BB @ BF)

    def lr_step_squares_jit(
        BF: np.ndarray,
        BB: np.ndarray,
        Fstar: np.ndarray,
        Bstar: np.ndarray,
        m: int
    ) -> None:
        """Pure Python squares computation."""
        np.copyto(Fstar, BF @ BF)
        np.copyto(Bstar, BB @ BB)

    def stationary_dist_loop_jit(
        pi0: np.ndarray,
        R: np.ndarray,
        K: int,
        m: int,
        output: np.ndarray
    ) -> None:
        """Pure Python stationary distribution loop."""
        output[:m] = pi0.flatten()
        pix = pi0.flatten().copy()
        for k in range(1, K + 1):
            pix = pix @ R
            output[k * m:(k + 1) * m] = pix

    def scale_and_add_identity_jit(
        A: np.ndarray,
        scale: float,
        m: int,
        output: np.ndarray
    ) -> None:
        """Pure Python scale and add identity."""
        np.copyto(output, A / scale + np.eye(m))

    def scale_matrix_inplace_jit(A: np.ndarray, scale: float, m: int) -> None:
        """Pure Python in-place scaling."""
        A /= scale

    def compute_drift_jit(
        theta: np.ndarray,
        B: np.ndarray,
        F: np.ndarray,
        m: int
    ) -> float:
        """Pure Python drift computation."""
        return float(theta @ np.sum(B, axis=1) - theta @ np.sum(F, axis=1))

    def apply_shift_transient_jit(
        F: np.ndarray,
        L: np.ndarray,
        theta: np.ndarray,
        B: np.ndarray,
        m: int
    ) -> None:
        """Pure Python shift for transient case."""
        thetaF = theta @ F
        thetaB = theta @ B
        F -= np.ones((m, 1)) @ thetaF.reshape(1, -1)
        L += np.ones((m, 1)) @ thetaB.reshape(1, -1)

    def apply_shift_recurrent_jit(
        B: np.ndarray,
        L: np.ndarray,
        F: np.ndarray,
        m: int
    ) -> None:
        """Pure Python shift for recurrent case."""
        uT = np.ones((1, m)) / m
        B -= np.sum(B, axis=1, keepdims=True) @ uT
        L += np.sum(F, axis=1, keepdims=True) @ uT

    def check_convergence_jit(BB: np.ndarray, BF: np.ndarray, m: int, tol: float) -> bool:
        """Pure Python convergence check."""
        return min(np.linalg.norm(BB, np.inf), np.linalg.norm(BF, np.inf)) < tol


__all__ = [
    'HAS_NUMBA',
    'matrix_inf_norm_jit',
    'matmul_jit',
    'matmul_add_jit',
    'lr_step_lstar_jit',
    'lr_step_squares_jit',
    'stationary_dist_loop_jit',
    'scale_and_add_identity_jit',
    'scale_matrix_inplace_jit',
    'compute_drift_jit',
    'apply_shift_transient_jit',
    'apply_shift_recurrent_jit',
    'check_convergence_jit',
]
