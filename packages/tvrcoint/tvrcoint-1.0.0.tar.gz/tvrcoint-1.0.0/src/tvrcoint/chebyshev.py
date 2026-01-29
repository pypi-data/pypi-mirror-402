"""
Chebyshev Time Polynomials

This module implements Chebyshev time polynomials as defined in 
Bierens & Martins (2010) for approximating time-varying cointegrating vectors.

The Chebyshev polynomials are defined as:
    P_{0,T}(t) = 1
    P_{i,T}(t) = sqrt(2) * cos(i*pi*(t-0.5)/T)  for i = 1, 2, 3, ...

They are orthonormal in the sense that:
    (1/T) * sum_{t=1}^{T} P_{i,T}(t) * P_{j,T}(t) = 1 if i=j, 0 otherwise
"""

import numpy as np
from typing import Tuple, Optional


def chebyshev_poly(i: int, t: int, T: int) -> float:
    """
    Compute the Chebyshev time polynomial P_{i,T}(t).
    
    Parameters
    ----------
    i : int
        Order of the polynomial (i >= 0)
    t : int
        Time index (1 <= t <= T)
    T : int
        Total number of observations
        
    Returns
    -------
    float
        Value of P_{i,T}(t)
        
    Examples
    --------
    >>> chebyshev_poly(0, 1, 100)
    1.0
    >>> chebyshev_poly(1, 50, 100)  # Should be close to 0
    """
    if i < 0:
        raise ValueError("Order i must be non-negative")
    if t < 1 or t > T:
        raise ValueError(f"Time t must be in [1, T], got t={t}, T={T}")
    
    if i == 0:
        return 1.0
    else:
        return np.sqrt(2) * np.cos(i * np.pi * (t - 0.5) / T)


def chebyshev_polynomials(m: int, T: int) -> np.ndarray:
    """
    Compute Chebyshev polynomials P_{i,T}(t) for i=0,...,m and t=1,...,T.
    
    Parameters
    ----------
    m : int
        Maximum order of polynomials (m >= 0)
    T : int
        Total number of observations
        
    Returns
    -------
    np.ndarray
        Array of shape (m+1, T) where element [i, t-1] is P_{i,T}(t)
        
    Examples
    --------
    >>> P = chebyshev_polynomials(2, 100)
    >>> P.shape
    (3, 100)
    """
    if m < 0:
        raise ValueError("Order m must be non-negative")
    if T < 1:
        raise ValueError("T must be positive")
        
    P = np.zeros((m + 1, T))
    
    for i in range(m + 1):
        for t in range(1, T + 1):
            P[i, t - 1] = chebyshev_poly(i, t, T)
            
    return P


def chebyshev_matrix(Y: np.ndarray, m: int) -> np.ndarray:
    """
    Construct the extended lagged variable matrix Y^{(m)}_{t-1}.
    
    For each observation t, Y^{(m)}_{t-1} is defined as:
        Y^{(m)}_{t-1} = (Y'_{t-1}, P_{1,T}(t)*Y'_{t-1}, ..., P_{m,T}(t)*Y'_{t-1})'
    
    This is an (m+1)*k dimensional vector for each t.
    
    Parameters
    ----------
    Y : np.ndarray
        Original data matrix of shape (T, k), where T is the number of
        observations and k is the number of variables
    m : int
        Order of Chebyshev polynomial expansion (m >= 0)
        
    Returns
    -------
    np.ndarray
        Extended lagged variable matrix of shape (T-1, (m+1)*k)
        Row t corresponds to Y^{(m)}_{t} for t = 1, ..., T-1
        (to be used as regressors for observations 2, ..., T)
        
    Examples
    --------
    >>> Y = np.random.randn(100, 3)
    >>> Y_m = chebyshev_matrix(Y, 2)
    >>> Y_m.shape
    (99, 9)  # (T-1, (m+1)*k) = (99, 3*3)
    """
    T, k = Y.shape
    
    if m < 0:
        raise ValueError("Order m must be non-negative")
    if T < 2:
        raise ValueError("Need at least 2 observations")
        
    # Compute Chebyshev polynomials
    P = chebyshev_polynomials(m, T)
    
    # Initialize output matrix
    # We use t = 2, ..., T as the "current" observations
    # So Y_{t-1} for t = 2, ..., T gives us T-1 lagged observations
    T_eff = T - 1  # Effective number of observations
    Y_m = np.zeros((T_eff, (m + 1) * k))
    
    for t_idx in range(T_eff):
        t = t_idx + 2  # t = 2, ..., T (current observation index, 1-based)
        Y_lag = Y[t - 2, :]  # Y_{t-1}
        
        for i in range(m + 1):
            P_it = P[i, t - 1]  # P_{i,T}(t) for the current observation
            Y_m[t_idx, i * k:(i + 1) * k] = P_it * Y_lag
            
    return Y_m


def verify_orthonormality(m: int, T: int, tol: float = 1e-10) -> bool:
    """
    Verify that Chebyshev polynomials satisfy orthonormality.
    
    (1/T) * sum_{t=1}^{T} P_{i,T}(t) * P_{j,T}(t) = delta_{ij}
    
    Parameters
    ----------
    m : int
        Maximum order to check
    T : int
        Number of observations
    tol : float
        Tolerance for checking equality
        
    Returns
    -------
    bool
        True if orthonormality is satisfied within tolerance
    """
    P = chebyshev_polynomials(m, T)
    
    # Compute (1/T) * P @ P'
    inner_product = (1 / T) * P @ P.T
    
    # Should be identity matrix
    identity = np.eye(m + 1)
    
    return np.allclose(inner_product, identity, atol=tol)


def fourier_coefficients(beta_t: np.ndarray, T: int, m: int) -> np.ndarray:
    """
    Compute Fourier (Chebyshev) coefficients for a time-varying beta.
    
    Given beta_t for t = 1, ..., T, compute:
        xi_i = (1/T) * sum_{t=1}^{T} beta_t * P_{i,T}(t)
    
    Parameters
    ----------
    beta_t : np.ndarray
        Time-varying parameter matrix of shape (T, k, r) or (T, k) for r=1
    T : int
        Number of observations
    m : int
        Order of approximation
        
    Returns
    -------
    np.ndarray
        Fourier coefficients xi of shape (m+1, k, r) or (m+1, k)
    """
    P = chebyshev_polynomials(m, T)
    
    if beta_t.ndim == 2:
        # Shape (T, k)
        _, k = beta_t.shape
        xi = np.zeros((m + 1, k))
        for i in range(m + 1):
            xi[i, :] = (1 / T) * np.sum(beta_t * P[i, :, np.newaxis], axis=0)
    else:
        # Shape (T, k, r)
        _, k, r = beta_t.shape
        xi = np.zeros((m + 1, k, r))
        for i in range(m + 1):
            xi[i, :, :] = (1 / T) * np.sum(
                beta_t * P[i, :, np.newaxis, np.newaxis], axis=0
            )
            
    return xi


def reconstruct_beta(xi: np.ndarray, T: int) -> np.ndarray:
    """
    Reconstruct time-varying beta from Fourier coefficients.
    
    beta_t = sum_{i=0}^{m} xi_i * P_{i,T}(t)
    
    Parameters
    ----------
    xi : np.ndarray
        Fourier coefficients of shape (m+1, k, r) or (m+1, k)
    T : int
        Number of observations
        
    Returns
    -------
    np.ndarray
        Reconstructed beta_t of shape (T, k, r) or (T, k)
    """
    m_plus_1 = xi.shape[0]
    m = m_plus_1 - 1
    
    P = chebyshev_polynomials(m, T)
    
    if xi.ndim == 2:
        # Shape (m+1, k)
        k = xi.shape[1]
        beta_t = np.zeros((T, k))
        for t in range(T):
            for i in range(m + 1):
                beta_t[t, :] += xi[i, :] * P[i, t]
    else:
        # Shape (m+1, k, r)
        k, r = xi.shape[1], xi.shape[2]
        beta_t = np.zeros((T, k, r))
        for t in range(T):
            for i in range(m + 1):
                beta_t[t, :, :] += xi[i, :, :] * P[i, t]
                
    return beta_t
