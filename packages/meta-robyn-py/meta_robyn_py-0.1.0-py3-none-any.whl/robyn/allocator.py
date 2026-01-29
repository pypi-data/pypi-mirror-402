
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from robyn.response import robyn_response, fx_objective
from robyn.checks import check_allocator

def robyn_allocator(input_collect, output_collect, select_model, scenario="max_response",
                    total_budget=None, channel_constr_low=None, channel_constr_up=None,
                    channel_constr_multiplier=3, date_range="all", 
                    optim_algo="SLSQP", max_eval=100000, constr_mode="eq",
                    quiet=False, **kwargs):
    
    # 1. Prep
    dt_hyppar = output_collect['resultHypParam']
    dt_coef = output_collect['xDecompAgg']
    
    # helper to get scalar
    def get_scalar(df, col):
        return df[col].iloc[0] if not df.empty else 0
        
    paid_media_selected = input_collect['paid_media_selected']
    media_order = sorted(paid_media_selected) # Sort or keep order? R sorts?
    # R: media_order <- order(paid_media_selected) (indices)
    
    # 2. Checks
    # check_allocator(output_collect, select_model, ...)
    
    # 3. Get Model Params
    row_hyp = dt_hyppar[dt_hyppar['solID'] == select_model]
    
    coefs = {}
    alphas = {}
    inflexions = {}
    
    for media in paid_media_selected:
        # Get coef
        row_c = dt_coef[(dt_coef['solID'] == select_model) & (dt_coef['rn'] == media)]
        coefs[media] = get_scalar(row_c, 'coef')
        
        # Get alpha/inflexion
        # Need to handle adstock logic to find suffix?
        # R code assumes names like media + "_alphas"
        alphas[media] = get_scalar(row_hyp, f"{media}_alphas")
        inflexions[media] = get_scalar(row_hyp, f"{media}_inflexion") # inflexion vs gammas
        # Note: gammas are converted to inflexion in transformation usually? 
        # In transformation.py, we save inflexion in dt_modSaturated?
        # R saves it in resultHypParam?
        # Let's check transformation.py: inflexion_collect is returned.
        # But resultHypParam comes from model.R hyper_collector.
        # Need to ensure inflexion is in resultHypParam or calculated.
        # R's model.R calculates inflexion and saves it.
        
    # 4. Get Historical Spend/Carryover
    hist_carryover = {}
    init_spend_unit = []
    
    for media in paid_media_selected:
        resp = robyn_response(
             input_collect=input_collect,
             output_collect=output_collect,
             select_model=select_model,
             metric_name=media,
             date_range=date_range,
             quiet=True
        )
        # R uses window_loc
        # Carryover is input_carryover
        # We need mean carryover for the period
        hist_carryover[media] = np.mean(resp['input_carryover']) # This is full range or sliced by date_range?
        # robyn_response returns sliced if date_range is set?
        # Actually robyn_response returns dict with input_carryover.
        # If date_range='all', it is full.
        # We need to slice it using window_loc if we want optimization over window?
        # R: hist_carryover[[i]] <- hist_carryover_temp (which is resp$input_carryover[window_loc])
        
        # NOTE: robyn_response implementation should handle date_range slicing for return values 'mean_input_carryover'
        hist_carryover[media] = resp['mean_input_carryover']
        init_spend_unit.append(resp['mean_input_immediate']) # initial spend unit
        
    init_spend_unit = np.array(init_spend_unit)
    
    if total_budget is None:
        total_budget = np.sum(init_spend_unit)
        
    # 5. Optimization
    
    # Constraints
    # Lower/Upper bounds
    if channel_constr_low is None:
         channel_constr_low = 0.5 if scenario == "max_response" else 0.1
    if channel_constr_up is None:
         channel_constr_up = 2.0 if scenario == "max_response" else 10.0
         
    if np.isscalar(channel_constr_low):
        channel_constr_low = np.full(len(paid_media_selected), channel_constr_low)
    if np.isscalar(channel_constr_up):
        channel_constr_up = np.full(len(paid_media_selected), channel_constr_up)
        
    lb = init_spend_unit * channel_constr_low
    ub = init_spend_unit * channel_constr_up
    bounds = list(zip(lb, ub))
    
    # Objective Function
    def objective_func(x):
        # Maximize response -> Minimize negative response
        res = 0
        for i, media in enumerate(paid_media_selected):
             # fx_objective return sum or scalar? 
             # We want TOTAL response.
             val = fx_objective(
                 x=x[i],
                 coeff=coefs[media],
                 alpha=alphas[media],
                 inflexion=inflexions[media],
                 x_hist_carryover=hist_carryover[media],
                 get_sum=False # scalar input, scalar output
             )
             res += val
        return -res
        
    # Constraints for Total Budget
    constraints = []
    if constr_mode == "eq":
        constraints.append({'type': 'eq', 'fun': lambda x: np.sum(x) - total_budget})
    else:
        constraints.append({'type': 'ineq', 'fun': lambda x: total_budget - np.sum(x)}) # sum(x) <= total_budget
        
    # Initial guess
    x0 = init_spend_unit
    
    # Run Optimization
    res = minimize(objective_func, x0, method=optim_algo, bounds=bounds, constraints=constraints, 
                   options={'maxiter': max_eval, 'disp': not quiet})
    
    # 6. Results
    optm_spend_unit = res.x
    optm_response_unit = -res.fun # Actually we need to recalc per channel
    
    # Collect details
    results = []
    for i, media in enumerate(paid_media_selected):
        resp_opt = fx_objective(
             x=optm_spend_unit[i],
             coeff=coefs[media],
             alpha=alphas[media],
             inflexion=inflexions[media],
             x_hist_carryover=hist_carryover[media],
             get_sum=False
        )
        results.append({
            'channel': media,
            'init_spend': init_spend_unit[i],
            'optm_spend': optm_spend_unit[i],
            'optm_response': resp_opt
            # Add init response too
        })
        
    dt_optim_out = pd.DataFrame(results)
    
    return {
        'dt_optimOut': dt_optim_out,
        'solution': res,
        'scenario': scenario
    }
