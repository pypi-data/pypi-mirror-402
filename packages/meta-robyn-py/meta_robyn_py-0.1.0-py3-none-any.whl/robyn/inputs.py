
import pandas as pd
import numpy as np
import warnings
from .checks import (
    check_varnames, check_allneg, check_nas, check_datevar, check_depvar,
    check_prophet, check_context, check_paidmedia, check_organicvars,
    check_factorvars, check_allvars, check_datadim, check_windows,
    check_adstock, check_novar, check_hyperparameters
)

# Placeholder for prophet
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


def robyn_inputs(dt_input=None,
                 dep_var=None,
                 dep_var_type=None,
                 date_var="auto",
                 paid_media_spends=None,
                 paid_media_vars=None,
                 paid_media_signs=None,
                 organic_vars=None,
                 organic_signs=None,
                 context_vars=None,
                 context_signs=None,
                 factor_vars=None,
                 dt_holidays=None,
                 prophet_vars=None,
                 prophet_signs=None,
                 prophet_country=None,
                 adstock=None,
                 hyperparameters=None,
                 window_start=None,
                 window_end=None,
                 calibration_input=None,
                 json_file=None,
                 InputCollect=None,
                 **kwargs):
                 
    # Use case 1: Running for the first time
    if InputCollect is None:
        dt_input = dt_input.copy()
        if dt_holidays is not None:
            dt_holidays = dt_holidays.copy()
            
        check_varnames(dt_input, dt_holidays)
        
        dt_input = check_allneg(dt_input)
        check_nas(dt_input) # specific columns check inside checks if validation needed
        if dt_holidays is not None:
            check_nas(dt_holidays)
            
        date_input = check_datevar(dt_input, date_var)
        dt_input = date_input['dt_input']
        date_var = date_input['date_var']
        dayInterval = date_input['dayInterval']
        intervalType = date_input['intervalType']
        
        check_depvar(dt_input, dep_var, dep_var_type)
        
        if dt_holidays is None or prophet_vars is None:
            dt_holidays = None
            prophet_vars = None
            prophet_country = None
            prophet_signs = None
            
        prophet_signs = check_prophet(dt_holidays, prophet_country, prophet_vars, prophet_signs, dayInterval)
        
        context = check_context(dt_input, context_vars, context_signs)
        if context:
            context_signs = context['context_signs']
            
        if paid_media_vars is None:
            paid_media_vars = paid_media_spends
            
        paid_collect = check_paidmedia(dt_input, paid_media_vars, paid_media_signs, paid_media_spends)
        paid_media_signs = paid_collect['paid_media_signs']
        
        exposure_vars = [v for v, s in zip(paid_media_vars, paid_media_spends) if v != s]
        
        organic = check_organicvars(dt_input, organic_vars, organic_signs)
        if organic:
            organic_signs = organic['organic_signs']
            
        factor_vars = check_factorvars(dt_input, factor_vars, context_vars)
        
        all_media = paid_collect['paid_media_selected'] + (organic_vars if organic_vars else [])
        all_ind_vars = []
        if prophet_vars:
            all_ind_vars.extend([p.lower() for p in prophet_vars])
        if context_vars:
            all_ind_vars.extend(context_vars)
        all_ind_vars.extend(all_media)
        
        check_allvars(all_ind_vars)
        
        check_datadim(dt_input, all_ind_vars)
        
        windows = check_windows(dt_input, date_var, all_media, window_start, window_end)
        window_start = windows['window_start']
        window_end = windows['window_end']
        
        adstock = check_adstock(adstock)
        
        unused_vars = [c for c in dt_input.columns if c not in [dep_var, date_var] + (context_vars or []) + (paid_media_vars or []) + (paid_media_spends or []) + (organic_vars or [])]
        
        # Check novar ignoring unused
        # check_novar(dt_input.drop(columns=unused_vars))
        
        # Calculate paid_media_total
        # filter window
        mask = (dt_input[date_var] >= window_start) & (dt_input[date_var] <= window_end)
        paid_media_total = dt_input.loc[mask, paid_media_spends].sum().sum()
        
        InputCollect = {
            'dt_input': dt_input,
            'dt_holidays': dt_holidays,
            'dt_mod': None,
            'dt_modRollWind': None,
            'date_var': date_var,
            'dayInterval': dayInterval,
            'intervalType': intervalType,
            'dep_var': dep_var,
            'dep_var_type': dep_var_type,
            'prophet_vars': [p.lower() for p in prophet_vars] if prophet_vars else [],
            'prophet_signs': prophet_signs,
            'prophet_country': prophet_country,
            'context_vars': context_vars or [],
            'context_signs': context_signs,
            'paid_media_vars': paid_media_vars,
            'paid_media_signs': paid_media_signs,
            'paid_media_spends': paid_media_spends,
            'paid_media_selected': paid_collect['paid_media_selected'],
            'paid_media_total': paid_media_total,
            'exposure_vars': exposure_vars,
            'organic_vars': organic_vars or [],
            'organic_signs': organic_signs,
            'all_media': all_media,
            'all_ind_vars': all_ind_vars,
            'factor_vars': factor_vars,
            'unused_vars': unused_vars,
            'window_start': window_start,
            'rollingWindowStartWhich': windows['rollingWindowStartWhich'],
            'window_end': window_end,
            'rollingWindowEndWhich': windows['rollingWindowEndWhich'],
            'rollingWindowLength': windows['rollingWindowLength'],
            'adstock': adstock,
            'hyperparameters': hyperparameters,
            'custom_params': kwargs
        }
        
        if hyperparameters is not None:
             hyperparameters = check_hyperparameters(hyperparameters, adstock, InputCollect['paid_media_selected'], 
                                                     paid_media_spends, organic_vars, exposure_vars, prophet_vars, context_vars)
             InputCollect = robyn_engineering(InputCollect, **kwargs)
             
        return InputCollect
        
    else:
        if hyperparameters is not None:
             InputCollect['hyperparameters'] = check_hyperparameters(
                 hyperparameters, 
                 InputCollect['adstock'], 
                 InputCollect['paid_media_selected'],
                 InputCollect['paid_media_spends'],
                 InputCollect['organic_vars'],
                 InputCollect['exposure_vars'],
                 InputCollect['prophet_vars'],
                 InputCollect['context_vars']
             )
             InputCollect = robyn_engineering(InputCollect, **kwargs)
             
        return InputCollect

def robyn_engineering(InputCollect, quiet=False, **kwargs):
    if not quiet:
        print(">> Running feature engineering...")
        
    dt_input = InputCollect['dt_input'].drop(columns=InputCollect['unused_vars'], errors='ignore')
    
    # Standardise ds and dep_var
    dt_transform = dt_input.rename(columns={
        InputCollect['date_var']: 'ds',
        InputCollect['dep_var']: 'dep_var'
    }).sort_values('ds')
    
    # Factor vars
    if InputCollect['factor_vars']:
        for f in InputCollect['factor_vars']:
            dt_transform[f] = dt_transform[f].astype('category')
            
    # Prophet logic
    if InputCollect['prophet_vars']:
        dt_transform = prophet_decomp(dt_transform, InputCollect['dt_holidays'], 
                                      InputCollect['prophet_country'], InputCollect['prophet_vars'], 
                                      InputCollect['prophet_signs'], InputCollect['factor_vars'],
                                      InputCollect['context_vars'], InputCollect['organic_vars'],
                                      InputCollect['paid_media_spends'], InputCollect['paid_media_vars'],
                                      InputCollect['intervalType'], InputCollect['dayInterval'],
                                      kwargs)
        
        # Check for missing prophet vars (if prophet failed or not installed)
        missing_prophet = [p for p in InputCollect['prophet_vars'] if p not in dt_transform.columns]
        if missing_prophet:
             warnings.warn(f"Prophet variables {missing_prophet} are missing in data (Prophet likely failed). Filling with 0.")
             for p in missing_prophet:
                 dt_transform[p] = 0.0
                                      
    # Exposure handling
    InputCollect['ExposureCollect'] = exposure_handling(dt_transform, 
                                                        InputCollect['rollingWindowStartWhich'], 
                                                        InputCollect['rollingWindowEndWhich'],
                                                        InputCollect['paid_media_spends'],
                                                        InputCollect['paid_media_vars'])
                                                        
    dt_transform = InputCollect['ExposureCollect']['dt_transform']
    
    # Finalize
    # select ds, dep_var, all_ind_vars
    cols = ['ds', 'dep_var'] + InputCollect['all_ind_vars']
    dt_transform = dt_transform[cols]
    
    InputCollect['dt_mod'] = dt_transform
    InputCollect['dt_modRollWind'] = dt_transform.iloc[InputCollect['rollingWindowStartWhich']:InputCollect['rollingWindowEndWhich']+1]
    
    return InputCollect

def prophet_decomp(dt_transform, dt_holidays, prophet_country, prophet_vars, prophet_signs,
                   factor_vars, context_vars, organic_vars, paid_media_spends,
                   paid_media_vars, intervalType, dayInterval, custom_params):
                   
    if not PROPHET_AVAILABLE:
        warnings.warn("Prophet is not installed. Skipping prophet decomposition. Results will be incorrect if prophet_vars are used.")
        return dt_transform

    # Prophet implementation
    # Basic recurrence dataframe
    recurrence = dt_transform[['ds', 'dep_var']].rename(columns={'dep_var': 'y'})
    
    use_trend = "trend" in prophet_vars
    use_holiday = "holiday" in prophet_vars
    use_season = "season" in prophet_vars or "yearly.seasonality" in prophet_vars
    use_monthly = "monthly" in prophet_vars # custom seasonality
    use_weekday = "weekday" in prophet_vars or "weekly.seasonality" in prophet_vars
    
    holidays = None
    if use_holiday and dt_holidays is not None:
         holidays = dt_holidays[dt_holidays['country'] == prophet_country]
         
    # Setup Prophet
    # yearly.seasonality logic
    yearly_seasonality = custom_params.get('yearly_seasonality', use_season)
    weekly_seasonality = custom_params.get('weekly_seasonality', use_weekday)
    
    m = Prophet(
        holidays=holidays,
        yearly_seasonality=yearly_seasonality,
        weekly_seasonality=weekly_seasonality,
        daily_seasonality=False
    )
    
    if use_monthly:
        m.add_seasonality(name='monthly', period=30.5, fourier_order=5)
        
    # Add regressors?
    # R: dt_regressors includes paid_media, etc.
    # But R's prophet_decomp creates dt_regressors but does NOT add them as regressors to Prophet model unless they are factor_vars?
    # R code: Only if factor_vars > 0, it calls add_regressor.
    # Otherwise fit.prophet(modelRecurrence, dt_regressors)
    # Wait, if we don't add_regressor, Prophet ignores extra columns in 'df'.
    # R code seems to treat this strictly as time series decomposition of Y.
    # It does NOT seem to regress on paid_media vars inside Prophet?
    # "decompose ... from the dependent variable".
    # So we just fit on y and ds.
    
    m.fit(recurrence)
    forecast = m.predict(recurrence)
    
    # Extract components
    if use_trend:
        dt_transform['trend'] = forecast['trend']
    if use_season:
        dt_transform['season'] = forecast['yearly']
    if use_monthly:
        dt_transform['monthly'] = forecast['monthly']
    if use_weekday:
        dt_transform['weekday'] = forecast['weekly']
    if use_holiday:
        dt_transform['holiday'] = forecast['holidays']
        
    return dt_transform

def exposure_handling(dt_transform, window_start_loc, window_end_loc, paid_media_spends, paid_media_vars):
    # R: exposure_selector <- paid_media_spends != paid_media_vars
    # Here we assume list order matches
    
    for i, (spend, var) in enumerate(zip(paid_media_spends, paid_media_vars)):
        if spend != var:
            # Modeled exposure
            temp_spend = dt_transform[spend]
            temp_expo = dt_transform[var]
            
            # window slice
            temp_spend_window = temp_spend.iloc[window_start_loc:window_end_loc+1]
            temp_expo_window = temp_expo.iloc[window_start_loc:window_end_loc+1]
            
            cpe = temp_spend.sum() / temp_expo.sum()
            cpe_window = temp_spend_window.sum() / temp_expo_window.sum()
            
            # If we need to scale exposure to match spend scale for modeling
            # R: temp_spend_scaled <- ifelse(selector, temp_expo * temp_cpe, temp_spend)
            # R uses temp_cpe (total) or temp_cpe_window?
            # R: spend_scaled_extrapolated <- temp_expo * temp_cpe_window
            # effectively replacing the spend variable with scaled exposure?
            
            spend_scaled_extrapolated = temp_expo * cpe_window
            
            # Update dt_transform
            # paid_media_selected[i] is var (exposure) if different. 
            # In R: dt_transform <- mutate_at(vars(paid_media_selected[i]), function(x) unlist(spend_scaled_extrapolated))
            # Wait, `paid_media_selected` is the exposure var name.
            # So it overwrites the exposure column with the scaled version (which looks like spend).
            # This effectively makes the model use "Scaled Exposure" as the input, which has same magnitude as Spend.
            
            dt_transform[var] = spend_scaled_extrapolated
            
    return {'dt_transform': dt_transform}

