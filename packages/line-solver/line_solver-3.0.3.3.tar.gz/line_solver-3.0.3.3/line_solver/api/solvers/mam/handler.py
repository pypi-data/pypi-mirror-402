"""
MAM Solver handler.

Native Python implementation of MAM (Matrix-Analytic Methods) solver handler
that analyzes queueing networks with phase-type distributions and Markovian
arrival processes.

Port from MATLAB solver_mam_basic.m
"""

import numpy as np
import numpy.matlib as ml
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple, Any
import time
import warnings

from ...sn import (
    NetworkStruct,
    SchedStrategy,
    NodeType,
    sn_is_open_model,
    sn_is_closed_model,
    sn_get_demands_chain,
)

# Try to import MMAPPH1FCFS for accurate MMAP/PH/1/FCFS analysis
try:
    from ...butools.queues import MMAPPH1FCFS
    HAS_MMAPPH1FCFS = True
except ImportError:
    HAS_MMAPPH1FCFS = False
    MMAPPH1FCFS = None


@dataclass
class SolverMAMOptions:
    """Options for MAM solver."""
    method: str = 'default'
    tol: float = 1e-6
    verbose: bool = False
    iter_max: int = 100
    iter_tol: float = 1e-6
    space_max: int = 128
    merge: str = 'super'
    compress: str = 'mixture.order1'
    num_cdf_pts: int = 200  # Number of points for CDF computation


@dataclass
class SolverMAMReturn:
    """
    Result of MAM solver handler.

    Attributes:
        Q: Mean queue lengths (M x K)
        U: Utilizations (M x K)
        R: Response times (M x K)
        T: Throughputs (M x K)
        C: Cycle times (1 x K)
        X: System throughputs (1 x K)
        A: Arrival rates (M x K)
        W: Waiting times (M x K)
        runtime: Runtime in seconds
        method: Method used
        it: Number of iterations
    """
    Q: Optional[np.ndarray] = None
    U: Optional[np.ndarray] = None
    R: Optional[np.ndarray] = None
    T: Optional[np.ndarray] = None
    C: Optional[np.ndarray] = None
    X: Optional[np.ndarray] = None
    A: Optional[np.ndarray] = None
    W: Optional[np.ndarray] = None
    runtime: float = 0.0
    method: str = "default"
    it: int = 0


def _get_visits(sn: NetworkStruct) -> np.ndarray:
    """
    Compute station visit ratios from routing matrix.
    Equivalent to MATLAB: V = cellsum(sn.visits)

    NOTE: sn.visits[c] is indexed by STATEFUL NODE index (shape nstateful x K).
    We must convert station index to stateful index using stationToStateful.

    Args:
        sn: Network structure

    Returns:
        Visit ratios matrix (M x K)
    """
    M = sn.nstations
    K = sn.nclasses

    # Initialize visits matrix
    V = np.zeros((M, K))

    if sn.visits is not None and len(sn.visits) > 0:
        # Get station to stateful mapping
        stationToStateful = sn.stationToStateful
        if stationToStateful is None or len(stationToStateful) == 0:
            stationToStateful = np.arange(M)
        else:
            stationToStateful = np.asarray(stationToStateful).flatten()

        # Sum visits across all chains
        for c, visit_matrix in sn.visits.items():
            if visit_matrix is not None:
                v = np.asarray(visit_matrix)
                # Extract station rows using stationToStateful mapping
                for ist in range(M):
                    if ist < len(stationToStateful):
                        isf = int(stationToStateful[ist])
                        if isf < v.shape[0]:
                            V[ist, :] += v[isf, :]
    else:
        # Default: equal visits
        V = np.ones((M, K))

    return V


def _get_service_times(sn: NetworkStruct) -> np.ndarray:
    """
    Extract service times from network structure.
    S = 1 / rates

    Args:
        sn: Network structure

    Returns:
        Service times matrix (M x K)
    """
    M = sn.nstations
    K = sn.nclasses

    if hasattr(sn, 'rates') and sn.rates is not None:
        rates = np.asarray(sn.rates)
        with np.errstate(divide='ignore', invalid='ignore'):
            S = np.where(rates > 0, 1.0 / rates, 0.0)
            S = np.nan_to_num(S, nan=0.0, posinf=0.0, neginf=0.0)
        return S

    return np.ones((M, K))


def _get_nservers(sn: NetworkStruct) -> np.ndarray:
    """
    Get number of servers per station.

    Args:
        sn: Network structure

    Returns:
        Number of servers array (M,)
    """
    M = sn.nstations

    if hasattr(sn, 'nservers') and sn.nservers is not None:
        nservers = np.asarray(sn.nservers).flatten()
        if len(nservers) == M:
            return nservers

    return np.ones(M)


def _get_scheduling(sn: NetworkStruct, station_idx: int) -> SchedStrategy:
    """
    Get scheduling strategy for a station.

    Args:
        sn: Network structure
        station_idx: Station index

    Returns:
        Scheduling strategy
    """
    if hasattr(sn, 'sched') and sn.sched is not None:
        if isinstance(sn.sched, dict):
            return sn.sched.get(station_idx, SchedStrategy.FCFS)
        elif isinstance(sn.sched, (list, np.ndarray)) and station_idx < len(sn.sched):
            return sn.sched[station_idx]

    return SchedStrategy.FCFS


def _is_delay_station(sn: NetworkStruct, station_idx: int) -> bool:
    """Check if station is a delay (infinite server) station."""
    nservers = _get_nservers(sn)
    return np.isinf(nservers[station_idx])


def _is_source_station(sn: NetworkStruct, station_idx: int) -> bool:
    """Check if station is a source."""
    sched = _get_scheduling(sn, station_idx)
    return sched == SchedStrategy.EXT


def _is_ps_station(sn: NetworkStruct, station_idx: int) -> bool:
    """Check if station uses processor sharing."""
    sched = _get_scheduling(sn, station_idx)
    return sched == SchedStrategy.PS


def _solve_fcfs_mmapph1(
    sn: NetworkStruct,
    ist: int,
    lambdas: np.ndarray,
    V: np.ndarray,
    S: np.ndarray,
    K: int,
    C: int
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Solve MMAP/PH/1/FCFS queue using matrix-analytic method.

    Args:
        sn: Network structure
        ist: Station index
        lambdas: Arrival rates per chain
        V: Visit ratios
        S: Service times
        K: Number of classes
        C: Number of chains

    Returns:
        Tuple of (QN, RN) arrays for the station, or (None, None) if not applicable
    """
    if not HAS_MMAPPH1FCFS:
        return None, None

    # Check if this is a single-server queue with PH service
    nservers = _get_nservers(sn)
    if nservers[ist] != 1:
        return None, None

    # Check if we have PH service distributions
    if not hasattr(sn, 'proc') or sn.proc is None or len(sn.proc) <= ist:
        return None, None

    proc_ist = sn.proc[ist] if ist < len(sn.proc) else None
    if proc_ist is None or not isinstance(proc_ist, (list, dict)):
        return None, None

    try:
        # Build PH service parameters (pie and D0) for each class
        pie_list = []
        D0_list = []

        for k in range(K):
            ph = proc_ist[k] if k < len(proc_ist) else None
            if ph is None:
                # Use exponential as fallback
                rate = 1.0 / S[ist, k] if S[ist, k] > 0 else 1.0
                pie_list.append(ml.matrix([[1.0]]))
                D0_list.append(ml.matrix([[-rate]]))
            elif isinstance(ph, dict):
                # Check for Erlang distribution {'k': phases, 'mu': rate_per_phase}
                if 'k' in ph and 'mu' in ph:
                    # Convert Erlang(k, mu) to PH representation
                    k_phases = int(ph['k'])
                    mu = float(ph['mu'])
                    # Initial vector: start in first phase
                    alpha = np.zeros(k_phases)
                    alpha[0] = 1.0
                    # Generator: -mu on diagonal, mu on superdiagonal
                    T = np.zeros((k_phases, k_phases))
                    for i in range(k_phases):
                        T[i, i] = -mu
                        if i < k_phases - 1:
                            T[i, i + 1] = mu
                    pie_list.append(ml.matrix(alpha.reshape(1, -1)))
                    D0_list.append(ml.matrix(T))
                elif 'rate' in ph:
                    # Simple rate-based service (exponential)
                    rate = float(ph['rate'])
                    pie_list.append(ml.matrix([[1.0]]))
                    D0_list.append(ml.matrix([[-rate]]))
                else:
                    # Unknown dict format, use exponential fallback
                    rate = 1.0 / S[ist, k] if S[ist, k] > 0 else 1.0
                    pie_list.append(ml.matrix([[1.0]]))
                    D0_list.append(ml.matrix([[-rate]]))
            elif isinstance(ph, (list, tuple)) and len(ph) >= 2:
                # PH representation [alpha, T]
                alpha = np.asarray(ph[0]).flatten()
                T = np.asarray(ph[1])
                pie_list.append(ml.matrix(alpha.reshape(1, -1)))
                D0_list.append(ml.matrix(T))
            else:
                # Fallback to exponential
                rate = 1.0 / S[ist, k] if S[ist, k] > 0 else 1.0
                pie_list.append(ml.matrix([[1.0]]))
                D0_list.append(ml.matrix([[-rate]]))

        # Build MMAP arrival process
        # Aggregate arrival rate
        total_lambda = sum(lambdas[c] * V[ist, k]
                         for c in range(C) if c in sn.inchain
                         for k in sn.inchain[c].flatten().astype(int)
                         if V[ist, k] > 0)

        if total_lambda <= 1e-10:
            return None, None

        # Build MMAP with arrivals per class
        # D0: background transitions (just diagonal rate)
        # D1, D2, ...: arrival marking for each class
        D0_mmap = ml.matrix([[-total_lambda]])
        D_list = [D0_mmap]

        # Add marking matrix for each class
        class_rates = []
        for k in range(K):
            rate_k = sum(lambdas[c] * V[ist, k]
                        for c in range(C) if c in sn.inchain
                        if k in sn.inchain[c].flatten().astype(int))
            class_rates.append(rate_k)
            D_list.append(ml.matrix([[rate_k]]))

        # Call MMAPPH1FCFS
        result = MMAPPH1FCFS(D_list, pie_list, D0_list, 'ncMoms', 1)

        # Parse result - should be list of queue lengths per class
        if result is not None:
            QN = np.zeros(K)
            RN = np.zeros(K)

            if isinstance(result, list):
                for k in range(min(len(result), K)):
                    q_k = result[k]
                    if hasattr(q_k, '__iter__'):
                        q_k = float(q_k[0]) if len(q_k) > 0 else 0.0
                    QN[k] = float(q_k) if q_k is not None else 0.0
            else:
                QN[0] = float(result) if result is not None else 0.0

            # Compute response times from Little's Law: R = Q / lambda
            for c in range(C):
                if c not in sn.inchain:
                    continue
                inchain = sn.inchain[c].flatten().astype(int)
                for k in inchain:
                    TN_k = lambdas[c] * V[ist, k]
                    if TN_k > 1e-10:
                        RN[k] = QN[k] / TN_k

            return QN, RN

    except Exception as e:
        warnings.warn(f"MMAPPH1FCFS failed: {e}")
        return None, None

    return None, None


def solver_mam_basic(
    sn: NetworkStruct,
    options: Optional[SolverMAMOptions] = None
) -> SolverMAMReturn:
    """
    Basic MAM solver using source decomposition.

    Implements basic matrix-analytic decomposition for queueing networks.
    Port of MATLAB solver_mam_basic.m

    Args:
        sn: Network structure
        options: Solver options

    Returns:
        SolverMAMReturn with performance metrics
    """
    start_time = time.time()

    if options is None:
        options = SolverMAMOptions()

    tol = options.tol
    FINE_TOL = 1e-8

    M = sn.nstations
    K = sn.nclasses
    C = sn.nchains
    N = sn.njobs.flatten() if sn.njobs is not None else np.zeros(K)

    # Get network parameters
    V = _get_visits(sn)
    S = _get_service_times(sn)
    nservers = _get_nservers(sn)

    # Get chain-level demands
    demands_result = sn_get_demands_chain(sn)
    Lchain = demands_result.Lchain

    # Initialize result matrices
    QN = np.zeros((M, K))
    UN = np.zeros((M, K))
    RN = np.zeros((M, K))
    TN = np.zeros((M, K))
    CN = np.zeros((1, K))
    XN = np.zeros((1, K))

    # Check model type
    is_open = sn_is_open_model(sn)
    is_closed = sn_is_closed_model(sn)
    is_mixed = is_open and is_closed

    if is_mixed:
        raise RuntimeError("SolverMAM does not support mixed models with both open and closed classes.")

    # Initialize lambda (arrival rate per chain)
    lambdas = np.zeros(C)

    # Get arrival rates for open chains and initial estimates for closed chains
    for c in range(C):
        if c not in sn.inchain:
            continue
        inchain = sn.inchain[c].flatten().astype(int)

        # Check if chain is open
        is_open_chain = np.any(np.isinf(N[inchain]))

        if is_open_chain:
            # Open chain: get arrival rate from source (refstat)
            refstat_c = int(sn.refstat.flatten()[inchain[0]]) if sn.refstat is not None else 0

            if hasattr(sn, 'rates') and sn.rates is not None:
                rates_at_source = sn.rates[refstat_c, inchain]
                finite_rates = rates_at_source[np.isfinite(rates_at_source)]
                lambdas[c] = np.sum(finite_rates) if len(finite_rates) > 0 else 0.0
        else:
            # Closed chain: initialize with lower bound (N_c / sum(Lchain[:, c]))
            Nc = np.sum(N[inchain])
            Lchain_sum = np.sum(Lchain[:, c])
            if Lchain_sum > FINE_TOL:
                lambdas[c] = Nc / Lchain_sum
            else:
                lambdas[c] = 1.0

    # For open chains, set throughputs at source
    for c in range(C):
        if c not in sn.inchain:
            continue
        inchain = sn.inchain[c].flatten().astype(int)
        is_open_chain = np.any(np.isinf(N[inchain]))

        if is_open_chain:
            refstat_c = int(sn.refstat.flatten()[inchain[0]]) if sn.refstat is not None else 0
            if hasattr(sn, 'rates') and sn.rates is not None:
                TN[refstat_c, inchain] = sn.rates[refstat_c, inchain]

    # Identify stations with finite servers (for utilization check)
    sd = np.isfinite(nservers)

    # Main iteration loop
    TN_prev = TN.copy() + np.inf
    it = 0

    while np.max(np.abs(TN - TN_prev)) > tol and it <= options.iter_max:
        it += 1
        TN_prev = TN.copy()

        # Check utilization bound
        Umax = np.max(np.sum(UN[sd, :], axis=1)) if np.any(sd) else 0.0
        if Umax >= 1.0:
            lambdas = lambdas / Umax  # MATLAB: lambda = lambda * 1/Umax
        else:
            # Adjust lambda for closed chains based on queue lengths
            for c in range(C):
                if c not in sn.inchain:
                    continue
                inchain = sn.inchain[c].flatten().astype(int)
                is_open_chain = np.any(np.isinf(N[inchain]))

                if not is_open_chain:
                    Nc = np.sum(N[inchain])
                    QNc = max(tol, np.sum(QN[:, inchain]))
                    TNlb = Nc / max(FINE_TOL, np.sum(Lchain[:, c]))

                    if it == 1:
                        lambdas[c] = TNlb
                    else:
                        # Regula falsi iteration (iteration-averaged)
                        alpha = it / options.iter_max
                        lambdas[c] = lambdas[c] * alpha + (Nc / QNc) * lambdas[c] * (1 - alpha)

        # Update throughputs: TN[m, k] = V[m, k] * lambda[c] for k in chain c
        for c in range(C):
            if c not in sn.inchain:
                continue
            inchain = sn.inchain[c].flatten().astype(int)
            for m in range(M):
                TN[m, inchain] = V[m, inchain] * lambdas[c]

        # Compute metrics for each station
        for ist in range(M):
            if _is_source_station(sn, ist):
                # Source station: throughput equals arrival rate, no queue
                for c in range(C):
                    if c not in sn.inchain:
                        continue
                    inchain = sn.inchain[c].flatten().astype(int)
                    is_open_chain = np.any(np.isinf(N[inchain]))
                    if is_open_chain and sn.rates is not None:
                        TN[ist, inchain] = sn.rates[ist, inchain]
                QN[ist, :] = 0.0
                UN[ist, :] = 0.0
                RN[ist, :] = 0.0
                continue

            if _is_delay_station(sn, ist):
                # Delay station (infinite server)
                # MATLAB: TN = lambda*V, UN = S*TN, QN = TN*S*V, RN = QN/TN
                for c in range(C):
                    if c not in sn.inchain:
                        continue
                    inchain = sn.inchain[c].flatten().astype(int)
                    for k in inchain:
                        TN[ist, k] = lambdas[c] * V[ist, k]
                        UN[ist, k] = S[ist, k] * TN[ist, k]
                        QN[ist, k] = TN[ist, k] * S[ist, k] * V[ist, k]
                        RN[ist, k] = QN[ist, k] / TN[ist, k] if TN[ist, k] > FINE_TOL else 0.0

            elif _is_ps_station(sn, ist):
                # Processor Sharing station
                # MATLAB: TN = lambda*V, UN = S*TN, QN = UN/(1-Usum)
                for c in range(C):
                    if c not in sn.inchain:
                        continue
                    inchain = sn.inchain[c].flatten().astype(int)
                    for k in inchain:
                        TN[ist, k] = lambdas[c] * V[ist, k]
                        UN[ist, k] = S[ist, k] * TN[ist, k]

                # Compute queue lengths using PS formula
                Uden = min(1.0 - FINE_TOL, np.sum(UN[ist, :]))
                for c in range(C):
                    if c not in sn.inchain:
                        continue
                    inchain = sn.inchain[c].flatten().astype(int)
                    for k in inchain:
                        if Uden < 1.0 - FINE_TOL:
                            QN[ist, k] = UN[ist, k] / (1.0 - Uden)
                        else:
                            QN[ist, k] = N[k] if np.isfinite(N[k]) else UN[ist, k]
                        RN[ist, k] = QN[ist, k] / TN[ist, k] if TN[ist, k] > FINE_TOL else 0.0

            else:
                # FCFS or other queue
                # MATLAB: TN = lambda*V, UN = S*TN/nservers
                for c in range(C):
                    if c not in sn.inchain:
                        continue
                    inchain = sn.inchain[c].flatten().astype(int)
                    for k in inchain:
                        TN[ist, k] = lambdas[c] * V[ist, k]
                        UN[ist, k] = S[ist, k] * TN[ist, k] / nservers[ist]

                # Try to use MMAPPH1FCFS for accurate MMAP/PH/1/FCFS analysis
                aggr_util = np.sum(UN[ist, :])
                mmapph1_success = False

                if aggr_util < 1.0 - FINE_TOL and np.any(np.isinf(N)):
                    # Try MMAPPH1FCFS for open classes
                    QN_mmap, RN_mmap = _solve_fcfs_mmapph1(sn, ist, lambdas, V, S, K, C)
                    if QN_mmap is not None:
                        QN[ist, :] = QN_mmap
                        RN[ist, :] = RN_mmap
                        mmapph1_success = True

                if not mmapph1_success:
                    # Fallback: approximate queue lengths using M/M/c formula
                    if aggr_util < 1.0 - FINE_TOL:
                        for c in range(C):
                            if c not in sn.inchain:
                                continue
                            inchain = sn.inchain[c].flatten().astype(int)
                            for k in inchain:
                                # Simplified M/M/c approximation
                                QN[ist, k] = UN[ist, k] / (1.0 - aggr_util)
                                # Add surrogate delay for multiserver
                                QN[ist, k] += TN[ist, k] * S[ist, k] * (nservers[ist] - 1) / nservers[ist]
                                RN[ist, k] = QN[ist, k] / TN[ist, k] if TN[ist, k] > FINE_TOL else 0.0
                    else:
                        # Saturated queue
                        for c in range(C):
                            if c not in sn.inchain:
                                continue
                            inchain = sn.inchain[c].flatten().astype(int)
                            for k in inchain:
                                QN[ist, k] = N[k] if np.isfinite(N[k]) else UN[ist, k]
                                RN[ist, k] = QN[ist, k] / TN[ist, k] if TN[ist, k] > FINE_TOL else 0.0

    totiter = it + 2

    # Compute cycle times
    CN = np.sum(RN, axis=0).reshape(1, -1)
    QN = np.abs(QN)

    # Second pass: renormalize queue lengths to match population (MATLAB lines 338-377)
    for _ in range(2):
        for c in range(C):
            if c not in sn.inchain:
                continue
            inchain = sn.inchain[c].flatten().astype(int)
            Nc = np.sum(N[inchain])

            if np.isfinite(Nc) and Nc > 0:
                QNc = np.sum(QN[:, inchain])
                if QNc > FINE_TOL:
                    ratio = Nc / QNc
                    QN[:, inchain] = QN[:, inchain] * ratio

            # Recompute response times
            for ist in range(M):
                # Skip source stations - they have no queue (Q=0, R=0)
                if _is_source_station(sn, ist):
                    continue
                for k in inchain:
                    if V[ist, k] > 0:
                        if _is_delay_station(sn, ist):
                            RN[ist, k] = S[ist, k]
                        else:
                            RN[ist, k] = max(S[ist, k], QN[ist, k] / TN[ist, k]) if TN[ist, k] > FINE_TOL else 0.0
                    else:
                        RN[ist, k] = 0.0
                    QN[ist, k] = RN[ist, k] * TN[ist, k]

            # Handle zero population chains
            if Nc == 0:
                QN[:, inchain] = 0.0
                UN[:, inchain] = 0.0
                RN[:, inchain] = 0.0
                TN[:, inchain] = 0.0

    # Set system throughputs
    for c in range(C):
        if c not in sn.inchain:
            continue
        inchain = sn.inchain[c].flatten().astype(int)
        XN[0, inchain] = lambdas[c]

    # Clean up NaN values
    QN = np.nan_to_num(QN, nan=0.0)
    UN = np.nan_to_num(UN, nan=0.0)
    RN = np.nan_to_num(RN, nan=0.0)
    TN = np.nan_to_num(TN, nan=0.0)
    CN = np.nan_to_num(CN, nan=0.0)
    XN = np.nan_to_num(XN, nan=0.0)

    result = SolverMAMReturn()
    result.Q = QN
    result.U = UN
    result.R = RN
    result.T = TN
    result.C = CN
    result.X = XN
    result.A = TN.copy()
    result.W = RN.copy()
    result.runtime = time.time() - start_time
    result.method = "dec.source"
    result.it = totiter

    return result


def solver_mam(
    sn: NetworkStruct,
    options: Optional[SolverMAMOptions] = None
) -> SolverMAMReturn:
    """
    Main MAM solver handler.

    Routes to appropriate method based on options and network characteristics.

    Args:
        sn: Network structure
        options: Solver options

    Returns:
        SolverMAMReturn with performance metrics
    """
    if options is None:
        options = SolverMAMOptions()

    method = options.method.lower()

    if method in ['default', 'dec.source', 'dec.poisson']:
        # Use basic decomposition method
        if method == 'dec.poisson':
            options.space_max = 1
        return solver_mam_basic(sn, options)
    elif method == 'dec.mmap':
        # MMAP decomposition - use basic for now
        return solver_mam_basic(sn, options)
    elif method in ['mna', 'inap', 'exact']:
        # Matrix-analytic / RCAT methods - use basic for now
        return solver_mam_basic(sn, options)
    else:
        # Unknown method - use basic
        if options.verbose:
            print(f"Warning: Unknown MAM method '{method}'. Using dec.source.")
        return solver_mam_basic(sn, options)


__all__ = [
    'solver_mam',
    'solver_mam_basic',
    'SolverMAMReturn',
    'SolverMAMOptions',
]
