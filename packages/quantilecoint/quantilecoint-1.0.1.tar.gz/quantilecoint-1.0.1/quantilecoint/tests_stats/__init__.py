"""
Test statistics module for quantile cointegration analysis.
"""

from quantilecoint.tests_stats.wald_test import wald_test, WaldTestResult
from quantilecoint.tests_stats.stability_test import stability_test, StabilityTestResult
from quantilecoint.tests_stats.cointegration_test import (
    cointegration_test,
    CointegrationTestResult,
)

__all__ = [
    "wald_test",
    "WaldTestResult",
    "stability_test",
    "StabilityTestResult",
    "cointegration_test",
    "CointegrationTestResult",
]
