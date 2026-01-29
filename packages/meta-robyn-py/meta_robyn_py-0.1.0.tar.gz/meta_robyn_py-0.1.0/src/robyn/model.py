
import numpy as np
import pandas as pd
import time
from scipy.optimize import lsq_linear
import nevergrad as ng
from io import StringIO
import sys

from .checks import check_adstock
from .transformation import run_transformations

def robyn_run(InputCollect,
              dt_hyper_fixed=None,
              ts_validation=False,
              add_penalty_factor=False,
              refresh=False,
              seed=123,
              outputs=False,
              quiet=False,
              cores=None,
              trials=5,
              iterations=2000,
              nevergrad_algo="TwoPointsDE",
              intercept_sign="non_negative",
              intercept=True,
              lambda_control=None,
              rssd_zero_penalty=True,
              objective_weights=None,
              time_limit=None,
              **kwargs):
              
    t0 = time.time()
    
    # Validation
    if 'hyperparameters' not in InputCollect or InputCollect['hyperparameters'] is None:
        raise ValueError("Must provide 'hyperparameters' in robyn_inputs()'s output first")
        
    hyps_fixed = dt_hyper_fixed is not None
    if hyps_fixed:
        trials = 1
        iterations = 1
        
    # Prepare hyperparameters
    hyper_collect = hyper_collector(
        InputCollect,
        InputCollect['hyperparameters'],
        ts_validation=ts_validation,
        add_penalty_factor=add_penalty_factor,
        dt_hyper_fixed=dt_hyper_fixed
    )
    
    # Run trials
    OutputModels = robyn_train(
        InputCollect, hyper_collect,
        cores=cores, iterations=iterations, trials=trials,
        intercept_sign=intercept_sign, intercept=intercept,
        nevergrad_algo=nevergrad_algo,
        dt_hyper_fixed=dt_hyper_fixed,
        ts_validation=ts_validation,
        add_penalty_factor=add_penalty_factor,
        rssd_zero_penalty=rssd_zero_penalty,
        objective_weights=objective_weights,
        refresh=refresh, seed=seed, quiet=quiet
    )
    
    # Collect results... for now return OutputModels
    return OutputModels

def robyn_train(InputCollect, hyper_collect,
                cores, iterations, trials,
                intercept_sign, intercept,
                nevergrad_algo,
                dt_hyper_fixed=None,
                ts_validation=True,
                add_penalty_factor=False,
                objective_weights=None,
                rssd_zero_penalty=True,
                refresh=False, seed=123,
                quiet=False):
                
    hyper_fixed = hyper_collect['all_fixed']
    
    OutputModels = {}
    
    if not quiet:
        print(f">>> Starting {trials} trials with {iterations} iterations each using {nevergrad_algo}...")
        
    for ngt in range(1, trials + 1):
        if not quiet:
            print(f"  Running trial {ngt} of {trials}")
            
        model_output = robyn_mmm(
            InputCollect=InputCollect,
            hyper_collect=hyper_collect,
            iterations=iterations,
            nevergrad_algo=nevergrad_algo,
            intercept=intercept,
            intercept_sign=intercept_sign,
            ts_validation=ts_validation,
            add_penalty_factor=add_penalty_factor,
            rssd_zero_penalty=rssd_zero_penalty,
            objective_weights=objective_weights,
            refresh=refresh,
            trial=ngt,
            seed=seed + ngt,
            quiet=quiet
        )
        OutputModels[f"trial{ngt}"] = model_output
        
    return OutputModels

def robyn_mmm(InputCollect, hyper_collect, iterations, nevergrad_algo,
              intercept=True, intercept_sign="non_negative",
              ts_validation=True, add_penalty_factor=False,
              objective_weights=None, dt_hyper_fixed=None,
              rssd_zero_penalty=True, refresh=False,
              trial=1, seed=123, quiet=False):
              
    np.random.seed(seed)
    
    # Setup optimizer
    hyper_bound_list_updated = hyper_collect['hyper_bound_list_updated']
    hyper_bound_list_fixed = hyper_collect['hyper_bound_list_fixed']
    
    # Parameter names
    updated_names = list(hyper_bound_list_updated.keys())
    fixed_names = list(hyper_bound_list_fixed.keys())
    
    # Nevergrad instrumentation
    # We map [0,1]^d to the parameter space
    dimension = len(updated_names)
    parametrization = ng.p.Array(shape=(dimension,), lower=0, upper=1)
    optimizer = ng.optimizers.registry[nevergrad_algo](parametrization=parametrization, budget=iterations)
    
    # Prepare data
    dt_mod = InputCollect['dt_mod']
    if dt_mod is None:
        raise ValueError("Run Engineering first")
        
    rollingWindowStartWhich = InputCollect['rollingWindowStartWhich']
    rollingWindowEndWhich = InputCollect['rollingWindowEndWhich']
    rollingWindowLength = InputCollect['rollingWindowLength']
    
    # Spend share for RSSD
    dt_inputTrain = InputCollect['dt_input'].iloc[rollingWindowStartWhich:rollingWindowEndWhich+1]
    paid_media_spends = InputCollect['paid_media_spends']
    paid_media_selected = InputCollect['paid_media_selected']
    
    total_spend = dt_inputTrain[paid_media_spends].sum()
    spend_share = total_spend / total_spend.sum()
    # Map spends to paid_media_selected names if different?
    # R logic: uses paid_media_selected names for the result
    spend_share.index = paid_media_selected # Assuming order matches
    
    # Lambda range
    # Prepare X and y for lambda calculation
    # We need to exclude ds and dep_var
    X_lambda = dt_mod.drop(columns=['ds', 'dep_var'])
    # Handle factors/categories
    X_lambda = pd.get_dummies(X_lambda, drop_first=True).astype(float)
    
    y_lambda = dt_mod['dep_var']
    lambdas = lambda_seq(X_lambda, y_lambda)
    lambda_max = np.max(lambdas) * 0.1
    lambda_min = lambda_max * 0.0001
    
    # Results container
    resultCollectNG = []
    
    for i in range(iterations):
        # Ask
        candidate = optimizer.ask()
        params = candidate.value # [0,1] vector
        
        # Map params to values
        hypParamSam = {}
        for idx, name in enumerate(updated_names):
            bounds = hyper_bound_list_updated[name]
            val = bounds[0] + (bounds[1] - bounds[0]) * params[idx]
            hypParamSam[name] = val
            
        # Add fixed
        for name in fixed_names:
            hypParamSam[name] = hyper_bound_list_fixed[name][0]
            
        # Convert to Series/DF for interaction
        dt_hyppar = pd.DataFrame([hypParamSam])
        
        # Transformations
        # Check adstock validity
        adstock = check_adstock(InputCollect['adstock'])
        
        temp = run_transformations(
            all_media=InputCollect['all_media'],
            window_start_loc=rollingWindowStartWhich,
            window_end_loc=rollingWindowEndWhich,
            dt_mod=dt_mod,
            adstock=adstock,
            dt_hyppar=dt_hyppar
        )
        
        dt_modSaturated = temp['dt_modSaturated']
        y_window = dt_modSaturated['dep_var'].values
        # drop dep_var to get X
        X_window = dt_modSaturated.drop(columns=['dep_var'])
        # One hot encoding? R uses lares::ohse.
        # factor_vars should be handled. In Python, pd.get_dummies if they are categories.
        # Assuming dt_modSaturated has factors if prepared.
        X_window = pd.get_dummies(X_window, drop_first=True).astype(float).values
        
        # Train/Test split
        train_size = hypParamSam['train_size']
        n_obs = len(y_window)
        
        if train_size < 1:
             train_idx = int(n_obs * train_size)
             val_idx = train_idx + int(n_obs * (1 - train_size) / 2)
             
             y_train = y_window[:train_idx]
             y_val = y_window[train_idx:val_idx]
             y_test = y_window[val_idx:]
             
             X_train = X_window[:train_idx, :]
             X_val = X_window[train_idx:val_idx, :]
             X_test = X_window[val_idx:, :]
        else:
             y_train = y_window
             X_train = X_window
             y_val = y_test = X_val = X_test = None

        # Feature signs
        # We need to map column names of X_window to signs.
        # Complex if One Hot Encoding added columns.
        # For now assume no factors or handle simple case.
        # R logic parses names.
        
        lower_limits = []
        upper_limits = []
        # Stub logic for bounds:
        # If paid_media (positive), organic (positive), context (default/positive/negative).
        # We assume 0 to Inf for positive, -Inf to Inf for default.
        # We need to map X_window columns to variables.
        # pd.get_dummies changes names.
        
        # Simplified: all media positive.
        # Context vars: look up signs.
        # Prophent vars: look up signs.
        
        # Since I used .values, I lost column names. I should keep them.
        X_cols = pd.get_dummies(dt_modSaturated.drop(columns=['dep_var']), drop_first=True).columns
        
        for col in X_cols:
            # Determine sign
            # This requires mapping col back to original var.
            # Simplified: default to -Inf, Inf.
            # If col in paid_media_selected -> 0, Inf.
            lower = -np.inf
            upper = np.inf
            
            # Simple substring check (risky but okay for prototype)
            # Or strict check against lists
            if col in InputCollect['paid_media_selected'] or col in InputCollect['organic_vars']:
                 lower = 0
            
            lower_limits.append(lower)
            upper_limits.append(upper)
            
        lower_limits = np.array(lower_limits)
        upper_limits = np.array(upper_limits)
        
        # Lambda
        lambda_hp = hypParamSam.get('lambda', 0) # nevergrad 0-1
        lambda_scaled = lambda_min + (lambda_max - lambda_min) * lambda_hp
        
        # Ridge
        mod_out = model_refit(
            X_train, y_train, X_val, y_val, X_test, y_test,
            lambda_=lambda_scaled,
            lower_limits=lower_limits,
            upper_limits=upper_limits,
            intercept=intercept,
            intercept_sign=intercept_sign
        )
        
        # Errors
        nrmse = mod_out['nrmse_val'] if ts_validation else mod_out['nrmse_train']
        mape = mod_out['mape_val'] if ts_validation else mod_out['mape_train']
        
        # Decomp RSSD
        # Need decomposition.
        decompCollect = model_decomp(
            coefs=mod_out['coefs'],
            y_pred=mod_out['y_pred'],
            dt_modSaturated=temp['dt_modSaturated'],
            X_cols=X_cols # Pass feature names
        )
        
        # Business logic for RSSD
        xDecompAgg = decompCollect['xDecompAgg']
        # Compare shares
        # Assuming xDecompAgg has rows for each media
        # Join with spend_share
        
        # Calculate RSSD
        # Simplified
        rssd = 0 
        for media in paid_media_selected:
             if media in xDecompAgg.index:
                 eff_share = xDecompAgg.loc[media, 'xDecompPerc']
                 sp_share = spend_share[media]
                 rssd += (eff_share - sp_share)**2
        rssd = np.sqrt(rssd)
        
        # Tell optimization
        # Objectives
        # We optimize NRMSE and RSSD (MAPE is just tracked)
        optimizer.tell(candidate, [nrmse, rssd])
        
        # Collect result
        # We need to flatten hypParamSam
        row = {'iter': i, 'nrmse': nrmse, 'decomp.rssd': rssd, 'mape': mape} # Use . for R compat
        row.update(hypParamSam)
        # Add inflexions
        row.update(temp['inflexions']) # These keys are like "{media}_inflexion"
        
        # Add loop info
        row['iterNG'] = i + 1 # 1-based
        row['iterPar'] = 1 # Serial
        
        resultCollectNG.append(row)
        
        # xDecompAgg check
        # Add metadata to xDecompAgg
        xDecompAgg['iterNG'] = i + 1
        xDecompAgg['iterPar'] = 1
        # xDecompAgg['solID'] = ... added later
        xDecompAgg['rn'] = xDecompAgg.index
        
        # To avoid memory explosion, R might be storing this efficiently or just big DF.
        if i == 0:
            xDecompVecCollect = [xDecompAgg]
        else:
            xDecompVecCollect.append(xDecompAgg)
            
    # Convert to DataFrames
    resultHypParam = pd.DataFrame(resultCollectNG)
    xDecompAgg = pd.concat(xDecompVecCollect, ignore_index=True)
    
    # Add solID
    # trial_iter
    # trial is int.
    # solID format: "1_1", "1_2" ...
    resultHypParam['solID'] = f"{trial}_" + resultHypParam['iterNG'].astype(str) + "_" + resultHypParam['iterPar'].astype(str)
    
    # helper for xDecompAgg
    # Join logic? or just map.
    # xDecompAgg has iterNG. iterPar is 1.
    xDecompAgg['solID'] = f"{trial}_" + xDecompAgg['iterNG'].astype(str) + "_" + xDecompAgg['iterPar'].astype(str)
    
    # Reorder/Rename columns to match R expected
    # R resultHypParam has: solID, trial, iterNG, iterPar, nrmse, decomp.rssd, ...hyperparams...
    
    return {
        'resultCollect': {
            'resultHypParam': resultHypParam,
            'xDecompAgg': xDecompAgg,
            'liftCalibration': None
        },
        'hyper_collect': hyper_collect,
        'trial': trial
    }

def model_refit(X_train, y_train, X_val, y_val, X_test, y_test,
                lambda_, lower_limits, upper_limits,
                intercept=True, intercept_sign="non_negative"):
    
    n_samples, n_features = X_train.shape
    
    # Augmented matrices for constrained Ridge
    # Objective: ||y - Xb||^2 + lambda*2N * ||b||^2
    # sqrt_lambda = sqrt(lambda_ * 2 * n_samples)
    
    sqrt_lambda = np.sqrt(lambda_ * 2 * n_samples)
    
    X_aug = np.vstack([X_train, sqrt_lambda * np.eye(n_features)])
    y_aug = np.concatenate([y_train, np.zeros(n_features)])
    
    # Intercept handling:
    # If intercept=True, likely handled by lsq_linear if we add a column of 1s, OR convert center data.
    # Robyn often uses Intercept. lsq_linear doesn't support intercept argument directly.
    # We must add column of 1s.
    
    if intercept:
        # Add column of 1s to X_aug (but NOT to identity part for penalty? Intercept usually not penalized)
        # To not penalize intercept, the corresponding row in identity part should be 0.
        
        col_ones = np.ones((n_samples, 1))
        # For penalty rows, intercept row should be 0s.
        col_zeros = np.zeros((n_features, 1))
        
        X_aug_int = np.hstack([ 
            np.vstack([col_ones, col_zeros]), 
            X_aug 
        ])
        
        # Adjust limits for intercept (usually -Inf to Inf, or 0 to Inf)
        int_lower = 0 if intercept_sign == "non_negative" else -np.inf
        int_upper = np.inf
        
        lower_limits = np.concatenate(([int_lower], lower_limits))
        upper_limits = np.concatenate(([int_upper], upper_limits))
        
        X_fit = X_aug_int
    else:
        X_fit = X_aug
        
    # Fit
    res = lsq_linear(X_fit, y_aug, bounds=(lower_limits, upper_limits), lsmr_tol='auto')
    
    coefs = res.x
    
    # Predictions
    # Need to handle intercept in prediction
    if intercept:
        beta = coefs[1:]
        beta_0 = coefs[0]
        y_train_pred = X_train @ beta + beta_0
        if X_val is not None:
             y_val_pred = X_val @ beta + beta_0
             y_test_pred = X_test @ beta + beta_0
    else:
        beta = coefs
        beta_0 = 0
        y_train_pred = X_train @ beta
        if X_val is not None:
             y_val_pred = X_val @ beta
             y_test_pred = X_test @ beta
    
    # NRMSE
    nrmse_train = np.sqrt(np.mean((y_train - y_train_pred)**2)) / (np.max(y_train) - np.min(y_train))
    
    # MAPE
    # Avoid div by zero
    y_train_safe = np.where(y_train == 0, 1e-9, y_train)
    mape_train = np.mean(np.abs((y_train - y_train_pred) / y_train_safe))
    
    nrmse_val = 0
    mape_val = 0
    if X_val is not None:
         nrmse_val = np.sqrt(np.mean((y_val - y_val_pred)**2)) / (np.max(y_val) - np.min(y_val))
         y_val_safe = np.where(y_val == 0, 1e-9, y_val)
         mape_val = np.mean(np.abs((y_val - y_val_pred) / y_val_safe))
         
    return {
        'coefs': coefs, # Includes intercept at index 0 if present
        'y_train_pred': y_train_pred,
        'y_val_pred': y_val_pred if X_val is not None else None,
        'y_pred': y_train_pred, # Concatenate if full
        'nrmse_train': nrmse_train,
        'nrmse_val': nrmse_val,
        'mape_train': mape_train,
        'mape_val': mape_val
    }

def model_decomp(coefs, y_pred, dt_modSaturated, X_cols):
    # Simplified decomp
    # Assume coefs[0] is intercept
    intercept = coefs[0]
    betas = coefs[1:]
    
    # We must dummify X to match betas dimensions
    X_raw = dt_modSaturated.drop(columns=['dep_var'])
    X = pd.get_dummies(X_raw, drop_first=True).astype(float)
    
    # Ensure columns match X_cols order and content
    # For robust alignment, reindex
    X = X.reindex(columns=X_cols, fill_value=0)
    
    # xDecomp
    # Elementwise multiply X * betas (broadcasting)
    # betas is array, X is DF.
    xDecomp = X * betas
    xDecomp['intercept'] = intercept
    
    # Aggregation
    xDecompAgg = xDecomp.sum() # Sum over time
    xDecompPerc = xDecompAgg / xDecompAgg.sum()
    
    # Map coefs to names
    # intersect indices
    coef_series = pd.Series(betas, index=X_cols) # Use X_cols which aligns with betas
    # actually X came from dt_modSaturated.drop('dep_var').
    # betas came from lsq_linear(X_aug ...).
    # X_aug was built from X_train which is X_window.
    # X_window was built from dt_modSaturated -> get_dummies.
    # So headers match X_cols.
    
    # We need to supply coefs for intercept too? 
    # xDecomp has 'intercept'.
    coef_series['intercept'] = intercept
    
    # Align
    coefs_aligned = coef_series.reindex(xDecompAgg.index)
    
    res = pd.DataFrame({
        'xDecompAgg': xDecompAgg, 
        'xDecompPerc': xDecompPerc,
        'coef': coefs_aligned
    })
    return {'xDecompAgg': res}

def lambda_seq(x, y, seq_len=100, lambda_min_ratio=0.0001):
    # Simple lambda sequence like glmnet
    # lambda_max = max( |x'y| ) / N ?
    # R: max(abs(colSums(sx * sy))) / (0.001 * nrow(x))
    # where sx, sy are scaled.
    
    n, p = x.shape
    # Scale
    sd_x = x.std(axis=0) + 1e-10 # avoid div 0
    sx = (x - x.mean(axis=0)) / sd_x
    sy = y # R says sy <- y, not scaled? Line 1261
    
    # colSums(sx * sy) is dot product
    dot = sx.T @ sy
    lambda_max = np.max(np.abs(dot)) / (0.001 * n)
    
    lambdas = np.logspace(np.log10(lambda_max * lambda_min_ratio), np.log10(lambda_max), num=seq_len)
    return lambdas

def hyper_collector(InputCollect, hyper_in, ts_validation, add_penalty_factor, dt_hyper_fixed=None):
    # Flatten/organize hyperparameters
    # hyper_in contains ranges.
    
    updated = {}
    fixed = {}
    
    for k, v in hyper_in.items():
        if len(v) == 2:
            updated[k] = v
        else:
            fixed[k] = v
            
    # Add lambda if missing
    if 'lambda' not in updated and 'lambda' not in fixed:
        updated['lambda'] = [0, 1]
        
    return {
        'hyper_bound_list_updated': updated,
        'hyper_bound_list_fixed': fixed,
        'all_fixed': dt_hyper_fixed is not None # Logic from R
    }
