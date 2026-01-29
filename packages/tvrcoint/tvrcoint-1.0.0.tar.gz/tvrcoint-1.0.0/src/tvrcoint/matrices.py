"""
Matrix Computations for Time-Varying Cointegration

This module implements the S matrix computations and generalized eigenvalue 
problem solving required for the TV-VECM estimation and LR test.

The key matrices are:
    S_{00,T}: Sample covariance of differenced data (adjusted for X)
    S_{11,T}^{(m)}: Sample covariance of extended lagged data (adjusted for X)
    S_{01,T}^{(m)}: Cross-covariance (adjusted for X)
    S_{10,T}^{(m)}: Transpose of S_{01}^{(m)}

The generalized eigenvalue problem:
    det[λ * S_{11}^{(m)} - S_{10}^{(m)} * S_{00}^{-1} * S_{01}^{(m)}] = 0
"""

import numpy as np
from scipy import linalg
from typing import Tuple, Dict, Optional


def compute_s_matrices(
    delta_Y: np.ndarray,
    Y_m: np.ndarray,
    X: Optional[np.ndarray] = None,
    include_intercept: bool = True
) -> Dict[str, np.ndarray]:
    """
    Compute the S matrices for the generalized eigenvalue problem.
    
    S_{00,T} = (1/T) * ΔY'ΔY - (1/T) * ΔY'X * (X'X)^{-1} * X'ΔY
    S_{11,T}^{(m)} = (1/T) * Y_m'Y_m - (1/T) * Y_m'X * (X'X)^{-1} * X'Y_m
    S_{01,T}^{(m)} = (1/T) * ΔY'Y_m - (1/T) * ΔY'X * (X'X)^{-1} * X'Y_m
    S_{10,T}^{(m)} = S_{01,T}^{(m)}'
    
    Parameters
    ----------
    delta_Y : np.ndarray
        Differenced data of shape (T_eff, k)
    Y_m : np.ndarray
        Extended lagged data of shape (T_eff, (m+1)*k)
    X : np.ndarray, optional
        Additional regressors of shape (T_eff, n_x). If None, includes
        only intercept or nothing based on include_intercept.
    include_intercept : bool
        Whether to include intercept in X (default True)
        
    Returns
    -------
    dict
        Dictionary with keys 'S00', 'S11', 'S01', 'S10' containing the matrices
        
    Examples
    --------
    >>> delta_Y = np.random.randn(98, 3)
    >>> Y_m = np.random.randn(98, 9)  # m=2, k=3
    >>> S = compute_s_matrices(delta_Y, Y_m)
    >>> S['S00'].shape
    (3, 3)
    """
    T_eff = delta_Y.shape[0]
    k = delta_Y.shape[1]
    dim_m = Y_m.shape[1]  # (m+1)*k
    
    # Build X matrix (regressors to partial out)
    if X is None:
        if include_intercept:
            X = np.ones((T_eff, 1))
        else:
            X = None
    else:
        if include_intercept:
            X = np.column_stack([np.ones(T_eff), X])
    
    # Compute raw moment matrices
    S00_raw = (1 / T_eff) * delta_Y.T @ delta_Y
    S11_raw = (1 / T_eff) * Y_m.T @ Y_m
    S01_raw = (1 / T_eff) * delta_Y.T @ Y_m
    
    if X is not None and X.shape[1] > 0:
        # Compute adjustments for X
        Sxx = (1 / T_eff) * X.T @ X
        Sx0 = (1 / T_eff) * X.T @ delta_Y
        Sx1 = (1 / T_eff) * X.T @ Y_m
        S0x = Sx0.T
        S1x = Sx1.T
        
        # Regularized inverse with pseudo-inverse for stability
        try:
            Sxx_inv = np.linalg.inv(Sxx)
        except np.linalg.LinAlgError:
            Sxx_inv = np.linalg.pinv(Sxx)
        
        # Adjusted matrices (partialling out X)
        S00 = S00_raw - S0x @ Sxx_inv @ Sx0
        S11 = S11_raw - S1x @ Sxx_inv @ Sx1
        S01 = S01_raw - S0x @ Sxx_inv @ Sx1
    else:
        S00 = S00_raw
        S11 = S11_raw
        S01 = S01_raw
    
    S10 = S01.T
    
    return {
        'S00': S00,
        'S11': S11,
        'S01': S01,
        'S10': S10
    }


def solve_eigenvalue_problem(
    S11: np.ndarray,
    S10: np.ndarray,
    S00: np.ndarray,
    S01: np.ndarray,
    r: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Solve the generalized eigenvalue problem for cointegration analysis.
    
    det[λ * S_{11} - S_{10} * S_{00}^{-1} * S_{01}] = 0
    
    This is equivalent to finding eigenvalues of:
        S_{11}^{-1} * S_{10} * S_{00}^{-1} * S_{01}
    
    Parameters
    ----------
    S11 : np.ndarray
        Matrix of shape ((m+1)*k, (m+1)*k)
    S10 : np.ndarray
        Matrix of shape ((m+1)*k, k)
    S00 : np.ndarray
        Matrix of shape (k, k)
    S01 : np.ndarray
        Matrix of shape (k, (m+1)*k)
    r : int, optional
        If provided, return only the r largest eigenvalues/vectors
        
    Returns
    -------
    eigenvalues : np.ndarray
        Ordered eigenvalues (largest first)
    eigenvectors : np.ndarray
        Corresponding eigenvectors (columns)
        
    Notes
    -----
    The eigenvalues should satisfy 0 ≤ λ ≤ 1 for properly specified problems.
    """
    # Compute S00^{-1}
    try:
        S00_inv = np.linalg.inv(S00)
    except np.linalg.LinAlgError:
        S00_inv = np.linalg.pinv(S00)
    
    # Form the matrix S_{11}^{-1} * S_{10} * S_{00}^{-1} * S_{01}
    # First compute S_{10} * S_{00}^{-1} * S_{01}
    product = S10 @ S00_inv @ S01
    
    # Solve generalized eigenvalue problem: product * v = λ * S11 * v
    try:
        eigenvalues, eigenvectors = linalg.eigh(product, S11)
    except (np.linalg.LinAlgError, ValueError):
        # Fall back to regularized approach
        S11_reg = S11 + 1e-10 * np.eye(S11.shape[0])
        try:
            S11_inv = np.linalg.inv(S11_reg)
        except np.linalg.LinAlgError:
            S11_inv = np.linalg.pinv(S11_reg)
        
        M = S11_inv @ product
        eigenvalues, eigenvectors = np.linalg.eig(M)
        eigenvalues = eigenvalues.real
        eigenvectors = eigenvectors.real
    
    # Sort in decreasing order
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    # Clip eigenvalues to [0, 1] range (numerical stability)
    eigenvalues = np.clip(eigenvalues, 0, 1 - 1e-15)
    
    if r is not None:
        eigenvalues = eigenvalues[:r]
        eigenvectors = eigenvectors[:, :r]
    
    return eigenvalues, eigenvectors


def compute_lr_statistic(
    lambda_0: np.ndarray,
    lambda_m: np.ndarray,
    T: int,
    r: int
) -> float:
    """
    Compute the LR test statistic for time-varying cointegration.
    
    LR_{m,T}^{tvc} = T * sum_{j=1}^{r} ln((1 - λ_{0,j}) / (1 - λ_{m,j}))
    
    Parameters
    ----------
    lambda_0 : np.ndarray
        Eigenvalues from standard cointegration (m=0), shape (r,)
    lambda_m : np.ndarray
        Eigenvalues from TV cointegration, shape (r,)
    T : int
        Number of observations
    r : int
        Cointegration rank
        
    Returns
    -------
    float
        LR test statistic
        
    Notes
    -----
    Under H0 (time-invariant cointegration), LR ~ χ²(m*k*r)
    """
    # Ensure we have r eigenvalues
    lambda_0_r = lambda_0[:r]
    lambda_m_r = lambda_m[:r]
    
    # Clip eigenvalues to avoid log(0) or log(negative)
    lambda_0_r = np.clip(lambda_0_r, 0, 1 - 1e-15)
    lambda_m_r = np.clip(lambda_m_r, 0, 1 - 1e-15)
    
    # Compute LR statistic
    log_ratios = np.log((1 - lambda_0_r) / (1 - lambda_m_r))
    lr_statistic = T * np.sum(log_ratios)
    
    return lr_statistic


def compute_johansen_trace_statistic(eigenvalues: np.ndarray, T: int, r: int) -> float:
    """
    Compute Johansen's trace statistic for cointegration rank testing.
    
    trace(r) = -T * sum_{j=r+1}^{k} ln(1 - λ_j)
    
    Parameters
    ----------
    eigenvalues : np.ndarray
        All eigenvalues from standard cointegration, shape (k,)
    T : int
        Number of observations
    r : int
        Hypothesized cointegration rank
        
    Returns
    -------
    float
        Trace statistic for testing H0: rank <= r
    """
    k = len(eigenvalues)
    if r >= k:
        return 0.0
    
    lambda_rest = eigenvalues[r:k]
    lambda_rest = np.clip(lambda_rest, 0, 1 - 1e-15)
    
    trace_stat = -T * np.sum(np.log(1 - lambda_rest))
    
    return trace_stat


def estimate_alpha_beta(
    delta_Y: np.ndarray,
    Y_m: np.ndarray,
    X: Optional[np.ndarray],
    S: Dict[str, np.ndarray],
    eigenvectors: np.ndarray,
    r: int,
    include_intercept: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Estimate alpha and beta matrices after solving eigenvalue problem.
    
    Parameters
    ----------
    delta_Y : np.ndarray
        Differenced data of shape (T_eff, k)
    Y_m : np.ndarray
        Extended lagged data of shape (T_eff, (m+1)*k)
    X : np.ndarray or None
        Additional regressors
    S : dict
        Dictionary of S matrices
    eigenvectors : np.ndarray
        Eigenvectors from generalized eigenvalue problem
    r : int
        Cointegration rank
    include_intercept : bool
        Whether intercept was included
        
    Returns
    -------
    alpha : np.ndarray
        Adjustment matrix of shape (k, r)
    beta : np.ndarray
        Cointegrating vectors of shape ((m+1)*k, r)
    """
    T_eff = delta_Y.shape[0]
    k = delta_Y.shape[1]
    
    # xi = beta (normalized eigenvectors)
    xi = eigenvectors[:, :r]
    
    # Normalize: xi' * S11 * xi = I_r
    norm = xi.T @ S['S11'] @ xi
    try:
        norm_sqrt_inv = linalg.sqrtm(np.linalg.inv(norm))
    except:
        norm_sqrt_inv = np.eye(r)
    xi = xi @ norm_sqrt_inv.real
    
    beta = xi
    
    # Compute alpha: α = S01 * β
    alpha = S['S01'] @ beta
    
    return alpha, beta


def stabilize_matrix(M: np.ndarray, eps: float = 1e-10) -> np.ndarray:
    """
    Add small regularization to a matrix for numerical stability.
    
    Parameters
    ----------
    M : np.ndarray
        Input matrix
    eps : float
        Regularization parameter
        
    Returns
    -------
    np.ndarray
        Regularized matrix
    """
    return M + eps * np.eye(M.shape[0])
