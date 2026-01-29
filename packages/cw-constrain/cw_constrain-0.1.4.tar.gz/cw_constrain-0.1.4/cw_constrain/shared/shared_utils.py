
import numpy as np
from astropy import constants as const
from astropy import units
import os
from pathlib import Path

def get_Tobs_OX(run):
    """
    Returns the observation time Tobs in seconds for a given observing run.

    Parameters:
    - run (str): Name of the observing run ('O2', 'O3a', 'O3', or 'O4a').

    Returns:
    - float: Observation time in seconds.
    """
    if run == 'O2':
        Tobs = 268.37 * 86400
    elif run == 'O3a':
        Tobs = 250 * 86400 / 2
    elif run == 'O3':
        Tobs = 361 * 86400  # 2019 April 1 to 27 March 2020
    elif run == 'O4a':
        duty_cycle = 0.7
        Tobs = 237 * 86400 * duty_cycle
    else:
        raise ValueError(f"Unknown run name: {run}")
    
    return Tobs


import os
import numpy as np

def load_cw_search_upper_limits(run, search):
    fs_UL = []
    h0s_UL = []
    data_path = os.environ.get("CW_CONSTRAIN_LIMITS_PATH")
    if data_path is None:
        raise RuntimeError("Please set the CW_CONSTRAIN_LIMITS_PATH environment variable.")

    def check_file_exists(fname):
        if not os.path.exists(fname):
            raise FileNotFoundError(
                f"Could not find file: {fname}\n"
                "Hint: Is CW_CONSTRAIN_LIMITS_PATH set correctly?"
            )
        return fname

    if search == 'FH':
        if run == 'O2':
            fname = os.path.join(data_path, 'FH_95UL.txt')
            check_file_exists(fname)
            with open(fname, 'r') as fid:
                A = [line.split() for line in fid]
                fs_UL = [float(row[0]) for row in A]
                h0s_UL = [float(row[1]) for row in A]
        elif run == 'O3':
            fname = os.path.join(data_path, 'O3_FH_UL.txt')
            check_file_exists(fname)
            with open(fname, 'r') as fid:
                A = [line.split() for line in fid]
                fs_UL = [float(row[0]) for row in A]
                h0s_UL = [float(row[1]) for row in A]
        elif run == 'O4a':
            fname = os.path.join(data_path, 'f_vs_h0min_o4a_FH.txt')
            check_file_exists(fname)
            with open(fname, 'r') as fid:
                A = [line.split() for line in fid]
                fs_UL = [float(row[0]) for row in A]
                h0s_UL = [float(row[1]) for row in A]

    elif search == 'powerflux':
        if run == 'O3a':
            fname = os.path.join(data_path, 'Downloads/csv files/o3a_ul_all_simplified.csv')
            check_file_exists(fname)
            A = np.loadtxt(fname, delimiter=',', skiprows=1)
            fs_UL = A[:, 0]
            h0s_UL_circ = A[:, 8]
            h0s_UL = h0s_UL_circ * 2.30
        elif run == 'O4a':
            fname = os.path.join(data_path, 'uls_powerflux_popave_O4a.txt')
            check_file_exists(fname)
            with open(fname, 'r') as fid:
                A = [line.split() for line in fid]
                fs_UL = [float(row[0]) for row in A]
                h0s_UL = [float(row[1]) for row in A]

    elif search == 'SOAP':
        if run == 'O4a':
            fname = os.path.join(data_path, 'o4a_limits_SOAP.txt')
            check_file_exists(fname)
            with open(fname, 'r') as fid:
                A = [line.split() for line in fid if not line.strip().startswith('#')]
                fs_UL = [float(row[0]) for row in A]
                h0s_UL = [float(row[1]) for row in A]

    if run == 'O4a' and search == 'SOAP':
        return np.array(fs_UL), 10**(np.array(h0s_UL))
    else:
        return np.array(fs_UL), np.array(h0s_UL)


def get_cw_search_parms(run, search):
    if search == 'FH':
        if run == 'O3':
            fmin, fmax = 20, 2048
        elif run == 'O4a':
            fmin, fmax = 20, 1024
        fdotmin = -1e-8
        fdotmax = 2e-9

    elif search == 'powerflux':
        fmin, fmax = 20, 2000
        fdotmin = -1e-8
        fdotmax = 1e-9

    elif search == 'SOAP':
        fmin, fmax = 20, 2000
        fdotmin = -1e-8
        fdotmax = 1e-8

    return fmin, fmax, fdotmin, fdotmax

def get_cw_search_TFFTs(run, search, fs_UL):
    """
    Determine TFFT values for continuous wave (CW) search based on run, search type, and frequency upper limits.

    Parameters:
    - run (str): Observing run ('O2', 'O3', 'O4a').
    - search (str): Search method ('FH', 'powerflux', 'SOAP').
    - fs_UL (array-like): Frequency upper limits (Hz).

    Returns:
    - np.ndarray: TFFT values corresponding to fs_UL.
    """
    fs_UL = np.asarray(fs_UL)
    TFFTs = np.zeros_like(fs_UL, dtype=int)

    if search == 'FH':
        if run in ['O2', 'O3']:
            fmax_db1 = 128
            fmax_db2 = 512
            fmax_db3 = 1024

            TFFTs[fs_UL <= fmax_db1] = 8192
            TFFTs[(fs_UL > fmax_db1) & (fs_UL <= fmax_db2)] = 4096
            TFFTs[(fs_UL > fmax_db2) & (fs_UL <= fmax_db3)] = 2048
            TFFTs[fs_UL > fmax_db3] = 1024

        elif run == 'O4a':
            TFFTs,_,_ = calc_TFFT_doppler(fs_UL)

    elif search == 'powerflux':
        fmax_db1 = 475
        fmax_db2 = 1475

        TFFTs[fs_UL <= fmax_db1] = 7200
        TFFTs[(fs_UL > fmax_db1) & (fs_UL <= fmax_db2)] = 3600
        TFFTs[fs_UL > fmax_db2] = 1800

    elif search == 'SOAP':
        if run == 'O4a':
            TFFTs[:] = 1800

    return TFFTs


def calc_TFFT_doppler(f0):
    """
    Calculate TFFT and sky resolution deltas from Doppler modulation.

    Parameters:
    - f0 (array-like): Frequencies in Hz

    Returns:
    - tuple of np.ndarray: TFFT (s), deltaLambda (rad), deltaBeta (rad)
    """
    consts = Constants()
    f0 = np.asarray(f0)
    vorb = consts.v_earth_orb
    c_val = const.c.value
    Rorb = consts.Rorb

    TFFT = np.sqrt(Rorb * c_val / vorb**2) * np.sqrt(1. / f0)
    ND = calc_ND(f0, TFFT)

    beta_GC = np.deg2rad(-5.6)  # galactic center declination in radians

    deltaLambda = 1. / (ND * np.cos(beta_GC))
    deltaBeta = 1. / (ND * np.sin(beta_GC))

    deg_sq_area = np.abs(np.rad2deg(deltaLambda) * np.rad2deg(deltaBeta))
    return TFFT, deltaLambda, deltaBeta

def calc_ND(f0, tfft):
    """
    Calculate number of Doppler bins.

    Parameters:
    - f0 (array-like): Frequencies in Hz
    - tfft (array-like): FFT durations in seconds

    Returns:
    - np.ndarray: Nd values
    """
    consts = Constants()
    vorb = consts.v_earth_orb

    v_over_c = vorb / const.c.value
    f0 = np.asarray(f0)
    tfft = np.asarray(tfft)

    Nd = f0 * v_over_c * tfft
    return Nd



class Constants:
    def __init__(self):
        self.c = const.c.value  # speed of light (m/s)
        self.h = const.h.value  # Planck constant (J s)
        self.hbar = self.h / (2 * np.pi)
        
        self.ev = const.e.value  
        
        self.Msun = const.M_sun.value  # Solar mass in kg
        self.G = const.G.value  # Gravitational constant (m^3 kg^-1 s^-2)
        self.eps0 = const.eps0.value  # Vacuum permittivity (F/m)
        
        self.fine_struct = const.alpha.value 
        
        sday = units.sday.to(units.s)
        
        self.f_earth = 1 / sday  
        
        # Stellar day length in seconds (given value)
        self.StellarDay = sday
        
        # Angular frequency of Earth's orbit (radians per second)
        self.omega_earth_orb = 2 * np.pi / units.yr.to(units.s)  # orbital period in seconds
        
        # Angular frequency of Earth's rotation
        self.omega_earth_rot = 2 * np.pi * self.f_earth
        
        # Earth radius in meters (from astropy)
        self.R_earth = const.R_earth.value
        
        # Earth orbital radius (semi-major axis) in meters (hardcoded)
        self.Rorb = 149597871e3
        
        # Speeds relative to speed of light
        self.v0 = 0.000766667  # relative to c
        self.vesc = 0.00181459  # relative to c
        
        # Dark matter energy density in eV/m^3 (as given)
        self.rhodm = 0.4e9 / 1e-6  
        
        # Earth surface rotation speed (m/s)
        self.v_earth_rot = self.omega_earth_rot * self.R_earth
        
        # Earth orbital speed (m/s)
        self.v_earth_orb = self.omega_earth_orb * self.Rorb
        
        # Units conversion factors
        self.units = {}
        self.units['ev_to_inv_s'] = self.ev / self.hbar
        self.units['ev_to_inv_m'] = self.ev / (self.hbar * self.c)
        self.units['ev_to_kg'] = self.ev / self.c**2
        self.units['kg_to_ev'] = self.c**2 / self.ev
        self.units['charge_LH'] = self.ev / np.sqrt(4 * np.pi * self.fine_struct)
        self.units['charge_G'] = self.ev / np.sqrt(self.fine_struct)
        self.units['pc_to_m'] = const.pc.value
        self.units['kpc_to_m'] = const.kpc.value
        self.units['mpc_to_m'] = const.pc.value * 1e6


def index_noise_curve(fsss, det_freq):
    """
    Find index of closest frequency match between detector and array.

    Parameters:
    fsss : array-like
    det_freq : array-like

    Returns:
    index : ndarray of indices
    """
    
#     fsss = np.asarray(fsss)
#     det_freq = np.asarray(det_freq)
#     index = np.argmin(np.abs(fsss[:, None] - det_freq), axis=0)
#     return index
    index = []
    for i in range(len(fsss)):
        ii = np.argmin(np.abs(fsss[i]-det_freq))
        index.append(ii)
    return index

def calc_ellipticity(h00, f, d=8, Iz=1e38):
    """
    Compute ellipticity from strain amplitude h0, frequency, and distance.

    Parameters:
    h00 : array-like
    f : array-like (Hz)
    d : float (kpc)
    Iz : float (kg*m^2)

    Returns:
    ellip : ndarray
    """
    pi = np.pi
    c = const.c.value
    G = const.G.value
    kpc_to_m = const.kpc.value

    d_m = d * kpc_to_m
    ellip = h00 / ((4 * pi**2 * G / c**4) * Iz * f**2 / d_m)
    return ellip

def calc_ellip_from_f0_fdot(f0, fdot, Izz=1e38):
    """
    Compute ellipticity from f0 and fdot.

    Parameters:
    f0 : array-like (Hz)
    fdot : array-like (Hz/s)
    Izz : float (kg*m^2)

    Returns:
    ellip : ndarray
    """
    pi = np.pi
    c = const.c.value
    G = const.G.value

    ellip = np.sqrt(np.abs(fdot) * 5 * c**5 / (32 * pi**4 * G * Izz * f0**5))
    return ellip

def calc_eps_sd(freqs, fdots, I=1e38):
    """
    Compute ellipticity from spin-down frequency and frequency derivative.

    Parameters:
    freqs : array-like
        Rotational frequencies (Hz)
    fdots : array-like
        Rotational frequency derivatives (Hz/s)
    I : float
        Moment of inertia (kg*m^2), default is 1e38

    Returns:
    epsilon : ndarray
        Ellipticity values
    """
    pi = np.pi
    c = const.c.value  # m/s
    G = const.G.value  # m^3/kg/s^2
    
    prefact = (1 / (16 * pi**2)) * np.sqrt(5 / 2)
    factor = np.sqrt(c**5 * np.abs(fdots) / (G * I * freqs**5))
    epsilon = prefact * factor
    return epsilon
