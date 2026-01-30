.. _manual-missing-data:

------------
Missing data
------------

Supporting missing data
=======================

Consider the following alignment of 10 sequences, with 30 sites, of which 10
are polymorphic (those at indexes: 2, 5, 7, 8, 12, 13, 14, 18, 22, and 26)::

    GCACCATCATGACTTACGGTATTATCGTAT
    .....T......A.A...........C...
    .....T.GT...A.................
    ......................A...C...
    ......................A...C...
    ..T..T.GT.............A...C...
    ..T..T.......G................
    ..T..T........A...........C...
    ..T....GT.....A...C...A...C...
    ..T..T........A...C.......C...

Assumed it is saved a Fasta in ``align6A.fas``. Without missing data,
computing diversity is relatively straightforward::

    >>> cs = egglib.stats.ComputeStats()
    >>> cs.add_stats('lseff', 'nseff', 'S', 'sites')
    >>> alnA = egglib.io.from_fasta('align6A.fas',egglib.alphabets.DNA)
    >>> print(cs.process_align(alnA))
    {'sites': [2, 5, 7, 8, 12, 13, 14, 18, 22, 26], 'lseff': 30, 'S': 10, 'nseff': 10.0}

Suppose now that the same data were obtained but with less than a perfect
sequencing technology and that consequently some data are missing::

    GCACCATCATGACTTACGGTATTATCGTAT
    .....T......A.A...........C...
    .....T.GT...A.................
    ......................A...C...
    ......................A...C...
    ..T..T.GW....K....S...A...C...
    ..T..T.......G............S...
    ..T..T........A...........S...
    ..T....GT.....A...C...A...C...
    ..T..T........A.??????????????

By default, all sites with at least one missing data will be excluded,
causing a significant loss of data::

    >>> alnB = egglib.io.from_fasta('align6B.fas',egglib.alphabets.DNA)
    >>> print(cs.process_align(alnB))
    {'sites': [2, 5, 7, 12, 14], 'lseff': 14, 'S': 5, 'nseff': 10.0}

Note that it is important to always refer to ``lseff`` to know how many 
sites have been actually used for the analysis (usually smaller than 
:py:obj:`~.Align.ls`). In this case, only 14 of the 30 sites are 
considered. In particular, the sites 8 and 13, which are polymorphic, 
are excluded because the 6th sequence has ambiguity data. Furthermore, 
all sites after index 15 are excluded because the last sequence (and 
sometimes other ones) has missing data. Among those 14 sites included, 
only 5 remain polymorphic.

EggLib has a specific option to allow considering sites even if they 
contain missing data, up to a user-specified threshold. In 
:meth:`.stats.ComputeStats.process_align`, the threshold is expressed as a 
proportion. Assume we want to allow for only one missing data (10%). We 
can do it as shown below::

    >>> print(cs.process_align(alnB, max_missing=0.1))
    {'sites': [2, 5, 7, 8, 12, 13, 14, 22], 'lseff': 28, 'S': 8, 'nseff': 9.5}

This analysis has included 28 sites: all except two that have more than one
missing piece of data (sites at indexes 18 and 26, which appear to be both polymorphic).
The statistic ``nseff`` gives the average number of samples in sites included in the
analysis. While *max_missing* was set to the default (0), all included sites
necessarily had have all samples, so the value was always equal to 10. Now,
included sites may have less than all samples available. For 14 of them all
samples are available, while the 14 others have one missing data, thereby the
average value of 9.5. Whenever possible, computations take this effect into
account and in all cases frequencies are expressed relatively to the effective
number of samples for a given site.

It is possible to be even more liberal and allow for more missing data.
Here, we need to allow for at least 3 missing data to accept all sites (and
detect all polymorphic sites)::

    >>> print(cs.process_align(alnB, max_missing=0.3))
    {'sites': [2, 5, 7, 8, 12, 13, 14, 18, 22, 26], 'lseff': 30, 'S': 10, 'nseff': 9.366666666666667}

Eventually, all sites are processed and all 10 polymorphic sites are detected,
while the average number of samples in used sites drops to 9.37.

The cost of increasing the value for *max_missing* is primarily that large
values (if there are many missing data) lead to including a lot of sites
with few exploitable samples for which all statistics will be poorly estimated,
which will be in the end counter-productive.

---------------------------------
Linkage disequilibrium statistics
---------------------------------

Part of the statistics connected to linkage between distant sites can be
computed using the :class:`.stats.ComputeStats` class. Other require separate
tools, also available in the :ref:`stats <stats>` module.

From :class:`!ComputeStats`
===========================

A number of linkage-related statistics are available among the list of 
statistics proposed by :class:`!ComputeStats`. They include proper 
linkage disequilibrium statistics such as Kelly *et al.*'s and Rozas 
*et al.*'s statistics (such as ``Za``, ``ZZ`` and ``ZnS``) and closely 
related as Hudson's ``Rmin``. We can also consider that statistics 
based on haplotypes are somewhat connected (including ``K``, Hudson's 
``Fst``, Fu's ``Fs``, but also Ramos-Onsins and Rozas's ``R2`` or 
Wall's ``B`` and ``Q``). Please refer to :ref:`stats-notice` for the 
full list. It should be noted that all those statistics require that 
the data are phased, meaning that the order of samples must match over 
all provided sites (including the order of alleles within individuals 
if the individuals are not haploid). This may seem obvious, but keep in 
mind that you may compute haplotype or linkage disequilibrium 
statistics over completely unrelated sites (with non-matching lists of 
samples). Provided that the number of samples matches, EggLib will 
compute all statistics you ask and it is up to you to decide whether 
they are meaningful or not.

This being said, you can compute linkage disequilibrium and haplotype 
statistics using the methods :meth:`!process_align` and 
:meth:`!process_sites` of :class:`!ComputeStats`. In both cases, it 
will be assumed that the data are phased. When using an alignment, 
computing this category of statistics is rather straighforward, but 
note that it is also possible to process a list of :class:`.Site` 
instances as in the example below::

    >>> site1 = egglib.site_from_list('AAAAAAAACCCCCCCC', egglib.alphabets.DNA)
    >>> site2 = egglib.site_from_list('GGGGGGGGGGGTTTTT', egglib.alphabets.DNA)
    >>> site3 = egglib.site_from_list('CCCCCCAAAAAAAAAA', egglib.alphabets.DNA)
    >>> site4 = egglib.site_from_list('TTTTAAAAAAATTTTT', egglib.alphabets.DNA)
    >>> site5 = egglib.site_from_list('CCGGGGGGGGGGCCCG', egglib.alphabets.DNA)
    >>> site6 = egglib.site_from_list('AATTAAAAAAAAAAAT', egglib.alphabets.DNA)
    >>> cs = egglib.stats.ComputeStats()
    >>> cs.add_stats('Rmin', 'Rintervals', 'ZnS', 'Ki') 
    >>> print(cs.process_sites([site1, site2, site3, site4, site5, site6]))
   {'Rintervals': [(2, 3)], 'Rmin': 1, 'Ki': 8, 'ZnS': 0.17767944289156412} 

Note that several options can be set using :meth:`~.ComputeStats.configure`
to control the computation of several statistics in this category (refer to
the documentation of this method for all details).

Note also that the presence of missing data can be a problem, since, on 
one hand, a sequence that contain any missing data cannot be easily 
used while identifying haplotypes and, on the other hand, the effect of 
missing data is magnified in the context of pairwise comparisons. To 
compute this family of statistics, it can be better to remove samples 
for which the amount of missing data is above a given threshold while
keeping the argument *max_missing* to a (very) low value.

Pairwise linkage disequilibrium
===============================

There are two functions in the :ref:`stats <stats>` module to compute linkage
disequilibrium between sites: one to process a pair of sites (:func:`.stats.pairwise_LD`)
and one to process all sites for an alignment (:func:`.stats.matrix_LD`).

The :func:`!stats.pairwise_LD` function
****************************************

This function takes two sites as arguments. It is up to the user to provide
sites with little enough missing data to make the computation relevant.
The function has options to control what happens if there are more than two
alleles at either site (this is not addressed here; see the function's :func:`documentation <.stats.pairwise_LD>`
for more details).

The fragment of code below shows what the function does::

    >>> print(egglib.stats.pairwise_LD(site1, site2))
    {'D': 0.15625, 'Dp': 1.0, 'r': 0.674199862463242, 'rsq': 0.4545454545454545, 'n': 1}
    >>> print(egglib.stats.pairwise_LD(site1, site4))
    {'D': -0.03125, 'Dp': -0.14285714285714285, 'r': -0.1259881576697424, 'rsq': 0.01587301587301587, 'n': 1}

The values are:

    * ``n``, the number of pair of alleles considered (significant if there are more than two alleles at either site).
    * ``D``, linkage disequilibrium.
    * ``Dp``, Lewontin's D'.
    * ``r``, Pearson's correlation coefficient.
    * ``rsq``, squared Pearson's correlation coefficient.

Note that if statistics cannot be computed (typically, because of the presence of
missing data), values in the returned dictionary are replaced by ``None``.

The :func:`!stats.matrix_LD` function
*************************************

This function generates the linkage disequilibrium matrix between all pairs of sites
(for which computation is possible) from a user-provided alignment. This
function has a bunch of options:

    * Options to control what happens if there are more than two
      alleles at either site.
    * Options to apply filters on sites based on allelic frequencies
      (to exclude sites with too unbalanced frequencies, which are less informative) and
      the number of available data.
    * List of positions of sites provided in the alignment (by default, the index of sites
      is used).

The function requires two mandatory arguments: an :class:`.Align` instance and
the list of statistics: ``d``, ``D``, ``Dp``, ``r``, and ``rsq``, as listed
above.

In this example, we consider a very simple alignment of 10 sequences and
10 sites (of which only 3 are variable), saved in a Fasta-formatted file
named ``align7.fas``::

    >sample01
    CACATGTGGA
    >sample02
    CACATGTGGA
    >sample03
    CAGATGTGGT
    >sample04
    CAGATGTGGT
    >sample05
    CACATGTAGT
    >sample06
    CACATGTAGT
    >sample07
    CAGATGTGGT
    >sample08
    CAGATGTGGT
    >sample09
    CACATGTGGT
    >sample10
    CACATGTGGA

The code below demonstrates the usage of :func:`.stats.matrix_LD` and will help
describe its return value::

    >>> aln = egglib.io.from_fasta('align7.fas', egglib.alphabets.DNA)
    >>> print(egglib.stats.matrix_LD(aln, ('d', 'rsq')))
    ([2.0, 7.0, 9.0], [[None], [[5.0, 0.16666666666666652], None],
     [[7.0, 0.28571428571428575], [2.0, 0.10714285714285716], None]])

The usage is fairly straighforward. Just remember to specify the list 
of statistics you want to be computed (in this case, we requested ``d`` 
and ``rsq``) and consider if some of the optional arguments are needed.

The return value is a :class:`tuple` of two lists. The first list is 
the position of sites that have been included in the analysis, in this 
case the three polymorphic sites, which appear to be at positions 2, 7, 
and 9 (there is currently an automatic conversion to floating-point 
number but this may change in the future).

The second item of the return value is a nested list, containing the 
lower half-matrix with requested values. The additional example below 
shows how to collect results in such as way that we loop over all pairs 
of sites::

    >>> pos, mat = egglib.stats.matrix_LD(aln, ('d', 'rsq'))
    >>> n = len(pos)
    >>> for i in range(n):
    ...     for j in range(i):
    ...         p1 = pos[i]
    ...         p2 = pos[j]
    ...         d = mat[i][j][0]
    ...         r2 = mat[i][j][1]
    ...         print('pos:', p1, p2, 'd:', d, 'r2:', r2)
    ...
    pos: 7.0 2.0 d: 5.0 r2: 0.166666666667
    pos: 9.0 2.0 d: 7.0 r2: 0.285714285714
    pos: 9.0 7.0 d: 2.0 r2: 0.107142857143

Note that there is a "gotcha" with this function. If one requests a 
class:`!list` of statistics as the *stats* argument, the values in 
the half-matrix provided as the second return value are a :class:`list` 
of values, even if only one statistic is requested, as in::

    >>> print(egglib.stats.matrix_LD(aln, ['rsq']))
    ([2.0, 7.0, 9.0], [[None], [[0.16666666666666652], None], [[0.28571428571428575], [0.10714285714285716], None]])

However, if one passes a statistic code (not an iterable) as value for
the *stat* option, the items in the returned half-matrix are statistic 
values, not embedded in a list::

    >>> print(egglib.stats.matrix_LD(aln, 'rsq'))
    ([2.0, 7.0, 9.0], [[None], [0.16666666666666652, None], [0.28571428571428575, 0.10714285714285716, None]])

The diagonal values are always ``None``.

EHH statistics
==============

Extended haplotype homozygosity (EHH) statistics are one a set of 
statistics specifically developed with the aim of exploiting 
large-scale sequencing data. The documentation for the class 
:class:`.stats.EHH` provides all details and the list of literature 
references. In this section we provide a quick overview of the usage of 
this class.

EHH would be too complex to be included among statistics proposed by
:class:`.stats.ComputeStats`. It is the reason why it has a class of its own.
To use it, one must therefore first create a class instance::

    >>> ehh = egglib.stats.EHH()

Loading the core site
*********************

The first step consists in loading a core site, which will be used as reference
for all computations. In the original paper, it was a non-recombining region for
which haplotypes have been determined. It can as well be a two-allele SNP marker.
Assume that we have a file named ``sites1.txt``, of which the first line is:

.. code-block:: none

    0000000000000000010002000000010001001000000000000001000000002000000100000000101000000101000010010010

This is one way to represent haplotypic data for 100 individuals in a simple manner.
We will use simple code to import this string of haplotype identifiers as a
:class:`.Site`::

    >>> f = open('sites1.txt')
    >>> core = list(map(int,f.readline().strip()))
    >>> site = egglib.Site()
    >>> site.from_list(core, egglib.alphabets.positive_infinite)

There is a method to set a :class:`!Site` instance as the core site for 
:class:`!EHH`, but first we need to set its position because it will be 
needed to compute EHH statistics. But, when created from a list, 
:class:`!Site` instances don't have a position. Here we will record 
distances relatively to the core site so we set its position to 0.

    >>> site.position = 0
    >>> ehh.set_core(site)

This method takes an array of options, one of which (*min_freq*) 
controlling the frequency threshold (to exclude low-frequency 
haplotypes from the analysis). But we don't use it in this example.

After the core site has been loaded, basic statistics can be accessed::

    >>> print(ehh.num_haplotypes)
    3
    >>> print(ehh.nsam)
    100
    >>> print([ehh.nsam_core(i) for i in range(ehh.num_haplotypes)])
    [85, 13, 2]

These three lines show, respectively:

* :py:obj:`~.stats.EHH.num_haplotypes`, the number of core haplotypes
  (if haplotypes have been excluded due
  to the *min_freq* option, this property gives the number of included
  haplotypes).
* :py:obj:`~.stats.EHH.nsam`, the total number of samples (only considering included haplotypes).
* :meth:`~.stats.EHH.nsam_core`, the  absolute frequency (at the core site) of a core haplotype.

Below we show the initial value of some of the EHH statistics (they 
actually have a value after loading the core site, but it is only after 
loading other sites that they can be interpreted)::

    >>> print(ehh.cur_haplotypes)
    3
    >>> print(ehh.get_EHH(0))
    1.0
    >>> print(ehh.get_EHH(1))
    1.0
    >>> print(ehh.get_EHH(2))
    1.0
    >>> print(ehh.get_rEHH(0))
    1.32911392405
    >>> print(ehh.get_iHH(0))
    0.0
    >>> print(ehh.get_iHS(0))
    None
    >>> print(ehh.get_EHHS())
    1.0
    >>> print(ehh.get_iES())
    0.0

The table below lists the statistics shown (more are available):

+--------------------+-------------------------------------------+-----------------------------------------------+
| Statistic          | Meaning                                   | Initial value                                 |
+====================+===========================================+===============================================+
| ``cur_haplotypes`` | current number of haplotypes              | equal to :py:obj:`~.stats.EHH.num_haplotypes` |
+--------------------+-------------------------------------------+-----------------------------------------------+
| ``get_EHH(i)``     | EHH value for haplotype ``i``             | equal to 1                                    |
+--------------------+-------------------------------------------+-----------------------------------------------+
| ``get_rEHH(i)``    | Ratio of EHH and EHHc for haplotype ``i`` | not defined                                   |
+--------------------+-------------------------------------------+-----------------------------------------------+
| ``get_iHH(i)``     | Integrated value of EHH                   | equal to 0                                    |
+--------------------+-------------------------------------------+-----------------------------------------------+
| ``get_iHS(i)``     | Ratio of iHH and its complement iHHc      | not computable because both terms are 0       |
+--------------------+-------------------------------------------+-----------------------------------------------+
| ``get_EHHS()``     | Site-wise EHHS                            | equal to 1                                    |
+--------------------+-------------------------------------------+-----------------------------------------------+
| ``get_iES()``      | Integrated value of iES                   | equal to 0                                    |
+--------------------+-------------------------------------------+-----------------------------------------------+

Loading the distant sites
*************************

After this, we can start to load other sites (referred to as distant sites).
Distant sites are classically SNP markers located at increasing distance from the
core site (the increasing distance is required). Here we continue reading the
file ``sites1.txt`` which contains, after the core site, biallelic sites
formatted as shown below, taking the first 5 sites as example:

.. code-block:: none

    0000000000000000010000000000010001001000000000000001000000000000000100000000100000000101000010000000
    0000100001000100000000000000000010000100001001001000100000100001100000100000000010000010100000000100
    0000000000000000010000000000010001001000000000000001000000000000000100000000101000000101000010010010
    0000100001000100010000000000010001001000000000000001000000000000000100100000101000000101000010010010
    0000000000100000000000000000000000000000000000000000000000000000000000000100000000000000000100000000

The code below processes the next site in file (using a similar syntax than for the core site)
and pass it to the :class:`.stats.EHH` instance. The positon of the new site must also be set
(when recycling the :class:`.Site` instance, its distance is reset to ``None`` so we need
to set it to a proper value, say 0.1.::

    >>> distant = list(map(int,f.readline().strip()))
    >>> site.from_list(distant, egglib.alphabets.positive_infinite)
    >>> site.position = 0.1
    >>> ehh.load_distant(site)
    >>> print(ehh.cur_haplotypes)
    4
    >>> print(ehh.get_EHH(0))
    1.0
    >>> print(ehh.get_EHH(1))
    0.6153846153846154
    >>> print(ehh.get_EHH(2))
    1.0
    >>> print(ehh.get_rEHH(0))
    2.14285714286
    >>> print(ehh.get_iHH(0))
    0.1
    >>> print(ehh.get_iHS(0))
    -0.495077266798
    >>> print(ehh.get_EHHS())
    0.991778569471
    >>> print(ehh.get_iES())
    0.0995889284736

We can observe that there is already an additional haplotype, meaning 
that the first distant site already modifies the sample partition. It 
concerns the second haplotype, whose EHH value drops to ~0.6. The rEHH 
value of the first haplotype has increased because the complement of 
the first haplotype is affected by the new haplotype. iHH is 0.1 
(integration of EHH over the distance arbitrarily set to 0.1). The 
value of iHS is negative, which is possible because it is the logarithm 
of a ratio. The whole-site EHHS value has decreased because it accounts 
for data at the whole site.

The code below reads all the other sites of the file and displays final values,
always using an increment of 0.1 for the position of each site::

    >>> for i, line in enumerate(f):
    ...     site.from_list(list(map(int,line.strip())), egglib.alphabets.positive_infinite)
    ...     site.position = 0.2 + i / 10.0
    ...     ehh.load_distant(site)
    ...
    >>> print(ehh.cur_haplotypes)
    42
    >>> print(ehh.get_EHH(0))
    0.0392156862745098
    >>> print(ehh.get_EHH(1))
    0.2058823529411765
    >>> print(ehh.get_EHH(2))
    1.566554621848739
    >>> print(ehh.get_rEHH(0))
    0.7030486479143488
    >>> print(ehh.get_iHH(0))
    0.04384762948753081
    >>> print(ehh.get_iHS(0))
    0.703048647914
    >>> print(ehh.get_EHHS())
    0.04384762948753081
    >>> print(ehh.get_iES())
    1.623691422307482

For more details about controlling at what point integration of EHH statistics
should stop, or management of missing data, see the class's :class:`manual <.stats.EHH>`.
