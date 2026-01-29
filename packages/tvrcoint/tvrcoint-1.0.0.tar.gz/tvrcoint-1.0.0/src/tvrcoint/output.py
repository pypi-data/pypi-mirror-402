"""
Output Formatting for Publication-Ready Results

This module provides functions to format test results for publication
in academic journals, including LaTeX, Markdown, and HTML output.
"""

import numpy as np
from typing import Optional, List, Dict, Union
from dataclasses import dataclass


def format_number(x: float, precision: int = 4) -> str:
    """Format a number with given precision."""
    if np.isnan(x) or np.isinf(x):
        return "N/A"
    return f"{x:.{precision}f}"


def format_pvalue(pvalue: float) -> str:
    """Format p-value with significance stars."""
    if pvalue < 0.01:
        return f"{pvalue:.4f}***"
    elif pvalue < 0.05:
        return f"{pvalue:.4f}**"
    elif pvalue < 0.10:
        return f"{pvalue:.4f}*"
    else:
        return f"{pvalue:.4f}"


def format_results(results, format_type: str = 'text') -> str:
    """
    Format test results for display.
    
    Parameters
    ----------
    results : TVCTestResults or BootstrapTVCTestResults
        Test results object
    format_type : str
        Output format: 'text', 'latex', 'markdown', or 'html'
        
    Returns
    -------
    str
        Formatted output string
    """
    if format_type == 'latex':
        return results_to_latex(results)
    elif format_type == 'markdown':
        return results_to_markdown(results)
    elif format_type == 'html':
        return results_to_html(results)
    else:
        return results.summary()


def results_to_latex(results) -> str:
    """
    Convert test results to LaTeX table format.
    
    Parameters
    ----------
    results : TVCTestResults or BootstrapTVCTestResults
        Test results object
        
    Returns
    -------
    str
        LaTeX formatted table
    """
    is_bootstrap = hasattr(results, 'pvalue_bootstrap')
    
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Time-Varying Cointegration Test Results}",
        r"\label{tab:tvc_test}",
        r"\begin{tabular}{lc}",
        r"\toprule",
    ]
    
    # Header
    lines.append(r"Statistic & Value \\")
    lines.append(r"\midrule")
    
    # Model specification
    lines.append(rf"Number of variables ($k$) & {results.k} \\")
    lines.append(rf"Cointegration rank ($r$) & {results.r} \\")
    lines.append(rf"Chebyshev order ($m$) & {results.m} \\")
    lines.append(rf"VAR lag order ($p$) & {results.p} \\")
    lines.append(rf"Sample size ($T$) & {results.T} \\")
    lines.append(r"\midrule")
    
    # Test results
    lines.append(rf"LR statistic & {results.statistic:.4f} \\")
    lines.append(rf"Degrees of freedom & {results.df} \\")
    
    if is_bootstrap:
        pvalue_asym = format_pvalue(results.pvalue_asymptotic)
        pvalue_boot = format_pvalue(results.pvalue_bootstrap)
        lines.append(rf"Asymptotic $p$-value & {pvalue_asym} \\")
        lines.append(rf"Bootstrap $p$-value & {pvalue_boot} \\")
        lines.append(r"\midrule")
        lines.append(rf"Bootstrap method & {results.method.capitalize()} \\")
        lines.append(rf"Replications ($B$) & {results.B} \\")
    else:
        pvalue = format_pvalue(results.pvalue)
        lines.append(rf"$p$-value & {pvalue} \\")
    
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    
    # Notes
    lines.append(r"\begin{tablenotes}")
    lines.append(r"\small")
    lines.append(r"\item Notes: $H_0$: Time-invariant cointegration; "
                 r"$H_1$: Time-varying cointegration. ")
    lines.append(r"\item ***, **, * denote significance at 1\%, 5\%, 10\% levels.")
    lines.append(r"\end{tablenotes}")
    
    lines.append(r"\end{table}")
    
    return "\n".join(lines)


def results_to_markdown(results) -> str:
    """
    Convert test results to Markdown table format.
    
    Parameters
    ----------
    results : TVCTestResults or BootstrapTVCTestResults
        Test results object
        
    Returns
    -------
    str
        Markdown formatted table
    """
    is_bootstrap = hasattr(results, 'pvalue_bootstrap')
    
    lines = [
        "## Time-Varying Cointegration Test Results",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        f"| Variables (k) | {results.k} |",
        f"| Cointegration rank (r) | {results.r} |",
        f"| Chebyshev order (m) | {results.m} |",
        f"| VAR lag order (p) | {results.p} |",
        f"| Sample size (T) | {results.T} |",
        "",
        "| Test Statistic | Value |",
        "|----------------|-------|",
        f"| LR statistic | {results.statistic:.4f} |",
        f"| Degrees of freedom | {results.df} |",
    ]
    
    if is_bootstrap:
        lines.extend([
            f"| Asymptotic p-value | {format_pvalue(results.pvalue_asymptotic)} |",
            f"| Bootstrap p-value | {format_pvalue(results.pvalue_bootstrap)} |",
            "",
            f"**Bootstrap Method**: {results.method.capitalize()}",
            f"**Replications (B)**: {results.B}",
        ])
    else:
        lines.append(f"| p-value | {format_pvalue(results.pvalue)} |")
    
    lines.extend([
        "",
        "**Notes**: H₀: Time-invariant cointegration; H₁: Time-varying cointegration.",
        "***, **, * denote significance at 1%, 5%, 10% levels.",
    ])
    
    return "\n".join(lines)


def results_to_html(results) -> str:
    """
    Convert test results to HTML table format.
    
    Parameters
    ----------
    results : TVCTestResults or BootstrapTVCTestResults
        Test results object
        
    Returns
    -------
    str
        HTML formatted table
    """
    is_bootstrap = hasattr(results, 'pvalue_bootstrap')
    
    # Determine conclusion
    if is_bootstrap:
        pvalue = results.pvalue_bootstrap
    else:
        pvalue = results.pvalue
    
    if pvalue < 0.01:
        conclusion = "Strong evidence of TIME-VARYING cointegration (p < 0.01)"
        conclusion_class = "reject-strong"
    elif pvalue < 0.05:
        conclusion = "Evidence of TIME-VARYING cointegration (p < 0.05)"
        conclusion_class = "reject"
    elif pvalue < 0.10:
        conclusion = "Weak evidence of TIME-VARYING cointegration (p < 0.10)"
        conclusion_class = "reject-weak"
    else:
        conclusion = "Cannot reject TIME-INVARIANT cointegration"
        conclusion_class = "accept"
    
    html = f"""
<div class="tvc-results">
    <h3>Time-Varying Cointegration Test Results</h3>
    
    <table class="tvc-table">
        <thead>
            <tr>
                <th colspan="2">Model Specification</th>
            </tr>
        </thead>
        <tbody>
            <tr><td>Number of Variables (k)</td><td>{results.k}</td></tr>
            <tr><td>Cointegration Rank (r)</td><td>{results.r}</td></tr>
            <tr><td>Chebyshev Order (m)</td><td>{results.m}</td></tr>
            <tr><td>VAR Lag Order (p)</td><td>{results.p}</td></tr>
            <tr><td>Sample Size (T)</td><td>{results.T}</td></tr>
        </tbody>
    </table>
    
    <table class="tvc-table">
        <thead>
            <tr>
                <th colspan="2">Test Results</th>
            </tr>
        </thead>
        <tbody>
            <tr><td>LR Statistic</td><td><strong>{results.statistic:.4f}</strong></td></tr>
            <tr><td>Degrees of Freedom</td><td>{results.df}</td></tr>
"""
    
    if is_bootstrap:
        html += f"""
            <tr><td>Asymptotic p-value</td><td>{format_pvalue(results.pvalue_asymptotic)}</td></tr>
            <tr><td>Bootstrap p-value</td><td><strong>{format_pvalue(results.pvalue_bootstrap)}</strong></td></tr>
            <tr><td>Bootstrap Method</td><td>{results.method.capitalize()}</td></tr>
            <tr><td>Replications (B)</td><td>{results.B}</td></tr>
"""
    else:
        html += f"""
            <tr><td>p-value</td><td><strong>{format_pvalue(results.pvalue)}</strong></td></tr>
"""
    
    html += f"""
        </tbody>
    </table>
    
    <div class="conclusion {conclusion_class}">
        <strong>Conclusion:</strong> {conclusion}
    </div>
    
    <p class="notes">
        <small>
            <strong>Notes:</strong> H₀: Time-invariant cointegration; H₁: Time-varying cointegration.<br>
            ***, **, * denote significance at 1%, 5%, 10% levels.
        </small>
    </p>
</div>

<style>
.tvc-results {{
    font-family: Arial, sans-serif;
    max-width: 600px;
}}
.tvc-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
}}
.tvc-table th, .tvc-table td {{
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}}
.tvc-table th {{
    background-color: #f2f2f2;
}}
.conclusion {{
    padding: 10px;
    margin: 10px 0;
    border-radius: 4px;
}}
.reject-strong {{ background-color: #ffcccc; }}
.reject {{ background-color: #ffe6cc; }}
.reject-weak {{ background-color: #ffffcc; }}
.accept {{ background-color: #ccffcc; }}
.notes {{ color: #666; }}
</style>
"""
    
    return html


def create_comparison_table(
    results_list: List,
    labels: Optional[List[str]] = None
) -> str:
    """
    Create a comparison table for multiple test results.
    
    Parameters
    ----------
    results_list : list
        List of test results objects
    labels : list, optional
        Labels for each result
        
    Returns
    -------
    str
        LaTeX table comparing results
    """
    if labels is None:
        labels = [f"Model {i+1}" for i in range(len(results_list))]
    
    n = len(results_list)
    
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Comparison of Time-Varying Cointegration Tests}",
        r"\label{tab:tvc_comparison}",
        r"\begin{tabular}{l" + "c" * n + "}",
        r"\toprule",
    ]
    
    # Header
    header = "Statistic & " + " & ".join(labels) + r" \\"
    lines.append(header)
    lines.append(r"\midrule")
    
    # Parameters
    m_row = "$m$ & " + " & ".join([str(r.m) for r in results_list]) + r" \\"
    lines.append(m_row)
    
    # Statistics
    lr_row = "LR statistic & " + " & ".join([f"{r.statistic:.2f}" for r in results_list]) + r" \\"
    lines.append(lr_row)
    
    # P-values
    pvalues = []
    for r in results_list:
        if hasattr(r, 'pvalue_bootstrap'):
            pvalues.append(format_pvalue(r.pvalue_bootstrap))
        else:
            pvalues.append(format_pvalue(r.pvalue))
    
    pv_row = "p-value & " + " & ".join(pvalues) + r" \\"
    lines.append(pv_row)
    
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    
    return "\n".join(lines)


def create_ppp_results_table(
    country_results: Dict[str, dict],
    bootstrap: bool = True
) -> str:
    """
    Create a publication-ready PPP results table.
    
    Parameters
    ----------
    country_results : dict
        Dictionary with country names as keys and result dicts as values
    bootstrap : bool
        Whether results are from bootstrap test
        
    Returns
    -------
    str
        LaTeX table
    """
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Purchasing Power Parity Test Results}",
        r"\label{tab:ppp_results}",
        r"\begin{tabular}{lccccc}",
        r"\toprule",
        r"Country & $m^*_{HQ}$ & LR Stat & p-value (Asym) & p-value (Boot) & Conclusion \\",
        r"\midrule",
    ]
    
    for country, result in country_results.items():
        m_hq = result.get('m_hq', '-')
        lr_stat = result.get('lr_stat', np.nan)
        p_asym = result.get('p_asym', np.nan)
        p_boot = result.get('p_boot', np.nan)
        
        if p_boot < 0.05:
            conclusion = "TV"
        else:
            conclusion = "TI"
        
        lines.append(
            f"{country} & {m_hq} & {lr_stat:.2f} & "
            f"{format_pvalue(p_asym)} & {format_pvalue(p_boot)} & {conclusion} \\\\"
        )
    
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\begin{tablenotes}",
        r"\small",
        r"\item Notes: $m^*_{HQ}$ is the Hannan-Quinn selected Chebyshev order.",
        r"\item TV = Time-varying cointegration; TI = Time-invariant cointegration.",
        r"\item ***, **, * denote significance at 1\%, 5\%, 10\% levels.",
        r"\end{tablenotes}",
        r"\end{table}",
    ])
    
    return "\n".join(lines)
