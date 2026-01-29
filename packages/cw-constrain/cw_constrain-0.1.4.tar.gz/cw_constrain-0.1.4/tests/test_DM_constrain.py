import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import numpy as np
import pandas as pd
import pytest
from cw_constrain.DM_constrain.dm_constrain import (
    dp_calc_eps_from_h0,
    tb_get_constraint_from_h0s,
    dm_calc_m,
    dm_calc_f0,
    dp_finite_travel_factor,
    sb_get_constraint_from_h0s
)

def test_dm_calc_m_and_f0_inverse():
    freq = 100.0  # Hz
    mass = dm_calc_m(freq)
    recovered_freq = dm_calc_f0(mass)
    assert np.allclose(freq, recovered_freq, rtol=1e-10)

def test_dp_calc_eps_from_h0_scalar():
    epsilon = dp_calc_eps_from_h0(m=1e-12, h0=1e-23)
    assert np.isscalar(epsilon)
    assert epsilon > 0

def test_tb_get_constraint_from_h0s_positive():
    freqs = np.array([100.0])
    h0s = np.array([1e-24])
    alpha = tb_get_constraint_from_h0s(freqs, h0s)
    assert alpha.shape == freqs.shape
    assert alpha[0] > 0

def test_dp_finite_travel_factor_scalar():
    factor = dp_finite_travel_factor(mA=1e-12, detector='ligo')
    assert np.isscalar(factor)
    assert factor > 1

def test_dp_finite_travel_factor_array():
    m_vals = np.logspace(-13, -10, 5)
    factors = dp_finite_travel_factor(m_vals, detector='ligo')
    assert factors.shape == m_vals.shape
    assert np.all(factors > 1)

def test_sb_get_constraint_from_h0s_with_dummy_calibration(tmp_path):
    # Create dummy calibration data
    df = pd.DataFrame({
        'Freq_o': [50, 100, 200],
        'Amp_Cal_LHO': [1.0, 2.0, 3.0],
        'amp_cal_LLO': [1.1, 2.1, 3.1],
    })
    path_LHO = tmp_path / "O3_Amp_Cal_LHO.txt"
    path_LLO = tmp_path / "O3_Amp_Cal_LLO.txt"
    df.to_csv(path_LHO, sep=' ', index=False)
    df.to_csv(path_LLO, sep=' ', index=False)

    fs = np.array([100.0])
    h0s = np.array([1e-24])
    result = sb_get_constraint_from_h0s(fs, h0s, run='O3', detector='LLO',
                                        path_LHO=str(path_LHO),
                                        path_LLO=str(path_LLO))
    assert result.shape == fs.shape
    assert result[0] > 0

