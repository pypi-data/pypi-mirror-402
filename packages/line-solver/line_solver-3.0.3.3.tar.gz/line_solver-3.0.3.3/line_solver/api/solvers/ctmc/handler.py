"""
CTMC Solver handler.

Native Python implementation of CTMC (Continuous-Time Markov Chain) solver
handler that analyzes queueing networks through exact state-space enumeration.

The CTMC solver builds the complete state space and infinitesimal generator
matrix, then solves for steady-state probabilities to compute performance metrics.

Port from:

"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple, Any
from itertools import product
import time

import warnings
from ...sn import (
    NetworkStruct,
    SchedStrategy,
    NodeType,
    RoutingStrategy,
    sn_is_open_model,
    sn_is_closed_model,
    sn_has_open_classes,
)
from ....constants import ProcessType
from ...mc import ctmc_solve, ctmc_makeinfgen


def _get_phases_info(sn: NetworkStruct) -> Tuple[np.ndarray, bool]:
    """
    Get number of phases for each (station, class) pair and detect if phase augmentation is needed.

    For phase-type distributions (PH, APH, MAP, MMPP2, Erlang, HyperExp, Coxian),
    the number of phases is determined from the distribution parameters stored in sn.proc.

    Args:
        sn: Network structure

    Returns:
        Tuple of (phases matrix [M x K], needs_phase_augmentation bool)
    """
    M = sn.nstations
    K = sn.nclasses
    phases = np.ones((M, K), dtype=int)
    needs_augmentation = False

    if not hasattr(sn, 'proc') or sn.proc is None:
        return phases, needs_augmentation

    # sn.proc can be a list or dict - handle both
    proc_is_list = isinstance(sn.proc, list)

    for ist in range(M):
        # Check if this station has proc data
        if proc_is_list:
            if ist >= len(sn.proc) or sn.proc[ist] is None:
                continue
            station_proc = sn.proc[ist]
        else:
            if ist not in sn.proc:
                continue
            station_proc = sn.proc[ist]

        for k in range(K):
            # Get proc entry for this (station, class)
            proc_entry = None
            if isinstance(station_proc, (list, tuple)):
                if k < len(station_proc):
                    proc_entry = station_proc[k]
            elif isinstance(station_proc, dict):
                proc_entry = station_proc.get(k)

            if proc_entry is None:
                continue

            n_phases = 1

            # Handle different storage formats
            if isinstance(proc_entry, dict):
                # Erlang: {'k': phases, 'mu': rate}
                if 'k' in proc_entry:
                    n_phases = int(proc_entry['k'])
                # HyperExp: {'probs': [...], 'rates': [...]}
                elif 'probs' in proc_entry and 'rates' in proc_entry:
                    probs = np.array(proc_entry['probs'])
                    proc_rates = np.array(proc_entry['rates'])
                    # Check if rates data is valid (not same as probs)
                    # If rates == probs, this indicates a data bug - treat as single phase
                    if np.allclose(proc_rates, probs):
                        n_phases = 1
                    else:
                        n_phases = len(proc_entry['probs'])
                # Exp: {'rate': ...} - single phase
                else:
                    n_phases = 1
            elif isinstance(proc_entry, (list, tuple)) and len(proc_entry) >= 1:
                # PH/APH/MAP: [alpha/D0, T/D1] where alpha/D0 determines phases
                first_elem = proc_entry[0]
                if isinstance(first_elem, np.ndarray):
                    if first_elem.ndim == 1:
                        # alpha vector
                        n_phases = len(first_elem)
                    else:
                        # D0 matrix
                        n_phases = first_elem.shape[0]
                elif isinstance(first_elem, (list, tuple)):
                    if len(first_elem) > 0 and isinstance(first_elem[0], (list, tuple, np.ndarray)):
                        # 2D structure
                        n_phases = len(first_elem)
                    else:
                        # 1D structure
                        n_phases = len(first_elem)

            phases[ist, k] = max(1, n_phases)
            if n_phases > 1:
                needs_augmentation = True

    return phases, needs_augmentation


def _get_map_fcfs_info(sn: NetworkStruct) -> Tuple[Dict[Tuple[int, int], int], bool]:
    """
    Identify (station, class) pairs that have MAP distributions at FCFS stations.

    For FCFS stations with MAP distributions, the state must include an additional
    variable tracking the MAP modulating phase (the "mode" of the MAP process).

    Args:
        sn: Network structure

    Returns:
        Tuple of (map_fcfs dict mapping (ist, k) to n_phases, has_map_fcfs bool)
    """
    M = sn.nstations
    K = sn.nclasses
    map_fcfs = {}  # (ist, k) -> n_phases for MAP distributions at FCFS stations
    has_map_fcfs = False

    if not hasattr(sn, 'proc') or sn.proc is None:
        return map_fcfs, has_map_fcfs
    if not hasattr(sn, 'sched') or sn.sched is None:
        return map_fcfs, has_map_fcfs
    if not hasattr(sn, 'procid') or sn.procid is None:
        return map_fcfs, has_map_fcfs

    proc_is_list = isinstance(sn.proc, list)

    for ist in range(M):
        # Check if this is an FCFS station
        sched = sn.sched.get(ist, SchedStrategy.FCFS)
        # FCFS variants that need MAP phase tracking
        fcfs_variants = [SchedStrategy.FCFS, SchedStrategy.HOL, SchedStrategy.LCFS, SchedStrategy.LCFSPR]
        # Check for specific FCFS scheduling strategies
        is_fcfs_type = (sched in fcfs_variants or
                       (isinstance(sched, int) and sched in [1, 2, 3]))  # FCFS=1, LCFS=2, etc.

        if not is_fcfs_type:
            continue

        # Check if this station has proc data
        if proc_is_list:
            if ist >= len(sn.proc) or sn.proc[ist] is None:
                continue
            station_proc = sn.proc[ist]
        else:
            if ist not in sn.proc:
                continue
            station_proc = sn.proc[ist]

        for k in range(K):
            # Check process type
            if ist >= sn.procid.shape[0] or k >= sn.procid.shape[1]:
                continue
            procid = sn.procid[ist, k]

            # Check if MAP or MMPP2
            if procid not in [ProcessType.MAP, ProcessType.MMPP2]:
                continue

            # Get number of phases from proc entry
            proc_entry = None
            if isinstance(station_proc, (list, tuple)):
                if k < len(station_proc):
                    proc_entry = station_proc[k]
            elif isinstance(station_proc, dict):
                proc_entry = station_proc.get(k)

            if proc_entry is None:
                continue

            n_phases = 1
            if isinstance(proc_entry, (list, tuple)) and len(proc_entry) >= 2:
                # MAP: [D0, D1]
                D0 = np.atleast_2d(np.array(proc_entry[0], dtype=float))
                n_phases = D0.shape[0]

            if n_phases > 1:
                map_fcfs[(ist, k)] = n_phases
                has_map_fcfs = True

    return map_fcfs, has_map_fcfs


def _generate_phase_distributions(n_jobs: int, n_phases: int) -> List[Tuple[int, ...]]:
    """
    Generate all ways to distribute n_jobs across n_phases.

    This is equivalent to MATLAB's State.spaceClosedSingle.

    Args:
        n_jobs: Number of jobs to distribute
        n_phases: Number of phases

    Returns:
        List of tuples, each tuple has n_phases elements summing to n_jobs
    """
    if n_phases == 1:
        return [(n_jobs,)]
    if n_jobs == 0:
        return [tuple([0] * n_phases)]

    result = []
    for k in range(n_jobs + 1):
        # k jobs in first phase, rest in remaining phases
        for rest in _generate_phase_distributions(n_jobs - k, n_phases - 1):
            result.append((k,) + rest)
    return result


def _get_phase_transition_params(sn: NetworkStruct, ist: int, k: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Get phase transition parameters for a (station, class) pair.

    For PH/APH distributions: Returns (mu, phi, alpha) where
        - mu[i] = service rate in phase i
        - phi[i] = probability of completion from phase i (vs moving to another phase)
        - alpha[i] = initial probability of starting in phase i

    For MAP distributions: Returns (D0, D1, pi) where
        - D0 = transition matrix without completions
        - D1 = transition matrix with completions
        - pi = stationary distribution (initial phases)

    Args:
        sn: Network structure
        ist: Station index
        k: Class index

    Returns:
        For PH/APH: (mu, phi, alpha)
        For MAP: (D0, D1, pi)
    """
    if not hasattr(sn, 'proc') or sn.proc is None:
        return np.array([1.0]), np.array([1.0]), np.array([1.0])

    # Handle both list and dict formats for sn.proc
    proc_is_list = isinstance(sn.proc, list)
    if proc_is_list:
        if ist >= len(sn.proc) or sn.proc[ist] is None:
            rate = sn.rates[ist, k] if hasattr(sn, 'rates') and ist < sn.rates.shape[0] and k < sn.rates.shape[1] else 1.0
            return np.array([rate]), np.array([1.0]), np.array([1.0])
        station_proc = sn.proc[ist]
    else:
        if ist not in sn.proc or sn.proc[ist] is None:
            rate = sn.rates[ist, k] if hasattr(sn, 'rates') and ist < sn.rates.shape[0] and k < sn.rates.shape[1] else 1.0
            return np.array([rate]), np.array([1.0]), np.array([1.0])
        station_proc = sn.proc[ist]

    # Get proc entry for this class
    if isinstance(station_proc, (list, tuple)):
        if k >= len(station_proc) or station_proc[k] is None:
            rate = sn.rates[ist, k] if hasattr(sn, 'rates') and ist < sn.rates.shape[0] and k < sn.rates.shape[1] else 1.0
            return np.array([rate]), np.array([1.0]), np.array([1.0])
        proc_entry = station_proc[k]
    elif isinstance(station_proc, dict):
        if k not in station_proc or station_proc[k] is None:
            rate = sn.rates[ist, k] if hasattr(sn, 'rates') and ist < sn.rates.shape[0] and k < sn.rates.shape[1] else 1.0
            return np.array([rate]), np.array([1.0]), np.array([1.0])
        proc_entry = station_proc[k]
    else:
        rate = sn.rates[ist, k] if hasattr(sn, 'rates') and ist < sn.rates.shape[0] and k < sn.rates.shape[1] else 1.0
        return np.array([rate]), np.array([1.0]), np.array([1.0])

    # Check process type
    procid = None
    if hasattr(sn, 'procid') and sn.procid is not None:
        if ist < sn.procid.shape[0] and k < sn.procid.shape[1]:
            procid = sn.procid[ist, k]

    # Handle different distribution types
    if isinstance(proc_entry, dict):
        # Erlang: {'k': phases, 'mu': rate}
        if 'k' in proc_entry:
            n_phases = int(proc_entry['k'])
            rate = proc_entry.get('mu', 1.0)
            mu = np.full(n_phases, rate)
            phi = np.concatenate([np.zeros(n_phases - 1), [1.0]])  # Only complete from last phase
            alpha = np.zeros(n_phases)
            alpha[0] = 1.0  # Start in first phase
            return mu, phi, alpha
        # HyperExp: {'probs': [...], 'rates': [...]}
        elif 'probs' in proc_entry and 'rates' in proc_entry:
            probs = np.array(proc_entry['probs'])
            proc_rates = np.array(proc_entry['rates'])
            # Check if rates data is valid (not same as probs)
            # If rates == probs, this indicates a data bug - fall back to single-phase
            if np.allclose(proc_rates, probs):
                rate = sn.rates[ist, k] if hasattr(sn, 'rates') and ist < sn.rates.shape[0] and k < sn.rates.shape[1] else 1.0
                return np.array([rate]), np.array([1.0]), np.array([1.0])
            phi = np.ones(len(proc_rates))  # Each phase completes immediately
            return proc_rates, phi, probs
        # Exp: {'rate': ...}
        else:
            rate = proc_entry.get('rate', 1.0)
            return np.array([rate]), np.array([1.0]), np.array([1.0])

    elif isinstance(proc_entry, (list, tuple)) and len(proc_entry) >= 2:
        # PH/APH: [alpha, T]
        # MAP: [D0, D1]
        first = np.atleast_1d(np.array(proc_entry[0], dtype=float))
        second = np.atleast_2d(np.array(proc_entry[1], dtype=float))

        is_map = procid in [ProcessType.MAP, ProcessType.MMPP2] if procid is not None else False

        if is_map or (first.ndim == 2):
            # MAP: [D0, D1]
            D0 = np.atleast_2d(first)
            D1 = second
            # Compute stationary distribution
            Q = D0 + D1
            n = Q.shape[0]
            A = np.vstack([Q.T, np.ones(n)])
            b = np.zeros(n + 1)
            b[-1] = 1.0
            try:
                from scipy import linalg
                pi, _, _, _ = linalg.lstsq(A, b)
                pi = np.maximum(pi, 0)
                pi /= pi.sum() if pi.sum() > 0 else 1
            except:
                pi = np.ones(n) / n
            return D0, D1, pi
        else:
            # PH/APH: [alpha, T]
            alpha = first.flatten()
            T = second
            n_phases = len(alpha)

            # Extract service rates (negative diagonal of T)
            mu = -np.diag(T)

            # Compute exit rates (completion probability)
            exit_rates = -T.sum(axis=1)  # -T * e gives exit rates
            phi = np.zeros(n_phases)
            for i in range(n_phases):
                if mu[i] > 0:
                    phi[i] = exit_rates[i] / mu[i]

            return mu, phi, alpha

    # Default: exponential
    rate = sn.rates[ist, k] if hasattr(sn, 'rates') and ist < sn.rates.shape[0] and k < sn.rates.shape[1] else 1.0
    return np.array([rate]), np.array([1.0]), np.array([1.0])


def _ctmc_stochcomp(Q: np.ndarray, keep_indices: List[int]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Perform stochastic complementation to remove immediate states.

    This removes states where jobs are at non-station stateful nodes
    (like Router) by computing the equivalent transitions that bypass
    these nodes.

    Args:
        Q: Full infinitesimal generator matrix
        keep_indices: Indices of states to keep (non-immediate states)

    Returns:
        Tuple of (reduced Q matrix, transformation matrix for rates)
    """
    n = Q.shape[0]
    all_indices = set(range(n))
    remove_indices = sorted(all_indices - set(keep_indices))

    if not remove_indices:
        return Q, np.eye(n)

    keep_indices = sorted(keep_indices)

    # Partition Q into blocks:
    # Q = [Q11 Q12]  where 1 = keep, 2 = remove
    #     [Q21 Q22]
    Q11 = Q[np.ix_(keep_indices, keep_indices)]
    Q12 = Q[np.ix_(keep_indices, remove_indices)]
    Q21 = Q[np.ix_(remove_indices, keep_indices)]
    Q22 = Q[np.ix_(remove_indices, remove_indices)]

    # Stochastic complement: Q_reduced = Q11 + Q12 * (-Q22)^{-1} * Q21
    # For immediate transitions, Q22 should be invertible
    try:
        # Add small regularization for numerical stability
        Q22_inv = np.linalg.inv(-Q22 + np.eye(len(remove_indices)) * 1e-10)
        Q_reduced = Q11 + Q12 @ Q22_inv @ Q21
    except np.linalg.LinAlgError:
        # Fallback: just return the kept states without complementation
        Q_reduced = Q11

    # Make it a valid generator
    Q_reduced = ctmc_makeinfgen(Q_reduced)

    return Q_reduced, Q12 @ Q22_inv if len(remove_indices) > 0 else np.eye(len(keep_indices))


def _get_rrobin_outlinks(sn: NetworkStruct) -> dict:
    """
    Get outlinks for nodes with RROBIN/WRROBIN routing.

    Returns a dict: {(node_idx, class_idx): [outlink_node_indices]}
    """
    outlinks = {}

    if not hasattr(sn, 'routing') or sn.routing is None:
        return outlinks
    if not hasattr(sn, 'connmatrix') or sn.connmatrix is None:
        return outlinks

    routing = np.asarray(sn.routing)
    connmatrix = np.asarray(sn.connmatrix)

    N = routing.shape[0]  # Number of nodes
    K = routing.shape[1]  # Number of classes

    for ind in range(N):
        for r in range(K):
            strategy = routing[ind, r]
            # Check for RROBIN (3) or WRROBIN (4)
            if strategy == 3 or strategy == 4:  # RROBIN or WRROBIN
                # Get outgoing links from connection matrix
                links = np.where(connmatrix[ind, :] > 0)[0].tolist()
                if links:
                    outlinks[(ind, r)] = links

    return outlinks


def _build_rrobin_state_info(sn: NetworkStruct) -> dict:
    """
    Build information about round-robin state variables.

    Returns a dict with:
        'outlinks': {(node_idx, class_idx): [outlink_indices]}
        'state_vars': List of (node_idx, class_idx, num_outlinks) tuples
        'total_vars': Total number of extra state variables
        'non_station_stateful': Set of node indices that are stateful but not stations
    """
    outlinks = _get_rrobin_outlinks(sn)

    state_vars = []
    for (node_idx, class_idx), links in sorted(outlinks.items()):
        state_vars.append((node_idx, class_idx, len(links)))

    # Identify non-station stateful nodes (like Router)
    non_station_stateful = set()
    if hasattr(sn, 'isstation') and hasattr(sn, 'isstateful'):
        isstation = np.asarray(sn.isstation).flatten()
        isstateful = np.asarray(sn.isstateful).flatten()
        for i in range(len(isstation)):
            if isstateful[i] and not isstation[i]:
                non_station_stateful.add(i)

    return {
        'outlinks': outlinks,
        'state_vars': state_vars,
        'total_vars': len(state_vars),
        'non_station_stateful': non_station_stateful
    }


def _resolve_routing_through_non_stations(
    sn: NetworkStruct,
    src_node: int,
    dst_node: int,
    job_class: int,
    rrobin_info: dict,
    state: np.ndarray,
    rr_var_map: dict,
    M: int,
    K: int
) -> Tuple[int, int, np.ndarray]:
    """
    Resolve routing through non-station stateful nodes.

    When a job routes to a non-station node (like Router) with RROBIN,
    this function finds the final station destination and updates the
    RR pointer.

    Args:
        sn: Network structure
        src_node: Source node index
        dst_node: Destination node index (may be non-station)
        job_class: Job class index
        rrobin_info: Round-robin routing info
        state: Current state vector
        rr_var_map: Map from (node, class) to state variable index
        M: Number of stations
        K: Number of classes

    Returns:
        Tuple of (final_node, final_station, updated_state)
        Returns (-1, -1, state) if destination is a sink or invalid
    """
    non_station_stateful = rrobin_info['non_station_stateful']
    outlinks = rrobin_info['outlinks']

    # Get node to station mapping
    node_to_station = None
    if hasattr(sn, 'nodeToStation') and sn.nodeToStation is not None:
        node_to_station = np.asarray(sn.nodeToStation).flatten()

    current_node = dst_node
    new_state = state.copy()
    max_hops = 10  # Prevent infinite loops

    for _ in range(max_hops):
        # Check if current node is a station
        if node_to_station is not None and current_node < len(node_to_station):
            station_idx = int(node_to_station[current_node])
            if station_idx >= 0:
                return current_node, station_idx, new_state

        # Current node is not a station - check if it's a non-station stateful node
        if current_node not in non_station_stateful:
            # Node is neither station nor stateful (e.g., Sink)
            return -1, -1, new_state

        # It's a non-station stateful node - check for RROBIN routing
        if (current_node, job_class) in outlinks:
            # Apply RROBIN routing
            links = outlinks[(current_node, job_class)]
            rr_var_idx = rr_var_map.get((current_node, job_class))
            if rr_var_idx is not None:
                current_rr_ptr = int(new_state[rr_var_idx])
                next_node = links[current_rr_ptr]
                # Advance RR pointer
                new_state[rr_var_idx] = (current_rr_ptr + 1) % len(links)
                current_node = next_node
            else:
                # No RR state variable - use first outlink
                current_node = links[0]
        else:
            # No RROBIN - use connection matrix to find next node
            if hasattr(sn, 'connmatrix') and sn.connmatrix is not None:
                conn = np.asarray(sn.connmatrix)
                next_nodes = np.where(conn[current_node, :] > 0)[0]
                if len(next_nodes) > 0:
                    current_node = next_nodes[0]
                else:
                    return -1, -1, new_state
            else:
                return -1, -1, new_state

    # Max hops exceeded
    return -1, -1, new_state


@dataclass
class SolverCTMCOptions:
    """Options for CTMC solver."""
    method: str = 'default'
    tol: float = 1e-6
    verbose: bool = False
    cutoff: int = 10  # Cutoff for open class populations
    hide_immediate: bool = True  # Hide immediate transitions
    state_space_gen: str = 'default'  # 'default', 'full', 'reachable'


@dataclass
class SolverCTMCReturn:
    """
    Result of CTMC solver handler.

    Attributes:
        Q: Mean queue lengths (M x K)
        U: Utilizations (M x K)
        R: Response times (M x K)
        T: Throughputs (M x K)
        C: Cycle times (1 x K)
        X: System throughputs (1 x K)
        pi: Steady-state distribution
        infgen: Infinitesimal generator matrix
        space: State space matrix
        station_col_ranges: List of (start, end) tuples for each station's columns in state space
        runtime: Runtime in seconds
        method: Method used
    """
    Q: Optional[np.ndarray] = None
    U: Optional[np.ndarray] = None
    R: Optional[np.ndarray] = None
    T: Optional[np.ndarray] = None
    C: Optional[np.ndarray] = None
    X: Optional[np.ndarray] = None
    pi: Optional[np.ndarray] = None
    infgen: Optional[np.ndarray] = None
    space: Optional[np.ndarray] = None
    station_col_ranges: Optional[List[Tuple[int, int]]] = None
    runtime: float = 0.0
    method: str = "default"


def _normalize_sched_strategy(sched_val) -> str:
    """
    Normalize a scheduling strategy value to its name string.

    This handles the case where sched_val might come from different
    SchedStrategy enum definitions (constants.py vs network_struct.py).

    Args:
        sched_val: A SchedStrategy enum value or its name

    Returns:
        The strategy name as a string (e.g., 'FCFS', 'LCFS')
    """
    if hasattr(sched_val, 'name'):
        return sched_val.name
    return str(sched_val)


def _sched_is(sched_val, *names) -> bool:
    """
    Check if a scheduling strategy matches any of the given names.

    This handles the case where sched_val might come from different
    SchedStrategy enum definitions.

    Args:
        sched_val: A SchedStrategy enum value
        *names: One or more strategy names to check (e.g., 'LCFS', 'LCFSPR')

    Returns:
        True if sched_val matches any of the given names
    """
    sched_name = _normalize_sched_strategy(sched_val)
    return sched_name in names


def _get_fcfs_stations(sn: NetworkStruct) -> set:
    """
    Identify stations using FCFS-like scheduling (buffer-based state representation).

    This includes FCFS, HOL, and LCFS scheduling strategies, which use explicit
    buffer ordering (sequence of class IDs) in the CTMC state representation.

    Note: SIRO uses a different buffer structure (job counts per class, not sequence),
    so it is NOT included here. SIRO is handled like PS for state enumeration.

    Returns:
        Set of station indices using FCFS-like scheduling.
    """
    fcfs_stations = set()
    # Scheduling strategies that use buffer ordering (sequence of class IDs)
    # SIRO is excluded because it stores counts per class, not a sequence
    # Use name strings for comparison to handle different enum definitions
    buffer_order_names = {'FCFS', 'HOL', 'LCFS', 'LCFSPR'}
    if hasattr(sn, 'sched') and sn.sched is not None:
        for ist, sched_val in sn.sched.items():
            sched_name = _normalize_sched_strategy(sched_val)
            if sched_name in buffer_order_names:
                fcfs_stations.add(ist)
    return fcfs_stations


def _get_siro_stations(sn: NetworkStruct) -> set:
    """
    Identify stations using SIRO scheduling (count-based buffer representation).

    SIRO uses an unordered buffer where we track job counts per class, not the
    sequence of jobs. This is different from FCFS/HOL/LCFS which use ordered buffers.

    Returns:
        Set of station indices using SIRO scheduling.
    """
    siro_stations = set()
    # Scheduling strategies that use count-based buffer (per-class job counts)
    # Only SIRO is commonly used; LEPT/SEPT/SRPT are less common and may not be defined
    # Use name strings for comparison to handle different enum definitions
    siro_names = {'SIRO'}
    if hasattr(sn, 'sched') and sn.sched is not None:
        for ist, sched_val in sn.sched.items():
            sched_name = _normalize_sched_strategy(sched_val)
            if sched_name in siro_names:
                siro_stations.add(ist)
    return siro_stations


def _generate_fcfs_buffer_orderings(n: np.ndarray, S: int, K: int) -> List[Tuple[Tuple[int, ...], np.ndarray]]:
    """
    Generate all unique buffer orderings for FCFS state enumeration.

    For FCFS with n[k] jobs of class k and S servers, generate all unique
    permutations of job classes in the buffer/server.

    Args:
        n: Array of job counts per class (length K)
        S: Number of servers
        K: Number of classes

    Returns:
        List of (all_positions, jobs_in_service_per_class) tuples
        - all_positions: tuple of class IDs (1-based) for ALL jobs (buffer + service)
          The rightmost S positions are the jobs in service (MATLAB FCFS format)
        - jobs_in_service_per_class: array[K] with count of each class in service
    """
    from itertools import permutations

    total_jobs = int(sum(n))
    if total_jobs == 0:
        # Empty queue: no buffer, no jobs in service
        return [(tuple(), np.zeros(K, dtype=int))]

    # Build list of job classes with repetition (1-based class IDs)
    # MATLAB uses standard encoding: class k (0-based) -> marker (k + 1)
    # e.g., K=2, n=[2,0] -> vi=[1,1] (class 0 -> marker 1)
    # e.g., K=2, n=[0,2] -> vi=[2,2] (class 1 -> marker 2)
    vi = []
    for k in range(K):
        vi.extend([k + 1] * int(n[k]))  # 1-based class IDs

    # Generate all unique permutations
    unique_perms = list(set(permutations(vi)))

    result = []
    for perm in unique_perms:
        # Last S jobs are in service, rest are in buffer
        num_in_service = min(total_jobs, S)
        num_in_buffer = total_jobs - num_in_service

        # Return ALL positions (buffer + service) - MATLAB format
        # The rightmost positions are in service
        all_positions = perm  # Full permutation includes all jobs

        # Count jobs of each class in service (last S positions)
        jobs_in_service = np.zeros(K, dtype=int)
        for class_id in perm[num_in_buffer:]:
            jobs_in_service[int(class_id) - 1] += 1  # Convert to 0-based

        result.append((all_positions, jobs_in_service))

    return result


def _multichoose_con(n: np.ndarray, S: int) -> List[np.ndarray]:
    """
    Generate all ways to pick S elements from available units in vector n.

    For SIRO scheduling, this enumerates all possible distributions of S
    jobs in service across K classes, where n[k] is the max number of
    class k jobs that can be selected.

    Args:
        n: Array of available counts per class (length K)
        S: Number of elements to pick (typically = number of servers)

    Returns:
        List of arrays, each representing how many of each class is selected.
        Each array has length K, with sum = S.
    """
    K = len(n)

    if S == 0:
        return [np.zeros(K, dtype=int)]

    if S == 1:
        result = []
        for i in range(K):
            if n[i] > 0:
                v = np.zeros(K, dtype=int)
                v[i] = 1
                result.append(v)
        return result if result else [np.zeros(K, dtype=int)]

    result = []
    for i in range(K):
        if n[i] > 0:
            n_1 = n.copy()
            n_1[i] = n_1[i] - 1
            sub_results = _multichoose_con(n_1, S - 1)
            for sub in sub_results:
                v = sub.copy()
                v[i] += 1
                result.append(v)

    # Remove duplicates
    if result:
        seen = set()
        unique_result = []
        for v in result:
            key = tuple(v)
            if key not in seen:
                seen.add(key)
                unique_result.append(v)
        return unique_result

    return [np.zeros(K, dtype=int)]


def _enumerate_state_space(
    sn: NetworkStruct,
    cutoff = 10,
    rrobin_info: Optional[dict] = None,
    use_phase_augmentation: bool = True
) -> Tuple[np.ndarray, np.ndarray, dict]:
    """
    Enumerate the state space for a queueing network.

    For closed networks, enumerates all valid job distributions.
    For open networks, uses cutoff to bound the state space.

    State vector format (without phase augmentation):
    - First M*K elements: job counts at each (station, class) pair
    - Remaining elements: round-robin pointers for state-dependent routing

    State vector format (with phase augmentation):
    - Phase counts for each (station, class): sum(phases[i,k]) elements per station/class
    - Round-robin pointers
    - MAP phase variables for FCFS stations with MAP distributions

    Args:
        sn: Network structure
        cutoff: Maximum jobs per station for open networks.
                Can be an int (same cutoff for all), or a matrix (M x K)
                with per-station, per-class cutoffs.
        rrobin_info: Optional pre-computed round-robin routing info
        use_phase_augmentation: Whether to use phase-augmented state space

    Returns:
        Tuple of (state_space, state_space_aggr, rrobin_info)
    """
    # Get round-robin routing info if not provided
    if rrobin_info is None:
        rrobin_info = _build_rrobin_state_info(sn)
    M = sn.nstations
    K = sn.nclasses
    # Use sn_has_open_classes instead of sn_is_open_model to properly handle
    # mixed networks (which have both open and closed classes)
    is_open = sn_has_open_classes(sn)

    # Get population constraints
    if sn.njobs is not None:
        N = sn.njobs.flatten()
    else:
        N = np.ones(K)

    # Check if model contains Cache nodes - these require reduced cutoff
    # This matches MATLAB's behavior where cache_replc_routing uses cutoff=1
    # Note: Router nodes with RROBIN do NOT require reduced cutoff - they just need state tracking
    has_cache = False
    if hasattr(sn, 'nodetype') and sn.nodetype is not None:
        for nt in sn.nodetype:
            nt_val = int(nt.value) if hasattr(nt, 'value') else int(nt)
            if nt_val == 6:  # CACHE only (not ROUTER)
                has_cache = True
                break

    # For models with Cache nodes, limit cutoff to 1 to prevent state explosion
    # This matches MATLAB's approach in cache_replc_routing.m which uses cutoff=1
    if has_cache and (np.isscalar(cutoff) or np.atleast_2d(cutoff).size == 1):
        effective_cutoff = min(cutoff, 1) if np.isscalar(cutoff) else min(np.atleast_2d(cutoff).flat[0], 1)
        cutoff = effective_cutoff

    # Handle cutoff as scalar or matrix
    cutoff_arr = np.atleast_2d(cutoff)
    is_matrix_cutoff = cutoff_arr.shape[0] > 1 or cutoff_arr.shape[1] > 1

    # Identify Cache stations - these have immediate processing (capacity 1)
    # This matches MATLAB's spaceGeneratorNodes.m behavior
    # Note: Router nodes are not stations - they're pass-through nodes tracked separately
    # Note: We need to map station indices to node indices since nodetype is indexed by node
    cache_stations = set()
    if hasattr(sn, 'nodetype') and sn.nodetype is not None:
        # Get station to node mapping if available
        station_to_node = None
        if hasattr(sn, 'stationToNode') and sn.stationToNode is not None:
            station_to_node = sn.stationToNode

        for ist in range(M):
            # Get the node index for this station
            if station_to_node is not None and ist < len(station_to_node):
                node_idx = int(station_to_node[ist])
            else:
                node_idx = ist  # Fallback: assume station index = node index

            if node_idx >= 0 and node_idx < len(sn.nodetype):
                nt = sn.nodetype[node_idx]
                # NodeType.CACHE = 6
                nt_val = int(nt.value) if hasattr(nt, 'value') else int(nt)
                if nt_val == 6:  # CACHE only
                    cache_stations.add(ist)

    def get_cutoff(ist: int, k: int) -> int:
        """Get cutoff for station ist and class k."""
        # Cache nodes have capacity 1 (immediate processing)
        # This prevents state space explosion in models with Cache nodes
        if ist in cache_stations:
            return 1

        # Determine base cutoff from options
        if is_matrix_cutoff:
            # Matrix cutoff: index by station and class
            # Handle different matrix layouts
            if cutoff_arr.shape[0] >= M and cutoff_arr.shape[1] >= K:
                base_cutoff = int(cutoff_arr[ist, k])
            elif cutoff_arr.shape[0] >= K and cutoff_arr.shape[1] >= M:
                # Transposed: (K x M) layout
                base_cutoff = int(cutoff_arr[k, ist])
            else:
                # Fallback: use first valid value or default
                base_cutoff = int(cutoff_arr.flat[0]) if cutoff_arr.size > 0 else 10
        else:
            base_cutoff = int(cutoff_arr.flat[0])

        # Also check station capacity from sn.cap
        # Capacity limits the maximum number of jobs that can be at the station
        if hasattr(sn, 'cap') and sn.cap is not None and ist < len(sn.cap):
            station_cap = sn.cap[ist]
            if np.isfinite(station_cap) and station_cap > 0:
                # Use the minimum of cutoff and capacity
                return min(base_cutoff, int(station_cap))

        return base_cutoff

    states = []

    # Helper function for closed class distributions
    def _enumerate_distributions(n_jobs: int, n_stations: int) -> List[List[int]]:
        """Enumerate all ways to distribute n_jobs among n_stations."""
        if n_stations == 1:
            return [[n_jobs]]
        if n_jobs == 0:
            return [[0] * n_stations]

        result = []
        for i in range(n_jobs + 1):
            for rest in _enumerate_distributions(n_jobs - i, n_stations - 1):
                result.append([i] + rest)
        return result

    # Determine which classes are open vs closed
    open_classes = [k for k in range(K) if np.isinf(N[k])]
    closed_classes = [k for k in range(K) if np.isfinite(N[k]) and N[k] > 0]

    # Identify Source and Sink stations (closed class jobs should NOT be there)
    # Note: nodetype is indexed by NODE index, not station index
    # Use stationToNode mapping to convert station index to node index
    source_station = -1
    sink_station = -1

    # Get station to node mapping
    station_to_node = None
    if hasattr(sn, 'stationToNode') and sn.stationToNode is not None:
        station_to_node = np.asarray(sn.stationToNode).flatten()

    # First check sched for EXT scheduling (Source marker)
    # Note: sched dict may store enum values or integer values
    if hasattr(sn, 'sched') and sn.sched is not None:
        for ist, sched_val in sn.sched.items():
            if _sched_is(sched_val, 'EXT') or (isinstance(sched_val, int) and sched_val == SchedStrategy.EXT.value):
                source_station = ist

    # Also check nodetype for Source and Sink
    if hasattr(sn, 'nodetype') and sn.nodetype is not None:
        for ist in range(M):
            # Convert station index to node index
            if station_to_node is not None and ist < len(station_to_node):
                node_idx = int(station_to_node[ist])
            else:
                node_idx = ist  # Fallback if no mapping

            if node_idx < len(sn.nodetype):
                if sn.nodetype[node_idx] == NodeType.SOURCE:
                    source_station = ist
                elif sn.nodetype[node_idx] == NodeType.SINK:
                    sink_station = ist

    # Compute reachable stations for each closed class based on routing
    # This prevents generating states where closed jobs are at unreachable stations
    def _get_reachable_stations(class_k: int, ref_station: int) -> set:
        """Find all stations reachable by class k starting from ref_station."""
        if not hasattr(sn, 'rt') or sn.rt is None:
            # No routing info - assume all non-Source/Sink stations are reachable
            return set(ist for ist in range(M) if ist != source_station and ist != sink_station)

        rt = np.asarray(sn.rt)
        reachable = set()
        to_visit = [ref_station]

        while to_visit:
            ist = to_visit.pop()
            if ist in reachable:
                continue
            if ist == source_station or ist == sink_station:
                continue
            reachable.add(ist)

            # Find outgoing transitions for this class at this station
            src_idx = ist * K + class_k
            if src_idx >= rt.shape[0]:
                continue
            for jst in range(M):
                dst_idx = jst * K + class_k
                if dst_idx >= rt.shape[1]:
                    continue
                if rt[src_idx, dst_idx] > 1e-10 and jst not in reachable:
                    to_visit.append(jst)

        return reachable

    # For each closed class, compute reachable stations
    closed_class_reachable = {}
    for k in closed_classes:
        # Get reference station for this class
        ref_station = 0  # Default
        if hasattr(sn, 'refstat') and sn.refstat is not None:
            refstat = np.asarray(sn.refstat).flatten()
            if k < len(refstat):
                ref_station = int(refstat[k])
        closed_class_reachable[k] = _get_reachable_stations(k, ref_station)

    # Stations where closed class jobs can reside (exclude Source/Sink)
    # For enumeration, use union of all reachable stations across all closed classes
    if closed_classes and closed_class_reachable:
        closed_valid_stations = sorted(set.union(*closed_class_reachable.values()) if closed_class_reachable else set())
    else:
        closed_valid_stations = [ist for ist in range(M) if ist != source_station and ist != sink_station]
    n_closed_stations = len(closed_valid_stations)

    if is_open and closed_classes:
        # Mixed network: combine closed class distributions with open class enumeration
        # For closed classes: enumerate valid distributions (conserving population)
        #                     only among valid (non-Source/Sink) stations
        # For open classes: enumerate 0 to cutoff at each station (except Source for arrivals)

        # Generate closed class distributions among valid stations only
        closed_class_dists = []
        for k in closed_classes:
            n_k = int(N[k])
            # Distribute among valid stations only
            class_dists = _enumerate_distributions(n_k, n_closed_stations)
            closed_class_dists.append((k, class_dists))

        # Generate open class ranges (per non-Source station for queue occupancy)
        # Open class jobs can be at any station except Source (which generates arrivals)
        open_class_ranges = []
        for k in open_classes:
            station_ranges = []
            for ist in range(M):
                if ist == source_station:
                    # Source doesn't hold jobs - only range is 0
                    station_ranges.append(range(1))  # Just [0]
                else:
                    c = get_cutoff(ist, k)
                    station_ranges.append(range(c + 1))
            open_class_ranges.append((k, station_ranges))

        # Combine: iterate over closed distributions × open combinations
        from itertools import product as iter_product

        # Get all combinations of closed class distributions
        if closed_class_dists:
            closed_combos = list(iter_product(*[dists for _, dists in closed_class_dists]))
        else:
            closed_combos = [()]

        # Get all combinations of open class values at each station
        if open_class_ranges:
            # Flatten: for each open class, product over stations
            open_station_products = []
            for k, station_ranges in open_class_ranges:
                open_station_products.append(list(iter_product(*station_ranges)))
            open_combos = list(iter_product(*open_station_products))
        else:
            open_combos = [()]

        # Build states from combinations
        for closed_combo in closed_combos:
            for open_combo in open_combos:
                # Build state vector: [n_11, n_12, ..., n_1K, n_21, ..., n_MK]
                state = [0] * (M * K)
                # Fill in closed classes (mapping from valid station indices to full indices)
                for idx, (k, _) in enumerate(closed_class_dists):
                    dist = closed_combo[idx]
                    for valid_idx, ist in enumerate(closed_valid_stations):
                        state[ist * K + k] = dist[valid_idx]
                # Fill in open classes
                for idx, (k, _) in enumerate(open_class_ranges):
                    station_vals = open_combo[idx]
                    for ist in range(M):
                        state[ist * K + k] = station_vals[ist]
                states.append(state)

    elif is_open:
        # Pure open network: enumerate all valid job distributions
        # MATLAB behavior: cutoff limits TOTAL jobs per class in the ENTIRE network
        # Each class can have at most cutoff jobs distributed across all stations
        # This matches MATLAB's spaceGenerator.m where Np(r) = max(capacityc(:,r))

        # Get valid stations (exclude Source/Sink)
        valid_stations = [ist for ist in range(M) if ist != source_station and ist != sink_station]
        n_valid = len(valid_stations)

        # Get per-class cutoff (max jobs per class in network)
        class_cutoffs = []
        for k in range(K):
            if is_matrix_cutoff:
                # Matrix cutoff: max across stations for this class
                max_cutoff = max(get_cutoff(ist, k) for ist in valid_stations) if valid_stations else 1
            else:
                max_cutoff = int(cutoff_arr.flat[0])
            class_cutoffs.append(max_cutoff)

        # Enumerate all combinations of total jobs per class (0 to cutoff for each class)
        from itertools import product as iter_product
        total_job_combos = list(iter_product(*[range(c + 1) for c in class_cutoffs]))

        for total_jobs in total_job_combos:
            # For each combination of total jobs per class, distribute across stations
            # Generate all ways to distribute total_jobs[k] jobs of class k across valid_stations
            class_distributions = []
            for k, n_jobs in enumerate(total_jobs):
                # Distribute n_jobs across n_valid stations
                class_dists = _enumerate_distributions(n_jobs, n_valid)
                class_distributions.append(class_dists)

            # Combine distributions across classes
            for dist_combo in iter_product(*class_distributions):
                # dist_combo[k] = distribution of class k jobs across valid_stations
                state = [0] * (M * K)
                for k, dist in enumerate(dist_combo):
                    for valid_idx, ist in enumerate(valid_stations):
                        state[ist * K + k] = dist[valid_idx]
                states.append(state)
    else:
        # Pure closed network: enumerate valid distributions
        # Check for class switching (chains) - classes in the same chain can exchange jobs
        has_chains = (hasattr(sn, 'chains') and sn.chains is not None and
                      hasattr(sn, 'inchain') and sn.inchain is not None and
                      hasattr(sn, 'nchains') and sn.nchains is not None)

        # Determine if class switching exists (some chain has multiple classes)
        has_class_switching = False
        if has_chains and sn.nchains < K:
            for chain_id in range(sn.nchains):
                if chain_id in sn.inchain and len(sn.inchain[chain_id]) > 1:
                    has_class_switching = True
                    break

        if has_class_switching:
            # Class switching exists - enumerate based on chain populations
            # For each chain, enumerate all ways to distribute the chain population
            # across (station, class) pairs within the chain
            all_chain_dists = []

            for chain_id in range(sn.nchains):
                if chain_id not in sn.inchain:
                    continue
                chain_classes = list(sn.inchain[chain_id])  # Array of class indices in this chain

                # Chain population = sum of N[k] for all k in chain
                chain_pop = sum(int(N[k]) for k in chain_classes if np.isfinite(N[k]))

                if chain_pop == 0:
                    # No jobs in this chain - single empty distribution
                    n_pairs = M * len(chain_classes)
                    chain_dists = [[0] * n_pairs]
                else:
                    # Number of (station, class) pairs in this chain
                    n_pairs = M * len(chain_classes)

                    # Enumerate all ways to distribute chain_pop among n_pairs
                    chain_dists = _enumerate_distributions(chain_pop, n_pairs)

                all_chain_dists.append((chain_id, chain_classes, chain_dists))

            # Combine distributions across chains
            for combo in product(*[dists for _, _, dists in all_chain_dists]):
                state = [0] * (M * K)
                for idx, (chain_id, chain_classes, _) in enumerate(all_chain_dists):
                    dist = combo[idx]
                    # Map distribution back to (station, class) pairs
                    # The distribution is ordered by station first, then by class within chain
                    pair_idx = 0
                    for ist in range(M):
                        for k in chain_classes:
                            state[ist * K + k] = dist[pair_idx]
                            pair_idx += 1
                states.append(state)
        else:
            # No class switching - original per-class enumeration
            all_class_dists = []
            for k in range(K):
                n_k = int(N[k]) if np.isfinite(N[k]) else 0
                class_dists = _enumerate_distributions(n_k, M)
                all_class_dists.append(class_dists)

            # Combine all class distributions
            for combo in product(*all_class_dists):
                # combo is tuple of distributions, one per class
                # Convert to state vector: [n_11, n_12, ..., n_1K, n_21, ..., n_MK]
                state = []
                for ist in range(M):
                    for k in range(K):
                        state.append(combo[k][ist])
                states.append(state)

    if not states:
        states = [[0] * (M * K)]

    # Filter states to respect station capacity constraints
    # For each station, sum of jobs across all classes must be <= capacity
    if hasattr(sn, 'cap') and sn.cap is not None:
        filtered_states = []
        for state in states:
            valid = True
            for ist in range(M):
                if ist < len(sn.cap):
                    cap_val = sn.cap[ist]
                    if np.isfinite(cap_val) and cap_val > 0:
                        # Sum jobs at this station across all classes
                        total_at_station = sum(state[ist * K + k] for k in range(K))
                        if total_at_station > cap_val:
                            valid = False
                            break
            if valid:
                filtered_states.append(state)
        states = filtered_states if filtered_states else [[0] * (M * K)]

    # Get phase information for phase-type state augmentation
    phases, needs_phase_augmentation = _get_phases_info(sn)

    # Compute phase-related state offsets for later use
    # phase_offset[ist, k] = starting index of phases for (ist, k) in phase-augmented state
    total_phases = int(np.sum(phases))
    phase_offset = np.zeros((M, K), dtype=int)
    idx = 0
    for ist in range(M):
        for k in range(K):
            phase_offset[ist, k] = idx
            idx += phases[ist, k]

    # Store phase information in rrobin_info for use by generator
    rrobin_info['phases'] = phases
    rrobin_info['phase_offset'] = phase_offset
    rrobin_info['total_phases'] = total_phases
    # Note: needs_phase_augmentation will be set after FCFS stations are identified

    # Identify FCFS stations for proper buffer ordering
    fcfs_stations = _get_fcfs_stations(sn)
    rrobin_info['fcfs_stations'] = fcfs_stations

    # Identify SIRO stations for count-based buffer tracking
    siro_stations = _get_siro_stations(sn)
    rrobin_info['siro_stations'] = siro_stations

    # Get number of servers per station
    nservers = sn.nservers if hasattr(sn, 'nservers') and sn.nservers is not None else np.ones(M, dtype=int)

    # Identify Source and Sink stations to skip from state space
    # These stations don't contribute to the CTMC state (infinite population for Source)
    skip_stations = set()
    if hasattr(sn, 'nodetype') and sn.nodetype is not None:
        station_to_node = getattr(sn, 'stationToNode', None)
        for ist in range(M):
            # Map station to node index
            node_idx = ist
            if station_to_node is not None:
                node_arr = np.atleast_1d(station_to_node)
                if ist < len(node_arr):
                    node_idx = int(node_arr[ist])
            # Check if this node is Source or Sink
            if node_idx >= 0 and node_idx < len(sn.nodetype):
                nt = sn.nodetype[node_idx]
                if nt == NodeType.SOURCE or nt == NodeType.SINK:
                    skip_stations.add(ist)
    rrobin_info['skip_stations'] = skip_stations

    # If phase augmentation is needed and enabled, expand states with phase distributions
    # For FCFS stations, also expand with buffer orderings
    # For SIRO stations, also expand with per-class buffer counts
    # IMPORTANT: Always run state expansion for FCFS/SIRO stations to match MATLAB format
    # MATLAB generates [buffer, phases] format even for single-phase (Exp) distributions
    needs_state_expansion = (needs_phase_augmentation and use_phase_augmentation) or bool(fcfs_stations - skip_stations) or bool(siro_stations - skip_stations)
    # Update rrobin_info to reflect actual state expansion status
    rrobin_info['needs_phase_augmentation'] = needs_state_expansion
    if needs_state_expansion:
        # For each basic state (job counts), expand to all possible phase distributions
        phase_augmented_states = []

        # Track FCFS buffer structure for later use
        # fcfs_buffer_info[ist] = (buffer_start_idx, max_buffer_size)
        fcfs_buffer_info = {}

        # Compute maximum buffer size for each FCFS station
        # MATLAB format: buffer only stores WAITING jobs (class indices), not in-service jobs
        # In-service jobs are tracked by phase counts
        # Buffer size = max_jobs_at_station - servers (to hold waiting jobs when station is full)
        # For closed models, max_jobs_at_station = total_population
        # For open models, use cutoff
        fcfs_max_buffer = {}  # Maps ist -> maximum buffer size
        for ist in fcfs_stations:
            S_ist = int(nservers[ist]) if ist < len(nservers) else 1
            if is_open:
                # Open model: use cutoff per class * number of classes
                # MATLAB treats scalar cutoff as per-class, so max total = cutoff * K
                effective_cutoff = int(cutoff_arr.flat[0]) if cutoff_arr.size > 0 else 10
                max_at_station = effective_cutoff * K
            else:
                # Closed model: max at any station is total population
                max_at_station = int(np.sum(N[np.isfinite(N)]))
            # Buffer only holds waiting jobs: max_waiting = max_at_station - servers
            # Use at least 1 to ensure consistent state format even when max_waiting=0
            fcfs_max_buffer[ist] = max(1, max_at_station - S_ist)

        rrobin_info['fcfs_max_buffer'] = fcfs_max_buffer

        for base_state in states:
            # base_state has format [n_11, n_12, ..., n_1K, n_21, ..., n_MK]
            # We need to expand each n_ik into phase distribution
            # For FCFS stations with multiple classes, also enumerate buffer orderings

            # First pass: compute station-level job counts and identify FCFS expansion
            station_jobs = {}  # Maps ist -> array of job counts per class
            for ist in range(M):
                n_ist = np.array([int(base_state[ist * K + k]) for k in range(K)])
                station_jobs[ist] = n_ist

            # For each FCFS station, generate buffer orderings
            # For non-FCFS stations, use PS-style phase distribution
            fcfs_buffer_combos = {}  # Maps ist -> list of (buffer, jobs_in_service) tuples
            for ist in fcfs_stations:
                n_ist = station_jobs[ist]
                total_at_station = int(sum(n_ist))
                if total_at_station > 0 and sum(n_ist > 0) > 1:
                    # Multiple classes at station - need buffer ordering
                    S_ist = int(nservers[ist]) if ist < len(nservers) else 1
                    fcfs_buffer_combos[ist] = _generate_fcfs_buffer_orderings(n_ist, S_ist, K)
                else:
                    # Single class or empty - buffer ordering is trivial
                    fcfs_buffer_combos[ist] = None

            # Generate all phase distribution combinations for non-FCFS parts
            # and combine with FCFS buffer orderings
            def _expand_state(base_state, remaining_stations, current_phases):
                """Recursively expand state with phase distributions and FCFS buffers."""
                if not remaining_stations:
                    # All stations processed - yield the expanded state
                    yield current_phases
                    return

                ist = remaining_stations[0]
                rest = remaining_stations[1:]
                n_ist = station_jobs[ist]

                # Skip Source and Sink stations - they don't contribute to state space
                if ist in skip_stations:
                    for expanded in _expand_state(base_state, rest, current_phases):
                        yield expanded
                    return

                if ist in fcfs_buffer_combos and fcfs_buffer_combos[ist] is not None:
                    # FCFS station with multiple classes - expand with buffer orderings
                    max_buf_size = fcfs_max_buffer.get(ist, 0)

                    for all_positions, jobs_in_service in fcfs_buffer_combos[ist]:
                        # Generate all buffer orderings without class imbalance constraint
                        # The constraint was causing unreachable states for larger cutoffs

                        # For each class, generate phase distributions for jobs in service
                        phase_combos_for_service = []
                        for k in range(K):
                            n_in_service = jobs_in_service[k]
                            n_phases_k = phases[ist, k]
                            if n_phases_k > 1 and n_in_service > 0:
                                phase_dists = _generate_phase_distributions(int(n_in_service), int(n_phases_k))
                            else:
                                phase_dists = [tuple([int(n_in_service)] + [0] * (n_phases_k - 1))] if n_phases_k > 1 else [(int(n_in_service),)]
                            phase_combos_for_service.append(phase_dists)

                        # Get number of servers at this station
                        S_ist = int(nservers[ist]) if ist < len(nservers) else 1

                        # Cartesian product of phase distributions for this station
                        for phase_combo in product(*phase_combos_for_service):
                            # Build station state: buffer positions (padded) + server phases
                            station_state = [0] * max_buf_size  # Initialize with zeros

                            # all_positions includes all jobs: leftmost are buffer, rightmost are in service
                            # Only place the BUFFER positions (first num_in_buffer elements) into buffer
                            # Service jobs are tracked by phase counts, not buffer positions
                            total_jobs = len(all_positions)
                            num_in_buffer = total_jobs - min(total_jobs, S_ist)
                            buffer_positions = all_positions[:num_in_buffer]

                            # Place buffer positions at the end (right-justified)
                            for i, bp in enumerate(buffer_positions):
                                station_state[max_buf_size - num_in_buffer + i] = bp

                            # Add phase distributions for server
                            for pd in phase_combo:
                                station_state.extend(pd)
                            # Recurse
                            for expanded in _expand_state(base_state, rest, current_phases + station_state):
                                yield expanded
                elif ist in fcfs_stations:
                    # FCFS station with single class or empty
                    # For FCFS: only S jobs can be in service, rest must be in buffer
                    max_buf_size = fcfs_max_buffer.get(ist, 0)
                    S_ist = int(nservers[ist]) if ist < len(nservers) else 1
                    total_at_station = int(sum(n_ist))

                    if total_at_station == 0:
                        # Empty station
                        station_state = [0] * max_buf_size
                        for k in range(K):
                            n_phases_k = phases[ist, k]
                            station_state.extend([0] * n_phases_k)
                        for expanded in _expand_state(base_state, rest, current_phases + station_state):
                            yield expanded
                    else:
                        # Find which class has jobs (single-class case)
                        active_class = -1
                        for k in range(K):
                            if n_ist[k] > 0:
                                active_class = k
                                break

                        if active_class >= 0:
                            n_active = int(n_ist[active_class])
                            num_in_service = min(n_active, S_ist)
                            num_in_buffer = n_active - num_in_service

                            # NOTE: Previously had a constraint to skip pure single-class states
                            # with 3+ jobs in buffer. This was removed because multiclass states
                            # can depart to these single-class states, causing absorbing states
                            # if the targets are filtered out.

                            # Generate buffer: class IDs for WAITING jobs only (1-based)
                            # MATLAB format: buffer tracks waiting jobs, phase counts track in-service
                            # num_in_buffer = jobs waiting (not in service)
                            buffer_positions = [active_class + 1] * num_in_buffer

                            # Generate phase distributions for jobs in service
                            n_phases_active = phases[ist, active_class]
                            if n_phases_active > 1 and num_in_service > 0:
                                service_phase_dists = _generate_phase_distributions(num_in_service, int(n_phases_active))
                            else:
                                service_phase_dists = [tuple([num_in_service] + [0] * (n_phases_active - 1))] if n_phases_active > 1 else [(num_in_service,)]

                            for service_phases in service_phase_dists:
                                # Build station state: buffer + phases for all classes
                                station_state = [0] * max_buf_size
                                # Place buffer positions at the end (right-justified)
                                # MATLAB format: buffer holds waiting jobs only, right-justified
                                for i, bp in enumerate(buffer_positions):
                                    station_state[max_buf_size - num_in_buffer + i] = bp

                                # Add phase distributions for all classes
                                for k in range(K):
                                    n_phases_k = phases[ist, k]
                                    if k == active_class:
                                        station_state.extend(service_phases)
                                    else:
                                        station_state.extend([0] * n_phases_k)

                                for expanded in _expand_state(base_state, rest, current_phases + station_state):
                                    yield expanded
                        else:
                            # No active class - empty state
                            station_state = [0] * max_buf_size
                            for k in range(K):
                                n_phases_k = phases[ist, k]
                                station_state.extend([0] * n_phases_k)
                            for expanded in _expand_state(base_state, rest, current_phases + station_state):
                                yield expanded
                elif ist in siro_stations:
                    # SIRO station - use count-based buffer (per-class counts, not ordered)
                    # SIRO state format: [buffer_counts[K], phase_counts]
                    # where buffer_counts[k] = jobs of class k waiting in buffer
                    S_ist = int(nservers[ist]) if ist < len(nservers) else 1
                    total_at_station = int(sum(n_ist))

                    if total_at_station == 0:
                        # Empty station: buffer counts are 0, phase counts are 0
                        station_state = [0] * K  # Buffer counts (one per class)
                        for k in range(K):
                            n_phases_k = phases[ist, k]
                            station_state.extend([0] * n_phases_k)
                        for expanded in _expand_state(base_state, rest, current_phases + station_state):
                            yield expanded
                    elif total_at_station <= S_ist:
                        # All jobs in service, no buffer
                        station_state = [0] * K  # Buffer counts (all zeros)
                        for k in range(K):
                            n_ik = int(n_ist[k])
                            n_phases_k = phases[ist, k]
                            if n_phases_k > 1 and n_ik > 0:
                                phase_dists = _generate_phase_distributions(n_ik, int(n_phases_k))
                            else:
                                phase_dists = [tuple([n_ik] + [0] * (n_phases_k - 1))] if n_phases_k > 1 else [(n_ik,)]
                            for pd in phase_dists:
                                inner_state = station_state.copy()
                                inner_state.extend(pd)
                                station_state = inner_state
                                break  # Only take first phase distribution here
                        # Enumerate all phase combinations
                        phase_combos_for_station = []
                        for k in range(K):
                            n_ik = int(n_ist[k])
                            n_phases_k = phases[ist, k]
                            if n_phases_k > 1 and n_ik > 0:
                                phase_dists = _generate_phase_distributions(n_ik, int(n_phases_k))
                            else:
                                phase_dists = [(n_ik,)] if n_phases_k <= 1 else [tuple([n_ik] + [0] * (n_phases_k - 1))]
                            phase_combos_for_station.append(phase_dists)
                        for phase_combo in product(*phase_combos_for_station):
                            station_state = [0] * K  # Buffer counts
                            for pd in phase_combo:
                                station_state.extend(pd)
                            for expanded in _expand_state(base_state, rest, current_phases + station_state):
                                yield expanded
                    else:
                        # Jobs exceed servers - need to enumerate buffer/service distributions
                        # Use multichoose to enumerate how many jobs of each class are in service
                        service_distributions = _multichoose_con(np.array(n_ist), S_ist)
                        for si in service_distributions:
                            # si[k] = number of class k jobs in service
                            # buffer[k] = n_ist[k] - si[k]
                            buffer_counts = [int(n_ist[k]) - int(si[k]) for k in range(K)]
                            # Generate phase distributions for jobs in service
                            phase_combos_for_station = []
                            for k in range(K):
                                n_in_service = int(si[k])
                                n_phases_k = phases[ist, k]
                                if n_phases_k > 1 and n_in_service > 0:
                                    phase_dists = _generate_phase_distributions(n_in_service, int(n_phases_k))
                                else:
                                    phase_dists = [(n_in_service,)] if n_phases_k <= 1 else [tuple([n_in_service] + [0] * (n_phases_k - 1))]
                                phase_combos_for_station.append(phase_dists)
                            for phase_combo in product(*phase_combos_for_station):
                                station_state = buffer_counts.copy()  # Buffer counts per class
                                for pd in phase_combo:
                                    station_state.extend(pd)
                                for expanded in _expand_state(base_state, rest, current_phases + station_state):
                                    yield expanded
                else:
                    # Non-FCFS/non-SIRO station - use PS-style phase distribution (no buffer)
                    phase_combos_for_station = []
                    for k in range(K):
                        n_ik = int(n_ist[k])
                        n_phases_k = phases[ist, k]
                        if n_phases_k > 1:
                            phase_dists = _generate_phase_distributions(n_ik, int(n_phases_k))
                        else:
                            phase_dists = [(n_ik,)]
                        phase_combos_for_station.append(phase_dists)

                    for phase_combo in product(*phase_combos_for_station):
                        station_state = []
                        for pd in phase_combo:
                            station_state.extend(pd)
                        for expanded in _expand_state(base_state, rest, current_phases + station_state):
                            yield expanded

            # Expand this base state
            all_stations = list(range(M))
            for expanded_state in _expand_state(base_state, all_stations, []):
                phase_augmented_states.append(expanded_state)

        # De-duplicate states (enumerate can produce duplicates for multi-class FCFS)
        seen = set()
        unique_states = []
        for s in phase_augmented_states:
            key = tuple(int(x) for x in s)
            if key not in seen:
                seen.add(key)
                unique_states.append(s)
        states = unique_states

        # Compute state_dim from actual state sizes (should be consistent now)
        if states:
            state_dim = len(states[0])
            # Verify all states have same size
            for s in states:
                if len(s) != state_dim:
                    print(f"Warning: inconsistent state size {len(s)} vs {state_dim}")
        else:
            state_dim = total_phases

        # Recompute phase_offset to account for FCFS/SIRO buffer positions
        # For FCFS stations: state = [buffer_positions, phases_class0, phases_class1, ...]
        # For SIRO stations: state = [buffer_counts_class0..K, phases_class0, phases_class1, ...]
        # For non-FCFS/non-SIRO stations: state = [phases_class0, phases_class1, ...]
        # Skip Source/Sink stations as they don't contribute to state
        fcfs_phase_offset = np.zeros((M, K), dtype=int)
        idx = 0
        for ist in range(M):
            # Skip Source/Sink stations
            if ist in skip_stations:
                fcfs_phase_offset[ist, :] = -1  # Mark as invalid
                continue
            if ist in fcfs_stations:
                # FCFS station: buffer comes first
                max_buf = fcfs_max_buffer.get(ist, 0)
                idx += max_buf  # Skip buffer positions
            elif ist in siro_stations:
                # SIRO station: K buffer counts come first
                idx += K  # Skip buffer count positions
            for k in range(K):
                fcfs_phase_offset[ist, k] = idx
                idx += phases[ist, k]

        # Update phase_offset with FCFS-aware offsets
        phase_offset = fcfs_phase_offset
        rrobin_info['phase_offset'] = phase_offset

        # Store FCFS buffer info for generator
        rrobin_info['fcfs_buffer_info'] = fcfs_buffer_info
    else:
        # No phase augmentation - use simple job counts
        state_dim = M * K

    rrobin_info['state_dim'] = state_dim

    # Get MAP FCFS information for additional state variables
    map_fcfs, has_map_fcfs = _get_map_fcfs_info(sn)
    rrobin_info['map_fcfs'] = map_fcfs
    rrobin_info['has_map_fcfs'] = has_map_fcfs

    # Augment states with MAP phase variables for FCFS stations with MAP distributions
    # The MAP phase tracks the "mode" of the MAP process (separate from service phase counts)
    if has_map_fcfs:
        map_augmented_states = []
        # Sort the map_fcfs keys for consistent ordering
        map_fcfs_keys = sorted(map_fcfs.keys())
        rrobin_info['map_fcfs_keys'] = map_fcfs_keys

        # Create map offset mapping: position in state vector where each MAP phase var starts
        map_var_offset = {}
        offset = state_dim  # MAP vars start after the job count variables
        for (ist, k) in map_fcfs_keys:
            map_var_offset[(ist, k)] = offset
            offset += 1  # Each MAP phase is a single integer (the current phase)
        rrobin_info['map_var_offset'] = map_var_offset
        rrobin_info['map_var_count'] = len(map_fcfs_keys)

        # Expand each base state with valid MAP phase combinations
        # MATLAB constraint: when jobs of a MAP class are in service at a single-server
        # FCFS station, the MAP phase must equal the occupied service phase.
        # When no jobs in service, all phases are valid.
        for base_state in states:
            # For each MAP class, determine valid MAP phases based on service state
            valid_map_phases = []
            for (ist, k) in map_fcfs_keys:
                n_phases = map_fcfs[(ist, k)]
                S_ist = int(nservers[ist]) if ist < len(nservers) else 1

                # Get the phase counts for this class from base_state
                start_idx = phase_offset[ist, k]
                end_idx = start_idx + n_phases
                if end_idx <= len(base_state):
                    phase_counts = base_state[start_idx:end_idx]
                else:
                    phase_counts = [0] * n_phases

                jobs_in_service = sum(phase_counts)

                if jobs_in_service > 0 and S_ist == 1:
                    # Single server with jobs in service: MAP phase = occupied phase
                    # Find which phase has the job (there can only be one in single server)
                    occupied_phase = None
                    for p in range(n_phases):
                        if phase_counts[p] > 0:
                            occupied_phase = p
                            break
                    if occupied_phase is not None:
                        valid_map_phases.append([occupied_phase])
                    else:
                        # Fallback: allow all phases
                        valid_map_phases.append(list(range(n_phases)))
                else:
                    # No jobs in service or multi-server: all phases are valid
                    valid_map_phases.append(list(range(n_phases)))

            # Create all valid MAP phase combinations for this base state
            for map_combo in product(*valid_map_phases):
                augmented_state = list(base_state) + list(map_combo)
                map_augmented_states.append(augmented_state)

        states = map_augmented_states
        # Note: state_dim stays the same - it's only the job count variables
        # MAP phase variables are stored separately after state_dim
    else:
        rrobin_info['map_fcfs_keys'] = []
        rrobin_info['map_var_offset'] = {}
        rrobin_info['map_var_count'] = 0

    # Augment states with round-robin pointers if there are RROBIN routing nodes
    # Each RROBIN (node, class) adds a state variable that tracks which outlink
    # the round-robin pointer is pointing to
    if rrobin_info['total_vars'] > 0:
        augmented_states = []
        # Get all possible round-robin pointer combinations
        rr_ranges = []
        for node_idx, class_idx, num_outlinks in rrobin_info['state_vars']:
            # Each pointer can be any of the outlinks (0 to num_outlinks-1)
            rr_ranges.append(range(num_outlinks))

        # Expand each base state with all possible RR pointer combinations
        for base_state in states:
            for rr_combo in product(*rr_ranges):
                augmented_state = list(base_state) + list(rr_combo)
                augmented_states.append(augmented_state)
        states = augmented_states

    state_space = np.array(states, dtype=np.float64)

    # Aggregated state space: sum over classes at each station (exclude RR pointers)
    # For phase-augmented states:
    # - FCFS stations: count buffer entries (buffer stores ALL jobs at station)
    # - Non-FCFS stations: sum over phases (phase counts represent jobs in each phase)
    # Note: use needs_state_expansion (not just phase augmentation flag) because
    # FCFS stations always get state expansion regardless of use_phase_augmentation
    state_space_aggr = np.zeros((len(states), M))
    for i, state in enumerate(states):
        for ist in range(M):
            # Source/Sink stations always have 0 jobs (they're skipped from state space)
            if ist in skip_stations:
                state_space_aggr[i, ist] = 0.0
                continue

            if needs_state_expansion:
                if ist in fcfs_stations:
                    # FCFS stations: count buffer entries for each class
                    # Buffer stores ALL jobs at station (waiting + in-service)
                    max_buf = fcfs_max_buffer.get(ist, 0)
                    buffer_start = fcfs_buffer_info.get(ist, {}).get('buffer_start', 0)
                    for buf_pos in range(max_buf):
                        buf_val = int(state[buffer_start + buf_pos])
                        if buf_val > 0:  # Non-empty buffer position
                            state_space_aggr[i, ist] += 1.0
                else:
                    # Non-FCFS stations: sum over phases
                    for k in range(K):
                        start_idx = phase_offset[ist, k]
                        if start_idx >= 0:  # Valid offset (not skipped station)
                            end_idx = start_idx + phases[ist, k]
                            state_space_aggr[i, ist] += sum(state[start_idx:end_idx])
            else:
                for k in range(K):
                    state_space_aggr[i, ist] += state[ist * K + k]

    return state_space, state_space_aggr, rrobin_info


def _build_state_index_map(state_space: np.ndarray) -> dict:
    """
    Build a hash map from state tuples to indices for O(1) lookup.

    Args:
        state_space: Enumerated state space (n_states x state_dim)

    Returns:
        Dictionary mapping state tuples to their indices
    """
    state_map = {}
    for i, state in enumerate(state_space):
        # Convert to tuple of integers for hashing
        state_key = tuple(int(x) for x in state)
        state_map[state_key] = i
    return state_map


def _find_state_index_fast(state_map: dict, state: np.ndarray) -> int:
    """
    Find index of state using hash map (O(1) lookup).

    Args:
        state_map: Hash map from state tuples to indices
        state: State vector to find

    Returns:
        Index of state, or -1 if not found
    """
    state_key = tuple(int(x) for x in state)
    return state_map.get(state_key, -1)


def _build_generator(
    sn: NetworkStruct,
    state_space: np.ndarray,
    options: SolverCTMCOptions,
    rrobin_info: Optional[dict] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build the infinitesimal generator matrix for the queueing network.

    Supports state-dependent routing (RROBIN, WRROBIN) by using routing state
    variables in the state vector to determine destinations.

    Also supports phase-type distributions (PH, APH, MAP, etc.) when phase
    augmentation is enabled in rrobin_info.

    Args:
        sn: Network structure
        state_space: Enumerated state space
        options: Solver options
        rrobin_info: Round-robin routing information (also contains phase info)

    Returns:
        Tuple of (infinitesimal generator matrix Q, departure rates array depRates)
        depRates[s, ist, k] = total departure rate from state s at station ist for class k
    """
    M = sn.nstations
    K = sn.nclasses
    n_states = state_space.shape[0]

    Q = np.zeros((n_states, n_states))
    # Track departure rates: depRates[s, ist, k] = sum of departure rates from state s
    # for class k at station ist (used for accurate throughput computation)
    depRates = np.zeros((n_states, M, K))

    # Get round-robin info if not provided
    if rrobin_info is None:
        rrobin_info = _build_rrobin_state_info(sn)

    # Check if phase augmentation is used
    use_phase_aug = rrobin_info.get('needs_phase_augmentation', False)
    phases = rrobin_info.get('phases', np.ones((M, K), dtype=int))
    phase_offset = rrobin_info.get('phase_offset', None)
    state_dim = rrobin_info.get('state_dim', M * K)

    # Get MAP FCFS info
    map_fcfs = rrobin_info.get('map_fcfs', {})
    has_map_fcfs = rrobin_info.get('has_map_fcfs', False)
    map_var_offset = rrobin_info.get('map_var_offset', {})
    map_var_count = rrobin_info.get('map_var_count', 0)

    # Build mapping from (node_idx, class_idx) to state variable index
    # RR pointers come after state variables AND MAP phase variables
    rr_state_offset = state_dim + map_var_count  # RR pointers start after MAP vars
    rr_var_map = {}  # Maps (node_idx, class_idx) -> index in state vector
    for i, (node_idx, class_idx, _) in enumerate(rrobin_info['state_vars']):
        rr_var_map[(node_idx, class_idx)] = rr_state_offset + i

    def get_map_matrices(ist: int, k: int) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Get MAP D0 and D1 matrices for (station, class)."""
        if not hasattr(sn, 'proc') or sn.proc is None:
            return None, None
        proc_is_list = isinstance(sn.proc, list)
        if proc_is_list:
            if ist >= len(sn.proc) or sn.proc[ist] is None:
                return None, None
            station_proc = sn.proc[ist]
        else:
            if ist not in sn.proc:
                return None, None
            station_proc = sn.proc[ist]

        proc_entry = None
        if isinstance(station_proc, (list, tuple)):
            if k < len(station_proc):
                proc_entry = station_proc[k]
        elif isinstance(station_proc, dict):
            proc_entry = station_proc.get(k)

        if proc_entry is None:
            return None, None

        # Handle PH/APH distributions stored as [alpha, T] or direct D0/D1 matrices
        if isinstance(proc_entry, (list, tuple)) and len(proc_entry) >= 2:
            first_elem = np.atleast_2d(np.array(proc_entry[0], dtype=float))
            second_elem = np.atleast_2d(np.array(proc_entry[1], dtype=float))

            # Check if this is [alpha, T] format (alpha is 1D/row vector, T is square matrix)
            # vs [D0, D1] format (both D0 and D1 are square matrices)
            if first_elem.shape[0] == 1 and second_elem.shape[0] == second_elem.shape[1]:
                # This is [alpha, T] format for PH/APH distributions
                alpha = first_elem.flatten()
                T = second_elem
                # Convert to D0/D1:
                # D0 = T (the transition matrix, including diagonal absorption rates)
                # D1 = outer(exit_rates, alpha) where exit_rates = -sum(T, axis=1)
                D0 = T
                exit_rates = -np.sum(T, axis=1)
                D1 = np.outer(exit_rates, alpha)
                return D0, D1
            else:
                # Assume direct D0/D1 matrices
                D0 = first_elem
                D1 = second_elem
                return D0, D1

        # Handle Erlang distribution stored as dict with 'k' and 'mu'
        if isinstance(proc_entry, dict):
            if 'k' in proc_entry and 'mu' in proc_entry:
                n_phases = int(proc_entry['k'])
                mu = float(proc_entry['mu'])  # per-phase rate
                if n_phases > 1:
                    # Construct Erlang D0/D1 matrices
                    # D0: diagonal = -mu (absorption), off-diagonal D0[i,i+1] = mu (phase transition)
                    # D1: D1[k-1,0] = mu (completion from last phase)
                    D0 = np.zeros((n_phases, n_phases))
                    D1 = np.zeros((n_phases, n_phases))
                    for p in range(n_phases):
                        D0[p, p] = -mu
                        if p < n_phases - 1:
                            D0[p, p + 1] = mu  # phase transition
                    D1[n_phases - 1, 0] = mu  # completion from last phase
                    return D0, D1
                else:
                    # Single phase: exponential
                    D0 = np.array([[-mu]])
                    D1 = np.array([[mu]])
                    return D0, D1
            elif 'probs' in proc_entry and 'rates' in proc_entry:
                # HyperExp distribution: each phase completes independently
                probs = np.array(proc_entry['probs'])
                rates = np.array(proc_entry['rates'])
                n_phases = len(rates)
                # D0: diagonal with -rate_i (no inter-phase transitions in HyperExp)
                D0 = np.diag(-rates)
                # D1: completion from phase i, restart in phase j with prob_j
                # D1[i,j] = rate_i * prob_j
                D1 = np.outer(rates, probs)
                return D0, D1
            elif 'rate' in proc_entry:
                # Exponential distribution
                mu = float(proc_entry['rate'])
                D0 = np.array([[-mu]])
                D1 = np.array([[mu]])
                return D0, D1

        return None, None

    def get_map_phase(state: np.ndarray, ist: int, k: int) -> int:
        """Get current MAP phase for (station, class) from state vector."""
        if (ist, k) not in map_var_offset:
            return 0
        idx = map_var_offset[(ist, k)]
        return int(state[idx])

    def set_map_phase(state: np.ndarray, ist: int, k: int, phase: int) -> np.ndarray:
        """Set MAP phase for (station, class) in state vector."""
        new_state = state.copy()
        if (ist, k) in map_var_offset:
            idx = map_var_offset[(ist, k)]
            new_state[idx] = phase
        return new_state

    def get_job_count(state: np.ndarray, ist: int, k: int) -> int:
        """Get total job count for (station, class) from state vector.

        For FCFS stations with buffer, this includes:
        - Jobs waiting in buffer (count of buffer positions with class k+1)
        - Jobs in service (sum of phase counts for class k)

        For SIRO stations, this includes:
        - Jobs waiting in buffer (count stored at buffer_start + k)
        - Jobs in service (sum of phase counts for class k)
        """
        if use_phase_aug and phase_offset is not None:
            # Get jobs in service from phase counts
            start_idx = phase_offset[ist, k]
            end_idx = start_idx + phases[ist, k]
            in_service = int(sum(state[start_idx:end_idx]))

            # For FCFS stations, also count buffer jobs for this class
            if ist in fcfs_stations:
                buffer_start = fcfs_buffer_start.get(ist, -1)
                max_buf = fcfs_max_buffer.get(ist, 0)
                if buffer_start >= 0 and max_buf > 0:
                    # Buffer stores class IDs (1-based), count entries matching class k
                    in_buffer = sum(1 for i in range(max_buf) if int(state[buffer_start + i]) == k + 1)
                    return in_service + in_buffer
            # For SIRO stations, count buffer jobs (count-based)
            elif ist in siro_stations:
                buffer_start = siro_buffer_start.get(ist, -1)
                if buffer_start >= 0:
                    in_buffer = int(state[buffer_start + k])
                    return in_service + in_buffer

            return in_service
        else:
            return int(state[ist * K + k])

    def get_phase_counts(state: np.ndarray, ist: int, k: int) -> np.ndarray:
        """Get phase counts for (station, class) from state vector."""
        if use_phase_aug and phase_offset is not None:
            start_idx = phase_offset[ist, k]
            end_idx = start_idx + phases[ist, k]
            return np.array([int(x) for x in state[start_idx:end_idx]])
        else:
            # Single phase
            return np.array([int(state[ist * K + k])])

    def set_job_count(state: np.ndarray, ist: int, k: int, delta: int, phase_idx: int = -1) -> np.ndarray:
        """
        Modify job count for (station, class) in state vector.

        Args:
            state: Current state vector
            ist: Station index
            k: Class index
            delta: Change in job count (+1 for arrival, -1 for departure)
            phase_idx: Phase index to modify. If -1:
                       - For arrivals (delta > 0): use first phase (phase 0), or buffer for FCFS
                       - For departures (delta < 0): find first phase with jobs

        Returns:
            New state vector with modified job count
        """
        new_state = state.copy()
        if use_phase_aug and phase_offset is not None:
            # Check if this is an FCFS or SIRO station
            is_fcfs_station = ist in fcfs_stations
            is_siro_station = ist in siro_stations
            buffer_start = fcfs_buffer_start.get(ist, -1) if is_fcfs_station else -1
            phases_start = fcfs_phases_start.get(ist, -1) if is_fcfs_station else -1
            max_buf = fcfs_max_buffer.get(ist, 0) if is_fcfs_station else 0

            # SIRO buffer handling
            siro_buf_start = siro_buffer_start.get(ist, -1) if is_siro_station else -1
            siro_ph_start = siro_phases_start.get(ist, -1) if is_siro_station else -1

            if delta > 0 and is_siro_station and siro_buf_start >= 0:
                # SIRO arrival: check if all servers are busy
                total_in_service = 0
                for kk in range(K):
                    for p in range(phases[ist, kk]):
                        idx = siro_ph_start + sum(phases[ist, :kk]) + p
                        total_in_service += int(new_state[idx])

                n_servers_ist = int(nservers[ist]) if ist < len(nservers) else 1

                if total_in_service >= n_servers_ist:
                    # All servers busy - new arrival goes to buffer (increment class count)
                    new_state[siro_buf_start + k] += 1
                    return new_state
                else:
                    # Free server available - arrival goes directly to service (phase 0)
                    if phase_idx < 0:
                        phase_idx = 0
                    class_phase_start = siro_ph_start + sum(phases[ist, :k])
                    new_state[class_phase_start + phase_idx] += delta
                    return new_state

            if delta > 0 and is_fcfs_station and buffer_start >= 0 and max_buf > 0:
                # FCFS/HOL/LCFS/LCFSPR arrival: check if all servers are busy
                total_in_service = 0
                for kk in range(K):
                    for p in range(phases[ist, kk]):
                        idx = phases_start + sum(phases[ist, :kk]) + p
                        total_in_service += int(new_state[idx])

                # Get number of servers at this station
                n_servers_ist = int(nservers[ist]) if ist < len(nservers) else 1

                # Get scheduling strategy for this station
                ist_sched = sn.sched.get(ist, SchedStrategy.FCFS) if hasattr(sn, 'sched') and sn.sched else SchedStrategy.FCFS

                if total_in_service >= n_servers_ist:
                    # All servers busy - behavior depends on scheduling strategy
                    if _sched_is(ist_sched, 'LCFSPR'):
                        # LCFSPR: arriving job PREEMPTS current job in service
                        # 1. Find which class is currently in service
                        # 2. Move that job to buffer (as newest = leftmost)
                        # 3. Put arriving job in service

                        # Find class currently in service
                        preempted_class = -1
                        for kk in range(K):
                            class_phase_start = phases_start + sum(phases[ist, :kk])
                            for p in range(phases[ist, kk]):
                                if new_state[class_phase_start + p] > 0:
                                    preempted_class = kk
                                    # Remove from service
                                    new_state[class_phase_start + p] -= 1
                                    break
                            if preempted_class >= 0:
                                break

                        if preempted_class >= 0:
                            # Move preempted job to buffer (as newest = leftmost position)
                            # Buffer format: [padding..., oldest, ..., newest] but we store
                            # newest at the leftmost filled position
                            # Find the leftmost empty position to place the preempted job
                            # This is "one position left of current leftmost filled"
                            leftmost_filled = -1
                            for buf_pos in range(max_buf):
                                if new_state[buffer_start + buf_pos] > 0:
                                    leftmost_filled = buf_pos
                                    break

                            if leftmost_filled > 0:
                                # Put preempted job one position to the left of oldest
                                new_state[buffer_start + leftmost_filled - 1] = preempted_class + 1
                            elif leftmost_filled == -1:
                                # Buffer is empty - put at rightmost position
                                new_state[buffer_start + max_buf - 1] = preempted_class + 1
                            else:
                                # Buffer full (leftmost_filled == 0), cannot preempt
                                # Return invalid state
                                new_state[buffer_start] = -1
                                return new_state

                        # Put arriving job in service (phase 0)
                        if phase_idx < 0:
                            phase_idx = 0
                        idx = phase_offset[ist, k] + phase_idx
                        new_state[idx] += 1
                        return new_state
                    else:
                        # FCFS/HOL/LCFS (non-preemptive): new arrival goes to buffer
                        # Buffer is right-justified: [padding..., oldest, ..., newest]
                        # New arrival goes to position immediately LEFT of oldest job (leftmost filled)
                        # Find the leftmost filled position, then put new job one position to its left
                        leftmost_filled = -1
                        for buf_pos in range(max_buf):  # Search from left to right
                            if new_state[buffer_start + buf_pos] > 0:
                                leftmost_filled = buf_pos
                                break
                        if leftmost_filled > 0:
                            # Put new arrival one position to the left of oldest
                            new_state[buffer_start + leftmost_filled - 1] = k + 1  # 1-based class ID
                            return new_state
                        elif leftmost_filled == -1:
                            # Buffer is empty - put at rightmost position (will be only job)
                            new_state[buffer_start + max_buf - 1] = k + 1
                            return new_state
                        else:
                            # leftmost_filled == 0, buffer is full - return invalid state
                            # Setting a buffer position to -1 ensures this state won't be
                            # found in the state space, correctly blocking the arrival
                            new_state[buffer_start] = -1
                            return new_state
                else:
                    # Free server available - arrival goes directly to service (phase 0)
                    # Do NOT set buffer marker - buffer only tracks WAITING jobs
                    if phase_idx < 0:
                        phase_idx = 0
                    idx = phase_offset[ist, k] + phase_idx
                    new_state[idx] += delta
                    return new_state

            # For non-FCFS stations with arrivals, check if cutoff would be exceeded
            if delta > 0 and not is_fcfs_station:
                # Check if adding a job would exceed cutoff for this (station, class)
                current_count = get_job_count(state, ist, k)
                station_cutoff = get_cutoff(ist, k)
                if current_count >= station_cutoff:
                    # At or above cutoff - block arrival by returning invalid state
                    idx = phase_offset[ist, k]
                    new_state[idx] = -1
                    return new_state

            if phase_idx < 0:
                # Auto-select phase
                start_idx = phase_offset[ist, k]
                n_phases = phases[ist, k]
                if delta > 0:
                    # Arrival: add to first phase
                    phase_idx = 0
                else:
                    # Departure: find first phase with jobs
                    for p in range(n_phases):
                        if new_state[start_idx + p] > 0:
                            phase_idx = p
                            break
                    else:
                        # No jobs found - use first phase (will create invalid state)
                        phase_idx = 0
            idx = phase_offset[ist, k] + phase_idx
            new_state[idx] += delta
        else:
            new_state[ist * K + k] += delta
        return new_state

    def get_entry_probs(ist: int, k: int) -> np.ndarray:
        """
        Get entry probabilities for (station, class).

        For HyperExp: returns probs array (distributed across phases)
        For Erlang: returns [1, 0, 0, ...] (always start in phase 0)
        For Exp: returns [1.0]
        """
        if not use_phase_aug or phase_offset is None:
            return np.array([1.0])

        n_phases = phases[ist, k]
        if n_phases <= 1:
            return np.array([1.0])

        # Get proc entry for this (station, class)
        if not hasattr(sn, 'proc') or sn.proc is None:
            return np.array([1.0] + [0.0] * (n_phases - 1))

        proc_is_list = isinstance(sn.proc, list)
        if proc_is_list:
            if ist >= len(sn.proc) or sn.proc[ist] is None:
                return np.array([1.0] + [0.0] * (n_phases - 1))
            station_proc = sn.proc[ist]
        else:
            if ist not in sn.proc:
                return np.array([1.0] + [0.0] * (n_phases - 1))
            station_proc = sn.proc[ist]

        proc_entry = None
        if isinstance(station_proc, (list, tuple)):
            if k < len(station_proc):
                proc_entry = station_proc[k]
        elif isinstance(station_proc, dict):
            proc_entry = station_proc.get(k)

        if proc_entry is None:
            return np.array([1.0] + [0.0] * (n_phases - 1))

        if isinstance(proc_entry, dict):
            if 'probs' in proc_entry and 'rates' in proc_entry:
                # HyperExp: entry probability = probs
                return np.array(proc_entry['probs'])
            elif 'k' in proc_entry:
                # Erlang: always enter phase 0
                return np.array([1.0] + [0.0] * (n_phases - 1))
            else:
                # Exp: single phase
                return np.array([1.0])

        # For PH/APH with [alpha, T] format, extract alpha as entry probabilities
        if isinstance(proc_entry, (list, tuple)) and len(proc_entry) >= 2:
            first_elem = proc_entry[0]
            if isinstance(first_elem, np.ndarray):
                first_elem = np.atleast_1d(first_elem)
                # Check if first element is 1D (alpha vector) and second is 2D (T matrix)
                if first_elem.ndim == 1 and len(first_elem) == n_phases:
                    # This is [alpha, T] format - alpha is the entry probability
                    return first_elem.copy()

        # Default: enter first phase
        return np.array([1.0] + [0.0] * (n_phases - 1))

    def get_state_matrix(state: np.ndarray) -> np.ndarray:
        """Get job counts as (M, K) matrix from state vector."""
        result = np.zeros((M, K))
        for ist in range(M):
            for k in range(K):
                result[ist, k] = get_job_count(state, ist, k)
        return result

    # Get station to node mapping
    station_to_node = None
    if hasattr(sn, 'stationToNode') and sn.stationToNode is not None:
        station_to_node = np.asarray(sn.stationToNode).flatten()

    # Get node to station mapping
    node_to_station = None
    if hasattr(sn, 'nodeToStation') and sn.nodeToStation is not None:
        node_to_station = np.asarray(sn.nodeToStation).flatten()

    # Handle cutoff as scalar or matrix for state validation
    cutoff = options.cutoff
    cutoff_arr = np.atleast_2d(cutoff)
    is_matrix_cutoff = cutoff_arr.shape[0] > 1 or cutoff_arr.shape[1] > 1

    def is_within_cutoff(new_state: np.ndarray) -> bool:
        """Check if state is within cutoff bounds."""
        if is_matrix_cutoff:
            # Reshape state to (M, K) and compare with cutoff matrix
            state_matrix = new_state.reshape(M, K)
            # Handle different cutoff matrix layouts
            if cutoff_arr.shape[0] >= M and cutoff_arr.shape[1] >= K:
                return np.all(state_matrix <= cutoff_arr[:M, :K])
            elif cutoff_arr.shape[0] >= K and cutoff_arr.shape[1] >= M:
                return np.all(state_matrix <= cutoff_arr[:K, :M].T)
            else:
                # Fallback: use scalar comparison
                return np.all(new_state <= cutoff_arr.flat[0])
        else:
            return np.all(new_state <= cutoff_arr.flat[0])

    def get_cutoff(ist: int, k: int) -> int:
        """Get cutoff for station ist and class k."""
        if is_matrix_cutoff:
            # Matrix cutoff: index by station and class
            if cutoff_arr.shape[0] >= M and cutoff_arr.shape[1] >= K:
                return int(cutoff_arr[ist, k])
            elif cutoff_arr.shape[0] >= K and cutoff_arr.shape[1] >= M:
                # Transposed: (K x M) layout
                return int(cutoff_arr[k, ist])
            else:
                return int(cutoff_arr.flat[0]) if cutoff_arr.size > 0 else 10
        else:
            return int(cutoff_arr.flat[0])

    # Get FCFS station information for proper departure rate computation
    fcfs_stations = rrobin_info.get('fcfs_stations', set())
    fcfs_max_buffer = rrobin_info.get('fcfs_max_buffer', {})

    # Get SIRO station information
    siro_stations = rrobin_info.get('siro_stations', set())

    # Compute buffer offsets in the state vector
    # For each station, we need to know where its data starts in the state
    fcfs_buffer_start = {}  # Maps ist -> starting index of buffer in state
    fcfs_phases_start = {}  # Maps ist -> starting index of phases in state
    siro_buffer_start = {}  # Maps ist -> starting index of SIRO buffer counts
    siro_phases_start = {}  # Maps ist -> starting index of SIRO phases

    # Get skip_stations from rrobin_info (Source/Sink stations to exclude)
    skip_stations = rrobin_info.get('skip_stations', set())

    if use_phase_aug and (fcfs_stations or siro_stations):
        # Compute offsets based on state structure
        # State format: [station0_data, station1_data, ...]
        # For FCFS station: [buffer_pos..., phases_class0..., phases_class1..., ...]
        # For SIRO station: [buffer_count_class0, ..., buffer_count_classK-1, phases_class0..., ...]
        # For non-FCFS/non-SIRO station: [phases_class0..., phases_class1..., ...]
        # Skip Source/Sink stations as they don't contribute to state
        current_offset = 0
        for ist in range(M):
            # Skip Source/Sink stations
            if ist in skip_stations:
                fcfs_buffer_start[ist] = -1
                fcfs_phases_start[ist] = -1
                siro_buffer_start[ist] = -1
                siro_phases_start[ist] = -1
                continue
            if ist in fcfs_stations:
                max_buf = fcfs_max_buffer.get(ist, 0)
                fcfs_buffer_start[ist] = current_offset
                fcfs_phases_start[ist] = current_offset + max_buf
                siro_buffer_start[ist] = -1
                siro_phases_start[ist] = -1
                current_offset += max_buf + sum(phases[ist, :])
            elif ist in siro_stations:
                # SIRO: buffer counts (K elements) + phases
                siro_buffer_start[ist] = current_offset
                siro_phases_start[ist] = current_offset + K
                fcfs_buffer_start[ist] = -1
                fcfs_phases_start[ist] = -1
                current_offset += K + sum(phases[ist, :])
            else:
                fcfs_buffer_start[ist] = -1  # Not FCFS
                fcfs_phases_start[ist] = current_offset
                siro_buffer_start[ist] = -1
                siro_phases_start[ist] = current_offset
                current_offset += sum(phases[ist, :])

    def get_fcfs_class_in_service(state: np.ndarray, ist: int) -> int:
        """
        Determine which class is in service for an FCFS station.

        Returns:
            Class index (0-based) of the class in service, or -1 if no jobs in service.
        """
        if ist not in fcfs_stations:
            return -1

        # For FCFS, look at the server phases to see which class has jobs in service
        phases_start = fcfs_phases_start.get(ist, -1)
        if phases_start < 0:
            return -1

        # Check each class for non-zero phase counts
        for k in range(K):
            n_phases_k = phases[ist, k]
            phase_sum = sum(state[phases_start + sum(phases[ist, :j]) + p]
                           for j in range(k) for p in range(phases[ist, j]))
            # Actually, calculate offset correctly
            class_phase_start = phases_start + sum(phases[ist, :k])
            class_jobs_in_service = sum(int(state[class_phase_start + p]) for p in range(n_phases_k))
            if class_jobs_in_service > 0:
                return k
        return -1

    def get_fcfs_jobs_in_service(state: np.ndarray, ist: int, k: int) -> int:
        """
        Get number of class k jobs in service at FCFS station ist.

        For FCFS with single server, this is either 0 or 1.
        """
        if ist not in fcfs_stations:
            return 0

        phases_start = fcfs_phases_start.get(ist, -1)
        if phases_start < 0:
            return 0

        # Calculate offset for class k phases
        class_phase_start = phases_start + sum(phases[ist, :k])
        n_phases_k = phases[ist, k]
        return sum(int(state[class_phase_start + p]) for p in range(n_phases_k))

    def fcfs_promote_from_buffer_with_alpha(state: np.ndarray, ist: int, sched=None, classprio=None) -> List[Tuple[np.ndarray, float, int]]:
        """
        For FCFS/HOL/LCFS station with buffer, return possible promotion states with alpha probabilities.

        When a job completes service, the next job in the buffer should enter service.
        For PH/APH distributions, the starting phase is chosen according to the alpha
        (initial probability) distribution.

        The selection of which job is promoted depends on the scheduling strategy:
        - FCFS: Oldest job (rightmost non-zero position in buffer)
        - HOL: Highest priority job (lowest classprio value), then FCFS within priority
        - LCFS: Newest job (leftmost non-zero position in buffer)

        Args:
            state: Current state vector (will be copied, not modified)
            ist: Station index
            sched: Scheduling strategy (optional, defaults to FCFS behavior)
            classprio: Array of class priorities (required for HOL scheduling)

        Returns:
            List of (new_state, probability, class_k) tuples for each possible starting phase.
            Empty list if no jobs in buffer.
        """
        if ist not in fcfs_stations:
            return []

        buffer_start = fcfs_buffer_start.get(ist, -1)
        phases_start = fcfs_phases_start.get(ist, -1)
        max_buf = fcfs_max_buffer.get(ist, 0)

        if buffer_start < 0 or max_buf <= 0:
            return []

        # Find the job to promote based on scheduling strategy
        buf_pos = -1

        if _sched_is(sched, 'HOL') and classprio is not None:
            # HOL: Find highest priority job (lowest priority value), then rightmost (FCFS) within same priority
            # Collect all buffer positions with jobs
            occupied_positions = []
            for i in range(max_buf):
                buf_val = int(state[buffer_start + i])
                if buf_val > 0:
                    class_k = buf_val - 1  # 0-based class index
                    prio = classprio[class_k] if class_k < len(classprio) else float('inf')
                    occupied_positions.append((i, class_k, prio))

            if occupied_positions:
                # Find minimum priority (highest priority level)
                min_prio = min(p for _, _, p in occupied_positions)
                # Among positions with min priority, find rightmost (oldest in FCFS order)
                candidates = [(pos, ck) for pos, ck, p in occupied_positions if p == min_prio]
                buf_pos = max(pos for pos, _ in candidates)  # rightmost position
        elif _sched_is(sched, 'LCFS', 'LCFSPR'):
            # LCFS/LCFSPR: Find newest job (leftmost non-zero position)
            for i in range(max_buf):  # Search from left to right
                buf_val = int(state[buffer_start + i])
                if buf_val > 0:
                    buf_pos = i
                    break
        else:
            # FCFS (default): Find oldest job (rightmost non-zero position)
            for i in range(max_buf - 1, -1, -1):  # Search from right to left
                buf_val = int(state[buffer_start + i])
                if buf_val > 0:
                    buf_pos = i
                    break

        if buf_pos < 0:
            # No jobs in buffer
            return []

        # Get the class of the job to promote
        buf_val = int(state[buffer_start + buf_pos])
        class_k = buf_val - 1  # Convert from 1-based to 0-based class index

        # Get entry probabilities (alpha) for this class
        entry_probs = get_entry_probs(ist, class_k)

        results = []
        n_phases_k = phases[ist, class_k]
        class_phase_start = phases_start + sum(phases[ist, :class_k])

        for phase_idx, prob in enumerate(entry_probs):
            if prob > 0 and phase_idx < n_phases_k:
                new_state = state.copy()

                # Collect all buffer markers (excluding the promoted job)
                remaining_markers = []
                for i in range(max_buf):
                    if i != buf_pos and new_state[buffer_start + i] > 0:
                        remaining_markers.append(int(new_state[buffer_start + i]))

                # Clear entire buffer
                for i in range(max_buf):
                    new_state[buffer_start + i] = 0

                # Re-pack buffer: place REMAINING jobs at rightmost positions (MATLAB format)
                # The promoted job moves to SERVICE, NOT buffer
                # Only remaining_markers stay in buffer
                if remaining_markers:
                    n_remaining = len(remaining_markers)
                    start_pos = max_buf - n_remaining
                    for i, marker in enumerate(remaining_markers):
                        new_state[buffer_start + start_pos + i] = marker

                # Add promoted job to service at this phase (NOT to buffer)
                new_state[class_phase_start + phase_idx] += 1
                results.append((new_state, prob, class_k))

        return results

    def fcfs_promote_from_buffer(state: np.ndarray, ist: int) -> np.ndarray:
        """
        For FCFS station with buffer, promote the first waiting job to service (phase 1 only).

        DEPRECATED: Use fcfs_promote_from_buffer_with_alpha for correct PH/APH handling.
        This function is kept for backward compatibility but always uses phase 1.
        """
        results = fcfs_promote_from_buffer_with_alpha(state, ist)
        if results:
            # Return the first result (shouldn't be used in new code)
            return results[0][0]
        return state

    def siro_get_jobs_in_service(state: np.ndarray, ist: int, k: int) -> int:
        """Get number of class k jobs in service at SIRO station ist."""
        if ist not in siro_stations:
            return 0
        phases_start = siro_phases_start.get(ist, -1)
        if phases_start < 0:
            return 0
        # Calculate offset for class k phases
        class_phase_start = phases_start + sum(phases[ist, :k])
        n_phases_k = phases[ist, k]
        return sum(int(state[class_phase_start + p]) for p in range(n_phases_k))

    def siro_get_buffer_count(state: np.ndarray, ist: int, k: int) -> int:
        """Get buffer count for class k at SIRO station ist."""
        if ist not in siro_stations:
            return 0
        buffer_start = siro_buffer_start.get(ist, -1)
        if buffer_start < 0:
            return 0
        return int(state[buffer_start + k])

    def siro_get_total_jobs(state: np.ndarray, ist: int, k: int) -> int:
        """Get total jobs (buffer + service) for class k at SIRO station ist."""
        return siro_get_buffer_count(state, ist, k) + siro_get_jobs_in_service(state, ist, k)

    def siro_get_total_at_station(state: np.ndarray, ist: int) -> int:
        """Get total jobs at SIRO station (all classes)."""
        total = 0
        for k in range(K):
            total += siro_get_total_jobs(state, ist, k)
        return total

    def siro_promote_from_buffer_with_alpha(state: np.ndarray, ist: int, k: int) -> List[Tuple[np.ndarray, float, int]]:
        """
        For SIRO station with buffer, promote a class k job from buffer to service.

        SIRO selects randomly from buffer, but we just pick specified class k.
        The starting phase is chosen according to alpha distribution.

        Returns:
            List of (new_state, probability, class_k) tuples for each possible starting phase.
            Empty list if no class k jobs in buffer.
        """
        if ist not in siro_stations:
            return []

        buffer_start = siro_buffer_start.get(ist, -1)
        phases_start = siro_phases_start.get(ist, -1)

        if buffer_start < 0 or phases_start < 0:
            return []

        # Check if there's a class k job in buffer
        buf_count = int(state[buffer_start + k])
        if buf_count <= 0:
            return []

        # Get entry probabilities (alpha) for this class
        entry_probs = get_entry_probs(ist, k)

        results = []
        n_phases_k = phases[ist, k]
        class_phase_start = phases_start + sum(phases[ist, :k])

        for phase_idx, prob in enumerate(entry_probs):
            if prob > 0 and phase_idx < n_phases_k:
                new_state = state.copy()

                # Decrement buffer count for class k
                new_state[buffer_start + k] -= 1

                # Add job to service at this phase
                new_state[class_phase_start + phase_idx] += 1

                results.append((new_state, prob, k))

        return results

    # Build hash map for O(1) state lookup instead of O(n) linear search
    state_map = _build_state_index_map(state_space)

    # Get service rates
    if hasattr(sn, 'rates') and sn.rates is not None:
        rates = np.asarray(sn.rates)
    else:
        rates = np.ones((M, K))

    # Get routing probabilities
    if hasattr(sn, 'rt') and sn.rt is not None:
        P = np.asarray(sn.rt)
    else:
        # Default: uniform routing
        P = np.ones((M * K, M * K)) / (M * K)

    # Get number of servers
    if hasattr(sn, 'nservers') and sn.nservers is not None:
        nservers = np.asarray(sn.nservers).flatten()
    else:
        nservers = np.ones(M)

    # Get load-dependent scaling
    lldscaling = None
    if hasattr(sn, 'lldscaling') and sn.lldscaling is not None:
        lldscaling = np.asarray(sn.lldscaling)

    # Track which stations are infinite servers
    inf_server_stations = set()
    if hasattr(sn, 'sched') and sn.sched is not None:
        for ist, sched_val in sn.sched.items():
            if _sched_is(sched_val, 'INF'):
                inf_server_stations.add(ist)

    def get_load_scaling(ist: int, total_jobs: int) -> float:
        """Get service rate scaling factor for station ist with total_jobs present."""
        if total_jobs <= 0:
            return 0.0  # No jobs, no service
        # For infinite servers, each job gets its own server
        if ist in inf_server_stations:
            return float(total_jobs)
        if lldscaling is not None and ist < lldscaling.shape[0]:
            # lldscaling[ist, n-1] gives scaling when n jobs present
            idx = total_jobs - 1
            if lldscaling.ndim > 1 and idx < lldscaling.shape[1]:
                return lldscaling[ist, idx]
            elif lldscaling.ndim > 1:
                return lldscaling[ist, -1]  # Use last value if beyond range
        # Fall back to min(n, c) behavior
        c = nservers[ist] if ist < len(nservers) else 1
        return min(total_jobs, c)

    # Identify Source station (EXT scheduling) for open network arrivals
    # Use sn_has_open_classes to properly handle mixed networks
    is_open = sn_has_open_classes(sn)
    source_station = -1
    if is_open and hasattr(sn, 'sched'):
        for ist, sched_val in sn.sched.items():
            # Check for EXT scheduling (Source station)
            if _sched_is(sched_val, 'EXT') or (isinstance(sched_val, int) and sched_val == SchedStrategy.EXT.value):
                source_station = ist
                break

    # Extract class priorities for HOL scheduling (once, before the main loop)
    classprio = None
    if hasattr(sn, 'classprio') and sn.classprio is not None:
        classprio = np.asarray(sn.classprio).flatten()

    # Build transitions
    for s, state in enumerate(state_space):
        # Get job counts as (M, K) matrix from state vector
        state_matrix = get_state_matrix(state)

        # === External arrivals from Source ===
        # For open networks, Source generates arrivals that enter the next station
        # Handle routing through non-station nodes (like Router with RROBIN)
        if source_station >= 0:
            source_node = int(station_to_node[source_station]) if station_to_node is not None and source_station < len(station_to_node) else source_station

            for k in range(K):
                # Arrival rate at source
                arrival_rate = rates[source_station, k] if source_station < rates.shape[0] and k < rates.shape[1] else 0

                if arrival_rate <= 0:
                    continue

                # Get direct destinations from connection matrix
                conn = np.asarray(sn.connmatrix) if hasattr(sn, 'connmatrix') and sn.connmatrix is not None else None
                if conn is not None:
                    direct_dests = np.where(conn[source_node, :] > 0)[0]
                else:
                    direct_dests = []

                for dest_node in direct_dests:
                    # Resolve routing through non-station nodes
                    final_node, final_station, new_state = _resolve_routing_through_non_stations(
                        sn, source_node, dest_node, k, rrobin_info, state, rr_var_map, M, K
                    )

                    if final_station >= 0 and final_station < M and final_station != source_station:
                        # Arrival to final station, same class (no class switching at Router)
                        # Get entry probabilities for destination
                        entry_probs = get_entry_probs(final_station, k)
                        for entry_phase, entry_prob in enumerate(entry_probs):
                            if entry_prob <= 0:
                                continue
                            # Use phase-aware state modification with entry phase
                            arrival_state = set_job_count(new_state, final_station, k, +1, phase_idx=entry_phase)

                            # Check if within cutoff (only for open networks)
                            ns = _find_state_index_fast(state_map, arrival_state)
                            if ns >= 0:
                                # Probability is 1/num_direct_dests if no RROBIN at source
                                # (RROBIN state already handled in resolve function)
                                p = 1.0 / len(direct_dests) if len(direct_dests) > 1 else 1.0
                                Q[s, ns] += arrival_rate * p * entry_prob
                                # Track departure from Source station for throughput computation
                                # This captures the effective arrival rate accounting for state
                                # space truncation (blocked arrivals when system is full)
                                depRates[s, source_station, k] += arrival_rate * p * entry_prob
                    elif final_station == -1:
                        # Destination is Sink - this shouldn't happen for arrivals
                        pass

        # === MAP phase transitions (D0 off-diagonal, no service completion) ===
        # These are transitions within the MAP process that don't complete service
        if has_map_fcfs:
            for (ist, k) in map_fcfs.keys():
                n_ik = state_matrix[ist, k]
                if n_ik <= 0:
                    continue  # No jobs, no MAP transitions

                D0, D1 = get_map_matrices(ist, k)
                if D0 is None:
                    continue

                current_map_phase = get_map_phase(state, ist, k)
                n_phases = D0.shape[0]

                # For multi-class FCFS: scale by probability this class is in service
                total_jobs = np.sum(state_matrix[ist, :])
                class_fraction = (n_ik / total_jobs) if total_jobs > 0 else 0
                scaling_d0 = get_load_scaling(ist, int(total_jobs)) if total_jobs > 0 else 0

                # D0 off-diagonal entries: phase transitions without completion
                # Scaled for multi-class approximation
                for j in range(n_phases):
                    if j == current_map_phase:
                        continue  # Skip diagonal
                    rate = D0[current_map_phase, j] * scaling_d0 * class_fraction
                    if rate <= 0:
                        continue

                    # Create new state with updated MAP phase (no job movement)
                    new_state = set_map_phase(state, ist, k, j)

                    ns = _find_state_index_fast(state_map, new_state)
                    if ns >= 0:
                        Q[s, ns] += rate

        # === Phase-type (non-MAP) phase transitions (D0 off-diagonal) at FCFS stations ===
        # For PH/APH/Erlang/HyperExp, phase counts are tracked in the state vector directly
        # D0 off-diagonal transitions move jobs between phases without service completion
        if use_phase_aug:
            for ist in range(M):
                if ist == source_station:
                    continue

                # Check scheduling strategy
                if hasattr(sn, 'sched') and sn.sched is not None:
                    sched = sn.sched.get(ist, SchedStrategy.FCFS)
                else:
                    sched = SchedStrategy.FCFS

                # Handle FCFS and similar scheduling strategies
                sched_name = _normalize_sched_strategy(sched)
                if sched_name not in {'FCFS', 'HOL', 'LCFS', 'LCFSPR', 'PS', 'DPS', 'GPS'}:
                    continue

                for k in range(K):
                    # Skip if this is a MAP distribution (handled separately above)
                    if (ist, k) in map_fcfs:
                        continue

                    n_phases_ik = phases[ist, k]
                    if n_phases_ik <= 1:
                        continue  # No internal phase transitions

                    D0, D1 = get_map_matrices(ist, k)
                    if D0 is None:
                        continue

                    # Get phase counts from state
                    phase_counts = get_phase_counts(state, ist, k)

                    # For multi-class: use PS approximation
                    total_jobs = np.sum(state_matrix[ist, :])
                    scaling_d0 = get_load_scaling(ist, int(total_jobs)) if total_jobs > 0 else 0

                    # For each source phase with jobs
                    for p_src in range(n_phases_ik):
                        n_src = int(phase_counts[p_src])
                        if n_src <= 0:
                            continue

                        # For each destination phase (D0 off-diagonal)
                        for p_dst in range(n_phases_ik):
                            if p_src == p_dst:
                                continue  # Skip diagonal

                            # D0 off-diagonal: phase transition rate
                            phase_transition_rate = D0[p_src, p_dst]
                            if phase_transition_rate <= 0:
                                continue

                            # Rate for phase transition:
                            # For FCFS/HOL/LCFS: full rate (only jobs in service progress)
                            # For PS/DPS/GPS: PS approximation (share of capacity)
                            if _sched_is(sched, 'FCFS', 'HOL', 'LCFS', 'LCFSPR'):
                                # FCFS-like: jobs in service get full rate
                                total_rate = n_src * phase_transition_rate * scaling_d0
                            else:
                                # PS-like: share rate among all jobs
                                total_rate = (n_src / total_jobs) * phase_transition_rate * scaling_d0 if total_jobs > 0 else 0

                            # Create new state: move one job from p_src to p_dst
                            new_state = state.copy()
                            start_idx = phase_offset[ist, k]
                            new_state[start_idx + p_src] -= 1
                            new_state[start_idx + p_dst] += 1

                            if np.all(new_state[:state_dim] >= 0):
                                ns = _find_state_index_fast(state_map, new_state)
                                if ns >= 0:
                                    Q[s, ns] += total_rate

        # === Service completions and internal routing ===
        for ist in range(M):
            # Skip source station - it doesn't hold jobs for service
            if ist == source_station:
                continue

            for k in range(K):
                n_ik = state_matrix[ist, k]
                if n_ik <= 0:
                    continue

                # Service completion at station ist, class k
                # Rate depends on scheduling discipline
                if hasattr(sn, 'sched') and sn.sched is not None:
                    sched = sn.sched.get(ist, SchedStrategy.FCFS)
                else:
                    sched = SchedStrategy.FCFS

                # Check if this is a MAP distribution at FCFS station
                is_map_fcfs_class = (ist, k) in map_fcfs
                mu = rates[ist, k] if ist < rates.shape[0] and k < rates.shape[1] else 1.0

                if _sched_is(sched, 'INF'):
                    # Infinite server: rate depends on phase-type distribution
                    n_phases_ik = phases[ist, k]
                    if use_phase_aug and n_phases_ik > 1:
                        # Phase-type distribution: need separate transitions for each completing phase
                        D0, D1 = get_map_matrices(ist, k)
                        if D0 is not None and D1 is not None:
                            phase_counts = get_phase_counts(state, ist, k)
                            # For each phase with completions, create separate routing transitions
                            for p in range(n_phases_ik):
                                n_p = int(phase_counts[p])
                                if n_p <= 0:
                                    continue
                                completion_rate_p = np.sum(D1[p, :])
                                if completion_rate_p <= 0:
                                    continue
                                # Rate for completions from this phase
                                rate_p = n_p * completion_rate_p
                                # Create transitions for each destination
                                src_idx = ist * K + k
                                for jst in range(M):
                                    if jst == source_station:
                                        continue
                                    for r in range(K):
                                        dst_idx = jst * K + r
                                        if src_idx < P.shape[0] and dst_idx < P.shape[1]:
                                            prob = P[src_idx, dst_idx]
                                        else:
                                            prob = 0
                                        if prob <= 0:
                                            continue
                                        # Get entry probabilities for destination
                                        entry_probs = get_entry_probs(jst, r)
                                        for entry_phase, entry_prob in enumerate(entry_probs):
                                            if entry_prob <= 0:
                                                continue
                                            # Create base state: remove from phase p
                                            base_state = state.copy()
                                            start_idx = phase_offset[ist, k]
                                            base_state[start_idx + p] -= 1  # Remove from completing phase
                                            if np.any(base_state[:state_dim] < 0):
                                                continue
                                            # FCFS/HOL/LCFS buffer promotion with alpha distribution
                                            if ist in fcfs_stations:
                                                promo_results = fcfs_promote_from_buffer_with_alpha(base_state, ist, sched, classprio)
                                                if promo_results:
                                                    # Multiple destination states based on alpha
                                                    for promo_state, promo_prob, _ in promo_results:
                                                        new_state = set_job_count(promo_state.copy(), jst, r, +1, phase_idx=entry_phase)
                                                        if np.any(new_state[:state_dim] < 0):
                                                            continue
                                                        ns = _find_state_index_fast(state_map, new_state)
                                                        if ns >= 0:
                                                            Q[s, ns] += rate_p * prob * entry_prob * promo_prob
                                                            depRates[s, ist, k] += rate_p * prob * entry_prob * promo_prob
                                                    continue  # Skip non-promotion path
                                            # SIRO buffer promotion with alpha distribution
                                            if ist in siro_stations:
                                                # Compute total buffer count for SIRO selection probability
                                                total_buf = sum(siro_get_buffer_count(base_state, ist, kk) for kk in range(K))
                                                if total_buf > 0:
                                                    found_promo = False
                                                    for buf_k in range(K):
                                                        buf_count_k = siro_get_buffer_count(base_state, ist, buf_k)
                                                        if buf_count_k > 0:
                                                            # Probability of selecting class buf_k
                                                            select_prob = buf_count_k / total_buf
                                                            promo_results = siro_promote_from_buffer_with_alpha(base_state, ist, buf_k)
                                                            for promo_state, promo_prob, _ in promo_results:
                                                                new_state = set_job_count(promo_state.copy(), jst, r, +1, phase_idx=entry_phase)
                                                                if np.any(new_state[:state_dim] < 0):
                                                                    continue
                                                                ns = _find_state_index_fast(state_map, new_state)
                                                                if ns >= 0:
                                                                    Q[s, ns] += rate_p * prob * entry_prob * promo_prob * select_prob
                                                                    depRates[s, ist, k] += rate_p * prob * entry_prob * promo_prob * select_prob
                                                                    found_promo = True
                                                    if found_promo:
                                                        continue  # Skip non-promotion path
                                            # No buffer jobs or not FCFS
                                            new_state = set_job_count(base_state.copy(), jst, r, +1, phase_idx=entry_phase)
                                            if np.any(new_state[:state_dim] < 0):
                                                continue
                                            ns = _find_state_index_fast(state_map, new_state)
                                            if ns >= 0:
                                                Q[s, ns] += rate_p * prob * entry_prob
                                                # Track departure rate for class k from station ist
                                                depRates[s, ist, k] += rate_p * prob * entry_prob
                            # Skip the normal routing below since we handled it here
                            continue
                        else:
                            # Fallback to aggregate rate
                            rate = n_ik * mu
                    else:
                        # Single phase (exponential): rate = n * mu
                        rate = n_ik * mu
                elif _sched_is(sched, 'DPS'):
                    # Discriminatory Processor Sharing: weighted by schedparam
                    total_jobs = np.sum(state_matrix[ist, :])
                    if total_jobs > 0:
                        # Get weight for this class (default 1.0)
                        w_k = 1.0
                        if hasattr(sn, 'schedparam') and sn.schedparam is not None:
                            if ist < sn.schedparam.shape[0] and k < sn.schedparam.shape[1]:
                                w_k = sn.schedparam[ist, k]
                        # Compute weighted share: sum of w_j * n_j for all classes
                        weighted_total = 0.0
                        for kk in range(K):
                            n_kk = state_matrix[ist, kk]
                            w_kk = 1.0
                            if hasattr(sn, 'schedparam') and sn.schedparam is not None:
                                if ist < sn.schedparam.shape[0] and kk < sn.schedparam.shape[1]:
                                    w_kk = sn.schedparam[ist, kk]
                            weighted_total += w_kk * n_kk
                        # Rate = (w_k * n_k / weighted_total) * scaling * mu
                        scaling = get_load_scaling(ist, int(total_jobs))
                        if weighted_total > 0:
                            rate = (w_k * n_ik / weighted_total) * scaling * mu
                        else:
                            rate = 0
                    else:
                        rate = 0
                elif _sched_is(sched, 'PSPRIO'):
                    # PS with Priority: only jobs at highest priority level get service
                    total_jobs = np.sum(state_matrix[ist, :])
                    if total_jobs <= 0:
                        rate = 0
                    else:
                        scaling = get_load_scaling(ist, int(total_jobs))
                        nservers_ist = nservers[ist] if ist < len(nservers) else 1

                        # Get class priorities (lower value = higher priority)
                        classprio = None
                        if hasattr(sn, 'classprio') and sn.classprio is not None:
                            classprio = np.asarray(sn.classprio).flatten()

                        if classprio is None or total_jobs <= nservers_ist:
                            # No priorities or all jobs get service: regular PS
                            rate = scaling * mu * (n_ik / total_jobs)
                        else:
                            # Find minimum priority value among classes with jobs present
                            present_classes = [kk for kk in range(K) if state_matrix[ist, kk] > 0]
                            min_prio = min(classprio[kk] for kk in present_classes)

                            if classprio[k] == min_prio:
                                # This class is at highest priority - gets PS among same priority
                                niprio = sum(state_matrix[ist, kk] for kk in range(K)
                                           if classprio[kk] == min_prio)
                                scaling_prio = min(niprio, nservers_ist)
                                rate = scaling_prio * mu * (n_ik / niprio)
                            else:
                                # Not highest priority: rate = 0
                                rate = 0

                elif _sched_is(sched, 'GPSPRIO'):
                    # GPS with Priority: weighted sharing among highest priority jobs
                    total_jobs = np.sum(state_matrix[ist, :])
                    if total_jobs <= 0:
                        rate = 0
                    else:
                        nservers_ist = nservers[ist] if ist < len(nservers) else 1

                        # Get class priorities
                        classprio = None
                        if hasattr(sn, 'classprio') and sn.classprio is not None:
                            classprio = np.asarray(sn.classprio).flatten()

                        # Get weights from schedparam
                        weights = np.ones(K)
                        if hasattr(sn, 'schedparam') and sn.schedparam is not None:
                            if ist < sn.schedparam.shape[0]:
                                weights = sn.schedparam[ist, :K].flatten()
                        weights = weights / np.sum(weights)  # Normalize

                        if classprio is None or total_jobs <= nservers_ist:
                            # No priorities or all jobs get service: regular GPS
                            # cir = min(nir, 1) - indicator of presence
                            cir = np.minimum(state_matrix[ist, :], 1)
                            weighted_total = np.sum(weights * cir)
                            if weighted_total > 0:
                                rate = mu * (n_ik / state_matrix[ist, k]) * weights[k] / weighted_total if state_matrix[ist, k] > 0 else 0
                            else:
                                rate = 0
                        else:
                            # Find minimum priority value among classes with jobs present
                            present_classes = [kk for kk in range(K) if state_matrix[ist, kk] > 0]
                            min_prio = min(classprio[kk] for kk in present_classes)

                            if classprio[k] == min_prio:
                                # This class is at highest priority - GPS among same priority
                                nirprio = np.zeros(K)
                                for kk in range(K):
                                    if classprio[kk] == min_prio:
                                        nirprio[kk] = state_matrix[ist, kk]

                                cir = np.minimum(nirprio, 1)
                                weighted_total = np.sum(weights * cir)
                                if weighted_total > 0 and nirprio[k] > 0:
                                    rate = mu * (n_ik / nirprio[k]) * weights[k] / weighted_total
                                else:
                                    rate = 0
                            else:
                                # Not highest priority: rate = 0
                                rate = 0
                else:
                    # FCFS, PS, SIRO, etc.
                    total_jobs = np.sum(state_matrix[ist, :])
                    scaling = get_load_scaling(ist, int(total_jobs))

                    # For FCFS stations with single-phase (Exp) distributions, only jobs in service get rate
                    if _sched_is(sched, 'FCFS', 'HOL', 'LCFS', 'LCFSPR') and ist in fcfs_stations:
                        # FCFS: only jobs in service complete - no PS-style sharing
                        # Each job in service completes independently at rate mu
                        # No scaling: the server constraint is enforced by state space (at most nservers jobs in service)
                        jobs_in_service_k = get_fcfs_jobs_in_service(state, ist, k)
                        if jobs_in_service_k > 0:
                            # This class has jobs in service
                            rate = jobs_in_service_k * mu
                        else:
                            # No jobs in service for this class
                            rate = 0
                    elif ist in siro_stations:
                        # SIRO: only jobs IN SERVICE complete, not buffer jobs
                        # Jobs in buffer wait until server is free
                        jobs_in_service_k = siro_get_jobs_in_service(state, ist, k)
                        if jobs_in_service_k > 0:
                            # Get total jobs in service (all classes) for PS-style sharing
                            total_in_service = siro_get_total_at_station(state, ist) - sum(
                                siro_get_buffer_count(state, ist, kk) for kk in range(K)
                            )
                            if total_in_service > 0:
                                # PS-style sharing among jobs in service
                                rate = scaling * mu * (jobs_in_service_k / total_in_service)
                            else:
                                rate = jobs_in_service_k * mu
                        else:
                            # No jobs in service for this class
                            rate = 0
                    else:
                        # PS, DPS, GPS: share rate among all jobs
                        rate = scaling * mu * (n_ik / total_jobs) if total_jobs > 0 else 0

                # === Special handling for phase-type distributions (PH, APH, Erlang, HyperExp) at FCFS stations ===
                # For phase-type distributions, service completions use D1 matrix with phase-dependent rates
                # This includes APH, PH, Erlang, HyperExp, and MAP distributions
                n_phases_ik = phases[ist, k]
                is_ph_distribution = use_phase_aug and n_phases_ik > 1 and not is_map_fcfs_class

                if is_ph_distribution:
                    D0, D1 = get_map_matrices(ist, k)
                    if D0 is not None and D1 is not None:
                        total_jobs = np.sum(state_matrix[ist, :])
                        scaling = get_load_scaling(ist, int(total_jobs))

                        # Get phase counts from the state
                        phase_counts = get_phase_counts(state, ist, k)

                        # For each phase with jobs, compute service completions
                        src_idx = ist * K + k
                        total_routing = 0.0

                        # Get node index for this station
                        node_idx = int(station_to_node[ist]) if station_to_node is not None and ist < len(station_to_node) else ist
                        is_rrobin = (node_idx, k) in rrobin_info['outlinks']

                        # Determine if this is an FCFS station with buffer ordering
                        is_fcfs_with_buffer = ist in fcfs_stations

                        for p in range(n_phases_ik):
                            n_p = int(phase_counts[p])
                            if n_p <= 0:
                                continue

                            # Completion rate from phase p = sum of D1[p, :] (row sum)
                            completion_rate_p = np.sum(D1[p, :])
                            if completion_rate_p <= 0:
                                continue

                            # Rate computation depends on scheduling discipline
                            if is_fcfs_with_buffer:
                                # FCFS: only the class in service completes
                                # Check if this class has jobs in service (non-zero phase counts)
                                jobs_in_service_k = get_fcfs_jobs_in_service(state, ist, k)
                                if jobs_in_service_k > 0:
                                    # This class is in service - full D1 rate applies
                                    # Each job in phase p completes independently at completion_rate_p
                                    # No scaling: the server constraint is enforced by state space (at most nservers jobs in service)
                                    rate_p = n_p * completion_rate_p
                                else:
                                    # This class is NOT in service - rate is 0
                                    rate_p = 0
                            elif _sched_is(sched, 'PSPRIO'):
                                # PS with Priority: only jobs at highest priority get service
                                nservers_ist = nservers[ist] if ist < len(nservers) else 1
                                classprio = None
                                if hasattr(sn, 'classprio') and sn.classprio is not None:
                                    classprio = np.asarray(sn.classprio).flatten()

                                if classprio is None or total_jobs <= nservers_ist:
                                    # No priorities or all jobs get service: regular PS
                                    scaling_prio = min(total_jobs, nservers_ist)
                                    rate_p = (n_p / total_jobs) * completion_rate_p * scaling_prio if total_jobs > 0 else 0
                                else:
                                    # Find minimum priority value among classes with jobs present
                                    present_classes = [kk for kk in range(K) if state_matrix[ist, kk] > 0]
                                    min_prio = min(classprio[kk] for kk in present_classes)

                                    if classprio[k] == min_prio:
                                        # This class is at highest priority - gets PS among same priority
                                        niprio = sum(state_matrix[ist, kk] for kk in range(K)
                                                   if classprio[kk] == min_prio)
                                        scaling_prio = min(niprio, nservers_ist)
                                        rate_p = (n_p / niprio) * completion_rate_p * scaling_prio if niprio > 0 else 0
                                    else:
                                        # Not highest priority: rate = 0
                                        rate_p = 0
                            elif _sched_is(sched, 'GPSPRIO'):
                                # GPS with Priority: weighted sharing among highest priority jobs
                                nservers_ist = nservers[ist] if ist < len(nservers) else 1
                                classprio = None
                                if hasattr(sn, 'classprio') and sn.classprio is not None:
                                    classprio = np.asarray(sn.classprio).flatten()

                                # Get weights from schedparam
                                weights = np.ones(K)
                                if hasattr(sn, 'schedparam') and sn.schedparam is not None:
                                    if ist < sn.schedparam.shape[0]:
                                        weights = sn.schedparam[ist, :K].flatten()
                                weights = weights / np.sum(weights)  # Normalize

                                if classprio is None or total_jobs <= nservers_ist:
                                    # No priorities or all jobs get service: regular GPS
                                    cir = np.minimum(state_matrix[ist, :], 1)
                                    weighted_total = np.sum(weights * cir)
                                    if weighted_total > 0 and state_matrix[ist, k] > 0:
                                        rate_p = completion_rate_p * (n_p / state_matrix[ist, k]) * weights[k] / weighted_total
                                    else:
                                        rate_p = 0
                                else:
                                    # Find minimum priority value among classes with jobs present
                                    present_classes = [kk for kk in range(K) if state_matrix[ist, kk] > 0]
                                    min_prio = min(classprio[kk] for kk in present_classes)

                                    if classprio[k] == min_prio:
                                        # This class is at highest priority - GPS among same priority
                                        nirprio = np.zeros(K)
                                        for kk in range(K):
                                            if classprio[kk] == min_prio:
                                                nirprio[kk] = state_matrix[ist, kk]

                                        cir = np.minimum(nirprio, 1)
                                        weighted_total = np.sum(weights * cir)
                                        if weighted_total > 0 and nirprio[k] > 0:
                                            rate_p = completion_rate_p * (n_p / nirprio[k]) * weights[k] / weighted_total
                                        else:
                                            rate_p = 0
                                    else:
                                        # Not highest priority: rate = 0
                                        rate_p = 0
                            elif _sched_is(sched, 'INF'):
                                # Infinite server: rate is independent of total jobs
                                rate_p = n_p * completion_rate_p
                            else:
                                # Non-FCFS (PS, DPS, etc.): use PS approximation
                                # rate = (n_p / total_jobs) * completion_rate_p * scaling
                                rate_p = (n_p / total_jobs) * completion_rate_p * scaling if total_jobs > 0 else 0

                            if rate_p <= 0:
                                continue

                            if is_rrobin:
                                # RROBIN routing
                                outlinks = rrobin_info['outlinks'][(node_idx, k)]
                                rr_var_idx = rr_var_map[(node_idx, k)]
                                current_rr_ptr = int(state[rr_var_idx])
                                dest_node = outlinks[current_rr_ptr]
                                next_rr_ptr = (current_rr_ptr + 1) % len(outlinks)

                                if node_to_station is not None and dest_node < len(node_to_station):
                                    dest_station = int(node_to_station[dest_node])
                                else:
                                    dest_station = dest_node

                                r = k  # No class switching for RROBIN

                                if dest_station >= 0 and dest_station < M:
                                    entry_probs = get_entry_probs(dest_station, r)
                                    for entry_phase, entry_prob in enumerate(entry_probs):
                                        if entry_prob <= 0:
                                            continue
                                        # Create base state: remove from phase p
                                        base_state = state.copy()
                                        start_idx = phase_offset[ist, k]
                                        base_state[start_idx + p] -= 1
                                        if np.any(base_state[:state_dim] < 0):
                                            continue
                                        # FCFS buffer promotion with alpha distribution
                                        if ist in fcfs_stations:
                                            promo_results = fcfs_promote_from_buffer_with_alpha(base_state, ist, sched, classprio)
                                            if promo_results:
                                                for promo_state, promo_prob, _ in promo_results:
                                                    new_state = set_job_count(promo_state.copy(), dest_station, r, +1, phase_idx=entry_phase)
                                                    new_state[rr_var_idx] = next_rr_ptr
                                                    if np.all(new_state[:state_dim] >= 0):
                                                        ns = _find_state_index_fast(state_map, new_state)
                                                        if ns >= 0:
                                                            Q[s, ns] += rate_p * entry_prob * promo_prob
                                                            total_routing += rate_p * entry_prob * promo_prob
                                                            depRates[s, ist, k] += rate_p * entry_prob * promo_prob
                                                continue
                                        # SIRO buffer promotion with alpha distribution
                                        if ist in siro_stations:
                                            total_buf = sum(siro_get_buffer_count(base_state, ist, kk) for kk in range(K))
                                            if total_buf > 0:
                                                found_promo = False
                                                for buf_k in range(K):
                                                    buf_count_k = siro_get_buffer_count(base_state, ist, buf_k)
                                                    if buf_count_k > 0:
                                                        select_prob = buf_count_k / total_buf
                                                        promo_results = siro_promote_from_buffer_with_alpha(base_state, ist, buf_k)
                                                        for promo_state, promo_prob, _ in promo_results:
                                                            new_state = set_job_count(promo_state.copy(), dest_station, r, +1, phase_idx=entry_phase)
                                                            new_state[rr_var_idx] = next_rr_ptr
                                                            if np.all(new_state[:state_dim] >= 0):
                                                                ns = _find_state_index_fast(state_map, new_state)
                                                                if ns >= 0:
                                                                    Q[s, ns] += rate_p * entry_prob * promo_prob * select_prob
                                                                    total_routing += rate_p * entry_prob * promo_prob * select_prob
                                                                    depRates[s, ist, k] += rate_p * entry_prob * promo_prob * select_prob
                                                                    found_promo = True
                                                if found_promo:
                                                    continue
                                        # No buffer jobs or not FCFS/SIRO
                                        new_state = set_job_count(base_state.copy(), dest_station, r, +1, phase_idx=entry_phase)
                                        new_state[rr_var_idx] = next_rr_ptr
                                        if np.all(new_state[:state_dim] >= 0):
                                            ns = _find_state_index_fast(state_map, new_state)
                                            if ns >= 0:
                                                Q[s, ns] += rate_p * entry_prob
                                                total_routing += rate_p * entry_prob
                                                depRates[s, ist, k] += rate_p * entry_prob
                                else:
                                    # Destination is Sink
                                    base_state = state.copy()
                                    start_idx = phase_offset[ist, k]
                                    base_state[start_idx + p] -= 1
                                    if np.any(base_state[:state_dim] < 0):
                                        continue
                                    # FCFS buffer promotion with alpha distribution
                                    if ist in fcfs_stations:
                                        promo_results = fcfs_promote_from_buffer_with_alpha(base_state, ist, sched, classprio)
                                        if promo_results:
                                            for promo_state, promo_prob, _ in promo_results:
                                                new_state = promo_state.copy()
                                                new_state[rr_var_idx] = next_rr_ptr
                                                if np.all(new_state[:state_dim] >= 0):
                                                    ns = _find_state_index_fast(state_map, new_state)
                                                    if ns >= 0:
                                                        Q[s, ns] += rate_p * promo_prob
                                                        total_routing += rate_p * promo_prob
                                                        depRates[s, ist, k] += rate_p * promo_prob
                                            continue
                                    # SIRO buffer promotion with alpha distribution
                                    if ist in siro_stations:
                                        total_buf = sum(siro_get_buffer_count(base_state, ist, kk) for kk in range(K))
                                        if total_buf > 0:
                                            found_promo = False
                                            for buf_k in range(K):
                                                buf_count_k = siro_get_buffer_count(base_state, ist, buf_k)
                                                if buf_count_k > 0:
                                                    select_prob = buf_count_k / total_buf
                                                    promo_results = siro_promote_from_buffer_with_alpha(base_state, ist, buf_k)
                                                    for promo_state, promo_prob, _ in promo_results:
                                                        new_state = promo_state.copy()
                                                        new_state[rr_var_idx] = next_rr_ptr
                                                        if np.all(new_state[:state_dim] >= 0):
                                                            ns = _find_state_index_fast(state_map, new_state)
                                                            if ns >= 0:
                                                                Q[s, ns] += rate_p * promo_prob * select_prob
                                                                total_routing += rate_p * promo_prob * select_prob
                                                                depRates[s, ist, k] += rate_p * promo_prob * select_prob
                                                                found_promo = True
                                            if found_promo:
                                                continue
                                    # No buffer jobs or not FCFS/SIRO
                                    new_state = base_state.copy()
                                    new_state[rr_var_idx] = next_rr_ptr
                                    if np.all(new_state[:state_dim] >= 0):
                                        ns = _find_state_index_fast(state_map, new_state)
                                        if ns >= 0:
                                            Q[s, ns] += rate_p
                                            total_routing += rate_p
                                            depRates[s, ist, k] += rate_p
                            else:
                                # Standard probabilistic routing
                                for jst in range(M):
                                    if jst == source_station:
                                        continue
                                    for r in range(K):
                                        dst_idx = jst * K + r
                                        if src_idx < P.shape[0] and dst_idx < P.shape[1]:
                                            prob = P[src_idx, dst_idx]
                                        else:
                                            prob = 0
                                        if prob <= 0:
                                            continue
                                        entry_probs = get_entry_probs(jst, r)
                                        for entry_phase, entry_prob in enumerate(entry_probs):
                                            if entry_prob <= 0:
                                                continue
                                            # Create base state: remove from phase p
                                            base_state = state.copy()
                                            start_idx = phase_offset[ist, k]
                                            base_state[start_idx + p] -= 1
                                            if np.any(base_state[:state_dim] < 0):
                                                continue
                                            # FCFS buffer promotion with alpha distribution
                                            if ist in fcfs_stations:
                                                promo_results = fcfs_promote_from_buffer_with_alpha(base_state, ist, sched, classprio)
                                                if promo_results:
                                                    for promo_state, promo_prob, _ in promo_results:
                                                        new_state = set_job_count(promo_state.copy(), jst, r, +1, phase_idx=entry_phase)
                                                        if np.any(new_state[:state_dim] < 0):
                                                            continue
                                                        ns = _find_state_index_fast(state_map, new_state)
                                                        if ns >= 0:
                                                            Q[s, ns] += rate_p * prob * entry_prob * promo_prob
                                                            total_routing += rate_p * prob * entry_prob * promo_prob
                                                            depRates[s, ist, k] += rate_p * prob * entry_prob * promo_prob
                                                    continue
                                            # SIRO buffer promotion with alpha distribution
                                            if ist in siro_stations:
                                                total_buf = sum(siro_get_buffer_count(base_state, ist, kk) for kk in range(K))
                                                if total_buf > 0:
                                                    found_promo = False
                                                    for buf_k in range(K):
                                                        buf_count_k = siro_get_buffer_count(base_state, ist, buf_k)
                                                        if buf_count_k > 0:
                                                            select_prob = buf_count_k / total_buf
                                                            promo_results = siro_promote_from_buffer_with_alpha(base_state, ist, buf_k)
                                                            for promo_state, promo_prob, _ in promo_results:
                                                                new_state = set_job_count(promo_state.copy(), jst, r, +1, phase_idx=entry_phase)
                                                                if np.any(new_state[:state_dim] < 0):
                                                                    continue
                                                                ns = _find_state_index_fast(state_map, new_state)
                                                                if ns >= 0:
                                                                    Q[s, ns] += rate_p * prob * entry_prob * promo_prob * select_prob
                                                                    total_routing += rate_p * prob * entry_prob * promo_prob * select_prob
                                                                    depRates[s, ist, k] += rate_p * prob * entry_prob * promo_prob * select_prob
                                                                    found_promo = True
                                                    if found_promo:
                                                        continue
                                            # No buffer jobs or not FCFS/SIRO
                                            new_state = set_job_count(base_state.copy(), jst, r, +1, phase_idx=entry_phase)
                                            if np.any(new_state[:state_dim] < 0):
                                                continue
                                            ns = _find_state_index_fast(state_map, new_state)
                                            if ns >= 0:
                                                Q[s, ns] += rate_p * prob * entry_prob
                                                total_routing += rate_p * prob * entry_prob
                                                depRates[s, ist, k] += rate_p * prob * entry_prob

                        # Handle departures to sink for open networks
                        if is_open:
                            for p in range(n_phases_ik):
                                n_p = int(phase_counts[p])
                                if n_p <= 0:
                                    continue
                                completion_rate_p = np.sum(D1[p, :])
                                if completion_rate_p <= 0:
                                    continue
                                # Rate depends on scheduling discipline
                                if is_fcfs_with_buffer:
                                    # FCFS: only the class in service completes
                                    jobs_in_service_k = get_fcfs_jobs_in_service(state, ist, k)
                                    if jobs_in_service_k > 0:
                                        rate_p = n_p * completion_rate_p * scaling
                                    else:
                                        rate_p = 0
                                else:
                                    # Non-FCFS: PS approximation
                                    rate_p = (n_p / total_jobs) * completion_rate_p * scaling if total_jobs > 0 else 0
                                # Check routing to outside (sink) based on P matrix
                                # Exclude routing to source_station - in open networks, routing TO source
                                # represents exits to Sink (from dtmc_stochcomp absorption)
                                exit_prob = 0.0
                                for jst in range(M):
                                    if jst == source_station:
                                        continue  # Routing to Source means exit in open networks
                                    for r in range(K):
                                        dst_idx = jst * K + r
                                        if src_idx < P.shape[0] and dst_idx < P.shape[1]:
                                            exit_prob += P[src_idx, dst_idx]
                                exit_prob = max(0.0, 1.0 - exit_prob)
                                if exit_prob > 0:
                                    base_state = state.copy()
                                    start_idx = phase_offset[ist, k]
                                    base_state[start_idx + p] -= 1
                                    if np.any(base_state[:state_dim] < 0):
                                        continue

                                    # FCFS buffer promotion with alpha distribution
                                    # When service completes, the next job in buffer enters service
                                    # Note: we do NOT clear buffer markers here - fcfs_promote_from_buffer_with_alpha
                                    # handles finding the oldest waiting job and moving it from buffer to service
                                    if ist in fcfs_stations:
                                        promo_results = fcfs_promote_from_buffer_with_alpha(base_state, ist, sched, classprio)
                                        if promo_results:
                                            for promo_state, promo_prob, _ in promo_results:
                                                if np.all(promo_state[:state_dim] >= 0):
                                                    ns = _find_state_index_fast(state_map, promo_state)
                                                    if ns >= 0:
                                                        Q[s, ns] += rate_p * exit_prob * promo_prob
                                                        depRates[s, ist, k] += rate_p * exit_prob * promo_prob
                                            continue
                                    # SIRO buffer promotion with alpha distribution
                                    if ist in siro_stations:
                                        total_buf = sum(siro_get_buffer_count(base_state, ist, kk) for kk in range(K))
                                        if total_buf > 0:
                                            found_promo = False
                                            for buf_k in range(K):
                                                buf_count_k = siro_get_buffer_count(base_state, ist, buf_k)
                                                if buf_count_k > 0:
                                                    select_prob = buf_count_k / total_buf
                                                    promo_results = siro_promote_from_buffer_with_alpha(base_state, ist, buf_k)
                                                    for promo_state, promo_prob, _ in promo_results:
                                                        if np.all(promo_state[:state_dim] >= 0):
                                                            ns = _find_state_index_fast(state_map, promo_state)
                                                            if ns >= 0:
                                                                Q[s, ns] += rate_p * exit_prob * promo_prob * select_prob
                                                                depRates[s, ist, k] += rate_p * exit_prob * promo_prob * select_prob
                                                                found_promo = True
                                            if found_promo:
                                                continue
                                    # No buffer jobs or not FCFS/SIRO - buffer already cleared above
                                    if np.all(base_state[:state_dim] >= 0):
                                        ns = _find_state_index_fast(state_map, base_state)
                                        if ns >= 0:
                                            Q[s, ns] += rate_p * exit_prob
                                            depRates[s, ist, k] += rate_p * exit_prob

                        continue  # Skip the standard routing code below

                # === Special handling for MAP distributions at FCFS stations ===
                # For MAP, service completions use D1 matrix with phase-dependent rates
                if is_map_fcfs_class:
                    D0, D1 = get_map_matrices(ist, k)
                    if D0 is not None and D1 is not None:
                        current_map_phase = get_map_phase(state, ist, k)
                        n_phases = D1.shape[0]

                        total_jobs = np.sum(state_matrix[ist, :])
                        scaling = get_load_scaling(ist, int(total_jobs))

                        # Determine if this is an FCFS station with buffer ordering
                        is_fcfs_with_buffer = ist in fcfs_stations

                        if is_fcfs_with_buffer:
                            # FCFS: only the class in service completes
                            jobs_in_service_k = get_fcfs_jobs_in_service(state, ist, k)
                            if jobs_in_service_k > 0:
                                # This class is in service - full D1 rate applies
                                class_fraction = 1.0
                            else:
                                # This class is NOT in service - rate is 0
                                class_fraction = 0.0
                        else:
                            # Non-FCFS: use PS approximation
                            class_fraction = (n_ik / total_jobs) if total_jobs > 0 else 0

                        # Service completion rate from phase i = sum of D1[i, :] (row sum)
                        total_d1_rate = np.sum(D1[current_map_phase, :]) * scaling * class_fraction

                        if total_d1_rate <= 0:
                            continue

                        # Calculate routing probabilities
                        src_idx = ist * K + k
                        total_routing = 0.0

                        # Get node index for this station
                        node_idx = int(station_to_node[ist]) if station_to_node is not None and ist < len(station_to_node) else ist

                        # Check if this node has RROBIN routing for class k
                        is_rrobin = (node_idx, k) in rrobin_info['outlinks']

                        # For each destination MAP phase j, the rate is D1[current_phase, j]
                        # Scaled by class fraction for multi-class approximation
                        for new_map_phase in range(n_phases):
                            d1_rate = D1[current_map_phase, new_map_phase] * scaling * class_fraction
                            if d1_rate <= 0:
                                continue

                            if is_rrobin:
                                # RROBIN routing with MAP
                                outlinks = rrobin_info['outlinks'][(node_idx, k)]
                                rr_var_idx = rr_var_map[(node_idx, k)]
                                current_rr_ptr = int(state[rr_var_idx])
                                dest_node = outlinks[current_rr_ptr]
                                next_rr_ptr = (current_rr_ptr + 1) % len(outlinks)

                                if node_to_station is not None and dest_node < len(node_to_station):
                                    dest_station = int(node_to_station[dest_node])
                                else:
                                    dest_station = dest_node

                                r = k  # No class switching for RROBIN

                                if dest_station >= 0 and dest_station < M:
                                    # Get entry probabilities for destination
                                    entry_probs = get_entry_probs(dest_station, r)
                                    for entry_phase, entry_prob in enumerate(entry_probs):
                                        if entry_prob <= 0:
                                            continue
                                        new_state = set_job_count(state, ist, k, -1)
                                        new_state = set_job_count(new_state, dest_station, r, +1, phase_idx=entry_phase)
                                        new_state = set_map_phase(new_state, ist, k, new_map_phase)
                                        new_state[rr_var_idx] = next_rr_ptr

                                        if np.all(new_state[:state_dim] >= 0):
                                            ns = _find_state_index_fast(state_map, new_state)
                                            if ns >= 0:
                                                Q[s, ns] += d1_rate * entry_prob
                                                total_routing += d1_rate * entry_prob
                                else:
                                    # Destination is Sink
                                    new_state = set_job_count(state, ist, k, -1)
                                    new_state = set_map_phase(new_state, ist, k, new_map_phase)
                                    new_state[rr_var_idx] = next_rr_ptr

                                    if np.all(new_state[:state_dim] >= 0):
                                        ns = _find_state_index_fast(state_map, new_state)
                                        if ns >= 0:
                                            Q[s, ns] += d1_rate
                                            total_routing += d1_rate
                            else:
                                # Standard probabilistic routing with MAP
                                for jst in range(M):
                                    if jst == source_station:
                                        continue
                                    for r in range(K):
                                        dst_idx = jst * K + r

                                        if src_idx < P.shape[0] and dst_idx < P.shape[1]:
                                            p = P[src_idx, dst_idx]
                                        else:
                                            p = 0

                                        if p <= 0:
                                            continue

                                        # Get entry probabilities for destination
                                        entry_probs = get_entry_probs(jst, r)
                                        for entry_phase, entry_prob in enumerate(entry_probs):
                                            if entry_prob <= 0:
                                                continue
                                            # Create new state with job movement and MAP phase update
                                            new_state = set_job_count(state, ist, k, -1)
                                            new_state = set_job_count(new_state, jst, r, +1, phase_idx=entry_phase)
                                            new_state = set_map_phase(new_state, ist, k, new_map_phase)

                                            if np.any(new_state[:state_dim] < 0):
                                                continue

                                            ns = _find_state_index_fast(state_map, new_state)
                                            if ns >= 0:
                                                Q[s, ns] += d1_rate * p * entry_prob
                                                total_routing += d1_rate * p * entry_prob

                        # Handle departures to sink for open networks
                        if is_open and total_routing < total_d1_rate:
                            exit_rate = total_d1_rate - total_routing
                            if exit_rate > 0:
                                for new_map_phase in range(n_phases):
                                    d1_rate_raw = D1[current_map_phase, new_map_phase] * scaling * class_fraction
                                    if d1_rate_raw <= 0:
                                        continue
                                    new_state = set_job_count(state, ist, k, -1)
                                    new_state = set_map_phase(new_state, ist, k, new_map_phase)

                                    if np.all(new_state[:state_dim] >= 0):
                                        ns = _find_state_index_fast(state_map, new_state)
                                        if ns >= 0:
                                            # Exit probability proportional to D1 rate
                                            Q[s, ns] += d1_rate_raw * (1.0 - total_routing / total_d1_rate) if total_d1_rate > 0 else 0

                        continue  # Skip the standard routing code for MAP distributions

                if rate <= 0:
                    continue

                # Calculate routing probabilities
                src_idx = ist * K + k
                total_routing = 0.0

                # Get node index for this station
                node_idx = int(station_to_node[ist]) if station_to_node is not None and ist < len(station_to_node) else ist

                # Check if this node has RROBIN routing for class k
                is_rrobin = (node_idx, k) in rrobin_info['outlinks']

                if is_rrobin:
                    # === State-dependent routing (RROBIN) ===
                    outlinks = rrobin_info['outlinks'][(node_idx, k)]
                    rr_var_idx = rr_var_map[(node_idx, k)]
                    current_rr_ptr = int(state[rr_var_idx])  # Index into outlinks array
                    dest_node = outlinks[current_rr_ptr]

                    # Advance round-robin pointer for the next job (wraps around)
                    next_rr_ptr = (current_rr_ptr + 1) % len(outlinks)

                    # Get destination station from destination node
                    if node_to_station is not None and dest_node < len(node_to_station):
                        dest_station = int(node_to_station[dest_node])
                    else:
                        dest_station = dest_node  # Fallback

                    # For RROBIN, routing is deterministic: probability 1.0 to current destination
                    # No class switching for RROBIN (r = k)
                    r = k
                    if dest_station >= 0 and dest_station < M:
                        # Get entry probabilities for destination
                        entry_probs = get_entry_probs(dest_station, r)
                        for entry_phase, entry_prob in enumerate(entry_probs):
                            if entry_prob <= 0:
                                continue
                            # Create new state with job movement and updated RR pointer
                            # Use phase-aware state modification
                            new_state = set_job_count(state, ist, k, -1)  # Departure from ist, class k
                            new_state = set_job_count(new_state, dest_station, r, +1, phase_idx=entry_phase)
                            new_state[rr_var_idx] = next_rr_ptr  # Advance RR pointer

                            if np.all(new_state[:state_dim] >= 0):
                                ns = _find_state_index_fast(state_map, new_state)
                                if ns >= 0:
                                    Q[s, ns] += rate * 1.0 * entry_prob
                                    total_routing += entry_prob
                                    # Track departure rate for class k from station ist
                                    depRates[s, ist, k] += rate * 1.0 * entry_prob
                    else:
                        # Destination is Sink (exit system) - for open networks
                        new_state = set_job_count(state, ist, k, -1)
                        new_state[rr_var_idx] = next_rr_ptr  # Still advance RR pointer

                        if np.all(new_state[:state_dim] >= 0):
                            ns = _find_state_index_fast(state_map, new_state)
                            if ns >= 0:
                                Q[s, ns] += rate * 1.0
                                total_routing = 1.0
                                # Track departure rate for class k from station ist
                                depRates[s, ist, k] += rate * 1.0
                else:
                    # === Standard probabilistic routing ===
                    # Find destination states based on routing
                    for jst in range(M):
                        if jst == source_station:
                            continue  # Can't route to source
                        for r in range(K):
                            # Routing probability from (ist, k) to (jst, r)
                            dst_idx = jst * K + r

                            if src_idx < P.shape[0] and dst_idx < P.shape[1]:
                                p = P[src_idx, dst_idx]
                            else:
                                p = 0

                            if p <= 0:
                                continue

                            total_routing += p

                            # Get entry probabilities for destination
                            entry_probs = get_entry_probs(jst, r)
                            for entry_phase, entry_prob in enumerate(entry_probs):
                                if entry_prob <= 0:
                                    continue
                                # Create base state: departure from ist, class k
                                base_state = set_job_count(state, ist, k, -1)

                                # Check if new state is valid
                                if np.any(base_state[:state_dim] < 0):
                                    continue

                                # For FCFS stations: handle buffer promotion after departure
                                if ist in fcfs_stations:
                                    promo_results = fcfs_promote_from_buffer_with_alpha(base_state, ist, sched, classprio)
                                    if promo_results:
                                        # Jobs waiting in buffer - create transitions for each promotion outcome
                                        for promo_state, promo_prob, _ in promo_results:
                                            new_state = set_job_count(promo_state.copy(), jst, r, +1, phase_idx=entry_phase)
                                            if np.any(new_state[:state_dim] < 0):
                                                continue
                                            ns = _find_state_index_fast(state_map, new_state)
                                            if ns >= 0:
                                                Q[s, ns] += rate * p * entry_prob * promo_prob
                                                depRates[s, ist, k] += rate * p * entry_prob * promo_prob
                                        continue  # Skip non-promotion path

                                # For SIRO stations: handle buffer promotion after departure
                                if ist in siro_stations:
                                    total_buf = sum(siro_get_buffer_count(base_state, ist, kk) for kk in range(K))
                                    if total_buf > 0:
                                        found_promo = False
                                        for buf_k in range(K):
                                            buf_count_k = siro_get_buffer_count(base_state, ist, buf_k)
                                            if buf_count_k > 0:
                                                # SIRO selects randomly from buffer
                                                select_prob = buf_count_k / total_buf
                                                promo_results = siro_promote_from_buffer_with_alpha(base_state, ist, buf_k)
                                                for promo_state, promo_prob, _ in promo_results:
                                                    new_state = set_job_count(promo_state.copy(), jst, r, +1, phase_idx=entry_phase)
                                                    if np.any(new_state[:state_dim] < 0):
                                                        continue
                                                    ns = _find_state_index_fast(state_map, new_state)
                                                    if ns >= 0:
                                                        Q[s, ns] += rate * p * entry_prob * promo_prob * select_prob
                                                        depRates[s, ist, k] += rate * p * entry_prob * promo_prob * select_prob
                                                        found_promo = True
                                        if found_promo:
                                            continue  # Skip non-promotion path

                                # No buffer jobs or not FCFS/SIRO - standard state modification
                                new_state = set_job_count(base_state.copy(), jst, r, +1, phase_idx=entry_phase)

                                # Find new state index using O(1) hash lookup
                                ns = _find_state_index_fast(state_map, new_state)
                                if ns >= 0:
                                    Q[s, ns] += rate * p * entry_prob
                                    # Track departure rate for class k from station ist
                                    depRates[s, ist, k] += rate * p * entry_prob

                # === Departures to sink (for open networks) ===
                # If routing doesn't sum to 1, remaining probability exits to sink
                if is_open and total_routing < 1.0:
                    exit_prob = 1.0 - total_routing
                    if exit_prob > 0:
                        # Create base state with job leaving the system
                        base_state = set_job_count(state, ist, k, -1)

                        if np.all(base_state[:state_dim] >= 0):
                            # For FCFS stations: handle buffer promotion after departure
                            if ist in fcfs_stations:
                                promo_results = fcfs_promote_from_buffer_with_alpha(base_state, ist, sched, classprio)
                                if promo_results:
                                    # Jobs waiting in buffer - create transitions for each promotion outcome
                                    for promo_state, promo_prob, _ in promo_results:
                                        if np.all(promo_state[:state_dim] >= 0):
                                            ns = _find_state_index_fast(state_map, promo_state)
                                            if ns >= 0:
                                                Q[s, ns] += rate * exit_prob * promo_prob
                                                depRates[s, ist, k] += rate * exit_prob * promo_prob
                                    continue  # Skip non-promotion path

                            # For SIRO stations: handle buffer promotion after departure
                            if ist in siro_stations:
                                total_buf = sum(siro_get_buffer_count(base_state, ist, kk) for kk in range(K))
                                if total_buf > 0:
                                    found_promo = False
                                    for buf_k in range(K):
                                        buf_count_k = siro_get_buffer_count(base_state, ist, buf_k)
                                        if buf_count_k > 0:
                                            select_prob = buf_count_k / total_buf
                                            promo_results = siro_promote_from_buffer_with_alpha(base_state, ist, buf_k)
                                            for promo_state, promo_prob, _ in promo_results:
                                                if np.all(promo_state[:state_dim] >= 0):
                                                    ns = _find_state_index_fast(state_map, promo_state)
                                                    if ns >= 0:
                                                        Q[s, ns] += rate * exit_prob * promo_prob * select_prob
                                                        depRates[s, ist, k] += rate * exit_prob * promo_prob * select_prob
                                                        found_promo = True
                                    if found_promo:
                                        continue  # Skip non-promotion path

                            # No buffer jobs or not FCFS/SIRO - standard exit
                            ns = _find_state_index_fast(state_map, base_state)
                            if ns >= 0:
                                Q[s, ns] += rate * exit_prob
                                # Track departure rate for class k from station ist
                                depRates[s, ist, k] += rate * exit_prob

    # === Phase-to-phase transitions for INF stations with phase-type distributions ===
    # These are internal transitions (D0 off-diagonal) that don't involve departures
    if use_phase_aug:
        for s, state in enumerate(state_space):
            for ist in range(M):
                # Only handle INF (infinite server) stations
                if hasattr(sn, 'sched') and sn.sched is not None:
                    sched = sn.sched.get(ist, SchedStrategy.FCFS)
                else:
                    continue

                if sched != SchedStrategy.INF:
                    continue

                for k in range(K):
                    n_phases_ik = phases[ist, k]
                    if n_phases_ik <= 1:
                        continue  # No phase transitions for single-phase distributions

                    # Get D0 matrix for phase transitions
                    D0, D1 = get_map_matrices(ist, k)
                    if D0 is None:
                        continue

                    # Get current phase counts
                    phase_counts = get_phase_counts(state, ist, k)

                    # For each source phase with jobs
                    for p_src in range(n_phases_ik):
                        n_src = int(phase_counts[p_src])
                        if n_src <= 0:
                            continue

                        # For each destination phase (D0 off-diagonal)
                        for p_dst in range(n_phases_ik):
                            if p_src == p_dst:
                                continue  # Skip diagonal (absorbed into overall departure rate)

                            # D0 off-diagonal: phase transition rate
                            phase_transition_rate = D0[p_src, p_dst]
                            if phase_transition_rate <= 0:
                                continue

                            # Total rate = n_src * phase_transition_rate
                            total_rate = n_src * phase_transition_rate

                            # Create new state: one job moves from p_src to p_dst
                            new_state = state.copy()
                            start_idx = phase_offset[ist, k]
                            new_state[start_idx + p_src] -= 1
                            new_state[start_idx + p_dst] += 1

                            # Add transition to Q
                            if np.all(new_state[:state_dim] >= 0):
                                ns = _find_state_index_fast(state_map, new_state)
                                if ns >= 0:
                                    Q[s, ns] += total_rate

    # Make valid generator (set diagonal)
    Q = ctmc_makeinfgen(Q)

    return Q, depRates


def _compute_metrics_from_distribution(
    sn: NetworkStruct,
    pi: np.ndarray,
    state_space: np.ndarray,
    rrobin_info: Optional[dict] = None,
    depRates: Optional[np.ndarray] = None
) -> Dict[str, np.ndarray]:
    """
    Compute performance metrics from steady-state distribution.

    Args:
        sn: Network structure
        pi: Steady-state probability distribution
        state_space: State space matrix (may include RR state variables at end)
        rrobin_info: Round-robin routing information
        depRates: Departure rates array from generator construction (shape: n_states, M, K)
                  If provided, used for accurate throughput computation (matching MATLAB approach)

    Returns:
        Dictionary with Q, U, R, T matrices
    """
    M = sn.nstations
    K = sn.nclasses

    # Check if phase augmentation is used
    use_phase_aug = rrobin_info.get('needs_phase_augmentation', False) if rrobin_info else False
    phases = rrobin_info.get('phases', np.ones((M, K), dtype=int)) if rrobin_info else np.ones((M, K), dtype=int)
    phase_offset = rrobin_info.get('phase_offset', None) if rrobin_info else None
    state_dim = rrobin_info.get('state_dim', M * K) if rrobin_info else M * K

    # Get MAP FCFS info for throughput computation
    map_fcfs = rrobin_info.get('map_fcfs', {}) if rrobin_info else {}
    map_var_offset = rrobin_info.get('map_var_offset', {}) if rrobin_info else {}

    # Get FCFS buffer info for correct queue length computation
    fcfs_stations = rrobin_info.get('fcfs_stations', set()) if rrobin_info else set()
    fcfs_max_buffer = rrobin_info.get('fcfs_max_buffer', {}) if rrobin_info else {}
    skip_stations = rrobin_info.get('skip_stations', set()) if rrobin_info else set()

    # Get SIRO stations for count-based buffer handling
    siro_stations = rrobin_info.get('siro_stations', set()) if rrobin_info else set()

    # Compute buffer starts for FCFS and SIRO stations
    # Skip Source/Sink stations as they don't contribute to state space
    fcfs_buffer_start_metrics = {}
    siro_buffer_start_metrics = {}  # Maps ist -> start index of buffer counts
    if use_phase_aug and (fcfs_stations or siro_stations):
        current_offset = 0
        for ist in range(M):
            # Skip Source/Sink stations - they don't appear in state vector
            if ist in skip_stations:
                fcfs_buffer_start_metrics[ist] = -1
                siro_buffer_start_metrics[ist] = -1
                continue
            if ist in fcfs_stations:
                max_buf = fcfs_max_buffer.get(ist, 0)
                fcfs_buffer_start_metrics[ist] = current_offset
                siro_buffer_start_metrics[ist] = -1
                current_offset += max_buf + sum(phases[ist, :])
            elif ist in siro_stations:
                # SIRO: buffer counts (K elements) + phase counts
                siro_buffer_start_metrics[ist] = current_offset
                fcfs_buffer_start_metrics[ist] = -1
                current_offset += K + sum(phases[ist, :])  # K buffer counts + phases
            else:
                fcfs_buffer_start_metrics[ist] = -1
                siro_buffer_start_metrics[ist] = -1
                current_offset += sum(phases[ist, :])

    def get_job_count(state: np.ndarray, ist: int, k: int) -> float:
        """Get total job count for (station, class) from state vector.

        For FCFS stations with phase-augmented state: count BOTH buffer entries
        AND in-service jobs (phase counts). Buffer stores waiting jobs, phases
        track in-service jobs.

        For SIRO stations: buffer_counts[k] + phase_counts (count-based buffer).

        For non-FCFS/non-SIRO stations (PS-like): count phase sums.
        Each phase count represents jobs in that phase, sum = total jobs.
        """
        count = 0.0
        if use_phase_aug and phase_offset is not None:
            if ist in fcfs_stations:
                # FCFS stations: count buffer entries (waiting) + phase counts (in-service)
                buffer_start = fcfs_buffer_start_metrics.get(ist, -1)
                max_buf = fcfs_max_buffer.get(ist, 0)
                if buffer_start >= 0 and max_buf > 0:
                    # Count buffer entries matching this class (1-based class IDs)
                    for buf_pos in range(max_buf):
                        buf_val = int(state[buffer_start + buf_pos])
                        if buf_val == k + 1:  # 1-based class ID
                            count += 1.0
                # Also count jobs in service (phase counts)
                start_idx = phase_offset[ist, k]
                end_idx = start_idx + phases[ist, k]
                count += float(sum(state[start_idx:end_idx]))
            elif ist in siro_stations:
                # SIRO stations: buffer_counts[k] (count-based) + phase counts (in-service)
                buffer_start = siro_buffer_start_metrics.get(ist, -1)
                if buffer_start >= 0:
                    # Buffer counts are first K elements at the station
                    count += float(state[buffer_start + k])  # Buffer count for class k
                    # Also count jobs in service (phase counts)
                    # SIRO state: [buf_0, buf_1, ..., buf_{K-1}, phase_counts...]
                    # Phase counts start at buffer_start + K
                    phase_start = buffer_start + K
                    n_phases_k = int(phases[ist, k])
                    phase_start_k = int(phase_start + int(np.sum(phases[ist, :k])))
                    count += float(np.sum(state[phase_start_k:phase_start_k + n_phases_k]))
            else:
                # Non-FCFS/non-SIRO stations (PS-like): count phase sums
                start_idx = phase_offset[ist, k]
                end_idx = start_idx + phases[ist, k]
                count = float(sum(state[start_idx:end_idx]))
            return count
        else:
            return float(state[ist * K + k])

    def get_state_matrix(state: np.ndarray) -> np.ndarray:
        """Get job counts as (M, K) matrix from state vector."""
        result = np.zeros((M, K))
        for ist in range(M):
            for k in range(K):
                result[ist, k] = get_job_count(state, ist, k)
        return result

    def get_phase_counts_metrics(state: np.ndarray, ist: int, k: int) -> np.ndarray:
        """Get phase counts for (station, class) from state vector."""
        if use_phase_aug and phase_offset is not None:
            start_idx = phase_offset[ist, k]
            end_idx = start_idx + phases[ist, k]
            return np.array([int(x) for x in state[start_idx:end_idx]])
        else:
            # Single phase
            return np.array([int(state[ist * K + k])])

    def get_d1_matrix(ist: int, k: int) -> Optional[np.ndarray]:
        """Get D1 matrix for (station, class)."""
        if not hasattr(sn, 'proc') or sn.proc is None:
            return None
        proc_is_list = isinstance(sn.proc, list)
        if proc_is_list:
            if ist >= len(sn.proc) or sn.proc[ist] is None:
                return None
            station_proc = sn.proc[ist]
        else:
            if ist not in sn.proc:
                return None
            station_proc = sn.proc[ist]

        proc_entry = None
        if isinstance(station_proc, (list, tuple)):
            if k < len(station_proc):
                proc_entry = station_proc[k]
        elif isinstance(station_proc, dict):
            proc_entry = station_proc.get(k)

        if proc_entry is None:
            return None

        # Handle PH/APH distributions stored as [alpha, T] or direct D0/D1 matrices
        if isinstance(proc_entry, (list, tuple)) and len(proc_entry) >= 2:
            first_elem = np.atleast_2d(np.array(proc_entry[0], dtype=float))
            second_elem = np.atleast_2d(np.array(proc_entry[1], dtype=float))

            # Check if this is [alpha, T] format (alpha is 1D/row vector, T is square matrix)
            if first_elem.shape[0] == 1 and second_elem.shape[0] == second_elem.shape[1]:
                # This is [alpha, T] format for PH/APH distributions
                alpha = first_elem.flatten()
                T = second_elem
                # Compute D1 from T: exit_rates = -row_sums(T), D1 = outer(exit_rates, alpha)
                exit_rates = -np.sum(T, axis=1)
                D1 = np.outer(exit_rates, alpha)
                return D1
            else:
                # This is [D0, D1] format
                return second_elem

        # Handle Erlang distribution stored as dict with 'k' and 'mu'
        if isinstance(proc_entry, dict):
            if 'k' in proc_entry and 'mu' in proc_entry:
                n_phases = int(proc_entry['k'])
                mu = float(proc_entry['mu'])  # per-phase rate
                if n_phases > 1:
                    # Construct Erlang D1 matrix: D1[k-1,0] = mu (completion from last phase)
                    D1 = np.zeros((n_phases, n_phases))
                    D1[n_phases - 1, 0] = mu
                    return D1
                else:
                    # Single phase: exponential
                    return np.array([[mu]])
            elif 'probs' in proc_entry and 'rates' in proc_entry:
                # HyperExp distribution
                probs = np.array(proc_entry['probs'])
                rates = np.array(proc_entry['rates'])
                # D1: completion from phase i, restart in phase j with prob_j
                D1 = np.outer(rates, probs)
                return D1
            elif 'rate' in proc_entry:
                # Exponential distribution
                mu = float(proc_entry['rate'])
                return np.array([[mu]])

        return None

    def get_map_phase(state: np.ndarray, ist: int, k: int) -> int:
        """Get current MAP phase for (station, class) from state vector."""
        if (ist, k) not in map_var_offset:
            return 0
        idx = map_var_offset[(ist, k)]
        return int(state[idx])

    def get_map_d1_rate(ist: int, k: int, map_phase: int) -> float:
        """Get MAP D1 service completion rate from current phase."""
        if not hasattr(sn, 'proc') or sn.proc is None:
            return 1.0
        proc_is_list = isinstance(sn.proc, list)
        if proc_is_list:
            if ist >= len(sn.proc) or sn.proc[ist] is None:
                return 1.0
            station_proc = sn.proc[ist]
        else:
            if ist not in sn.proc:
                return 1.0
            station_proc = sn.proc[ist]

        proc_entry = None
        if isinstance(station_proc, (list, tuple)):
            if k < len(station_proc):
                proc_entry = station_proc[k]
        elif isinstance(station_proc, dict):
            proc_entry = station_proc.get(k)

        if proc_entry is None:
            return 1.0

        # Handle direct D0/D1 matrices
        if isinstance(proc_entry, (list, tuple)) and len(proc_entry) >= 2:
            D1 = np.atleast_2d(np.array(proc_entry[1], dtype=float))
            # Total completion rate from this phase = row sum of D1
            return np.sum(D1[map_phase, :])

        # Handle Erlang distribution stored as dict with 'k' and 'mu'
        if isinstance(proc_entry, dict):
            if 'k' in proc_entry and 'mu' in proc_entry:
                n_phases = int(proc_entry['k'])
                mu = float(proc_entry['mu'])  # per-phase rate
                # For Erlang, only last phase completes
                if map_phase == n_phases - 1:
                    return mu
                else:
                    return 0.0
            elif 'probs' in proc_entry and 'rates' in proc_entry:
                # HyperExp distribution: completion rate from phase = rate for that phase
                rates = np.array(proc_entry['rates'])
                if map_phase < len(rates):
                    return rates[map_phase]
                return 0.0
            elif 'rate' in proc_entry:
                # Exponential distribution
                return float(proc_entry['rate'])

        return 1.0

    # Initialize metrics
    QN = np.zeros((M, K))
    UN = np.zeros((M, K))
    RN = np.zeros((M, K))
    TN = np.zeros((M, K))

    # Get service rates
    if hasattr(sn, 'rates') and sn.rates is not None:
        rates = np.asarray(sn.rates)
    else:
        rates = np.ones((M, K))

    # Get number of servers
    if hasattr(sn, 'nservers') and sn.nservers is not None:
        nservers = np.asarray(sn.nservers).flatten()
    else:
        nservers = np.ones(M)

    # Get load-dependent scaling
    lldscaling = None
    if hasattr(sn, 'lldscaling') and sn.lldscaling is not None:
        lldscaling = np.asarray(sn.lldscaling)

    # Track which stations are infinite servers
    inf_server_stations = set()
    if hasattr(sn, 'sched') and sn.sched is not None:
        for ist, sched_val in sn.sched.items():
            if _sched_is(sched_val, 'INF'):
                inf_server_stations.add(ist)

    def get_load_scaling(ist: int, total_jobs: int) -> float:
        """Get service rate scaling factor for station ist with total_jobs present."""
        if total_jobs <= 0:
            return 0.0  # No jobs, no service
        # For infinite servers, each job gets its own server
        if ist in inf_server_stations:
            return float(total_jobs)
        if lldscaling is not None and ist < lldscaling.shape[0]:
            idx = total_jobs - 1
            if lldscaling.ndim > 1 and idx < lldscaling.shape[1]:
                return lldscaling[ist, idx]
            elif lldscaling.ndim > 1:
                return lldscaling[ist, -1]
        c = nservers[ist] if ist < len(nservers) else 1
        return min(total_jobs, c)

    def get_max_scaling(ist: int) -> float:
        """Get maximum scaling factor for station (for utilization normalization)."""
        if lldscaling is not None and ist < lldscaling.shape[0]:
            if lldscaling.ndim > 1:
                return np.max(lldscaling[ist, :])
            return lldscaling[ist]
        c = nservers[ist] if ist < len(nservers) else 1
        return c

    # Compute expected queue lengths E[n_ik]
    for s, state in enumerate(state_space):
        state_matrix = get_state_matrix(state)
        for ist in range(M):
            for k in range(K):
                QN[ist, k] += pi[s] * state_matrix[ist, k]

    # Compute throughputs from departure rates tracked during generator construction
    # This matches MATLAB's approach: TN[ist,k] = sum(pi * depRates[:, ist, k])
    # depRates tracks all service completion transitions from each state
    if depRates is not None:
        for ist in range(M):
            for k in range(K):
                # TN[ist, k] = sum(pi[s] * depRates[s, ist, k]) for all states s
                TN[ist, k] = np.sum(pi * depRates[:, ist, k])
    else:
        # Fallback: compute throughput from formula (legacy behavior)
        for s, state in enumerate(state_space):
            state_matrix = get_state_matrix(state)
            for ist in range(M):
                total_at_station = np.sum(state_matrix[ist, :])
                if total_at_station <= 0:
                    continue

                scaling = get_load_scaling(ist, int(total_at_station))

                if hasattr(sn, 'sched') and sn.sched is not None:
                    sched = sn.sched.get(ist, SchedStrategy.FCFS)
                else:
                    sched = SchedStrategy.FCFS

                for k in range(K):
                    n_k = state_matrix[ist, k]
                    if n_k <= 0:
                        continue

                    mu = rates[ist, k] if ist < rates.shape[0] and k < rates.shape[1] else 1.0

                    if _sched_is(sched, 'INF'):
                        # Infinite server: rate = n * mu
                        TN[ist, k] += pi[s] * n_k * mu
                    else:
                        # PS, FCFS, etc.: share of capacity proportional to number of jobs
                        TN[ist, k] += pi[s] * scaling * mu * (n_k / total_at_station)

    # Compute expected capacity (E[scaling]) at each station
    # E[scaling] = sum over states of pi(s) * lldscaling(station, n)
    expected_scaling = np.zeros(M)
    for s, state in enumerate(state_space):
        state_matrix = get_state_matrix(state)
        for ist in range(M):
            total_at_station = np.sum(state_matrix[ist, :])
            scaling = get_load_scaling(ist, int(total_at_station))
            expected_scaling[ist] += pi[s] * scaling
    # Ensure no division by zero
    expected_scaling = np.maximum(expected_scaling, 1e-10)

    # Compute utilizations using MATLAB's formulas
    # For INF servers: UN = QN
    # For LLD PS/DPS/etc: UN = E[n_k / n_total] (expected fraction of jobs that are class k)
    for ist in range(M):
        if hasattr(sn, 'sched') and sn.sched is not None:
            sched = sn.sched.get(ist, SchedStrategy.FCFS)
        else:
            sched = SchedStrategy.FCFS

        if _sched_is(sched, 'INF'):
            # For infinite servers, utilization = queue length
            for k in range(K):
                UN[ist, k] = QN[ist, k]
        elif _sched_is(sched, 'PS', 'DPS', 'GPS'):
            # For PS/DPS/GPS: UN = E[n_k / n_total]
            # This is already computed below via state iteration
            pass
        elif _sched_is(sched, 'PSPRIO', 'GPSPRIO'):
            # For priority variants: UN = T / (c * mu) like FCFS
            c = nservers[ist] if ist < len(nservers) else 1
            for k in range(K):
                mu = rates[ist, k] if ist < rates.shape[0] and k < rates.shape[1] else 1.0
                if mu > 0 and c > 0:
                    UN[ist, k] = TN[ist, k] / (c * mu)
        else:
            # For FCFS and others: UN = T / (c * mu) where c is number of servers
            # For MAP distributions, use expected D1 rate instead of mu
            c = nservers[ist] if ist < len(nservers) else 1
            for k in range(K):
                if (ist, k) in map_fcfs:
                    # For MAP: compute expected D1 rate across states
                    expected_d1 = 0.0
                    total_weight = 0.0
                    for s, state in enumerate(state_space):
                        state_matrix = get_state_matrix(state)
                        n_k = state_matrix[ist, k]
                        if n_k > 0:
                            map_phase = get_map_phase(state, ist, k)
                            d1_rate = get_map_d1_rate(ist, k, map_phase)
                            expected_d1 += pi[s] * d1_rate
                            total_weight += pi[s]
                    if total_weight > 0:
                        expected_d1 = expected_d1 / total_weight
                    if expected_d1 > 0 and c > 0:
                        UN[ist, k] = TN[ist, k] / (c * expected_d1)
                else:
                    mu = rates[ist, k] if ist < rates.shape[0] and k < rates.shape[1] else 1.0
                    if mu > 0 and c > 0:
                        UN[ist, k] = TN[ist, k] / (c * mu)

    # For PS/DPS with LLD, compute UN = E[n_k / n_total]
    for s, state in enumerate(state_space):
        state_matrix = get_state_matrix(state)
        for ist in range(M):
            if hasattr(sn, 'sched') and sn.sched is not None:
                sched = sn.sched.get(ist, SchedStrategy.FCFS)
            else:
                sched = SchedStrategy.FCFS

            if _sched_is(sched, 'PS', 'DPS', 'GPS'):
                n_total = np.sum(state_matrix[ist, :])
                if n_total > 0:
                    for k in range(K):
                        n_k = state_matrix[ist, k]
                        # With equal schedparam weights: n_k / n_total
                        UN[ist, k] += pi[s] * n_k / n_total

    # Compute response times: R = Q / T (Little's law)
    for ist in range(M):
        for k in range(K):
            if TN[ist, k] > 0:
                RN[ist, k] = QN[ist, k] / TN[ist, k]
            else:
                RN[ist, k] = 0

    # Handle Source station metrics for open networks
    # Source doesn't hold jobs - QLen, Util, RespT should be 0 for reporting
    # Throughput is computed from depRates (departure rates from Source) which accounts
    # for state-space truncation (blocked arrivals when downstream stations are full)
    if hasattr(sn, 'sched') and sn.sched is not None:
        for ist, sched_val in sn.sched.items():
            # Check for EXT scheduling (Source station)
            is_source = (_sched_is(sched_val, 'EXT') or
                        (isinstance(sched_val, int) and sched_val == SchedStrategy.EXT.value))
            if is_source and ist < M:
                for k in range(K):
                    # Source doesn't hold jobs in the traditional sense
                    QN[ist, k] = 0.0
                    UN[ist, k] = 0.0
                    RN[ist, k] = 0.0
                    # Note: TN[ist, k] for Source is computed from depRates above
                    # which correctly captures the effective arrival rate accounting
                    # for state-space truncation (blocked arrivals). Do NOT overwrite
                    # with raw arrival rate from sn.rates.

    return {
        'Q': QN,
        'U': UN,
        'R': RN,
        'T': TN
    }


def _is_lcfs_lcfspr_network(sn: NetworkStruct) -> Tuple[bool, int, int]:
    """
    Check if network is a 2-station LCFS+LCFSPR closed network.

    Returns:
        Tuple of (is_lcfs_lcfspr, lcfs_station, lcfspr_station)
    """
    if sn.sched is None:
        return False, -1, -1

    # Check for closed network
    njobs = sn.njobs if sn.njobs is not None else np.zeros(sn.nclasses)
    if np.any(np.isinf(njobs)):
        return False, -1, -1

    # Find LCFS and LCFSPR stations
    lcfs_stats = []
    lcfspr_stats = []
    for ist, sched in sn.sched.items():
        if _sched_is(sched, 'LCFS'):
            lcfs_stats.append(ist)
        elif _sched_is(sched, 'LCFSPR'):
            lcfspr_stats.append(ist)

    # Must have exactly one of each
    if len(lcfs_stats) == 1 and len(lcfspr_stats) == 1:
        return True, lcfs_stats[0], lcfspr_stats[0]

    return False, -1, -1


def _solver_ctmc_lcfsqn(
    sn: NetworkStruct,
    options: SolverCTMCOptions,
    lcfs_stat: int,
    lcfspr_stat: int
) -> SolverCTMCReturn:
    """
    Specialized CTMC solver for LCFS+LCFSPR 2-station networks.

    Uses the product-form property: for LCFS+LCFSPR networks, the steady-state
    distribution is insensitive to buffer ordering, so we can use a simplified
    state representation and PS-like generator construction.

    Args:
        sn: Network structure
        options: Solver options
        lcfs_stat: Index of LCFS station
        lcfspr_stat: Index of LCFSPR station

    Returns:
        SolverCTMCReturn with performance metrics
    """
    start_time = time.time()

    M = sn.nstations
    K = sn.nclasses
    rates = sn.rates
    njobs = sn.njobs if sn.njobs is not None else np.zeros(K)
    N = njobs.astype(int)

    # For LCFS+LCFSPR product-form networks, enumerate states without buffer ordering
    # State format: [n_11, n_12, ..., n_1K, n_21, ..., n_MK] where n_ik = jobs of class k at station i
    # Only include the two LCFS/LCFSPR stations in state enumeration

    # Generate all valid population distributions across the two stations
    from itertools import product as cart_product

    total_jobs = int(np.sum(N))
    states = []

    # For each class, distribute jobs between the two stations
    class_distributions = []
    for k in range(K):
        n_k = int(N[k])
        # All ways to distribute n_k jobs of class k between station 0 and station 1
        class_distributions.append([(i, n_k - i) for i in range(n_k + 1)])

    # Cartesian product of all class distributions
    for dist in cart_product(*class_distributions):
        # dist is a tuple of (n_k_at_lcfs, n_k_at_lcfspr) for each class k
        state = np.zeros(2 * K)
        for k, (n_lcfs, n_lcfspr) in enumerate(dist):
            state[k] = n_lcfs          # Jobs at LCFS station
            state[K + k] = n_lcfspr    # Jobs at LCFSPR station
        states.append(state)

    state_space = np.array(states)
    n_states = len(state_space)

    # Build generator matrix using PS-like rates (product-form insensitivity)
    Q = np.zeros((n_states, n_states))
    depRates = np.zeros((n_states, 2, K))  # Only 2 stations

    # Map (lcfs_stat, lcfspr_stat) to (0, 1) for state indexing
    stat_map = {lcfs_stat: 0, lcfspr_stat: 1}

    # Get routing matrix
    P = sn.rt if sn.rt is not None else np.zeros((M * K, M * K))

    state_map = {}
    for i, s in enumerate(state_space):
        state_map[tuple(s)] = i

    for s_idx, state in enumerate(state_space):
        # Service completions at each station
        for local_ist, ist in enumerate([lcfs_stat, lcfspr_stat]):
            total_at_station = np.sum(state[local_ist * K:(local_ist + 1) * K])
            if total_at_station <= 0:
                continue

            for k in range(K):
                n_ik = state[local_ist * K + k]
                if n_ik <= 0:
                    continue

                mu = rates[ist, k] if ist < rates.shape[0] and k < rates.shape[1] else 1.0
                if mu <= 0:
                    continue

                # For product-form LCFS+LCFSPR: use PS-like service rate
                # Rate = mu * (n_ik / total_at_station) for single server
                # This is the key insight: product-form means insensitivity
                rate = mu * (n_ik / total_at_station)

                # Route to destination (for closed network, routes between the two stations)
                src_idx = ist * K + k
                for local_jst, jst in enumerate([lcfs_stat, lcfspr_stat]):
                    for r in range(K):
                        dst_idx = jst * K + r
                        if src_idx < P.shape[0] and dst_idx < P.shape[1]:
                            p = P[src_idx, dst_idx]
                        else:
                            p = 0

                        if p <= 0:
                            continue

                        # Create new state
                        new_state = state.copy()
                        new_state[local_ist * K + k] -= 1  # Departure
                        new_state[local_jst * K + r] += 1  # Arrival

                        if np.all(new_state >= 0):
                            ns_key = tuple(new_state)
                            if ns_key in state_map:
                                ns_idx = state_map[ns_key]
                                Q[s_idx, ns_idx] += rate * p
                                depRates[s_idx, local_ist, k] += rate * p

    # Set diagonal elements
    for s in range(n_states):
        Q[s, s] = -np.sum(Q[s, :])

    # Solve for stationary distribution
    pi = ctmc_solve(Q)

    # Compute metrics
    QN = np.zeros((M, K))
    UN = np.zeros((M, K))
    TN = np.zeros((M, K))
    RN = np.zeros((M, K))

    # Map local station indices back to original indices
    local_to_orig = {0: lcfs_stat, 1: lcfspr_stat}

    for s_idx, state in enumerate(state_space):
        for local_ist in range(2):
            ist = local_to_orig[local_ist]
            for k in range(K):
                QN[ist, k] += pi[s_idx] * state[local_ist * K + k]

    # Throughput from departure rates
    for local_ist in range(2):
        ist = local_to_orig[local_ist]
        for k in range(K):
            TN[ist, k] = np.sum(pi * depRates[:, local_ist, k])

    # Utilization: UN = TN / mu for single server
    for local_ist in range(2):
        ist = local_to_orig[local_ist]
        for k in range(K):
            mu = rates[ist, k] if ist < rates.shape[0] and k < rates.shape[1] else 1.0
            if mu > 0:
                UN[ist, k] = TN[ist, k] / mu

    # Response time: RN = QN / TN (Little's Law)
    for ist in [lcfs_stat, lcfspr_stat]:
        for k in range(K):
            if TN[ist, k] > 0:
                RN[ist, k] = QN[ist, k] / TN[ist, k]

    # System throughput
    XN = np.zeros((1, K))
    for k in range(K):
        XN[0, k] = TN[lcfs_stat, k]  # Same at both stations for closed network

    # Cycle time
    CN = np.zeros((1, K))
    for k in range(K):
        if XN[0, k] > 0:
            CN[0, k] = N[k] / XN[0, k]

    result = SolverCTMCReturn(
        Q=QN,
        U=UN,
        R=RN,
        T=TN,
        C=CN,
        X=XN,
        infgen=Q,
        space=state_space,
        runtime=time.time() - start_time,
        method="lcfsqn"
    )

    return result


def solver_ctmc_basic(
    sn: NetworkStruct,
    options: Optional[SolverCTMCOptions] = None
) -> SolverCTMCReturn:
    """
    Basic CTMC solver using state-space enumeration.

    Enumerates all valid states, builds the infinitesimal generator,
    and solves for steady-state distribution.

    Args:
        sn: Network structure
        options: Solver options

    Returns:
        SolverCTMCReturn with performance metrics
    """
    start_time = time.time()

    if options is None:
        options = SolverCTMCOptions()

    M = sn.nstations
    K = sn.nclasses

    # LCFS+LCFSPR networks should be handled by the standard solver
    # The standard state-space enumeration and generator construction
    # correctly handles LCFS scheduling when buffer ordering is enabled

    # Enumerate state space
    state_space, state_space_aggr, rrobin_info = _enumerate_state_space(sn, options.cutoff)

    # Mandatory truncation warning for open/mixed models
    if sn_has_open_classes(sn):
        print(f"CTMC solver using state space cutoff = {options.cutoff} for open/mixed model.")
        warnings.warn(
            "State space truncation may cause inaccurate results. "
            "Consider varying cutoff to assess sensitivity.",
            UserWarning
        )

    if options.verbose:
        print(f"CTMC state space size: {len(state_space)}")
        if rrobin_info['total_vars'] > 0:
            print(f"  Including {rrobin_info['total_vars']} round-robin state variables")

    # Build generator matrix and departure rates
    Q, depRates = _build_generator(sn, state_space, options, rrobin_info)

    # NOTE: Stochastic complementation for Router immediate transitions is not yet implemented
    # in Python native CTMC. This can cause numerical issues for Cache+Router networks.
    # For accurate results on such networks, use SSA, MVA, or NC solvers instead.
    # See MATLAB's solver_ctmc.m for reference implementation of hide_immediate.

    # Solve for steady-state distribution
    pi = ctmc_solve(Q)

    # Compute performance metrics using departure rates from generator construction
    metrics = _compute_metrics_from_distribution(sn, pi, state_space, rrobin_info, depRates)

    QN = metrics['Q']
    UN = metrics['U']
    RN = metrics['R']
    TN = metrics['T']

    # Compute cycle times and system throughput
    CN = np.sum(RN, axis=0).reshape(1, -1)
    XN = np.zeros((1, K))
    for k in range(K):
        ref_stat = int(sn.refstat[k]) if hasattr(sn, 'refstat') and k < len(sn.refstat) else 0
        if ref_stat < M:
            XN[0, k] = TN[ref_stat, k]

    # Clean up NaN values
    QN = np.nan_to_num(QN, nan=0.0)
    UN = np.nan_to_num(UN, nan=0.0)
    RN = np.nan_to_num(RN, nan=0.0)
    TN = np.nan_to_num(TN, nan=0.0)
    CN = np.nan_to_num(CN, nan=0.0)
    XN = np.nan_to_num(XN, nan=0.0)

    # Compute station column ranges for nodeStateSpace extraction
    # Each station has a range [start, end) of columns in the state space
    station_col_ranges = []
    phases = rrobin_info.get('phases', np.ones((M, K), dtype=int))
    fcfs_stations = rrobin_info.get('fcfs_stations', set())
    fcfs_max_buffer = rrobin_info.get('fcfs_max_buffer', {})
    skip_stations = rrobin_info.get('skip_stations', set())

    col_idx = 0
    for ist in range(M):
        if ist in skip_stations:
            # Source/Sink stations have no columns in state space
            station_col_ranges.append((col_idx, col_idx))
            continue

        start_col = col_idx
        if ist in fcfs_stations:
            # FCFS station: buffer columns + phase columns
            buffer_size = fcfs_max_buffer.get(ist, 0)
            col_idx += buffer_size
        # Add phase columns for all classes at this station
        for k in range(K):
            col_idx += int(phases[ist, k])
        station_col_ranges.append((start_col, col_idx))

    result = SolverCTMCReturn()
    result.Q = QN
    result.U = UN
    result.R = RN
    result.T = TN
    result.C = CN
    result.X = XN
    result.pi = pi
    result.infgen = Q
    result.space = state_space
    result.station_col_ranges = station_col_ranges
    result.depRates = depRates  # Include departure rates for debugging
    result.runtime = time.time() - start_time
    result.method = "basic"

    return result


def solver_ctmc(
    sn: NetworkStruct,
    options: Optional[SolverCTMCOptions] = None
) -> SolverCTMCReturn:
    """
    Main CTMC solver handler.

    Routes to appropriate method based on options and network characteristics.

    Args:
        sn: Network structure
        options: Solver options

    Returns:
        SolverCTMCReturn with performance metrics
    """
    if options is None:
        options = SolverCTMCOptions()

    method = options.method.lower()

    if method in ['default', 'basic']:
        return solver_ctmc_basic(sn, options)
    else:
        # Unknown method - use basic
        if options.verbose:
            print(f"Warning: Unknown CTMC method '{method}'. Using basic.")
        return solver_ctmc_basic(sn, options)


__all__ = [
    'solver_ctmc',
    'solver_ctmc_basic',
    'SolverCTMCReturn',
    'SolverCTMCOptions',
]
