"""
    Copyright 2025 Mathieu Siol, Stéphane De Mita

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

from .. import config
from ._vcfparser import VCF, index_vcf

class VcfSlider:
    r"""
    Run a sliding window on a VCF file.

    If a chromosome and a start position are specified, the sliding
    windows starts at this position; if only a chromosome is specified,
    the sliding windows starts at the beginning of this chromosome. If a
    chromosome is specified, the sliding window stops at the specified
    stop position or at the end of the chrososome. If no chromosome is
    specified, the sliding windows starts at the current position and
    stops at the end of the file.

    The sliding windows stops as soon as the last variant is processed.
    As a result, the last window is never empty unless there is a single
    window overall and, if *as_variants* is set, the successive windows
    should not overlap. In line with this behaviour, empty windows are
    never returned with *as_variants* although the last window can
    contain less than *size* sites.

    :param vcf: open :class:`~.io.VCF` instance.
    :param size: window size (see note below).
    :param step: window step (see note below).
    :param as_variants: window size and step are expressed as number of
        variants instead of genomic coordinates.
    :param chrom: chromosome where to perform sliding window (by default,
        start at current position). This option requires that VCF to be
        indexed.
    :param start: start position (only if *chrom* is specified; by
        default, chromosome start if *chrom* is specified or, otherwise,
        current positon).
    :param stop: stop position (only if *chrom* is specified; by
        default, chromosome end). Not included in windows.
    :param max_missing: maximum number of missing data to consider a
        variants.
    :param mode: 0: include only SNP variants (variants with at least
        two alleles, all corresponding to a single nucleotide, although
        those alleles are not required to be called in genotypes); 1:
        include SNP variants and invariant positions; 2: include all
        variants from the VCF.

    .. note::
        If *as_variants* is ``True``, both *size* and *step* are
        expressed in number of variants. Otherwise, they are expressed
        in bp with respect to the reference genome.

    VCF sliding window objects are iterable and indexable with respect
    to the sites stored within the current window. Empty and
    uninitialized windows have length 0. Sites correspond to variants in
    the VCF file and are represented by :class:`.Site` instances.

    +----------------------+------------------------------------------+
    | Operation            | Action                                   |
    +======================+==========================================+
    | ``len(sld)``         | number of sites in the current window    |
    +----------------------+------------------------------------------+
    | site = ``sld[i]``    | get ``i``\ th site of current window     |
    +----------------------+------------------------------------------+
    | ``for site in sld:`` | iterate over sites of the current window |
    +----------------------+------------------------------------------+

    The sliding window is operated by the :meth:`.move`
    method which returns a boolean to indicate the end.

    .. versionadded:: 3.4

    .. versionchanged:: 3.6
        Add *skip_empty* argument.
    """

    def __init__(self, vcf, size, step, as_variants=False, chrom=None, start=None, stop=None, max_missing=0, mode=0, skip_empty=False):
        if not isinstance(vcf, VCF):
            raise TypeError('expect a VCF instance')
        if not isinstance(size, int) or size < 1:
            raise ValueError('size must be a strictly positive integer')
        if not isinstance(step, int) or step < 1:
            raise ValueError('step must be a strictly positive integer')
        if start is not None and (not isinstance(start, int) or start < 0):
            raise ValueError('start must be None or a positive integer')
        if stop is not None and (not isinstance(stop, int) or stop < 0):
            raise ValueError('stop must be None or a positive integer')
        if mode not in {0, 1, 2}:
            raise ValueError('invalid value for `mode`')

        self._sites = []
        self._vcf   = vcf
        self._size  = size
        self._step  = step
        self._as_variants = as_variants
        self._chrom = chrom
        self._start = start
        self._stop = stop
        self._max_missing = max_missing
        self._mode = mode
        self._skip_empty = skip_empty
        if self._chrom is not None:
            if self._start is None:
                self._flag = not self._vcf.goto(self._chrom) # FALSE if chromosome has been found
                if not as_variants: self._start = 0
            else:
                self._flag = not self._vcf.goto(self._chrom, self._start, VCF.END) # FALSE if position has been found
        else:
            if self._start is not None or self._stop is not None:
                raise ValueError('cannot specify start or stop position without specifying chromosome')
            self._flag = not self._vcf.read() # FALSE if a first variant is present
            if not as_variants: self._start = 0
        if not self._flag:
            self._curr_chrom = self._vcf.get_chrom()
        else:
            self._curr_chrom = None
        if as_variants:
            self._site_added = False
        else:
            self._nextstart = self._start
            self._curstart = None

    @property
    def span(self):
        """
        Length of the current window in terms of genomic length.
        Actually, distance between the first and last site of the
        window. If the window doesn't contain sites, equal to ``None``.
        """
        if  len(self._sites) == 0: return None
        else: return int(self._sites[-1].position - self._sites[0].position) + 1
        
    @property
    def bounds(self):
        """
        Bounds of the current window. Bounds are defined as ``(start, stop)``
        in such a way that the sequence corresponding to the window can
        be extracted using ``[start, stop]`` as slice operator (meaning
        that ``stop`` is not included in the window in any case. If
        *as_variants* is ``True``, bounds are position of the first site
        and the position immediately after the last site or ``None`` if
        the window is empty. If *as_variants* is ``False``, bounds are
        the start and stop positions. Before start of the iteration, set
        as ``None``.
        """
        if self._as_variants:
            if len(self._sites):
                return int(self._sites[0].position), int(self._sites[-1].position + 1)
            else:
                return None
        else:
            if self._curstart is None: return None
            else: return self._curstart, self._curstart + self._size
    
    @property
    def chromosome(self):
        """
        Current chromosome. Before iteration start, or after iteration
        end, the value is undefined.
        """
        return self._curr_chrom
        
    def __len__(self):
        return len(self._sites)

    def __iter__(self):
        return iter(self._sites)
    
    def __getitem__(self, idx):
        try: return self._sites[idx]
        except IndexError: raise IndexError('site index out of range')

    def move(self):
        """
        Move to the next window. Sites that are shared by consecutive
        windows are represented by the same :class:`.Site` instances
        although they will generally shifted in index.

        :return: ``True`` if the operation succeeded and ``False``
            otherwise. In the former case, the window may or may not
            contain sites depending on the presence of sites passing
            criteri within the window range. In the latter case, the
            window should be considered to be uninitialized, and further
            calls to :meth:`.move` will keep on returning ``False``
            without error.
        """

        # case where there is nothing left to read
        if self._flag:
            del self._sites[:]
            return False

        # new window is on new chromosome
        if self._vcf.get_chrom() != self._curr_chrom:
            if self._chrom is not None:
                self._flag = True
                return False
            else:
                del self._sites[:]
                self._curr_chrom = self._vcf.get_chrom()
                if not self._as_variants:
                    self._curstart = 0

        # delete first sites up to start of next window according to argument step (EXCEPT for very first window OR after change of chromosome)
        else:
            if self._as_variants:
                del self._sites[:self._step]
            else:
                self._curstart = self._nextstart
                while len(self._sites) and self._sites[0].position < self._curstart:
                    del self._sites[0]

        if self._stop is not None:
            if self._as_variants:
                if len(self._sites) == 0 and self._vcf.get_pos() >= self._stop:
                    self._flag = True   
                    return False
            elif self._curstart >= self._stop:
                self._flag = True   
                return False

        # initialize flag to assert that at least one site has been added
        if self._as_variants:
            self._site_added = False

        # process all sites until end of window (window size exhausted, end of chromosome) or end of sliding window (end of VCF, end of chromosome or stop parameter)
        while True:

            # reached end of chromosome
            if self._vcf.get_chrom() != self._curr_chrom:
                break
            
            # read past the last site of sliding window
            if self._stop is not None and self._vcf.get_pos() >= self._stop:
                self._flag = True
                if len(self._sites) == 0 and self._skip_empty:
                    del self._sites[:]
                    return False
                else:
                    return True
            
            # end of window reached
            if self._as_variants:
                if len(self._sites) == self._size: # window full
                    break
            else:
                if self._vcf.get_pos() >= self._curstart + self._size: # reached window's end
                    break

            # REF/ALT alleles acceptable
            if ((self._mode == 0 and self._vcf.is_snp()) or
                (self._mode == 1 and self._vcf.is_single()) or
                 self._mode == 2):

                # if number of missing data is acceptable
                site = self._vcf.as_site()
                if site.num_missing <= self._max_missing:

                    # add site to window (when all filters passed)
                    self._sites.append(site)
                    if self._as_variants:
                        self._site_added |= 1

            # read next site (and set flag to True if nothing more to be read)
            if not self._vcf.read():
                self._flag = True
                if self._as_variants and not self._site_added:
                    return False # require that at least 1 site has been added in this window
                elif len(self._sites) == 0 and self._skip_empty:
                    del self._sites[:]
                    return False
                else:
                    return True

        # window finished but there might a next one
        if self._as_variants:

            # ignore sites between windows (if step > size)
            for i in range(self._size, self._step):
                if self._stop and self._vcf.get_pos() >= self._stop:
                    self._flag = True
                    break
                if self._vcf.get_chrom() != self._curr_chrom:
                    break
                if not self._vcf.read():
                    self._flag = True
                    break
        else:
            self._nextstart = self._curstart + self._step
            if self._stop and self._nextstart >= self._stop: return False

            # ignore sites between windows (if step > size)
            while self._vcf.get_pos() < self._nextstart and self._vcf.get_chrom() == self._curr_chrom:
                if self._stop and self._vcf.get_pos() >= self._stop:
                    self._flag = True
                    break
                if not self._vcf.read():
                    self._flag = True
                    break

        # skip empty window
        if self._skip_empty and len(self._sites) == 0: return self.move()
        else: return True
