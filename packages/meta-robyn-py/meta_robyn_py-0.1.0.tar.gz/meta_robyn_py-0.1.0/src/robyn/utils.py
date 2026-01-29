
import numpy as np
import pandas as pd

def errors_scores(df, balance=[1, 1, 1], ts_validation=True):
    """
    Calculate error scores based on NRMSE, DECOMP.RSSD, and MAPE.
    """
    if len(balance) != 3:
        raise ValueError("balance must be a list of length 3")
        
    error_cols = [
        "nrmse_test" if ts_validation else "nrmse_train",
        "decomp.rssd",
        "mape"
    ]
    
    # Check if columns exist
    if not all(col in df.columns for col in error_cols):
        # Fallback if specific nrmse not found but 'nrmse' is
        if "nrmse" in df.columns and error_cols[0] not in df.columns:
            error_cols[0] = "nrmse"
    
    if not all(col in df.columns for col in error_cols):
         missing = [col for col in error_cols if col not in df.columns]
         raise ValueError(f"Missing error columns: {missing}")

    # Normalize balance
    balance = np.array(balance) / np.sum(balance)
    
    # Handle infinite values (replace with max finite)
    df_copy = df[error_cols].copy()
    for col in error_cols:
         is_inf = np.isinf(df_copy[col])
         if is_inf.any():
             max_val = df_copy.loc[~is_inf, col].max()
             df_copy.loc[is_inf, col] = max_val
             
    # Min-max normalization
    nrmse_n = min_max_norm(df_copy[error_cols[0]])
    decomp_rssd_n = min_max_norm(df_copy[error_cols[1]])
    mape_n = min_max_norm(df_copy[error_cols[2]])
    
    # Weighted score
    nrmse_w = balance[0] * nrmse_n
    decomp_rssd_w = balance[1] * decomp_rssd_n
    mape_w = balance[2] * mape_n
    
    error_score = np.sqrt(nrmse_w**2 + decomp_rssd_w**2 + mape_w**2)
    
    return error_score

def min_max_norm(x, min_val=0, max_val=1):
    x = np.array(x)
    # Handle NaN/Inf
    mask_fin = np.isfinite(x)
    if not mask_fin.any():
        return x # All nan/inf
        
    x_fin = x[mask_fin]
    a = np.min(x_fin)
    b = np.max(x_fin)
    
    if b - a != 0:
        x_norm = (max_val - min_val) * (x - a) / (b - a) + min_val
        return x_norm
    else:
        return x
