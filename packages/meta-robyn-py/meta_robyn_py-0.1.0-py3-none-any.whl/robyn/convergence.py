
import numpy as np
import pandas as pd
from typing import List, Dict, Union

def robyn_converge(output_models: Dict, n_cuts: int = 20, 
                   sd_qtref: int = 3, med_lowb: int = 2, 
                   nrmse_win: List[float] = [0, 0.998], **kwargs):
    """
    Check Models Convergence.
    Calculates convergence status.
    Plots are skipped for now (matplotlib dependency optional).
    """
    
    # Check
    if n_cuts <= min(sd_qtref, med_lowb) + 1:
        raise ValueError("n_cuts must be > min(sd_qtref, med_lowb) + 1")
    
    # Gather trials
    # OutputModels is a dict with keys 'trial1', 'trial2' etc.
    trials = [k for k in output_models.keys() if k.startswith("trial")]
    
    dfs = []
    for t in trials:
        df_trial = output_models[t]['resultCollect']['resultHypParam'].copy()
        df_trial['trial'] = int(t.replace("trial", ""))
        dfs.append(df_trial)
        
    df = pd.concat(dfs, ignore_index=True)
    calibrated = (df['mape'].sum() > 0)
    
    # Prepare data for calculations
    # Gather nrmse, decomp.rssd, mape
    if 'mape' not in df.columns:
         cols = ['nrmse', 'decomp.rssd']
    else:
         cols = ['nrmse', 'decomp.rssd', 'mape']
         
    dt_objfunc_cvg = df.melt(id_vars=['trial', 'iterNG'], 
                             value_vars=cols, 
                             var_name='error_type', value_name='value')
    
    # Filter valid
    dt_objfunc_cvg = dt_objfunc_cvg[ (dt_objfunc_cvg['value'] > 0) & np.isfinite(dt_objfunc_cvg['value']) ].copy()
    dt_objfunc_cvg['error_type'] = dt_objfunc_cvg['error_type'].str.upper()
    
    # Arrange and group
    # We want cumulative iteration count across trials to sort?
    # R: arrange(.data$trial, .data$ElapsedAccum) - we don't have ElapsedAccum?
    # We have iterNG (iteration number).
    # Assuming standard order.
    
    dt_objfunc_cvg = dt_objfunc_cvg.sort_values(['trial', 'iterNG'])
    
    # Add global iteration index per error_type
    dt_objfunc_cvg['iter'] = dt_objfunc_cvg.groupby(['error_type']).cumcount() + 1
    
    # Cuts
    # pd.cut
    max_iter = dt_objfunc_cvg['iter'].max()
    # R breaks: seq(0, max, length.out=n_cuts+1)
    # labels: round(seq(max/n_cuts, max, length.out=n_cuts))
    breaks = np.linspace(0, max_iter, n_cuts + 1)
    labels = np.round(np.linspace(max_iter / n_cuts, max_iter, n_cuts)).astype(int)
    
    dt_objfunc_cvg['cuts'] = pd.cut(dt_objfunc_cvg['iter'], bins=breaks, labels=labels, include_lowest=True, ordered=True)
    
    # Calculate stats
    # Group by error_type, cuts
    summary = dt_objfunc_cvg.groupby(['error_type', 'cuts'], observed=True)['value'].agg(['median', 'std', 'count']).reset_index()
    
    # Sort first
    summary = summary.sort_values(['error_type', 'cuts'])
    
    # Function to apply per error_type
    def calc_stats(group):
        # med_var_P
        median_lag = group['median'].shift(1)
        group['med_var_P'] = np.abs(np.round(100 * (group['median'] - median_lag) / group['median'], 2))
        
        # Fixed stats based on first/last
        first_med = np.abs(group['median'].iloc[0])
        # first 3 quantiles for mean
        first_med_avg = np.abs(group['median'].iloc[:sd_qtref].mean())
        last_med = np.abs(group['median'].iloc[-1])
        
        first_sd = group['std'].iloc[0]
        first_sd_avg = group['std'].iloc[:sd_qtref].mean()
        last_sd = group['std'].iloc[-1]
        
        group['first_med'] = first_med
        group['first_med_avg'] = first_med_avg
        group['last_med'] = last_med
        group['first_sd'] = first_sd
        group['first_sd_avg'] = first_sd_avg
        group['last_sd'] = last_sd
        
        # Flags
        # Criteria 2: Median
        med_thres = np.abs(first_med - med_lowb * first_sd_avg)
        group['med_thres'] = med_thres
        group['flag_med'] = np.abs(group['median']) < med_thres
        
        # Criteria 1: SD
        group['flag_sd'] = group['std'] < first_sd_avg
        
        return group

    errors = summary.groupby('error_type').apply(calc_stats).reset_index(drop=True)
    
    # Generate messages
    conv_msg = []
    
    for error_type in errors['error_type'].unique():
        last_qt = errors[errors['error_type'] == error_type].iloc[-1]
        
        flag_sd = last_qt['flag_sd']
        flag_med = last_qt['flag_med']
        
        did_converge = "" if (flag_sd and flag_med) else "NOT "
        
        symb_sd = "<=" if flag_sd else ">"
        symb_med = "<=" if flag_med else ">"
        
        msg = (f"{error_type} {did_converge}converged: "
               f"sd@qt.{n_cuts} {last_qt['last_sd']:.2g} {symb_sd} {last_qt['first_sd_avg']:.2g} & "
               f"|med@qt.{n_cuts}| {last_qt['last_med']:.2g} {symb_med} {last_qt['med_thres']:.2g}")
        
        conv_msg.append(msg)
        
    print("\n".join(["- " + m for m in conv_msg]))
    
    return {
        'errors': errors,
        'conv_msg': conv_msg
    }

