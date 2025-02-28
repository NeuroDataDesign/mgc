import numpy as np
from numba import njit
from sklearn.metrics.pairwise import rbf_kernel

from .base import IndependenceTest
from ._utils import _CheckInputs
from . import Dcorr


class Hsic(IndependenceTest):
    r"""
    Class for calculating the Hsic test statistic and p-value.

    Hsic is a kernel based independence test and is a way to measure
    multivariate nonlinear associations given a specified kernel [#1Hsic]_.
    The default choice is the Gaussian kernel, which uses the median distance
    as the bandwidth, which is a characteristic kernel that guarantees that
    Hsic is a consistent test [#1Hsic]_ [#2Hsic]_.

    Parameters
    ----------
    compute_kernel : callable(), optional (default: rbf kernel)
        A function that computes the similarity among the samples within each
        data matrix. Set to `None` if `x` and `y` are already similarity
        matrices. To call a custom function, either create the distance matrix
        before-hand or create a function of the form ``compute_kernel(x)``
        where `x` is the data matrix for which pairwise similarties are
        calculated.

    See Also
    --------
    Dcorr : Distance correlation test statistic and p-value.
    HHG : Heller Heller Gorfine test statistic and p-value.

    Notes
    -----
    The statistic can be derived as follows [#1Hsic]_:

    Let :math:`x` and :math:`y` be :math:`(n, p)` samples of random variables
    :math:`X` and :math:`Y`. Let :math:`K^x` be the :math:`n \times n` kernel
    similarity matrix of :math:`x` and :math:`D^y` be the :math:`n \times n`
    be the kernel similarity matrix of :math:`y`. The Hsic statistic is,

    .. math::

        \mathrm{Hsic}_n (x, y) = \frac{1}{n^2} \mathrm{tr} (K^x H K^y H)

    where :math:`\mathrm{tr} (\cdot)` is the trace operator and :math:`H` is
    defined as :math:`H = I - (1/n) J` where :math:`I` is the identity matrix
    and :math:`J` is a matrix of ones. The normalized version of Hsic
    [#1Dcor]_ and is

    .. math::

        \mathrm{Hsic}_n (x, y) = \frac{\mathrm{Hsic}_n (x, y)}
                                      {\sqrt{\mathrm{Hsic}_n (x, x)
                                             \mathrm{Hsic}_n (y, y)}}

    This version of Hsic is defined using the following centering process
    where :math:`\mathbb{1}(\cdot)` is the indicator
    function:

    .. math::

        C^x_{ij} = \left[ D^x_{ij} - \frac{1}{n-2} \sum_{t=1}^n D^x_{it}
            - \frac{1}{n-2} \sum_{s=1}^n D^x_{sj}
            + \frac{1}{(n-1) (n-2)} \sum_{s,t=1}^n D^x_{st} \right]
            \mathbb{1}_{i \neq j}

    and similarly for :math:`C^y`. Then, this unbiased Dcorr is,

    .. math::

        \mathrm{UHsic}_n (x, y) = \frac{1}{n (n-3)} \mathrm{tr} (C^x C^y)

    The normalized version of this covariance [#2Dcor]_ is

    .. math::

        \mathrm{UHsic}_n (x, y) = \frac{\mathrm{UHsic}_n (x, y)}
                                       {\sqrt{\mathrm{UHsic}_n (x, x)
                                              \mathrm{UHsic}_n (y, y)}}

    References
    ----------
    .. [#1Hsic] Gretton, A., Fukumizu, K., Teo, C. H., Song, L., Schölkopf,
                B., & Smola, A. J. (2008). A kernel statistical test of
                independence. In *Advances in neural information processing
                systems* (pp. 585-592).
    .. [#2Hsic] Gretton, A., & GyĂśrfi, L. (2010). Consistent nonparametric
                tests of independence. *Journal of Machine Learning Research*,
                11(Apr), 1391-1423.
    """

    def __init__(self, compute_kernel=rbf_kernel):
        # set statistic and p-value
        self.stat = None
        self.pvalue = None
        self.compute_kernel = compute_kernel

    def _statistic(self, x, y):
        r"""
        Helper function that calculates the Hsic test statistic.

        Parameters
        ----------
        x, y : ndarray
            Input data matrices. `x` and `y` must have the same number of
            samples. That is, the shapes must be `(n, p)` and `(n, q)` where
            `n` is the number of samples and `p` and `q` are the number of
            dimensions. Alternatively, `x` and `y` can be distance matrices,
            where the shapes must both be `(n, n)`.

        Returns
        -------
        stat : float
            The computed Hsic statistic.
        """

        dcorr = Dcorr(compute_distance=self.compute_kernel)
        stat = dcorr.test(x, y)[0]
        self.stat = stat

        return stat

    def test(self, x, y, reps=1000, workers=-1):
        r"""
        Calculates the Hsic test statistic and p-value.

        Parameters
        ----------
        x, y : ndarray
            Input data matrices. `x` and `y` must have the same number of
            samples. That is, the shapes must be `(n, p)` and `(n, q)` where
            `n` is the number of samples and `p` and `q` are the number of
            dimensions. Alternatively, `x` and `y` can be distance matrices,
            where the shapes must both be `(n, n)`.
        reps : int, optional (default: 1000)
            The number of replications used to estimate the null distribution
            when using the permutation test used to calculate the p-value.
        workers : int, optional (default: -1)
            The number of cores to parallelize the p-value computation over.
            Supply -1 to use all cores available to the Process.

        Returns
        -------
        stat : float
            The computed Hsic statistic.
        pvalue : float
            The computed Hsic p-value.

        Examples
        --------
        >>> import numpy as np
        >>> from mgc.independence import Hsic
        >>> x = np.arange(7)
        >>> y = x
        >>> stat, pvalue = Hsic().test(x, y)
        >>> '%.1f, %.2f' % (stat, pvalue)
        '1.0, 0.00'

        The number of replications can give p-values with higher confidence
        (greater alpha levels).

        >>> import numpy as np
        >>> from mgc.independence import Hsic
        >>> x = np.arange(7)
        >>> y = x
        >>> stat, pvalue = Hsic().test(x, y, reps=10000)
        >>> '%.1f, %.2f' % (stat, pvalue)
        '1.0, 0.00'

        In addition, the inputs can be distance matrices. Using this is the,
        same as before, except the ``compute_kernel`` parameter must be set
        to ``None``.

        >>> import numpy as np
        >>> from mgc.independence import Hsic
        >>> x = np.ones((10, 10)) - np.identity(10)
        >>> y = 2 * x
        >>> hsic = Hsic(compute_kernel=None)
        >>> stat, pvalue = hsic.test(x, y)
        >>> '%.1f, %.2f' % (stat, pvalue)
        '1.0, 1.00'

        """

        dcorr = Dcorr(compute_distance=self.compute_kernel)
        stat, pvalue = dcorr.test(x, y, reps=reps, workers=workers)
        self.stat = stat
        self.pvalue = pvalue

        return stat, pvalue
