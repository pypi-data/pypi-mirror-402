"""
JIT-compiled kernels for State Space Generation.

Provides Numba-accelerated versions of state enumeration computational hotspots:
- Phase distribution generation (stars and bars)
- Integer partition enumeration
- Cartesian product computation
- Population enumeration (pprod)

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
    def phase_distribution_count_jit(n_jobs: int, n_phases: int) -> int:
        """
        JIT-compiled count of phase distributions.

        Returns the number of ways to distribute n_jobs across n_phases.
        This equals C(n_jobs + n_phases - 1, n_phases - 1).

        Args:
            n_jobs: Number of jobs to distribute
            n_phases: Number of phases

        Returns:
            Number of distinct distributions
        """
        if n_jobs == 0:
            return 1
        if n_phases == 1:
            return 1

        # Compute C(n_jobs + n_phases - 1, n_phases - 1)
        n = n_jobs + n_phases - 1
        k = min(n_phases - 1, n_jobs)

        result = 1
        for i in range(k):
            result = result * (n - i) // (i + 1)

        return result

    @njit(cache=True)
    def generate_phase_distribution_jit(
        n_jobs: int,
        n_phases: int,
        output: np.ndarray
    ) -> int:
        """
        JIT-compiled generation of phase distributions.

        Generates all ways to distribute n_jobs across n_phases (stars and bars).

        Args:
            n_jobs: Number of jobs to distribute
            n_phases: Number of phases
            output: Pre-allocated output array of shape (count, n_phases)

        Returns:
            Number of distributions generated
        """
        if n_jobs == 0:
            for j in range(n_phases):
                output[0, j] = 0
            return 1

        if n_phases == 1:
            output[0, 0] = n_jobs
            return 1

        row = 0
        # Use iterative approach with stack simulation
        state = np.zeros(n_phases, dtype=np.int64)
        state[0] = n_jobs

        while True:
            # Copy current state to output
            for j in range(n_phases):
                output[row, j] = state[j]
            row += 1

            # Find rightmost position that can be decremented
            pos = n_phases - 2
            while pos >= 0 and state[pos] == 0:
                pos -= 1

            if pos < 0:
                break

            # Decrement and move to next position
            state[pos] -= 1
            state[pos + 1] += 1

            # Collapse all remaining to pos+1
            total_right = 0
            for j in range(pos + 2, n_phases):
                total_right += state[j]
                state[j] = 0
            state[pos + 1] += total_right

        return row

    @njit(cache=True)
    def pprod_next_jit(arr: np.ndarray, max_vals: np.ndarray, n: int) -> bool:
        """
        JIT-compiled population product iteration.

        Advances arr to next valid population combination.
        Similar to incrementing a multi-digit counter with varying bases.

        Args:
            arr: Current population vector (modified in place)
            max_vals: Maximum value for each position
            n: Length of arr

        Returns:
            True if next valid combination exists, False if exhausted
        """
        # Find rightmost position that can be incremented
        pos = n - 1
        while pos >= 0:
            if arr[pos] < max_vals[pos]:
                arr[pos] += 1
                # Reset all positions to the right
                for j in range(pos + 1, n):
                    arr[j] = 0
                return True
            pos -= 1

        return False

    @njit(cache=True)
    def pprod_prev_jit(arr: np.ndarray, n: int) -> bool:
        """
        JIT-compiled population product decrement.

        Decrements arr to previous population combination.

        Args:
            arr: Current population vector (modified in place)
            n: Length of arr

        Returns:
            True if previous valid combination exists, False if exhausted
        """
        # Find rightmost position that can be decremented
        pos = n - 1
        while pos >= 0:
            if arr[pos] > 0:
                arr[pos] -= 1
                return True
            pos -= 1

        return False

    @njit(cache=True)
    def cartesian_product_count_jit(sizes: np.ndarray, n_arrays: int) -> int:
        """
        JIT-compiled count of cartesian product size.

        Args:
            sizes: Array of sizes for each component
            n_arrays: Number of arrays

        Returns:
            Total number of combinations
        """
        result = 1
        for i in range(n_arrays):
            result *= sizes[i]
        return result

    @njit(cache=True)
    def cartesian_product_indices_jit(
        sizes: np.ndarray,
        n_arrays: int,
        output: np.ndarray
    ) -> int:
        """
        JIT-compiled generation of cartesian product indices.

        Generates indices into each component array for the cartesian product.

        Args:
            sizes: Array of sizes for each component
            n_arrays: Number of arrays
            output: Pre-allocated output array of shape (total_count, n_arrays)

        Returns:
            Number of combinations generated
        """
        if n_arrays == 0:
            return 0

        total = 1
        for i in range(n_arrays):
            total *= sizes[i]

        if total == 0:
            return 0

        # Generate indices
        idx = np.zeros(n_arrays, dtype=np.int64)
        for row in range(total):
            # Copy current indices to output
            for j in range(n_arrays):
                output[row, j] = idx[j]

            # Increment indices (rightmost first, like a counter)
            pos = n_arrays - 1
            while pos >= 0:
                idx[pos] += 1
                if idx[pos] < sizes[pos]:
                    break
                idx[pos] = 0
                pos -= 1

        return total

    @njit(cache=True)
    def integer_partitions_count_jit(total: int, num_parts: int, max_vals: np.ndarray) -> int:
        """
        JIT-compiled count of integer partitions with constraints.

        Counts ways to partition total into num_parts where part[i] <= max_vals[i].

        Args:
            total: Total to partition
            num_parts: Number of parts
            max_vals: Maximum value for each part

        Returns:
            Number of valid partitions
        """
        if num_parts == 0:
            return 1 if total == 0 else 0

        if total == 0:
            return 1

        if num_parts == 1:
            return 1 if total <= max_vals[0] else 0

        count = 0
        for i in range(min(total, int(max_vals[0])) + 1):
            # Recursively count partitions for remaining
            rest_count = integer_partitions_count_jit(total - i, num_parts - 1, max_vals[1:])
            count += rest_count

        return count

    @njit(cache=True)
    def generate_integer_partitions_jit(
        total: int,
        num_parts: int,
        max_vals: np.ndarray,
        output: np.ndarray
    ) -> int:
        """
        JIT-compiled generation of constrained integer partitions.

        Generates all ways to partition total into num_parts where part[i] <= max_vals[i].

        Args:
            total: Total to partition
            num_parts: Number of parts
            max_vals: Maximum value for each part
            output: Pre-allocated output array of shape (count, num_parts)

        Returns:
            Number of partitions generated
        """
        if num_parts == 0:
            return 0

        if total == 0:
            for j in range(num_parts):
                output[0, j] = 0
            return 1

        if num_parts == 1:
            if total <= max_vals[0]:
                output[0, 0] = total
                return 1
            return 0

        row = 0
        # Use iterative approach
        state = np.zeros(num_parts, dtype=np.int64)

        # Find first valid partition
        remaining = total
        for j in range(num_parts - 1):
            state[j] = min(remaining, int(max_vals[j]))
            remaining -= state[j]

        if remaining <= max_vals[num_parts - 1]:
            state[num_parts - 1] = remaining
        else:
            # No valid initial state, need to backtrack
            pass

        # Generate all partitions
        while True:
            # Check if current state is valid
            current_sum = 0
            for j in range(num_parts):
                current_sum += state[j]

            if current_sum == total:
                # Copy to output
                for j in range(num_parts):
                    output[row, j] = state[j]
                row += 1

            # Move to next partition
            # Find rightmost position that can be decremented
            pos = num_parts - 2
            while pos >= 0 and state[pos] == 0:
                pos -= 1

            if pos < 0:
                break

            # Decrement this position
            state[pos] -= 1

            # Redistribute remainder to the right
            remaining = total
            for j in range(pos + 1):
                remaining -= state[j]

            # Fill remaining positions
            for j in range(pos + 1, num_parts - 1):
                state[j] = min(remaining, int(max_vals[j]))
                remaining -= state[j]

            if remaining <= max_vals[num_parts - 1]:
                state[num_parts - 1] = remaining
            else:
                # Invalid, continue
                state[num_parts - 1] = 0
                continue

        return row

    @njit(fastmath=True, cache=True)
    def state_hash_jit(state: np.ndarray, n: int, multipliers: np.ndarray) -> int:
        """
        JIT-compiled state hashing for efficient lookup.

        Computes a hash value for a state vector using polynomial hashing.

        Args:
            state: State vector
            n: Length of state vector
            multipliers: Pre-computed multipliers for each position

        Returns:
            Hash value
        """
        h = 0
        for i in range(n):
            h += int(state[i]) * multipliers[i]
        return h

    @njit(cache=True)
    def state_search_jit(
        state_space: np.ndarray,
        target: np.ndarray,
        n_states: int,
        n_cols: int
    ) -> int:
        """
        JIT-compiled linear search for state in state space.

        Args:
            state_space: State space matrix (n_states x n_cols)
            target: Target state to find
            n_states: Number of states
            n_cols: Number of columns

        Returns:
            Index if found (0-based), -1 if not found
        """
        for i in range(n_states):
            match = True
            for j in range(n_cols):
                if state_space[i, j] != target[j]:
                    match = False
                    break
            if match:
                return i
        return -1

    @njit(fastmath=True, cache=True)
    def enumerate_populations_jit(
        N: np.ndarray,
        n_classes: int,
        output: np.ndarray
    ) -> int:
        """
        JIT-compiled enumeration of all population vectors.

        Generates all non-negative integer vectors n where n[r] <= N[r].

        Args:
            N: Maximum population per class
            n_classes: Number of classes
            output: Pre-allocated output array

        Returns:
            Number of population vectors generated
        """
        if n_classes == 0:
            return 0

        # Count total combinations
        total = 1
        for r in range(n_classes):
            total *= int(N[r]) + 1

        # Generate all combinations
        n = np.zeros(n_classes, dtype=np.int64)
        for row in range(total):
            # Copy current population to output
            for r in range(n_classes):
                output[row, r] = n[r]

            # Increment (rightmost first)
            pos = n_classes - 1
            while pos >= 0:
                n[pos] += 1
                if n[pos] <= N[pos]:
                    break
                n[pos] = 0
                pos -= 1

        return total

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def phase_distribution_count_jit(n_jobs: int, n_phases: int) -> int:
        """Pure Python count of phase distributions."""
        from scipy.special import comb
        if n_jobs == 0 or n_phases == 1:
            return 1
        return int(comb(n_jobs + n_phases - 1, n_phases - 1, exact=True))

    def generate_phase_distribution_jit(
        n_jobs: int,
        n_phases: int,
        output: np.ndarray
    ) -> int:
        """Pure Python generation of phase distributions."""
        if n_jobs == 0:
            output[0, :] = 0
            return 1

        if n_phases == 1:
            output[0, 0] = n_jobs
            return 1

        row = 0
        state = np.zeros(n_phases, dtype=int)
        state[0] = n_jobs

        while True:
            output[row, :] = state
            row += 1

            pos = n_phases - 2
            while pos >= 0 and state[pos] == 0:
                pos -= 1

            if pos < 0:
                break

            state[pos] -= 1
            state[pos + 1] += 1

            total_right = np.sum(state[pos + 2:])
            state[pos + 2:] = 0
            state[pos + 1] += total_right

        return row

    def pprod_next_jit(arr: np.ndarray, max_vals: np.ndarray, n: int) -> bool:
        """Pure Python population product iteration."""
        pos = n - 1
        while pos >= 0:
            if arr[pos] < max_vals[pos]:
                arr[pos] += 1
                arr[pos + 1:] = 0
                return True
            pos -= 1
        return False

    def pprod_prev_jit(arr: np.ndarray, n: int) -> bool:
        """Pure Python population product decrement."""
        pos = n - 1
        while pos >= 0:
            if arr[pos] > 0:
                arr[pos] -= 1
                return True
            pos -= 1
        return False

    def cartesian_product_count_jit(sizes: np.ndarray, n_arrays: int) -> int:
        """Pure Python count of cartesian product size."""
        return int(np.prod(sizes[:n_arrays]))

    def cartesian_product_indices_jit(
        sizes: np.ndarray,
        n_arrays: int,
        output: np.ndarray
    ) -> int:
        """Pure Python generation of cartesian product indices."""
        if n_arrays == 0:
            return 0

        total = int(np.prod(sizes[:n_arrays]))
        if total == 0:
            return 0

        idx = np.zeros(n_arrays, dtype=int)
        for row in range(total):
            output[row, :n_arrays] = idx

            pos = n_arrays - 1
            while pos >= 0:
                idx[pos] += 1
                if idx[pos] < sizes[pos]:
                    break
                idx[pos] = 0
                pos -= 1

        return total

    def integer_partitions_count_jit(total: int, num_parts: int, max_vals: np.ndarray) -> int:
        """Pure Python count of integer partitions."""
        if num_parts == 0:
            return 1 if total == 0 else 0
        if total == 0:
            return 1
        if num_parts == 1:
            return 1 if total <= max_vals[0] else 0

        count = 0
        for i in range(min(total, int(max_vals[0])) + 1):
            count += integer_partitions_count_jit(total - i, num_parts - 1, max_vals[1:])
        return count

    def generate_integer_partitions_jit(
        total: int,
        num_parts: int,
        max_vals: np.ndarray,
        output: np.ndarray
    ) -> int:
        """Pure Python generation of integer partitions."""
        if num_parts == 0:
            return 0

        if total == 0:
            output[0, :num_parts] = 0
            return 1

        if num_parts == 1:
            if total <= max_vals[0]:
                output[0, 0] = total
                return 1
            return 0

        # Use recursive generation
        row = [0]  # Use list for mutable closure

        def _generate(pos, remaining, state):
            if pos == num_parts - 1:
                if remaining <= max_vals[pos]:
                    state[pos] = remaining
                    output[row[0], :num_parts] = state
                    row[0] += 1
                return

            for v in range(min(remaining, int(max_vals[pos])) + 1):
                state[pos] = v
                _generate(pos + 1, remaining - v, state)

        _generate(0, total, np.zeros(num_parts, dtype=int))
        return row[0]

    def state_hash_jit(state: np.ndarray, n: int, multipliers: np.ndarray) -> int:
        """Pure Python state hashing."""
        return int(np.sum(state[:n] * multipliers[:n]))

    def state_search_jit(
        state_space: np.ndarray,
        target: np.ndarray,
        n_states: int,
        n_cols: int
    ) -> int:
        """Pure Python state search."""
        for i in range(n_states):
            if np.array_equal(state_space[i, :n_cols], target[:n_cols]):
                return i
        return -1

    def enumerate_populations_jit(
        N: np.ndarray,
        n_classes: int,
        output: np.ndarray
    ) -> int:
        """Pure Python enumeration of populations."""
        if n_classes == 0:
            return 0

        total = int(np.prod(N[:n_classes] + 1))
        n = np.zeros(n_classes, dtype=int)

        for row in range(total):
            output[row, :n_classes] = n

            pos = n_classes - 1
            while pos >= 0:
                n[pos] += 1
                if n[pos] <= N[pos]:
                    break
                n[pos] = 0
                pos -= 1

        return total


__all__ = [
    'HAS_NUMBA',
    'phase_distribution_count_jit',
    'generate_phase_distribution_jit',
    'pprod_next_jit',
    'pprod_prev_jit',
    'cartesian_product_count_jit',
    'cartesian_product_indices_jit',
    'integer_partitions_count_jit',
    'generate_integer_partitions_jit',
    'state_hash_jit',
    'state_search_jit',
    'enumerate_populations_jit',
]
