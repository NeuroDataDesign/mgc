import pytest
import numpy as np
from numpy.testing import assert_almost_equal, assert_warns, assert_raises

from ...benchmarks.indep_sim import linear
from .. import Hsic


class TestHsicStat:
    @pytest.mark.parametrize("n", [10, 100, 1000])
    @pytest.mark.parametrize("obs_stat", [1.0])
    @pytest.mark.parametrize("obs_pvalue", [1/1000])
    def test_linear_oned(self, n, obs_stat, obs_pvalue):
        np.random.seed(123456789)
        x, y = linear(n, 1, noise=0)
        stat, pvalue = Hsic().test(x, y)

        assert_almost_equal(stat, obs_stat, decimal=2)
        assert_almost_equal(pvalue, obs_pvalue, decimal=2)

class TestHsicErrorWarn:
    """ Tests errors and warnings derived from MGC.
    """
    def test_error_notndarray(self):
        # raises error if x or y is not a ndarray
        x = np.arange(20)
        y = [5] * 20
        assert_raises(ValueError, Hsic().test, x, y)
        assert_raises(ValueError, Hsic().test, y, x)

    def test_error_shape(self):
        # raises error if number of samples different (n)
        x = np.arange(100).reshape(25, 4)
        y = x.reshape(10, 10)
        assert_raises(ValueError, Hsic().test, x, y)

    def test_error_lowsamples(self):
        # raises error if samples are low (< 3)
        x = np.arange(3)
        y = np.arange(3)
        assert_raises(ValueError, Hsic().test, x, y)

    def test_error_nans(self):
        # raises error if inputs contain NaNs
        x = np.arange(20, dtype=float)
        x[0] = np.nan
        assert_raises(ValueError, Hsic().test, x, x)

        y = np.arange(20)
        assert_raises(ValueError, Hsic().test, x, y)

    def test_error_wrongdisttype(self):
        # raises error if compute_distance is not a function
        x = np.arange(20)
        compute_kernel = 1
        hsic = Hsic(compute_kernel=compute_kernel)
        assert_raises(ValueError, hsic.test, x, x)

    @pytest.mark.parametrize("reps", [
        -1,    # reps is negative
        '1',   # reps is not integer
    ])
    def test_error_reps(self, reps):
        # raises error if reps is negative
        x = np.arange(20)
        assert_raises(ValueError, Hsic().test, x, x, reps=reps)

    def test_warns_reps(self):
        # raises warning when reps is less than 1000
        x = np.arange(20)
        reps = 100
        assert_warns(RuntimeWarning, Hsic().test, x, x, reps=reps)
