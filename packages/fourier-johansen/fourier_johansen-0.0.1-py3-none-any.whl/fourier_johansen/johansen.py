"""
Standard Johansen cointegration test implementation.

Reference:
    Johansen, S. (1991). Estimation and hypothesis testing of cointegration 
    vectors in gaussian Vector Autoregressive models. Econometrica 59(6), 1551-1580.
"""

import numpy as np
from numpy.linalg import inv, det, eig, cholesky
from scipy.linalg import eigh
from dataclasses import dataclass
from typing import Optional

from .critical_values import CV_JOHANSEN_TRACE


def _lagn(x: np.ndarray, n: int) -> np.ndarray:
    """Create lagged array with NaN padding."""
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
    """Trim rows from array."""
    if bottom == 0:
        return x[top:].copy()
    return x[top:-bottom].copy()


@dataclass
class JohansenResult:
    """Container for Johansen cointegration test results."""
    eigenvalues: np.ndarray
    lambda_max: np.ndarray
    trace: np.ndarray
    cv_trace: np.ndarray
    cv_lambda: Optional[np.ndarray]
    log_likelihood: np.ndarray
    n_vars: int
    n_obs: int
    model: int
    k: int
    
    def summary(self) -> str:
        """Generate publication-ready summary table."""
        lines = []
        lines.append("=" * 65)
        lines.append("              Johansen Cointegration Test Results")
        lines.append("=" * 65)
        lines.append(f" # Variables : {self.n_vars}")
        lines.append(f" Model       : {self._model_name()}")
        lines.append(f" VAR Lags    : {self.k}")
        lines.append(f" VECM Lags   : {self.k - 1}")
        lines.append(f" Observations: {self.n_obs}")
        lines.append("-" * 65)
        lines.append(f"{'Rank':>6}  {'Eigenvalue':>12}  {'Lambda-max':>12}  "
                     f"{'Trace':>10}  {'CV(5%)':>10}")
        lines.append("-" * 65)
        
        for i in range(len(self.eigenvalues)):
            ev = self.eigenvalues[i]
            lm = self.lambda_max[i]
            tr = self.trace[i]
            cv = self.cv_trace[i] if i < len(self.cv_trace) else np.nan
            sig = "*" if tr > cv else ""
            
            lines.append(f"{i+1:>6}  {ev:>12.6f}  {lm:>12.4f}  "
                         f"{tr:>10.4f}{sig:1}  {cv:>10.3f}")
        
        lines.append("=" * 65)
        lines.append("Note: * indicates rejection of null at 5% level")
        
        return "\n".join(lines)
    
    def _model_name(self) -> str:
        names = {
            1: "None (no deterministic terms)",
            2: "Restricted Constant (RC)",
            3: "Unrestricted Constant",
            4: "Restricted Trend (RT)",
            5: "Unrestricted Trend"
        }
        return names.get(self.model, f"Model {self.model}")
    
    def __repr__(self) -> str:
        return self.summary()


def johansen(x: np.ndarray, model: int = 2, k: int = 2) -> JohansenResult:
    """
    Johansen cointegration test.
    
    Parameters
    ----------
    x : np.ndarray
        T x m matrix of endogenous variables
    model : int, default=2
        1=None, 2=Restricted Constant, 3=Unrestricted Constant,
        4=Restricted Trend, 5=Unrestricted Trend
    k : int, default=2
        Number of lags for VAR model
        
    Returns
    -------
    JohansenResult
        Object containing test statistics and critical values
    """
    x = np.asarray(x, dtype=np.float64)
    
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    
    T, m = x.shape
    
    # First differences: dx has T-1 rows
    dx = x[1:, :] - x[:-1, :]
    
    # Deterministic terms (T rows for levels)
    constant = np.ones((T, 1))
    trend = np.arange(1, T + 1).reshape(-1, 1)
    
    # Model-specific setup
    if model == 1:
        # None
        dt = np.zeros((T - 1, 0))  # Empty for differences
        x_aug = x.copy()
    elif model == 2:
        # Restricted constant
        dt = np.zeros((T - 1, 0))  # Empty for differences
        x_aug = np.column_stack([x, constant])
    elif model == 3:
        # Unrestricted constant
        dt = constant[1:, :]  # Match dx dimensions
        x_aug = x.copy()
    elif model == 4:
        # Restricted trend
        dt = constant[1:, :]
        x_aug = np.column_stack([x, trend])
    elif model == 5:
        # Unrestricted trend
        dt = np.column_stack([constant[1:], trend[1:]])
        x_aug = x.copy()
    else:
        raise ValueError(f"Model must be 1-5, got {model}")
    
    # Build lagged differences: Z = [DX_{t-1}, ..., DX_{t-k+1}]
    z = _lagn(dx, 1)
    for q in range(2, k):
        z = np.column_stack([z, _lagn(dx, q)])
    
    # Add deterministic terms if present
    if dt.shape[1] > 0:
        z = np.column_stack([z, dt])
    
    # Trim for lags
    z = _trimr(z, k, 0)
    dx_trimmed = _trimr(dx, k, 0)
    
    # Lagged levels: X_{t-k}
    lx = _trimr(_lagn(x_aug, k), k, 0)
    
    # Fix dimension: lx has T-k rows, dx_trimmed has T-1-k rows
    lx = lx[:-1, :]  # Remove last row to match
    
    T_eff = dx_trimmed.shape[0]
    
    # OLS residuals
    def ols_resid(y, X):
        if X.shape[1] == 0:
            return y.copy()
        try:
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            return y - X @ beta
        except:
            XtX = X.T @ X + np.eye(X.shape[1]) * 1e-10
            beta = np.linalg.solve(XtX, X.T @ y)
            return y - X @ beta
    
    r0 = ols_resid(dx_trimmed, z)
    r1 = ols_resid(lx, z)
    
    # Compute S matrices
    s00 = (r0.T @ r0) / T_eff
    s01 = (r0.T @ r1) / T_eff
    s10 = (r1.T @ r0) / T_eff
    s11 = (r1.T @ r1) / T_eff
    
    # Eigenvalue problem
    sig = s10 @ inv(s00) @ s01
    
    try:
        eigenvalues_all, _ = eig(inv(s11) @ sig)
    except:
        eigenvalues_all, _ = eig(np.linalg.pinv(s11) @ sig)
    
    eigenvalues_all = np.real(eigenvalues_all)
    eigenvalues_all = np.sort(eigenvalues_all)[::-1]
    eigenvalues_all = np.clip(eigenvalues_all, 0, 0.9999999)
    eigenvalues = eigenvalues_all[:m]
    
    # Trace statistics
    trace = np.zeros(m)
    for i in range(m):
        trace[i] = -T_eff * np.sum(np.log(1 - eigenvalues[i:]))
    
    # Lambda-max statistics
    lambda_max = -T_eff * np.log(1 - eigenvalues)
    
    # Log-likelihood
    try:
        Li = inv(cholesky(r1.T @ r1).T)
        lam_full = eigh(Li @ r1.T @ r0 @ np.linalg.pinv(r0.T @ r0) @ r0.T @ r1 @ Li.T,
                        eigvals_only=True)
        lam = np.concatenate([[0], np.sort(lam_full)[::-1]])
    except:
        lam = np.concatenate([[0], eigenvalues])
    
    lam = np.clip(lam, 0, 0.9999999)
    
    k_params = max(z.shape[1], 1)
    log_det = np.log(max(det(s00), 1e-300))
    log_likelihood = -(T_eff / 2) * (
        k_params * (1 + np.log(2 * np.pi)) + 
        log_det + 
        np.cumsum(np.log(1 - lam))
    )
    
    cv_trace = _get_cv_trace(model, m)
    
    return JohansenResult(
        eigenvalues=eigenvalues,
        lambda_max=lambda_max,
        trace=trace,
        cv_trace=cv_trace,
        cv_lambda=None,
        log_likelihood=log_likelihood,
        n_vars=m,
        n_obs=T_eff,
        model=model,
        k=k
    )


def _get_cv_trace(model: int, n_vars: int) -> np.ndarray:
    """Get critical values for trace test."""
    if model not in CV_JOHANSEN_TRACE:
        model = 2
    cv_all = CV_JOHANSEN_TRACE[model]
    n = min(n_vars, len(cv_all))
    return cv_all[:n][::-1]
