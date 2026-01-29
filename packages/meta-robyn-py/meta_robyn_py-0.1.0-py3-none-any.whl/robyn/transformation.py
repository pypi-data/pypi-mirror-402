
import numpy as np
import pandas as pd
from scipy import stats

def mic_men(x, Vmax, Km, reverse=False):
    """
    Michaelis-Menten Transformation
    
    The Michaelis-Menten mic_men() function is used to fit the spend
    exposure relationship for paid media variables, when exposure metrics like
    impressions, clicks or GRPs are provided in paid_media_vars instead
    of spend metric.
    """
    if not reverse:
        mm_out = Vmax * x / (Km + x)
    else:
        mm_out = x * Km / (Vmax - x)
    return mm_out

def adstock_geometric(x, theta):
    """
    Adstocking Transformation (Geometric)
    
    adstock_geometric() for Geometric Adstocking is the classic one-parametric
    adstock function.
    """
    x = np.array(x)
    if len(x) > 1:
        x_decayed = np.zeros_like(x, dtype=float)
        x_decayed[0] = x[0]
        for xi in range(1, len(x)):
            x_decayed[xi] = x[xi] + theta * x_decayed[xi - 1]
            
        thetaVecCum = np.array([theta] * len(x))
        for t in range(1, len(x)):
            thetaVecCum[t] = thetaVecCum[t-1] * theta
    else:
        x_decayed = x
        thetaVecCum = theta
        
    inflation_total = np.sum(x_decayed) / np.sum(x)
    
    return {
        'x': x,
        'x_decayed': x_decayed,
        'thetaVecCum': thetaVecCum,
        'inflation_total': inflation_total
    }

def adstock_weibull(x, shape, scale, windlen=None, type="pdf"):
    """
    Adstocking Transformation (Weibull)
    
    adstock_weibull() for Weibull Adstocking is a two-parametric adstock
    function that allows changing decay rate over time.
    """
    x = np.array(x)
    if windlen is None:
        windlen = len(x)
        
    if len(x) > 1:
        x_bin = np.arange(1, windlen + 1)
        scaleTrans = np.round(np.quantile(x_bin, scale)) 
        
        if shape == 0 or scale == 0:
            x_decayed = x
            thetaVecCum = np.zeros(windlen)
            x_imme = x
        else:
            if type.lower() == "pdf":
                thetaVecCum = _normalize(stats.weibull_min.pdf(x_bin, c=shape, scale=scaleTrans))
            elif type.lower() == "cdf":
                prob_sub = stats.weibull_min.cdf(x_bin[:-1], c=shape, scale=scaleTrans)
                thetaVec = np.concatenate(([1], 1 - prob_sub))
                thetaVecCum = np.cumprod(thetaVec)
            
            x_decayed = np.convolve(x, thetaVecCum)[:len(x)]
            
            theta0 = thetaVecCum[0]
            x_imme = x * theta0
            
    else:
        x_decayed = x
        x_imme = x
        thetaVecCum = 1
        
    inflation_total = np.sum(x_decayed) / np.sum(x)
    
    return {
        'x': x,
        'x_decayed': x_decayed,
        'thetaVecCum': thetaVecCum,
        'inflation_total': inflation_total,
        'x_imme': x_imme
    }

def transform_adstock(x, adstock, theta=None, shape=None, scale=None, windlen=None):
    if windlen is None:
        windlen = len(x)
        
    if adstock == "geometric":
        return adstock_geometric(x, theta)
    else:
        type_ = adstock.split('_')[-1]
        return adstock_weibull(x, shape=shape, scale=scale, windlen=windlen, type=type_)

def saturation_hill(x, alpha, gamma, x_marginal=None):
    """
    Hill Saturation Transformation
    """
    x = np.array(x)
    inflexion = np.max(x) * gamma
    
    if x_marginal is None:
        x_saturated = (x ** alpha) / (x ** alpha + inflexion ** alpha)
    else:
        x_marginal = np.array(x_marginal)
        x_saturated = (x_marginal ** alpha) / (x_marginal ** alpha + inflexion ** alpha)
        
    return {
        'x_saturated': x_saturated,
        'inflexion': inflexion
    }

def _normalize(x):
    if np.max(x) - np.min(x) == 0:
        return np.concatenate(([1], np.zeros(len(x) - 1)))
    else:
        return (x - np.min(x)) / (np.max(x) - np.min(x))

def run_transformations(all_media, window_start_loc, window_end_loc, dt_mod, adstock, dt_hyppar):
    dt_modAdstocked = dt_mod.copy().drop(columns=['ds'], errors='ignore')
    window_loc = slice(window_start_loc, window_end_loc + 1)
    
    adstocked_collect = {}
    saturated_total_collect = {}
    saturated_immediate_collect = {}
    saturated_carryover_collect = {}
    inflexion_collect = {}
    inflation_collect = {}
    
    for v in all_media:
        # 1. Adstocking
        m = dt_modAdstocked[v].values
        
        theta = None
        shape = None
        scale = None
        
        if adstock == "geometric":
            theta = dt_hyppar[f"{v}_thetas"].iloc[0]
        elif "weibull" in adstock:
            shape = dt_hyppar[f"{v}_shapes"].iloc[0]
            scale = dt_hyppar[f"{v}_scales"].iloc[0]
            
        x_list = transform_adstock(m, adstock, theta=theta, shape=shape, scale=scale)
        input_total = x_list['x_decayed']
        input_immediate = x_list['x_imme'] if 'x_imme' in x_list else m
        
        adstocked_collect[v] = input_total
        input_carryover = input_total - input_immediate
        
        # 2. Saturation (only window data)
        # Saturated response = Immediate + Carryover
        input_total_rw = input_total[window_loc]
        input_carryover_rw = input_carryover[window_loc]
        
        alpha = dt_hyppar[f"{v}_alphas"].iloc[0]
        gamma = dt_hyppar[f"{v}_gammas"].iloc[0]
        
        sat_temp_total = saturation_hill(input_total_rw, alpha, gamma)
        sat_temp_caov = saturation_hill(input_total_rw, alpha, gamma, x_marginal=input_carryover_rw)
        
        saturated_total_collect[v] = sat_temp_total['x_saturated']
        saturated_carryover_collect[v] = sat_temp_caov['x_saturated']
        # Immediate logic: Total - Carryover
        saturated_immediate_collect[v] = saturated_total_collect[v] - saturated_carryover_collect[v]
        
        inflexion_collect[f"{v}_inflexion"] = sat_temp_total['inflexion']
        inflation_collect[f"{v}_inflation"] = x_list['inflation_total']
        
    # Assemble dataframes
    
    dt_modAdstocked = dt_modAdstocked.drop(columns=all_media)
    for v, col in adstocked_collect.items():
        dt_modAdstocked[v] = col
        
    dt_modSaturated = dt_modAdstocked.iloc[window_loc].copy()
    dt_modSaturated = dt_modSaturated.drop(columns=list(adstocked_collect.keys()), errors='ignore')
    
    dt_modSaturated = dt_modSaturated.drop(columns=all_media, errors='ignore')
    for v, col in saturated_total_collect.items():
        dt_modSaturated[v] = col
        
    dt_saturatedImmediate = pd.DataFrame(saturated_immediate_collect).fillna(0)
    dt_saturatedCarryover = pd.DataFrame(saturated_carryover_collect).fillna(0)
    
    return {
        'dt_modSaturated': dt_modSaturated,
        'dt_saturatedImmediate': dt_saturatedImmediate,
        'dt_saturatedCarryover': dt_saturatedCarryover,
        'inflexions': inflexion_collect,
        'inflations': inflation_collect
    }

def fx_objective(x, coeff, alpha, inflexion, x_hist_carryover, inflation=None, get_sum=True):
    """
    Apply Hill transformation to scale spend to exposure.
    """
    # Adstock scales
    x_adstocked = x + np.mean(x_hist_carryover)
    
    # Avoid zero/negative issues for power
    # x_adstocked should be > 0 ideally.
    if np.any(x_adstocked <= 0):
         # Handle or just let it warn/NaN?
         # R doesn't check explicitly here.
         pass
         
    # Hill transformation
    # xOut = coeff * ((1 + inflexion**alpha / xAdstocked**alpha)**-1)
    
    denom = (1 + (inflexion**alpha) / (x_adstocked**alpha))
    x_out = coeff * (denom**-1)
    
    if get_sum:
        return np.sum(x_out)
    else:
        return x_out

def fx_gradient(x, coeff, alpha, inflexion, x_hist_carryover, inflation=None):
    """
    Gradient of fx_objective.
    """
    x_adstocked = x + np.mean(x_hist_carryover)
    
    # R impl:
    term1 = alpha * (inflexion**alpha) * (x_adstocked**(alpha - 1))
    term2 = (x_adstocked**alpha + inflexion**alpha)**2
    x_out = coeff * (term1 / term2)
    
    return np.sum(x_out)
