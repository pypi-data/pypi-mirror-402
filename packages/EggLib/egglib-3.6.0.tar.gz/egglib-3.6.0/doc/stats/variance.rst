.. _stats_allelesize:

----------------------
Allele size statistics
----------------------

The following statistics make use of the allele size. They are available
from :meth:`~.stats.ComputeStats` (all methods), but require that an
alphabet with alleles coded as integers is provided. The allele values
are interpreted as allele sizes (even if negative values are found: in
that case it is assumed that allele sizes are shifted).

+-----------------+-----------------------------+-----------+
| Code            | Definition                  | Equation  |
+=================+=============================+===========+
| ``+allelesize`` | All statistics from table   |           |
+-----------------+-----------------------------+-----------+
| ``V``           | Allele size variance        | :eq:`V`   |
+-----------------+-----------------------------+-----------+
| ``Ar``          | Allele range                | :eq:`Ar`  |
+-----------------+-----------------------------+-----------+
| ``M``           | Garza and Williamson\'s *M* | :eq:`M`   |
+-----------------+-----------------------------+-----------+
| ``Rst``         | Slatkin\'s :math:`R_{ST}`   | :eq:`Rst` |
+-----------------+-----------------------------+-----------+

If :math:`k` is the number of alleles, :math:`A_i` if the size of allele
:math:`i`, :math:`p_i` is the frequency of this allele and
:math:`n = \sum p_i` is the number of samples, the allele size variance
is computed as a sample variance:

.. math::
    V = \frac{n}{n-1} \left[ \frac{1}{n} \sum_i^k p_i {A_i}^2 - \left( \frac{1}{n} \sum_i^k p_i A_i \right) ^2 \right]
    :label: V

The allele range is simply:

.. math::
    A_R = \max(A_i) - \min(A_i)
    :label: Ar

Garza and Williamson's :math:`M` (*Mol. Ecol.* 2001 **10**:305-318) is
computed as:

.. math::
    M = \frac{k}{A_R+1}
    :label: M

Finally, Slatkin's :math:`R_{ST}` (*Genetics* 1995 **139**:457-462) is
computed as shown below, considering only samples from populations with
at least 2 samples. Note that when computing the value for several
sites the value of :math:`R_{ST}` is computed as the ratio of the sums
of the different terms (rather than the average of the per-site values).
:math:`\bar{V}` is the average of within-population allele size variance.

.. math::
    R_{ST} = 1 - \frac{\bar{V}} {V}
    :label: Rst

