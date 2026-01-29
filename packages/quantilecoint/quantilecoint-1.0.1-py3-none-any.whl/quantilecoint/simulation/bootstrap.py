"""
Bootstrap Procedures for Quantile Cointegration

This module implements bootstrap methods for inference in quantile cointegrating
regression, including the sieve bootstrap from Xiao (2009), Section 3.2.

Reference:
    Xiao, Z. (2009). Quantile cointegrating regression. 
    Journal of Econometrics, 150(2), 248-260. Section 3.2.
"""

import numpy as np
from typing import Tuple, Optional, Callable
import warnings


def sieve_bootstrap(endog: np.ndarray, exog: np.ndarray,
                    residuals: np.ndarray = None,
                    var_order: int = None,
                    n_bootstrap: int = 500,
                    beta_null: np.ndarray = None,
                    seed: int = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Sieve bootstrap for cointegrated time series.
    
    Implements the bootstrap procedure from Xiao (2009), Section 3.2, Steps 1-5:
    
    1. Get residuals from OLS regression
    2. Fit VAR(q) on ŵ_t = (v_t, û_t)
    3. Draw i.i.d. from centered fitted residuals
    4. Generate bootstrap samples using the VAR structure
    5. Reconstruct (y*, x*) under the null hypothesis
    
    Parameters
    ----------
    endog : np.ndarray
        Dependent variable y_t (n,)
    exog : np.ndarray
        Regressors x_t (n,) or (n, k)
    residuals : np.ndarray, optional
        Pre-computed residuals. If None, uses OLS residuals.
    var_order : int, optional
        VAR order q. Default is int(n^(1/3)).
    n_bootstrap : int, default 500
        Number of bootstrap samples to generate
    beta_null : np.ndarray, optional
        Coefficient vector under H_0. Default uses OLS estimates.
    seed : int, optional
        Random seed
        
    Returns
    -------
    y_bootstrap : np.ndarray
        Bootstrap y samples, shape (n_bootstrap, n)
    x_bootstrap : np.ndarray
        Bootstrap x samples, shape (n_bootstrap, n, k)
        
    Reference
    ---------
    Xiao (2009), Section 3.2.
    """
    if seed is not None:
        np.random.seed(seed)
    
    endog = np.asarray(endog).flatten()
    exog = np.asarray(exog)
    if exog.ndim == 1:
        exog = exog.reshape(-1, 1)
    
    n = len(endog)
    k = exog.shape[1]
    
    # Step 1: Get OLS estimates and residuals
    X = np.column_stack([np.ones(n), exog])
    
    if beta_null is None:
        beta_null = np.linalg.lstsq(X, endog, rcond=None)[0]
    
    if residuals is None:
        residuals = endog - X @ beta_null
    
    # Compute v_t = Δx_t
    v = np.diff(exog, axis=0)  # (n-1) x k
    u = residuals[1:]  # Match length with v
    
    # Construct ŵ_t = (v_t, û_t)
    w = np.column_stack([v, u])  # (n-1) x (k+1)
    n_w = len(w)
    
    # Step 2: Fit VAR on ŵ_t
    if var_order is None:
        var_order = max(1, int(n_w**(1/3)))
    q = min(var_order, n_w // 3)
    
    # Build VAR design matrix
    W_lags = np.column_stack([w[q-j-1:n_w-j-1] for j in range(q)])
    W_y = w[q:]
    n_eff = len(W_y)
    
    # VAR coefficients: W_y = W_lags @ B + e
    B_hat, _, _, _ = np.linalg.lstsq(W_lags, W_y, rcond=None)
    
    # Step 3: Get fitted residuals and center them
    e_hat = W_y - W_lags @ B_hat
    e_centered = e_hat - np.mean(e_hat, axis=0)
    
    # Generate bootstrap samples
    y_bootstrap = np.zeros((n_bootstrap, n))
    x_bootstrap = np.zeros((n_bootstrap, n, k))
    
    for b in range(n_bootstrap):
        try:
            # Draw i.i.d. from centered residuals
            indices = np.random.randint(0, len(e_centered), size=n_w)
            e_star = e_centered[indices]
            
            # Generate w* from VAR
            w_star = np.zeros((n_w + q, k + 1))
            w_star[:q] = w[:q]
            
            for t in range(q, n_w + q):
                w_lags_t = w_star[t-q:t][::-1].flatten()
                w_star[t] = w_lags_t @ B_hat.reshape(-1, k + 1).T + e_star[t - q]
            
            w_star = w_star[q:]
            
            # Split into v* and u*
            v_star = w_star[:, :k]
            u_star = w_star[:, k:]
            
            # Step 4: Generate x* by cumulating v*
            x_star = np.zeros((n, k))
            x_star[0] = exog[0]
            x_star[1:] = exog[0] + np.cumsum(v_star, axis=0)
            
            # Step 5: Generate y* under H_0
            X_star = np.column_stack([np.ones(n), x_star])
            y_star = X_star @ beta_null + np.concatenate([[0], u_star.flatten()])
            
            y_bootstrap[b] = y_star
            x_bootstrap[b] = x_star
            
        except Exception as e:
            warnings.warn(f"Bootstrap iteration {b} failed: {e}")
            y_bootstrap[b] = endog
            x_bootstrap[b] = exog
    
    return y_bootstrap, x_bootstrap


def wild_bootstrap(endog: np.ndarray, exog: np.ndarray,
                   residuals: np.ndarray,
                   n_bootstrap: int = 500,
                   distribution: str = 'rademacher',
                   seed: int = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Wild bootstrap for heteroskedasticity-robust inference.
    
    Generates bootstrap samples by multiplying residuals by random weights.
    
    Parameters
    ----------
    endog : np.ndarray
        Dependent variable
    exog : np.ndarray
        Regressors
    residuals : np.ndarray
        Regression residuals
    n_bootstrap : int, default 500
        Number of bootstrap samples
    distribution : str, default 'rademacher'
        Distribution for weights: 'rademacher' (±1) or 'normal'
    seed : int, optional
        Random seed
        
    Returns
    -------
    y_bootstrap : np.ndarray
        Bootstrap y samples
    x_bootstrap : np.ndarray
        Bootstrap x samples (just repeated, not resampled)
    """
    if seed is not None:
        np.random.seed(seed)
    
    endog = np.asarray(endog).flatten()
    exog = np.asarray(exog)
    if exog.ndim == 1:
        exog = exog.reshape(-1, 1)
    
    n = len(endog)
    k = exog.shape[1]
    
    # OLS fitted values
    X = np.column_stack([np.ones(n), exog])
    beta_hat = np.linalg.lstsq(X, endog, rcond=None)[0]
    fitted = X @ beta_hat
    
    y_bootstrap = np.zeros((n_bootstrap, n))
    x_bootstrap = np.tile(exog, (n_bootstrap, 1, 1))
    
    for b in range(n_bootstrap):
        # Generate random weights
        if distribution == 'rademacher':
            weights = np.random.choice([-1, 1], size=n)
        else:
            weights = np.random.randn(n)
        
        # Wild bootstrap residuals
        u_star = residuals * weights
        
        # Bootstrap y
        y_bootstrap[b] = fitted + u_star
    
    return y_bootstrap, x_bootstrap


def bootstrap_quantile_regression(endog: np.ndarray, exog: np.ndarray,
                                   tau: float, 
                                   n_bootstrap: int = 500,
                                   method: str = 'sieve',
                                   seed: int = None) -> dict:
    """
    Bootstrap inference for quantile regression coefficients.
    
    Parameters
    ----------
    endog : np.ndarray
        Dependent variable
    exog : np.ndarray
        Regressors
    tau : float
        Quantile level
    n_bootstrap : int, default 500
        Number of bootstrap replications
    method : str, default 'sieve'
        Bootstrap method: 'sieve' or 'wild'
    seed : int, optional
        Random seed
        
    Returns
    -------
    dict
        Dictionary with 'coefficients', 'std_errors', 'conf_int'
    """
    if seed is not None:
        np.random.seed(seed)
    
    from quantilecoint.core.quantile_regression import QuantileRegression
    
    # Fit original model
    qr = QuantileRegression(endog, exog)
    original = qr.fit(tau=tau)
    
    # Generate bootstrap samples
    if method == 'sieve':
        y_boot, x_boot = sieve_bootstrap(
            endog, exog, 
            n_bootstrap=n_bootstrap, 
            seed=seed
        )
    else:
        y_boot, x_boot = wild_bootstrap(
            endog, exog, 
            original.residuals,
            n_bootstrap=n_bootstrap,
            seed=seed
        )
    
    # Compute bootstrap estimates
    boot_params = []
    
    for b in range(n_bootstrap):
        try:
            qr_boot = QuantileRegression(y_boot[b], x_boot[b])
            result_boot = qr_boot.fit(tau=tau)
            boot_params.append(result_boot.params)
        except:
            continue
    
    boot_params = np.array(boot_params)
    
    # Compute standard errors and confidence intervals
    std_errors = np.std(boot_params, axis=0)
    conf_int = np.column_stack([
        np.percentile(boot_params, 2.5, axis=0),
        np.percentile(boot_params, 97.5, axis=0)
    ])
    
    return {
        'coefficients': original.params,
        'std_errors': std_errors,
        'conf_int': conf_int,
        'boot_params': boot_params,
        'n_success': len(boot_params),
    }
