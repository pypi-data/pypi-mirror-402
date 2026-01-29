"""
JIT-compiled kernels for AMVA-LD algorithms.

Provides Numba-accelerated versions of the core AMVALD computational hotspots:
- Arrival queue length computation
- Waiting time accumulation
- Metric update loops

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


# Scheduling strategy constants (matching SchedStrategy enum values)
SCHED_INF = 0
SCHED_FCFS = 1
SCHED_SIRO = 2
SCHED_PS = 3
SCHED_HOL = 4
SCHED_LCFSPR = 5
SCHED_EXT = 6


if HAS_NUMBA:
    # =========================================================================
    # JIT-compiled versions
    # =========================================================================

    @njit(fastmath=True, cache=True)
    def compute_arrival_queue_lengths_jit(
        M: int,
        K: int,
        delta: float,
        deltaclass: np.ndarray,
        Qchain_in: np.ndarray,
        nnzclasses: np.ndarray,
        sched_arr: np.ndarray,
        classprio: np.ndarray,
        has_classprio: bool
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        JIT-compiled arrival queue length computation.

        Args:
            M: Number of stations
            K: Number of chains
            delta: Population ratio (Nt-1)/Nt
            deltaclass: Per-class population ratios
            Qchain_in: Queue lengths (M x K)
            nnzclasses: Non-zero class indices
            sched_arr: Scheduling strategy per station (M,) as integers
            classprio: Class priorities (K,)
            has_classprio: Whether class priorities are provided

        Returns:
            Tuple of (interpTotArvlQlen, selfArvlQlenSeenByClosed,
                     totArvlQlenSeenByClosed, stationaryQlen)
        """
        interpTotArvlQlen = np.zeros(M)
        selfArvlQlenSeenByClosed = np.zeros((M, K))
        totArvlQlenSeenByClosed = np.zeros((M, K))
        stationaryQlen = np.zeros((M, K))

        n_nnz = len(nnzclasses)

        for k in range(M):
            # Compute total queue length across non-zero classes
            tot_q = 0.0
            for i in range(n_nnz):
                r = nnzclasses[i]
                tot_q += Qchain_in[k, r]
            interpTotArvlQlen[k] = delta * tot_q

            for i in range(n_nnz):
                r = nnzclasses[i]
                selfArvlQlenSeenByClosed[k, r] = deltaclass[r] * Qchain_in[k, r]
                totArvlQlenSeenByClosed[k, r] = (deltaclass[r] * Qchain_in[k, r] +
                                                  tot_q - Qchain_in[k, r])
                stationaryQlen[k, r] = Qchain_in[k, r]

        return interpTotArvlQlen, selfArvlQlenSeenByClosed, totArvlQlenSeenByClosed, stationaryQlen

    @njit(fastmath=True, cache=True)
    def compute_fcfs_waiting_time_jit(
        STeff_k_r: float,
        ns: float,
        deltaclass: np.ndarray,
        deltaclass_r: float,
        Xchain_in: np.ndarray,
        Vchain_k: np.ndarray,
        STeff_k: np.ndarray,
        selfArvlQlenSeenByClosed_k_r: float,
        stationaryQlen_k: np.ndarray,
        nnzclasses: np.ndarray,
        r: int,
        is_open: bool
    ) -> float:
        """
        JIT-compiled FCFS waiting time computation for one station/class.

        Args:
            STeff_k_r: Effective service time at station k for class r
            ns: Number of servers
            deltaclass: Per-class population ratios
            deltaclass_r: Population ratio for class r
            Xchain_in: Throughputs
            Vchain_k: Visit ratios at station k
            STeff_k: Effective service times at station k
            selfArvlQlenSeenByClosed_k_r: Self-arrival queue length
            stationaryQlen_k: Stationary queue lengths at station k
            nnzclasses: Non-zero class indices
            r: Current class index
            is_open: Whether class r is open

        Returns:
            Waiting time for class r at station k
        """
        if STeff_k_r <= 0:
            return 0.0

        K = len(deltaclass)
        n_nnz = len(nnzclasses)

        # Compute Bk for multiserver correction
        Bk = np.ones(K)
        if ns > 1 and not np.isinf(ns):
            # Compute rho_sum with deltaclass_r for class r
            rho_sum = 0.0
            for i in range(n_nnz):
                c = nnzclasses[i]
                dc = deltaclass_r if c == r else deltaclass[c]
                rho_sum += dc * Xchain_in[c] * Vchain_k[c] * STeff_k[c]

            if rho_sum < 0.75:
                # Light-load
                for i in range(n_nnz):
                    c = nnzclasses[i]
                    dc = deltaclass_r if c == r else deltaclass[c]
                    Bk[c] = dc * Xchain_in[c] * Vchain_k[c] * STeff_k[c]
            else:
                # High-load
                for i in range(n_nnz):
                    c = nnzclasses[i]
                    dc = deltaclass_r if c == r else deltaclass[c]
                    Bk[c] = (dc * Xchain_in[c] * Vchain_k[c] * STeff_k[c]) ** (ns - 1)

            # Cap non-finite values
            for c in range(K):
                if not np.isfinite(Bk[c]):
                    Bk[c] = 1.0

        # Compute waiting time
        Wchain_k_r = 0.0

        # Multi-server correction
        if ns > 1:
            Wchain_k_r = STeff_k_r * (ns - 1)

        # Add service time
        Wchain_k_r += STeff_k_r

        # Add queueing delay
        if is_open:
            Wchain_k_r += STeff_k_r * deltaclass_r * stationaryQlen_k[r] * Bk[r]
        else:
            Wchain_k_r += STeff_k_r * selfArvlQlenSeenByClosed_k_r * Bk[r]

        # Add contribution from other classes
        for i in range(n_nnz):
            c = nnzclasses[i]
            if c != r:
                Wchain_k_r += STeff_k[c] * Bk[c] * stationaryQlen_k[c]

        return Wchain_k_r

    @njit(fastmath=True, cache=True)
    def update_metrics_jit(
        M: int,
        K: int,
        omicron: float,
        Nchain: np.ndarray,
        nnzclasses: np.ndarray,
        Vchain: np.ndarray,
        Wchain: np.ndarray,
        STeff: np.ndarray,
        Xchain_1: np.ndarray,
        Qchain_1: np.ndarray,
        Uchain_1: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        JIT-compiled metric update loop.

        Args:
            M: Number of stations
            K: Number of chains
            omicron: Under-relaxation parameter
            Nchain: Population per chain
            nnzclasses: Non-zero class indices
            Vchain: Visit ratios (M x K)
            Wchain: Waiting times (M x K)
            STeff: Effective service times (M x K)
            Xchain_1: Previous throughputs
            Qchain_1: Previous queue lengths
            Uchain_1: Previous utilizations

        Returns:
            Tuple of (Xchain, Qchain, Uchain, Tchain, Rchain, Cchain_s)
        """
        Xchain = Xchain_1.copy()
        Qchain = Qchain_1.copy()
        Uchain = Uchain_1.copy()
        Tchain = np.zeros((M, K))
        Rchain = np.zeros((M, K))
        Cchain_s = np.zeros(K)

        n_nnz = len(nnzclasses)

        for i in range(n_nnz):
            r = nnzclasses[i]

            # Compute cycle time
            W_sum = 0.0
            for k in range(M):
                W_sum += Vchain[k, r] * Wchain[k, r]

            if W_sum == 0:
                Xchain[r] = 0.0
            elif np.isinf(Nchain[r]):
                # Open class - X remains constant
                Cchain_s[r] = W_sum
            elif Nchain[r] == 0:
                Xchain[r] = 0.0
                Cchain_s[r] = 0.0
            else:
                Cchain_s[r] = W_sum
                Xchain[r] = omicron * Nchain[r] / Cchain_s[r] + (1 - omicron) * Xchain_1[r]

            # Update per-station metrics
            for k in range(M):
                Rchain[k, r] = Vchain[k, r] * Wchain[k, r]
                Qchain[k, r] = omicron * Xchain[r] * Vchain[k, r] * Wchain[k, r] + (1 - omicron) * Qchain_1[k, r]
                Tchain[k, r] = Xchain[r] * Vchain[k, r]
                Uchain[k, r] = omicron * Vchain[k, r] * STeff[k, r] * Xchain[r] + (1 - omicron) * Uchain_1[k, r]

        return Xchain, Qchain, Uchain, Tchain, Rchain, Cchain_s

    @njit(fastmath=True, cache=True)
    def cap_utilizations_jit(
        M: int,
        K: int,
        Uchain: np.ndarray,
        Vchain: np.ndarray,
        STeff: np.ndarray,
        Xchain: np.ndarray,
        sched_arr: np.ndarray
    ) -> np.ndarray:
        """
        JIT-compiled utilization capping.

        Args:
            M: Number of stations
            K: Number of chains
            Uchain: Utilizations (M x K)
            Vchain: Visit ratios (M x K)
            STeff: Effective service times (M x K)
            Xchain: Throughputs (K,)
            sched_arr: Scheduling strategy per station (M,)

        Returns:
            Capped utilizations (M x K)
        """
        Uchain_out = Uchain.copy()

        for k in range(M):
            sched_k = sched_arr[k]
            # Cap for FCFS, SIRO, PS, LCFSPR, HOL (values 1-5)
            if sched_k >= SCHED_FCFS and sched_k <= SCHED_LCFSPR:
                U_sum = 0.0
                for r in range(K):
                    U_sum += Uchain[k, r]

                if U_sum > 1.0:
                    denom = 0.0
                    for r in range(K):
                        denom += Vchain[k, r] * STeff[k, r] * Xchain[r]

                    if denom > 0:
                        cap = min(1.0, U_sum)
                        for r in range(K):
                            if Vchain[k, r] * STeff[k, r] > 0:
                                Uchain_out[k, r] = cap * Vchain[k, r] * STeff[k, r] * Xchain[r] / denom

        return Uchain_out

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def compute_arrival_queue_lengths_jit(
        M: int,
        K: int,
        delta: float,
        deltaclass: np.ndarray,
        Qchain_in: np.ndarray,
        nnzclasses: np.ndarray,
        sched_arr: np.ndarray,
        classprio: np.ndarray,
        has_classprio: bool
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Pure Python arrival queue length computation."""
        interpTotArvlQlen = np.zeros(M)
        selfArvlQlenSeenByClosed = np.zeros((M, K))
        totArvlQlenSeenByClosed = np.zeros((M, K))
        stationaryQlen = np.zeros((M, K))

        for k in range(M):
            tot_q = np.sum(Qchain_in[k, nnzclasses])
            interpTotArvlQlen[k] = delta * tot_q

            for r in nnzclasses:
                selfArvlQlenSeenByClosed[k, r] = deltaclass[r] * Qchain_in[k, r]
                totArvlQlenSeenByClosed[k, r] = (deltaclass[r] * Qchain_in[k, r] +
                                                  tot_q - Qchain_in[k, r])
                stationaryQlen[k, r] = Qchain_in[k, r]

        return interpTotArvlQlen, selfArvlQlenSeenByClosed, totArvlQlenSeenByClosed, stationaryQlen

    def compute_fcfs_waiting_time_jit(
        STeff_k_r: float,
        ns: float,
        deltaclass: np.ndarray,
        deltaclass_r: float,
        Xchain_in: np.ndarray,
        Vchain_k: np.ndarray,
        STeff_k: np.ndarray,
        selfArvlQlenSeenByClosed_k_r: float,
        stationaryQlen_k: np.ndarray,
        nnzclasses: np.ndarray,
        r: int,
        is_open: bool
    ) -> float:
        """Pure Python FCFS waiting time computation."""
        if STeff_k_r <= 0:
            return 0.0

        K = len(deltaclass)
        Bk = np.ones(K)

        if ns > 1 and not np.isinf(ns):
            deltaclass_vec = deltaclass.copy()
            deltaclass_vec[r] = deltaclass_r
            rho_sum = np.sum(deltaclass_vec[nnzclasses] * Xchain_in[nnzclasses] *
                            Vchain_k[nnzclasses] * STeff_k[nnzclasses])

            if rho_sum < 0.75:
                Bk[nnzclasses] = (deltaclass_vec[nnzclasses] * Xchain_in[nnzclasses] *
                                  Vchain_k[nnzclasses] * STeff_k[nnzclasses])
            else:
                Bk[nnzclasses] = (deltaclass_vec[nnzclasses] * Xchain_in[nnzclasses] *
                                  Vchain_k[nnzclasses] * STeff_k[nnzclasses]) ** (ns - 1)

            Bk = np.where(np.isfinite(Bk), Bk, 1.0)

        Wchain_k_r = 0.0
        if ns > 1:
            Wchain_k_r = STeff_k_r * (ns - 1)
        Wchain_k_r += STeff_k_r

        if is_open:
            Wchain_k_r += STeff_k_r * deltaclass_r * stationaryQlen_k[r] * Bk[r]
        else:
            Wchain_k_r += STeff_k_r * selfArvlQlenSeenByClosed_k_r * Bk[r]

        sd = np.setdiff1d(nnzclasses, [r])
        Wchain_k_r += np.sum(STeff_k[sd] * Bk[sd] * stationaryQlen_k[sd])

        return Wchain_k_r

    def update_metrics_jit(
        M: int,
        K: int,
        omicron: float,
        Nchain: np.ndarray,
        nnzclasses: np.ndarray,
        Vchain: np.ndarray,
        Wchain: np.ndarray,
        STeff: np.ndarray,
        Xchain_1: np.ndarray,
        Qchain_1: np.ndarray,
        Uchain_1: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Pure Python metric update loop."""
        Xchain = Xchain_1.copy()
        Qchain = Qchain_1.copy()
        Uchain = Uchain_1.copy()
        Tchain = np.zeros((M, K))
        Rchain = np.zeros((M, K))
        Cchain_s = np.zeros(K)

        for r in nnzclasses:
            W_sum = np.dot(Vchain[:, r], Wchain[:, r])

            if W_sum == 0:
                Xchain[r] = 0.0
            elif np.isinf(Nchain[r]):
                Cchain_s[r] = W_sum
            elif Nchain[r] == 0:
                Xchain[r] = 0.0
                Cchain_s[r] = 0.0
            else:
                Cchain_s[r] = W_sum
                Xchain[r] = omicron * Nchain[r] / Cchain_s[r] + (1 - omicron) * Xchain_1[r]

            for k in range(M):
                Rchain[k, r] = Vchain[k, r] * Wchain[k, r]
                Qchain[k, r] = omicron * Xchain[r] * Vchain[k, r] * Wchain[k, r] + (1 - omicron) * Qchain_1[k, r]
                Tchain[k, r] = Xchain[r] * Vchain[k, r]
                Uchain[k, r] = omicron * Vchain[k, r] * STeff[k, r] * Xchain[r] + (1 - omicron) * Uchain_1[k, r]

        return Xchain, Qchain, Uchain, Tchain, Rchain, Cchain_s

    def cap_utilizations_jit(
        M: int,
        K: int,
        Uchain: np.ndarray,
        Vchain: np.ndarray,
        STeff: np.ndarray,
        Xchain: np.ndarray,
        sched_arr: np.ndarray
    ) -> np.ndarray:
        """Pure Python utilization capping."""
        Uchain_out = Uchain.copy()

        for k in range(M):
            sched_k = sched_arr[k]
            if sched_k >= SCHED_FCFS and sched_k <= SCHED_LCFSPR:
                U_sum = np.sum(Uchain[k, :])

                if U_sum > 1.0:
                    denom = np.sum(Vchain[k, :] * STeff[k, :] * Xchain)
                    if denom > 0:
                        cap = min(1.0, U_sum)
                        for r in range(K):
                            if Vchain[k, r] * STeff[k, r] > 0:
                                Uchain_out[k, r] = cap * Vchain[k, r] * STeff[k, r] * Xchain[r] / denom

        return Uchain_out


__all__ = [
    'HAS_NUMBA',
    'SCHED_INF',
    'SCHED_FCFS',
    'SCHED_SIRO',
    'SCHED_PS',
    'SCHED_HOL',
    'SCHED_LCFSPR',
    'SCHED_EXT',
    'compute_arrival_queue_lengths_jit',
    'compute_fcfs_waiting_time_jit',
    'update_metrics_jit',
    'cap_utilizations_jit',
]
