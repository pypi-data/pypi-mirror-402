
import pytest
import numpy as np
from src.robyn.transformation import mic_men, adstock_geometric, adstock_weibull, saturation_hill

def test_mic_men():
    x = np.array([5, 6, 7, 8, 9, 10])
    Vmax = 5
    Km = 0.5
    # R output check:
    # 5 * 5 / (0.5 + 5) = 25 / 5.5 = 4.545455
    # 5 * 10 / (0.5 + 10) = 50 / 10.5 = 4.761905
    
    res = mic_men(x, Vmax, Km)
    expected_first = 5 * 5 / (0.5 + 5)
    expected_last = 5 * 10 / (0.5 + 10)
    
    assert np.isclose(res[0], expected_first)
    assert np.isclose(res[-1], expected_last)

def test_mic_men_reverse():
    x = np.array([4.545455])
    Vmax = 5
    Km = 0.5
    # Reverse: x * Km / (Vmax - x)
    # 4.545455 * 0.5 / (5 - 4.545455) = 2.2727 / 0.454545 = 5
    
    res = mic_men(x, Vmax, Km, reverse=True)
    assert np.isclose(res[0], 5.0, atol=1e-5)

def test_adstock_geometric():
    x = np.array([100, 100, 100, 100, 100])
    theta = 0.5
    
    # Day 1: 100
    # Day 2: 100 + 0.5 * 100 = 150
    # Day 3: 100 + 0.5 * 150 = 100 + 75 = 175
    # Day 4: 100 + 0.5 * 175 = 100 + 87.5 = 187.5
    # Day 5: 100 + 0.5 * 187.5 = 100 + 93.75 = 193.75
    
    res = adstock_geometric(x, theta)
    x_decayed = res['x_decayed']
    
    assert np.isclose(x_decayed[0], 100)
    assert np.isclose(x_decayed[1], 150)
    assert np.isclose(x_decayed[2], 175)
    assert np.isclose(x_decayed[3], 187.5)
    assert np.isclose(x_decayed[4], 193.75)

def test_adstock_weibull_cdf():
    x = np.array([100, 100, 100, 100, 100])
    shape = 0.5
    scale = 0.5
    # We rely on internal consistency or manually checking R output.
    # Since we ported logic, we verify it runs and produces expected shape.
    
    res = adstock_weibull(x, shape, scale, type="cdf")
    x_decayed = res['x_decayed']
    
    # Basic checks
    assert len(x_decayed) == 5
    assert x_decayed[0] == 100 # First point should be fully itself?
    # Actually wait, for CDF:
    # thetaVec starts with 1.
    # x_decayed[0] = x[0] * thetaVec[0] = 100 * 1 = 100.
    assert np.all(x_decayed >= 0)

def test_adstock_weibull_pdf():
    x = np.array([100, 100, 100, 100, 100])
    shape = 0.5
    scale = 0.5
    
    res = adstock_weibull(x, shape, scale, type="pdf")
    x_decayed = res['x_decayed']
    
    assert len(x_decayed) == 5
    # For PDF, thetaVecCum[0] might not be 1. It is normalized.
    # If shape=0.5, scale=small, max prob might be at 0?
    # If shape < 1, curve peaks at x=0.
    # So idx 0 should be max.
    
    assert np.all(x_decayed >= 0)

def test_saturation_hill():
    x = np.array([100, 150, 170, 190, 200])
    alpha = 3
    gamma = 0.5
    
    # Inflexion = max(x) * gamma = 200 * 0.5 = 100
    # x=100 -> 100^3 / (100^3 + 100^3) = 0.5
    
    res = saturation_hill(x, alpha, gamma)
    x_saturated = res['x_saturated']
    inflexion = res['inflexion']
    
    assert inflexion == 100
    assert np.isclose(x_saturated[0], 0.5)
