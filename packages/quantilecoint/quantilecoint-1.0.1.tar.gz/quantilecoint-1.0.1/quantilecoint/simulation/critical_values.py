"""
Critical Value Simulation for Quantile Cointegration Tests

This module generates critical values for the test statistics via Monte Carlo
simulation of the limiting Brownian motion distributions.

Reference:
    Xiao, Z. (2009). Quantile cointegrating regression. 
    Journal of Econometrics, 150(2), 248-260.
"""

import numpy as np
from scipy import stats
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class CriticalValueTable:
    """
    Container for critical value tables.
    
    Attributes
    ----------
    test_type : str
        Type of test
    k : int
        Number of regressors
    n_simulations : int
        Number of Monte Carlo replications
    critical_values : dict
        Dictionary mapping significance levels to critical values
    quantiles_tested : list
        Quantile levels if applicable
    """
    test_type: str
    k: int
    n_simulations: int
    critical_values: Dict[str, float]
    quantiles_tested: list = None
    
    def __repr__(self) -> str:
        return (f"CriticalValueTable(test_type='{self.test_type}', k={self.k}, "
                f"n_simulations={self.n_simulations})")
    
    def to_latex(self) -> str:
        """Generate LaTeX table format."""
        lines = []
        lines.append("\\begin{tabular}{lc}")
        lines.append("\\hline")
        lines.append("Significance Level & Critical Value \\\\")
        lines.append("\\hline")
        for level, value in self.critical_values.items():
            lines.append(f"{level} & {value:.4f} \\\\")
        lines.append("\\hline")
        lines.append("\\end{tabular}")
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'test_type': self.test_type,
            'k': self.k,
            'n_simulations': self.n_simulations,
            'critical_values': self.critical_values,
            'quantiles_tested': self.quantiles_tested,
        }


def simulate_wald_critical_values(k: int, n_simulations: int = 100000,
                                   seed: int = None) -> CriticalValueTable:
    """
    Simulate critical values for Wald test.
    
    Under H_0, W_n(τ) → χ²_q, so we use the chi-square distribution directly.
    
    Parameters
    ----------
    k : int
        Degrees of freedom (number of restrictions)
    n_simulations : int
        Number of simulations
    seed : int, optional
        Random seed
        
    Returns
    -------
    CriticalValueTable
        Critical values at standard significance levels
    """
    # For Wald test, use chi-square distribution
    critical_values = {
        '1%': float(stats.chi2.ppf(0.99, k)),
        '5%': float(stats.chi2.ppf(0.95, k)),
        '10%': float(stats.chi2.ppf(0.90, k)),
    }
    
    return CriticalValueTable(
        test_type='wald',
        k=k,
        n_simulations=n_simulations,
        critical_values=critical_values,
    )


def simulate_stability_critical_values(k: int = 1, n_simulations: int = 10000,
                                        n_quantiles: int = 19,
                                        n_steps: int = 1000,
                                        seed: int = None) -> CriticalValueTable:
    """
    Simulate critical values for stability test (constant vs. varying coefficients).
    
    Simulates the limiting distribution from Xiao (2009), Section 3.2:
    
        sup_τ |V_n(τ)| → sup_τ |[∫B_v B_v']^{-1} ∫B_v d(B*_ψ - f(τ)B*_ε)|
    
    Parameters
    ----------
    k : int, default 1
        Number of slope coefficients
    n_simulations : int, default 10000
        Number of Monte Carlo replications
    n_quantiles : int, default 19
        Number of quantile grid points
    n_steps : int, default 1000
        Number of time steps for Brownian motion
    seed : int, optional
        Random seed
        
    Returns
    -------
    CriticalValueTable
        Critical values
    """
    if seed is not None:
        np.random.seed(seed)
    
    quantiles = np.linspace(0.1, 0.9, n_quantiles)
    sup_stats = []
    
    for _ in range(n_simulations):
        # Simulate Brownian motions
        dW_v = np.random.randn(n_steps, k) / np.sqrt(n_steps)
        dW_psi = np.random.randn(n_steps) / np.sqrt(n_steps)
        dW_eps = np.random.randn(n_steps) / np.sqrt(n_steps)
        
        B_v = np.cumsum(dW_v, axis=0)
        B_psi = np.cumsum(dW_psi)
        B_eps = np.cumsum(dW_eps)
        
        # Compute ∫B_v B_v'
        int_BvBv = np.sum(B_v.T @ B_v) / n_steps
        
        max_stat = 0
        for tau in quantiles:
            f_tau = stats.norm.pdf(stats.norm.ppf(tau))
            
            # B*_ψ - f(τ)B*_ε
            adjusted_process = B_psi - f_tau * B_eps
            dB_adj = np.diff(np.concatenate([[0], adjusted_process]))
            
            # ∫B_v dB_adj
            int_BvdB = np.sum(B_v * dB_adj.reshape(-1, 1), axis=0)
            
            # V(τ) = [∫B_v B_v']^{-1} ∫B_v dB_adj
            if k == 1:
                V_tau = int_BvdB / (int_BvBv + 1e-10)
            else:
                V_tau = int_BvdB / (int_BvBv + 1e-10)
            
            max_stat = max(max_stat, np.max(np.abs(V_tau)))
        
        sup_stats.append(max_stat)
    
    sup_stats = np.array(sup_stats)
    
    critical_values = {
        '1%': float(np.percentile(sup_stats, 99)),
        '5%': float(np.percentile(sup_stats, 95)),
        '10%': float(np.percentile(sup_stats, 90)),
    }
    
    return CriticalValueTable(
        test_type='stability',
        k=k,
        n_simulations=n_simulations,
        critical_values=critical_values,
        quantiles_tested=list(quantiles),
    )


def simulate_cointegration_critical_values(k: int = 1, test_type: str = 'ks',
                                            n_simulations: int = 50000,
                                            n_steps: int = 1000,
                                            seed: int = None) -> CriticalValueTable:
    """
    Simulate critical values for CUSUM cointegration test.
    
    Under H_0, Ŷ_n(r) → W̃(r), a standardized residual Brownian motion.
    
    Parameters
    ----------
    k : int, default 1
        Number of regressors
    test_type : str, default 'ks'
        'ks' for Kolmogorov-Smirnov, 'cvm' for Cramér-von Mises
    n_simulations : int, default 50000
        Number of Monte Carlo replications
    n_steps : int, default 1000
        Number of time steps
    seed : int, optional
        Random seed
        
    Returns
    -------
    CriticalValueTable
        Critical values
    """
    if seed is not None:
        np.random.seed(seed)
    
    test_stats = []
    
    for _ in range(n_simulations):
        # Simulate k+1 independent Brownian motions
        dW = np.random.randn(n_steps, k + 1) / np.sqrt(n_steps)
        W = np.cumsum(dW, axis=0)
        
        W1 = W[:, 0]  # For residuals
        W2 = W[:, 1:]  # For regressors
        
        r = np.arange(1, n_steps + 1) / n_steps
        
        # Tied-down process accounting for regression
        # W̃ = W1 - ∫dW1 W2' [∫W2 W2']^{-1} ∫W2 dr
        int_W2W2 = W2.T @ W2 / n_steps
        int_dW1_W2 = np.sum(np.diff(np.concatenate([[0], W1])).reshape(-1, 1) * W2, axis=0)
        
        try:
            correction = W2 @ np.linalg.solve(int_W2W2 + 1e-8 * np.eye(k), int_dW1_W2)
        except:
            correction = np.zeros_like(W1)
        
        W_tilde = W1 - correction
        
        # Tie down at endpoint
        W_tilde = W_tilde - r * W_tilde[-1]
        
        if test_type.lower() == 'ks':
            test_stats.append(np.max(np.abs(W_tilde)))
        else:
            test_stats.append(np.mean(W_tilde**2))
    
    test_stats = np.array(test_stats)
    
    critical_values = {
        '1%': float(np.percentile(test_stats, 99)),
        '5%': float(np.percentile(test_stats, 95)),
        '10%': float(np.percentile(test_stats, 90)),
    }
    
    return CriticalValueTable(
        test_type=f'cointegration_{test_type}',
        k=k,
        n_simulations=n_simulations,
        critical_values=critical_values,
    )


def simulate_critical_values(test_type: str, k: int = 1,
                             n_simulations: int = 10000,
                             seed: int = None, **kwargs) -> CriticalValueTable:
    """
    Unified function to simulate critical values for any test type.
    
    Parameters
    ----------
    test_type : str
        Type of test: 'wald', 'stability', 'cointegration_ks', 'cointegration_cvm'
    k : int
        Number of regressors or degrees of freedom
    n_simulations : int
        Number of Monte Carlo replications
    seed : int, optional
        Random seed
    **kwargs
        Additional arguments passed to specific simulation functions
        
    Returns
    -------
    CriticalValueTable
        Critical values
    """
    test_type_lower = test_type.lower()
    
    if test_type_lower == 'wald':
        return simulate_wald_critical_values(k, n_simulations, seed)
    elif test_type_lower == 'stability':
        return simulate_stability_critical_values(k, n_simulations, seed=seed, **kwargs)
    elif test_type_lower in ['cointegration_ks', 'cointegration_cvm']:
        coint_type = 'ks' if 'ks' in test_type_lower else 'cvm'
        return simulate_cointegration_critical_values(k, coint_type, n_simulations, seed=seed, **kwargs)
    else:
        raise ValueError(f"Unknown test type: {test_type}")


def get_critical_value(test_type: str, k: int = 1, alpha: float = 0.05) -> float:
    """
    Get critical value from analytical distribution or standard tables.
    
    Parameters
    ----------
    test_type : str
        Type of test
    k : int
        Degrees of freedom
    alpha : float
        Significance level
        
    Returns
    -------
    float
        Critical value
    """
    if test_type.lower() == 'wald':
        return float(stats.chi2.ppf(1 - alpha, k))
    else:
        # Use simulation
        table = simulate_critical_values(test_type, k, n_simulations=10000)
        level = f'{int(alpha * 100)}%'
        if level in table.critical_values:
            return table.critical_values[level]
        else:
            return table.critical_values['5%']
