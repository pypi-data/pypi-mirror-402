"""
JIT-compiled kernels for SSA (Stochastic Simulation Algorithm).

Provides Numba-accelerated versions of core SSA computational hotspots:
- Rate computation for transitions
- Weighted random selection
- Statistics accumulation

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
    def compute_service_rates_jit(
        state: np.ndarray,
        rates: np.ndarray,
        nservers: np.ndarray,
        M: int,
        K: int
    ) -> np.ndarray:
        """
        JIT-compiled service rate computation.

        Computes effective service rate at each station for each class,
        accounting for multiserver stations.

        Args:
            state: Current state (M x K)
            rates: Base service rates (M x K)
            nservers: Number of servers per station (M,)
            M: Number of stations
            K: Number of classes

        Returns:
            Effective service rates (M x K)
        """
        effective_rates = np.zeros((M, K))

        for ist in range(M):
            total_at_station = 0.0
            for k in range(K):
                total_at_station += state[ist, k]

            if total_at_station <= 0:
                continue

            ns = nservers[ist]
            if np.isinf(ns):
                # Infinite server: rate proportional to jobs
                for k in range(K):
                    if state[ist, k] > 0:
                        effective_rates[ist, k] = rates[ist, k] * state[ist, k]
            else:
                # Finite server(s)
                active_servers = min(total_at_station, ns)
                for k in range(K):
                    if state[ist, k] > 0:
                        # Fair share of service capacity
                        effective_rates[ist, k] = rates[ist, k] * active_servers * (state[ist, k] / total_at_station)

        return effective_rates

    @njit(cache=True)
    def weighted_random_selection_jit(
        weights: np.ndarray,
        random_uniform: float
    ) -> int:
        """
        JIT-compiled weighted random selection.

        Selects an index proportional to weights using a uniform random value.

        Args:
            weights: Array of weights (must be positive)
            random_uniform: Uniform random number in [0, 1)

        Returns:
            Selected index
        """
        n = len(weights)
        total = 0.0
        for i in range(n):
            total += weights[i]

        if total <= 0:
            return 0

        target = random_uniform * total
        cumsum = 0.0

        for i in range(n):
            cumsum += weights[i]
            if cumsum >= target:
                return i

        return n - 1

    @njit(fastmath=True, cache=True)
    def accumulate_statistics_jit(
        state: np.ndarray,
        busy: np.ndarray,
        sojourn_time: float,
        Q_accum: np.ndarray,
        U_accum: np.ndarray,
        total_time: float
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        JIT-compiled statistics accumulation.

        Updates cumulative statistics with current state contribution.

        Args:
            state: Current state (M x K)
            busy: Server busy state (M x K)
            sojourn_time: Time spent in current state
            Q_accum: Accumulated queue lengths
            U_accum: Accumulated utilizations
            total_time: Total accumulated time

        Returns:
            Tuple of (Q_accum, U_accum, new_total_time)
        """
        M = state.shape[0]
        K = state.shape[1]

        for ist in range(M):
            for k in range(K):
                Q_accum[ist, k] += state[ist, k] * sojourn_time
                U_accum[ist, k] += busy[ist, k] * sojourn_time

        return Q_accum, U_accum, total_time + sojourn_time

    @njit(fastmath=True, cache=True)
    def compute_busy_state_jit(
        state: np.ndarray,
        nservers: np.ndarray,
        M: int,
        K: int
    ) -> np.ndarray:
        """
        JIT-compiled busy state computation.

        Computes server busy fraction for each class.

        Args:
            state: Current state (M x K)
            nservers: Number of servers per station (M,)
            M: Number of stations
            K: Number of classes

        Returns:
            Busy state matrix (M x K)
        """
        busy = np.zeros((M, K))

        for ist in range(M):
            total_at_station = 0.0
            for k in range(K):
                total_at_station += state[ist, k]

            if total_at_station <= 0:
                continue

            ns = nservers[ist]
            if np.isinf(ns):
                # Infinite server: utilization = n * service_time
                for k in range(K):
                    if state[ist, k] > 0:
                        busy[ist, k] = state[ist, k]
            else:
                # Finite server: fraction of capacity used
                util_factor = min(1.0, total_at_station / ns)
                for k in range(K):
                    if state[ist, k] > 0:
                        busy[ist, k] = util_factor * (state[ist, k] / total_at_station)

        return busy

    @njit(fastmath=True, cache=True)
    def finalize_statistics_jit(
        Q_accum: np.ndarray,
        U_accum: np.ndarray,
        T_accum: np.ndarray,
        total_time: float,
        M: int,
        K: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        JIT-compiled statistics finalization.

        Computes final averages from accumulated statistics.

        Args:
            Q_accum: Accumulated queue lengths
            U_accum: Accumulated utilizations
            T_accum: Accumulated completions (M x K)
            total_time: Total simulation time
            M: Number of stations
            K: Number of classes

        Returns:
            Tuple of (Q, U, T) - average queue lengths, utilizations, throughputs
        """
        Q = np.zeros((M, K))
        U = np.zeros((M, K))
        T = np.zeros((M, K))

        if total_time > 0:
            for ist in range(M):
                for k in range(K):
                    Q[ist, k] = Q_accum[ist, k] / total_time
                    U[ist, k] = U_accum[ist, k] / total_time
                    T[ist, k] = T_accum[ist, k] / total_time

        return Q, U, T

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def compute_service_rates_jit(
        state: np.ndarray,
        rates: np.ndarray,
        nservers: np.ndarray,
        M: int,
        K: int
    ) -> np.ndarray:
        """Pure Python service rate computation."""
        effective_rates = np.zeros((M, K))

        for ist in range(M):
            total_at_station = np.sum(state[ist, :])
            if total_at_station <= 0:
                continue

            ns = nservers[ist]
            if np.isinf(ns):
                effective_rates[ist, :] = rates[ist, :] * state[ist, :]
            else:
                active_servers = min(total_at_station, ns)
                for k in range(K):
                    if state[ist, k] > 0:
                        effective_rates[ist, k] = rates[ist, k] * active_servers * (state[ist, k] / total_at_station)

        return effective_rates

    def weighted_random_selection_jit(
        weights: np.ndarray,
        random_uniform: float
    ) -> int:
        """Pure Python weighted selection."""
        total = np.sum(weights)
        if total <= 0:
            return 0

        target = random_uniform * total
        cumsum = 0.0

        for i, w in enumerate(weights):
            cumsum += w
            if cumsum >= target:
                return i

        return len(weights) - 1

    def accumulate_statistics_jit(
        state: np.ndarray,
        busy: np.ndarray,
        sojourn_time: float,
        Q_accum: np.ndarray,
        U_accum: np.ndarray,
        total_time: float
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """Pure Python statistics accumulation."""
        Q_accum += state * sojourn_time
        U_accum += busy * sojourn_time
        return Q_accum, U_accum, total_time + sojourn_time

    def compute_busy_state_jit(
        state: np.ndarray,
        nservers: np.ndarray,
        M: int,
        K: int
    ) -> np.ndarray:
        """Pure Python busy state computation."""
        busy = np.zeros((M, K))

        for ist in range(M):
            total_at_station = np.sum(state[ist, :])
            if total_at_station <= 0:
                continue

            ns = nservers[ist]
            if np.isinf(ns):
                busy[ist, :] = state[ist, :]
            else:
                util_factor = min(1.0, total_at_station / ns)
                for k in range(K):
                    if state[ist, k] > 0:
                        busy[ist, k] = util_factor * (state[ist, k] / total_at_station)

        return busy

    def finalize_statistics_jit(
        Q_accum: np.ndarray,
        U_accum: np.ndarray,
        T_accum: np.ndarray,
        total_time: float,
        M: int,
        K: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Pure Python statistics finalization."""
        if total_time > 0:
            Q = Q_accum / total_time
            U = U_accum / total_time
            T = T_accum / total_time
        else:
            Q = np.zeros((M, K))
            U = np.zeros((M, K))
            T = np.zeros((M, K))

        return Q, U, T


__all__ = [
    'HAS_NUMBA',
    'compute_service_rates_jit',
    'weighted_random_selection_jit',
    'accumulate_statistics_jit',
    'compute_busy_state_jit',
    'finalize_statistics_jit',
]
