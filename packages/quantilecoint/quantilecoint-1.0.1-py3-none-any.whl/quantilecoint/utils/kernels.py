"""
Kernel Functions for HAC Covariance Estimation

This module implements kernel functions used in long-run variance estimation
for the fully-modified quantile regression estimator.

Reference:
    Andrews, D.W.K. (1991). Heteroskedasticity and autocorrelation consistent 
    covariance matrix estimation. Econometrica, 59(3), 817-858.
    
    Xiao (2009), Section 2.2, kernel estimate descriptions.
"""

import numpy as np
from typing import Callable, Optional


def bartlett_kernel(x: np.ndarray) -> np.ndarray:
    """
    Bartlett (triangular) kernel.
    
    k(x) = 1 - |x| for |x| <= 1, 0 otherwise
    
    Parameters
    ----------
    x : np.ndarray
        Normalized lag values h/M where h is lag and M is bandwidth
        
    Returns
    -------
    np.ndarray
        Kernel weights
        
    Reference
    ---------
    Andrews (1991), Table I.
    """
    x = np.asarray(x)
    return np.where(np.abs(x) <= 1, 1 - np.abs(x), 0)


def parzen_kernel(x: np.ndarray) -> np.ndarray:
    """
    Parzen kernel.
    
    k(x) = 1 - 6x^2 + 6|x|^3  for |x| <= 0.5
         = 2(1 - |x|)^3       for 0.5 < |x| <= 1
         = 0                  otherwise
    
    Parameters
    ----------
    x : np.ndarray
        Normalized lag values
        
    Returns
    -------
    np.ndarray
        Kernel weights
        
    Reference
    ---------
    Andrews (1991), Table I.
    """
    x = np.asarray(x)
    abs_x = np.abs(x)
    
    result = np.zeros_like(x, dtype=float)
    
    # |x| <= 0.5
    mask1 = abs_x <= 0.5
    result[mask1] = 1 - 6 * abs_x[mask1]**2 + 6 * abs_x[mask1]**3
    
    # 0.5 < |x| <= 1
    mask2 = (abs_x > 0.5) & (abs_x <= 1)
    result[mask2] = 2 * (1 - abs_x[mask2])**3
    
    return result


def quadratic_spectral_kernel(x: np.ndarray) -> np.ndarray:
    """
    Quadratic Spectral (QS) kernel.
    
    k(x) = (25/(12π²x²)) * [sin(6πx/5)/(6πx/5) - cos(6πx/5)]
    
    For x = 0: k(0) = 1
    
    Parameters
    ----------
    x : np.ndarray
        Normalized lag values
        
    Returns
    -------
    np.ndarray
        Kernel weights
        
    Reference
    ---------
    Andrews (1991), Table I.
    """
    x = np.asarray(x, dtype=float)
    result = np.ones_like(x)
    
    # Avoid division by zero
    nonzero = x != 0
    
    if np.any(nonzero):
        z = 6 * np.pi * x[nonzero] / 5
        term1 = np.sin(z) / z
        term2 = np.cos(z)
        result[nonzero] = (25 / (12 * np.pi**2 * x[nonzero]**2)) * (term1 - term2)
    
    return result


def tukey_hanning_kernel(x: np.ndarray) -> np.ndarray:
    """
    Tukey-Hanning kernel.
    
    k(x) = (1 + cos(πx))/2 for |x| <= 1, 0 otherwise
    
    Parameters
    ----------
    x : np.ndarray
        Normalized lag values
        
    Returns
    -------
    np.ndarray
        Kernel weights
    """
    x = np.asarray(x)
    return np.where(np.abs(x) <= 1, (1 + np.cos(np.pi * x)) / 2, 0)


def get_kernel(name: str) -> Callable:
    """
    Get kernel function by name.
    
    Parameters
    ----------
    name : str
        Kernel name: 'bartlett', 'parzen', 'qs', or 'tukey-hanning'
        
    Returns
    -------
    Callable
        Kernel function
    """
    kernels = {
        'bartlett': bartlett_kernel,
        'parzen': parzen_kernel,
        'qs': quadratic_spectral_kernel,
        'quadratic-spectral': quadratic_spectral_kernel,
        'tukey-hanning': tukey_hanning_kernel,
    }
    
    name_lower = name.lower().replace('_', '-')
    if name_lower not in kernels:
        raise ValueError(
            f"Unknown kernel: {name}. Available: {list(kernels.keys())}"
        )
    
    return kernels[name_lower]


def get_bandwidth(n: int, kernel: str = 'bartlett', 
                  method: str = 'andrews') -> int:
    """
    Compute optimal bandwidth for kernel estimation.
    
    Parameters
    ----------
    n : int
        Sample size
    kernel : str, default 'bartlett'
        Kernel name
    method : str, default 'andrews'
        Bandwidth selection method: 'andrews' or 'newey-west'
        
    Returns
    -------
    int
        Optimal bandwidth M
        
    Notes
    -----
    Andrews (1991) suggests M = O(n^(1/3)) for many kernels.
    Xiao (2009), Section 2.2 states: "M → ∞ and M/n → 0 
    (say M = O(n^(1/3)) for many commonly used kernels)"
    
    Reference
    ---------
    Andrews (1991), Theorem 1.
    Xiao (2009), after equation (4).
    """
    if method == 'andrews':
        # Standard rate for Bartlett/Parzen kernels
        if kernel.lower() in ['bartlett', 'parzen', 'tukey-hanning']:
            # M = c * n^(1/3), with typical c between 1 and 2
            M = int(np.ceil(1.3 * n**(1/3)))
        else:  # QS kernel
            # M = c * n^(1/5) for QS kernel
            M = int(np.ceil(1.3 * n**(1/5)))
    elif method == 'newey-west':
        # Newey-West rule: M = floor(4(n/100)^(2/9))
        M = int(np.floor(4 * (n / 100)**(2/9)))
    else:
        raise ValueError(f"Unknown bandwidth method: {method}")
    
    # Ensure M is at least 1 and at most n-1
    M = max(1, min(M, n - 1))
    
    return M
