.. _stats-notice:

********************
Diversity statistics
********************

In the module :ref:`stats <stats>`, a number of tools are provided to
compute diversity statistics out of :class:`.Site` or :class:`.Align`
instances. Some statistics are applicable to individual sites, some
to sets of sites, and some to phased sequences alignments. Note that
the objects may indifferently contain nucleotide sequences, protein
sequences, microsatellite alleles encoded (or not) as allele length, or
any arbitrary representation of allelic diversity.

The :ref:`alphabets <alphabets>` define lists of alleles and their 
representation, but have not influence regarding what statistics can be 
computed or not. What is important to note that EggLib will compute any 
statistic you request out of your data, even if it is meaningless. 
Special attention should be granted to statistics requiring a phase, 
since you can easily load unphased data to objects that can be used to 
compute those statistics.

In many cases, not computable statistics are returned as ``None``, but
this is only when they are technically not computable (due to missing
data or unvailability of a specific feature such as outgroup sequences
or subpopulations).

In the sections of this chapter, we will present statistics available 
in the :mod:`!stats` module. Statistics will be grouped by families (a 
family of statistics being a group of statistics that require the same 
type of data and the same kind of information). Most of the statistics 
are computed by :class:`.stats.ComputeStats` (see this :ref:`tutorial 
section <manual_compute_stats>` for an introduction) and the others by 
other functions available in the same module.

--------
Outgroup
--------

Some of the statistics require an outgroup to be computed. The outgroup 
should be included in the analysed dataset (:class:`!Site` or 
:class:`!Align` instance) and identified by the means of a 
:class:`.Structure` instance. There might be more than one outgroup 
samples. The ougroup information will be used to identify the ancestral 
variant (that is, the one which is shared with the outgroup) if the 
outgroup has one of the alleles present in the main sample (the 
ingroup), this allele will be considered to be ancestral. If there are
several outgroup samples, all of them are expected to have the same
allele (if they are non-missing at this position). If the outgroup has
an allele not found in the outgroup, or if the outgroup contains several
alleles, then the site will be considered not orientable and won't be
used for statistics requiring an outgroup. Statistics not requiring an
outgroup will be computed normally, though.

--------------------
Population structure
--------------------

Many statistics require that several populations are present, some 
require that an individual structure is defined, and one statistic 
(``FisctWC``) clusters of populations in addition to populations and 
individuals. Like the outgroup, the structure of samples is described 
by :class:`!Structure` instances (see :ref:`here <group-labels>` for an 
introduction). If the appropriate level of structure is not defined in 
the :class:`!Structure` provided to the class or function computing 
statistics (or if no :class:`!Structure` is provided), the concerned 
statistics will be ``None``.

Here is the list of families of statistics that are described in the
following sections:

.. toctree::
    :maxdepth: 1

    site
    unphased
    phased
    variance
    ehh
    ld
    innan
    misoriente
