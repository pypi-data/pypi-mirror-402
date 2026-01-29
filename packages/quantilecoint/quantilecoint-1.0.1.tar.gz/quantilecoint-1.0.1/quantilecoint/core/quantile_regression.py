"""
Quantile Regression for Cointegrated Time Series

This module implements the basic quantile regression estimator for cointegrated 
time series as described in Xiao (2009), Theorem 1.

Reference:
    Xiao, Z. (2009). Quantile cointegrating regression. 
    Journal of Econometrics, 150(2), 248-260.
"""

import numpy as np
from scipy import optimize
from scipy import stats
from typing import Optional, Union, Tuple
import warnings


def check_function(u: np.ndarray, tau: float) -> np.ndarray:
    """
    Koenker-Bassett check function (asymmetric loss function).
    
    ρ_τ(u) = u * (τ - I(u < 0))
    
    Parameters
    ----------
    u : np.ndarray
        Residuals
    tau : float
        Quantile level in (0, 1)
        
    Returns
    -------
    np.ndarray
        Check function values
        
    Reference
    ---------
    Koenker, R., & Bassett, G. (1978). Regression quantiles. 
    Econometrica, 46(1), 33-50. Equation (1).
    """
    return u * (tau - (u < 0).astype(float))


def quantile_objective(beta: np.ndarray, X: np.ndarray, y: np.ndarray, 
                       tau: float) -> float:
    """
    Objective function for quantile regression.
    
    Minimizes: Σ ρ_τ(y_t - X_t'β)
    
    Parameters
    ----------
    beta : np.ndarray
        Coefficient vector
    X : np.ndarray
        Design matrix (n x p)
    y : np.ndarray
        Dependent variable (n,)
    tau : float
        Quantile level
        
    Returns
    -------
    float
        Sum of check function values
    """
    residuals = y - X @ beta
    return np.sum(check_function(residuals, tau))


class QuantileRegression:
    """
    Quantile Regression Estimator for Cointegrated Time Series.
    
    Implements the quantile regression estimator θ̂(τ) from Xiao (2009), 
    equation (2):
    
        θ̂(τ) = argmin Σ ρ_τ(y_t - z_t'θ)
        
    where ρ_τ(u) = u(τ - I(u < 0)) is the check function.
    
    Parameters
    ----------
    endog : np.ndarray
        Dependent variable y_t (n,)
    exog : np.ndarray
        Integrated regressors x_t (n,) or (n, k)
    add_constant : bool, default True
        Whether to add a constant term
        
    Attributes
    ----------
    n : int
        Number of observations
    k : int
        Number of regressors (including constant if added)
    endog : np.ndarray
        Dependent variable
    exog : np.ndarray
        Design matrix with constant (if added)
        
    Notes
    -----
    The limiting distribution of the quantile regression estimator is given
    by Theorem 1 in Xiao (2009):
    
        n(β̂(τ) - β) => (1/f(F^{-1}(τ))) * [∫B_v B_v']^{-1} * [∫B_v dB_ψ + λ_vψ]
        
    This estimator may have second-order bias when regressors are endogenous.
    Use FullyModifiedQuantileRegression for bias-corrected estimates.
    
    Reference
    ---------
    Xiao, Z. (2009). Quantile cointegrating regression. 
    Journal of Econometrics, 150(2), 248-260. Section 2, Theorem 1.
    """
    
    def __init__(self, endog: np.ndarray, exog: np.ndarray, 
                 add_constant: bool = True):
        """Initialize the quantile regression model."""
        self.endog = np.asarray(endog).flatten()
        self.n = len(self.endog)
        
        exog = np.asarray(exog)
        if exog.ndim == 1:
            exog = exog.reshape(-1, 1)
            
        if add_constant:
            ones = np.ones((self.n, 1))
            self.exog = np.hstack([ones, exog])
            self._has_constant = True
        else:
            self.exog = exog
            self._has_constant = False
            
        self.k = self.exog.shape[1]
        
        # Validate dimensions
        if self.exog.shape[0] != self.n:
            raise ValueError(
                f"Dimensions mismatch: endog has {self.n} observations, "
                f"exog has {self.exog.shape[0]}"
            )
    
    def fit(self, tau: float = 0.5, 
            method: str = 'interior-point') -> 'QuantileRegressionResults':
        """
        Fit quantile regression at specified quantile level.
        
        Solves the linear programming problem in equation (2) of Xiao (2009).
        
        Parameters
        ----------
        tau : float, default 0.5
            Quantile level in (0, 1). Default is median regression.
        method : str, default 'interior-point'
            Optimization method: 'interior-point' (default), 'simplex', 
            or 'bfgs' (gradient-based, less accurate but faster)
            
        Returns
        -------
        QuantileRegressionResults
            Results object with coefficients, residuals, and diagnostics
            
        Notes
        -----
        For τ = 0.5 (median), this is the Least Absolute Deviations (LAD) 
        estimator mentioned in Section 2.
        
        Reference
        ---------
        Xiao (2009), equation (2).
        """
        if not 0 < tau < 1:
            raise ValueError(f"tau must be in (0, 1), got {tau}")
        
        n, k = self.n, self.k
        y = self.endog
        X = self.exog
        
        if method in ['interior-point', 'simplex']:
            # Linear programming formulation
            # min τ * u+ + (1-τ) * u-
            # s.t. X @ beta + u+ - u- = y
            #      u+, u- >= 0
            
            # Decision variables: [beta, u+, u-]
            c = np.concatenate([
                np.zeros(k),           # beta coefficients
                tau * np.ones(n),      # u+ weights
                (1 - tau) * np.ones(n) # u- weights
            ])
            
            # Equality constraint: X @ beta + u+ - u- = y
            A_eq = np.hstack([X, np.eye(n), -np.eye(n)])
            b_eq = y
            
            # Bounds: beta unbounded, u+/u- >= 0
            bounds = [(None, None)] * k + [(0, None)] * (2 * n)
            
            result = optimize.linprog(
                c, A_eq=A_eq, b_eq=b_eq, bounds=bounds,
                method='highs' if method == 'interior-point' else 'highs-ds',
                options={'disp': False}
            )
            
            if not result.success:
                warnings.warn(
                    f"Optimization did not converge: {result.message}",
                    RuntimeWarning
                )
            
            beta = result.x[:k]
            
        else:  # BFGS method
            # Initial estimate from OLS
            beta0 = np.linalg.lstsq(X, y, rcond=None)[0]
            
            result = optimize.minimize(
                quantile_objective,
                beta0,
                args=(X, y, tau),
                method='L-BFGS-B',
                options={'disp': False, 'maxiter': 1000}
            )
            
            if not result.success:
                warnings.warn(
                    f"Optimization did not converge: {result.message}",
                    RuntimeWarning
                )
            
            beta = result.x
        
        # Compute residuals and fitted values
        residuals = y - X @ beta
        fitted = X @ beta
        
        return QuantileRegressionResults(
            params=beta,
            residuals=residuals,
            fitted_values=fitted,
            tau=tau,
            nobs=n,
            nvar=k,
            endog=y,
            exog=X,
            has_constant=self._has_constant
        )
    
    def fit_multiple(self, quantiles: Union[list, np.ndarray] = None,
                     method: str = 'interior-point') -> dict:
        """
        Fit quantile regression at multiple quantile levels.
        
        Parameters
        ----------
        quantiles : array-like, optional
            Quantile levels. Default is [0.05, 0.1, ..., 0.9, 0.95].
        method : str, default 'interior-point'
            Optimization method
            
        Returns
        -------
        dict
            Dictionary mapping tau -> QuantileRegressionResults
        """
        if quantiles is None:
            quantiles = np.arange(0.05, 0.96, 0.05)
        
        results = {}
        for tau in quantiles:
            results[tau] = self.fit(tau=tau, method=method)
        
        return results


class QuantileRegressionResults:
    """
    Results from quantile regression estimation.
    
    Attributes
    ----------
    params : np.ndarray
        Estimated coefficients θ̂(τ)
    residuals : np.ndarray
        Regression residuals u_tτ = y_t - θ̂(τ)'z_t
    fitted_values : np.ndarray
        Fitted values ŷ_t = θ̂(τ)'z_t
    tau : float
        Quantile level
    nobs : int
        Number of observations
    nvar : int
        Number of variables
    """
    
    def __init__(self, params: np.ndarray, residuals: np.ndarray,
                 fitted_values: np.ndarray, tau: float, nobs: int,
                 nvar: int, endog: np.ndarray, exog: np.ndarray,
                 has_constant: bool):
        """Initialize results object."""
        self.params = params
        self.residuals = residuals
        self.fitted_values = fitted_values
        self.tau = tau
        self.nobs = nobs
        self.nvar = nvar
        self._endog = endog
        self._exog = exog
        self._has_constant = has_constant
        
        # Cache for computed values
        self._std_errors = None
        self._sparsity = None
    
    @property
    def alpha(self) -> Optional[float]:
        """Intercept coefficient α(τ) if model has constant."""
        if self._has_constant:
            return self.params[0]
        return None
    
    @property
    def beta(self) -> np.ndarray:
        """Slope coefficients β(τ)."""
        if self._has_constant:
            return self.params[1:]
        return self.params
    
    def psi_tau(self, residuals: np.ndarray = None) -> np.ndarray:
        """
        Compute ψ_τ(u) = τ - I(u < 0).
        
        This is the subgradient of the check function.
        
        Parameters
        ----------
        residuals : np.ndarray, optional
            Residuals to use. Default is self.residuals.
            
        Returns
        -------
        np.ndarray
            Values of ψ_τ function
            
        Reference
        ---------
        Xiao (2009), equation after (2).
        """
        if residuals is None:
            residuals = self.residuals
        return self.tau - (residuals < 0).astype(float)
    
    def summary(self) -> str:
        """Generate summary string for display."""
        lines = []
        lines.append("=" * 60)
        lines.append("         Quantile Regression Results")
        lines.append("=" * 60)
        lines.append(f"Quantile (τ):            {self.tau:.4f}")
        lines.append(f"No. Observations:        {self.nobs}")
        lines.append(f"No. Variables:           {self.nvar}")
        lines.append("-" * 60)
        lines.append(f"{'Variable':<15} {'Coefficient':>15}")
        lines.append("-" * 60)
        
        var_names = ['const'] if self._has_constant else []
        var_names += [f'x{i+1}' for i in range(self.nvar - len(var_names))]
        
        for name, coef in zip(var_names, self.params):
            lines.append(f"{name:<15} {coef:>15.6f}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"QuantileRegressionResults(tau={self.tau}, nobs={self.nobs})"
