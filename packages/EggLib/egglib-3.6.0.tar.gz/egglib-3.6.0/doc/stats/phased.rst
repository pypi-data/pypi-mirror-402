.. _stats_phased:

-----------------------
Phased sites statistics
-----------------------

The following statistics are designed to be computed over a set of
phased sites. If individuals are defined, alleles within individuals
must be phased as well (with the exception of :math:`\bar{r}_d`).

They are computed by :meth:`~.stats.ComputeStats.process_align` and
:meth:`~.stats.ComputeStats.process_sites` of :class:`!ComputeStats`,
as well as :meth:`~.stats.ComputeStats.process_site` in the multiple
site mode, but not :meth:`~.stats.ComputeStats.process_freq`.

+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| Code           | Definition                                                            | Equation    | Requirement | Notes |
+================+=======================================================================+=============+=============+=======+
| ``+phased``    | All statistics from table                                             |             |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``R2``         | Ramos-Onsins and Rozas's :math:`R_2`                                  | :eq:`Rp`    |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``R3``         | Ramos-Onsins and Rozas's :math:`R_3`                                  | :eq:`Rp`    |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``R4``         | Ramos-Onsins and Rozas's :math:`R_4`                                  | :eq:`Rp`    |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``Ch``         | Ramos-Onsins and Rozas's :math:`Ch`                                   | :eq:`Ch`    |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``R2E``        | Ramos-Onsins and Rozas's :math:`R_{2E}`                               |             | Outgroup    | 1     |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``R3E``        | Ramos-Onsins and Rozas's :math:`R_{3E}`                               |             | Outgroup    | 1     |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``R4E``        | Ramos-Onsins and Rozas's :math:`R_{4E}`                               |             | Outgroup    | 1     |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``ChE``        | Ramos-Onsins and Rozas's :math:`Ch_E`                                 |             | Outgroup    | 1     |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``B``          | Wall's *B* statistic                                                  | :eq:`B`     |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``Q``          | Walls *Q* statistic                                                   | :eq:`Q`     |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``Ki``         | Number of haplotypes (only ingroup)                                   |             |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``Kt``         | Total number of haplotypes (including outgroup)                       |             |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``FstH``       | Hudson *et al*'s :math:`F_{ST}`                                       | :eq:`Fst`   | Populations |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``Kst``        | Hudson *et al*'s :math:`K_{ST}`                                       | :eq:`Kst`   | Populations |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``Snn``        | Hudson's nearest nearest neighbour statistic'                         | :eq:`Snn`   | Populations |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``rD``         | :math:`\bar{r}_d` statistic                                           | :eq:`rD`    |             | 2     |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``Rmin``       | Minimal number of recombination events                                |             |             | 3     |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``RminL``      | Number of sites used to compute Rmin                                  |             |             | 3     |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``Rintervals`` | List of start/end positions of recombination intervals                |             |             | 3     |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``nPairs``     | Number of allele pairs used for :math:`Z_{nS}` and related statistics |             |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``nPairsAdj``  | Allele pairs at adjacent sites (used for :math:`ZZ` and :math:`Z_A`)  |             |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``ZnS``        | Kelly *et al.*'s :math:`Z_{nS}`                                       | :eq:`ZnS`   |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``Z*nS``       | Kelly *et al.*'s :math:`Z^*_{nS}`                                     | :eq:`ZsnS`  |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``Z*nS*``      | Kelly *et al.*'s :math:`Z^*_{nS}{}^*`                                 | :eq:`ZsnSs` |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``Za``         | Rozas *et al.*'s :math:`Z_A`                                          | :eq:`ZZ`    |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``ZZ``         | Rozas *et al.*'s :math:`ZZ`                                           | :eq:`ZZ`    |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+
| ``Fs``         | Fu's *F_S*                                                            | :eq:`Fs`    |             |       |
+----------------+-----------------------------------------------------------------------+-------------+-------------+-------+

Notes:

#. Based on mutations on external branches (that is, derived singletons) instead of all singletons.
#. Does not consider the phase of alleles within individuals.
#. The minimal number of recombination events (``Rmin``) is computed after Hudson and Kaplan (*Genetics* 1985 **111**:147-164). Briefly,
   this number of equal to the minimal number of non-overlapping segments defined by incompatible sites (ie breaking the
   three-allele rule). Site with missing data or with more than two alleles are skipped. The number of sites used for this
   analysis and the positions of those intervals are provided as ``RminL`` and ``Rintervals``, respectively.


Ramos-Onsins and Rozas's test statistics
========================================

Ramos-Onsins and Rozas (*Mol. Biol. Evol.* 2002 **19**:2092-2100) develop several
tests of neutrality based on singletons. :math:`R_2`, :math:`R_3`, and :math:`R_4`
are computed as:

.. math::
    R_p = \left[ \frac{1}{n} \sum_i^n \left( S_i - \frac{k}{2} \right) ^ p \right] ^ \frac{1}{p}
    :label: Rp

with:

.. math::
    k = \frac{n}{n-1} \sum_i^S 1 - \sum_j^{k_i} p_{ij} ^2

:math:`n` the number of samples, :math:`S` the number of segregating sites,
:math:`k_i` the number of alleles at site :math:`i`,
:math:`S_i` the number of singletons borne by the :math:`i`\ th sample,
and :math:`p_{ij}` the relative frequency of allele :math:`j` at site :math:`i`.

and :math:`Ch` is computed as:

.. math::
    Ch = (U - k) ^2 \frac{S} {k (S - k)}
    :label: Ch

where :math:`U` is the total number of singletons.

Wall's statistics
=================

Tests based on partitions of the sample defined by polymorphic are defined by Wall (*Genet. Res.* 1999 **74**:65-79):

.. math::
    B = \frac{B'}{S-1}
    :label: B

.. math::
    Q = \frac{B' + n_P}{S}
    :label: Q

where :math:`B'` is defined as the number of pairs of adjacent polymorphic sites (considering only sites
with no missing data and two alleles) that are congruent (that is, for each there is only two haplotypes
considering the pair of sites) and :math:`n_P` is the number of distinct partitions of the sample set
defined by sites (:math:`S` is the number of sites considered in the analysis).

Hudson's differentiation statistics
===================================

Hudson *et al.* (*Mol. Biol. Evol.* 1992 **9**:138-151) haplotype statistics based on Wright's fixation index.

.. math::
    F_{ST} = 1 - \frac{H_W/n_W}{H_B/n_B}
    :label: Fst

.. math::
    K_{ST} = 1 - \frac{K_S}{K_T}
    :label: Kst

with:

.. math::
    H_W = \sum_i^r \frac{2}{n_i(n_i-1)}K_i

.. math::
    H_B = \sum_i^{r-1} \sum_{j=i+1}^r \frac{K_{d_{ij}}}{n_i n_j}

.. math::
    K_S = \frac{1}{n} \sum_i^r n_i \frac{2}{n_i(n_i-1)}K_i

.. math::
    K_T = \frac{1}{2n(n-1)} \left( \sum_i^r K_i + \sum_i^{r-1} \sum_{j=i+1}^r K_{d_{ij}} \right)



where :math:`r` is the number of populations, :math:`n` is the total number of samples,
:math:`n_i` is the number of samples in population :math:`i`,
:math:`K_i` is the sum of the number of pairwise differences between all pairs of samples of population
:math:`i`, :math:`K_{d_{ij}}` is the sum of pairwise differences between all pairs of samples comprising
one sample from population :math:`i` and the other from population :math:`j`,
:math:`n_W` is the number of populations, :math:`n_B` is the number of pairs of populations
(populations with less than two samples are excluded).

Hudson (*Genetics* 2000 **155**:2011-2014) introduced the nearest neighbour statistic. The nearest
neighbour is, for a given sequence :math:`i`, the sequence which has the less pairwise differences
relatively to sequence :math:`i` (excluding itself). There can be several *ex aequo* nearest neighbours.
Then, :math:`X_i` is the proportion of those nearest neighbours which come from the same population
as sequence :math:`i`, and :math:`S_{nn}` is the average of :math:`X_i`:

.. math::
    S_{nn} = \frac{1}{n}\sum_i X_i
    :label: Snn

Standardized association index
==============================

The :math:`\bar{r}_d` statistic has been introduced by Agapow and Burt (*Mol. Ecol. Notes* 2001 **1**:101-102).

.. math::
    \bar{r}_d = \left(V_O - V_E\right)/\left(2 \sum_i^{L-1} \sum_{j=i+1}^L \sqrt{V_i V_j}\right)
    :label: rD

with:

.. math::
    V_O = \frac{1}{n_P} \left( \sum_s^L \sum_i^{n-1} \sum_{j=i+1}^n {d_{sij}}^2 \right)

and:

.. math::
    V_E = \sum_s^L V_s

where the site variance is given, for site :math:`s`, by:

.. math::
    V_s = \frac{2}{n_s(n_s-1)} \left[  \sum_i^{n_s-1} \sum_{j=i+1}^{n_s} {d_{sij}}^2 - \frac{2}{n_s(n_s-1)} \left( \sum_{j=i+1}^{n_s} d_{sij} \right) ^2 \right]

where :math:`L` is the total number of sites considered, :math:`k_{ij}` is the number of sites with available data
for samples :math:`i` and :math:`j`, :math:`n_P` is the number of pairs of samples with :math:`k_{ij}`
greater than 0, :math:`n_s` is the number of samples available at site :math:`s`,
and :math:`d_{sij}` is the number of alleles of the genotype of individual :math:`i` that are not
present in the genotype of individual :math:`j` as site :math:`s`.

Linkage disequilibrium summary statistics
=========================================

Kelly (*Genetics* 1997 **146**:1197-1206) introduced a neutrality statistic based on
pairwise linkage disequilibrium values:

.. math::
    Z_{nS} = \frac{\sum r^2}{n}
    :label: ZnS

Two variants are available:

.. math::
    Z^*_{nS} = Z_{nS} + 1 - \frac{\sum {D'}^2}{n}
    :label: ZsnS

.. math::
    Z^*_{nS}{}^* = Z_{nS} \frac{n}{\sum {D'}^2}
    :label: ZsnSs

Rozas *et al.* (*Genetics* 2001 **158**:1147-1155) introduced the additional statistics :math:`ZZ`:

.. math::
    ZZ = Z_A - Z_{nS}
    :label: ZZ

where :math:`Z_a` is computed as :math:`Z_{nS}` but considering only adjacent polymorphic sites
(that is, pairs of polymorphic sites that don't have a polymorphic site in between).

:math:`n` is the number of allele pairs considered for each statistic.

The sums of :math:`r^2` and of :math:`{D'}^2` are computed over all pairs of sites. For sites with
more than two alleles, the behaviour is controlled by the option *LD_multiallelic*:

* ``ignore``: skip all sites with more than two alleles.
* ``use_main``: use the most frequeny allele.
* ``use_all``: use all possible pairs of alleles.

Linkage disequilibrium statistics are defined :ref:`here <ld>`

Fu's statistic
==============

Fu's :math:`F_S` (*Genetics* 1997 **147**:915-925) is computed as:

.. math::
    F_S = \log{\left(S'\right)} - \log{\left(1-S'\right)}
    :label: Fs

with:

.. math::
    S' = \sum_{k=K}^n \exp {\left[ S_n^k + k \log{(\pi)} - \sum_{i=1}^n \log{(\pi+i-1)} \right]}

where :math:`K` is the number of haplotypes, :math:`n` is the number of
samples used, and :math:`S_n^k` is the Sterling number of the first
kind as computed:

.. math::
    S_n^k = \log{\left( \lvert s_n^k \rvert \right)}

.. math::
    s_n^k = s_{n-1}^{k-1} - (n-1) s_{n-1}^k

:math:`F_S` is not defined if :math:`n` is less than 2.
