"""
Augmented Quantile Cointegrating Regression

This module implements the augmented quantile cointegrating regression from 
Xiao (2009), Section 3. The augmented model uses leads and lags of the 
differenced regressors to handle endogeneity parametrically.

The model from equation (12) in Xiao (2009):

    Θ̂(τ) = argmin Σ ρ_τ(y_t - Θ'Z_t)
    
where Z_t includes z_t = (1, x_t) and (Δx_{t-j}, j = -K,...,K)

This also allows for quantile-varying coefficients, enabling the quantile 
cointegration model from Section 3.1.

Reference:
    Xiao, Z. (2009). Quantile cointegrating regression. 
    Journal of Econometrics, 150(2), 248-260. Section 3, Theorem 4.
    
    Saikkonen, P. (1991). Asymptotically efficient estimation of 
    cointegration regression. Econometric Theory, 7, 1-21.
"""

import numpy as np
from scipy import optimize
from scipy import stats
from typing import Optional, Union, Tuple
import warnings

from quantilecoint.core.quantile_regression import check_function


class AugmentedQuantileRegression:
    """
    Augmented Quantile Cointegrating Regression.
    
    Implements the leads-and-lags approach from Xiao (2009), Section 3.
    The augmented regression takes the form:
    
        y_t = α + β'x_t + Σ_{j=-K}^{K} Π_j'Δx_{t-j} + ε_t
        
    At the τ-th quantile:
    
        Q_{y_t}(τ|F_t) = α(τ) + β(τ)'x_t + Σ Π_j(τ)'Δx_{t-j}
    
    Parameters
    ----------
    endog : np.ndarray
        Dependent variable y_t (n,)
    exog : np.ndarray
        Integrated regressors x_t (n,) or (n, k)
    n_lags : int, default 4
        Number of leads and lags K to include
        
    Attributes
    ----------
    n : int
        Number of observations (after trimming)
    n_lags : int
        Number of leads/lags K
    n_vars : int
        Total number of parameters
        
    Notes
    -----
    The limiting distribution from Theorem 4 is mixture normal:
    
        n(β̂(τ) - β(τ)) => (1/f_ε(F_ε^{-1}(τ))) × [∫B_v B_v']^{-1} × ∫B_v dB*_ψ
        
    The Brownian motions are independent due to the orthogonalization 
    achieved by including leads and lags.
    
    Reference
    ---------
    Xiao (2009), Section 3, Theorem 4.
    """
    
    def __init__(self, endog: np.ndarray, exog: np.ndarray, n_lags: int = 4):
        """Initialize the augmented quantile regression model."""
        self.endog_full = np.asarray(endog).flatten()
        n_full = len(self.endog_full)
        
        exog = np.asarray(exog)
        if exog.ndim == 1:
            exog = exog.reshape(-1, 1)
        self.exog_full = exog
        self.k = exog.shape[1]  # Number of integrated regressors
        
        self.n_lags = n_lags
        K = n_lags
        
        # Compute differenced regressors
        delta_x = np.diff(exog, axis=0)  # (n-1) x k
        
        # Effective sample: t = K+1, ..., n-K (to have K leads and K lags)
        # Python indexing: t = K, ..., n-1-K
        start_idx = K
        end_idx = n_full - K
        
        if end_idx <= start_idx:
            raise ValueError(
                f"Sample size {n_full} too small for {K} leads/lags. "
                f"Need at least {2*K + 1} observations."
            )
        
        self.n = end_idx - start_idx
        
        # Extract effective sample
        self.endog = self.endog_full[start_idx:end_idx]
        
        # Build augmented regressor matrix Z_t
        # Z_t = (1, x_t, Δx_{t-K}, ..., Δx_{t}, ..., Δx_{t+K})
        
        # x_t for effective sample
        x_t = exog[start_idx:end_idx]  # (n_eff) x k
        
        # Build leads and lags of Δx_t
        # For each t in effective sample, we need Δx_{t-K}, ..., Δx_{t+K}
        # Note: Δx_t = x_t - x_{t-1}, so Δx_t corresponds to index t-1 in delta_x
        # For t in [K, n-K-1], Δx_{t+j} is at index (t-1+j) in delta_x
        
        delta_x_lags = []
        for j in range(-K, K + 1):
            # For t in [K, n-K-1], we need delta_x at indices (t-1+j)
            # t ranges from K to n_full-K-1
            # So indices range from (K-1+j) to (n_full-K-1-1+j) = (n_full-K+j-2)
            # Slice: delta_x[K-1+j : n_full-K-1+j]
            lag_start = K - 1 + j
            lag_end = n_full - K - 1 + j
            
            # Ensure valid indices
            if lag_start < 0:
                lag_start = 0
            if lag_end > len(delta_x):
                lag_end = len(delta_x)
            
            lag_slice = delta_x[lag_start:lag_end]
            
            # Pad if necessary to match self.n
            if len(lag_slice) < self.n:
                pad_size = self.n - len(lag_slice)
                lag_slice = np.vstack([np.zeros((pad_size, self.k)), lag_slice])
            elif len(lag_slice) > self.n:
                lag_slice = lag_slice[:self.n]
            
            delta_x_lags.append(lag_slice)
        
        # Stack: shape (n_eff, (2K+1)*k)
        self.delta_x_augmented = np.hstack(delta_x_lags)
        
        # Full design matrix: (1, x_t, Δx augmented)
        ones = np.ones((self.n, 1))
        self.exog = np.hstack([ones, x_t, self.delta_x_augmented])
        self.n_vars = self.exog.shape[1]
        
        # Number of Π parameters: (2K+1) * k
        self.n_pi = (2 * K + 1) * self.k
    
    def fit(self, tau: float = 0.5,
            method: str = 'interior-point') -> 'AugmentedResults':
        """
        Fit augmented quantile cointegrating regression.
        
        Solves the optimization problem in equation (12) of Xiao (2009):
        
            Θ̂(τ) = argmin Σ ρ_τ(y_t - Θ'Z_t)
        
        Parameters
        ----------
        tau : float, default 0.5
            Quantile level in (0, 1)
        method : str, default 'interior-point'
            Optimization method
            
        Returns
        -------
        AugmentedResults
            Results object with coefficients
            
        Reference
        ---------
        Xiao (2009), equation (12), Theorem 4.
        """
        if not 0 < tau < 1:
            raise ValueError(f"tau must be in (0, 1), got {tau}")
        
        n = self.n
        p = self.n_vars
        y = self.endog
        Z = self.exog
        
        if method in ['interior-point', 'simplex']:
            # Linear programming formulation
            c = np.concatenate([
                np.zeros(p),
                tau * np.ones(n),
                (1 - tau) * np.ones(n)
            ])
            
            A_eq = np.hstack([Z, np.eye(n), -np.eye(n)])
            b_eq = y
            
            bounds = [(None, None)] * p + [(0, None)] * (2 * n)
            
            result = optimize.linprog(
                c, A_eq=A_eq, b_eq=b_eq, bounds=bounds,
                method='highs',
                options={'disp': False}
            )
            
            if not result.success:
                warnings.warn(
                    f"Optimization did not converge: {result.message}",
                    RuntimeWarning
                )
            
            theta = result.x[:p]
            
        else:
            # BFGS method
            theta0 = np.linalg.lstsq(Z, y, rcond=None)[0]
            
            def objective(theta):
                resid = y - Z @ theta
                return np.sum(check_function(resid, tau))
            
            result = optimize.minimize(
                objective, theta0,
                method='L-BFGS-B',
                options={'disp': False, 'maxiter': 1000}
            )
            
            theta = result.x
        
        # Parse coefficients
        # θ = (α, β_1, ..., β_k, Π_{-K}, ..., Π_K)
        alpha = theta[0]
        beta = theta[1:1+self.k]
        pi_coeffs = theta[1+self.k:]
        
        # Reshape Π coefficients
        pi_matrix = pi_coeffs.reshape(2*self.n_lags + 1, self.k)
        
        # Compute residuals
        residuals = y - Z @ theta
        fitted = Z @ theta
        
        # Compute standard errors (simplified asymptotic variance)
        # This uses the mixture normal result from Theorem 4
        from quantilecoint.utils.sparsity import estimate_sparsity
        f_tau = estimate_sparsity(residuals, tau)
        
        # Asymptotic variance approximation
        # Based on sandwich estimator
        X_beta = self.exog[:, :1+self.k]  # Just constant and x_t
        XX = X_beta.T @ X_beta / n
        XX_inv = np.linalg.inv(XX)
        
        # ω²_ψ ≈ τ(1-τ) for i.i.d. errors
        omega_psi_v = tau * (1 - tau)
        var_factor = omega_psi_v / (f_tau ** 2)
        
        var_beta = var_factor * XX_inv / n
        std_errors_beta = np.sqrt(np.diag(var_beta))
        
        return AugmentedResults(
            params=theta,
            alpha=alpha,
            beta=beta,
            pi_coeffs=pi_matrix,
            std_errors_beta=std_errors_beta,
            residuals=residuals,
            fitted_values=fitted,
            tau=tau,
            nobs=n,
            n_lags=self.n_lags,
            k=self.k,
            sparsity=f_tau,
            endog=y,
            exog=Z,
        )
    
    def fit_multiple(self, quantiles: Union[list, np.ndarray] = None) -> dict:
        """
        Fit augmented quantile regression at multiple quantiles.
        
        Parameters
        ----------
        quantiles : array-like, optional
            Quantile levels. Default is [0.05, 0.1, ..., 0.9, 0.95].
            
        Returns
        -------
        dict
            Dictionary mapping tau -> AugmentedResults
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


class AugmentedResults:
    """
    Results from augmented quantile cointegrating regression.
    
    Attributes
    ----------
    params : np.ndarray
        All estimated parameters Θ̂(τ)
    alpha : float
        Intercept α(τ)
    beta : np.ndarray
        Cointegrating coefficients β(τ)
    pi_coeffs : np.ndarray
        Lead/lag coefficients Π_j(τ), shape (2K+1, k)
    std_errors_beta : np.ndarray
        Standard errors for (α, β)
    residuals : np.ndarray
        Regression residuals ε_tτ
    tau : float
        Quantile level
    n_lags : int
        Number of leads/lags K
    """
    
    def __init__(self, params: np.ndarray, alpha: float, beta: np.ndarray,
                 pi_coeffs: np.ndarray, std_errors_beta: np.ndarray,
                 residuals: np.ndarray, fitted_values: np.ndarray,
                 tau: float, nobs: int, n_lags: int, k: int,
                 sparsity: float, endog: np.ndarray, exog: np.ndarray):
        """Initialize results object."""
        self.params = params
        self.alpha = alpha
        self.beta = beta
        self.pi_coeffs = pi_coeffs
        self.std_errors_beta = std_errors_beta
        self.residuals = residuals
        self.fitted_values = fitted_values
        self.tau = tau
        self.nobs = nobs
        self.n_lags = n_lags
        self.k = k
        self.sparsity = sparsity
        self._endog = endog
        self._exog = exog
    
    @property
    def tvalues_beta(self) -> np.ndarray:
        """t-statistics for (α, β) coefficients."""
        coeffs = np.concatenate([[self.alpha], self.beta])
        return coeffs / self.std_errors_beta
    
    @property
    def pvalues_beta(self) -> np.ndarray:
        """p-values for (α, β) coefficients."""
        return 2 * (1 - stats.norm.cdf(np.abs(self.tvalues_beta)))
    
    def conf_int_beta(self, alpha: float = 0.05) -> np.ndarray:
        """Confidence intervals for (α, β) coefficients."""
        z = stats.norm.ppf(1 - alpha / 2)
        coeffs = np.concatenate([[self.alpha], self.beta])
        lower = coeffs - z * self.std_errors_beta
        upper = coeffs + z * self.std_errors_beta
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
        ci = self.conf_int_beta(alpha)
        coeffs = np.concatenate([[self.alpha], self.beta])
        
        lines = []
        lines.append("=" * 78)
        lines.append("         Augmented Quantile Cointegrating Regression Results")
        lines.append("=" * 78)
        lines.append(f"Quantile (τ):              {self.tau:.4f}")
        lines.append(f"No. Observations:          {self.nobs}")
        lines.append(f"No. Leads/Lags (K):        {self.n_lags}")
        lines.append(f"Sparsity f(F⁻¹(τ)):        {self.sparsity:.6f}")
        lines.append("-" * 78)
        lines.append("Cointegrating Coefficients:")
        lines.append("-" * 78)
        lines.append(f"{'Variable':<10} {'Coef':>12} {'Std.Err':>12} {'t-stat':>10} "
                     f"{'P>|t|':>8} {'[{:.0%}'.format(1-alpha):>10} {'{:.0%}]'.format(1-alpha):>8}")
        lines.append("-" * 78)
        
        var_names = ['const'] + [f'x{i}' for i in range(1, self.k + 1)]
        
        for i, name in enumerate(var_names):
            stars = ''
            if self.pvalues_beta[i] < 0.01:
                stars = '***'
            elif self.pvalues_beta[i] < 0.05:
                stars = '**'
            elif self.pvalues_beta[i] < 0.10:
                stars = '*'
            
            lines.append(
                f"{name:<10} {coeffs[i]:>12.6f} {self.std_errors_beta[i]:>12.6f} "
                f"{self.tvalues_beta[i]:>10.3f} {self.pvalues_beta[i]:>8.4f} "
                f"{ci[i, 0]:>10.4f} {ci[i, 1]:>8.4f} {stars}"
            )
        
        lines.append("-" * 78)
        lines.append("Lead/Lag Coefficients (Π):")
        lines.append("-" * 78)
        
        for j, lag in enumerate(range(-self.n_lags, self.n_lags + 1)):
            lag_str = f"Δx(t{lag:+d})" if lag != 0 else "Δx(t)"
            pi_vals = self.pi_coeffs[j]
            lines.append(f"{lag_str:<12} " + " ".join([f"{v:>10.4f}" for v in pi_vals]))
        
        lines.append("-" * 78)
        lines.append("Significance: *** p<0.01, ** p<0.05, * p<0.10")
        lines.append("=" * 78)
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return (f"AugmentedResults(tau={self.tau}, nobs={self.nobs}, "
                f"beta={self.beta}, n_lags={self.n_lags})")
