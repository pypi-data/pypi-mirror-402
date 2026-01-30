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

import re, itertools
from .. import eggwrapper as _eggwrapper
from .. import _interface, alphabets
from . import _reading_frame, _seq_manip

# preload all genetic codes
_codes = {}
for i in range(_eggwrapper.GeneticCode.num_codes()):
    code = _eggwrapper.GeneticCode(i)
    key = code.get_code()
    _codes[key] = code

class Translator(object):
    """
    Class to translate nucleotide sequences to proteins.

    :param code: genetic code identifier (see :ref:`here <genetic-codes>`).
        Required to be an integer among the valid values. The default
        value is the standard genetic code.
    """

    def _help_frame_processor(self, ls, frame):
        # take the frame argument and ls and generate self._frame and self._naa
        if frame is None:
            if ls == 0: self._frame = _reading_frame.ReadingFrame([])
            elif ls % 3 != 0: raise ValueError('alignment length must be a multiple of 3')
            else: self._frame = _reading_frame.ReadingFrame([(0, ls)])
        else:
            if frame.num_needed_bases > ls:
                raise ValueError('reading frame is extending past the end of the sequence')
            self._frame = frame
        self._naa = self._frame.num_codons

    def __init__(self, code=1):
        if code not in _codes: raise ValueError('unknown genetic code: {0}'.format(code))
        self._code = _codes[code]

    def translate_codon(self, codon):
        """
        Translate a single codon. Translation is based on the 
        genetic code defined at construction time. Alternative start 
        codons are not supported.

        :param codon: codon as a three-character string
        :return: The one-letter amino acid code if the codon can be
            translated, or ``-`` if the codon is ``---``, or ``X`` in all
            other cases
            (including all cases with invalid nucleotides).
        """
        return alphabets.protein.get_value(
                    self._code.translate(
                        alphabets.codons.get_code(codon)))

    def translate_sequence(self, sequence, allow_alt=False):
        """
        Translate a sequence.

        :param sequence: a :class:`str`, :class:`~.SequenceView` or
            compatible instance containing codon sequences. Only
            upper-case strings.

        :param frame: a :class:`~.ReadingFrame` instance providing the
            exon positions in the correct frame. By default, a
            non-segmented frame covering all sequences is assumed (in
            case the provided alignment is the coding region and length
            must be a multiple of 3).

        :param allow_alt: a boolean telling whether alternative start
            (initiation) codons should be considered. If ``False``,
            codons are translated as a methionine (M) if, and only if,
            there are among the alternative start codons for the considered
            genetic code and they appear at the first position for the
            sequence.

        :return: A new :class:`str` instance containing translated
            (protein) sequences.
        """
        if isinstance(sequence, str):
            if len(sequence) % 3 != 0: raise ValueError('number of bases must be a multiple of 3')
            sequence = re.findall('...', sequence.upper())
        if allow_alt:
            for i, codon in enumerate(sequence):
                if codon == '---': continue
                if self._code.start(alphabets.codons.get_code(codon)):
                    start = i
                    break
                if alphabets.codons.get_code(codon) < 0:
                    start = None
                    break
            else: start = None
        dest = [self._code.translate(alphabets.codons.get_code(codon)) for codon in sequence]
        if allow_alt and start is not None and dest[start] != 10: dest[start] = 10
        return ''.join(map(alphabets.protein.get_value, dest))

    def translate_align(self, src, allow_alt=False, in_place=False):
        """
        Translate an :class:`.Align` instance.

        :param src: an :class:`!Align` containing codon sequences and
            using the :py:obj:`.alphabets.codons` alphabet.

        :param allow_alt: a boolean telling whether alternative start
            (initiation) codons should be considered. If ``True``,
            codons are translated as a methionine (M) if
            they are among the alternative start codons for the considered
            genetic code and they appear at the first position for the
            considered sequence (excluding all triplets of gap symbols
            appearing at the 5' end of the sequence).

        :param in_place: place translated sequences into the original
            :class:`!Align` instance (this discards original data and
            replaces the original alphabet by the protein alphabet). By
            default, returns a new instance.

        :return: By default, an original :class:`!Align` instance
            containing translated (protein) sequences. If *in_place* was
            ``True``, return ``None``.
        """

        # check input
        if not isinstance(src, _interface.Align): raise TypeError('expect an Align instance')
        if src._alphabet._obj.get_type() != 'codons': raise ValueError('alphabet must be codons')
        ns = src.ns
        ls = src.ls

        # create destination
        if not in_place:
            dest = _interface.Align(nsam=ns, nsit=ls, alphabet=alphabets.protein)
            for i in range(ns):
                dest.set_name(i, src.get_name(i))
                dest._obj.set_nlabels(i, src._obj.get_nlabels(i))
                for j in range(src._obj.get_nlabels(i)):
                    dest.set_label(i, j, src.get_label(i, j))
        else:
            dest = src
            dest._alphabet = alphabets.protein

        # iterate over sequences
        for i in range(ns):
            if allow_alt:
                for j in range(ls):
                    codon = src._obj.get_sample(i, j)
                    if codon == -1165: continue
                    if self._code.start(codon):
                        start = j
                        break
                    if codon < 0:
                        start = None
                        break
                else: start = None
            for j in range(ls):
                dest._obj.set_sample(i, j, self._code.translate(src._obj.get_sample(i, j)))
            if allow_alt and start is not None and dest._obj.get_sample(i, start) != 10: dest._obj.set_sample(i, start, 10)

        # return
        if not in_place: return dest

    def translate_container(self, src, allow_alt=False, in_place=False):
        """
        Translate a :class:`.Container` instance.

        :param align: a :class:`!Container` containing codons sequences.

        :param allow_alt: a boolean telling whether alternative start
            (initiation) codons should be considered. If ``False``,
            codons are translated as a methionine (M) if, and only if,
            they are among the alternative start codons for the considered
            genetic code and they appear at the first position for the
            considered sequence.

        :param in_place: place translated sequences into the original
            :class:`!Container` instance (this discards original data).
            By default, return a new instance.

        :return: By default, a new :class:`!Container` instance
            containing translated (protein) sequences. If *in_place* was
            ``True``, return ``None``.
        """

        # check input
        if not isinstance(src, _interface.Container): raise TypeError('expect a Container instance')
        if src._alphabet._obj.get_type() != 'codons': raise ValueError('alphabet must be codons')
        ns = src.ns

        # create destination
        if not in_place:
            dest = _interface.Container(alphabet=alphabets.protein)
            dest._obj.set_nsam(ns)
            dest._ns = ns
            for i in range(ns):
                dest.set_name(i, src.get_name(i))
                dest._obj.set_nlabels(i, src._obj.get_nlabels(i))
                for j in range(src._obj.get_nlabels(i)):
                    dest.set_label(i, j, src.get_label(i, j))
        else:
            dest = src
            dest._alphabet = alphabets.protein

        # iterate over sequences
        for i in range(ns):
            ls = src._obj.get_nsit_sample(i)
            if not in_place: dest._obj.set_nsit_sample(i, ls)
            if allow_alt:
                for j in range(ls):
                    codon = src._obj.get_sample(i, j)
                    if codon == -1165: continue
                    if self._code.start(codon):
                        start = j
                        break
                    if codon < 0:
                        start = None
                        break
                    else: start = None
            for j in range(ls):
                dest._obj.set_sample(i, j, self._code.translate(src._obj.get_sample(i, j)))
            if allow_alt and start is not None and dest._obj.get_sample(i, start) != 10: dest._obj.set_sample(i, start, 10)

        # return
        if not in_place: return dest

def translate(seq, code=1, allow_alt=False, in_place=False):
    """
    Translates coding nucleotide sequences to proteins. See the class
    :class:`.tools.Translator` for more details. This is a convenience method
    allowing to translate nucleotide sequences in a single call. For
    repetitive calls, direct use of :class:`!Translator` can be more
    efficient.

    :param seq: input codon sequences. Accepted types are
        :class:`.Align`, :class:`.Container`, :class:`.SequenceView`
        or :class:`str` (or also types compatible with :class:`str`).
        If the input object is an :class:`!Align` or a :class:`!Container`,
        the alphabet must be :py:obj:`.alphabets.codons`.

    :param code: genetic code identifier (see below).
        Required to be an integer among the valid values. The default
        value is the standard genetic code.

    :param allow_alt: a boolean telling whether alternative start
        (initiation) codons should be considered. If ``True``,
        codons are translated as a methionine (M) if, and only if,
        there are among the alternative start codons for the considered
        genetic code and they appear at the first position for the
        sequence. If *seq* is an :class:`!Align`, leading gaps are
        ignored as long as they appear as multiples of 3 (fully missing codons).

    :param in_place: place translated sequences in the provided
        :class:`!Align` or :class:`!Container` instance, overwriting
        initial data. Not allowed if *seq* is not of one of these two
        types. Replace the original alphabet by :py:obj:`.alphabets.protein`.
        By default, return a new instance.

    :return: Protein sequences as an :class:`!Align` or a
        :class:`!Container` if either of these types have been provided
        as *seq*, or as a string otherwise. If *in_place* has been
        specified, return ``None``.

    .. _genetic-codes:

    All genetic codes defined by the National Center for Biotechnology
    Information are supported and can be accessed using codes corresponding
    to the GenBank ``/trans_table`` qualifier. The codes are integers.

    .. include:: list_genetic_codes.txt

    Reference: National Center for Biotechnology Information
    [`<http://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi>`_]
   """

    T = Translator(code=code)
    if isinstance(seq, _interface.Align):
        return T.translate_align(seq, allow_alt=allow_alt, in_place=in_place)
    elif isinstance(seq, _interface.Container):
        return T.translate_container(seq, allow_alt=allow_alt, in_place=in_place)
    else:
        if in_place == True: raise ValueError('cannot translate sequence in place')
        return T.translate_sequence(seq, allow_alt=allow_alt)

class orf_iter:
    """
    Iterate over open reading frames.
    Return an iterator over non-segmented open reading frames (ORFs)
    found in a provided codon sequence in any of the six possible frames.

    :param sequence: a string or a :class:`.SequenceView` representing a codon sequence.

    :param code: genetic code identifier (see :ref:`here <genetic-codes>`).
        Required to be an integer among the valid values. The default
        value is the standard genetic code.

    :param min_length: minimum length of returned ORFs. This value must
        be at least 1. It is understood as the length of the encoded
        peptide (since ORFs are returned as nucleotide sequences, they
        will have a length of least three times this value).

    :param forward_only: consider only the three forward frames (do not
        consider the reverse strand).

    :param force_start: if ``True``, all returned ORFs are required to
        start with a start codon. Otherwise, all non-stop codons are
        included in ORFs. Note that alternative start codons (``CTG``
        and ``TTG`` for the standard genetic code) are also supported.

    :param allow_alt: allow alternative start codons (only considered
        if *force_start* is set).

    :param force_stop: require that ORFs
        end with a stop codon (this only excludes 3'-partial ORFs, that
        is ORFs that end with the end of the provided sequennce).

    :return: An iterator over all detected ORFs. Each ORF is represented
        by a ``(start, stop, length, frame)`` tuple where ``start`` is the
        start position of the ORF and ``stop`` the stop position (such as
        ``sequence[start:stop]`` returns the ORF sequence or its reverse
        complement [note that the stop codon, if present, is included]),
        ``length`` is the ORF length (number of amino acids, excluding any
        stop codon) and ``frame`` is the reading frame on which it was found: +1, +2,
        +3 are the frames on the forward strand (starting respectively at
        the first, second, and third base), and -1, -2, -3 are the frames
        on the reverse strand (starting respectively at the last, last
        but one, and last but two bases).
    """

    def __init__(self, sequence, code=1, min_length=1,
                 forward_only=False, force_start=True, allow_alt=False,
                 force_stop=True):

        # get/check arguments
        if code not in _codes: raise ValueError('unknown genetic code: {0}'.format(code))
        code = _codes[code]
        if min_length < 1: raise ValueError('value for `min_length` is too small')
        self._ls = len(sequence)
        self._sequence = sequence
        self._code = code
        self._min_length = min_length
        self._forward_only = forward_only
        self._force_start = force_start
        self._force_stop = force_stop
        self._frames = [None] * 6

        # make a list of codon status (1:start/2:stop/3:valid/4:missing)
        self._codon_table = {}
        aa_stop = alphabets.protein.get_code('*')
        valid, missing = alphabets.codons.get_alleles()
        for cod in valid:
            c = alphabets.codons.get_code(cod)
            if cod == 'ATG' or (allow_alt and code.start(c)):
                self._codon_table[cod] = 1
            elif code.translate(c) == aa_stop:
                self._codon_table[cod] = 2
            else:
                self._codon_table[cod] = 3
        for cod in missing:
            self._codon_table[cod] = 4

    def __iter__(self):
        self._pos = 0
        self._iter_f = itertools.cycle([1, 2, 3])
        self._iter_r = itertools.cycle([-1, -3, -2])
        if self._ls % 3 == 1:
            next(self._iter_r)
            next(self._iter_r)
        elif self._ls % 3 == 2:
            next(self._iter_r)
        self._cache = None
        return self

    def __next__(self):

        # return cache frame if any
        if self._cache:
            r = self._cache
            self._cache = None
            return r

        # proceed until an ORF (or the end) is found
        while True:

            # if reached end of sequence, process hanging ORFs and finish
            if self._pos > self._ls-3:
                return self.finishing() # ultimately raises StopIteration

            orf_f = None
            orf_r = None

            # process forward frame
            F = next(self._iter_f)
            cod = self._codon_table[self._sequence[self._pos:self._pos + 3]]
            if self._frames[F-1] is None:
                if (self._force_start == True and cod == 1) or (self._force_start == False and cod in [1, 3]):
                    self._frames[F-1] = [self._pos, None, None, F]
            else:
                if cod == 2:
                    self._frames[F-1][1] = self._pos + 3
                    self._frames[F-1][2] = (self._pos + 3 - self._frames[F-1][0]) // 3 - 1 # -1 because of stop
                    if self._frames[F-1][2] >= self._min_length: orf_f = tuple(self._frames[F-1])
                    self._frames[F-1] = None

            # process reverse frame
            if not self._forward_only:
                R = next(self._iter_r)
                cod = self._codon_table[_seq_manip.rc(self._sequence[self._pos:self._pos + 3])]
                if self._frames[2-R] is None:
                    if cod == 2:            # start, stop, len, frame, final_stop, last_M, has_non_stop
                        self._frames[2-R] = [self._pos, None, None, R, 1, None, False]
                    elif cod != 4 and not self._force_stop:
                        self._frames[2-R] = [self._pos, None, None, R, 0, self._pos + 3 if cod==1 else None, True]
                else:
                    if self._force_start == True and cod == 1:
                        self._frames[2-R][5] = self._pos + 3
                        self._frames[2-R][6] |= True
                    elif cod == 2:
                        if self._force_start:
                            if self._frames[2-R][5] is not None: # there is an M
                                self._frames[2-R][1] = self._frames[2-R][5]
                                self._frames[2-R][2] = (self._frames[2-R][5] - self._frames[2-R][0]) // 3 - self._frames[2-R][4]
                                if self._frames[2-R][2] >= self._min_length: orf_r = tuple(self._frames[2-R][:4])
                        elif self._frames[2-R][6]:
                            self._frames[2-R][1] = self._pos
                            self._frames[2-R][2] = (self._pos - self._frames[2-R][0]) // 3  - self._frames[2-R][4]
                            if self._frames[2-R][2] >= self._min_length: orf_r = tuple(self._frames[2-R][:4])
                        self._frames[2-R] = [self._pos, None, None, R, 1, None, False]
                    elif cod != 4:
                        self._frames[2-R][6] |= True

            # return frame (return orf_f and cache orf_r if both)
            self._pos += 1
            if orf_f and orf_r:
                self._cache = orf_r
                return orf_f
            if orf_f:
                return orf_f
            if orf_r:
                return orf_r

    def finishing(self):
        # if we reached the end, return any remaining still-running ORF (if allowed by options)

        # forward frames
        if not self._force_stop:
            for i in range(3):
                if self._frames[i] is not None:
                    self._frames[i][1] = (self._ls - i) // 3 * 3 + i
                    self._frames[i][2] = (self._frames[i][1] - self._frames[i][0]) // 3
                    r = self._frames[i]
                    self._frames[i] = None
                    if r[2] >= self._min_length: return tuple(r)

        # reverse frames
        for i in range(3):
            if self._frames[3+i] is not None:
                if self._force_start:
                    if self._frames[3+i][5] is None:
                        self._frames[3+i] = None
                        continue
                    self._frames[3+i][1] = self._frames[3+i][5]
                    self._frames[3+i][2] = (self._frames[3+i][5] - self._frames[3+i][0]) // 3 - self._frames[3+i][4]
                elif self._frames[3+i][6]:
                    self._frames[3+i][1] = self._ls - i
                    self._frames[3+i][2] = (self._frames[3+i][1] - self._frames[3+i][0]) // 3 - self._frames[3+i][4]
                if self._frames[3+i][6]:
                    r = self._frames[3+i][:4]
                    self._frames[3+i] = None
                    if r[2] >= self._min_length: return tuple(r)
                else:
                    self._frames[3+i] = None

        raise StopIteration

def longest_orf(*args, **kwargs):
    """
    longest_orf(sequence, code=1, min_length=1,
                 forward_only=False, force_start=True, allow_alt=False,
                 force_stop=True)

    Detect the longest open reading frame. Arguments are identical to :func:`.orf_iter`.
    A :exc:`ValueError` is raised if two or more open
    reading frames have the largest length.

    :return: A ``(start, stop, length, frame)`` tuple (see the return
        value of :func:`.orf_iter` for details), or ``None`` if no open
        reading frame fits the requirements.
    """
    max_length = 0
    candidate = None
    for start, stop, length, frame in orf_iter(*args, **kwargs):
        if length == max_length:
            candidate = None
            num += 1
        elif length > max_length:
            max_length = length
            candidate = start, stop, length, frame
            num = 1

    if max_length == 0: return None
    if num > 1: raise ValueError('several equally long ORFs found')
    return candidate

def backalign(nucl, aln, code=1, ignore_names=False, ignore_mismatches=False, fix_stop=False, allow_alt=True):
    """
    Align coding sequence based on the protein alignment.

    :param nucl: a :class:`.Container` or :class:`.Align` instance
        containing coding sequences that should be aligned. There should
        not be any alignment gap in the sequences. The alphabet must be
        :class:`.alphabets.codons`.

    :param aln: an :class:`!Align` instance containing an alignment of
        the protein sequences encoded by the coding sequences provided
        as *nucl*. Group labels of *aln*
        are not taken into account. The alphabet must be :class:`.alphabets.protein`.

    :param code: genetic code identifier (see :ref:`here <genetic-codes>`).
        Required to be an integer among the valid values. The default
        value is the standard genetic code.

    :param ignore_names: if ``True``, ignore names for matching
        sequences in the protein alignment to coding sequences.
        Sequences will be matched using their rank and the names in the
        returned alignment will be taken from *nucl*.

    :param ignore_mismatches: if ``True``, do not generate any exception
        if a predicted protein does not match the provided protein
        sequence (if the lengths differ, an exception is always raised).

    :param fix_stop: if ``True``, support a single trailing stop codon
        in coding sequences not represented by a ``*`` in the provided
        protein alignment (if the final stop codons have been
        stripped during alignment). If found, this stop codon will be
        flushed as left as possible (immediately after the last non-gap
        character) in the returned coding alignment.

    :return: An :class:`.Align` instance containing aligned coding codon
        sequences.

    If a mismatch is detected between a protein from *aln* and the
    corresponding prediction from *nucl*, an instance of
    :exc:`.tools.BackalignError` (a subclass of :exc:`ValueError`)
    is raised. Its attribute :py:obj:`~.tools.BackalignError.alignment` can be
    used to help identify the reason of the error. Mismatches (but not
    differences of length) can be ignored with the option
    *ignore_mismatches*.
    """
    # checking
    if not isinstance(aln, _interface.Align): raise TypeError('expect an Align instance')
    if aln._alphabet._obj.get_name() != 'protein': raise ValueError('alignment alphabet must be protein')
    if not isinstance(nucl, _interface.Container): raise TypeError('argument must be a Container instance')
    if nucl._alphabet._obj.get_type() != 'codons': raise ValueError('alignment alphabet must be codons')

    # get code
    translator = Translator(code=code)

    # initialize the return object
    ns = aln.ns
    ls = aln.ls
    result = _eggwrapper.DataHolder(True)
    result.set_nsam(ns)
    result.set_nsit_all(ls + int(fix_stop))

    # set a trailing gape at the end of all sequences to allow 1 or more additional stop codons
    if fix_stop:
        for i in range(ns): result.set_sample(i, ls, -1165)
        last_used = False # set to True if at least one sequence uses the last three bases

    # get mapping of indexes
    nucl = nucl._obj
    aln = aln._obj
    if nucl.get_nsam() != ns: raise ValueError('numbers of sequences don\'t match')
    names = list(map(nucl.get_name, range(ns)))
    if not ignore_names:
        if len(set(names)) < ns: raise ValueError('duplicate name found')
        aln_names = list(map(aln.get_name, range(ns)))
        ranks = []
        for name in names:
            try: ranks.append(aln_names.index(name))
            except ValueError: 'sequence name not found in protein alignment: {0}'.format(name)
    else:
        ranks = list(range(ns))

    # set names and group labels
    for idx_cds in range(ns):
        result.set_name(idx_cds, names[idx_cds])
        result.set_nlabels(idx_cds, nucl.get_nlabels(idx_cds))
        for k in range(nucl.get_nlabels(idx_cds)):
            result.set_label(idx_cds, k, nucl.get_label(idx_cds, k))

    # main loop
    last_used = False
    for idx_cds, idx_aln in enumerate(ranks):
        ls_nucl = nucl.get_nsit_sample(idx_cds)
        if ls_nucl < 1: raise ValueError('empty nucleotide sequence')

        # process all aligned aa positions
        c = 0
        for idx in range(ls):
            aa = aln.get_sample(idx_aln, idx)

            # process gaps
            if aa == -1: result.set_sample(idx_cds, idx, -1165)

            # non-gap
            else:
                codon = nucl.get_sample(idx_cds, c)
                c += 1
                if (not ignore_mismatches and translator._code.translate(codon) != aa): # check mismatch
                    raise BackalignError(names[idx_cds], nucl.get_sample, aln.get_sample, idx_cds, idx_aln, ls, ls_nucl, translator)
                result.set_sample(idx_cds, idx, codon) # set codon

        # if there is an additional codon at the end
        if c != ls_nucl:

            # if requested, check that it is a stop codon
            if fix_stop:
                codon = nucl.get_sample(idx_cds, c)
                c += 1

                # fix stop codon (only if all bases have been read)
                if c == ls_nucl and translator._code.translate(codon) == 20:
                    i = ls # there is necessarily room there, filled by gaps
                    while i > 0 and result.get_sample(idx_cds, i-1) == -1165: i -= 1
                    result.set_sample(idx_cds, i, codon)
                    if i == ls: last_used = True
                else: raise BackalignError(names[idx_cds], nucl.get_sample, aln.get_sample, idx_cds, idx_aln, ls, ls_nucl, translator)
            else: raise BackalignError(names[idx_cds], nucl.get_sample, aln.get_sample, idx_cds, idx_aln, ls, ls_nucl, translator)

    # if the last codon position has not been used at least once by fix_stop, remove them
    if fix_stop and not last_used:
        result.set_nsit_all(ls) # decrease by three

    # that's all, folks!
    return _interface.Align._create_from_data_holder(result, alphabets.codons)

class BackalignError(ValueError):
    """
    Exception used to report errors
    occurring during the use of :func:`.tools.backalign` because of mismatches
    between the provided alignment and predicted proteins.
    """

    def __init__(self, name, fnuc, faln, i_nuc, i_aln, ls_aln, ls_nuc, translator):
        self._name = name
        message = 'mismatch between provided and predicted proteins for `{0}`'.format(name)
        prov = ''.join(map(alphabets.protein.get_value, [faln(i_aln, i) for i in range(ls_aln)])).replace('-', '')
        pred = ''.join(map(alphabets.codons.get_value, [fnuc(i_nuc, i) for i in range(ls_nuc)])).replace('-', '')
        if len(pred) % 3 != 0: message = 'length of nucleotide sequence not a multiple of 3 for {0}'.format(name)
        pred = ''.join([translator.translate_codon(''.join(codon)) for codon in zip(pred[::3], pred[1::3], pred[2::3])])

        n = max([len(prov), len(pred)])

        mid = []
        for i in range(n):
            if i >= len(prov):
                prov += '-'
                mid.append('~')
            elif i >= len(pred):
                pred += '-'
                mid.append('~')
            elif prov[i] != pred[i]:
                mid.append('#')
            else:
                mid.append('|')
        mid = ''.join(mid)

        c = 0
        self._alignment = []
        while True:
            A = prov[c:c+60]
            A = ' '.join([A[i*10:i*10+10] for i in range(6)])
            B = mid[c:c+60]
            B = ' '.join([B[i*10:i*10+10] for i in range(6)])
            C = pred[c:c+60]
            C = ' '.join([C[i*10:i*10+10] for i in range(6)])
            self._alignment.append('[provided]  {0}'.format(A) + '[{0}]\n'.format(c+60).rjust(7))
            self._alignment.append('            {0}\n'.format(B))
            self._alignment.append('[predicted] {0}'.format(C) + '[{0}]\n'.format(c+60).rjust(7))
            c += 40
            if c < n: self._alignment.append('\n')
            else: break

        self._alignment = ''.join(self._alignment)
        ValueError.__init__(self, message)

    @property
    def name(self):
        """
        Name of sequence for which the error occurred.
        """
        return self._name

    @property
    def alignment(self):
        """
        Comparaison of provided and predicted proteins.
        This string shows the two proteins with a middle line composed
        of the following symbols:

        * ``|``: match.
        * ``#``: mismatch.
        * ``~``: one protein shorter.
        """
        return self._alignment

def trailing_stops(align, action=0, code=1, replacement='???'):
    """
    Process stop codons at the end of the sequences. This function
    detects and (optionally) fix trailing stop codons.
    The algorithm consists in locating the last non-gap codon of each
    sequence. If the last codon is partially gapped (which can happen
    if coding sequences are aligned using a DNA-based algorithm), it
    will not be detected and ignored.

    :param align: an :class:`.Align` containing aligned coding
        sequences. The alphabet must be :py:obj:`.alphabets.codons`.

    :param action: an integer specifying what should be done if a stop
        codon is found at the end of a given sequence. Possible actions
        are listed in the following table:

        +------+---------------------------------------------------+
        | Code | Action                                            +
        +======+===================================================+
        | 0    | Nothing (just count them).                        +
        +------+---------------------------------------------------+
        | 1    | Replace them by a gap, and delete the last        +
        |      | position if it is made by gaps only.              +
        +------+---------------------------------------------------+
        | 2    | Replace them by the value given as *replacement*. +
        +------+---------------------------------------------------+

        Note that using ``action=1`` is not stricly equivalent to using
        ``action=2, replacement='---'`` because the former deletes the
        last three positions of the alignment if needed while the latter
        does not.

    :param code: genetic code identifier (see :ref:`here <genetic-codes>`).
        Required to be an integer among the valid values. The default
        value is the standard genetic code.

    :param replacement: if *action* is set to 2, provide the codon
        that should be used to replace stop codons.

    :return: The number of sequences that had a trailing stop codons
        among the considered sequences.
    """

    # argument check
    if not isinstance(align, _interface.Align): raise TypeError('expect an Align instance')
    if align._alphabet.type != 'codons': raise ValueError('alignment alphabet must be codons')
    if code not in _codes: raise ValueError('unknown genetic code: {0}'.format(code))
    code = _codes[code]
    ns = align.ns
    ls = align.ls
    try: replacement = alphabets.codons.get_code(replacement)
    except ValueError: raise ValueError('invalid codon: {0}'.format(replacement))
    cnt = 0
    num_gapped = 0

    for i in range(ns):
        cur = ls - 1
        for cur in range(ls-1, -1, -1):
            if align._obj.get_sample(i, cur) != -1165:
                if code.translate(align._obj.get_sample(i, cur)) == 20:
                    cnt += 1
                    if action == 1:
                        align._obj.set_sample(i, cur, -1165)
                        num_gapped += 1
                    elif action == 2:
                        align._obj.set_sample(i, cur, replacement)
                break

    # remove final 3 gaps (only if ALL samples where replaced by gaps, in particular only if include_outgroup was true)
    if action == 1 and num_gapped == ns:
        align._obj.set_nsit_all(ls-3)

    return cnt

def iter_stops(src, code=1):
    """
    Iterate over stop codons.
    Return an iterator providing the coordinates of all stop codons
    over all sequences. Each iteration returns a
    ``(sample, position)`` where ``sample`` is the sample index and
    ``position`` is the index of the stop codon.

    :param src: an :class:`.Align` or :class:`.Container` containing
        coding sequences. The alphabet must be :py:obj:`.alphabets.codons`.

    :param code: genetic code identifier (see :ref:`here <genetic-codes>`).
        Required to be an integer among the valid values. The default
        value is the standard genetic code.

    :return: An iterator over the ``(sample, position)`` tuples
        corresponding to each stop codon found in the alignment (see
        above).
    """

    # argument check
    if not isinstance(src, (_interface.Align, _interface.Container)): raise TypeError('expect an Align or Container instance')
    if src._alphabet.type != 'codons': raise ValueError('alignment alphabet must be codons')
    ns = src.ns
    if code not in _codes: raise ValueError('unknown genetic code: {0}'.format(code))
    code = _codes[code]
    if isinstance(src, _interface.Align): ls = src.ls

    for i in range(ns):
        if isinstance(src, _interface.Container): ls = src.ls(i)
        for j in range(ls):
            if code.translate(src._obj.get_sample(i, j)) == 20:
                yield (i, j)

def has_stop(src, code=1):
    """
    Test if there is at least one stop codon.
    Return ``True`` if the sequences contain at least one codon stop
    at any position in any sequence, and ``False`` otherwise.

    :param src: an :class:`.Align` or :class:`.Container` containing
        aligned coding sequences.

    :param code: genetic code identifier (see :ref:`here <genetic-codes>`).
        Required to be an integer among the valid values. The default
        value is the standard genetic code.

    :return: A boolean.
    """
    for stop in iter_stops(src, code=code): break
    else: return False
    return True
