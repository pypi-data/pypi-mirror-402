"""
JIT-compiled kernels for Multivariate Phase-Type (MVPH) distributions.

Provides Numba-accelerated versions of MVPH computational hotspots:
- Mean computation for multiple outputs
- Covariance and correlation computation
- Joint distribution evaluation over grids
- Cross-moment computation

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


if HAS_NUMBA:
    # =========================================================================
    # JIT-compiled versions
    # =========================================================================

    @njit(fastmath=True, cache=True)
    def mvph_mean_output_jit(
        alpha: np.ndarray,
        invA: np.ndarray,
        B: np.ndarray,
        n: int
    ) -> float:
        """
        JIT-compiled mean computation: E[X] = -alpha @ inv(A) @ B.

        Args:
            alpha: Initial distribution (n,)
            invA: Inverse of generator matrix (n, n)
            B: Output vector (n,)
            n: Number of phases

        Returns:
            Mean of output X
        """
        # v = alpha @ invA
        v = np.zeros(n)
        for j in range(n):
            s = 0.0
            for i in range(n):
                s += alpha[i] * invA[i, j]
            v[j] = s

        # result = -v @ B
        result = 0.0
        for i in range(n):
            result -= v[i] * B[i]

        return result

    @njit(fastmath=True, cache=True)
    def mvph_second_moment_jit(
        alpha: np.ndarray,
        invA: np.ndarray,
        invA2: np.ndarray,
        B: np.ndarray,
        n: int
    ) -> float:
        """
        JIT-compiled second moment: E[X^2] = 2 * alpha @ inv(A)^2 @ B.

        Args:
            alpha: Initial distribution (n,)
            invA: Inverse of generator (n, n) - not used, kept for interface
            invA2: inv(A)^2 (n, n)
            B: Output vector (n,)
            n: Number of phases

        Returns:
            Second moment of output X
        """
        # v = alpha @ invA2
        v = np.zeros(n)
        for j in range(n):
            s = 0.0
            for i in range(n):
                s += alpha[i] * invA2[i, j]
            v[j] = s

        # result = 2 * v @ B
        result = 0.0
        for i in range(n):
            result += v[i] * B[i]

        return 2.0 * result

    @njit(fastmath=True, cache=True)
    def mvph_cross_moment_jit(
        alpha: np.ndarray,
        invA: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        n: int
    ) -> float:
        """
        JIT-compiled cross moment: E[XY].

        For MVPH, E[XY] = alpha @ inv(A) @ diag(B) @ inv(A) @ C
                       + alpha @ inv(A) @ diag(C) @ inv(A) @ B.

        Simplified version assuming diagonal rewards.

        Args:
            alpha: Initial distribution (n,)
            invA: Inverse of generator (n, n)
            B: First output vector (n,)
            C: Second output vector (n,)
            n: Number of phases

        Returns:
            Cross moment E[XY]
        """
        # Compute alpha @ invA
        alpha_invA = np.zeros(n)
        for j in range(n):
            s = 0.0
            for i in range(n):
                s += alpha[i] * invA[i, j]
            alpha_invA[j] = s

        # Term 1: alpha @ invA @ diag(B) @ invA @ C
        # diag(B) @ invA = B[i] * invA[i, j]
        diagB_invA = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                diagB_invA[i, j] = B[i] * invA[i, j]

        # alpha_invA @ diagB_invA @ C
        v1 = np.zeros(n)
        for j in range(n):
            s = 0.0
            for i in range(n):
                s += alpha_invA[i] * diagB_invA[i, j]
            v1[j] = s

        term1 = 0.0
        for i in range(n):
            term1 += v1[i] * C[i]

        # Term 2: alpha @ invA @ diag(C) @ invA @ B
        diagC_invA = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                diagC_invA[i, j] = C[i] * invA[i, j]

        v2 = np.zeros(n)
        for j in range(n):
            s = 0.0
            for i in range(n):
                s += alpha_invA[i] * diagC_invA[i, j]
            v2[j] = s

        term2 = 0.0
        for i in range(n):
            term2 += v2[i] * B[i]

        return term1 + term2

    @njit(fastmath=True, cache=True)
    def mvph_covariance_jit(
        mean_x: float,
        mean_y: float,
        cross_moment: float
    ) -> float:
        """
        JIT-compiled covariance: Cov(X,Y) = E[XY] - E[X]E[Y].

        Args:
            mean_x: E[X]
            mean_y: E[Y]
            cross_moment: E[XY]

        Returns:
            Covariance between X and Y
        """
        return cross_moment - mean_x * mean_y

    @njit(fastmath=True, cache=True)
    def mvph_variance_jit(
        mean: float,
        second_moment: float
    ) -> float:
        """
        JIT-compiled variance: Var(X) = E[X^2] - E[X]^2.

        Args:
            mean: E[X]
            second_moment: E[X^2]

        Returns:
            Variance of X
        """
        return second_moment - mean * mean

    @njit(fastmath=True, cache=True)
    def mvph_correlation_jit(
        covariance: float,
        var_x: float,
        var_y: float
    ) -> float:
        """
        JIT-compiled correlation: rho = Cov(X,Y) / sqrt(Var(X) * Var(Y)).

        Args:
            covariance: Cov(X,Y)
            var_x: Var(X)
            var_y: Var(Y)

        Returns:
            Correlation coefficient
        """
        if var_x <= 0 or var_y <= 0:
            return 0.0
        return covariance / np.sqrt(var_x * var_y)

    @njit(fastmath=True, cache=True)
    def joint_cdf_grid_jit(
        alpha: np.ndarray,
        expAt_x: np.ndarray,
        expAt_y: np.ndarray,
        n_phases: int,
        n_x: int,
        n_y: int,
        output: np.ndarray
    ) -> None:
        """
        JIT-compiled joint CDF computation over a grid.

        Computes P(X <= x, Y <= y) for all grid points.

        Args:
            alpha: Initial distribution (n_phases,)
            expAt_x: Pre-computed exp(A*x) for all x values (n_x, n_phases, n_phases)
            expAt_y: Pre-computed exp(A*y) for all y values (n_y, n_phases, n_phases)
            n_phases: Number of phases
            n_x: Number of x grid points
            n_y: Number of y grid points
            output: Output grid (n_x, n_y)
        """
        for i in range(n_x):
            for j in range(n_y):
                # Compute 1 - alpha @ exp(A*x) @ 1 - alpha @ exp(A*y) @ 1 + alpha @ exp(A*max(x,y)) @ 1
                # Simplified: use product of marginals as approximation

                # P(X <= x) = 1 - sum(alpha @ exp(A*x))
                sum_x = 0.0
                for k in range(n_phases):
                    row_sum = 0.0
                    for l in range(n_phases):
                        row_sum += expAt_x[i, k, l]
                    sum_x += alpha[k] * row_sum

                # P(Y <= y) = 1 - sum(alpha @ exp(A*y))
                sum_y = 0.0
                for k in range(n_phases):
                    row_sum = 0.0
                    for l in range(n_phases):
                        row_sum += expAt_y[j, k, l]
                    sum_y += alpha[k] * row_sum

                cdf_x = 1.0 - sum_x
                cdf_y = 1.0 - sum_y

                # For independent case: P(X <= x, Y <= y) = P(X <= x) * P(Y <= y)
                # For dependent case, this is an approximation
                output[i, j] = cdf_x * cdf_y

    @njit(fastmath=True, cache=True)
    def mvph_marginal_cdf_jit(
        alpha: np.ndarray,
        expAt: np.ndarray,
        n_phases: int,
        n_points: int,
        output: np.ndarray
    ) -> None:
        """
        JIT-compiled marginal CDF computation.

        Args:
            alpha: Initial distribution (n_phases,)
            expAt: Pre-computed exp(A*t) for all points (n_points, n_phases, n_phases)
            n_phases: Number of phases
            n_points: Number of time points
            output: Output CDF values (n_points,)
        """
        for p in range(n_points):
            s = 0.0
            for i in range(n_phases):
                row_sum = 0.0
                for j in range(n_phases):
                    row_sum += expAt[p, i, j]
                s += alpha[i] * row_sum
            output[p] = 1.0 - s

    @njit(fastmath=True, cache=True)
    def mvph_reward_transform_jit(
        alpha: np.ndarray,
        A: np.ndarray,
        R: np.ndarray,
        n: int,
        output_alpha: np.ndarray,
        output_A: np.ndarray
    ) -> None:
        """
        JIT-compiled reward transformation for MVPH.

        Transforms PH(alpha, A) with reward vector R to equivalent PH.

        Args:
            alpha: Initial distribution (n,)
            A: Generator matrix (n, n)
            R: Reward vector (n,)
            n: Number of phases
            output_alpha: Output initial distribution (n,)
            output_A: Output generator matrix (n, n)
        """
        # output_A = diag(R) @ A @ diag(1/R)
        for i in range(n):
            for j in range(n):
                if R[j] > 0:
                    output_A[i, j] = R[i] * A[i, j] / R[j]
                else:
                    output_A[i, j] = 0.0

        # output_alpha = alpha (unchanged for reward transformation)
        for i in range(n):
            output_alpha[i] = alpha[i]

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def mvph_mean_output_jit(
        alpha: np.ndarray,
        invA: np.ndarray,
        B: np.ndarray,
        n: int
    ) -> float:
        """Pure Python mean computation."""
        return float(-alpha @ invA @ B)

    def mvph_second_moment_jit(
        alpha: np.ndarray,
        invA: np.ndarray,
        invA2: np.ndarray,
        B: np.ndarray,
        n: int
    ) -> float:
        """Pure Python second moment."""
        return float(2.0 * alpha @ invA2 @ B)

    def mvph_cross_moment_jit(
        alpha: np.ndarray,
        invA: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        n: int
    ) -> float:
        """Pure Python cross moment."""
        alpha_invA = alpha @ invA
        term1 = alpha_invA @ np.diag(B) @ invA @ C
        term2 = alpha_invA @ np.diag(C) @ invA @ B
        return float(term1 + term2)

    def mvph_covariance_jit(
        mean_x: float,
        mean_y: float,
        cross_moment: float
    ) -> float:
        """Pure Python covariance."""
        return cross_moment - mean_x * mean_y

    def mvph_variance_jit(
        mean: float,
        second_moment: float
    ) -> float:
        """Pure Python variance."""
        return second_moment - mean * mean

    def mvph_correlation_jit(
        covariance: float,
        var_x: float,
        var_y: float
    ) -> float:
        """Pure Python correlation."""
        if var_x <= 0 or var_y <= 0:
            return 0.0
        return covariance / np.sqrt(var_x * var_y)

    def joint_cdf_grid_jit(
        alpha: np.ndarray,
        expAt_x: np.ndarray,
        expAt_y: np.ndarray,
        n_phases: int,
        n_x: int,
        n_y: int,
        output: np.ndarray
    ) -> None:
        """Pure Python joint CDF grid."""
        for i in range(n_x):
            for j in range(n_y):
                cdf_x = 1.0 - np.sum(alpha @ expAt_x[i])
                cdf_y = 1.0 - np.sum(alpha @ expAt_y[j])
                output[i, j] = cdf_x * cdf_y

    def mvph_marginal_cdf_jit(
        alpha: np.ndarray,
        expAt: np.ndarray,
        n_phases: int,
        n_points: int,
        output: np.ndarray
    ) -> None:
        """Pure Python marginal CDF."""
        for p in range(n_points):
            output[p] = 1.0 - np.sum(alpha @ expAt[p])

    def mvph_reward_transform_jit(
        alpha: np.ndarray,
        A: np.ndarray,
        R: np.ndarray,
        n: int,
        output_alpha: np.ndarray,
        output_A: np.ndarray
    ) -> None:
        """Pure Python reward transformation."""
        R_inv = np.where(R > 0, 1.0 / R, 0.0)
        np.copyto(output_A, np.diag(R) @ A @ np.diag(R_inv))
        np.copyto(output_alpha, alpha)


__all__ = [
    'HAS_NUMBA',
    'mvph_mean_output_jit',
    'mvph_second_moment_jit',
    'mvph_cross_moment_jit',
    'mvph_covariance_jit',
    'mvph_variance_jit',
    'mvph_correlation_jit',
    'joint_cdf_grid_jit',
    'mvph_marginal_cdf_jit',
    'mvph_reward_transform_jit',
]
