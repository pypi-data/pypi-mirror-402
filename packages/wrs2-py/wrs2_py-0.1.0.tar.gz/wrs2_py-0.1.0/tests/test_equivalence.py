
import json
import numpy as np
import pytest
from wrs2_py import (
    winvar, winmean, winvarN, trim_mean, pbos,
    wincor, pbcor,
    t1way, t2way, bwtrim, rmanova,
    yuen, yuenbt, trimse
)

def load_test_data():
    with open("tests/test_comparison_data.json", "r") as f:
        return json.load(f)

def test_location():
    data = load_test_data()
    x = np.array(data["input_data"]["x"])
    
    assert np.allclose(winvar(x), data["winvar"], atol=1e-7)
    assert np.allclose(winmean(x), data["winmean"], atol=1e-7)
    assert np.allclose(winvarN(x), data["winvarN"], atol=1e-7)
    assert np.allclose(trim_mean(x), data["trim_mean"], atol=1e-7)
    assert np.allclose(pbos(x), data["pbos"], atol=1e-7)

def test_correlation():
    data = load_test_data()
    x = np.array(data["input_data"]["x"])
    y = np.array(data["input_data"]["y"])
    
    wc = wincor(x, y)
    assert np.allclose(wc["cor"], data["wincor"]["cor"], atol=1e-7)
    assert np.allclose(wc["cov"], data["wincor"]["cov"], atol=1e-7)
    
    pbc = pbcor(x, y)
    assert np.allclose(pbc["cor"], data["pbcor"]["cor"], atol=1e-7)
    assert np.allclose(pbc["test"], data["pbcor"]["test"], atol=1e-7)
    assert np.allclose(pbc["p_value"], data["pbcor"]["p.value"], atol=1e-7)

def test_t1way():
    data = load_test_data()
    groups = [np.array(g) for g in data["input_data"]["groups_t1"]]
    
    res = t1way(groups)
    assert np.allclose(res["test"], data["t1way"]["test"], atol=1e-7)
    assert np.allclose(res["df1"], data["t1way"]["df1"], atol=1e-7)
    assert np.allclose(res["df2"], data["t1way"]["df2"], atol=1e-7)
    assert np.allclose(res["p_value"], data["t1way"]["p_value"], atol=1e-7)
    # effsize might differ slightly due to bootstrapping randomness in R vs Python if not seeded the same
    # but let's check if it's close
    assert np.allclose(res["effsize"], data["t1way"]["effsize"], atol=0.1)

def test_yuen():
    data = load_test_data()
    g1 = np.array(data["input_data"]["g1"])
    g2 = np.array(data["input_data"]["g2"])
    
    res = yuen(g1, g2)
    assert np.allclose(res["test"], data["yuen"]["test"], atol=1e-7)
    assert np.allclose(res["p_value"], data["yuen"]["p_value"], atol=1e-7)
    assert np.allclose(res["df"], data["yuen"]["df"], atol=1e-7)
    assert np.allclose(res["diff"], data["yuen"]["diff"], atol=1e-7)
    assert np.allclose(res["effsize"], data["yuen"]["effsize"], atol=0.1)

def test_t2way():
    data = load_test_data()
    groups = [np.array(g) for g in data["input_data"]["t2way_groups"]]
    
    res = t2way(groups, J=2, K=2)
    assert np.allclose(res["Qa"], data["t2way"]["Qa"], atol=1e-7)
    assert np.allclose(res["Qb"], data["t2way"]["Qb"], atol=1e-7)
    assert np.allclose(res["Qab"], data["t2way"]["Qab"], atol=1e-7)
    assert np.allclose(res["A_p_value"], data["t2way"]["A_p_value"], atol=1e-3)
    assert np.allclose(res["B_p_value"], data["t2way"]["B_p_value"], atol=1e-3)
    assert np.allclose(res["AB_p_value"], data["t2way"]["AB_p_value"], atol=1e-3)

def test_rmanova():
    data = load_test_data()
    rm_data = np.array(data["input_data"]["rm_data"])
    
    res = rmanova(rm_data)
    assert np.allclose(res["test"], data["rmanova"]["test"], atol=1e-7)
    assert np.allclose(res["df1"], data["rmanova"]["df1"], atol=1e-7)
    assert np.allclose(res["df2"], data["rmanova"]["df2"], atol=1e-7)
    assert np.allclose(res["p_value"], data["rmanova"]["p_value"], atol=1e-7)

def test_bwtrim():
    data = load_test_data()
    # reconstruct groups
    # In generate_test_data.R, I saved bw_groups which is a list of J groups, each being a (n_j, K) array?
    # No, I saved list(rm_data[1:10, 1:3], rm_data[11:20, 1:3])
    groups = [np.array(g) for g in data["input_data"]["bw_groups"]]
    
    res = bwtrim(groups)
    assert np.allclose(res["Qa"], data["bwtrim"]["Qa"], atol=1e-7)
    assert np.allclose(res["Qb"], data["bwtrim"]["Qb"], atol=1e-7)
    assert np.allclose(res["Qab"], data["bwtrim"]["Qab"], atol=1e-7)
    # p-values should also be close
    assert np.allclose(res["A_p_value"], data["bwtrim"]["A_p_value"], atol=1e-5)
    assert np.allclose(res["B_p_value"], data["bwtrim"]["B_p_value"], atol=1e-5)
    assert np.allclose(res["AB_p_value"], data["bwtrim"]["AB_p_value"], atol=1e-5)

def test_yuenbt():
    data = load_test_data()
    g1 = np.array(data["input_data"]["g1"])
    g2 = np.array(data["input_data"]["g2"])
    
    # Bootstrap test results may vary slightly due to random sampling, 
    # but the test statistic and difference should be identical.
    res = yuenbt(g1, g2, nboot=500)
    assert np.allclose(res["test"], data["yuenbt"]["test"], atol=1e-7)
    assert np.allclose(res["diff"], data["yuenbt"]["diff"], atol=1e-7)
    # p-value might differ slightly, but should be in the same ballpark
    assert abs(res["p_value"] - data["yuenbt"]["p_value"]) < 0.05
