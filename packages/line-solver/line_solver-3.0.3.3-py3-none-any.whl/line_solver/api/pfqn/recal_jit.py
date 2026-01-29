"""
JIT-compiled kernels for RECAL Algorithm.

Provides Numba-accelerated versions of RECAL computational hotspots:
- Main recursion loop
- Row matching for lookup
- Contribution computation

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
    def matchrow_jit(matrix: np.ndarray, row: np.ndarray, n_rows: int, n_cols: int) -> int:
        """
        JIT-compiled row matching.

        Finds the 1-based index of row in matrix, or 0 if not found.

        Args:
            matrix: 2D matrix to search
            row: Row vector to find
            n_rows: Number of rows in matrix
            n_cols: Number of columns to compare

        Returns:
            1-based index if found, 0 otherwise
        """
        for i in range(n_rows):
            match = True
            for j in range(n_cols):
                if matrix[i, j] != row[j]:
                    match = False
                    break
            if match:
                return i + 1  # 1-based index
        return 0

    @njit(fastmath=True, cache=True)
    def recal_inner_loop_jit(
        I: np.ndarray,
        I_1: np.ndarray,
        G: np.ndarray,
        G_1: np.ndarray,
        L: np.ndarray,
        Z_r: float,
        m0: np.ndarray,
        M: int,
        nr: int,
        n_I: int,
        n_I_1: int
    ) -> np.ndarray:
        """
        JIT-compiled inner loop for RECAL recursion.

        Args:
            I: Current state index matrix (n_I x M+1)
            I_1: Previous state index matrix (n_I_1 x M+1)
            G: Current G values (n_I,)
            G_1: Previous G values (n_I_1,)
            L: Service demand row for class r (M,)
            Z_r: Think time for class r
            m0: Multiplicity vector (M,)
            M: Number of stations
            nr: Current job count
            n_I: Number of rows in I
            n_I_1: Number of rows in I_1

        Returns:
            Updated G values
        """
        for i in range(n_I):
            m = np.zeros(M + 1, dtype=np.int64)
            for j in range(M + 1):
                m[j] = I[i, j]
            mZ = m[:M].copy()

            # Find matching row for think time contribution
            idx = matchrow_jit(I_1, mZ, n_I_1, M)
            if idx > 0:
                G[i] = Z_r * G_1[idx - 1] / nr
            else:
                G[i] = 0.0

            # Station contributions
            for jst in range(M):
                m[jst] += 1
                idx_station = matchrow_jit(I_1, m, n_I_1, M + 1)
                if idx_station > 0:
                    G[i] += (m[jst] + m0[jst] - 1) * L[jst] * G_1[idx_station - 1] / nr
                m[jst] -= 1

        return G

    @njit(cache=True)
    def multichoose_count_jit(n: int, k: int) -> int:
        """
        JIT-compiled count of multichoose(n, k) = C(n+k-1, k).

        Args:
            n: Number of categories
            k: Number of items to choose

        Returns:
            Number of combinations with repetition
        """
        if k == 0:
            return 1
        if n == 0:
            return 0

        # Compute C(n+k-1, min(k, n-1))
        numerator = n + k - 1
        r = min(k, n - 1)

        result = 1
        for i in range(r):
            result = result * (numerator - i) // (i + 1)

        return result

    @njit(cache=True)
    def generate_multichoose_jit(n: int, k: int, output: np.ndarray) -> int:
        """
        JIT-compiled generation of multichoose combinations.

        Generates all ways to place k items into n bins.

        Args:
            n: Number of bins
            k: Number of items
            output: Pre-allocated output array of shape (count, n)

        Returns:
            Number of combinations generated
        """
        if k == 0:
            for j in range(n):
                output[0, j] = 0
            return 1

        if n == 1:
            output[0, 0] = k
            return 1

        row = 0
        # Use recursive enumeration via iteration
        state = np.zeros(n, dtype=np.int64)
        state[0] = k

        while True:
            # Copy current state to output
            for j in range(n):
                output[row, j] = state[j]
            row += 1

            # Find rightmost position that can be decremented
            pos = n - 2
            while pos >= 0 and state[pos] == 0:
                pos -= 1

            if pos < 0:
                break

            # Decrement and move to next position
            state[pos] -= 1
            state[pos + 1] += 1

            # Collapse all remaining to pos+1
            total_right = 0
            for j in range(pos + 2, n):
                total_right += state[j]
                state[j] = 0
            state[pos + 1] += total_right

        return row

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def matchrow_jit(matrix: np.ndarray, row: np.ndarray, n_rows: int, n_cols: int) -> int:
        """Pure Python row matching."""
        for i in range(n_rows):
            if np.array_equal(matrix[i, :n_cols], row[:n_cols]):
                return i + 1
        return 0

    def recal_inner_loop_jit(
        I: np.ndarray,
        I_1: np.ndarray,
        G: np.ndarray,
        G_1: np.ndarray,
        L: np.ndarray,
        Z_r: float,
        m0: np.ndarray,
        M: int,
        nr: int,
        n_I: int,
        n_I_1: int
    ) -> np.ndarray:
        """Pure Python RECAL inner loop."""
        for i in range(n_I):
            m = I[i, :].copy()
            mZ = m[:M]

            idx = matchrow_jit(I_1, mZ, n_I_1, M)
            if idx > 0:
                G[i] = Z_r * G_1[idx - 1] / nr
            else:
                G[i] = 0.0

            for jst in range(M):
                m[jst] += 1
                idx_station = matchrow_jit(I_1, m, n_I_1, M + 1)
                if idx_station > 0:
                    G[i] += (m[jst] + m0[jst] - 1) * L[jst] * G_1[idx_station - 1] / nr
                m[jst] -= 1

        return G

    def multichoose_count_jit(n: int, k: int) -> int:
        """Pure Python multichoose count."""
        from scipy.special import comb
        return int(comb(n + k - 1, k, exact=True))

    def generate_multichoose_jit(n: int, k: int, output: np.ndarray) -> int:
        """Pure Python multichoose generation."""
        from scipy.special import comb
        count = int(comb(n + k - 1, k, exact=True))

        if k == 0:
            output[0, :] = 0
            return 1

        if n == 1:
            output[0, 0] = k
            return 1

        row = 0
        state = np.zeros(n, dtype=int)
        state[0] = k

        while True:
            output[row, :] = state
            row += 1

            pos = n - 2
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


__all__ = [
    'HAS_NUMBA',
    'matchrow_jit',
    'recal_inner_loop_jit',
    'multichoose_count_jit',
    'generate_multichoose_jit',
]
