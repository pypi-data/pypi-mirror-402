"""
JIT-compiled kernels for Laplace Transform Inversion.

Provides Numba-accelerated versions of LTI computational hotspots:
- Coefficient generation for Euler, Talbot, Gaver-Stehfest methods
- Weighted summation kernels for inversion
- Multi-point evaluation loops

Graceful fallback to pure Python if Numba is not available.

License: MIT (same as LINE)
"""

import numpy as np
from typing import Tuple
from math import pi, log, tan, exp, factorial

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

    @njit(cache=True)
    def euler_get_alpha_jit(n: int, alpha_real: np.ndarray, alpha_imag: np.ndarray) -> None:
        """
        JIT-compiled Euler alpha coefficient generation.

        Args:
            n: Number of terms (should be odd)
            alpha_real: Output array for real parts (n,)
            alpha_imag: Output array for imaginary parts (n,)
        """
        log10_factor = (n - 1) * np.log(10.0) / 6.0
        for i in range(n):
            alpha_real[i] = log10_factor
            alpha_imag[i] = np.pi * i

    @njit(cache=True)
    def euler_get_eta_jit(n: int, eta: np.ndarray) -> None:
        """
        JIT-compiled Euler eta coefficient generation.

        Args:
            n: Number of terms (should be odd)
            eta: Output array (n,)
        """
        eta[0] = 0.5

        # Euler defined only for odd n
        half_n = (n + 1) // 2
        for i in range(1, half_n):
            eta[i] = 1.0

        eta[n - 1] = 1.0 / (2.0 ** ((n - 1) / 2.0))

        # Binomial coefficient computation
        half_n_minus_1 = (n - 1) // 2
        for i in range(1, half_n_minus_1):
            # Compute C(half_n_minus_1, i)
            binom = 1
            for j in range(i):
                binom = binom * (half_n_minus_1 - j) // (j + 1)

            eta[n - i - 1] = eta[n - i] + (2.0 ** ((1 - n) / 2.0)) * binom

    @njit(cache=True)
    def euler_get_omega_jit(n: int, eta: np.ndarray, omega_real: np.ndarray, omega_imag: np.ndarray) -> None:
        """
        JIT-compiled Euler omega coefficient generation.

        Args:
            n: Number of terms (should be odd)
            eta: Eta coefficients (n,)
            omega_real: Output array for real parts (n,)
            omega_imag: Output array for imaginary parts (n,)
        """
        scale = 10.0 ** ((n - 1) / 6.0)
        for i in range(n):
            sign = (-1.0) ** i
            omega_real[i] = scale * sign * eta[i]
            omega_imag[i] = 0.0

    @njit(cache=True)
    def talbot_get_alpha_jit(n: int, alpha_real: np.ndarray, alpha_imag: np.ndarray) -> None:
        """
        JIT-compiled Talbot alpha coefficient generation.

        Args:
            n: Number of terms
            alpha_real: Output array for real parts (n,)
            alpha_imag: Output array for imaginary parts (n,)
        """
        # For k = 1
        alpha_real[0] = 2.0 * n / 5.0
        alpha_imag[0] = 0.0

        # For k = 2 onwards
        for i in range(1, n):
            theta = i * np.pi / n
            cot_theta = 1.0 / np.tan(theta)
            alpha_real[i] = 2 * i * np.pi / 5 * cot_theta
            alpha_imag[i] = 2 * i * np.pi / 5

    @njit(cache=True)
    def talbot_get_omega_jit(
        n: int,
        alpha_real: np.ndarray,
        alpha_imag: np.ndarray,
        omega_real: np.ndarray,
        omega_imag: np.ndarray
    ) -> None:
        """
        JIT-compiled Talbot omega coefficient generation.

        Args:
            n: Number of terms
            alpha_real: Alpha real parts (n,)
            alpha_imag: Alpha imaginary parts (n,)
            omega_real: Output array for real parts (n,)
            omega_imag: Output array for imaginary parts (n,)
        """
        # For k = 1
        exp_alpha_0 = np.exp(alpha_real[0])
        omega_real[0] = exp_alpha_0 / 5.0
        omega_imag[0] = 0.0

        # For k = 2 onwards
        for i in range(1, n):
            theta = i * np.pi / n
            tan_theta = np.tan(theta)
            cot_theta = 1.0 / tan_theta

            # exp(alpha) where alpha is complex
            exp_real = np.exp(alpha_real[i]) * np.cos(alpha_imag[i])
            exp_imag = np.exp(alpha_real[i]) * np.sin(alpha_imag[i])

            # Multiplier: 1 + i*(theta*(1+cot^2) - cot)
            mult_real = 1.0
            mult_imag = theta * (1 + cot_theta ** 2) - cot_theta

            # Complex multiplication: exp * mult
            result_real = exp_real * mult_real - exp_imag * mult_imag
            result_imag = exp_real * mult_imag + exp_imag * mult_real

            omega_real[i] = 2 * result_real / 5.0
            omega_imag[i] = 2 * result_imag / 5.0

    @njit(cache=True)
    def gaver_stehfest_get_alpha_jit(n: int, alpha: np.ndarray) -> int:
        """
        JIT-compiled Gaver-Stehfest alpha coefficient generation.

        Args:
            n: Number of terms (will be rounded to even)
            alpha: Output array (n,)

        Returns:
            Actual n used (even number)
        """
        if n % 2 == 1:
            n = n - 1

        log2 = np.log(2.0)
        for k in range(n):
            alpha[k] = (k + 1) * log2

        return n

    @njit(cache=True)
    def gaver_stehfest_get_omega_jit(n: int, omega: np.ndarray) -> int:
        """
        JIT-compiled Gaver-Stehfest omega coefficient generation.

        Args:
            n: Number of terms (will be rounded to even)
            omega: Output array (n,)

        Returns:
            Actual n used (even number)
        """
        if n % 2 == 1:
            n = n - 1

        log2 = np.log(2.0)
        half_n = n // 2

        # Compute factorial of half_n
        fact_half_n = 1.0
        for i in range(1, half_n + 1):
            fact_half_n *= i

        for k in range(1, n + 1):
            val = ((-1.0) ** (half_n + k)) * log2

            # Summation
            sum_val = 0.0
            j = int((k + 1) // 2)
            while j <= min(k, half_n):
                # Compute: j^(half_n+1) / fact_half_n * C(half_n, j) * C(2j, j) * C(j, k-j)
                val2 = (j ** (half_n + 1)) / fact_half_n

                # C(half_n, j)
                binom1 = 1
                for i in range(j):
                    binom1 = binom1 * (half_n - i) // (i + 1)

                # C(2j, j)
                binom2 = 1
                for i in range(j):
                    binom2 = binom2 * (2 * j - i) // (i + 1)

                # C(j, k-j)
                binom3 = 1
                for i in range(k - j):
                    binom3 = binom3 * (j - i) // (i + 1)

                val2 *= binom1 * binom2 * binom3
                sum_val += val2
                j += 1

            omega[k - 1] = val * sum_val

        return n

    @njit(fastmath=True, cache=True)
    def euler_sum_jit(
        F_real: np.ndarray,
        F_imag: np.ndarray,
        omega_real: np.ndarray,
        omega_imag: np.ndarray,
        n: int
    ) -> float:
        """
        JIT-compiled Euler method summation.

        Computes sum(real(omega * F)) for Euler inversion.

        Args:
            F_real: Real parts of F(s) evaluations (n,)
            F_imag: Imaginary parts of F(s) evaluations (n,)
            omega_real: Omega real parts (n,)
            omega_imag: Omega imaginary parts (n,)
            n: Number of terms

        Returns:
            Sum of real parts of omega * F
        """
        result = 0.0
        for i in range(n):
            # Complex multiplication: omega * F
            prod_real = omega_real[i] * F_real[i] - omega_imag[i] * F_imag[i]
            result += prod_real
        return result

    @njit(fastmath=True, cache=True)
    def talbot_sum_jit(
        F_real: np.ndarray,
        F_imag: np.ndarray,
        omega_real: np.ndarray,
        omega_imag: np.ndarray,
        n: int
    ) -> float:
        """
        JIT-compiled Talbot method summation.

        Computes sum(real(omega * F)) for Talbot inversion.

        Args:
            F_real: Real parts of F(s) evaluations (n,)
            F_imag: Imaginary parts of F(s) evaluations (n,)
            omega_real: Omega real parts (n,)
            omega_imag: Omega imaginary parts (n,)
            n: Number of terms

        Returns:
            Sum of real parts of omega * F
        """
        result = 0.0
        for i in range(n):
            # Complex multiplication: omega * F
            prod_real = omega_real[i] * F_real[i] - omega_imag[i] * F_imag[i]
            result += prod_real
        return result

    @njit(fastmath=True, cache=True)
    def gaver_stehfest_sum_jit(
        F_vals: np.ndarray,
        omega: np.ndarray,
        n: int
    ) -> float:
        """
        JIT-compiled Gaver-Stehfest method summation.

        Computes sum(omega * F) for Gaver-Stehfest inversion.

        Args:
            F_vals: F(s) evaluations (n,)
            omega: Omega coefficients (n,)
            n: Number of terms

        Returns:
            Weighted sum
        """
        result = 0.0
        for i in range(n):
            result += omega[i] * F_vals[i]
        return result

    @njit(fastmath=True, cache=True)
    def compute_s_values_euler_jit(
        alpha_real: np.ndarray,
        alpha_imag: np.ndarray,
        t: float,
        n: int,
        s_real: np.ndarray,
        s_imag: np.ndarray
    ) -> None:
        """
        JIT-compiled computation of s values for Euler method.

        Args:
            alpha_real: Alpha real parts (n,)
            alpha_imag: Alpha imaginary parts (n,)
            t: Time point
            n: Number of terms
            s_real: Output real parts (n,)
            s_imag: Output imaginary parts (n,)
        """
        inv_t = 1.0 / t
        for i in range(n):
            s_real[i] = alpha_real[i] * inv_t
            s_imag[i] = alpha_imag[i] * inv_t

    @njit(fastmath=True, cache=True)
    def compute_s_values_talbot_jit(
        alpha_real: np.ndarray,
        alpha_imag: np.ndarray,
        t: float,
        n: int,
        s_real: np.ndarray,
        s_imag: np.ndarray
    ) -> None:
        """
        JIT-compiled computation of s values for Talbot method.

        Args:
            alpha_real: Alpha real parts (n,)
            alpha_imag: Alpha imaginary parts (n,)
            t: Time point
            n: Number of terms
            s_real: Output real parts (n,)
            s_imag: Output imaginary parts (n,)
        """
        inv_t = 1.0 / t
        for i in range(n):
            s_real[i] = alpha_real[i] * inv_t
            s_imag[i] = alpha_imag[i] * inv_t

    @njit(fastmath=True, cache=True)
    def compute_s_values_gaver_jit(
        alpha: np.ndarray,
        t: float,
        n: int,
        s: np.ndarray
    ) -> None:
        """
        JIT-compiled computation of s values for Gaver-Stehfest method.

        Args:
            alpha: Alpha coefficients (n,)
            t: Time point
            n: Number of terms
            s: Output s values (n,)
        """
        inv_t = 1.0 / t
        for i in range(n):
            s[i] = alpha[i] * inv_t

else:
    # =========================================================================
    # Pure Python fallback versions
    # =========================================================================

    def euler_get_alpha_jit(n: int, alpha_real: np.ndarray, alpha_imag: np.ndarray) -> None:
        """Pure Python Euler alpha generation."""
        log10_factor = (n - 1) * np.log(10.0) / 6.0
        for i in range(n):
            alpha_real[i] = log10_factor
            alpha_imag[i] = np.pi * i

    def euler_get_eta_jit(n: int, eta: np.ndarray) -> None:
        """Pure Python Euler eta generation."""
        from scipy.special import comb

        eta[0] = 0.5
        half_n = (n + 1) // 2
        for i in range(1, half_n):
            eta[i] = 1.0

        eta[n - 1] = 1.0 / (2.0 ** ((n - 1) / 2.0))

        half_n_minus_1 = (n - 1) // 2
        for i in range(1, half_n_minus_1):
            eta[n - i - 1] = eta[n - i] + (2.0 ** ((1 - n) / 2.0)) * comb(half_n_minus_1, i, exact=True)

    def euler_get_omega_jit(n: int, eta: np.ndarray, omega_real: np.ndarray, omega_imag: np.ndarray) -> None:
        """Pure Python Euler omega generation."""
        scale = 10.0 ** ((n - 1) / 6.0)
        for i in range(n):
            sign = (-1.0) ** i
            omega_real[i] = scale * sign * eta[i]
            omega_imag[i] = 0.0

    def talbot_get_alpha_jit(n: int, alpha_real: np.ndarray, alpha_imag: np.ndarray) -> None:
        """Pure Python Talbot alpha generation."""
        alpha_real[0] = 2.0 * n / 5.0
        alpha_imag[0] = 0.0

        for i in range(1, n):
            theta = i * np.pi / n
            cot_theta = 1.0 / np.tan(theta)
            alpha_real[i] = 2 * i * np.pi / 5 * cot_theta
            alpha_imag[i] = 2 * i * np.pi / 5

    def talbot_get_omega_jit(
        n: int,
        alpha_real: np.ndarray,
        alpha_imag: np.ndarray,
        omega_real: np.ndarray,
        omega_imag: np.ndarray
    ) -> None:
        """Pure Python Talbot omega generation."""
        exp_alpha_0 = np.exp(alpha_real[0])
        omega_real[0] = exp_alpha_0 / 5.0
        omega_imag[0] = 0.0

        for i in range(1, n):
            theta = i * np.pi / n
            tan_theta = np.tan(theta)
            cot_theta = 1.0 / tan_theta

            alpha_complex = complex(alpha_real[i], alpha_imag[i])
            exp_alpha = np.exp(alpha_complex)

            mult = complex(1.0, theta * (1 + cot_theta ** 2) - cot_theta)
            result = 2 * exp_alpha * mult / 5.0

            omega_real[i] = result.real
            omega_imag[i] = result.imag

    def gaver_stehfest_get_alpha_jit(n: int, alpha: np.ndarray) -> int:
        """Pure Python Gaver-Stehfest alpha generation."""
        if n % 2 == 1:
            n = n - 1

        log2 = np.log(2.0)
        for k in range(n):
            alpha[k] = (k + 1) * log2

        return n

    def gaver_stehfest_get_omega_jit(n: int, omega: np.ndarray) -> int:
        """Pure Python Gaver-Stehfest omega generation."""
        from scipy.special import comb
        from math import factorial

        if n % 2 == 1:
            n = n - 1

        log2 = np.log(2.0)
        half_n = n // 2

        for k in range(1, n + 1):
            val = ((-1.0) ** (half_n + k)) * log2

            sum_val = 0.0
            j = int((k + 1) // 2)
            while j <= min(k, half_n):
                val2 = (j ** (half_n + 1)) / factorial(half_n)
                val2 *= comb(half_n, j, exact=True)
                val2 *= comb(2 * j, j, exact=True)
                val2 *= comb(j, k - j, exact=True)
                sum_val += val2
                j += 1

            omega[k - 1] = val * sum_val

        return n

    def euler_sum_jit(
        F_real: np.ndarray,
        F_imag: np.ndarray,
        omega_real: np.ndarray,
        omega_imag: np.ndarray,
        n: int
    ) -> float:
        """Pure Python Euler summation."""
        result = 0.0
        for i in range(n):
            prod_real = omega_real[i] * F_real[i] - omega_imag[i] * F_imag[i]
            result += prod_real
        return result

    def talbot_sum_jit(
        F_real: np.ndarray,
        F_imag: np.ndarray,
        omega_real: np.ndarray,
        omega_imag: np.ndarray,
        n: int
    ) -> float:
        """Pure Python Talbot summation."""
        result = 0.0
        for i in range(n):
            prod_real = omega_real[i] * F_real[i] - omega_imag[i] * F_imag[i]
            result += prod_real
        return result

    def gaver_stehfest_sum_jit(
        F_vals: np.ndarray,
        omega: np.ndarray,
        n: int
    ) -> float:
        """Pure Python Gaver-Stehfest summation."""
        return float(np.sum(omega[:n] * F_vals[:n]))

    def compute_s_values_euler_jit(
        alpha_real: np.ndarray,
        alpha_imag: np.ndarray,
        t: float,
        n: int,
        s_real: np.ndarray,
        s_imag: np.ndarray
    ) -> None:
        """Pure Python s value computation for Euler."""
        inv_t = 1.0 / t
        s_real[:n] = alpha_real[:n] * inv_t
        s_imag[:n] = alpha_imag[:n] * inv_t

    def compute_s_values_talbot_jit(
        alpha_real: np.ndarray,
        alpha_imag: np.ndarray,
        t: float,
        n: int,
        s_real: np.ndarray,
        s_imag: np.ndarray
    ) -> None:
        """Pure Python s value computation for Talbot."""
        inv_t = 1.0 / t
        s_real[:n] = alpha_real[:n] * inv_t
        s_imag[:n] = alpha_imag[:n] * inv_t

    def compute_s_values_gaver_jit(
        alpha: np.ndarray,
        t: float,
        n: int,
        s: np.ndarray
    ) -> None:
        """Pure Python s value computation for Gaver-Stehfest."""
        inv_t = 1.0 / t
        s[:n] = alpha[:n] * inv_t


__all__ = [
    'HAS_NUMBA',
    'euler_get_alpha_jit',
    'euler_get_eta_jit',
    'euler_get_omega_jit',
    'talbot_get_alpha_jit',
    'talbot_get_omega_jit',
    'gaver_stehfest_get_alpha_jit',
    'gaver_stehfest_get_omega_jit',
    'euler_sum_jit',
    'talbot_sum_jit',
    'gaver_stehfest_sum_jit',
    'compute_s_values_euler_jit',
    'compute_s_values_talbot_jit',
    'compute_s_values_gaver_jit',
]
