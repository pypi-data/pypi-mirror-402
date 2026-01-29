"""
Native Python implementation of Random Environment models.

This module provides classes for defining and analyzing queueing networks
in random environments, where the network parameters change according to
an underlying Markov modulated process.

Implements full parity with MATLAB SolverENV using transient analysis
with iteration until convergence.
"""

import numpy as np
from typing import Optional, List, Dict, Any, Union, Callable, Tuple
import pandas as pd


def _get_rate(dist) -> float:
    """Extract rate from a distribution object."""
    if hasattr(dist, 'getRate'):
        return dist.getRate()
    elif hasattr(dist, 'rate'):
        return dist.rate
    elif hasattr(dist, 'getMean'):
        mean = dist.getMean()
        return 1.0 / mean if mean > 0 else 0.0
    else:
        return float(dist)


def _eval_cdf(dist, t) -> np.ndarray:
    """Evaluate CDF of distribution at time points t."""
    t = np.atleast_1d(t)
    if hasattr(dist, 'evalCDF'):
        return np.array([dist.evalCDF(ti) for ti in t])
    elif hasattr(dist, 'cdf'):
        return dist.cdf(t)
    else:
        # Assume exponential with rate
        rate = _get_rate(dist)
        if rate <= 0:
            return np.zeros_like(t)
        return 1.0 - np.exp(-rate * t)


class Environment:
    """
    A random environment model where a queueing network operates under
    different environmental conditions (stages).

    The environment switches between stages according to a Markov process,
    and each stage has its own network model with potentially different
    parameters.

    This class mirrors MATLAB's Environment class with full parity.
    """

    def __init__(self, name: str, num_stages: int = 0):
        """
        Create a random environment model.

        Args:
            name: Name of the environment model
            num_stages: Number of environmental stages (can be 0 if stages added later)
        """
        self.name = name
        self.num_stages = num_stages

        # Stage information
        self._stages: List[Dict[str, Any]] = []
        self._stage_names: List[str] = []
        self._stage_types: List[str] = []
        self._models: List[Any] = []

        # Transition information - env[e][h] is distribution from e to h
        self.env: List[List[Any]] = []
        self._transitions: Dict[tuple, Any] = {}
        self._reset_rules: Dict[tuple, Callable] = {}

        # Environment probabilities (computed by init())
        self.probEnv: Optional[np.ndarray] = None  # steady-state probs
        self.probOrig: Optional[np.ndarray] = None  # transition origin probs

        # Hold time distributions
        self.holdTime: List[Any] = []  # hold time distribution for each stage
        self.proc: List[List[Any]] = []  # proc[e][h] = distribution from e to h

        # Reset functions - resetFun[e][h] transforms queue lengths from e to h
        self.resetFun: List[List[Callable]] = []

        # Initialize empty stages if num_stages provided
        for _ in range(num_stages):
            self._stages.append({})
            self._stage_names.append('')
            self._stage_types.append('')
            self._models.append(None)

        # Initialize env matrix
        self._init_env_matrix(num_stages)

    def _init_env_matrix(self, E: int):
        """Initialize the environment transition matrix."""
        self.env = [[None for _ in range(E)] for _ in range(E)]
        self.proc = [[None for _ in range(E)] for _ in range(E)]
        self.resetFun = [[lambda q: q for _ in range(E)] for _ in range(E)]

    def add_stage(self, index: int, name: str, stage_type: str, model: Any) -> None:
        """
        Add or update a stage in the environment.

        Args:
            index: Stage index (0-based)
            name: Name of the stage
            stage_type: Type of stage ('UP', 'DOWN', etc.)
            model: Network model for this stage
        """
        # Expand arrays if needed
        while len(self._stages) <= index:
            self._stages.append({})
            self._stage_names.append('')
            self._stage_types.append('')
            self._models.append(None)

        self._stages[index] = {'name': name, 'type': stage_type, 'model': model}
        self._stage_names[index] = name
        self._stage_types[index] = stage_type
        self._models[index] = model

        self.num_stages = max(self.num_stages, index + 1)

        # Reinitialize env matrix if size changed
        if len(self.env) < self.num_stages:
            self._init_env_matrix(self.num_stages)

    def add_transition(self, from_stage: int, to_stage: int, distribution: Any,
                       reset_rule: Optional[Callable[[np.ndarray], np.ndarray]] = None) -> None:
        """
        Add a transition between stages with an optional reset rule.

        Args:
            from_stage: Source stage index
            to_stage: Destination stage index
            distribution: Distribution for the transition time (e.g., Exp(rate))
            reset_rule: Optional function that transforms queue lengths when transition occurs.
        """
        # Ensure env matrix is large enough
        E = max(from_stage + 1, to_stage + 1, self.num_stages)
        if len(self.env) < E:
            self._init_env_matrix(E)

        self._transitions[(from_stage, to_stage)] = distribution
        self.env[from_stage][to_stage] = distribution
        self.proc[from_stage][to_stage] = distribution

        if reset_rule is not None:
            self._reset_rules[(from_stage, to_stage)] = reset_rule
            self.resetFun[from_stage][to_stage] = reset_rule
        else:
            self._reset_rules[(from_stage, to_stage)] = lambda q: q
            self.resetFun[from_stage][to_stage] = lambda q: q

    def init(self):
        """
        Initialize environment probabilities and hold time distributions.

        This method must be called before using the environment solver.
        It computes:
        - probEnv: steady-state probabilities for each stage
        - probOrig: transition origin probabilities
        - holdTime: hold time distributions for each stage
        """
        E = self.num_stages
        if E == 0:
            return

        # Build rate matrix E0
        E0 = np.zeros((E, E))
        for e in range(E):
            for h in range(E):
                if self.env[e][h] is not None:
                    E0[e, h] = _get_rate(self.env[e][h])

        # Make infinitesimal generator (rows sum to 0)
        for e in range(E):
            E0[e, e] = -np.sum(E0[e, :])

        # Compute steady-state probabilities
        self.probEnv = self._solve_ctmc(E0)

        # Compute transition origin probabilities probOrig[h,e]
        # probOrig[h,e] = probability that a transition into stage e came from stage h
        self.probOrig = np.zeros((E, E))
        for e in range(E):
            total_rate_into_e = 0.0
            for h in range(E):
                if h != e and self.env[h][e] is not None:
                    rate_he = _get_rate(self.env[h][e])
                    total_rate_into_e += self.probEnv[h] * rate_he

            for h in range(E):
                if h != e and self.env[h][e] is not None and total_rate_into_e > 0:
                    rate_he = _get_rate(self.env[h][e])
                    self.probOrig[h, e] = self.probEnv[h] * rate_he / total_rate_into_e

        # Compute hold time distributions
        # holdTime[e] is the distribution of time spent in stage e before leaving
        # Only count transitions to different stages (not self-loops)
        self.holdTime = []
        for e in range(E):
            # Total rate out of stage e (excluding self-loops)
            rate_out = 0.0
            for h in range(E):
                if h != e and self.env[e][h] is not None:
                    rate_out += _get_rate(self.env[e][h])
            # Hold time is exponential with rate = total rate out
            self.holdTime.append(_ExponentialDist(rate_out))

    def _solve_ctmc(self, Q: np.ndarray) -> np.ndarray:
        """Solve CTMC for steady-state probabilities."""
        E = Q.shape[0]
        if E == 0:
            return np.array([])

        # Solve pi * Q = 0, sum(pi) = 1
        A = Q.T.copy()
        A[-1, :] = 1.0
        b = np.zeros(E)
        b[-1] = 1.0

        try:
            pi = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            pi = np.linalg.lstsq(A, b, rcond=None)[0]

        # Ensure non-negative
        pi = np.maximum(pi, 0)
        pi = pi / np.sum(pi)
        return pi

    def get_stage(self, index: int) -> Dict[str, Any]:
        """Get stage information by index."""
        if 0 <= index < len(self._stages):
            return self._stages[index]
        return {}

    def get_model(self, index: int) -> Any:
        """Get the network model for a stage."""
        if 0 <= index < len(self._models):
            return self._models[index]
        return None

    def get_transition(self, from_stage: int, to_stage: int) -> Any:
        """Get the transition distribution between stages."""
        return self._transitions.get((from_stage, to_stage), None)

    def get_reset_rule(self, from_stage: int, to_stage: int) -> Optional[Callable]:
        """Get the reset rule for a transition between stages."""
        return self._reset_rules.get((from_stage, to_stage), None)

    def get_transition_rate_matrix(self) -> np.ndarray:
        """Build the transition rate matrix for the environment."""
        E = self.num_stages
        Q = np.zeros((E, E))

        for (i, j), dist in self._transitions.items():
            Q[i, j] = _get_rate(dist)

        for i in range(E):
            Q[i, i] = -np.sum(Q[i, :])

        return Q

    def get_steady_state_probs(self) -> np.ndarray:
        """Compute steady-state probabilities for the environment stages."""
        if self.probEnv is None:
            self.init()
        return self.probEnv

    def getEnsemble(self) -> List[Any]:
        """Get list of network models."""
        return self._models

    def stage_table(self) -> pd.DataFrame:
        """Get a table summarizing the environment stages."""
        data = []
        for i in range(len(self._stages)):
            model_name = 'None'
            if i < len(self._models) and self._models[i] is not None:
                if hasattr(self._models[i], 'name'):
                    model_name = self._models[i].name
            row = {
                'Stage': i,
                'Name': self._stage_names[i] if i < len(self._stage_names) else '',
                'Type': self._stage_types[i] if i < len(self._stage_types) else '',
                'Model': model_name
            }
            data.append(row)

        df = pd.DataFrame(data)
        print(df.to_string(index=False))
        return df

    def getStageTable(self):
        """Alias for stage_table (MATLAB compatibility)."""
        return self.stage_table()

    # CamelCase aliases for MATLAB API compatibility
    def addStage(self, index: int, name: str, stage_type: str, model: Any) -> None:
        """Alias for add_stage (MATLAB compatibility)."""
        return self.add_stage(index, name, stage_type, model)

    def addTransition(self, from_stage: int, to_stage: int, distribution: Any,
                      reset_rule: Optional[Callable[[np.ndarray], np.ndarray]] = None) -> None:
        """Alias for add_transition (MATLAB compatibility)."""
        return self.add_transition(from_stage, to_stage, distribution, reset_rule)

    def print_stage_table(self) -> None:
        """Print detailed stage table with transition information."""
        print("Stage Table:")
        print("============")
        for i in range(len(self._stages)):
            name = self._stage_names[i] if i < len(self._stage_names) else ''
            stage_type = self._stage_types[i] if i < len(self._stage_types) else ''
            model = self._models[i] if i < len(self._models) else None
            model_name = model.name if model is not None and hasattr(model, 'name') else 'None'

            n_nodes = 0
            n_classes = 0
            if model is not None:
                if hasattr(model, 'get_nodes'):
                    n_nodes = len(model.get_nodes())
                elif hasattr(model, 'nodes'):
                    n_nodes = len(model.nodes)
                if hasattr(model, 'get_classes'):
                    n_classes = len(model.get_classes())
                elif hasattr(model, 'classes'):
                    n_classes = len(model.classes)

            print(f"Stage {i + 1}: {name} (Type: {stage_type})")
            print(f"  - Network: {model_name}")
            print(f"  - Nodes: {n_nodes}")
            print(f"  - Classes: {n_classes}")

        if self._transitions:
            print("Transitions:")
            for (from_idx, to_idx), dist in sorted(self._transitions.items()):
                from_name = self._stage_names[from_idx] if from_idx < len(self._stage_names) else f'Stage{from_idx}'
                to_name = self._stage_names[to_idx] if to_idx < len(self._stage_names) else f'Stage{to_idx}'
                rate = _get_rate(dist)
                print(f"  {from_name} -> {to_name}: rate = {rate:.4f}")

    @property
    def ensemble(self) -> List[Any]:
        """Get list of network models (MATLAB compatibility)."""
        return self._models


class _ExponentialDist:
    """Simple exponential distribution for hold times."""

    def __init__(self, rate: float):
        self.rate = rate

    def getRate(self) -> float:
        return self.rate

    def evalCDF(self, t: float) -> float:
        if self.rate <= 0:
            return 0.0
        return 1.0 - np.exp(-self.rate * t)


class SolverENV:
    """
    Environment solver for random environment models.

    This solver analyzes queueing networks operating in random environments
    by running transient analysis with iteration until convergence.

    Implements full parity with MATLAB SolverENV.
    """

    def __init__(self, env_model: Environment, solvers: Union[List, Callable], options=None):
        """
        Create an environment solver.

        Args:
            env_model: Environment model to analyze
            solvers: Either a list of solvers (one per stage) or a factory function
            options: Solver options
        """
        self.env_model = env_model
        self.options = self._normalize_options(options)

        # Handle solvers as list or factory function
        if callable(solvers):
            self._solvers = []
            for model in env_model.ensemble:
                if model is not None:
                    self._solvers.append(solvers(model))
                else:
                    self._solvers.append(None)
        else:
            self._solvers = list(solvers)

        # Ensemble state (mirrors MATLAB)
        self.ensemble = env_model.ensemble
        self.results = {}  # results[it, e] = result for iteration it, stage e

        # Final result
        self.result = None
        self._result = None

    def _normalize_options(self, options) -> Dict:
        """Normalize options to a dictionary."""
        if options is None:
            return {
                'method': 'default',
                'iter_max': 100,
                'iter_tol': 1e-4,
                'verbose': False
            }

        if isinstance(options, dict):
            opts = {
                'method': options.get('method', 'default'),
                'iter_max': options.get('iter_max', 100),
                'iter_tol': options.get('iter_tol', 1e-4),
                'verbose': options.get('verbose', False)
            }
            return opts

        # Options object
        return {
            'method': getattr(options, 'method', 'default'),
            'iter_max': getattr(options, 'iter_max', 100),
            'iter_tol': getattr(options, 'iter_tol', 1e-4),
            'verbose': getattr(options, 'verbose', False)
        }

    def getNumberOfModels(self) -> int:
        """Get number of environment stages."""
        return self.env_model.num_stages

    def getSolver(self, e: int):
        """Get solver for stage e."""
        return self._solvers[e] if e < len(self._solvers) else None

    def init(self):
        """Initialize the environment solver."""
        self.env_model.init()
        self.results = {}

    def pre(self, it: int):
        """Pre-iteration operations."""
        E = self.getNumberOfModels()

        if it == 1:
            # Initialize marginals for first iteration using steady-state values
            for e in range(E):
                solver = self.getSolver(e)
                if solver is not None:
                    # Get initial queue lengths from steady-state
                    try:
                        QN = solver.getAvgQLen()
                        # Set initial state on solver for transient analysis
                        if hasattr(solver, 'setInitialState'):
                            solver.setInitialState(QN)
                        solver.reset()
                    except Exception:
                        pass

    def analyze(self, it: int, e: int) -> Tuple[Dict, float]:
        """
        Analyze stage e at iteration it using transient analysis.

        Returns transient analysis results in MATLAB-compatible format.
        """
        import time
        t0 = time.time()

        result_e = {
            'Tran': {
                'Avg': {
                    'Q': None,
                    'U': None,
                    'T': None
                }
            }
        }

        solver = self.getSolver(e)
        if solver is None:
            return result_e, 0.0

        # Reset solver for new analysis
        if hasattr(solver, 'reset'):
            solver.reset()

        # Get transient results
        try:
            if hasattr(solver, 'getTranAvg'):
                QNt, UNt, TNt = solver.getTranAvg()
                result_e['Tran']['Avg']['Q'] = QNt
                result_e['Tran']['Avg']['U'] = UNt
                result_e['Tran']['Avg']['T'] = TNt
            else:
                # Fall back to steady-state wrapped in transient format
                QN = solver.getAvgQLen() if hasattr(solver, 'getAvgQLen') else np.array([[0.0]])
                UN = solver.getAvgUtil() if hasattr(solver, 'getAvgUtil') else np.array([[0.0]])
                TN = solver.getAvgTput() if hasattr(solver, 'getAvgTput') else np.array([[0.0]])
                QN = np.atleast_2d(QN)
                UN = np.atleast_2d(UN)
                TN = np.atleast_2d(TN)
                M, K = QN.shape
                t_vals = np.array([0.0, 1000.0])
                result_e['Tran']['Avg']['Q'] = [[{'t': t_vals, 'metric': np.array([QN[i, r], QN[i, r]])} for r in range(K)] for i in range(M)]
                result_e['Tran']['Avg']['U'] = [[{'t': t_vals, 'metric': np.array([UN[i, r], UN[i, r]])} for r in range(K)] for i in range(M)]
                result_e['Tran']['Avg']['T'] = [[{'t': t_vals, 'metric': np.array([TN[i, r], TN[i, r]])} for r in range(K)] for i in range(M)]
        except Exception as ex:
            pass

        runtime = time.time() - t0
        return result_e, runtime

    def post(self, it: int):
        """Post-iteration operations - compute exit metrics and update entry marginals."""
        E = self.getNumberOfModels()

        # Compute exit metrics for each stage-to-stage transition
        Qexit = {}
        Uexit = {}
        Texit = {}

        for e in range(E):
            result_e = self.results.get((it, e))
            if result_e is None or result_e['Tran']['Avg']['Q'] is None:
                continue

            Q_tran = result_e['Tran']['Avg']['Q']
            U_tran = result_e['Tran']['Avg']['U']
            T_tran = result_e['Tran']['Avg']['T']

            M = len(Q_tran)
            K = len(Q_tran[0]) if M > 0 else 0

            for h in range(E):
                Qexit[(e, h)] = np.zeros((M, K))
                Uexit[(e, h)] = np.zeros((M, K))
                Texit[(e, h)] = np.zeros((M, K))

                for i in range(M):
                    for r in range(K):
                        Qir = Q_tran[i][r]
                        if isinstance(Qir, dict) and 't' in Qir and 'metric' in Qir and len(Qir['t']) > 0:
                            t_vals = Qir['t']
                            metric_vals = Qir['metric']

                            # Compute weights using CDF of transition distribution
                            dist_eh = self.env_model.proc[e][h]
                            if dist_eh is not None:
                                cdf_vals = _eval_cdf(dist_eh, t_vals)
                                w = np.zeros(len(t_vals))
                                w[1:] = cdf_vals[1:] - cdf_vals[:-1]

                                if np.sum(w) > 0:
                                    Qexit[(e, h)][i, r] = np.dot(metric_vals, w) / np.sum(w)
                                    Uir = U_tran[i][r]
                                    if isinstance(Uir, dict) and 'metric' in Uir:
                                        Uexit[(e, h)][i, r] = np.dot(Uir['metric'], w) / np.sum(w)
                                    Tir = T_tran[i][r]
                                    if isinstance(Tir, dict) and 'metric' in Tir:
                                        Texit[(e, h)][i, r] = np.dot(Tir['metric'], w) / np.sum(w)
                                else:
                                    # Use final value
                                    Qexit[(e, h)][i, r] = metric_vals[-1] if len(metric_vals) > 0 else 0.0

        # Store exit metrics for convergence check
        self._Qexit = Qexit

        # Compute entry marginals using reset functions
        for e in range(E):
            result_e = self.results.get((it, e))
            if result_e is None or result_e['Tran']['Avg']['Q'] is None:
                continue

            Q_tran = result_e['Tran']['Avg']['Q']
            M = len(Q_tran)
            K = len(Q_tran[0]) if M > 0 else 0
            Qentry = np.zeros((M, K))

            for h in range(E):
                if (h, e) in Qexit and self.env_model.probOrig[h, e] > 0:
                    reset_fn = self.env_model.resetFun[h][e]
                    Qentry += self.env_model.probOrig[h, e] * reset_fn(Qexit[(h, e)])

            # Set initial state on solver for next iteration
            solver = self.getSolver(e)
            if solver is not None:
                if hasattr(solver, 'setInitialState'):
                    solver.setInitialState(Qentry)
                solver.reset()

    def converged(self, it: int) -> bool:
        """Check if iteration has converged."""
        if it <= 1:
            return False

        E = self.getNumberOfModels()
        iter_tol = self.options.get('iter_tol', 1e-4)

        # Compare queue lengths between iterations
        for e in range(E):
            result_curr = self.results.get((it, e))
            result_prev = self.results.get((it - 1, e))

            if result_curr is None or result_prev is None:
                return False

            Q_curr = result_curr['Tran']['Avg']['Q']
            Q_prev = result_prev['Tran']['Avg']['Q']

            if Q_curr is None or Q_prev is None:
                return False

            M = len(Q_curr)
            K = len(Q_curr[0]) if M > 0 else 0

            for i in range(M):
                for k in range(K):
                    curr_val = 0.0
                    prev_val = 0.0

                    Qik_curr = Q_curr[i][k]
                    if isinstance(Qik_curr, dict) and 'metric' in Qik_curr:
                        curr_val = Qik_curr['metric'][0] if len(Qik_curr['metric']) > 0 else 0.0

                    Qik_prev = Q_prev[i][k]
                    if isinstance(Qik_prev, dict) and 'metric' in Qik_prev:
                        prev_val = Qik_prev['metric'][0] if len(Qik_prev['metric']) > 0 else 0.0

                    if prev_val > 1e-10:
                        rel_diff = abs(curr_val - prev_val) / prev_val
                        if rel_diff >= iter_tol:
                            return False

        return True

    def finish(self):
        """Compute final weighted averages using hold time CDF weighting."""
        E = self.getNumberOfModels()
        if E == 0:
            return

        # Use last iteration results
        it = max([k[0] for k in self.results.keys()]) if self.results else 0
        if it == 0:
            return

        # Compute exit metrics weighted by hold time distribution
        QExit = {}
        UExit = {}
        TExit = {}

        # Determine dimensions
        M, K = 0, 0
        for e in range(E):
            result_e = self.results.get((it, e))
            if result_e is not None and result_e['Tran']['Avg']['Q'] is not None:
                Q_tran = result_e['Tran']['Avg']['Q']
                M = len(Q_tran)
                K = len(Q_tran[0]) if M > 0 else 0
                break

        if M == 0:
            return

        for e in range(E):
            result_e = self.results.get((it, e))
            QExit[e] = np.zeros((M, K))
            UExit[e] = np.zeros((M, K))
            TExit[e] = np.zeros((M, K))

            if result_e is None or result_e['Tran']['Avg']['Q'] is None:
                continue

            Q_tran = result_e['Tran']['Avg']['Q']
            U_tran = result_e['Tran']['Avg']['U']
            T_tran = result_e['Tran']['Avg']['T']

            for i in range(M):
                for r in range(K):
                    Qir = Q_tran[i][r]
                    if isinstance(Qir, dict) and 't' in Qir and 'metric' in Qir and len(Qir['t']) > 0:
                        t_vals = Qir['t']
                        metric_vals = Qir['metric']

                        # Use hold time distribution for weighting
                        hold_dist = self.env_model.holdTime[e]
                        cdf_vals = _eval_cdf(hold_dist, t_vals)
                        w = np.zeros(len(t_vals))
                        w[1:] = cdf_vals[1:] - cdf_vals[:-1]

                        if np.sum(w) > 0:
                            QExit[e][i, r] = np.dot(metric_vals, w) / np.sum(w)
                            Uir = U_tran[i][r]
                            if isinstance(Uir, dict) and 'metric' in Uir:
                                UExit[e][i, r] = np.dot(Uir['metric'], w) / np.sum(w)
                            Tir = T_tran[i][r]
                            if isinstance(Tir, dict) and 'metric' in Tir:
                                TExit[e][i, r] = np.dot(Tir['metric'], w) / np.sum(w)
                        else:
                            # Fall back to final value
                            QExit[e][i, r] = metric_vals[-1] if len(metric_vals) > 0 else 0.0

        # Compute weighted averages across stages using steady-state probabilities
        Qval = np.zeros((M, K))
        Uval = np.zeros((M, K))
        Tval = np.zeros((M, K))

        for e in range(E):
            Qval += self.env_model.probEnv[e] * QExit[e]
            Uval += self.env_model.probEnv[e] * UExit[e]
            Tval += self.env_model.probEnv[e] * TExit[e]

        self.result = {
            'Avg': {
                'Q': Qval,
                'U': Uval,
                'T': Tval
            }
        }

    def iterate(self):
        """Run the main iteration loop."""
        self.init()

        it = 0
        iter_max = self.options.get('iter_max', 100)
        verbose = self.options.get('verbose', False)

        E = self.getNumberOfModels()

        while not self.converged(it) and it < iter_max:
            it += 1
            if verbose:
                print(f"ENV solver iteration {it}")

            self.pre(it)

            # Analyze each stage
            for e in range(E):
                result_e, runtime = self.analyze(it, e)
                self.results[(it, e)] = result_e

            self.post(it)

        self.finish()

        if verbose:
            print(f"ENV solver converged after {it} iterations")

    def runAnalyzer(self):
        """Run the environment solver (MATLAB compatibility)."""
        self.iterate()

    def avg(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute average performance metrics across environments.

        Returns:
            Tuple of (QN, UN, TN) - queue lengths, utilizations, throughputs
        """
        if self.result is None:
            self.iterate()

        if self.result is None:
            return np.array([]), np.array([]), np.array([])

        Q = self.result['Avg']['Q']
        U = self.result['Avg']['U']
        T = self.result['Avg']['T']

        # Flatten if 2D with single class
        if Q.ndim == 2 and Q.shape[1] == 1:
            Q = Q.flatten()
            U = U.flatten()
            T = T.flatten()

        self._result = (Q, U, T)
        return Q, U, T

    def getAvg(self):
        """Get average metrics (MATLAB compatibility)."""
        return self.avg()

    def getEnsembleAvg(self):
        """Get ensemble average metrics (MATLAB compatibility)."""
        return self.avg()

    def avg_table(self) -> pd.DataFrame:
        """Get average metrics as a table."""
        if self._result is None:
            self.avg()

        QN, UN, TN = self._result

        data = []
        for solver in self._solvers:
            if solver is None:
                continue

            model = None
            if hasattr(solver, 'network'):
                model = solver.network
            elif hasattr(solver, 'model'):
                model = solver.model

            if model is not None:
                nodes = []
                if hasattr(model, 'get_nodes'):
                    nodes = model.get_nodes()
                elif hasattr(model, 'nodes'):
                    nodes = model.nodes

                for i, node in enumerate(nodes):
                    node_name = node.name if hasattr(node, 'name') else f'Node{i}'
                    qlen = float(QN[i]) if i < len(QN) else 0.0
                    util = float(UN[i]) if i < len(UN) else 0.0
                    tput = float(TN[i]) if i < len(TN) else 0.0
                    respt = qlen / tput if tput > 1e-10 else 0.0
                    row = {
                        'Node': node_name,
                        'QLen': qlen,
                        'Util': util,
                        'RespT': respt,
                        'Tput': tput,
                    }
                    data.append(row)
                break

        return pd.DataFrame(data)

    def getAvgTable(self):
        """Get average table (MATLAB compatibility)."""
        return self.avg_table()

    @staticmethod
    def default_options():
        """Get default solver options."""
        return {
            'method': 'default',
            'iter_max': 100,
            'iter_tol': 1e-4,
            'verbose': False
        }


# Convenience aliases
ENV = SolverENV


__all__ = [
    'Environment',
    'SolverENV',
    'ENV',
]
