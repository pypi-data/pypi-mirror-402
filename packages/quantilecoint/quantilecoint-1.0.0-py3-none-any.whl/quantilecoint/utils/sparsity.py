"""
Sparsity Function Estimation

This module implements estimators for the sparsity function f(F^{-1}(τ)),
which is the reciprocal of the probability density function evaluated at
the τ-th quantile. The sparsity function appears in the limiting distribution
of the quantile regression estimator.

Reference:
    Siddiqui, M. (1960). Distribution of quantiles from a bivariate population.
    Journal of Research of the National Bureau of Standards, 64B, 145-150.
    
    Bofinger, E. (1975). Estimation of a density function using order statistics.
    Australian Journal of Statistics, 17, 1-7.
    
    Xiao (2009), Section 2.2, and equation (4).
"""

import numpy as np
from scipy import stats
from typing import Optional


def estimate_sparsity(residuals: np.ndarray, tau: float, 
                      method: str = 'bofinger') -> float:
    """
    Estimate the sparsity function f(F^{-1}(τ)).
    
    The sparsity function is the reciprocal of the density at the quantile:
    s(τ) = 1/f(F^{-1}(τ))
    
    This function returns f(F^{-1}(τ)), not the sparsity itself.
    
    Parameters
    ----------
    residuals : np.ndarray
        Regression residuals (centered at quantile)
    tau : float
        Quantile level in (0, 1)
    method : str, default 'bofinger'
        Estimation method: 'bofinger', 'hall-sheather', or 'kernel'
        
    Returns
    -------
    float
        Estimate of f(F^{-1}(τ))
        
    Reference
    ---------
    Xiao (2009), Section 2.2: "Let f(F̂^{-1}(τ)) be a nonparametric sparsity 
    estimator of f(F^{-1}(τ)) (see, e.g., Siddiqui (1960), Bofinger (1975))"
    """
    if method == 'bofinger':
        return estimate_sparsity_bofinger(residuals, tau)
    elif method == 'hall-sheather':
        return estimate_sparsity_hall_sheather(residuals, tau)
    elif method == 'kernel':
        return estimate_sparsity_kernel(residuals, tau)
    else:
        raise ValueError(f"Unknown sparsity estimation method: {method}")


def estimate_sparsity_bofinger(residuals: np.ndarray, tau: float) -> float:
    """
    Bofinger (1975) sparsity estimator.
    
    Uses difference quotients based on order statistics:
    
    f̂(F^{-1}(τ)) = (2h_n) / (x_{[n(τ+h_n)]} - x_{[n(τ-h_n)]})
    
    where h_n = n^{-1/3} * [1.5 * φ(Φ^{-1}(τ))^2 / (2(Φ^{-1}(τ))^2 + 1)]^{1/3}
    
    Parameters
    ----------
    residuals : np.ndarray
        Regression residuals
    tau : float
        Quantile level
        
    Returns
    -------
    float
        Sparsity estimate f̂(F^{-1}(τ))
        
    Reference
    ---------
    Bofinger, E. (1975). Estimation of a density function using order statistics.
    Australian Journal of Statistics, 17, 1-7.
    """
    n = len(residuals)
    residuals_sorted = np.sort(residuals)
    
    # Normal quantile
    z_tau = stats.norm.ppf(tau)
    phi_z = stats.norm.pdf(z_tau)
    
    # Bofinger bandwidth
    # h_n = n^{-1/3} * c_τ where c_τ depends on τ
    c_tau = (1.5 * phi_z**2 / (2 * z_tau**2 + 1))**(1/3)
    h_n = n**(-1/3) * c_tau
    
    # Ensure h_n is reasonable
    h_n = max(h_n, 0.05)  # At least 5%
    h_n = min(h_n, min(tau, 1 - tau) - 0.01)  # Don't exceed bounds
    
    # Get quantile indices
    idx_upper = min(int(np.ceil(n * (tau + h_n))), n - 1)
    idx_lower = max(int(np.floor(n * (tau - h_n))), 0)
    
    # Difference quotient
    q_upper = residuals_sorted[idx_upper]
    q_lower = residuals_sorted[idx_lower]
    
    if q_upper - q_lower < 1e-10:
        # Avoid division by zero, use kernel estimate as fallback
        return estimate_sparsity_kernel(residuals, tau)
    
    # f̂(F^{-1}(τ)) = 2h_n / (q_upper - q_lower)
    f_hat = 2 * h_n / (q_upper - q_lower)
    
    return f_hat


def estimate_sparsity_hall_sheather(residuals: np.ndarray, tau: float,
                                     alpha: float = 0.05) -> float:
    """
    Hall-Sheather sparsity estimator.
    
    Uses a bandwidth optimized for confidence interval construction.
    
    Parameters
    ----------
    residuals : np.ndarray
        Regression residuals
    tau : float
        Quantile level
    alpha : float, default 0.05
        Significance level for confidence intervals
        
    Returns
    -------
    float
        Sparsity estimate
        
    Reference
    ---------
    Hall, P. & Sheather, S.J. (1988). On the distribution of a studentized 
    quantile. Journal of the Royal Statistical Society B, 50, 381-391.
    """
    n = len(residuals)
    residuals_sorted = np.sort(residuals)
    
    # Normal quantiles
    z_tau = stats.norm.ppf(tau)
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    phi_z = stats.norm.pdf(z_tau)
    
    # Hall-Sheather bandwidth
    h_n = n**(-1/3) * z_alpha**(2/3) * (
        1.5 * phi_z**2 / (2 * z_tau**2 + 1)
    )**(1/3)
    
    # Clamp bandwidth
    h_n = max(h_n, 0.05)
    h_n = min(h_n, min(tau, 1 - tau) - 0.01)
    
    # Get order statistics
    idx_upper = min(int(np.ceil(n * (tau + h_n))), n - 1)
    idx_lower = max(int(np.floor(n * (tau - h_n))), 0)
    
    q_upper = residuals_sorted[idx_upper]
    q_lower = residuals_sorted[idx_lower]
    
    if q_upper - q_lower < 1e-10:
        return estimate_sparsity_kernel(residuals, tau)
    
    return 2 * h_n / (q_upper - q_lower)


def estimate_sparsity_kernel(residuals: np.ndarray, tau: float) -> float:
    """
    Kernel density estimation of the sparsity function.
    
    Uses Gaussian kernel density estimation to estimate f(F^{-1}(τ)).
    
    Parameters
    ----------
    residuals : np.ndarray
        Regression residuals
    tau : float
        Quantile level
        
    Returns
    -------
    float
        Sparsity estimate
    """
    n = len(residuals)
    
    # Silverman's rule of thumb for bandwidth
    std = np.std(residuals, ddof=1)
    iqr = np.percentile(residuals, 75) - np.percentile(residuals, 25)
    h = 0.9 * min(std, iqr / 1.34) * n**(-0.2)
    
    # Get empirical quantile
    q_tau = np.percentile(residuals, tau * 100)
    
    # Gaussian kernel density estimate at quantile
    kernel_values = stats.norm.pdf((residuals - q_tau) / h)
    f_hat = np.mean(kernel_values) / h
    
    # Ensure positive
    f_hat = max(f_hat, 1e-10)
    
    return f_hat
