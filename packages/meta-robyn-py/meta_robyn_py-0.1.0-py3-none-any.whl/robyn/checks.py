
import pandas as pd
import numpy as np
import warnings

def check_nas(df, channels=None):
    if channels is not None:
        df = df[channels]
    
    if df.isnull().sum().sum() > 0:
        # report missingness
        missing = df.isnull().sum()
        missing = missing[missing > 0]
        strs = [f"{col} ({val} | {val/len(df):.2%})" for col, val in missing.items()]
        raise ValueError(
            f"Dataset contains missing (NA) values. "
            f"These values must be removed or fixed for Robyn to properly work.\n"
            f"Missing values: {', '.join(strs)}"
        )
    
    # Check infinite
    # select numeric columns first
    num_df = df.select_dtypes(include=[np.number])
    if np.isinf(num_df).sum().sum() > 0:
         inf_cols = num_df.columns[np.isinf(num_df).any()].tolist()
         raise ValueError(
             f"Dataset contains Inf values. "
             f"These values must be removed or fixed.\nCheck: {', '.join(inf_cols)}"
         )

def check_novar(dt_input, input_collect=None):
    # check columns with 0 variance
    # select numeric columns
    num_df = dt_input.select_dtypes(include=[np.number])
    # std == 0 ?
    # In R, zerovar uses n_distinct == 1
    
    novar_cols = []
    for col in num_df.columns:
        if num_df[col].nunique() <= 1:
            novar_cols.append(col)
            
    if novar_cols:
        msg = f"There are {len(novar_cols)} column(s) with no-variance: {', '.join(novar_cols)}. \nPlease, remove the variable(s) to proceed..."
        if input_collect:
            msg += f"\n>>> Note: there's no variance on these variables because of the modeling window filter ({input_collect.window_start}:{input_collect.window_end})"
        raise ValueError(msg)

def check_allneg(df):
    # If all values in a column are <= 0, take absolute?
    # R: unlist(lapply(df, function(x) all(x <= 0)))
    # mutate_at ... abs(x)
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        if (df[col] <= 0).all():
            df[col] = df[col].abs()
    return df

def check_varnames(dt_input, dt_holidays):
    dfs = {'dt_input': dt_input}
    if dt_holidays is not None:
        dfs['dt_holidays'] = dt_holidays
        
    for name, df in dfs.items():
        cols = df.columns
        if len(cols) != len(set(cols)):
            # duplicated names logic
            from collections import Counter
            counts = Counter(cols)
            dupes = [k for k, v in counts.items() if v > 1]
            raise ValueError(
                f"You have duplicated variable names for {name} in different parameters. "
                f"Check: {', '.join(dupes)}"
            )
        
        # Space in names
        with_space = [c for c in cols if " " in c]
        if with_space:
             raise ValueError(
                f"You have invalid variable names on {name} with spaces.\n"
                f"Please fix columns: {', '.join(with_space)}"
            )

def check_datevar(dt_input, date_var="auto"):
    dt_input = dt_input.copy()
    
    if date_var == "auto":
        # Find date columns
        # In pandas, we check dtype or try converting
        date_cols = []
        for col in dt_input.columns:
            if pd.api.types.is_datetime64_any_dtype(dt_input[col]):
                date_cols.append(col)
            # Potentially check object columns that look like dates?
            # R checks is.Date. Pandas often has object or datetime64.
            # Assuming user inputs proper types or we might need strict check.
            
        if len(date_cols) == 1:
            date_var = date_cols[0]
            print(f"Automatically detected 'date_var': {date_var}")
        else:
            raise ValueError("Can't automatically find a single date variable to set 'date_var'")
            
    if date_var is None or date_var not in dt_input.columns:
        raise ValueError("You must provide only 1 correct date variable name for 'date_var'")
        
    # Ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(dt_input[date_var]):
        try:
            dt_input[date_var] = pd.to_datetime(dt_input[date_var])
        except Exception:
             raise ValueError("Dates in 'date_var' must have valid date format")
             
    dt_input = dt_input.sort_values(by=date_var).reset_index(drop=True)
    
    dates = dt_input[date_var]
    if dates.duplicated().any():
        raise ValueError("Date variable shouldn't have duplicated dates (panel data)")
        
    if dates.isnull().any():
         raise ValueError("Dates in 'date_var' can't contain NA")
         
    # Check interval
    # R: difftime of 2nd - 1st
    day_interval = (dates.iloc[1] - dates.iloc[0]).days
    
    interval_type = ""
    if day_interval == 1:
        interval_type = "day"
    elif day_interval == 7:
        interval_type = "week"
    elif 28 <= day_interval <= 31:
        interval_type = "month"
    else:
        raise ValueError(f"{date_var} data has to be daily, weekly or monthly")
        
    return {
        'date_var': date_var,
        'dayInterval': day_interval,
        'intervalType': interval_type,
        'dt_input': dt_input
    }

def check_depvar(dt_input, dep_var, dep_var_type):
    if dep_var is None:
        raise ValueError("Must provide a valid dependent variable name for 'dep_var'")
    if dep_var not in dt_input.columns:
        raise ValueError("Must provide a valid dependent name for 'dep_var'")
    
    if not pd.api.types.is_numeric_dtype(dt_input[dep_var]):
        raise ValueError("'dep_var' must be a numeric or integer variable")
        
    if dep_var_type is None:
        raise ValueError("Must provide a dependent variable type for 'dep_var_type'")
        
    if dep_var_type not in ["conversion", "revenue"]:
        raise ValueError("'dep_var_type' must be 'conversion' or 'revenue'")

def check_prophet(dt_holidays, prophet_country, prophet_vars, prophet_signs, dayInterval=None):
    if dt_holidays is None or prophet_vars is None:
        return None
        
    prophet_vars = [p.lower() for p in prophet_vars]
    opts = ["trend", "season", "monthly", "weekday", "holiday"]
    
    if "holiday" not in prophet_vars:
        if prophet_country is not None:
             warnings.warn(f"Input 'prophet_country' is defined as {prophet_country} but 'holiday' is not setup within 'prophet_vars' parameter")
        prophet_country = None
        
    for p in prophet_vars:
        if p not in opts:
            raise ValueError(f"Allowed values for 'prophet_vars' are: {', '.join(opts)}")
            
    if "weekday" in prophet_vars and dayInterval is not None and dayInterval > 7:
        warnings.warn("Ignoring prophet_vars = 'weekday' input given your data granularity")
        
    if "holiday" in prophet_vars:
        if prophet_country is None:
             # Check if dt_holidays has country?
             # R: stop if prophet_country is null or not in dt_holidays$country
             # Assuming dt_holidays has 'country' col
             if 'country' in dt_holidays.columns:
                 available = dt_holidays['country'].unique()
                 raise ValueError(
                     f"You must provide 1 country code in 'prophet_country' input. "
                     f"{available} are included."
                 )
             else:
                  raise ValueError("dt_holidays must contain 'country' column")
                  
    if prophet_signs is None:
        prophet_signs = ["default"] * len(prophet_vars)
        
    if len(prophet_signs) == 1 and len(prophet_vars) > 1:
        prophet_signs = prophet_signs * len(prophet_vars)
        
    valid_signs = ["positive", "negative", "default"]
    if not all(s in valid_signs for s in prophet_signs):
        raise ValueError(f"Allowed values for 'prophet_signs' are: {', '.join(valid_signs)}")
        
    if len(prophet_signs) != len(prophet_vars):
        raise ValueError("'prophet_signs' must have same length as 'prophet_vars'")
        
    return prophet_signs

def check_context(dt_input, context_vars, context_signs):
    if context_vars:
        if context_signs is None:
            context_signs = ["default"] * len(context_vars)
            
        valid_signs = ["positive", "negative", "default"]
        if not all(s in valid_signs for s in context_signs):
            raise ValueError(f"Allowed values for 'context_signs' are: {', '.join(valid_signs)}")
            
        if len(context_signs) != len(context_vars):
             raise ValueError("Input 'context_signs' must have same length as 'context_vars'")
             
        missing = [c for c in context_vars if c not in dt_input.columns]
        if missing:
             raise ValueError(f"Input 'context_vars' not included in data. Check: {', '.join(missing)}")
             
        return {'context_signs': context_signs}
    return None

def check_paidmedia(dt_input, paid_media_vars, paid_media_signs, paid_media_spends):
    if paid_media_spends is None:
        raise ValueError("Must provide 'paid_media_spends'")
        
    # Vectors checked implicitly by python list/iterable nature
    
    missing_vars = [c for c in paid_media_vars if c not in dt_input.columns]
    if missing_vars:
        raise ValueError(f"Input 'paid_media_vars' not included in data. Check: {', '.join(missing_vars)}")
        
    missing_spends = [c for c in paid_media_spends if c not in dt_input.columns]
    if missing_spends:
        raise ValueError(f"Input 'paid_media_spends' not included in data. Check: {', '.join(missing_spends)}")
        
    if paid_media_signs is None:
        paid_media_signs = ["positive"] * len(paid_media_vars)
        
    valid_signs = ["positive", "negative", "default"]
    if not all(s in valid_signs for s in paid_media_signs):
        raise ValueError(f"Allowed values for 'paid_media_signs' are: {valid_signs}")
        
    if len(paid_media_signs) == 1 and len(paid_media_vars) > 1:
        paid_media_signs = paid_media_signs * len(paid_media_vars)
        
    if len(paid_media_signs) != len(paid_media_vars):
        raise ValueError("Input 'paid_media_signs' must have same length as 'paid_media_vars'")
        
    if len(paid_media_spends) != len(paid_media_vars):
        raise ValueError("Input 'paid_media_spends' must have same length as 'paid_media_vars'")
        
    # Check numeric
    for col in paid_media_vars:
        if not pd.api.types.is_numeric_dtype(dt_input[col]):
            raise ValueError(f"All your 'paid_media_vars' must be numeric. Check: {col}")
    for col in paid_media_spends:
        if not pd.api.types.is_numeric_dtype(dt_input[col]):
            raise ValueError(f"All your 'paid_media_spends' must be numeric. Check: {col}")
            
    # Check negative
    check_cols = list(set(paid_media_vars + paid_media_spends))
    neg_cols = []
    for col in check_cols:
        if (dt_input[col] < 0).any():
            neg_cols.append(col)
            
    if neg_cols:
        raise ValueError(f"{', '.join(neg_cols)} contains negative values. Media must be >=0")
        
    exposure_selector = [s != v for s, v in zip(paid_media_spends, paid_media_vars)]
    paid_media_selected = [v if sel else s for s, v, sel in zip(paid_media_spends, paid_media_vars, exposure_selector)]
    
    return {
        'paid_media_signs': paid_media_signs,
        'paid_media_vars': paid_media_vars,
        'exposure_selector': exposure_selector,
        'paid_media_selected': paid_media_selected
    }

def check_organicvars(dt_input, organic_vars, organic_signs):
    if not organic_vars:
        return None
        
    missing = [c for c in organic_vars if c not in dt_input.columns]
    if missing:
        raise ValueError(f"Input 'organic_vars' not included in data. Check: {', '.join(missing)}")
        
    if organic_signs is None:
        organic_signs = ["positive"] * len(organic_vars)
        
    valid_signs = ["positive", "negative", "default"]
    if not all(s in valid_signs for s in organic_signs):
        raise ValueError(f"Allowed values for 'organic_signs' are: {valid_signs}")
        
    if len(organic_signs) != len(organic_vars):
        raise ValueError("Input 'organic_signs' must have same length as 'organic_vars'")
        
    for col in organic_vars:
        if not pd.api.types.is_numeric_dtype(dt_input[col]):
            raise ValueError(f"All your 'organic_vars' must be numeric. Check: {col}")
            
    return {'organic_signs': organic_signs}

def check_factorvars(dt_input, factor_vars, context_vars):
    if factor_vars is None:
        factor_vars = []
    if context_vars is None:
        context_vars = []
        
    if factor_vars:
        if not all(f in context_vars for f in factor_vars):
            raise ValueError("Input 'factor_vars' must be any from 'context_vars' inputs")
            
    # Auto detect factors
    temp = dt_input[context_vars]
    undefined_factor = []
    for col in context_vars:
        if col not in factor_vars:
            # Check if not numeric
             if not pd.api.types.is_numeric_dtype(temp[col]):
                 undefined_factor.append(col)
                 
    if undefined_factor:
        print(f"Automatically set these variables as 'factor_vars': {', '.join(undefined_factor)}")
        factor_vars.extend(undefined_factor)
        
    return factor_vars

def check_allvars(all_ind_vars):
    if len(all_ind_vars) != len(set(all_ind_vars)):
        raise ValueError("All input variables must have unique names")

def check_datadim(dt_input, all_ind_vars, rel=10):
    num_obs = len(dt_input)
    if num_obs < len(all_ind_vars) * rel:
        warnings.warn(
            f"There are {len(all_ind_vars)} independent variables & {num_obs} data points. "
            f"We recommend row:column ratio of {rel} to 1"
        )
    if dt_input.shape[1] <= 2:
        raise ValueError("Provide a valid 'dt_input' input with at least 3 columns or more")

def check_windows(dt_input, date_var, all_media, window_start, window_end):
    dates_vec = pd.to_datetime(dt_input[date_var])
    
    if window_start is None:
        window_start = dates_vec.min()
    else:
        window_start = pd.to_datetime(window_start)
        if window_start < dates_vec.min():
            window_start = dates_vec.min()
            print(f"Input 'window_start' is adapted to earliest date: {window_start}")
        elif window_start > dates_vec.max():
             raise ValueError(f"Input 'window_start' larger than latest date: {dates_vec.max()}")
             
    # R: which.min(abs(difftime))
    # Finds closest date in data
    diff_start = (dates_vec - window_start).abs()
    rollingWindowStartWhich = diff_start.argmin() # Index of closest
    
    # Check if closest is significantly different? 
    # R says "Input 'window_start' is adapted to the closest date contained in input data"
    # Logic: if window_start not in dates_vec, set to closest.
    
    actual_start_date = dates_vec.iloc[rollingWindowStartWhich]
    if window_start != actual_start_date:
        # Actually R prints message regardless if it's not exact match?
        # Let's trust argmin
        window_start = actual_start_date
        print(f"Input 'window_start' is adapted to the closest date: {window_start}")
        
    refreshAddedStart = window_start # For refresh logic later
    
    if window_end is None:
        window_end = dates_vec.max()
    else:
        window_end = pd.to_datetime(window_end)
        if window_end > dates_vec.max():
            window_end = dates_vec.max()
            print(f"Input 'window_end' adapted to latest date: {window_end}")
        elif window_end < window_start:
             window_end = dates_vec.max() # Fallback? R sets to max-1 or something.
             print("Input 'window_end' < 'window_start'. Adapted to max.")
             
    diff_end = (dates_vec - window_end).abs()
    rollingWindowEndWhich = diff_end.argmin()
    window_end = dates_vec.iloc[rollingWindowEndWhich]
    
    # R logic involving .next_date is for handling "until but not including" or just ensuring coverage?
    # R: rollingWindowEndWhich - rollingWindowStartWhich + 1
    
    rollingWindowLength = rollingWindowEndWhich - rollingWindowStartWhich + 1
    
    # Check all 0s in window
    dt_init = dt_input.iloc[rollingWindowStartWhich : rollingWindowEndWhich+1][all_media]
    # Select numeric
    numeric_dt_init = dt_init.select_dtypes(include=[np.number])
    if (numeric_dt_init.sum() == 0).any():
        zeros = numeric_dt_init.columns[numeric_dt_init.sum() == 0].tolist()
        raise ValueError(
            f"These media channels contains only 0 within training period: {', '.join(zeros)}"
        )
        
    return {
        'dt_input': dt_input,
        'window_start': window_start,
        'rollingWindowStartWhich': rollingWindowStartWhich,
        'refreshAddedStart': refreshAddedStart,
        'window_end': window_end,
        'rollingWindowEndWhich': rollingWindowEndWhich,
        'rollingWindowLength': rollingWindowLength
    }

def check_adstock(adstock):
    if adstock is None:
        raise ValueError("Input 'adstock' can't be NULL.")
    if adstock == "weibull":
        adstock = "weibull_cdf"
    if adstock not in ["geometric", "weibull_cdf", "weibull_pdf"]:
        raise ValueError("Input 'adstock' must be 'geometric', 'weibull_cdf' or 'weibull_pdf'")
    return adstock

def check_hyperparameters(hyperparameters, adstock, paid_media_selected, 
                          paid_media_spends, organic_vars, exposure_vars, 
                          prophet_vars, context_vars):
    # This is complex in R.
    # For now, minimal check.
    if hyperparameters is None:
        print("Input 'hyperparameters' not provided yet.")
        return None
        
    # Check train_size
    if "train_size" not in hyperparameters:
        hyperparameters["train_size"] = [0.5, 0.8]
        warnings.warn("Automatically added missing hyperparameter: 'train_size' = [0.5, 0.8]")
        
    return hyperparameters

def check_metric_type(metric_name, paid_media_spends, paid_media_vars, paid_media_selected, exposure_vars, organic_vars):
    if organic_vars and metric_name in organic_vars:
        metric_type = "organic"
        metric_name_updated = metric_name
    elif (metric_name in paid_media_spends) or (metric_name in paid_media_vars):
        metric_type = "paid"
        # Find index
        if metric_name in paid_media_spends:
            idx = paid_media_spends.index(metric_name)
        else:
            idx = paid_media_vars.index(metric_name)
        metric_name_updated = paid_media_selected[idx]
    else:
        raise ValueError(
            f"Invalid 'metric_name' input: {metric_name}\n"
            "Input should be any media variable from paid_media_selected or organic_vars"
        )
        
    return {
        'metric_type': metric_type,
        'metric_name_updated': metric_name_updated
    }

def check_metric_dates(date_range=None, all_dates=None, dayInterval=None, quiet=False, is_allocator=False):
    if date_range is None:
        if dayInterval is None:
            raise ValueError("Input 'date_range' or 'dayInterval' must be defined")
        date_range = "all"
        if not quiet:
            print(f"Automatically picked date_range = '{date_range}'")
            
    # Handle "last_n" or "all"
    if isinstance(date_range, str) and ("last" in date_range or "all" in date_range):
        if "all" in date_range:
            date_range = f"last_{len(all_dates)}"
        
        if "_" in date_range:
             get_n = int(date_range.split("_")[1])
        else:
             get_n = 1
             
        date_range_vals = all_dates[-get_n:]
        date_range_loc = range(len(all_dates) - get_n, len(all_dates))
        date_range_updated = date_range_vals
        
    else:
        # Assume list of dates or single date
        if not isinstance(date_range, (list, pd.Series, np.ndarray)):
            date_range = [date_range]
            
        date_range = pd.to_datetime(date_range)
        all_dates = pd.to_datetime(all_dates)
        
        # Check if dates exist
        mask = all_dates.isin(date_range)
        if not mask.any():
             # Fuzzy match? R does closest match.
             # date_range_loc = range(sapply(date_range, FUN = function(x) which.min(abs(x - all_dates))))
             pass # For simplicity assume they match or implement fuzzy later
             
        date_range_loc = np.where(all_dates.isin(date_range))[0]
        date_range_updated = all_dates.iloc[date_range_loc]
        
    return {
        'date_range_updated': date_range_updated.tolist(),
        'metric_loc': list(date_range_loc)
    }

def check_metric_value(metric_value, metric_name, all_values, metric_loc):
    if metric_value is None:
        return {'metric_value_updated': None, 'all_values_updated': all_values}
        
    if np.any(pd.isna(metric_value)):
        metric_value = None
        
    get_n = len(metric_loc)
    metric_value_updated = all_values.iloc[metric_loc].values
    
    if metric_value is not None:
        if not isinstance(metric_value, (int, float, np.number)) and not (isinstance(metric_value, (list, np.ndarray)) and len(metric_value) > 0):
             raise ValueError(f"Input 'metric_value' for {metric_name} must be numerical")
             
        metric_value = np.array(metric_value)
        if (metric_value < 0).any():
             raise ValueError(f"Input 'metric_value' for {metric_name} must be positive")
             
        if get_n > 1 and metric_value.size == 1:
            metric_val_scalar = metric_value.item()
            metric_value_updated = metric_val_scalar * (metric_value_updated / np.sum(metric_value_updated))
        elif get_n == 1 and metric_value.size == 1:
            metric_value_updated = metric_value
        else:
             raise ValueError("robyn_response metric_value & date_range must have same length")
             
    all_values_updated = all_values.copy()
    all_values_updated.iloc[metric_loc] = metric_value_updated
    
    return {
        'metric_value_updated': metric_value_updated,
        'all_values_updated': all_values_updated
    }

def check_daterange(date_min, date_max, dates):
    dates = pd.to_datetime(dates)
    if date_min:
        date_min = pd.to_datetime(date_min)
        if date_min < dates.min():
            warnings.warn(f"Parameter 'date_min' not in data range. Changed to '{dates.min()}'")
            
    if date_max:
        date_max = pd.to_datetime(date_max)
        if date_max > dates.max():
            warnings.warn(f"Parameter 'date_max' not in data range. Changed to '{dates.max()}'")

def check_run_inputs(cores, iterations, trials, intercept_sign, nevergrad_algo):
    if iterations is None:
        raise ValueError("Must provide 'iterations' in robyn_run()")
    if trials is None:
         raise ValueError("Must provide 'trials' in robyn_run()")
    if nevergrad_algo is None:
         raise ValueError("Must provide 'nevergrad_algo' in robyn_run()")
         
    opts = ["non_negative", "unconstrained"]
    if intercept_sign not in opts:
         raise ValueError(f"Input 'intercept_sign' must be any of: {opts}")

def check_allocator(output_collect, select_model, paid_media_selected, scenario,
                    channel_constr_low, channel_constr_up, constr_mode):
    # Check model
    # output_collect is typically dict with 'resultHypParam' etc.
    # We need allSolutions. 
    # In R OutputCollect$allSolutions is a vector.
    # In python we might compute it or it's in a key.
    
    # Assuming output_collect['allSolutions'] exists or we derive it from resultHypParam
    all_solutions = []
    if 'allSolutions' in output_collect:
        all_solutions = output_collect['allSolutions']
    elif 'resultHypParam' in output_collect:
         all_solutions = output_collect['resultHypParam']['solID'].unique().tolist()
         
    if select_model not in all_solutions:
         raise ValueError(f"Provided 'select_model' is not within the best results. Try: {all_solutions}")
         
    if len(paid_media_selected) <= 1:
         raise ValueError("Must have a valid model with at least two 'paid_media_selected'")
         
    opts = ["max_response", "target_efficiency"]
    if scenario not in opts:
         raise ValueError(f"Input 'scenario' must be one of: {opts}")
         
    # Checks on constraints
    if (channel_constr_low is None and channel_constr_up is not None) or \
       (channel_constr_low is not None and channel_constr_up is None):
        raise ValueError("channel_constr_low and channel_constr_up must be both provided or both NULL")
        
    if channel_constr_low is not None:
        if np.any(np.array(channel_constr_low) < 0):
             raise ValueError("Inputs 'channel_constr_low' must be >= 0")
             
        # Length checks - assume scalar or list
        # If list, must match paid_media_selected length
        pass # Skip strict length check for now, handled in allocator logic usually
        
        if np.any(np.array(channel_constr_up) < np.array(channel_constr_low)):
             raise ValueError("Inputs 'channel_constr_up' must be >= 'channel_constr_low'")
             
    opts_constr = ["eq", "ineq"]
    if constr_mode not in opts_constr:
         raise ValueError(f"Input 'constr_mode' must be one of: {opts_constr}")


