"""
    Copyright 2008-2023 Stephane De Mita, Mathieu Siol

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

import sys, re, functools
from .. import _interface
from .. import alphabets

_iupac = {
    '?': set('ACGT-'),
    '-': set('-'),
    'A': set('A'),
    'C': set('C'),
    'G': set('G'),
    'T': set('T'),
    'M': set('AC'),
    'R': set('AG'),
    'W': set('AT'),
    'S': set('CG'),
    'Y': set('CT'),
    'K': set('GT'),
    'B': set('CGT'),
    'D': set('AGT'),
    'H': set('ACT'),
    'V': set('ACG'),
    'N': set('ACGT')
}

for _i in list(_iupac.keys()):
    if _i != '?' and _i != '-': # it would be no harm but awkward
        _iupac[_i.lower()] = _iupac[_i]

_iupac_set = set(_iupac.keys())
_bases_set = _iupac_set - set('-?')

_trans = dict(zip('ACGT-?', 'TGCA-?'))

_a = []
_b = []
for _i, _values in _iupac.items():
    if _i.islower(): continue
    values = set([_trans[_j] for _j in _values])
    for _j, _k in _iupac.items():
        if _k == values:
            _a.append(_i)
            _b.append(_j)
            if _i.lower() != _i:
                _a.append(_i.lower())
                _b.append(_j.lower())
            break
    else: raise RuntimeError('internal error')
_rc_conv =  str.maketrans(''.join(_a), ''.join(_b))

_regex_map = {}
for _i, _j in _iupac.items():
    _map = set()
    for _m, _n in _iupac.items():
        if _m.isupper():
            for _k in _n:
                 if _k not in _j: break
            else:
                _map.add(_m)
    _regex_map[_i] = _map.pop() if len(_map) == 1 else '[' + ''.join(_map) + ']'

_gap_codes = {
    'DNA': [alphabets.DNA.get_code('-')],
    'protein': [alphabets.protein.get_code('-')],
    'codons': [alphabets.codons.get_code(allele) for allele in alphabets.codons.get_alleles()[1] if '-' in allele]
}

def rc(seq):
    """
    Reverse-complement a DNA sequence.

    :param seq: input nucleotide sequence, as a :class:`str`, or a :class:`.SequenceView`.

    :return: The reverse-complemented sequence (see details below).

    The case of the provided sequence is preserved. Ambiguity characters
    are complemented according to the table shown :ref:`here <iupac-nomenclature>`.
    Invalid characters characters raise a :exc:`ValueError`.
    """
    if isinstance(seq, _interface.SequenceView): seq = seq.string()
    if not _iupac_set.issuperset(seq): raise ValueError('invalid character in DNA sequence')
    return seq[::-1].translate(_rc_conv) 

def compare(seq1, seq2):
    """
    Compare two sequences. The comparison supports ambiguity characters
    (see :ref:`here <iupac-nomenclature>`) such that partially overlapping
    ambiguity sets characters are not treated as different. For example,
    ``A`` and ``M`` are not treated as different, nor are ``M`` and
    ``R``. Only IUPAC characters may be supplied.

    :param seq1: a DNA sequence (as a :class:`str` or  a :class:`.SequenceView`).
    :param seq2: another DNA sequence (idem).

    :return: ``True`` if sequences have the same length and they either
        are identical or differ only by overlapping IUPAC characters,
        ``False`` otherwise.
    """
    
    if isinstance(seq1, _interface.SequenceView): seq1 = seq1.string()
    if isinstance(seq2, _interface.SequenceView): seq2 = seq2.string() 
    
    if len(seq1) != len(seq2):
        return False

    try:
        for i, j in zip(seq1, seq2):
                if _iupac[i].isdisjoint(_iupac[j]):
                    return False
    except KeyError as e:
        raise ValueError('unknown DNA base: {0}'.format(e.args[0]))

    return True

def regex(query, both_strands=False):
    """
    Turn a DNA sequence into a regular expression. The input sequence
    should contain IUPAC characters only (see
    :ref:`here <iupac-nomenclature>`). Ambiguity characters will be teated as
    follows: an ambiguity will match either (1) itself, (2) one of the
    characters it defines, or (3) one of the ambiguity characters that
    define a subset of the characters it defines. For example, a ``M``
    in the query will match an ``A``, a ``C`` or a ``M``, and a ``D``
    will match all the following: ``A``, ``G``, ``T``, ``R``, ``W``,
    ``K``, and ``D``. The fully degenerated ``N`` matches all four bases
    and all intermediate ambiguity characters and, finally, ``?``
    matches all allowed characters (including alignment gaps). Note ``-``
    only matches itself.

    :param query: a :class:`str` containing IUPAC characters or a :class:`.SequenceView`.

    :param both_strands: look for the query on both forward and reverse
        strands (by default, only on forward strand).

    :return: A regular expression as a  :class:`!str` expanding ambiguity
        characters to all compatible characters.

    Result of this function can be used with the module :mod:`re` to
    locate occurrences of a motif or the position of a sequence as in:

    .. code:: python

        >>> regex = egglib.tools.regex(query)
        >>> for hit in re.finditer(regex, subject):
        ...     print(hit.start(), hit.end(), hit.group(0))

    The returned regular expression includes upper-case characters,
    regardless of the case of input characters. To perform a
    case-insensitive search, use the :data:`re.IGNORECASE` flag of the
    :mod:`!re` module in regular expression searches (as in
    ``re.search(egglib.tools.regex(query), subject, re.IGNORECASE)``.
    Note that the regular expression is contained into a group if
    *both_strands* is ``False``, and two groups otherwise (one for each
    strand).
    """
    
    if isinstance(query, _interface.SequenceView): query = query.string()
    
    chars = list(query)
    for i, v in enumerate(chars):
        if v not in _regex_map: raise ValueError('invalid character in DNA sequence')
        chars[i] = _regex_map[v]
    if both_strands: return '({0})|{1}'.format(''.join(chars), regex(rc(query), False))
    else: return '(' + ''.join(chars) + ')'

def motif_iter(subject, query, mismatches=0, both_strands=False, case_independent=True, only_base=True):
    """
    Iterate over hits of a given query.
    Return an iterator over hits of the provided query in the subject
    sequence. The query should only contain bases (including IUPAC
    ambiguity characters as listed in :ref:`here <iupac-nomenclature>`, but
    excluding ``-`` and ``?``). Ambiguity characters are treated as
    described in :func:`.regex` (the bottom line is that ambiguities in
    the query can only match identical or less degenerate ambiguities in
    the subject). Mismatches are allowed, and the iterator will first
    yield identical hits (if they exist), then hits with one mismatch,
    then hits with two mismatches, and so on.

    :param subject: a DNA sequence as :class:`str` or a :class:`.SequenceView`. The sequence may
        contain ambiguity characters. In principle, the subject sequence
        should contain IUPAC characters only, but this is not strictly
        enforced (non-IUPAC characters will always be treated as
        different of IUPAC characters).

    :param query: a DNA sequence as :class:`!str` or a :class:`!SequenceView`, also containing
        IUPAC characters only.

    :param mismatches: maximum number of mismatches.

    :param both_strands: look for the query on both forward and reverse
        strands (by default, only on forward strand).

    :param case_independent: if ``True``, perform case-independent
        searches.

    :param only_base: if ``True``, never create a hit if the putative
        hit sequence contains an alignment gap (``-``) or a ``?``
        character, irrespective of the number of allowed mismatches.

    :return: An iterator returning, for each hit, a
        ``(start, stop, strand, num)`` tuple where ``start`` and ``stop``
        are the position of the hit such that ``subject[start:stop]``
        returns the hit sequence, ``strand`` is the strand as ``+`` or
        ``-``, and ``num`` is the number of mismatches of the hit.

    .. note::

        If a given query has a hit on both strands at the same position
        (this only happens if the sequence is a motif equal to its
        reverse-complement like ``AATCGATT``), it is guaranteed that the
        only one hit will be returned for a given position (no twice on
        each strand). However, the value of the ``strand`` flag is not
        defined.

    .. warning::

        This function is designed to be efficient only if the number of
        mismatches is small (only a few). A combination of a large
        number of mismatches (more than 2 or 3) and a large query
        sequence (as early as 10 or 20), will take significant time to
        complete. More complex problems require the use of genuine
        pairwise ocal alignment tools.
    """

    if isinstance(subject, _interface.SequenceView): subject = subject.string()
    if isinstance(query, _interface.SequenceView): query = query.string()
    
    # get query length
    ln = len(query)
    if ln < 1: raise ValueError('query must not be empty')
    if not _bases_set.issuperset(query): raise ValueError('invalid character in DNA sequence')
    if mismatches > ln: raise ValueError('too many mismatches allowed')

    # initialize table of positions of mismatches
    # if n>1, mismatch indexes are always increasing (first value for n=3 is [0,1,2])
    n = 1 # pos cannot be incremented if 0
    pos = [-1] # the last (and only) index will be incremented once before use

    # current query (initially without mismatches)
    cur = list(query)

    # cache to avoid returning several times the same hit
    cache = set()

    # process all possibilities (no mismatches, then 1, then 2, etc.)
    while True:

        # perform search (will be done at least once)
        for mo in re.finditer(regex(''.join(cur), both_strands), subject, re.I if case_independent else 0):
            if mo.start() not in cache:
                yield mo.start(), mo.end(), '+-'[mo.lastindex-1], 0 if pos[0]==-1 else n
                cache.add(mo.start())

        # increment mismatch index (initialized to -1)
        i = n -1 # current mismatch index
        pos[i] += 1 # increment last index
        stop = ln # stop value (maximum pos for n=3 and ln=10 is [7,8,9])

        # increment previous index if end is reached (and so one)
        while pos[i] == stop:

            # all mismatches processed, add a new mismatch
            if i == 0:
                n += 1
                pos = list(range(n))
                break

            # increment previous index
            else:
                i -= 1
                stop -= 1
                pos[i] += 1
                pos[i+1:] = range(pos[i]+1, pos[i]+n-i)

        # quit if already too many mismatches
        if n > mismatches: break

        # create a list from the query with allowed mismatches (at least 1)
        cur = list(query)
        for i, v in enumerate(pos):
            cur[v] = 'N' if only_base else '?'

def _get_gaps(gaps, alph):
    # helper to validate gap option
    if gaps is None:
        gap_codes = _gap_codes.get(alph.name, None)
        if gap_codes is None: raise ValueError('`gap` argument is required for non-standard alphabets')
    else:
        if not isinstance(gaps, (list, tuple)):
            raise TypeError('invalid type for gaps')
        if len(gaps) == 0:
            raise ValueError('at least one gap value is expected')
        try:
            gap_codes = list(map(alph.get_code, gaps))
        except ValueError:
            raise ValueError('invalid gap value for the input alphabet')
    return gap_codes

def ungap_all(obj, gaps=None):
    """
    Remove all gaps from an object.
    Generate a :class:`.Container` instance containing all sequences of
    the provided object excluding any gaps.

    :param obj: input object as an :class:`.Align` or a :class:`.Container`.

    :param gaps: the list of allelic value(s) representing gaps. The
        argument must be a :class:`list` or :class:`tuple` containing
        one gap allele value, or more than one if appropriate. All
        values must be valid alleles for the input alphabet. By
        default, use the ``-`` character for the DNA and protein
        alphabets, and all triplets containing at least one alignment
        gaps for the codon alphabet. There is no default for other
        alphabets.

    :return: A :class:`!Container` instance.
    """
    if not isinstance(obj, (_interface.Align, _interface.Container)): raise TypeError('expect an Align or a Container instance')
    gap_codes = _get_gaps(gaps, obj._alphabet)
    ls = obj.ls
    result = _interface.Container(alphabet=obj._alphabet)
    for i in range(obj.ns):
        result.add_sample(
            obj.get_name(i),
            [obj._alphabet.get_value(obj._obj.get_sample(i, j)) for j in range(ls) if obj._obj.get_sample(i, j) not in gap_codes],
            obj.get_sample(i).labels)
    return result

def ungap(align, freq, gaps=None):
    """
    Remove sites with too many gaps.
    Generate a new :class:`.Align` instance containing all sequences of
    the provided alignment but with only those sites for which the
    frequency of alignment gaps is less than or equal to *freq*.

    :param align: input alignment as an :class:`!Align`.

    :param freq: maximum gap frequency in a site (if there are more
        gaps, the site is not included in the returned :class:`.Align`
        instance). This value is a
        relative frequency (included in the [0, 1] range).

    :param gaps: the list of allelic value(s) representing gaps. The
        argument must be a :class:`list` or :class:`tuple` containing
        one gap allele value, or more than one if appropriate. All
        values must be valid alleles for the alignment alphabet. By
        default, use the ``-`` character for the DNA and protein
        alphabets, and all triplets containing at least one alignment
        gaps for the codon alphabet. There is no default for other
        alphabets.

    :return: A new :class:`!Align` instance.
    """

    # process arguments
    if not isinstance(align, _interface.Align): raise TypeError('expect an Align instance')
    gap_codes = _get_gaps(gaps, align._alphabet)

    # get statistics
    ls = align.ls
    if freq < 0.0 or freq > 1.0: raise ValueError('`freq` value is out of range')
    ns = align.ns
    if ns == 0: raise ValueError('not enough sequences in alignment')

    # collect retained positions
    good = []
    for i in range(ls):
        gaps = 0
        for j in range(ns):
            if align._obj.get_sample(j, i) in gap_codes: gaps += 1
        if gaps/ns <= freq:
            good.append(i)

    # return requested object
    return align.extract(good)
