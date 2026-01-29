"""
Fully-Modified Quantile Regression Estimator

This module implements the fully-modified quantile regression estimator from 
Xiao (2009), Theorem 2. The fully-modified estimator removes second-order bias
that arises from correlation between the integrated regressor and the error term.

The key formula from equation (4) in Xiao (2009):

    β̂(τ)⁺ = β̂(τ) - [Σ x_t x_t']^{-1} × 
             [Σ x_t v_t' Ω̂_vv^{-1} Ω̂_vψ / f(F̂^{-1}(τ)) + n λ̂⁺_vψ]

Reference:
    Xiao, Z. (2009). Quantile cointegrating regression. 
    Journal of Econometrics, 150(2), 248-260. Section 2.2, Theorem 2.
    
    Phillips, P.C.B., & Hansen, B.E. (1990). Statistical inference in 
    instrumental variables regression with I(1) processes. 
    Review of Economic Studies, 57, 99-125.
"""

import numpy as np
from scipy import stats
from typing import Optional, Union, Tuple
import warnings

from quantilecoint.core.quantile_regression import (
    QuantileRegression, 
    QuantileRegressionResults
)
from quantilecoint.utils.sparsity import estimate_sparsity
from quantilecoint.utils.long_run_variance import estimate_omega


class FullyModifiedQuantileRegression:
    """
    Fully-Modified Quantile Regression for Cointegrated Time Series.
    
    Implements the bias-corrected quantile regression estimator from 
    Xiao (2009), Theorem 2. This estimator has a mixture normal limiting
    distribution, enabling standard inference.
    
    Parameters
    ----------
    endog : np.ndarray
        Dependent variable y_t (n,)
    exog : np.ndarray
        Integrated regressors x_t (n,) or (n, k)
    kernel : str, default 'bartlett'
        Kernel for long-run variance estimation
    bandwidth : int, optional
        Bandwidth for kernel estimation. If None, uses automatic selection.
    sparsity_method : str, default 'bofinger'
        Method for sparsity function estimation: 'bofinger', 'hall-sheather'
        
    Attributes
    ----------
    n : int
        Number of observations
    k : int
        Number of regressors (including constant)
        
    Notes
    -----
    The fully-modified estimator achieves a mixed normal limit:
    
        n(β̂(τ)⁺ - β) => MN(0, (ω²_ψ.v / f(F^{-1}(τ))²) × [∫B_v B_v']^{-1})
        
    This enables construction of standard Wald tests.
    
    Reference
    ---------
    Xiao (2009), Section 2.2, Theorem 2.
    """
    
    def __init__(self, endog: np.ndarray, exog: np.ndarray,
                 kernel: str = 'bartlett', bandwidth: int = None,
                 sparsity_method: str = 'bofinger'):
        """Initialize the fully-modified quantile regression model."""
        self.endog = np.asarray(endog).flatten()
        self.n = len(self.endog)
        
        exog = np.asarray(exog)
        if exog.ndim == 1:
            exog = exog.reshape(-1, 1)
        self.exog_raw = exog
        
        # Add constant
        ones = np.ones((self.n, 1))
        self.exog = np.hstack([ones, exog])
        self.k = self.exog.shape[1]
        
        # Compute differenced regressors v_t = Δx_t
        self.v = np.diff(exog, axis=0)
        
        self.kernel = kernel
        self.bandwidth = bandwidth
        self.sparsity_method = sparsity_method
    
    def fit(self, tau: float = 0.5) -> 'FullyModifiedResults':
        """
        Fit fully-modified quantile regression at specified quantile.
        
        Implements equation (4) from Xiao (2009):
        
        β̂(τ)⁺ = β̂(τ) - [Σ x_t x_t']^{-1} × 
                 [Σ x_t v_t' Ω̂_vv^{-1} Ω̂_vψ / f(F̂^{-1}(τ)) + n λ̂⁺_vψ]
        
        Parameters
        ----------
        tau : float, default 0.5
            Quantile level in (0, 1)
            
        Returns
        -------
        FullyModifiedResults
            Results object with bias-corrected coefficients
            
        Reference
        ---------
        Xiao (2009), Theorem 2.
        """
        if not 0 < tau < 1:
            raise ValueError(f"tau must be in (0, 1), got {tau}")
        
        n = self.n
        y = self.endog
        X = self.exog
        x_raw = self.exog_raw
        v = self.v
        
        # Step 1: Get initial quantile regression estimate
        qr = QuantileRegression(y, x_raw, add_constant=True)
        initial_result = qr.fit(tau=tau)
        beta_initial = initial_result.params
        residuals = initial_result.residuals
        
        # Step 2: Compute ψ_τ(u_tτ) = τ - I(u_tτ < 0)
        # Use residuals from t=2,...,n to match with v_t
        psi_tau = tau - (residuals[1:] < 0).astype(float)
        
        # Step 3: Estimate long-run covariances
        omega_estimates = estimate_omega(
            v, psi_tau, 
            kernel=self.kernel, 
            bandwidth=self.bandwidth
        )
        
        omega_vv = omega_estimates['omega_vv']
        omega_vv_inv = omega_estimates['omega_vv_inv']
        omega_vpsi = omega_estimates['omega_vpsi']
        lambda_vpsi_plus = omega_estimates['lambda_vpsi_plus']
        omega_psi_v = omega_estimates['omega_psi_v']
        
        # Step 4: Estimate sparsity function f(F^{-1}(τ))
        f_tau = estimate_sparsity(residuals, tau, method=self.sparsity_method)
        
        # Step 5: Compute bias correction
        # [Σ x_t x_t']^{-1}
        X_x = x_raw  # n x k (without constant)
        XX = X_x.T @ X_x  # k x k
        XX_inv = np.linalg.inv(XX)
        
        # Σ x_t v_t' for matched observations (t=2,...,n)
        X_v = X_x[1:].T @ v  # k x k
        
        # First correction term: X_v @ Ω_vv^{-1} @ Ω_vψ / f(τ)
        omega_vpsi = np.atleast_1d(omega_vpsi).reshape(-1, 1)
        correction1 = X_v @ omega_vv_inv @ omega_vpsi / f_tau
        
        # Second correction term: n × λ⁺_vψ
        lambda_vpsi_plus = np.atleast_1d(lambda_vpsi_plus).reshape(-1, 1)
        correction2 = n * lambda_vpsi_plus
        
        # Total correction
        total_correction = XX_inv @ (correction1 + correction2)
        
        # Step 6: Apply correction to slope coefficients
        beta_corrected = beta_initial.copy()
        beta_corrected[1:] = beta_corrected[1:] - total_correction.flatten()
        
        # Recompute residuals with corrected coefficients
        residuals_corrected = y - X @ beta_corrected
        fitted_corrected = X @ beta_corrected
        
        # Step 7: Compute standard errors
        # From Theorem 2: Var(β̂⁺) ≈ (ω²_ψ.v / f²) × [Σ x_t x_t']^{-1} / n
        var_factor = omega_psi_v / (f_tau ** 2)
        var_beta = var_factor * XX_inv / n
        std_errors = np.sqrt(np.diag(var_beta))
        
        # Add std error for constant (use residual variance approximation)
        const_var = var_factor * np.mean(X_x ** 2) / n
        std_errors_full = np.concatenate([[np.sqrt(const_var)], std_errors])
        
        return FullyModifiedResults(
            params=beta_corrected,
            params_initial=beta_initial,
            std_errors=std_errors_full,
            residuals=residuals_corrected,
            fitted_values=fitted_corrected,
            tau=tau,
            nobs=n,
            nvar=self.k,
            sparsity=f_tau,
            omega_psi_v=omega_psi_v,
            correction=np.concatenate([[0], total_correction.flatten()]),
            endog=y,
            exog=X,
        )
    
    def fit_multiple(self, quantiles: Union[list, np.ndarray] = None) -> dict:
        """
        Fit fully-modified quantile regression at multiple quantiles.
        
        Parameters
        ----------
        quantiles : array-like, optional
            Quantile levels. Default is [0.05, 0.1, ..., 0.9, 0.95].
            
        Returns
        -------
        dict
            Dictionary mapping tau -> FullyModifiedResults
        """
        if quantiles is None:
            quantiles = np.arange(0.05, 0.96, 0.05)
        
        results = {}
        for tau in quantiles:
            try:
                results[tau] = self.fit(tau=tau)
            except Exception as e:
                warnings.warn(f"Failed to fit at tau={tau}: {e}")
        
        return results


class FullyModifiedResults:
    """
    Results from fully-modified quantile regression.
    
    Attributes
    ----------
    params : np.ndarray
        Bias-corrected coefficients θ̂(τ)⁺
    params_initial : np.ndarray
        Initial (uncorrected) coefficients θ̂(τ)
    std_errors : np.ndarray
        Standard errors from asymptotic distribution
    residuals : np.ndarray
        Residuals from corrected model
    tau : float
        Quantile level
    sparsity : float
        Estimated sparsity f(F^{-1}(τ))
    omega_psi_v : float
        Conditional long-run variance ω²_ψ.v
    correction : np.ndarray
        Bias correction applied to coefficients
    """
    
    def __init__(self, params: np.ndarray, params_initial: np.ndarray,
                 std_errors: np.ndarray, residuals: np.ndarray,
                 fitted_values: np.ndarray, tau: float, nobs: int,
                 nvar: int, sparsity: float, omega_psi_v: float,
                 correction: np.ndarray, endog: np.ndarray,
                 exog: np.ndarray):
        """Initialize results object."""
        self.params = params
        self.params_initial = params_initial
        self.std_errors = std_errors
        self.residuals = residuals
        self.fitted_values = fitted_values
        self.tau = tau
        self.nobs = nobs
        self.nvar = nvar
        self.sparsity = sparsity
        self.omega_psi_v = omega_psi_v
        self.correction = correction
        self._endog = endog
        self._exog = exog
    
    @property
    def alpha(self) -> float:
        """Intercept coefficient α(τ)⁺."""
        return self.params[0]
    
    @property
    def beta(self) -> np.ndarray:
        """Slope coefficients β(τ)⁺."""
        return self.params[1:]
    
    @property
    def tvalues(self) -> np.ndarray:
        """t-statistics for coefficient estimates."""
        return self.params / self.std_errors
    
    @property
    def pvalues(self) -> np.ndarray:
        """Two-sided p-values for coefficient estimates."""
        return 2 * (1 - stats.norm.cdf(np.abs(self.tvalues)))
    
    def conf_int(self, alpha: float = 0.05) -> np.ndarray:
        """
        Compute confidence intervals for coefficients.
        
        Parameters
        ----------
        alpha : float, default 0.05
            Significance level (1-alpha confidence)
            
        Returns
        -------
        np.ndarray
            Array of shape (nvar, 2) with lower and upper bounds
        """
        z = stats.norm.ppf(1 - alpha / 2)
        lower = self.params - z * self.std_errors
        upper = self.params + z * self.std_errors
        return np.column_stack([lower, upper])
    
    def summary(self, alpha: float = 0.05) -> str:
        """
        Generate publication-ready summary output.
        
        Parameters
        ----------
        alpha : float, default 0.05
            Significance level for confidence intervals
            
        Returns
        -------
        str
            Formatted summary string
        """
        ci = self.conf_int(alpha)
        
        lines = []
        lines.append("=" * 78)
        lines.append("         Fully-Modified Quantile Cointegrating Regression Results")
        lines.append("=" * 78)
        lines.append(f"Quantile (τ):              {self.tau:.4f}")
        lines.append(f"No. Observations:          {self.nobs}")
        lines.append(f"No. Variables:             {self.nvar}")
        lines.append(f"Sparsity f(F⁻¹(τ)):        {self.sparsity:.6f}")
        lines.append(f"Cond. Variance ω²_ψ.v:     {self.omega_psi_v:.6f}")
        lines.append("-" * 78)
        lines.append(f"{'Variable':<10} {'Coef':>12} {'Std.Err':>12} {'t-stat':>10} "
                     f"{'P>|t|':>8} {'[{:.0%}'.format(1-alpha):>10} {'{:.0%}]'.format(1-alpha):>8}")
        lines.append("-" * 78)
        
        var_names = ['const'] + [f'x{i}' for i in range(1, self.nvar)]
        
        for i, name in enumerate(var_names):
            stars = ''
            if self.pvalues[i] < 0.01:
                stars = '***'
            elif self.pvalues[i] < 0.05:
                stars = '**'
            elif self.pvalues[i] < 0.10:
                stars = '*'
            
            lines.append(
                f"{name:<10} {self.params[i]:>12.6f} {self.std_errors[i]:>12.6f} "
                f"{self.tvalues[i]:>10.3f} {self.pvalues[i]:>8.4f} "
                f"{ci[i, 0]:>10.4f} {ci[i, 1]:>8.4f} {stars}"
            )
        
        lines.append("-" * 78)
        lines.append("Significance: *** p<0.01, ** p<0.05, * p<0.10")
        lines.append("=" * 78)
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return (f"FullyModifiedResults(tau={self.tau}, nobs={self.nobs}, "
                f"beta={self.beta})")
