"""
Johansen-Fourier cointegration test implementation.

This module implements the Johansen-type cointegration test with a Fourier 
function to capture unknown structural breaks.

Reference:
    Pascalau, R., Lee, J., Nazlioglu, S., Lu, Y. O. (2022).
    "Johansen-type Cointegration Tests with a Fourier Function".
    Journal of Time Series Analysis 43(5): 828-852.
    DOI: 10.1111/jtsa.12640
"""

import numpy as np
from numpy.linalg import inv, det, eig, cholesky
from scipy.linalg import eigh
from dataclasses import dataclass
from typing import Optional, Tuple

from .utils import fourier_terms
from .critical_values import (
    CV_FOURIER_TRACE_SINGLE, CV_FOURIER_TRACE_CUMULATIVE,
    CV_FOURIER_LAMBDA_SINGLE, CV_FOURIER_LAMBDA_CUMULATIVE,
    get_fourier_trace_cv, get_fourier_lambda_cv
)


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
class JohansenFourierResult:
    """
    Container for Johansen-Fourier cointegration test results.
    """
    eigenvalues: np.ndarray
    lambda_max: np.ndarray
    trace: np.ndarray
    cv_trace: np.ndarray
    cv_lambda: np.ndarray
    log_likelihood: np.ndarray
    n_vars: int
    n_obs: int
    model: int
    k: int
    frequency: int
    option: int
    
    def summary(self) -> str:
        """Generate publication-ready summary table."""
        lines = []
        lines.append("=" * 75)
        lines.append("           Johansen-Fourier Cointegration Test Results")
        lines.append("=" * 75)
        lines.append(f" # Variables : {self.n_vars}")
        lines.append(f" Model       : {self._model_name()}")
        lines.append(f" Frequency   : {self.frequency} ({'Single' if self.option == 1 else 'Cumulative'})")
        lines.append(f" VAR Lags    : {self.k}")
        lines.append(f" VECM Lags   : {self.k - 1}")
        lines.append(f" Observations: {self.n_obs}")
        lines.append("-" * 75)
        lines.append(f"{'Rank':>6}  {'Fourier':>12}  {'Fourier':>12}  "
                     f"{'CV(5%)':>10}  {'CV(5%)':>10}  {'Log-Lik':>12}")
        lines.append(f"{'':>6}  {'Lambda':>12}  {'Trace':>12}  "
                     f"{'Lambda':>10}  {'Trace':>10}  {'':>12}")
        lines.append("-" * 75)
        
        # Rank 0 row
        lines.append(f"{0:>6}  {'':>12}  {'':>12}  "
                     f"{'':>10}  {'':>10}  {self.log_likelihood[0]:>12.3f}")
        
        for i in range(len(self.eigenvalues)):
            lm = self.lambda_max[i]
            tr = self.trace[i]
            cv_lm = self.cv_lambda[i] if i < len(self.cv_lambda) else np.nan
            cv_tr = self.cv_trace[i] if i < len(self.cv_trace) else np.nan
            ll = self.log_likelihood[i + 1] if i + 1 < len(self.log_likelihood) else np.nan
            
            sig_tr = "*" if tr > cv_tr else ""
            sig_lm = "*" if lm > cv_lm else ""
            
            lines.append(f"{i+1:>6}  {lm:>11.3f}{sig_lm:1}  {tr:>11.3f}{sig_tr:1}  "
                         f"{cv_lm:>10.3f}  {cv_tr:>10.3f}  {ll:>12.3f}")
        
        lines.append("=" * 75)
        lines.append("Note: * indicates rejection of null at 5% level")
        
        return "\n".join(lines)
    
    def _model_name(self) -> str:
        names = {
            1: "Constant (Unrestricted)",
            2: "Trend (Unrestricted)",
            3: "Restricted Constant (RC)",
            4: "Restricted Trend (RT)"
        }
        return names.get(self.model, f"Model {self.model}")
    
    def get_cointegration_rank(self, alpha: float = 0.05) -> int:
        """Determine cointegration rank based on trace test."""
        for i in range(len(self.trace)):
            if self.trace[i] <= self.cv_trace[i]:
                return i
        return len(self.trace)
    
    def __repr__(self) -> str:
        return self.summary()


def johansen_fourier(x: np.ndarray, model: int = 3, k: int = 2,
                     f: int = 1, option: int = 1) -> JohansenFourierResult:
    """
    Johansen-Fourier cointegration test with Fourier function.
    
    Parameters
    ----------
    x : np.ndarray
        T x m matrix of endogenous variables.
    model : int, default=3
        1 = Constant (unrestricted), 2 = Trend (unrestricted),
        3 = Restricted Constant (RC), 4 = Restricted Trend (RT)
    k : int, default=2
        Number of lags for VAR model.
    f : int, default=1
        Fourier frequency (1-5).
    option : int, default=1
        1 = Single frequency, 2 = Cumulative frequency
        
    Returns
    -------
    JohansenFourierResult
        Object containing test statistics and critical values.
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
    
    # Fourier terms (T rows)
    sink, cosk = fourier_terms(T, f, option)
    
    # Model-specific setup
    if model == 1:
        # Unrestricted constant
        dt = np.column_stack([constant, sink, cosk])
        x_aug = x.copy()
    elif model == 2:
        # Unrestricted trend
        dt = np.column_stack([constant, trend, sink, cosk])
        x_aug = x.copy()
    elif model == 3:
        # Restricted constant (RC)
        dt = np.column_stack([sink, cosk])
        x_aug = np.column_stack([x, constant])
    elif model == 4:
        # Restricted trend (RT)
        dt = np.column_stack([constant, sink, cosk])
        x_aug = np.column_stack([x, trend])
    else:
        raise ValueError(f"Model must be 1-4, got {model}")
    
    # Build lagged differences: Z = [ΔX_{t-1}, ..., ΔX_{t-k+1}]
    z = _lagn(dx, 1)
    for q in range(2, k):
        z = np.column_stack([z, _lagn(dx, q)])
    
    # Add deterministic terms (trim dt to match dx length: T-1 rows)
    # In GAUSS, dt[k+1:T] is used, but since dx already has T-1 rows,
    # we need to align properly
    z = np.column_stack([z, dt[1:, :]])  # dt[1:] has T-1 rows like dx
    
    # Trim for lags: remove first k rows where lags are NaN
    z = _trimr(z, k, 0)
    dx_trimmed = _trimr(dx, k, 0)
    
    # Lagged levels: X_{t-k}
    # x_aug has T rows, lag by k gives T rows with first k being NaN
    # Then trim k from top to get T-k rows
    lx = _trimr(_lagn(x_aug, k), k, 0)
    
    # At this point:
    # dx_trimmed has T-1-k rows
    # z has T-1-k rows  
    # lx has T-k rows (one more than needed!)
    
    # Fix: we need lx to also have T-1-k rows
    # The lagged levels should be trimmed to match dx_trimmed
    lx = lx[:-1, :]  # Remove last row to match dx_trimmed length
    
    T_eff = dx_trimmed.shape[0]
    
    # OLS residuals: r = y - Z*(Z'Z)^{-1}*Z'y
    def ols_resid(y, X):
        try:
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            return y - X @ beta
        except np.linalg.LinAlgError:
            # Fallback with regularization
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
    
    # Eigenvalue problem: |λS11 - S10*S00^{-1}*S01| = 0
    sig = s10 @ inv(s00) @ s01
    
    try:
        eigenvalues_all, eigenvectors = eig(inv(s11) @ sig)
    except np.linalg.LinAlgError:
        eigenvalues_all, eigenvectors = eig(np.linalg.pinv(s11) @ sig)
    
    # Get real parts and sort descending
    eigenvalues_all = np.real(eigenvalues_all)
    idx = np.argsort(-eigenvalues_all)
    eigenvalues_all = eigenvalues_all[idx]
    
    # Clip to valid range
    eigenvalues_all = np.clip(eigenvalues_all, 0, 0.9999999)
    
    # For restricted models, use only first m eigenvalues
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
        if model >= 3:
            lam_full = eigh(Li @ r1.T @ r0 @ np.linalg.pinv(r0.T @ r0) @ r0.T @ r1 @ Li.T,
                            eigvals_only=True)
            lam = np.concatenate([[0], np.sort(lam_full)[::-1][:-1]])
        else:
            lam_full = eigh(Li @ r1.T @ r0 @ np.linalg.pinv(r0.T @ r0) @ r0.T @ r1 @ Li.T,
                            eigvals_only=True)
            lam = np.concatenate([[0], np.sort(lam_full)[::-1]])
    except np.linalg.LinAlgError:
        lam = np.concatenate([[0], eigenvalues])
    
    lam = np.clip(lam, 0, 0.9999999)
    
    k_params = z.shape[1] if z.shape[1] > 0 else 1
    log_det = np.log(max(det(r0.T @ r0 / T_eff), 1e-300))
    log_likelihood = -(T_eff / 2) * (
        k_params * (1 + np.log(2 * np.pi)) + 
        log_det + 
        np.cumsum(np.log(1 - lam))
    )
    
    # Critical values
    cv_trace = _get_cv_fourier_trace(model, f, m, option)
    cv_lambda = _get_cv_fourier_lambda(model, f, m, option)
    
    return JohansenFourierResult(
        eigenvalues=eigenvalues,
        lambda_max=lambda_max,
        trace=trace,
        cv_trace=cv_trace,
        cv_lambda=cv_lambda,
        log_likelihood=log_likelihood,
        n_vars=m,
        n_obs=T_eff,
        model=model,
        k=k,
        frequency=f,
        option=option
    )


def _get_cv_fourier_trace(model: int, freq: int, n_vars: int, option: int) -> np.ndarray:
    """Get critical values for Fourier trace test."""
    cv_table = CV_FOURIER_TRACE_SINGLE if option == 1 else CV_FOURIER_TRACE_CUMULATIVE
    
    if model not in cv_table:
        model = 3
    
    freq_idx = min(freq, 5) - 1
    n = min(n_vars, 5)
    
    cv_all = cv_table[model][freq_idx, :n]
    return cv_all[::-1]


def _get_cv_fourier_lambda(model: int, freq: int, n_vars: int, option: int) -> np.ndarray:
    """Get critical values for Fourier lambda-max test."""
    cv_table = CV_FOURIER_LAMBDA_SINGLE if option == 1 else CV_FOURIER_LAMBDA_CUMULATIVE
    
    if model not in cv_table:
        model = 3
    
    freq_idx = min(freq, 5) - 1
    n = min(n_vars, 5)
    
    cv_all = cv_table[model][freq_idx, :n]
    return cv_all[::-1]


def sc_fourier(r: int, y: np.ndarray, model: int, k_max: int, 
               f_max: int, option: int) -> Tuple:
    """
    SC-Fourier procedure for optimal frequency and lag selection.
    """
    n = y.shape[1]
    keep_mat = []
    
    for freq in range(1, f_max + 1):
        for lag in range(1, k_max + 1):
            try:
                result = johansen_fourier(y, model, lag, freq, option)
                if r < len(result.trace):
                    tr = result.trace[r]
                    sbc = _compute_sbc(result, r, n, lag)
                    keep_mat.append([freq, lag, tr, sbc])
            except Exception:
                continue
    
    if len(keep_mat) == 0:
        # Return defaults if all failed
        return 0.0, np.inf, 1, 20.0, 1, np.array([[1, 1, 0, np.inf]])
    
    keep_mat = np.array(keep_mat)
    
    min_idx = np.argmin(keep_mat[:, 3])
    
    f_hat = int(keep_mat[min_idx, 0])
    p_hat = int(keep_mat[min_idx, 1])
    tr_fp = keep_mat[min_idx, 2]
    sbc_fp = keep_mat[min_idx, 3]
    
    cv = get_fourier_trace_cv(model, f_hat, max(n - r, 1), option)
    
    return tr_fp, sbc_fp, p_hat, cv, f_hat, keep_mat


def _compute_sbc(result: JohansenFourierResult, r: int, n: int, k: int) -> float:
    """Compute Schwarz Bayesian Criterion."""
    T = result.n_obs
    
    if r + 1 < len(result.log_likelihood):
        logL = result.log_likelihood[r + 1]
    else:
        logL = result.log_likelihood[-1]
    
    sbc = -2 * logL + (n + r + 2 + (n ** 2) * k) * np.log(T)
    
    return sbc
