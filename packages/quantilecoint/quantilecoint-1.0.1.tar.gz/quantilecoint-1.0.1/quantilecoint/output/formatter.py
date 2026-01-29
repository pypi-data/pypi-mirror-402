"""
Output Formatting for Publication-Ready Results

This module provides functions to format quantile cointegration results
for publication in academic journals.

Features:
- LaTeX table generation
- HTML output
- Plain text summaries
- Multi-quantile comparison tables
"""

import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime


class QuantileCointegrationSummary:
    """
    Container for formatted regression summary.
    
    Provides multiple output formats suitable for academic publication.
    """
    
    def __init__(self, results_dict: Dict, model_info: dict = None):
        """
        Initialize summary object.
        
        Parameters
        ----------
        results_dict : dict
            Dictionary mapping quantile -> results object
        model_info : dict, optional
            Model information (nobs, method, etc.)
        """
        self.results_dict = results_dict
        self.model_info = model_info or {}
        self.quantiles = sorted(results_dict.keys())
        
    def as_text(self) -> str:
        """Generate plain text summary."""
        return format_results(self.results_dict, format='text')
    
    def as_latex(self) -> str:
        """Generate LaTeX table."""
        return format_latex_table(self.results_dict)
    
    def as_html(self) -> str:
        """Generate HTML table."""
        return format_results(self.results_dict, format='html')
    
    def __repr__(self) -> str:
        return f"QuantileCointegrationSummary(quantiles={self.quantiles})"
    
    def __str__(self) -> str:
        return self.as_text()


def format_results(results: Union[Dict, object], format: str = 'text',
                   decimal_places: int = 4) -> str:
    """
    Format quantile cointegration results.
    
    Parameters
    ----------
    results : dict or results object
        Single results object or dict mapping tau -> results
    format : str, default 'text'
        Output format: 'text', 'latex', or 'html'
    decimal_places : int, default 4
        Number of decimal places
        
    Returns
    -------
    str
        Formatted output
    """
    if format == 'latex':
        return format_latex_table(results, decimal_places)
    elif format == 'html':
        return format_html_table(results, decimal_places)
    else:
        return format_text_table(results, decimal_places)


def format_text_table(results: Union[Dict, object], 
                      decimal_places: int = 4) -> str:
    """Format results as plain text table."""
    
    if not isinstance(results, dict):
        # Single results object
        if hasattr(results, 'summary'):
            return results.summary()
        results = {results.tau: results}
    
    lines = []
    lines.append("=" * 82)
    lines.append("              Quantile Cointegrating Regression Results")
    lines.append("              Based on Xiao (2009) Journal of Econometrics")
    lines.append("=" * 82)
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # Get first result for model info
    first_result = list(results.values())[0]
    if hasattr(first_result, 'nobs'):
        lines.append(f"No. Observations: {first_result.nobs}")
    
    lines.append(f"Quantiles estimated: {len(results)}")
    lines.append("-" * 82)
    lines.append("")
    
    # Coefficient table header
    lines.append("Cointegrating Coefficients β(τ) across Quantiles:")
    lines.append("-" * 82)
    
    # Get number of coefficients
    n_coef = len(first_result.params) if hasattr(first_result, 'params') else 2
    var_names = ['const'] + [f'x{i}' for i in range(1, n_coef)]
    
    # Header row
    header = f"{'τ':>8}"
    for name in var_names:
        header += f"  {name:>12}"
    lines.append(header)
    lines.append("-" * 82)
    
    # Data rows
    for tau in sorted(results.keys()):
        res = results[tau]
        row = f"{tau:>8.2f}"
        
        if hasattr(res, 'params'):
            params = res.params
        elif hasattr(res, 'beta'):
            params = np.concatenate([[res.alpha], res.beta])
        else:
            params = [0] * n_coef
        
        for p in params:
            row += f"  {p:>12.{decimal_places}f}"
        lines.append(row)
    
    lines.append("-" * 82)
    lines.append("")
    
    # Add standard errors for median if available
    if 0.5 in results and hasattr(results[0.5], 'std_errors'):
        lines.append("Standard Errors at τ = 0.50:")
        lines.append("-" * 40)
        res = results[0.5]
        for i, (name, se) in enumerate(zip(var_names, res.std_errors)):
            lines.append(f"  {name}: {se:.{decimal_places}f}")
        lines.append("")
    
    lines.append("=" * 82)
    
    return "\n".join(lines)


def format_latex_table(results: Union[Dict, object],
                       decimal_places: int = 4,
                       caption: str = None,
                       label: str = None) -> str:
    """
    Format results as LaTeX table.
    
    Parameters
    ----------
    results : dict or results object
        Results to format
    decimal_places : int
        Decimal places
    caption : str, optional
        Table caption
    label : str, optional
        LaTeX label
        
    Returns
    -------
    str
        LaTeX table code
    """
    if not isinstance(results, dict):
        results = {results.tau: results}
    
    # Get coefficient info
    first_result = list(results.values())[0]
    n_coef = len(first_result.params) if hasattr(first_result, 'params') else 2
    var_names = ['Constant'] + [f'$x_{{{i}}}$' for i in range(1, n_coef)]
    
    lines = []
    
    # Table header
    lines.append("\\begin{table}[htbp]")
    lines.append("\\centering")
    if caption:
        lines.append(f"\\caption{{{caption}}}")
    if label:
        lines.append(f"\\label{{{label}}}")
    
    # Column specification
    col_spec = "l" + "c" * n_coef
    lines.append(f"\\begin{{tabular}}{{{col_spec}}}")
    lines.append("\\hline\\hline")
    
    # Header row
    header = "$\\tau$"
    for name in var_names:
        header += f" & {name}"
    header += " \\\\"
    lines.append(header)
    lines.append("\\hline")
    
    # Data rows
    for tau in sorted(results.keys()):
        res = results[tau]
        row = f"{tau:.2f}"
        
        if hasattr(res, 'params'):
            params = res.params
        elif hasattr(res, 'beta'):
            params = np.concatenate([[res.alpha], res.beta])
        else:
            params = [0] * n_coef
        
        for p in params:
            row += f" & {p:.{decimal_places}f}"
        row += " \\\\"
        lines.append(row)
    
    lines.append("\\hline\\hline")
    lines.append("\\end{tabular}")
    
    # Notes
    lines.append("\\begin{tablenotes}")
    lines.append("\\small")
    lines.append("\\item Notes: Estimates from quantile cointegrating regression ")
    lines.append("following Xiao (2009). Standard errors available upon request.")
    lines.append("\\end{tablenotes}")
    
    lines.append("\\end{table}")
    
    return "\n".join(lines)


def format_html_table(results: Union[Dict, object],
                      decimal_places: int = 4) -> str:
    """Format results as HTML table."""
    
    if not isinstance(results, dict):
        results = {results.tau: results}
    
    first_result = list(results.values())[0]
    n_coef = len(first_result.params) if hasattr(first_result, 'params') else 2
    var_names = ['const'] + [f'x<sub>{i}</sub>' for i in range(1, n_coef)]
    
    lines = []
    lines.append('<table class="quantile-cointegration-results">')
    lines.append('<thead>')
    lines.append('<tr>')
    lines.append('<th>&tau;</th>')
    for name in var_names:
        lines.append(f'<th>{name}</th>')
    lines.append('</tr>')
    lines.append('</thead>')
    lines.append('<tbody>')
    
    for tau in sorted(results.keys()):
        res = results[tau]
        lines.append('<tr>')
        lines.append(f'<td>{tau:.2f}</td>')
        
        if hasattr(res, 'params'):
            params = res.params
        elif hasattr(res, 'beta'):
            params = np.concatenate([[res.alpha], res.beta])
        else:
            params = [0] * n_coef
        
        for p in params:
            lines.append(f'<td>{p:.{decimal_places}f}</td>')
        lines.append('</tr>')
    
    lines.append('</tbody>')
    lines.append('</table>')
    
    return "\n".join(lines)


def format_coefficient_table(quantiles: np.ndarray, 
                             coefficients: np.ndarray,
                             std_errors: np.ndarray = None,
                             var_names: List[str] = None,
                             format: str = 'text') -> str:
    """
    Format a coefficient table across quantiles.
    
    Parameters
    ----------
    quantiles : np.ndarray
        Quantile levels
    coefficients : np.ndarray
        Coefficients, shape (n_quantiles, n_coef)
    std_errors : np.ndarray, optional
        Standard errors, same shape as coefficients
    var_names : list, optional
        Variable names
    format : str
        Output format
        
    Returns
    -------
    str
        Formatted table
    """
    n_coef = coefficients.shape[1]
    if var_names is None:
        var_names = ['const'] + [f'x{i}' for i in range(1, n_coef)]
    
    if format == 'latex':
        lines = []
        col_spec = "l" + "c" * n_coef
        lines.append(f"\\begin{{tabular}}{{{col_spec}}}")
        lines.append("\\hline")
        lines.append("$\\tau$ & " + " & ".join(var_names) + " \\\\")
        lines.append("\\hline")
        
        for i, tau in enumerate(quantiles):
            row = f"{tau:.2f}"
            for j in range(n_coef):
                coef = coefficients[i, j]
                if std_errors is not None:
                    se = std_errors[i, j]
                    row += f" & {coef:.4f} ({se:.4f})"
                else:
                    row += f" & {coef:.4f}"
            row += " \\\\"
            lines.append(row)
        
        lines.append("\\hline")
        lines.append("\\end{tabular}")
        return "\n".join(lines)
    
    else:
        # Text format
        lines = []
        header = f"{'τ':>6}"
        for name in var_names:
            header += f"  {name:>14}"
        lines.append(header)
        lines.append("-" * (8 + 16 * n_coef))
        
        for i, tau in enumerate(quantiles):
            row = f"{tau:>6.2f}"
            for j in range(n_coef):
                coef = coefficients[i, j]
                if std_errors is not None:
                    se = std_errors[i, j]
                    row += f"  {coef:>6.4f}({se:.4f})"
                else:
                    row += f"  {coef:>14.4f}"
            lines.append(row)
        
        return "\n".join(lines)
