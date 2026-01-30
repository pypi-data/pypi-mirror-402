"""
Utility functions for Johansen-Fourier cointegration tests.

These functions mirror the GAUSS helper functions for exact compatibility
with the original implementation.
"""

import numpy as np
from numpy.linalg import inv, cholesky, det, eig
from scipy.linalg import eigh


def lagn(x: np.ndarray, n: int) -> np.ndarray:
    """
    Create lagged version of array x by n periods.
    
    Parameters
    ----------
    x : np.ndarray
        Input array (T x m)
    n : int
        Number of lags
        
    Returns
    -------
    np.ndarray
        Lagged array with NaN for first n rows
    """
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


def trimr(x: np.ndarray, top: int, bottom: int) -> np.ndarray:
    """
    Trim rows from top and bottom of array.
    
    Parameters
    ----------
    x : np.ndarray
        Input array
    top : int
        Number of rows to trim from top
    bottom : int
        Number of rows to trim from bottom
        
    Returns
    -------
    np.ndarray
        Trimmed array
    """
    if bottom == 0:
        return x[top:].copy()
    return x[top:-bottom].copy()


def fourier_terms(T: int, f: int, option: int) -> tuple:
    """
    Generate Fourier sine and cosine terms.
    
    Parameters
    ----------
    T : int
        Sample size
    f : int
        Frequency (single) or max frequency (cumulative)
    option : int
        1 = Single frequency
        2 = Cumulative frequencies
        
    Returns
    -------
    tuple
        (sin_terms, cos_terms) as np.ndarray
    """
    t = np.arange(1, T + 1)
    
    if option == 1:
        # Single frequency
        sink = np.sin(2 * np.pi * f * t / T).reshape(-1, 1)
        cosk = np.cos(2 * np.pi * f * t / T).reshape(-1, 1)
    else:
        # Cumulative frequencies
        sink = np.column_stack([np.sin(2 * np.pi * j * t / T) for j in range(1, f + 1)])
        cosk = np.column_stack([np.cos(2 * np.pi * j * t / T) for j in range(1, f + 1)])
    
    return sink, cosk


def eigrg2(A: np.ndarray) -> tuple:
    """
    Compute eigenvalues and eigenvectors for generalized eigenvalue problem.
    
    Matches GAUSS eigrg2 function behavior.
    
    Parameters
    ----------
    A : np.ndarray
        Square matrix
        
    Returns
    -------
    tuple
        (eigenvalues, right_eigenvectors, left_eigenvectors, condition)
    """
    eigenvalues, eigenvectors = eig(A)
    
    # Get real parts (eigenvalues should be real for symmetric problems)
    eigenvalues = np.real(eigenvalues)
    eigenvectors = np.real(eigenvectors)
    
    # Sort by eigenvalue magnitude (descending)
    idx = np.argsort(-eigenvalues)
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    return eigenvalues, eigenvectors, eigenvectors.T, np.ones(len(eigenvalues))


def ols_residuals(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """
    Compute OLS residuals: y - X*(X'X)^{-1}*X'y
    
    Parameters
    ----------
    y : np.ndarray
        Dependent variable (T x m)
    x : np.ndarray
        Regressors (T x k)
        
    Returns
    -------
    np.ndarray
        Residuals (T x m)
    """
    if x.shape[0] == 0:
        return y.copy()
    
    # Handle rank-deficient X
    try:
        # Use pseudo-inverse for numerical stability
        beta = np.linalg.lstsq(x, y, rcond=None)[0]
        residuals = y - x @ beta
    except np.linalg.LinAlgError:
        # Fallback to normal equations with regularization
        XtX = x.T @ x
        XtX += np.eye(XtX.shape[0]) * 1e-10  # Small regularization
        beta = inv(XtX) @ (x.T @ y)
        residuals = y - x @ beta
    
    return residuals


def build_lag_matrix(dx: np.ndarray, k: int) -> np.ndarray:
    """
    Build matrix of lagged differences for VECM.
    
    Z = [ΔX_{t-1}, ΔX_{t-2}, ..., ΔX_{t-k+1}]
    
    Parameters
    ----------
    dx : np.ndarray
        First differences (T x m)
    k : int
        Number of VAR lags
        
    Returns
    -------
    np.ndarray
        Lag matrix (T x (k-1)*m)
    """
    T, m = dx.shape
    
    if k <= 1:
        return np.zeros((T, 0))
    
    z = lagn(dx, 1)
    for q in range(2, k):
        z = np.column_stack([z, lagn(dx, q)])
    
    return z


def compute_sij_matrices(r0: np.ndarray, r1: np.ndarray) -> tuple:
    """
    Compute S00, S01, S10, S11 matrices for Johansen procedure.
    
    Sij = (1/T) * Σ Rit * Rjt'
    
    Parameters
    ----------
    r0 : np.ndarray
        Residuals from ΔX on Z (T x m)
    r1 : np.ndarray
        Residuals from X_{t-k} on Z (T x n)
        
    Returns
    -------
    tuple
        (S00, S01, S10, S11)
    """
    T = r0.shape[0]
    
    s00 = (r0.T @ r0) / T
    s01 = (r0.T @ r1) / T
    s10 = (r1.T @ r0) / T
    s11 = (r1.T @ r1) / T
    
    return s00, s01, s10, s11


def compute_trace_stat(eigenvalues: np.ndarray, T: int, r: int) -> np.ndarray:
    """
    Compute trace statistics for each rank.
    
    LR_trace(r) = -T * Σ ln(1 - λ_i) for i = r+1 to p
    
    Parameters
    ----------
    eigenvalues : np.ndarray
        Ordered eigenvalues (descending)
    T : int
        Sample size
    r : int
        Number of ranks to compute (usually p)
        
    Returns
    -------
    np.ndarray
        Trace statistics for ranks 0, 1, ..., r-1
    """
    p = len(eigenvalues)
    trace_stats = np.zeros(r)
    
    for i in range(r):
        # Sum from i to p-1
        trace_stats[i] = -T * np.sum(np.log(1 - eigenvalues[i:]))
    
    return trace_stats


def compute_lambda_max_stat(eigenvalues: np.ndarray, T: int) -> np.ndarray:
    """
    Compute lambda-max statistics.
    
    λ_max(r) = -T * ln(1 - λ_{r+1})
    
    Parameters
    ----------
    eigenvalues : np.ndarray
        Ordered eigenvalues (descending)
    T : int
        Sample size
        
    Returns
    -------
    np.ndarray
        Lambda-max statistics
    """
    return -T * np.log(1 - eigenvalues)


def compute_log_likelihood(r0: np.ndarray, eigenvalues: np.ndarray, k: int) -> np.ndarray:
    """
    Compute log-likelihood for each rank.
    
    Parameters
    ----------
    r0 : np.ndarray
        Residuals (T x m)
    eigenvalues : np.ndarray
        Ordered eigenvalues
    k : int
        Number of parameters
        
    Returns
    -------
    np.ndarray
        Log-likelihood for each rank
    """
    T = r0.shape[0]
    m = r0.shape[1] if r0.ndim > 1 else 1
    
    # S00 = r0'r0/T
    s00 = (r0.T @ r0) / T
    
    # Cumulative sum of log(1 - λ)
    lam = np.concatenate([[0], eigenvalues])
    cum_ln = np.cumsum(np.log(1 - lam))
    
    # Log-likelihood
    log_det = np.log(det(s00)) if det(s00) > 0 else -np.inf
    logL = -(T / 2) * (m * (1 + np.log(2 * np.pi)) + log_det + cum_ln)
    
    return logL


def seqa(start: float, step: float, n: int) -> np.ndarray:
    """
    Create sequence array (equivalent to GAUSS seqa).
    
    Parameters
    ----------
    start : float
        Starting value
    step : float
        Step size
    n : int
        Number of elements
        
    Returns
    -------
    np.ndarray
        Sequence array
    """
    return np.arange(start, start + step * n, step)[:n]
