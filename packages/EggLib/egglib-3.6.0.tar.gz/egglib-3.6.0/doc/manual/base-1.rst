---------------------------------------
Importing sequences in the fasta format
---------------------------------------

The fasta format is described formally :ref:`here <fasta-format>`. The function
:func:`.io.from_fasta` imports a fasta-formatted file without any regard for
the kind of data it contains (DNA or RNA nucleotides, protein sequences).

Note that it is also possible to import Genepop-formatted genotypic data
using the :func:`.io.from_genepop` function. This function returns an
:class:`.Align` instance, like :func:`.io.from_fasta`.

Simplest case
=============

Let ``align1.fas`` be the name of a fasta-formatted file containing an
alignment of DNA sequences. To import it as an EggLib object, all you have to do is run::

    >>> import egglib
    >>> aln = egglib.io.from_fasta('align1.fas', alphabet=egglib.alphabets.DNA)

The type of the object is :class:`.Align`, which is central to most of 
EggLib's functionality. One must necessarily provide an 
:class:`.Alphabet` to specify the type of data (such as
:data:`.alphabets.DNA`, :data:`.alphabets.protein`, among a few others,
or a custom type, see
the :ref:`alphabets <encoding>` module for further 
information). :class:`!Align` instances are accepted as arguments by 
many other methods of the package. If you want to see the contents of 
an :class:`!Align` instance, the expression ``print(aln)`` will not be 
useful. It will only give you an unique identifier of the object. This 
manual will introduce some of the functionality offered by this class 
and its relative :class:`.Container`, but to get started you can access 
the number of samples and the alignment length by the instance 
properties :py:obj:`~.Align.ns` and :py:obj:`~.Align.ls`::

    >>> print(aln.ns)
    101
    >>> print(aln.ls)
    8942

Alignments and containers
=========================

The instances of type :class:`.Container` are very similar to :class:`.Align`
except that the number of data entries is allowed to vary between samples.
There are specifically designed to hold unaligned sequences. Much of
:class:`!Align`'s functionality is shared with :class:`!Container`.

Automatic detection of alignments
*********************************

There is no difference, in the fasta format, between sequence alignments and
sets of unaligned sequences. By default, :func:`.io.from_fasta` detects automatically
whether all sequences have the same lengths: if so, it returns an
:class:`!Align`; otherwise, it returns a :class:`!Container`. You can test this by running::

    >>> cnt = egglib.io.from_fasta('sequences1.fas',alphabet=egglib.alphabets.DNA)
    >>> print(type(cnt))
    <class 'egglib._interface.Container'>


Enforcing return type
*********************

In some cases you want to enforce the return type of :func:`.io.from_fasta`.
Typically, unaligned sequences may have the same length just by chance, making
the function returns a :class:`!Align` when a :class:`!Container` would
actually make sense. Conversely, malformed fasta files may exist in large sets
of alignments, and forcing return types to be :class:`!Align` will help detect 
invalid files and process them accordingly.

To force the return type to be an :class:`!Align` or a :class:`!Container`, use the option :fparam:`cls` of
:func:`.io.from_fasta` as follows::

    >>> aln2 = egglib.io.from_fasta('align1.fas', cls=egglib.Align, alphabet=egglib.alphabets.DNA)
    >>> cnt2 = egglib.io.from_fasta('align1.fas', cls=egglib.Container, alphabet=egglib.alphabets.DNA)

The object ``aln2`` will be an :class:`!Align`, and the object ``cnt2`` 
will be a :class:`!Container`. Even if they contain actually the same 
data, you will not be able to do the same things with them since they 
are instances of different types.

--------------
Exporting data
--------------

Exporting as fasta
==================

All :class:`.Align`/:class:`.Container` instances have a 
:meth:`~.Align.fasta` method generating a fasta representation of 
the instance. The first argument of this method is the name of an 
output file (:fparam:`fname`)::

    >>> aln.fasta('align_out.fas')

If the :fparam:`fname` argument is omitted (or ``None``), the fasta representation of
the set of sequences is returned as a string (built-in Python :class:`str` instance)::

    >>> print(aln.fasta())
    >sample_01 @0,0
    CATGGAGGATGCAAACACTGCAATCTCGCGTGGGCCGCCACATATAATCC
    CCAGATCACCTCTTGGCACTATTACACCCGCAGTTTCAAACCCGTCCCCA
    GGTGTCGGCCTTACCCGACCTCAAATGACCCCGGACAGGGCAGGCTGACC
    ANAGGCCGTTTNCGCCACTGTGTGAGTCACATCGTCAATTTTCAGCGNCA
    CAAGTGCTTAGCTATCGTCANTCCCGCACCAGAACGTAGGTGGCTGTTAG
    CGGGATGTCCCGAGATATCTACGATCGCTCCAACTCGCTGGACAAACAAT
    CTATGTCAGTACCCGAGAGTTNTTACCTACCTTGTAAAATTAAACTTTAA
    TTATTTCGAAATATTACCGATGTTGATGCAG------ATACATGATCGCT
    CGTTAGTTCATGTATGTCTAACTAGCTCGTGCTGTTACACGGACCGAAGA
    ...
    
Other arguments can be fed to the function for exporting full names with labels for example
or only exporting some sequences.

Other formats
=============

Sequence alignments can be exported to the following formats:

    * Output format of the `ms <http://home.uchicago.edu/rhudson1/source/mksamples.html>`_ software
      (:func:`.io.to_ms`).
    * NEXUS format (:meth:`.Align.nexus`).
    * Phylip phylogenetic software format (:meth:`.Align.phylip`).
    * PhyML phylogenetic software format (:meth:`.Align.phyml`).

Besides, sequence alignments can be imported from:

    * `Clustal <http://www.clustal.org/>`_ alignment software format
      (:func:`.io.from_clustal`).
    * `Staden package <http://staden.sourceforge.net/>`_ software "contig dump" format
      (:func:`.io.from_staden`).
    * Genalys software (which is discontinued) format (:func:`.io.from_genalys`).

---------
Iteration
---------

.. _proxy-types:

Principle of proxy types
========================

Both :class:`.Align` and :class:`.Container` classes are iterable (that 
is they support the ``for item in aln4`` expression if we take the last 
alignment we imported as example). Iteration steps yield instances of a 
specialized type, named :class:`.SampleView` wichi represents one 
sample of a :class:`!Align`/:class:`!Container`: the name is accessible 
as the property :py:obj:`~.SampleView.name`, the sequence as 
:py:obj:`~.SampleView.sequence` and the list of group labels as 
:py:obj:`~.SampleView.labels` (see example below). The name is a 
standard :class:`str` instance, but the sequence and list of group 
labels (see :ref:`group-labels`) are other specialized types 
(:class:`.SequenceView` and :class:`.LabelView`, respectively).

In total, :class:`.SampleView` instances have the following properties:

+---------------------------------+----------------------------------------+---------------------------------+
| Attribute                       | Type                                   | Meaning                         |
+---------------------------------+----------------------------------------+---------------------------------+
| :py:obj:`~.SampleView.name`     | :class:`str`                           | Sample name                     |
+---------------------------------+----------------------------------------+---------------------------------+
| :py:obj:`~.SampleView.sequence` | :class:`.SequenceView`                 | Array of genetic data           |
+---------------------------------+----------------------------------------+---------------------------------+
| :py:obj:`~.SampleView.labels`   | :class:`.LabelView`                    | Array of labels                 |
+---------------------------------+----------------------------------------+---------------------------------+
| :py:obj:`~.SampleView.parent`   | :class:`.Align` or :class:`.Container` | Reference to owner              |
+---------------------------------+----------------------------------------+---------------------------------+
| :py:obj:`~.SampleView.index`    | :class:`int`                           | Sample index in parent          |
+---------------------------------+----------------------------------------+---------------------------------+
| :py:obj:`~.SampleView.ls`       | :class:`int`                           | Number of items for this sample |
+---------------------------------+----------------------------------------+---------------------------------+

All the three types :class:`.SampleView`, :class:`.SequenceView`, and
:class:`.LabelView` are proxy classes similar in principle to
`dictionary views <https://docs.python.org/3/library/stdtypes.html#dictionary-view-objects>`_:
they do not contain a deep copy of the :class:`!Align`/:class:`!Container`
data but rather act as a proxy to edit it more conveniently. As dictionary
views, if the content of the alignment changes, the data accessible from the
proxy might change or even disappear (causing an error if one tries to access data that
are not available anymore), as we will show later. In comparison with dictionary views, :class:`!Align`/:class:`!Container` proxy
types allow a wider range of editing operations, which will be addressed later
in this manual.

Example
=================

The example below shows how to display the names of all samples of the last alignment 
we considered by iterating over the items ::

    >>> aln4 = egglib.io.from_fasta('align4.fas', alphabet=egglib.alphabets.DNA, labels=True)
    >>> print(aln4.ns)
    7
    >>> for item in aln4:
    ...     print(item.name)
    sam1
    sam2
    sam3
    sam4
    sam5
    sam6
    outgroup
