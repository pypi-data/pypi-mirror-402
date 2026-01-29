
import pytest
import pandas as pd
import numpy as np
from src.robyn.inputs import robyn_inputs, check_datevar
from src.robyn.checks import check_windows

@pytest.fixture
def dt_simulated_weekly():
    # Create 2 years of weekly data
    dates = pd.date_range(start="2016-01-01", periods=104, freq="W-MON")
    df = pd.DataFrame({
        'DATE': dates,
        'revenue': np.random.rand(104) * 1000,
        'tv_S': np.random.rand(104) * 100,
        'facebook_I': np.random.rand(104) * 10000,
        'facebook_S': np.random.rand(104) * 100, # Spend
        'competitor_sales_B': np.random.rand(104) * 500
    })
    return df

@pytest.fixture
def dt_prophet_holidays():
    return pd.DataFrame({
        'ds': pd.to_datetime(["2016-01-01", "2016-12-25"]),
        'holiday': ['ny', 'xmas'],
        'country': ['US', 'US'],
        'year': [2016, 2016]
    })

def test_check_datevar(dt_simulated_weekly):
    res = check_datevar(dt_simulated_weekly, date_var="DATE")
    assert res['intervalType'] == 'week'
    assert res['dayInterval'] == 7

def test_robyn_inputs_basic(dt_simulated_weekly, dt_prophet_holidays):
    # Basic run without prophet or exposure
    inp = robyn_inputs(
        dt_input=dt_simulated_weekly,
        dt_holidays=dt_prophet_holidays,
        date_var="DATE",
        dep_var="revenue",
        dep_var_type="revenue",
        paid_media_spends=["tv_S", "facebook_S"],
        paid_media_vars=["tv_S", "facebook_I"],
        context_vars=["competitor_sales_B"],
        adstock="geometric",
        window_start="2016-01-04",
        window_end="2016-12-26"
    )
    
    assert inp['dep_var'] == "revenue"
    assert len(inp['paid_media_vars']) == 2
    assert inp['intervalType'] == "week"
    # exposure vars: facebook_I differs from facebook_S
    assert "facebook_I" in inp['exposure_vars']
    assert "tv_S" not in inp['exposure_vars'] 

def test_check_windows(dt_simulated_weekly):
    # Test window adaptation
    # Data starts 2016-01-04 (W-MON)
    
    res = check_windows(
        dt_input=dt_simulated_weekly,
        date_var="DATE",
        all_media=["tv_S"],
        window_start="2016-05-01", # Not a Monday
        window_end="2016-06-01" 
    )
    
    # closest Monday to 2016-05-01 (Sun). 2016-05-02 (Mon)
    expected_start = pd.Timestamp("2016-05-02")
    assert res['window_start'] == expected_start

def test_exposure_handling(dt_simulated_weekly):
    # Manual check of exposure handling logic
    # robyn_inputs calls it via robyn_engineering if hyperparameters present? 
    # Actually exposure_handling is called in robyn_engineering.
    # robyn_inputs ONLY calls robyn_engineering if hyperparameters are NOT NULL.
    # But for initial run, it calls engineering if hyperparameters is passed?
    # R: if (!is.null(hyperparameters)) ... robyn_engineering
    # Otherwise InputCollect returned without dt_mod.
    
    # We test robyn_inputs without hyperparameters first (returns InputCollect structure)
    inp = robyn_inputs(
        dt_input=dt_simulated_weekly,
        dep_var="revenue",
        dep_var_type="revenue",
        date_var="DATE",
        paid_media_spends=["tv_S", "facebook_S"],
        paid_media_vars=["tv_S", "facebook_I"],
        adstock="geometric"
    )
    
    assert inp['dt_mod'] is None
    
    # If we pass hyperparameters, it should trigger engineering
    hyps = {
        "tv_S_alphas": [0.5, 3],
        "tv_S_gammas": [0.3, 1],
        "tv_S_thetas": [0, 0.3],
        "facebook_I_alphas": [0.5, 3],
        "facebook_I_gammas": [0.3, 1],
        "facebook_I_thetas": [0.1, 0.4],
        "train_size": [0.5, 0.8]
    }
    
    inp_eng = robyn_inputs(
        dt_input=dt_simulated_weekly,
        dep_var="revenue",
        dep_var_type="revenue",
        date_var="DATE",
        paid_media_spends=["tv_S", "facebook_S"],
        paid_media_vars=["tv_S", "facebook_I"],
        adstock="geometric",
        hyperparameters=hyps
    )
    
    assert inp_eng['dt_mod'] is not None
    # Check if facebook_I was scaled
    # We need to peek into the logic or checking values
    # But if dt_mod exists, exposure handling ran.
