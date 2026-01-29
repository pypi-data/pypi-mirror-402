"""
Alternative linearizer for mixed open/closed queueing networks.

IMPORTANT: This module is NOT exported from the package. The main implementation
used by solvers is in linearizerms.py. This file provides an alternative
implementation using Seidmann transformation for multiserver networks.

Note:
    For multiserver networks, this implementation uses Seidmann transformation to
    convert multiserver to equivalent single-server problems. The main implementation
    in linearizerms.py instead uses pfqn_linearizerms (Conway/De Souza-Muntz algorithm)
    for multiserver, matching MATLAB's pfqn_linearizermx design more closely.

References:
    MATLAB: matlab/src/api/pfqn/pfqn_linearizermx.m
"""

import numpy as np
from typing import Tuple, List, Optional

from .linearizer import pfqn_linearizer, pfqn_gflinearizer, pfqn_egflinearizer
from .linearizerms import pfqn_linearizerms


def pfqn_linearizermx(
    lambda_arr: np.ndarray,
    L: np.ndarray,
    N: np.ndarray,
    Z: np.ndarray,
    nservers: np.ndarray,
    sched_type: List[str],
    tol: float = 1e-8,
    maxiter: int = 1000,
    method: str = 'egflin'
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
    """
    Linearizer for mixed open/closed queueing networks.

    This function extends the linearizer algorithm to handle networks with
    both open classes (with external arrivals) and closed classes (with
    fixed populations).

    Args:
        lambda_arr: Arrival rate vector (R,). For closed classes, should be 0 or inf.
        L: Service demand matrix (M x R)
        N: Population vector (R,). Inf for open classes, finite for closed.
        Z: Think time vector (R,) or matrix
        nservers: Number of servers per station (M,)
        sched_type: Scheduling strategy per station (list of strings)
        tol: Convergence tolerance
        maxiter: Maximum iterations
        method: Linearizer variant ('lin', 'gflin', 'egflin')

    Returns:
        QN: Mean queue lengths (M x R)
        UN: Utilization (M x R)
        WN: Waiting times (M x R)
        TN: Throughputs (M x R)
        CN: Cycle times (1 x R)
        XN: System throughput (R,)
        totiter: Total iterations

    References:
        MATLAB: matlab/src/api/pfqn/pfqn_linearizermx.m
    """
    L = np.atleast_2d(L).astype(float)
    N = np.atleast_1d(N).astype(float)
    lambda_arr = np.atleast_1d(lambda_arr).astype(float)

    M, R = L.shape

    if Z is None:
        Z = np.zeros(R)
    else:
        Z = np.atleast_1d(Z).astype(float)
        if Z.ndim > 1:
            Z = np.sum(Z, axis=0)

    # Replace NaN with 0
    lambda_arr = np.nan_to_num(lambda_arr, nan=0.0)
    L = np.nan_to_num(L, nan=0.0)
    Z = np.nan_to_num(Z, nan=0.0)

    # Identify open and closed classes
    open_classes = np.where(np.isinf(N))[0]
    closed_classes = np.array([r for r in range(R) if r not in open_classes])

    # Initialize outputs
    XN = np.zeros(R)
    UN = np.zeros((M, R))
    WN = np.zeros((M, R))
    QN = np.zeros((M, R))
    CN = np.zeros(R)
    TN = np.zeros((M, R))

    # Process open classes: U = lambda * L / c (per-server utilization), X = lambda
    nservers_arr = np.atleast_1d(nservers).astype(float) if nservers is not None else np.ones(M)
    if len(nservers_arr) < M:
        nservers_arr = np.concatenate([nservers_arr, np.ones(M - len(nservers_arr))])

    for r in open_classes:
        for ist in range(M):
            c = max(1, nservers_arr[ist])
            UN[ist, r] = lambda_arr[r] * L[ist, r] / c  # Per-server utilization
        XN[r] = lambda_arr[r]

    # Total utilization from open classes (per-server)
    UNt = np.sum(UN, axis=1)

    # Check for overload
    if np.any(UNt >= 1.0):
        # System is unstable - return infinity for open class metrics
        for r in open_classes:
            QN[:, r] = np.inf
            WN[:, r] = np.inf
        # For closed classes, we can still try to compute but results may be inaccurate
        if len(closed_classes) == 0:
            totiter = 0
            TN = UN.copy()  # For open classes, throughput = arrival rate * visits
            for r in open_classes:
                TN[:, r] = XN[r] * np.ones(M)  # Simplified
            return QN, UN, WN, TN, CN, XN, totiter

    # Adjust demands for closed classes to account for open class utilization
    if len(closed_classes) > 0:
        # Dc = L_closed / (1 - U_open_total)
        Dc = np.zeros((M, len(closed_classes)))
        for idx, r in enumerate(closed_classes):
            for ist in range(M):
                if UNt[ist] < 1.0:
                    Dc[ist, idx] = L[ist, r] / (1.0 - UNt[ist])
                else:
                    Dc[ist, idx] = L[ist, r] * 1e6  # Large value for near-saturation

        N_closed = N[closed_classes]
        Z_closed = Z[closed_classes]

        # Call appropriate linearizer for closed classes
        # Filter out infinite server counts (Delay nodes) when determining max_servers
        finite_servers = nservers_arr[np.isfinite(nservers_arr)]
        max_servers = int(np.max(finite_servers)) if len(finite_servers) > 0 else 1

        # Apply Seidmann transformation for multiserver networks
        # This converts multiserver to equivalent single-server problem
        # Reference: MATLAB solver_amva.m lines 91-97
        Dc_seidmann = Dc.copy()
        Z_seidmann = Z_closed.copy()

        if max_servers > 1:
            # Apply Seidmann transformation:
            # 1. Divide demands by number of servers: L_s = L / c
            # 2. Add extra think time: Z_s = Z + L * (c-1) / c
            for ist in range(M):
                c = nservers_arr[ist]
                if np.isfinite(c) and c > 1:
                    # Add (c-1)/c of original demand to think time
                    Z_seidmann += Dc[ist, :] * (c - 1) / c
                    # Divide demand by number of servers
                    Dc_seidmann[ist, :] = Dc[ist, :] / c

        # After Seidmann transformation, always use single-server linearizer
        if method == 'gflin':
            result = pfqn_gflinearizer(Dc_seidmann, N_closed, Z_seidmann, sched_type, tol, maxiter)
        elif method == 'egflin':
            result = pfqn_egflinearizer(Dc_seidmann, N_closed, Z_seidmann, sched_type, tol, maxiter)
        else:  # 'lin' or default
            result = pfqn_linearizer(Dc_seidmann, N_closed, Z_seidmann, sched_type, tol, maxiter)
        # Single-server linearizers return 7 values: (Q, U, W, T, C, X, iter)
        QNc, UNc, WNc, TNc, CNc, XNc, totiter = result

        # Un-apply Seidmann transformation to queue lengths if multiserver was used
        if max_servers > 1:
            for ist in range(M):
                c = nservers_arr[ist]
                if np.isfinite(c) and c > 1:
                    # Add back the (c-1)/c component that was moved to think time
                    # Q_original = Q_seidmann + X * L * (c-1) / c
                    for idx in range(len(closed_classes)):
                        QNc[ist, idx] += XNc[idx] * Dc[ist, idx] * (c - 1) / c

        # Map closed class results back
        for idx, r in enumerate(closed_classes):
            XN[r] = XNc[idx] if idx < len(XNc) else 0.0
            CN[r] = CNc[idx] if idx < len(CNc) else 0.0
            for ist in range(M):
                if idx < QNc.shape[1]:
                    QN[ist, r] = QNc[ist, idx]
                    WN[ist, r] = WNc[ist, idx]
                    # Recompute utilization with original demands (per-server for multiserver queues)
                    c = max(1, nservers_arr[ist])
                    UN[ist, r] = XN[r] * L[ist, r] / c
    else:
        totiter = 0

    # Compute open class response times using closed class queue lengths
    for ist in range(M):
        for r in open_classes:
            if UNt[ist] < 1.0:
                if len(closed_classes) > 0 and QN.shape[1] > 0:
                    # Response time includes effect of closed class jobs
                    closed_qlen = np.sum(QN[ist, closed_classes])
                    WN[ist, r] = L[ist, r] * (1 + closed_qlen) / (1 - UNt[ist])
                else:
                    WN[ist, r] = L[ist, r] / (1 - UNt[ist])
                QN[ist, r] = WN[ist, r] * XN[r]
            else:
                WN[ist, r] = np.inf
                QN[ist, r] = np.inf

    # Cycle times for open classes
    for r in open_classes:
        CN[r] = np.sum(WN[:, r])

    # Compute throughputs
    for r in range(R):
        TN[:, r] = XN[r] * np.ones(M)

    return QN, UN, WN, TN, CN, XN, totiter
