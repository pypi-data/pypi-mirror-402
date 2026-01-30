"""
    Copyright 2016-2025 Stephane De Mita, Mathieu Siol

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
from . import _interface

def site_from_align(align, index):
    """
    Create a site from a position of an alignment.
    Import allelic and genotypic data from a position of the provided
    :class:`.Align` instance.

    :param align: an :class:`!Align` instance.
    :param index: the index of a valid (not out of range) position of
        the alignment.
    :return: A new :class:`!Site` instance.
    """
    obj = Site()
    obj.from_align(align, index)
    return obj

def site_from_list(array, alphabet):
    """
    Create a site based on a list of allelic values.

    :param array: a :class:`list` of allelic values.
    :param alphabet: an alphabet (input allelic values must match this
        alphabet).
    """
    obj = Site()
    obj.from_list(array, alphabet)
    return obj

def site_from_vcf(vcf, start=0, stop=None):
    """
    Extract a site from a VCF parser.
    Import allelic and genotypic data from a VCF parser. The VCF parser
    must have processed a variant and the variant is required to have
    genotypic data available as the GT format field. An exception is
    raised otherwise.

    :param vcf: an :class:`.io.VcfParser` instance containing data. There
        must at least one sample and the GT format field must be
        available. It is not required to extract variant data manually.

    :param start: index of the first sample to process. Index is
        required to be within available bounds (it must be at least 0
        and smaller than the number of samples in the VCF data). Note
        that in a VCF file a sample corresponds to a genotype.

    :param stop: sample index at which processing must be stopped (this
        sample is not processed). Index is required to be within
        available bounds (if must be at least equal to *start* and not
        larger than the number of samples in the VCF data). Note that in
        a VCF file, a sample corresponds to a genotype.
    """
    obj = Site()
    obj.from_vcf(vcf, start, stop)
    return obj

class Site(object):
    """
    Store alleles from a single site. Instances can be created from a
    position in an :class:`.Align` instance (using :func:`.site_from_align`),
    from the current position of a :class:`.VcfParser` (using :func:`.site_from_vcf`),
    or from a user-provided list of allelic values (using :func:`.site_from_list`).

    :param alphabet: an :class:`.Alphabet` instance (only useful if
        data are supposed to be loaded one by one :meth:`~.Site.append`
        or :meth:`~.Site.extend`).

    The following operations are available on ``site`` if it is a :class:`!Site`
    instance:

    +------------------------+---------------------------------+
    | Operation              | Result                          |
    +========================+=================================+
    | ``len(site)``          | number of samples               |
    +------------------------+---------------------------------+
    | ``for i in site: ...`` | iterate over alleles            |
    +------------------------+---------------------------------+
    | ``site[i]``            | access allele at given index    |
    +------------------------+---------------------------------+
    | ``site[i] = a``        | overwrite allele at given index |
    +------------------------+---------------------------------+
    | ``del site[i]``        | delete allele at given index    |
    +------------------------+---------------------------------+
    """

    @classmethod
    def _from_site_holder(cls, obj, alphabet):
        ret = object.__new__(cls)
        ret._obj = obj
        ret._alphabet = alphabet
        return ret

    def __init__(self, alphabet=None):
        self._obj = _eggwrapper.SiteHolder()
        self._alphabet = alphabet

    def reset(self):
        """Clear all data from the instance (including the alphabet)."""
        self._obj.reset()
        self._alphabet = None

    @property
    def position(self):
        """
        Position of the site. The position is set automatically if the
        instance is created or reset from an :class:`.Align`
        or a :class:`.VCF`. In all cases, the value can be modified.
        """
        return None if self._obj.get_position() == _eggwrapper.UNDEF else self._obj.get_position()

    @position.setter
    def position(self, value):
        self._obj.set_position(value)

    @property
    def chrom(self):
        """
        Chromosome of the site. The chromosome is set automatically if
        the instance is created from a :class:`.VCF`. By default, it is
        ``None``. To modify the value, it is required to pass a
        non-empty :class:`str`.
        """
        s = self._obj.get_chrom()
        if s == '': return None
        else: return s

    @chrom.setter
    def chrom(self, value):
        if not isinstance(value, str): raise TypeError('this property requires type str' )
        if value == '': raise ValueError('a non-empty string is required')
        self._obj.set_chrom(value)

    @property
    def ns(self):
        """Number of samples"""
        return self._obj.get_ns()

    def __len__(self):
        return self._obj.get_ns()

    @property
    def num_missing(self):
        """Number of missing data."""
        return self._obj.get_missing()

    @property
    def alphabet(self):
        """
        Alphabet attached to the instance. It is possible to set the
        alphabet, but not change it (the alphabet can be changed only
        immediately after creation if no alphabet has been
        specified, or after calling :meth:`~.Site.reset`.
        """
        return self._alphabet

    @alphabet.setter
    def alphabet(self, alph):
        if self._alphabet is not None: raise ValueError('cannot change alphabet of a Site')
        self._alphabet = alph

    def as_list(self):
        """
        Generate a list containing data from the instance.

        :return: A :class:`list` of allelic values.
        """
        return [self._alphabet.get_value(self._obj.get_sample(i)) for i in range(self._obj.get_ns())]

    def __getitem__(self, idx):
        if isinstance(idx, slice): raise ValueError('slices are not supported')
        if idx < 0: idx = self._obj.get_ns() + idx
        if idx < 0 or idx >= self._obj.get_ns(): raise IndexError('invalid sample index')
        return self._alphabet.get_value(self._obj.get_sample(idx))

    def __setitem__(self, idx, val):
        if isinstance(idx, slice): raise ValueError('slices are not supported')
        if idx < 0: idx = self._obj.get_ns() + idx
        if idx < 0 or idx >= self._obj.get_ns(): raise IndexError('invalid sample index')
        self._obj.set_sample(idx, self._alphabet.get_code(val))

    def __delitem__(self, idx):
        if isinstance(idx, slice): raise ValueError('slices are not supported')
        if idx < 0: idx = self._obj.get_ns() + idx
        if idx < 0 or idx >= self._obj.get_ns(): raise IndexError('invalid sample index')
        self._obj.del_sample(idx)

    def append(self, val):
        """ Add an allele at the end of the site. """
        self._obj.add(1)
        self._obj.set_sample(self._obj.get_ns()-1, self._alphabet.get_code(val))

    def extend(self, vals):
        """
        Add several alleles at the end of the site. The alleles
        must be provided as an iterable. """
        old_ns = self._obj.get_ns()
        self._obj.add(len(vals))
        for i, val in enumerate(vals):
            self._obj.set_sample(old_ns+i, self._alphabet.get_code(val))

    def from_align(self, align, index):
        """
        Import data from the provided :class:`.Align`. All data
        currently stored in the instance are discarded.

        :param align: an :class:`!Align` instance.
        :param index: index of the site to extract.
        """
        self._obj.reset()
        self._alphabet = align._alphabet
        if index >= align.ls: raise IndexError('invalid site index')
        self._obj.process_align(align._obj, index)
        self._position = index

    def from_list(self, array, alphabet):
        """
        Import alleles from the provided list.

        :param array: a :class:`list` of allelic values.
        :param alphabet: an alphabet (input allelic values must match this
            alphabet).
        """
        self._obj.reset()
        self._alphabet = alphabet
        if len(array) == 0: return
        self._obj.add(len(array))
        for i, v in enumerate(array):
            self._obj.set_sample(i, self._alphabet.get_code(v))
        self._position = None

    def from_vcf(self, vcf, start=0, stop=None):
        """
        Import data from the provided :class:`.io.VcfParser`.  
        The VCF parser
        must have processed a variant and the variant is required to have
        genotypic data available as the GT format field. An exception is
        raised otherwise.

        :param vcf: a :class:`!VcfParser` instance containing data. There
            must at least one sample and the GT format field must be
            available. It is not required to extract variant data manually.

        :param start: index of the first sample to process. Index is
            required to be within available bounds (it must be at least 0
            and smaller than the number of samples in the VCF data). Note
            that in a VCF file a sample corresponds to a genotype.

        :param stop: sample index at which processing must be stopped (this
            sample is not processed). Index is required to be within
            available bounds (if must be at least equal to *start* and not
            larger than the number of samples in the VCF data). Note that in
            a VCF file, a sample corresponds to a genotype.
        """
        self._obj.reset()
        vcf.get_genotypes(start, stop, self)
