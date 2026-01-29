"""
Stability Test for Constant vs. Time-Varying Cointegrating Coefficients

This module implements the bootstrap-based test from Xiao (2009), Section 3.2,
for testing whether the cointegrating coefficients are constant across quantiles:

    H_0: β(τ) = β for all τ ∈ T

The test statistic is the supremum of the standardized process:

    sup_τ |V̂_n(τ)| where V̂_n(τ) = n(β̂(τ) - β̂_OLS)

Critical values are obtained via sieve bootstrap.

Reference:
    Xiao, Z. (2009). Quantile cointegrating regression. 
    Journal of Econometrics, 150(2), 248-260. Section 3.2.
"""

import numpy as np
from scipy import stats
from typing import Union, Optional, Tuple
from dataclasses import dataclass
import warnings


@dataclass
class StabilityTestResult:
    """
    Results from stability test for constant coefficients.
    
    Attributes
    ----------
    statistic : float
        Test statistic sup_τ |V̂_n(τ)|
    critical_values : dict
        Critical values at 1%, 5%, 10% levels
    pvalue : float
        Bootstrap p-value
    reject_at_05 : bool
        Whether to reject H_0 at 5% level
    tau_max : float
        Quantile where maximum deviation occurs
    V_n_process : dict
        V̂_n(τ) values at each quantile
    quantiles : np.ndarray
        Quantile levels tested
    n_bootstrap : int
        Number of bootstrap replications
    """
    statistic: float
    critical_values: dict
    pvalue: float
    reject_at_05: bool
    tau_max: float
    V_n_process: dict
    quantiles: np.ndarray
    n_bootstrap: int
    
    def __repr__(self) -> str:
        return (f"StabilityTestResult(statistic={self.statistic:.4f}, "
                f"pvalue={self.pvalue:.4f}, reject_at_05={self.reject_at_05})")
    
    def summary(self) -> str:
        """Generate formatted summary."""
        lines = []
        lines.append("=" * 70)
        lines.append("      Test for Constant Cointegrating Coefficients")
        lines.append("      H_0: β(τ) = β (constant across quantiles)")
        lines.append("=" * 70)
        lines.append(f"Number of quantiles tested:     {len(self.quantiles)}")
        lines.append(f"Quantile range:                 [{self.quantiles.min():.2f}, {self.quantiles.max():.2f}]")
        lines.append(f"Number of bootstrap reps:       {self.n_bootstrap}")
        lines.append("-" * 70)
        lines.append(f"Test statistic sup|V̂_n(τ)|:     {self.statistic:.4f}")
        lines.append(f"τ with maximum deviation:       {self.tau_max:.4f}")
        lines.append("-" * 70)
        lines.append("Bootstrap Critical Values:")
        lines.append(f"  10% level:                    {self.critical_values['10%']:.4f}")
        lines.append(f"  5% level:                     {self.critical_values['5%']:.4f}")
        lines.append(f"  1% level:                     {self.critical_values['1%']:.4f}")
        lines.append("-" * 70)
        lines.append(f"Bootstrap p-value:              {self.pvalue:.4f}")
        
        if self.pvalue < 0.01:
            conclusion = "Reject H_0 at 1% level: Evidence of time-varying coefficients ***"
        elif self.pvalue < 0.05:
            conclusion = "Reject H_0 at 5% level: Evidence of time-varying coefficients **"
        elif self.pvalue < 0.10:
            conclusion = "Reject H_0 at 10% level: Weak evidence of time-varying coefficients *"
        else:
            conclusion = "Fail to reject H_0: Coefficients appear constant"
        
        lines.append(f"Conclusion: {conclusion}")
        lines.append("=" * 70)
        
        return "\n".join(lines)


def stability_test(endog: np.ndarray, exog: np.ndarray,
                   quantiles: np.ndarray = None,
                   n_lags: int = 4,
                   n_bootstrap: int = 500,
                   var_order: int = None,
                   seed: int = None) -> StabilityTestResult:
    """
    Test for constant vs. time-varying cointegrating coefficients.
    
    Tests H_0: β(τ) = β for all τ vs H_1: β(τ) varies with τ
    
    Uses the sieve bootstrap procedure from Xiao (2009), Section 3.2:
    
    1. Estimate β̂(τ) at each quantile and β̂_OLS
    2. Compute V̂_n(τ) = n(β̂(τ) - β̂_OLS)
    3. Test statistic: sup_τ |V̂_n(τ)|
    4. Bootstrap critical values using sieve bootstrap
    
    Parameters
    ----------
    endog : np.ndarray
        Dependent variable y_t (n,)
    exog : np.ndarray
        Integrated regressors x_t (n,) or (n, k)
    quantiles : np.ndarray, optional
        Quantile levels to test. Default is np.arange(0.1, 0.91, 0.05).
    n_lags : int, default 4
        Number of leads/lags for augmented regression
    n_bootstrap : int, default 500
        Number of bootstrap replications
    var_order : int, optional
        VAR order for sieve bootstrap. Default is int(n^(1/3)).
    seed : int, optional
        Random seed for reproducibility
        
    Returns
    -------
    StabilityTestResult
        Test results including statistic, critical values, and p-value
        
    Reference
    ---------
    Xiao (2009), Section 3.2, Steps 1-5.
    Koenker, R., & Xiao, Z. (2002). Inference on the quantile regression 
    process. Econometrica, 70, 1583-1612.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if quantiles is None:
        quantiles = np.arange(0.1, 0.91, 0.05)
    quantiles = np.atleast_1d(quantiles)
    
    endog = np.asarray(endog).flatten()
    exog = np.asarray(exog)
    if exog.ndim == 1:
        exog = exog.reshape(-1, 1)
    
    n = len(endog)
    k = exog.shape[1]
    
    if var_order is None:
        var_order = max(1, int(n**(1/3)))
    
    # Step 1: Estimate β̂(τ) and β̂_OLS
    from quantilecoint.core.augmented import AugmentedQuantileRegression
    
    # OLS estimate
    X_ols = np.column_stack([np.ones(n), exog])
    beta_ols = np.linalg.lstsq(X_ols, endog, rcond=None)[0]
    ols_residuals = endog - X_ols @ beta_ols
    
    # Quantile regression estimates at each τ
    aqr = AugmentedQuantileRegression(endog, exog, n_lags=n_lags)
    
    beta_qr = {}
    V_n = {}
    
    for tau in quantiles:
        try:
            result = aqr.fit(tau=tau)
            # Get cointegrating coefficients (constant + slopes)
            beta_tau = np.concatenate([[result.alpha], result.beta])
            beta_qr[tau] = beta_tau
            
            # V̂_n(τ) = n(β̂(τ) - β̂_OLS) - only for slope coefficients
            V_n[tau] = n * (beta_tau[1:k+1] - beta_ols[1:k+1])
        except Exception as e:
            warnings.warn(f"Failed to estimate at tau={tau}: {e}")
            continue
    
    if len(V_n) < 3:
        raise ValueError("Too few quantile estimates succeeded")
    
    # Compute test statistic: sup_τ |V̂_n(τ)|
    # For multivariate β, use max of absolute values across all components
    valid_quantiles = np.array([tau for tau in quantiles if tau in V_n])
    V_n_values = np.array([np.max(np.abs(V_n[tau])) for tau in valid_quantiles])
    
    test_stat = np.max(V_n_values)
    tau_max = valid_quantiles[np.argmax(V_n_values)]
    
    # Step 2-5: Sieve bootstrap
    # Get effective sample from augmented regression
    K = n_lags
    start_idx = K
    end_idx = n - K
    n_eff = end_idx - start_idx
    
    # Construct ŵ_t = (v_t, û_t) where v_t = Δx_t
    v = np.diff(exog, axis=0)  # (n-1) x k
    u_hat = ols_residuals[1:]  # Match with v
    
    # Trim to effective sample length
    v_eff = v[start_idx-1:end_idx-1]
    u_eff = u_hat[start_idx:end_idx]
    
    w = np.column_stack([v_eff, u_eff])  # n_eff x (k+1)
    
    # Step 2: Fit VAR on ŵ_t
    q = var_order
    
    # Build VAR design matrix
    if q >= n_eff - 1:
        q = max(1, n_eff // 3)
    
    W_lags = np.column_stack([w[q-j-1:n_eff-j-1] for j in range(q)])
    W_y = w[q:]
    
    # VAR coefficients
    B_hat = np.linalg.lstsq(W_lags, W_y, rcond=None)[0]
    B_hat = B_hat.reshape(q, -1, w.shape[1])
    
    # Get residuals
    e_hat = W_y - W_lags @ B_hat.reshape(-1, w.shape[1])
    e_centered = e_hat - np.mean(e_hat, axis=0)
    
    # Bootstrap replications
    bootstrap_stats = []
    
    for b in range(n_bootstrap):
        try:
            # Step 3: Draw i.i.d. from centered residuals
            indices = np.random.randint(0, len(e_centered), size=n_eff)
            e_star = e_centered[indices]
            
            # Generate w* from VAR
            w_star = np.zeros((n_eff + q, w.shape[1]))
            w_star[:q] = w[:q]
            
            for t in range(q, n_eff + q):
                w_lags = w_star[t-q:t][::-1].flatten()
                w_star[t] = B_hat.reshape(-1, w.shape[1]).T @ w_lags + e_star[t-q]
            
            w_star = w_star[q:]
            
            # Step 4: Generate x* and y*
            v_star = w_star[:, :k]
            u_star = w_star[:, k:]
            
            # Cumulate v* to get x*
            x_star = np.cumsum(v_star, axis=0)
            x_star = x_star + exog[start_idx:end_idx] - x_star[0]  # Match initial value
            
            # Generate y* under H_0 (constant β)
            X_star = np.column_stack([np.ones(n_eff), x_star])
            y_star = X_star @ beta_ols[:k+1] + u_star.flatten()
            
            # Step 5: Compute bootstrap test statistic
            # OLS on bootstrap sample
            beta_ols_star = np.linalg.lstsq(X_star, y_star, rcond=None)[0]
            
            # QR at each quantile on bootstrap sample
            V_n_star_max = 0
            
            for tau in valid_quantiles[::2]:  # Use subset for speed
                try:
                    # Simple QR (without augmentation for speed)
                    from quantilecoint.core.quantile_regression import QuantileRegression
                    qr_boot = QuantileRegression(y_star, x_star, add_constant=True)
                    result_star = qr_boot.fit(tau=tau)
                    
                    V_n_star = n_eff * np.abs(result_star.params[1:] - beta_ols_star[1:])
                    V_n_star_max = max(V_n_star_max, np.max(V_n_star))
                except:
                    continue
            
            bootstrap_stats.append(V_n_star_max)
            
        except Exception as e:
            continue
    
    if len(bootstrap_stats) < 100:
        warnings.warn(
            f"Only {len(bootstrap_stats)} bootstrap replications succeeded"
        )
    
    bootstrap_stats = np.array(bootstrap_stats)
    
    # Compute critical values and p-value
    critical_values = {
        '10%': np.percentile(bootstrap_stats, 90),
        '5%': np.percentile(bootstrap_stats, 95),
        '1%': np.percentile(bootstrap_stats, 99),
    }
    
    pvalue = np.mean(bootstrap_stats >= test_stat)
    
    return StabilityTestResult(
        statistic=test_stat,
        critical_values=critical_values,
        pvalue=pvalue,
        reject_at_05=(test_stat > critical_values['5%']),
        tau_max=tau_max,
        V_n_process=V_n,
        quantiles=valid_quantiles,
        n_bootstrap=len(bootstrap_stats),
    )
