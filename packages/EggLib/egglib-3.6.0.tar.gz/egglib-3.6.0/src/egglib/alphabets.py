"""
    Copyright 2018-2023 Stephane De Mita, Mathieu Siol

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

from . import eggwrapper as _eggwrapper

class Alphabet(object):
    """
    Define acceptable lists of alleles for a type of data.
    This class is designed to be associated to EggLib objects holding
    diversity data (:class:`~Align`, :class:`~Container`, and :class:`~Site`).
    It defines the lists of exploitable and missing allelic values (both
    being allowed in all objects using this alphabet).
    Several pre-defined instances instances are
    available in :ref:`alphabets`, but the user can easily define his own
    alphabets using this class. It is strongly advised to use the pre-defined
    alphabet designed for DNA sequences as it is optimized for access speed.

    :param cat: Type of the alphabet, as a string taken from the following list:

        +---------------+-------------------------------------+
        |               |                                     |
        +---------------+-------------------------------------+
        | ``int``       | Positive or negative, discrete      |
        |               | integers. ``range`` is more         |
        |               | adapted to cases with many alleles. |
        +---------------+-------------------------------------+
        | ``char``      | Single-character strings            |
        |               | (such as DNA).                      |
        +---------------+-------------------------------------+
        | ``string``    | Strings representing segments of    |
        |               | biological sequences (appropriate   |
        |               | for codons or indel variants).      |
        +---------------+-------------------------------------+
        | ``custom``    | Alleles represented by a code or a  |
        |               | name (e.g. for genomic              |
        |               | rearrangements). In particular,     |
        |               | this type of alphabets does not     |
        |               | allow sequence concatenation,       |
        |               | contrary to ``string``.             |
        +---------------+-------------------------------------+
        | ``range``     | Continuous ranges of integers       |
        |               | (regardless of their sign). This is |
        |               | much more efficient than using an   |
        |               | integer alphabet with many alleles. |
        +---------------+-------------------------------------+

    :param expl: list of exploitable alleles (for ``range``, see :ref:`below <range_spec>`).

    :param miss: list of missing alleles (for ``range``, see :ref:`below <range_spec>`).
        There must not be any overlap between exploitable and missing
        alleles in any case.

    :param case_insensitive: if set to ``True``, case will be ignored
        for allele comparison (alleles differing in case only will be
        considered to be identical). Note that this does not preserve
        case of provided alleles which are all converted to upper case.
        Only accepted for ``char`` and ``string`` alphabets.

    :param name: name of the alphabet. Alphabet name is of relatively
        modest importance and is not required to be unique. The alphabet
        name is used in error messages when an invalid allele is
        processed. By default, use the alphabet type as name.

    .. _range_spec:

    For ``range`` alphabets, both parameters *expl* and *miss*
    must be specified as a ``(start, stop)`` expression. All values from
    ``start`` up to ``stop``-1 will be considered as valid allele values
    (``stop`` is not included).
    To specify a unique value, use ``(value, value+1)``. To specify no
    value at all, use ``None`` (you can also abuse the syntax by using
    ``(x, x)`` with any ``x`` value. You can omit either term, or both,
    to denote a semi-infinite or fully infinite range. Of course, setting
    ``expl=(None, None)`` prevent you from specifying any missing allele
    value.
    """

    @classmethod
    def _make(cls, obj): # make an instance around a provided _eggwrapper.AbstractBaseAlphabet subclass instance
        inst = cls.__new__(cls)
        inst._obj = obj
        return inst

    def __init__(self, cat, expl, miss, case_insensitive=False, name=None):
        # create object of right type
        if cat == 'int':
            if case_insensitive == False: self._obj = _eggwrapper.IntAlphabet()
            else: raise ValueError('case insensitivity not available for int alphabet')
        elif cat == 'char':
            if case_insensitive == False: self._obj = _eggwrapper.CharAlphabet()
            else: self._obj = _eggwrapper.CaseInsensitiveCharAlphabet()
        elif cat == 'string':
            if case_insensitive == False: self._obj = _eggwrapper.StringAlphabet()
            else: self._obj = _eggwrapper.CaseInsensitiveStringAlphabet()
        elif cat == 'custom':
            if case_insensitive == False: self._obj = _eggwrapper.CustomStringAlphabet()
            else: raise ValueError('case insensitivity not available for custom alphabet')
        elif cat == 'range':
            if case_insensitive == False: self._obj = _eggwrapper.RangeAlphabet()
            else: raise ValueError('case insensitivity not available for range alphabet')
        else: raise ValueError('invalid alphabet category')

        # set name
        if name is None:
            name = type(self._obj).__name__
        elif not isinstance(name, str): raise TypeError('name must be a string')
        self._obj.set_name(name)

        # set type
        self._obj.set_type(cat)

        # configure RangeAlphabet
        if cat == 'range':
            if expl is None: expl = [0, 0]
            else:
                try: expl = list(expl)
                except TypeError: raise TypeError('invalid exploitable range definition: {0}'.format(expl))
            if len(expl) == 1: miss = [expl[0], expl[0]+1]
            if len(expl) != 2: raise ValueError('invalid exploitable range specification')
            if expl[0] is None: expl[0] = - _eggwrapper.MAX_ALLELE_RANGE
            elif expl[0] < - _eggwrapper.MAX_ALLELE_RANGE: raise ValueError('lower bound of exploitable range is out of allowed range')
            if expl[1] is None: expl[1] = _eggwrapper.MAX_ALLELE_RANGE + 1
            elif expl[1] > _eggwrapper.MAX_ALLELE_RANGE + 1: raise ValueError('higher bound of exploitable range is out of allowed range')
            if not isinstance(expl[0], int) or not isinstance(expl[1], int): raise ValueError('invalid exploitable range specification')
            if expl[1] < expl[0]: raise ValueError('invalid exploitable range specification')
            self._obj.set_exploitable(expl[0], expl[1])
            if miss is None: miss = [0, 0]
            else:
                try: miss = list(miss)
                except TypeError: raise TypeError('invalid missing range definition: {0}'.format(miss))
            if len(miss) == 1: miss = [miss[0], miss[0]+1]
            if len(miss) != 2: raise ValueError('invalid missing range specification')
            if miss[0] is None: miss[0] = - _eggwrapper.MAX_ALLELE_RANGE
            elif miss[0] < - _eggwrapper.MAX_ALLELE_RANGE: raise ValueError('lower bound of missing range out of allowed range')
            if miss[1] is None: miss[1] = _eggwrapper.MAX_ALLELE_RANGE + 1
            elif miss[1] > _eggwrapper.MAX_ALLELE_RANGE + 1: raise ValueError('higher bound of missing range out of allowed range')
            if not isinstance(miss[0], int) or not isinstance(miss[1], int): raise ValueError('invalid missing range specification')
            if miss[1] < miss[0]: raise ValueError('invalid missing range specification')
            self._obj.set_missing(miss[0], miss[1])
        else:
            if expl is None: expl = []
            if miss is None: miss = []
            for i in expl:
                self._check(i)
                self._obj.add_exploitable(i)
            for i in miss:
                self._check(i)
                self._obj.add_missing(i)

    def _check(self, value):
        # check that the passed allelic value is of the appropriate type for the instance
        if self._obj.get_type() == 'DNA':
            if not (isinstance(value, str) and len(value) == 1): raise TypeError('expect single-character string alleles')
            return
        if self._obj.get_type() == 'codons':
            if not (isinstance(value, str) and len(value) == 3): raise TypeError('expect three-character string alleles')
            return
        if self._obj.get_type() == 'char':
            if not (isinstance(value, str) and len(value) == 1): raise TypeError('expect single-character string alleles')
            return
        if self._obj.get_type() == 'int':
            if not isinstance(value, int): raise TypeError('expect integer alleles')
            return
        if self._obj.get_type() == 'string':
            if not isinstance(value, str): raise TypeError('expect string alleles')
            return
        if self._obj.get_type() == 'custom':
            if not isinstance(value, str): raise TypeError('expect string alleles')
            return
        if self._obj.get_type() == 'range':
            raise ValueError('range alphabets cannot be modified')
            return
        raise TypeError('invalid type for {0} alphabet: {1}'.format(self._obj.get_type(), type(value).__name__))

    @property
    def name(self):
        """
        Name of the alphabet. The value might be changed.
        """
        return self._obj.get_name()

    @name.setter
    def name(self, value):
        if not isinstance(value, str): raise TypeError('name must be a string')
        self._obj.set_name(value)

    def get_alleles(self):
        """
        Generate the list of alleles.
        Return a tuple with two items: the list of exploitable
        and the list of missing alleles, respectively. For a ``range`` alphabet, each
        list is replaced by a tuple with the bounds of the range
        (replaced by ``None`` in case of an empty range).
        """
        if isinstance(self._obj, _eggwrapper.RangeAlphabet):
            a = self._obj.first_exploitable()
            b = self._obj.end_exploitable()
            c = self._obj.first_missing()
            d = self._obj.end_missing()
            if b == a:
                ab = None
            else:
                if a == -_eggwrapper.MAX_ALLELE_RANGE: a = None
                if b ==  _eggwrapper.MAX_ALLELE_RANGE + 1: b = None
                ab = (a, b)
            if d == c:
                cd = None
            else:
                if c == -_eggwrapper.MAX_ALLELE_RANGE: c = None
                if d ==  _eggwrapper.MAX_ALLELE_RANGE + 1: d = None
                cd = (c, d)
            return (ab, cd)
        else:
            return ([self._obj.get_value(i) for i in range(self._obj.num_exploitable())],
                    [self._obj.get_value(-i-1) for i in range(self._obj.num_missing())])

    @property
    def num_alleles(self):
        """
        Total number of alleles.
        """
        return self._obj.num_exploitable() + self._obj.num_missing()

    @property
    def num_exploitable(self):
        """
        Number of exploitable alleles.
        """
        return self._obj.num_exploitable()

    @property
    def num_missing(self):
        """
        Number of missing alleles.
        """
        return self._obj.num_missing()

    def add_exploitable(self, value):
        """
        Add an exploitable allele to the instance. Not allowed for ``range``
        alphabets and for the special alphabet :py:obj:`.alphabets.DNA`.
        The allele value
        must be of the appropriate type, and unique.
        """
        self._check(value)
        self._obj.add_exploitable(value)

    def add_missing(self, value):
        """
        Add a missing allele to the instance. Not allowed for ``range``
        alphabets and for the special alphabet :py:obj:`.alphabets.DNA`.
        The allele value must be of the appropriate type, and unique.
        """
        self._check(value)
        self._obj.add_missing(value)

    @property
    def case_insensitive(self):
        """
        Boolean indicating if the alphabet is case-insensitive.
        """
        return self._obj.case_insensitive()

    @property
    def type(self):
        """ Type of the alphabet. Same as the *cat* argument of the constructor. """
        return self._obj.get_type()

    def get_code(self, value):
        """
        Return the code of a given allele. Missing alleles are indicated
        by a negative code.
        """
        try: return self._obj.get_code(value)
        except TypeError: raise TypeError('invalid allele type for this alphabet')

    def get_value(self, code):
        """
        Return the value of for given code. Missing alleles are indicated
        by a negative code.
        """
        if not isinstance(code, int): raise TypeError('allele codes must be represented by an integer')
        return self._obj.get_value(code)

    def lock(self):
        """
        Lock the alphabet. When the alphabet is locked, a :exc:`ValueError`
        will be raised if an attempt to modify the alphabet is made.
        """
        self._obj.lock()

    @property
    def locked(self):
        """
        ``True`` if the alphabet is locked.
        """
        return self._obj.is_locked()

#
# WARNING: ORDER OF DNA, PROTEIN and CODON ALPHABETS _MUST NOT_ BE MODIFIED
# C++ implementation of GeneticCode depends on it
#

DNA = Alphabet._make(_eggwrapper.get_static_DNAAlphabet())
"""Alphabet optimized for DNA sequences (case-insensitive)."""

codons = Alphabet._make(_eggwrapper.get_static_CodonAlphabet())
"""Alphabet for codon triplets (only upper case)."""

protein = Alphabet('char', 'ACDEFGHIKLMNPQRSTVWY*', '-X?', case_insensitive=False, name='protein')
"""Alphabet for amino acids (only upper case). Stop codons are supported as ``*``."""
protein.lock()

positive_infinite = Alphabet('range', [0, None], [-1], case_insensitive=False, name='positive infinite')
"""Alphabet with all positive integer values."""
positive_infinite.lock()

genepop = Alphabet('range', (1, 1000), (0, 1), name='genepop')
"""Alphabet matching the Genepop format."""
genepop.lock()

binary = Alphabet('int', [0, 1], [-9, -1, 999], name='binary')
"""Alphabet for binary data (0/1 integers)."""
binary.lock()
