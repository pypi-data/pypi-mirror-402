"""
Multivariate Phase-Type (MVPH) distribution utilities.

This module provides functions for analyzing multivariate phase-type
distributions, including joint moments, correlations, and distributions.
"""

from .mvph_jit import *

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
