
import pytest
import pandas as pd
import numpy as np
from src.robyn.inputs import robyn_inputs
from src.robyn.model import robyn_run

@pytest.fixture
def dt_simulated_weekly():
    dates = pd.date_range(start="2016-01-01", periods=104, freq="W-MON")
    df = pd.DataFrame({
        'DATE': dates,
        'revenue': np.random.rand(104) * 1000 + 500, # Ensure positive
        'tv_S': np.random.rand(104) * 100,
        'facebook_I': np.random.rand(104) * 10000,
        'facebook_S': np.random.rand(104) * 100, 
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

def test_robyn_run_workflow(dt_simulated_weekly, dt_prophet_holidays):
    # 1. Inputs
    hyps = {
        "tv_S_alphas": [0.5, 3],
        "tv_S_gammas": [0.3, 1],
        "tv_S_thetas": [0, 0.3],
        "facebook_I_alphas": [0.5, 3],
        "facebook_I_gammas": [0.3, 1],
        "facebook_I_thetas": [0.1, 0.4],
        "train_size": [0.5, 0.8],
        "lambda": [0, 1]
    }
    
    # We use a mocked robyn_inputs or real one? Real one.
    # Note: If prophet not installed, it warns but returns data
    inp = robyn_inputs(
        dt_input=dt_simulated_weekly,
        dt_holidays=dt_prophet_holidays,
        date_var="DATE",
        dep_var="revenue",
        dep_var_type="revenue",
        paid_media_spends=["tv_S", "facebook_S"],
        paid_media_vars=["tv_S", "facebook_I"],
        context_vars=["competitor_sales_B"],
        prophet_vars=["trend", "season"], # Should assume unavailable or stubbed
        prophet_country="US",
        adstock="geometric",
        hyperparameters=hyps,
        window_start="2016-01-04",
        window_end="2016-12-26"
    )
    
    # 2. Run
    # Use very few iterations for speed testing
    models = robyn_run(
        InputCollect=inp,
        iterations=2,
        trials=1,
        nevergrad_algo="RandomSearch", # Faster/Simpler
        quiet=False
    )
    
    assert "trial1" in models
    assert len(models["trial1"]["resultCollect"]) == 2 # 2 iterations
    
    # Check result structure
    res = models["trial1"]["resultCollect"][0]
    assert "nrmse" in res
    assert "rssd" in res
    assert "hypParamSam" in res
    
    print(f"NRMSE: {res['nrmse']}")
