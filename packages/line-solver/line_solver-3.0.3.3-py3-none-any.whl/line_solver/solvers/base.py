"""
Base class for native LINE solvers.

Provides common functionality shared across all native solver implementations.
The class hierarchy mirrors the JAR implementation:
- Solver: Base class for all solvers
- NetworkSolver(Solver): For single-network solvers (MVA, NC, CTMC, SSA, etc.)
- EnsembleSolver(Solver): For multi-model solvers (LN, Posterior, ENV)
"""


class Solver:
    """Base class for all LINE solvers.

    Provides common attributes and default behaviors for all solvers.

    Attributes:
        _table_silent (bool): If True, suppress automatic table printing in
            getAvgTable() and similar methods. Defaults to True so that
            tables are only printed when explicitly requested by the user.
    """

    # Suppress automatic table printing by default
    _table_silent = False 


class NetworkSolver(Solver):
    """Base class for single-network LINE solvers.

    Used by: SolverMVA, SolverNC, SolverCTMC, SolverSSA, SolverMAM, SolverJMT,
             SolverDES, SolverQNS, SolverAuto, SolverFLD
    """
    pass


class EnsembleSolver(Solver):
    """Base class for ensemble/multi-model LINE solvers.

    Used by: SolverLN, SolverPosterior, SolverENV
    """
    pass
