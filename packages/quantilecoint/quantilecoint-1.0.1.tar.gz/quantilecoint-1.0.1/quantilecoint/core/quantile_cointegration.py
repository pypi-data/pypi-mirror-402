"""
Main Quantile Cointegration Class

This module provides the primary user-facing interface for quantile 
cointegrating regression analysis.

Reference:
    Xiao, Z. (2009). Quantile cointegrating regression. 
    Journal of Econometrics, 150(2), 248-260.
"""

import numpy as np
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

from quantilecoint.core.quantile_regression import QuantileRegression
from quantilecoint.core.fully_modified import FullyModifiedQuantileRegression
from quantilecoint.core.augmented import AugmentedQuantileRegression
from quantilecoint.tests_stats.wald_test import wald_test, WaldTestResult
from quantilecoint.tests_stats.stability_test import stability_test, StabilityTestResult
from quantilecoint.tests_stats.cointegration_test import (
    cointegration_test, CointegrationTestResult
)
from quantilecoint.output.formatter import QuantileCointegrationSummary


@dataclass
class QuantileCointegrationResults:
    """
    Container for quantile cointegration results.
    
    Attributes
    ----------
    quantile_results : dict
        Dictionary mapping τ -> results at each quantile
    ols_result : object
        OLS regression result for comparison
    method : str
        Estimation method used
    nobs : int
        Number of observations
    n_lags : int
        Number of leads/lags (if augmented)
    """
    quantile_results: Dict
    ols_result: object
    method: str
    nobs: int
    n_lags: int
    
    def __getitem__(self, tau):
        """Allow indexing by quantile."""
        return self.quantile_results[tau]
    
    def quantiles(self) -> np.ndarray:
        """Return array of estimated quantiles."""
        return np.array(sorted(self.quantile_results.keys()))
    
    def beta(self, tau: float = None) -> np.ndarray:
        """
        Get cointegrating coefficients.
        
        Parameters
        ----------
        tau : float, optional
            Quantile. If None, returns all betas as 2D array.
        """
        if tau is not None:
            res = self.quantile_results[tau]
            if hasattr(res, 'beta'):
                return res.beta
            return res.params[1:]
        
        betas = []
        for t in self.quantiles():
            res = self.quantile_results[t]
            if hasattr(res, 'beta'):
                betas.append(res.beta)
            else:
                betas.append(res.params[1:])
        return np.array(betas)
    
    def summary(self) -> QuantileCointegrationSummary:
        """Generate formatted summary."""
        return QuantileCointegrationSummary(
            self.quantile_results,
            {'nobs': self.nobs, 'method': self.method, 'n_lags': self.n_lags}
        )
    
    def __repr__(self) -> str:
        return (f"QuantileCointegrationResults(method='{self.method}', "
                f"quantiles={len(self.quantile_results)}, nobs={self.nobs})")


class QuantileCointegration:
    """
    Quantile Cointegrating Regression.
    
    Main class for estimating cointegrating relationships at different 
    quantiles, following Xiao (2009).
    
    Parameters
    ----------
    endog : array-like
        Dependent variable y_t
    exog : array-like
        Integrated regressor(s) x_t
    n_lags : int, default 4
        Number of leads and lags for augmented regression
    kernel : str, default 'bartlett'
        Kernel for long-run variance estimation
        
    Examples
    --------
    >>> import numpy as np
    >>> from quantilecoint import QuantileCointegration
    >>> 
    >>> # Generate cointegrated data
    >>> np.random.seed(42)
    >>> n = 200
    >>> x = np.cumsum(np.random.randn(n))
    >>> y = 2.0 + 1.5 * x + np.random.randn(n)
    >>> 
    >>> # Fit model
    >>> model = QuantileCointegration(y, x, n_lags=4)
    >>> results = model.fit(quantiles=[0.1, 0.25, 0.5, 0.75, 0.9])
    >>> 
    >>> # Print summary
    >>> print(results.summary())
    >>> 
    >>> # Test for time-varying coefficients
    >>> stability = model.test_stability()
    >>> print(stability.summary())
    
    Reference
    ---------
    Xiao, Z. (2009). Quantile cointegrating regression. 
    Journal of Econometrics, 150(2), 248-260.
    """
    
    def __init__(self, endog: np.ndarray, exog: np.ndarray,
                 n_lags: int = 4, kernel: str = 'bartlett'):
        """Initialize the quantile cointegration model."""
        self.endog = np.asarray(endog).flatten()
        self.exog = np.asarray(exog)
        if self.exog.ndim == 1:
            self.exog = self.exog.reshape(-1, 1)
        
        self.n = len(self.endog)
        self.k = self.exog.shape[1]
        self.n_lags = n_lags
        self.kernel = kernel
        
        # Compute OLS for comparison
        X = np.column_stack([np.ones(self.n), self.exog])
        self._ols_coef = np.linalg.lstsq(X, self.endog, rcond=None)[0]
        self._ols_residuals = self.endog - X @ self._ols_coef
    
    def fit(self, quantiles: Union[float, List, np.ndarray] = None,
            tau: Union[float, List, np.ndarray] = None,
            method: str = 'augmented') -> QuantileCointegrationResults:
        """
        Fit quantile cointegrating regression.
        
        Parameters
        ----------
        quantiles : float or array-like, optional
            Quantile levels to estimate. Default is np.arange(0.05, 0.96, 0.05).
            Can also use 'tau' parameter (alias for quantiles).
        tau : float or array-like, optional
            Alias for 'quantiles' parameter. If both are provided, 'tau' is used.
        method : str, default 'augmented'
            Estimation method: 'basic', 'fully_modified', or 'augmented'
            
        Returns
        -------
        QuantileCointegrationResults
            Results container
        """
        # Support tau as alias for quantiles
        if tau is not None:
            quantiles = tau
        if quantiles is None:
            quantiles = np.arange(0.05, 0.96, 0.05)
        elif isinstance(quantiles, (int, float)):
            quantiles = [quantiles]
        quantiles = np.atleast_1d(quantiles)
        
        results_dict = {}
        
        for tau in quantiles:
            if method == 'basic':
                model = QuantileRegression(self.endog, self.exog)
                results_dict[tau] = model.fit(tau=tau)
            elif method == 'fully_modified':
                model = FullyModifiedQuantileRegression(
                    self.endog, self.exog, kernel=self.kernel
                )
                results_dict[tau] = model.fit(tau=tau)
            else:  # augmented
                model = AugmentedQuantileRegression(
                    self.endog, self.exog, n_lags=self.n_lags
                )
                results_dict[tau] = model.fit(tau=tau)
        
        # Create OLS result placeholder
        class OLSPlaceholder:
            def __init__(self, coef, resid):
                self.params = coef
                self.residuals = resid
        
        return QuantileCointegrationResults(
            quantile_results=results_dict,
            ols_result=OLSPlaceholder(self._ols_coef, self._ols_residuals),
            method=method,
            nobs=self.n,
            n_lags=self.n_lags if method == 'augmented' else 0,
        )
    
    def fit_fully_modified(self, tau: float = 0.5):
        """
        Fit fully-modified quantile regression at a single quantile.
        
        Parameters
        ----------
        tau : float, default 0.5
            Quantile level
            
        Returns
        -------
        FullyModifiedResults
            Results with bias-corrected estimates
        """
        model = FullyModifiedQuantileRegression(
            self.endog, self.exog, kernel=self.kernel
        )
        return model.fit(tau=tau)
    
    def test_stability(self, quantiles: np.ndarray = None,
                       n_bootstrap: int = 500,
                       seed: int = None) -> StabilityTestResult:
        """
        Test for constant vs. time-varying cointegrating coefficients.
        
        Tests H_0: β(τ) = β (constant) vs H_1: β(τ) varies with τ
        
        Parameters
        ----------
        quantiles : np.ndarray, optional
            Quantiles to test over
        n_bootstrap : int, default 500
            Number of bootstrap replications
        seed : int, optional
            Random seed
            
        Returns
        -------
        StabilityTestResult
            Test results
        """
        return stability_test(
            self.endog, self.exog,
            quantiles=quantiles,
            n_lags=self.n_lags,
            n_bootstrap=n_bootstrap,
            seed=seed
        )
    
    def test_cointegration(self, tau: float = 0.5,
                           test_type: str = 'ks') -> CointegrationTestResult:
        """
        Test for cointegration using CUSUM test.
        
        Tests H_0: Cointegration exists
        
        Parameters
        ----------
        tau : float, default 0.5
            Quantile level
        test_type : str, default 'ks'
            Test type: 'ks' or 'cvm'
            
        Returns
        -------
        CointegrationTestResult
            Test results
        """
        return cointegration_test(
            self.endog, self.exog,
            tau=tau,
            n_lags=self.n_lags,
            test_type=test_type
        )
    
    def wald_test(self, R: np.ndarray, r: np.ndarray = None,
                  tau: float = 0.5) -> WaldTestResult:
        """
        Wald test for linear restrictions on coefficients.
        
        Tests H_0: Rβ = r
        
        Parameters
        ----------
        R : np.ndarray
            Restriction matrix
        r : np.ndarray, optional
            Restriction values (default zeros)
        tau : float, default 0.5
            Quantile level
            
        Returns
        -------
        WaldTestResult
            Test results
        """
        fm_result = self.fit_fully_modified(tau=tau)
        return wald_test(fm_result, R, r)
