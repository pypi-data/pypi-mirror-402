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

from .. import alphabets

class ReadingFrame(object):
    """
    Handle reading frame positions. The reading frame positions can be
    loaded as constructor argument or using the method
    :meth:`~.ReadingFrame.process`. By default, build an instance with
    no exons.

    .. _reading-frame-constructor-arguments:

    :param frame: the reading frame specification must be a sequence
        of ``(start, stop[, codon_start])`` pairs or triplets where
        *start* and *stop* give the limits of an exon, such that
        ``sequence[start:stop]`` returns the exon sequence, and
        *codon_start*, if specified, can be:
        
        * 1 if the first position of the exon is the first position
          of a codon (e.g. ``ATG ATG``),

        * 2 if the first position of the segment is the second
          position of a codon (e.g. ``TG ATG``),

        * 3 if the first position of the segment is the third
          position a of codon (e.g. ``G ATG``),

        * ``None`` if the reading frame is continuing the previous
          exon.

    :param keep_truncated: if ``True``, codons that are truncated
        (either because the reading frame is 5', internally, or 3'
        partial, or if the number of bases is not a multiple of
        three) are not skipped (missing positions of truncated
        codons are replaced by ``None``).

    If *codon_start* of the first segment is ``None``, 1 will be
    assumed. If *codon_start* of any non-first segment is not
    ``None``, the reading frame is supposed to be interupted. This
    means that if any codon was not completed at the end of the
    previous exon, it will assumed to be assumed incomplete, and the first
    codon of the current codon will be incomplete as well.
    """

    def __init__(self, frame=None, keep_truncated=False):
        if frame is None: frame = []
        self.process(frame, keep_truncated)

    def process(self, frame, keep_truncated=False):
        """
        Reset instance with a new reading frame. All previously loaded data are discarded.
        The arguments of this method are identical to the :ref:`constructor <reading-frame-constructor-arguments>`.
        """
        cur = -1
        self._starts = []
        self._stops = []
        self._codon_starts = []
        for exon in frame:
            if len(exon) == 2:
                start, stop = exon
                codon_start = None
            elif len(exon) == 3:
                start, stop, codon_start  = exon
                if codon_start not in set([1, 2, 3, None]): raise ValueError('invalid value for `codon_start`: {0}'.format(codon_start))
            if start < cur: raise ValueError('exon limits must in increasing order')
            if stop <= start: raise ValueError('exon limits must in increasing order')
            cur = stop
            self._starts.append(start)
            self._stops.append(stop)
            self._codon_starts.append(codon_start)

        self._num_exons = len(self._starts)
        if self._num_exons > 0:
            self._num_tot_bases = self._stops[-1] - self._starts[0]
            self._num_exon_bases = sum([stop-start for (start, stop) in zip(self._starts, self._stops)])
            if self._codon_starts[0] is None: self._codon_starts[0] = 1 # important
        else:
            self._num_tot_bases = 0
            self._num_exon_bases = 0

        self._codons = []
        self._bases = {} # keys are bases, values are [exon, codon] indexes pairs
        for idx, (start, stop, codon_start) in enumerate(zip(self._starts, self._stops, self._codon_starts)):
            if codon_start != None:
                # if codon_start is specified, complete the previous codon
                if len(self._codons):
                    if keep_truncated:
                        self._codons[-1] += [None] * (3 - len(self._codons[-1]))
                    else:
                        if len(self._codons[-1]) != 3: del self._codons[-1]

                # add non codon with shift if needed
                if keep_truncated:
                    if codon_start == 1: self._codons.append([])
                    elif codon_start == 2: self._codons.append([None])
                    elif codon_start == 3: self._codons.append([None, None])
                    else: raise ValueError('invalid value for codon start')
                else:
                    self._codons.append([])
                    if codon_start == 1: pass
                    elif codon_start == 2:
                        self._bases[start] = [idx, None] # avoid side effect of deleting bases due to shift
                        self._bases[start+1] = [idx, None]
                        start += 2
                    elif codon_start == 3:
                        self._bases[start] = [idx, None]
                        start += 1
                    else: raise ValueError('invalid value for codon start')

            # loop over bases, adding codons when the current is filled
            # it is guaranteed that there will always be one codon (because 1st exon is in frame 1)
            for i in range(start, stop):
                if len(self._codons[-1]) == 3: self._codons.append([])
                self._codons[-1].append(i)
                self._bases[i] = [idx, None]

        # complete last codon if needed
        if len(self._codons) > 0:
            if keep_truncated:
                self._codons[-1] += [None] * (3 - len(self._codons[-1]))
            else:
                if len(self._codons[-1]) != 3: del self._codons[-1]

        # final processing
        self._codons = tuple(map(tuple, self._codons))
        for idx, codon in enumerate(self._codons):
            for i in codon:
                if i is not None:
                    if i not in self._bases or self._bases[i][1] is not None:
                        raise RuntimeError('error in ReadingFrame code')
                    self._bases[i][1] = idx
        if self._num_exons > 0:
            self._needed_bases = self._stops[-1]
        else: self._needed_bases = 0

    @property
    def num_needed_bases(self):
        """
        Number of bases needed to apply this reading
        frame. Minimum size of a sequence to be consistent with this
        reading frame. In practice, the value equals to the end of the last exon
        or zero if there are no exons. If the reading frame is used with
        a shorter sequence, it can lead to errors.
        """
        return self._needed_bases

    @property
    def num_tot_bases(self):
        """
        Number of bases of the reading frame. All introns and exons are
        included, starting from the start of the first exon
        up to end of the last one.
        """
        return self._num_tot_bases

    @property
    def num_exon_bases(self):
        """ Number of bases in exons. """
        return self._num_exon_bases

    @property
    def num_exons(self):
        """ Number of exons. """
        return self._num_exons

    @property
    def num_codons(self):
        """ Number of codons. Truncated codons are included. """
        return len(self._codons)

    def exon_index(self, base):
        """
        Find the exon in which a given base falls.

        :param base: any base index.
        :return: The index of the corresponding exon, or ``None`` if the
            base does not fall in any exon.
        """
        if base in self._bases: return self._bases[base][0]
        else: return None

    def codon_index(self, base):
        """
        Find the codon in which a given base falls.

        :param base: any base index.
        :return: The index of the corresponding codon, or ``None`` if
            the base does not fall in any codon.
        """
        if base in self._bases: return self._bases[base][1]
        else: return None

    def codon_position(self, base):
        """
        Tell the position of a base within the
        codon in which it falls.

        :param base: any base index.
        :return: The index of the base in the codon (0, 1 or 3), or
            ``None`` if the base does not fall in any codon.
        """
        if base in self._bases and self._bases[base][1] is not None:
            return self._codons[self._bases[base][1]].index(base)
        else: return None

    def codon_bases(self, codon):
        """
        Give the position of the three bases of a given codon. One or
        two positions (but never the middle one alone) will be ``None``
        if the codon is truncated (beginning/end of an exon without
        coverage of the previous/next one). If the codon index is out of
        range, return ``None``.
        
        :param codon: any codon index.
        :return: A tuple with the three base positions (containing potentially
            one or two ``None``) or
            ``None`` if the codon index is out of range.
        """
        try: return self._codons[codon]
        except IndexError: return None

    def iter_exon_bounds(self):
        """
        Iterate over exons.
        This iterator returns ``(start, stop)`` tuples of the positions
        of the limits of each exon.
        """
        for start, stop in zip(self._starts, self._stops): yield start, stop

    def iter_codons(self):
        """
        Iterate over codons.
        This iterator returns ``(first, second, third)`` tuples of the
        positions of the three bases of each codon. Positions might be
        ``None`` if *keep_truncated* has been set to ``True``.
        """
        for codon in self._codons: yield codon
