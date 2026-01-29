import numpy as np
import os
from cw_constrain.PBH_constrain.pbh_constrain import pbh_get_constraints


os.environ["CW_CONSTRAIN_LIMITS_PATH"] = "/Users/andrewmiller/Desktop/O4/limits/"

def test_pbh_get_constraints_output_shapes_and_values():
    # Use a short list of chirp masses for a fast test
    test_Mcs = np.logspace(-6, -5, 5)

    rate_model, Mcs_out, ftilde_equal, ftilde_asymm, m22 = pbh_get_constraints(
        m1=2.5,
        run='O4a',
        search='powerflux',
        lin_flag=1,
        Mcs=test_Mcs
    )

    # Check that outputs are numpy arrays of the same length
    N = len(test_Mcs)
    assert isinstance(rate_model, np.ndarray)
    assert isinstance(Mcs_out, np.ndarray)
    assert isinstance(ftilde_equal, np.ndarray)
    assert isinstance(ftilde_asymm, np.ndarray)
    assert isinstance(m22, np.ndarray)

    assert len(rate_model) == N
    assert len(Mcs_out) == N
    assert len(ftilde_equal) == N
    assert len(ftilde_asymm) == N
    assert len(m22) == N

    # Basic sanity checks: positive rates and ftilde
    assert np.all(rate_model >= 0)
    assert np.all(ftilde_equal >= 0)
    assert np.all(ftilde_asymm >= 0)
    assert np.all(m22 > 0)

