--------------------------
Analysing coding sequences
--------------------------

From an alignment
=================

This section presents the tools allowing to compute diversity statistics
from coding sequences or, more precisely, on specifically either
synonymous or non-synonymous variation.

The principle is to restrict the analysis of diversity to sites that can
unambiguously be assigned to a synonymous or non-synonymous status, i.e.
sites with only two alleles or sites where either all alleles code for
the same amino acid (synonymous) or all alleles code for different amino
acids (non-synonymous). This analysis must be performed at the level of
coding sites, i.e. triplet of nucleotide sites in the coding region that
encode an amino acid.

Let's first assume that the :class:`.Align` object ``aln`` contains aligned
sequences loaded from the Fasta file, i.e. associated to the standard
DNA alphabet::

    >>> aln = egglib.io.from_fasta_string("input file.fas", egglib.alphabets.DNA)

In some cases, it is necessary to splice the alignment, in other words
to extract the region or regions corresponding to the coding region. In
this example there are two exons, representing 100 amino acids split
into two exons of respectively 30 and 69 amino acids, one codon being
sliced by the splicing site. The following code snippet extracts these
two exons and converts the alignment from the DNA alphabet to an
alphabet considering codons are single units::

    >>> rf = egglib.tools.ReadingFrame([(139, 231), (451, 659)])
    >>> cds = egglib.tools.to_codons(aln, frame=rf)

The function :func:`~.tools.to_codons` transforms a DNA-encoded
alignement to an alignment of codons (i.e. where each allele is one
unit representing three consecutive bases). For convenience, the
optional argument *frame* allows to process specific regions, here
represented by an instance of the dedicated class :class:`~.tools.ReadingFrame`.
The resulting object is still an :class:`.Align` but with a different alphabet
designed for codons.

Next, a class is dedicated to identify variable coding sites by
separating synonymous and non-synonymous variation. This class is
:class:`.stats.CodingDiversity`::

    >>> cdiv = egglib.stats.CodingDiversity(cds)

It takes an alignment of coding sequences using the codons alphabet, and
provides several counters to access the number of analysed sites, the
estimated number of non-synonymous and synonymous potential sites, and
the actual (available number of variable non-synonymous and synonymous
sites; see the class documentation for details). Variable sites that
could be assigned to either status are available as attributes of the
objects (``sites_NS`` and ``sites_S``), and these attributes can be
passed to :class:`.stats.ComputeStats` for analysing diversity, using
any available statistics::

    >>> cs = egglib.stats.ComputeStats()
    >>> cs.add_stats('S', 'lseff', 'Pi', 'D')
    >>> statsS = cs.process_sites(cdiv.sites_S)
    >>> statsNS = cs.process_sites(cdiv.sites_NS)

One should be aware that only variable sites are exported (obviously,
fixed sites cannot be assigned to non-synonymous ou synonymous status).
To express the statistics per site (and that's important since there are
much more non-synonymous than synonymous sites), one should use the
``num_sites_S`` and ``num_sites_NS`` attributes of :class:`!CodingDiversity`
objects for standardization.

From a VCF file
===============

If data are available in a VCF file, it is possible to use a class named
:class:`.io.CodonVCF` to assign each site contained in the VCF to the
non-synonymous or synonymous status.

In the example below, we create two :class:`.stats.ComputeStats` objects
to compute statistics separately on respectively synonymous and
non-synonymous variation. The objects are configured to process multiple
sites and to compute the same list of simple statistics::

    >>> cs_syn = egglib.stats.ComputeStats(multi=True)
    >>> cs_syn.add_stats('Pi', 'D', 'lseff')
    >>> cs_nsyn = egglib.stats.ComputeStats(multi=True)
    >>> cs_nsyn.add_stats('Pi', 'D', 'lseff')

Next we create the :class:`!CodonVCF` object, which requires the name of
a VCF file and a GFF3 file providing the annotation::

    >>> cdnVCF = egglib.io.CodonVCF('sequence5-example.bcf', 'sequence5-example.gff3')

It is then necessary to specify which coding region (that is, the CDS
feature) will be processed::

    >>> cdnVCF.set_cds('CDS_1')

After that, we can iterate over all codon positions of this coding
region that are represented in the VCF file. The code below allows to
exclude codons where more than one position is variable (according to
the VCF file), and to analyse the site with the correct :class:`~ComputeStats`
object according to its status::

    >>> for cdn in cdnVCF.iter_codons():
    ...     if not cdn.flag & cdn.MMUT:
    ...         if cdn.flag & cdn.SYN: cs_syn.process_site(cdn)
    ...         if cdn.flag & cdn.NSYN: cs_nsyn.process_site(cdn)
    >>> print(cs_syn.results())
    >>> print(cs_nsyn.results())

The object returned in the iteration is a specific type describing a
coding site obtained from a VCF. It can be used as a site, in particular
for computing statistics. It has also other members, such as ``flag``
which might not be easily intuitive but allows to perform a series of
tests. The ``flag`` variable is a single integer that, if combined by
the ``&`` operator to one of the pre-defined values ``MMUT``, ``SYN``,
``NSYN``, and others, allows to check if the current coding site has a
given property. In this case, ``cdn.flag & cds.MMUT`` is ``True`` if the
site has more than two alleles. The supported tests are listed in the
reference manual.


.. _group-labels:

--------------------------
Structure and group labels
--------------------------

Principle
=========

Many statistics, including :math:`F_{ST}`, require that a structure is 
defined.

In EggLib, the structure is controlled by instances of a specific class 
(:class:`.Structure`) that define groups and identify samples that 
belong to them. These structure objects define which samples belong to 
the outgroup and, how the other samples are organized in individuals 
and/or populations and/or clusters of populations. In this way, a 
three-level hierarchical structure can be defined. It is not required 
to provide information for all the three levels.

The rationale of this system is to allow processing the same data set 
assuming different structurations (in order to either compare the 
effect of different ways to group samples, or analyze different subsets 
of the data separately). The approach is to keep the data set static, 
and provide a separate :class:`!Structure` instance holding the 
description of the structure for each analysis.

There are four ways of creating a :class:`!Structure` instance. First, 
based on group labels of an :class:`.Align` instance. Second, based on 
group labels provided in a :class:`list` or another iterable. Third, by 
providing the sample size of each population. Fourth, from a more 
flexible explicit description of the structure as a :class:`dict` 
instance. Those approaches are described in the next paragraphs.

Group labels
============

To account for structure, EggLib uses a specific system that consists 
in attaching labels to each samples. All samples bearing the same label 
are supposed to belong to the same group. There can be several labels 
per samples. We sometimes refer to an index among group labels as a 
*level*. Different levels of structure are aimed to represent either 
nested levels of structure (clusters of populations and/or populations 
and/or individuals) or alternative levels of structure. There are 
little restrictions on group labels besides being strings.

All :class:`.Align` and :class:`.Container` instances have a list of 
labels attached to each sample. They can be set or edited using either 
:class:`.LabelView` which is a part of :class:`.SampleView` (see 
:ref:`proxy-types`) or direct class-level methods 
:meth:`~.Align.get_label` and :meth:`~.Align.set_label`. By default, 
this list of labels is empty.

The aim of these group labels is essentially to be interpreted by the
class :class:`!Structure` (actually through the method :meth:`.from_labels`)
to be used for computing diversity statistics or restrict an operation
to a given subgroup.

In the following we explain how to specify group labels in Fasta files 
such as EggLib will properly interpret them and store them within an 
:class:`!Align` or :class:`!Container` instance.

Group labels in Fasta files
===========================

Single group label
******************

Let ``align2.fas`` be a Fasta file with six samples, the first three belonging to
population "pop1" and the other three belonging to population "pop2". EggLib
supports a specific system of tags within sequence headers in the Fasta format
to indicate group labels. The tags must appear as suffix starting with a ``@``
followed by a string, as in the following example::

    >sample1@pop1
    ACCGTGGAGAGCGCGTTGCA
    >sample2@pop1
    ACCGTGGAGAGCGCGTTGCA
    >sample3@pop1
    ACCGTGGAGAGCGCGTTGCA
    >sample4@pop2
    ACCGTGGAGAGCGCGTTGCA
    >sample5@pop2
    ACCGTGGAGAGCGCGTTGCA
    >sample6@pop2
    ACCGTGGAGAGCGCGTTGCA

To import group labels, one is required to set the *labels* option of
:func:`~.io.from_fasta` to ``True``::

    >>> aln2 = egglib.io.from_fasta('align2.fas', alphabet=egglib.alphabets.DNA, labels=True)
    >>> print(aln2.get_name(0), aln2.get_label(0, 0))
    sample1 1

If labels have not been imported, accessing any label will cause an
error because, by default, there is no group labels at all included in
:class:`!Align` instances::

    >>> aln2 = egglib.io.from_fasta('align2.fas', alphabet=egglib.alphabets.DNA)
    >>> print(aln2.get_label(0, 0))
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/home/stephane/.local/lib/python3.9/site-packages/egglib/_interface.py", line 986, in get_label
        v = self._obj.get_label(self._sample(sample), self._label(index, self._sample(sample)))
      File "/home/stephane/.local/lib/python3.9/site-packages/egglib/_interface.py", line 827, in _label
        if index >= self._obj.get_nlabels(sample): raise IndexError('invalid label index')
    IndexError: invalid label index

.. note::

    :func:`.io.from_fasta` has an option (*label_marker*) to use a 
    different character than ``@`` to separate the name and the tag.

Multiple group labels
*********************

There can be any number of group levels, either nested or not. To specify
several labels for a sample, one can write several strings separated
by commas, as in the following example::

    >sam1@c1,i1
    ACCGTGGAGAGCGCGTTGCA
    >sam2@c1,i1
    ACCGTGGAGAGCGCGTTGCA
    >sam3@c1,i2
    ACCGTGGAGAGCGCGTTGCA
    >sam1@c1,pop1,i1
    ACCGTGGAGAGCGCGTTGCA
    >sam5@c2,pop1,i1
    ACCGTGGAGAGCGCGTTGCA
    >sam6@c2,pop1,i2
    ACCGTGGAGAGCGCGTTGCA

The example above also demonstrate that it is possible to omit group labels for part of the samples,
although it is probably better to avoid it (because it is error-prone). Labels
absent for a given level are not added or initialised in any way. As a result, if the
file shown above is saved as ``align3.fas`` we can access the second label
of the first sample as shown in the highlighted line below:

.. code-block:: python
   :emphasize-lines: 6

    >>> aln3 = egglib.io.from_fasta('align3.fas', alphabet=egglib.alphabets.DNA, labels=True)
    >>> print(aln3.get_name(0))
    sample1
    >>> print(aln3.get_label(0, 0))
    c1
    >>> print(aln3.get_label(0, 1))
    i1

So, at this point, one should understand labels as list of 0, 1 or more
arbitrary identifiers attached to each sample. How this labels will be
used to group samples in individuals, populations or possibly multi-level
hierachical structure is up to the :class:`!Structure` class.

.. note::

    The separator can also be changed. This can be done using the
    *label_separator* argument of the :func:`.io.from_fasta` method.

Outgroup specification
######################

Tools analysing diversity in EggLib can account for one or more 
outgroup samples. If individuals are defined in the main group 
(ingroup), it is required that outgroup samples also come as one or 
more individuals sharing the same ploidy.

Individuals must be specified by the label ``#`` (obligatory as the 
only or first label), followed by maximum one other label (if the 
individual level is to be considered). Thus, outgroup samples are 
denoted by the tag ``@#`` or ``@#,IND`` where ``IND`` is an individual 
label. Note that if there are individuals in the ingroup then there 
must be also individuals in the outgroup (with the same ploidy).

Very importantly, one must keep in mind that neither 
:func:`!io.from_fasta` nor :class:`!Align` have a notion of the 
outgroup. They don't interpret the ``#`` label as special and don't 
process outgroup samples differently of other samples. It will be the 
job of :class:`!Structure` to separate the outgroup from the rest of 
the samples. This means that, if you have outgroup samples including in 
your data, you *must* use a :class:`Structure` instance for treating 
them properly. Also, if you want to use another label than ``#`` to 
identify outgroup samples, you need to tell it to :class:`Structure`.

Creating a structure from an alignment
======================================

To present the usage of the :class:`.Structure` class, we will use a
complete, albeit over-simplified example. Consider the Fasta
alignment below:

.. code-block:: none

    >sample01@c1,p1,i01
    CTTCCGGGAAGCGCCAGCAGAAGGTTGCTGCTAAGGCCCGCACACGTCTGCAGCACTTCG
    >sample02@c1,p1,i01
    CTTCCGCGCAGGGCCAGGAGCATGTAGCTTCTAAGGCTTGCACAGGTCTTCAGCACTACG
    >sample03@c1,p1,i02
    CTTCCGCGCAGGGCCAGGAGCATGTAGCTTCTAAGGCTTGCACAGGTCTTCAGCACTACG
    >sample04@c1,p1,i02
    CTTCCGCGCAGGGCCAGGAGCATGTAGCTTCTAAGGCTTGCACAGGTCTTCAGCACTACG
    >sample05@c1,p1,i03
    CTACCGTGACGAGCTAGCCGAGCCTGACGCAGGGGGCGAGTAAGGGAGATTACGACTTGG
    >sample06@c1,p1,i03
    CTTCCGCGCAGGGCCAGGAGAATGTTGCTTCTAAGGCTTGCACAGGTCTTCAGCACTAAG
    >sample07@c1,p2,i04
    CTGCTATGACGAACTACCCGAGCCTGGGGCATGGGGCGTGTATGGGAGCTTACAACTTGG
    >sample08@c1,p2,i04
    CTTACGCGACGTGCCAGCATAGGGAAGCTGCTAAGGCCTGCACACGTCCGCAGCACTACG
    >sample09@c1,p2,i05
    CTGCTATGACGAACTACCCGAGGCTGGGGCATGGGGCGTGTATGGGAGCTTACAACTTGG
    >sample10@c1,p2,i05
    CTGCTATGACGAACTACCCGAGGCTGGGGCATGGGGCGTGTATGGGAGCTTACAACTTGG
    >sample11@c1,p2,i06
    CTTACGCGACGCGCCAGCAGAGGGATGCTGCTAAGGCCTGCACACGTCCGCAGCACTACG
    >sample12@c1,p2,i06
    CTTACGCGACGCGCCAGCAGAGGGATGCTGCTAAGGCCTGCACACGTCCGCAGCACTACG
    >sample13@c1,p2,i07
    CTGCTATGACGAACTACCCGAGCCTGGGGCATGGGGCGTGTATGGGAGCTTACAACTTGG
    >sample14@c1,p2,i07
    CTGCTATGACGAACTACCCGAGGCTGGGGCATGGGGCGTGTATGGGAGCTTACAACTTGG
    >sample15@c2,p3,i08
    CTCCGGGGCCGGTTTCGCATAACGTCGCGCAGGGGACGTGTAGGGGCGCATACACCTGGG
    >sample16@c2,p3,i08
    CTCCGGGGCCGGTTTCGCATAACGTCGCGCAGGGGACGTGTAGGGGCGCATACACCTGGG
    >sample17@c2,p3,i09
    TTGCCGGGTCGAACTAGCCGACCTTGGCGCAGGGGTCGTTTAAGGGTCCTTACAACTTGG
    >sample18@c2,p3,i09
    TTGCCGGGTCGAACTAGCCGACCTTGGCGCAGGGGTCGTTTAAGGGTCCTTACAACTTGG
    >sample19@c2,p3,i10
    CTCCGGCGCCGGTTTCGCATAACGTCGCGCAGGGGACGTGTAGGGGCGCATACACCTGGG
    >sample20@c2,p3,i10
    TTGCCGGGTCGAACTAGCCGACCTTGGCGAAGGGGTCGTTTAAGGGACCTTACAACTTGG
    >sample21@c2,p4,i11
    TTGCCAGGACGAACTAGCCGCGCCTGGCGCAGGGGTCGTTTAAGGGAGCTTACAACTTGG
    >sample22@c2,p4,i11
    TTGCCAGGACGAACTAGCCGCGCCTGGCGCAGGGGTCGTTTAAGGGAGCTTACAACTTGG
    >sample23@c2,p4,i12
    TTGCCGGGACGAACTAGCCGAGCCTGGCGCAGGGGTCGTTTAAGGGAGCTTACAACTTGG
    >sample24@c2,p4,i12
    TTGCCGGGACGAACTAGCCGAGCCTGGCGCAGGGGTCGTTTAAGGGAGCTTACAACTTGG
    >sample25@c2,p5,i13
    CTACCGTGACGAACTAGCCGAGCCTGGCGCAGGGGGCGAGTAAGGGAGAGTACAACTTGG
    >sample26@c2,p5,i13
    CTACCGTGACGAACTAGCCGAGCCTGGCGCAGGGGGCGAGTAAGGGAGAGTACAACTTGG
    >sample27@c2,p5,i14
    CTACCGTGACGAACTAGCCGAGCCTGGCGCAGGGGGCGAGTAAGGGAGAGTACAACTTGG
    >sample28@c2,p5,i14
    CTACCGTGACGAACTAGCCGAGCCTGGCGCAGGGGGCGAGTAAGGGAGAGTACAACTTGG
    >sample29@c2,p5,i15
    TTGCCGCGACGAACTAGCCGAGCCTGGCGCAGGGGTCGTTTAAGGGAGCTAACAACTTGG
    >sample30@c2,p5,i15
    CTACCGTGACGAACTAGCCGAGCCTGGCGCAGGGGGCGAGTAAGGGAGAGTACAACTTGG
    >sample31@#,i98
    CATACCACCTTGGCCCGGAGAGTGCGGAGTACCGGGCGTGGAAGGCTGCATGCAAATGGA
    >sample32@#,i98
    CATACCACCTTGGCCCGGAGAGTGCGGAGTACCGGGCGTGGAAGGCTGCATGCAAATGGA
    >sample33@#,i99
    CATACCACCTTGGCCCGGAGAGAGCGCAGTGCCGGGCGTGGAAGGCTGCATTCAAATGCG
    >sample34@#,i99
    CATACCACCTTGGCCCGGAGAGAGCGCAGTGCCGGGCGTGGAAGGCTGCATTCAAATGCG

It has a total of 30 ingroup samples and 4 outgroup samples. These are
actually respectively 15 and 2 individuals, and the ingroup is organized
in two clusters of respectively two and three populations, themselves composed of two,
three, or four individuals each. Remember the labels are arbitrary. In this case,
cluster labels are ``c1`` and ``c2``, population labels ``p1`` to ``p5``
and individual labels ``i01`` to ``i15`` (``i98`` and ``i99`` for the
two outgroup individuals).

Let use name this file ``align5.fas`` and import it with group labels::

    >>> aln = egglib.io.from_fasta('align5.fas', alphabet=egglib.alphabets.DNA, labels=True)

Now, we will directly show a :class:`.Structure` instance incorporating
all structure information (all three levels) can be created::

    >>> struct = egglib.struct_from_labels(aln, lvl_clust=0, lvl_pop=1, lvl_indiv=2)
    >>> print(struct.as_dict())
     ({'c2': {'p3': {'i09': [16, 17], 'i08': [14, 15], 'i10': [18, 19]},
                'p5': {'i13': [24, 25], 'i15': [28, 29], 'i14': [26, 27]}, 
                'p4': {'i11': [20, 21], 'i12': [22, 23]}}, 
       'c1': {'p1': {'i01': [0, 1], 'i03': [4, 5], 'i02': [2, 3]}, 
                'p2': {'i05': [8, 9], 'i04': [6, 7], 'i07': [12, 13], 'i06': [10, 11]}}}, 
      {'i99': [32, 33], 'i98': [30, 31]})

We used the function :func:`.struct_from_labels` that generates a new
:class:`!Structure` instance based on group labels of an :class:`!Align`
(or :class:`!Container`). To use this method, it is necessary to tell
which group level corresponds to the clusters, populations, and individuals
in such a way that they are properly hierarchical. It is possible to skip
any of these three levels of structure, simply by dropping the corresponding
option parameter(s).

The method :meth:`~.Structure.as_dict` is aimed to provide an intuitive
representation of the structure held by the instance. In practice, it is as
intuitive as possible while being flexible enough to represent all possible cases.

.. _structure-dict:

Dictionary representation of :class:`!Structure` instances
**********************************************************

It is a :class:`tuple` containing two items,
each being a :class:`dict`. The first one represents the ingroup and the second
represents the outgroup.

The ingroup dictionary is itself a dictionary holding more dictionaries, one
for each cluster of populations. Each cluster dictionary is a dictionary of
populations, populations being themselves represented by a dictionary. A
population dictionary is, again, a dictionary of individuals. Finally
individuals are represented by lists or integers.

An individual list contains the index
of all samples belonging to this individual. For haploid data, individuals
will be one-item lists. In other cases, all individual lists are required to have
the same number of items (consistent ploidy). Note that, if the ploidy is more
than one, nothing enforces that samples of a given individual are grouped within
the original data, meaning that you can shuffle labels in :class:`.Align` instances
(or in your Fasta file) if you need to.

The keys of the ingroup dictionary are the labels identifying each cluster.
Within a cluster dictionary, the keys are population labels. Finally, within
a population dictionary, the keys are individual labels.

The second dictionary represents the outgroup. Its structure is simpler: it has
individual labels as keys, and lists of corresponding sample indexes as values.
The outgroup dictionary is similar to any ingroup population dictionary. The
ploidy is required to match over all ingroup and outgroup individuals.

If we go back to our example, we see that the returned dictionary for the
ingroup has two items, with keys ``c1`` and ``c2``, respectively, and that
the correct structure appears at lower levels, with two-item (diploid) individuals
within populations withing clusters. Similarly, the two outgroup individuals,
labelled ``i98`` and ``i99``, appear as expected in the second dictionary returned by
the :meth:`!as_dict` method. Ultimately, the values contained by the
lists are the lowest levels are the index referring to the original
:class:`!Align` instance (from 0 to 29 in the ingroup, 30 to 33 in the
outgroup).

Alternative structure
*********************

Occasionally, one will want to generate different :class:`!Structure` instances
based on different levels of structure in group labels (for example if there are
alternative structurations of the data). It is not required that all levels of
a :class:`.Structure` instances are populated, and it is not necessary to import
all structure levels of an :class:`.Align`. The example below demonstrates all
this by importing the first level (previously, clusters) as populations in a new
instance, skipping all other information::

    >>> struct2 = egglib.struct_from_labels(aln, lvl_pop=0)
    >>> print(struct2.as_dict())
     ({None: {'c2': {'24': [24], '25': [25], '23': [23], '27': [27], 
                     '15': [15],'14': [14], '17': [17], '16': [16], 
                     '19': [19], '18': [18], '22': [22], '28': [28], 
                     '26': [26], '29': [29], '20': [20], '21': [21]}, 
              'c1': {'11': [11], '10': [10], '13': [13], '12': [12], 
                      '1': [1], '0': [0], '3': [3], '2': [2], '5': [5],
                      '4': [4], '7': [7], '6': [6], '9': [9], '8': [8]}}}, 
     {'33': [33], '32': [32], '31': [31], '30': [30]})

Note that it is also possible to recycle an already existing :class:`!Structure`
instance instead creating a new one (with the method :meth:`~.Structure.from_labels`
of :class:`!Structure` instances.).

Since we did not specify any group label index for the cluster level, there is
no information regarding clusters, and all populations are placed in a single
cluster. The default label is ``None`` in that case. The two labels ``c1`` and ``c2`` are
now considered as population labels. At the lowest level (also in the outgroup),
all samples are placed in a single-item individuals because, likewise, no index
has been provided for the individual level. Then, haploidy is assumed, and the
sample index is used as default value for individual labels (incremented in the
outgroup).

This example demonstrates that the group labels in :class:`!Align`
instances have no particular meaning *per se* until they are interpreted
while configuring a :class:`!Structure` instance.

Passing labels directly
=======================

Labels are not required to be included in a Fasta file. They can be
passed as a :class:`!list` (or other iterable) of labels (or
:class:`!list`/:class:`!tuple` of labels) to create a
:class:`!structure` instance. This is done using the
:func:`.struct_from_iterable` funtion. If a single label is passed, it
is treated as a population label. If several labels are passed (as in
the example below), the argument *fmt* must be used to specify the level
represented by each column of the label table. The limitation is that
this method doesn't allow to import ingroup. If the :class:`!Structure`
instance created by the example below is used, samples corresponding to
outgroups, which are not included in the :class:`!Structure`, will be
ignored altogether (because :class:`!Structure` are not required to
represent all samples of genetic data objects)::

    >>> labels = [
    ...     ('c1', 'p1', 'i01'),
    ...     ('c1', 'p1', 'i01'),
    ...     ('c1', 'p1', 'i02'),
    ...     ('c1', 'p1', 'i02'),
    ...     ('c1', 'p1', 'i03'),
    ...     ('c1', 'p1', 'i03'),
    ...     ('c1', 'p2', 'i04'),
    ...     ('c1', 'p2', 'i04'),
    ...     ('c1', 'p2', 'i05'),
    ...     ('c1', 'p2', 'i05'),
    ...     ('c1', 'p2', 'i06'),
    ...     ('c1', 'p2', 'i06'),
    ...     ('c1', 'p2', 'i07'),
    ...     ('c1', 'p2', 'i07'),
    ...     ('c2', 'p3', 'i08'),
    ...     ('c2', 'p3', 'i08'),
    ...     ('c2', 'p3', 'i09'),
    ...     ('c2', 'p3', 'i09'),
    ...     ('c2', 'p3', 'i10'),
    ...     ('c2', 'p3', 'i10'),
    ...     ('c2', 'p4', 'i11'),
    ...     ('c2', 'p4', 'i11'),
    ...     ('c2', 'p4', 'i12'),
    ...     ('c2', 'p4', 'i12'),
    ...     ('c2', 'p5', 'i13'),
    ...     ('c2', 'p5', 'i13'),
    ...     ('c2', 'p5', 'i14'),
    ...     ('c2', 'p5', 'i14'),
    ...     ('c2', 'p5', 'i15'),
    ...     ('c2', 'p5', 'i15')]
    >>> struct = egglib.struct_from_iterable(labels, fmt='CPI')
    >>> print(struct.as_dict())
    ({'c1': {'p1': {'i01': [0, 1], 'i02': [2, 3], 'i03': [4, 5]},
             'p2': {'i04': [6, 7], 'i05': [8, 9], 'i06': [10, 11], 'i07': [12, 13]}},
      'c2': {'p3': {'i08': [14, 15], 'i09': [16, 17], 'i10': [18, 19]},
             'p4': {'i11': [20, 21], 'i12': [22, 23]}, 'p5': {'i13': [24, 25], 'i14': [26, 27], 'i15': [28, 29]}}}, 
     {})

Simple structure
================

If your data are organized in an intuitive way (that is, samples organized
per individual and individuals grouped per population), and if the cluster
level is not needed, you can use the function :func:`.struct_from_samplesizes`.
This function takes a list of sample sizes (one item per population).
For example, if your dataset contains two populations of 20 haploid
individuals, you can enter simply::

    >>> struct = egglib.struct_from_samplesizes([20, 20])
    >>> print(struct.as_dict())
    ({None: {'pop1': {'idv1': [0], 'idv2': [1], 'idv3': [2], 'idv4': [3],
                      'idv5': [4], 'idv6': [5], 'idv7': [6], 'idv8': [7],
                      'idv9': [8], 'idv10': [9], 'idv11': [10],'idv12': [11],
                      'idv13': [12], 'idv14': [13], 'idv15': [14], 'idv16': [15],
                      'idv17': [16], 'idv18': [17], 'idv19': [18], 'idv20': [19]},
             'pop2': {'idv21': [20], 'idv22': [21], 'idv23': [22], 'idv24': [23],
                      'idv25': [24], 'idv26': [25], 'idv27': [26], 'idv28': [27],
                      'idv29': [28], 'idv30': [29], 'idv31': [30], 'idv32': [31],
                      'idv33': [32], 'idv34': [33], 'idv35': [34], 'idv36': [35],
                      'idv37': [36], 'idv38': [37], 'idv39': [38], 'idv40': [39]}}}, {})

This function supports ploidy and outgroup individuals, so you can also
declare, for example, two populations of 10 diploid individuals plus one
outgroup individual::

    >>> struct = egglib.struct_from_samplesizes([10, 10], ploidy=2, outgroup=1)
    >>> print(struct.as_dict())
    ({None: {'pop1': {'idv1': [0, 1], 'idv2': [2, 3], 'idv3': [4, 5],
                      'idv4': [6, 7], 'idv5': [8, 9], 'idv6': [10, 11],
                      'idv7': [12, 13], 'idv8': [14, 15], 'idv9': [16, 17],
                      'idv10': [18, 19]},
             'pop2': {'idv11': [20, 21], 'idv12': [22, 23], 'idv13': [24, 25],
                      'idv14': [26, 27], 'idv15': [28, 29], 'idv16': [30, 31],
                      'idv17': [32, 33], 'idv18': [34, 35], 'idv19': [36, 37],
                      'idv20': [38, 39]}}}, {'idv21': [40, 41]})

Be careful that the order of samples in the :class:`!Align` or
:class:`!Site` you'll be analyzing with the resulting :class:`!Structure`
instance must be consistent. Populations must be grouped together in the
order indicated (if sample sizes differ), as well as individuals in
populations, and the outgroup must be at the end.

Mapping individuals to populations
==================================

The function :func:`.struct_from_mapping`, available since version 3.6,
allows to create a :class:`.Structure` object using one or several
:class:`dict` objects mapping individuals to populations and specify the
number of alleles per individuals (i.e. the ploidy), assuming alleles
are consecutive in the data. The list of names of individual, as they
appear in the dataset, must be provided as the first argument of the
function.  The method is intended to be used describe structure of
individuals from a VCF file (whatever the ploidy), as in the example
below::

    >>> vcf = egglib.io.VCF('data.bcf')
    >>> pops = {'pop1': ['sample1', 'sample2', 'sample3'],
    >>> ...     'pop2': ['sample4', 'sample5', 'sample6']}
    >>> struct = egglib.struct_from_mapping(vcf.get_samples(), pop=pops, diploid=2)

Other options allow to specify an outgroup, a :class:`!dict` describing
the organization of populations in clusters and, in the case where the
provided names described alleles within individuals (in case a
:class:`.Align` or :class:`.Site` is provided with ploidy > 1), a
:class:`!dict` describing the organization of samples in individuals.

Fully flexible dictionary
=========================

It is possible to create a :class:`!Structure` instance from 
user-provided data formatted as dictionaries, using either the function 
:func:`.struct_from_dict` or the equivalent :meth:`method 
<.Structure.from_dict>` of :class:`!Structure` instances to recycle an 
existing instance. This approach allows maximal flexibility but 
requires that you create a properly formatted dictionary. Both methods 
take an *ingroup* and an *outgroup* argument, which are formatted 
exactly as the output of :meth:`!as_dict` (see :ref:`structure-dict`). 
This feature can be used to import complex structure information.

Using the structure
===================

Once a :class:`!Structure` has been configured to represent the structuration
of the data set, it can be used as a descriptor while computing diversity
statistics. This will make available a wide array of statistics requiring
this type of information. For example, the statistics with codes
``Fis``, ``Gst``, ``WCist``, and ``WCisct`` require individual and/or
population structure information and won't be computed if no structure
is provided::

    >>> cs = egglib.stats.ComputeStats()
    >>> cs.add_stats('Fis', 'FistWC', 'FisctWC', 'Gst')
    >>> print(cs.process_align(aln))
    {'Gst': None, 'Fis': None, 'WCisct': None, 'WCist': None}

To provide the :class:`!Structure` to :class:`.stats.ComputeStats`, one 
just needs to pass the instance as a value for the *struct* argument of 
the class constructor (or the :meth:`~.stats.ComputeStats.configure` 
method of :class:`!ComputeStats` instances or alternatively, their
:meth:`~.ComputeStats.set_structure` method)::

    >>> cs.configure(struct=struct)
    >>> print(cs.process_align(aln))
    {'FisctWC': (0.39885944313988575, 0.4964142771064885, 0.2339234438730581, 0.6972741981129913),
     'Gst': 0.42684652746367224, 'Fis': 0.6361192023302706,
     'FistWC': (0.39885944313988586, 0.4485871173702674, 0.6685233526761218)}

The code above shows that, with proper structure, we can compute statistics
taking into account the individual, population, and cluster levels. In particular,
``FisctWC`` takes all levels into account. In comparison, ``FistWC`` ignores
the cluster level, but nothing prevents you from computing it at this point.
The code below shows that we can analyse the same data with a different structure
(using the second instance we created before, using the clusters as populations
and ignoring other levels)::

    >>> cs.configure(struct=struct2)
    >>> print(cs.process_align(aln))
    {'Fis': None, 'FistWC': None, 'Gst': 0.1987618106564927, 'FisctWC': None}

Since the individual level is not available, the statistics ``Fis``,
``WCist``, and ``WCisct`` (which also requires the cluster level) cannot
be computed. Only ``Gst`` can. It is still possible to call for statistics
that cannot be computed, but their value will be set to ``None``.

Phased individuals
==================

Statistics are organized in groups. As its name suggests, the group
``+phased`` takes into account the phase of alleles when the ploidy is
above 1. :class:`!ComputeStats` assumes that individuals are unphased,
so alleles of each individual are collapsed in a single allele
representing the genotype before computing statistics of this group. The
example below demonstrates the problem: with 5 diploid individuals, all
haplotypes being different, the number of haplotypes is 5 by default
(5 different genotypes). If alleles are actually phased, we expect to
find 10 unique haplotypes::

    >>> aln = egglib.Align.create([
    ...     ('idv1/1', 'AAAAAAAAA'), ('idv1/2', 'AAAAAAAAC'),
    ...     ('idv2/1', 'AAAAAAACC'), ('idv2/2', 'AAAAAACCC'),
    ...     ('idv3/1', 'AAAAACCCC'), ('idv3/2', 'AAAACCCCC'),
    ...     ('idv4/1', 'AAACCCCCC'), ('idv4/2', 'AACCCCCCC'),
    ...     ('idv5/1', 'ACCCCCCCC'), ('idv5/2', 'CCCCCCCCC')
    ...     ], egglib.alphabets.DNA)
    >>> struct = egglib.struct_from_samplesizes([5], ploidy=2)
    >>> cs = egglib.stats.ComputeStats(struct=struct)
    >>> cs.add_stats('Ki')
    >>> cs.process_align(aln)
    {'Ki': 5}

To properly analyse phased data, one can either drop the individual
level of the structure or, starting with version 3.6, use the *phased*
argument::

    >>> cs.set_structure(None)
    >>> cs.process_align(aln)
    {'Ki': 10}

    >>> cs.configure(struct=struct, phased=True)
    >>> cs.process_align(aln)
    {'Ki': 10}
