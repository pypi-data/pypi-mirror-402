.. _stats_unphased:

-------------------------
Unphased sites statistics
-------------------------

The following statistics are designed to be computed over a set of sites
but do not require that the sites are phased. Most of them are applicable
to an alignment of DNA sequences (or for a set of single-nucleotide
polymorphism markers).

They are computed by :meth:`~.stats.ComputeStats.process_align` and
:meth:`~.stats.ComputeStats.process_sites` of :class:`!ComputeStats`,
as well as :meth:`~.stats.ComputeStats.process_freq` and
:meth:`~.stats.ComputeStats.process_site` in the multiple site mode.

+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| Code          | Definition                                                | Equation    | Requirement     | Notes |
+===============+===========================================================+=============+=================+=======+
| ``+unphased`` | All statistics from table                                 |             |                 |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``nseff``     | Average number of exploitable samples                     |             |                 |  1    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``lseff``     | Number of analysed sites                                  |             |                 |  2    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``nsmax``     | Maximal number of available samples per site              |             |                 |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``S``         | Number of segregating sites                               |             |                 |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``Ss``        | Number of sites with one singleton allele                 |             |                 |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``eta``       | Minimal number of mutations                               |             |                 |  3    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``sites``     | Polymorphic sites                                         |             |                 |  5    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``singl``     | Sites with one singleton allele                           |             |                 |  5    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``nall``      | Number of alleles per polymorphic site                    |             |                 |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``frq``       | Allelic frequencies per polymorphic site                  |             |                 |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``frqp``      | Population allelic frequencies per polymorphic site       |             |                 |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``thetaW``    | Watterson's estimator of :math:`\theta`                   | :eq:`tW`    |                 |  4    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``Pi``        | Nucleotide diversity                                      | :eq:`Pi`    |                 |  4    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``lseffo``    | Number of analysed orientable sites                       |             | Outgroup        |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``nseffo``    | Average number of exploitable samples at orientable sites |             | Outgroup        |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``nsmaxo``    | Maximal number of available samples per orientable site   |             | Outgroup        |  2    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``sites_o``   | Orientable polymorphic sites                              |             | Outgroup        |  5    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``singl_o``   | Orientable sites with one singleton allele                |             | Outgroup        |  5    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``So``        | Number of segregating orientable sites                    |             | Outgroup        |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``Sso``       | Number of orientable sites with one singleton allele      |             | Outgroup        |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``nsingld``   | Number of sites with one derived singleton allele         |             | Outgroup        |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``etao``      | Minimal number of mutations are orientable sites          |             | Outgroup        |  3    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``D``         | Tajima's *D*                                              | :eq:`Dtaj`  |                 |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``Deta``      | Tajima's *D* using ``eta`` instead of ``S``               | :eq:`Deta`  |                 |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``Dfl``       | Fu and Li's *D*                                           | :eq:`Dfl`   | Outgroup        |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``F``         | Fu and Li's *F*                                           | :eq:`F`     | Outgroup        |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``D*``        | Fu and Li's *D**                                          | :eq:`Dstar` |                 |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``F*``        | Fu and Li's *F**                                          | :eq:`Fstar` |                 |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``nM``        | Number of sites used for the MFDM test                    |             | Outgroup        |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``pM``        | P-value of MDFM test                                      | :eq:`pM`    | Outgroup        |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``thetaPi``   | Pi using orientable sites                                 | :eq:`tP`    | Outgroup        |  4    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``thetaH``    | Fay and Wu's estimator of :math:`\theta`                  | :eq:`tH`    | Outgroup        |  4    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``thetaL``    | Zeng et al.'s estimator of :math:`\theta`                 | :eq:`tL`    | Outgroup        |  4    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``Hns``       | Fay and Wu's *H* (unstandardized)                         | :eq:`Hns`   | Outgroup        |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``Hsd``       | Fay and Wu's *H* (standardized)                           | :eq:`Hsd`   | Outgroup        |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``E``         | Zeng et al.'s *E*                                         | :eq:`E`     | Outgroup        |       |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``Dxy``       | Pairwise distance                                         | :eq:`Dxy`   | Two populations |  6    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+
| ``Da``        | Net pairwise distance                                     | :eq:`Da`    | Two populations |  6    |
+---------------+-----------------------------------------------------------+-------------+-----------------+-------+

Notes:

#. The number of exploitable samples may vary between sites due to missing
   data.
#. Number of sites considered for polymorphism detection, after discarding
   sites with too many missing data in the case of the method
   :meth:`!process_align` (controlled by the parameter *max_missing*).
   Sites with less than two non-missing samples are always discarded.
#. This value is properly computed even if sites with more than two alleles
   are excluded.
#. Provided per gene (must be divided by ``lseff`` or ``lseffo`` to be
   expressed per site). 
#. Returned as a :class:`!list` containing the index of all concerned sites.
#. Only computed if there are two populations exactly.

Level of diversity
==================

The so-called Watterson's estimator of :math:`\theta` (``theta_W``)
is mentioned in Watterson (*Theor. Popul. Biol.* 1975, **7**:256-276).

.. math::
    \hat{\theta}_{W} = \frac{S}{\sum_i^{n-1}\frac{1}{i}}
    :label: tW

where *n* is equal to nseff rounded to the closest integer.

Nucleotide diversity (``Pi``) is given by:

.. math::
    \pi = \sum_i \left[ (1 - \sum_j {p_{i,j}}^2) \frac{n_i} {(n_i-1)} \right]
    :label: Pi

where :math:`p_{i,j}` is the relative frequency of allele *j* at site *i*
and :math:`n_i` is the number of exploitable samples at site *i*.

Tajima's D
==========

Tajima's *D* (*Genetics* 1989 **123**:585-595) is computed as follows:

.. math::
    D = \frac{\pi - \hat{\theta}_W} {\sqrt{V(\pi - \hat{\theta}_W)}}
    :label: Dtaj

where the variance is computed as follows:

.. math::
    a_1 = \sum_i^{n-1} \frac{1}{i}

.. math::
    a_2 = \sum_i^{n-1} \frac{1}{i^2}

.. math::
    b_1 = \frac{n+1} {3 * (n-1)}

.. math::
    b_2 = \frac{2(n^2 + n + 3)} {9 n (n-1)}

.. math::
    c_1 = b_1 - \frac{1}{a_1}

.. math::
    c_2 = b_2 - \frac{n+2} {a_1 n} + \frac{a_2}{{a_1}^2}

.. math::
    e_1 = \frac{c_1}{a_1}

.. math::
    e_2 = \frac{c_2}{{a_1}^2 + a_2}

.. math::
    V(\pi - \hat{\theta}_W) = e_1 S + e_2 S (S-1)

A variant is available where :math:`\eta` (the minimal number of mutation)
is used instead of :math:`S`:

.. math::
    D = \frac{\pi - \eta/a_1} {\sqrt{V(\pi - \eta/a_1)}}
    :label: Deta

with:

.. math::
    V(\pi - \eta/a_1) = e_1 \eta + e_2 \eta (\eta-1)

Fu and Li's tests with an outgroup
==================================

Fu and Li (*Genetics* 1993 **133**:693-709) proposed alternatives to
Tajima's *D* computed as follows:

.. math::
    D = \frac{\eta - a_1 \eta_e} {\sqrt{u_D \eta + v_D \eta ^2}}
    :label: Dfl

and

.. math::
    F = \frac{\sum H_{e_i} - \eta_e} {\sqrt{u_F \eta + v_F \eta ^2}}
    :label: F

where :math:`\eta` is the minimal number of mutations at orientable sites,
:math:`\eta_e` is the total number of singletons at orientable sites,
and :math:`H_{e_i}` is the heterozygosity at site :math:`i`.

.. math::
    c_n = \frac{2 [n a_1 - 2 (n - 1)]} {(n - 1) (n - 2)}

(If :math:`n` is equal to 2, :math:`c_n` is set to 1.)

.. math::
    v_D = 1 + \frac{{a_1}^2} {b_n + {a_1}^2} \left( c_n - \frac{n + 1} {n - 1} \right)

.. math::
    u_D = a_1 - 1 - v_D

The variance for *F* is computed as follows:

.. math::
    v_F = \frac{1}{{a_1}^2 + b_n} \left[c_n + \frac{2 (n^2 + n + 3)}{9 n (n-1)}
                - \frac{2}{n-1} \right]

.. math::
    u_F = \frac{1}{a_1} \left[ 1 + \frac{n+1} {3 (n-1)}
           - 4 \frac{n+1}{(n-1)^2}
                    \left( a_1 + \frac{1}{n} - \frac{2n}{n+1} \right) \right] - v_F

Variables are computed as for Tajima's *D* but considering only orientable sites.

Fu and Li's tests without outgroup
==================================

The following tests don't require an outgroup:

.. math::
    D* = \frac{\frac{n} {n-1} \eta - a_1 \eta_e} {\sqrt{u_D \eta + v_D \eta ^ 2}}
    :label: Dstar

.. math::
    F* = \frac{\pi - (n - 1) \frac{\eta_e}{n}} {\sqrt{u_F \eta + v_F \eta^2}}
    :label: Fstar

.. math::
    c_n = \frac{2 [n a_1 - 2 (n - 1)]} {(n - 1) (n - 2)}

.. math::
    d_n = c_n + \frac{n-2} {(n-1)^2} + \frac{2} {n-1} \left[ \frac{3}{2} - \frac{2 (a_1 + \frac{1}{n})-3} {n-2} - \frac{1}{n} \right]

.. math::
    v_D = \frac{\frac{n^2} {(n-1)^2} a_2 + {a_1}^2 d_n - a_1 (a_1+1) \frac{2n} {(n-1)^2}} {{a_1}^2 + a_2}

.. math::
    u_D = \frac{n} {n-1} \left( a_1 - \frac{n} {n-1} \right) - v_D

.. math::
    v_F = \frac{1}{{a_1}^2+a_2} \left[ \frac{2n^3 + 110n^2 - 255n + 153}
              {9n^2(n-1)}
                    + \frac{2(n-1)a_1}{n^2} - \frac{8a_2}{n} \right]

.. math::
    u_F = \frac{1}{a_1} \frac{4n^2 + 19n + 3 - 12(n+1)(a_1+\frac{1}{n})}{3n(n-1)} - v_F

:math:`n` is ``nseff`` rounded to unity as for Tajima's *D*, :math:`\eta_e` is
the total number of singletons.
Expressions for :math:`v_F` and :math:`u_F` are given by Simonsen *et al.* (*Genetics* 1995 **141**:413-429).

MFDM test
=========

The P-value of the MFDM (maximum frequency of derived mutation) test
(Li *Mol. Biol. Evol.* 2011 **28**:365-375) is computed as follows:

.. math::
    P = \min_i \left( 2 \frac{n_i - \max_j{d_{i,j}}}{n_i - 1} \right)
    :label: pM

where :math:`n_i` is the number of available samples at site *i* and
:math:`d_{i,j}` is the absolute frequency of the derived allele *j*, assuming
that its frequency is more than half of the sample.
If no site has a derived allele most frequent than half of the sample,
the P-value is set to 1. If no site has a derived allele at least as frequent
as half of the sample, the P-value is undefined.

Neutrality tests with an outgroup
=================================

Statistics defined by Fay and Wu (*Genetics* 2000 **155**:1405-1413) and
Zeng *et al.* (*Genetics* 2006 **174**:1431-1439).

Three additional :math:`\theta` estimators are defined based on orientable sites:

.. math::
    \hat{\theta}_\pi = \frac{2}{n_{max}(n_{max}-1)} \sum_i^{n_{max}} i (n_{max}-1) S_i
    :label: tP

.. math::
    \hat{\theta}_H = \frac{2}{n_{max}(n_{max}-1)} \sum_i^{n_{max}} i^2 S_i
    :label: tH

.. math::
    \hat{\theta}_L = \frac{1}{n_{max}-1} \sum_i^{n_{max}} i S_i
    :label: tL


where :math:`n_{max}` is the maximal number of exploitable samples over
orientable sites, and :math:`S_i` is the number of derived alleles
(aggregating all alleles from all considered sites) which have been
found in *i* copies.

The following test statistics are defined. First, the non-standardized
*H* statistic of Fay and Wu:

.. math::
    H_{ns} = \hat{\theta}_\pi - \hat{\theta}_H
    :label: Hns

Second, the standardized version of the above:

.. math::
    H_{sd} = \frac{\hat{\theta}_\pi - \hat{\theta}_L}{\sqrt{V(\hat{\theta}_\pi - \hat{\theta}_L)}}
    :label: Hsd

with the numerator variance estimated as follows:

.. math::
    a_1 = \sum_i^{n_o'} \frac{1}{i}

.. math::
    b_n = \sum_i^{n_o'} \frac{1}{i^2}

.. math::
    b_{np1} = b_n + \frac{1}{{n_o'}^2}

.. math::
    \theta = \frac{\eta_o}{a_1}

.. math::
    \theta_2 =  \frac{\eta_o(\eta_o - 1)}{{a_1}^2 + b_n}

.. math::
    V(\hat{\theta}_\pi - \hat{\theta}_L) = \theta \frac{n_o-2}{6(n_o-1)} +
        \theta_2 \frac{18{n_o}^2(3n_o+2)b_{np1} - 
        (88n_o^3+9{n_o}^2-13n_o+6)}
            {9n_o(n_o-1)^2}

where :math:`\eta_o` is equal to ``etao``, the total number of mutations at
orientable sites, :math:`n_o` is equal to ``nseffo``, the average number of
samples at orientable sites, and :math:`n_o'` is  ``nseffo`` rounded to unity. 

Third, the *E* statistic:

.. math::
    E = \frac{\hat{\theta}_E - \theta}{\sqrt{V(\hat{\theta}_E - \theta)}}
    :label: E

with:

.. math::
    V(\hat{\theta}_E - \theta) = \theta \left[ \frac{n_o}{2(n_o-1)}-\frac{1}{a_1} \right]
             +  \theta_2 \left[
                   \frac{b_n}{{a_1}^2} + 2 b_n \left( \frac{n_o}{n_o-1} \right)^2
                 - 2 \frac{n_o \cdot b_n-n_o+1}{(n_o-1)a_1}
                 - \frac{3n_o+1}{n_o-1} \right]

Pairwise population distance
============================

Here is how pairwise distance is computed (Nei 1987 *Molecular Evolutionary Genetics*), with

.. math::
    D_{xy} = \frac{1}{L} \sum_i^L 1 - \sum_j^{k_i} p_{ij1} p_{ij2}
    :label: Dxy

Here is the formula for the net pairwise distance:

.. math::
    D_a = D_{xy} - \frac {\pi_1 + \pi_2} {2L}
    :label: Da


where :math:`L` is the number of sites, :math:`k_i` is the number of alleles at site :math:`i`,
:math:`p_{ijk}` is the relative frequency of allele :math:`j` of site :math:`i` in
population :math:`k`, and :math:`\pi_k` is :math:`\pi` for population :math:`k`.
These statistics are only computed for a pair of populations.
