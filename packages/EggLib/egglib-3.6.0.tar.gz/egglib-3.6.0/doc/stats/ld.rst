.. _ld:

----------------------
Linkage disequilibrium
----------------------

Linkage disequilibrium statistics are computed by two methods,
:func:`.stats.pairwise_LD` and :func:`.stats.matrix_LD`.

The available statistics are:

The statistics listed in the table below are available as methods or
attributes of this class. The documentation provides more information
regarding the usage.

.. table::
    :widths: 5 15 5 5

    +---------+---------------------------------+----------+-----------+
    | Code    | Statistic                       | Equation | Reference |
    +=========+=================================+==========+===========+
    | ``D``   | Standard linkage disequilibrium | :eq:`D`  | 1         |
    +---------+---------------------------------+----------+-----------+
    | ``Dp``  | Lewontin's :math:`D'`           | :eq:`Dp` | 2         |
    +---------+---------------------------------+----------+-----------+
    | ``r``   | Correlation coefficient         | :eq:`r2` | 3         |
    +---------+---------------------------------+----------+-----------+
    | ``rsq`` | Correlation coefficient         | :eq:`r2` | 3         |
    +---------+---------------------------------+----------+-----------+

**Reference**

#. Lewontin and Kojima (*Evolution* 1960 **14**:458-472).
#. Lewontin (*Genetics* 1964 **49**:49-67).
#. Hill and Robertson (*Theor. Appl. Genet.* 1968 **38**:226-231).

To compute linkage disequilibrium statistics, we assume pair of alleles at two different
sites that are respectively at relative frequencies :math:`p_1` and :math:`p_2` while the genotype
constituted by the two alleles is at frequency :math:`p_{12}`. The standard linkage disequilibrium
is:

.. math::
    D = p_{12} - p_1 p_2
    :label: D

The standardized linkage disequilibrum is computed as:

.. math::
    D' = \frac{D}{k}
    :label: Dp

where:

* :math:`k = p_1 p_2` if :math:`D` < 0 and :math:`p_1 p_2 < (1-p_1) (1-p_2)`,
* :math:`k = (1-p_1) (1-p_2)` if :math:`D` < 0 and :math:`p_1 p_2 \ge (1-p_1) (1-p_2)`,
* :math:`k = p_1 (1-p_2)` if :math:`D` > 0 and :math:`p_1 (1-p_2) < (1-p_1) p_2`, and
* :math:`k = (1-p_1) p_2` otherwise.

Finally, the pairwise correlation coefficient :math:`r^2`
is computed as follows:

.. math::
    r^2 = \left( \frac{D}{\sqrt{p_1 p_2 (1-p_1) (1-p_2)}}  \right) ^2
    :label: r2
