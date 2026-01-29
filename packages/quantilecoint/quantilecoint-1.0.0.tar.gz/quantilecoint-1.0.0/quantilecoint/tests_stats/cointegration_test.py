"""
CUSUM Test for Cointegration

This module implements the quantile-based CUSUM test for cointegration from 
Xiao (2009), Section 3.3. The test examines whether the cointegrating 
relationship is stable.

Under the null of cointegration, the residual process should be stable.
The test statistic is based on the partial sum of ψ_τ(ε_tτ).

Reference:
    Xiao, Z. (2009). Quantile cointegrating regression. 
    Journal of Econometrics, 150(2), 248-260. Section 3.3.
    
    Xiao, Z., & Phillips, P.C.B. (2002). A CUSUM test for cointegration 
    using regression residuals. Journal of Econometrics, 108, 43-61.
"""

import numpy as np
from scipy import stats
from typing import Union, Optional
from dataclasses import dataclass


@dataclass
class CointegrationTestResult:
    """
    Results from CUSUM cointegration test.
    
    Attributes
    ----------
    statistic : float
        Test statistic (Kolmogorov-Smirnov or Cramér-von Mises)
    critical_values : dict
        Critical values at 1%, 5%, 10% levels
    pvalue : float
        Asymptotic or simulated p-value
    reject_at_05 : bool
        Whether to reject H_0 (cointegration) at 5% level
    tau : float
        Quantile level used
    test_type : str
        Type of test ('ks' or 'cvm')
    Y_n_process : np.ndarray
        Partial sum process Ŷ_n(r)
    """
    statistic: float
    critical_values: dict
    pvalue: float
    reject_at_05: bool
    tau: float
    test_type: str
    Y_n_process: np.ndarray
    
    def __repr__(self) -> str:
        return (f"CointegrationTestResult(statistic={self.statistic:.4f}, "
                f"pvalue={self.pvalue:.4f}, test_type='{self.test_type}')")
    
    def summary(self) -> str:
        """Generate formatted summary."""
        lines = []
        lines.append("=" * 65)
        lines.append("          CUSUM Test for Cointegration")
        lines.append("          H_0: Series are cointegrated")
        lines.append("=" * 65)
        lines.append(f"Quantile (τ):                  {self.tau:.4f}")
        lines.append(f"Test type:                     {self.test_type.upper()}")
        lines.append(f"Test statistic:                {self.statistic:.4f}")
        lines.append("-" * 65)
        lines.append("Critical Values:")
        lines.append(f"  10% level:                   {self.critical_values['10%']:.4f}")
        lines.append(f"  5% level:                    {self.critical_values['5%']:.4f}")
        lines.append(f"  1% level:                    {self.critical_values['1%']:.4f}")
        lines.append("-" * 65)
        lines.append(f"P-value:                       {self.pvalue:.4f}")
        
        if self.reject_at_05:
            conclusion = "Reject H_0: Evidence against cointegration"
        else:
            conclusion = "Fail to reject H_0: Series appear cointegrated"
        
        lines.append(f"Conclusion: {conclusion}")
        lines.append("=" * 65)
        
        return "\n".join(lines)


def cointegration_test(endog: np.ndarray, exog: np.ndarray,
                       tau: float = 0.5,
                       n_lags: int = 4,
                       test_type: str = 'ks',
                       n_simulations: int = 10000,
                       kernel: str = 'bartlett',
                       seed: int = None) -> CointegrationTestResult:
    """
    CUSUM test for the null of cointegration.
    
    Tests whether the cointegrating relationship is stable using the 
    partial sum process of quantile regression residuals.
    
    From Xiao (2009), Section 3.3:
    
        Ŷ_n(r) = (1/(ω̂*_ψ √n)) × Σ_{j=1}^{[nr]} ψ_τ(ε̂_jτ)
    
    Under H_0 (cointegration), Ŷ_n(r) → W̃(r), a tied-down Brownian motion.
    
    Parameters
    ----------
    endog : np.ndarray
        Dependent variable y_t (n,)
    exog : np.ndarray
        Integrated regressors x_t (n,) or (n, k)
    tau : float, default 0.5
        Quantile level
    n_lags : int, default 4
        Number of leads/lags for augmented regression
    test_type : str, default 'ks'
        Test type: 'ks' (Kolmogorov-Smirnov sup test) or 
        'cvm' (Cramér-von Mises integral test)
    n_simulations : int, default 10000
        Number of simulations for critical values
    kernel : str, default 'bartlett'
        Kernel for long-run variance estimation
    seed : int, optional
        Random seed for simulations
        
    Returns
    -------
    CointegrationTestResult
        Test results including statistic and critical values
        
    Notes
    -----
    The test statistic depends on the number of regressors k.
    Critical values are obtained by simulating the limiting distribution
    which involves tied-down Brownian motions.
    
    Reference
    ---------
    Xiao (2009), Section 3.3.
    Xiao & Phillips (2002).
    """
    if seed is not None:
        np.random.seed(seed)
    
    endog = np.asarray(endog).flatten()
    exog = np.asarray(exog)
    if exog.ndim == 1:
        exog = exog.reshape(-1, 1)
    
    n = len(endog)
    k = exog.shape[1]
    
    # Step 1: Fit augmented quantile regression to get residuals
    from quantilecoint.core.augmented import AugmentedQuantileRegression
    
    aqr = AugmentedQuantileRegression(endog, exog, n_lags=n_lags)
    result = aqr.fit(tau=tau)
    
    residuals = result.residuals
    n_eff = len(residuals)
    
    # Step 2: Compute ψ_τ(ε̂_tτ) = τ - I(ε̂_tτ < 0)
    psi_tau = tau - (residuals < 0).astype(float)
    
    # Step 3: Estimate long-run variance ω*²_ψ
    from quantilecoint.utils.long_run_variance import long_run_variance
    from quantilecoint.utils.kernels import get_bandwidth
    
    bandwidth = get_bandwidth(n_eff, kernel)
    omega_psi_sq = float(long_run_variance(psi_tau, kernel=kernel, bandwidth=bandwidth))
    omega_psi = np.sqrt(max(omega_psi_sq, 1e-10))
    
    # Step 4: Compute partial sum process Ŷ_n(r)
    cumsum_psi = np.cumsum(psi_tau)
    Y_n = cumsum_psi / (omega_psi * np.sqrt(n_eff))
    
    # Step 5: Compute test statistic
    if test_type.lower() == 'ks':
        # Kolmogorov-Smirnov (supremum)
        test_stat = np.max(np.abs(Y_n))
    elif test_type.lower() == 'cvm':
        # Cramér-von Mises (integral)
        test_stat = np.mean(Y_n**2)
    else:
        raise ValueError(f"Unknown test type: {test_type}")
    
    # Step 6: Simulate critical values
    # Under H_0, Ŷ_n(r) → W̃(r) = W₁(r) - ∫dW₁ W₂' [∫W₂W₂']⁻¹ ∫W₂(s)
    # For simplicity, use standard Brownian bridge approximation
    
    sim_stats = []
    
    for _ in range(n_simulations):
        # Simulate Brownian motion
        W1 = np.cumsum(np.random.randn(n_eff)) / np.sqrt(n_eff)
        W2 = np.cumsum(np.random.randn(n_eff, k), axis=0) / np.sqrt(n_eff)
        
        # Tied-down process (Brownian bridge-like adjustment)
        r = np.arange(1, n_eff + 1) / n_eff
        
        # Correction for regression effect
        W2_cov = np.sum(W2**2, axis=0) / n_eff
        W2_W1 = np.sum(W2 * W1.reshape(-1, 1), axis=0) / n_eff
        
        if k == 1:
            correction = W2.flatten() * W2_W1[0] / (W2_cov[0] + 1e-10)
        else:
            correction = W2 @ np.linalg.lstsq(
                np.diag(W2_cov + 1e-10), W2_W1, rcond=None
            )[0]
        
        W_tilde = W1 - correction.flatten() if k == 1 else W1 - correction
        
        # Further tie down at endpoints
        W_tilde = W_tilde - r * W_tilde[-1]
        
        if test_type.lower() == 'ks':
            sim_stats.append(np.max(np.abs(W_tilde)))
        else:
            sim_stats.append(np.mean(W_tilde**2))
    
    sim_stats = np.array(sim_stats)
    
    # Critical values
    critical_values = {
        '10%': np.percentile(sim_stats, 90),
        '5%': np.percentile(sim_stats, 95),
        '1%': np.percentile(sim_stats, 99),
    }
    
    # P-value
    pvalue = np.mean(sim_stats >= test_stat)
    
    return CointegrationTestResult(
        statistic=test_stat,
        critical_values=critical_values,
        pvalue=pvalue,
        reject_at_05=(test_stat > critical_values['5%']),
        tau=tau,
        test_type=test_type,
        Y_n_process=Y_n,
    )
