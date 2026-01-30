"""
Output formatting utilities for publication-ready results.

Provides functions to format test results as LaTeX tables, Markdown tables,
and formatted text suitable for academic publications.
"""

import numpy as np
from typing import Union, List, Optional
from tabulate import tabulate


def format_results(result, format_type: str = "text") -> str:
    """
    Format test results for output.
    
    Parameters
    ----------
    result : JohansenResult, JohansenFourierResult, SCVECMResult, SBCResult, or UnionResult
        Any test result object from this library.
    format_type : str, default="text"
        Output format: "text", "latex", "markdown", or "html"
        
    Returns
    -------
    str
        Formatted output string.
        
    Examples
    --------
    >>> from fourier_johansen import johansen_fourier, format_results
    >>> result = johansen_fourier(X, model=3, k=2, f=1)
    >>> print(format_results(result, format_type="latex"))
    """
    if hasattr(result, 'summary'):
        if format_type == "text":
            return result.summary()
        elif format_type == "latex":
            return to_latex(result)
        elif format_type == "markdown":
            return to_markdown(result)
        elif format_type == "html":
            return to_html(result)
    
    return str(result)


def to_latex(result) -> str:
    """
    Convert test results to LaTeX table format.
    
    Parameters
    ----------
    result : Result object
        Any test result object from this library.
        
    Returns
    -------
    str
        LaTeX table code.
    """
    if hasattr(result, 'trace') and hasattr(result, 'lambda_max'):
        return _johansen_to_latex(result)
    elif hasattr(result, 'trace_no_break'):
        return _scvecm_to_latex(result)
    elif hasattr(result, 'all_sbc'):
        return _sbc_to_latex(result)
    elif hasattr(result, 'fourier_trace'):
        return _union_to_latex(result)
    else:
        return "% Unsupported result type for LaTeX conversion"


def to_markdown(result) -> str:
    """
    Convert test results to Markdown table format.
    
    Parameters
    ----------
    result : Result object
        Any test result object from this library.
        
    Returns
    -------
    str
        Markdown table.
    """
    if hasattr(result, 'trace') and hasattr(result, 'lambda_max'):
        return _johansen_to_markdown(result)
    elif hasattr(result, 'trace_no_break'):
        return _scvecm_to_markdown(result)
    elif hasattr(result, 'all_sbc'):
        return _sbc_to_markdown(result)
    elif hasattr(result, 'fourier_trace'):
        return _union_to_markdown(result)
    else:
        return "Unsupported result type for Markdown conversion"


def to_html(result) -> str:
    """
    Convert test results to HTML table format.
    
    Parameters
    ----------
    result : Result object
        Any test result object from this library.
        
    Returns
    -------
    str
        HTML table code.
    """
    if hasattr(result, 'trace') and hasattr(result, 'lambda_max'):
        return _johansen_to_html(result)
    else:
        # Use tabulate for basic HTML conversion
        return tabulate([[str(result)]], tablefmt="html")


def _johansen_to_latex(result) -> str:
    """Convert Johansen/Johansen-Fourier result to LaTeX."""
    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    
    # Determine test type
    if hasattr(result, 'frequency'):
        lines.append(r"\caption{Johansen-Fourier Cointegration Test Results}")
    else:
        lines.append(r"\caption{Johansen Cointegration Test Results}")
    
    lines.append(r"\begin{tabular}{ccccc}")
    lines.append(r"\hline\hline")
    lines.append(r"Rank & Eigenvalue & $\lambda_{max}$ & Trace & CV (5\%) \\")
    lines.append(r"\hline")
    
    for i in range(len(result.eigenvalues)):
        ev = result.eigenvalues[i]
        lm = result.lambda_max[i]
        tr = result.trace[i]
        cv = result.cv_trace[i] if i < len(result.cv_trace) else np.nan
        
        # Add significance marker
        sig = r"$^{*}$" if tr > cv else ""
        
        lines.append(f"{i+1} & {ev:.6f} & {lm:.4f} & {tr:.4f}{sig} & {cv:.3f} \\\\")
    
    lines.append(r"\hline\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\begin{tablenotes}")
    lines.append(r"\small")
    lines.append(r"\item Note: $^{*}$ indicates rejection of the null hypothesis at the 5\% significance level.")
    
    if hasattr(result, 'frequency'):
        freq_type = "cumulative" if result.option == 2 else "single"
        lines.append(f"\\item Fourier frequency: {result.frequency} ({freq_type}).")
    
    lines.append(r"\end{tablenotes}")
    lines.append(r"\end{table}")
    
    return "\n".join(lines)


def _johansen_to_markdown(result) -> str:
    """Convert Johansen/Johansen-Fourier result to Markdown."""
    headers = ["Rank", "Eigenvalue", "λ-max", "Trace", "CV (5%)"]
    rows = []
    
    for i in range(len(result.eigenvalues)):
        ev = result.eigenvalues[i]
        lm = result.lambda_max[i]
        tr = result.trace[i]
        cv = result.cv_trace[i] if i < len(result.cv_trace) else np.nan
        sig = "*" if tr > cv else ""
        
        rows.append([
            i + 1,
            f"{ev:.6f}",
            f"{lm:.4f}",
            f"{tr:.4f}{sig}",
            f"{cv:.3f}"
        ])
    
    table = tabulate(rows, headers=headers, tablefmt="github")
    
    lines = []
    if hasattr(result, 'frequency'):
        lines.append("### Johansen-Fourier Cointegration Test Results")
        freq_type = "cumulative" if result.option == 2 else "single"
        lines.append(f"\n**Frequency:** {result.frequency} ({freq_type})")
    else:
        lines.append("### Johansen Cointegration Test Results")
    
    lines.append(f"\n**Model:** {result._model_name()}")
    lines.append(f"**Observations:** {result.n_obs}")
    lines.append(f"\n{table}")
    lines.append("\n*Note: \\* indicates rejection at 5% significance level*")
    
    return "\n".join(lines)


def _johansen_to_html(result) -> str:
    """Convert Johansen/Johansen-Fourier result to HTML."""
    headers = ["Rank", "Eigenvalue", "λ-max", "Trace", "CV (5%)"]
    rows = []
    
    for i in range(len(result.eigenvalues)):
        ev = result.eigenvalues[i]
        lm = result.lambda_max[i]
        tr = result.trace[i]
        cv = result.cv_trace[i] if i < len(result.cv_trace) else np.nan
        sig = "<sup>*</sup>" if tr > cv else ""
        
        rows.append([
            i + 1,
            f"{ev:.6f}",
            f"{lm:.4f}",
            f"{tr:.4f}{sig}",
            f"{cv:.3f}"
        ])
    
    return tabulate(rows, headers=headers, tablefmt="html")


def _scvecm_to_latex(result) -> str:
    """Convert SC-VECM result to LaTeX."""
    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\caption{SC-VECM Cointegration Test Results}")
    lines.append(r"\begin{tabular}{lcc}")
    lines.append(r"\hline\hline")
    lines.append(r" & No Break & With Break \\")
    lines.append(r"\hline")
    lines.append(f"Trace Statistic & {result.trace_no_break:.4f} & {result.trace_break:.4f} \\\\")
    lines.append(f"SBC & {result.sbc_no_break:.4f} & {result.sbc_break:.4f} \\\\")
    lines.append(f"Optimal Lag & {result.lag_no_break} & {result.lag_break} \\\\")
    lines.append(f"CV (5\\%) & {result.cv_no_break:.3f} & {result.cv_break:.3f} \\\\")
    lines.append(r"\hline")
    lines.append(f"Selected Model & \\multicolumn{{2}}{{c}}{{{result.selected_model.replace('_', ' ').title()}}} \\\\")
    lines.append(r"\hline\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    
    return "\n".join(lines)


def _scvecm_to_markdown(result) -> str:
    """Convert SC-VECM result to Markdown."""
    headers = ["", "No Break", "With Break"]
    rows = [
        ["Trace Statistic", f"{result.trace_no_break:.4f}", f"{result.trace_break:.4f}"],
        ["SBC", f"{result.sbc_no_break:.4f}", f"{result.sbc_break:.4f}"],
        ["Optimal Lag", str(result.lag_no_break), str(result.lag_break)],
        ["CV (5%)", f"{result.cv_no_break:.3f}", f"{result.cv_break:.3f}"]
    ]
    
    table = tabulate(rows, headers=headers, tablefmt="github")
    
    lines = [
        "### SC-VECM Cointegration Test Results",
        f"\n**Selected Model:** {result.selected_model.replace('_', ' ').title()}",
        f"\n{table}"
    ]
    
    if result.break_location is not None:
        lines.append(f"\n**Break Location:** {result.break_location} (fraction: {result.break_fraction:.3f})")
    
    return "\n".join(lines)


def _sbc_to_latex(result) -> str:
    """Convert SBC result to LaTeX."""
    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\caption{SBC Model Selection Test Results}")
    lines.append(r"\begin{tabular}{lccc}")
    lines.append(r"\hline\hline")
    lines.append(r" & Johansen & SC-VECM & Fourier \\")
    lines.append(r"\hline")
    lines.append(f"Trace & {result.all_trace['johansen']:.4f} & "
                 f"{result.all_trace['sc_vecm']:.4f} & {result.all_trace['fourier']:.4f} \\\\")
    lines.append(f"SBC & {result.all_sbc['johansen']:.4f} & "
                 f"{result.all_sbc['sc_vecm']:.4f} & {result.all_sbc['fourier']:.4f} \\\\")
    lines.append(r"\hline")
    lines.append(f"Selected & \\multicolumn{{3}}{{c}}{{{result.selected_model.title()}}} \\\\")
    lines.append(r"\hline\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    
    return "\n".join(lines)


def _sbc_to_markdown(result) -> str:
    """Convert SBC result to Markdown."""
    headers = ["", "Johansen", "SC-VECM", "Fourier"]
    rows = [
        ["Trace", f"{result.all_trace['johansen']:.4f}", 
         f"{result.all_trace['sc_vecm']:.4f}", f"{result.all_trace['fourier']:.4f}"],
        ["SBC", f"{result.all_sbc['johansen']:.4f}", 
         f"{result.all_sbc['sc_vecm']:.4f}", f"{result.all_sbc['fourier']:.4f}"]
    ]
    
    table = tabulate(rows, headers=headers, tablefmt="github")
    
    lines = [
        "### SBC Model Selection Test Results",
        f"\n**Selected Model:** {result.selected_model.title()}",
        f"\n{table}",
        f"\n**Trace from selected:** {result.trace:.4f}",
        f"**Critical Value (5%):** {result.cv:.4f}"
    ]
    
    return "\n".join(lines)


def _union_to_latex(result) -> str:
    """Convert Union test result to LaTeX."""
    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\caption{Union of Rejections Test Results}")
    lines.append(r"\begin{tabular}{lcc}")
    lines.append(r"\hline\hline")
    lines.append(r" & Fourier & SC-VECM \\")
    lines.append(r"\hline")
    lines.append(f"Trace Statistic & {result.fourier_trace:.4f} & {result.scvecm_trace:.4f} \\\\")
    lines.append(f"CV (original) & {result.fourier_cv:.3f} & {result.scvecm_cv:.3f} \\\\")
    lines.append(f"CV (scaled) & {result.fourier_cv_scaled:.3f} & {result.scvecm_cv_scaled:.3f} \\\\")
    rejects_f = "Yes" if result.fourier_rejects else "No"
    rejects_s = "Yes" if result.scvecm_rejects else "No"
    lines.append(f"Rejects H0 & {rejects_f} & {rejects_s} \\\\")
    lines.append(r"\hline")
    union_decision = "Reject H0" if result.reject_h0 else "Fail to reject H0"
    lines.append(f"Union Test & \\multicolumn{{2}}{{c}}{{{union_decision}}} \\\\")
    lines.append(r"\hline\hline")
    lines.append(r"\end{tabular}")
    lines.append(f"\\footnotesize{{Scale factor: {result.scale_factor:.4f}}}")
    lines.append(r"\end{table}")
    
    return "\n".join(lines)


def _union_to_markdown(result) -> str:
    """Convert Union test result to Markdown."""
    headers = ["", "Fourier", "SC-VECM"]
    rejects_f = "Yes" if result.fourier_rejects else "No"
    rejects_s = "Yes" if result.scvecm_rejects else "No"
    rows = [
        ["Trace Statistic", f"{result.fourier_trace:.4f}", f"{result.scvecm_trace:.4f}"],
        ["CV (original)", f"{result.fourier_cv:.3f}", f"{result.scvecm_cv:.3f}"],
        ["CV (scaled)", f"{result.fourier_cv_scaled:.3f}", f"{result.scvecm_cv_scaled:.3f}"],
        ["Rejects H0", rejects_f, rejects_s]
    ]
    
    table = tabulate(rows, headers=headers, tablefmt="github")
    
    union_decision = "**REJECT H0**" if result.reject_h0 else "Fail to reject H0"
    
    lines = [
        "### Union of Rejections Test Results",
        f"\n{table}",
        f"\n**Union Test Decision:** {union_decision}",
        f"**Scale Factor:** {result.scale_factor:.4f}"
    ]
    
    return "\n".join(lines)


def create_publication_table(results: list, test_names: list = None,
                            caption: str = "Cointegration Test Results",
                            label: str = "tab:coint") -> str:
    """
    Create a comprehensive LaTeX table comparing multiple test results.
    
    Parameters
    ----------
    results : list
        List of test result objects
    test_names : list, optional
        Names for each test (default: auto-generated)
    caption : str
        Table caption
    label : str
        LaTeX label for referencing
        
    Returns
    -------
    str
        Complete LaTeX table code
    """
    if test_names is None:
        test_names = [f"Test {i+1}" for i in range(len(results))]
    
    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(f"\\caption{{{caption}}}")
    lines.append(f"\\label{{{label}}}")
    lines.append(r"\begin{tabular}{l" + "c" * len(results) + "}")
    lines.append(r"\hline\hline")
    
    # Header row
    header = " & " + " & ".join(test_names) + r" \\"
    lines.append(header)
    lines.append(r"\hline")
    
    # Extract comparable statistics
    traces = []
    cvs = []
    rejects = []
    
    for r in results:
        if hasattr(r, 'trace') and hasattr(r, 'cv_trace'):
            traces.append(r.trace[0] if len(r.trace) > 0 else np.nan)
            cvs.append(r.cv_trace[0] if len(r.cv_trace) > 0 else np.nan)
            rejects.append(r.trace[0] > r.cv_trace[0] if len(r.trace) > 0 else False)
        elif hasattr(r, 'trace'):
            traces.append(r.trace)
            cvs.append(r.cv)
            rejects.append(r.trace > r.cv)
        else:
            traces.append(np.nan)
            cvs.append(np.nan)
            rejects.append(False)
    
    # Data rows
    trace_row = "Trace & " + " & ".join([f"{t:.4f}" for t in traces]) + r" \\"
    cv_row = "CV (5\\%) & " + " & ".join([f"{c:.3f}" for c in cvs]) + r" \\"
    reject_row = "Reject H0 & " + " & ".join(["Yes" if r else "No" for r in rejects]) + r" \\"
    
    lines.append(trace_row)
    lines.append(cv_row)
    lines.append(reject_row)
    
    lines.append(r"\hline\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    
    return "\n".join(lines)
