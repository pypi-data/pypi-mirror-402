"""
JIT-compiled kernels for Mean Value Analysis (MVA) algorithms.

Provides Numba-accelerated versions of the core MVA computational hotspots:
- Population vector manipulation (pprod, hashpop)
- Single-class MVA recursion
- Multi-class MVA population recursion
- Schweitzer/AQL iteration loop

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

    # Graceful fallback: create dummy decorators
    def njit(*args, **kwargs):
        """Decorator that does nothing if Numba is not available."""
        def decorator(func):
            return func
        # Handle both @njit and @njit() syntax
        if args and callable(args[0]):
            return args[0]
        return decorator

    def prange(*args, **kwargs):
        """Fallback for prange: just return regular range."""
        return range(*args)


if HAS_NUMBA:
    # =========================================================================
    # JIT-compiled versions
    # =========================================================================

    @njit(fastmath=True, cache=True)
    def pprod_next_jit(n: np.ndarray, N: np.ndarray) -> np.ndarray:
        """
        JIT-compiled population vector increment in lexicographic order.

        Args:
            n: Current population vector (R,)
            N: Maximum population vector (R,)

        Returns:
            Next population vector, or all -1 when exhausted
        """
        R = len(n)
        n_next = n.copy()

        # Find rightmost position that can be incremented
        for i in range(R - 1, -1, -1):
            if n_next[i] < N[i]:
                n_next[i] += 1
                # Reset all positions to the right to 0
                for j in range(i + 1, R):
                    n_next[j] = 0
                return n_next

        # All exhausted - return sentinel
        for i in range(R):
            n_next[i] = -1
        return n_next

    @njit(fastmath=True, cache=True)
    def hashpop_jit(n: np.ndarray, N: np.ndarray) -> int:
        """
        JIT-compiled population vector hash for indexing.

        Computes linear index in flattened population lattice.

        Args:
            n: Population vector (R,)
            N: Maximum population vector (R,)

        Returns:
            Linear index in [0, prod(N+1))
        """
        R = len(n)
        idx = 0
        mult = 1
        for i in range(R - 1, -1, -1):
            idx += int(n[i]) * mult
            mult *= int(N[i]) + 1
        return idx

    @njit(fastmath=True, cache=True)
    def mva_single_class_jit(
        N: int,
        L: np.ndarray,
        Z: float,
        mi: np.ndarray
    ) -> Tuple[float, np.ndarray, np.ndarray, np.ndarray, float]:
        """
        JIT-compiled single-class MVA recursion.

        Args:
            N: Number of customers
            L: Service demands (M,)
            Z: Think time
            mi: Server multiplicity (M,)

        Returns:
            Tuple of (X, Q, R, U, lG):
                X: Throughput
                Q: Queue lengths (M,)
                R: Residence times (M,)
                U: Utilizations (M,)
                lG: Log normalizing constant
        """
        M = len(L)

        if N <= 0:
            return 0.0, np.zeros(M), L.copy(), np.zeros(M), 0.0

        Q = np.zeros(M)
        R = np.zeros(M)
        lG = 0.0
        X = 0.0

        for n in range(1, N + 1):
            # Residence times: R_i = L_i * (m_i + Q_i(n-1))
            total_R = 0.0
            for i in range(M):
                R[i] = L[i] * (mi[i] + Q[i])
                total_R += R[i]

            # Throughput: X = n / (Z + sum(R))
            denom = Z + total_R
            if denom > 0:
                X = n / denom
            else:
                X = 0.0

            # Update queue lengths: Q_i = X * R_i
            for i in range(M):
                Q[i] = X * R[i]

            # Update log normalizing constant
            if X > 0:
                lG -= np.log(X)

        # Utilizations: U_i = X * L_i
        U = np.zeros(M)
        for i in range(M):
            U[i] = X * L[i]

        return X, Q, R, U, lG

    @njit(fastmath=True, cache=True)
    def mva_population_recursion_jit(
        L: np.ndarray,
        N: np.ndarray,
        Z: np.ndarray,
        mi: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        """
        JIT-compiled multi-class MVA population recursion.

        Core computational kernel for exact MVA. Iterates through all
        population vectors in lexicographic order.

        Args:
            L: Service demand matrix (M x R)
            N: Population vector (R,) as int
            Z: Think times (R,)
            mi: Server multiplicity (M,)

        Returns:
            Tuple of (XN, QN, CN, lGN):
                XN: Throughputs (R,)
                QN: Queue lengths (M x R)
                CN: Residence times (M x R)
                lGN: Log normalizing constant
        """
        M = L.shape[0]
        R = L.shape[1]

        # Compute products for indexing
        prods = np.zeros(R - 1)
        for w in range(R - 1):
            prod = 1
            for i in range(w + 1, R):
                prod *= int(N[i]) + 1
            prods[w] = prod

        # Find first non-empty class (from end)
        first_non_empty = R - 1
        while first_non_empty >= 0 and N[first_non_empty] == 0:
            first_non_empty -= 1

        if first_non_empty < 0:
            return np.zeros(R), np.zeros((M, R)), np.zeros((M, R)), 0.0

        # Total population combinations
        totpop = 1
        for r in range(R):
            totpop *= int(N[r]) + 1

        # Q[pop_idx, station] stores cumulative queue length
        Q_table = np.zeros((totpop, M))

        # Output arrays
        XN = np.zeros(R)
        QN = np.zeros((M, R))
        CN = np.zeros((M, R))
        lGN = 0.0

        # Initialize population vector
        n = np.zeros(R, dtype=np.int64)
        n[first_non_empty] = 1

        currentpop = 1
        ctr = totpop

        while ctr > 0:
            for s in range(R):
                if n[s] > 0:
                    # Compute index for n - e_s
                    n[s] -= 1
                    pos_n_1s = int(n[R - 1])
                    for w in range(R - 1):
                        pos_n_1s += int(n[w] * prods[w])
                    n[s] += 1
                else:
                    pos_n_1s = 0

                # Compute residence times
                CNtot = 0.0
                for i in range(M):
                    CN[i, s] = L[i, s] * (mi[i] + Q_table[pos_n_1s, i])
                    CNtot += CN[i, s]

                # Compute throughput
                denom = Z[s] + CNtot
                if denom > 0:
                    XN[s] = n[s] / denom
                else:
                    XN[s] = 0.0

                # Compute queue lengths and accumulate
                for i in range(M):
                    QN[i, s] = XN[s] * CN[i, s]
                    Q_table[currentpop, i] += QN[i, s]

            # Update log normalizing constant
            # Find last non-zero class
            last_nnz = -1
            for r in range(R):
                if n[r] > 0:
                    last_nnz = r

            if last_nnz >= 0:
                sumn = 0
                sumN = 0
                for i in range(last_nnz):
                    sumn += n[i]
                    sumN += N[i]
                sumnprime = 0
                for i in range(last_nnz + 1, R):
                    sumnprime += n[i]

                if sumn == sumN and sumnprime == 0 and XN[last_nnz] > 0:
                    lGN -= np.log(XN[last_nnz])

            # Find next population vector
            s = R - 1
            while s >= 0 and (n[s] == N[s] or s > first_non_empty):
                s -= 1

            if s < 0:
                break

            n[s] += 1
            for i in range(s + 1, R):
                n[i] = 0

            ctr -= 1
            currentpop += 1

        return XN, QN, CN, lGN

    @njit(fastmath=True, cache=True)
    def schweitzer_iteration_jit(
        L: np.ndarray,
        N: np.ndarray,
        Z: np.ndarray,
        QN_init: np.ndarray,
        max_iter: int,
        tol: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
        """
        JIT-compiled Schweitzer/AQL iteration loop.

        Args:
            L: Service demand matrix (M x R)
            N: Population vector (R,)
            Z: Think times (R,)
            QN_init: Initial queue lengths (M x R)
            max_iter: Maximum iterations
            tol: Convergence tolerance

        Returns:
            Tuple of (XN, QN, UN, RN, iterations):
                XN: Throughputs (R,)
                QN: Queue lengths (M x R)
                UN: Utilizations (M x R)
                RN: Residence times (M x R)
                iterations: Number of iterations performed
        """
        M = L.shape[0]
        R = L.shape[1]

        QN = QN_init.copy()
        Q_old = np.zeros((M, R))
        XN = np.zeros(R)
        UN = np.zeros((M, R))
        RN = np.zeros((M, R))

        for iteration in range(max_iter):
            # Copy old values
            for m in range(M):
                for r in range(R):
                    Q_old[m, r] = QN[m, r]

            for r in range(R):
                if N[r] <= 0:
                    continue

                for m in range(M):
                    # Schweitzer: E[Q_i | arrival of class r] ≈ (N_r - 1) / N_r * Q_i
                    if N[r] > 1:
                        Q_others = (N[r] - 1) / N[r] * Q_old[m, r]
                    else:
                        Q_others = 0.0

                    # Add other class contributions
                    for s in range(R):
                        if s != r:
                            Q_others += Q_old[m, s]

                    # Update residence time
                    RN[m, r] = L[m, r] * (1.0 + Q_others)

                # Throughput
                R_total = 0.0
                for m in range(M):
                    R_total += RN[m, r]

                denom = Z[r] + R_total
                if denom > 0:
                    XN[r] = N[r] / denom
                else:
                    XN[r] = 0.0

                # Queue lengths and utilizations
                for m in range(M):
                    QN[m, r] = XN[r] * RN[m, r]
                    UN[m, r] = XN[r] * L[m, r]

            # Check convergence
            max_diff = 0.0
            for m in range(M):
                for r in range(R):
                    diff = abs(QN[m, r] - Q_old[m, r])
                    if diff > max_diff:
                        max_diff = diff

            if max_diff < tol:
                return XN, QN, UN, RN, iteration + 1

        return XN, QN, UN, RN, max_iter

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def pprod_next_jit(n: np.ndarray, N: np.ndarray) -> np.ndarray:
        """Pure Python population vector increment."""
        R = len(n)
        n_next = n.copy()

        for i in range(R - 1, -1, -1):
            if n_next[i] < N[i]:
                n_next[i] += 1
                for j in range(i + 1, R):
                    n_next[j] = 0
                return n_next

        return -np.ones(R)

    def hashpop_jit(n: np.ndarray, N: np.ndarray) -> int:
        """Pure Python population hashing."""
        R = len(n)
        idx = 0
        mult = 1
        for i in range(R - 1, -1, -1):
            idx += int(n[i]) * mult
            mult *= int(N[i]) + 1
        return idx

    def mva_single_class_jit(
        N: int,
        L: np.ndarray,
        Z: float,
        mi: np.ndarray
    ) -> Tuple[float, np.ndarray, np.ndarray, np.ndarray, float]:
        """Pure Python single-class MVA."""
        M = len(L)

        if N <= 0:
            return 0.0, np.zeros(M), L.copy(), np.zeros(M), 0.0

        Q = np.zeros(M)
        lG = 0.0

        for n in range(1, N + 1):
            R = L * (mi + Q)
            total_R = R.sum()
            X = n / (Z + total_R) if (Z + total_R) > 0 else 0.0
            Q = X * R
            if X > 0:
                lG -= np.log(X)

        U = X * L
        return X, Q, R, U, lG

    def mva_population_recursion_jit(
        L: np.ndarray,
        N: np.ndarray,
        Z: np.ndarray,
        mi: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        """Pure Python multi-class MVA population recursion."""
        M, R = L.shape

        prods = np.zeros(R - 1)
        for w in range(R - 1):
            prods[w] = np.prod(np.ones(R - w - 1) + N[w + 1:])

        first_non_empty = R - 1
        while first_non_empty >= 0 and N[first_non_empty] == 0:
            first_non_empty -= 1

        if first_non_empty < 0:
            return np.zeros(R), np.zeros((M, R)), np.zeros((M, R)), 0.0

        totpop = int(np.prod(N + 1))
        Q_table = np.zeros((totpop, M))

        XN = np.zeros(R)
        QN = np.zeros((M, R))
        CN = np.zeros((M, R))
        lGN = 0.0

        n = np.zeros(R, dtype=int)
        n[first_non_empty] = 1

        currentpop = 1
        ctr = totpop

        while ctr > 0:
            for s in range(R):
                if n[s] > 0:
                    n[s] -= 1
                    pos_n_1s = int(n[R - 1])
                    for w in range(R - 1):
                        pos_n_1s += int(n[w] * prods[w])
                    n[s] += 1
                else:
                    pos_n_1s = 0

                CNtot = 0.0
                for i in range(M):
                    CN[i, s] = L[i, s] * (mi[i] + Q_table[pos_n_1s, i])
                    CNtot += CN[i, s]

                XN[s] = n[s] / (Z[s] + CNtot) if (Z[s] + CNtot) > 0 else 0.0

                for i in range(M):
                    QN[i, s] = XN[s] * CN[i, s]
                    Q_table[currentpop, i] += QN[i, s]

            nonzero_idx = np.where(n > 0)[0]
            if len(nonzero_idx) > 0:
                last_nnz = nonzero_idx[-1]
                sumn = np.sum(n[:last_nnz])
                sumN = np.sum(N[:last_nnz])
                sumnprime = np.sum(n[last_nnz + 1:])
                if sumn == sumN and sumnprime == 0 and XN[last_nnz] > 0:
                    lGN -= np.log(XN[last_nnz])

            s = R - 1
            while s >= 0 and (n[s] == N[s] or s > first_non_empty):
                s -= 1

            if s < 0:
                break

            n[s] += 1
            for i in range(s + 1, R):
                n[i] = 0

            ctr -= 1
            currentpop += 1

        return XN, QN, CN, lGN

    def schweitzer_iteration_jit(
        L: np.ndarray,
        N: np.ndarray,
        Z: np.ndarray,
        QN_init: np.ndarray,
        max_iter: int,
        tol: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
        """Pure Python Schweitzer iteration."""
        M, R = L.shape

        QN = QN_init.copy()
        XN = np.zeros(R)
        UN = np.zeros((M, R))
        RN = np.zeros((M, R))

        for iteration in range(max_iter):
            Q_old = QN.copy()

            for r in range(R):
                if N[r] <= 0:
                    continue

                for m in range(M):
                    Q_others = (N[r] - 1) / N[r] * Q_old[m, r] if N[r] > 1 else 0.0
                    for s in range(R):
                        if s != r:
                            Q_others += Q_old[m, s]
                    RN[m, r] = L[m, r] * (1.0 + Q_others)

                R_total = RN[:, r].sum()
                XN[r] = N[r] / (Z[r] + R_total) if (Z[r] + R_total) > 0 else 0.0

                for m in range(M):
                    QN[m, r] = XN[r] * RN[m, r]
                    UN[m, r] = XN[r] * L[m, r]

            if np.abs(QN - Q_old).max() < tol:
                return XN, QN, UN, RN, iteration + 1

        return XN, QN, UN, RN, max_iter


__all__ = [
    'HAS_NUMBA',
    'pprod_next_jit',
    'hashpop_jit',
    'mva_single_class_jit',
    'mva_population_recursion_jit',
    'schweitzer_iteration_jit',
]
