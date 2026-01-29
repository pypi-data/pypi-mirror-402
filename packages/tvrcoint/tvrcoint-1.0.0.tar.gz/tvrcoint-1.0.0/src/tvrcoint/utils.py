"""
Utility Functions for TVRCoint

This module provides common utility functions used throughout the library.
"""

import numpy as np
from typing import Tuple, Optional, List


def difference(Y: np.ndarray, d: int = 1) -> np.ndarray:
    """
    Compute d-th order differences of a time series.
    
    Parameters
    ----------
    Y : np.ndarray
        Input data of shape (T, k) or (T,)
    d : int
        Order of differencing (default 1)
        
    Returns
    -------
    np.ndarray
        Differenced data of shape (T-d, k) or (T-d,)
    """
    if d == 0:
        return Y
    elif d == 1:
        return np.diff(Y, axis=0)
    else:
        return difference(np.diff(Y, axis=0), d - 1)


def lag_matrix(Y: np.ndarray, lags: int) -> np.ndarray:
    """
    Create a matrix of lagged values.
    
    Parameters
    ----------
    Y : np.ndarray
        Input data of shape (T, k)
    lags : int
        Number of lags to include
        
    Returns
    -------
    np.ndarray
        Lagged matrix of shape (T-lags, k*lags)
    """
    T, k = Y.shape
    if lags == 0:
        return np.zeros((T, 0))
    
    result = np.zeros((T - lags, k * lags))
    for i in range(lags):
        result[:, i * k:(i + 1) * k] = Y[lags - 1 - i:T - 1 - i, :]
    
    return result


def create_delta_Y_and_X(
    Y: np.ndarray,
    p: int,
    include_intercept: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Create differenced data and regressor matrices for VECM estimation.
    
    Parameters
    ----------
    Y : np.ndarray
        Original levels data of shape (T, k)
    p : int
        VAR lag order (p >= 1)
    include_intercept : bool
        Whether to include intercept
        
    Returns
    -------
    delta_Y : np.ndarray
        Differenced data of shape (T-p, k)
    Y_lag : np.ndarray
        Lagged levels of shape (T-p, k)
    X : np.ndarray
        Regressors (lagged differences) of shape (T-p, k*(p-1)) or with intercept
    """
    T, k = Y.shape
    
    # Differences
    delta_Y_full = np.diff(Y, axis=0)  # Shape (T-1, k)
    
    # We need observations from t = p+1 to T for delta_Y
    delta_Y = delta_Y_full[p - 1:, :]  # Shape (T-p, k)
    
    # Lagged levels Y_{t-1} for t = p+1, ..., T
    Y_lag = Y[p - 1:T - 1, :]  # Shape (T-p, k)
    
    # Lagged differences for t = p+1, ..., T
    T_eff = T - p
    
    if p > 1:
        # X contains lagged differences: ΔY_{t-1}, ..., ΔY_{t-p+1}
        X = np.zeros((T_eff, k * (p - 1)))
        for j in range(1, p):
            # ΔY_{t-j} for t = p+1, ..., T
            X[:, (j - 1) * k:j * k] = delta_Y_full[p - 1 - j:T - 1 - j, :]
    else:
        X = np.zeros((T_eff, 0))
    
    if include_intercept:
        X = np.column_stack([np.ones(T_eff), X])
    
    return delta_Y, Y_lag, X


def chi2_pvalue(statistic: float, df: int) -> float:
    """
    Compute p-value from chi-square distribution.
    
    Parameters
    ----------
    statistic : float
        Test statistic value
    df : int
        Degrees of freedom
        
    Returns
    -------
    float
        P-value (probability of observing a value >= statistic)
    """
    from scipy import stats
    return 1 - stats.chi2.cdf(statistic, df)


def check_data(Y: np.ndarray) -> Tuple[int, int]:
    """
    Validate input data and return dimensions.
    
    Parameters
    ----------
    Y : np.ndarray
        Input data
        
    Returns
    -------
    T : int
        Number of observations
    k : int
        Number of variables
        
    Raises
    ------
    ValueError
        If data is not valid
    """
    if not isinstance(Y, np.ndarray):
        Y = np.array(Y)
    
    if Y.ndim == 1:
        Y = Y.reshape(-1, 1)
    
    if Y.ndim != 2:
        raise ValueError("Data must be 2-dimensional (T x k)")
    
    T, k = Y.shape
    
    if T < k + 10:
        raise ValueError(f"Not enough observations: T={T}, k={k}")
    
    if np.any(np.isnan(Y)) or np.any(np.isinf(Y)):
        raise ValueError("Data contains NaN or Inf values")
    
    return T, k


def format_significance(pvalue: float) -> str:
    """
    Format significance stars for p-value.
    
    Parameters
    ----------
    pvalue : float
        P-value
        
    Returns
    -------
    str
        Significance indicator ('***', '**', '*', or '')
    """
    if pvalue < 0.01:
        return '***'
    elif pvalue < 0.05:
        return '**'
    elif pvalue < 0.10:
        return '*'
    else:
        return ''


def print_matrix(M: np.ndarray, name: str = "", precision: int = 4) -> None:
    """
    Pretty print a matrix.
    
    Parameters
    ----------
    M : np.ndarray
        Matrix to print
    name : str
        Name to display
    precision : int
        Decimal precision
    """
    if name:
        print(f"{name}:")
    print(np.array2string(M, precision=precision, suppress_small=True))
    print()


def information_criteria(
    log_likelihood: float,
    n_params: int,
    T: int
) -> Tuple[float, float, float]:
    """
    Compute information criteria (AIC, BIC, HQ).
    
    Parameters
    ----------
    log_likelihood : float
        Log-likelihood value
    n_params : int
        Number of estimated parameters
    T : int
        Number of observations
        
    Returns
    -------
    aic : float
        Akaike Information Criterion
    bic : float
        Bayesian Information Criterion
    hq : float
        Hannan-Quinn Criterion
    """
    aic = -2 * log_likelihood + 2 * n_params
    bic = -2 * log_likelihood + np.log(T) * n_params
    hq = -2 * log_likelihood + 2 * np.log(np.log(T)) * n_params
    
    return aic, bic, hq


def vec(M: np.ndarray) -> np.ndarray:
    """
    Vectorize a matrix (column-stacking).
    
    Parameters
    ----------
    M : np.ndarray
        Matrix of shape (m, n)
        
    Returns
    -------
    np.ndarray
        Vector of shape (m*n,)
    """
    return M.flatten('F')


def unvec(v: np.ndarray, m: int, n: int) -> np.ndarray:
    """
    Un-vectorize a vector into a matrix.
    
    Parameters
    ----------
    v : np.ndarray
        Vector of shape (m*n,)
    m : int
        Number of rows
    n : int
        Number of columns
        
    Returns
    -------
    np.ndarray
        Matrix of shape (m, n)
    """
    return v.reshape((m, n), order='F')
