"""
JIT-compiled kernels for CTMC analysis algorithms.

Provides Numba-accelerated versions of the core CTMC computational hotspots:
- Time-reversal computation
- Randomization iteration
- Gillespie simulation step

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
    def time_reverse_kernel_jit(Q: np.ndarray, pi: np.ndarray) -> np.ndarray:
        """
        JIT-compiled time-reversal kernel.

        Computes Q*_{ij} = π_j * Q_{ji} / π_i

        Args:
            Q: Original generator matrix (n x n)
            pi: Steady-state distribution (n,)

        Returns:
            Time-reversed generator matrix (n x n)
        """
        n = Q.shape[0]
        Q_rev = np.zeros((n, n))

        for i in range(n):
            if pi[i] > 0:
                for j in range(n):
                    Q_rev[i, j] = pi[j] * Q[j, i] / pi[i]

        # Make valid generator: set diagonal to -row sum
        for i in range(n):
            row_sum = 0.0
            for j in range(n):
                if i != j:
                    row_sum += Q_rev[i, j]
            Q_rev[i, i] = -row_sum

        return Q_rev

    @njit(fastmath=True, cache=True)
    def randomization_step_jit(
        pi_k: np.ndarray,
        P: np.ndarray,
        poisson_probs: np.ndarray,
        k_max: int
    ) -> np.ndarray:
        """
        JIT-compiled randomization iteration.

        Computes π(t) = Σ_k P(N(t)=k) * π(0) * P^k

        Args:
            pi_k: Initial distribution π(0)
            P: Uniformized transition matrix
            poisson_probs: Poisson probability array
            k_max: Maximum number of steps

        Returns:
            Transient probability vector
        """
        n = P.shape[0]
        pi_t = np.zeros(n)
        pi_current = pi_k.copy()

        for k in range(k_max + 1):
            # Accumulate: pi_t += poisson_probs[k] * pi_current
            for i in range(n):
                pi_t[i] += poisson_probs[k] * pi_current[i]

            # Update: pi_current = pi_current @ P
            pi_next = np.zeros(n)
            for i in range(n):
                for j in range(n):
                    pi_next[i] += pi_current[j] * P[j, i]
            pi_current = pi_next

        return pi_t

    @njit(cache=True)
    def gillespie_step_jit(
        Q: np.ndarray,
        current_state: int,
        random_uniform1: float,
        random_uniform2: float
    ) -> Tuple[int, float]:
        """
        JIT-compiled single Gillespie step.

        Computes next state and sojourn time for CTMC simulation.

        Args:
            Q: Generator matrix
            current_state: Current state index
            random_uniform1: Uniform random for exponential time
            random_uniform2: Uniform random for next state selection

        Returns:
            Tuple of (next_state, sojourn_time)
        """
        n = Q.shape[0]

        # Exit rate from current state
        exit_rate = -Q[current_state, current_state]

        if exit_rate <= 0:
            # Absorbing state
            return current_state, np.inf

        # Time to next transition (inverse transform of exponential)
        sojourn = -np.log(random_uniform1) / exit_rate

        # Determine next state using cumulative probabilities
        rates = np.zeros(n)
        total_rate = 0.0
        for j in range(n):
            if j != current_state:
                rates[j] = Q[current_state, j]
                total_rate += rates[j]

        if total_rate <= 0:
            return current_state, np.inf

        # Sample next state
        target = random_uniform2 * total_rate
        cumsum = 0.0
        next_state = current_state

        for j in range(n):
            if j != current_state:
                cumsum += rates[j]
                if cumsum >= target:
                    next_state = j
                    break

        return next_state, sojourn

    @njit(cache=True)
    def simulate_ctmc_jit(
        Q: np.ndarray,
        initial_state: int,
        max_time: float,
        max_events: int,
        random_uniforms: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        JIT-compiled CTMC simulation using Gillespie algorithm.

        Args:
            Q: Generator matrix
            initial_state: Starting state
            max_time: Maximum simulation time
            max_events: Maximum number of transitions
            random_uniforms: Pre-generated uniform random numbers (2 * max_events,)

        Returns:
            Tuple of (states, times, sojourn_times)
        """
        n = Q.shape[0]

        # Allocate output arrays
        states = np.zeros(max_events + 1, dtype=np.int64)
        times = np.zeros(max_events + 1)
        sojourn_times = np.zeros(max_events)

        states[0] = initial_state
        times[0] = 0.0

        current_state = initial_state
        current_time = 0.0
        event_count = 0

        for i in range(max_events):
            # Get random numbers for this step
            r1 = random_uniforms[2 * i]
            r2 = random_uniforms[2 * i + 1]

            next_state, sojourn = gillespie_step_jit(Q, current_state, r1, r2)

            if np.isinf(sojourn):
                # Absorbing state
                sojourn_times[i] = max_time - current_time
                event_count = i + 1
                break

            if current_time + sojourn > max_time:
                sojourn_times[i] = max_time - current_time
                event_count = i + 1
                break

            sojourn_times[i] = sojourn
            current_time += sojourn

            states[i + 1] = next_state
            times[i + 1] = current_time
            current_state = next_state
            event_count = i + 2

        # Return only used portions
        return states[:event_count], times[:event_count], sojourn_times[:event_count - 1] if event_count > 1 else sojourn_times[:1]

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def time_reverse_kernel_jit(Q: np.ndarray, pi: np.ndarray) -> np.ndarray:
        """Pure Python time-reversal."""
        n = Q.shape[0]
        Q_rev = np.zeros((n, n))

        for i in range(n):
            if pi[i] > 0:
                for j in range(n):
                    Q_rev[i, j] = pi[j] * Q[j, i] / pi[i]

        # Make valid generator
        row_sums = Q_rev.sum(axis=1) - np.diag(Q_rev)
        np.fill_diagonal(Q_rev, -row_sums)

        return Q_rev

    def randomization_step_jit(
        pi_k: np.ndarray,
        P: np.ndarray,
        poisson_probs: np.ndarray,
        k_max: int
    ) -> np.ndarray:
        """Pure Python randomization."""
        n = P.shape[0]
        pi_t = np.zeros(n)
        pi_current = pi_k.copy()

        for k in range(k_max + 1):
            pi_t += poisson_probs[k] * pi_current
            pi_current = pi_current @ P

        return pi_t

    def gillespie_step_jit(
        Q: np.ndarray,
        current_state: int,
        random_uniform1: float,
        random_uniform2: float
    ) -> Tuple[int, float]:
        """Pure Python Gillespie step."""
        n = Q.shape[0]
        exit_rate = -Q[current_state, current_state]

        if exit_rate <= 0:
            return current_state, float('inf')

        sojourn = -np.log(random_uniform1) / exit_rate

        rates = Q[current_state, :].copy()
        rates[current_state] = 0.0
        total_rate = rates.sum()

        if total_rate <= 0:
            return current_state, float('inf')

        target = random_uniform2 * total_rate
        cumsum = 0.0
        for j in range(n):
            if j != current_state:
                cumsum += rates[j]
                if cumsum >= target:
                    return j, sojourn

        return current_state, sojourn

    def simulate_ctmc_jit(
        Q: np.ndarray,
        initial_state: int,
        max_time: float,
        max_events: int,
        random_uniforms: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Pure Python CTMC simulation."""
        states = [initial_state]
        times = [0.0]
        sojourn_times = []

        current_state = initial_state
        current_time = 0.0

        for i in range(max_events):
            r1 = random_uniforms[2 * i]
            r2 = random_uniforms[2 * i + 1]

            next_state, sojourn = gillespie_step_jit(Q, current_state, r1, r2)

            if np.isinf(sojourn):
                sojourn_times.append(max_time - current_time)
                break

            if current_time + sojourn > max_time:
                sojourn_times.append(max_time - current_time)
                break

            sojourn_times.append(sojourn)
            current_time += sojourn

            states.append(next_state)
            times.append(current_time)
            current_state = next_state

        return (np.array(states), np.array(times),
                np.array(sojourn_times) if sojourn_times else np.array([]))


__all__ = [
    'HAS_NUMBA',
    'time_reverse_kernel_jit',
    'randomization_step_jit',
    'gillespie_step_jit',
    'simulate_ctmc_jit',
]
