
import pandas as pd
import numpy as np
import warnings
from robyn.checks import check_metric_type, check_metric_dates, check_metric_value
from robyn.transformation import transform_adstock, saturation_hill, fx_objective

def robyn_response(input_collect=None, output_collect=None, json_file=None,
                   select_build=None, select_model=None, metric_name=None,
                   metric_value=None, date_range=None, dt_hyppar=None,
                   dt_coef=None, quiet=False, **kwargs):
    """
    Returns the response for a given spend level of a given metric from a selected model result.
    """
    
    # 1. Handle JSON / Input/Output prep
    if json_file is not None:
        raise NotImplementedError("JSON import not yet implemented. Please provide input_collect and output_collect.")
        
    if dt_hyppar is None:
        dt_hyppar = output_collect.get('resultHypParam')
    if dt_coef is None:
        dt_coef = output_collect.get('xDecompAgg')
        
    if any(x is None for x in [dt_hyppar, dt_coef, input_collect, output_collect]):
         raise ValueError("When 'json_file' is not provided, 'input_collect' & 'output_collect' must be provided")

    if 'selectID' in output_collect:
        select_model = output_collect['selectID']
        
    # 2. Prep environment
    dt_input = input_collect['dt_input']
    dt_mod = input_collect['dt_mod']
    window_start_loc = input_collect['rollingWindowStartWhich']
    window_end_loc = input_collect['rollingWindowEndWhich']
    window_loc = list(range(window_start_loc, window_end_loc + 1))
    adstock = input_collect['adstock']
    paid_media_vars = input_collect['paid_media_vars']
    paid_media_spends = input_collect['paid_media_spends']
    paid_media_selected = input_collect['paid_media_selected']
    exposure_vars = input_collect['exposure_vars']
    organic_vars = input_collect['organic_vars']
    all_solutions = dt_hyppar['solID'].unique()
    day_interval = input_collect['dayInterval']
    date_var = input_collect['date_var']
    
    if select_model not in all_solutions and select_model is not None:
         raise ValueError(f"Input 'select_model' must be one of these values: {all_solutions}")
         
    # 3. Use Case
    usecase = which_usecase(metric_value, date_range)
    
    # 4. Checks
    metric_check = check_metric_type(metric_name, paid_media_spends, paid_media_vars, 
                                     paid_media_selected, exposure_vars, organic_vars)
    metric_name_updated = metric_check['metric_name_updated']
    metric_type = metric_check['metric_type']
    
    all_dates = dt_input[date_var]
    # R: all_values <- dt_mod[[metric_name_updated]]
    all_values = dt_mod[metric_name_updated]
    
    # Check metric dates
    # R: all_dates[1:window_end_loc] implies up to window_end_loc (1-based in R)
    # Python: all_dates[:window_end_loc+1]
    ds_list = check_metric_dates(date_range, all_dates.iloc[:window_end_loc+1], day_interval, quiet)
    
    val_list = check_metric_value(metric_value, metric_name_updated, all_values, ds_list['metric_loc'])
    
    if metric_value is not None and date_range is None:
        raise ValueError("Must specify date_range when using metric_value")
        
    date_range_updated = ds_list['date_range_updated']
    all_values_updated = val_list['all_values_updated']
    
    # 5. Get hyperparameters & beta coef
    # dt_hyppar is a DataFrame
    row_hyp = dt_hyppar[dt_hyppar['solID'] == select_model]
    
    theta = shape = scale = None
    if adstock == "geometric":
        theta = row_hyp[f"{metric_name_updated}_thetas"].iloc[0]
    elif "weibull" in adstock:
        shape = row_hyp[f"{metric_name_updated}_shapes"].iloc[0]
        scale = row_hyp[f"{metric_name_updated}_scales"].iloc[0]
        
    alpha = row_hyp[f"{metric_name_updated}_alphas"].iloc[0]
    gamma = row_hyp[f"{metric_name_updated}_gammas"].iloc[0]
    
    row_coef = dt_coef[(dt_coef['solID'] == select_model) & (dt_coef['rn'] == metric_name_updated)]
    if row_coef.empty:
        # Happens if coef is 0 or removed?
        coeff = 0
    else:
        coeff = row_coef['coef'].iloc[0]
        
    # 6. Historical transformation
    hist_transform = transform_decomp(
        all_values=all_values,
        adstock=adstock,
        theta=theta, shape=shape, scale=scale,
        alpha=alpha, gamma=gamma,
        window_loc=window_loc,
        coeff=coeff,
        metric_loc=ds_list['metric_loc']
    )
    
    # Data for Plotting
    # dt_line
    # metric = hist_transform['input_total'][window_loc]
    # response = hist_transform['response_total']
    
    # In R, window_loc is indices.
    # input_total is full length?
    
    dt_line = pd.DataFrame({
        'metric': hist_transform['input_total'][window_loc],
        'response': hist_transform['response_total'], # This is response_total which corresponds to window_loc in R's transform_decomp?
        'channel': metric_name_updated
    })
    
    dt_point = pd.DataFrame({
        'mean_input_immediate': [hist_transform['mean_input_immediate']],
        'mean_input_carryover': [hist_transform['mean_input_carryover']],
        'mean_input_total': [hist_transform['mean_input_immediate'] + hist_transform['mean_input_carryover']],
        'mean_response_immediate': [hist_transform['mean_response_total'] - hist_transform['mean_response_carryover']],
        'mean_response_carryover': [hist_transform['mean_response_carryover']],
        'mean_response_total': [hist_transform['mean_response_total']]
    })
    
    dt_point_sim = None
    if date_range is not None:
         dt_point_sim = pd.DataFrame({
             'input': [hist_transform['sim_mean_spend'] + hist_transform['sim_mean_carryover']],
             'output': [hist_transform['sim_mean_response']]
         })

    # 7. Simulated transformation
    hist_transform_sim = None
    if metric_value is not None:
        hist_transform_sim = transform_decomp(
            all_values=all_values_updated,
            adstock=adstock,
            theta=theta, shape=shape, scale=scale,
            alpha=alpha, gamma=gamma,
            window_loc=window_loc,
            coeff=coeff,
            metric_loc=ds_list['metric_loc'],
            calibrate_inflexion=hist_transform['inflexion']
        )
        dt_point_sim = pd.DataFrame({
             'input': [hist_transform_sim['sim_mean_spend'] + hist_transform_sim['sim_mean_carryover']],
             'output': [hist_transform_sim['sim_mean_response']]
         })
         
    # Return
    return {
        'metric_name': metric_name_updated,
        'date': date_range_updated,
        'input_total': hist_transform['input_total'],
        'input_carryover': hist_transform['input_carryover'],
        'input_immediate': hist_transform['input_immediate'],
        'response_total': hist_transform['response_total'],
        'response_carryover': hist_transform['response_carryover'],
        'response_immediate': hist_transform['response_immediate'],
        'inflexion': hist_transform['inflexion'],
        'mean_input_immediate': hist_transform['mean_input_immediate'],
        'mean_input_carryover': hist_transform['mean_input_carryover'],
        'mean_response_total': hist_transform['mean_response_total'],
        'mean_response_carryover': hist_transform['mean_response_carryover'],
        'mean_response': hist_transform['mean_response'],
        'sim_mean_spend': hist_transform_sim['sim_mean_spend'] if hist_transform_sim else hist_transform['sim_mean_spend'],
        'sim_mean_carryover': hist_transform_sim['sim_mean_carryover'] if hist_transform_sim else hist_transform['sim_mean_carryover'],
        'sim_mean_response': hist_transform_sim['sim_mean_response'] if hist_transform_sim else hist_transform['sim_mean_response'],
        'usecase': usecase,
        'dt_line': dt_line,
        'dt_point': dt_point,
        'dt_point_sim': dt_point_sim
    }

def which_usecase(metric_value, date_range):
    if metric_value is None and date_range is None:
        return "all_historical_vec"
    if metric_value is None and date_range is not None:
        return "selected_historical_vec"
    
    # Simulations
    if metric_value is not None:
        is_scalar_metric = isinstance(metric_value, (int, float, np.number)) or (isinstance(metric_value, (list, np.ndarray)) and len(metric_value) == 1)
        if is_scalar_metric and date_range is None:
            return "total_metric_default_range"
        if is_scalar_metric and date_range is not None:
            return "total_metric_selected_range"
        if not is_scalar_metric and date_range is None:
            return "unit_metric_default_last_n"
            
    return "unit_metric_selected_dates"

def transform_decomp(all_values, adstock, theta, shape, scale, alpha, gamma, window_loc, coeff, metric_loc, calibrate_inflexion=None):
    # Adstock
    x_list = transform_adstock(all_values, adstock, theta=theta, shape=shape, scale=scale)
    input_total = x_list['x_decayed']
    input_immediate = x_list['x_imme'] if 'x_imme' in x_list else x_list['x']
    input_carryover = input_total - input_immediate
    
    # Filter to window
    # window_loc is list of indices
    input_total_rw = input_total[window_loc]
    input_carryover_rw = input_carryover[window_loc]
    
    # Saturation
    saturated_total = saturation_hill(input_total_rw, alpha, gamma)
    saturated_carryover = saturation_hill(input_total_rw, alpha, gamma, x_marginal=input_carryover_rw)
    
    saturated_immediate = saturated_total['x_saturated'] - saturated_carryover['x_saturated']
    
    # Mean response all_values
    mean_input_immediate = np.mean(input_immediate[window_loc])
    mean_input_carryover = np.mean(input_carryover_rw)
    
    if len(window_loc) != len(saturated_total['x_saturated']):
        # Should match if window_loc used to slice input_total
        # In R: if length(window_loc) != length(saturated_total$x_saturated)
        # But we sliced input_total_rw using window_loc, so it should match.
        pass
        
    mean_response = np.mean(saturated_total['x_saturated'] * coeff)
    
    mean_response_total = fx_objective(
        x = mean_input_immediate,
        coeff = coeff,
        alpha = alpha,
        inflexion = saturated_total['inflexion'],
        x_hist_carryover = mean_input_carryover,
        get_sum = False
    )
    
    mean_response_carryover = fx_objective(
        x = 0,
        coeff = coeff,
        alpha = alpha,
        inflexion = saturated_total['inflexion'],
        x_hist_carryover = mean_input_carryover,
        get_sum = False
    )
    
    # Sim mean response date_range
    sim_mean_spend = np.mean(input_immediate[metric_loc])
    sim_mean_carryover = np.mean(input_carryover[metric_loc])
    
    if calibrate_inflexion is None:
        calibrate_inflexion = saturated_total['inflexion']
        
    sim_mean_response = fx_objective(
        x = sim_mean_spend,
        coeff = coeff,
        alpha = alpha,
        inflexion = calibrate_inflexion,
        x_hist_carryover = sim_mean_carryover,
        get_sum = False
    )
    
    return {
        'input_total': input_total,
        'input_immediate': input_immediate,
        'input_carryover': input_carryover,
        'saturated_total': saturated_total['x_saturated'],
        'saturated_carryover': saturated_carryover['x_saturated'],
        'saturated_immediate': saturated_immediate,
        'response_total': saturated_total['x_saturated'] * coeff,
        'response_carryover': saturated_carryover['x_saturated'] * coeff,
        'response_immediate': saturated_immediate * coeff,
        'inflexion': saturated_total['inflexion'],
        'mean_input_immediate': mean_input_immediate,
        'mean_input_carryover': mean_input_carryover,
        'mean_response_total': mean_response_total,
        'mean_response': mean_response,
        'mean_response_carryover': mean_response_carryover,
        'sim_mean_spend': sim_mean_spend,
        'sim_mean_carryover': sim_mean_carryover,
        'sim_mean_response': sim_mean_response
    }
