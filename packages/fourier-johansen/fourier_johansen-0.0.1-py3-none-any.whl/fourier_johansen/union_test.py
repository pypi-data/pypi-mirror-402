"""
Union of rejections test.

Combines the Johansen-Fourier test (for smooth breaks) with the SC-VECM test
(for sharp breaks) using a union of rejections strategy.

Reference:
    Pascalau, R., Lee, J., Nazlioglu, S., Lu, Y. O. (2022).
    "Johansen-type Cointegration Tests with a Fourier Function".
    Journal of Time Series Analysis 43(5): 828-852.
    Section 4: Union of Rejections Strategy and SBC Tests
    
    Harvey, D., Leybourne, S., Taylor, A. (2009). 
    Unit root testing in practice: dealing with uncertainty over the 
    trend and initial condition. Econometric Theory 25:587-636.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple

from .johansen_fourier import johansen_fourier, sc_fourier
from .sc_vecm import sc_vecm
from .critical_values import get_union_scale


@dataclass
class UnionResult:
    """
    Container for Union of Rejections test results.
    
    Attributes
    ----------
    reject_h0 : bool
        Whether null hypothesis is rejected by union test
    fourier_trace : float
        Trace statistic from Johansen-Fourier test
    fourier_cv : float
        Critical value for Fourier test
    fourier_cv_scaled : float
        Scaled critical value for union test
    scvecm_trace : float
        Trace statistic from SC-VECM test
    scvecm_cv : float
        Critical value for SC-VECM test
    scvecm_cv_scaled : float
        Scaled critical value for union test
    scale_factor : float
        Scale factor used for size adjustment
    fourier_rejects : bool
        Whether Fourier test rejects H0
    scvecm_rejects : bool
        Whether SC-VECM test rejects H0
    frequency : int
        Fourier frequency used
    break_location : Optional[int]
        SC-VECM break location
    rank : int
        Cointegration rank tested
    n_vars : int
        Number of variables
    n_obs : int
        Number of observations
    """
    reject_h0: bool
    fourier_trace: float
    fourier_cv: float
    fourier_cv_scaled: float
    scvecm_trace: float
    scvecm_cv: float
    scvecm_cv_scaled: float
    scale_factor: float
    fourier_rejects: bool
    scvecm_rejects: bool
    frequency: int
    break_location: Optional[int]
    rank: int
    n_vars: int
    n_obs: int
    
    def summary(self) -> str:
        """Generate publication-ready summary table."""
        lines = []
        lines.append("=" * 70)
        lines.append("              Union of Rejections Test Results")
        lines.append("=" * 70)
        lines.append(f" # Variables   : {self.n_vars}")
        lines.append(f" Observations  : {self.n_obs}")
        lines.append(f" Rank Tested   : {self.rank}")
        lines.append(f" Scale Factor  : {self.scale_factor:.4f}")
        lines.append("-" * 70)
        lines.append(f"{'':>20}  {'Fourier':>15}  {'SC-VECM':>15}")
        lines.append("-" * 70)
        lines.append(f"{'Trace Statistic':>20}  {self.fourier_trace:>15.4f}  {self.scvecm_trace:>15.4f}")
        lines.append(f"{'CV (5%, original)':>20}  {self.fourier_cv:>15.3f}  {self.scvecm_cv:>15.3f}")
        lines.append(f"{'CV (5%, scaled)':>20}  {self.fourier_cv_scaled:>15.3f}  {self.scvecm_cv_scaled:>15.3f}")
        lines.append(f"{'Individual Reject':>20}  {'Yes' if self.fourier_rejects else 'No':>15}  "
                     f"{'Yes' if self.scvecm_rejects else 'No':>15}")
        lines.append("=" * 70)
        lines.append(f" UNION TEST RESULT: {'REJECT H0' if self.reject_h0 else 'FAIL TO REJECT H0'}")
        lines.append(f" (Rejects if either scaled test rejects)")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return self.summary()


def union_test(x: np.ndarray, model: int = 3, k: int = 2, f: int = 2,
               option: int = 2, lambda_loc: float = 0.5, 
               alpha: float = 0.05, r: int = 0) -> UnionResult:
    """
    Union of rejections test combining Fourier and SC-VECM tests.
    
    The union test rejects H0 if either the Johansen-Fourier test or the
    SC-VECM test rejects, after applying a size adjustment to maintain
    the correct nominal size.
    
    The test uses scaled critical values:
    Reject H0 if (Trace_JF > c_γ * CV_JF) OR (Trace_SCVECM > c_γ * CV_SCVECM)
    
    where c_γ is the scale factor from Tables I-II of the paper.
    
    Parameters
    ----------
    x : np.ndarray
        T x m matrix of endogenous variables
    model : int, default=3
        Johansen-Fourier model type (1-4)
    k : int, default=2
        Number of VAR lags
    f : int, default=2
        Fourier frequency (or max cumulative frequency)
    option : int, default=2
        Fourier option: 1=single, 2=cumulative frequency
    lambda_loc : float, default=0.5
        Break location for SC-VECM (0.25, 0.50, or 0.75)
    alpha : float, default=0.05
        Significance level (0.01, 0.05, or 0.10)
    r : int, default=0
        Cointegration rank to test
        
    Returns
    -------
    UnionResult
        Object containing test results and diagnostics.
        
    Examples
    --------
    >>> import numpy as np
    >>> from fourier_johansen import union_test
    >>> 
    >>> np.random.seed(42)
    >>> T = 200
    >>> x1 = np.cumsum(np.random.randn(T))
    >>> x2 = x1 + np.random.randn(T) * 0.5
    >>> X = np.column_stack([x1, x2])
    >>> 
    >>> result = union_test(X, model=3, k=2, f=2, option=2)
    >>> print(result)
    
    Notes
    -----
    The union test is recommended when the nature of breaks is unknown:
    - Johansen-Fourier works better with smooth breaks
    - SC-VECM works better with sharp breaks
    - Union test combines benefits of both
    
    From the paper (Section 4):
    - Size-adjusted power of union test is higher than either test in most cases
    - Size distortions may occur with very pronounced smooth breaks
    
    References
    ----------
    Pascalau, R., Lee, J., Nazlioglu, S., Lu, Y. O. (2022).
    "Johansen-type Cointegration Tests with a Fourier Function".
    Journal of Time Series Analysis 43(5): 828-852.
    
    Harvey, D., Leybourne, S., Taylor, A. (2009). 
    Unit root testing in practice: dealing with uncertainty over the 
    trend and initial condition. Econometric Theory 25:587-636.
    """
    x = np.asarray(x, dtype=np.float64)
    
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    
    T, n = x.shape
    
    # Run Johansen-Fourier test
    jf_result = johansen_fourier(x, model, k, f, option)
    
    if r < len(jf_result.trace):
        jf_trace = jf_result.trace[r]
        jf_cv = jf_result.cv_trace[r]
    else:
        jf_trace = jf_result.trace[-1]
        jf_cv = jf_result.cv_trace[-1]
    
    # Run SC-VECM test
    scvecm_result = sc_vecm(r, x, max_lag=k + 2, lambda_L=0.1)
    
    # Use the selected model's trace and CV
    if scvecm_result.selected_model == "break":
        scvecm_trace = scvecm_result.trace_break
        scvecm_cv = scvecm_result.cv_break
        break_loc = scvecm_result.break_location
    else:
        scvecm_trace = scvecm_result.trace_no_break
        scvecm_cv = scvecm_result.cv_no_break
        break_loc = None
    
    # Get scale factor for union test
    scale = get_union_scale(n, f, lambda_loc, T, alpha)
    
    # Apply scaling to critical values
    jf_cv_scaled = scale * jf_cv
    scvecm_cv_scaled = scale * scvecm_cv
    
    # Individual rejections (with scaled CVs)
    jf_rejects = jf_trace > jf_cv_scaled
    scvecm_rejects = scvecm_trace > scvecm_cv_scaled
    
    # Union rejection: reject if either rejects
    union_rejects = jf_rejects or scvecm_rejects
    
    return UnionResult(
        reject_h0=union_rejects,
        fourier_trace=jf_trace,
        fourier_cv=jf_cv,
        fourier_cv_scaled=jf_cv_scaled,
        scvecm_trace=scvecm_trace,
        scvecm_cv=scvecm_cv,
        scvecm_cv_scaled=scvecm_cv_scaled,
        scale_factor=scale,
        fourier_rejects=jf_rejects,
        scvecm_rejects=scvecm_rejects,
        frequency=f,
        break_location=break_loc,
        rank=r,
        n_vars=n,
        n_obs=T
    )
