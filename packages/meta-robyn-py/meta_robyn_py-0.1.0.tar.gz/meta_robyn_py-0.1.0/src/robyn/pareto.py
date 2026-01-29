
import pandas as pd
import numpy as np
import warnings
from robyn.utils import errors_scores
from robyn.response import robyn_response

def robyn_pareto(input_collect, output_models, pareto_fronts="auto", min_candidates=100, 
                 calibration_constraint=0.1, quiet=False, calibrated=False):
    
    hyper_fixed = output_models.get('hyper_fixed', False)
    # Collect results from all trials
    # output_models should be a dict with keys like 'trial1', 'trial2', etc... or just the list of output objects
    
    out_models = [v for k, v in output_models.items() if "resultCollect" in v]
    
    # helper to bind rows
    def bind_rows(list_of_dfs):
        if not list_of_dfs:
            return pd.DataFrame()
        return pd.concat(list_of_dfs, ignore_index=True)

    result_hyp_param = bind_rows([
        x['resultCollect']['resultHypParam'].assign(trial=x['trial']) 
        for x in out_models
    ])
    
    x_decomp_agg = bind_rows([
        x['resultCollect']['xDecompAgg'].assign(trial=x['trial'])
        for x in out_models
    ])
    
    if calibrated:
        # TODO: Implement calibration handling
        pass
        
    # Add iterations count
    # output_models['cores'] might be needed
    cores = output_models.get('cores', 1)
    # R: iterations = (.data$iterNG - 1) * OutputModels$cores + .data$iterPar
    if 'iterNG' in result_hyp_param.columns and 'iterPar' in result_hyp_param.columns:
        result_hyp_param['iterations'] = (result_hyp_param['iterNG'] - 1) * cores + result_hyp_param['iterPar']
        
    # Handle bootstrap if present (omitted for now)
    
    # Pareto Logic
    if not hyper_fixed:
        # Filter by calibration constraint (simple version: top 10% mape?)
        # R: mape <= quantile(mape, calibration_constraint)
        # But wait, logic:
        # mape_qt10 = mape <= quantile(0.1) & nrmse <= quantile(0.9) & rssd <= quantile(0.9)
        
        subset = result_hyp_param
        
        # Check if columns exist
        if all(c in subset.columns for c in ['mape', 'nrmse', 'decomp.rssd']):
             mape_q = subset['mape'].quantile(calibration_constraint)
             nrmse_q = subset['nrmse'].quantile(0.90)
             rssd_q = subset['decomp.rssd'].quantile(0.90)
             
             subset['mape_qt10'] = (subset['mape'] <= mape_q) & \
                                   (subset['nrmse'] <= nrmse_q) & \
                                   (subset['decomp.rssd'] <= rssd_q)
        else:
             subset['mape_qt10'] = True # Fallback
             
        # Calculate Pareto fronts for those passing constraint
        pareto_candidates = subset[subset['mape_qt10']].copy()
        
        if not pareto_candidates.empty:
            # We want to minimize nrmse and decomp.rssd
            objectives = pareto_candidates[['nrmse', 'decomp.rssd']].values
            fronts = pareto_front(objectives[:, 0], objectives[:, 1]) # Returns front index (1, 2, 3...)
            pareto_candidates['robynPareto'] = fronts
            
            # Join back to result_hyp_param
            # We need to join on specific columns or ID. solID is unique?
            # solID should be unique across trials if properly generated
            result_hyp_param = pd.merge(result_hyp_param, pareto_candidates[['solID', 'robynPareto']], 
                                        on='solID', how='left')
        else:
             result_hyp_param['robynPareto'] = np.nan
             
    else:
        result_hyp_param['mape_qt10'] = True
        result_hyp_param['robynPareto'] = 1
        
    # Calculate error scores
    # R: resultHypParam$error_score <- errors_scores(...)
    # ts_validation = output_models.get('ts_validation', True)
    # We apply row-wise? errors_scores expects df
    result_hyp_param['error_score'] = errors_scores(result_hyp_param, ts_validation=output_models.get('ts_validation', True))
    
    # Join robynPareto to xDecompAgg
    x_decomp_agg = pd.merge(x_decomp_agg, result_hyp_param[['solID', 'robynPareto']], on='solID', how='left')
    
    # Select pareto fronts
    if hyper_fixed:
        pareto_fronts = 1
        
    if pareto_fronts == "auto":
        # Auto selection logic
        freq = result_hyp_param['robynPareto'].value_counts().sort_index()
        cum_freq = freq.cumsum()
        # Find first front where cum >= min_candidates
        valid_fronts = cum_freq[cum_freq >= min_candidates]
        if not valid_fronts.empty:
            pareto_fronts = int(valid_fronts.index[0])
        else:
            pareto_fronts = int(cum_freq.index[-1]) if not cum_freq.empty else 1
            
        if not quiet:
             print(f">> Automatically selected {pareto_fronts} Pareto-fronts to contain at least {min_candidates} models")
             
    pareto_fronts_vec = list(range(1, int(pareto_fronts) + 1))
    
    # Filter for response calculation
    result_hyp_param_par = result_hyp_param[result_hyp_param['robynPareto'].isin(pareto_fronts_vec)]
    x_decomp_agg_media_par = x_decomp_agg[
        (x_decomp_agg['robynPareto'].isin(pareto_fronts_vec)) & 
        (x_decomp_agg['rn'].isin(input_collect['all_media']))
    ]
    
    # Calculate Response Curves
    if not quiet:
        print(f">>> Calculating response curves for all models' media variables ({len(x_decomp_agg_media_par)})...")
        
    dt_resp_list = []
    
    # Iterate unique solID and media
    # This might be slow if loop. R uses parallel.
    # We can simple loop for now.
    
    for _, row in x_decomp_agg_media_par.iterrows():
        sol_id = row['solID']
        media_name = row['rn']
        
        # Call robyn_response
        resp = robyn_response(
            input_collect=input_collect,
            output_collect=output_models,
            select_model=sol_id,
            metric_name=media_name,
            date_range="all",
            dt_hyppar=result_hyp_param_par,
            dt_coef=x_decomp_agg_media_par,
            quiet=True
        )
        
        # Collect results
        dt_resp_list.append({
            'mean_response': resp['mean_response'],
            'mean_spend_adstocked': resp['mean_input_immediate'] + resp['mean_input_carryover'],
            'mean_carryover': resp['mean_input_carryover'],
            'rn': media_name,
            'solID': sol_id,
            'mean_spend': resp['mean_input_immediate'] # check if mean_spend is immediate or total?
            # R: mean_spend_adstocked = mean_input_immediate + mean_input_carryover
        })
        
    dt_resp = pd.DataFrame(dt_resp_list)
    
    # Join back to xDecompAgg
    if not dt_resp.empty:
        x_decomp_agg = pd.merge(x_decomp_agg, dt_resp, on=['solID', 'rn'], how='left')
        
    # Final Output preparation
    # Return lists similar to R's OutputCollect
    
    output_collect = output_models.copy()
    output_collect['resultHypParam'] = result_hyp_param
    output_collect['xDecompAgg'] = x_decomp_agg
    output_collect['pareto_fronts'] = pareto_fronts
    output_collect['mediaVecCollect'] = None # Populate if we want full vector data (memory heavy)
    
    return output_collect

def pareto_front(xi, yi, pareto_fronts=float('inf'), sort=False):
    """
    Calculate Pareto fronts for two objectives (minimization).
    Returns an array of integers indicating the front number (1-based).
    """
    n = len(xi)
    if n == 0:
        return np.array([])
        
    # Prepare data: [nrmse, rssd, original_index]
    data = np.vstack((xi, yi, np.arange(n))).T
    
    # Sort by first objective
    # This optimization helps for 2D pareto
    # But for standard NSGA-II non-dominated sort:
    
    # We'll use a simple iterative peeling method since 2D is easy?
    # Actually, let's implement the generic one or simple one.
    
    ranks = np.zeros(n, dtype=int)
    current_front = 1
    
    remaining_indices = np.arange(n)
    
    while len(remaining_indices) > 0 and current_front <= pareto_fronts:
        # Find non-dominated points in remaining
        subset = data[remaining_indices]
        is_dominated = np.zeros(len(subset), dtype=bool)
        
        # Simple nested loop for N points (boring but works)
        # Or sorting trick for 2D:
        # Sort by x ascending. Then iterate and keep track of min y so far?
        # Points with y < min_y correspond to non-dominated?
        
        # For minimization of x and y:
        # Sort by x ascending.
        # The first point is definitely non-dominated.
        # Then, a point is non-dominated if its y is smaller than the y of all previous points effectively? 
        # Actually it must be smaller than the minimum y seen so far?
        
        # Sort subset by x (primary) and y (secondary)
        # Using lexical sort
        # indices in subset array
        sorted_idx = np.lexsort((subset[:, 1], subset[:, 0])) 
        subset_sorted = subset[sorted_idx]
        
        front_subset_indices = []
        min_y = float('inf')
        
        for i in range(len(subset_sorted)):
            # If current point's y is smaller than min_y, it's non-dominated
            # (since x is already >= previous x's)
            curr_y = subset_sorted[i, 1]
            if curr_y < min_y:
                front_subset_indices.append(sorted_idx[i])
                min_y = curr_y
            # Note: strict inequality for strong dominance?
            # R's rPref uses strict?
            # pareto_front in R checks for pareto optimal.
            # Usually < min_y for strict.
            
        # These are indices within 'remaining_indices'
        # Get actual original indices
        dominated_in_subset = np.ones(len(subset), dtype=bool)
        dominated_in_subset[front_subset_indices] = False
        
        # Assign rank
        # subset[front_subset_indices, 2] contains original indices
        original_indices_front = subset[front_subset_indices, 2].astype(int)
        ranks[original_indices_front] = current_front
        
        # Remove from remaining
        remaining_indices = remaining_indices[dominated_in_subset] # Keep only dominated
        
        current_front += 1
        
    return ranks

