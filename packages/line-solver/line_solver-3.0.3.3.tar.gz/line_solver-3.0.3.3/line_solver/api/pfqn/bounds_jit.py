"""
JIT-compiled kernels for Asymptotic Bounds.

Provides Numba-accelerated versions of asymptotic bound computations:
- Queue length bounds (Zahorjan-Gittelsohn-Bryant)
- Throughput bounds (ZGSB)

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
    def xzabalow_jit(L: np.ndarray, N: float, Z: float, M: int) -> float:
        """
        JIT-compiled lower asymptotic bound on throughput (Zahorjan-Balanced).

        Args:
            L: Service demand vector (M,)
            N: Population (scalar)
            Z: Think time
            M: Number of stations

        Returns:
            Lower bound on throughput
        """
        Ltot = 0.0
        for i in range(M):
            Ltot += L[i]
        return N / (Z + Ltot * N)

    @njit(fastmath=True, cache=True)
    def xzabaup_jit(L: np.ndarray, N: float, Z: float, M: int) -> float:
        """
        JIT-compiled upper asymptotic bound on throughput (Zahorjan-Balanced).

        Args:
            L: Service demand vector (M,)
            N: Population (scalar)
            Z: Think time
            M: Number of stations

        Returns:
            Upper bound on throughput
        """
        max_L = L[0]
        Ltot = 0.0
        for i in range(M):
            if L[i] > max_L:
                max_L = L[i]
            Ltot += L[i]

        bound1 = 1.0 / max_L
        bound2 = N / (Ltot + Z)
        return min(bound1, bound2)

    @njit(fastmath=True, cache=True)
    def qzgblow_jit(L: np.ndarray, N: float, Z: float, i: int, M: int) -> float:
        """
        JIT-compiled lower asymptotic bound on queue length (Zahorjan-Gittelsohn-Bryant).

        Args:
            L: Service demand vector (M,)
            N: Population (scalar)
            Z: Think time
            i: Station index (0-based)
            M: Number of stations

        Returns:
            Lower bound on mean queue length at station i
        """
        max_L = L[0]
        Ltot = 0.0
        for k in range(M):
            if L[k] > max_L:
                max_L = L[k]
            Ltot += L[k]

        yi = N * L[i] / (Z + Ltot + max_L * N)

        if yi >= 1:
            return N

        Qgb = yi / (1 - yi) - (yi ** (N + 1)) / (1 - yi)
        if Qgb < 0:
            return 0.0
        return Qgb

    @njit(fastmath=True, cache=True)
    def qzgbup_jit(L: np.ndarray, N: float, Z: float, i: int, M: int) -> float:
        """
        JIT-compiled upper asymptotic bound on queue length (Zahorjan-Gittelsohn-Bryant).

        Args:
            L: Service demand vector (M,)
            N: Population (scalar)
            Z: Think time
            i: Station index (0-based)
            M: Number of stations

        Returns:
            Upper bound on mean queue length at station i
        """
        max_L = L[0]
        Ltot = 0.0
        L_sq_sum = 0.0
        for k in range(M):
            if L[k] > max_L:
                max_L = L[k]
            Ltot += L[k]
            L_sq_sum += L[k] * L[k]

        sigma = L_sq_sum / Ltot

        # Compute upper bound on throughput at N-1
        if N > 1:
            X_N_minus_1 = xzabaup_jit(L, N - 1, Z, M)
        else:
            X_N_minus_1 = 0.0

        bound1 = 1.0 / max_L
        bound2 = N / (Z + Ltot + sigma * (N - 1 - Z * X_N_minus_1))
        Yi = L[i] * min(bound1, bound2)

        if Yi < 1:
            Qgb = Yi / (1 - Yi) - (Yi ** (N + 1)) / (1 - Yi)
            if Qgb < 0:
                return 0.0
            return Qgb
        else:
            return N

    @njit(fastmath=True, cache=True)
    def xzgsblow_jit(L: np.ndarray, N: float, Z: float, M: int) -> float:
        """
        JIT-compiled lower asymptotic bound on throughput (ZGSB).

        Args:
            L: Service demand vector (M,)
            N: Population (scalar)
            Z: Think time
            M: Number of stations

        Returns:
            Lower bound on throughput
        """
        max_L = L[0]
        Ltot = 0.0
        for k in range(M):
            if L[k] > max_L:
                max_L = L[k]
            Ltot += L[k]

        R = Z + Ltot + max_L * (N - 1)

        for i in range(M):
            if L[i] < max_L:
                R = R + (L[i] - max_L) * qzgblow_jit(L, N - 1, Z, i, M)

        discriminant = R * R - 4 * Z * max_L * (N - 1)
        if discriminant < 0:
            # Fall back to simple bound
            return xzabalow_jit(L, N, Z, M)

        X = 2 * N / (R + np.sqrt(discriminant))
        return X

    @njit(fastmath=True, cache=True)
    def xzgsbup_jit(L: np.ndarray, N: float, Z: float, M: int) -> float:
        """
        JIT-compiled upper asymptotic bound on throughput (ZGSB).

        Args:
            L: Service demand vector (M,)
            N: Population (scalar)
            Z: Think time
            M: Number of stations

        Returns:
            Upper bound on throughput
        """
        max_L = L[0]
        Ltot = 0.0
        for k in range(M):
            if L[k] > max_L:
                max_L = L[k]
            Ltot += L[k]

        R = Z + Ltot + max_L * (N - 1)

        for i in range(M):
            if L[i] < max_L:
                R = R + (L[i] - max_L) * qzgbup_jit(L, N - 1, Z, i, M)

        discriminant = R * R - 4 * Z * max_L * N
        if discriminant < 0:
            # Fall back to simple bound
            return xzabaup_jit(L, N, Z, M)

        X = 2 * N / (R + np.sqrt(discriminant))
        return X

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def xzabalow_jit(L: np.ndarray, N: float, Z: float, M: int) -> float:
        """Pure Python lower throughput bound."""
        Ltot = np.sum(L)
        return float(N / (Z + Ltot * N))

    def xzabaup_jit(L: np.ndarray, N: float, Z: float, M: int) -> float:
        """Pure Python upper throughput bound."""
        return float(min(1.0 / np.max(L), N / (np.sum(L) + Z)))

    def qzgblow_jit(L: np.ndarray, N: float, Z: float, i: int, M: int) -> float:
        """Pure Python lower queue length bound."""
        yi = N * L[i] / (Z + np.sum(L) + np.max(L) * N)

        if yi >= 1:
            return float(N)

        Qgb = yi / (1 - yi) - (yi ** (N + 1)) / (1 - yi)
        return float(max(0, Qgb))

    def qzgbup_jit(L: np.ndarray, N: float, Z: float, i: int, M: int) -> float:
        """Pure Python upper queue length bound."""
        sigma = np.sum(L ** 2) / np.sum(L)

        if N > 1:
            X_N_minus_1 = xzabaup_jit(L, N - 1, Z, M)
        else:
            X_N_minus_1 = 0.0

        Yi = L[i] * min(
            1.0 / np.max(L),
            N / (Z + np.sum(L) + sigma * (N - 1 - Z * X_N_minus_1))
        )

        if Yi < 1:
            Qgb = Yi / (1 - Yi) - (Yi ** (N + 1)) / (1 - Yi)
            return float(max(0, Qgb))
        else:
            return float(N)

    def xzgsblow_jit(L: np.ndarray, N: float, Z: float, M: int) -> float:
        """Pure Python lower throughput bound (ZGSB)."""
        max_L = np.max(L)
        R = Z + np.sum(L) + max_L * (N - 1)

        for i in range(M):
            if L[i] < max_L:
                R = R + (L[i] - max_L) * qzgblow_jit(L, N - 1, Z, i, M)

        discriminant = R ** 2 - 4 * Z * max_L * (N - 1)
        if discriminant < 0:
            return xzabalow_jit(L, N, Z, M)

        X = 2 * N / (R + np.sqrt(discriminant))
        return float(X)

    def xzgsbup_jit(L: np.ndarray, N: float, Z: float, M: int) -> float:
        """Pure Python upper throughput bound (ZGSB)."""
        max_L = np.max(L)
        R = Z + np.sum(L) + max_L * (N - 1)

        for i in range(M):
            if L[i] < max_L:
                R = R + (L[i] - max_L) * qzgbup_jit(L, N - 1, Z, i, M)

        discriminant = R ** 2 - 4 * Z * max_L * N
        if discriminant < 0:
            return xzabaup_jit(L, N, Z, M)

        X = 2 * N / (R + np.sqrt(discriminant))
        return float(X)


__all__ = [
    'HAS_NUMBA',
    'xzabalow_jit',
    'xzabaup_jit',
    'qzgblow_jit',
    'qzgbup_jit',
    'xzgsblow_jit',
    'xzgsbup_jit',
]
