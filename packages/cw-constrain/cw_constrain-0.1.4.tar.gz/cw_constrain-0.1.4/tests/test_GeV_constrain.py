import numpy as np
import os
# Import your function (adjust the import path as needed)
from cw_constrain.GeV_constrain.gev_constrain import GeV_excess_get_constraints

os.environ["CW_CONSTRAIN_LIMITS_PATH"] = "/Users/andrewmiller/Desktop/O4/limits/"

def test_GeV_excess_basic_run():
    # Run the function with default parameters
    L0, sigmaL, Nmsp, Ngw, Pgw = GeV_excess_get_constraints()

    # Check output types — allow numpy arrays or floats where applicable
    assert isinstance(L0, (float, np.floating, np.ndarray))
    assert isinstance(sigmaL, (float, np.floating, np.ndarray))
    assert isinstance(Nmsp, (int, np.floating,np.ndarray))
    assert isinstance(Ngw, (float, np.floating, np.ndarray))
    assert isinstance(Pgw, (float, np.floating, np.ndarray))

    # Basic sanity checks on outputs (not NaN, not inf)
    assert not np.any(np.isnan(L0))
    assert not np.any(np.isnan(sigmaL))
    assert np.all(Nmsp > 0)
    assert not np.any(np.isnan(Ngw))
    assert not np.isnan(Pgw)
    assert Pgw >= 0


def test_GeV_excess_with_different_ellip_dist():
    # Try the 'log10exp' option for ellip_dist
    L0, sigmaL, Nmsp, Ngw, Pgw = GeV_excess_get_constraints(ellip_dist='log10exp')
    assert Pgw >= 0

def test_GeV_excess_with_plot_flag(monkeypatch):
    # Patch plt.show to avoid rendering plots during test
    import matplotlib.pyplot as plt
    monkeypatch.setattr(plt, "show", lambda *args, **kwargs: None)

    # Call with plot_flag > 2 to trigger plotting code
    L0, sigmaL, Nmsp, Ngw, Pgw = GeV_excess_get_constraints(plot_flag=3)
    assert Pgw >= 0

def test_GeV_excess_with_diff_lims():
    L0, sigmaL, Nmsp, Ngw, Pgw = GeV_excess_get_constraints(run='O4a',search='FH')
    assert Pgw >=0 
