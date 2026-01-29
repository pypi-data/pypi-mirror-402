"""
Monte Carlo Simulation for Critical Values

This module implements Monte Carlo simulations to generate critical values
for the TVC LR test under the null hypothesis of time-invariant cointegration.

The simulations can be used to:
1. Verify the chi-square asymptotic distribution
2. Generate finite-sample critical values
3. Assess the size properties of the tests
"""

import numpy as np
from scipy import stats
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
import warnings


@dataclass
class SimulationResults:
    """
    Results from Monte Carlo simulation.
    
    Attributes
    ----------
    critical_values : dict
        Critical values at various significance levels
    empirical_size : dict
        Empirical rejection rates at asymptotic critical values
    mean_statistic : float
        Mean of simulated statistics
    std_statistic : float
        Standard deviation of simulated statistics
    statistics : np.ndarray
        Array of all simulated statistics
    m : int
        Chebyshev polynomial order
    k : int
        Number of variables
    r : int
        Cointegration rank
    T : int
        Sample size
    n_simulations : int
        Number of simulations
    """
    critical_values: dict
    empirical_size: dict
    mean_statistic: float
    std_statistic: float
    statistics: np.ndarray
    m: int
    k: int
    r: int
    T: int
    n_simulations: int


def generate_cointegrated_data(
    T: int,
    k: int,
    r: int,
    alpha: Optional[np.ndarray] = None,
    beta: Optional[np.ndarray] = None,
    gamma: Optional[np.ndarray] = None,
    omega: Optional[np.ndarray] = None,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate data from a cointegrated VECM under the null hypothesis.
    
    The DGP follows:
        ΔY_t = α β' Y_{t-1} + Γ ΔY_{t-1} + ε_t
        ε_t ~ N(0, Ω)
    
    Parameters
    ----------
    T : int
        Number of observations
    k : int
        Number of variables
    r : int
        Cointegration rank
    alpha : np.ndarray, optional
        Adjustment matrix (k x r). If None, uses default.
    beta : np.ndarray, optional
        Cointegrating vectors (k x r). If None, uses default.
    gamma : np.ndarray, optional
        Short-run dynamics (k x k). If None, uses zeros.
    omega : np.ndarray, optional
        Error covariance (k x k). If None, uses identity.
    seed : int, optional
        Random seed
        
    Returns
    -------
    np.ndarray
        Simulated data of shape (T, k)
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Default parameters (as in the papers)
    if alpha is None:
        alpha = np.zeros((k, r))
        alpha[0, 0] = -0.5  # First variable adjusts to first cointegrating relation
        if r > 1 and k > 1:
            for i in range(1, min(r, k)):
                alpha[i, i] = -0.3
    
    if beta is None:
        beta = np.zeros((k, r))
        # First cointegrating vector: (1, 1, 0, ..., 0) or similar
        if k >= 2:
            beta[0, 0] = 1
            beta[1, 0] = 1
        else:
            beta[0, 0] = 1
        if r > 1:
            for i in range(1, r):
                if i + 1 < k:
                    beta[i, i] = 1
                    beta[i + 1, i] = 1
    
    if gamma is None:
        gamma = np.zeros((k, k))
        # Small AR effect
        gamma[0, 0] = 0.25
    
    if omega is None:
        omega = np.eye(k)
    
    # Generate innovations
    L = np.linalg.cholesky(omega)
    eps = np.random.randn(T, k) @ L.T
    
    # Initialize Y
    Y = np.zeros((T, k))
    
    # Burn-in period
    burn = 50
    Y_burn = np.zeros((burn, k))
    
    for t in range(1, burn):
        ec_term = alpha @ beta.T @ Y_burn[t - 1]
        ar_term = gamma @ (Y_burn[t - 1] - Y_burn[t - 2]) if t > 1 else np.zeros(k)
        Y_burn[t] = Y_burn[t - 1] + ec_term + ar_term + eps[t % T]
    
    # Main simulation
    Y[0] = Y_burn[-1]
    
    for t in range(1, T):
        ec_term = alpha @ beta.T @ Y[t - 1]
        ar_term = gamma @ (Y[t - 1] - Y[t - 2]) if t > 1 else np.zeros(k)
        Y[t] = Y[t - 1] + ec_term + ar_term + eps[t]
    
    return Y


def simulate_critical_values(
    m: int,
    k: int,
    r: int,
    T: int,
    n_simulations: int = 10000,
    p: int = 1,
    levels: List[float] = [0.10, 0.05, 0.01],
    seed: Optional[int] = None,
    verbose: bool = True
) -> SimulationResults:
    """
    Simulate critical values for the TVC LR test.
    
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
    n_simulations : int
        Number of Monte Carlo replications
    p : int
        VAR lag order
    levels : list
        Significance levels for critical values
    seed : int, optional
        Random seed
    verbose : bool
        Print progress
        
    Returns
    -------
    SimulationResults
        Simulation results including critical values and empirical sizes
    """
    from .lr_test import TVCTest
    
    if seed is not None:
        np.random.seed(seed)
    
    if verbose:
        print(f"Simulating TVC test: m={m}, k={k}, r={r}, T={T}")
        print(f"Number of simulations: {n_simulations}")
    
    # Degrees of freedom
    df = m * k * r
    
    # Asymptotic critical values
    asymptotic_cv = {level: stats.chi2.ppf(1 - level, df) for level in levels}
    
    # Store statistics
    statistics = np.zeros(n_simulations)
    
    # Simulation loop
    for sim in range(n_simulations):
        if verbose and (sim + 1) % 1000 == 0:
            print(f"  Simulation {sim + 1}/{n_simulations}")
        
        try:
            # Generate data under H0
            Y = generate_cointegrated_data(T, k, r)
            
            # Compute LR statistic
            test = TVCTest()
            results = test.test(Y, r=r, m=m, p=p, include_drift=True)
            statistics[sim] = results.statistic
        except Exception as e:
            statistics[sim] = np.nan
            if verbose:
                warnings.warn(f"Simulation {sim} failed: {e}")
    
    # Remove NaN values
    valid_stats = statistics[~np.isnan(statistics)]
    n_valid = len(valid_stats)
    
    if verbose:
        print(f"Valid simulations: {n_valid}/{n_simulations}")
    
    # Compute empirical critical values
    critical_values = {}
    for level in levels:
        critical_values[level] = np.percentile(valid_stats, 100 * (1 - level))
    
    # Compute empirical size (rejection rate at asymptotic CV)
    empirical_size = {}
    for level in levels:
        rejection_rate = np.mean(valid_stats > asymptotic_cv[level])
        empirical_size[level] = rejection_rate
    
    return SimulationResults(
        critical_values=critical_values,
        empirical_size=empirical_size,
        mean_statistic=np.mean(valid_stats),
        std_statistic=np.std(valid_stats),
        statistics=valid_stats,
        m=m,
        k=k,
        r=r,
        T=T,
        n_simulations=n_valid
    )


def generate_critical_value_tables(
    T_values: List[int] = [50, 100, 200],
    m_values: List[int] = [1, 2, 5],
    k_values: List[int] = [2, 3],
    r: int = 1,
    n_simulations: int = 10000,
    seed: Optional[int] = None
) -> Dict:
    """
    Generate comprehensive critical value tables.
    
    Parameters
    ----------
    T_values : list
        Sample sizes to simulate
    m_values : list
        Chebyshev orders to simulate
    k_values : list
        Numbers of variables to simulate
    r : int
        Cointegration rank
    n_simulations : int
        Number of simulations per configuration
    seed : int, optional
        Random seed
        
    Returns
    -------
    dict
        Nested dictionary with critical values
    """
    tables = {}
    
    for k in k_values:
        tables[k] = {}
        for T in T_values:
            tables[k][T] = {}
            for m in m_values:
                if m * (T / 10) > T / 2:
                    continue  # Skip if m is too large for T
                
                print(f"\nSimulating: k={k}, T={T}, m={m}")
                
                results = simulate_critical_values(
                    m=m, k=k, r=r, T=T,
                    n_simulations=n_simulations,
                    seed=seed,
                    verbose=False
                )
                
                tables[k][T][m] = {
                    'cv_10': results.critical_values.get(0.10),
                    'cv_05': results.critical_values.get(0.05),
                    'cv_01': results.critical_values.get(0.01),
                    'size_10': results.empirical_size.get(0.10),
                    'size_05': results.empirical_size.get(0.05),
                    'size_01': results.empirical_size.get(0.01),
                    'mean': results.mean_statistic,
                    'std': results.std_statistic
                }
    
    return tables


def print_simulation_summary(results: SimulationResults) -> None:
    """Print a summary of simulation results."""
    df = results.m * results.k * results.r
    
    print("\n" + "=" * 60)
    print("Monte Carlo Simulation Results")
    print("=" * 60)
    print(f"\nConfiguration: m={results.m}, k={results.k}, r={results.r}, T={results.T}")
    print(f"Degrees of freedom: {df}")
    print(f"Number of simulations: {results.n_simulations}")
    
    print("\n--- Statistic Summary ---")
    print(f"Mean:     {results.mean_statistic:.4f}  (Theoretical: {df:.4f})")
    print(f"Std Dev:  {results.std_statistic:.4f}  (Theoretical: {np.sqrt(2 * df):.4f})")
    
    print("\n--- Critical Values ---")
    print(f"Level     Empirical    Asymptotic")
    for level in sorted(results.critical_values.keys(), reverse=True):
        emp_cv = results.critical_values[level]
        asym_cv = stats.chi2.ppf(1 - level, df)
        print(f"{level:.0%}       {emp_cv:.4f}       {asym_cv:.4f}")
    
    print("\n--- Empirical Size (at asymptotic CV) ---")
    for level in sorted(results.empirical_size.keys(), reverse=True):
        emp_size = results.empirical_size[level]
        print(f"{level:.0%}:     {emp_size:.4f}  (Nominal: {level:.4f})")
    
    print("=" * 60)


# Data generating processes from the papers

def dgp_bm(T: int, k: int = 2, p: int = 2, seed: Optional[int] = None) -> np.ndarray:
    """
    Bierens-Martins (2010) DGP.
    
    Bivariate system with r=1, k=2, p=2
    α = (-0.5, 0)', β = (1, 1)'
    Γ = [[0.25, 0], [0, 0]]
    """
    if seed is not None:
        np.random.seed(seed)
    
    alpha = np.array([[-0.5], [0.0]])
    beta = np.array([[1.0], [1.0]])
    gamma = np.array([[0.25, 0.0], [0.0, 0.0]])
    omega = np.eye(k)
    
    return generate_cointegrated_data(T, k, 1, alpha, beta, gamma, omega)


def dgp_js(T: int, k: int = 3, seed: Optional[int] = None) -> np.ndarray:
    """
    Johansen-Swensen (2002, 2006) DGP.
    
    Trivariate system with r=1, k=3, p=1
    α = (-0.4, -0.4, 0)', β = (1, 0, 0)'
    """
    if seed is not None:
        np.random.seed(seed)
    
    alpha = np.array([[-0.4], [-0.4], [0.0]])
    beta = np.array([[1.0], [0.0], [0.0]])
    gamma = np.zeros((k, k))
    omega = np.eye(k)
    
    return generate_cointegrated_data(T, k, 1, alpha, beta, gamma, omega)


def dgp_ey(T: int, k: int = 3, seed: Optional[int] = None) -> np.ndarray:
    """
    Engle-Yoo (1987) DGP.
    
    Trivariate system with r=2, k=3, p=1
    α = [[-0.4, 0.1], [0.1, 0.2], [0.1, 0.3]]
    β = [[1, 1], [-2, -0.5], [1, -0.5]]
    """
    if seed is not None:
        np.random.seed(seed)
    
    alpha = np.array([[-0.4, 0.1], [0.1, 0.2], [0.1, 0.3]])
    beta = np.array([[1.0, 1.0], [-2.0, -0.5], [1.0, -0.5]])
    gamma = np.zeros((k, k))
    omega = 100 * np.eye(k)
    
    return generate_cointegrated_data(T, k, 2, alpha, beta, gamma, omega)
