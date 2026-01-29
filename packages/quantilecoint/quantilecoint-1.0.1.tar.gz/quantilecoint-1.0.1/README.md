# Quantilecoint

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.1-green.svg)]()

**Quantile Cointegrating Regression** - A Python implementation based on Xiao (2009) "Quantile cointegrating regression", *Journal of Econometrics*, 150, 248-260.

## Author

**Dr Merwan Roudane**  
Email: merwanroudane920@gmail.com  
GitHub: https://github.com/merwanroudane/quantilecoint

## Overview

This package implements quantile regression methods for cointegrated time series, including:

- **Quantile Cointegrating Regression**: Estimate cointegrating relationships at different quantiles
- **Fully-Modified Quantile Regression**: Bias-corrected estimator for endogenous regressors
- **Augmented Quantile Cointegrating Regression**: Uses leads and lags to handle endogeneity
- **Wald Test**: Test linear restrictions on cointegrating coefficients
- **Stability Test**: Bootstrap-based test for constant vs. time-varying coefficients
- **CUSUM Cointegration Test**: Robust test for the null of cointegration

## Installation

```bash
pip install quantilecoint
```

Or install from source:

```bash
git clone https://github.com/merwanroudane/quantilecoint.git
cd quantilecoint
pip install -e .
```

## Complete Example: All Functions Demonstrated

```python
import numpy as np
from quantilecoint import QuantileCointegration

# =============================================================================
# 1. GENERATE COINTEGRATED DATA
# =============================================================================
np.random.seed(42)
n = 200

# x_t is an I(1) process (random walk)
x = np.cumsum(np.random.randn(n))

# y_t is cointegrated with x_t: y = α + β*x + u
alpha_true = 2.0
beta_true = 1.5
y = alpha_true + beta_true * x + np.random.randn(n) * 0.5

print("=" * 70)
print("QUANTILECOINT LIBRARY - COMPLETE DEMONSTRATION")
print("Based on Xiao (2009) Journal of Econometrics")
print("=" * 70)

# =============================================================================
# 2. CREATE MODEL
# =============================================================================
model = QuantileCointegration(y, x, n_lags=4)
print(f"\nModel created with {n} observations, K=4 leads/lags")

# =============================================================================
# 3. FIT AT SINGLE QUANTILE (tau=0.5 for median)
# =============================================================================
print("\n" + "-" * 70)
print("3. SINGLE QUANTILE ESTIMATION (τ = 0.5)")
print("-" * 70)

results_single = model.fit(tau=0.5)
res = results_single[0.5]
print(f"   Intercept α(0.5): {res.alpha:.4f} (true: {alpha_true})")
print(f"   Slope β(0.5):     {res.beta[0]:.4f} (true: {beta_true})")

# =============================================================================
# 4. FIT AT MULTIPLE QUANTILES
# =============================================================================
print("\n" + "-" * 70)
print("4. MULTIPLE QUANTILE ESTIMATION")
print("-" * 70)

quantiles = [0.1, 0.25, 0.5, 0.75, 0.9]
results = model.fit(tau=quantiles)

print(f"{'τ':>8} {'α(τ)':>12} {'β(τ)':>12}")
print("-" * 35)
for tau in quantiles:
    res = results[tau]
    print(f"{tau:>8.2f} {res.alpha:>12.4f} {res.beta[0]:>12.4f}")

# =============================================================================
# 5. FULLY-MODIFIED QUANTILE REGRESSION (bias-corrected)
# =============================================================================
print("\n" + "-" * 70)
print("5. FULLY-MODIFIED QUANTILE REGRESSION (Theorem 2)")
print("-" * 70)

fm_result = model.fit_fully_modified(tau=0.5)
print(f"   β̂⁺(0.5):      {fm_result.beta[0]:.6f}")
print(f"   Std. Error:   {fm_result.std_errors[1]:.6f}")
print(f"   t-statistic:  {fm_result.tvalues[1]:.4f}")
print(f"   p-value:      {fm_result.pvalues[1]:.6f}")
ci = fm_result.conf_int()
print(f"   95% CI:       [{ci[1, 0]:.4f}, {ci[1, 1]:.4f}]")

# =============================================================================
# 6. WALD TEST FOR LINEAR RESTRICTIONS
# =============================================================================
print("\n" + "-" * 70)
print("6. WALD TEST (Theorem 3): H₀: β = 1.5")
print("-" * 70)

R = np.array([[0, 1]])  # Test the slope coefficient
r = np.array([1.5])     # Against value 1.5
wald_result = model.wald_test(R, r, tau=0.5)

print(f"   Wald statistic:  {wald_result.statistic:.4f}")
print(f"   Degrees of freedom: {wald_result.df}")
print(f"   P-value:         {wald_result.pvalue:.4f}")
if wald_result.pvalue > 0.05:
    print("   Conclusion: FAIL TO REJECT H₀ (β = 1.5)")
else:
    print("   Conclusion: REJECT H₀")

# =============================================================================
# 7. STABILITY TEST (constant vs. time-varying coefficients)
# =============================================================================
print("\n" + "-" * 70)
print("7. STABILITY TEST (Section 3.2): H₀: β(τ) = β (constant)")
print("-" * 70)

stability = model.test_stability(
    quantiles=np.arange(0.1, 0.91, 0.1),
    n_bootstrap=200  # Use more (e.g., 1000) for publication
)

print(f"   Test statistic sup|V̂ₙ(τ)|: {stability.statistic:.4f}")
print(f"   τ with max deviation:      {stability.tau_max:.2f}")
print(f"   Bootstrap p-value:         {stability.pvalue:.4f}")
print(f"   Critical values:")
print(f"      10%: {stability.critical_values['10%']:.4f}")
print(f"       5%: {stability.critical_values['5%']:.4f}")
print(f"       1%: {stability.critical_values['1%']:.4f}")
if stability.reject_at_05:
    print("   Conclusion: REJECT H₀ - Evidence of time-varying coefficients")
else:
    print("   Conclusion: FAIL TO REJECT H₀ - Coefficients appear constant")

# =============================================================================
# 8. CUSUM COINTEGRATION TEST
# =============================================================================
print("\n" + "-" * 70)
print("8. CUSUM COINTEGRATION TEST (Section 3.3): H₀: Cointegrated")
print("-" * 70)

coint_test = model.test_cointegration(tau=0.5, test_type='ks')

print(f"   CUSUM statistic: {coint_test.statistic:.4f}")
print(f"   Test type:       {coint_test.test_type.upper()}")
print(f"   P-value:         {coint_test.pvalue:.4f}")
if coint_test.reject_at_05:
    print("   Conclusion: REJECT H₀ - Evidence against cointegration")
else:
    print("   Conclusion: FAIL TO REJECT H₀ - Series appear cointegrated")

# =============================================================================
# 9. GET FORMATTED SUMMARY
# =============================================================================
print("\n" + "-" * 70)
print("9. PUBLICATION-READY SUMMARY OUTPUT")
print("-" * 70)

summary = results.summary()
print("\nText format (first 500 chars):")
print(summary.as_text()[:500] + "...")

# =============================================================================
# 10. LATEX OUTPUT FOR PAPERS
# =============================================================================
print("\n" + "-" * 70)
print("10. LATEX TABLE OUTPUT")
print("-" * 70)

latex = summary.as_latex()
print(latex[:400] + "...\n")

print("=" * 70)
print("ALL FUNCTIONS DEMONSTRATED SUCCESSFULLY!")
print("=" * 70)
```

## Quick Reference

### Basic Usage
```python
from quantilecoint import QuantileCointegration

model = QuantileCointegration(y, x, n_lags=4)

# Fit at single quantile
results = model.fit(tau=0.5)

# Fit at multiple quantiles  
results = model.fit(tau=[0.1, 0.25, 0.5, 0.75, 0.9])

# Access coefficients
beta = results[0.5].beta
alpha = results[0.5].alpha
```

### Fully-Modified Estimates (Bias-Corrected)
```python
fm_result = model.fit_fully_modified(tau=0.5)
print(fm_result.summary())
```

### Statistical Tests
```python
# Test H₀: β = 1.0
wald = model.wald_test(R=np.array([[0, 1]]), r=np.array([1.0]), tau=0.5)

# Test for time-varying coefficients
stability = model.test_stability(n_bootstrap=1000)

# Test for cointegration
coint = model.test_cointegration(tau=0.5)
```

### Output Formats
```python
results = model.fit(tau=[0.1, 0.5, 0.9])
summary = results.summary()

# Plain text
print(summary.as_text())

# LaTeX (for papers)
print(summary.as_latex())

# HTML (for web)
print(summary.as_html())
```

## API Reference

### Classes
- `QuantileCointegration` - Main model class
- `QuantileCointegrationResults` - Results container

### Methods
| Method | Description |
|--------|-------------|
| `fit(tau=, method=)` | Fit quantile regression at specified quantile(s) |
| `fit_fully_modified(tau=)` | Fit bias-corrected estimator |
| `wald_test(R, r, tau=)` | Test linear restrictions on β |
| `test_stability(n_bootstrap=)` | Test for constant coefficients |
| `test_cointegration(tau=)` | CUSUM test for cointegration |

## References

- Xiao, Z. (2009). Quantile cointegrating regression. *Journal of Econometrics*, 150(2), 248-260.
- Koenker, R., & Bassett, G. (1978). Regression quantiles. *Econometrica*, 46(1), 33-50.
- Koenker, R., & Xiao, Z. (2006). Quantile autoregression. *Journal of the American Statistical Association*, 101(475), 980-990.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Citation

```bibtex
@software{roudane2026quantilecoint,
  author = {Roudane, Merwan},
  title = {quantilecoint: Quantile Cointegrating Regression in Python},
  year = {2026},
  version = {1.0.1},
  url = {https://github.com/merwanroudane/quantilecoint}
}
```
