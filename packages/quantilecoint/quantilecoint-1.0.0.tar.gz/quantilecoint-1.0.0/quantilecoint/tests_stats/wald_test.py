"""
Wald Test for Linear Restrictions on Cointegrating Coefficients

This module implements the Wald test from Xiao (2009), Theorem 3, for testing
linear restrictions on the cointegrating coefficients:

    H_0: Rβ = r

The test statistic from Section 2.3:

    W_n(τ) = [f(F̂^{-1}(τ))/ω̂_ψ.v] × (Rβ̂⁺(τ) - r)' × [R M_X^{-1} R']^{-1} × (Rβ̂⁺(τ) - r)

Under H_0, W_n(τ) → χ²_q where q is the number of restrictions.

Reference:
    Xiao, Z. (2009). Quantile cointegrating regression. 
    Journal of Econometrics, 150(2), 248-260. Section 2.3, Theorem 3.
"""

import numpy as np
from scipy import stats
from typing import Union, Optional
from dataclasses import dataclass


@dataclass
class WaldTestResult:
    """
    Results from Wald test for linear restrictions.
    
    Attributes
    ----------
    statistic : float
        Wald test statistic W_n(τ)
    pvalue : float
        P-value from χ² distribution
    df : int
        Degrees of freedom (number of restrictions q)
    tau : float
        Quantile level
    R : np.ndarray
        Restriction matrix
    r : np.ndarray
        Restriction values
    restricted_value : np.ndarray
        Value of Rβ̂⁺(τ) - r under the estimates
    """
    statistic: float
    pvalue: float
    df: int
    tau: float
    R: np.ndarray
    r: np.ndarray
    restricted_value: np.ndarray
    
    def __repr__(self) -> str:
        return (f"WaldTestResult(statistic={self.statistic:.4f}, "
                f"pvalue={self.pvalue:.4f}, df={self.df})")
    
    def summary(self) -> str:
        """Generate formatted summary."""
        lines = []
        lines.append("=" * 60)
        lines.append("            Wald Test for Linear Restrictions")
        lines.append("=" * 60)
        lines.append(f"Quantile (τ):              {self.tau:.4f}")
        lines.append(f"Number of restrictions:    {self.df}")
        lines.append(f"Wald statistic:            {self.statistic:.4f}")
        lines.append(f"P-value (χ²_{self.df}):          {self.pvalue:.4f}")
        lines.append("-" * 60)
        
        if self.pvalue < 0.01:
            conclusion = "Reject H_0 at 1% level ***"
        elif self.pvalue < 0.05:
            conclusion = "Reject H_0 at 5% level **"
        elif self.pvalue < 0.10:
            conclusion = "Reject H_0 at 10% level *"
        else:
            conclusion = "Fail to reject H_0"
        
        lines.append(f"Conclusion:                {conclusion}")
        lines.append("=" * 60)
        
        return "\n".join(lines)


def wald_test(results, R: np.ndarray, r: np.ndarray = None,
              use_robust: bool = True) -> WaldTestResult:
    """
    Perform Wald test for linear restrictions on cointegrating coefficients.
    
    Tests H_0: Rβ = r using the Wald statistic from Xiao (2009), Theorem 3:
    
        W_n(τ) = [f(F̂^{-1}(τ))/ω̂_ψ.v] × (Rβ̂⁺(τ) - r)' × [R M_X^{-1} R']^{-1} × (Rβ̂⁺(τ) - r)
    
    Under H_0, W_n(τ) → χ²_q
    
    Parameters
    ----------
    results : FullyModifiedResults or AugmentedResults
        Results from fully-modified or augmented quantile regression
    R : np.ndarray
        Restriction matrix of shape (q, k+1) where q is number of restrictions
        and k+1 is number of coefficients (including constant)
    r : np.ndarray, optional
        Restriction values of shape (q,). Default is zeros.
    use_robust : bool, default True
        Whether to use robust (HAC) standard errors
        
    Returns
    -------
    WaldTestResult
        Test results including statistic, p-value, and degrees of freedom
        
    Examples
    --------
    >>> # Test H_0: β_1 = 1
    >>> R = np.array([[0, 1]])  # Select second coefficient (first slope)
    >>> r = np.array([1])
    >>> result = wald_test(fm_results, R, r)
    >>> print(result.summary())
    
    >>> # Test H_0: β_1 = β_2
    >>> R = np.array([[0, 1, -1]])  # β_1 - β_2 = 0
    >>> result = wald_test(fm_results, R)
    
    Reference
    ---------
    Xiao (2009), Section 2.3, Theorem 3.
    """
    R = np.atleast_2d(R)
    q, p = R.shape  # q restrictions, p coefficients
    
    if r is None:
        r = np.zeros(q)
    r = np.atleast_1d(r)
    
    if len(r) != q:
        raise ValueError(f"r must have {q} elements, got {len(r)}")
    
    # Get coefficient estimates
    beta_hat = results.params
    
    if len(beta_hat) != p:
        raise ValueError(
            f"R has {p} columns but there are {len(beta_hat)} coefficients"
        )
    
    # Compute Rβ̂ - r
    restriction_value = R @ beta_hat - r
    
    # Get variance-covariance matrix
    # For FullyModifiedResults, we can use the asymptotic variance
    tau = results.tau
    nobs = results.nobs
    
    # Get sparsity and conditional variance
    if hasattr(results, 'sparsity'):
        f_tau = results.sparsity
    else:
        from quantilecoint.utils.sparsity import estimate_sparsity
        f_tau = estimate_sparsity(results.residuals, tau)
    
    if hasattr(results, 'omega_psi_v'):
        omega_psi_v = results.omega_psi_v
    else:
        omega_psi_v = tau * (1 - tau)  # Approximation for i.i.d. case
    
    # Compute M_X = (1/n) Σ x_t x_t'
    X = results._exog
    M_X = (X.T @ X) / nobs
    
    try:
        M_X_inv = np.linalg.inv(M_X)
    except np.linalg.LinAlgError:
        M_X_inv = np.linalg.pinv(M_X)
    
    # Variance of β̂⁺: (ω²_ψ.v / f²) × M_X^{-1} / n
    var_beta = (omega_psi_v / f_tau**2) * M_X_inv / nobs
    
    # Variance of Rβ̂: R × Var(β̂) × R'
    var_Rbeta = R @ var_beta @ R.T
    
    try:
        var_Rbeta_inv = np.linalg.inv(var_Rbeta)
    except np.linalg.LinAlgError:
        var_Rbeta_inv = np.linalg.pinv(var_Rbeta)
    
    # Wald statistic: (Rβ̂ - r)' × [Var(Rβ̂)]^{-1} × (Rβ̂ - r)
    W_n = float(restriction_value @ var_Rbeta_inv @ restriction_value)
    
    # P-value from chi-square distribution
    pvalue = 1 - stats.chi2.cdf(W_n, q)
    
    return WaldTestResult(
        statistic=W_n,
        pvalue=pvalue,
        df=q,
        tau=tau,
        R=R,
        r=r,
        restricted_value=restriction_value,
    )


def test_coef_equals(results, coef_idx: int, value: float) -> WaldTestResult:
    """
    Test if a single coefficient equals a specified value.
    
    Tests H_0: β_j = value
    
    Parameters
    ----------
    results : FullyModifiedResults or AugmentedResults
        Regression results
    coef_idx : int
        Index of coefficient to test (0 for constant, 1 for first slope, etc.)
    value : float
        Value to test against
        
    Returns
    -------
    WaldTestResult
        Test results
    """
    p = len(results.params)
    R = np.zeros((1, p))
    R[0, coef_idx] = 1
    r = np.array([value])
    
    return wald_test(results, R, r)


def test_coef_equals_zero(results, coef_indices: Union[int, list]) -> WaldTestResult:
    """
    Test if coefficients are jointly equal to zero.
    
    Tests H_0: β_{i_1} = β_{i_2} = ... = β_{i_q} = 0
    
    Parameters
    ----------
    results : FullyModifiedResults or AugmentedResults
        Regression results
    coef_indices : int or list
        Index or indices of coefficients to test
        
    Returns
    -------
    WaldTestResult
        Test results
    """
    if isinstance(coef_indices, int):
        coef_indices = [coef_indices]
    
    q = len(coef_indices)
    p = len(results.params)
    R = np.zeros((q, p))
    
    for i, idx in enumerate(coef_indices):
        R[i, idx] = 1
    
    return wald_test(results, R)
