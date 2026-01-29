"""
Bootstrap Tests for Time-Varying Cointegration

This module implements the Wild and i.i.d. Bootstrap tests for time-varying
cointegration as described in Martins (2015).

The bootstrap tests provide more accurate finite-sample inference compared
to the asymptotic chi-square distribution, especially for:
- Small to medium sample sizes
- Large values of m (Chebyshev polynomial order)
- Conditionally heteroskedastic errors (Wild bootstrap preferred)

Bootstrap Algorithms:
1. Wild Bootstrap: ε^b_t = ε̂_t * w_t where w_t ~ N(0,1)
2. i.i.d. Bootstrap: ε^b_t drawn with replacement from ε̂_t

Both unrestricted (UR) and restricted (R) residual approaches are implemented.
"""

import numpy as np
from scipy import stats
from typing import Optional, Tuple, Literal
from dataclasses import dataclass
import warnings

from .tvvecm import TVVECM, TVVECMResults
from .lr_test import TVCTest, TVCTestResults
from .chebyshev import chebyshev_polynomials
from .matrices import compute_s_matrices, solve_eigenvalue_problem
from .utils import check_data, create_delta_Y_and_X


@dataclass
class BootstrapTVCTestResults:
    """
    Results container for Bootstrap TVC test.
    
    Attributes
    ----------
    statistic : float
        Original LR test statistic
    pvalue_asymptotic : float
        P-value from asymptotic χ² distribution
    pvalue_bootstrap : float
        Bootstrap p-value
    df : int
        Degrees of freedom (m * k * r)
    m : int
        Chebyshev polynomial order
    k : int
        Number of variables
    r : int
        Cointegration rank
    p : int
        VAR lag order
    T : int
        Effective sample size
    B : int
        Number of bootstrap replications
    method : str
        Bootstrap method ('wild' or 'iid')
    restricted : bool
        Whether restricted residuals were used
    bootstrap_statistics : np.ndarray
        Array of bootstrap LR statistics
    critical_values : dict
        Bootstrap critical values at 10%, 5%, 1% levels
    """
    statistic: float
    pvalue_asymptotic: float
    pvalue_bootstrap: float
    df: int
    m: int
    k: int
    r: int
    p: int
    T: int
    B: int
    method: str
    restricted: bool
    bootstrap_statistics: np.ndarray
    critical_values: dict
    
    def summary(self) -> str:
        """
        Generate a summary of the test results.
        
        Returns
        -------
        str
            Formatted summary string
        """
        method_label = "Wild Bootstrap" if self.method == 'wild' else "i.i.d. Bootstrap"
        residual_label = "Restricted" if self.restricted else "Unrestricted"
        
        lines = [
            "",
            "=" * 70,
            f"Bootstrap Time-Varying Cointegration Test ({method_label})",
            "Martins (2015)",
            "=" * 70,
            "",
            "Model Specification:",
            f"  Number of variables (k):        {self.k}",
            f"  Cointegration rank (r):         {self.r}",
            f"  Chebyshev polynomial order (m): {self.m}",
            f"  VAR lag order (p):              {self.p}",
            f"  Effective sample size (T):      {self.T}",
            "",
            "Bootstrap Settings:",
            f"  Method:               {method_label}",
            f"  Residuals:            {residual_label}",
            f"  Number of replications (B): {self.B}",
            "",
            "Hypothesis:",
            "  H0: Time-invariant cointegration (β_t = β for all t)",
            "  H1: Time-varying cointegration",
            "",
            "Test Results:",
            f"  LR statistic:           {self.statistic:.4f}",
            f"  Degrees of freedom:     {self.df}",
            f"  Asymptotic p-value:     {self.pvalue_asymptotic:.4f}",
            f"  Bootstrap p-value:      {self.pvalue_bootstrap:.4f}",
            "",
            "Bootstrap Critical Values:",
            f"  10% level: {self.critical_values.get(0.10, 'N/A'):.4f}",
            f"   5% level: {self.critical_values.get(0.05, 'N/A'):.4f}",
            f"   1% level: {self.critical_values.get(0.01, 'N/A'):.4f}",
            "",
            "Conclusion (using bootstrap p-value):",
        ]
        
        if self.pvalue_bootstrap < 0.01:
            lines.append("  Strong evidence against H0 (p < 0.01) ***")
            lines.append("  → Evidence of TIME-VARYING cointegration")
        elif self.pvalue_bootstrap < 0.05:
            lines.append("  Evidence against H0 at 5% level **")
            lines.append("  → Evidence of TIME-VARYING cointegration")
        elif self.pvalue_bootstrap < 0.10:
            lines.append("  Weak evidence against H0 at 10% level *")
            lines.append("  → Mixed evidence")
        else:
            lines.append("  Cannot reject H0")
            lines.append("  → Evidence of TIME-INVARIANT cointegration")
        
        lines.extend([
            "",
            "=" * 70,
            ""
        ])
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return (f"BootstrapTVCTestResults(statistic={self.statistic:.4f}, "
                f"pvalue_bootstrap={self.pvalue_bootstrap:.4f}, method='{self.method}')")


class BootstrapTVCTest:
    """
    Bootstrap Test for Time-Varying Cointegration.
    
    Implements Wild and i.i.d. bootstrap tests from Martins (2015).
    The bootstrap tests provide accurate size in finite samples,
    unlike the asymptotic chi-square distribution which tends to
    over-reject the null hypothesis.
    
    Examples
    --------
    >>> import numpy as np
    >>> from tvrcoint import BootstrapTVCTest
    >>> 
    >>> # Generate some data
    >>> np.random.seed(42)
    >>> T, k = 200, 3
    >>> Y = np.cumsum(np.random.randn(T, k), axis=0)
    >>> 
    >>> # Perform bootstrap test
    >>> test = BootstrapTVCTest()
    >>> results = test.test(Y, r=1, m=5, p=1, method='wild', B=399)
    >>> 
    >>> print(results.summary())
    """
    
    def __init__(self):
        self.results_ = None
    
    def test(
        self,
        Y: np.ndarray,
        r: int,
        m: int,
        p: int = 1,
        method: Literal['wild', 'iid'] = 'wild',
        restricted: bool = False,
        B: int = 399,
        include_drift: bool = True,
        seed: Optional[int] = None
    ) -> BootstrapTVCTestResults:
        """
        Perform the bootstrap TVC test.
        
        Parameters
        ----------
        Y : np.ndarray
            Data matrix of shape (T, k)
        r : int
            Cointegration rank (1 <= r < k)
        m : int
            Chebyshev polynomial order (m >= 1)
        p : int
            VAR lag order (p >= 1)
        method : str
            Bootstrap method: 'wild' or 'iid'
        restricted : bool
            If True, use restricted residuals (from m=0 model)
            If False, use unrestricted residuals (from m>0 model)
        B : int
            Number of bootstrap replications (default: 399)
        include_drift : bool
            Whether to include drift term
        seed : int, optional
            Random seed for reproducibility
            
        Returns
        -------
        BootstrapTVCTestResults
            Test results including bootstrap p-value and critical values
        """
        # Set random seed
        if seed is not None:
            np.random.seed(seed)
        
        # Validate inputs
        T_full, k = check_data(Y)
        
        if r < 1 or r >= k:
            raise ValueError(f"Cointegration rank r must satisfy 1 <= r < k, got r={r}, k={k}")
        if m < 1:
            raise ValueError(f"Chebyshev order m must be >= 1 for testing, got m={m}")
        if p < 1:
            raise ValueError(f"VAR lag order p must be >= 1, got p={p}")
        if method not in ['wild', 'iid']:
            raise ValueError(f"method must be 'wild' or 'iid', got '{method}'")
        if B < 100:
            warnings.warn("B < 100 may give unreliable results. Recommend B >= 399.")
        
        # First, perform the original LR test
        tvc_test = TVCTest()
        original_results = tvc_test.test(Y, r, m, p, include_drift)
        
        # Get parameter estimates under H0 (standard cointegration)
        model_h0 = original_results.model_0
        
        # Get residuals
        if restricted:
            # Use residuals from H0 model
            residuals = model_h0.residuals
            alpha_hat = model_h0.alpha
            beta_hat = model_h0.beta
            gamma_hat = model_h0.gamma
            mu_hat = model_h0.mu
        else:
            # Use residuals from Ha model (unrestricted)
            model_ha = original_results.model_m
            residuals = model_ha.residuals
            # But generate data under H0 using H0 parameters
            alpha_hat = model_h0.alpha
            beta_hat = model_h0.beta
            gamma_hat = model_h0.gamma
            mu_hat = model_h0.mu
        
        T_eff = residuals.shape[0]
        
        # Bootstrap loop
        bootstrap_statistics = np.zeros(B)
        
        for b in range(B):
            # Generate bootstrap pseudo-disturbances
            if method == 'wild':
                eps_b = self._wild_bootstrap_disturbances(residuals)
            else:
                eps_b = self._iid_bootstrap_disturbances(residuals)
            
            # Generate bootstrap sample
            Y_b = self._generate_bootstrap_sample(
                Y, eps_b, alpha_hat, beta_hat, gamma_hat, mu_hat, p, include_drift
            )
            
            # Compute bootstrap LR statistic
            try:
                lr_b = self._compute_bootstrap_lr(Y_b, r, m, p, include_drift)
                bootstrap_statistics[b] = lr_b
            except Exception as e:
                # If bootstrap sample causes issues, use NaN
                bootstrap_statistics[b] = np.nan
        
        # Remove any NaN values
        valid_stats = bootstrap_statistics[~np.isnan(bootstrap_statistics)]
        if len(valid_stats) < B * 0.5:
            warnings.warn(f"More than 50% of bootstrap samples failed. Results may be unreliable.")
        
        # Compute bootstrap p-value
        pvalue_bootstrap = np.mean(valid_stats > original_results.statistic)
        
        # Compute critical values
        critical_values = {
            0.10: np.nanpercentile(valid_stats, 90),
            0.05: np.nanpercentile(valid_stats, 95),
            0.01: np.nanpercentile(valid_stats, 99)
        }
        
        self.results_ = BootstrapTVCTestResults(
            statistic=original_results.statistic,
            pvalue_asymptotic=original_results.pvalue,
            pvalue_bootstrap=pvalue_bootstrap,
            df=original_results.df,
            m=m,
            k=k,
            r=r,
            p=p,
            T=T_eff,
            B=B,
            method=method,
            restricted=restricted,
            bootstrap_statistics=bootstrap_statistics,
            critical_values=critical_values
        )
        
        return self.results_
    
    def _wild_bootstrap_disturbances(self, residuals: np.ndarray) -> np.ndarray:
        """
        Generate wild bootstrap pseudo-disturbances.
        
        ε^b_t = ε̂_t * w_t where w_t ~ N(0,1) (Rademacher could also be used)
        """
        T_eff, k = residuals.shape
        w = np.random.randn(T_eff, 1)  # Same w for all variables at time t
        return residuals * w
    
    def _iid_bootstrap_disturbances(self, residuals: np.ndarray) -> np.ndarray:
        """
        Generate i.i.d. bootstrap pseudo-disturbances.
        
        ε^b_t drawn with replacement from centered residuals.
        """
        T_eff, k = residuals.shape
        
        # Center residuals
        residuals_centered = residuals - np.mean(residuals, axis=0)
        
        # Draw with replacement
        indices = np.random.choice(T_eff, size=T_eff, replace=True)
        return residuals_centered[indices]
    
    def _generate_bootstrap_sample(
        self,
        Y_original: np.ndarray,
        eps_b: np.ndarray,
        alpha: np.ndarray,
        beta: np.ndarray,
        gamma: Optional[np.ndarray],
        mu: Optional[np.ndarray],
        p: int,
        include_drift: bool
    ) -> np.ndarray:
        """
        Generate bootstrap sample recursively.
        
        ΔY^b_t = μ̂ + α̂β̂'Y^b_{t-1} + Σ Γ̂_j ΔY^b_{t-j} + ε^b_t
        """
        T_full, k = Y_original.shape
        T_eff = eps_b.shape[0]
        
        # Initialize bootstrap sample with original initial values
        Y_b = np.zeros_like(Y_original)
        Y_b[:p] = Y_original[:p]  # Use original initial values
        
        # Recursively generate
        for t in range(p, T_full):
            t_eff = t - p  # Index in eps_b
            
            if t_eff >= T_eff:
                break
            
            delta_Y_t = np.zeros(k)
            
            # Error correction term: α β' Y^b_{t-1}
            ec_term = alpha @ beta.T @ Y_b[t - 1]
            delta_Y_t += ec_term
            
            # Intercept
            if include_drift and mu is not None:
                delta_Y_t += mu
            
            # Short-run dynamics: Σ Γ_j ΔY^b_{t-j}
            if gamma is not None and p > 1:
                for j in range(1, p):
                    if t - j >= 1:
                        delta_Y_lag = Y_b[t - j] - Y_b[t - j - 1]
                        # Gamma is stored as (k*(p-1), k) or similar
                        if gamma.shape[0] >= j * k:
                            gamma_j = gamma[(j - 1) * k:j * k, :].T
                            delta_Y_t += gamma_j @ delta_Y_lag
            
            # Bootstrap innovation
            delta_Y_t += eps_b[t_eff]
            
            # Update Y^b_t
            Y_b[t] = Y_b[t - 1] + delta_Y_t
        
        return Y_b
    
    def _compute_bootstrap_lr(
        self,
        Y_b: np.ndarray,
        r: int,
        m: int,
        p: int,
        include_drift: bool
    ) -> float:
        """
        Compute LR statistic for bootstrap sample.
        """
        try:
            # Fit H0 model (m=0)
            model_h0 = TVVECM()
            results_0 = model_h0.fit(Y_b, r=r, m=0, p=p, include_drift=include_drift)
            
            # Fit Ha model (m>0)
            model_ha = TVVECM()
            results_m = model_ha.fit(Y_b, r=r, m=m, p=p, include_drift=include_drift)
            
            # Compute LR statistic
            lambda_0 = results_0.eigenvalues[:r]
            lambda_m = results_m.eigenvalues[:r]
            
            T_eff = results_0.T
            
            # Clip eigenvalues
            eps = 1e-15
            lambda_0 = np.clip(lambda_0, eps, 1 - eps)
            lambda_m = np.clip(lambda_m, eps, 1 - eps)
            
            log_ratios = np.log((1 - lambda_0) / (1 - lambda_m))
            lr_stat = T_eff * np.sum(log_ratios)
            
            return max(0, lr_stat)
        except Exception:
            return np.nan
    
    @property
    def results(self) -> Optional[BootstrapTVCTestResults]:
        """Get test results."""
        return self.results_


def bootstrap_tvc_test(
    Y: np.ndarray,
    r: int,
    m: int,
    p: int = 1,
    method: str = 'wild',
    restricted: bool = False,
    B: int = 399,
    include_drift: bool = True,
    seed: Optional[int] = None
) -> BootstrapTVCTestResults:
    """
    Convenience function for bootstrap TVC test.
    
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
    method : str
        Bootstrap method: 'wild' or 'iid'
    restricted : bool
        Use restricted residuals
    B : int
        Number of bootstrap replications
    include_drift : bool
        Include drift term
    seed : int, optional
        Random seed
        
    Returns
    -------
    BootstrapTVCTestResults
        Test results
        
    Examples
    --------
    >>> from tvrcoint import bootstrap_tvc_test
    >>> results = bootstrap_tvc_test(Y, r=1, m=5, p=1, method='wild', B=399)
    >>> print(f"Bootstrap p-value: {results.pvalue_bootstrap:.4f}")
    """
    test = BootstrapTVCTest()
    return test.test(Y, r, m, p, method, restricted, B, include_drift, seed)
