"""
JIT-compiled kernels for Normalizing Constant (NC) algorithms.

Provides Numba-accelerated versions of the core NC computational hotspots:
- Population vector hashing
- Delay station product-form factor
- Convolution algorithm recursion

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
    def hashpop_nc_jit(n: np.ndarray, N: np.ndarray) -> int:
        """
        JIT-compiled population vector hashing.

        Maps population vector n to unique integer index in
        the flattened population lattice [0, prod(N+1)).

        Args:
            n: Population vector
            N: Maximum population per class

        Returns:
            Linear index
        """
        R = len(n)
        idx = 0
        mult = 1
        for i in range(R - 1, -1, -1):
            idx += int(n[i]) * mult
            mult *= int(N[i]) + 1
        return idx

    @njit(fastmath=True, cache=True)
    def pprod_next_nc_jit(n: np.ndarray, N: np.ndarray) -> Tuple[np.ndarray, bool]:
        """
        JIT-compiled population vector increment.

        Args:
            n: Current population vector
            N: Maximum population per class

        Returns:
            Tuple of (next_n, is_valid) where is_valid is False when exhausted
        """
        R = len(n)
        n_next = n.copy()

        # Find rightmost position that can be incremented
        for i in range(R - 1, -1, -1):
            if n_next[i] < N[i]:
                n_next[i] += 1
                # Reset positions to the right
                for j in range(i + 1, R):
                    n_next[j] = 0
                return n_next, True

        # All exhausted
        return n_next, False

    @njit(fastmath=True, cache=True)
    def pff_delay_jit(Z: np.ndarray, n: np.ndarray) -> float:
        """
        JIT-compiled product-form factor for delay stations.

        Computes contribution to normalizing constant from delay stations:
        prod_r (Z[r]^n[r] / n[r]!)

        Args:
            Z: Think times per class
            n: Population vector

        Returns:
            Product-form factor
        """
        R = len(n)
        log_result = 0.0

        for r in range(R):
            nr = int(n[r])
            if nr > 0:
                # If Z[r] = 0 and n[r] > 0, then Z[r]^n[r] = 0^n = 0
                if Z[r] <= 0:
                    return 0.0
                # log(Z[r]^n[r] / n[r]!) = n[r]*log(Z[r]) - log(n[r]!)
                log_result += nr * np.log(Z[r])
                # Subtract log(n[r]!) using lgamma(n+1)
                log_result -= lgamma(nr + 1)

        return np.exp(log_result)

    @njit(fastmath=True, cache=True)
    def convolution_recursion_jit(
        L: np.ndarray,
        N: np.ndarray,
        Z: np.ndarray,
        M: int,
        R: int
    ) -> Tuple[float, float]:
        """
        JIT-compiled Buzen's convolution algorithm.

        Computes the normalizing constant G(N) for a closed product-form
        queueing network.

        Args:
            L: Service demand matrix (M x R)
            N: Population vector (R,) as int
            Z: Think time vector (R,)
            M: Number of stations
            R: Number of classes

        Returns:
            Tuple of (G, lG) - normalizing constant and its log
        """
        # Total number of population vectors
        product_N_plus_one = 1
        for r in range(R):
            product_N_plus_one *= int(N[r]) + 1

        # G[m, idx] = G_m(n) where idx = hashpop(n, N)
        G = np.ones((M + 1, product_N_plus_one))

        # Iterate through all population vectors
        n = np.zeros(R, dtype=np.int64)

        while True:
            idxn = hashpop_nc_jit(n, N)

            # Base case: delay station contribution
            G[0, idxn] = pff_delay_jit(Z, n)

            # Convolution recursion: G_m(n) = G_{m-1}(n) + sum_r L[m-1,r] * G_m(n - e_r)
            for m in range(1, M + 1):
                G[m, idxn] = G[m - 1, idxn]
                for r in range(R):
                    if n[r] >= 1:
                        n[r] -= 1
                        idxn_1r = hashpop_nc_jit(n, N)
                        n[r] += 1
                        G[m, idxn] += L[m - 1, r] * G[m, idxn_1r]

            # Next population vector
            n_next, is_valid = pprod_next_nc_jit(n, N)
            if not is_valid:
                break
            n = n_next

        # Final normalizing constant
        Gn = G[M, product_N_plus_one - 1]
        if Gn > 0:
            lGn = np.log(Gn)
        else:
            lGn = -np.inf

        return Gn, lGn

    @njit(fastmath=True, cache=True)
    def factln_jit(n: float) -> float:
        """JIT-compiled log(n!) using lgamma."""
        if n <= 0:
            return 0.0
        return lgamma(n + 1)

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def hashpop_nc_jit(n: np.ndarray, N: np.ndarray) -> int:
        """Pure Python population hashing."""
        R = len(n)
        idx = 0
        mult = 1
        for i in range(R - 1, -1, -1):
            idx += int(n[i]) * mult
            mult *= int(N[i]) + 1
        return idx

    def pprod_next_nc_jit(n: np.ndarray, N: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Pure Python population increment."""
        R = len(n)
        n_next = n.copy()

        for i in range(R - 1, -1, -1):
            if n_next[i] < N[i]:
                n_next[i] += 1
                for j in range(i + 1, R):
                    n_next[j] = 0
                return n_next, True

        return n_next, False

    def pff_delay_jit(Z: np.ndarray, n: np.ndarray) -> float:
        """Pure Python delay station factor."""
        from math import factorial
        R = len(n)
        result = 1.0
        for r in range(R):
            nr = int(n[r])
            if nr > 0:
                result *= (Z[r] ** nr) / factorial(nr)
        return result

    def convolution_recursion_jit(
        L: np.ndarray,
        N: np.ndarray,
        Z: np.ndarray,
        M: int,
        R: int
    ) -> Tuple[float, float]:
        """Pure Python convolution algorithm."""
        product_N_plus_one = int(np.prod(N + 1))
        G = np.ones((M + 1, product_N_plus_one))

        n = np.zeros(R, dtype=int)

        while True:
            idxn = hashpop_nc_jit(n, N)
            G[0, idxn] = pff_delay_jit(Z, n)

            for m in range(1, M + 1):
                G[m, idxn] = G[m - 1, idxn]
                for r in range(R):
                    if n[r] >= 1:
                        n[r] -= 1
                        idxn_1r = hashpop_nc_jit(n, N)
                        n[r] += 1
                        G[m, idxn] += L[m - 1, r] * G[m, idxn_1r]

            n_next, is_valid = pprod_next_nc_jit(n, N)
            if not is_valid:
                break
            n = n_next

        Gn = G[M, product_N_plus_one - 1]
        lGn = np.log(Gn) if Gn > 0 else float('-inf')

        return Gn, lGn

    def factln_jit(n: float) -> float:
        """Pure Python log(n!)."""
        if n <= 0:
            return 0.0
        return lgamma(n + 1)


__all__ = [
    'HAS_NUMBA',
    'hashpop_nc_jit',
    'pprod_next_nc_jit',
    'pff_delay_jit',
    'convolution_recursion_jit',
    'factln_jit',
]
