import numpy as np
import pandas as pd

from cw_constrain.shared.shared_utils import *

consts = Constants()
rhodm = consts.rhodm      # in eV/m^3
h = consts.h              # Planck's constant
eps0 = consts.eps0        # Vacuum permittivity
c = consts.c              # Speed of light
hbar = consts.hbar        # Reduced Planck's constant
ev = consts.ev            # Electron charge in Coulombs
mp = 0.93827e9;           #eV; mass of proton
conversion = 1.9733e-16   # m = 1/GeV
rhodm_in_ev4 = rhodm * conversion**3 * (1e9)**3  # (1e9)^3
ev_to_inv_m = consts.units['ev_to_inv_m']


def sb_get_constraint_from_h0s(fs, h0s, run='O3', detector='LLO',path_LLO=None,path_LHO=None):
    """
    Calculates the coupling strength (lambda inv) from a dilaton signal amplitude (h0).
    
    Parameters
    ----------
    fs : float or np.ndarray
        signal frequency (Hz).
    h0s : float or np.ndarray
        Signal amplitude (Delta L / L).
    detector : string
        which detector ('LHO','LLO', anything else if you want to use both LHO and LLO Acals)
    path_LLO: path to Acal for LLO
    path_LHO: path to Acal for LHO

    Returns
    -------
    epsilon : float or np.ndarray
        Coupling strength (dimensionless).
    """

    # Load calibration tables
    if run == 'O3':
        if path_LHO is None:
            path_LHO = '~/Desktop/dp_searches/O4/O3_Amp_Cal_LHO.txt'
        if path_LLO is None:
            path_LLO = '~/Desktop/dp_searches/O4/O3_Amp_Cal_LLO.txt'

        T_LHO = pd.read_csv(path_LHO, delim_whitespace=True)
        T_LLO = pd.read_csv(path_LLO, delim_whitespace=True)
        fcal = T_LHO['Freq_o'].to_numpy()
        Acal_LHO = T_LHO['Amp_Cal_LHO'].to_numpy()
        Acal_LLO = T_LLO['amp_cal_LLO'].to_numpy()

    elif run == 'O4a':
        if path_LHO is None:
            path_LHO = '~/Desktop/O4/Scalar-Dark-Matter-LPSD/O4a_results/Amp_Cal_LHO.txt'
        if path_LLO is None:
            path_LLO = '~/Desktop/O4/Scalar-Dark-Matter-LPSD/O4a_results/Amp_Cal_LLO.txt'

        T_LHO = pd.read_csv(path_LHO, delim_whitespace=True, comment='#', names=["Frequency", "Amplitude"])
        T_LLO = pd.read_csv(path_LLO, delim_whitespace=True, comment='#', names=["Frequency", "Amplitude"])
        fcal = T_LHO['Frequency'].to_numpy()
        Acal_LHO = T_LHO['Amplitude'].to_numpy()
        Acal_LLO = T_LLO['Amplitude'].to_numpy()
    else:
        raise ValueError(f"Unknown run: {run}")

    # Choose calibration factor
    if detector == 'LLO':
        Acal = Acal_LLO
    elif detector == 'LHO':
        Acal = Acal_LHO
    else:
        Acal = (Acal_LHO + Acal_LLO) / 2

    # Convert DM density to eV^4 units
    

    ms = dm_calc_m(fs)  # boson mass in eV
    index = index_noise_curve(fs, fcal)

    LHS = h0s * Acal[index]
    RHS = np.sqrt(2 * rhodm_in_ev4) / ms

    Lambda_i_inv = LHS / RHS  # in eV^-1
    Lambda_i_Gev_inv = Lambda_i_inv * 1e9  # in GeV^-1

    return Lambda_i_Gev_inv



def dp_calc_eps_from_h0(m, h0, v0=0.000766667):
    """
    Calculates the coupling strength (epsilon) from a dark photon signal amplitude (h0).
    
    Parameters
    ----------
    m : float or np.ndarray
        Dark photon mass in eV.
    h0 : float or np.ndarray
        Signal amplitude (Delta L / L).
    v0 : float
        Virial velocity over c (unitless) or velocity in m/s.

    Returns
    -------
    epsilon : float or np.ndarray
        Coupling strength (dimensionless).
    """
    
    geo_avg = 2/9
    # Convert proton mass to kg
    mp_kg = mp * ev / c**2
    q_over_M = 1 / mp_kg      # Could be 1/(2M) for B-L coupling

    # Convert energy density to J/m^3
    rhodm_J = rhodm * ev

    # Convert dark photon mass to kg
    m_kg = m * ev / c**2

    # Compute wavevector k
    if v0 < 1:
        k = 2 * np.pi * m_kg * v0 * c / h
    else:
        k = 2 * np.pi * m_kg * v0 / h

    denominator = hbar**2 * k * ev * np.sqrt(2 * rhodm_J) * q_over_M
    numerator = m_kg**2 * c**4 * np.sqrt(eps0)

    epsilon = ( h0 / np.sqrt(geo_avg)) * numerator / denominator # Eq. A4 in 10.1103/PhysRevLett.121.061102

    return epsilon


def tb_get_constraint_from_h0s(fs, h0s):
    """
    Computes the upper bound on the coupling strength alpha
    from strain amplitude h0s for tensor boson dark matter.
    
    Parameters
    ----------
    fs : np.ndarray
        Array of frequencies (Hz).
    h0s : np.ndarray
        Corresponding array of strain amplitudes.
    
    Returns
    -------
    alpha : np.ndarray
        Constraint on coupling alpha (dimensionless).
    """
    conversion = 1.9733e-16     # m = 1/GeV
    # ev / m^3 --> ev^4
    rhodm_in_ev_to_the_4 = rhodm * conversion**3 * (1e9)**3

    # Planck mass
    Mp = 1.2209e19              # GeV (natural units)

    Mp_reduced = Mp / np.sqrt(8 * np.pi)

    # boson mass in eV
    ms = dm_calc_m(fs)          

    # Eq. (2.4) of arXiv:2012.13997
    alpha = (
        np.sqrt(2)
        * ms
        * (Mp_reduced * 1e9)
        / np.sqrt(rhodm_in_ev_to_the_4)
        * h0s
    )

    alpha = alpha / 2
    return alpha


def dm_calc_m(f0):
    """
    Convert frequency f0 (in Hz) to mass m (in eV) for dark photon.

    Parameters:
    - f0: float or array-like
        Frequency in Hz

    Returns:
    - m: float or ndarray
        Mass in eV
    """

    m = f0 * hbar * 2 * np.pi / ev
    return m

def dm_calc_f0(m):
    """
    Convert frequency f0 (in Hz) to mass m (in eV) for dark photon.

    Parameters:
    - f0: float or array-like
        Frequency in Hz

    Returns:
    - m: float or ndarray
        Mass in eV
    """
    f0 = m * ev/(hbar * 2 * np.pi) 
    return f0

def dp_finite_travel_factor(mA, detector='ligo', v0=0.000766667):
    """
    Calculates the factor of improvement in both epsilon and epsilon^2
    upper limits due to finite travel time effects.

    Based on: https://arxiv.org/abs/2011.03589

    Parameters
    ----------
    mA : float or np.ndarray
        Dark photon mass in eV (can be array of shape N x 1)
    detector : str
        Detector name: 'ligo' (default), 'lisa', 'et', 'ce', or 'decigo'
    v0 : float
        Dark matter velocity in m/s (default: 230e3/3e8 = 7.66667e-3)

    Returns
    -------
    fact_eps : np.ndarray
        Factor of improvement in epsilon
    fact_eps2 : np.ndarray
        Factor of improvement in epsilon^2
    """
    # Detector parameters
    if detector == 'ligo':
        L = 4000  # m
        ndotm = 0
    elif detector == 'lisa':
        L = 2.5e9
        ndotm = 0.5
    elif detector == 'et':
        L = 1e4
        ndotm = 0.5
    elif detector == 'ce':
        L = 4e4
        ndotm = 0.5
    elif detector == 'decigo':
        L = 1e6
        ndotm = 0.5
    else:
        raise ValueError(f"Unknown detector: {detector}")


    # Normalize v0 to units of c if needed
    if v0 > 1:
        v0 = v0 / c

    # Convert dark photon mass from eV to inverse meters
    mA = np.asarray(mA) * ev_to_inv_m

    # Eqns (23) and (24) in the paper
    ndotm_fact = (1 - ndotm) / (1 - ndotm**2)

    fact_h1_sq_over_h2_sq = (
        12 / (mA**2 * L**2 * v0**2)
        * np.sin(mA * L / 2)**4
        * ndotm_fact
    )

    # Eq under heading "Advanced LIGO O1"
    fact_eps = np.sqrt(1 + fact_h1_sq_over_h2_sq)

    return fact_eps

