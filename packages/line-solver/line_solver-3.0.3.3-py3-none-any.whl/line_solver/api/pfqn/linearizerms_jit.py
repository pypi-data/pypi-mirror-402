"""
JIT-compiled kernels for Multi-server Linearizer algorithms.

Provides Numba-accelerated versions of the core Linearizer computational hotspots:
- Estimate step (triple nested loops)
- Forward MVA step (residence time computation)
- Population enumeration (stars and bars)
- Conway multi-server specific computations

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
    def estimate_ms_jit(
        M: int,
        R: int,
        N_1: np.ndarray,
        nservers: np.ndarray,
        Q: np.ndarray,
        P: np.ndarray,
        PB: np.ndarray,
        Delta: np.ndarray,
        max_servers: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        JIT-compiled estimate step for multiserver linearizer.

        Computes Q_1, P_1, PB_1 from current estimates.

        Args:
            M: Number of stations
            R: Number of classes
            N_1: Reduced population vector
            nservers: Number of servers per station
            Q: Current queue length estimates (M, R)
            P: Current probability estimates (M, max_servers)
            PB: Current blocking probability (M,)
            Delta: Delta corrections (M, R, R)
            max_servers: Maximum server count

        Returns:
            Tuple of (Q_1, P_1, PB_1)
        """
        P_1 = np.zeros((M, max_servers, 1 + R))
        PB_1 = np.zeros((M, 1 + R))
        Q_1 = np.zeros((M, R, 1 + R))

        for ist in range(M):
            ns = nservers[ist]
            if ns > 1 and not np.isinf(ns):
                ns_int = int(ns)
                for j in range(ns_int):
                    for s in range(R + 1):
                        P_1[ist, j, s] = P[ist, j]

                for s in range(R + 1):
                    PB_1[ist, s] = PB[ist]

            for r in range(R):
                for s in range(R):
                    # Compute Ns[r] = N_1[r] - (1 if s==r else 0)
                    Ns_r = N_1[r] - (1.0 if s == r else 0.0)
                    if N_1[r] > 0:
                        # Store at s+1 to match MATLAB's 1+s indexing
                        Q_1[ist, r, s + 1] = Ns_r * (Q[ist, r] / N_1[r] + Delta[ist, r, s])
                    else:
                        Q_1[ist, r, s + 1] = 0.0

        return Q_1, P_1, PB_1

    @njit(fastmath=True, cache=True)
    def forward_mva_ms_jit(
        L: np.ndarray,
        M: int,
        R: int,
        N_1: np.ndarray,
        Z: np.ndarray,
        nservers: np.ndarray,
        type_sched: np.ndarray,
        Q_1: np.ndarray,
        P_1: np.ndarray,
        PB_1: np.ndarray,
        max_servers: int,
        SCHED_FCFS: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        JIT-compiled forward MVA step for multiserver linearizer.

        Args:
            L: Service demand matrix (M, R)
            M: Number of stations
            R: Number of classes
            N_1: Population vector
            Z: Think time vector
            nservers: Number of servers per station
            type_sched: Scheduling strategy per station (int array)
            Q_1: Estimated queue lengths (M, R, 1+R)
            P_1: Estimated probabilities (M, max_servers, 1+R)
            PB_1: Estimated blocking probabilities (M, 1+R)
            max_servers: Maximum server count
            SCHED_FCFS: Integer code for FCFS scheduling

        Returns:
            Tuple of (Q, W, T, P, PB)
        """
        W = np.zeros((M, R))
        T = np.zeros(R)
        Q = np.zeros((M, R))
        P = np.zeros((M, max_servers))
        PB = np.zeros(M)

        # Compute residence times
        for ist in range(M):
            ns = nservers[ist]
            ns_int = int(ns) if not np.isinf(ns) else 1

            for r in range(R):
                W[ist, r] = L[ist, r] / ns
                if L[ist, r] == 0:
                    continue

                # Use r+1 for 3rd dim to match MATLAB's 1+r indexing
                if type_sched[ist] == SCHED_FCFS:
                    for s in range(R):
                        W[ist, r] += (L[ist, s] / ns) * Q_1[ist, s, r + 1]
                else:
                    for s in range(R):
                        W[ist, r] += (L[ist, r] / ns) * Q_1[ist, s, r + 1]

                if ns > 1 and not np.isinf(ns):
                    for j in range(ns_int - 1):
                        if type_sched[ist] == SCHED_FCFS:
                            for s in range(R):
                                W[ist, r] += L[ist, s] * (ns - 1 - j) * P_1[ist, j, r + 1]
                        else:
                            for s in range(R):
                                W[ist, r] += L[ist, r] * (ns - 1 - j) * P_1[ist, j, r + 1]

        # Compute throughputs and queue lengths
        for r in range(R):
            denom = Z[r]
            for ist in range(M):
                denom += W[ist, r]
            if denom > 0:
                T[r] = N_1[r] / denom
            else:
                T[r] = 0.0

            for ist in range(M):
                Q[ist, r] = T[r] * W[ist, r]

        # Compute marginal probabilities for multiserver stations
        for ist in range(M):
            ns = nservers[ist]
            if ns > 1 and not np.isinf(ns):
                ns_int = int(ns)
                for k in range(max_servers):
                    P[ist, k] = 0.0
                for j in range(1, ns_int):
                    for s in range(R):
                        # Use s+1 for 3rd dim to match MATLAB's 1+s indexing
                        P[ist, j] += L[ist, s] * T[s] * P_1[ist, j - 1, s + 1] / j

        # Compute blocking probabilities
        for ist in range(M):
            ns = nservers[ist]
            if ns > 1 and not np.isinf(ns):
                ns_int = int(ns)
                PB[ist] = 0.0
                for s in range(R):
                    # Use s+1 for indices to match MATLAB's 1+s indexing
                    PB[ist] += L[ist, s] * T[s] * (PB_1[ist, s + 1] + P_1[ist, ns_int - 1, s + 1]) / ns

        # Normalize P[ist, 0]
        for ist in range(M):
            ns = nservers[ist]
            if ns > 1 and not np.isinf(ns):
                ns_int = int(ns)
                P[ist, 0] = 1.0 - PB[ist]
                for j in range(1, ns_int):
                    P[ist, 0] -= P[ist, j]

        return Q, W, T, P, PB

    @njit(cache=True)
    def sprod_count_jit(n: int, R: int) -> int:
        """
        JIT-compiled count of combinations (n+R-1 choose R-1).

        Uses iterative calculation to avoid overflow.

        Args:
            n: Total population
            R: Number of classes

        Returns:
            Number of combinations
        """
        if R <= 1:
            return 1

        # Compute binomial coefficient (n + R - 1) choose (R - 1)
        # Use smaller of (R-1) and n to minimize iterations
        k = R - 1
        if k > n:
            k = n

        result = 1
        for i in range(k):
            result = result * (n + R - 1 - i) // (i + 1)

        return result

    @njit(cache=True)
    def sprod_next_jit(
        s: int,
        n: int,
        R: int,
        nvec_in: np.ndarray
    ) -> Tuple[int, np.ndarray]:
        """
        JIT-compiled population vector increment (stars and bars).

        Args:
            s: Current state index
            n: Total population
            R: Number of classes
            nvec_in: Current population vector (modified in place)

        Returns:
            Tuple of (new_s, nvec) where new_s < 0 if exhausted
        """
        nvec = nvec_in.copy()

        if s < 0:
            return s, nvec

        total = sprod_count_jit(n, R)

        s += 1
        if s >= total:
            return -1, nvec

        # Convert s to nvec using stars and bars
        remaining = n
        temp_s = s

        for i in range(R - 1):
            for k in range(remaining + 1):
                # Compute comb(remaining - k + R - i - 2, R - i - 2)
                c = sprod_count_jit(remaining - k, R - i - 1)
                if temp_s < c:
                    nvec[i] = k
                    remaining -= k
                    break
                temp_s -= c

        nvec[R - 1] = remaining

        return 0, nvec

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

    @njit(fastmath=True, cache=True)
    def conway_estimate_jit(
        M: int,
        R: int,
        N_1: np.ndarray,
        nservers: np.ndarray,
        Q: np.ndarray,
        P: np.ndarray,
        PB: np.ndarray,
        Delta: np.ndarray,
        W: np.ndarray,
        max_servers: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        JIT-compiled estimate step for Conway multiserver linearizer.

        Args:
            M: Number of stations
            R: Number of classes
            N_1: Population vector
            nservers: Number of servers per station
            Q: Queue length estimates (M, R)
            P: Probability estimates (M, max_servers)
            PB: Blocking probability (M,)
            Delta: Delta corrections (M, R, R)
            W: Residence times (M, R)
            max_servers: Maximum server count

        Returns:
            Tuple of (Q_1, P_1, PB_1, T_1)
        """
        P_1 = np.zeros((M, max_servers, 1 + R))
        PB_1 = np.zeros((M, 1 + R))
        Q_1 = np.zeros((M, R, 1 + R))
        T_1 = np.zeros((R, 1 + R))

        for ist in range(M):
            ns = nservers[ist]
            if ns > 1 and not np.isinf(ns):
                ns_int = int(ns)
                for j in range(ns_int):
                    for s in range(R + 1):
                        P_1[ist, j, s] = P[ist, j]
                for s in range(R + 1):
                    PB_1[ist, s] = PB[ist]

            for r in range(R):
                for s in range(R):
                    # Compute Ns[r] = N_1[r] - (1 if s==r else 0)
                    Ns_r = N_1[r] - (1.0 if s == r else 0.0)
                    if N_1[r] > 0:
                        Q_1[ist, r, s] = Ns_r * (Q[ist, r] / N_1[r] + Delta[ist, r, s])
                    else:
                        Q_1[ist, r, s] = 0.0

        # Compute T_1
        for r in range(R):
            for s in range(R):
                # Compute Nr[s] = N_1[s] - (1 if r==s else 0)
                Nr_s = N_1[s] - (1.0 if r == s else 0.0)
                for ist in range(M):
                    if W[ist, s] > 0 and N_1[s] > 0:
                        T_1[s, r] = Nr_s * (Q[ist, s] / N_1[s] + Delta[ist, r, s]) / W[ist, s]
                        break

        return Q_1, P_1, PB_1, T_1

    @njit(fastmath=True, cache=True)
    def conway_compute_F_jit(
        M: int,
        R: int,
        L: np.ndarray,
        T_1: np.ndarray
    ) -> np.ndarray:
        """
        JIT-compiled F matrix computation for Conway algorithm.

        Args:
            M: Number of stations
            R: Number of classes
            L: Service demand matrix (M, R)
            T_1: Throughput estimates (R, 1+R)

        Returns:
            F matrix (R, M, R)
        """
        F = np.zeros((R, M, R))

        for r in range(R):
            for ist in range(M):
                den = 0.0
                for c in range(R):
                    den += L[ist, c] * T_1[c, r]
                if den > 0:
                    for c in range(R):
                        F[r, ist, c] = T_1[c, r] * L[ist, c] / den

        return F

    @njit(fastmath=True, cache=True)
    def conway_compute_XR_jit(
        M: int,
        R: int,
        N_1: np.ndarray,
        nservers: np.ndarray,
        L: np.ndarray,
        F: np.ndarray
    ) -> np.ndarray:
        """
        JIT-compiled XR computation for Conway multi-server.

        Args:
            M: Number of stations
            R: Number of classes
            N_1: Population vector
            nservers: Number of servers per station
            L: Service demand matrix (M, R)
            F: F matrix (R, M, R)

        Returns:
            XR matrix (M, R)
        """
        XR = np.zeros((M, R))
        mu = np.zeros((M, R))

        for ist in range(M):
            for c in range(R):
                if L[ist, c] > 1e-12:
                    mu[ist, c] = 1.0 / L[ist, c]
                else:
                    mu[ist, c] = 1e12

        for ist in range(M):
            ns = nservers[ist]
            if ns > 1 and not np.isinf(ns):
                ns_int = int(ns)

                for r in range(R):
                    XR_sum = 0.0
                    C_val = 0.0

                    # Enumerate population vectors with sum = ns_int
                    nvec = np.zeros(R, dtype=np.int64)
                    nvec[0] = ns_int
                    s = 0

                    while s >= 0:
                        # Check if nvec <= Nr (N_1 with element r reduced by 1)
                        valid = True
                        for c in range(R):
                            Nr_c = N_1[c] - (1.0 if c == r else 0.0)
                            if nvec[c] > Nr_c:
                                valid = False
                                break

                        if valid:
                            # Compute Ai = exp(multinomialln + sum(nvec * log(F)))
                            log_F_sum = 0.0
                            for c in range(R):
                                if nvec[c] > 0:
                                    F_val = F[r, ist, c]
                                    if F_val > 1e-300:
                                        log_F_sum += nvec[c] * np.log(F_val)
                                    else:
                                        log_F_sum += nvec[c] * np.log(1e-300)

                            Ai = np.exp(multinomialln_jit(nvec.astype(np.float64)) + log_F_sum)
                            C_val += Ai

                            mu_sum = 0.0
                            for c in range(R):
                                mu_sum += mu[ist, c] * nvec[c]
                            if mu_sum > 0:
                                XR_sum += Ai / mu_sum

                        s, nvec = sprod_next_jit(s, ns_int, R, nvec)

                    if C_val > 0:
                        XR[ist, r] = XR_sum / C_val

        return XR

    @njit(fastmath=True, cache=True)
    def conway_compute_XE_jit(
        M: int,
        R: int,
        N_1: np.ndarray,
        nservers: np.ndarray,
        L: np.ndarray,
        F: np.ndarray
    ) -> np.ndarray:
        """
        JIT-compiled XE computation for Conway multi-server.

        Args:
            M: Number of stations
            R: Number of classes
            N_1: Population vector
            nservers: Number of servers per station
            L: Service demand matrix (M, R)
            F: F matrix (R, M, R)

        Returns:
            XE matrix (M, R, R)
        """
        XE = np.zeros((M, R, R))
        mu = np.zeros((M, R))

        for ist in range(M):
            for c in range(R):
                if L[ist, c] > 1e-12:
                    mu[ist, c] = 1.0 / L[ist, c]
                else:
                    mu[ist, c] = 1e12

        for ist in range(M):
            ns = nservers[ist]
            if ns > 1 and not np.isinf(ns):
                ns_int = int(ns)

                for r in range(R):
                    for target_c in range(R):
                        XE_sum = 0.0
                        Cx = 0.0

                        # Enumerate population vectors with sum = ns_int
                        nvec = np.zeros(R, dtype=np.int64)
                        nvec[0] = ns_int
                        s = 0

                        while s >= 0:
                            # Check if nvec <= Nr and nvec[target_c] >= 1
                            valid = True
                            for c in range(R):
                                Nr_c = N_1[c] - (1.0 if c == r else 0.0)
                                if nvec[c] > Nr_c:
                                    valid = False
                                    break

                            if valid and nvec[target_c] >= 1:
                                # Compute Aix
                                log_F_sum = 0.0
                                for c in range(R):
                                    if nvec[c] > 0:
                                        F_val = F[r, ist, c]
                                        if F_val > 1e-300:
                                            log_F_sum += nvec[c] * np.log(F_val)
                                        else:
                                            log_F_sum += nvec[c] * np.log(1e-300)

                                Aix = np.exp(multinomialln_jit(nvec.astype(np.float64)) + log_F_sum)
                                Cx += Aix

                                mu_sum = 0.0
                                for c in range(R):
                                    mu_sum += mu[ist, c] * nvec[c]
                                if mu_sum > 0:
                                    XE_sum += Aix / mu_sum

                            s, nvec = sprod_next_jit(s, ns_int, R, nvec)

                        if Cx > 0:
                            XE[ist, r, target_c] = XE_sum / Cx

        return XE

    @njit(fastmath=True, cache=True)
    def conway_forward_mva_residence_jit(
        L: np.ndarray,
        M: int,
        R: int,
        nservers: np.ndarray,
        type_sched: np.ndarray,
        Q_1: np.ndarray,
        PB_1: np.ndarray,
        T_1: np.ndarray,
        XR: np.ndarray,
        XE: np.ndarray,
        SCHED_FCFS: int
    ) -> np.ndarray:
        """
        JIT-compiled residence time computation for Conway forward MVA.

        Args:
            L: Service demand matrix (M, R)
            M: Number of stations
            R: Number of classes
            nservers: Number of servers per station
            type_sched: Scheduling strategy per station
            Q_1: Estimated queue lengths (M, R, 1+R)
            PB_1: Blocking probabilities (M, 1+R)
            T_1: Throughput estimates (R, 1+R)
            XR: XR matrix (M, R)
            XE: XE matrix (M, R, R)
            SCHED_FCFS: Integer code for FCFS scheduling

        Returns:
            W: Residence times (M, R)
        """
        W = np.zeros((M, R))

        for ist in range(M):
            ns = nservers[ist]
            for r in range(R):
                if ns == 1 or np.isinf(ns):
                    if type_sched[ist] == SCHED_FCFS:
                        W[ist, r] = L[ist, r]
                        for c in range(R):
                            W[ist, r] += L[ist, c] * Q_1[ist, c, r]
                    else:
                        W[ist, r] = L[ist, r]
                        for c in range(R):
                            W[ist, r] += L[ist, r] * Q_1[ist, c, r]
                else:
                    W[ist, r] = L[ist, r] + PB_1[ist, r] * XR[ist, r]
                    for c in range(R):
                        W[ist, r] += XE[ist, r, c] * (Q_1[ist, c, r] - L[ist, c] * T_1[c, r])

        return W

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def estimate_ms_jit(
        M: int,
        R: int,
        N_1: np.ndarray,
        nservers: np.ndarray,
        Q: np.ndarray,
        P: np.ndarray,
        PB: np.ndarray,
        Delta: np.ndarray,
        max_servers: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Pure Python estimate step."""
        P_1 = np.zeros((M, max_servers, 1 + R))
        PB_1 = np.zeros((M, 1 + R))
        Q_1 = np.zeros((M, R, 1 + R))

        for ist in range(M):
            ns = nservers[ist]
            if ns > 1 and not np.isinf(ns):
                ns_int = int(ns)
                for j in range(ns_int):
                    for s in range(R + 1):
                        P_1[ist, j, s] = P[ist, j]
                for s in range(R + 1):
                    PB_1[ist, s] = PB[ist]

            for r in range(R):
                for s in range(R):
                    Ns_r = N_1[r] - (1.0 if s == r else 0.0)
                    if N_1[r] > 0:
                        Q_1[ist, r, s + 1] = Ns_r * (Q[ist, r] / N_1[r] + Delta[ist, r, s])
                    else:
                        Q_1[ist, r, s + 1] = 0.0

        return Q_1, P_1, PB_1

    def forward_mva_ms_jit(
        L: np.ndarray,
        M: int,
        R: int,
        N_1: np.ndarray,
        Z: np.ndarray,
        nservers: np.ndarray,
        type_sched: np.ndarray,
        Q_1: np.ndarray,
        P_1: np.ndarray,
        PB_1: np.ndarray,
        max_servers: int,
        SCHED_FCFS: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Pure Python forward MVA step."""
        W = np.zeros((M, R))
        T = np.zeros(R)
        Q = np.zeros((M, R))
        P = np.zeros((M, max_servers))
        PB = np.zeros(M)

        for ist in range(M):
            ns = nservers[ist]
            ns_int = int(ns) if not np.isinf(ns) else 1

            for r in range(R):
                W[ist, r] = L[ist, r] / ns
                if L[ist, r] == 0:
                    continue

                if type_sched[ist] == SCHED_FCFS:
                    for s in range(R):
                        W[ist, r] += (L[ist, s] / ns) * Q_1[ist, s, r + 1]
                else:
                    for s in range(R):
                        W[ist, r] += (L[ist, r] / ns) * Q_1[ist, s, r + 1]

                if ns > 1 and not np.isinf(ns):
                    for j in range(ns_int - 1):
                        if type_sched[ist] == SCHED_FCFS:
                            for s in range(R):
                                W[ist, r] += L[ist, s] * (ns - 1 - j) * P_1[ist, j, r + 1]
                        else:
                            for s in range(R):
                                W[ist, r] += L[ist, r] * (ns - 1 - j) * P_1[ist, j, r + 1]

        for r in range(R):
            denom = Z[r] + np.sum(W[:, r])
            if denom > 0:
                T[r] = N_1[r] / denom
            else:
                T[r] = 0.0

            for ist in range(M):
                Q[ist, r] = T[r] * W[ist, r]

        for ist in range(M):
            ns = nservers[ist]
            if ns > 1 and not np.isinf(ns):
                ns_int = int(ns)
                P[ist, :] = 0
                for j in range(1, ns_int):
                    for s in range(R):
                        P[ist, j] += L[ist, s] * T[s] * P_1[ist, j - 1, s + 1] / j

        for ist in range(M):
            ns = nservers[ist]
            if ns > 1 and not np.isinf(ns):
                ns_int = int(ns)
                PB[ist] = 0.0
                for s in range(R):
                    PB[ist] += L[ist, s] * T[s] * (PB_1[ist, s + 1] + P_1[ist, ns_int - 1, s + 1]) / ns

        for ist in range(M):
            ns = nservers[ist]
            if ns > 1 and not np.isinf(ns):
                ns_int = int(ns)
                P[ist, 0] = 1.0 - PB[ist]
                for j in range(1, ns_int):
                    P[ist, 0] -= P[ist, j]

        return Q, W, T, P, PB

    def sprod_count_jit(n: int, R: int) -> int:
        """Pure Python combination count."""
        from scipy.special import comb
        return int(comb(n + R - 1, R - 1))

    def sprod_next_jit(
        s: int,
        n: int,
        R: int,
        nvec_in: np.ndarray
    ) -> Tuple[int, np.ndarray]:
        """Pure Python population increment."""
        from scipy.special import comb
        nvec = nvec_in.copy()

        if s < 0:
            return s, nvec

        total = int(comb(n + R - 1, R - 1))
        s += 1
        if s >= total:
            return -1, nvec

        remaining = n
        temp_s = s

        for i in range(R - 1):
            for k in range(remaining + 1):
                c = int(comb(remaining - k + R - i - 2, R - i - 2))
                if temp_s < c:
                    nvec[i] = k
                    remaining -= k
                    break
                temp_s -= c

        nvec[R - 1] = remaining
        return 0, nvec

    def multinomialln_jit(n: np.ndarray) -> float:
        """Pure Python log multinomial."""
        from scipy.special import gammaln
        return float(gammaln(np.sum(n) + 1) - np.sum(gammaln(np.asarray(n) + 1)))

    def conway_estimate_jit(
        M: int,
        R: int,
        N_1: np.ndarray,
        nservers: np.ndarray,
        Q: np.ndarray,
        P: np.ndarray,
        PB: np.ndarray,
        Delta: np.ndarray,
        W: np.ndarray,
        max_servers: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Pure Python Conway estimate."""
        P_1 = np.zeros((M, max_servers, 1 + R))
        PB_1 = np.zeros((M, 1 + R))
        Q_1 = np.zeros((M, R, 1 + R))
        T_1 = np.zeros((R, 1 + R))

        for ist in range(M):
            ns = nservers[ist]
            if ns > 1 and not np.isinf(ns):
                ns_int = int(ns)
                for j in range(ns_int):
                    for s in range(R + 1):
                        P_1[ist, j, s] = P[ist, j]
                for s in range(R + 1):
                    PB_1[ist, s] = PB[ist]

            for r in range(R):
                for s in range(R):
                    Ns_r = N_1[r] - (1.0 if s == r else 0.0)
                    if N_1[r] > 0:
                        Q_1[ist, r, s] = Ns_r * (Q[ist, r] / N_1[r] + Delta[ist, r, s])
                    else:
                        Q_1[ist, r, s] = 0.0

        for r in range(R):
            for s in range(R):
                Nr_s = N_1[s] - (1.0 if r == s else 0.0)
                for ist in range(M):
                    if W[ist, s] > 0 and N_1[s] > 0:
                        T_1[s, r] = Nr_s * (Q[ist, s] / N_1[s] + Delta[ist, r, s]) / W[ist, s]
                        break

        return Q_1, P_1, PB_1, T_1

    def conway_compute_F_jit(
        M: int,
        R: int,
        L: np.ndarray,
        T_1: np.ndarray
    ) -> np.ndarray:
        """Pure Python F matrix computation."""
        F = np.zeros((R, M, R))

        for r in range(R):
            for ist in range(M):
                den = np.dot(L[ist, :], T_1[:, r])
                if den > 0:
                    for c in range(R):
                        F[r, ist, c] = T_1[c, r] * L[ist, c] / den

        return F

    def conway_compute_XR_jit(
        M: int,
        R: int,
        N_1: np.ndarray,
        nservers: np.ndarray,
        L: np.ndarray,
        F: np.ndarray
    ) -> np.ndarray:
        """Pure Python XR computation."""
        from .linearizerms import sprod, sprod_next, multinomialln

        XR = np.zeros((M, R))
        mu = 1.0 / np.maximum(L, 1e-12)

        for ist in range(M):
            ns = nservers[ist]
            if ns > 1 and not np.isinf(ns):
                ns_int = int(ns)
                for r in range(R):
                    XR_sum = 0.0
                    C_val = 0.0

                    s, nvec, SD, D = sprod(R, ns_int)
                    while s >= 0:
                        Nr = N_1.copy()
                        Nr[r] -= 1
                        if np.all(nvec <= Nr):
                            Ai = np.exp(multinomialln(nvec) + np.dot(nvec, np.log(np.maximum(F[r, ist, :], 1e-300))))
                            C_val += Ai
                            mu_sum = np.dot(mu[ist, :], nvec)
                            if mu_sum > 0:
                                XR_sum += Ai / mu_sum

                        s, nvec = sprod_next(s, SD, D)

                    if C_val > 0:
                        XR[ist, r] = XR_sum / C_val

        return XR

    def conway_compute_XE_jit(
        M: int,
        R: int,
        N_1: np.ndarray,
        nservers: np.ndarray,
        L: np.ndarray,
        F: np.ndarray
    ) -> np.ndarray:
        """Pure Python XE computation."""
        from .linearizerms import sprod, sprod_next, multinomialln

        XE = np.zeros((M, R, R))
        mu = 1.0 / np.maximum(L, 1e-12)

        for ist in range(M):
            ns = nservers[ist]
            if ns > 1 and not np.isinf(ns):
                ns_int = int(ns)
                for r in range(R):
                    for target_c in range(R):
                        XE_sum = 0.0
                        Cx = 0.0

                        s, nvec, SD, D = sprod(R, ns_int)
                        while s >= 0:
                            Nr = N_1.copy()
                            Nr[r] -= 1
                            if np.all(nvec <= Nr) and nvec[target_c] >= 1:
                                Aix = np.exp(multinomialln(nvec) + np.dot(nvec, np.log(np.maximum(F[r, ist, :], 1e-300))))
                                Cx += Aix
                                mu_sum = np.dot(mu[ist, :], nvec)
                                if mu_sum > 0:
                                    XE_sum += Aix / mu_sum

                            s, nvec = sprod_next(s, SD, D)

                        if Cx > 0:
                            XE[ist, r, target_c] = XE_sum / Cx

        return XE

    def conway_forward_mva_residence_jit(
        L: np.ndarray,
        M: int,
        R: int,
        nservers: np.ndarray,
        type_sched: np.ndarray,
        Q_1: np.ndarray,
        PB_1: np.ndarray,
        T_1: np.ndarray,
        XR: np.ndarray,
        XE: np.ndarray,
        SCHED_FCFS: int
    ) -> np.ndarray:
        """Pure Python Conway residence time computation."""
        W = np.zeros((M, R))

        for ist in range(M):
            ns = nservers[ist]
            for r in range(R):
                if ns == 1 or np.isinf(ns):
                    if type_sched[ist] == SCHED_FCFS:
                        W[ist, r] = L[ist, r]
                        for c in range(R):
                            W[ist, r] += L[ist, c] * Q_1[ist, c, r]
                    else:
                        W[ist, r] = L[ist, r]
                        for c in range(R):
                            W[ist, r] += L[ist, r] * Q_1[ist, c, r]
                else:
                    W[ist, r] = L[ist, r] + PB_1[ist, r] * XR[ist, r]
                    for c in range(R):
                        W[ist, r] += XE[ist, r, c] * (Q_1[ist, c, r] - L[ist, c] * T_1[c, r])

        return W


__all__ = [
    'HAS_NUMBA',
    'estimate_ms_jit',
    'forward_mva_ms_jit',
    'sprod_count_jit',
    'sprod_next_jit',
    'multinomialln_jit',
    'conway_estimate_jit',
    'conway_compute_F_jit',
    'conway_compute_XR_jit',
    'conway_compute_XE_jit',
    'conway_forward_mva_residence_jit',
]
