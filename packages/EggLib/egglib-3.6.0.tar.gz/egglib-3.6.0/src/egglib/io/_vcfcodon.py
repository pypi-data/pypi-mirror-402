"""
    Copyright 2025 Stephane De Mita, Mathieu Siol

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

from ._vcftools import VCF
from ._gff3 import GFF3, Gff3Feature
from .._interface import Container
from .._site import Site
from .._freq import Freq
from ..tools import ReadingFrame, Translator
from ..alphabets import codons

class CodonVCF:
    """
    Analysis of coding sites from VCF data.

    This class takes a VCF, which is required to be indexed, and the GFF
    annotation (in GFF3 format) of the reference sequence. It allows to
    iterate over coding sites of a given CDS feature (using
    :meth:`.iter_codons`) or extract the coding site which includes a
    random position (using :meth:`.from_position`).

    .. note::
        Codons with at least one missing nucleotide are ignored
        altogether.

    :param vcf_name: name of an indexed VCF file.
    :param gff_name: name of a GFF3-fomatted annotation file
        corresponding to the reference of the VCF file.
    :param use_ref: assume positions not referred to in the VCF file are
        identical to the reference.
    :param ref: only if *use_ref* is ``True``: reference genome as a
        :class:`.Container` instance. By default, use the reference
        genome included in the GFF3. If no reference genome is provided
        and *use_ref* if ``True``, a ``ValueError`` is raised.

    .. versionadded:: 3.5
    """
    _complement = {
        'A': 'T',
        'C': 'G',
        'G': 'C',
        'T': 'A',
        'R': 'Y',
        'Y': 'R',
        'S': 'S',
        'W': 'W',
        'K': 'M',
        'M': 'K',
        'B': 'V',
        'D': 'H',
        'H': 'D',
        'V': 'B',
        'N': 'N',
        '-': '-',
        '?': '?'}

    def __init__(self, vcf_name, gff_name, fill_with_ref=False, ref=None):

        # open requested files
        self._vcf = VCF(vcf_name)
        self._gff = GFF3(gff_name, strict=True)
        if not self._vcf.has_index: raise ValueError('VCF file must be indexed')

        # make a database of CDS features
        self._db = {}
        for feat in self._gff.iter_features(all_features=True):
            if feat.type == 'CDS':
                self._db[feat.ID] = feat

        # get the reference
        if fill_with_ref:
            if ref:
                if not isinstance(ref, Container): raise TypeError('`ref` must be a Container instance')
                self._ref = ref
            else:
                if self._gff.sequences is None: raise ValueError('a reference genome must be provided')
                self._ref = self._gff.sequences
        else:
            self._ref = None

        # initialize placeholders for reading frame information
        self._rf = None
        self._seqid = None
        self._ref_sample = None

        # utilities
        self._frq = Freq()
        self._tr = Translator(code=1)

    def set_cds(self, ID, subset=None):
        """
        Specify the CDS feature to consider.

        :param ID: name of a CDS feature of the annotation.
        :param subset: optional list of indexes of samples to include
            (by default, all samples are included). If the sample
            indexes are reshuffled or repeated, the exported sites will
            be affected accordingly. Samples must be understood as per
            the VCF file (e.g. individuals if the VCF contains diploid
            individuals).

        .. note::

            The provided annotation ID must correspond to a *CDS*
            feature (and not a *gene* or a *mRNA*). 
        """
        if ID not in self._db: raise ValueError(f'cannot find CDS with ID: {ID}')
        feat = self._db[ID]
        segs = feat.segments

        if feat.strand == '-':
            # reverse exons and count positions from the end
            segs = [(feat.end-b, feat.end-a, c) for (a,b,c) in reversed(segs)]
            self._anchor = feat.end-1
        else:
            segs = [(a,b,c) for (a,b,c) in segs] # deep copy in case the feature is used again
            self._anchor = None

        # validate list of samples
        self._subset = subset
        if subset is not None:
            for i in subset:
                if i < 0 or i >= self._vcf.num_samples:
                    raise ValueError(f'sample index of out range: {i}')

        # ensure that exons are continuous (no partial exons expect 5' end of first and 3' end of last)
        codon_start = [1, 3, 2]
        cur = codon_start[segs[0][2]] - 1 + (segs[0][1] - segs[0][0])
        segs[0] = (segs[0][0], segs[0][1], codon_start[segs[0][2]])
        for i in range(1, len(segs)):
            if cur%3 != codon_start[segs[i][2]] - 1: raise ValueError(f'Mismatch between expected phase and value in GFF3. Exon {i} or {i+1} seems to be partial. Cannot proceed.')
            segs[i] = segs[i][:2]
            cur += segs[i][1] - segs[i][0]

        # create ReadingFrame
        self._rf = ReadingFrame(segs, keep_truncated=False)
        self._seqid = feat.seqid

        # detect reference
        if self._ref is None:
            self._ref_sample = None
        else:
            self._ref_sample = self._ref.find(feat.seqid)
            if self._ref_sample is None: raise ValueError(f'seqid {feat.seqid} not found in reference genome')

    def iter_codons(self):
        """
        Iterate over coding sites.
        Return an iterator over :class:`.CodingSite` objects
        representing all codon positions defined by the current CDS
        annotation. Codons positions which are incomplete in the feature
        due to missing 5' or 3' end are not included in the iteration.
        """

        if self._rf is None: raise ValueError('a CDS feature must be specified first')
        for idx, bases in enumerate(self._rf.iter_codons()):
            yield self._get_site(bases, idx)

    def from_position(self, pos):
        """
        Return the :class:`.CodingSite` corresponding to the codon to
        which the passed position belongs to.
        """
        if self._rf is None: raise ValueError('a CDS feature must be specified first')
        idx = self._rf.codon_index(pos if self._anchor is None else self._anchor-pos)
        if idx is None: return CodingSite(CodingSite.NCOD, None, None, None)
        bases = self._rf.codon_bases(idx)
        if None in bases: return CodingSite(CodingSite.NCOD, None, None, None)
        return self._get_site(bases, idx)

    def _get_site(self, pos, codon_index):
        # revert positions if needed
        if self._anchor is not None:
            pos = [self._anchor-p for p in pos] # reverse the codon

        flag = 0 # flag telling which site(s) are available
        sites = [None] * 3
        ns = set()
        for idx in range(3):
            if not self._vcf.goto(self._seqid, pos[idx]):
                continue
            # move forward until a type-0 variant is found, if any
            while self._vcf.get_allele_type() != 0 or self._vcf.get_pos() < pos[idx]:
                if not self._vcf.read(): break

            # if valid site
            if self._vcf.get_pos() == pos[idx] and self._vcf.get_allele_type() == 0:
                flag |= 1 << idx
                genotypes = self._vcf.get_genotypes()
                if self._subset is None: genotypes = [j for i in genotypes for j in i]
                else: genotypes = [j for i in self._subset for j in genotypes[i]]
                if self._anchor: sites[idx] = ['?' if i is None else self._complement[i] for i in genotypes]
                else: sites[idx] = ['?' if i is None else i for i in genotypes]
                ns.add(len(sites[idx]))

        # mismatch in sample size
        if len(ns) > 1:
            return CodingSite(CodingSite.MISM, self._seqid, codon_index, pos[1])

        # unavailable positions
        if flag != 7:
            if flag == 0 or self._ref_sample is None: return CodingSite(CodingSite.UNAVAIL, self._seqid, codon_index, pos[1])
            ns = ns.pop()
            if flag&1 == 0:
                try: b = self._ref_sample.sequence[pos[0]]
                except IndexError: raise ValueError('cannot find site in reference while filling a gap in VCF')
                sites[0] = [b] * ns
            if flag&2 == 0:
                try: b = self._ref_sample.sequence[pos[1]]
                except IndexError: raise ValueError('cannot find site in reference while filling a gap in VCF')
                sites[1] = [b] * ns
            if flag&4 == 0:
                try: b = self._ref_sample.sequence[pos[2]]
                except IndexError: raise ValueError('cannot find site in reference while filling a gap in VCF')
                sites[2] = [b] * ns

        # build site
        site = CodingSite(0, self._seqid, codon_index, pos[1])
        site.extend(list(map(''.join, zip(sites[0], sites[1], sites[2]))))

        # analyse site
        self._frq.from_site(site)
        if self._frq.num_alleles > 2:
            site.set_bit(CodingSite.MMUT)
        aas = [self._tr.translate_codon(self._frq.allele(idx)) for idx in range(self._frq.num_alleles)]
        for i in range(self._frq.num_alleles):
            a1 = self._frq.allele(i)
            if aas[i] == '*':
                site.set_bit(CodingSite.STOP)
            else:
                for j in range(i+1, self._frq.num_alleles):
                    a2 = self._frq.allele(j)
                    if a1 != a2:
                        site.set_bit(CodingSite.VAR)
                    if (a1[0] != a2[0] and (a1[1] != a2[1] or a1[2] != a2[2])) or (a1[1] != a1[1] and a1[2] != a2[2]):
                        site.set_bit(CodingSite.MHIT)
                    if aas[j] == '*': continue
                    if aas[i] == aas[j]:
                        site.set_bit(CodingSite.SYN)
                    else:
                        site.set_bit(CodingSite.NSYN)

        # return site
        return site

class CodingSite(Site):
    """
    Represent a coding site extracted from VCF data. Instances of this
    class are normally generated by :class:`CodonVCF` .

    .. versionadded:: 3.5

    :ivar NCOD: requested position is not in coding region. Only if site
        is obtained from :meth:`.from_position`. If this flag is on, all
        the others are off.

    :ivar MISM: there is a mismatch in sample size (including mismatch
        in ploidy) between sites of the codon. If this flag is on, all
        the others are off.

    :ivar UNAVAIL: at least one of the three codon position is
        unavailable and there is not available reference genome. If this
        flag is on, all the others are off.

    :ivar STOP: a stop codon has been found in the site. The stop codon
        is not counted as missing data but is not considered for
        synonymous / nonsynonymous analysis either. However it is
        considered to determine if there is polymorphism, multiple hits
        and multiple mutations.

    :ivar MHIT: more than one of the three codon positions is variable.

    :ivar MMUT: there are more than two different codons.

    :ivar SYN: there is at least one synonymous change (excluding stop
        codons).

    :ivar NSYN: there is at least one non-synonymous change (excluding
        stop codons).

    :ivar VAR: there is at least one change (including stop codons).
    """

    NCOD =    1
    MISM =    2
    UNAVAIL = 4
    STOP =    8
    MHIT =   16
    MMUT =   32
    SYN =    64
    NSYN =  128
    VAR  =  256

    def __init__(self, flag, chrom, idx, pos):
        super().__init__(alphabet=codons)
        self._flag = flag
        self._codon_index = idx
        if chrom is not None: self.chrom = chrom
        if pos is not None: self.position = pos

    def set_bit(self, flag):
        """
        Turn a flag on. For example, to specify the the site has a stop
        codon, use: ``cdn.set_bit(cdn.STOP)``
        """
        self._flag |= flag

    @property
    def codon_index(self):
        """
        Codon index. Index of the codon in the CDS specification.

        .. note::
            Only complete codons are included in the numeration.
        """
        return self._codon_index

    @property
    def flag(self):
        """
        Flag value.
        """
        return self._flag

    def is_valid(self):
        """
        Check if site is valid. ``True`` if the site is in coding
        region, has no mismatch, has all available position and doesn't
        contain a stop codon.
        """
        return self._flag&(self.NCOD|self.MISM|self.UNAVAIL|self.STOP) == 0
