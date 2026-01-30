"""
SBC-based model selection test.

Extends Harris et al. (2016) to select among Johansen, SC-VECM, and 
Johansen-Fourier models using Schwarz Bayesian Criterion.

Reference:
    Pascalau, R., Lee, J., Nazlioglu, S., Lu, Y. O. (2022).
    "Johansen-type Cointegration Tests with a Fourier Function".
    Journal of Time Series Analysis 43(5): 828-852.
    Section 4: Union of Rejections Strategy and SBC Tests
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional

from .johansen import johansen
from .johansen_fourier import johansen_fourier, sc_fourier
from .sc_vecm import sc_vecm


@dataclass
class SBCResult:
    """
    Container for SBC model selection test results.
    
    Attributes
    ----------
    trace : float
        Trace statistic from selected model
    sbc : float
        SBC value for selected model
    lag : int
        Optimal lag from selected model
    cv : float
        Critical value from selected model
    selected_model : str
        Name of selected model ("johansen", "sc_vecm", or "fourier")
    break_or_freq : Optional[float]
        Break location (for SC-VECM) or frequency (for Fourier)
    all_sbc : dict
        SBC values for all models
    all_trace : dict
        Trace statistics for all models
    rank : int
        Cointegration rank tested
    n_vars : int
        Number of variables
    n_obs : int
        Number of observations
    """
    trace: float
    sbc: float
    lag: int
    cv: float
    selected_model: str
    break_or_freq: Optional[float]
    all_sbc: dict
    all_trace: dict
    rank: int
    n_vars: int
    n_obs: int
    
    def summary(self) -> str:
        """Generate publication-ready summary table."""
        lines = []
        lines.append("=" * 75)
        lines.append("                 SBC Model Selection Test Results")
        lines.append("=" * 75)
        lines.append(f" # Variables   : {self.n_vars}")
        lines.append(f" Observations  : {self.n_obs}")
        lines.append(f" Rank Tested   : {self.rank}")
        lines.append(f" Selected Model: {self.selected_model.title()}")
        lines.append("-" * 75)
        lines.append(f"{'':>18}  {'Johansen':>12}  {'SC-VECM':>12}  {'Fourier':>12}")
        lines.append("-" * 75)
        lines.append(f"{'Trace Statistic':>18}  {self.all_trace.get('johansen', np.nan):>12.4f}  "
                     f"{self.all_trace.get('sc_vecm', np.nan):>12.4f}  "
                     f"{self.all_trace.get('fourier', np.nan):>12.4f}")
        lines.append(f"{'SBC':>18}  {self.all_sbc.get('johansen', np.nan):>12.4f}  "
                     f"{self.all_sbc.get('sc_vecm', np.nan):>12.4f}  "
                     f"{self.all_sbc.get('fourier', np.nan):>12.4f}")
        lines.append("=" * 75)
        lines.append(f" Selected: {self.selected_model.upper()}")
        lines.append(f" Trace from selected model: {self.trace:.4f}")
        lines.append(f" Critical value (5%): {self.cv:.4f}")
        
        reject = self.trace > self.cv
        decision = "Reject H0 (cointegration detected)" if reject else "Fail to reject H0"
        lines.append(f" Decision: {decision}")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return self.summary()


def sbc_test(r: int, y: np.ndarray, max_lag: int = 4, lambda_L: float = 0.1,
             f_max: int = 3, option: int = 2, model: int = 3) -> SBCResult:
    """
    SBC-based model selection among Johansen, SC-VECM, and Fourier models.
    
    This procedure selects the best model using Schwarz Bayesian Criterion
    and returns the corresponding test statistic and critical value.
    
    Parameters
    ----------
    r : int
        Cointegration rank to test
    y : np.ndarray
        T x n matrix of endogenous variables
    max_lag : int, default=4
        Maximum lag for VAR model
    lambda_L : float, default=0.1
        Trimming rate for SC-VECM break search
    f_max : int, default=3
        Maximum Fourier frequency
    option : int, default=2
        Fourier option: 1=single, 2=cumulative frequency
    model : int, default=3
        Johansen-Fourier model type (1-4)
        
    Returns
    -------
    SBCResult
        Object containing selected model statistics and comparison.
        
    Examples
    --------
    >>> import numpy as np
    >>> from fourier_johansen import sbc_test
    >>> 
    >>> np.random.seed(42)
    >>> T = 200
    >>> x1 = np.cumsum(np.random.randn(T))
    >>> x2 = x1 + np.random.randn(T) * 0.5
    >>> x3 = np.cumsum(np.random.randn(T))
    >>> X = np.column_stack([x1, x2, x3])
    >>> 
    >>> result = sbc_test(0, X, max_lag=4, f_max=3)
    >>> print(result)
    
    Notes
    -----
    The SBC test has fairly correct sizes in all cases, including sharp breaks,
    smooth breaks, and no break. This is a practically useful procedure since
    the type of breaks is usually unknown.
    
    From the paper (Section 4):
    - When no break: Johansen model selected ~80-90% of the time
    - When smooth breaks: Fourier model selected ~40-100% depending on magnitude
    - When sharp breaks: SC-VECM model selected ~100% of the time
    
    References
    ----------
    Pascalau, R., Lee, J., Nazlioglu, S., Lu, Y. O. (2022).
    "Johansen-type Cointegration Tests with a Fourier Function".
    Journal of Time Series Analysis 43(5): 828-852.
    """
    y = np.asarray(y, dtype=np.float64)
    
    if y.ndim == 1:
        y = y.reshape(-1, 1)
    
    T, n = y.shape
    
    # Run SC-VECM test
    scvecm_result = sc_vecm(r, y, max_lag, lambda_L)
    
    # Get Johansen and SC-VECM statistics
    tr0 = scvecm_result.trace_no_break
    sbc0 = scvecm_result.sbc_no_break
    p0 = scvecm_result.lag_no_break
    cv0 = scvecm_result.cv_no_break
    
    tr1 = scvecm_result.trace_break
    sbc1 = scvecm_result.sbc_break
    p1 = scvecm_result.lag_break
    cv1 = scvecm_result.cv_break
    tb = scvecm_result.break_location
    
    # Run SC-Fourier for optimal frequency selection
    tr2, sbc2, p2, cv2, f_hat, _ = sc_fourier(r, y, model, max_lag, f_max, option)
    
    # Collect all values
    sbc_vec = np.array([sbc0, sbc1, sbc2])
    tr_vec = np.array([tr0, tr1, tr2])
    cv_vec = np.array([cv0, cv1, cv2])
    p_vec = np.array([p0, p1, p2])
    br_vec = [None, tb, f_hat]
    model_names = ["johansen", "sc_vecm", "fourier"]
    
    # Select model with minimum SBC
    min_idx = np.argmin(sbc_vec)
    
    selected_model = model_names[min_idx]
    selected_trace = tr_vec[min_idx]
    selected_sbc = sbc_vec[min_idx]
    selected_cv = cv_vec[min_idx]
    selected_lag = int(p_vec[min_idx])
    selected_br = br_vec[min_idx]
    
    return SBCResult(
        trace=selected_trace,
        sbc=selected_sbc,
        lag=selected_lag,
        cv=selected_cv,
        selected_model=selected_model,
        break_or_freq=selected_br,
        all_sbc={"johansen": sbc0, "sc_vecm": sbc1, "fourier": sbc2},
        all_trace={"johansen": tr0, "sc_vecm": tr1, "fourier": tr2},
        rank=r,
        n_vars=n,
        n_obs=T
    )
