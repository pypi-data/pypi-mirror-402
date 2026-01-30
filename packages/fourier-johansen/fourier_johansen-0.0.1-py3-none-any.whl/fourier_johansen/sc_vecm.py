"""
SC-VECM cointegration test for sharp breaks.

Implements the SC-VECM test from Harris et al. (2016) which allows for 
a possible trend break at an unknown point.

Reference:
    Harris, D., Leybourne, S.J., Taylor, A.R. (2016). 
    Tests of the co-integration rank in VAR models in the presence of 
    a possible break in trend at an unknown point. 
    Journal of Econometrics 192(2): 451-467.
"""

import numpy as np
from numpy.linalg import inv, det, cholesky
from scipy.linalg import eigh
from dataclasses import dataclass
from typing import Optional

from .critical_values import CV_SCVECM_NO_BREAK, CV_SCVECM_BREAK, SCVECM_BREAK_FRACTIONS


def _lagn(x: np.ndarray, n: int) -> np.ndarray:
    """Create lagged array."""
    if n <= 0:
        return x.copy()
    T = x.shape[0]
    if x.ndim == 1:
        result = np.full(T, np.nan)
        result[n:] = x[:-n]
    else:
        m = x.shape[1]
        result = np.full((T, m), np.nan)
        result[n:, :] = x[:-n, :]
    return result


def _trimr(x: np.ndarray, top: int, bottom: int) -> np.ndarray:
    """Trim rows."""
    if bottom == 0:
        return x[top:].copy()
    return x[top:-bottom].copy()


@dataclass
class SCVECMResult:
    """Container for SC-VECM test results."""
    trace_no_break: float
    sbc_no_break: float
    lag_no_break: int
    cv_no_break: float
    trace_break: float
    sbc_break: float
    lag_break: int
    cv_break: float
    break_location: Optional[int]
    break_fraction: Optional[float]
    selected_model: str
    rank: int
    n_vars: int
    n_obs: int
    
    def summary(self) -> str:
        """Generate summary table."""
        lines = []
        lines.append("=" * 70)
        lines.append("              SC-VECM Cointegration Test Results")
        lines.append("=" * 70)
        lines.append(f" # Variables   : {self.n_vars}")
        lines.append(f" Observations  : {self.n_obs}")
        lines.append(f" Rank Tested   : {self.rank}")
        lines.append(f" Selected Model: {self.selected_model.replace('_', ' ').title()}")
        if self.break_location is not None:
            lines.append(f" Break Location: {self.break_location} (fraction: {self.break_fraction:.3f})")
        lines.append("-" * 70)
        lines.append(f"{'':>18}  {'No Break':>12}  {'With Break':>12}")
        lines.append("-" * 70)
        lines.append(f"{'Trace Statistic':>18}  {self.trace_no_break:>12.4f}  {self.trace_break:>12.4f}")
        lines.append(f"{'SBC':>18}  {self.sbc_no_break:>12.4f}  {self.sbc_break:>12.4f}")
        lines.append(f"{'Optimal Lag':>18}  {self.lag_no_break:>12d}  {self.lag_break:>12d}")
        lines.append(f"{'CV (5%)':>18}  {self.cv_no_break:>12.3f}  {self.cv_break:>12.3f}")
        lines.append("=" * 70)
        
        if self.selected_model == "break":
            reject = self.trace_break > self.cv_break
        else:
            reject = self.trace_no_break > self.cv_no_break
        
        decision = "Reject H0" if reject else "Fail to reject H0"
        lines.append(f"Decision at 5% level: {decision}")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return self.summary()


def sc_vecm(r: int, y: np.ndarray, max_lag: int = 4, 
            lambda_L: float = 0.1) -> SCVECMResult:
    """
    SC-VECM cointegration test with possible trend break.
    
    Parameters
    ----------
    r : int
        Cointegration rank to test
    y : np.ndarray
        T x n matrix of endogenous variables
    max_lag : int, default=4
        Maximum lag for VAR model
    lambda_L : float, default=0.1
        Trimming rate for break search
        
    Returns
    -------
    SCVECMResult
        Test results and model selection
    """
    y = np.asarray(y, dtype=np.float64)
    
    if y.ndim == 1:
        y = y.reshape(-1, 1)
    
    T, n = y.shape
    
    # Break search range
    trim_start = int(np.floor(lambda_L * T))
    trim_end = int(np.floor((1 - lambda_L) * T))
    break_candidates = np.arange(trim_start, trim_end + 1)
    
    # Compute log-likelihood for no-break models
    logL_no_break = np.zeros((max_lag, n + 1))
    for p in range(1, max_lag + 1):
        try:
            logL_no_break[p - 1, :] = _get_logL_vecm(y, p)
        except:
            logL_no_break[p - 1, :] = -np.inf
    
    # Compute log-likelihood for break models
    logL_break = np.zeros((len(break_candidates), max_lag, n + 1))
    for b_idx, b in enumerate(break_candidates):
        for p in range(1, max_lag + 1):
            try:
                logL_break[b_idx, p - 1, :] = _get_logL_vecm_break(y, p, b)
            except:
                logL_break[b_idx, p - 1, :] = -np.inf
    
    # Find optimal break points for each lag
    break_hat_idx = np.argmax(logL_break[:, :, n], axis=0)
    
    # No-break model: select optimal lag using SBC
    lag_candidates = np.arange(1, max_lag + 1)
    sbc_no_break_all = -2 * logL_no_break[:, n] + np.log(T) * (n ** 2 * lag_candidates)
    p_no_break = np.argmin(sbc_no_break_all) + 1
    
    # Break model: select optimal lag using SBC
    logL_break_optimal = np.array([logL_break[break_hat_idx[p - 1], p - 1, n] 
                                    for p in lag_candidates])
    sbc_break_all = -2 * logL_break_optimal + np.log(T) * (n ** 2 * lag_candidates)
    p_break = np.argmin(sbc_break_all) + 1
    
    # Get break location for optimal lag
    b_hat_idx = break_hat_idx[p_break - 1]
    b_hat = break_candidates[b_hat_idx]
    b_fraction = b_hat / T
    
    # Trace statistics
    r_col = min(r, n)
    n_col = n
    
    tr0 = 2 * (logL_no_break[p_no_break - 1, n_col] - logL_no_break[p_no_break - 1, r_col])
    tr1 = 2 * (logL_break[b_hat_idx, p_break - 1, n_col] - 
               logL_break[b_hat_idx, p_break - 1, r_col])
    
    # Critical values
    cv0 = CV_SCVECM_NO_BREAK[min(n - r - 1, len(CV_SCVECM_NO_BREAK) - 1)]
    
    frac_idx = np.argmin(np.abs(SCVECM_BREAK_FRACTIONS - b_fraction))
    cv1 = CV_SCVECM_BREAK[frac_idx, min(n - r - 1, CV_SCVECM_BREAK.shape[1] - 1)]
    
    # SBC for model selection
    sbc0 = -2 * logL_no_break[p_no_break - 1, r_col] + (n ** 2 * p_no_break) * np.log(T)
    sbc1 = -2 * logL_break[b_hat_idx, p_break - 1, r_col] + \
           (n + r + 2 + (n ** 2) * p_break) * np.log(T)
    
    selected = "break" if sbc1 < sbc0 else "no_break"
    
    return SCVECMResult(
        trace_no_break=max(tr0, 0),
        sbc_no_break=sbc0,
        lag_no_break=p_no_break,
        cv_no_break=cv0,
        trace_break=max(tr1, 0),
        sbc_break=sbc1,
        lag_break=p_break,
        cv_break=cv1,
        break_location=b_hat if selected == "break" else None,
        break_fraction=b_fraction if selected == "break" else None,
        selected_model=selected,
        rank=r,
        n_vars=n,
        n_obs=T
    )


def _get_logL_vecm(y: np.ndarray, p: int) -> np.ndarray:
    """Compute log-likelihood for VECM without break."""
    T, n = y.shape
    trend = np.arange(1, T + 1).reshape(-1, 1)
    
    # First differences
    dy = y[1:, :] - y[:-1, :]
    
    # Build matrices
    z0 = _trimr(dy, p - 1, 0)
    z1 = np.column_stack([_trimr(_lagn(y, p - 1), p, 0), _trimr(trend, p, 0)])
    
    z2 = np.ones((T - p, 1))
    for j in range(1, p):
        z2 = np.column_stack([z2, _trimr(_lagn(dy, p - 1 - j), j, 0)])
    
    # Fix dimensions: z0 has T-1-(p-1) = T-p rows
    # z1 and z2 should match
    min_rows = min(z0.shape[0], z1.shape[0], z2.shape[0])
    z0 = z0[:min_rows]
    z1 = z1[:min_rows]
    z2 = z2[:min_rows]
    
    # OLS residuals
    def ols_resid(Y, X):
        try:
            beta = np.linalg.lstsq(X, Y, rcond=None)[0]
            return Y - X @ beta
        except:
            return Y
    
    r0 = ols_resid(z0, z2)
    r1 = ols_resid(z1, z2)
    
    # Eigenvalues
    try:
        Li = inv(cholesky(r1.T @ r1).T)
        lam_full = eigh(Li @ r1.T @ r0 @ np.linalg.pinv(r0.T @ r0) @ r0.T @ r1 @ Li.T,
                        eigvals_only=True)
        lam = np.concatenate([[0], np.sort(lam_full[::-1])[:-1]])
    except:
        lam = np.zeros(n + 1)
    
    lam = np.clip(lam, 0, 0.9999999)
    
    if len(lam) < n + 1:
        lam = np.concatenate([lam, np.zeros(n + 1 - len(lam))])
    
    T_eff = min_rows
    det_val = max(det(r0.T @ r0 / T_eff), 1e-300)
    logL = -(T_eff / 2) * (np.log(det_val) + np.cumsum(np.log(1 - lam[:n + 1])))
    
    return logL


def _get_logL_vecm_break(y: np.ndarray, k: int, b: int) -> np.ndarray:
    """Compute log-likelihood for VECM with break at b."""
    T, n = y.shape
    trend = np.arange(1, T + 1).reshape(-1, 1)
    
    dy = y[1:, :] - y[:-1, :]
    
    # Break dummies
    E1 = (trend <= b).astype(float)
    E2 = (trend > b).astype(float)
    tE = np.column_stack([np.cumsum(E1), np.cumsum(E2)])
    
    # Impulse dummies
    D = np.zeros((T, k))
    for j in range(k):
        if b + j < T:
            D[b + j, j] = 1.0
    
    z0 = _trimr(dy, k - 1, 0)
    z1 = np.column_stack([_trimr(_lagn(y, k - 1), k, 0), _trimr(tE, k, 0)])
    
    z2 = np.column_stack([_trimr(E1, k, 0), _trimr(E2, k, 0), _trimr(D, k, 0)])
    for j in range(1, k):
        z2 = np.column_stack([z2, _trimr(_lagn(dy, k - 1 - j), j, 0)])
    
    # Fix dimensions
    min_rows = min(z0.shape[0], z1.shape[0], z2.shape[0])
    z0 = z0[:min_rows]
    z1 = z1[:min_rows]
    z2 = z2[:min_rows]
    
    def ols_resid(Y, X):
        try:
            beta = np.linalg.lstsq(X, Y, rcond=None)[0]
            return Y - X @ beta
        except:
            return Y
    
    r0 = ols_resid(z0, z2)
    r1 = ols_resid(z1, z2)
    
    try:
        Li = inv(cholesky(r1.T @ r1).T)
        lam_full = eigh(Li @ r1.T @ r0 @ np.linalg.pinv(r0.T @ r0) @ r0.T @ r1 @ Li.T,
                        eigvals_only=True)
        lam = np.concatenate([[0], np.sort(lam_full[::-1])[:-2]])
    except:
        lam = np.zeros(n + 1)
    
    lam = np.clip(lam, 0, 0.9999999)
    
    if len(lam) < n + 1:
        lam = np.concatenate([lam, np.zeros(n + 1 - len(lam))])
    
    T_eff = min_rows
    det_val = max(det(r0.T @ r0 / T_eff), 1e-300)
    logL = -(T_eff / 2) * (np.log(det_val) + np.cumsum(np.log(1 - lam[:n + 1])))
    
    return logL
