"""
    Copyright 2008-2026 Stéphane De Mita, Mathieu Siol

    This file is part of EggLib.

    EggLib is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    EggLib is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with EggLib.  If not, see <http://www.gnu.org/licenses/>.
"""

import re, operator, functools
from . import eggwrapper as _eggwrapper
from . import alphabets
from . import random
from . import _site
from .tools._reading_frame import ReadingFrame

_CONSENSUS_MAPPING_SOURCE = {('A', 'A'): 'A', ('A', 'C'): 'M', ('A', 'G'): 'R', ('A', 'T'): 'W', ('A', '-'): '?', ('A', 'N'): 'N', ('A', '?'): '?', ('A', 'R'): 'R', ('A', 'Y'): 'H', ('A', 'S'): 'V', ('A', 'W'): 'W', ('A', 'K'): 'D', ('A', 'M'): 'M', ('A', 'B'): 'N', ('A', 'D'): 'D', ('A', 'H'): 'H', ('A', 'V'): 'V',
                             ('C', 'A'): 'M', ('C', 'C'): 'C', ('C', 'G'): 'S', ('C', 'T'): 'Y', ('C', '-'): '?', ('C', 'N'): 'N', ('C', '?'): '?', ('C', 'R'): 'V', ('C', 'Y'): 'Y', ('C', 'S'): 'S', ('C', 'W'): 'H', ('C', 'K'): 'B', ('C', 'M'): 'M', ('C', 'B'): 'B', ('C', 'D'): 'N', ('C', 'H'): 'H', ('C', 'V'): 'V',
                             ('G', 'A'): 'R', ('G', 'C'): 'S', ('G', 'G'): 'G', ('G', 'T'): 'K', ('G', '-'): '?', ('G', 'N'): 'N', ('G', '?'): '?', ('G', 'R'): 'R', ('G', 'Y'): 'B', ('G', 'S'): 'S', ('G', 'W'): 'D', ('G', 'K'): 'K', ('G', 'M'): 'V', ('G', 'B'): 'B', ('G', 'D'): 'D', ('G', 'H'): 'N', ('G', 'V'): 'V',
                             ('T', 'A'): 'W', ('T', 'C'): 'Y', ('T', 'G'): 'K', ('T', 'T'): 'T', ('T', '-'): '?', ('T', 'N'): 'N', ('T', '?'): '?', ('T', 'R'): 'D', ('T', 'Y'): 'Y', ('T', 'S'): 'B', ('T', 'W'): 'W', ('T', 'K'): 'K', ('T', 'M'): 'H', ('T', 'B'): 'B', ('T', 'D'): 'D', ('T', 'H'): 'H', ('T', 'V'): 'N',
                             ('-', 'A'): '?', ('-', 'C'): '?', ('-', 'G'): '?', ('-', 'T'): '?', ('-', '-'): '-', ('-', 'N'): '?', ('-', '?'): '?', ('-', 'R'): '?', ('-', 'Y'): '?', ('-', 'S'): '?', ('-', 'W'): '?', ('-', 'K'): '?', ('-', 'M'): '?', ('-', 'B'): '?', ('-', 'D'): '?', ('-', 'H'): '?', ('-', 'V'): '?',
                             ('N', 'A'): 'N', ('N', 'C'): 'N', ('N', 'G'): 'N', ('N', 'T'): 'N', ('N', '-'): '?', ('N', 'N'): 'N', ('N', '?'): '?', ('N', 'R'): 'N', ('N', 'Y'): 'N', ('N', 'S'): 'N', ('N', 'W'): 'N', ('N', 'K'): 'N', ('N', 'M'): 'N', ('N', 'B'): 'N', ('N', 'D'): 'N', ('N', 'H'): 'N', ('N', 'V'): 'N',
                             ('?', 'A'): '?', ('?', 'C'): '?', ('?', 'G'): '?', ('?', 'T'): '?', ('?', '-'): '?', ('?', 'N'): '?', ('?', '?'): '?', ('?', 'R'): '?', ('?', 'Y'): '?', ('?', 'S'): '?', ('?', 'W'): '?', ('?', 'K'): '?', ('?', 'M'): '?', ('?', 'B'): '?', ('?', 'D'): '?', ('?', 'H'): '?', ('?', 'V'): '?',
                             ('R', 'A'): 'R', ('R', 'C'): 'V', ('R', 'G'): 'R', ('R', 'T'): 'D', ('R', '-'): '?', ('R', 'N'): 'N', ('R', '?'): '?', ('R', 'R'): 'R', ('R', 'Y'): 'N', ('R', 'S'): 'V', ('R', 'W'): 'D', ('R', 'K'): 'D', ('R', 'M'): 'V', ('R', 'B'): 'N', ('R', 'D'): 'D', ('R', 'H'): 'N', ('R', 'V'): 'V',
                             ('Y', 'A'): 'H', ('Y', 'C'): 'Y', ('Y', 'G'): 'B', ('Y', 'T'): 'Y', ('Y', '-'): '?', ('Y', 'N'): 'N', ('Y', '?'): '?', ('Y', 'R'): 'N', ('Y', 'Y'): 'Y', ('Y', 'S'): 'B', ('Y', 'W'): 'H', ('Y', 'K'): 'B', ('Y', 'M'): 'H', ('Y', 'B'): 'B', ('Y', 'D'): 'N', ('Y', 'H'): 'H', ('Y', 'V'): 'N',
                             ('S', 'A'): 'V', ('S', 'C'): 'S', ('S', 'G'): 'S', ('S', 'T'): 'B', ('S', '-'): '?', ('S', 'N'): 'N', ('S', '?'): '?', ('S', 'R'): 'V', ('S', 'Y'): 'B', ('S', 'S'): 'S', ('S', 'W'): 'N', ('S', 'K'): 'B', ('S', 'M'): 'V', ('S', 'B'): 'B', ('S', 'D'): 'N', ('S', 'H'): 'N', ('S', 'V'): 'V',
                             ('W', 'A'): 'W', ('W', 'C'): 'H', ('W', 'G'): 'D', ('W', 'T'): 'W', ('W', '-'): '?', ('W', 'N'): 'N', ('W', '?'): '?', ('W', 'R'): 'D', ('W', 'Y'): 'H', ('W', 'S'): 'N', ('W', 'W'): 'W', ('W', 'K'): 'D', ('W', 'M'): 'H', ('W', 'B'): 'N', ('W', 'D'): 'D', ('W', 'H'): 'H', ('W', 'V'): 'N',
                             ('K', 'A'): 'D', ('K', 'C'): 'B', ('K', 'G'): 'K', ('K', 'T'): 'K', ('K', '-'): '?', ('K', 'N'): 'N', ('K', '?'): '?', ('K', 'R'): 'D', ('K', 'Y'): 'B', ('K', 'S'): 'B', ('K', 'W'): 'D', ('K', 'K'): 'K', ('K', 'M'): 'N', ('K', 'B'): 'B', ('K', 'D'): 'D', ('K', 'H'): 'N', ('K', 'V'): 'N',
                             ('M', 'A'): 'M', ('M', 'C'): 'M', ('M', 'G'): 'V', ('M', 'T'): 'H', ('M', '-'): '?', ('M', 'N'): 'N', ('M', '?'): '?', ('M', 'R'): 'V', ('M', 'Y'): 'H', ('M', 'S'): 'V', ('M', 'W'): 'H', ('M', 'K'): 'N', ('M', 'M'): 'M', ('M', 'B'): 'N', ('M', 'D'): 'N', ('M', 'H'): 'H', ('M', 'V'): 'V',
                             ('B', 'A'): 'N', ('B', 'C'): 'B', ('B', 'G'): 'B', ('B', 'T'): 'B', ('B', '-'): '?', ('B', 'N'): 'N', ('B', '?'): '?', ('B', 'R'): 'N', ('B', 'Y'): 'B', ('B', 'S'): 'B', ('B', 'W'): 'N', ('B', 'K'): 'B', ('B', 'M'): 'N', ('B', 'B'): 'B', ('B', 'D'): 'N', ('B', 'H'): 'N', ('B', 'V'): 'N',
                             ('D', 'A'): 'D', ('D', 'C'): 'N', ('D', 'G'): 'D', ('D', 'T'): 'D', ('D', '-'): '?', ('D', 'N'): 'N', ('D', '?'): '?', ('D', 'R'): 'D', ('D', 'Y'): 'N', ('D', 'S'): 'N', ('D', 'W'): 'D', ('D', 'K'): 'D', ('D', 'M'): 'N', ('D', 'B'): 'N', ('D', 'D'): 'D', ('D', 'H'): 'N', ('D', 'V'): 'N',
                             ('H', 'A'): 'H', ('H', 'C'): 'H', ('H', 'G'): 'N', ('H', 'T'): 'H', ('H', '-'): '?', ('H', 'N'): 'N', ('H', '?'): '?', ('H', 'R'): 'N', ('H', 'Y'): 'H', ('H', 'S'): 'N', ('H', 'W'): 'H', ('H', 'K'): 'N', ('H', 'M'): 'H', ('H', 'B'): 'N', ('H', 'D'): 'N', ('H', 'H'): 'H', ('H', 'V'): 'N',
                             ('V', 'A'): 'V', ('V', 'C'): 'V', ('V', 'G'): 'V', ('V', 'T'): 'N', ('V', '-'): '?', ('V', 'N'): 'N', ('V', '?'): '?', ('V', 'R'): 'V', ('V', 'Y'): 'N', ('V', 'S'): 'V', ('V', 'W'): 'N', ('V', 'K'): 'N', ('V', 'M'): 'V', ('V', 'B'): 'N', ('V', 'D'): 'N', ('V', 'H'): 'N', ('V', 'V'): 'V'}
_CONSENSUS_MAPPING = {}
for (a, b), c in _CONSENSUS_MAPPING_SOURCE.items():
    a, b, c = map(alphabets.DNA.get_code, (a, b, c))
    _CONSENSUS_MAPPING[(a,b)] = c
_alleles = alphabets.DNA.get_alleles()
_alleles = _alleles[0] + _alleles[1]
for i in _alleles:
    c = alphabets.DNA.get_code(i)
    _CONSENSUS_MAPPING[(None, c)] = c
del _alleles, i

class SampleView(object):
    """
    Proxy class representing a given sample.
    :class:`!SampleView` objects allow iteration and general
    manipulation of (large) data sets stored in an
    :class:`.Align` or a :class:`.Container` instance
    without unnecessary extraction of
    full sequences. Modifications of :class:`!SampleView` objects are
    immediately applied to the underlying data holder object.
    :class:`!SampleView` instances are iterable.

    In principle, only :class:`!Align` and :class:`!Container` instances
    are supposed to build :class:`!SampleView` instances.

    :param parent: a :class:`!Align` or :class:`!Container` instance.
    :param index: an index within the parent instance.
    """
    def __init__(self, parent, index):
        self._parent = parent
        self._index = index
        self._sequence = SequenceView(self._parent, self._index)
        self._labels = LabelView(self._parent, self._index)

    @property
    def ls(self):
        """
        Length of the sequence. If the underlying object is an
        :class:`!Align` instance, this is the alignment length. Otherwise,
        this is the length of this particular sequence.
        """
        if self._parent._is_matrix:
            return self._parent._obj.get_nsit_all()
        else:
            return self._parent._obj.get_nsit_sample(self._index)

    def __iter__(self):
        for i in (self.name, self.sequence, self.labels):
            yield i

    def __len__(self):
        return 3

    def __getitem__(self, index):
        if index == 0: return self.name
        elif index == 1: return self.sequence
        elif index == 2: return self.labels
        elif isinstance(index, int):
            if index < 0: raise ValueError('negative indexes are not supported by SampleIndex')
            raise IndexError('SampleView instances contain only three items')
        elif isinstance(index, slice): raise ValueError('slices are not supported by SampleIndex')
        else: raise TypeError('invalid type passed as index')

    @property
    def index(self):
        """
        Index of the sample. Index of the sample within the
        :class:`!Align` or
        :class:`!Container` instance containing this sample.
        """
        return self._index

    @property
    def parent(self):
        """
        Reference of the parent. Reference of the :class:`!Align` or
        :class:`!Container` instance containing this sample.
        """
        return self._parent

    @property
    def name(self):
        """
        Sample name. The name can be modified by a new string.
        """
        return self._parent._obj.get_name(self._index)

    @name.setter
    def name(self, value):
        if not isinstance(value, str): raise TypeError('name must be a string')
        self._parent._obj.set_name(self._index, value)

    @property
    def sequence(self):
        """
        Access to allele values. This attribute is represented by a
        :class:`.SequenceView` instance which allow modifying the
        underlying sequence container object through its own attributes
        and methods. It is also possible to change this member
        altogether using either a string, a list of allele values
        (matching the alphabet of the parent instance). When
        modifying an :class:`!Align` instance, all sequences must have
        the same length as the current alignment length.
        """
        return self._sequence

    @sequence.setter
    def sequence(self, value):
        self._parent.set_sequence(self._index, value)

    @property
    def labels(self):
        """
        Access to labels. Return a :class:`.LabelView` instance
        which can be modified to edit labels. This attribute can also
        be modified altogether using a list of labels of any length,
        erasing completely the previous list of labels.
        """
        return self._labels

    @labels.setter
    def labels(self, value):
        self._parent._obj.set_nlabels(self._index, len(value))
        if isinstance(value, str): raise TypeError('labels must be a list of strings')
        for i, v in enumerate(value):
            if v is None: v = ''
            if not isinstance(v, str): raise TypeError('labels must be a list of strings')
            self._parent._obj.set_label(self._index, i, v)

class SequenceView(object):
    """
    Proxy class representing the sequence of a given sample.
    This class manages the sequence of a sample of an :class:`.Align`
    or :class:`.Container` instance. It can be obtained directly from
    one of those classes or from the intermediate :class:`.SampleView`.

    In principle, only :class:`!SampleView`, :class:`!Align`, and
    :class:`!Container` instances are supposed to build
    :class:`!SequenceView` instances.

    :param parent: a :class:`!Align` or :class:`!Container` instance.
    :param index: an index within the parent instance.

    :class:`!SequenceView` instances behave somewhat like editable
    strings. They support the following operations:

    +-----------------------+----------------------------------------------+-------+
    | Operation             | Action                                       | Notes |
    +=======================+==============================================+=======+
    | ``len(seq)``          | length of the sequence                       | (1)   |
    +-----------------------+----------------------------------------------+-------+
    | ``for i in seq: ...`` | iterate over alleles                         |       |
    +-----------------------+----------------------------------------------+-------+
    | ``a = seq[i]``        | get allele at index *i*                      |       |
    +-----------------------+----------------------------------------------+-------+
    | ``s = seq[i:j]``      | get alleles from index *i* to index *j*-1    |       |
    +-----------------------+----------------------------------------------+-------+
    | ``seq[i] = a``        | modify allele *i* by *a*                     |       |
    +-----------------------+----------------------------------------------+-------+
    | ``seq[i:j] = s``      | modify alleles *i* to *j*-1                  | (2)   |
    +-----------------------+----------------------------------------------+-------+
    | ``del seq[i]``        | remove allele at index *i*                   | (3)   |
    +-----------------------+----------------------------------------------+-------+
    | ``del seq[i:j]``      | remove alleles from index *i* to index *j*-1 | (3)   |
    +-----------------------+----------------------------------------------+-------+

    Notes:

    #. This is the same as the alignment length for an :class:`!Align` and
       can also be accessed as :py:obj:`!SampleView.ls` on the corresponding
       :class:`!SampleView` instance.

    #. The length of *s* is required to be equal to ``(j-i)`` (replacing a
       segment by a segment of the same size) if the parent instance is
       an :class:`!Align`, otherwise it can have a different length.

    #. Only available if the parent instance is a :class:`!Container`.

    .. note::

        When editing large sequences, it is much more efficient to use
        the operators described above than replace the whole sequence by
        the edited one.
    """

    def __init__(self, parent, index):
        self._parent = parent
        self._index = index

    def __iter__(self):
        for i in range(len(self)):
            yield self._parent.get(self._index, i)

    def string(self):
        """
        Generate a string from all data entries by concatenating all
        allelic values. The alphabet type must be character or string.

        :return: A string.
        """
        if self._parent._alphabet._obj.get_type() not in ['DNA', 'char', 'string', 'codons']:
            raise ValueError('cannot generate sequence string with alphabet {0}'.format(self._parent._alphabet.name))
        return ''.join(self)

    def __getitem__(self, index):
        if isinstance(index, slice):
            if self._parent._alphabet._obj.get_type() in ['char', 'string', 'DNA', 'codons']:
                return ''.join([self._parent.get(self._index, i) for i in range(* index.indices(len(self)))])
            else:
                return [self._parent.get(self._index, i) for i in range(* index.indices(len(self)))]
        elif isinstance(index, int):
            if index < 0:
                index = len(self) + index
                if index < 0: raise IndexError('data index out of range')
            return self._parent.get(self._index, index)
        else:
            raise TypeError('invalid index type')

    def __setitem__(self, index, value):
        if isinstance(index, int):
            # all checking is done by set_sampple
            self._parent.set(self._index, index, value)

        elif isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            num = stop - start

            # allow a non-None argument only if the number values matches
            if step != 1:
                indices = list(range(start, stop, step))
                if len(indices) != len(value): raise ValueError('the number of values must match when a step is used')
                for i,j in zip(indices, value):
                    self._parent.set(self._index, i, j)
                # from now, the step may be ignored

            # conservative set (except those with step)
            elif num == len(value):
                for i, j in zip(range(start, stop), value):
                    self._parent.set(self._index, i, j)

            # non conservative set
            else:
                if self._parent._is_matrix:
                    raise ValueError('the length of the sequence cannot be changed -- provided {0} data items (required: {1})'.format(len(value), num))

                # insert
                if len(value) > num:
                    self._parent.insert_sites(self._index, stop, value[num:])
                    for i,v in enumerate(value[:num]): self._parent.set(self._index, start+i, v)

                # delete
                elif len(value) < num:
                    self._parent._obj.del_sites_sample(self._index, start+len(value), start+num)
                    for i,v in enumerate(value): self._parent.set(self._index, start+i, v)

                else:
                    raise RuntimeError('Wait.  What am I doing here?')

        else:
            raise TypeError('invalid index type')

    def __delitem__(self, sites):
        if self._parent._is_matrix:
            raise ValueError('cannot delete sites from an Align\'s sequence')
        if isinstance(sites, int):
            self._parent._obj.del_sites_sample(self._index, sites, 1)
        elif isinstance(sites, slice):
            start, stop, step = sites.indices(len(self))
            if step == 1:
                self._parent._obj.del_sites_sample(self._index, start, stop-start)
            elif step < 0:
                raise ValueError('negative step is not supported for deleting') # because we will process sites backward (to avoid site shifting and be more efficient)
            else:
                for i in list(range(start, stop, step))[::-1]:
                    self._parent._obj.del_sites_sample(self._index, i, i+1)
        else:
            raise TypeError('invalid index type')
 
    def __len__(self):
        if self._parent._is_matrix: return self._parent._obj.get_nsit_all()
        else: return self._parent._obj.get_nsit_sample(self._index)

    def insert(self, position, values):
        """
        Insert data entries. This method is only available for samples belonging to a
        :class:`!Container` instance. For :class:`!Align` instances,
        it is possible to insert data entries to all samples using
        the method :meth:`~.Align.insert_columns`.

        :param position: the position at which to insert sites. The new
            sites are inserted before the specified index. Use 0 to add
            sites at the beginning of the sequence, and the current
            number of sites for this sample to add sites at the end. If
            the value is larger than the current number of sites for
            this sample, or if ``None`` is provided, new sites are added
            at the end of the sequence.
        :param values: list of allelic values to insert in the sequence.
        """
        if self._parent._is_matrix:
            raise ValueError('cannot insert sites in sequences from an Align')
        self._parent.insert_sites(self._index, position, values)

    def find(self, motif, start=0, stop=None):
        """
        Locate the first instance of a motif.
        Return the index of the first exact hit to a given substring.
        The returned value is the position of the first base of the hit.
        Only exact forward matches are implemented. To use regular expression
        (for example to find degenerated motifs), one should extract the
        string for the sequence and use a tool such as the regular
        expression module (:mod:`re`).

        :param motif: list of allelic values constituting the motif to search.
        :param start: position at which to start searching. The method
            will never return a value smaller than *start*. By default,
            search from the start of the sequence.
        :param stop: position at which to stop search (the motif
            cannot overlap this position). No returned value will be
            larger than ` stop - len(motif)``. By default, or if *stop*
            is equal to
            or larger than the length of the sequence, search until the
            end of the sequence.
        :return: An integer.
        """
        return self._parent.find_motif(self._index, motif, start, stop)

    def upper(self, start=0, stop=None):
        """
        Converts allele values of this sample to upper case. Only
        applicable for characters that have an upper case equivalent. All
        other allele values are ignored. The underlying object data is
        modified and this method returns ``None``. Only accepted for
        case-sensitive character and string alphabets. Furthermore, all
        lower case alleles that are implied are required to be valid
        alleles in the alphabet.

        :param start: index of the first allele to convert. By default,
            from the start of the sequence.
        :param stop: stop index (index of the allele immediately after
            the last allele to convert). By default, to the end of the
            sequence.
        """
        self._parent.upper(self._index, start, stop)

    def lower(self, start=0, stop=None):
        """
        Converts allele values of this sample to lower case. Only accepted for
        case-sensitive character and string alphabet. The alphabet must
        support all lower-case alleles that will be generated. Alleles that don't
        have a lower-case equivalent are ignored. The underlying object data is
        modified and this method returns ``None``

        :param start: index of the first allele to convert. By default,
            from the start of the sequence.
        :param stop: stop index (index of the allele immediately after
            the last allele to convert). By default, to the end of the
            sequence.
        """
        self._parent.lower(self._index, start, stop)

    def strip(self, values):
        """
        Delete leading and trailing occurrences of any characters
        given in the *values* argument. The underlying object is
        modified and this method returns ``None``. See also :meth:`.lstrip`
        and :meth:`.rstrip`.

        :param values: an iterable containing the allelic values
            to strip out. They must be all be
            valid values with respect to the current alphabet. Repetitions
            are silently supported.
        """
        self._parent._obj.strip_clear()
        for v in values: self._parent._obj.strip_add(self._parent._alphabet.get_code(v))
        self._parent._obj.strip(self._index, True, True)

    def lstrip(self, values):
        """
        Delete leading occurrences of any characters
        given in the *values* argument (starting from the beginning).
        The underlying object is
        modified and this method returns ``None``.

        :param values: an iterable containing the allelic values
            to strip out. They must be all be
            valid values with respect to the current alphabet. Repetitions
            are silently supported.
        """
        self._parent._obj.strip_clear()
        for v in values: self._parent._obj.strip_add(self._parent._alphabet.get_code(v))
        self._parent._obj.strip(self._index, True, False)

    def rstrip(self, values):
        """
        Delete trailing occurrences of any characters
        given in the *values* argument (starting from the end).
        The underlying object is
        modified and this method returns ``None``.

        :param values: an iterable containing the allelic values
            to strip out. They must be all be
            valid values with respect to the current alphabet. Repetitions
            are silently supported.
        """
        self._parent._obj.strip_clear()
        for v in values: self._parent._obj.strip_add(self._parent._alphabet.get_code(v))
        self._parent._obj.strip(self._index, False, True)

class LabelView(object):
    """
    Proxy class representing the labels of a given sample.
    This class manages the list of labels of a sample of the
    :class:`.Align` and :class:`.Container` classes. This class can be
    considered as a list of unsigned integers, is iterable.

    In principle, only :class:`!SampleView`, :class:`!Align`, and
    :class:`!Container` instances are supposed to build
    :class:`!LabelView` instances.

    :param parent: a :class:`!Align` or :class:`!Container` instance.
    :param index: an index within the parent instance.

    :class:`!LabelView` instances support the following operations:

    +----------------------------+----------------------------------+
    | Operation                  | Action                           |
    +============================+==================================+
    | ``len(labels)``            | number of labels for this sample |
    +----------------------------+----------------------------------+
    | ``for lbl in labels: ...`` | iterate over labels              |
    +----------------------------+----------------------------------+
    | ``labels[i]``              | get an arbitrary label           |
    +----------------------------+----------------------------------+
    | ``labels[i] = lbl``        | modify label *i*                 |
    +----------------------------+----------------------------------+
    """
    def __init__(self, parent, index):
        self._parent = parent
        self._index = index

    def __len__(self):
        if self._index >= self._parent._obj.get_nsam(): raise ValueError('invalid sample index')
        return self._parent._obj.get_nlabels(self._parent._sample(self._index))

    def __iter__(self):
        if self._index >= self._parent._obj.get_nsam(): raise ValueError('invalid sample index')
        for i in range(self._parent._obj.get_nlabels(self._index)):
            v = self._parent._obj.get_label(self._parent._sample(self._index), i)
            if v == '': yield None
            else: yield v

    def __getitem__(self, index):
        v = self._parent.get_label(self._index, index)
        if v == '': return None
        else: return v

    def __setitem__(self, index, value):
        if value is None: value = ''
        if not isinstance(value, str): raise TypeError('labels must be strings')
        self._parent.set_label(self._index, index, value)

    def append(self, value):
        """
        Add a label at the end of the list.
        """
        self._parent._obj.add_label(self._parent._sample(self._index), value)

class Base(object):
    @classmethod
    def _create_from_data_holder(cls, obj, alphabet):
        if not isinstance(obj, _eggwrapper.DataHolder):
            raise TypeError('unsupported type: {0}'.format(type(obj)))

        new_instance = cls.__new__(cls)
        if cls == Align:
            if not obj.get_is_matrix():
                if obj.get_nsam() != 0:
                    ls = obj.get_nsit_sample(0) # there is at least one sample
                    for i in range(1, obj.get_nsam()):
                        if obj.get_nsit_sample(i) != ls: raise ValueError('cannot convert non-matrix DataHolder to Align: sequence lengths don\'t match')
            obj.set_is_matrix(True)
            new_instance._is_matrix = True
            new_instance._window = None
        else:
            obj.set_is_matrix(False)
            new_instance._is_matrix = False
        new_instance._ns = obj.get_nsam()
        new_instance._motif = _eggwrapper.VectorInt()
        new_instance._obj = obj
        new_instance._alphabet = alphabet
        return new_instance

    def _reset_from_data_holder(self, obj):
        if isinstance(obj, _eggwrapper.DataHolder):
            if self._is_matrix:
                if not obj.get_is_matrix():
                    if obj.get_nsam() != 0:
                        for i in range(1, obj.get_nsam()):
                            if obj.get_nsit_sample(i) != ls: raise ValueError('cannot convert non-matrix DataHolder to Align: sequence lengths don\'t match')
                obj.set_is_matrix(True)
                self._window = None
            else:
                obj.set_is_matrix(False)
            self._ns = obj.get_nsam()
            self._obj = obj
        else:
            raise TypeError('unsupported type: {0}'.format(type(obj)))

    @classmethod
    def create(cls, source, alphabet=None):
        """
        Copy provided data and create a new instance.

        :param source: input data
        :param alphabet: an :class:`.Alphabet` instance (only if  *source*
            is not an :class:`.Align` or a :class:`.Container`).

        The object *source* can be:

        * an :class:`.Align`,
        * a :class:`.Container`,
        * a list containing acceptable items (as described in :meth:`~.Align.add_samples`).

        To be used as in::

            >>> aln = egglib.Align.create([('name1', 'AAACCGGCAC', [0]),
            ...     ('name2', 'AAACCTGCCC', [0]), ('name3', 'TCACCGGCAA', [1])
            ...     ('name4', 'TCAGAGGCAA', [1])], alphabet=egglib.alphabets.DNA)

        or in::

            >>> aln2 = egglib.Container.create(aln)

        The type of the created object is determined by the class on which
        you call the method. The object passed an argument can be an
        instance of the same type or not, or a compatible list. It is therefore
        possible to convert between :class:`!Align` and :class:`!Container`
        (but note that in the case of a :class:`!Container` to :class:`!Align`
        conversion, all sequences must have the same length).
        """

        new_instance = cls.__new__(cls)

        if not isinstance(source, (Align, Container)):
            if alphabet is None: raise ValueError('alphabet is required for object creation from an iterable')
            new_instance.__init__(alphabet)
            new_instance.add_samples(source)

        else:
            if alphabet is not None: raise ValueError('it is not allowed to change alphabet when copying an object')
            new_instance.__init__(source._alphabet)
            new_instance._ns = source._ns
            new_instance._obj.set_nsam(source._ns)
            for i in range(source._ns):
                new_instance._obj.set_name(i, source._obj.get_name(i))
                new_instance._obj.set_nlabels(i, source._obj.get_nlabels(i))
                for j in range(source._obj.get_nlabels(i)):
                    new_instance._obj.set_label(i, j, source._obj.get_label(i, j))

            if cls is Align:
                if isinstance(source, Align):
                    ls = source._obj.get_nsit_all()
                else:
                    ls = set(source._obj.get_nsit_sample(i) for i in range(source._ns))
                    if len(ls) == 0: ls = 0
                    elif len(ls) > 1: raise ValueError('cannot convert Container to Align: sequence lengths must match')
                    else: ls = ls.pop()
                new_instance._obj.set_nsit_all(ls)
                for i in range(source._ns):
                    for j in range(ls):
                        new_instance._obj.set_sample(i, j, source._obj.get_sample(i, j))

            else:
                if isinstance(source, Align):
                    ls = [source._obj.get_nsit_all()] * source._ns
                else:
                    ls = [source._obj.get_nsit_sample(i) for i in range(source._ns)]
                for i in range(source._ns):
                    new_instance._obj.set_nsit_sample(i, ls[i])
                    for j in range(ls[i]):
                        new_instance._obj.set_sample(i, j, source._obj.get_sample(i, j))

        return new_instance

    def __init__(self):
        raise NotImplementedError('cannot create a Base instance')

    @property
    def alphabet(self):
        """
        :class:`~.Alphabet` instance associated to this object. This
        member cannot be modified.
        """
        return self._alphabet

    def fasta(self, fname=None, first=None, last=None,
        alphabet=None, labels=False, linelength=50):
        """
        Export alignment in the fasta format. The data are required to
        be encoded using a char or a string alphabet. If not, the user
        may use the *alphabet* argument to pass a valid
        alphabet that will be used for exporting.

        :param fname: name of the file to export data to. By default, the
            file is created (or overwritten if it already exists). If the
            option *append* is ``True``, data is appended at the end of the
            file (and it must exist). If *fname* is ``None`` (default), no
            file is created and the formatted data is returned as a
            string. In the alternative case, nothing is returned and the
            fasta string is written to a file.

        :param first: if only part of the sequences should be exported:
            index of the first sequence to export. By default, use the
            first sequence if any, otherwise, generate an empty string.

        :param last: if only part of the sequences should be exported: index
            of the last sequence to export. If the value is larger than the
            index of the last sequence, all sequences are exported until the
            last (this is the default). If *last* < *first*, no sequences are
            exported.

        :param alphabet: exporting class:`.Alphabet` instance to use
            instead of the instance's alphabet. The provided
            alphabet must contain character or string values, and all data in
            the object must be valid with respect to this alphabet. All
            alleles of the instance are mapped to an allele of the exporting
            alphabet based on their rank in their respective alphabets.

        :param labels: a boolean indicating whether group labels
            should be exported or ignored.

        :param linelength: the length of lines for internal breaking of
            sequences.

        :return: If *fname* is ``None``: a fasta-formatted string.
            Otherwise: ``None``.
        """
        fasta_formatter = _eggwrapper.FastaFormatter()
        if fname != None:
            if fasta_formatter.open_file(fname) == False:
                raise ValueError('cannot open {0}'.format(fname))
        else:
            fasta_formatter.to_str()
        if first is None: first = 0
        else: first = self._sample(first)
        if last is None: last = _eggwrapper.MAX
        if alphabet is None: alphabet = self._alphabet
        fasta_formatter.set_first(first)
        fasta_formatter.set_last(last)
        fasta_formatter.set_labels(labels)
        if linelength < 1: raise ValueError('too small value for `linelength` argument')
        fasta_formatter.set_linelength(linelength)
        fasta_formatter.write(self._obj, alphabet._obj)
        if fname == None:
            ret = fasta_formatter.get_str()
            return ret
        else:
            del fasta_formatter # force closing of file

    def clear(self):
        """
        Clear the instance and release all memory. In most cases, it is
        preferable to use the method :meth:`~.Align.reset`.
        """
        self._obj.clear(self._is_matrix)
        self._ns = 0
        self._motif.clear()

    def reset(self, alphabet=None):
        """
        Reset the instance. If the alphabet is specified, it replaces
        the previous one.
        """
        self._obj.reset(self._is_matrix)
        self._ns = 0
        if alphabet is not None: self._alphabet = alphabet

    @property
    def is_matrix(self):
        """
        ``True`` if the instance is an :class:`.Align`, and ``False`` if
        it is a :class:`.Container`.
        """
        return self._is_matrix

    def __len__(self):
        return self._ns

    @property
    def ns(self):
        """
        Number of samples.
        """
        return self._ns

    def add_sample(self, name, data, labels=None):
        """
        Add a sample to the instance.

        :param name: name of the new sample.
        :param data: an iterable of allele values containing
            the data to set for the new sample. For an :class:`.Align`
            instance and if the sample is not the first, the number of
            data must fit any previous ones.
        :param labels: if not None, must be an iterable of strings
        """
        if self._is_matrix and self._ns == 0:
            self._obj.set_nsit_all(len(data))
        index = self._ns
        self._ns += 1
        self._obj.set_nsam(self._ns)
        try:
            self.set_sample(index, name, data, labels)
        except:
            self.del_sample(index)
            raise

    def add_samples(self, items):
        """
        Add several samples at the end of the instance.

        :param items: must be a sequence, an :class:`.Align` instance, or a
            :class:`.Container` instance. If a sequence is passed, each item must be
            of length 2 or 3 and contain the sample name
            string, the sequence of data values and, if provided,
            the sequence of labels. See the method
            :meth:`~.Align.add_sample` for more details about the structure
            of each item. If the current instance is an :class:`.Align`,
            all sequence length must be identical. For a
            :class:`.Container`, sequences may have different lengths.
        """

        # increase the number of sites if needed
        if self._is_matrix and self._ns == 0 and len(items) > 0 and len(items[0]) > 1:
            self._obj.set_nsit_all(len(items[0][1]))

        # increase the number of samples
        incr = len(items)
        cur = self._ns
        self._ns += incr
        self._obj.set_nsam(self._ns)

        # set values
        for i,v in enumerate(items):
            if len(v) not in [2,3]: raise ValueError('invalid number of items for sample')
            try:
                self.set_sample(cur+i, * v)
            except:
                self._ns -= incr
                self._obj.set_nsam(self._ns)
                raise

    def __iter__(self):
        for i in range(self._ns):
            yield SampleView(self, i)

    def _sample(self, index):
        if isinstance(index, slice):
            raise ValueError('slices are not supported')
        if index < 0:
            index = self._ns + index
            if index < 0: raise IndexError('sample index out of range')
        if index >= self._ns: raise IndexError('sample index out of range')
        return index

    def _site(self, index, sample):
        if isinstance(index, slice):
            raise ValueError('slices are not supported')
        if index < 0:
            if self._is_matrix: index = self._obj.get_nsit_all() + index
            else: index = self._obj.get_nsit_sample(sample) + index
            if index < 0: raise IndexError('site index out of range')
        if self._is_matrix:
            if index >= self._obj.get_nsit_all(): raise IndexError('site index out of range')
        elif index >= self._obj.get_nsit_sample(sample): raise IndexError('site index out of range')
        return index

    def _label(self, index, sample):
        if isinstance(index, slice):
            raise ValueError('slices are not supported')
        if index < 0:
            index = self._obj.get_nlabels(sample) + index
            if index < 0: raise IndexError('invalid label index')
        if index >= self._obj.get_nlabels(sample): raise IndexError('invalid label index')
        return index

    def get_name(self, index):
        """
        Get the name of a sample.

        :param index: sample index.
        :retur: A string.
        """
        return self._obj.get_name(self._sample(index))

    def set_name(self, index, name):
        """
        Set the name of a sample.

        :param index: index of the sample
        :param name: new name value.
        """
        if not isinstance(name, str): raise TypeError('name must be string')
        self._obj.set_name(self._sample(index), name)

    def get_sequence(self, index):
        """
        Get a sequence as a :class:`.SequenceView`.
        The returned object allows modifying the
        underlying data.

        :param index: sample index.
        :return: A :class:`!SequenceView` instance.
        """
        return SequenceView(self, self._sample(index))

    def set_sequence(self, index, value):
        """
        Overwrite sequence data for a given sample.

        :param index: sample index.
        :param value: can be a :class:`.SequenceView` instance, a
            list of allelic values, or a string (only for single-character
            alphabets such as :py:obj:`.alphabets.DNA`). In the case of
            an :class:`.Align` instance, the length of the sequence must
            match the current alignment length.
        """

        # check index
        index = self._sample(index)

        # check input sequence
        value = list(map(self._alphabet.get_code, value))
        n = len(value)

        # get current length of the sequence
        if self._is_matrix:
            ls = self._obj.get_nsit_all()
            if n != ls: raise ValueError('cannot change length of a sequence for an Align')
        else: ls = self._obj.get_nsit_sample(index)

        # change sequence length as needed
        if n != ls: self._obj.set_nsit_sample(index, n)

        # set all values
        for i, v in enumerate(value): self._obj.set_sample(index, i, v)

    def __getitem__(self, index):
        return self.get_sample(index)

    def get_sample(self, index):
        """
        Get a sample as a :class:`.SampleView` instance.
        The returned object allows to modify the
        underlying data.

        :param index: index of the sample to access.
        :return: A :class:`!SampleView` instance.
        """
        return SampleView(self, self._sample(index))

    def __delitem__(self, index):
        self.del_sample(index)

    def del_sample(self, index):
        """
        Delete a sample.

        :param index: index of the sample to delete.
        """
        self._obj.del_sample(self._sample(index))
        self._ns -= 1

    def __setitem__(self, index, sample):
        self.set_sample(index, *sample)

    def set_sample(self, index, name, sequence, labels=None):
        """
        Overwrite all data for a given sample.

        :param index: index of the sample to access (slices are not
            permitted).
        :param name: new name of the sample.
        :param sequence: list of allelic values giving the new values to
            set. :class:`str` is supported for character alphabets such
            as :py:obj:`.alphabets.DNA`.
            In case of an :class:`.Align`, it is required to pass a
            sequence with length matching the number of sites of the
            instance.
        :param labels: a list of string labels. The default corresponds
            to an empty list.
        """
        self._sample(index) # check index
        self._obj.set_name(index, name)
        ls = len(sequence)

        if self._is_matrix:
            if ls != self._obj.get_nsit_all():
                raise ValueError('sequence length must match the alignment length')
            for i,v in enumerate(sequence): self.set(index, i, v)
        else:
            self._obj.set_nsit_sample(index, ls)
            for i,v in enumerate(sequence): self.set(index, i, v)

        if labels is None: labels = []
        ng = len(labels)
        self._obj.set_nlabels(index, ng)
        if isinstance(labels, str): raise TypeError('labels must be a list of strings')
        for i, v in enumerate(labels):
            if v is None: v = ''
            if not isinstance(v, str): raise TypeError('labels must be a list of strings')
            self._obj.set_label(index, i, v)

    def get(self, sample, site):
        """
        Get a data entry.

        :param sample: sample index.
        :param site: site index.
        :return: An allele value (type depends on the alphabet)
        """
        return self._alphabet.get_value(self._obj.get_sample(self._sample(sample), self._site(site, sample)))

    def set(self, sample, site, value):
        """
        Set a data entry. The value must be a valid allelic
        value for this instance.

        :param sample: sample index.
        :param site: site index.
        :param value: allele value (type depends on the alphabet).
        """
        self._obj.set_sample(self._sample(sample), self._site(site, sample), self._alphabet.get_code(value))

    def get_label(self, sample, index):
        """
        Get a group label.

        :param sample: sample index.
        :param index: label index.
        :return: A string.
        """
        v = self._obj.get_label(self._sample(sample), self._label(index, self._sample(sample)))
        if v == '': return None
        else: return v

    def set_label(self, sample, index, value):
        """
        Set a group label.

        :param sample: sample index.
        :param index: label index.
        :param value: new label value.
        """
        if value is None: value = ''
        if not isinstance(value, str): raise TypeError('label must be a string')
        self._obj.set_label(self._sample(sample), self._label(index, self._sample(sample)), value)

    def add_label(self, sample, value):
        """
        Add a group label to a specific sample.

        :param sample: sample index.
        :param value: new label value.
        """
        if not isinstance(value, str): raise TypeError('label must be a string')
        self._obj.add_label(self._sample(sample), value)

    def reserve(self, nsam=0, lnames=0, nlbl=0, nsit=0):
        """
        Pre-allocate memory. This method can be used when the size of
        arrays is known a priori, in order to speed up memory
        allocations. It is not necessary to set all values. Values less
        than 0 are ignored.

        :param nsam: number of samples in the ingroup.
        :param lnames: length of sample names.
        :param nlbl: number of labels.
        :param nsit: number of sites.
        """
        self._obj.reserve(max(0, nsam), max(0, lnames), max(0, nlbl), max(0, nsit))

    def find(self, name, regex=False, flags=None, multi=False, index=False):
        """
        Find a sample by its name.

        :param name: name of sample to identify.
        :param regex: a boolean indicating whether the value passed as
            *name* is a regular expression. If so, the string is passed
            as is to the re module (using function
            :py:func:`re.search`).
            Otherwise, only exact matches will be considered.
        :param flags: list of flags to be passed to :py:func:`re.search`
            (only considered if *regex* is ``True``). For example, when looking
            for samples containing the term "sample" but being case-insensitive,
            use the following syntax:
            ``align.find("sample", regex=True, flags=[re.I])``. By
            default (``None``) no further argument is passed.
        :param multi: a boolean indicating whether all hits should be
            returned. If so, a list of :class:`.SampleView` instances
            is always returned (the list will be empty in case of no
            hits). Otherwise, a single :class:`!SampleView` instance
            (or its index)  will be returned for the first hit, or
            ``None`` in case of no hits.
        :param index: boolean indicating whether the index of the sample
            should be returned. In that case return values for hits are
            :class:`int` (by default, :class:`!SampleView` instances).

        :return: The type of the returned value depends on the argument
            *multi* and on whether any hits were found:

            ========= ========= ======================================
            *multi*   *index*   return value
            ========= ========= ======================================
            ``False`` ``False`` :class:`!SampleView` or ``None``
            ``False`` ``True``  integer or ``None``
            ``True``  ``False`` list of :class:`!SampleView` instances
            ``True``  ``True``  list of integers
            ========= ========= ======================================

        """
        if multi: ret = []
        if flags==None: flags = []
        for item in self:
            if ((regex==True and re.search(name, item.name, functools.reduce(operator.or_, flags, 0))) or
                (regex==False and name==item.name)):
                    if multi: ret.append(item.index if index else item)
                    else: return item.index if index else item
        if multi: return ret
        else: return None

    def find_motif(self, sample, motif, start=0, stop=None):
        """
        Locate the first instance of a sequence motif.

        Return the index of the first exact hit to a given substring.
        The returned value is the position of the first base of the hit.
        Only exact forward matches are implemented. To use regular expression
        (for example to find degenerated motifs), one should extract the
        string for the sequence and use a tool such as the regular
        expression module (:mod:`re`).

        :param sample: sample index.
        :param motif: list of allelic values constituting the motif to search.
        :param start: position at which to start searching. The method
            will never return a value smaller than *start*. By default,
            search from the start of the sequence.
        :param stop: position at which to stop search (the motif
            cannot overlap this position). No returned value will be
            larger than ` stop - len(motif)``. By default, or if *stop* is equal to
            or larger than the length of the sequence, search until the
            end of the sequence.
        """

        # adjust indexes
        sample = self._sample(sample)
        start = self._site(start, sample)

        # adjust stop position
        if self._is_matrix: ls = self._obj.get_nsit_all()
        else: ls = self._obj.get_nsit_sample(sample)
        if stop == None or stop > ls: stop = ls
        else: stop = self._site(stop, sample)

        # set motif sequence
        self._motif.set_num_values(len(motif))
        for i,v in enumerate(motif):
            self._motif.set_item(i, self._alphabet.get_code(v))

        ret = self._obj.find(sample, self._motif, start, stop)
        if ret == _eggwrapper.MAX: return None
        else: return ret

    def upper(self, index, start=0, stop=None):
        """
        Converts allele values of a sample to upper case. Only
        applicable for alleles that have an upper case equivalent. All
        other allele values are ignored. The underlying object data is
        modified and this method returns ``None``. Only accepted for
        case-sensitive character and string alphabets. Furthermore, all
        upper case alleles that are implied are required to be valid
        alleles in the alphabet.

        :param index: sample index.
        :param start: index of the first allele to convert. By default,
            from the start of the sequence.
        :param stop: stop index (index of the allele immediately after
            the last allele to convert). By default, convert until
            the end of the sequence.
        """
        self._obj.change_case(False, index, start, _eggwrapper.MISSINGDATA if stop is None else stop, self._alphabet._obj)

    def lower(self, index, start=0, stop=None):
        """
        Converts allele values of a sample to lower case. Only
        applicable for alleles that have an lower case equivalent. All
        other allele values are ignored. The underlying object data is
        modified and this method returns ``None``. Only accepted for
        case-sensitive character and string alphabets. Furthermore, all
        lower case alleles that are implied are required to be valid
        alleles in the alphabet.

        :param index: sample index.
        :param start: index of the first allele to convert. By default,
            from the start of the sequence.
        :param stop: stop index (index of the allele immediately after
            the last allele to convert). By default, convert until
            the end of the sequence.
        """
        self._obj.change_case(True, index, start, _eggwrapper.MISSINGDATA if stop is None else stop, self._alphabet._obj)

    def names(self):
        """
        Generate the list of sample names.

        :return: A :class:`list`.
        """
        return [item.name for item in self]

    def __contains__(self, name):
        return self.find(name) != None

    def name_mapping(self):
        """
        Map sample names to lists of :class:`.SampleView`
        instances. This method
        is most useful when several sequences have the same name. It may
        be used to detect and process duplicates.

        :return: A :class:`dict`.
        """
        res = {}
        for i in self:
            if i.name not in res: res[i.name] = []
            res[i.name].append(i)
        return res

    def group_mapping(self, level=0, as_position=False, liberal=False):
        """
        Map labels to samples. Each sample is
        either represented by a
        :class:`.SampleView` instance (by default) or its position
        index within the instance.

        :param level: index of labels to consider.
        :param as_position: if ``True``, represent samples by their position
            index in the instance
            instead of a :class:`!SampleView` instance.
        :param liberal: if ``True``, ignore samples for which this label
            level is not defined (by default, an :exc:`IndexError` is raised).
        :return: A :class:`dict` of lists, containing
            either integers or :class:`!SampleView`.
        """
        if level < 0: raise ValueError('negative index is not supported')
        res = {}
        for i, item in enumerate(self):
            if level < self._obj.get_nlabels(i):
                label = item.labels[self._label(level, i)]
                if label not in res: res[label] = []
                res[label].append(i if as_position else item)
            elif not liberal:
                raise IndexError('invalid label index')
        return res

    def remove_duplicates(self):
        """
        Remove all duplicates, based on name exact matching. For all
        pairs of samples with identical name, only the one occurring
        first is conserved. The current instance is modified and this
        method returns ``None``.
        """
        names = set()
        i = 0
        while i < self._ns:
            name = self.get_sample(i).name
            if name in names:
                self.del_sample(i)
            else:
                names.add(name)
                i+=1

    _key_init = 'ABCDEDGHIJKLMNOPQRSTUVWXYZ'
    _key_code = _key_init + _key_init.lower() + '0123456789_'

    def encode(self, nbits=10):
        """
        Rename all samples using unique keys.

        Generate a random mapping
        of names to unique keys and use this keys as names for samples.
        Keys are of length *nbits*, using alphanumerical
        characters only but always starting with a capital letter.

        :param nbits: length of the keys (encoded names). This value
            must be >= 4 and <= 63.

        :return: A :class:`dict` mapping all the generated keys to the
            actual sequence names. The keys are case-dependent and
            guaranteed not to start with a number.
        
        The returned mapping can be used to restore the original names
        using :meth:`~.Align.rename`. This method is not affected by
        the presence of sequences with identical names in the original
        instance (and :meth:`~.Align.rename` will also work properly
        in that case).
        """
        if nbits<4 or nbits>len(self._key_code):
            raise ValueError('invalid value for `nbits`')
        mapping = {}
        for item in self:
            while True:
                key = (self._key_init[random.integer(len(self._key_init))]
                    + ''.join([ self._key_code[random.integer(len(self._key_code))] for i in range(nbits-1) ]))
                if key not in mapping: break
            mapping[key] = item.name
            item.name = key
        return mapping

    def rename(self, mapping, liberal=False):
        """
        Rename sequences of the instance.

        :param mapping: a :class:`dict` providing the mapping of old
            names (as keys) to new names (which may, if needed, contain
            duplicates).

        :param liberal: if this argument is ``False`` and a name does not
            appear in *mapping*, a :exc:`ValueError` is
            raised. If *liberal* is ``True``, names that don't appear in
            *mapping* are left unchanged.

        :return: The number of samples that have been actually renamed,
            overall.
        """
        cnt = 0
        for item in self:
            name = item.name
            if name in mapping:
                item.name = mapping[name]
                cnt += 1
            else:
                if not liberal:
                    raise ValueError('cannot rename sequence: {0} not found in mapping'.format(name))
        return cnt

    def subset(self, samples):
        """
        Extract a subset of samples.
        Generate and return a copy of the instance with only a specified
        list of samples. Sample indices are not required to be consecutive.

        :param samples: a list of
            sample indices, or a :class:`Structure` instance, giving the
            list of samples that must be exported to the returned object.
            In the latter case, all samples referred to in the structure
            are extracted.

        :return: A new instance of the same type.
        """
        if isinstance(samples, Structure):
            if samples.req_ns > self._ns: raise ValueError('invalid structure')
            i = samples._obj.init_i()
            array = []
            while i != _eggwrapper.UNKNOWN:
                array.append(i)
                i = samples._obj.iter_i() 
            i = samples._obj.init_o()
            while i != _eggwrapper.UNKNOWN:
                array.append(i)
                i = samples._obj.iter_o() 
            samples = array
        else:
            if samples is None: samples = []
            elif max(samples) >= self._ns: raise ValueError('invalid index in list')

        if self._is_matrix: ret = Align(self._alphabet)
        else: ret = Container(self._alphabet)
        ret._ns = len(samples)
        ret._obj.set_nsam(ret._ns)
        if self._is_matrix:
            ls = self._obj.get_nsit_all()
            ret._obj.set_nsit_all(ls)
        for i, v in enumerate(samples):
            v = self._sample(v)
            ret.set_name(i, self.get_name(v))
            ng = self._obj.get_nlabels(v)
            ret._obj.set_nlabels(i, ng)
            for j in range(ng):
                ret._obj.set_label(i, j, self._obj.get_label(v, j))
            if not self._is_matrix:
                ls = self._obj.get_nsit_sample(v)
                ret._obj.set_nsit_sample(i, ls)
            for j in range(ls):
                ret._obj.set_sample(i, j, self._obj.get_sample(v, j))
        return ret

class Align(Base):
    """
    Dataset of aligned sequences. The data
    consists of a given number of samples, each with
    the same number of sites. There can be any number of labels for any
    sample meaning  that samples can be described by several labels in
    addition to their name. The type of genetic data stored in the
    instance is determined by the alphabet. The optional constructor
    arguments allow to setup a matrix of a pre-defined dimension
    (by default, :py:obj:`~.Align.ns` and :py:obj:`~.Align.ls` are equal
    to 0). If samples are created at construction, they have empty names
    and no labels.

    :param alphabet: an :class:`~.Alphabet` instance. There must be at
        least one valid allele (either exploitable or missing).
    :param num_sam: number of samples to initialize.
    :param num_sit: number of sites to initialize.
    :param init: initial values for all data entries. Must be a valid
        allele of the alphabet. Ignored if *num_sam* or *num_sit* is 0.
        By default, use the first exploitable allele or the first missing
        allele if there are none). Only considered if *num_sam* and
        *num_sit* are set to non-null values.

    .. _align_operations:

    Both :class:`.Align` and :class:`.Container` instances support the
    following operations:

    +-------------------------+-----------------------------+-----------------------------------------------+-------+
    | Operation               | Alternative                 | Action                                        | Notes |
    +=========================+=============================+===============================================+=======+
    | ``len(aln)``            | ``aln.ns``                  | number of samples                             |       |
    +-------------------------+-----------------------------+-----------------------------------------------+-------+
    | ``for sam in aln: ...`` |                             | perform an iteration over samples             | (1)   |
    +-------------------------+-----------------------------+-----------------------------------------------+-------+
    | ``aln[i]``              | ``aln.get_sample(i)``       |  access a given sample                        |       |
    +-------------------------+-----------------------------+-----------------------------------------------+-------+
    | ``aln[i] = sam``        | ``aln.set_sample(i, *sam)`` | copy data over an existing sample             | (2)   |
    +-------------------------+-----------------------------+-----------------------------------------------+-------+
    | ``del aln[i]``          | ``aln.del_sample(i)``       | delete a sample                               |       |
    +-------------------------+-----------------------------+-----------------------------------------------+-------+
    | ``name in aln``         | ``aln.find(name) != None``  | ``True`` if at least one sample has this name |       |
    +-------------------------+-----------------------------+-----------------------------------------------+-------+
    | ``name not in aln``     | ``aln.find(name) == None``  | ``True`` if no sample has this name           |       |
    +-------------------------+-----------------------------+-----------------------------------------------+-------+

    Notes:

    #. To iterate over sites, use: ``for site in aln.iter_sites()``.
    #. All values that can be interpreted as a ``(name, sequence)`` or
       ``(name, sequence, labels)`` tuple can be passed as right-hand
       operand (including :class:`.SampleView` instances).
    """
    def __init__(self, alphabet, nsam=0, nsit=0, init=None):
        if alphabet is None: raise ValueError('an alphabet must be provided at object construction')
        self._is_matrix = True
        self._window = None
        self._motif = _eggwrapper.VectorInt()
        self._obj = _eggwrapper.DataHolder(True)
        self._alphabet = alphabet
        if init is None:
            if alphabet._obj.num_exploitable() > 0: init = alphabet.get_value(0)
            elif alphabet._obj.num_missing() > 0: init = alphabet.get_value(-1)
            else: raise ValueError('to allow initialization, alphabet must have at least one valid allele')
        if nsam != 0 or nsit != 0:
            self._ns = nsam
            self._obj.set_nsam(nsam)
            self._obj.set_nsit_all(nsit)
            for i in range(nsam):
                for j in range(nsit):
                    self._obj.set_sample(i, j, alphabet.get_code(init))
        else:
            self._ns = 0

    @property
    def ls(self):
        """
        Alignment length. This value cannot be set or modified directly.
        """
        return self._obj.get_nsit_all()

    def del_columns(self, site, num=1):
        """
        Delete one or more full columns of the alignment.

        By default (if ``num=1``), remove a single site. If *num* is
        larger than 1, remove a range of sites.

        :param site: index of the (first) site to remove. This site must
            be a valid index.
        :param num: maximal number of sites to remove. The value cannot
            be negative.
        """
        if num < 0: raise ValueError('cannot delete a negative number of columns')
        site = self._site(site, None)
        self._obj.del_sites_all(site, site+num)

    def insert_columns(self, position, values):
        """
        Insert sites at a given position of an alignment.

        :param position: the position at which to insert sites. Sites
            are inserted *before* the specified position, so the user
            can use 0 to insert sites at the beginning of the sequence.
            To insert sites at the end of the sequence, pass the current
            length of the alignment, or ``None``. If *position* is
            larger than the length of the sequence or ``None``, new
            sites are inserted at the end of the alignment. The position
            might be negative to count from the end. Warning: the
            position -1 means *before* the last position.
        :param values: a sequence to insert for each sample. To insert a single
            site, use a single-item
            list, or a single-character string for character alphabets
            (such as :py:obj:`.alphabets.DNA`).
        """
        num = len(values)
        ls = self._obj.get_nsit_all()
        if position == None or position > ls: position = ls
        if position < 0:
            position = ls + position
            if position < 0: raise IndexError('invalid index (negative value out of bound)')

        self._obj.insert_sites_all(position, num)
        for i in range(self._ns):
            for j, v in enumerate(values):
                self._obj.set_sample(i, position+j, self._alphabet.get_code(v))

    def extract(self, *args):
        """
        extract(...)

        Create a sub-alignment based on specified positions.

        The thre possible ways to call this method are:

            ``extract(start, stop)`` to extract a continuous range of
            sites,

            ``extract(rf)`` to extract exon positions from a
            :class:`.ReadingFrame` instance, and

            ``extract(indices)`` to extract an arbitrary list of positions
            (in any order).

        :param start: first position to extract. This position must be
            a valid index for this alignment.
        :param stop: stop position for the range to extract. *This
            position is not extracted. If this position is equal to or
            smaller than *start*, empty sequences are generated. If this
            position is equal to or larger than the length of the
            alignment, or if it is equal to ``None``, all positions
            until the end of the alignment are extracted.
        :param rf: a :class:`.ReadingFrame` object. Note that the
            *keep_truncated* argument of :class:`!ReadingFrame` has an
            effect.
        :param indices: a list (or other iterable type with a length) of
            alignment positions (or column indices). This list may
            contain repetitions and does not need to be sorted. The
            positions will be extracted in the specified order.
        :return: A new :class:`!Align` instance.

        .. note::

            Keyword arguments are not supported.
    """

        # initialize the output object
        ret = Align(self._alphabet)
        ret._ns = self._ns
        ret._obj.set_nsam(self._ns)

        # load the names and group labels
        for i in range(self._ns):
            ret.set_name(i, self.get_name(i))
            ret._obj.set_nlabels(i, self._obj.get_nlabels(i))
            for j in range(self._obj.get_nlabels(i)):
                ret._obj.set_label(i, j, self._obj.get_label(i, j))

        # load the sequences
        if len(args) == 1:
            if isinstance(args[0], ReadingFrame):
                pos = [j for i in args[0].iter_codons() for j in i if j is not None]
            else:
                pos = args[0]

            ls = len(pos)
            ret._obj.set_nsit_all(ls)
            for j,v in enumerate(pos):
                v = self._site(v, None) # check site / supports -1 based
                for i in range(self._ns):
                    ret._obj.set_sample(i, j, self._obj.get_sample(i, v))

        elif len(args) == 2:
            start = self._site(args[0], None)
            if args[1] is None:
                stop = self._obj.get_nsit_all()
            elif args[1] < 0:
                stop = self._site(args[1], None)
                if stop < 0: raise IndexError('stop position is out of range')
            else:
                stop = min(args[1], self._obj.get_nsit_all())
            if stop < start: stop = start
            ls = stop - start
            ret._obj.set_nsit_all(ls)
            for i in range(self._ns):
                for j in range(ls):
                    ret._obj.set_sample(i, j, self._obj.get_sample(i, start+j))

        # capture type error
        else:
            raise ValueError('extract() expects 1 or 2 arguments, got {0}'.format(len(args)))

        return ret

    def fix_ends(self, replaced='-', replacing='?'):
        """
        Replace characters at both ends of each sequence.

        Replace all leading and trailing occurrence of the allele
        specified by *replaced* by the one specified by *replacing*.
        Internal occurrences of the replaced allele (those having at
        least one character other than either the replaced and replacing
        allele at both sides) are left unchanged. Both alleles are required to be
        valid alleles for this alphabet
        """
        src = self._alphabet.get_code(replaced)
        dst = self._alphabet.get_code(replacing)
        ls = self._obj.get_nsit_all()

        for i in range(self._ns):
            # clean left
            j = 0
            k = ls - 1
            while j < ls:
                if self._obj.get_sample(i, j) == src: self._obj.set_sample(i, j, dst)
                elif self._obj.get_sample(i, j) != dst: break
                j += 1
            else:
                k = -1 # prevent right clean

            # clean right (unless reached end of previous while)
            while k >= 0:
                if self._obj.get_sample(i, k) == src: self._obj.set_sample(i, k, dst)
                elif self._obj.get_sample(i, k) != dst: break
                k -= 1

    def column(self, index):
        """
        Extract the allele values of a site at a given position.

        :param index: the index of a site within the alignment.
        :return: A list of allelic values.
        """
        index = self._site(index, None)
        return list(map(self._alphabet.get_value, [self._obj.get_sample(i, index) for i in range(self._ns)]))

    def nexus(self, prot='auto'):
        """
        Generates a simple nexus-formatted string. If *prot* is
        ``True``, add ``datatype=protein`` in the file, allowing it to
        be imported as proteins (but doesn't perform further checking).
        If *prot* is ``False``, never add this command.
        By default, add the protein datatype command if the alphabet is
        :py:data:`.alphabets.protein`.

        :return: A nexus-formatted string. Note: any spaces and tabs in
            sequence names are replaced by underscores.

        .. note::

            This nexus implementation is minimal but will normally suffice
            to import sequences to programs expecting nexus.

            The data must be exportable as strings.
        """
        if self._alphabet._obj.get_type() != 'DNA' and self._alphabet._obj.get_type() != 'char':
            raise ValueError('cannot export alignment: invalid alphabet')
        if prot == 'auto': prot = self._alphabet == alphabets.protein

        string = ['#NEXUS\n']
        string += ['begin data;\n']
        string += ['dimensions ntax={0} nchar={1};\n'.format(self.ns, self.ls)]
        if prot: type = 'prot'
        else: type = 'dna'
        string += ['format datatype={0} interleave=no gap=-;\n'.format(type)]
        string += ['matrix\n']
        L = 0
        for i in self:
            if (len(i.name) > L): L = len(i.name)
        for i in self:
            string += ['%s  %s\n' %(i.name.ljust(L).replace(' ', '_').replace('\t', '_'), i.sequence.string())]
        string += [';\nend;\n']
        return ''.join(string)

    def filter(self, ratio, relative=False):
        """
        Remove the sequences with too few exploitable data. The list of
        exploitable data is defined by the alphabet attached to the
        instance. This method
        modifies the current instance and returns ``None``.

        :param ratio: limit threshold, expressed as a proportion of
            the alignment length (default) or as a proportion of the
            maximum number of exploitable data over all considered samples
            (if the *relative* argument is ``True``).
        :param relative: Take as a reference the number of exploitable data
            of the sequence which has most.

        .. note::

            If the length of the alignment is 0,nothing is done.
        """

        # get the threshold
        if ratio < 0.0 or ratio > 1.0:
            raise ValueError('invalid value for ratio argument')

        # get the number of exploitable data of all samples
        cnt = []
        for i in range(self._ns):
            c = 0
            for j in range(self._obj.get_nsit_all()):
                if self._obj.get_sample(i, j) >= 0: c += 1
            cnt.append(c)
        if len(cnt) == 0: return

        # get threshold
        if relative:
            ref = max(cnt)
        else:
            ref = self._obj.get_nsit_all()
        cnt = [i/ref for i in cnt]

        # delete the samples with not enough exploitable samples (last first)
        i = self._ns-1
        while i>=0:
            if cnt[i] < ratio:
                self._obj.del_sample(i)
                self._ns -= 1
            i -= 1

    def phyml(self):
        """
        Return a phyml-formatted string.
        The phyml format is suitable as input data for the
        PhyML and PAML programs. Raise a :exc:`ValueError`
        if any name of the instance contains at least one character in
        the following list: ``()[]{},;`` or a space, tab, newline or
        linefeed. Labels are never exported.

        The alphabet must be represented as characters (such as :py:obj:`.alphabets.DNA`).
        """
        if self._alphabet.type != 'DNA' and self._alphabet.type != 'char':
            raise ValueError('cannot export alignment: invalid alphabet')
        if not self._obj.valid_phyml_names():
                raise ValueError('cannot perform phyml conversion: invalid character in names, or empty name')
        lines = ['{0} {1}'.format(self._ns, self._obj.get_nsit_all())]
        lines += ['{0}  {1}'.format(i.name, i.sequence.string()) for i in self]
        return '\n'.join(lines)

    def phylip(self, format='I'):
        """
        Return a phylip-formatted string. Raise a :exc:`ValueError` if any
        name of the instance contains at least one character of the
        following list: ``()[]{},;`` or a space, tab, newline or
        linefeed. Labels are never exported. Sequence names cannot
        be longer than 10 characters. A :exc:`!ValueError`
        will be raised if a longer name is met. *format* must be 'I' or
        'S' (case-independent), indicating whether the data should be
        formatted in the sequential (S) or interleaved (I) format (see
        PHYLIP's documentation for definitions). The user is responsible
        of ensuring that all names are unique. If not, the exported file
        may cause subsequent programs to fail.

        The alphabet must be represented as characters (such as :py:obj:`.alphabets.DNA`).
        """
        if self._alphabet._obj.get_type() != 'DNA' and self._alphabet._obj.get_type() != 'char':
            raise ValueError('cannot export alignment: invalid alphabet')
        BLOCK = 10
        NBLOCKS = 6
        format = format.upper()
        if format not in set('IS'): 
            raise ValueError('unknown value for option `format`: %s' %(format))
        lines = ['  {0:d} {1:d}'.format(self._ns, self._obj.get_nsit_all())]
        c = 0
        ci = 0
        for i in self:
            line = []
            name = i.name
            if len(set('(){}[],; \n\r\t').intersection(name)):
                raise ValueError('phylip format conversion error, invalid character in name: {0}'.format(name))
            if len(name)>10:
                raise ValueError('phylip format conversion error, this name is too long: {0}'.format(name))
            ci = c
            line.append('{0}{1}'.format(name.ljust(10), ''.join(i.sequence[:BLOCK-10])))
            ci += BLOCK-10
            n = 0
            while n < (NBLOCKS-1) and ci<self._obj.get_nsit_all():
                line.append(' {0}'.format(''.join(i.sequence[ci:ci+BLOCK])))
                ci += BLOCK
                if format=='I': n += 1
            lines.append(''.join(line))
        c = ci

        # if sequential, c should be full
        while c < self._obj.get_nsit_all():
            lines.append('')
            line = []
            for i in self:
                ci = c
                n = 0
                while n < NBLOCKS and ci < self._obj.get_nsit_all():
                    if n != 0: line.append(' ')
                    line.append('{0}'.format(''.join(i.sequence[ci:ci+BLOCK])))
                    ci += BLOCK
                    n += 1
                lines.append(''.join(line))
                line = []
            c = ci
            
        return '\n'.join(lines)

    def slider(self, wwidth, wstep):
        """
        Run a sliding window over the alignment.

        This method returns an iterator that can be used as::

            >>> for window in align.slider(wwidth, wstep):
            ...     ...
        
        where, for each step, *window* will be the reference an
        :class:`.Align` instance of length *wwidth* (or less if not
        enough sequence is available near the end of the alignment).
        Each step moves forward following the value of *wstep*. Note that
        the returned :class:`!Align` object is always the same and is
        updated at each iteration round.

        :param wwidth: size of the window (the last window might be smaller).
        :param wstep: iteration step.
        :return: An iterator.
        """
        if self._window == None:
            self._window = Align(self._alphabet)
        cache = 0
        for i in range(0, self._obj.get_nsit_all(), wstep):
            if min(self._obj.get_nsit_all(), i+wwidth) == cache: break # avoids redundant windows
            self._window.reset()
            for seq in self: self._window.add_sample(seq.name, seq.sequence[i:i+wwidth], seq.labels)
            yield self._window
            cache = min(self._obj.get_nsit_all(), i+wwidth) # record the new position

    def random_missing(self, rate, missing='N'):
        """
        Randomly introduces missing data in the current instance. Random
        positions of the alignment are changed to missing data. Only
        data that are currently non-missing data are considered.

        :param rate: probability that a non-missing allele is turned into
            missing data. 
        :param missing: missing data allele value, to be used for all
            replacements. This must be a valid missing allele for the instance's alphabet.
        """

        # check that rate is valid
        if rate < 0 or rate > 1:
            raise ValueError('invalid value for rate argument')

        # convert missing allele
        subst = self._alphabet.get_code(missing)
        if subst >= 0: raise ValueError('replacement allele must be a missing allele')

        # process samples
        for i in range(self._ns):
            indices = [j for j in range(self._obj.get_nsit_all()) if self._obj.get_sample(i, j) >= 0]
            n = random.binomial(len(indices), rate)
            for j in range(n):
                x = random.integer(len(indices))
                pos = indices.pop(x)
                self._obj.set_sample(i, pos, subst)

    def consensus(self):
        """
        Generates the consensus of the object. The alphabet must be
        :py:obj:`.alphabets.DNA`. The consensus is generated based on standard
        ambiguity codes (see :ref:`here <iupac-nomenclature>`). The consensus is returned as a string,
        of length matching the alignment length. In case of a
        disagrement involving an occurrence of "?" and "-", the output
        base is always "?". Otherwise, the consensus base defined by
        the IUPAC convention is followed. If a site is not variable,
        the fixed value is incorporated in the consensus in all cases.

        :return: A string.
        """
        if self._alphabet._obj.get_type() != 'DNA': raise ValueError('alphabet must be DNA')
        return ''.join([self._consensus_site(i) for i in range(self._obj.get_nsit_all())])

    def _consensus_site(self, pos):
        cur = None
        for i in range(self._ns):
            cur = _CONSENSUS_MAPPING[(cur, self._obj.get_sample(i, pos))]
        if cur is None: return '?'
        else: return self._alphabet.get_value(cur)

    def intersperse(self, length, positions=None, alleles='A'):
        """
        Insert non-varying sites within the alignment. The current
        object is permanently modified.

        :param length: Desired length of the final alignment. If the
            value is smaller than the original (current) alignment
            length, nothing is done and the alignment is unchanged.

        :param positions: Position that each site of the current alignment
            must have in the final alignment.
            The number of positions must be equal to the number of sites
            of the alignment (before interspersing). The argument value
            must be either a sequence of positive integers or a sequence
            of real numbers comprised between 0 and 1. In either case,
            values must be in increasing order. In the former case, the
            last (maximal) value must be smaller than the desired length
            of the final alignment. In the latter case, values are
            expressed relatively, and they will be converted to integer
            indices by the method. In that case, if site positioning is
            non-trivial (typically, if conversion of positions to
            integer yield identical position for different conscutive
            sites), it will be resolved randomly. By default (if
            ``None``), sites are placed regularly along the final
            alignment length. If :class:`int` and :class:`float` types
            are mixed, the first occurring type will condition what will
            happen.

        :param alleles: List of allelic values  providing the alleles to
            be used to fill non-varying positions of the resulting
            alignment. If there is more than one allele, the allele will
            be picked randomly for each site, independently for each
            inserted site. All alleles must be valid alleles for the
            current alphabet.
        """

        # escape if length = 0 (nothing will be done, and it can cause internal errors
        if length < 1: return
        intersperse = _eggwrapper.IntersperseAlign()
        intersperse.set_length(length)

        # load alignment
        intersperse.load(self._obj)

        # get positions
        if positions is None:
            if self._obj.get_nsit_all() == 1: positions = [0.5]
            else: positions = [i/(self._obj.get_nsit_all()-1) for i in range(self._obj.get_nsit_all())]
        if len(positions) != self._obj.get_nsit_all(): raise ValueError('lengths of `positions` must be equal to the original alignment length')
        if isinstance(positions[0], int): need_rounding = False
        elif isinstance(positions[0], float): need_rounding = True
        else: raise TypeError('argument `positions` only support `int` and `float` items')
        for idx, pos in enumerate(positions):
            cache = -1
            if pos < cache: raise ValueError('item in `positions` is not larger than the previous one: {0}'.format(pos))
            cache = pos
            if need_rounding:
                if pos<0 or pos>1: raise ValueError('invalid value provided in `positions`: {0}'.format(pos))
                intersperse.set_position(idx, pos)
            else:
                if pos<0 or pos>=length: raise ValueError('invalid value provided in `positions`: {0}'.format(pos))
                intersperse.set_round_position(idx, pos)

        # get alleles
        intersperse.set_num_alleles(len(alleles))
        for idx, allele in enumerate(alleles):
            intersperse.set_allele(idx, self._alphabet.get_code(allele))

        # process
        intersperse.intersperse(need_rounding)

    def to_codons(self, frame=None):
        """
        DNA to codons conversion.
        Convert the instance from the :py:obj:`.alphabets.DNA` alphabet
        to the :py:obj:`.alphabets.codons` alphabet. This method
        overwrites the current instance. After the conversion, there
        will one site per codon.

        :param frame: a :class:`.ReadingFrame` instance providing the
            exon positions in the correct frame. By default, a
            non-segmented frame covering all sequences is assumed (in
            case the provided alignment is the coding region; in such
            case the length must be a multiple of 3).
        """

        # change alphabet
        if self._alphabet._obj.get_name() != 'DNA': raise ValueError('object must have DNA alphabet')
        self._alphabet = alphabets.codons

        # get frame
        if frame is None:
            if self._obj.get_nsit_all() == 0: frame = ReadingFrame([])
            elif self._obj.get_nsit_all() % 3 != 0: raise ValueError('alignment length must be a multiple of 3')
            else: frame = ReadingFrame([(0, self._obj.get_nsit_all())])
        elif self._obj.get_nsit_all() < frame.num_needed_bases:
            raise ValueError('reading frame is extending past the end of the alignment')
        ncod = frame.num_codons

        # set all codons
        for i in range(self._ns):
            for j, (a, b, c) in enumerate(frame.iter_codons()):
                self._obj.set_sample(i, j, 
                    alphabets.codons._obj.get_code_from_bases(
                        -3 if a is None else self._obj.get_sample(i, a),
                        -3 if b is None else self._obj.get_sample(i, b),
                        -3 if c is None else self._obj.get_sample(i, c)))

        # adjust ls
        self._obj.set_nsit_all(frame.num_codons)

    def to_bases(self):
        """
        Codon to DNA conversion.
        Convert the instance from the :py:obj:`.alphabets.codons` alphabet
        to the :py:obj:`.alphabets.DNA` alphabet.
        The number of sites will be multiplied by three.
        """
        if self._alphabet._obj.get_name() != 'codons': raise ValueError('alignment must have codons alphabet')
        ls = self._obj.get_nsit_all()
        self._obj.set_nsit_all(ls*3)
        self._alphabet = alphabets.DNA
        for i in range(self._ns):
            for j in range(ls-1, -1, -1): # read/write backward to avoid writing before conversion
                cdn = alphabets.codons.get_value(self._obj.get_sample(i, j))
                self._obj.set_sample(i, j*3, alphabets.DNA.get_code(cdn[0]))
                self._obj.set_sample(i, j*3+1, alphabets.DNA.get_code(cdn[1]))
                self._obj.set_sample(i, j*3+2, alphabets.DNA.get_code(cdn[2]))

    def iter_sites(self, start=0, stop=None):
        """
        Iterate over sites of the alignment.

        :param start: first site to consider; by default, start at beginning
            of alignment.
        :param stop: site where to stop iteration (this site is not included);
            by default, continue until the end of the alignment.

        This method allows to run the
        following type of iterations::
        
            >>> for site in aln.iter_sites():
            ...     ...

        where ``site`` is a unique :class:`.Site` object which is reset
        and updated at each iteration round.
        """
        site = _site.Site()
        if stop is None: stop = self._obj.get_nsit_all()
        for idx in range(start, stop):
            site.from_align(self, idx)
            yield site

class Container(Base):
    """
    Dataset of unaligned sequences.
    
    This class shares most of its functionalities with :class:`.Align`.
    The fundamental difference is that each sample may have a different number of sites.

    All operations listed :ref:`here <align_operations>` are available
    for :class:`!Container` instances.

    :param alphabet: an :class:`~.Alphabet` instance.
    """

    def __init__(self, alphabet):
        if alphabet is None: raise ValueError('an alphabet must be provided at object construction')
        self._ns = 0
        self._is_matrix = False
        self._obj = _eggwrapper.DataHolder(False)
        self._motif = _eggwrapper.VectorInt()
        self._alphabet = alphabet

    def ls(self, index):
        """
        Get the number of sites of an ingroup sample.

        :param index: sample index.
        """
        return self._obj.get_nsit_sample(self._sample(index))

    def del_sites(self, sample, site, num=1):
        """
        Delete data entries from a sample.

        By default (if ``num=1``), remove a single site. If *num* is
        larger than 1, remove a range of sites.

        :param sample: sample index.
        :param site: index of the (first) site to remove. This site must
            be a valid index.
        :param num: maximal number of sites to remove. The value cannot
            be negative.
        """
        if num < 0: raise ValueError('the number of sites to remove cannot be negative')
        sample = self._sample(sample)
        site = self._site(site, sample)
        self._obj.del_sites_sample(sample, site, site+num)

    def insert_sites(self, sample, position, values):
        """
        Insert sites at a given position for a given sample

        :param sample: index of the sample to which insert
            sites.
        :param position: the position at which to insert sites. Sites
            are inserted *before* the specified position, so the user
            can use 0 to insert sites at the beginning of the sequence.
            To insert sites at the end of the sequence, pass the current
            length of the sequence. If *position* is larger than the
            length of the sequence or ``None``, new sites are inserted
            at the end of the sequence. The position might be negative
            Warning: the position -1 means *before* the last position.
        :param values: a list of allelic values, or a string for
            compatible alphabets such as :py:obj:`.alphabets.DNA`
            to be inserted into the sequence.
        """
        num = len(values)
        sample = self._sample(sample)
        if position == None or position >= self._obj.get_nsit_sample(sample):
            position = self._obj.get_nsit_sample(sample)
        else:
            position = self._site(position, sample)
        self._obj.insert_sites_sample(sample, position, num)
        for i,v in enumerate(values):
            self._obj.set_sample(sample, position+i, self._alphabet.get_code(values[i]))

    def equalize(self, value='?'):
        """
        Equalize the length of all sequences. Extend sequences such as
        they all have the length of the longest sequence.

        :param value: the value to use to extend sequences. It must be
            a valid allelic value for the instance's alphabet.
        """
        value = self._alphabet.get_code(value)
        ls = 0
        for i in range(self._ns):
            if self._obj.get_nsit_sample(i) > ls:
                ls = self._obj.get_nsit_sample(i)
        for i in range(self._ns):
            if self._obj.get_nsit_sample(i) < ls:
                lsi  = self._obj.get_nsit_sample(i)
                self._obj.insert_sites_sample(i, lsi, ls-lsi)
                for j in range(lsi, ls): self._obj.set_sample(i, j, value)

    def to_codons(self):
        """
        DNA to codons conversion.
        Convert the instance from the :py:obj:`.alphabets.DNA` alphabet
        to the :py:obj:`.alphabets.codon` alphabet. In the
        output alignment, there is one site per codon.
        """
        # change alphabet
        if self._alphabet._obj.get_name() != 'DNA': raise ValueError('object must have DNA alphabet')
        self._alphabet = alphabets.codons

        # set all codons
        for i in range(self._ns):
            ls = self._obj.get_nsit_sample(i)
            if ls % 3 != 0: raise ValueError('sequence length must be a multiple of 3')
            for j, a in enumerate(range(0, ls, 3)):
                 self._obj.set_sample(i, j, 
                    alphabets.codons._obj.get_code_from_bases(self._obj.get_sample(i, a),
                                        self._obj.get_sample(i, a+1), self._obj.get_sample(i, a+2)))
            self._obj.set_nsit_sample(i, ls//3)

    def to_bases(self):
        """
        Codon to DNA conversion.
        Convert the instance from the :py:obj:`.alphabets.codon` alphabet
        to the :py:obj:`.alphabets.DNA` alphabet.
        The number of sites will be multiplied by three.
        """
        if self._alphabet._obj.get_name() != 'codons': raise ValueError('alignment must have codons alphabet')
        self._alphabet = alphabets.DNA
        for i in range(self._ns):
            ls = self._obj.get_nsit_sample(i)
            self._obj.set_nsit_sample(i, ls*3)
            for j in range(ls-1, -1, -1): # read/write backward to avoid writing before conversion
                cdn = alphabets.codons.get_value(self._obj.get_sample(i, j))
                self._obj.set_sample(i, j*3, alphabets.DNA.get_code(cdn[0]))
                self._obj.set_sample(i, j*3+1, alphabets.DNA.get_code(cdn[1]))
                self._obj.set_sample(i, j*3+2, alphabets.DNA.get_code(cdn[2]))

class encode(object):
    """
    Temporarily rename samples using unique keys.
    
    This is a context
    manager that can be used to perform some code using a
    :class:`.Align` or :class:`.Container` instance with temporarily
    renamed samples. The names are encoded (using the
    :meth:`~.Align.encode` method) before executing user code and then
    decoded (using :meth:`~.Align.rename`) as the end of the block
    (even if an exception occurs)::

        >>> with egglib.encode(obj) as mapping:
        ...     ...

    In the example above, the names of the original object ``obj``
    have been renamed using random, unique keys composed of alphanumerical
    characters. If needed, the mapping of the temporary keys to original
    names is available as ``mapping``. Operations requiring unique names
    or names compatible with external programs can be performed in the body
    of the ``with`` statement. And, finally, the original names will be
    restored when leaving the ``with`` statement, even if an exception occurs.

    .. note::
        There is a race condition with this context manager: while it is
        operating, the passed object is actually modified.
    """

    def __init__(self, obj, nbits=10):
        self.obj = obj
        self.nbits = nbits

    def __enter__(self):
        self.mapping = self.obj.encode(self.nbits)
        return self.mapping

    def __exit__(self, tp, value, traceback):
        self.obj.rename(self.mapping)

def struct_from_labels(data, lvl_clust=None, lvl_pop=None, lvl_indiv=None,
                       ploidy=None, skip_outgroup=False, outgroup_label='#'):
    """
    Extract structure from labels attached to an alignment.
    Create a new instance based on the labels
    of an :class:`Align` (or :class:`Container`) instance.

    :param data: an :class:`!Align` or :class:`!Container` instance
        containing the labels to be processed.

    :param lvl_clust: index of cluster labels. If ``None``, all
        populations are placed in a single cluster with ``None`` as label.

    :param lvl_pop: index of population labels. If ``None``, all
        individuals of a cluster are placed in a single population with
        the same label as their cluster.

    :param lvl_indiv: index of individual labels. If ``None``, the
        individual level is skipped and each sample is placed in a haploid
        individual. If specified, it is required that, if present and not
        ignored, outgroup samples have a label indicating individuals. If
        *lvl_indiv* is ``None``, any additional label of outgroup individuals
        will be ignored, even if present.

    :param ploidy: indicate the ploidy. Must be a positive number and,
        if specified, data must match the value. If not specified,
        ploidy will be detected automatically. Ploidy must still be
        consistent with ingroup and outgroup individuals, except for the
        case where there is a single outgroup sample, which is allowed
        whatever the ploidy for ingroup individual. Ploidy argument is
        ignored if *lvl_indiv* is ``None`` (ploidy is set to 1 in that
        case).

    :param skip_outgroup: indicate that outgroup samples should be skipped.
        No effect if there are no outgroup samples.

    :param outgroup_label: Label identifying outgroup samples. Only
        considered when it is the first label. Outgroup samples can only
        have either one or two labels (the first one equal to the one
        specified by this option, and the second one an optional
        individual label).

    :return: A new :class:`.Structure` object.

    .. versionchanged:: 3.6
        Allow outgroup with a single sequence even if ingroup ploidy is
        not 1.
    """

    obj = Structure()
    obj.from_labels(data, lvl_clust=lvl_clust, lvl_pop=lvl_pop,
            lvl_indiv=lvl_indiv, ploidy=ploidy,
            skip_outgroup=skip_outgroup, outgroup_label=outgroup_label)
    return obj

def struct_from_dict(ingroup, outgroup):
    """
    Build a structure from dictionaries. Create a new instance based on
    the structure specification provided as dictionaries. The two
    arguments are in the same format as  the return value of the
    :meth:`~.Structure.as_dict` method (see the documentation). Either
    argument can be replaced by ``None`` which is equivalent to an empty
    dictionary (no samples). Note that all keys must be strings.

    :param ingroup: a three-fold nested :class:`dict` of ingroup samples
        indices, or ``None``. The keys of the outter dictionary are
        cluster labels and its values are dictionaries representing
        each cluster. Each cluster dictionary has population labels as
        keys and dictionaries representing populations has values. Each
        population dictionary has ingroup individual labels as keys and
        lists of sample indices, pointing to samples in an
        :class:`.Align`, :class:`.Container`, or :class:`.Site` instance.

    :param outgroup: a :class:`dict` of outgroup samples indices, or
        ``None``. The keys must be outgroup individual labels, and the
        values lists of sample indices, pointing to samples in an
        :class:`!Align`, :class:`!Container`, or :class:`!Site` instance.

    :return: A new :class:`.Structure` object.
    """

    obj = Structure()
    obj.from_dict(ingroup, outgroup)
    return obj

def struct_from_samplesizes(pops, ploidy=1, outgroup=0):
    """
    Build a structure based on sample size per population.

    :param pops: list of sample sizes (one item per population). The
        values are interpreted as numbers of individuals.
    :param ploidy: ploidy (number of samples per individual).
    :param outgroup: number of outgroup individuals.

    :return: A new :class:`.Structure` object.

    The returned instance contains a single cluster, referenced as
    ``None`` and the specified number of populations. Population keys
    are ``pop1``, ``pop2``, ... If there is only one population, its
    label is ``pop1``. Similarly, individuals are referenced as
    ``idv1``, ..., consecutively for all populations and for the
    outgroup (in that order).
    """
    obj = Structure()
    obj.from_samplesizes(pops, ploidy, outgroup)
    return obj

def struct_from_iterable(iterable, fmt=None, data=None, missing=None,
        start=0, stop=None, function=None, skip_missing_names=False,
        outgroup=None):
    """
    Build a structure based on a list or other iterable. The iterable
    contains labels. Their maybe be one (i.e. a population label) item
    per iteration step or more (if each sample is described by several
    labels). In the latter case, the labels are to be provided as as a
    list of lists, typically. By default, labels are mapped to samples
    based on their position in the iterable (the first label is applied
    to the first sample, and so on). Alternatively, names can be
    provided along labels (i.e. be included in each of the sublists
    provided as input, identified by including ``N`` in *fmt*). Then the
    index is not considered and the labels are applied to the samples as
    identified by their names within an :class:`Align` or
    :class:`Container` passed as *data*.

    :param iterable: any iterable except :class:`str` (typically a list,
        possibly an open file). Iteration rounds (rows) must be
        non-empty string if *fmt*  is ``None``, or sequences (e.g.
        :class:`list`) of non-empty strings otherwise.  If rows are
        sequences, they must contain strings and have number of items
        specified by *fmt*. If an open file is passed, it is probably
        required to use the *function* option (such as
        ``function=str.split`` to split rows or ``function=str.strip``
        to just strip trailing newlines, or anything more complex as
        needed).

    :param fmt: specifies the meaning of items contained by each row. If
        ``None``, rows must be strings and specify population labels.
        Otherwise, *fmt* must be a sequence of one-character strings 
        (*fmt* may be a string) specifying what each item of a given row
        is supposed to represent. ``C``, ``P``, and ``I`` stand for
        cluster,  population, and individual labels, respectively. They
        may appear in  any order but cannot be repeated. There must be
        at least one of them and ``C``, if present, requires that ``P``
        is present also. ``N`` refers to sample names. It is
        optional and must also appear also once. If present, *data* must
        also be specified and the passed instance must not have
        duplicate names. If a name is missing in *data*, it will be
        silently skipped and excluded from the resulting structure. In
        addition, ``*`` can be used to specify irrelevant columns that
        should be ignored. It is optional and can be repeated. Note that
        if *outgroup* if specified, population labels matching the value
        given by *outgroup* are interpreted as membership to the
        outgroup. In that case, labels corresponding to the cluster
        field are ignored.

    :param data: an :class:`Align` or :class:`Container` instance in
        which sample names should be searched. Required if ``N`` is
        specified in *fmt* and not allowed otherwise.

    :param missing: value used to specify that a sample should not be
        included in the structure. Allows to skip an index (in
        particular when using the function in the default mode, not
        relying on sample names). If one label has the *missing* value,
        all labels must have it. Note that the string ``"None"`` (e.g.
        as read from a file) is not interpreted as the builtin object
        ``None``.

    :param start: index of the first row to process (also: number of
        rows to skip before starting processing). To skip a header line,
        one would use ``start=1``. Skipped rows don't affect the counter
        used to identify samples by index (the default, if names are not
        specified).

    :param stop: index where to stop processing (this row is not
        processed and iteration stops).

    :param function: a function to be applied to each
        processed row (rows before *start* and from *stop* on are not
        concerned).

    :param skip_missing_names: if names are searched in an :class:`!Align`
        or :class:`!Container` (*fmt* containing the ``N`` flag), names
        not appearing in the instance passed as *data* are skipped (the
        default is to raise an error).

    :param outgroup: population label interpreted as membership to the
        outgroup. By default (``None``), no samples can be affected to
        the outgroup. If not ``None``, the presence of this label in the
        population field will send the sample to the outgroup. In such
        case, the value interpreted as cluster label, if present, is
        ignored but the value interpreted as individual label, if
        present, is considered. This system implicitly forces the user
        to declare a population field to specify an outgroup (either by
        leaving *fmt* as ``None`` or including ``P`` in *fmt*).
        Obviously, the outgroup label cannot be used as a population
        label.

    :return: A new :class:`.Structure` object.

    .. versionchanged:: 3.6
        Added option *outgroup*.
    """
    obj = Structure()
    obj.from_iterable(iterable, fmt, data, missing, start, stop, function, skip_missing_names, outgroup)
    return obj

def struct_from_mapping(names, ploidy=1, clust=None, pop=None, outgroup=None, outgroup_haploid=False, indiv=None):
    """
    Build a structure with optional mappings. The user is required to
    provide a list of names and optional structure levels, each
    represented by a separate :class:`dict`.

    This method is mostly useful to generate a :class:`Structure` object
    for analyzing a VCF file whose samples are organized in known
    populations. Assume that the ``data.bcf`` file contains data for 6
    individuals organized in two populations and that the populations
    are described in the dictionary ``pops``. If the individuals are
    diploid, the following code is sufficient::

        vcf = egglib.io.VCF('data.bcf')
        pops = {'pop1': ['sample1', 'sample2', 'sample3'],
                'pop2': ['sample4', 'sample5', 'sample6']}
        struct = egglib.struct_from_mapping(vcf.get_samples(), pop=pops, diploid=2)

    :param names: :class:`list` or other sequence of names, in the order
        in which they appear in the data (:class:`.Align`,
        :class:`.io.VCF` or :class:`.Site` that will be analysed using
        the  resulting :class:`.Structure` object). This option is
        intended to receive the result of :meth:`.io.VCF.get_samples` or
        :meth:`.Align.names`.

    :param ploidy: to be used if *names* refers to individuals and if
        alleles represented by a given individuals appear consecutively
        in the data. Typically, for a VCF containing diploid data, the
        first two arguments would be ``names=vcf.get_samples()`` and
        ``ploidy=2``. If *names* refers to alleles within individuals
        (or to alleles not mapped to individuals, or to haploid
        individuals), *ploidy* should be left to 1.

    :param clust: mapping containing cluster names as keys and, for each
        cluster, a sequence of population names as value. The use of
        this option requires the option *pop*. Each item of the values
        of *clust* must one of the keys of *pop* and there may not be
        duplicates. If *clust* is ``None``, it is assumed that all
        samples belong to a single, unnamed cluster.

    :param pop: mapping containing population names as keys and, for
        each population, a sequence of individual names as value. If
        *indiv* is ``None``, each item of the values of *pop* must match
        one item of *names* (not all items of *names* need to be
        referred to by *pop*). If *indiv* is specified, each itme of the
        values of *pop* must match one key of *indiv*. In either case,
        there must not be any duplicates. If *pop* is ``None``, it is
        assumed that all samples belong to a single, unnamed population.

    :param outgroup: sequence of names of individuals belonging to the
        outgroup. The names must be part of the items of *names* if
        *indiv* is not specified, or part of the keys of *indiv*
        otherwise.

    :param outgroup_haploid: boolean flag specifying that the outgroup
        is represented by a single allele. Should only be set if *indiv*
        is ``None`` and if there is a single outgroup. Makes sense only
        if *ploidy* is more than 1.

    :param indiv: this argument should be used if *names* refers to
        alleles of an individual, when ploidy is larger than 1. This way
        of specifying structure is required if alleles belonging to a
        given individual are not consecutive. When *indiv* is specified,
        the *ploidy* argument should still be 1 (the ploidy level is
        implied by the value of this argument). *indiv* must be a
        dictionary mapping individual names to names provided by
        *names*. All items of the values of *indiv* must be present
        in the sequence given by *names*, but not all items of *names*
        need to be referred to. By default, each item of *names* is
        treated as an individual (possibly represented by several
        alleles, depending on the ploidy).

    :return: A new :class:`.Structure` object.

    .. versionadded:: 3.6
    """
    obj = Structure()
    obj.from_mapping(names, ploidy, clust, pop, outgroup, outgroup_haploid, indiv)
    return obj

class Structure(object):
    """
    Class describing organisation of samples. This class allows to map the
    samples of a :class:`.Site`, :class:`.Align`, or (probably more rarely)
    a :class:`.Container` instance to four levels of structuration: ingroup
    versus outgroup, then (within the ingroup) clusters of populations,
    populations, and individuals. If data is lacking a particular
    level of structure, it can be skipped. The number of individuals per
    population can vary, but the number of samples per individuals (that
    is, the ploidy) must be constant. An exception is allowed if there is
    a single outgroup sample overall although the ingroup ploidy is more
    than 1.

    New objects are created using the fonctions :func:`.struct_from_labels`
    and :func:`.struct_from_dict`, and existing objects can be recycled with
    their corresponding methods (:meth:`~.Structure.from_labels` and
    :meth:`~.Structure.from_dict`).

    .. versionchanged:: 3.6
        Support single-sample outgroup.
    """

    def __init__(self):
        self._obj = _eggwrapper.StructureHolder()

    @classmethod
    def _mk_from_obj(cls, obj):
        ret = cls.__new__(cls)
        ret._obj = obj
        return ret

    def from_labels(self, data, lvl_clust=None, lvl_pop=None,
                lvl_indiv=None, ploidy=None, skip_outgroup=False, outgroup_label='#'):
        """
        Import structure from an :class:`.Align` or :class:`.Container`.
        Reset the instance as if it was built using the standalone function
        :func:`.struct_from_labels`.
        The definitions of arguments are identical, but return ``None``.
        """

        self._obj.reset()

        # convert arguments to C++ friendly + checking
        if lvl_clust is None: lvl_clust = _eggwrapper.MISSING
        if lvl_clust < 0: raise ValueError('label index cannot be negative')
        if lvl_pop is None: lvl_pop = _eggwrapper.MISSING
        if lvl_pop < 0: raise ValueError('label index cannot be negative')
        if lvl_indiv is None: lvl_indiv = _eggwrapper.MISSING
        if lvl_indiv < 0: raise ValueError('label index cannot be negative')
        if ploidy is None: ploidy = _eggwrapper.MISSING
        elif ploidy < 0: raise ValueError('ploidy must be strictly positive')

        # import data
        self._obj.get_structure(data._obj, lvl_clust, lvl_pop, lvl_indiv, ploidy, skip_outgroup, outgroup_label)
        return

    def from_dict(self, ingroup, outgroup):
        """
        Import structure from user-specified dictionaries.
        Reset the instance as if it was built using the standalone
        function :func:`.struct_from_dict`.
        Arguments are identical, but this method returns ``None``.
        """

        # check None
        if None in ingroup and len(ingroup) > 1:
            raise ValueError('`None` can only be used as a cluster label if there is only one cluster')
        for clu in ingroup:
            if None in ingroup[clu]:
                if len(ingroup) > 1 or clu is not None or len(ingroup[None]) > 1:
                    raise ValueError('`None` can only be used as a population label if there is only one population in a single cluster also labelled `None`')

        self._obj.reset()
        idx_cache = set()

        if ingroup is not None:
            for clt, clt_d in ingroup.items():
                if clt is None: clt = ''
                if not isinstance(clt, str): raise TypeError('cluster label must be a string')
                clt_o = self._obj.add_cluster(clt)

                for pop, pop_d in clt_d.items():
                    if pop is None: pop = ''
                    if not isinstance(pop, str): raise TypeError('population label must be a string')
                    pop_o = self._obj.add_population(pop, clt_o)

                    for idv, samples in pop_d.items():
                        if not isinstance(idv, str): raise TypeError('individual label must be a string')
                        idv_o = self._obj.add_individual_ingroup(idv, pop_o)

                        for idx in samples:
                            if idx in idx_cache: raise ValueError('sample index found several times: {0}'.format(idx))
                            idx_cache.add(idx)
                            self._obj.add_sample_ingroup(idx, idv_o)

        if outgroup is not None:
            for idv, samples in outgroup.items():
                if not isinstance(idv, str): raise TypeError('outgroup individual label must be a string')
                idv_o = self._obj.add_individual_outgroup(idv)

                for idx in samples:
                    if idx in idx_cache: raise ValueError('sample index found several times: {0}'.format(idx))
                    idx_cache.add(idx)
                    self._obj.add_sample_outgroup(idx, idv_o)

        self._obj.check_ploidy()

    def from_samplesizes(self, pops, ploidy=1, outgroup=0):
        """
        Create structure from sample sizes per population.
        Reset the instance as if it was built using the standalone
        function :func:`.struct_from_samplesizes`.
        Arguments are identical, but this method returns ``None``.
        """
        if ploidy < 1: raise ValueError('invalid ploidy option')
        if outgroup < 0: raise ValueError('invalid outgroup option')
        idx = 0
        idv = 0
        ing = {None: {}}
        for i, n in enumerate(pops):
            d = {}
            for j in range(n):
                d['idv{0}'.format(idv+1)] = [idx+k for k in range(ploidy)]
                idv += 1
                idx += ploidy
            ing[None]['pop{0}'.format(i+1)] = d
        otg = {'idv{0}'.format(idv+i+1): [idx+i*ploidy+k for k in range(ploidy)] for i in range(outgroup)}
            # the line above can be replaced if the haploid outgroup is trigger (#324)
        self.from_dict(ing, otg)

    def from_iterable(self, iterable, fmt=None, data=None,
                missing=None, start=0, stop=None, function=None,
                skip_missing_names=False, outgroup=None):
        """
        Create structure from a list of labels.
        Reset the instance as if it was built using the standalone
        function :func:`.struct_from_iterable`.
        Arguments are identical, but this method returns ``None``.

        .. versionchanged:: 3.6
            Added option *outgroup*.
        """
        ing = {}
        if start is not None:
            if start < 0: raise ValueError('negative index not supported')
        else: start = 0
        if stop is not None and stop < 0: raise ValueError('negative index not supported')

        # ad hoc test to avoid obvious error (easy to just pass a string or a filename)
        if isinstance(iterable, str):
            raise TypeError('strings are not supported')

        # validate fmt and data
        if fmt is not None:
            if len(set(fmt) - set('NCPI*')) > 0:
                raise ValueError('invalid character in fmt')
            a = fmt.count('C')
            b = fmt.count('P')
            c = fmt.count('I')
            d = fmt.count('N')
            if a > 1: raise ValueError('character C cannot be repeated in fmt')
            if b > 1: raise ValueError('character P cannot be repeated in fmt')
            if c > 1: raise ValueError('character I cannot be repeated in fmt')
            if d > 1: raise ValueError('character N cannot be repeated in fmt')
            if (a+b+c == 0): raise ValueError('fmt must contain at least one of CPI')
            if a == 1 and b == 0: raise ValueError('in fmt, C requires P') 

        if fmt is not None and 'N' in fmt:
            if data is None:
                raise ValueError('a value should be provided for data if fmt is not None')
            else:
                if not isinstance(data, (Align, Container)):
                    raise TypeError('invalid type for data')

        elif data is not None:
                raise ValueError('no value should be provided for data if fmt is None')

        # perform iteration
        ing = {}
        otg = {}
        idx = 0
        for idx, row in enumerate(iterable):
            if idx < start: continue # skip until start
            if idx == stop: break # stop
            if function is not None: row = function(row)
            values = dict.fromkeys('CPI', None)
            if fmt is None:
                if row == missing: continue
                if row == outgroup:
                    values['I'] = f'idv{idx+1}'
                    values['P'] = outgroup
                else:
                    if not isinstance(row, str):
                        raise TypeError(f'row must be a string at iteration round #{idx+1}') 
                    if len(row) == 0: raise ValueError('empty labels not accepted')
                    values['P'] = row
                    values['I'] = f'idv{idx+1}'
            else:
                if isinstance(row, str):
                    raise TypeError(f'row must not be a string at iteration round #{idx+1}') 
                if len(row) != len(fmt):
                    raise ValueError(f'invalid number of items at iteration round #{idx+1}') 
                row = dict(zip(fmt, row))
                flag = 0b00
                for k in values:
                    if k in fmt:
                        x = row[k]
                        if x == missing:
                            flag |= 0b01
                        else:
                            if len(x) == 0: raise ValueError('empty labels not accepted')
                            flag |= 0b10
                            values[k] = x
                if flag == 0b11:
                    raise ValueError('either none or all labels should be missing')
                if flag == 0b01:
                    continue
                if 'N' in fmt:
                    name = row['N']
                    if 'I' not in fmt:
                        values['I'] = name
                if values['I'] is None:
                    values['I'] = f'idv{idx-start+1}'

            if fmt is not None and 'N' in fmt:
                res = data.find(name, index=True, multi=True)
                if len(res) == 0:
                    if skip_missing_names:
                        continue # silently supported
                    else:
                        raise ValueError(f'sample not found in data: {name}')
                if len(res) > 1:
                    raise ValueError(f'sample name repeated in data: {name}')
                sample_idx = res[0]
            else:
                sample_idx = idx-start

            if outgroup is not None and values['P'] == outgroup:
                if values['I'] not in otg:
                    otg[values['I']] = []
                otg[values['I']].append(sample_idx)
            else:
                if values['C'] not in ing:
                    ing[values['C']] = {}
                if values['P'] not in ing[values['C']]:
                    ing[values['C']][values['P']] = {}
                if values['I'] not in ing[values['C']][values['P']]:
                    ing[values['C']][values['P']][values['I']] = []
                ing[values['C']][values['P']][values['I']].append(sample_idx)

        self.from_dict(ing, otg)

    def from_mapping(self, names, ploidy=1, clust=None, pop=None,
                    outgroup=None, outgroup_haploid=False, indiv=None):
        """
        Create structure from mappings.
        Reset the instance as if it was built using the standalone
        function :func:`.struct_from_mapping`.
        Arguments are identical, but this method returns ``None``.

        .. versionadded:: 3.6
        """
        # make flat dictionary of individuals
        if indiv is None:
            if ploidy < 1: raise ValueError('ploidy must be at least 1')
            ing = {name: [ploidy*i+j for j in range(ploidy)] for i, name in enumerate(names)}
        else:
            if ploidy != 1: raise ValueError('if indiv is specified, ploidy must be 1')
            ing = {}
            cache = set()
            for key, values in indiv.items():
                ing[key] = []
                for name in values:
                    if name not in names: raise ValueError(f'indiv item {name} not in names')
                    if name in cache: raise ValueError(f'name {name} is duplicated in indiv')
                    cache.add(name)
                    ing[key].append(names.index(name))

        # pick up individuals belonging to outgroup
        otg = {}
        if outgroup is not None:
            cache = set()
            for name in outgroup:
                if name in cache:
                    raise ValueError(f'outgroup indiv {name} is duplicated')
                cache.add(name)
                if name not in ing:
                    raise ValueError(f'outgroup indiv {name} not found')
                otg[name] = ing.pop(name)

            # for haploid outgroup, correct all indices >= outgroup's index
            if outgroup_haploid:
                if len(outgroup) != 1:
                    raise ValueError('with outgroup_haploid option, there must be only one outgroup sample')
                if ploidy > 1:
                    lim = otg[outgroup[0]][-1]
                    del otg[outgroup[0]][1:]
                    for k, v in ing.items():
                        if v[0] > lim:
                            ing[k] = [i-1 for i in v]

        # create populations
        if pop is None:
            ing = {None: ing}

        else:
            res = {}
            cache = set()
            for key, values in pop.items():
                res[key] = {}
                for name in values:
                    if name in cache: raise ValueError(f'individual {name} is duplicated in populations')
                    cache.add(name)
                    if name not in ing:
                        if outgroup and name in outgroup: raise ValueError(f'individual both in ingroup and outgroup: {name}')
                        else: raise ValueError(f'individual not found: {name}')
                    res[key][name] = ing[name]
            ing = res

        # create clusters
        if clust is None:
            ing = {None: ing}
        else:
            if pop is None: raise ValueError('cannot specify clusters without populations')
            res = {}
            cache = set()
            for key, values in clust.items():
                res[key] = {}
                for name in values:
                    if name in cache: raise ValueError(f'population {name} is duplicated in clusters')
                    cache.add(name)
                    if name not in ing:
                        raise ValueError(f'population not found: {name}')
                    res[key][name] = ing[name]
            ing = res

        self.from_dict(ing, otg)

    def as_dict(self):
        """
        Generate dictionaries representing the structure.
        Return a :class:`tuple` of two :class:`dict` instances representing,
        respectively, the ingroup and outgroup structure.

        The ingroup dictionary is a three-fold nested dictionary
        (meaning it is a dictionary of dictionaries of dictionaries)
        holding lists of sample indices. The keys for these three nested
        levels are, respectively,
        cluster, population, and individual labels. Based on how the
        instance was created, there may be just one item or even none at
        all in any dictionary. In practice, if ``d`` is the ingroup
        dictionary and ``clt``, ``pop`` and ``idv`` are, respectively,
        cluster, population, and individual labels, the expression
        ``d[clt][pop][idv]`` will yield a :class:`list` of sample indices.

        The outgroup dictionary is a non-nested dictionary with
        individual labels as keys and lists of sample indices as values.
        """
        ingroup = {}
        for idx_clust in range(self._obj.num_clust()):
            clust = self._obj.get_cluster(idx_clust)
            k = clust.get_label()
            if k == '': k = None
            ingroup[k] = {}
            for idx_pop in range(clust.num_pop()):
                pop = clust.get_population(idx_pop)
                p = pop.get_label()
                if p == '': p = None
                ingroup[k][p] = {}
                for idx_indiv in range(pop.num_indiv()):
                    indiv = pop.get_indiv(idx_indiv)
                    i = indiv.get_label()
                    if i == '': i = None
                    ingroup[k][p][i] = [
                        indiv.get_sample(idx_sam) for idx_sam in range(indiv.num_samples())]
        outgroup = {}
        for idx_indiv in range(self._obj.num_indiv_outgroup()):
            indiv = self._obj.get_indiv_outgroup(idx_indiv)
            i = indiv.get_label()
            if i == '': i = None
            outgroup[i] = [
                indiv.get_sample(idx_sam) for idx_sam in range(indiv.num_samples())]
        return ingroup, outgroup

    def subset(self, pops=None, clusters=None, outgroup=True):
        """
        Make of copy with only selected populations.
        Generate a new :class:`Structure` instance containing only the
        specified populations. There must be at least one population
        and all populations must be valid.

        *pops* and *clusters* are lists of valid population and cluster
        labels. The order and possible replicates are not significant
        (if a label is replicated, the corresponding item is only
        included once).
        *outgroup* specifies if the outgroup must be included.

        .. versionadded:: 3.2
        """
        if pops is None: pops = []
        if clusters is None: clusters = []
        if len(pops)+len(clusters) == 0: raise ValueError('there must be at least one population')
        ret = Structure()
        res = ret._obj.subset(self._obj, '\x1f'.join(pops) + '\x1f', '\x1f'.join(clusters) + '\x1f', outgroup)
        if res != "": raise ValueError(f'invalid population label: {res}')
        return ret

    def make_auxiliary(self):
        """
        Generate the derived structure. This method generates the
        :class:`!Structure` instance that should be used to analyse data
        that have been filtered using the original structure and wherein the
        individual level has been collapsed.
        Formally return a new :class:`!Structure` instance describing the organisation
        of individuals in clusters and populations (ignoring the intra-individual
        level) using the rank of individuals as indices, the individuals
        being ranked in the order of increasing cluster and population
        indices.
        """
        ret = Structure()
        self._make_auxiliary(self._obj, ret._obj)
        return ret

    @staticmethod
    def _make_auxiliary(source, dest):
        dest.reset()
        cur = 0
        for c in range(source.num_clust()):
            clu = source.get_cluster(c)
            for p in range(clu.num_pop()):
                pop = clu.get_population(p)
                for i in range(pop.num_indiv()):
                    lbl1, lbl2, lbl3 = clu.get_label(), pop.get_label(), pop.get_indiv(i).get_label()
                    if lbl1 is None: lbl1 = ''
                    if lbl2 is None: lbl2 = ''
                    if lbl3 is None: lbl3 = ''
                    dest.process_ingroup(cur, lbl1, lbl2, lbl3)
                    cur += 1
        for i in range(source.num_indiv_outgroup()):
            lbl = source.get_indiv_outgroup(i).get_label()
            if lbl == '': lbl = None
            dest.process_outgroup(cur, lbl)
            cur += 1
        dest.check_ploidy(1)

    def make_sorted_auxiliary(self):
        """
        Generate the sorted version of the derived structure.
        Return a new :class:`!Structure` instance with sample indices
        ordered (to be used with objects which have been filtered using
        the original structure but wherein the individual level has not
        been collapsed).
        """
        dest = Structure()
        cur = 0
        for c in range(self._obj.num_clust()):
            clu = self._obj.get_cluster(c)
            lbl1 = clu.get_label()
            if lbl1 is None: lbl1 = ''
            for p in range(clu.num_pop()):
                pop = clu.get_population(p)
                lbl2 = pop.get_label()
                if lbl2 is None: lbl2 = ''
                for i in range(pop.num_indiv()):
                    idv = pop.get_indiv(i)
                    lbl3 = idv.get_label()
                    if lbl3 is None: lbl3 = ''
                    for j in range(idv.num_samples()):
                        dest._obj.process_ingroup(cur, lbl1, lbl2, lbl3)
                        cur += 1
        for i in range(self._obj.num_indiv_outgroup()):
            idv = self._obj.get_indiv_outgroup(i)
            lbl = idv.get_label()
            if lbl == '': lbl = None
            for j in range(idv.num_samples()): # if outgroup is haploid, will be 1 regardless of ploidy
                dest._obj.process_outgroup(cur, lbl)
                cur += 1
        dest._obj.check_ploidy(self._obj.get_ploidy()) # should support haploid outgroup
        return dest

    @property
    def ns(self):
        """ Number of ingroup samples included in the structure. """
        return self._obj.get_ni()

    @property
    def no(self):
        """ Number of outgroup samples included in the structure. """
        return self._obj.get_no()

    @property
    def req_ns(self):
        """
        Required number of samples. Equal to the largest index
        overall, plus one.

        .. versionchanged:: 3.2
            Return the larged sample index overall, not only of ingroup
            samples (which made little sense).
        """
        return self._obj.get_req()

    @property
    def num_clust(self):
        """ Number of clusters. """
        return self._obj.num_clust()

    @property
    def num_pop(self):
        """ Total number of populations. """
        return self._obj.num_pop()

    @property
    def num_indiv_ingroup(self):
        """ Total number of ingroup individuals. """
        return self._obj.num_indiv_ingroup()

    @property
    def num_indiv_outgroup(self):
        """ Number of outgroup individuals. """
        return self._obj.num_indiv_outgroup()

    @property
    def ploidy(self):
        """ Ploidy. """
        return self._obj.get_ploidy()

    def get_samples(self):
        """
        Return a :class:`set` with the index of all samples from
        the ingroup. All clusters, populations, and individuals stored
        in this object, excluding the outgroup.
        """
        return set([self._obj.get_indiv_ingroup(i).get_sample(j)
                    for i in range(self._obj.num_indiv_ingroup())
                            for j in range(self._obj.get_ploidy())])

    def get_populations(self):
        """
        Return a :class:`list` with the label of all populations from
        all clusters.

        .. versionadded: 3.2
        """
        return [lbl if (lbl:=self._obj.get_population(i).get_label()) != '' else None for i in range(self._obj.num_pop())]

    def get_clusters(self):
        """
        Return a :class:`list` with the label of all clusters.

        .. versionadded: 3.2
        """
        return [lbl if (lbl:=self._obj.get_cluster(i).get_label()) != '' else None for i in range(self._obj.num_clust())]

    def shuffle(self, mode='it', nr=None, rnd=None):
        """
        Shuffle randomly the structure (context manager).
        This method allows to test for independence of any level of
        structuration. It is not allowed to modify the structure object
        while the object returned by this method is in use. This
        method is designed to be used in a context manager, and the
        returned object is iterable (see examples below).

        A simple example::

            >>> struct = egglib.struct_from_labels(aln, lvl_clust=0, lvl_pop=1, lvl_idv=2)
            >>> cs = egglib.ComputeStats(struct=struct)
            >>> cs.add_stats('FistWC')
            >>> with struct.shuffle(mode='st'):
            ...     print(cs.process_align(aln))

        Example as an iterator::

            >>> with struct.shuffle(mode='st', nr=100) as shuffler:
            ...     for _ in shuffler:
            ...         print(cs.process_align(aln))

        .. note::

            We can ignore the return value of the iterator since it
            constantly returns the same instance, which is internally
            modified at each iterator round. The modifications will be
            taken in account by :class:`!ComputeStats` when computing
            diversity statistics.

        :param mode: A string describing what structure level to shuffle
            and with what constraint. This is best understood with reference
            to the corresponding F-statistic: for example, the mode ``is``
            assumes that :math:`F_{is}` is zero.

            * ``it`` -- samples shuffled in total.
            * ``ic`` -- samples shuffled within their original cluster.
            * ``is`` -- samples shuffled within their original population.
            * ``st`` -- whole individuals shuffled in total.
            * ``sc`` -- whole individuals shuffled within their original cluster.
            * ``ct`` -- whole populations shuffled in total.

        :param nr: number of replicates. If ``None``, the instance is
            shuffled immediately, and once, when entering the context
            manager. Otherwise,
            return an iterable context manager which will perform the
            requested number of shuffling replicates and yield back the
            same (modified) structure at each iteration. In the latter
            case, shuffling won't start until iteration has been entered.

        :return: A context manager, which itself is iterable if *nr*
            is not ``None``.
        """
        try: mode = ['it', 'ic', 'is', 'st', 'sc', 'ct'].index(mode)
        except ValueError: raise ValueError('invalid string passed as `mode`: {0}'.format(mode))
        else: return StructureShuffler(self, mode, nr, rnd)

class StructureShuffler(object):
    def __init__(self, struct, mode, nr, rnd):
        self._struct = struct
        self._mode = mode
        self._nr = nr
        if self._nr is not None:
            if not isinstance(self._nr, int): raise TypeError('invalid type for argument `nr`')
            if self._nr < 0: raise ValueError('negative values not allowed for argument `nr`')

    def __enter__(self):
        self._struct._obj.shuffle_init(self._mode)
        if self._nr is None: self._struct._obj.shuffle()
        return self

    def __exit__(self, tp, value, traceback):
        self._struct._obj.shuffle_restore()

    def __iter__(self):
        if self._nr is None: raise TypeError('this object is not iterable')
        self._it = 0
        return self

    def __next__(self):
        if self._it == self._nr: raise StopIteration
        self._it += 1
        self._struct._obj.shuffle()
        return self._it - 1
