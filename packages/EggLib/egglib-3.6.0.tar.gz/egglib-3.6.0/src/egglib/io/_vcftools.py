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

from .. import config
from .. import _site
from .. import alphabets

try:
    from . import _vcfparser
    from ._vcfparser import VCF, index_vcf, hts_set_log_level
    from ._vcfslider import VcfSlider
    from ._vcfcodon import CodonVCF
    config.htslib = 1
    class VCF(VCF):
        def as_site(self):
            """
            Extract current variant. Return the current genotype values
            as a :class:`.Site` object. The alphabet is DNA if the site
            is a SNP, a string-type alphabet with ad hoc available
            alleles and ``?`` and ``-`` as missing alleles for indels,
            and a custom-type alphabet with ad hoc available alleles and
            ``?`` a missing data otherwise.

            .. versionadded:: 3.4

            .. versionchanged:: 3.5.1
                The ``*`` is not included anymore a available allele if
                there is an indel while ``-`` is always added as
                potential missing allele for string-type alphabets.
            """
            site = _site.Site()
            genotypes = self.get_genotypes()
            if genotypes is None:
                raise TypeError('genotype field not available for this variant')
            match self.get_allele_type():
                case 0: alphabet = alphabets.DNA
                case 1: alphabet = alphabets.Alphabet('string', self.get_alleles(), ['?', '-'])
                case 2: alphabet = alphabets.Alphabet('custom', self.get_alleles(), ['?'])
                case None: return None
                case _: raise RuntimeError('unexpected return code of VCF.get_allele_type()')
            site.from_list([j if j is not None else '?' for i in genotypes for j in i], alphabet = alphabet)
            site.position = self.get_pos()
            site.chrom = self.get_chrom()
            return site

        def iter_sites(self, *args, **kwargs):
            """iter_sites([chrom[, start][, stop]][, max_missing][, mode])

            Return an iterator over sites. Each variant found in the VCF
            file is returned as a :class:`.Site` instance.

            By default, process sites from the current position up to
            the end of the file. To control the region used for
            iteration, use the *chrom*, *start*, and *stop* argument.

            :param chrom: name of the chromosome to process. If *None*,
                process all chromosomes. By default (if *start* and
                *stop* are not specified) process the whole chromosome,
                going back to the first position if needed. Only
                available if the VCF is indexed.

            :param start: start position. Only allowed if *chrom* is
                specified. The first site returned will be at the
                smallest available position starting from *start*. By
                default, start at the beginning of the chromosome.

            :param stop: stop position. Only allowed if *chrom* is
                specified. The position of the last site returned will
                be a most the one before the *stop* position. By
                default, stop at the last site of the chromosome.

            :param max_missing: maximum number of missing data to
                consider a variant. By default, all sites with at least
                one missing data are ignored.

            :param mode: 0: include only SNP variants (variants with at
                least two alleles, all corresponding to a single
                nucleotide, although those alleles are not required to
                be called in genotypes); 1: include SNP variants and
                invariant positions; 2: include all variants from the 
                VCF. The default is 0.

            .. versionadded:: 3.4

            .. versionchanged:: 3.5.1
                See change described in :meth:`.as_site` relative to
                the management of gaps due to overlaping deletions.
            """
            return self.site_iterator(self, *args, **kwargs)

        class site_iterator:
            def __init__(self, vcf, chrom=None, start=None, stop=None, max_missing=0, mode=0):
                if start is not None and chrom is None:
                    raise ValueError('cannot specify `start` without `chrom`')
                if stop is not None:
                    if stop < 0:
                        raise ValueError('invalid value for `stop`')
                    if chrom is None:
                        raise ValueError('cannot specify `stop` without `chrom`')
                if max_missing < 0:
                    raise ValueError('invalid value for `max_missing`')
                if mode not in {0, 1, 2}:
                    raise ValueError('invalid value for `mode`')
                if chrom is not None:
                    if start is None: self.b = vcf.goto(chrom)
                    else: self.b = vcf.goto(chrom, start, vcf.END)
                else: self.b = vcf.read()
                self.vcf = vcf
                self.chrom = chrom
                self.stop = stop
                self.max_missing = max_missing
                self.mode = mode

            def __iter__(self):
                return self

            def __next__(self):
                while True:
                    if not self.b: raise StopIteration
                    if self.chrom is not None and self.vcf.get_chrom() != self.chrom: raise StopIteration
                    if self.stop is not None and self.vcf.get_pos() >= self.stop: raise StopIteration
                    if (    (self.mode == 0 and self.vcf.is_snp()) or
                            (self.mode == 1 and self.vcf.is_single()) or
                             self.mode == 2 ):
                        site = self.vcf.as_site()
                        if site.num_missing <= self.max_missing:
                            self.b = self.vcf.read()
                            return site
                    self.b = self.vcf.read()

    VCF.__doc__ = _vcfparser.VCF.__doc__

except ImportError:
    msg = '''The required dependency htslib is not available.
    Please refer to the installation instructions for more information
    at https://egglib.org/install.html.
Feature not available.'''
    config.htslib = 0
    def VCF(*args, **kwargs):
        raise NotImplementedError(msg)
    def index_vcf(*args, **kwargs):
        raise NotImplementedError(msg)
    def hts_set_log_level(*args, **kwargs):
        raise NotImplementedError(msg)
    def VcfSlider(*args, **kwargs):
        raise NotImplementedError(msg)
    def CodonVCF(*args, **kwargs):
        raise NotImplementedError(msg)
