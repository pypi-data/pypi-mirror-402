# Translating the MATLAB functions into Python equivalents.
import numpy as np
from astropy import constants as const
from astropy import units
from cw_constrain.shared.shared_utils import *


def pbh_get_constraints(m1=2.5, run='O3', search='FH', lin_flag=1, Mcs=None):
    # Constants
    sec_to_year = units.yr.to(units.s)
    n = 11 / 3  # braking index
    age_of_univ = 13.6e9  # years
    cutoff_time = (age_of_univ / 10) * sec_to_year  # seconds

    if Mcs is None:
        Mcs = np.logspace(-7, -4, 50)

    Tobs = get_Tobs_OX(run)
    Tobs_yr = Tobs / sec_to_year

    fs_UL, h0s_UL = load_cw_search_upper_limits(run, search)
    fs_UL = np.array(fs_UL, dtype=float)
    h0s_UL = np.array(h0s_UL, dtype=float)

    # Clean up non-physical data
    valid = (h0s_UL > 0) & (h0s_UL < 1)
    fs_UL = fs_UL[valid]
    h0s_UL = h0s_UL[valid]

    fmin, fmax, fdotmin, fdotmax = get_cw_search_parms(run, search)
    if run == 'O3' and search == 'FH':
        fdotmax = np.abs(fdotmin)
    delta_f = fdotmax * Tobs

    interp_fs = np.arange(np.min(fs_UL), np.max(fs_UL), delta_f)
    h0s_UL_interp = np.interp(interp_fs, fs_UL, h0s_UL)
    fs_UL = interp_fs
    h0s_UL = h0s_UL_interp

    tffts_interp = get_cw_search_TFFTs(run, search, fs_UL)
    rate_model_indep = np.zeros(len(Mcs))
    rate_model_indep_asymm = np.zeros(len(Mcs))
    ftilde_equal = np.zeros(len(Mcs))
    m22 = np.zeros(len(Mcs))
    ftilde_asymm = np.zeros(len(Mcs))

    fmaxes = power_law(Tobs, fs_UL, fdotmax, n)

    for kk, Mc in enumerate(Mcs):
        dists = calc_chirp_d(h0s_UL, Mc, fs_UL)
        fdots = calc_fdot_chirp(Mc, fmaxes)
        allowed_indices_fdot = fdots <= fdotmax

        # Equal-mass case
        mtot_equal = 2 ** (6 / 5) * Mc
        fisco_equal = calc_f_isco(mtot_equal)
        linear_inds,_ = is_fevol_linear(Tobs, fs_UL, fdots, tffts_interp, n)
        if lin_flag == 0:
            linear_inds = np.ones_like(fs_UL, dtype=bool)

        delta_T = calc_delta_T(Mc, fs_UL, fmaxes)
        delta_T_isco_equal = calc_delta_T(Mc, fs_UL, fisco_equal)
        inds_allowed_times_equal = delta_T_isco_equal < cutoff_time

        allowed_dists = dists[allowed_indices_fdot & inds_allowed_times_equal & linear_inds]
        allowed_times = delta_T[allowed_indices_fdot & inds_allowed_times_equal & linear_inds] / sec_to_year
        allowed_times[allowed_times < Tobs_yr] = Tobs_yr

        rate_model_indep[kk] = calc_rate_VT(allowed_dists, allowed_times)
        ftilde_equal[kk] = calc_ftilde_equal_mass(rate_model_indep[kk], mtot_equal)

        # Asymmetric-mass case
        m2 = (Mc / m1 ** (2 / 5)) ** (5 / 3)
        m22[kk] = m2
        fisco_asymm_mass = calc_f_isco(m1)
        delta_T_isco_asymm = calc_delta_T(Mc, fs_UL, fisco_asymm_mass)
        inds_allowed_times_asymm = delta_T_isco_asymm < cutoff_time

        allowed_dists_asymm = dists[allowed_indices_fdot & inds_allowed_times_asymm &
                                    (fs_UL < fisco_asymm_mass) & linear_inds]
        allowed_times_asymm = delta_T[allowed_indices_fdot & inds_allowed_times_asymm &
                                      (fs_UL < fisco_asymm_mass) & linear_inds] / sec_to_year
        allowed_times_asymm[allowed_times_asymm < Tobs_yr] = Tobs_yr

        rate_model_indep_asymm[kk] = calc_rate_VT(allowed_dists_asymm, allowed_times_asymm)
        ftilde_asymm[kk] = calc_ftilde_asymm_mass(rate_model_indep_asymm[kk], m1, m2)

    return rate_model_indep, Mcs, ftilde_equal, ftilde_asymm, m22


def calc_chirp_d(h0, Mc, f):
    c = const.c.value  # m/s
    G = const.G.value  # m^3/kg/s^2
    Msun = const.M_sun.value
    kpc_to_m = const.kpc.value


    Mc *= Msun
    d = 4.0 / h0 * (G * Mc / c**2)**(5/3) * (np.pi * f / c)**(2/3)
    return d / kpc_to_m

import numpy as np
import warnings

def power_law(times, f0, fdot0, n):
    pow_ = n - 1
    kn = fdot0 / f0**n
    kconst = kn * pow_ * f0**pow_

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        if n != 1:
            if n == 11/3:
                f_of_t = f0 * (1 - kconst * times)**(-1.0 / pow_)
            else:
                f_of_t = f0 * (1 + kconst * times)**(-1.0 / pow_)
        else:
            f_of_t = f0 * np.exp(-kn * times)

    return f_of_t


def calc_f_isco(mtot):
    return 2 * 2200 * (1.0 / mtot)

def is_fevol_linear(tt, f0, fdot0, TFFT, n, num_bins=1):
    flins = f_taylor(tt, f0, fdot0)
    fpls = power_law(tt, f0, fdot0, n)
    df = np.abs(flins - fpls)
    df_fft = 1.0 / TFFT
    is_linear = df < (df_fft * num_bins)
    return is_linear, df

def calc_delta_T(Mc, fs_UL, fmaxes):
    c = const.c.value
    G = const.G.value
    Msun = const.M_sun.value
    Delta_f = fs_UL**(-8/3) - fmaxes**(-8/3)
    return (5 / 256) * np.pi**(-8/3) * (c**3 / (G * Mc * Msun))**(5/3) * Delta_f

def calc_rate_VT(dists, delta_T, times=1):
    dists_cubed = dists**3
    summation_term = np.sum(dists_cubed * delta_T * times**(-34/37))
    
    if summation_term == 0:
        return np.inf
    else:
        return 3 / (4 * np.pi * summation_term)

def calc_ftilde_equal_mass(rate_density, Mtot):
    prefact_equal = 1.9e-6
    Mterm = (Mtot / 1)**(-32/37)
    return (rate_density / (Mterm * prefact_equal))**(37/53)

def calc_ftilde_asymm_mass(rate_density, m1, m2):
    prefact_asymm = 5.3e-7
    m1_term = (m1 / 1)**(-32/37)
    m2_term = (m2 / m1)**(-34/37)
    return (rate_density / (m1_term * m2_term * prefact_asymm))**(37/53)

def f_taylor(times, f0, fdot0, fddot0=0, fdddot0=0):
    """
    Taylor series expansion of the frequency evolution (up to 3rd derivative).

    Parameters:
    - times: np.ndarray or float, times at which to evaluate the frequency (s)
    - f0: float, initial frequency (Hz)
    - fdot0: float, first derivative of frequency (Hz/s)
    - fddot0: float, second derivative of frequency (Hz/s^2) (optional)
    - fdddot0: float, third derivative of frequency (Hz/s^3) (optional)

    Returns:
    - fs: np.ndarray or float, frequency at given times (Hz)
    """

    times = np.asarray(times)
    fs = (
        f0
        + fdot0 * times
        + (fddot0 / 2) * times**2
        + (fdddot0 / 6) * times**3
    )
    return fs


def calc_fdot_chirp(mc, fgw):
    """
    Calculates spin-up of a chirping gravitational-wave signal, eqn. 2
    
    Parameters:
    - mc: chirp mass in solar masses (float or array-like)
    - fgw: gravitational-wave frequency in Hz (float or array-like)
    
    Returns:
    - fdot: spin-up (Hz/s)
    """
    mc_kg = mc * const.M_sun.value
    G = const.G.value
    c = const.c.value
    term1 = (G * mc_kg / c**3)**(5/3)
    fdot = (96/5) * np.pi**(8/3) * term1 * fgw**(11/3)
    
    return fdot




# Usage:
# consts = Constants()

