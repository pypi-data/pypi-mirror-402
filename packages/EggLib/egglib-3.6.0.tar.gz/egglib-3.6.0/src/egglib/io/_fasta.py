"""
    Copyright 2015-2023 Stephane De Mita, Mathieu Siol

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

from .. import eggwrapper as _eggwrapper
from .. import _interface
from .. import alphabets

def from_fasta(fname, alphabet, labels=False, label_marker='@', label_separator=',', cls=None):
    """
    Import sequences from a fasta file.
    Create a new instance of either :class:`.Align` or
    :class:`.Container` from data read from a fasta-formatted file.
    To process data from a fasta-formatted string, use
    :func:`.io.from_fasta_string`.

    :param source: name of a fasta-formatted sequence file.
    :param alphabet: an :class:`.Alphabet` instance defining the type
        of data. Only character alphabets are allowed (such as
        :py:obj:`.alphabets.DNA`, or :py:obj:`.alphabets.protein`).
    :param labels: import group labels. If so, they are not actually required to be
        present for each (or any) sequence. By default tags in sequence names
        considered to be part of the name and not as labels.
    :param label_marker: this option allows to change the character
        indicating the start of the labels.
    :param label_separator: this options allows to change character used
        to separate labels.
    :param cls: type that should be generated. Possible values are:
        :class:`!Align` (then, data must be aligned),
        :class:`!Container`, or ``None``. In the latter case, an
        :class:`!Align` is returned if data are found to be aligned or
        if the data set is empty, and otherwise a :class:`!Container` is
        returned.

    :return: A new :class:`.Container` or :class:`.Align` instance
        depending on the value of the *cls* option.
    """
    if not isinstance(alphabet._obj, _eggwrapper.CharAlphabet):
        raise ValueError('invalid alphabet for parsing fasta data: {0}'.format(alphabet.name))
    fasta_parser = _eggwrapper.FastaParser()
    fasta_parser.open_file(str(fname), alphabet._obj)
    return _from_fasta(fasta_parser, alphabet, labels, label_marker, label_separator, cls)

def from_fasta_string(string, alphabet, labels=False, label_marker='@', label_separator=',', cls=None):
    """
    Import sequences from a fasta-formatted string. Identical
    to :func:`.io.from_fasta` but directly takes an fasta-formatted string as first argument.
    """
    if not isinstance(alphabet._obj, _eggwrapper.CharAlphabet):
        raise ValueError('invalid alphabet for parsing fasta data: {0}'.format(alphabet.name))
    fasta_parser = _eggwrapper.FastaParser()
    fasta_parser.set_string(string, alphabet._obj)
    return _from_fasta(fasta_parser, alphabet, labels, label_marker, label_separator, cls)

def _from_fasta(fasta_parser, alphabet, labels, label_marker, label_separator, cls):
    obj = _eggwrapper.DataHolder(False)
    fasta_parser.read_all(labels, obj, label_marker, label_separator)
    if cls is _interface.Align or cls is None:
        ns = set([obj.get_nsit_sample(i) for i in range(obj.get_nsam())])
        if len(ns) == 0:
            ns = 0
            if cls is None: cls = _interface.Align
        elif len(ns) == 1:
            ns = ns.pop()
            if cls is None: cls = _interface.Align
        else:
            if cls is _interface.Align:
                raise ValueError('cannot create `Align`: lengths of sequences do not match')
            cls = _interface.Container
    elif cls is not _interface.Container:
        raise ValueError('invalid value provided for `cls`')

    if cls is _interface.Container: return _interface.Container._create_from_data_holder(obj, alphabet)
    else: return _interface.Align._create_from_data_holder(obj, alphabet)

class fasta_iter(object):
    """
    Iterative sequence-by-sequence fasta parser.
    
    :param fname: name of a fasta-formatted file.
    :param alphabet: an :class:`.Alphabet` instance defining the type
        of data. Only character alphabets are allowed (such as
        :py:obj:`.alphabets.DNA` and :py:obj:`.alphabets.protein`).
    :param labels: import group labels from sequence names
        (by default, they are considered as part of the name).

    This function can be
    used in an iteration as shown below:

    .. code-block:: python

        >>> for item in egglib.io.fasta_iter(fname):
        ...     ...

    The ``with`` statement is also supported, which
        ensures that the input file is properly closed whenever the
        ``with`` statement completes:

    .. code-block:: python

       >>> with egglib.io.fasta_iter(fname) as f:
       ...     for item in f:
       ...         ...

    Each iteration yields a :class:`.SampleView` instance (which is
    valid only during the iteration round, see the warning below).

    .. warning::
        The aim of this iterator is to iterate over large fasta files
        without actually storing all data in memory at the same time.
        The :class:`.SampleView` instance provided at each iteration is a proxy to
        a local :class:`.Container` instance that is recycled at each
        iteration step. The iteration variable should be used immediately
        and never stored as this. If one wants to sequence data, they should
        copy them immediately (typically using the
        :meth:`~.Container.add_sample` method of a separate
        :class:`.Container` instance).
    """

    def __init__(self, fname, alphabet, labels=False):
        self._parser = _eggwrapper.FastaParser() # define it before, otherwise the exit code will break in case of error
        if not isinstance(alphabet._obj, _eggwrapper.CharAlphabet):
            raise ValueError('invalid alphabet for parsing fasta data: {0}'.format(alphabet.name))
        self._parser.open_file(fname, alphabet._obj)
        self._cont = _interface.Container(alphabet)
        self._labels = labels

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._parser.close()

    def __del__(self):
        self._parser.close()

    def __iter__(self):
        return self

    def __next__(self):
        if not self._parser.good(): raise StopIteration
        self._cont.reset()
        self._parser.read_sequence(self._labels, self._cont._obj)
        self._cont._ns = self._cont._obj.get_nsam()
        return _interface.SampleView(self._cont, 0)
