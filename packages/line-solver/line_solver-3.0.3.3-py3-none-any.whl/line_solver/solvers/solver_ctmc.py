"""
Native Python implementation of CTMC (Continuous-Time Markov Chain) solver.

This implementation uses pure Python/NumPy algorithms from the api.solvers.ctmc
module, providing the same functionality as the JPype wrapper without .
"""

import numpy as np
import pandas as pd
import sys
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

from ..api.sn.transforms import sn_get_residt_from_respt
from ..api.sn.getters import sn_get_node_tput_from_tput, sn_get_node_arvr_from_tput
from ..api.sn.network_struct import NodeType
from .base import NetworkSolver


class OptionsDict(dict):
    """A dict that supports attribute-style access."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'OptionsDict' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"'OptionsDict' object has no attribute '{name}'")


@dataclass
class EventInfo:
    """Information about a single event in a simulation trace."""
    node: int = 0
    jobclass: int = 0
    t: float = 0.0
    event: str = None


@dataclass
class SampleResult:
    """Container for sample-based simulation results."""
    handle: str = ""
    t: np.ndarray = None
    state: np.ndarray = None
    event: List[EventInfo] = None
    isaggregate: bool = False
    nodeIndex: int = None
    numSamples: int = 0

    def __post_init__(self):
        if self.event is None:
            self.event = []


@dataclass
class SolverCTMCOptions:
    """Options for the native CTMC solver."""
    method: str = 'default'
    tol: float = 1e-6
    cutoff: int = 10
    seed: int = 23000
    samples: int = 10000  # Number of samples for simulation-based methods
    verbose: bool = False
    keep: bool = True  # Whether to keep state space after analysis
    config: Dict[str, Any] = field(default_factory=dict)  # Configuration dict (e.g., {'nonmkv': 'none'})


class SolverCTMC(NetworkSolver):
    """
    Native Python CTMC (Continuous-Time Markov Chain) solver.

    This solver analyzes queueing networks through exact state-space enumeration
    using pure Python/NumPy, providing the same functionality as the Java wrapper
    without requiring the JVM.

    Supported methods:
        - 'default': Basic state-space enumeration
        - 'basic': Same as default

    Args:
        model: Network model (Python wrapper or native structure)
        method: Solution method (default: 'default')
        **kwargs: Additional solver options
    """

    def __init__(self, model, method_or_options=None, **kwargs):
        self.model = model
        self._result = None
        self._sn = None

        # Handle options passed as second argument (MATLAB-style)
        if method_or_options is None:
            self.method = 'default'
        elif isinstance(method_or_options, str):
            self.method = method_or_options.lower()
        elif hasattr(method_or_options, 'get'):
            # Dict-like options object
            self.method = method_or_options.get('method', 'default')
            if hasattr(method_or_options, 'verbose'):
                kwargs.setdefault('verbose', method_or_options.verbose)
            if hasattr(method_or_options, 'cutoff'):
                kwargs.setdefault('cutoff', method_or_options.cutoff)
            if hasattr(method_or_options, 'seed'):
                kwargs.setdefault('seed', method_or_options.seed)
        elif hasattr(method_or_options, 'method'):
            # SolverOptions-like object
            self.method = getattr(method_or_options, 'method', 'default')
            if hasattr(method_or_options, 'verbose'):
                kwargs.setdefault('verbose', method_or_options.verbose)
            if hasattr(method_or_options, 'cutoff'):
                kwargs.setdefault('cutoff', method_or_options.cutoff)
            if hasattr(method_or_options, 'seed'):
                kwargs.setdefault('seed', method_or_options.seed)
        else:
            self.method = 'default'

        # Remove 'method' from kwargs if present to avoid duplicate argument
        kwargs.pop('method', None)
        self.options = SolverCTMCOptions(method=self.method, **kwargs)

        # Extract network structure
        self._extract_network_params()

    def getName(self) -> str:
        """Get the name of this solver."""
        return "CTMC"

    get_name = getName

    def _extract_network_params(self):
        """Extract parameters from the model for CTMC computation."""
        model = self.model

        # Priority 1: Native model with _sn
        if hasattr(model, '_sn') and model._sn is not None:
            self._sn = model._sn
            return

        # Priority 2: Native model with refresh_struct
        if hasattr(model, 'refresh_struct'):
            model.refresh_struct()
            if hasattr(model, '_sn'):
                self._sn = model._sn
                return

        # Priority 3: JPype wrapper
        if hasattr(model, 'obj'):
            try:
                from ..solvers.convert import wrapper_sn_to_native
                sn = model.getStruct()
                self._sn = wrapper_sn_to_native(sn)
                return
            except Exception:
                pass

        # Priority 4: Has getStruct method
        if hasattr(model, 'getStruct'):
            from ..solvers.convert import wrapper_sn_to_native
            sn = model.getStruct()
            self._sn = wrapper_sn_to_native(sn)
            return

        # Priority 5: Already a struct
        if hasattr(model, 'nclasses') and hasattr(model, 'nstations'):
            self._sn = model
            return

        raise ValueError("Cannot extract NetworkStruct from model")

    def runAnalyzer(self) -> 'SolverCTMC':
        """Run the CTMC analysis."""
        from ..api.solvers.ctmc.handler import (
            solver_ctmc, SolverCTMCOptions as HandlerOptions
        )

        # Create handler options
        handler_options = HandlerOptions(
            method=self.options.method,
            tol=self.options.tol,
            cutoff=self.options.cutoff,
            verbose=self.options.verbose
        )

        # Run the solver
        self._result = solver_ctmc(self._sn, handler_options)

        # Extract station and class names
        self._extract_names()

        # Compute cache hit/miss probabilities for cache nodes
        self._compute_cache_hit_miss_probs()

        # Print completion message if verbose
        if self.options.verbose:
            py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            runtime = self._result.runtime if hasattr(self._result, 'runtime') else 0.0
            method = self._result.method if hasattr(self._result, 'method') else 'basic'
            print(f"CTMC analysis [method: {method}, lang: python, env: {py_version}] completed in {runtime:.6f}s.")

        return self

    def _extract_names(self):
        """Extract station and class names from network struct."""
        if self._sn is not None:
            # Get station names by mapping station indices to node indices
            if hasattr(self._sn, 'stationToNode') and self._sn.stationToNode is not None and \
               hasattr(self._sn, 'nodenames') and self._sn.nodenames:
                import numpy as np
                station_to_node = np.asarray(self._sn.stationToNode).flatten()
                self.station_names = []
                for ist in range(self._sn.nstations):
                    if ist < len(station_to_node):
                        node_idx = int(station_to_node[ist])
                        if node_idx >= 0 and node_idx < len(self._sn.nodenames):
                            self.station_names.append(self._sn.nodenames[node_idx])
                        else:
                            self.station_names.append(f'Station{ist}')
                    else:
                        self.station_names.append(f'Station{ist}')
            elif hasattr(self._sn, 'nodenames') and self._sn.nodenames:
                # Fallback: use first nstations node names (for simple networks)
                self.station_names = list(self._sn.nodenames[:self._sn.nstations])
            else:
                self.station_names = [f'Station{i}' for i in range(self._sn.nstations)]

            self.class_names = list(self._sn.classnames) if hasattr(self._sn, 'classnames') and self._sn.classnames else \
                              [f'Class{i}' for i in range(self._sn.nclasses)]
        else:
            self.station_names = []
            self.class_names = []

    def _compute_cache_hit_miss_probs(self):
        """
        Compute actual hit/miss probabilities for cache nodes from CTMC results.

        This matches MATLAB's solver_ctmc_analyzer behavior where it computes
        actualhitprob and actualmissprob for cache nodes using the departure rates.
        These probabilities are then used by sn_get_node_tput_from_tput to compute
        node-level throughputs for hit/miss classes at cache nodes.

        References:
            MATLAB: solver_ctmc_analyzer.m lines 215-240
        """
        if self._sn is None or self._result is None:
            return

        sn = self._sn
        K = sn.nclasses
        I = sn.nnodes
        M = sn.nstations

        # Find cache nodes
        cache_nodes = []
        if hasattr(sn, 'nodetype') and sn.nodetype is not None:
            for ind in range(len(sn.nodetype)):
                if sn.nodetype[ind] == NodeType.CACHE:
                    cache_nodes.append(ind)

        if not cache_nodes:
            return

        # Get station-level throughput
        TN = self._result.T

        # For each cache node, compute actual hit/miss probabilities
        # We use routing probabilities from rtnodes to compute the hit/miss split
        # The rtnodes matrix encodes the probability of routing to hit vs miss class

        for cache_ind in cache_nodes:
            if sn.nodeparam is None or cache_ind not in sn.nodeparam:
                continue

            node_param = sn.nodeparam[cache_ind]
            if not hasattr(node_param, 'hitclass') or not hasattr(node_param, 'missclass'):
                continue

            hitclass = np.atleast_1d(node_param.hitclass).flatten()
            missclass = np.atleast_1d(node_param.missclass).flatten()

            # Initialize actual probabilities
            actual_hit_prob = np.zeros(K)
            actual_miss_prob = np.zeros(K)

            # Get cache throughput for the requesting class
            # The cache is a station, find its station index
            cache_ist = int(sn.nodeToStation[cache_ind]) if cache_ind < len(sn.nodeToStation) else -1

            # For each input class that has hit/miss classes defined
            for orig_class in range(len(hitclass)):
                h = int(hitclass[orig_class]) if orig_class < len(hitclass) else -1
                m = int(missclass[orig_class]) if orig_class < len(missclass) else -1

                if h < 0 or m < 0 or h >= K or m >= K:
                    continue

                # Get hit/miss probabilities from routing matrix (rtnodes)
                # The routing matrix encodes P(orig_class at cache -> hit_class at next node)
                # and P(orig_class at cache -> miss_class at next node)
                hit_prob = 0.0
                miss_prob = 0.0

                if hasattr(sn, 'rtnodes') and sn.rtnodes is not None:
                    # Sum routing probabilities from cache to any node for hit/miss classes
                    for jnd in range(I):
                        from_idx = cache_ind * K + orig_class
                        to_h_idx = jnd * K + h
                        to_m_idx = jnd * K + m
                        if from_idx < sn.rtnodes.shape[0]:
                            if to_h_idx < sn.rtnodes.shape[1]:
                                p = sn.rtnodes[from_idx, to_h_idx]
                                if p > 0:
                                    hit_prob += p
                            if to_m_idx < sn.rtnodes.shape[1]:
                                p = sn.rtnodes[from_idx, to_m_idx]
                                if p > 0:
                                    miss_prob += p

                # Normalize probabilities
                total_prob = hit_prob + miss_prob
                if total_prob > 0:
                    actual_hit_prob[orig_class] = hit_prob / total_prob
                    actual_miss_prob[orig_class] = miss_prob / total_prob

            # Store in nodeparam
            node_param.actualhitprob = actual_hit_prob
            node_param.actualmissprob = actual_miss_prob

    # =========================================================================
    # Table Output
    # =========================================================================

    def getAvgTable(self) -> pd.DataFrame:
        """
        Get comprehensive average performance metrics table.

        Returns node-level results (one row per node per class) to match MATLAB output format.
        Non-station nodes (e.g., Fork, ClassSwitch) are included with computed metrics.
        Cache nodes include HitClass/MissClass throughputs using actual hit/miss probabilities.

        Returns:
            pandas.DataFrame with columns: Node, JobClass, QLen, Util, RespT, ResidT, ArvR, Tput
        """
        if self._result is None:
            self.runAnalyzer()

        sn = self._sn
        M = self._result.Q.shape[0]  # nstations
        K = self._result.Q.shape[1]  # nclasses
        I = sn.nnodes if sn is not None else M

        # Get station-level results
        QN = self._result.Q
        UN = self._result.U
        RN = self._result.R
        TN = self._result.T

        # Compute ResidT using proper visit ratios from network structure
        if sn is not None and sn.visits:
            WN = sn_get_residt_from_respt(sn, RN, None)
        else:
            WN = RN.copy()

        # Convert station-level to node-level results
        # Initialize node-level arrays
        QNn = np.zeros((I, K))
        UNn = np.zeros((I, K))
        RNn = np.zeros((I, K))
        WNn = np.zeros((I, K))

        # Map station metrics to node metrics
        if sn is not None and hasattr(sn, 'stationToNode'):
            stationToNode = np.asarray(sn.stationToNode).flatten()
            for ist in range(M):
                if ist < len(stationToNode):
                    ind = int(stationToNode[ist])
                    if ind >= 0 and ind < I:
                        QNn[ind, :] = QN[ist, :]
                        UNn[ind, :] = UN[ist, :]
                        RNn[ind, :] = RN[ist, :]
                        WNn[ind, :] = WN[ist, :]
        else:
            # No mapping - assume stations are nodes
            for ist in range(min(M, I)):
                QNn[ist, :] = QN[ist, :]
                UNn[ist, :] = UN[ist, :]
                RNn[ist, :] = RN[ist, :]
                WNn[ist, :] = WN[ist, :]

        # Compute node-level throughputs and arrival rates
        # This properly handles cache hit/miss class throughputs using actual probabilities
        ANn = sn_get_node_arvr_from_tput(sn, TN, TN)
        TNn = sn_get_node_tput_from_tput(sn, TN, TN, ANn)

        # Post-processing for cache nodes:
        # For cache nodes, the throughput of hit/miss classes equals the arrival rate
        # at the downstream ClassSwitch node for those classes.
        # Also, the throughput of the requesting class at the cache should be 0
        # (since jobs leave as hit/miss classes, not the original class).
        if hasattr(sn, 'nodetype') and sn.nodetype is not None:
            for cache_ind in range(I):
                if sn.nodetype[cache_ind] != NodeType.CACHE:
                    continue
                if sn.nodeparam is None or cache_ind not in sn.nodeparam:
                    continue

                node_param = sn.nodeparam[cache_ind]
                if not hasattr(node_param, 'hitclass') or not hasattr(node_param, 'missclass'):
                    continue

                hitclass = np.atleast_1d(node_param.hitclass).flatten()
                missclass = np.atleast_1d(node_param.missclass).flatten()

                # Find ClassSwitch node connected to this cache
                cs_ind = -1
                for jnd in range(I):
                    if sn.nodetype[jnd] == NodeType.CLASSSWITCH:
                        if hasattr(sn, 'connmatrix') and sn.connmatrix is not None:
                            if sn.connmatrix[cache_ind, jnd] > 0:
                                cs_ind = jnd
                                break

                # For each requesting class that has hit/miss classes
                for orig_class in range(len(hitclass)):
                    h = int(hitclass[orig_class]) if orig_class < len(hitclass) else -1
                    m = int(missclass[orig_class]) if orig_class < len(missclass) else -1

                    if h >= 0 and h < K and m >= 0 and m < K:
                        # Set throughput of requesting class at cache to 0
                        # (jobs leave as hit/miss classes)
                        TNn[cache_ind, orig_class] = 0.0

                        # Set throughput of hit/miss classes at cache
                        # equals the arrival rate at ClassSwitch for those classes
                        if cs_ind >= 0 and cs_ind < I:
                            if h < ANn.shape[1]:
                                TNn[cache_ind, h] = ANn[cs_ind, h]
                            if m < ANn.shape[1]:
                                TNn[cache_ind, m] = ANn[cs_ind, m]

        # Build table with node-level results
        rows = []
        nodenames = list(sn.nodenames) if sn is not None and hasattr(sn, 'nodenames') and sn.nodenames else []
        classnames = list(sn.classnames) if sn is not None and hasattr(sn, 'classnames') and sn.classnames else []

        for ind in range(I):
            for r in range(K):
                node_name = nodenames[ind] if ind < len(nodenames) else f'Node{ind}'
                class_name = classnames[r] if r < len(classnames) else f'Class{r}'

                rows.append({
                    'Node': node_name,
                    'JobClass': class_name,
                    'QLen': QNn[ind, r],
                    'Util': UNn[ind, r],
                    'RespT': RNn[ind, r],
                    'ResidT': WNn[ind, r],
                    'ArvR': ANn[ind, r],
                    'Tput': TNn[ind, r],
                })

        df = pd.DataFrame(rows)

        # Filter out all-zero rows (MATLAB excludes nodes with no metrics)
        numeric_cols = ['QLen', 'Util', 'RespT', 'ResidT', 'ArvR', 'Tput']
        tokeep = ~(df[numeric_cols] <= 0.0).all(axis=1)
        df = df.loc[tokeep].reset_index(drop=True)

        if not self._table_silent:
            print(df.to_string(index=False))

        return df

    # =========================================================================
    # Individual Metric Accessors
    # =========================================================================

    def getAvgQLen(self) -> np.ndarray:
        """Get average queue lengths (M x K)."""
        if self._result is None:
            self.runAnalyzer()
        return self._result.Q.copy()

    def getAvgUtil(self) -> np.ndarray:
        """Get average utilizations (M x K)."""
        if self._result is None:
            self.runAnalyzer()
        return self._result.U.copy()

    def getAvgRespT(self) -> np.ndarray:
        """Get average response times (M x K)."""
        if self._result is None:
            self.runAnalyzer()
        return self._result.R.copy()

    def getAvgResidT(self) -> np.ndarray:
        """Get average residence times (M x K).

        Residence time is computed from response time using visit ratios:
        WN[ist,k] = RN[ist,k] * V[ist,k] / V[refstat,refclass]
        """
        if self._result is None:
            self.runAnalyzer()

        # Compute ResidT using proper visit ratios from network structure
        if self._sn is not None and self._sn.visits:
            return sn_get_residt_from_respt(self._sn, self._result.R, None)
        else:
            # Fallback: ResidT = RespT (no visit information available)
            return self._result.R.copy()

    def getAvgWaitT(self) -> np.ndarray:
        """Get average waiting times (M x K)."""
        if self._result is None:
            self.runAnalyzer()

        R = self._result.R.copy()
        # W = R - S where S is service time (1/rate)
        if hasattr(self._sn, 'rates') and self._sn.rates is not None:
            rates = np.asarray(self._sn.rates)
            S = np.zeros_like(rates)
            nonzero = rates > 0
            S[nonzero] = 1.0 / rates[nonzero]
            W = R - S
            W = np.maximum(W, 0.0)
            return W
        return R

    def getAvgTput(self) -> np.ndarray:
        """Get average throughputs (M x K)."""
        if self._result is None:
            self.runAnalyzer()
        return self._result.T.copy()

    def getAvgArvR(self) -> np.ndarray:
        """Get average arrival rates (M x K)."""
        return self.getAvgTput()

    def getAvgSysRespT(self) -> np.ndarray:
        """Get system response times (cycle times) (K,).

        Note:
            For closed networks: uses Little's Law C = N/X
            For open networks: sum of response times across all stations
        """
        if self._result is None:
            self.runAnalyzer()

        X = self._result.X.flatten()
        njobs = self._sn.njobs.flatten() if self._sn is not None and hasattr(self._sn, 'njobs') else None
        nclasses = len(X)
        C = np.zeros(nclasses)

        for k in range(nclasses):
            if njobs is not None and k < len(njobs) and np.isfinite(njobs[k]):
                # Closed class: use Little's Law (matching MATLAB getAvgSys.m line 135)
                if X[k] > 0:
                    C[k] = njobs[k] / X[k]
                else:
                    C[k] = np.inf
            else:
                # Open class: sum of response times across all stations
                R = self._result.R
                C[k] = np.sum(R[:, k])

        return C

    def getAvgSysTput(self) -> np.ndarray:
        """Get system throughputs (K,)."""
        if self._result is None:
            self.runAnalyzer()
        return self._result.X.flatten()

    # =========================================================================
    # CTMC-Specific Methods
    # =========================================================================

    def getStateSpace(self):
        """Get the enumerated state space.

        Returns:
            tuple: (stateSpace, localStateSpace) where stateSpace is the global
                state matrix and localStateSpace is a list of per-station state arrays.
                For FCFS queues with multiple servers, localStateSpace includes
                buffer and phase columns (matching MATLAB's nodeStateSpace format).
        """
        if self._result is None:
            self.runAnalyzer()
        space = self._result.space.copy() if self._result.space is not None else np.array([])

        # Generate localStateSpace - slice state space by station using column ranges
        localStateSpace = []
        if self._sn is not None and space.size > 0:
            nstations = self._sn.nstations

            # Use station_col_ranges if available (proper column structure)
            if hasattr(self._result, 'station_col_ranges') and self._result.station_col_ranges is not None:
                for ist in range(nstations):
                    if ist < len(self._result.station_col_ranges):
                        start_col, end_col = self._result.station_col_ranges[ist]
                        if end_col > start_col and end_col <= space.shape[1]:
                            localStateSpace.append(space[:, start_col:end_col])
                        else:
                            # Empty range for this station (e.g., Source/Sink)
                            localStateSpace.append(np.array([]).reshape(space.shape[0], 0))
                    else:
                        localStateSpace.append(np.array([]).reshape(space.shape[0], 0))
            else:
                # Fallback: assume one column per (station, class) pair (old behavior)
                nclasses = self._sn.nclasses
                for i in range(nstations):
                    station_cols = []
                    for r in range(nclasses):
                        col_idx = i * nclasses + r
                        if col_idx < space.shape[1]:
                            station_cols.append(space[:, col_idx:col_idx+1])
                    if station_cols:
                        localStateSpace.append(np.hstack(station_cols))
                    else:
                        localStateSpace.append(np.array([]))

        return space, localStateSpace

    def getSteadyState(self) -> np.ndarray:
        """Get the steady-state probability distribution."""
        if self._result is None:
            self.runAnalyzer()
        return self._result.pi.copy() if self._result.pi is not None else np.array([])

    def getInfGen(self) -> np.ndarray:
        """Get the infinitesimal generator matrix."""
        if self._result is None:
            self.runAnalyzer()
        return self._result.infgen.copy() if self._result.infgen is not None else np.array([])

    # =========================================================================
    # CDF and Percentile Methods
    # =========================================================================

    def getCdfRespT(self, R: Optional[np.ndarray] = None) -> List[Dict]:
        """
        Get response time CDF using exponential approximation.

        Returns:
            List of dicts with 'station', 'class', 't', 'p' keys
        """
        if self._result is None:
            self.runAnalyzer()

        if R is None:
            R = self._result.R

        nstations, nclasses = R.shape
        RD = []

        for i in range(nstations):
            for r in range(nclasses):
                mean_resp_t = R[i, r]
                if mean_resp_t <= 0:
                    continue

                lambda_rate = 1.0 / mean_resp_t
                quantiles = np.linspace(0.001, 0.999, 100)
                times = -np.log(1 - quantiles) / lambda_rate
                cdf_vals = 1 - np.exp(-lambda_rate * times)

                RD.append({
                    'station': i + 1,
                    'class': r + 1,
                    't': times,
                    'p': cdf_vals,
                })

        return RD

    def getPerctRespT(
        self,
        percentiles: Optional[List[float]] = None,
        jobclass: Optional[int] = None
    ) -> Tuple[List[Dict], pd.DataFrame]:
        """
        Extract percentiles from response time distribution.

        Args:
            percentiles: List of percentiles (0-100). Default: [10, 25, 50, 75, 90, 95, 99]
            jobclass: Optional class filter (1-based)

        Returns:
            Tuple of (percentile_list, percentile_table)
        """
        if percentiles is None:
            percentiles = [10, 25, 50, 75, 90, 95, 99]

        percentiles = np.asarray(percentiles)
        percentiles = np.clip(percentiles, 0.01, 99.99)
        percentiles_normalized = percentiles / 100.0

        if self._result is None:
            self.runAnalyzer()

        R = self._result.R
        nstations, nclasses = R.shape

        PercRT = []
        rows = []
        perc_col_names = [f'P{int(p)}' for p in percentiles]

        for i in range(nstations):
            for r in range(nclasses):
                if jobclass is not None and (r + 1) != jobclass:
                    continue

                mean_resp_t = R[i, r]
                if mean_resp_t <= 0:
                    continue

                lambda_rate = 1.0 / mean_resp_t
                perc_values = -np.log(1 - percentiles_normalized) / lambda_rate

                PercRT.append({
                    'station': i + 1,
                    'class': r + 1,
                    'percentiles': percentiles.tolist(),
                    'values': perc_values.tolist(),
                })

                row_data = {
                    'Station': self.station_names[i] if i < len(self.station_names) else f'Station{i}',
                    'Class': self.class_names[r] if r < len(self.class_names) else f'Class{r}',
                }
                for perc_col, perc_val in zip(perc_col_names, perc_values):
                    row_data[perc_col] = perc_val
                rows.append(row_data)

        PercTable = pd.DataFrame(rows) if rows else pd.DataFrame()
        return PercRT, PercTable

    # =========================================================================
    # Probability Methods
    # =========================================================================

    def getProbAggr(self, ist) -> float:
        """
        Get probability of a specific per-class job distribution at a station.

        Returns P(n1 jobs of class 1, n2 jobs of class 2, ...) for the state
        that was set via setState() on the station.

        Args:
            ist: Station index (0-based) or node object

        Returns:
            Probability that station ist is in the specified state.
        """
        # Convert node object to index if needed (like MATLAB)
        if not isinstance(ist, (int, np.integer)):
            ist = ist.get_station_index0()

        if self._result is None:
            self.runAnalyzer()

        if self._result.pi is None or len(self._result.pi) == 0:
            return 0.0

        pi = self._result.pi
        space = self._result.space

        if space is None or len(space) == 0:
            return 0.0

        # Get the query state for this station from _sn.state
        # _sn.state is a list of arrays, one per station
        if self._sn is None or self._sn.state is None:
            return 0.0

        # Get query state for station ist
        if ist >= len(self._sn.state) or self._sn.state[ist] is None:
            # No state set for this station - return total probability (1.0)
            return 1.0

        query_state = np.atleast_1d(self._sn.state[ist])

        # For aggregated state space, each column in space represents
        # the total number of jobs at that station (summed across classes)
        # We need to match against the query state

        # Sum probabilities for all states where station ist matches the query
        prob = 0.0

        # Check if space is aggregated (nstations columns) or detailed
        nstations = self._sn.nstations if self._sn else space.shape[1]

        if space.shape[1] == nstations:
            # Aggregated space: each column is total jobs at a station
            # Query state may be per-class [n1, n2, ...] or total [n]
            query_total = np.sum(query_state)

            for s_idx, state_prob in enumerate(pi):
                if ist < space.shape[1]:
                    state_jobs_at_ist = space[s_idx, ist]
                    if np.isclose(state_jobs_at_ist, query_total):
                        prob += state_prob
        else:
            # Detailed space: need to extract station portion
            # This handles the case where space has per-class columns
            # Space layout: [station1_class1, station1_class2, ..., station2_class1, ...]
            nclasses = self._sn.nclasses if self._sn else 1
            start_col = ist * nclasses
            end_col = start_col + nclasses

            if end_col <= space.shape[1]:
                for s_idx, state_prob in enumerate(pi):
                    state_at_ist = space[s_idx, start_col:end_col]
                    # Compare with query state (handle different lengths)
                    if len(query_state) == len(state_at_ist):
                        if np.allclose(state_at_ist, query_state):
                            prob += state_prob
                    else:
                        # Compare totals
                        if np.isclose(np.sum(state_at_ist), np.sum(query_state)):
                            prob += state_prob

        return prob

    def getProbSysAggr(self) -> Tuple[float, float]:
        """
        Get probability of the entire system being in the specified state.

        Returns the joint probability of the system being in the aggregated
        state configuration set via setState() on all stations.

        Returns:
            Tuple of (log_prob, prob) where prob is the joint probability
            of the entire system being in the specified state.
        """
        if self._result is None:
            self.runAnalyzer()

        if self._result.pi is None or len(self._result.pi) == 0:
            return float('-inf'), 0.0

        pi = self._result.pi
        space = self._result.space

        if space is None or len(space) == 0:
            return float('-inf'), 0.0

        if self._sn is None or self._sn.state is None:
            return float('-inf'), 0.0

        nstations = self._sn.nstations
        nclasses = self._sn.nclasses

        # Determine if state space is aggregated or detailed
        expected_detailed_cols = nstations * nclasses
        is_detailed = space.shape[1] == expected_detailed_cols

        if is_detailed:
            # Build the full query vector by concatenating station states
            # State space layout: [sta0_cls0, sta0_cls1, ..., sta1_cls0, ...]
            query_vector = []
            for ist in range(nstations):
                if ist < len(self._sn.state) and self._sn.state[ist] is not None:
                    station_state = np.atleast_1d(self._sn.state[ist])
                    # Ensure it has nclasses elements
                    if len(station_state) < nclasses:
                        station_state = np.pad(station_state, (0, nclasses - len(station_state)))
                    query_vector.extend(station_state[:nclasses])
                else:
                    # No state set - use -1 as wildcard
                    query_vector.extend([-1] * nclasses)

            query_vector = np.array(query_vector)

            # Sum probabilities for all states that match the query
            prob = 0.0
            for s_idx, state_prob in enumerate(pi):
                state_row = space[s_idx, :]

                # Check if this state matches the query (ignoring wildcards)
                match = True
                for col_idx in range(len(query_vector)):
                    if query_vector[col_idx] >= 0:  # Not a wildcard
                        if col_idx < len(state_row):
                            if not np.isclose(state_row[col_idx], query_vector[col_idx]):
                                match = False
                                break
                        else:
                            match = False
                            break

                if match:
                    prob += state_prob
        else:
            # Aggregated state space - compare totals per station
            query_totals = []
            for ist in range(nstations):
                if ist < len(self._sn.state) and self._sn.state[ist] is not None:
                    query_totals.append(np.sum(np.atleast_1d(self._sn.state[ist])))
                else:
                    query_totals.append(-1)  # -1 means "ignore this station"

            query_totals = np.array(query_totals)

            prob = 0.0
            for s_idx, state_prob in enumerate(pi):
                state_totals = space[s_idx, :nstations] if space.shape[1] >= nstations else space[s_idx, :]

                # Check if this state matches the query
                match = True
                for ist in range(min(nstations, len(state_totals))):
                    if query_totals[ist] >= 0:  # Not a wildcard
                        if not np.isclose(state_totals[ist], query_totals[ist]):
                            match = False
                            break

                if match:
                    prob += state_prob

        log_prob = np.log(prob) if prob > 0 else float('-inf')
        return log_prob, prob

    def getProb(self, station=None) -> np.ndarray:
        """Get state probabilities at station.

        Args:
            station: Station index (0-based) or node object. If None, returns steady-state.

        Returns:
            Probability vector
        """
        if self._result is None:
            self.runAnalyzer()

        if station is None:
            return self.getSteadyState()

        # Convert node object to index if needed (like MATLAB)
        if not isinstance(station, (int, np.integer)):
            station = station.get_station_index0()

        # Return marginal for station
        pi = self._result.pi
        space = self._result.space

        if pi is None or space is None:
            return np.array([1.0])

        # Compute marginal probability for station
        max_n = int(np.max(space[:, station]) if space.shape[1] > station else 0) + 1
        marginal = np.zeros(max_n)

        for s, prob in enumerate(pi):
            n = int(space[s, station]) if space.shape[1] > station else 0
            if n < max_n:
                marginal[n] += prob

        return marginal

    def getGenerator(self):
        """Get the infinitesimal generator matrix and event filters.

        Returns:
            tuple: (infGen, eventFilt) where infGen is the infinitesimal generator
                matrix and eventFilt is a dictionary mapping event types to sparse matrices
        """
        infGen = self.getInfGen()

        # Generate event filters from the stored event information
        eventFilt = {}
        if self._result is not None and hasattr(self._result, 'eventFilt') and self._result.eventFilt is not None:
            eventFilt = self._result.eventFilt
        elif self._result is not None and hasattr(self._result, 'infgen') and self._result.infgen is not None:
            # Return empty dict if eventFilt not available
            eventFilt = {}

        return infGen, eventFilt

    def getStateSpaceAggr(self) -> np.ndarray:
        """Get aggregated state space (total jobs per station).

        Returns:
            Array where each row is aggregated state (total jobs at each station)
        """
        if self._result is None:
            self.runAnalyzer()

        space = self._result.space
        if space is None or len(space) == 0:
            return np.array([])

        # For multi-class, aggregate over classes
        nstations = self._sn.nstations if self._sn else space.shape[1]
        nclasses = self._sn.nclasses if self._sn else 1

        if nclasses == 1:
            return space.copy()

        # Aggregate: sum jobs across classes for each station
        # Assuming space has shape (nstates, nstations * nclasses)
        nstates = space.shape[0]
        aggr_space = np.zeros((nstates, nstations))

        for i in range(nstations):
            for r in range(nclasses):
                col = i * nclasses + r
                if col < space.shape[1]:
                    aggr_space[:, i] += space[:, col]

        return aggr_space

    def getCdfSysRespT(self) -> List[Dict]:
        """Get system response time CDF.

        Returns:
            List of dicts with 'class', 't', 'p' keys
        """
        if self._result is None:
            self.runAnalyzer()

        C = self._result.C
        nclasses = len(C)
        RD = []

        for r in range(nclasses):
            mean_sys_resp_t = C[r]
            if mean_sys_resp_t <= 0:
                continue

            lambda_rate = 1.0 / mean_sys_resp_t
            quantiles = np.linspace(0.001, 0.999, 100)
            times = -np.log(1 - quantiles) / lambda_rate
            cdf_vals = 1 - np.exp(-lambda_rate * times)

            RD.append({
                'class': r + 1,
                't': times,
                'p': cdf_vals,
            })

        return RD

    def getReward(self, reward_vector: Optional[np.ndarray] = None) -> float:
        """Compute reward function over steady-state distribution.

        Args:
            reward_vector: Reward for each state. If None, uses queue length.

        Returns:
            Expected reward
        """
        if self._result is None:
            self.runAnalyzer()

        pi = self._result.pi
        if pi is None:
            return 0.0

        if reward_vector is None:
            # Default: expected queue length
            space = self._result.space
            if space is None:
                return 0.0
            reward_vector = np.sum(space, axis=1)

        return np.dot(pi, reward_vector)

    def getAvgReward(self) -> Tuple[np.ndarray, List[str]]:
        """Get steady-state expected reward values.

        Computes the steady-state expected reward for reward functions
        previously defined using model.setReward().

        Returns:
            Tuple of (R, names) where:
            - R: numpy array of expected reward values
            - names: list of reward function names

        Example:
            >>> model.setReward('QueueLength', lambda state: state.at(queue, oclass))
            >>> solver = CTMC(model)
            >>> R, names = solver.getAvgReward()
        """
        if self._result is None:
            self.runAnalyzer()

        # Get rewards from the model
        if hasattr(self.model, 'get_rewards'):
            rewards_dict = self.model.get_rewards()
        elif hasattr(self.model, '_rewards'):
            rewards_dict = self.model._rewards
        else:
            rewards_dict = {}

        if not rewards_dict:
            return np.array([]), []

        # Get state space and steady-state probabilities
        pi = self._result.pi
        space = self._result.space

        if pi is None or len(pi) == 0 or space is None or len(space) == 0:
            return np.array([0.0] * len(rewards_dict)), list(rewards_dict.keys())

        # Build mappings for RewardState
        from ..lang.reward_state import RewardState
        sn = self._sn

        # Build node-to-station mapping
        nodes_to_station = {}
        if hasattr(self.model, 'get_nodes'):
            for node in self.model.get_nodes():
                if hasattr(node, 'get_index'):
                    node_idx = node.get_index()
                elif hasattr(node, 'index'):
                    node_idx = node.index
                else:
                    continue

                if hasattr(sn, 'nodeToStation'):
                    node_idx0 = node_idx - 1  # 0-indexed
                    if node_idx0 < len(sn.nodeToStation):
                        station_idx = int(sn.nodeToStation[node_idx0])
                        if station_idx >= 0:
                            nodes_to_station[node_idx] = station_idx + 1  # 1-based

        # Build class-to-index mapping
        classes_to_idx = {}
        if hasattr(self.model, 'get_classes'):
            for i, jobclass in enumerate(self.model.get_classes()):
                if hasattr(jobclass, 'get_index'):
                    class_idx = jobclass.get_index()
                elif hasattr(jobclass, 'index'):
                    class_idx = jobclass.index
                else:
                    class_idx = i + 1
                classes_to_idx[class_idx] = i + 1

        # Compute expected reward for each reward function
        R = []
        names = list(rewards_dict.keys())

        for name, reward_fn in rewards_dict.items():
            expected_value = 0.0

            for state_idx, state_vec in enumerate(space):
                prob = pi[state_idx]
                if prob <= 0:
                    continue

                # Create RewardState for this state vector
                reward_state = RewardState(state_vec, sn, nodes_to_station, classes_to_idx)

                # Evaluate reward function
                try:
                    # Check if reward_fn takes sn argument (for Reward templates)
                    import inspect
                    sig = inspect.signature(reward_fn)
                    if len(sig.parameters) >= 2:
                        reward_value = reward_fn(reward_state, sn)
                    else:
                        reward_value = reward_fn(reward_state)
                    expected_value += prob * reward_value
                except Exception as e:
                    # Skip if reward function fails for this state
                    pass

            R.append(expected_value)

        return np.array(R), names

    get_avg_reward = getAvgReward

    def getTranCdfRespT(self, t_max: float = 10.0, n_points: int = 100) -> List[Dict]:
        """Get transient response time CDF approximation.

        Uses steady-state CDF as approximation for transient behavior.

        Args:
            t_max: Maximum time horizon
            n_points: Number of time points

        Returns:
            List of dicts with 'station', 'class', 't', 'p' keys
        """
        # For CTMC, transient analysis requires matrix exponential
        # Use steady-state as approximation
        return self.getCdfRespT()

    # =========================================================================
    # Transient Probability Methods
    # =========================================================================

    def getTranProb(self, node: int, t: float = 1.0) -> np.ndarray:
        """Get transient state probabilities at a node.

        Computes π(t) = π(0) * exp(Q*t) using matrix exponential.

        Args:
            node: Node/station index (0-based)
            t: Time point for transient analysis

        Returns:
            Transient probability vector at time t
        """
        if self._result is None:
            self.runAnalyzer()

        from scipy.linalg import expm

        Q = self._result.Q_matrix
        if Q is None:
            # Fall back to steady-state
            return self.getProb(node)

        # Initial distribution (start from state 0)
        n_states = Q.shape[0]
        pi_0 = np.zeros(n_states)
        pi_0[0] = 1.0

        # Compute transient probability: π(t) = π(0) * exp(Q*t)
        pi_t = pi_0 @ expm(Q * t)

        # Extract marginal for node
        space = self._result.space
        if space is None or node >= space.shape[1]:
            return pi_t

        # Compute marginal probability for node
        max_n = int(np.max(space[:, node])) + 1
        marginal = np.zeros(max_n)

        for s, prob in enumerate(pi_t):
            n = int(space[s, node])
            if n < max_n:
                marginal[n] += prob

        return marginal

    def getTranProbAggr(self, node: int, t: float = 1.0) -> np.ndarray:
        """Get transient aggregated state probabilities at a node.

        Args:
            node: Node/station index (0-based)
            t: Time point for transient analysis

        Returns:
            Transient aggregated probability vector at time t
        """
        return self.getTranProb(node, t)

    def getTranProbSys(self, t: float = 1.0) -> np.ndarray:
        """Get transient system state probabilities.

        Computes full system state probability at time t.

        Args:
            t: Time point for transient analysis

        Returns:
            Transient system probability vector at time t
        """
        if self._result is None:
            self.runAnalyzer()

        from scipy.linalg import expm

        Q = self._result.Q_matrix
        if Q is None:
            # Fall back to steady-state
            return self.getSteadyState()

        # Initial distribution (start from state 0)
        n_states = Q.shape[0]
        pi_0 = np.zeros(n_states)
        pi_0[0] = 1.0

        # Compute transient probability: π(t) = π(0) * exp(Q*t)
        pi_t = pi_0 @ expm(Q * t)

        return pi_t

    def getTranProbSysAggr(self, t: float = 1.0) -> np.ndarray:
        """Get transient aggregated system state probabilities.

        Args:
            t: Time point for transient analysis

        Returns:
            Transient system probability vector at time t
        """
        return self.getTranProbSys(t)

    # =========================================================================
    # Symbolic Generator Methods
    # =========================================================================

    def getSymbolicGenerator(self, invert_symbol: bool = False,
                             prime_numbers: Optional[List[int]] = None) -> np.ndarray:
        """Get symbolic generator matrix using prime number encoding.

        Each transition is encoded using prime numbers to identify
        the event type that triggers the transition.

        Args:
            invert_symbol: If True, invert the symbol encoding
            prime_numbers: Custom list of prime numbers for encoding.
                          If None, uses first N primes where N = number of event types.

        Returns:
            Symbolic generator matrix with prime-encoded transitions
        """
        if self._result is None:
            self.runAnalyzer()

        Q = self._result.Q_matrix
        if Q is None:
            return np.array([[]])

        n_states = Q.shape[0]

        # Generate prime numbers for encoding if not provided
        if prime_numbers is None:
            # Use simple prime generator for first 100 primes
            def sieve_primes(n):
                sieve = [True] * (n + 1)
                sieve[0] = sieve[1] = False
                for i in range(2, int(n ** 0.5) + 1):
                    if sieve[i]:
                        for j in range(i * i, n + 1, i):
                            sieve[j] = False
                return [i for i in range(n + 1) if sieve[i]]

            prime_numbers = sieve_primes(500)[:100]

        # Create symbolic generator
        Q_sym = np.zeros_like(Q)

        prime_idx = 0
        for i in range(n_states):
            for j in range(n_states):
                if i != j and Q[i, j] != 0:
                    if prime_idx < len(prime_numbers):
                        symbol = prime_numbers[prime_idx]
                        if invert_symbol:
                            symbol = 1.0 / symbol
                        Q_sym[i, j] = symbol * np.sign(Q[i, j])
                        prime_idx += 1
                    else:
                        Q_sym[i, j] = Q[i, j]

        # Diagonal elements are negative sum of row
        for i in range(n_states):
            Q_sym[i, i] = -np.sum(Q_sym[i, :])

        return Q_sym

    def getMarkedCTMC(self) -> Dict[str, Any]:
        """Get a marked CTMC object representation.

        Returns a dictionary containing the CTMC with marked transitions
        for reward and passage time analysis.

        Returns:
            Dictionary with 'Q' (generator), 'space' (state space),
            'pi' (steady-state), and 'marks' (transition markings)
        """
        if self._result is None:
            self.runAnalyzer()

        Q = self._result.Q_matrix
        space = self._result.space
        pi = self._result.pi

        # Create transition markings (identify each transition type)
        n_states = Q.shape[0] if Q is not None else 0
        marks = {}

        if Q is not None:
            mark_id = 0
            for i in range(n_states):
                for j in range(n_states):
                    if i != j and Q[i, j] != 0:
                        marks[(i, j)] = {
                            'id': mark_id,
                            'rate': Q[i, j],
                            'from_state': i,
                            'to_state': j,
                        }
                        mark_id += 1

        return {
            'Q': Q,
            'space': space,
            'pi': pi,
            'marks': marks,
            'n_states': n_states,
            'n_transitions': len(marks),
        }

    # =========================================================================
    # Reward Analysis Methods
    # =========================================================================

    def runRewardAnalyzer(self, reward_vector: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Run reward analysis on the CTMC.

        Computes expected rewards in steady-state and optionally transient.

        Args:
            reward_vector: Reward for each state. If None, uses queue length.

        Returns:
            Dictionary with 'steady_state_reward', 'reward_per_state', etc.
        """
        if self._result is None:
            self.runAnalyzer()

        pi = self._result.pi
        space = self._result.space

        if reward_vector is None:
            # Default: use total queue length as reward
            if space is not None:
                reward_vector = np.sum(space, axis=1)
            else:
                return {'steady_state_reward': 0.0, 'error': 'No state space available'}

        if pi is None:
            return {'steady_state_reward': 0.0, 'error': 'No steady-state distribution'}

        # Compute steady-state reward
        steady_state_reward = np.dot(pi, reward_vector)

        # Compute per-state rewards
        reward_per_state = pi * reward_vector

        return {
            'steady_state_reward': steady_state_reward,
            'reward_per_state': reward_per_state,
            'reward_vector': reward_vector,
            'pi': pi,
        }

    def getTranReward(self, t: float = 1.0,
                      reward_vector: Optional[np.ndarray] = None) -> float:
        """Get transient reward at time t.

        Computes expected reward at time t using matrix exponential.

        Args:
            t: Time point for transient analysis
            reward_vector: Reward for each state. If None, uses queue length.

        Returns:
            Expected reward at time t
        """
        if self._result is None:
            self.runAnalyzer()

        space = self._result.space

        if reward_vector is None:
            if space is not None:
                reward_vector = np.sum(space, axis=1)
            else:
                return 0.0

        # Get transient probabilities
        pi_t = self.getTranProbSys(t)

        # Compute transient reward
        return np.dot(pi_t, reward_vector)

    # Aliases for new methods
    GetGenerator = getGenerator
    GetStateSpaceAggr = getStateSpaceAggr
    GetProb = getProb
    GetCdfSysRespT = getCdfSysRespT
    GetReward = getReward
    GetAvgReward = getAvgReward
    GetTranCdfRespT = getTranCdfRespT
    GetTranProb = getTranProb
    GetTranProbAggr = getTranProbAggr
    GetTranProbSys = getTranProbSys
    GetTranProbSysAggr = getTranProbSysAggr
    GetSymbolicGenerator = getSymbolicGenerator
    GetMarkedCTMC = getMarkedCTMC
    RunRewardAnalyzer = runRewardAnalyzer
    GetTranReward = getTranReward

    # =========================================================================
    # UNIFIED METRICS METHOD
    # =========================================================================

    def getAvg(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Get all average metrics at once.

        Returns:
            Tuple of (Q, U, R, T, A, W) where:
            - Q: Queue lengths (M x K)
            - U: Utilizations (M x K)
            - R: Response times (M x K)
            - T: Throughputs (M x K)
            - A: Arrival rates (M x K)
            - W: Waiting times (M x K)
        """
        if self._result is None:
            self.runAnalyzer()

        Q = self._result.Q
        U = self._result.U
        R = self._result.R
        T = self._result.T if self._result.T.ndim > 1 else np.tile(self._result.T, (Q.shape[0], 1))
        A = T.copy()  # Arrival rate = throughput for open networks
        W = R.copy()  # Waiting time approximation

        return Q, U, R, T, A, W

    # =========================================================================
    # CHAIN-LEVEL METHODS
    # =========================================================================

    def _get_chains(self) -> List[List[int]]:
        """Get chain-to-class mapping from network structure."""
        if hasattr(self._sn, 'chains') and self._sn.chains is not None:
            chains_arr = np.asarray(self._sn.chains)
            nchains = self._sn.nchains if hasattr(self._sn, 'nchains') else 1

            # Check if chains is 1D (class->chain mapping) or 2D (chain,class membership)
            if chains_arr.ndim == 1:
                # 1D format: chains[k] = c means class k belongs to chain c
                if len(chains_arr) == 0:
                    return [[k] for k in range(self._sn.nclasses)]
                nchains = max(nchains, int(np.max(chains_arr)) + 1)
                chains = [[] for _ in range(nchains)]
                for k in range(self._sn.nclasses):
                    if k < len(chains_arr):
                        c = int(chains_arr[k])
                        if 0 <= c < nchains:
                            chains[c].append(k)
                chains = [c for c in chains if c]
                return chains if chains else [[k for k in range(self._sn.nclasses)]]
            else:
                # 2D format: chains[c, k] > 0 means class k is in chain c
                chains = []
                for c in range(nchains):
                    chain_classes = []
                    for k in range(self._sn.nclasses):
                        if c < chains_arr.shape[0] and k < chains_arr.shape[1]:
                            if chains_arr[c, k] > 0:
                                chain_classes.append(k)
                    chains.append(chain_classes)
                chains = [c for c in chains if c]
                return chains if chains else [[k for k in range(self._sn.nclasses)]]
        else:
            # Default: each class is its own chain
            return [[k] for k in range(self._sn.nclasses)]

    def getAvgQLenChain(self) -> np.ndarray:
        """Get average queue lengths aggregated by chain."""
        if self._result is None:
            self.runAnalyzer()

        Q = self._result.Q
        chains = self._get_chains()
        nstations = Q.shape[0]
        nchains = len(chains)

        QN_chain = np.zeros((nstations, nchains))
        for c, chain_classes in enumerate(chains):
            if chain_classes:
                QN_chain[:, c] = np.sum(Q[:, chain_classes], axis=1)

        return QN_chain

    def getAvgUtilChain(self) -> np.ndarray:
        """Get average utilizations aggregated by chain."""
        if self._result is None:
            self.runAnalyzer()

        U = self._result.U
        chains = self._get_chains()
        nstations = U.shape[0]
        nchains = len(chains)

        UN_chain = np.zeros((nstations, nchains))
        for c, chain_classes in enumerate(chains):
            if chain_classes:
                UN_chain[:, c] = np.sum(U[:, chain_classes], axis=1)

        return UN_chain

    def getAvgRespTChain(self) -> np.ndarray:
        """Get average response times aggregated by chain."""
        if self._result is None:
            self.runAnalyzer()

        R = self._result.R
        chains = self._get_chains()
        nstations = R.shape[0]
        nchains = len(chains)

        RN_chain = np.zeros((nstations, nchains))
        for c, chain_classes in enumerate(chains):
            if chain_classes:
                RN_chain[:, c] = np.mean(R[:, chain_classes], axis=1)

        return RN_chain

    def getAvgResidTChain(self) -> np.ndarray:
        """Get average residence times aggregated by chain."""
        return self.getAvgRespTChain()

    def getAvgTputChain(self) -> np.ndarray:
        """Get average throughputs aggregated by chain."""
        if self._result is None:
            self.runAnalyzer()

        T = self._result.T
        if T.ndim == 1:
            T = T.reshape(1, -1)

        chains = self._get_chains()
        nstations = self._result.Q.shape[0]
        nchains = len(chains)

        TN_chain = np.zeros((nstations, nchains))
        for c, chain_classes in enumerate(chains):
            if chain_classes:
                if T.shape[0] == nstations:
                    TN_chain[:, c] = np.sum(T[:, chain_classes], axis=1)
                else:
                    TN_chain[:, c] = np.sum(T[0, chain_classes])

        return TN_chain

    def getAvgArvRChain(self) -> np.ndarray:
        """Get average arrival rates aggregated by chain."""
        return self.getAvgTputChain()

    def getAvgChain(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Get all average metrics aggregated by chain.

        Returns:
            Tuple of (QN, UN, RN, WN, AN, TN) aggregated by chain
        """
        QN = self.getAvgQLenChain()
        UN = self.getAvgUtilChain()
        RN = self.getAvgRespTChain()
        WN = self.getAvgResidTChain()
        AN = self.getAvgArvRChain()
        TN = self.getAvgTputChain()
        return QN, UN, RN, WN, AN, TN

    def getAvgChainTable(self) -> pd.DataFrame:
        """Get average metrics by chain as DataFrame."""
        QN, UN, RN, WN, AN, TN = self.getAvgChain()

        nstations, nchains = QN.shape
        rows = []

        station_names = self.station_names if hasattr(self, 'station_names') else [f'Station{i}' for i in range(nstations)]

        for i in range(nstations):
            for c in range(nchains):
                rows.append({
                    'Station': station_names[i] if i < len(station_names) else f'Station{i}',
                    'Chain': f'Chain{c + 1}',  # 1-based to match MATLAB
                    'QLen': QN[i, c],
                    'Util': UN[i, c],
                    'RespT': RN[i, c],
                    'ResidT': WN[i, c],
                    'ArvR': AN[i, c],
                    'Tput': TN[i, c],
                })

        return pd.DataFrame(rows)

    # =========================================================================
    # NODE-LEVEL METHODS
    # =========================================================================

    def getAvgNode(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Get average metrics per node.

        Unlike getAvg() which returns station-level metrics, this method
        returns node-level metrics including non-station nodes (e.g., Cache).
        For Cache nodes, hit/miss class throughputs are computed using
        actual hit/miss probabilities.

        Returns:
            Tuple of (QNn, UNn, RNn, WNn, ANn, TNn) - node-level metrics
        """
        from ..api.sn.getters import sn_get_node_arvr_from_tput, sn_get_node_tput_from_tput
        from ..api.sn import NodeType

        if self._result is None:
            self.runAnalyzer()

        sn = self._sn
        I = sn.nnodes
        M = sn.nstations
        R = sn.nclasses

        # Get station-level metrics
        QN = self._result.Q
        UN = self._result.U
        RN = self._result.R
        TN = self._result.T
        AN = self._result.A if hasattr(self._result, 'A') else np.zeros_like(TN)

        # Compute actual hit/miss probabilities for Cache nodes
        # For LRU/FIFO with uniform access: hit prob = m/n (capacity/items)
        if sn.nodeparam is not None:
            for ind in range(I):
                if sn.nodetype is not None and ind < len(sn.nodetype):
                    if sn.nodetype[ind] == NodeType.CACHE and ind in sn.nodeparam:
                        cache_param = sn.nodeparam[ind]
                        nitems = getattr(cache_param, 'nitems', 0)
                        cap = getattr(cache_param, 'cap', 0)

                        # Get nitems and cap from model if not in param
                        if nitems == 0 or cap == 0:
                            # Try to get from model nodes
                            if hasattr(self, 'model') and hasattr(self.model, '_nodes'):
                                for node in self.model._nodes:
                                    if hasattr(node, '_nitems') and hasattr(node, '_capacity'):
                                        nitems = node._nitems if node._nitems else 0
                                        cap = node._capacity if node._capacity else 0
                                        break

                        if nitems > 0 and cap > 0:
                            # Get cache node for gamma matrix
                            cache_node = None
                            if hasattr(self, 'model') and hasattr(self.model, '_nodes'):
                                cache_node = self.model._nodes[ind]

                            # Get replacement strategy (default to LRU)
                            from ..lang.base import ReplacementStrategy
                            replacement = ReplacementStrategy.LRU
                            if hasattr(cache_param, 'replacestrat') and cache_param.replacestrat is not None:
                                rs = cache_param.replacestrat
                                if isinstance(rs, int):
                                    replacement = rs
                                elif hasattr(rs, 'value'):
                                    replacement = rs.value
                                else:
                                    replacement = int(rs)

                            # Compute hit probability using cache analysis
                            hit_prob = min(cap / nitems, 1.0)  # Default uniform
                            miss_prob = 1.0 - hit_prob

                            if cache_node is not None and hasattr(cache_node, 'get_gamma_matrix'):
                                try:
                                    # Get gamma matrix and cache capacity levels
                                    gamma = cache_node.get_gamma_matrix(R)
                                    m_levels = cache_node._item_level_cap if hasattr(cache_node, '_item_level_cap') else np.array([cap])

                                    if replacement == ReplacementStrategy.RR:
                                        # Use RRM mean-field for Random Replacement
                                        from ..api.cache import cache_rrm_meanfield
                                        # Convert gamma to arrival rates (lambda)
                                        lambd = np.sum(gamma, axis=1)
                                        lambd = lambd / np.sum(lambd) if np.sum(lambd) > 0 else lambd
                                        # Run RRM analysis
                                        prob, missrate, missratio = cache_rrm_meanfield(lambd, m_levels)
                                        # Miss probability is first column
                                        pi0 = prob[:, 0]
                                        # Compute overall hit rate weighted by access probabilities
                                        access_probs = lambd
                                        hit_prob = np.sum(access_probs * (1 - pi0))
                                        miss_prob = 1.0 - hit_prob
                                    else:
                                        # Use cache_mva for LRU/FIFO/SFIFO
                                        from ..api.cache import cache_mva
                                        # Run cache analysis (LRU-based)
                                        pi, pi0, pij, x, u, E = cache_mva(gamma, m_levels)
                                        # Compute overall hit rate weighted by access probabilities
                                        access_probs = np.sum(gamma, axis=1)
                                        access_probs = access_probs / np.sum(access_probs) if np.sum(access_probs) > 0 else access_probs
                                        hit_prob = np.sum(access_probs * (1 - pi0))
                                        miss_prob = 1.0 - hit_prob
                                except Exception:
                                    pass  # Fall back to uniform if cache analysis fails

                            # Store in nodeparam for use by sn_get_node_tput_from_tput
                            hitclass = getattr(cache_param, 'hitclass', np.array([]))
                            nclasses = len(hitclass) if hasattr(hitclass, '__len__') else R
                            cache_param.actualhitprob = np.zeros(nclasses)
                            cache_param.actualmissprob = np.zeros(nclasses)

                            for k in range(nclasses):
                                h = hitclass[k] if k < len(hitclass) else -1
                                missclass = getattr(cache_param, 'missclass', np.array([]))
                                m = missclass[k] if k < len(missclass) else -1
                                if h >= 0 and m >= 0:
                                    cache_param.actualhitprob[k] = hit_prob
                                    cache_param.actualmissprob[k] = miss_prob

                            # Set result on Cache node in model
                            if cache_node is not None:
                                if hasattr(cache_node, 'set_result_hit_prob'):
                                    cache_node.set_result_hit_prob(cache_param.actualhitprob)
                                if hasattr(cache_node, 'set_result_miss_prob'):
                                    cache_node.set_result_miss_prob(cache_param.actualmissprob)

        # Create TH (throughput handle) - indicates which station-classes have valid throughput
        TH = np.zeros_like(TN)
        TH[TN > 0] = 1.0

        # Compute node arrival rates and throughputs using helper functions
        ANn = sn_get_node_arvr_from_tput(sn, TN, TH, AN)
        TNn = sn_get_node_tput_from_tput(sn, TN, TH, ANn)

        # Initialize other node-level metrics
        QNn = np.zeros((I, R))
        UNn = np.zeros((I, R))
        RNn = np.zeros((I, R))
        WNn = np.zeros((I, R))

        # Copy station metrics to station nodes
        for ist in range(M):
            ind = sn.stationToNode[ist]
            if ind >= 0 and ind < I:
                QNn[ind, :] = QN[ist, :]
                UNn[ind, :] = UN[ist, :]
                RNn[ind, :] = RN[ist, :]
                WNn[ind, :] = RN[ist, :]  # ResidT = RespT for now

        return QNn, UNn, RNn, WNn, ANn, TNn

    def getAvgNodeTable(self) -> pd.DataFrame:
        """
        Get average metrics by node as DataFrame.

        Returns node-based results (one row per node per class) including
        non-station nodes like Cache. For Cache nodes, hit/miss class
        throughputs are computed using actual hit/miss probabilities.

        Returns:
            pandas.DataFrame with columns: Node, JobClass, QLen, Util, RespT, ResidT, ArvR, Tput
        """
        QNn, UNn, RNn, WNn, ANn, TNn = self.getAvgNode()

        sn = self._sn
        nodenames = list(sn.nodenames) if hasattr(sn, 'nodenames') and sn.nodenames else []

        rows = []
        for node_idx in range(sn.nnodes):
            node_name = nodenames[node_idx] if node_idx < len(nodenames) else f'Node{node_idx}'

            for r in range(sn.nclasses):
                class_name = self.class_names[r] if r < len(self.class_names) else f'Class{r}'

                # Filter out all-zero rows
                if QNn[node_idx, r] == 0 and UNn[node_idx, r] == 0 and \
                   RNn[node_idx, r] == 0 and ANn[node_idx, r] == 0 and TNn[node_idx, r] == 0:
                    continue

                rows.append({
                    'Node': node_name,
                    'JobClass': class_name,
                    'QLen': QNn[node_idx, r],
                    'Util': UNn[node_idx, r],
                    'RespT': RNn[node_idx, r],
                    'ResidT': WNn[node_idx, r],
                    'ArvR': ANn[node_idx, r],
                    'Tput': TNn[node_idx, r],
                })

        df = pd.DataFrame(rows)

        if not self._table_silent:
            print(df.to_string(index=False))

        return df

    def getAvgNodeChain(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Get average metrics by node and chain."""
        return self.getAvgChain()

    def getAvgNodeChainTable(self) -> pd.DataFrame:
        """Get average metrics by node and chain as DataFrame."""
        return self.getAvgChainTable()

    def getAvgNodeQLenChain(self) -> np.ndarray:
        """Get average queue lengths by node aggregated by chain."""
        return self.getAvgQLenChain()

    def getAvgNodeUtilChain(self) -> np.ndarray:
        """Get average utilizations by node aggregated by chain."""
        return self.getAvgUtilChain()

    def getAvgNodeRespTChain(self) -> np.ndarray:
        """Get average response times by node aggregated by chain."""
        return self.getAvgRespTChain()

    def getAvgNodeResidTChain(self) -> np.ndarray:
        """Get average residence times by node aggregated by chain."""
        return self.getAvgResidTChain()

    def getAvgNodeTputChain(self) -> np.ndarray:
        """Get average throughputs by node aggregated by chain."""
        return self.getAvgTputChain()

    def getAvgNodeArvRChain(self) -> np.ndarray:
        """Get average arrival rates by node aggregated by chain."""
        return self.getAvgArvRChain()

    def getTranAvg(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Get transient average metrics.

        Returns:
            Tuple of (Q_t, U_t, T_t) transient queue lengths, utilizations, and throughputs
        """
        # CTMC supports transient analysis via matrix exponential
        if self._result is None:
            self.runAnalyzer()

        Q = self._result.Q
        U = self._result.U
        T = self._result.T if hasattr(self._result, 'T') else np.zeros_like(Q)

        # For steady-state analysis, return steady-state values as "transient" at equilibrium
        return Q, U, T

    def getAvgSys(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get system-level average metrics.

        Returns:
            Tuple of (R, T) where R is system response time and T is system throughput
        """
        R = self.getAvgSysRespT()
        T = self.getAvgSysTput()
        return R, T

    def getAvgSysTable(self) -> pd.DataFrame:
        """Get system-level metrics as DataFrame."""
        R, T = self.getAvgSys()
        nclasses = len(R) if hasattr(R, '__len__') else 1
        class_names = self.class_names if hasattr(self, 'class_names') else [f'Class{k}' for k in range(nclasses)]

        rows = []
        for k in range(nclasses):
            rows.append({
                'Class': class_names[k] if k < len(class_names) else f'Class{k}',
                'SysRespT': R[k] if hasattr(R, '__getitem__') else R,
                'SysTput': T[k] if k < len(T) else 0,
            })

        return pd.DataFrame(rows)

    # =========================================================================
    # SAMPLING METHODS STUBS (CTMC is analytical, redirect to SSA)
    # =========================================================================

    def sampleAggr(self, node: int, numSamples: int = 1000) -> np.ndarray:
        """Sample aggregated states at node (not supported for CTMC).

        Raises:
            NotImplementedError: CTMC is an analytical solver
        """
        raise NotImplementedError("sampleAggr() not supported for analytical CTMC solver. Use SSA instead.")

    def sampleSys(self, numSamples: int = 1000) -> np.ndarray:
        """Sample system states (not supported for CTMC).

        Raises:
            NotImplementedError: CTMC is an analytical solver
        """
        raise NotImplementedError("sampleSys() not supported for analytical CTMC solver. Use SSA instead.")

    def sampleSysAggr(self, numSamples: int = 1000) -> SampleResult:
        """Sample aggregated system states using CTMC simulation.

        Uses the infinitesimal generator to simulate state transitions and
        records events (arrivals, departures) at each node.

        Args:
            numSamples: Number of events to generate

        Returns:
            SampleResult containing timestamps, states, and event information
        """
        from ..api.mc.ctmc import ctmc_simulate

        # Run analyzer if needed
        if self._result is None:
            self.runAnalyzer()

        # Get generator and state space
        infGen, eventFilt = self.getGenerator()
        stateSpace, _ = self.getStateSpace()

        if infGen is None or len(infGen) == 0:
            return SampleResult(isaggregate=True, numSamples=0)

        # Get network structure
        sn = self._sn

        # Build initial state index
        nstates = infGen.shape[0]
        initial_state = 0

        # Set random seed if provided
        seed = self.options.seed if hasattr(self.options, 'seed') else None

        # Simulate CTMC
        max_time = 1e10  # Large time to allow collecting enough events
        sim_result = ctmc_simulate(infGen, initial_state, max_time, numSamples, seed)

        states = sim_result['states']
        times = sim_result['times']

        # Build events by analyzing total population changes
        # For phase-type distributions, compute total jobs at each stateful node
        # by summing over all phase columns for that node
        events = []
        nstateful = sn.nstateful if hasattr(sn, 'nstateful') else 1

        # Compute total population for each state (sum of all 1s in state vector)
        # For M/E/1: state represents phase-level occupancy
        # Total queue population = sum of all non-zero entries
        state_populations = np.sum(stateSpace, axis=1)

        # Find which node corresponds to the queue (not source/sink)
        # In open networks: node 0 = source (stateful), node 1 = queue (stateful)
        queue_node_idx = 1  # Default: queue is second stateful node

        # Get node types to identify queue
        if hasattr(sn, 'nodetype') and sn.nodetype is not None:
            from ..api.sn.network_struct import NodeType
            statefulToNode = sn.statefulToNode if hasattr(sn, 'statefulToNode') else list(range(nstateful))
            for isf in range(nstateful):
                node_idx = int(statefulToNode[isf]) if isf < len(statefulToNode) else isf
                if node_idx < len(sn.nodetype):
                    if sn.nodetype[node_idx] == NodeType.QUEUE:
                        queue_node_idx = isf
                        break

        # Analyze each transition to detect arrivals/departures
        for i in range(1, len(states)):
            prev_state_idx = states[i - 1]
            curr_state_idx = states[i]

            if prev_state_idx >= len(stateSpace) or curr_state_idx >= len(stateSpace):
                continue

            event_time = times[i]

            # Compute total population change
            prev_pop = state_populations[prev_state_idx]
            curr_pop = state_populations[curr_state_idx]
            pop_change = curr_pop - prev_pop

            if pop_change > 0:
                # Arrival to the system (at queue)
                event_info = EventInfo(
                    node=queue_node_idx,
                    jobclass=0,
                    t=event_time,
                    event="ARV"
                )
                events.append(event_info)
            elif pop_change < 0:
                # Departure from the system (from queue)
                event_info = EventInfo(
                    node=queue_node_idx,
                    jobclass=0,
                    t=event_time,
                    event="DEP"
                )
                events.append(event_info)
            # pop_change == 0: internal phase transition, skip

        # Build result
        result = SampleResult(
            handle=f"ctmc_sample_{id(self)}",
            t=times.reshape(-1, 1) if len(times) > 0 else np.zeros((0, 1)),
            state=stateSpace[states] if len(states) > 0 else np.zeros((0, stateSpace.shape[1] if stateSpace.ndim > 1 else 1)),
            event=events,
            isaggregate=True,
            nodeIndex=None,
            numSamples=len(events)
        )

        return result

    # =========================================================================
    # Introspection Methods
    # =========================================================================

    def listValidMethods(self) -> List[str]:
        """List valid solution methods."""
        return ['default', 'basic']

    @staticmethod
    def getFeatureSet() -> set:
        """Get supported features."""
        return {
            'Sink', 'Source', 'Queue', 'Delay',
            'Exp', 'Erlang', 'HyperExp',
            'OpenClass', 'ClosedClass',
            'FCFS', 'PS', 'LCFS',
            'MultiServer', 'StateSpace', 'ExactAnalysis',
        }

    @staticmethod
    def supports(model) -> bool:
        """Check if model is supported."""
        try:
            if hasattr(model, 'nstations'):
                nstations = model.nstations
            elif hasattr(model, 'getNumberOfStations'):
                nstations = model.getNumberOfStations()
            else:
                return False

            if hasattr(model, 'nclasses'):
                nclasses = model.nclasses
            elif hasattr(model, 'getNumberOfClasses'):
                nclasses = model.getNumberOfClasses()
            else:
                return False

            return nstations > 0 and nclasses > 0
        except Exception:
            return False

    @staticmethod
    def defaultOptions() -> OptionsDict:
        """Get default solver options."""
        return OptionsDict({
            'method': 'default',
            'tol': 1e-6,
            'cutoff': 10,
            'verbose': False,
        })

    @staticmethod
    def printInfGen(infGen: np.ndarray, stateSpace: np.ndarray) -> None:
        """Print the infinitesimal generator matrix in MATLAB-compatible format.

        Output format matches MATLAB's CTMC.printInfGen():
        [from_state]->[to_state]: rate

        Args:
            infGen: Infinitesimal generator matrix
            stateSpace: State space matrix
        """
        if infGen is None or len(infGen) == 0:
            print("Empty generator matrix")
            return

        def format_state(state):
            """Format state vector as [a b c] with integers where possible."""
            parts = []
            for s in state:
                val = float(s)
                if val == int(val):
                    parts.append(str(int(val)))
                else:
                    parts.append(f"{val:.4f}")
            return "[" + " ".join(parts) + "]"

        nstates = infGen.shape[0]
        for i in range(nstates):
            state_i = stateSpace[i] if stateSpace is not None and i < len(stateSpace) else [i]
            for j in range(nstates):
                if i != j and infGen[i, j] > 0:
                    state_j = stateSpace[j] if stateSpace is not None and j < len(stateSpace) else [j]
                    from_str = format_state(state_i)
                    to_str = format_state(state_j)
                    print(f"{from_str}->{to_str}: {infGen[i, j]:.6f}")

    print_inf_gen = printInfGen

    # =========================================================================
    # Sampling Methods (Not Supported - Analytical Solver)
    # =========================================================================

    def sample(self, node: int, numSamples: int) -> np.ndarray:
        """Sampling not supported by CTMC (analytical solver)."""
        raise NotImplementedError(
            "Sampling not supported by SolverCTMC. "
            "Use SolverSSA or SolverDES for simulation-based analysis."
        )

    # =========================================================================
    # Aliases
    # =========================================================================

    GetAvg = getAvg
    GetAvgTable = getAvgTable
    GetAvgQLen = getAvgQLen
    GetAvgUtil = getAvgUtil
    GetAvgRespT = getAvgRespT
    GetAvgResidT = getAvgResidT
    GetAvgWaitT = getAvgWaitT
    GetAvgTput = getAvgTput
    GetAvgArvR = getAvgArvR
    GetAvgSysRespT = getAvgSysRespT
    GetAvgSysTput = getAvgSysTput
    GetStateSpace = getStateSpace
    GetSteadyState = getSteadyState
    GetInfGen = getInfGen
    GetCdfRespT = getCdfRespT
    GetPerctRespT = getPerctRespT
    ListValidMethods = listValidMethods
    GetFeatureSet = getFeatureSet
    Supports = supports
    DefaultOptions = defaultOptions
    default_options = defaultOptions

    # Chain-level aliases
    GetAvgChain = getAvgChain
    GetAvgChainTable = getAvgChainTable
    GetAvgQLenChain = getAvgQLenChain
    GetAvgUtilChain = getAvgUtilChain
    GetAvgRespTChain = getAvgRespTChain
    GetAvgResidTChain = getAvgResidTChain
    GetAvgTputChain = getAvgTputChain
    GetAvgArvRChain = getAvgArvRChain

    # Node-level aliases
    GetAvgNode = getAvgNode
    GetAvgNodeTable = getAvgNodeTable
    GetAvgNodeChain = getAvgNodeChain
    GetAvgNodeChainTable = getAvgNodeChainTable
    GetAvgNodeQLenChain = getAvgNodeQLenChain
    GetAvgNodeUtilChain = getAvgNodeUtilChain
    GetAvgNodeRespTChain = getAvgNodeRespTChain
    GetAvgNodeResidTChain = getAvgNodeResidTChain
    GetAvgNodeTputChain = getAvgNodeTputChain
    GetAvgNodeArvRChain = getAvgNodeArvRChain
    GetAvgSys = getAvgSys
    GetAvgSysTable = getAvgSysTable
    GetTranAvg = getTranAvg

    # Sampling stubs
    SampleAggr = sampleAggr
    SampleSys = sampleSys
    SampleSysAggr = sampleSysAggr

    # Short aliases (MATLAB compatibility)
    aT = getAvgTable
    aNT = getAvgNodeTable
    aCT = getAvgChainTable
    aNCT = getAvgNodeChainTable
    aST = getAvgSysTable
    avgT = getAvgTable
    nodeAvgT = getAvgNodeTable
    chainAvgT = getAvgChainTable
    nodeChainAvgT = getAvgNodeChainTable
    sysAvgT = getAvgSysTable
    avg_table = getAvgTable
    get_avg_table = getAvgTable
    avg_qlen = getAvgQLen
    avg_util = getAvgUtil
    avg_respt = getAvgRespT
    avg_resid_t = getAvgResidT
    avg_wait_t = getAvgWaitT
    avg_tput = getAvgTput
    avg_arv_r = getAvgArvR
    avg_sys_resp_t = getAvgSysRespT
    avg_sys_tput = getAvgSysTput
    avg_sys_table = getAvgSysTable
    avg_node = getAvgNode
    avg_node_table = getAvgNodeTable
    avg_node_chain = getAvgNodeChain
    avg_node_chain_table = getAvgNodeChainTable
    avg_chain = getAvgChain
    avg_chain_table = getAvgChainTable
    state_space = getStateSpace
    state_space_aggr = getStateSpaceAggr
    run_analyzer = runAnalyzer
    generator = getGenerator
    steady_state = getSteadyState
    sample_sys_aggr = sampleSysAggr
    sample_sys = sampleSys
    sample_aggr = sampleAggr
    inf_gen = getInfGen
    prob_aggr = getProbAggr
    prob_sys_aggr = getProbSysAggr
    prob = getProb
    tran_prob = getTranProb
    tran_prob_aggr = getTranProbAggr
    tran_prob_sys = getTranProbSys
    tran_prob_sys_aggr = getTranProbSysAggr


__all__ = ['SolverCTMC', 'SolverCTMCOptions']
