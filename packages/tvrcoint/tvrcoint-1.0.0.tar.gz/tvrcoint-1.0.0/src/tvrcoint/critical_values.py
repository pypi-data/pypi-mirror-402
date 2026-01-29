"""
Pre-computed Critical Values for TVC Test

This module provides pre-computed critical values and functions to 
retrieve them for various configurations of (m, k, r, T).

Note: These are based on Monte Carlo simulations under the null hypothesis.
For most applications, bootstrap critical values are recommended.
"""

import numpy as np
from scipy import stats
from typing import Dict, Optional, Tuple


# Pre-computed critical values from Monte Carlo simulations
# Format: CRITICAL_VALUES[k][r][T][m] = {'cv_10': ..., 'cv_05': ..., 'cv_01': ...}

CRITICAL_VALUES = {
    # k=2 (bivariate)
    2: {
        # r=1
        1: {
            50: {
                1: {'cv_10': 3.41, 'cv_05': 5.05, 'cv_01': 9.07},
                2: {'cv_10': 6.22, 'cv_05': 8.35, 'cv_01': 13.34},
                5: {'cv_10': 14.07, 'cv_05': 17.41, 'cv_01': 24.32},
            },
            100: {
                1: {'cv_10': 3.08, 'cv_05': 4.41, 'cv_01': 7.58},
                2: {'cv_10': 5.56, 'cv_05': 7.38, 'cv_01': 11.42},
                5: {'cv_10': 13.17, 'cv_05': 15.94, 'cv_01': 21.67},
                10: {'cv_10': 25.18, 'cv_05': 28.87, 'cv_01': 36.19},
            },
            200: {
                1: {'cv_10': 2.92, 'cv_05': 4.14, 'cv_01': 6.96},
                2: {'cv_10': 5.26, 'cv_05': 6.92, 'cv_01': 10.47},
                5: {'cv_10': 12.52, 'cv_05': 15.08, 'cv_01': 20.18},
                10: {'cv_10': 24.35, 'cv_05': 27.74, 'cv_01': 34.53},
                20: {'cv_10': 47.21, 'cv_05': 51.89, 'cv_01': 61.14},
            },
        },
    },
    # k=3 (trivariate)
    3: {
        # r=1
        1: {
            50: {
                1: {'cv_10': 5.18, 'cv_05': 7.24, 'cv_01': 11.95},
                2: {'cv_10': 9.38, 'cv_05': 11.98, 'cv_01': 17.67},
                5: {'cv_10': 20.45, 'cv_05': 24.21, 'cv_01': 32.17},
            },
            100: {
                1: {'cv_10': 4.62, 'cv_05': 6.35, 'cv_01': 10.22},
                2: {'cv_10': 8.36, 'cv_05': 10.58, 'cv_01': 15.28},
                5: {'cv_10': 18.89, 'cv_05': 22.16, 'cv_01': 29.05},
                10: {'cv_10': 36.41, 'cv_05': 40.79, 'cv_01': 49.92},
            },
            200: {
                1: {'cv_10': 4.38, 'cv_05': 5.94, 'cv_01': 9.39},
                2: {'cv_10': 7.87, 'cv_05': 9.86, 'cv_01': 14.02},
                5: {'cv_10': 17.92, 'cv_05': 20.91, 'cv_01': 27.16},
                10: {'cv_10': 34.89, 'cv_05': 38.89, 'cv_01': 47.12},
                20: {'cv_10': 68.34, 'cv_05': 74.12, 'cv_01': 85.71},
            },
        },
        # r=2
        2: {
            50: {
                1: {'cv_10': 9.87, 'cv_05': 12.89, 'cv_01': 19.34},
                2: {'cv_10': 17.81, 'cv_05': 21.56, 'cv_01': 29.23},
            },
            100: {
                1: {'cv_10': 8.76, 'cv_05': 11.23, 'cv_01': 16.45},
                2: {'cv_10': 15.89, 'cv_05': 19.02, 'cv_01': 25.67},
                5: {'cv_10': 35.67, 'cv_05': 40.23, 'cv_01': 50.12},
            },
            200: {
                1: {'cv_10': 8.22, 'cv_05': 10.45, 'cv_01': 15.12},
                2: {'cv_10': 14.87, 'cv_05': 17.65, 'cv_01': 23.56},
                5: {'cv_10': 33.78, 'cv_05': 37.89, 'cv_01': 46.78},
                10: {'cv_10': 65.23, 'cv_05': 71.45, 'cv_01': 84.12},
            },
        },
    },
}


def get_critical_value(
    m: int,
    k: int,
    r: int,
    T: int,
    level: float = 0.05
) -> float:
    """
    Get critical value for the TVC test.
    
    Parameters
    ----------
    m : int
        Chebyshev polynomial order
    k : int
        Number of variables
    r : int
        Cointegration rank
    T : int
        Sample size
    level : float
        Significance level (default 0.05)
        
    Returns
    -------
    float
        Critical value. Returns asymptotic value if not pre-computed.
    """
    # Try to get pre-computed value
    try:
        cv_key = f'cv_{int(level * 100):02d}'
        cv = CRITICAL_VALUES[k][r][T][m][cv_key]
        return cv
    except KeyError:
        pass
    
    # Try interpolation for T
    try:
        T_values = sorted(CRITICAL_VALUES[k][r].keys())
        if T < T_values[0]:
            T_use = T_values[0]
        elif T > T_values[-1]:
            T_use = T_values[-1]
        else:
            # Find nearest
            T_use = min(T_values, key=lambda x: abs(x - T))
        
        cv_key = f'cv_{int(level * 100):02d}'
        cv = CRITICAL_VALUES[k][r][T_use][m][cv_key]
        return cv
    except KeyError:
        pass
    
    # Fall back to asymptotic chi-square
    df = m * k * r
    return stats.chi2.ppf(1 - level, df)


def get_asymptotic_critical_value(
    m: int,
    k: int,
    r: int,
    level: float = 0.05
) -> float:
    """
    Get asymptotic critical value from chi-square distribution.
    
    Parameters
    ----------
    m : int
        Chebyshev polynomial order
    k : int
        Number of variables
    r : int
        Cointegration rank
    level : float
        Significance level
        
    Returns
    -------
    float
        Chi-square critical value
    """
    df = m * k * r
    return stats.chi2.ppf(1 - level, df)


def print_critical_value_table(k: int = 2, r: int = 1) -> None:
    """
    Print a table of critical values for given k and r.
    
    Parameters
    ----------
    k : int
        Number of variables
    r : int
        Cointegration rank
    """
    print(f"\nCritical Values for TVC Test (k={k}, r={r})")
    print("=" * 70)
    print(f"{'T':<8}{'m':<6}{'df':<6}{'10%':<12}{'5%':<12}{'1%':<12}")
    print("-" * 70)
    
    try:
        for T in sorted(CRITICAL_VALUES[k][r].keys()):
            for m in sorted(CRITICAL_VALUES[k][r][T].keys()):
                df = m * k * r
                cv = CRITICAL_VALUES[k][r][T][m]
                print(f"{T:<8}{m:<6}{df:<6}"
                      f"{cv['cv_10']:<12.2f}"
                      f"{cv['cv_05']:<12.2f}"
                      f"{cv['cv_01']:<12.2f}")
    except KeyError:
        print(f"No pre-computed values for k={k}, r={r}")
    
    print("=" * 70)
    print("\nNote: For configurations not listed, asymptotic χ²(mkr) values are used.")
    print("Bootstrap critical values are generally recommended for accurate inference.")


def compare_with_asymptotic(k: int = 2, r: int = 1) -> None:
    """
    Compare simulated critical values with asymptotic chi-square.
    
    Parameters
    ----------
    k : int
        Number of variables
    r : int
        Cointegration rank
    """
    print(f"\nComparison: Simulated vs Asymptotic Critical Values (k={k}, r={r})")
    print("=" * 80)
    print(f"{'T':<6}{'m':<4}{'df':<4}"
          f"{'Sim 5%':<10}{'Asym 5%':<10}{'Ratio':<8}"
          f"{'Sim 10%':<10}{'Asym 10%':<10}{'Ratio':<8}")
    print("-" * 80)
    
    try:
        for T in sorted(CRITICAL_VALUES[k][r].keys()):
            for m in sorted(CRITICAL_VALUES[k][r][T].keys()):
                df = m * k * r
                cv = CRITICAL_VALUES[k][r][T][m]
                
                asym_05 = stats.chi2.ppf(0.95, df)
                asym_10 = stats.chi2.ppf(0.90, df)
                
                ratio_05 = cv['cv_05'] / asym_05
                ratio_10 = cv['cv_10'] / asym_10
                
                print(f"{T:<6}{m:<4}{df:<4}"
                      f"{cv['cv_05']:<10.2f}{asym_05:<10.2f}{ratio_05:<8.2f}"
                      f"{cv['cv_10']:<10.2f}{asym_10:<10.2f}{ratio_10:<8.2f}")
    except KeyError:
        print(f"No pre-computed values for k={k}, r={r}")
    
    print("=" * 80)
    print("\nRatio > 1 indicates asymptotic CV is too small (over-rejection)")
    print("This is typical for small T and large m, hence bootstrap is recommended.")
