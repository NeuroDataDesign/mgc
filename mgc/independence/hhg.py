import numpy as np
from numba import njit

from .._utils import euclidean, check_xy_distmat
from .base import IndependenceTest
from ._utils import _CheckInputs


class HHG(IndependenceTest):
    r"""
    Class for calculating the HHG test statistic and p-value.

    This is a powerful test for independence based on calculating pairwise
    euclidean distances and associations between these distance matrices. The
    test statistic is a function of ranks of these distances, and is
    consistent against similar tests [#1HHG]_. It can also operate on multiple
    dimensions [#1HHG]_.

    Parameters
    ----------
    compute_distance : callable(), optional (default: euclidean)
        A function that computes the distance among the samples within each
        data matrix. Set to `None` if `x` and `y` are already distance
        matrices. To call a custom function, either create the distance matrix
        before-hand or create a function of the form ``compute_distance(x)``
        where `x` is the data matrix for which pairwise distances are
        calculated.

    See Also
    --------
    Dcorr : Distance correlation test statistic and p-value.
    Hsic : Hilbert-Schmidt independence criterion test statistic and p-value.

    Notes
    -----
    The statistic can be derived as follows [#1HHG]_:

    Let :math:`x` and :math:`y` be :math:`(n, p)` samples of random variables
    :math:`X` and :math:`Y`. For every sample :math:`j \neq i`, calculate the
    pairwise distances in :math:`x` and :math:`y` and denote this as
    :math:`d_x(x_i, x_j)` and :math:`d_y(y_i, y_j)`. The indicator function is
    denoted as :math:`\mathbb{1} \{ \cdot \}`. The cross-classification
    between these two random variables can be calculated as

    .. math::

        A_{11} = \sum_{k=1, k \neq i,j}^n
                    \mathbb{1} \{ d_x(x_i, x_k) \leq d_x(x_i, x_j) \}
                    \mathbb{1} \{ d_y(y_i, y_k) \leq d_y(y_i, y_j) \}

    and :math:`A_{12}`, :math:`A_{21}`, and :math:`A_{22}` are defined
    similarly. This is organized within the following table:

    +--------------------------------------------+--------------------------------------------+--------------------------------------------+---------------------------+
    |                                            | :math:`d_x(x_i, \cdot) \leq d_x(x_i, x_j)` | :math:`d_x(x_i, \cdot) \leq d_x(x_i, x_j)` |                           |
    +--------------------------------------------+--------------------------------------------+--------------------------------------------+---------------------------+
    | :math:`d_x(x_i, \cdot) \leq d_x(x_i, x_j)` | :math:`A_{11} (i,j)`                       | :math:`A_{12} (i,j)`                       | :math:`A_{1 \cdot} (i,j)` |
    +--------------------------------------------+--------------------------------------------+--------------------------------------------+---------------------------+
    | :math:`d_x(x_i, \cdot) > d_x(x_i, x_j)`    | :math:`A_{21} (i,j)`                       | :math:`A_{22} (i,j)`                       | :math:`A_{2 \cdot} (i,j)` |
    +--------------------------------------------+--------------------------------------------+--------------------------------------------+---------------------------+
    |                                            | :math:`A_{\cdot 1} (i,j)`                  | :math:`A_{\cdot 2} (i,j)`                  | :math:`n - 2`             |
    +--------------------------------------------+--------------------------------------------+--------------------------------------------+---------------------------+

    Here, :math:`A_{\cdot 1}` and :math:`A_{\cdot 2}` are the column sums,
    :math:`A_{1 \cdot}` and :math:`A_{2 \cdot}` are the row sums, and
    :math:`n - 2` is the number of degrees of freedom. From this table, we can
    calculate the Pearson's chi squared test statistic using,

    .. math::

        S(i, j) = \frac{(n-2) (A_{12} A_{21} - A_{11} A_{22})^2}
                       {A_{1 \cdot} A_{2 \cdot} A_{\cdot 1} A_{\cdot 2}}

    and the HHG test statistic is then,

    .. math::

        \mathrm{HHG}_n (x, y) = \sum_{i=1}^n \sum_{j=1, j \neq i}^n S(i, j)

    References
    ----------
    .. [#1HHG] Heller, R., Heller, Y., & Gorfine, M. (2012). A consistent
               multivariate test of association based on ranks of distances.
               *Biometrika*, 100(2), 503-510.
    """

    def __init__(self, compute_distance=euclidean):
        self.is_distance = False
        if not compute_distance:
            self.is_distance = True

        IndependenceTest.__init__(self, compute_distance=compute_distance)

    def _statistic(self, x, y):
        r"""
        Helper function that calculates the HHG test statistic.

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
            The computed HHG statistic.
        """

        distx = x
        disty = y

        if not self.is_distance:
            distx = self.compute_distance(x)
            disty = self.compute_distance(y)

        stat = _hhg(distx, disty)

        self.stat = stat

        return stat

    def test(self, x, y, reps=1000, workers=-1):
        r"""
        Calculates the HHG test statistic and p-value.

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
            The computed HHG statistic.
        pvalue : float
            The computed HHG p-value.

        Examples
        --------
        >>> import numpy as np
        >>> from mgc.independence import HHG
        >>> x = np.arange(7)
        >>> y = x
        >>> stat, pvalue = HHG().test(x, y)
        >>> '%.1f, %.2f' % (stat, pvalue)
        '160.0, 0.00'

        The number of replications can give p-values with higher confidence
        (greater alpha levels).

        >>> import numpy as np
        >>> from mgc.independence import HHG
        >>> x = np.arange(7)
        >>> y = x
        >>> stat, pvalue = HHG().test(x, y, reps=10000)
        >>> '%.1f, %.2f' % (stat, pvalue)
        '160.0, 0.00'

        In addition, the inputs can be distance matrices. Using this is the,
        same as before, except the ``compute_distance`` parameter must be set
        to ``None``.

        >>> import numpy as np
        >>> from mgc.independence import HHG
        >>> x = np.ones((10, 10)) - np.identity(10)
        >>> y = 2 * x
        >>> hhg = HHG(compute_distance=None)
        >>> stat, pvalue = hhg.test(x, y)
        >>> '%.1f, %.2f' % (stat, pvalue)
        '0.0, 1.00'

        """

        check_input = _CheckInputs(x, y, dim=2, reps=reps,
                                   compute_distance=self.compute_distance)
        x, y = check_input()

        if self.is_distance:
            check_xy_distmat(x, y)

        return super(HHG, self).test(x, y, reps, workers)


@njit
def _hhg(distx, disty):                                                     # pragma: no cover
    """Calculate the HHG test statistic"""

    n = distx.shape[0]
    S = np.zeros((n, n))

    # iterate over all samples in the distance matrix
    for i in range(n):
        for j in range(n):
            if i != j:
                a = distx[i, :] <= distx[i, j]
                b = disty[i, :] <= disty[i, j]

                t11 = np.sum(a * b) - 2
                t12 = np.sum(a * (1 - b))
                t21 = np.sum((1 - a) * b)
                t22 = np.sum((1 - a) * (1 - b))

                denom = (t11+t12) * (t21+t22) * (t11+t21) * (t12+t22)
                if denom > 0:
                    S[i, j] = ((n-2) * (t12*t21 - t11*t22) ** 2) / denom

    stat = np.sum(S)

    return stat
