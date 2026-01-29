"""
JIT-compiled kernels for Trace Analysis.

Provides Numba-accelerated versions of trace analysis computational hotspots:
- Autocovariance computation
- Autocorrelation function
- Index of dispersion for intervals
- Joint moment computation
- Trace binning

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
    def autocov_jit(X: np.ndarray, max_lag: int) -> np.ndarray:
        """
        JIT-compiled autocovariance computation.

        Args:
            X: Centered trace data (mean subtracted)
            max_lag: Maximum lag to compute

        Returns:
            Autocovariance values for lags 0 to max_lag-1
        """
        M = len(X)
        acv = np.zeros(max_lag)

        for p in range(max_lag):
            sum_val = 0.0
            count = M - p
            for i in range(count):
                sum_val += X[i] * X[i + p]
            acv[p] = sum_val / count

        return acv

    @njit(fastmath=True, cache=True)
    def acf_jit(trace: np.ndarray, lags: np.ndarray, mean: float) -> np.ndarray:
        """
        JIT-compiled autocorrelation function.

        Args:
            trace: Trace data
            lags: Array of lag values to compute
            mean: Mean of the trace

        Returns:
            Autocorrelation values at each lag
        """
        n = len(trace)
        n_lags = len(lags)
        rho = np.zeros(n_lags)

        # Compute variance (lag 0 autocovariance)
        var = 0.0
        for i in range(n):
            diff = trace[i] - mean
            var += diff * diff
        var /= n

        if var <= 0:
            return rho

        # Compute autocorrelation at each lag
        for k in range(n_lags):
            lag = lags[k]
            if lag <= 0 or lag >= n - 1:
                continue

            cov = 0.0
            count = n - lag
            for i in range(count):
                cov += (trace[i] - mean) * (trace[i + lag] - mean)
            cov /= count

            rho[k] = cov / var

        return rho

    @njit(fastmath=True, cache=True)
    def idi_jit(
        trace: np.ndarray,
        k: int,
        n: int
    ) -> float:
        """
        JIT-compiled Index of Dispersion for Intervals.

        Args:
            trace: Trace data
            k: Window size
            n: Trace length

        Returns:
            IDI value
        """
        if n - k <= 0:
            return 0.0

        # Compute windowed sums
        num_windows = n - k
        Sk = np.zeros(num_windows)

        for t in range(num_windows):
            sum_val = 0.0
            for i in range(k):
                sum_val += trace[t + i]
            Sk[t] = sum_val

        # Compute mean and variance
        mean_sk = 0.0
        for i in range(num_windows):
            mean_sk += Sk[i]
        mean_sk /= num_windows

        var_sk = 0.0
        for i in range(num_windows):
            diff = Sk[i] - mean_sk
            var_sk += diff * diff
        var_sk /= num_windows

        if mean_sk <= 0:
            return 0.0

        return k * var_sk / (mean_sk * mean_sk)

    @njit(fastmath=True, cache=True)
    def trace_joint_jit(
        trace: np.ndarray,
        adjusted_lag: np.ndarray,
        order: np.ndarray,
        n: int,
        n_order: int
    ) -> float:
        """
        JIT-compiled joint moment computation.

        Computes E[X^{k_1}_{i} * X^{k_2}_{i+j} * ...].

        Args:
            trace: Trace data
            adjusted_lag: Adjusted lag values (relative to base)
            order: Moment orders
            n: Trace length
            n_order: Number of order/lag pairs

        Returns:
            Joint moment value
        """
        max_lag = adjusted_lag[0]
        for i in range(1, len(adjusted_lag)):
            if adjusted_lag[i] > max_lag:
                max_lag = adjusted_lag[i]

        valid_length = n - max_lag

        if valid_length <= 0:
            return 0.0

        result = 0.0
        for i in range(valid_length):
            product = 1.0
            for j in range(n_order):
                lag_idx = j if j < len(adjusted_lag) else len(adjusted_lag) - 1
                idx = i + adjusted_lag[lag_idx]
                if idx < n:
                    product *= trace[idx] ** order[j]
            result += product

        return result / valid_length

    @njit(fastmath=True, cache=True)
    def iat2counts_jit(
        trace: np.ndarray,
        scale: float,
        n: int
    ) -> np.ndarray:
        """
        JIT-compiled counting process from inter-arrival times.

        Args:
            trace: Inter-arrival times
            scale: Time scale for counting
            n: Trace length

        Returns:
            Array of counts
        """
        # Cumulative sum with 0 at start
        CS = np.zeros(n + 1)
        for i in range(n):
            CS[i + 1] = CS[i] + trace[i]

        # Count arrivals within scale from each position
        counts = np.zeros(n - 1, dtype=np.int64)

        for i in range(n - 1):
            cur = i
            while cur + 1 < n and CS[cur + 1] - CS[i] <= scale:
                cur += 1
            counts[i] = cur - i
            if cur == n - 1:
                break

        return counts

    @njit(fastmath=True, cache=True)
    def iat2bins_jit(
        trace: np.ndarray,
        scale: float,
        n: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        JIT-compiled binning of inter-arrival times.

        Args:
            trace: Inter-arrival times
            scale: Bin timescale
            n: Trace length

        Returns:
            Tuple of (counts per bin, bin membership)
        """
        # Cumulative sum
        CS = np.zeros(n + 1)
        for i in range(n):
            CS[i + 1] = CS[i] + trace[i]

        total_time = CS[n] - CS[0]
        num_bins = int(np.ceil(total_time / scale))

        C = np.zeros(num_bins, dtype=np.int64)
        bC = np.zeros(n, dtype=np.int64)

        cur = 0
        last = 0
        bC_idx = 0

        for i in range(num_bins):
            if cur >= n - 1:
                break

            while cur < n - 1 and CS[cur + 1] <= (i + 1) * scale:
                cur += 1

            C[i] = cur - last
            for _ in range(cur - last):
                if bC_idx < n:
                    bC[bC_idx] = i
                    bC_idx += 1
            last = cur

        return C, bC[:bC_idx]

    @njit(fastmath=True, cache=True)
    def gamma_search_jit(
        rho: np.ndarray,
        lag: np.ndarray,
        RHO0: float,
        n_lags: int
    ) -> Tuple[float, float]:
        """
        JIT-compiled grid search for best gamma in autocorrelation decay.

        Args:
            rho: Autocorrelation values
            lag: Lag values
            RHO0: Initial correlation estimate
            n_lags: Number of lags

        Returns:
            Tuple of (best_gamma, min_residuals)
        """
        best_gamma = 0.99
        min_residuals = np.inf

        for gamma_int in range(990, 1000):
            g = gamma_int / 1000.0
            residuals = 0.0

            for i in range(n_lags):
                expected = RHO0 * (g ** lag[i])
                diff = rho[i] - expected
                residuals += diff * diff

            if residuals < min_residuals:
                min_residuals = residuals
                best_gamma = g

        return best_gamma, min_residuals

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def autocov_jit(X: np.ndarray, max_lag: int) -> np.ndarray:
        """Pure Python autocovariance."""
        M = len(X)
        acv = np.zeros(max_lag)
        for p in range(max_lag):
            acv[p] = np.mean(X[:M - p] * X[p:M]) if M > p else 0.0
        return acv

    def acf_jit(trace: np.ndarray, lags: np.ndarray, mean: float) -> np.ndarray:
        """Pure Python ACF."""
        n = len(trace)
        centered = trace - mean
        var = np.var(trace)
        if var <= 0:
            return np.zeros(len(lags))

        rho = np.zeros(len(lags))
        for k, lag in enumerate(lags):
            if lag > 0 and lag < n - 1:
                cov = np.mean(centered[:n - lag] * centered[lag:])
                rho[k] = cov / var
        return rho

    def idi_jit(trace: np.ndarray, k: int, n: int) -> float:
        """Pure Python IDI."""
        if n - k <= 0:
            return 0.0

        Sk = np.zeros(n - k)
        for t in range(n - k):
            Sk[t] = np.sum(trace[t:t + k])

        var = np.var(Sk)
        mean_sk = np.mean(Sk)

        if mean_sk <= 0:
            return 0.0

        return k * var / (mean_sk * mean_sk)

    def trace_joint_jit(
        trace: np.ndarray,
        adjusted_lag: np.ndarray,
        order: np.ndarray,
        n: int,
        n_order: int
    ) -> float:
        """Pure Python joint moment."""
        max_lag = np.max(adjusted_lag)
        valid_length = n - max_lag

        if valid_length <= 0:
            return 0.0

        result = 0.0
        for i in range(valid_length):
            product = 1.0
            for j in range(n_order):
                lag_idx = min(j, len(adjusted_lag) - 1)
                idx = i + adjusted_lag[lag_idx]
                if idx < n:
                    product *= trace[idx] ** order[j]
            result += product

        return result / valid_length

    def iat2counts_jit(
        trace: np.ndarray,
        scale: float,
        n: int
    ) -> np.ndarray:
        """Pure Python counting process."""
        CS = np.zeros(n + 1)
        CS[1:] = np.cumsum(trace)

        counts = []
        for i in range(n - 1):
            cur = i
            while cur + 1 < n and CS[cur + 1] - CS[i] <= scale:
                cur += 1
            counts.append(cur - i)
            if cur == n - 1:
                break

        return np.array(counts, dtype=np.int64)

    def iat2bins_jit(
        trace: np.ndarray,
        scale: float,
        n: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Pure Python binning."""
        CS = np.zeros(n + 1)
        CS[1:] = np.cumsum(trace)

        total_time = CS[n] - CS[0]
        num_bins = int(np.ceil(total_time / scale))

        C = np.zeros(num_bins, dtype=np.int64)
        bC = []

        cur = 0
        last = 0

        for i in range(num_bins):
            if cur >= n - 1:
                break

            while cur < n - 1 and CS[cur + 1] <= (i + 1) * scale:
                cur += 1

            C[i] = cur - last
            for _ in range(cur - last):
                bC.append(i)
            last = cur

        return C, np.array(bC, dtype=np.int64)

    def gamma_search_jit(
        rho: np.ndarray,
        lag: np.ndarray,
        RHO0: float,
        n_lags: int
    ) -> Tuple[float, float]:
        """Pure Python gamma search."""
        best_gamma = 0.99
        min_residuals = np.inf

        for gamma_int in range(990, 1000):
            g = gamma_int / 1000.0
            expected = RHO0 * (g ** lag[:n_lags])
            residuals = np.sum((rho[:n_lags] - expected) ** 2)

            if residuals < min_residuals:
                min_residuals = residuals
                best_gamma = g

        return best_gamma, min_residuals


__all__ = [
    'HAS_NUMBA',
    'autocov_jit',
    'acf_jit',
    'idi_jit',
    'trace_joint_jit',
    'iat2counts_jit',
    'iat2bins_jit',
    'gamma_search_jit',
]
