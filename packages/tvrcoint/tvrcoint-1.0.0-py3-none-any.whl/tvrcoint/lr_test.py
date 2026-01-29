"""
Likelihood Ratio Test for Time-Varying Cointegration

This module implements the LR test for testing time-invariant cointegration
(null hypothesis) against time-varying cointegration (alternative hypothesis)
as described in Bierens & Martins (2010).

The test statistic:
    LR_{m,T}^{tvc} = T * Σ_{j=1}^{r} ln((1 - λ_{0,j}) / (1 - λ_{m,j}))

Under H0 (time-invariant cointegration):
    LR_{m,T}^{tvc} ~ χ²(m*k*r)

where:
    - m is the Chebyshev polynomial order
    - k is the number of variables
    - r is the cointegration rank
"""

import numpy as np
from scipy import stats
from typing import Optional, Tuple
from dataclasses import dataclass

from .tvvecm import TVVECM, TVVECMResults
from .utils import check_data


@dataclass
class TVCTestResults:
    """
    Results container for Time-Varying Cointegration LR test.
    
    Attributes
    ----------
    statistic : float
        LR test statistic value
    pvalue : float
        P-value from asymptotic χ² distribution
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
    eigenvalues_0 : np.ndarray
        Eigenvalues under H0 (standard cointegration)
    eigenvalues_m : np.ndarray
        Eigenvalues under Ha (time-varying cointegration)
    model_0 : TVVECMResults
        Estimation results under H0
    model_m : TVVECMResults
        Estimation results under Ha
    """
    statistic: float
    pvalue: float
    df: int
    m: int
    k: int
    r: int
    p: int
    T: int
    eigenvalues_0: np.ndarray
    eigenvalues_m: np.ndarray
    model_0: TVVECMResults
    model_m: TVVECMResults
    
    def summary(self) -> str:
        """
        Generate a summary of the test results.
        
        Returns
        -------
        str
            Formatted summary string
        """
        lines = [
            "",
            "=" * 70,
            "Time-Varying Cointegration LR Test",
            "Bierens & Martins (2010)",
            "=" * 70,
            "",
            "Model Specification:",
            f"  Number of variables (k):        {self.k}",
            f"  Cointegration rank (r):         {self.r}",
            f"  Chebyshev polynomial order (m): {self.m}",
            f"  VAR lag order (p):              {self.p}",
            f"  Effective sample size (T):      {self.T}",
            "",
            "Hypothesis:",
            "  H0: Time-invariant cointegration (β_t = β for all t)",
            "  H1: Time-varying cointegration",
            "",
            "Test Results:",
            f"  LR statistic:     {self.statistic:.4f}",
            f"  Degrees of freedom: {self.df}",
            f"  Asymptotic p-value: {self.pvalue:.4f}",
            "",
            "Conclusion:",
        ]
        
        if self.pvalue < 0.01:
            lines.append("  Strong evidence against H0 (p < 0.01)")
            lines.append("  → Evidence of TIME-VARYING cointegration")
        elif self.pvalue < 0.05:
            lines.append("  Evidence against H0 at 5% level")
            lines.append("  → Evidence of TIME-VARYING cointegration")
        elif self.pvalue < 0.10:
            lines.append("  Weak evidence against H0 at 10% level")
            lines.append("  → Mixed evidence, consider bootstrap test")
        else:
            lines.append("  Cannot reject H0")
            lines.append("  → Evidence of TIME-INVARIANT cointegration")
        
        lines.extend([
            "",
            "Note: Asymptotic critical values may have size distortions",
            "      in small samples. Bootstrap test recommended.",
            "=" * 70,
            ""
        ])
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return (f"TVCTestResults(statistic={self.statistic:.4f}, "
                f"pvalue={self.pvalue:.4f}, df={self.df})")


class TVCTest:
    """
    Likelihood Ratio Test for Time-Varying Cointegration.
    
    This class implements the LR test from Bierens & Martins (2010) for
    testing time-invariant cointegration against time-varying cointegration.
    
    Examples
    --------
    >>> import numpy as np
    >>> from tvrcoint import TVCTest
    >>> 
    >>> # Generate some data
    >>> np.random.seed(42)
    >>> T, k = 200, 3
    >>> Y = np.cumsum(np.random.randn(T, k), axis=0)
    >>> 
    >>> # Perform test
    >>> test = TVCTest()
    >>> results = test.test(Y, r=1, m=5, p=1)
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
        include_drift: bool = True
    ) -> TVCTestResults:
        """
        Perform the LR test for time-varying cointegration.
        
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
        include_drift : bool
            Whether to include drift term
            
        Returns
        -------
        TVCTestResults
            Test results including statistic, p-value, and models
            
        Raises
        ------
        ValueError
            If parameters are invalid
        """
        # Validate inputs
        T, k = check_data(Y)
        
        if r < 1 or r >= k:
            raise ValueError(f"Cointegration rank r must satisfy 1 <= r < k, got r={r}, k={k}")
        if m < 1:
            raise ValueError(f"Chebyshev order m must be >= 1 for testing, got m={m}")
        if p < 1:
            raise ValueError(f"VAR lag order p must be >= 1, got p={p}")
        
        # Fit model under H0 (m=0, standard cointegration)
        model_h0 = TVVECM()
        results_0 = model_h0.fit(Y, r=r, m=0, p=p, include_drift=include_drift)
        
        # Fit model under Ha (m>0, time-varying cointegration)
        model_ha = TVVECM()
        results_m = model_ha.fit(Y, r=r, m=m, p=p, include_drift=include_drift)
        
        # Extract eigenvalues
        eigenvalues_0 = results_0.eigenvalues[:r]
        eigenvalues_m = results_m.eigenvalues[:r]
        
        # Compute LR statistic
        T_eff = results_0.T
        lr_statistic = self._compute_lr_statistic(eigenvalues_0, eigenvalues_m, T_eff, r)
        
        # Degrees of freedom
        df = m * k * r
        
        # P-value from chi-square distribution
        pvalue = 1 - stats.chi2.cdf(lr_statistic, df)
        
        self.results_ = TVCTestResults(
            statistic=lr_statistic,
            pvalue=pvalue,
            df=df,
            m=m,
            k=k,
            r=r,
            p=p,
            T=T_eff,
            eigenvalues_0=eigenvalues_0,
            eigenvalues_m=eigenvalues_m,
            model_0=results_0,
            model_m=results_m
        )
        
        return self.results_
    
    def _compute_lr_statistic(
        self,
        lambda_0: np.ndarray,
        lambda_m: np.ndarray,
        T: int,
        r: int
    ) -> float:
        """
        Compute the LR test statistic.
        
        LR_{m,T}^{tvc} = T * Σ_{j=1}^{r} ln((1 - λ_{0,j}) / (1 - λ_{m,j}))
        """
        # Clip eigenvalues to avoid numerical issues
        eps = 1e-15
        lambda_0 = np.clip(lambda_0[:r], eps, 1 - eps)
        lambda_m = np.clip(lambda_m[:r], eps, 1 - eps)
        
        # The TV model should have larger eigenvalues (or equal under H0)
        # Ensure proper ordering
        log_ratios = np.log((1 - lambda_0) / (1 - lambda_m))
        
        lr_statistic = T * np.sum(log_ratios)
        
        # LR should be non-negative
        return max(0, lr_statistic)
    
    def test_multiple_m(
        self,
        Y: np.ndarray,
        r: int,
        m_values: list,
        p: int = 1,
        include_drift: bool = True
    ) -> dict:
        """
        Perform tests for multiple values of m.
        
        Parameters
        ----------
        Y : np.ndarray
            Data matrix of shape (T, k)
        r : int
            Cointegration rank
        m_values : list
            List of Chebyshev polynomial orders to test
        p : int
            VAR lag order
        include_drift : bool
            Whether to include drift term
            
        Returns
        -------
        dict
            Dictionary with m values as keys and TVCTestResults as values
        """
        results = {}
        for m in m_values:
            results[m] = self.test(Y, r, m, p, include_drift)
        return results
    
    @property
    def results(self) -> Optional[TVCTestResults]:
        """Get test results."""
        return self.results_


def tvc_test(
    Y: np.ndarray,
    r: int,
    m: int,
    p: int = 1,
    include_drift: bool = True
) -> TVCTestResults:
    """
    Convenience function for performing the TVC LR test.
    
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
        Whether to include drift term
        
    Returns
    -------
    TVCTestResults
        Test results
        
    Examples
    --------
    >>> from tvrcoint import tvc_test
    >>> results = tvc_test(Y, r=1, m=5, p=1)
    >>> print(f"LR statistic: {results.statistic:.4f}")
    >>> print(f"P-value: {results.pvalue:.4f}")
    """
    test = TVCTest()
    return test.test(Y, r, m, p, include_drift)


def critical_values_chi2(df: int, levels: list = [0.10, 0.05, 0.01]) -> dict:
    """
    Get critical values from chi-square distribution.
    
    Parameters
    ----------
    df : int
        Degrees of freedom (m * k * r)
    levels : list
        Significance levels
        
    Returns
    -------
    dict
        Dictionary with levels as keys and critical values as values
    """
    cv = {}
    for level in levels:
        cv[level] = stats.chi2.ppf(1 - level, df)
    return cv
