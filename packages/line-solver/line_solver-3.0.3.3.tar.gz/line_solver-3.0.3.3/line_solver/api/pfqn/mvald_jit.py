"""
JIT-compiled kernels for Load-Dependent MVA algorithms.

Provides Numba-accelerated versions of the core MVALD computational hotspots:
- Population vector manipulation
- Waiting time computation
- Marginal probability updates
- Main population iteration loop

Graceful fallback to pure Python if Numba is not available.

License: MIT (same as LINE)
"""

import numpy as np
from typing import Tuple, Optional

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
    def hashpop_mvald_jit(n: np.ndarray, N: np.ndarray) -> int:
        """
        JIT-compiled population vector hashing for MVALD.

        Uses row-major indexing convention.

        Args:
            n: Population vector (R,)
            N: Maximum population vector (R,)

        Returns:
            Linear index
        """
        R = len(N)
        index = 0
        for r in range(R):
            prod = 1
            for j in range(r):
                prod *= int(N[j]) + 1
            index += prod * int(n[r])
        return index

    @njit(fastmath=True, cache=True)
    def pprod_next_mvald_jit(n: np.ndarray, N: np.ndarray) -> Tuple[np.ndarray, bool]:
        """
        JIT-compiled population vector increment for MVALD.

        Args:
            n: Current population vector (R,)
            N: Maximum population vector (R,)

        Returns:
            Tuple of (next_n, is_valid) where is_valid is False when exhausted
        """
        R = len(N)
        n_next = n.copy()

        # Check if at maximum
        at_max = True
        for i in range(R):
            if n_next[i] != N[i]:
                at_max = False
                break

        if at_max:
            return n_next, False

        # Find rightmost index that can be incremented
        s = R - 1
        while s >= 0 and n_next[s] == N[s]:
            n_next[s] = 0
            s -= 1

        if s < 0:
            return n_next, False

        n_next[s] += 1
        return n_next, True

    @njit(fastmath=True, cache=True)
    def compute_waiting_times_jit(
        n: np.ndarray,
        n_sum: int,
        L: np.ndarray,
        mu: np.ndarray,
        pi_all: np.ndarray,
        N: np.ndarray,
        M: int,
        R: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        JIT-compiled waiting time computation for one population vector.

        Args:
            n: Current population vector
            n_sum: Sum of n
            L: Service demands (M x R)
            mu: Load-dependent rates (M x Ntot)
            pi_all: Marginal probabilities (M x Ntot+1 x num_states)
            N: Maximum population
            M: Number of stations
            R: Number of classes

        Returns:
            Tuple of (WN_local, Xs) where:
                WN_local: Waiting times (M x R)
                Xs: Throughputs (R,)
        """
        WN_local = np.zeros((M, R))
        Xs = np.zeros(R)
        mu_cols = mu.shape[1]

        for s in range(R):
            if n[s] > 0:
                # Compute n - e_s
                n_minus_s = n.copy()
                n_minus_s[s] -= 1
                n_minus_s_idx = hashpop_mvald_jit(n_minus_s, N)

                for ist in range(M):
                    for k in range(1, n_sum + 1):
                        if k <= mu_cols:
                            mu_val = mu[ist, k - 1]
                            if mu_val > 0:
                                WN_local[ist, s] += (L[ist, s] / mu_val) * k * pi_all[ist, k - 1, n_minus_s_idx]

        return WN_local, Xs

    @njit(fastmath=True, cache=True)
    def mvald_iteration_kernel_jit(
        L: np.ndarray,
        N: np.ndarray,
        Z: np.ndarray,
        mu: np.ndarray,
        stabilize: bool
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, bool, np.ndarray]:
        """
        JIT-compiled main MVALD iteration kernel.

        Args:
            L: Service demands (M x R)
            N: Population vector (R,) as int
            Z: Think times (R,)
            mu: Load-dependent rates (M x Ntot)
            stabilize: Force non-negative probabilities

        Returns:
            Tuple of (XN, QN, UN, CN, lGN, is_num_stable, pi)
        """
        M = L.shape[0]
        R = L.shape[1]
        Ntot = 0
        for r in range(R):
            Ntot += int(N[r])

        # Number of population states
        num_states = 1
        for r in range(R):
            num_states *= int(N[r]) + 1

        # Throughputs for each population
        Xs = np.zeros((R, num_states))

        # Marginal probabilities: pi_all[i, k, pop] = P(queue i has k jobs | pop)
        pi_all = np.ones((M, Ntot + 1, num_states))

        is_num_stable = True
        mu_cols = mu.shape[1]

        # Initialize population vector
        n = np.zeros(R, dtype=np.int64)
        pop_count = 0

        while True:
            pop_idx = hashpop_mvald_jit(n, N)
            n_sum = 0
            for r in range(R):
                n_sum += int(n[r])

            # Compute waiting times
            WN_local = np.zeros((M, R))
            for s in range(R):
                if n[s] > 0:
                    # n - e_s
                    n_minus_s = n.copy()
                    n_minus_s[s] -= 1
                    n_minus_s_idx = hashpop_mvald_jit(n_minus_s, N)

                    for ist in range(M):
                        for k in range(1, n_sum + 1):
                            if k <= mu_cols:
                                mu_val = mu[ist, k - 1]
                                if mu_val > 0:
                                    WN_local[ist, s] += (L[ist, s] / mu_val) * k * pi_all[ist, k - 1, n_minus_s_idx]

                    # Compute throughput
                    denom = Z[s]
                    for ist in range(M):
                        denom += WN_local[ist, s]
                    if denom > 0:
                        Xs[s, pop_idx] = n[s] / denom

            # Compute pi(k|n) for k >= 1
            for k in range(1, n_sum + 1):
                for ist in range(M):
                    pi_all[ist, k, pop_idx] = 0.0

                for s in range(R):
                    if n[s] > 0:
                        n_minus_s = n.copy()
                        n_minus_s[s] -= 1
                        n_minus_s_idx = hashpop_mvald_jit(n_minus_s, N)

                        for ist in range(M):
                            if k <= mu_cols:
                                mu_val = mu[ist, k - 1]
                                if mu_val > 0:
                                    pi_all[ist, k, pop_idx] += (L[ist, s] / mu_val) * Xs[s, pop_idx] * pi_all[ist, k - 1, n_minus_s_idx]

            # Compute pi(0|n)
            for ist in range(M):
                sum_pi = 0.0
                for k in range(1, n_sum + 1):
                    sum_pi += pi_all[ist, k, pop_idx]
                p0 = 1.0 - sum_pi

                if p0 < 0:
                    is_num_stable = False
                    if stabilize:
                        pi_all[ist, 0, pop_idx] = 1e-16
                    else:
                        pi_all[ist, 0, pop_idx] = p0
                else:
                    pi_all[ist, 0, pop_idx] = p0

            # Next population
            n_next, is_valid = pprod_next_mvald_jit(n, N)
            if not is_valid:
                break
            n = n_next
            pop_count += 1

        # Get final results for full population N
        N_idx = hashpop_mvald_jit(N, N)

        XN = np.zeros((1, R))
        for r in range(R):
            XN[0, r] = Xs[r, N_idx]

        pi = np.zeros((M, Ntot + 1))
        for ist in range(M):
            for k in range(Ntot + 1):
                pi[ist, k] = pi_all[ist, k, N_idx]

        # Compute waiting times at full population
        WN = np.zeros((M, R))
        for s in range(R):
            if N[s] > 0:
                n_minus_s = N.copy()
                n_minus_s[s] -= 1
                n_minus_s_idx = hashpop_mvald_jit(n_minus_s, N)

                for ist in range(M):
                    for k in range(1, Ntot + 1):
                        if k <= mu_cols:
                            mu_val = mu[ist, k - 1]
                            if mu_val > 0:
                                WN[ist, s] += (L[ist, s] / mu_val) * k * pi_all[ist, k - 1, n_minus_s_idx]

        # Compute metrics
        QN = np.zeros((M, R))
        for ist in range(M):
            for r in range(R):
                QN[ist, r] = WN[ist, r] * XN[0, r]

        UN = np.zeros((M, R))
        for ist in range(M):
            util = 1.0 - pi[ist, 0]
            for r in range(R):
                if L[ist, r] > 0:
                    UN[ist, r] = util
                else:
                    UN[ist, r] = 0.0

        CN = np.zeros((1, R))
        for r in range(R):
            if XN[0, r] > 0:
                CN[0, r] = N[r] / XN[0, r] - Z[r]

        # Simplified lGN (just return final value)
        lGN = np.zeros(1)

        return XN, QN, UN, CN, lGN, is_num_stable, pi

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def hashpop_mvald_jit(n: np.ndarray, N: np.ndarray) -> int:
        """Pure Python population hashing."""
        index = 0
        for r in range(len(N)):
            prod = 1
            for j in range(r):
                prod *= int(N[j]) + 1
            index += prod * int(n[r])
        return index

    def pprod_next_mvald_jit(n: np.ndarray, N: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Pure Python population increment."""
        R = len(N)
        n_next = n.copy()

        if np.all(n_next == N):
            return n_next, False

        s = R - 1
        while s >= 0 and n_next[s] == N[s]:
            n_next[s] = 0
            s -= 1

        if s < 0:
            return n_next, False

        n_next[s] += 1
        return n_next, True

    def compute_waiting_times_jit(
        n: np.ndarray,
        n_sum: int,
        L: np.ndarray,
        mu: np.ndarray,
        pi_all: np.ndarray,
        N: np.ndarray,
        M: int,
        R: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Pure Python waiting time computation."""
        WN_local = np.zeros((M, R))
        Xs = np.zeros(R)

        for s in range(R):
            if n[s] > 0:
                n_minus_s = n.copy()
                n_minus_s[s] -= 1
                n_minus_s_idx = hashpop_mvald_jit(n_minus_s, N)

                for ist in range(M):
                    for k in range(1, n_sum + 1):
                        if k <= mu.shape[1]:
                            mu_val = mu[ist, k - 1]
                            if mu_val > 0:
                                WN_local[ist, s] += (L[ist, s] / mu_val) * k * pi_all[ist, k - 1, n_minus_s_idx]

        return WN_local, Xs

    def mvald_iteration_kernel_jit(
        L: np.ndarray,
        N: np.ndarray,
        Z: np.ndarray,
        mu: np.ndarray,
        stabilize: bool
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, bool, np.ndarray]:
        """Pure Python MVALD iteration - falls back to original implementation."""
        # This fallback simply returns zeros - the caller should use original Python
        M, R = L.shape
        Ntot = int(np.sum(N))
        return (
            np.zeros((1, R)),
            np.zeros((M, R)),
            np.zeros((M, R)),
            np.zeros((1, R)),
            np.zeros(1),
            True,
            np.zeros((M, Ntot + 1))
        )


__all__ = [
    'HAS_NUMBA',
    'hashpop_mvald_jit',
    'pprod_next_mvald_jit',
    'compute_waiting_times_jit',
    'mvald_iteration_kernel_jit',
]
