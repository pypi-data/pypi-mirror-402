--------------------------
Accessing and editing data
--------------------------

In general, :class:`.Align`/:class:`.Container` provide two ways to 
access/edit data they contain: through the methods of 
:class:`.SampleView` instances returned by the iterators, and through 
direct methods. Those two approaches are equivalent and your choice 
should be guided by readability first.

Accessing a given sample
========================

:class:`.SampleView` instances can be directly accessed using their 
index without requiring iteration using :class:`!Align`'s method 
:meth:`~.Align.get_sample`. The bracket operator ``[]`` is a synonym. 
Here is an illustratory example (both lines show the name of the first 
sample)::

    >>> print(aln4[0].name)
    sam1
    >>> print(aln4.get_sample(0).name)
    sam1

It is also possible to use the method :meth:`~.Align.find` to access
a :class:`.SampleView` based on its name.

Editing names
=============

There is no trick about reading/setting the name of a sample in :class:`!Container`/:class:`!Align`
instances. The :py:obj:`!name` property of :class:`!SampleView` is a standard :class:`str` and
can be modified by any new value, as long as it is, or can be casted to, a :class:`str`.
Alternatively, both :class:`!Container` and :class:`!Align` have methods to get and set the
name of a sample. All techniques are listed in the table below, with ``item`` being a
:class:`!SampleView` instance, and ``obj`` being either a :class:`!Align` 
or :class:`!Container` instance:

+--------------------------+----------------------------------------------------------------+
| Expression               | Result                                                         |
+==========================+================================================================+
| ``item.name``            | Get the name of a sample (1).                                  |
+--------------------------+----------------------------------------------------------------+
| ``item.name = x``        | Set the name of a sample to ``x`` (1)(2).                      |
+--------------------------+----------------------------------------------------------------+
| ``obj.get_name(i)``      | Get the name of the ``i``\ th sample.                          |
+--------------------------+----------------------------------------------------------------+
| ``obj.set_name(i,x)``    | Set the name of the ``i``\ th sample to ``x`` (2).             |
+--------------------------+----------------------------------------------------------------+

Notes:
    1. The identity of the sample is defined by the origin of the :class:`!SampleView` instance.
    2. ``x`` must be a :class:`str`.

The example below shows that those approaches are equivalent, and also demonstrates
that the content available through a :class:`!SampleView` is modified whenever
the underlying :class:`!Align` is modified, even if it is by an other mean::

    >>> item = aln4.get_sample(0)
    >>> print(item.name)
    sample1
    >>> print(aln4.get_name(0))
    sample1
    >>> aln4.set_name(0, 'another name')
    >>> print(item.name)
    another name

Editing sequences or data entries
=================================

The :class:`!SequenceView` type
*******************************

:class:`.SequenceView` is another proxy class, managing the sequence of 
data for a given sample. It can be obtained from a :class:`.SampleView` 
or from the method :meth:`~.Align.get_sequence` of both :class:`!Align` 
and :class:`!Container` instances. :class:`!SequenceView` instances can 
be treated, to some extent, as lists of data values. In particular, 
they offer the same functionalities for editing the data. There is one 
significant limitation: the length of a :class:`!SequenceView` instance
connected to a :class:`!Align` cannot be modified.

Operations using a :class:`!SequenceView` as a list-like instance
*****************************************************************

In the table below, assume ``seq`` is a :class:`!SequenceView` 
instance, ``s`` is a stretch of sequence as a :class:`str`, ``c`` is a 
one-character string (although an integer can be accepted depending on 
the :class:`.Alphabet` used), ``i`` is any valid index (and ``j`` a 
second one if a slice is needed).

+--------------------------+----------------------------------------------------------------+
| Expression               | Result                                                         |
+==========================+================================================================+
| ``len(seq)``             | Get the number of data entries.                                |
+--------------------------+----------------------------------------------------------------+
| ``for v in seq``         | Iterate over data entries.                                     |
+--------------------------+----------------------------------------------------------------+
| ``seq[i]``               | Access a data item.                                            |
+--------------------------+----------------------------------------------------------------+
| ``seq[i:j]``             | Access a section of the sequence.                              |
+--------------------------+----------------------------------------------------------------+
| ``seq[i] = c``           | Modify a data item.                                            |
+--------------------------+----------------------------------------------------------------+
| ``seq[i:j] = s``         | Replace a section of the sequence by a new sequence (1).       |
+--------------------------+----------------------------------------------------------------+
| ``del seq[i]``           | Delete a data entry (2).                                       |
+--------------------------+----------------------------------------------------------------+
| ``del seq[i:j]``         | Delete a section of the sequence (2).                          |
+--------------------------+----------------------------------------------------------------+
| ``seq.string()``         | Return the sequence as a :class:`!str`.                        |
+--------------------------+----------------------------------------------------------------+
| ``seq.insert(i, s)``     | Insert a stretch of sequence (2).                              |
+--------------------------+----------------------------------------------------------------+
| ``seq.find(s)``          | Find the position of a given motif.                            |
+--------------------------+----------------------------------------------------------------+
| ``seq.upper()``          | Modify the sequence to contain only upper-case characters (3). |
+--------------------------+----------------------------------------------------------------+
| ``seq.lower()``          | Modify the sequence to contain only lower-case characters (3). |
+--------------------------+----------------------------------------------------------------+
| ``seq.strip(s)``         | Remove left/right occurrences of characters present in ``s``.  |
+--------------------------+----------------------------------------------------------------+

Notes:
    1. Only available for :class:`!Align` instances if the length of the provided stretch matches.
    2. Not available for :class:`!Align` instances.
    3. Only available for instances using a case-sensitive alphabet (excluding DNA).
    
In addition, one can modify the whole sequence directly through the
:class:`!SampleView`, as in::

    >>> item = aln4.get_sample(0)
    >>> item.sequence = 'ACCGTGGAGAGCGCGTTGCA'

Obviously, and again, if the original instance is an :class:`!Align`, the
sequence length must be kept constant.

Using methods of :class:`!Align` and :class:`!Container`
**********************************************************

Most of the functionality available through :class:`!SequenceView` is 
also available as methods of the :class:`!Align`/:class:`!Container`. 
The table below lists the available methods (or properties), where 
``i`` is a sample index, ``j`` a position, ``n`` a number of sites, 
``c`` a data entry (either an integer or character, see :ref:`alphabets 
<encoding>`), and ``s`` a :class:`!str` or a list of data entries.

+-------------------------------+-------------------------------------------------------------------------+
| Expression                    | Result                                                                  |
+===============================+=========================================================================+
| ``aln.ls``                    | Get alignment length (cannot be modified) (1).                          |
+-------------------------------+-------------------------------------------------------------------------+
| ``cnt.ls(i)``                 | Length of the sequence for an ingroup sample (2).                       |
+-------------------------------+-------------------------------------------------------------------------+
| ``obj.get_sequence(i)``       | Get the sequence of a sample as a :class:`!SequenceView`.               |
+-------------------------------+-------------------------------------------------------------------------+
| ``obj.get_i(i,j)``            | Get a data entry of a sample.                                           |
+-------------------------------+-------------------------------------------------------------------------+
| ``obj.set_i(i,j,c)``          | Set a data entry of a sample.                                           |
+-------------------------------+-------------------------------------------------------------------------+
| ``obj.set_sequence(i,s)``     | Set the whole sequence of a sample.                                     |
+-------------------------------+-------------------------------------------------------------------------+
| ``cnt.del_sites(i,j,n)``      | Delete data entries for a sample (2).                                   |
+-------------------------------+-------------------------------------------------------------------------+
| ``cnt.insert_sites(i,j,s)``   | Insert a given sequence at a given position for a sample (2).           |
+-------------------------------+-------------------------------------------------------------------------+

Notes:
    1. Only available for :class:`!Align` instances.
    2. Only available for :class:`!Container` instances.

Using module functions
**********************

A few functions from the :mod:`.tools` module can be used with 
sequences. Note that they never modify the passed instance. On the 
other hand, they can accept sequences as :class:`!SequenceView` or 
:class:`!str` instances.

+---------------------------+--------------------------------------------------------------------+
| Function                  | Operation                                                          |
+===========================+====================================================================+
| :func:`.tools.rc`         | Reverse-complement of a DNA sequence.                              |
+---------------------------+--------------------------------------------------------------------+
| :func:`.tools.compare`    | Check if sequences matches (supporting ambiguity characters).      |
+---------------------------+--------------------------------------------------------------------+
| :func:`.tools.regex`      | Turn a sequence with ambiguity characters to a regular expression. |
+---------------------------+--------------------------------------------------------------------+
| :func:`.tools.motif_iter` | Iterate over occurrences of a motif.                               |
+---------------------------+--------------------------------------------------------------------+

Editing labels
====================

Using :class:`!LabelView`
*************************

In comparison to sequences, list of labels are relatively simple.
However, there is also a specialized proxy class, :class:`.LabelView`. Objects of this
type behave to a limited extent like a list of strings. It is not possible to delete any item 
from a :class:`!LabelView`. 
The supported functions are listed in the table below, where ``grp`` is a :class:`!LabelView`, 
``i`` a level index, and ``v`` a label value:

+--------------------------+---------------------------------------------------------------+
| Expression               | Result                                                        |
+==========================+===============================================================+
| ``len(grp)``             | Get the number of label levels.                               |
+--------------------------+---------------------------------------------------------------+
| ``grp[i]``               | Access a label level.                                         |
+--------------------------+---------------------------------------------------------------+
| ``grp[i] = v``           | Modify a label level.                                         |
+--------------------------+---------------------------------------------------------------+
| ``for v in grp``         | Iterate over group labels.                                    |
+--------------------------+---------------------------------------------------------------+
| ``append()``             | Append a label.                                               |
+--------------------------+---------------------------------------------------------------+

Using methods of :class:`!Align` and :class:`!Container`
**********************************************************

The methods (and one property) allowing to edit group labels are listed below,
where ``n`` is non-negative integer, ``i`` is a sample index, ``j`` is the
index of a group level and ``g`` is a group label:


+----------------------+------------------------------------------+
| Expression           | Result                                   |
+======================+==========================================+
| ``get_label(i,j)``   | Get one of the group labels of a sample. |
+----------------------+------------------------------------------+
| ``set_label(i,j,g)`` | Set one of the group labels of a sample. |
+----------------------+------------------------------------------+


Initializing instances
======================

We have seen how to create :class:`!Container` and :class:`!Align` instances
initialized from the content of a Fasta-formatted sequence file. In
:ref:`coalesce-manual` we will see how to generate data sets using coalescent
simulations. Several methods exist to create sequence set objects with
more flexibility.

Creating from empty instances
*****************************

The default constructors of :class:`!Container` and :class:`!Align` 
return empty instances that can later be filled manually with the 
methods described in the following sections. In addition, the 
:class:`.Align` constructor allows one to initialize the instance to 
specified dimensions, with an optional user-specified initial values 
for all data entries, as shown in the example below::

    >>> aln5 = egglib.Align(alphabet=egglib.alphabets.DNA)
    >>>> print(aln5.ns, aln5.ls)
    0, 0
    >>> aln6 = egglib.Align(nsam=6, nsit=4, init='N',alphabet=egglib.alphabets.DNA)
    >>> print(aln6.ns, aln6.ls)
    6 4
    >>> print(aln6.fasta())
    >
    NNNN
    >
    NNNN
    >
    NNNN
    >
    NNNN
    >
    NNNN
    >
    NNNN

Deep copy of :class:`!Align` and :class:`!Container` instances
**************************************************************

Both :class:`!Align` and :class:`!Container` have a class method
:meth:`~.Align.create` that returns a new instance initialized from the
content of the provided argument. There can be several uses for that
functionality, and one of them is performing a deep copy of an instance.
For example, let us assume one wants to create an independent copy of an
alignement. The approach exemplified below will **not** work as wanted::

    >>> aln = egglib.io.from_fasta('align4.fas', alphabet=egglib.alphabets.DNA, labels=True)
    >>> copy = aln
    >>> aln.set_sequence(0, 'CCTCCTCCTCCTCCTCCTCT')
    >>> print(copy.get_sequence(0).string()) # aln and copy refer to the same object!
    CCTCCTCCTCCTCCTCCTCT

.. warning:
    In Python, the assignment operator creates a new reference to the
    same object: in this case, ``aln`` and ``copy`` are two reference to
    the same :class:`!Align` object.

This results in the string ``CCTCCTCCTCCTCCTCCTCT`` since ``aln`` and 
``copy`` are actually references to the same underlying object (see 
`this FAQ <https://docs.python.org/2/faq/programming.html#why-did-changing-list-y-also-change-list-x>`_ 
in the Python documentation). The class method :meth:`!create` allows 
to make a proper deep copy as demonstrated in the code below, were 
``copy`` is created in such a way it is an object independent of 
``aln``::

    >>> aln = egglib.io.from_fasta('align4.fas', alphabet=egglib.alphabets.DNA, labels=True)
    >>> copy = egglib.Align.create(aln)
    >>> aln.set_sequence(0, 'CCTCCTCCTCCTCCTCCTCT')
    >>> print(copy.get_sequence(0).string())
    ACCGTGGAGAGCGCGTTGCA



Conversion between :class:`!Align` and :class:`!Container` instances
********************************************************************

Another use of :meth:`!create` is to convert between :class:`!Align` and
:class:`!Container` types. It is possible to make a :class:`!Container` copy of
an :class:`!Align` as in::

    >>> cnt = egglib.Container.create(aln)

Obviously, the opposite (from :class:`!Container` to :class:`!Align`) requires that
all sequences have the same length. For example, suppose that we have an alignment that
has, for some reason, a longer sequence, as in::

    >sample1
    ACCGTGGAGAGCGCGTTGCA
    >sample2
    ACCGTGGAGAGCGCGTTGCA
    >sample3
    ACCGTGGAGAGCGCGTTGCATTAAGTA
    >sample4
    ACCGTGGAGAGCGCGTTGCA

You must import this data set as a :class:`!Container`. The code below shows
that the resulting instance is a :class:`!Container` (the property
:py:obj:`~.Align.is_matrix` is another way to tell if an object is an
:class:`!Align`), and confirms that the third sequence is longer::

    >>> cnt = egglib.io.from_fasta('sequences2.fas', alphabet=egglib.alphabets.DNA)
    >>> print(type(cnt))
    <class 'egglib._interface.Container'>
    >>> print(cnt.is_matrix)
    False
    >>> print(cnt.ls(0))
    20
    >>> print(cnt.ls(2))
    27

After cropping the longer sequence such that all sequences have the same length,
we can turn the :class:`!Container` into an :class:`!Align`::

    >>> cnt.del_sites(2, 20, 7)
    >>> aln = egglib.Align.create(cnt)
    >>> print(aln.is_matrix)
    True
    >>> print(aln.fasta())
    >sample1
    ACCGTGGAGAGCGCGTTGCA
    >sample2
    ACCGTGGAGAGCGCGTTGCA
    >sample3
    ACCGTGGAGAGCGCGTTGCA
    >sample4
    ACCGTGGAGAGCGCGTTGCA

Creation from other iterable types
**********************************

Besides :class:`!Align` and :class:`!Container` instances, the method 
:meth:`!create` supports all compatible iterable object. To be 
compatible, an object must return, during iteration, ``(name, 
sequence)`` or ``(name, sequence, groups)`` items, where ``name`` is a 
name string, ``sequence`` is a sequence string (or a list of data 
entries), and ``groups`` (which may be omitted) is a list of group 
labels. For creating an :class:`!Align`, it is required that all 
sequences match in length. Typically, instances can be created from 
lists using this way::

    >>> aln = egglib.Align.create([('sample1', 'ACCGTGGAGAGCGCGTTGCA'),
    ...                            ('sample2', 'ACCGTGGAGAGCGCGTTGCA'),
    ...                            ('sample3', 'ACCGTGGAGAGCGCGTTGCA'),
    ...                            ('sample4', 'ACCGTGGAGAGCGCGTTGCA')],
    ...                            alphabet = egglib.alphabets.DNA)
    >>> print(aln.fasta())
    >sample1
    ACCGTGGAGAGCGCGTTGCA
    >sample2
    ACCGTGGAGAGCGCGTTGCA
    >sample3
    ACCGTGGAGAGCGCGTTGCA
    >sample4
    ACCGTGGAGAGCGCGTTGCA

The code above re-creates the alignment discussed in the previous 
section. Note that there is a method of :class:`!Container`, 
:meth:`~.Container.equalize`, that inserts stretches of ``?`` at the 
end of sequences of a :class:`!Container` in order to have all 
sequences of the same length. In such case, the :class:`!Container` 
could be converted to an :class:`!Align` using :meth:`.Align.create`, 
but it is not probably not what you want to do if you want to align 
sequences.

Add/remove samples
==================

Both :class:`!Align` and :class:`!Container` support the following operations
to change the list of samples of an instance:

+-----------------------------------------+-----------------------------------------------+---------------------+
| Method                                  | Syntax                                        | Action              |
+=========================================+===============================================+=====================+
| :meth:`~.Container.add_sample`          | ``cnt.add_sample(name, sequence[, groups])``  | Add a sample        |
+-----------------------------------------+-----------------------------------------------+---------------------+
| :meth:`~.Container.add_samples`         | ``cnt.add_samples(samples)``                  | Add several samples | 
+-----------------------------------------+-----------------------------------------------+---------------------+
| :meth:`~.Container.del_sample`          | ``cnt.del_sample(index)``                     | Delete a sample     |
+-----------------------------------------+-----------------------------------------------+---------------------+
| :meth:`~.Container.reset`               | ``cnt.reset()``                               | Remove all samples  |
+-----------------------------------------+-----------------------------------------------+---------------------+
| :meth:`~.Container.remove_duplicates()` | ``cnt.remove_duplicates()``                   | Remove duplicates   |
+-----------------------------------------+-----------------------------------------------+---------------------+

Editing alignments
==================

:class:`!Align` instances have additional methods that allow to extract or delete
sections of the alignment

+--------------------------------+---------------------------------------+----------------------------------------------------------+
| Method                         | Syntax                                | Action                                                   |
+================================+=======================================+==========================================================+
| :meth:`~.Align.column`         | ``aln.column(i)``                     | Extract a site as a list (1)                             |
+--------------------------------+---------------------------------------+----------------------------------------------------------+
| :meth:`~.Align.insert_columns` | ``aln.insert_columns(i, values)``     | Insert columns at a given position                       |
+--------------------------------+---------------------------------------+----------------------------------------------------------+
| :meth:`~.Align.del_columns`    | ``aln.del_columns(i[, num])``         | Delete one or more columns                               |
+--------------------------------+---------------------------------------+----------------------------------------------------------+
| :meth:`~.Align.extract`        | ``sub = aln.extract(start, stop)``    | Extract a specified range of positions                   |
+                                +---------------------------------------+----------------------------------------------------------+
|                                | ``sub = aln.extract(frame)``          | Extract exon positions based on a :class:`.ReadingFrame` |
+                                +---------------------------------------+----------------------------------------------------------+
|                                | ``sub = aln.extract([i, j, ..., z])`` | Extract an arbitrary list of positions                   |
+--------------------------------+---------------------------------------+----------------------------------------------------------+
| :meth:`~.Align.subset`         | ``sub = aln.subset(samples)``         | Generate a new instance with selected samples (1)        |
+--------------------------------+---------------------------------------+----------------------------------------------------------+
| :meth:`~.Align.intersperse`    | ``aln.intersperse(len[, ...])``       | Insert non-varying sites randomly                        |
+--------------------------------+---------------------------------------+----------------------------------------------------------+
| :meth:`~.Align.random_missing` | ``aln.random_missing(p[, ...])``      | Insert missing data randomly (1)                         |
+--------------------------------+---------------------------------------+----------------------------------------------------------+
| :meth:`~.Align.fix_ends`       | ``aln.fix_ends()``                    | Replace alignment gaps at ends by missing data           |
+--------------------------------+---------------------------------------+----------------------------------------------------------+

Note:
    1. Also available for :class:`!Container`.

The following functions lie in the :ref:`tools <tools>` module and provide additional
functionalities to manipulate alignments:

+--------------------------+----------------------------------------------+-------------------------------------------------------------------------+
| Function                 | Syntax                                       | Action                                                                  |
+==========================+==============================================+=========================================================================+
| :func:`.tools.concat`    | ``res = egglib.tool.concat(aln1, aln2)``     | Concatenate alignments                                                  |
+--------------------------+----------------------------------------------+-------------------------------------------------------------------------+
| :func:`.tools.ungap`     | ``cnt = egglib.tools.ungap(aln)``            | Remove all gaps from an alignment                                       |
+                          +----------------------------------------------+-------------------------------------------------------------------------+
|                          | ``aln2 = egglib.tools.sungap(aln, p)``       | Remove sites with too many gaps                                         |
+--------------------------+----------------------------------------------+-------------------------------------------------------------------------+
| :func:`.tools.backalign` | ``aln = egglib.tools.backalign(nucl, prot)`` | Align (unaligned) nucleotide sequences based on an amino acid alignment |
+--------------------------+----------------------------------------------+-------------------------------------------------------------------------+
