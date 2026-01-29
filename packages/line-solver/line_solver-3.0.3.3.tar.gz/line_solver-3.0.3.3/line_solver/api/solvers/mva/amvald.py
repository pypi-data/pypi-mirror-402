"""
Approximate MVA for Load-Dependent (AMVA-LD) networks.

This module implements the approximate MVA solver for load-dependent
queueing networks using QD-AMVA style corrections with under-relaxation.

References:
    Original MATLAB: matlab/src/solvers/MVA/solver_amvald.m
    Original MATLAB: matlab/src/solvers/MVA/solver_amvald_forward.m
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, Dict
from enum import IntEnum

# Import the proper pfqn_lldfun and pfqn_cdfun from utils
from ...pfqn.utils import pfqn_lldfun, pfqn_cdfun
# Import SchedStrategy from the canonical source
from ....lang.base import SchedStrategy

# Try to import JIT-compiled kernels
try:
    from .amvald_jit import (
        HAS_NUMBA as AMVALD_HAS_NUMBA,
        compute_arrival_queue_lengths_jit,
        update_metrics_jit,
        cap_utilizations_jit,
        SCHED_INF, SCHED_FCFS, SCHED_SIRO, SCHED_PS, SCHED_HOL, SCHED_LCFSPR, SCHED_EXT,
    )
except ImportError:
    AMVALD_HAS_NUMBA = False
    compute_arrival_queue_lengths_jit = None
    update_metrics_jit = None
    cap_utilizations_jit = None
    SCHED_INF, SCHED_FCFS, SCHED_SIRO, SCHED_PS, SCHED_HOL, SCHED_LCFSPR, SCHED_EXT = 0, 1, 2, 3, 4, 5, 6

# Threshold for using JIT (M * K iterations)
AMVALD_JIT_THRESHOLD = 50


def _sched_to_int(sched_strategy) -> int:
    """Convert SchedStrategy to integer for JIT functions."""
    if sched_strategy == SchedStrategy.INF:
        return SCHED_INF
    elif sched_strategy == SchedStrategy.FCFS:
        return SCHED_FCFS
    elif sched_strategy == SchedStrategy.SIRO:
        return SCHED_SIRO
    elif sched_strategy == SchedStrategy.PS:
        return SCHED_PS
    elif sched_strategy == SchedStrategy.HOL:
        return SCHED_HOL
    elif sched_strategy == SchedStrategy.LCFSPR:
        return SCHED_LCFSPR
    elif sched_strategy == SchedStrategy.EXT:
        return SCHED_EXT
    else:
        return SCHED_FCFS  # Default


def _build_sched_array(sched: Dict[int, int], M: int) -> np.ndarray:
    """Convert sched dict to numpy array for JIT functions."""
    sched_arr = np.zeros(M, dtype=np.int64)
    for k in range(M):
        sched_k = sched.get(k, SchedStrategy.FCFS)
        sched_arr[k] = _sched_to_int(sched_k)
    return sched_arr


@dataclass
class AmvaldOptions:
    """Options for AMVA-LD solver."""
    method: str = 'default'
    iter_tol: float = 1e-4  # Convergence tolerance (matches MATLAB default)
    iter_max: int = 1000
    tol: float = 1e-4  # Tolerance for all other uses (matches MATLAB default)
    verbose: bool = False

    @dataclass
    class Config:
        multiserver: str = 'default'
        np_priority: str = 'default'
        highvar: str = 'default'

    config: Config = None

    def __post_init__(self):
        if self.config is None:
            self.config = AmvaldOptions.Config()


@dataclass
class AmvaldResult:
    """Result from AMVA-LD solver."""
    Q: np.ndarray      # Queue lengths (M x K)
    U: np.ndarray      # Utilization (M x K)
    R: np.ndarray      # Response times (M x K)
    T: np.ndarray      # Throughputs (M x K)
    C: np.ndarray      # Cycle times (1 x K)
    X: np.ndarray      # System throughputs (1 x K)
    lG: float          # Log normalizing constant
    totiter: int       # Total iterations




def solver_amvald_forward(
    M: int, K: int,
    nservers: np.ndarray,
    lldscaling: Optional[np.ndarray],
    cdscaling: Optional[list],
    sched: Dict[int, int],
    classprio: Optional[np.ndarray],
    gamma: np.ndarray,
    tau: np.ndarray,
    Qchain_in: np.ndarray,
    Xchain_in: np.ndarray,
    Uchain_in: np.ndarray,
    STchain_in: np.ndarray,
    Vchain_in: np.ndarray,
    Nchain_in: np.ndarray,
    options: AmvaldOptions
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Forward step of AMVA-LD: compute waiting times from current estimates.

    Args:
        M: Number of stations
        K: Number of chains
        nservers: Number of servers at each station (M,)
        lldscaling: Load-dependent scaling matrix (M x Nmax)
        cdscaling: Class-dependent scaling functions (list of callables per station)
        sched: Scheduling strategy for each station
        classprio: Class priorities (K,) - lower value = higher priority
        gamma: Correction factors
        tau: Throughput differences
        Qchain_in: Current queue length estimates (M x K)
        Xchain_in: Current throughput estimates (K,)
        Uchain_in: Current utilization estimates (M x K)
        STchain_in: Service times (M x K)
        Vchain_in: Visit ratios (M x K)
        Nchain_in: Population per chain (K,)
        options: Solver options

    Returns:
        Wchain: Waiting times (M x K)
        STeff: Effective service times (M x K)
    """
    # Initialize gamma if empty
    if gamma.size == 0:
        gamma = np.zeros((M, K))

    Nt = np.sum(Nchain_in[np.isfinite(Nchain_in)])
    if np.all(np.isinf(Nchain_in)):
        delta = 1.0
    else:
        delta = (Nt - 1) / Nt if Nt > 0 else 0.0

    deltaclass = (Nchain_in - 1) / Nchain_in
    deltaclass[np.isinf(Nchain_in)] = 1.0
    deltaclass[Nchain_in == 0] = 0.0

    # Find class types
    ocl = np.where(np.isinf(Nchain_in))[0]  # open classes
    ccl = np.where(np.isfinite(Nchain_in) & (Nchain_in > 0))[0]  # closed classes
    nnzclasses = np.where(Nchain_in > 0)[0]  # non-zero classes

    # Build priority groupings (lower value = higher priority)
    # nnzclasses_hprio[r]: classes with strictly higher priority than r
    # nnzclasses_ehprio[r]: classes with equal or higher priority than r
    nnzclasses_hprio = {}
    nnzclasses_ehprio = {}
    if classprio is not None and len(classprio) == K:
        classprio = np.asarray(classprio).flatten()
        for r in nnzclasses:
            prio_r = classprio[r]
            nnzclasses_hprio[r] = [c for c in nnzclasses if classprio[c] < prio_r]
            nnzclasses_ehprio[r] = [c for c in nnzclasses if classprio[c] <= prio_r]
    else:
        # No priorities: all classes have same priority
        for r in nnzclasses:
            nnzclasses_hprio[r] = []
            nnzclasses_ehprio[r] = list(nnzclasses)

    # Compute arrival queue lengths
    interpTotArvlQlen = np.zeros(M)
    selfArvlQlenSeenByClosed = np.zeros((M, K))
    totArvlQlenSeenByClosed = np.zeros((M, K))
    stationaryQlen = np.zeros((M, K))
    # HOL-specific: queue length seen considering priority
    totArvlQlenSeenByOpen_HOL = np.zeros((K, M))  # (r, k) order for open classes
    totArvlQlenSeenByClosed_HOL = np.zeros((M, K))

    for k in range(M):
        interpTotArvlQlen[k] = delta * np.sum(Qchain_in[k, nnzclasses])
        sched_k = sched.get(k, SchedStrategy.FCFS)

        for r in nnzclasses:
            selfArvlQlenSeenByClosed[k, r] = deltaclass[r] * Qchain_in[k, r]
            totArvlQlenSeenByClosed[k, r] = (deltaclass[r] * Qchain_in[k, r] +
                                              np.sum(Qchain_in[k, nnzclasses]) - Qchain_in[k, r])
            stationaryQlen[k, r] = Qchain_in[k, r]

            # HOL-specific arrival queue lengths (only jobs with equal or higher priority)
            if sched_k == SchedStrategy.HOL:
                ehprio = nnzclasses_ehprio.get(r, list(nnzclasses))
                ehprio_without_r = [c for c in ehprio if c != r]
                # For open classes
                totArvlQlenSeenByOpen_HOL[r, k] = np.sum(Qchain_in[k, ehprio])
                # For closed classes: delta_r * Q[k,r] + sum(Q[k, ehprio - {r}])
                totArvlQlenSeenByClosed_HOL[k, r] = (deltaclass[r] * Qchain_in[k, r] +
                                                     np.sum(Qchain_in[k, ehprio_without_r]))

    # Initialize lldscaling if empty
    if lldscaling is None or lldscaling.size == 0:
        lldscaling = np.ones((M, max(1, int(np.ceil(Nt)))))

    # Compute LLD term (using proper cubic interpolation like MATLAB)
    lldterm = pfqn_lldfun(1 + interpTotArvlQlen, lldscaling)

    # Compute multi-server term with gamma correction for 'default' multiserver config
    # For PS stations (not FCFS-type), MATLAB uses different formulas based on method:
    # - 'lin'/'qdlin': g = sum over r in ccl of: ((Nt-1)/Nt) * Nchain(r) * gamma(ccl,:,r)
    #   then msterm = pfqn_lldfun(1 + interpTotArvlQlen + mean(g, axis=0), [], nservers)
    # - otherwise: g = sum over r in ccl of: (Nt-1)*gamma(r,:)
    #   then msterm = pfqn_lldfun(1 + interpTotArvlQlen + mean(g), [], nservers)
    # For FCFS-type stations, use Seidmann: msterm = 1/nservers
    if len(ccl) > 0 and gamma.size > 0 and Nt > 0:
        method = options.method if hasattr(options, 'method') else 'default'
        if method in ('lin', 'qdlin') and gamma.ndim == 3:
            # 3D gamma: gamma[s, k, r] - class-based corrections
            # g = sum over r in ccl of: ((Nt-1)/Nt) * Nchain(r) * gamma(ccl, :, r)
            # gamma[ccl, :, r] has shape (len(ccl), M) for each r
            g = np.zeros((len(ccl), M))
            for r in ccl:
                g = g + ((Nt - 1) / Nt) * Nchain_in[r] * gamma[ccl, :, r]
            # mean(g, axis=0) takes mean along classes (axis 0), giving (M,)
            g_mean = np.mean(g, axis=0)
            msterm = pfqn_lldfun(1 + interpTotArvlQlen + g_mean, None, nservers)
        else:
            # 2D gamma: gamma[r, k] - total corrections
            # g = sum over r in ccl of: (Nt-1)*gamma(r,:)
            g = np.zeros(M)
            for r in ccl:
                g = g + (Nt - 1) * gamma[r, :]
            # mean(g) takes mean of all elements, giving scalar
            g_mean = np.mean(g)
            msterm = pfqn_lldfun(1 + interpTotArvlQlen + g_mean, None, nservers)
    else:
        msterm = pfqn_lldfun(1 + interpTotArvlQlen, None, nservers)

    # For FCFS-type stations, use Seidmann approximation (override softmin)
    for k in range(M):
        sched_k = sched.get(k, SchedStrategy.FCFS)
        if sched_k in [SchedStrategy.FCFS, SchedStrategy.SIRO, SchedStrategy.LCFSPR]:
            if nservers[k] > 0 and not np.isinf(nservers[k]):
                msterm[k] = 1.0 / nservers[k]

    # Compute class-dependent scaling term (cdterm)
    # MATLAB: solver_amvald_forward.m lines 82-104
    cdterm = np.ones((M, K))
    if cdscaling is not None and len(cdscaling) > 0:
        method = options.method if hasattr(options, 'method') else 'default'
        for r in nnzclasses:
            if np.isfinite(Nchain_in[r]):
                # Closed class: use selfArvlQlenSeenByClosed
                # MATLAB: cdterm(:,r) = pfqn_cdfun(1 + selfArvlQlenSeenByClosed, cdscaling)
                cdterm[:, r] = pfqn_cdfun(1 + selfArvlQlenSeenByClosed, cdscaling)
            else:
                # Open class: use stationaryQlen
                # MATLAB: cdterm(:,r) = pfqn_cdfun(1 + stationaryQlen, cdscaling)
                cdterm[:, r] = pfqn_cdfun(1 + stationaryQlen, cdscaling)

    # Compute effective service times
    # MATLAB: STeff(k,r) = STchain_in(k,r) * lldterm(k,r) * msterm(k) * cdterm(k,r) * ljdterm(k,r)
    Wchain = np.zeros((M, K))
    STeff = np.zeros((M, K))

    lldterm_2d = np.tile(lldterm.reshape(-1, 1), (1, K))

    for r in nnzclasses:
        for k in range(M):
            STeff[k, r] = STchain_in[k, r] * lldterm_2d[k, r] * msterm[k] * cdterm[k, r]

    # Compute waiting times based on scheduling strategy
    for ir, r in enumerate(nnzclasses):
        sd = np.setdiff1d(nnzclasses, [r])  # other classes

        for k in range(M):
            sched_k = sched.get(k, SchedStrategy.FCFS)

            if sched_k == SchedStrategy.EXT:
                # External source station - no queueing, zero waiting time
                Wchain[k, r] = 0.0

            elif sched_k == SchedStrategy.INF:
                # Infinite server (delay)
                Wchain[k, r] = STeff[k, r]

            elif sched_k == SchedStrategy.PS:
                # Processor sharing
                if r in ocl:
                    totQlen = np.sum(Qchain_in[k, nnzclasses])
                    Wchain[k, r] = STeff[k, r] * (1 + totQlen)
                else:
                    # MATLAB uses totArvlQlenSeenByClosed(k) with linear indexing which
                    # always accesses column 1 (class index 0). Match this behavior.
                    Wchain[k, r] = STeff[k, r] * (1 + totArvlQlenSeenByClosed[k, 0])
                    if len(ccl) > 0:
                        # Add linearizer correction
                        Wchain[k, r] += STeff[k, r] * ((Nt - 1) * gamma[r, k] if gamma.ndim == 2 and r < gamma.shape[0] and k < gamma.shape[1] else 0)

            elif sched_k in [SchedStrategy.FCFS, SchedStrategy.SIRO, SchedStrategy.LCFSPR]:
                # FCFS-type stations
                if STeff[k, r] > 0:
                    ns = nservers[k]

                    # Compute multiserver correction Bk (MATLAB solver_amvald_forward.m lines 370-380)
                    # Bk is a utilization-like term, NOT divided by ns
                    if ns > 1 and not np.isinf(ns):
                        # Use deltaclass_r where only the current class r uses deltaclass(r)
                        deltaclass_r = np.ones(K)
                        deltaclass_r[r] = deltaclass[r]
                        rho_sum = np.sum(deltaclass_r * Xchain_in * Vchain_in[k, :] * STeff[k, :])
                        if rho_sum < 0.75:
                            # Light-load case: Bk is utilization-like term (no ns division)
                            Bk = deltaclass_r * Xchain_in * Vchain_in[k, :] * STeff[k, :]
                        else:
                            # High-load case: power of (ns-1), not ns
                            Bk = (deltaclass_r * Xchain_in * Vchain_in[k, :] * STeff[k, :]) ** (ns - 1)
                        Bk = np.where(np.isfinite(Bk), Bk, 1.0)
                    else:
                        Bk = np.ones(K)

                    # Multi-server correction with serial think time
                    if ns > 1:
                        Wchain[k, r] = STeff[k, r] * (ns - 1)
                    else:
                        Wchain[k, r] = 0.0

                    # Add service time
                    Wchain[k, r] += STeff[k, r]

                    # Add queueing delay
                    if r in ocl:
                        Wchain[k, r] += (STeff[k, r] * deltaclass[r] * stationaryQlen[k, r] * Bk[r] +
                                        np.sum(STeff[k, sd] * Bk[sd] * stationaryQlen[k, sd]))
                    else:
                        Wchain[k, r] += (STeff[k, r] * selfArvlQlenSeenByClosed[k, r] * Bk[r] +
                                        np.sum(STeff[k, sd] * Bk[sd] * stationaryQlen[k, sd]))

            elif sched_k == SchedStrategy.HOL:
                # Head of Line (Priority) scheduling - matches MATLAB solver_amvald_forward.m lines 441-547
                if STeff[k, r] > 0:
                    ns = nservers[k]
                    hprio = nnzclasses_hprio.get(r, [])

                    # Priority scaling using Chandy-Lakshmi approximation (MATLAB lines 446-458)
                    # UHigherPrio = sum over h in hprio of: V[k,h] * STeff[k,h] * (X[h] - Q[k,h]*tau[h])
                    # prioScaling = max(tol, 1 - UHigherPrio), capped at 1-tol
                    # Then Wchain = STeff / prioScaling
                    tol = options.tol if hasattr(options, 'tol') and options.tol else 1e-6
                    UHigherPrio = 0.0
                    if len(hprio) > 0:
                        for h in hprio:
                            # MATLAB tau(h) uses linear indexing on K×K matrix, which is tau(h,1) = first column
                            # In Python 0-indexed: tau[h, 0]
                            tau_h = tau[h, 0] if tau.ndim == 2 and h < tau.shape[0] else 0.0
                            UHigherPrio += Vchain_in[k, h] * STeff[k, h] * (Xchain_in[h] - Qchain_in[k, h] * tau_h)

                    # MATLAB: prioScaling = min([max([options.tol,1-UHigherPrio]),1-options.tol])
                    prioScaling = max(tol, 1.0 - UHigherPrio)
                    prioScaling = min(prioScaling, 1.0 - tol)

                    if ns == 1 or np.isinf(ns):
                        # Single server: matches MATLAB lines 494-506
                        # Wchain = STeff / prioScaling
                        Wchain[k, r] = STeff[k, r] / prioScaling  # Base
                        if r in ocl:
                            # Open class: use stationaryQlen
                            Wchain[k, r] += (STeff[k, r] * stationaryQlen[k, r]) / prioScaling
                        else:
                            # Closed class: use selfArvlQlenSeenByClosed
                            Wchain[k, r] += (STeff[k, r] * selfArvlQlenSeenByClosed[k, r]) / prioScaling
                    else:
                        # Multi-server: matches MATLAB lines 527-542 (seidmann method)
                        # Compute Bk for multiserver approximation (same as FCFS - lines 460-474)
                        # Use deltaclass, not deltaclass_r for HOL priority
                        if np.sum(deltaclass * Xchain_in * Vchain_in[k, :] * STeff[k, :]) < 0.75:
                            # Light load case: Bk = utilization / ns (seidmann)
                            Bk = (deltaclass * Xchain_in * Vchain_in[k, :] * STeff[k, :]) / ns
                        else:
                            # High load case: power of ns (seidmann)
                            Bk = ((deltaclass * Xchain_in * Vchain_in[k, :] * STeff[k, :]) / ns) ** ns
                        Bk = np.where(np.isfinite(Bk), Bk, 1.0)

                        # Multi-server correction with serial think time (MATLAB lines 528-529)
                        # (1/nservers term already in STeff via msterm)
                        Wchain[k, r] = STeff[k, r] * (ns - 1) / prioScaling
                        Wchain[k, r] += STeff[k, r] / prioScaling  # Base

                        if r in ocl:
                            # Open class (MATLAB line 532)
                            Wchain[k, r] += (STeff[k, r] * stationaryQlen[k, r] * Bk[r]) / prioScaling
                        else:
                            # Closed class (MATLAB line 542)
                            Wchain[k, r] += (STeff[k, r] * selfArvlQlenSeenByClosed[k, r] * Bk[r]) / prioScaling

            else:
                # Default: same as FCFS
                Wchain[k, r] = STeff[k, r] * (1 + selfArvlQlenSeenByClosed[k, r])

    return Wchain, STeff


def solver_amvald(
    sn,  # NetworkStruct
    Lchain: np.ndarray,
    STchain: np.ndarray,
    Vchain: np.ndarray,
    alpha: np.ndarray,
    Nchain: np.ndarray,
    SCVchain: np.ndarray,
    refstatchain: np.ndarray,
    options: Optional[AmvaldOptions] = None
) -> AmvaldResult:
    """
    Approximate MVA for Load-Dependent networks (AMVA-LD).

    Implements iterative approximate MVA with under-relaxation for
    load-dependent queueing networks.

    Args:
        sn: Network structure
        Lchain: Demands per chain (M x K)
        STchain: Service times per chain (M x K)
        Vchain: Visit ratios per chain (M x K)
        alpha: Class-to-chain mapping
        Nchain: Population per chain (K,)
        SCVchain: Squared coefficient of variation (M x K)
        refstatchain: Reference station per chain (K,)
        options: Solver options

    Returns:
        AmvaldResult with Q, U, R, T, C, X, lG, totiter
    """
    if options is None:
        options = AmvaldOptions()


    M = sn.nstations
    K = sn.nchains

    Nchain = np.asarray(Nchain).flatten()
    Nt = np.sum(Nchain[np.isfinite(Nchain)])
    delta = (Nt - 1) / Nt if Nt > 0 else 0.0
    deltaclass = (Nchain - 1) / Nchain
    deltaclass[np.isinf(Nchain)] = 1.0
    deltaclass[Nchain <= 0] = 0.0

    tol = options.iter_tol
    nservers = np.asarray(sn.nservers).flatten() if sn.nservers is not None else np.ones(M)
    lldscaling = sn.lldscaling if hasattr(sn, 'lldscaling') and sn.lldscaling is not None else None
    cdscaling = sn.cdscaling if hasattr(sn, 'cdscaling') and sn.cdscaling is not None else None

    # Convert sched to dict if it's an array
    # sn.sched can be: dict, numpy array of strings, or None
    if hasattr(sn, 'sched') and sn.sched is not None:
        if isinstance(sn.sched, dict):
            sched = sn.sched
        elif hasattr(sn.sched, '__iter__') and not isinstance(sn.sched, str):
            # Convert array of strings to dict
            sched = {}
            for i, s in enumerate(sn.sched):
                if s is not None:
                    if isinstance(s, str):
                        # Map string names to SchedStrategy enum values
                        sched_map = {
                            'INF': SchedStrategy.INF,
                            'FCFS': SchedStrategy.FCFS,
                            'SIRO': SchedStrategy.SIRO,
                            'PS': SchedStrategy.PS,
                            'HOL': SchedStrategy.HOL,
                            'LCFSPR': SchedStrategy.LCFSPR,
                            'EXT': SchedStrategy.EXT,
                        }
                        sched[i] = sched_map.get(s, SchedStrategy.FCFS)
                    else:
                        sched[i] = s
        else:
            sched = {}
    else:
        sched = {}

    classprio = np.asarray(sn.classprio).flatten() if hasattr(sn, 'classprio') and sn.classprio is not None else None

    # Initialize Q, X, U
    Uchain = np.zeros((M, K))
    Tchain = np.zeros((M, K))

    # Balanced initialization for queue lengths
    Qchain = np.ones((M, K))
    Qchain = Qchain / np.sum(Qchain, axis=0, keepdims=True) * Nchain.reshape(1, -1)
    Qchain[np.isinf(Qchain)] = 0.0
    Qchain[:, Nchain == 0] = 0.0

    # For open classes, zero out at reference station
    for r in range(K):
        if np.isinf(Nchain[r]):
            refstat = int(refstatchain[r, 0]) if refstatchain.ndim > 1 else int(refstatchain[r])
            if refstat < M:
                Qchain[refstat, r] = 0.0

    nnzclasses = np.where(Nchain > 0)[0]
    Xchain = 1.0 / np.sum(STchain, axis=0)
    Xchain[np.isinf(Xchain)] = 0.0

    # For open classes, use arrival rate
    for r in range(K):
        if np.isinf(Nchain[r]):
            refstat = int(refstatchain[r, 0]) if refstatchain.ndim > 1 else int(refstatchain[r])
            if refstat < M and STchain[refstat, r] > 0:
                Xchain[r] = 1.0 / STchain[refstat, r]

    # Initialize utilization
    for k in range(M):
        for r in nnzclasses:
            if np.isinf(nservers[k]):
                Uchain[k, r] = Vchain[k, r] * STchain[k, r] * Xchain[r]
            else:
                Uchain[k, r] = Vchain[k, r] * STchain[k, r] * Xchain[r] / nservers[k]

    # Initialize correction factors
    # For 'lin' and 'qdlin' methods, gamma is 3D (K, M, K): class-based corrections
    # For other methods, gamma is 2D (K, M): total customer fraction corrections
    if options.method in ('lin', 'qdlin'):
        gamma = np.zeros((K, M, K))  # 3D for class-based corrections
    else:
        gamma = np.zeros((K, M))  # 2D for total corrections
    tau = np.zeros((K, K))

    # Main iteration loop
    omicron = 0.5  # under-relaxation parameter
    totiter = 0
    outer_iter = 0
    max_outer_iter = int(np.sqrt(options.iter_max))

    QchainOuter_1 = Qchain + np.inf

    while (outer_iter < 2 or np.max(np.abs(Qchain - QchainOuter_1)) > tol) and outer_iter < max_outer_iter:
        outer_iter += 1
        QchainOuter_1 = Qchain.copy()
        XchainOuter_1 = Xchain.copy()
        UchainOuter_1 = Uchain.copy()

        inner_iter = 0
        Qchain_1 = Qchain + np.inf

        while (inner_iter < 2 or np.max(np.abs(Qchain - Qchain_1)) > tol) and inner_iter <= max_outer_iter:
            inner_iter += 1

            Qchain_1 = Qchain.copy()
            Xchain_1 = Xchain.copy()
            Uchain_1 = Uchain.copy()

            # Forward step
            Wchain, STeff = solver_amvald_forward(
                M, K, nservers, lldscaling, cdscaling, sched, classprio, gamma, tau,
                Qchain_1, Xchain_1, Uchain_1, STchain, Vchain, Nchain, options
            )

            totiter += 1
            if totiter > options.iter_max:
                break

            # Update metrics
            Cchain_s = np.zeros(K)
            Rchain = np.zeros((M, K))

            for r in nnzclasses:
                if np.sum(Wchain[:, r]) == 0:
                    Xchain[r] = 0.0
                else:
                    if np.isinf(Nchain[r]):
                        Cchain_s[r] = np.dot(Vchain[:, r], Wchain[:, r])
                        # X remains constant for open classes
                    elif Nchain[r] == 0:
                        Xchain[r] = 0.0
                        Cchain_s[r] = 0.0
                    else:
                        Cchain_s[r] = np.dot(Vchain[:, r], Wchain[:, r])
                        Xchain[r] = omicron * Nchain[r] / Cchain_s[r] + (1 - omicron) * Xchain_1[r]

                for k in range(M):
                    Rchain[k, r] = Vchain[k, r] * Wchain[k, r]
                    Qchain[k, r] = omicron * Xchain[r] * Vchain[k, r] * Wchain[k, r] + (1 - omicron) * Qchain_1[k, r]
                    Tchain[k, r] = Xchain[r] * Vchain[k, r]
                    Uchain[k, r] = omicron * Vchain[k, r] * STeff[k, r] * Xchain[r] + (1 - omicron) * Uchain_1[k, r]

        # Update gamma and tau for linearizer methods only
        # In MATLAB, the gamma/tau update loop only runs for 'lin'/'qdlin' methods
        # For 'default' method, gamma and tau remain at their initial zero values
        if options.method in ('lin', 'qdlin'):
            ccl = np.where(np.isfinite(Nchain) & (Nchain > 0))[0]
            for s in range(K):
                if np.isfinite(Nchain[s]) and Nchain[s] > 0:
                    Nchain_s = Nchain.copy()
                    Nchain_s[s] = Nchain[s] - 1  # Population with one less job in class s
                    if options.method == 'lin':
                        # 3D gamma: gamma(s, k, r) = Qchain(k,r)/Nchain_s(r) - QchainOuter(k,r)/Nchain(r)
                        for k in range(M):
                            for r in nnzclasses:
                                if not np.isinf(Nchain[r]) and Nchain_s[r] > 0:
                                    gamma[s, k, r] = (Qchain_1[k, r] / Nchain_s[r] -
                                                      QchainOuter_1[k, r] / Nchain[r])
                    else:
                        # 2D gamma: gamma(s, k) = sum(Qchain(k,:))/(Nt-1) - sum(QchainOuter(k,:))/Nt
                        for k in range(M):
                            gamma[s, k] = (np.sum(Qchain_1[k, :]) / (Nt - 1) -
                                           np.sum(QchainOuter_1[k, :]) / Nt) if Nt > 1 else 0.0
                    # tau is updated for 'lin'/'qdlin' methods only
                    for r in nnzclasses:
                        tau[s, r] = Xchain_1[r] - XchainOuter_1[r]

    # Utilization capping
    for k in range(M):
        sched_k = sched.get(k, SchedStrategy.FCFS)
        if sched_k in [SchedStrategy.FCFS, SchedStrategy.SIRO, SchedStrategy.PS, SchedStrategy.LCFSPR, SchedStrategy.HOL]:
            U_sum = np.sum(Uchain[k, :])
            if U_sum > 1:
                for r in range(K):
                    if Vchain[k, r] * STeff[k, r] > 0:
                        denom = np.sum(Vchain[k, :] * STeff[k, :] * Xchain)
                        if denom > 0:
                            Uchain[k, r] = min(1.0, U_sum) * Vchain[k, r] * STeff[k, r] * Xchain[r] / denom

    # Compute final response times
    Rchain = np.zeros((M, K))
    for k in range(M):
        for r in range(K):
            if Tchain[k, r] > 0:
                Rchain[k, r] = Qchain[k, r] / Tchain[k, r]

    # Clean up non-finite values
    Xchain = np.where(np.isfinite(Xchain), Xchain, 0.0)
    Uchain = np.where(np.isfinite(Uchain), Uchain, 0.0)
    Rchain = np.where(np.isfinite(Rchain), Rchain, 0.0)

    # Zero out results for zero population chains
    for j in range(K):
        if Nchain[j] == 0:
            Xchain[j] = 0.0
            Uchain[:, j] = 0.0
            Qchain[:, j] = 0.0
            Rchain[:, j] = 0.0
            Tchain[:, j] = 0.0

    # Compute cycle times
    C_result = np.sum(Rchain, axis=0).reshape(1, -1)

    # Estimate normalizing constant
    ccl = np.where(np.isfinite(Nchain))[0]
    Nclosed = Nchain[ccl]
    Xclosed = Xchain[ccl]
    valid = Xclosed > options.tol
    if np.any(valid):
        lG = -np.sum(Nclosed[valid] * np.log(Xclosed[valid]))
    else:
        lG = np.nan

    return AmvaldResult(
        Q=Qchain,
        U=Uchain,
        R=Rchain,
        T=Tchain,
        C=C_result,
        X=Xchain.reshape(1, -1),
        lG=lG,
        totiter=totiter
    )


__all__ = [
    'solver_amvald',
    'solver_amvald_forward',
    'AmvaldOptions',
    'AmvaldResult',
    'SchedStrategy',
]
