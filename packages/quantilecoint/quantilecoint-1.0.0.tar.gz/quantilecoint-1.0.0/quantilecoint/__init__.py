"""
Quantilecoint: Quantile Cointegrating Regression
=================================================

A Python implementation of quantile cointegrating regression methods based on
Xiao (2009) "Quantile cointegrating regression", Journal of Econometrics, 150, 248-260.

Author: Dr Merwan Roudane
Email: merwanroudane920@gmail.com
GitHub: https://github.com/merwanroudane/quantilecoint

Main Classes
------------
QuantileCointegration : Main class for quantile cointegrating regression
QuantileCointegrationResults : Results container with summary output

Functions
---------
fully_modified_qr : Fully-modified quantile regression estimator
augmented_qr : Augmented quantile cointegrating regression
wald_test : Wald test for linear restrictions
stability_test : Test for constant vs. time-varying coefficients
cointegration_test : CUSUM test for cointegration
"""

from quantilecoint.core.quantile_cointegration import (
    QuantileCointegration,
    QuantileCointegrationResults,
)
from quantilecoint.core.quantile_regression import QuantileRegression
from quantilecoint.core.fully_modified import FullyModifiedQuantileRegression
from quantilecoint.core.augmented import AugmentedQuantileRegression

from quantilecoint.tests_stats.wald_test import wald_test, WaldTestResult
from quantilecoint.tests_stats.stability_test import stability_test, StabilityTestResult
from quantilecoint.tests_stats.cointegration_test import (
    cointegration_test, 
    CointegrationTestResult
)

from quantilecoint.simulation.critical_values import (
    simulate_critical_values,
    get_critical_value,
)
from quantilecoint.simulation.bootstrap import sieve_bootstrap

from quantilecoint.output.formatter import format_results, format_latex_table

__version__ = "1.0.0"
__author__ = "Dr Merwan Roudane"
__email__ = "merwanroudane920@gmail.com"

__all__ = [
    # Main classes
    "QuantileCointegration",
    "QuantileCointegrationResults",
    "QuantileRegression",
    "FullyModifiedQuantileRegression",
    "AugmentedQuantileRegression",
    # Test functions
    "wald_test",
    "WaldTestResult",
    "stability_test",
    "StabilityTestResult",
    "cointegration_test",
    "CointegrationTestResult",
    # Simulation
    "simulate_critical_values",
    "get_critical_value",
    "sieve_bootstrap",
    # Output
    "format_results",
    "format_latex_table",
]
