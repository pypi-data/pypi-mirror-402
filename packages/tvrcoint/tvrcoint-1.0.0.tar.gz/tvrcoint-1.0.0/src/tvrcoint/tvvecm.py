"""
Time-Varying Vector Error Correction Model (TV-VECM)

This module implements the TV-VECM estimation as described in 
Bierens & Martins (2010).

The TV-VECM(p) model:
    ΔY_t = μ + α * β'_t * Y_{t-1} + Σ_{j=1}^{p-1} Γ_j * ΔY_{t-j} + ε_t

where β_t is the time-varying cointegrating vector approximated by:
    β_t = Σ_{i=0}^{m} ξ_i * P_{i,T}(t)

and P_{i,T}(t) are Chebyshev time polynomials.
"""

import numpy as np
from scipy import linalg
from typing import Optional, Tuple, Dict
from dataclasses import dataclass

from .chebyshev import chebyshev_matrix, chebyshev_polynomials, reconstruct_beta
from .matrices import compute_s_matrices, solve_eigenvalue_problem, estimate_alpha_beta
from .utils import create_delta_Y_and_X, check_data


@dataclass
class TVVECMResults:
    """
    Results container for TV-VECM estimation.
    
    Attributes
    ----------
    alpha : np.ndarray
        Adjustment matrix (k x r)
    xi : np.ndarray
        Chebyshev coefficients for β ((m+1)*k x r)
    beta : np.ndarray
        Standard cointegrating vectors if m=0, or first k rows of xi
    gamma : np.ndarray
        Short-run dynamics matrices
    mu : np.ndarray
        Intercept vector
    residuals : np.ndarray
        Model residuals (T_eff x k)
    omega : np.ndarray
        Residual covariance matrix (k x k)
    eigenvalues : np.ndarray
        Ordered eigenvalues from estimation
    log_likelihood : float
        Log-likelihood value
    T : int
        Number of observations used
    k : int
        Number of variables
    r : int
        Cointegration rank
    m : int
        Chebyshev polynomial order
    p : int
        VAR lag order
    """
    alpha: np.ndarray
    xi: np.ndarray
    beta: np.ndarray
    gamma: Optional[np.ndarray]
    mu: Optional[np.ndarray]
    residuals: np.ndarray
    omega: np.ndarray
    eigenvalues: np.ndarray
    log_likelihood: float
    T: int
    k: int
    r: int
    m: int
    p: int
    
    def beta_t(self, T: Optional[int] = None) -> np.ndarray:
        """
        Reconstruct time-varying β_t from Chebyshev coefficients.
        
        Parameters
        ----------
        T : int, optional
            Number of time points (default: self.T)
            
        Returns
        -------
        np.ndarray
            Time-varying β of shape (T, k, r)
        """
        if T is None:
            T = self.T
        
        k = self.k
        r = self.r
        m = self.m
        
        # Reshape xi to (m+1, k, r)
        xi_reshaped = np.zeros((m + 1, k, r))
        for i in range(m + 1):
            xi_reshaped[i, :, :] = self.xi[i * k:(i + 1) * k, :]
        
        return reconstruct_beta(xi_reshaped, T)


class TVVECM:
    """
    Time-Varying Vector Error Correction Model.
    
    This class implements the TV-VECM estimation using Chebyshev time 
    polynomials as described in Bierens & Martins (2010).
    
    Parameters
    ----------
    None
    
    Examples
    --------
    >>> import numpy as np
    >>> from tvrcoint import TVVECM
    >>> 
    >>> # Simulate some data
    >>> np.random.seed(42)
    >>> T, k = 200, 3
    >>> Y = np.cumsum(np.random.randn(T, k), axis=0)
    >>> 
    >>> # Fit TV-VECM
    >>> model = TVVECM()
    >>> results = model.fit(Y, r=1, m=2, p=2)
    >>> 
    >>> print(f"Log-likelihood: {results.log_likelihood:.2f}")
    """
    
    def __init__(self):
        self.results_ = None
    
    def fit(
        self,
        Y: np.ndarray,
        r: int,
        m: int = 0,
        p: int = 1,
        include_drift: bool = True
    ) -> TVVECMResults:
        """
        Estimate the TV-VECM model.
        
        Parameters
        ----------
        Y : np.ndarray
            Data matrix of shape (T, k)
        r : int
            Cointegration rank (1 <= r < k)
        m : int
            Order of Chebyshev polynomial expansion (m >= 0)
            m = 0 corresponds to standard VECM
        p : int
            VAR lag order (p >= 1)
        include_drift : bool
            Whether to include drift/intercept (default True)
            
        Returns
        -------
        TVVECMResults
            Estimation results
            
        Raises
        ------
        ValueError
            If parameters are invalid
        """
        # Validate inputs
        T, k = check_data(Y)
        
        if r < 1 or r >= k:
            raise ValueError(f"Cointegration rank r must satisfy 1 <= r < k, got r={r}, k={k}")
        if m < 0:
            raise ValueError(f"Chebyshev order m must be non-negative, got m={m}")
        if p < 1:
            raise ValueError(f"VAR lag order p must be >= 1, got p={p}")
        if T < k + p + m + 10:
            raise ValueError(f"Not enough observations: T={T}, need at least {k + p + m + 10}")
        
        # Create data matrices
        delta_Y, Y_lag, X_base = create_delta_Y_and_X(Y, p, include_intercept=False)
        T_eff = delta_Y.shape[0]
        
        # Create extended lagged matrix Y^{(m)}_{t-1}
        # We need to properly construct this for the effective sample
        Y_m = self._construct_extended_lag(Y, m, p)
        
        # Build X (lagged differences, and optionally intercept)
        if X_base.shape[1] > 0 or include_drift:
            if include_drift:
                X = np.column_stack([np.ones(T_eff), X_base]) if X_base.shape[1] > 0 else np.ones((T_eff, 1))
            else:
                X = X_base if X_base.shape[1] > 0 else None
        else:
            X = None
        
        # Compute S matrices
        S = compute_s_matrices(delta_Y, Y_m, X_base, include_intercept=include_drift)
        
        # Solve generalized eigenvalue problem
        eigenvalues, eigenvectors = solve_eigenvalue_problem(
            S['S11'], S['S10'], S['S00'], S['S01'], r=None
        )
        
        # Estimate alpha and xi (beta with Chebyshev expansion)
        alpha, xi = estimate_alpha_beta(
            delta_Y, Y_m, X_base, S, eigenvectors, r, include_intercept=include_drift
        )
        
        # Extract standard beta (first k rows of xi)
        beta = xi[:k, :]
        
        # Compute residuals
        residuals = self._compute_residuals(
            delta_Y, Y_m, X, alpha, xi, include_drift
        )
        
        # Compute residual covariance
        omega = (1 / T_eff) * residuals.T @ residuals
        
        # Compute log-likelihood
        log_likelihood = self._compute_log_likelihood(residuals, omega, T_eff)
        
        # Estimate Gamma matrices (short-run dynamics)
        gamma = self._estimate_gamma(delta_Y, Y_m, X, alpha, xi, p, k, include_drift)
        
        # Estimate intercept
        mu = None
        if include_drift:
            mu = self._estimate_mu(delta_Y, Y_m, X, alpha, xi, gamma, k, p)
        
        self.results_ = TVVECMResults(
            alpha=alpha,
            xi=xi,
            beta=beta,
            gamma=gamma,
            mu=mu,
            residuals=residuals,
            omega=omega,
            eigenvalues=eigenvalues,
            log_likelihood=log_likelihood,
            T=T_eff,
            k=k,
            r=r,
            m=m,
            p=p
        )
        
        return self.results_
    
    def _construct_extended_lag(self, Y: np.ndarray, m: int, p: int) -> np.ndarray:
        """
        Construct the extended lagged matrix Y^{(m)}_{t-1} for effective sample.
        
        For t = p+1, ..., T, we compute:
            Y^{(m)}_{t-1} = (Y'_{t-1}, P_{1,T}(t)*Y'_{t-1}, ..., P_{m,T}(t)*Y'_{t-1})'
        """
        T, k = Y.shape
        T_eff = T - p
        
        # Get Chebyshev polynomials
        P = chebyshev_polynomials(m, T)
        
        # Build extended lag matrix
        Y_m = np.zeros((T_eff, (m + 1) * k))
        
        for t_idx in range(T_eff):
            t = t_idx + p + 1  # t = p+1, ..., T (1-based)
            Y_lag = Y[t - 2, :]  # Y_{t-1} (0-based indexing: t-2)
            
            for i in range(m + 1):
                P_it = P[i, t - 1]  # P_{i,T}(t)
                Y_m[t_idx, i * k:(i + 1) * k] = P_it * Y_lag
        
        return Y_m
    
    def _compute_residuals(
        self,
        delta_Y: np.ndarray,
        Y_m: np.ndarray,
        X: Optional[np.ndarray],
        alpha: np.ndarray,
        xi: np.ndarray,
        include_drift: bool
    ) -> np.ndarray:
        """Compute model residuals."""
        # ε = ΔY - α * ξ' * Y^{(m)}_{t-1} - Γ * X
        fitted = delta_Y @ np.zeros((delta_Y.shape[1], 1))  # placeholder
        error_correction = Y_m @ xi @ alpha.T
        
        if X is not None and X.shape[1] > 0:
            # Regress delta_Y - error_correction on X to get residuals
            ec_residual = delta_Y - error_correction
            
            # OLS for remaining parameters
            X_pinv = np.linalg.pinv(X)
            gamma_mu = X_pinv @ ec_residual
            fitted_x = X @ gamma_mu
            
            residuals = ec_residual - fitted_x
        else:
            residuals = delta_Y - error_correction
        
        return residuals
    
    def _compute_log_likelihood(
        self,
        residuals: np.ndarray,
        omega: np.ndarray,
        T: int
    ) -> float:
        """Compute log-likelihood value."""
        k = residuals.shape[1]
        
        # Log-likelihood for multivariate normal
        try:
            sign, logdet = np.linalg.slogdet(omega)
            if sign <= 0:
                logdet = np.log(np.abs(np.linalg.det(omega)) + 1e-15)
        except:
            logdet = 0
        
        ll = -0.5 * T * k * np.log(2 * np.pi) - 0.5 * T * logdet - 0.5 * T * k
        
        return ll
    
    def _estimate_gamma(
        self,
        delta_Y: np.ndarray,
        Y_m: np.ndarray,
        X: Optional[np.ndarray],
        alpha: np.ndarray,
        xi: np.ndarray,
        p: int,
        k: int,
        include_drift: bool
    ) -> Optional[np.ndarray]:
        """Estimate short-run dynamics Γ matrices."""
        if p <= 1:
            return None
        
        # After removing error correction, regress on lagged differences
        ec_residual = delta_Y - Y_m @ xi @ alpha.T
        
        if X is not None and X.shape[1] > 0:
            # Extract lagged difference part (excluding intercept if present)
            if include_drift:
                X_gamma = X[:, 1:]
            else:
                X_gamma = X
            
            if X_gamma.shape[1] > 0:
                gamma_vec = np.linalg.lstsq(X_gamma, ec_residual, rcond=None)[0]
                return gamma_vec
        
        return None
    
    def _estimate_mu(
        self,
        delta_Y: np.ndarray,
        Y_m: np.ndarray,
        X: Optional[np.ndarray],
        alpha: np.ndarray,
        xi: np.ndarray,
        gamma: Optional[np.ndarray],
        k: int,
        p: int
    ) -> np.ndarray:
        """Estimate intercept/drift term."""
        ec_residual = delta_Y - Y_m @ xi @ alpha.T
        
        if gamma is not None and X is not None:
            X_gamma = X[:, 1:] if X.shape[1] > 1 else None
            if X_gamma is not None and X_gamma.shape[1] > 0:
                ec_residual = ec_residual - X_gamma @ gamma
        
        mu = np.mean(ec_residual, axis=0)
        return mu
    
    @property
    def results(self) -> Optional[TVVECMResults]:
        """Get estimation results."""
        return self.results_


def fit_vecm(
    Y: np.ndarray,
    r: int,
    p: int = 1,
    include_drift: bool = True
) -> TVVECMResults:
    """
    Convenience function for fitting standard VECM (m=0).
    
    Parameters
    ----------
    Y : np.ndarray
        Data matrix of shape (T, k)
    r : int
        Cointegration rank
    p : int
        VAR lag order
    include_drift : bool
        Whether to include drift
        
    Returns
    -------
    TVVECMResults
        Estimation results
    """
    model = TVVECM()
    return model.fit(Y, r=r, m=0, p=p, include_drift=include_drift)


def fit_tvvecm(
    Y: np.ndarray,
    r: int,
    m: int,
    p: int = 1,
    include_drift: bool = True
) -> TVVECMResults:
    """
    Convenience function for fitting TV-VECM.
    
    Parameters
    ----------
    Y : np.ndarray
        Data matrix of shape (T, k)
    r : int
        Cointegration rank
    m : int
        Chebyshev polynomial order
    p : int
        VAR lag order
    include_drift : bool
        Whether to include drift
        
    Returns
    -------
    TVVECMResults
        Estimation results
    """
    model = TVVECM()
    return model.fit(Y, r=r, m=m, p=p, include_drift=include_drift)
