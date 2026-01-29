import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import gaussian_kde
import matplotlib as mpl
import os
from cw_constrain.shared.shared_utils import *


def GeV_excess_get_constraints(
    ellip_dist='atnf',
    run='O3',
    search='FH',
    GC_dist=8,  # kpc
    Izz=1e38,
    plot_flag=0,
    sdlim_red_fact=1/0.1,
    lum_func='log-norm',
    msp_min_frot = 60,
    freq_dist='atnf'
):

    msp_min_fgw = 2 * msp_min_frot


    # this_dir = os.path.dirname(__file__)
    # data_path = os.path.join(this_dir, "data", "pulsar_data_atnf_f0_fdots_dist_Bfield_type_age.csv")
    # tbl = pd.read_csv(
    # data_path,
    # sep=';',
    # skiprows=1,
    # engine='python',
    # na_values='*',  # <-- for pandas >= 1.3.0
    # )
    this_dir =  '/Users/andrewmiller/Desktop/O4/o4-gev-excess/'
    data_path = os.path.join(this_dir, "data", "pulsars_filtered_clean.csv")
    tbl = pd.read_csv(
    data_path,
    sep=',',
    skiprows=1,
    engine='python',
    na_values='*',  # <-- for pandas >= 1.3.0
    )
    
    if freq_dist == 'atnf':
        fs_dist = np.array(tbl['(Hz)'].values * 2.)
        fdots_dist = np.array(tbl['(s^-2)'].values)
    else:
        print('user-selected freq dist')
        data_input_freq = os.path.join(this_dir,'data/freq_distributions/')
        fs_dist = np.array(pd.read_csv(data_input_freq+freq_dist,delim_whitespace=True, header=None)[0])

    inds = fs_dist >= msp_min_fgw
    inds1 = tbl['(type)'].notna().values


    log_f_dist = np.log10(fs_dist[inds & inds1])    
    # log_f_dist = np.log10(fs_dist[inds])



    if ellip_dist == 'atnf':
        fs_dist = np.array(tbl['(Hz)'].values * 2.)
        fdots_dist = np.array(tbl['(s^-2)'].values)
        epsilon = calc_eps_sd(fs_dist / 2., fdots_dist / 2., Izz) / sdlim_red_fact
        epsilon = epsilon[inds]
        epsilon = epsilon[epsilon > 0]
        
        log_ellip_dist = np.log10(epsilon)
    elif ellip_dist == 'log10exp':
        lam = sdlim_red_fact
        log_ellip_dist = gen_log10_exp_dist(1e-9, 1e-5, lam)
    elif ellip_dist == 'magnetic':
        pass  # Implement as needed
    elif ellip_dist == 'crustal':
        pass
    elif ellip_dist == 'temperature':
        pass
    else:
        print("user-selected ellipticity distribution")
        data_input_path = os.path.join(this_dir,'data/ellipticity_distributions/')
        ellip_dist = np.array(pd.read_csv(data_input_path+ellip_dist,delim_whitespace=True, header=None)[0])
        ellip_dist = ellip_dist[inds]
        ellip_dist = ellip_dist[ellip_dist > 0]
        log_ellip_dist = np.log10(ellip_dist)


    kde_el = gaussian_kde(log_ellip_dist)
    
    xmesh_el = make_xmesh_matlab_way(min(log_ellip_dist),max(log_ellip_dist))
    
    density_el = kde_el(xmesh_el)
    
    kde_f = gaussian_kde(log_f_dist)
    xmesh_f = make_xmesh_matlab_way(min(log_f_dist),max(log_f_dist))
    density_f = kde_f(xmesh_f)

    fs_UL, h0s_UL = load_cw_search_upper_limits(run, search)
    _, _, _, fdotmax = get_cw_search_parms(run, search)

    all_sky_to_GC_corr_factor = 1.01
    h0s_UL *= all_sky_to_GC_corr_factor

    mask = fs_UL >= msp_min_fgw
    h0s_UL = h0s_UL[mask]
    fs_UL = fs_UL[mask]

    ellip_UL = calc_ellipticity(h0s_UL, fs_UL, GC_dist, Izz)
    valid_freq_mask = xmesh_f >= np.log10(msp_min_fgw)
    ellip_kde = 10**xmesh_el[valid_freq_mask]
    ellip_pdf = density_el[valid_freq_mask]

    f_kde = 10**xmesh_f[valid_freq_mask]
    f_pdf = density_f[valid_freq_mask]

    d_logellip = np.abs(xmesh_el[1] - xmesh_el[0])
    d_logf = np.abs(xmesh_f[1] - xmesh_f[0])
    
    ellip_sum = np.zeros_like(ellip_UL)
    for i, one_ellip in enumerate(ellip_UL):
        ellip_max = calc_ellip_from_f0_fdot(fs_UL[i], fdotmax, Izz)
        mask = (ellip_kde > one_ellip) & (ellip_kde < ellip_max)
        ellip_sum[i] = np.sum(ellip_pdf[mask] * d_logellip)

    index = index_noise_curve(fs_UL, f_kde)
    
    f_selected = f_pdf[index] * d_logf

    
    Pgw = np.dot(ellip_sum, f_selected)

    # print('Pgw: ', Pgw)
    L0, sigmaL, Nmsp = load_luminosity_function(lum_func)
    Ngw = Pgw * Nmsp

    if plot_flag > 2:
        N, edges = np.histogram(log_ellip_dist, bins=50, density=True) ## works diff than in matlab!
        N_f, edges_f = np.histogram(log_f_dist, bins=50, density=True)
        
        plt.figure()
        plt.bar(edges[:-1], N, width=np.diff(edges), color='cyan')
        plt.plot(np.log10(ellip_kde), ellip_pdf, 'k', linewidth=2)
        plt.xlabel('log10 ellipticity')
        plt.ylabel('Probability Density Function')
        plt.grid(True)

        plt.figure()
        plt.bar(edges_f[:-1], N_f, width=np.diff(edges_f), color='blue')
        plt.plot(np.log10(f_kde), f_pdf, 'k', linewidth=2)
        plt.xlabel('log10 frequency (Hz)')
        plt.ylabel('Probability Density Function')
        plt.grid(True)

        plt.figure()
        plt.semilogy(fs_UL, ellip_UL)
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Ellipticity')
        plt.grid(True)

    return L0, sigmaL, Nmsp, Ngw, Pgw


def gen_log10_exp_dist(minellip=1e-9, maxellip=1e-4, lambda_=1, plot_flag=False):
    """
    Generate exponentially distributed samples in log10(ellipticity), truncated.

    Parameters:
    minellip : float
    maxellip : float
    lambda_ : float
    plot_flag : bool

    Returns:
    log10_epsilon : ndarray
    """
    N = 10000
    log10_epsmin = np.log10(minellip)
    log10_epsmax = np.log10(maxellip)

    Fmin = 1 - np.exp(-lambda_ * log10_epsmin)
    Fmax = 1 - np.exp(-lambda_ * log10_epsmax)

    u = np.random.rand(N) * (Fmax - Fmin) + Fmin
    log10_epsilon = -np.log(1 - u) / lambda_

    if plot_flag:
        plt.hist(log10_epsilon, bins=100)
        plt.xlabel('Value')
        plt.ylabel('Count')
        plt.title('Exponentially Distributed Samples (Truncated)')
        plt.show()

    return log10_epsilon




def load_luminosity_function(lum_func_filename):
    """
    Load a predefined or user-specified MSP luminosity function.

    Parameters
    ----------
    lum_func_filename : str
        One of the predefined models: 'log-norm', 'a-gamma', 'b-gamma', 'd-gamma',
        or a custom filename placed in `data/lum_funcs/`.

    Returns
    -------
    L0 : ndarray
        Array of base luminosity values.
    sigmaL : ndarray
        Array of luminosity standard deviations.
    Nmsp : ndarray
        Array of number of MSPs.

    Notes
    -----
    User-supplied files must be placed in: `data/lum_funcs/`.

    File format:
        - Whitespace-delimited (space or tab).
        - No header.
        - 3 columns:
            Column 0: L0 (base luminosity)
            Column 1: sigmaL (log-width or dispersion)
            Column 2: either Nmsp or log10(Nmsp), depending on model
              - For 'log-norm': this is Nmsp directly
              - For others: this is log10(Nmsp)

    Example file contents:
        0.01  0.80  200.0      # if 'log-norm'
        0.10  0.55  2.3010     # if other models
    """
    this_dir = os.path.dirname(__file__)
    data_path = os.path.join(this_dir, "data/lum_funcs/")

    model_files = {
        'log-norm': 'lumin.txt',
        'a-gamma': 'eta-ar.txt',
        'b-gamma': 'eta-br.txt',
        'd-gamma': 'eta-dr.txt'
    }
    if lum_func_filename in model_files:
        filename = model_files[lum_func_filename]
    else:
        filename = lum_func_filename  # assume user provided a file name

    full_path = os.path.join(data_path, filename)

    try:
        lum_func_model = pd.read_csv(full_path, delim_whitespace=True, header=None)
    except FileNotFoundError:
        raise FileNotFoundError(f"Luminosity function file not found: {full_path}")

    if lum_func_model.shape[1] < 3:
        raise ValueError("Input file must have at least 3 columns: L0, sigmaL, Nmsp or log10(Nmsp)")

    L0 = lum_func_model.iloc[:, 0].values
    sigmaL = lum_func_model.iloc[:, 1].values

    if lum_func_filename == 'log-norm' or filename == 'lumin.txt':
        Nmsp = lum_func_model.iloc[:, 2].values
    else:
        Nmsp = 10 ** lum_func_model.iloc[:, 2].values

    return L0, sigmaL, Nmsp




def GeV_plot_exclusions_log_norm(L0,sigmaL,Nmsp,Ngw,N):

    L0s_exc=(L0[Ngw>N])
    L0s_exc_unique=np.unique(L0s_exc)
    sigmaLs_exc=sigmaL[Ngw>N]
    sigmaLs_exc_unique=np.unique(sigmaLs_exc)

    maxL0=np.zeros(len(sigmaLs_exc_unique))


    for i in range(len(sigmaLs_exc_unique)):
        maxL0[i]=np.max(L0s_exc[sigmaLs_exc_unique[i]==sigmaLs_exc])

    fig=plt.figure()
    ax1 = fig.add_subplot()  
    plt.scatter(L0[Ngw<=N],sigmaL[Ngw<=N],c=Nmsp[Ngw<=N],\
                cmap='magma',marker='s',s=10)#,norm=mpl.colors.LogNorm())
    cbar=plt.colorbar(label=r'$N_{\rm MSP}$')
    cbar.set_label(label=r'$N_{\rm MSP}$',size=14,rotation=270,labelpad=20)

    plt.ylabel(r'$\sigma_L$',size=14)
    plt.xlabel(r'$\log_{10}L_0$',size=14)
    plt.fill_between(maxL0, sigmaLs_exc_unique, color='blue', alpha=0.2)
    plt.ylim(np.min(sigmaLs_exc_unique),1)
    plt.tricontourf(L0[Ngw >= N], sigmaL[Ngw >= N], Nmsp[Ngw >= N], levels=[1, np.max(Nmsp)], colors='blue', alpha=0.05)

def GeV_plot_exclusions_gammas(agamma,etamed,Nmsp_agamma,Ngw_agamma,N):
    agamma_exc=(agamma[Ngw_agamma>N])
    agamma_exc_unique=np.unique(agamma_exc)
    etamed_exc=etamed[Ngw_agamma>N]
    etamed_exc_unique=np.unique(etamed_exc)

    fig=plt.figure()
    ax1 = fig.add_subplot()  
    plt.scatter(agamma[Ngw_agamma<N],etamed[Ngw_agamma<N],c=Nmsp_agamma[Ngw_agamma<N],\
                cmap='magma',marker='s',s=10,norm=mpl.colors.LogNorm())

    cbar=plt.colorbar(label=r'$N_{\rm MSP}$')
    cbar.set_label(label=r'$N_{\rm MSP}$',size=14)
    plt.tricontourf(agamma[Ngw_agamma >= N], etamed[Ngw_agamma >= N], Nmsp_agamma[Ngw_agamma >= N], levels=[1, np.max(Nmsp_agamma)], colors='blue', alpha=0.2)

    
def make_xmesh_matlab_way(minimum,maximum,n=2**14):
    Range = maximum - minimum
    MIN=minimum-Range/2
    MAX=maximum+Range/2
    R=MAX-MIN; 
    dx=R/(n-1); 

    xmesh=MIN+np.arange(0,R+dx,dx)
    return xmesh
