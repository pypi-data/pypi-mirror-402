"""
TVRCoint - Time-Varying Cointegration Tests

A Python library for testing time-invariant cointegration against 
time-varying cointegration alternatives using bootstrap methods.

Based on:
- Bierens & Martins (2010) "Time-Varying Cointegration" - Econometric Theory
- Martins (2015) "Bootstrap Tests for Time Varying Cointegration" - Econometric Reviews

Author: Dr Merwan Roudane
Email: merwanroudane920@gmail.com
GitHub: https://github.com/merwanroudane/tvrcoint
"""

__version__ = "1.0.0"
__author__ = "Dr Merwan Roudane"
__email__ = "merwanroudane920@gmail.com"

from .chebyshev import chebyshev_poly, chebyshev_matrix, chebyshev_polynomials
from .matrices import compute_s_matrices, solve_eigenvalue_problem
from .tvvecm import TVVECM
from .lr_test import TVCTest, TVCTestResults
from .bootstrap import BootstrapTVCTest, BootstrapTVCTestResults
from .output import format_results, results_to_latex, results_to_markdown, results_to_html
from .simulation import simulate_critical_values, generate_critical_value_tables

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    # Chebyshev polynomials
    "chebyshev_poly",
    "chebyshev_matrix",
    "chebyshev_polynomials",
    # Matrix computations
    "compute_s_matrices",
    "solve_eigenvalue_problem",
    # TV-VECM
    "TVVECM",
    # LR Test
    "TVCTest",
    "TVCTestResults",
    # Bootstrap Tests
    "BootstrapTVCTest",
    "BootstrapTVCTestResults",
    # Output
    "format_results",
    "results_to_latex",
    "results_to_markdown",
    "results_to_html",
    # Simulation
    "simulate_critical_values",
    "generate_critical_value_tables",
]
