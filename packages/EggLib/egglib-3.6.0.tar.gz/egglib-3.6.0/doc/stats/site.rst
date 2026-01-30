.. _stats_site:

----------------------
Single site statistics
----------------------

Statistics that can be computed for a single site are mainly aimed at
genetic markers exhibiting many alleles (such as microsatellite). Some
of them can be relevant to DNA polymorphism, but in most cases they should
be averaged over many sites.

All those statistics are computed by the class :class:`!ComputeStats`.
The methods :meth:`~.stats.ComputeStats.process_freq` and
:meth:`~.stats.ComputeStats.process_site` return the values for
a single site, while :meth:`~.stats.ComputeStats.process_sites` and
:meth:`~.stats.ComputeStats.process_align` compute an average over all 
provided sites.

In addition, the method :func:`.stats.SFS` allows to compute the site
frequency spectrum from a set of sites based on either minor allele 
(folded) or derived allele (unfolded) frequencies for diallelic sites.

+---------------+----------------------------------------------+------------+--------------+-------+
| Code          | Definition                                   | Formula    | Requirement  | Notes |
+===============+==============================================+============+==============+=======+
| ``+site``     | All statistics from table                    |            |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``ns_site``   | Number of analyzed samples                   |            |              |  1    |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``ns_site_o`` | Number of analyzed outgroup samples          |            | Outgroup     |  1    |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``Aing``      | Number of alleles in ingroup                 |            |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``Aotg``      | Number of alleles in outgroup                |            | Outgroup     |       |   
+---------------+----------------------------------------------+------------+--------------+-------+
| ``Atot``      | Number of alleles in whole dataset           |            |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``As``        | Number of singleton alleles                  |            |              |  2    |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``Asd``       | Number of singleton alleles (derived)        |            | Outgroup     |  2    |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``R``         | Allelic richness                             | :eq:`R`    |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``He``        | Expected heterozygosity                      | :eq:`He`   |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``thetaIAM``  | :math:`\theta` estimator under the IAM model | :eq:`tIAM` |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``thetaSMM``  | :math:`\theta` estimator under the SMM model | :eq:`tSMM` |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``Ho``        | Observed heterozygosity                      |            | Individuals  |  3    |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``Fis``       | Inbreeding coefficient                       | :eq:`Fis`  | Individuals  |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``maf``       | Minority allele relative frequency           |            |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``maf_pop``   | Minority allele per population               |            | Populations  | 4,5   |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``Hst``       | Hudson's Hst                                 | :eq:`Hst`  | Populations  |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``Gst``       | Nei's Gst                                    | :eq:`Gst`  | Populations  |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``Gste``      | Hedrick's Gst'                               | :eq:`Gste` | Populations  |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``Dj``        | Jost's *D*                                   | :eq:`Jost` | Populations  |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``FstWC``     | Weir and Cockerham estimator (haploid data)  | :eq:`WC1`  | Populations  | 6     |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``FistWC``    | Weir and Cockerham estimators (diploid data) | :eq:`WC2a` | Populations, | 6,7   |
|               |                                              | :eq:`WC2b` | individuals  |       |
|               |                                              | :eq:`WC2c` |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``FisctWC``   | Weir and Cockerham estimators (hierarchical) | :eq:`WC3a` | Populations, | 6,7   |
|               |                                              | :eq:`WC3b` | individuals, |       |
|               |                                              | :eq:`WC3c` | clusters     |       |
|               |                                              | :eq:`WC3d` |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``f2``        | Patterson *et al*'s :math:`f_2`              | :eq:`f2`   | Two          |       |
|               |                                              |            | populations  |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``f3``        | Patterson *et al*'s :math:`f_3`              | :eq:`f3`   | Three        |       |
|               |                                              |            | population,  |       |
|               |                                              |            | one focal    |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``f4``        | Patterson *et al*'s :math:`f_4`              | :eq:`f4`   | Two clusters |       |
|               |                                              |            | of two       |       |
|               |                                              |            | populations  |       |
|               |                                              |            | each         |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``Dp``        | Patterson *et al*'s *D*                      | :eq:`Dpat` | Two clusters | 6     |
|               |                                              |            | of two       |       |
|               |                                              |            | populations  |       |
|               |                                              |            | each         |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``numSp``     | Number of population-specific alleles        |            | Populations  | 8     |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``numSpd``    | Number of population-specific derived        |            | Populations, | 8     |
|               | alleles                                      |            | outgroup     |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``numShA``    | Number of shared alleles                     |            | Populations  | 8     |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``numShP``    | Number of shared segregating alleles         |            | Populations  | 8     |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``numFxA``    | Number of fixed alleles                      |            | Populations  | 8     |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``numFxD``    | Number of fixed differences                  |            | Populations  | 8     |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``numSp*``    | Number of sites with at least one            |            | Populations  | 8, 9  |
|               | population-specific allele                   |            |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``numSpd*``   | Number of sites with at least one            |            | Populations, | 8, 9  |
|               | population-specific derived allele           |            | outgroup     |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``numShA*``   | Number of sites with at least one shared     |            | Populations  | 8, 9  |
|               | allele                                       |            |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``numShP*``   | Number of sites with at least one shared     |            | Populations  | 8, 9  |
|               | segregating allele                           |            |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``numFxA*``   | Number of sites with at least one fixed      |            | Populations  | 8, 9  |
|               | allele                                       |            |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``numFxD*``   | Number of sites with at least one fixed      |            | Populations  | 8, 9  |
|               | difference                                   |            |              |       |
+---------------+----------------------------------------------+------------+--------------+-------+
| ``triconfig`` | Number of sites falling into fixation        |            | Three        | 10    |
|               | pattern categories                           |            | populations  |       |
+---------------+----------------------------------------------+------------+--------------+-------+

Notes:

#. Total number of samples excluding all samples with missing data. A *sample*
   is defined as a sampled allele (a diploid individual corresponds to two samples).
#. A singleton allele is an allele present in one copy in the whole sample (excluding outgroup).
#. Computed as the proportion of heterozygote individuals.
#. Relative frequency in each population of the allele which is minority in the whole sample,
   even if it is absent or not minority in some populations. 
#. Returned as a :class:`!list`, even if there is only one population.
#. Multi-site average is computed as the ratio of the sum of numerator terms to the sum of
   numerator terms for all exploitable sites.
#. Returned as a :class:`!list` with the different estimators (see formulas).
#. A *population-specific allele* is an allele which is at non-null frequency in one population
   only. A *fixed allele* is an allele which is at frequency 0 in at least one population and
   at (relative) frequency 1 in at least one population. A *shared allele* is an allele which is
   at non-null frequencies in at least two populations. A *shared polymorphism* is a pair of
   populations which have at least two common segregating (0 < relative frequency < 1) alleles.
   A *fixed difference* is a pair of populations which have two different alleles at relative
   frequency 1.
#. Only computed if several sites are analyzed.
#. Only biallelic sites meeting the missing data criterion are considered.
   The criterion is given by the configuration option ``triconfig_min``
   (minimum number of samples per population, default 2) and ``max_missing``,
   if relevant, is ignored. The result is given as a 13-item list, filled
   with zeros by default, giving the counts for the patterns in the following
   order (where A and B stand for two arbitrary alleles fixed in a population,
   and P a polymorphism of the two alleles in the population): ABB, ABA, AAB,
   PAA, PAB, APA, APB, AAP, ABP, PPA, PAP, APP, PPP.

Basic statistics
================

.. math::
    R = \frac{k-1}{n-1}
    :label: R


.. math::
    H_e = (1 - \sum_i^k {p_i}^2) \frac{n} {(n-1)}
    :label: He

with:

* :math:`n`, the number of samples (given by ``ns_site``) 
* :math:`k`, the number of alleles
* :math:`p_i`, the relative frequency of allele :math:`i`

Theta estimators
================

``thetaIAM``

.. math::
    \hat{\theta}_{IAM} = \frac{H_e}{1 - H_e} 
    :label: tIAM

``thetaSMM``

.. math::
    \hat{\theta}_{SMM} = \frac{1}{2} \left[ \frac{1}{(1 - H_e)^2} - 1 \right]
    :label: tSMM

Fixation index (departure from Hardy Weinberg equilibrium)
==========================================================

.. math::
    F_{IS} = 1 - \frac{H_o}{H_e} 
    :label: Fis

Population differentiation
==========================

In this section we define:

+----------------+----------------------------------------------------------------+
| :math:`r`      | number of populations                                          |
+----------------+----------------------------------------------------------------+
| :math:`n_i`    | sample size of population :math:`i`                            |
+----------------+----------------------------------------------------------------+
| :math:`n_t`    | total sample size                                              |
+----------------+----------------------------------------------------------------+
| :math:`k`      | number of alleles                                              |
+----------------+----------------------------------------------------------------+
| :math:`p_i`    | relative frequency of allele :math:`i` in the whole sample     |
+----------------+----------------------------------------------------------------+
| :math:`p_{ij}` | relative frequency of allele :math:`i` in population :math:`j` |
+----------------+----------------------------------------------------------------+

and we exclude any populations with less than two samples.

:math:`H_{ST}` (Hudson *et al.* *Mol. Biol. Evol.* 1992 **9**:138-151) is defined as follows:

.. math::
    H_{ST} = 1 - \frac{H_{S_1}}{H_{T_1}}
    :label: Hst

with

.. math::
    H_{S_1} = \frac{1}{\sum_i^r n_i - 2} \sum_i^r (n_i-2) H_i

and

.. math::
    H_{T_1} = \frac{n_t}{n_t - 1} \left[ 1-\sum_i^k \left( \frac{1}{n_t}\sum_j^r p_{ij} n_i \right)^2 \right]

with:

.. math::
    H_i = \frac{n_i}{n_i-1} \left[ 1 - \sum_j^k {p_{ji}}^2 \right]

Nei's :math:`G_{ST}` (Hudson *et al.* *Mol. Biol. Evol.* 1992 **9**:138-151) is defined as follows:

.. math::
    G_{ST} = 1 - \frac{H_{S_2}}{\tilde{H}_T}
    :label: Gst

with

.. math::
    H_{S_2} = \frac{1}{n_t} \sum_i^r n_i H_i

and

.. math::
    \tilde{H}_T = 1 - \sum_i^k  \left( \frac{1}{n_t} \sum_j^r p_{ij} n_j \right) ^2 + \frac{1}{r \cdot \tilde{n}} H_{S_2}

with

.. math::
    \tilde{n} = \frac{r} {\sum_i^r \frac{1}{n_i}}

:math:`G_{ST}'` (Hedrick *Evolution* **17**:4015-4026) is defined as:

.. math::
    G'_{ST} = \frac{1 + H_{S_3}}{1 - H_{S_3}} \left( 1 - \frac{H_{S_3}}{H_{T_2}} \right)
    :label: Gste

with

.. math::
    H_{S_3} = \frac{1}{r} \sum_i^r \left( 1 - \sum_j^k {p_{ji}}^2 \right)

and

.. math::
    H_{T_2} = 1 - \sum_i^k \left( \frac{1}{r} \sum_j^r p_{ij} \right) ^2

Jost's :math:`D` (*Mol. Ecol.* 2008 **18**:4015-4026) is computed as:

.. math::
    D = \frac{r}{r-1} \frac{H_{T_3} - H_{S_4}} {1 - H_{S_4}}
    :label: Jost

with:

.. math::
    H_{S_4} = \frac{\tilde{n}}{\tilde{n}-1} H_{S_3}

and

.. math::
    H_{T_3} = H_{T_2} + \frac{1}{r \cdot \tilde{n}} H_{S_4}

F-statistics estimators
=======================

Estimators of *F*-statistics are based on
Weir and Cockerham (*Evolution* 1984 **38**:1358-1370) and
Weir and Hill (*Annu Rev. Genet.* **36**:721-750).

Different estimators are available depending on which levels of structure
are provided through a :class:`!Structure` instance.

Population structure only
-------------------------

If only the population structure is available, only the equivalent of :math:`F_{ST}`
(:math:`\hat{\theta}` in Weir and Cockerham's notation) is available.

.. math::
	n_c = \frac{1}{k - 1} \left( n_t - \frac{1}{n_t} \sum_p^k {n_p}^2 \right)

where :math:`n_p` is the number of samples of population :math:`p`, :math:`n_t` is the total number of samples,
and :math:`k`  is the number of considered populations.
Only populations with at least two samples are considered.

For a given allele :math:`i`, we compute:

.. math::
	\alpha_i = \frac{1}{k-1} \sum_p^k n_p (p_{ip} - \bar{p}_i) ^2

.. math::
	\delta_i = \frac{1}{n_t-k} \sum_p^k n_p \cdot p_{ip} (1-p_{ip})

where :math:`\bar{p}_i` is the overall relative frequency of allele :math:`i` in the whole sample
and :math:`p_{ip}` is the relative frequency of allele :math:`i` in population :math:`p`.

The equivalent of :math:`F_{ST}` is then computed as:

.. math::
    \hat{\theta} = \frac{\sum_i^A \alpha_i - \delta_i}{\sum_i \alpha_i + (n_c - 1) \delta_i}
    :label: WC1

Population and individual structure
-----------------------------------

If both population and individual structures are available, the 
decomposition of inbreeding in three terms, :math:`F` (equivalent to 
:math:`F_{IT}`), :math:`\theta` (equivalent to :math:`F_{ST}`, and 
:math:`f` (equivalent to :math:`F_{IS}`) is possible. The estimators of 
these fixation indexes are defined below, following Weir and Cockerham 
(*Evolution* 1984 **38**:1358-1370).

The estimators are based on three components of variance, noted :math:`a` (between
populations), :math:`b` (between individuals within populations), and :math:`c`
(within individuals):

.. math::
	a = \sum_i^A \frac{\bar{n}}{n_c} \left\{ s^2_i - \frac{1}{\bar{n}-1} \left[ \bar{p}_i(1-\bar{p}_i) - s^2_i\frac{k-1}{k} - \frac{\bar{h}_i}{4} \right] \right\}

.. math::
	b = \sum_i^A \frac{\bar{n}}{\bar{n}-1} \left[ \bar{p}_i(1-\bar{p}_i) - s^2_i \frac{k-1}{k} - \bar{h}_i\frac{2\bar{n}-1}{4\bar{n}} \right]

.. math::
	c = \sum_i^A \frac{1}{2} \bar{h}_i

with:

* :math:`A`, the number of alleles
* :math:`k`, the number of populations with at least one individual
* :math:`\bar{n}`, the average number of individuals per population
* :math:`\bar{p}_i`, the relative frequency of allele :math:`i` in the whole sample
* :math:`\bar{h}_i`, the proportion of individuals carrying allele :math:`i`
  as the heterozygote state, calculated in the whole sample
* :math:`s^2_i`, as defined below:

.. math::
    s^2_i = \frac{\bar{n}}{k-1} \sum_p^k n_p (p_{ap} - \bar{p}_a)^2

* :math:`n_c`, as defined below:

.. math::
    n_c = \frac{1}{k-1} \left( k \cdot \bar{n} - \frac{1}{k \cdot \bar{n}} \sum_p^k {n_p}^2 \right)

* :math:`n_p`, the number of individuals in population :math:`p`
* :math:`p_{ap}` the relative frequency of allele :math:`a` in population :math:`p`

The return value for ``FistWC`` is a tuple with the three F-statistics estimators:
:math:`\left(\hat{f}, \hat{\theta}, \hat{F}\right)`, which are equivalent to
:math:`\left(F_{IS}, F_{ST}, F_{IT}\right)` and are defined as follows:

.. math::
	1 - \hat{f} = \frac{c}{b+c}
	:label: WC2a

.. math::
	\hat{\theta} = \frac{a}{a+b+c}
	:label: WC2b

.. math::
	1 - \hat{F} = \frac{c}{a+b+c}
	:label: WC2c

Clusters, population and individual structure
---------------------------------------------

If, in addition, populations are grouped in clusters, it is possible to
compute an additional fixation index: the between-population fixation index
:math:`\theta` (or :math:`F_{ST}`) is subdivided in a between-population,
within-cluster component :math:`\theta_1` (or :math:`F_{SC}`) and a
between-cluster component :math:`\theta_2` (or :math:`F_{CT}`). The
estimators are based on four components of variance, noted :math:`a` (between
clusters), :math:`b_2` (between populations within clusters), :math:`b_1` (between
individuals within populations), and :math:`c` (within individuals). They
are computed as described in Weir and Cockerham (*Evolution* 1984 **38**:1358-1370).

.. math::
	a = \sum_i^A \frac{n_3 \epsilon_i - n_1 \delta_i - (n_3-n_1) \beta_i} {2 \cdot n_2 \cdot n_3}

.. math::
	b_2 = \sum_i^A \frac{\delta_i - \beta_i} {2 \cdot n_3}

.. math::
	b_1 = \sum_i^A \frac{1}{2} (\beta_i - \alpha_i)

.. math::
	c = \sum_i^A \alpha_i

:math:`\alpha` (MSG en Weir and Cockerham's article) is computed as:

.. math::
	\alpha_i = \frac{1}{2 n} \sum_p^k h_{ip}

:math:`\beta` (MSI en Weir and Cockerham's article) is computed as:

.. math::
	\beta_i = \frac{2 \sum_p^k n_p p_{ip} (1-p_{ip}) - \frac{1}{2} \sum_p^k h_{ip}} {n_t - k}

:math:`\delta` (MSD en Weir and Cockerham's article) is computed as:

.. math::
	\delta_i = \frac{2}{k - r} \sum_p^k n_p (p_{ip} - p_{ic_p}) ^2

:math:`\epsilon` (MSP en Weir and Cockerham's article) is computed as:

.. math::
	\epsilon_i = \frac{2}{r-1}\sum_c^r n_c (p_{ic} - p_i) ^2

with:

* :math:`k` number of populations with at least one individual
* :math:`r` number of clusters with at least one population
* :math:`n` total number of individuals (in considered populations)
* :math:`n_p` number of individuals in population :math:`p`
* :math:`n_c` number of individuals in population :math:`c`
* :math:`p_i` relative frequency of allele :math:`i` in the whole sample
* :math:`p_{ip}` relative frequency of allele :math:`i` in population :math:`p`
* :math:`p_{ic_p}` relative frequency of allele :math:`i` in the cluster containing population :math:`p`
* :math:`p_{ic}` relative frequency of allele :math:`i` in the cluster :math:`c`
* :math:`h_{ip}` number of heterozygote individuals carrying allele :math:`i` in population :math:`p`

The return value for ``FisctWC`` is a tuple with the four F-statistics estimators:
:math:`\left(\hat{f}, \hat{\theta}_1, \hat{\theta}_2, \hat{F}\right)`, which are equivalent to
:math:`\left(F_{IS}, F_{SC}, F_{CT}, F_{IT}\right)` and are defined as follows:

.. math::
	1 - \hat{f} = \frac{c}{b_1+c}
	:label: WC3a

.. math::
	\hat{\theta}_1 = \frac{a+b_2}{a+b_2+b+1+c}
	:label: WC3b

.. math::
	\hat{\theta}_2 = \frac{a}{a+b_2+b+1+c}
	:label: WC3c

.. math::
	1 - \hat{F} = \frac{c}{a+b_2+b+1+c}
	:label: WC3d

Patterson's *f* statistics
--------------------------

We implement statistics of Patterson *et al.* (*Genetics* 2012 **192**:1065-1093)
as follows.

``f2`` is only computed if there are two populations, each containing at
least two non-missing samples and there are at most two alleles. One of
the two alleles is chosen arbitrarily. The same requirements apply for
``f3`` with three populations, one of them being be designed as focal,
and for ``f4`` and ``Dp`` with four populations organized in two
clusters.

In the equations below, :math:`n_i` is the sample size and :math:`p_i`
is the frequency of the an allele chosen arbitrarily, both for
population *i*.

.. math::
    f_2 = (p_1 - p_2) ^ 2 - \frac{p_1(1-p_1)}{n_1-1} - \frac{p_2(1-p_2)}{n_2-1}
    :label: f2

Here is ``f3`` assuming that population :math:`1` is focal:

.. math::
    f_3 = (p_1 - p_2)(p_1 - p _3)  - \frac{p_1(1-p_1)}{n_1-1}
    :label: f3

For ``f4`` and ``Dp``, populations :math:`1` and :math:`2` are assumed
to belong to one cluster and populations :math:`3` and :math:`4` to the
other one:

.. math::
    f_4 = (p_1 - p_2) (p_3 - p_4)
    :label: f4

.. math::
    D_P = \frac{f_4} {(p_1 + p_2 - 2 p_1 p_2)(p_3 + p_4 - 2 p_3 p_4)}
    :label: Dpat
