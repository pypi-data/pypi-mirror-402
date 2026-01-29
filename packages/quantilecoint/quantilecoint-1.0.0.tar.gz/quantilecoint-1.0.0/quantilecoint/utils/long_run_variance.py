"""
Long-Run Variance Estimation

This module implements HAC (Heteroskedasticity and Autocorrelation Consistent)
covariance matrix estimation for the fully-modified quantile regression.

The key quantities from Xiao (2009), Section 2.2:
- Ω_vv: Long-run variance of v_t = Δx_t
- Ω_vψ: Long-run covariance between v_t and ψ_τ(u_tτ)
- λ_vψ: One-sided long-run covariance
- ω²_ψ.v: Conditional variance of ψ given v

Reference:
    Andrews, D.W.K. (1991). Heteroskedasticity and autocorrelation consistent 
    covariance matrix estimation. Econometrica, 59(3), 817-858.
    
    Xiao (2009), Section 2.2, equations around (4).
"""

import numpy as np
from typing import Tuple, Optional, Callable
from quantilecoint.utils.kernels import get_kernel, get_bandwidth


def sample_autocovariance(x: np.ndarray, y: np.ndarray = None, 
                          lag: int = 0) -> np.ndarray:
    """
    Compute sample autocovariance C_xy(h) at lag h.
    
    C_xy(h) = (1/n) * Σ x_t * y_{t+h}'
    
    Parameters
    ----------
    x : np.ndarray
        First time series (n,) or (n, k)
    y : np.ndarray, optional
        Second time series. If None, computes autocovariance of x.
    lag : int, default 0
        Lag h (can be negative)
        
    Returns
    -------
    np.ndarray
        Sample covariance at specified lag
        
    Reference
    ---------
    Xiao (2009), after equation (4): "C_vψ(h) = n^{-1} Σ' v_t ψ_τ(û_{t+h,τ})"
    """
    x = np.atleast_2d(x)
    if x.shape[0] < x.shape[1]:
        x = x.T
    n = x.shape[0]
    
    if y is None:
        y = x
    else:
        y = np.atleast_2d(y)
        if y.shape[0] < y.shape[1]:
            y = y.T
    
    if lag >= 0:
        x_slice = x[:n-lag] if lag > 0 else x
        y_slice = y[lag:] if lag > 0 else y
    else:
        x_slice = x[-lag:]
        y_slice = y[:n+lag]
    
    # Compute sample covariance
    n_eff = x_slice.shape[0]
    cov = (x_slice.T @ y_slice) / n_eff
    
    return np.squeeze(cov)


def long_run_variance(x: np.ndarray, y: np.ndarray = None,
                      kernel: str = 'bartlett', bandwidth: int = None,
                      demean: bool = True) -> np.ndarray:
    """
    Compute long-run variance (HAC estimator).
    
    Ω̂_xy = Σ_{h=-M}^{M} k(h/M) * C_xy(h)
    
    Parameters
    ----------
    x : np.ndarray
        First time series (n,) or (n, k)
    y : np.ndarray, optional
        Second time series. If None, computes long-run variance of x.
    kernel : str, default 'bartlett'
        Kernel function name
    bandwidth : int, optional
        Bandwidth M. If None, uses automatic selection.
    demean : bool, default True
        Whether to demean the series before estimation
        
    Returns
    -------
    np.ndarray
        Long-run variance/covariance estimate
        
    Reference
    ---------
    Xiao (2009), equation (4) and surrounding text.
    Andrews (1991).
    """
    x = np.atleast_2d(x)
    if x.shape[0] < x.shape[1]:
        x = x.T
    n = x.shape[0]
    
    if y is None:
        y = x
    else:
        y = np.atleast_2d(y)
        if y.shape[0] < y.shape[1]:
            y = y.T
    
    # Demean if requested
    if demean:
        x = x - np.mean(x, axis=0)
        y = y - np.mean(y, axis=0)
    
    # Get kernel function
    k_func = get_kernel(kernel)
    
    # Get bandwidth if not specified
    if bandwidth is None:
        bandwidth = get_bandwidth(n, kernel)
    M = bandwidth
    
    # Compute long-run variance
    # Start with lag 0
    omega = sample_autocovariance(x, y, lag=0)
    
    # Add weighted contributions from positive and negative lags
    for h in range(1, M + 1):
        weight = k_func(h / M)
        cov_h = sample_autocovariance(x, y, lag=h)
        cov_neg_h = sample_autocovariance(x, y, lag=-h)
        omega = omega + weight * (cov_h + cov_neg_h)
    
    return omega


def one_sided_long_run_variance(x: np.ndarray, y: np.ndarray = None,
                                 kernel: str = 'bartlett', 
                                 bandwidth: int = None) -> np.ndarray:
    """
    Compute one-sided long-run covariance λ_xy.
    
    λ̂_xy = Σ_{h=1}^{M} k(h/M) * C_xy(h)
    
    This is the one-sided contribution that creates bias in the quantile
    regression estimator.
    
    Parameters
    ----------
    x : np.ndarray
        First time series
    y : np.ndarray, optional
        Second time series
    kernel : str, default 'bartlett'
        Kernel function name
    bandwidth : int, optional
        Bandwidth M
        
    Returns
    -------
    np.ndarray
        One-sided long-run covariance
        
    Reference
    ---------
    Xiao (2009), Theorem 1: "λ_vψ is the one-sided long-run covariance 
    between v_t and ψ_τ(u_tτ)"
    """
    x = np.atleast_2d(x)
    if x.shape[0] < x.shape[1]:
        x = x.T
    n = x.shape[0]
    
    if y is None:
        y = x
    else:
        y = np.atleast_2d(y)
        if y.shape[0] < y.shape[1]:
            y = y.T
    
    # Demean
    x = x - np.mean(x, axis=0)
    y = y - np.mean(y, axis=0)
    
    # Get kernel function
    k_func = get_kernel(kernel)
    
    # Get bandwidth if not specified
    if bandwidth is None:
        bandwidth = get_bandwidth(n, kernel)
    M = bandwidth
    
    # Compute one-sided long-run covariance (only positive lags)
    lambda_xy = np.zeros_like(sample_autocovariance(x, y, lag=0))
    
    for h in range(1, M + 1):
        weight = k_func(h / M)
        lambda_xy = lambda_xy + weight * sample_autocovariance(x, y, lag=h)
    
    return lambda_xy


def estimate_omega(v: np.ndarray, psi: np.ndarray, 
                   kernel: str = 'bartlett',
                   bandwidth: int = None) -> dict:
    """
    Estimate all long-run covariance components needed for fully-modified
    quantile regression.
    
    Components from Xiao (2009), Section 2.2:
    - Ω_vv: Long-run variance of v_t
    - Ω_vψ: Long-run covariance of v_t and ψ_τ(u_tτ)
    - Ω_ψψ (ω²_ψ): Long-run variance of ψ_τ(u_tτ)
    - λ_vψ: One-sided long-run covariance
    - λ_vv: One-sided long-run variance
    - ω²_ψ.v: Conditional variance ω²_ψ - Ω_ψv Ω_vv^{-1} Ω_vψ
    - λ⁺_vψ: Adjusted one-sided covariance λ_vψ - λ_vv Ω_vv^{-1} Ω_vψ
    
    Parameters
    ----------
    v : np.ndarray
        Differenced regressors v_t = Δx_t, shape (n,) or (n, k)
    psi : np.ndarray
        ψ_τ(u_tτ) = τ - I(u_tτ < 0), shape (n,)
    kernel : str, default 'bartlett'
        Kernel function name
    bandwidth : int, optional
        Bandwidth M
        
    Returns
    -------
    dict
        Dictionary with keys: 'omega_vv', 'omega_vpsi', 'omega_psi',
        'lambda_vpsi', 'lambda_vv', 'omega_psi_v', 'lambda_vpsi_plus'
        
    Reference
    ---------
    Xiao (2009), Section 2.2, equation (4) and Theorem 2.
    """
    v = np.atleast_2d(v)
    if v.shape[0] < v.shape[1]:
        v = v.T
    psi = np.atleast_1d(psi).reshape(-1, 1)
    
    n = v.shape[0]
    k = v.shape[1]
    
    if bandwidth is None:
        bandwidth = get_bandwidth(n, kernel)
    
    # Long-run variances and covariances
    omega_vv = long_run_variance(v, kernel=kernel, bandwidth=bandwidth)
    omega_vpsi = long_run_variance(v, psi, kernel=kernel, bandwidth=bandwidth)
    omega_psi = long_run_variance(psi, kernel=kernel, bandwidth=bandwidth)
    
    # One-sided long-run covariances
    lambda_vpsi = one_sided_long_run_variance(v, psi, kernel=kernel, 
                                               bandwidth=bandwidth)
    lambda_vv = one_sided_long_run_variance(v, kernel=kernel, 
                                             bandwidth=bandwidth)
    
    # Ensure omega_vv is matrix for inversion
    omega_vv = np.atleast_2d(omega_vv)
    if omega_vv.ndim == 1:
        omega_vv = omega_vv.reshape(1, 1)
    
    # Conditional variance: ω²_ψ.v = ω²_ψ - Ω_ψv Ω_vv^{-1} Ω_vψ
    omega_vpsi = np.atleast_1d(omega_vpsi).reshape(-1, 1)
    
    try:
        omega_vv_inv = np.linalg.inv(omega_vv)
        omega_psi_v = omega_psi - omega_vpsi.T @ omega_vv_inv @ omega_vpsi
        omega_psi_v = float(omega_psi_v.squeeze())
    except np.linalg.LinAlgError:
        # Singular matrix, use pseudoinverse
        omega_vv_inv = np.linalg.pinv(omega_vv)
        omega_psi_v = omega_psi - omega_vpsi.T @ omega_vv_inv @ omega_vpsi
        omega_psi_v = float(np.abs(omega_psi_v.squeeze()))
    
    # Ensure positive
    omega_psi_v = max(omega_psi_v, 1e-10)
    
    # Adjusted one-sided covariance: λ⁺_vψ = λ_vψ - λ_vv Ω_vv^{-1} Ω_vψ
    lambda_vv = np.atleast_2d(lambda_vv)
    lambda_vpsi = np.atleast_1d(lambda_vpsi).reshape(-1, 1)
    
    try:
        lambda_vpsi_plus = lambda_vpsi - lambda_vv @ omega_vv_inv @ omega_vpsi
    except:
        lambda_vpsi_plus = lambda_vpsi
    
    return {
        'omega_vv': omega_vv,
        'omega_vv_inv': omega_vv_inv,
        'omega_vpsi': omega_vpsi.flatten(),
        'omega_psi': float(omega_psi),
        'lambda_vpsi': lambda_vpsi.flatten(),
        'lambda_vv': lambda_vv,
        'omega_psi_v': omega_psi_v,
        'lambda_vpsi_plus': lambda_vpsi_plus.flatten(),
        'bandwidth': bandwidth,
    }
