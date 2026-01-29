"""
JIT-compiled kernels for Asymptotic Methods (Leading Eigenvalue).

Provides Numba-accelerated versions of core asymptotic computational hotspots:
- Fixed-point iteration (FPI) for mode location
- Hessian matrix computation
- Multinomial coefficient computation

Graceful fallback to pure Python if Numba is not available.

License: MIT (same as LINE)
"""

import numpy as np
from typing import Tuple
from math import lgamma

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
    def le_fpi_jit(
        L: np.ndarray,
        N: np.ndarray,
        M: int,
        R: int,
        max_iter: int,
        tol: float
    ) -> np.ndarray:
        """
        JIT-compiled fixed-point iteration to find mode location (no think time).

        Solves for u such that u_i = f_i(u) converges.

        Args:
            L: Service demand matrix (M x R)
            N: Population vector (R,)
            M: Number of stations
            R: Number of classes
            max_iter: Maximum iterations
            tol: Convergence tolerance

        Returns:
            Mode location vector u (M,)
        """
        u = np.ones(M) / M
        u_prev = np.full(M, np.inf)
        Ntot = 0.0
        for r in range(R):
            Ntot += N[r]

        for _ in range(max_iter):
            # Check convergence
            diff = 0.0
            for i in range(M):
                diff += np.abs(u[i] - u_prev[i])
            if diff < tol:
                break

            # Copy current to previous
            for i in range(M):
                u_prev[i] = u[i]

            # Update u
            for i in range(M):
                u[i] = 1.0 / (Ntot + M)
                for r in range(R):
                    denom = 0.0
                    for k in range(M):
                        denom += u_prev[k] * L[k, r]
                    if denom > 0:
                        u[i] += N[r] / (Ntot + M) * L[i, r] * u_prev[i] / denom

        return u

    @njit(fastmath=True, cache=True)
    def le_fpiZ_jit(
        L: np.ndarray,
        N: np.ndarray,
        Z: np.ndarray,
        M: int,
        R: int,
        max_iter: int,
        tol: float
    ) -> Tuple[np.ndarray, float]:
        """
        JIT-compiled fixed-point iteration to find mode location (with think time).

        Args:
            L: Service demand matrix (M x R)
            N: Population vector (R,)
            Z: Think time vector (R,)
            M: Number of stations
            R: Number of classes
            max_iter: Maximum iterations
            tol: Convergence tolerance

        Returns:
            Tuple of (u, v) where u is mode location and v is scale factor
        """
        Ntot = 0.0
        for r in range(R):
            Ntot += N[r]
        eta = Ntot + M

        u = np.ones(M) / M
        v = eta + 1
        u_prev = np.full(M, np.inf)

        for _ in range(max_iter):
            # Check convergence
            diff = 0.0
            for i in range(M):
                diff += np.abs(u[i] - u_prev[i])
            if diff < tol:
                break

            # Copy current to previous
            for i in range(M):
                u_prev[i] = u[i]
            v_prev = v

            # Update u
            for i in range(M):
                u[i] = 1.0 / eta
                for r in range(R):
                    # Compute denom = Z[r] + v * u_prev.dot(L[:, r])
                    dot_uL = 0.0
                    for k in range(M):
                        dot_uL += u_prev[k] * L[k, r]
                    denom = Z[r] + v * dot_uL
                    if denom > 0:
                        u[i] += (N[r] / eta) * (Z[r] + v * L[i, r]) * u_prev[i] / denom

            # Compute xi and update v
            xi_sum = 0.0
            for r in range(R):
                dot_uL = 0.0
                for k in range(M):
                    dot_uL += u_prev[k] * L[k, r]
                denom = Z[r] + v_prev * dot_uL
                if denom > 0:
                    xi_sum += N[r] / denom * Z[r]

            v = eta + 1 - xi_sum

        return u, v

    @njit(fastmath=True, cache=True)
    def le_hessian_jit(
        L: np.ndarray,
        N: np.ndarray,
        u: np.ndarray,
        M: int,
        R: int
    ) -> np.ndarray:
        """
        JIT-compiled Hessian matrix computation (no think time case).

        Args:
            L: Service demand matrix (M x R)
            N: Population vector (R,)
            u: Mode location vector (M,)
            M: Number of stations
            R: Number of classes

        Returns:
            Hessian matrix (M-1 x M-1)
        """
        Ntot = 0.0
        for r in range(R):
            Ntot += N[r]

        hu = np.zeros((M - 1, M - 1))

        # Precompute u.dot(L[:, r]) for each r
        uL = np.zeros(R)
        for r in range(R):
            for k in range(M):
                uL[r] += u[k] * L[k, r]

        for i in range(M - 1):
            for j in range(M - 1):
                if i != j:
                    # Off-diagonal
                    hu[i, j] = -(Ntot + M) * u[i] * u[j]
                    for r in range(R):
                        denom = uL[r] * uL[r]
                        if denom > 0:
                            hu[i, j] += N[r] * L[i, r] * L[j, r] * u[i] * u[j] / denom
                else:
                    # Diagonal
                    # Compute sum of u excluding i
                    u_others_sum = 0.0
                    for k in range(M):
                        if k != i:
                            u_others_sum += u[k]

                    hu[i, j] = (Ntot + M) * u[i] * u_others_sum

                    for r in range(R):
                        denom = uL[r] * uL[r]
                        if denom > 0:
                            # Compute L_others.dot(u_others) = u.dot(L[:, r]) - u[i]*L[i, r]
                            L_others_u_others = uL[r] - u[i] * L[i, r]
                            hu[i, j] -= N[r] * L[i, r] * u[i] * L_others_u_others / denom

        return hu

    @njit(fastmath=True, cache=True)
    def le_hessianZ_jit(
        L: np.ndarray,
        N: np.ndarray,
        Z: np.ndarray,
        u: np.ndarray,
        v: float,
        M: int,
        R: int
    ) -> np.ndarray:
        """
        JIT-compiled Hessian matrix computation (with think time case).

        Args:
            L: Service demand matrix (M x R)
            N: Population vector (R,)
            Z: Think time vector (R,)
            u: Mode location vector (M,)
            v: Scale factor
            M: Number of stations (K in the original code)
            R: Number of classes

        Returns:
            Hessian matrix (M x M)
        """
        Ntot = 0.0
        for r in range(R):
            Ntot += N[r]
        eta = Ntot + M

        # Compute csi
        csi = np.zeros(R)
        for r in range(R):
            dot_uL = 0.0
            for k in range(M):
                dot_uL += u[k] * L[k, r]
            denom = Z[r] + v * dot_uL
            if denom > 0:
                csi[r] = N[r] / denom

        # Compute Lhat
        Lhat = np.zeros((M, R))
        for k in range(M):
            for r in range(R):
                Lhat[k, r] = Z[r] + v * L[k, r]

        # Compute A matrix
        A = np.zeros((M, M))

        # Off-diagonal elements
        for i in range(M):
            for j in range(M):
                if i != j:
                    A[i, j] = -eta * u[i] * u[j]
                    for r in range(R):
                        if N[r] > 0:
                            A[i, j] += csi[r] * csi[r] * Lhat[i, r] * Lhat[j, r] * u[i] * u[j] / N[r]

        # Diagonal elements (set so rows sum to zero)
        for i in range(M):
            row_sum = 0.0
            for j in range(M):
                if i != j:
                    row_sum += A[i, j]
            A[i, i] = -row_sum

        # Reduce to (M-1) x (M-1) and add extra element for v
        A_full = np.zeros((M, M))
        for i in range(M - 1):
            for j in range(M - 1):
                A_full[i, j] = A[i, j]

        # Compute element [M-1, M-1] for v
        A_full[M - 1, M - 1] = 1.0
        for r in range(R):
            if N[r] > 0:
                dot_uL = 0.0
                for k in range(M):
                    dot_uL += u[k] * L[k, r]
                A_full[M - 1, M - 1] -= (csi[r] * csi[r] / N[r]) * Z[r] * dot_uL
        A_full[M - 1, M - 1] *= v

        # Off-diagonal elements involving v
        for i in range(M - 1):
            val = 0.0
            for r in range(R):
                if N[r] > 0:
                    dot_uL = 0.0
                    for k in range(M):
                        dot_uL += u[k] * L[k, r]
                    val += v * u[i] * (
                        (csi[r] * csi[r] / N[r]) * Lhat[i, r] * dot_uL - csi[r] * L[i, r]
                    )
            A_full[i, M - 1] = val
            A_full[M - 1, i] = val

        return A_full

    @njit(fastmath=True, cache=True)
    def factln_jit(n: float) -> float:
        """JIT-compiled log(n!) using lgamma."""
        if n <= 0:
            return 0.0
        return lgamma(n + 1)

    @njit(fastmath=True, cache=True)
    def multinomialln_jit(n: np.ndarray) -> float:
        """
        JIT-compiled log multinomial coefficient.

        Args:
            n: Population vector

        Returns:
            log(multinomial(sum(n); n))
        """
        total = 0.0
        for i in range(len(n)):
            total += n[i]

        result = lgamma(total + 1)
        for i in range(len(n)):
            result -= lgamma(n[i] + 1)

        return result

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def le_fpi_jit(
        L: np.ndarray,
        N: np.ndarray,
        M: int,
        R: int,
        max_iter: int,
        tol: float
    ) -> np.ndarray:
        """Pure Python FPI (no think time)."""
        u = np.ones(M) / M
        u_prev = np.full(M, np.inf)
        Ntot = np.sum(N)

        for _ in range(max_iter):
            if np.linalg.norm(u - u_prev, 1) < tol:
                break
            u_prev = u.copy()

            for i in range(M):
                u[i] = 1.0 / (Ntot + M)
                for r in range(R):
                    denom = np.dot(u_prev, L[:, r])
                    if denom > 0:
                        u[i] += N[r] / (Ntot + M) * L[i, r] * u_prev[i] / denom

        return u

    def le_fpiZ_jit(
        L: np.ndarray,
        N: np.ndarray,
        Z: np.ndarray,
        M: int,
        R: int,
        max_iter: int,
        tol: float
    ) -> Tuple[np.ndarray, float]:
        """Pure Python FPI (with think time)."""
        Ntot = np.sum(N)
        eta = Ntot + M
        u = np.ones(M) / M
        v = eta + 1
        u_prev = np.full(M, np.inf)

        for _ in range(max_iter):
            if np.linalg.norm(u - u_prev, 1) < tol:
                break
            u_prev = u.copy()
            v_prev = v

            for i in range(M):
                u[i] = 1.0 / eta
                for r in range(R):
                    denom = Z[r] + v * np.dot(u_prev, L[:, r])
                    if denom > 0:
                        u[i] += (N[r] / eta) * (Z[r] + v * L[i, r]) * u_prev[i] / denom

            xi = np.zeros(R)
            for r in range(R):
                denom = Z[r] + v_prev * np.dot(u_prev, L[:, r])
                if denom > 0:
                    xi[r] = N[r] / denom

            v = eta + 1 - np.sum(xi * Z)

        return u, v

    def le_hessian_jit(
        L: np.ndarray,
        N: np.ndarray,
        u: np.ndarray,
        M: int,
        R: int
    ) -> np.ndarray:
        """Pure Python Hessian (no think time)."""
        Ntot = np.sum(N)
        hu = np.zeros((M - 1, M - 1))

        for i in range(M - 1):
            for j in range(M - 1):
                if i != j:
                    hu[i, j] = -(Ntot + M) * u[i] * u[j]
                    for r in range(R):
                        denom = np.dot(u, L[:, r]) ** 2
                        if denom > 0:
                            hu[i, j] += N[r] * L[i, r] * L[j, r] * u[i] * u[j] / denom
                else:
                    u_others = np.delete(u, i)
                    hu[i, j] = (Ntot + M) * u[i] * np.sum(u_others)
                    for r in range(R):
                        L_others = np.delete(L[:, r], i)
                        denom = np.dot(u, L[:, r]) ** 2
                        if denom > 0:
                            hu[i, j] -= N[r] * L[i, r] * u[i] * np.dot(u_others, L_others) / denom

        return hu

    def le_hessianZ_jit(
        L: np.ndarray,
        N: np.ndarray,
        Z: np.ndarray,
        u: np.ndarray,
        v: float,
        M: int,
        R: int
    ) -> np.ndarray:
        """Pure Python Hessian (with think time)."""
        Ntot = np.sum(N)
        eta = Ntot + M

        csi = np.zeros(R)
        for r in range(R):
            denom = Z[r] + v * np.dot(u, L[:, r])
            if denom > 0:
                csi[r] = N[r] / denom

        Lhat = np.zeros((M, R))
        for k in range(M):
            for r in range(R):
                Lhat[k, r] = Z[r] + v * L[k, r]

        A = np.zeros((M, M))

        for i in range(M):
            for j in range(M):
                if i != j:
                    A[i, j] = -eta * u[i] * u[j]
                    for r in range(R):
                        if N[r] > 0:
                            A[i, j] += csi[r] ** 2 * Lhat[i, r] * Lhat[j, r] * u[i] * u[j] / N[r]

        for i in range(M):
            row_sum = np.sum(np.delete(A[i, :], i))
            A[i, i] = -row_sum

        A_full = np.zeros((M, M))
        A_full[:M - 1, :M - 1] = A[:M - 1, :M - 1]

        A_full[M - 1, M - 1] = 1.0
        for r in range(R):
            if N[r] > 0:
                A_full[M - 1, M - 1] -= (csi[r] ** 2 / N[r]) * Z[r] * np.dot(u, L[:, r])
        A_full[M - 1, M - 1] *= v

        for i in range(M - 1):
            val = 0.0
            for r in range(R):
                if N[r] > 0:
                    val += v * u[i] * (
                        (csi[r] ** 2 / N[r]) * Lhat[i, r] * np.dot(u, L[:, r]) - csi[r] * L[i, r]
                    )
            A_full[i, M - 1] = val
            A_full[M - 1, i] = val

        return A_full

    def factln_jit(n: float) -> float:
        """Pure Python log(n!)."""
        if n <= 0:
            return 0.0
        return lgamma(n + 1)

    def multinomialln_jit(n: np.ndarray) -> float:
        """Pure Python log multinomial."""
        from scipy.special import gammaln
        return float(gammaln(np.sum(n) + 1) - np.sum(gammaln(np.asarray(n) + 1)))


__all__ = [
    'HAS_NUMBA',
    'le_fpi_jit',
    'le_fpiZ_jit',
    'le_hessian_jit',
    'le_hessianZ_jit',
    'factln_jit',
    'multinomialln_jit',
]
