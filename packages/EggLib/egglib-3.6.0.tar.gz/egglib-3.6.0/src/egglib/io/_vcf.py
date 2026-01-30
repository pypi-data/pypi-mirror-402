"""
    Copyright 2015-2025 Stephane De Mita, Mathieu Siol, Thomas Coudoux

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

import os
from .. import eggwrapper as _eggwrapper
from .. import alphabets
from .. import _site

FIRST = _eggwrapper.FIRST
LAST = _eggwrapper.LAST

### NOTE: it is necessary to replace the position() method of _eggwrapper.VcfParser!!! 

class _VcfParserBase(object):
    def _f_position(self):
        x = _eggwrapper.VcfParser.position(self._parser)
        return -1 if x == _eggwrapper.BEFORE else x

    def _position(self):
        raise NotImplementedError

    def __init__(self):
        raise NotImplementedError

    @staticmethod
    def _mk_index_fname(fname):
        basename, ext = os.path.splitext(fname)
        if ext == '.vcf': return basename + '.vcfi'
        else: return fname + '.vcfi'

    def _set_params(self, threshold_PL, threshold_GL):
        if threshold_PL is None and threshold_GL is None:
            self._parser.set_threshold_PL(_eggwrapper.UNKNOWN)
            self._parser.set_threshold_GL(_eggwrapper.UNKNOWN)
        elif threshold_PL is not None and threshold_GL is None :
            if threshold_PL < 1: raise ValueError('threshold_PL must be at least 1')
            else: self._parser.set_threshold_PL(threshold_PL) 
        elif threshold_GL is not None and threshold_PL is None :
            if threshold_GL < 1: raise ValueError('threshold_GL must be at least 1')
            else: self._parser.set_threshold_GL(threshold_GL)            
        else:
            raise ValueError('cannot use threshold_PL and threshold_GL at the same time')

    file_format = property(lambda self: self._parser.file_format(), doc='File format specified in the header.')
    num_info = property(lambda self: self._parser.num_info(), doc='Number of INFO definitions in the header.')
    num_format = property(lambda self: self._parser.num_format(), doc='Number of FORMAT definitions in the header.')
    num_filter = property(lambda self: self._parser.num_filter(), doc='Number of FILTER definitions in the header.')
    num_alt = property(lambda self: self._parser.num_alt(), doc='Number of ALT definitions in the header.')
    num_meta = property(lambda self: self._parser.num_meta(), doc='Number of META definitions in the header.')
    num_samples = property(lambda self: self._parser.num_samples(), doc='Number of samples defined in the header.')

    def get_sample(self, idx):
        """
        Get the name of a sample read from the header. The index
        must be smaller than :py:obj:`~.io.VcfParser.num_samples`.
        """
        if idx < 0 or idx >= self._parser.num_samples(): raise IndexError('sample index out of range')
        return self._parser.get_sample(idx)

    def get_info(self, idx):
        """
        Get an INFO definition from the header. The
        index must be smaller than :py:obj:`.num_info`. Return a
        dictionary containing the following data:

        * ``"id"``: identifier string.
        * ``"type"``: one of ``"Integer"``, ``"Float"``, ``"Flag"``,
          ``"Character"``, and ``"String"``.
        * ``"description"``: description string.
        * ``"number"``: expected number of items. Special values are
          ``None`` (if undefined), ``"NUM_GENOTYPES"`` (number matching
          the number of genotypes for any particular variant),
          ``"NUM_ALTERNATE"`` (number matching the number of alternate
          alleles for any particular variant), and ``"NUM_ALLELES"``
          (number matching the number of alleles--including the
          reference--for any particular variant).
        * ``"extra"``: all extra qualifiers, presented as a list
          of ``(key, value)`` :class:`tuple` instances.
        """
        if idx < 0 or idx >= self._parser.num_info(): raise IndexError('INFO index out of range')
        info = self._parser.get_info(idx)
        n = info.get_number()
        if n == _eggwrapper.UNKNOWN: n = None
        elif n == _eggwrapper.NUM_ALTERNATE: n = 'NUM_ALTERNATE'
        elif n == _eggwrapper.NUM_GENOTYPES: n = 'NUM_GENOTYPES'
        elif n == _eggwrapper.NUM_POSSIBLE_ALLELES: n = 'NUM_ALLELES'
        t = info.get_type()
        if t == _eggwrapper.Info.Integer: t = 'Integer'
        elif t == _eggwrapper.Info.Float: t = 'Float'
        elif t == _eggwrapper.Info.Flag: t = 'Flag'
        elif t == _eggwrapper.Info.Character: t = 'Character'
        elif t == _eggwrapper.Info.String: t = 'String'
        else: raise ValueError('invalid VCF metainformation type found')
        return {
            'id': info.get_ID(),
            'description': info.get_description(),
            'number': n,
            'extra': [(info.get_extra_key(j), info.get_extra_value(j))
                                for j in range(info.get_num_extra())],
            'type': t
        }

    def get_format(self, idx):
        """
        Get a FORMAT definition from the header. The
        index must be smaller than :py:obj:`~.io.VcfParser.num_format`. Return a
        dictionary containing the following data:

        * ``"id"``: identifier string.
        * ``"type"``: one of ``"Integer"``, ``"Float"``, ``"Character"``,
          and ``"String"``.
        * ``"description"``: description string.
        * ``"number"``: expected number of items. Special values are
          ``None`` (if undefined), ``"NUM_GENOTYPES"`` (number matching
          the number of genotypes for any particular variant),
          ``"NUM_ALTERNATE"`` (number matching the number of alternate
          alleles for any particular variant), and ``"NUM_ALLELES"``
          (number matching the number of alleles--including the
          reference--for any particular variant).
        * ``"extra"``: all extra qualifiers, presented as a list
          of ``(key, value)`` :class:`tuple` instances.
        """

        if idx < 0 or idx >= self._parser.num_format(): raise IndexError('FORMAT index out of range')
        format_ = self._parser.get_format(idx)

        n = format_.get_number()
        if n == _eggwrapper.UNKNOWN: n = None
        elif n == _eggwrapper.NUM_ALTERNATE: n = 'NUM_ALTERNATE'
        elif n == _eggwrapper.NUM_GENOTYPES: n = 'NUM_GENOTYPES'
        elif n == _eggwrapper.NUM_POSSIBLE_ALLELES: n = 'NUM_ALLELES'

        t = format_.get_type()
        if t == _eggwrapper.Info.Integer: t = 'Integer'
        elif t == _eggwrapper.Info.Float: t = 'Float'
        elif t == _eggwrapper.Info.Character: t = 'Character'
        elif t == _eggwrapper.Info.String: t = 'String'
        else: raise ValueError('invalid VCF metainformation type found')

        return {
            'id': format_.get_ID(),
            'description': format_.get_description(),
            'number': n,
            'extra': [(format_.get_extra_key(j), format_.get_extra_value(j))
                                for j in range(format_.get_num_extra())],
            'type': t
        }

    def get_filter(self, idx):
        """
        Get a FILTER definition from the header. The
        index must be smaller than :py:obj:`~.io.VcfParser.num_filter`. Return a
        dictionary containing the following data:

        * ``"id"``: identifier string.
        * ``"description"``: description string.
        * ``"extra"``: all extra qualifiers, presented as a list
          of ``(key, value)`` :class:`tuple` instances.
        """
        if idx < 0 or idx >= self._parser.num_filter(): raise IndexError('FILTER index out of range')
        filter_ = self._parser.get_filter(idx)
        return {
            'id': filter_.get_ID(),
            'description': filter_.get_description(),
            'extra': [(filter_.get_extra_key(j), filter_.get_extra_value(j))
                                for j in range(filter_.get_num_extra())]
        }

    def get_alt(self, idx):
        """
        Get an ALT definition from the header. The
        index must be smaller than :py:obj:`.num_alt`. Return a
        dictionary containing the following data:

        * ``"id"``: identifier string.
        * ``"description"``: description string.
        * ``"extra"s``: all extra qualifiers, presented as list
          of ``(key, value)`` :class:`tuple` instances.
        """
        if idx < 0 or idx >= self._parser.num_alt(): raise IndexError('ALT index out of range')
        alt = self._parser.get_alt(idx)
        return {
            'id': alt.get_ID(),
            'description': alt.get_description(),
            'extra': [(alt.get_extra_key(j), alt.get_extra_value(j))
                                for j in range(alt.get_num_extra())]
        }

    def get_meta(self, idx):
        """
        Get data for a given META field defined in the VCF header. The
        index must be smaller than :py:obj:`~.io.VcfParser.num_meta`. Return a
        :class:`tuple` containing the key and the value of the META
        field.
        """
        if idx < 0 or idx >= self._parser.num_meta(): raise IndexError('META index out of range')
        meta = self._parser.get_meta(idx)
        return ( meta.get_key(), meta.get_value() )

    def get_variant(self):
        """
        Get all data for the current variant.
        Return an :class:`.io.VcfVariant` instance containing all data available
        for the last variant processed by this instance. It is required
        that a variant has been effectively processed.
        """
        return VcfVariant._make(self)

    def get_genotypes(self, start=0, stop=None, dest=None):
        """
        Extract genotype data for the current site.

        It is required that a variant has been effectively processed.

        :param start: index of the first sample to process (at least
            0 and smaller than the number of samples).

        :param stop: sample index at which processing must be
            stopped (this sample is not processed; at least equal
            to *start* and smaller than the number of samples). 

        :param dest: a :class:`.Site`
            instance that will be recycled and used to place results.

        :return: A :class:`.Site` instance by default, or
            ``None`` if *dest* was specified.
        """

        # check parser
        if not self._parser.has_data(): raise ValueError('data must have been read from VCF parser')
        if not self._parser.has_GT(): raise ValueError('`VcfParser` instance must have `GT` data')
        pl = self._parser.ploidy()
        if pl < 1: raise ValueError('GT ploidy is 0')

        # check indexes
        n = self._parser.num_samples()
        if start < 0 or start >= n: raise IndexError('invalid start index')
        if stop is None: stop = n
        elif stop < start or stop > n: raise IndexError('invalid stop index')

        # create a new site instance or recycle if needed
        if dest is None: site = _site.Site()
        else: site = dest
        siteobj = site._obj
        siteobj.reset()
        site._alphabet = self._mk_alphabet()
        site._position = self._parser.position()

        # process
        siteobj.process_vcf(self._parser, start, stop)

        # create/recycle provided instance
        if dest is None:
            return site

    def _mk_alphabet(self):
        if self._parser.type_alleles() == 0:
            return alphabets.DNA
        if self._parser.type_alleles() == 1:
            alph = alphabets.Alphabet('string', [], [], case_insensitive=True, name=None)
            self._parser.set_alleles(alph._obj)
            return alph
        if self._parser.type_alleles() == 2 or self._parser.type_alleles() == 3:
            alph = alphabets.Alphabet('custom', [], [], case_insensitive=False, name=None)
            self._parser.set_alleles(alph._obj)
            return alph
        raise RuntimeError('unexpected value for `type_alleles` (internal error)')

class VcfStringParser(_VcfParserBase):
    """
    Import Variant Call Format data from a string.
    Alias of :class:`.io.VcfParser` processing strings instead of a file.
    The constructor takes a string containing a VCF header (the first
    line being the file format specification and the last line being the
    header line ,starting with ``#CHROM``).
    """

    def __init__(self, header, threshold_PL=None, threshold_GL=None):
        string = header.strip()
        self._parser = _eggwrapper.VcfParser()
        self._position = self._f_position # substitution function (replace BEFORE by -1)
        self._parser.read_header(string)
        self._set_params(threshold_PL, threshold_GL)

    def readline(self, string):
        """
        Read one variant from a user-provided single line. The string
        should contain a single line of VCF-formatted data (no header).
        All field specifications and sample information should be
        consistent with the information contained in the header that
        has been provided when creating this instance.

        :return: A :class:`tuple` with the chromosome name, the position, and
          the number of alleles at the variant (as indicated in the VCF
          line).
        """
        self._parser.readline(string)
        return self._parser.chromosome(), self._position(), self._parser.num_alternate() + 1

class VcfParser(_VcfParserBase):
    """
    Import Variant Call Format data from a file. The VCF format
    is designed to store data describing genomic variation in an
    extremely flexible way.
    See the `description of the VCF format. <https://github.com/samtools/hts-specs>`_
    To parse VCF data stored in string, use :class:`.io.VcfStringParser`.

    :param fname: name of a properly formatted VCF file. The header
        section will be processed upon instance creation, and lines will
        be read later, when the user iterates over the instance (or call
        :meth:`~.io.VcfParser.readline`).

    :param threshold_PL: call genotypes parameter.
        This parameter controls how genotype calling (GT field) is
        performed from the PL (phred-scaled genotype likelihood) field.
        By default (``None``), this conversion is never performed. If
        *threshold_PL* is specified, genotype calling is
        only performed if GT is not available and PL is available. The
        genotype with the lowest PL value is selected. The parameter gives the
        minimum acceptable gap between the best genotype and the second one.
        If the second genotype has a too good score, based on this parameter,
        the genotype is called unknown. The parameter must be at least 1.

    :class:`.io.VcfParser` instances are iterable. Everly loop
    yields a ``(chromosome, position, num_all)``
    :class:`tuple` that allows the user to determines if the variant is of
    interest. Note that the position is considered as an index and therefore
    has been decremented compared with the value found in the file.
    If the variant is of interest, :class:`.io.VcfParser` instances provide methods to
    extract all data for this variant. Iterating over VCF lines can be
    performed manually using the method :meth:`~.io.VcfParser.readline`.
    """

    def __init__(self, fname, threshold_PL=None, threshold_GL=None):
        self._parser = _eggwrapper.VcfParser()
        self._position = self._f_position # substitution function (replace BEFORE by -1)
        if not isinstance(fname, str): raise TypeError('invalid fname: invalid type')
        self._parser.open_file(fname)
        self._fname = fname
        self._set_params(threshold_PL, threshold_GL)

    def close(self):
        """
        Close file (if it is open)
        """
        self._parser.reset()

    @property
    def good(self):
        """
        Tell if the file is good for reading. ``False`` is the end of
        the file has been reached.
        """
        return self._parser.good()

    @property
    def currline(self):
        """ Index of the current line of the VCF file. """
        return self._parser.get_currline()

    def __iter__(self):
        return self

    def __next__(self):
        if not self._parser.good(): raise StopIteration
        self._parser.read()
        return self._parser.chromosome(), self._position(), self._parser.num_alternate() + 1

    def readline(self):
        """
        Read one variant.
        Return a :class:`tuple` with the chromosome name, the position, and
        the number of alleles at the variant (as indicated in the VCF
        file).
        Raise a :exc:`ValueError` if file is finished.
        """
        if not self._parser.good(): raise ValueError('cannot read line')
        self._parser.read()
        return self._parser.chromosome(), self._position(), self._parser.num_alternate() + 1

    def load_index(self, fname=None):
        """
        Load an index file allowing fast navigation.
        Index files allow fast navigation in VCF file regardless of
        their size, allowing to move instantly to a determined variant
        using its position or its index in file. Index files can be
        created by :func:`.io.make_vcf_index`.

        :param fname: name of the index file. By default, use the default
            index file name, which is the name of the VCF file with the
            ".vcfi" extension (removing the original extension only if it
            is ".vcf").
        """
        if fname is None:
            fname = self._mk_index_fname(self._fname)
        if not os.path.exists(fname):
            raise IOError('index file does not exist')
        self._parser.get_index().load_data(self._parser, fname)

    @property
    def num_index(self):
        """
        Number of indexed lines if the file index.
        """
        return self._parser.get_index().num()

    @property 
    def has_index(self):
        """
        ``True`` if an index file has been loaded.
        """
        return self._parser.get_index().has_data()

    def goto(self, contig, position=FIRST):
        """goto(self, contig, position=egglib.io.FIRST)

        Move to an arbitrary position of the VCF file.
        Requires an index (see :meth:`~.io.VcfParser.load_index`).
        A :exc:`ValueError` is raised if the position cannot be found.

        :param contig: contig name.
        :param position: contig position. Use :py:obj:`.io.FIRST` for the
            first available variant of the contig, :py:obj:`.io.LAST` for
            the last, and -1 for the position immediately before the
            first position (position 0 in VCF files).
        """
        self._parser.get_index().go_to(contig, _eggwrapper.BEFORE if position == -1 else position)

    def unread(self):
        """
        Go back to the previous variant. No index is required, but only
        allowed after reading one line (not allowed immediately after
        creating instance or calling :meth:`~.io.VcfParser.rewind`).
        """
        self._parser.unread()

    def rewind(self):
        """
        Reset the parser. Move back to the first variant.
        No index is required.
        """
        self._parser.rewind()

    def slider(self, size, step, as_variants=False, start=0, stop=None, max_missing=0, allow_indel=False, allow_custom=False):
        """
        Start a sliding window from the current position.

        :param size: size of the sliding window (by default, in base pairs).
        :param step: increment of the sliding window (by default, in base pairs).
        :param as_variants: express size and step in number of variants instead of base pairs.
        :param start: start position of the sliding window.
        :param stop: stop position of the sliding window.
        :param max_missing: maximum number of missing alleles (variants
            exceeding this threshold are ignored).

            .. warning::
                Here, *max_missing* must be an absolute number of
                samples.

        :param allow_indel: include variants with alleles of variable size
        :param allow_custom: include variants with custom alleles

        :return: An :class:`.io.VcfSlidingWindow` instance.

        .. versionchanged:: 3.2.0
            *max_missing* is required to be an integer.
        """
        if not self._parser.good(): raise ValueError('parser reached end of file')
        if max_missing > self._parser.num_samples(): raise ValueError('invalid value for `max_missing`')
        if not isinstance(max_missing, int): raise TypeError('`max_missing\' must be an integer')
        obj = VcfSlidingWindow.__new__(VcfSlidingWindow)
        obj._sld = _eggwrapper.VcfWindowSliderPerSite() if as_variants else _eggwrapper.VcfWindowSlider()
        obj._wdw = VcfWindow.__new__(VcfWindow)
        obj._wdw._sld = obj._sld
        obj._wdw._parser = self
        obj._parser = self._parser
        if stop is None: stop = _eggwrapper.UNKNOWN
        if start < 0: raise ValueError('invalid start value')
        if stop < start: raise ValueError('invalid stop value')
        ns = self._parser.num_samples()
        mask = 3
        if allow_indel: mask &= 2
        if allow_custom: mask &= 1
        obj._sld.setup(self._parser, size, step, start, stop, max_missing, mask)
        return obj

    def bed_slider(self, bed, max_missing=0, allow_indel=False, allow_custom=False):
        """
        Perform a sliding window based on BED coordinates.

        :param bed: an :class:`.io.BED` instance.
        :param max_missing: maximum number of missing alleles.

            .. warning::
                Here, *max_missing* must be an absolute number of
                samples.
        :param allow_indel: include variants with alleles of varying size.
        :param allow_custom: include variants with custom alleles.

        :return: An :class:`.io.VcfWindow` instance.

        .. versionchanged:: 3.2.0
            *max_missing* is required to be an integer.
        """
        if not self._parser.good(): raise ValueError('parser reached end of file')
        if not isinstance(max_missing, int): raise TypeError('`max_missing\' must be an integer')
        if max_missing > self._parser.num_samples(): raise ValueError('invalid value for `max_missing`')
        obj = VcfSlidingWindow.__new__(VcfSlidingWindow)
        obj._sld = _eggwrapper.VcfWindowBED()
        obj._wdw = VcfWindow.__new__(VcfWindow)
        obj._wdw._sld = obj._sld
        obj._wdw._parser = self
        obj._parser = self._parser
        ns = self._parser.num_samples()
        mask = 3
        if allow_indel: mask &= 2
        if allow_custom: mask &= 1
        obj._sld.setup(self._parser, bed._obj, max_missing, mask)
        obj._bed_reference = bed # keep a reference to BED slider to avoid intempestive garbage collection
        return obj

def make_vcf_index(fname, outname=None):
    """
    Create the index for a VCF file. 

    :param fname: name of a VCF file.
    :param outname: name of the index file. By default, use a default
        name. The default name is based on the VCF file name, stripping
        the extension only if it is vcf and appending the vcfi
        extension. Index files bearing this default name are
        automatically loaded if the corresponding VCF file is opened.
    """
    _parser = _eggwrapper.VcfParser()
    _parser.open_file(fname)
    if outname is None:
        outname = VcfParser._mk_index_fname(fname)
    _eggwrapper.make_vcf_index(_parser, outname)
    del _parser
    return outname

class VcfVariant(object):
    """
    Represent a single VCF variant.
    The user cannot create instances of this class himself
    (instances are generated by :class:`.io.VcfParser` or :class:`.io.VcfStringParser`).

    .. note::

        The ``AA`` (ancestral allele), ``AN`` (allele number),
        ``AC`` (allele count), and ``AF`` (allele frequency) INFO fields
        as well as the ``GT`` (deduced genotype) FORMAT are
        automatically extracted if they are present in the the file and
        if their definition matches the format specification (meaning
        that they were not re-defined with different number/type) in
        the header. If present, they are available through the dedicated
        attributes :py:obj:`~.io.VcfVariant.AN`, :py:obj:`~.io.VcfVariant.AA`,
        :py:obj:`~.io.VcfVariant.AC`, :py:obj:`~.io.VcfVariant.AF`,
        :py:obj:`~.io.VcfVariant.GT`, :py:obj:`~.io.VcfVariant.ploidy`
        and :py:obj:`~.io.VcfVariant.GT_phased`. However,
        they are also available in the respective
        :py:obj:`~.io.VcfVariant.info` and
        :py:obj:`~.io.VcfVariant.samples` (sub)-dictionaries.
    """

    # the following are provided for comparison to content of variant.alternate_types
    alt_type_default = _eggwrapper.Default #: Explicit alternate allele (the string represents the nucleotide sequence of the allele).
    alt_type_referred = _eggwrapper.Referred #: Alternate allele referring to a pre-defined allele (the string provides the ID of the allele).
    alt_type_breakend = _eggwrapper.Breakend #: Alternate allele symbolizing a breakend (see VCF description for more details).

    def __init__(self):
        raise NotImplementedError('cannot create `VcfVariant` instance')

    @staticmethod
    def _filter_missing(v, type_):
        if ((type_==int and v==_eggwrapper.MISSINGDATA) or
            (type_==float and v==_eggwrapper.UNDEF) or
            (type_==str and v[0]==_eggwrapper.MAXCHAR)): return None
        else: return v

    @classmethod
    def _make(cls, parser):
        if parser._parser.len_reference() == 0: raise ValueError('cannot generate `VcfVariant` instance: no VCF line has been parsed (or the length of the reference allele is null)')
        obj = cls.__new__(cls)

        # get chromosome
        obj._chrom = parser._parser.chromosome()
        if obj._chrom == '': obj._chrom = None

        # get position
        obj._pos = parser._position()
        if obj._pos == _eggwrapper.MISSING: obj._pos = None
        elif obj._pos == _eggwrapper.UNKNOWN: obj._pos = -1

        # get IDs
        obj._id = tuple(parser._parser.ID(i) for i in range(parser._parser.num_ID()))

        # get reference+alternate alleles
        obj._alleles = [parser._parser.reference()]
        if obj._alleles[0] == '': obj._alleles[0] = None
        obj._alternate_types = []
        obj._num_alternate = parser._parser.num_alternate()
        obj._num_alleles = obj._num_alternate + 1
        for i in range(obj._num_alternate):
            obj._alleles.append(parser._parser.alternate(i))
            obj._alternate_types.append(parser._parser.alternate_type(i))
        obj._alleles = tuple(obj._alleles)
        obj._alternate_types = tuple(obj._alternate_types)

        # get quality
        obj._quality = parser._parser.quality()
        if obj._quality == _eggwrapper.UNDEF: obj._quality = None

        # get test info
        n = parser._parser.num_failed_tests()
        if n == _eggwrapper.UNKNOWN: obj._failed_tests = None
        else: obj._failed_tests = tuple(parser._parser.failed_test(i) for i in range(n))

        # get info for the whole variant (site)
        obj._info = {}
        for i in range(parser._parser.num_FlagInfo()):
            item = parser._parser.FlagInfo(i)
            obj._info[item.get_ID()] = ()
        for i in range(parser._parser.num_IntegerInfo()):
            item = parser._parser.IntegerInfo(i)
            if item.get_expected_number() == 1:
                obj._info[item.get_ID()] = cls._filter_missing(item.item(0), int)
            else:
                obj._info[item.get_ID()] = tuple(cls._filter_missing(item.item(j), int) for j in range(item.num_items()))

        for i in range(parser._parser.num_FloatInfo()):
            item = parser._parser.FloatInfo(i)
            if item.get_expected_number() == 1:
                obj._info[item.get_ID()] = cls._filter_missing(item.item(0), float)
            else:
                obj._info[item.get_ID()] = tuple(cls._filter_missing(item.item(j), float) for j in range(item.num_items()))

        for i in range(parser._parser.num_CharacterInfo()):
            item = parser._parser.CharacterInfo(i)
            if item.get_expected_number() == 1:
                obj._info[item.get_ID()] = cls._filter_missing(item.item(0), str)
            else:
                obj._info[item.get_ID()] = tuple(cls._filter_missing(item.item(j), str) for j in range(item.num_items()))
        for i in range(parser._parser.num_StringInfo()):
            item = parser._parser.StringInfo(i)
            if item.get_expected_number() == 1:
                obj._info[item.get_ID()] = cls._filter_missing(item.item(0), str)
            else:
                obj._info[item.get_ID()] = tuple(cls._filter_missing(item.item(j), str) for j in range(item.num_items()))

        # get predefined AN/AA/AC/AF info fields if they are matching definition
        if parser._parser.has_AN(): obj._AN = parser._parser.AN()
        else: obj._AN = None
        if parser._parser.has_AA(): obj._AA = parser._parser.AA_string()
        else: obj._AA = None
        if parser._parser.has_AC(): obj._AC = tuple(parser._parser.AC(i) for i in range(parser._parser.num_AC()))
        else: obj._AC = None
        if parser._parser.has_AF(): obj._AF = tuple(parser._parser.AF(i) for i in range(parser._parser.num_AF()))
        else: obj._AF = None

        # pre-process the format column to allow match the ID's to the proper accessor method of SampleInfo
        fields = []
        for i in range(parser._parser.num_fields()):
            format_ = parser._parser.field(i)
            type_ = format_.get_type()
            if type_ == _eggwrapper.Info.String:
                f1 = _eggwrapper.SampleInfo.num_StringItems
                f2 = _eggwrapper.SampleInfo.StringItem
                t = str
            elif type_ == _eggwrapper.Info.Float:
                f1 = _eggwrapper.SampleInfo.num_FloatItems
                f2 = _eggwrapper.SampleInfo.FloatItem
                t = float
            elif type_ == _eggwrapper.Info.Integer:
                f1 = _eggwrapper.SampleInfo.num_IntegerItems
                f2 = _eggwrapper.SampleInfo.IntegerItem
                t = int
            elif type_ == _eggwrapper.Info.Character:
                f1 = _eggwrapper.SampleInfo.num_CharacterItems
                f2 = _eggwrapper.SampleInfo.CharacterItem
                t = str
            fields.append((
                format_.get_ID(), # the ID
                parser._parser.field_rank(i), # the index within range
                f1, # SampleInfo's method to get number of items
                f2, # SampleInfo's method to get a given item
                t   # type (required to convert missing data to None)
            ))
        obj._format_fields = frozenset(i[0] for i in fields)

        # get all SampleInfo data
        obj._num_samples = parser._parser.num_samples()
        obj._samples = []
        for sam in range(obj._num_samples):
            sample_info = parser._parser.sample_info(sam)
            sample_data = {}
            for ID, idx, f1, f2, t in fields:
                sample_data[ID] = (
                    None if f1(sample_info, idx)==0 else
                    tuple(cls._filter_missing(f2(sample_info, idx, i), t) for i in range(f1(sample_info, idx))))
                    # the above line get all items for a given FORMAT (using method pointers)
            obj._samples.append(sample_data)

        # get ploidy/num genotpes
        obj._ploidy = parser._parser.ploidy()
        obj._num_genotypes = parser._parser.num_genotypes()

        # get genotypes
        if parser._parser.has_GT():
            obj._gt = tuple(
                tuple((None if parser._parser.GT(i,j) == _eggwrapper.UNKNOWN
                            else obj._alleles[parser._parser.GT(i,j)])
                                    for j in range(obj._ploidy))
                                    for i in range(obj._num_samples))
            obj._gt_phased = tuple(parser._parser.GT_phased(i) for i in range(obj._num_samples))

            obj._gt_field = []
            gt_f = None
            for i in range(obj._num_samples):
                aa_f = []
                for j in range(obj._ploidy):
                    if parser._parser.GT(i,j) == _eggwrapper.UNKNOWN:
                        aa_f = None
                        break
                    else:
                        aa_f.append(parser._parser.GT(i,j))
                if aa_f is not None:
                    aa_fs = tuple(map(str, aa_f))
                    if not parser._parser.GT_phased(i):
                        gt_f = '/'.join(aa_fs)
                    else : gt_f = '|'.join(aa_fs)
                else:
                    gt_f = '.'
                obj._gt_field.append(gt_f)
            obj._gt_field= tuple(obj._gt_field)

        else:
            obj._gt = None
            obj._gt_phased = None

        # get PL
        if parser._parser.has_PL():
            obj._pl = tuple(
                    tuple(parser._parser.PL(i, j) for j in range(obj._num_genotypes))
                            for i in range(obj._num_samples))
        else:
            obj._pl = None

        # get GL
        if parser._parser.has_GL():
            obj._gl = tuple(
                    tuple(parser._parser.GL(i, j) for j in range(obj._num_genotypes))
                            for i in range(obj._num_samples))
        else:
            obj._gl = None


        return obj

    # block of accessors below: they don't DO anything (it's only doc who makes is cumbersome)
    chromosome = property(lambda self: self._chrom, doc='Chromosome name. ``None`` if missing.')
    position = property(lambda self: self._pos, doc='Position. Given as an index; first value is 0. ``None`` if missing.')
    ID = property(lambda self: self._id, doc='Tuple containing all IDs.')
    num_alleles = property(lambda self: len(self._alleles), doc='Number of alleles. The reference is always included.')
    num_alternate = property(lambda self: self._num_alternate, doc='Number of alternate alleles. Equal to :py:obj:`~.io.VcfVariant.num_alleles` minus 1.')
    alleles = property(lambda self: self._alleles, doc='Tuple of variant alleles. The first is the reference, which is not guaranteed to be present in samples.')
    alternate_types = property(lambda self: self._alternate_types, doc="""Alternate alleles types, as a tuple.\n
One value is provided for each alternate allele. The provided values are
integers whose values should always be compared to class attributes
:py:obj:`~.io.VcfVariant.alt_type_default`, :py:obj:`~.io.VcfVariant.alt_type_referred` and
:py:obj:`~.io.VcfVariant.alt_type_breakend`, as in (for the type of the first alternate
allele)::

    >>> type_ = variant.alternate_types[0]
    >>> if type_ == variant.alt_type_default:
    ...     allele = variant.allele(0)\n""")
    quality = property(lambda self: self._quality, doc='Variant quality. ``None`` if missing.')
    failed_tests = property(lambda self: self._failed_tests, doc='Filters at which this variant failed. Provided as a tuple or names, or ``None`` if no filters have been applied.')
    AA = property(lambda self: self._AA, doc='Value of the AA info field. ``None`` if missing.')
    AN = property(lambda self: self._AN, doc='Value of the AN info field. ``None`` if missing.')
    AC = property(lambda self: self._AC, doc='Value of the AC info field. Provided as a tuple. ``None`` if missing.')
    AF = property(lambda self: self._AF, doc='Value of the AF info field. Provided as a tuple. ``None`` if missing.')
    info = property(lambda self: self._info, doc="""Dictionary of INFO
fields for this variant. Keys are ID of INFO fields available for this
variant, and values are always a :class:`tuple` of items, even if there is only
one item. For flag INFO types,
the value is always an empty :class:`!tuple`.""")
    format_fields = property(lambda self: self._format_fields, doc='Frozenset of FORMAT fields ID\'s. The frozenset is empty if no sample data are available.')
    num_samples = property(lambda self: self._num_samples, doc='Number of samples. Equivalent to ``len(variant.samples)``.')
    samples = property(lambda self: self._samples, doc="""Information
for each sample. Empty list if no samples are
defined. Otherwise, the list contains one dictionary for each sample: keys of
these dictionaries are FORMAT fields identifiers (the keys are always the same as
the content of :py:obj:`~.io.VcfVariant.format_fields`), and their values are :class:`tuple` instances in
all cases.""")
    ploidy = property(lambda self: self._ploidy, doc='Ploidy among genotypes. Always 2 if GT is not available.')
    num_genotypes = property(lambda self: self._num_genotypes, doc='Number of genotypes.')
    GT_phased = property(lambda self: self._gt_phased, doc='Tell if the genotype for each sample is phased. ``None`` if GT is not available.')
    GT = property(lambda self: self._gt, doc="""Genotypes from GT
fields. Only if this format field is available. Provided as a :class:`tuple` of
sub-tuples. The number of sub-tuples is equal to the number of samples
(:py:obj:`~.io.VcfVariant.num_samples`). The number of items within each
sub-tuples is equal to the ploidy (:py:obj:`~.io.VcfVariant.ploidy`). These items are
allele expression (as found in :py:obj:`~.io.VcfVariant.alleles`), or ``None`` (for
missing values). This attribute is ``None`` if GT is not available.""")

    GT_vcf = property(lambda self: self._gt_field, doc = """GT field as written in the VCF file""")
    PL = property(lambda self: self._pl, doc = """PL values for all samples""")
    GL = property(lambda self: self._gl, doc = """GL values for all samples""")

class VcfSlidingWindow(object):
    """
    This class manages a sliding window on a VCF file.
    This class cannot be instanciated directly: instances are
    returned by the methods :meth:`~.io.VcfParser.slider` and
    :meth:`~.io.VcfParser.bed_slider` of :class:`.io.VcfParser`
    instances.

    :class:`.io.VcfSlidingWindow` instances are iterable:
    iteration steps return a common :class:`.io.VcfWindow` instance
    which is updated at each iteration round.
    """

    def __init__(self):
        raise NotImplementedError('cannot create `VcfSlidingWindow` instance')

    @property
    def good(self):
        """
        ``True`` if there is still data to be processed.
        """
        return self._sld.good()

    def __iter__(self):
        return self

    def __next__(self):
        if self._sld.good():
            self._sld.next_window()
            return self._wdw
        else: raise StopIteration

    next = __next__ # for python2

class VcfWindow(object):
    """
    Provide access to sites of a window from a VCF file. The following
    operations are supported by :class:`.io.VcfWindow` instances:

    +-----------------------------+------------------------------------------------+
    | Operation                   | Result                                         |
    +=============================+================================================+
    | ``len(win)``                | number of sites in the window                  |
    +-----------------------------+------------------------------------------------+
    | ``win[i]``                  | get a site as a :class:`.Site` instance        |
    +-----------------------------+------------------------------------------------+
    | ``for site in win:``        | iterate over sites as :class:`.Site` instances |
    +-----------------------------+------------------------------------------------+
    """

    def __init__(self):
        raise NotImplementedError('cannot create `VcfWindow` instance')

    num_sites = property(lambda self: self._sld.num_sites(), doc='Number of sites in window.')
    chromosome = property(lambda self: self._sld.chromosome(), doc='Name of the chromosome or contig.')

    @property
    def bounds(self):
        """Bounds of the window. The second bound is not included in the window."""
        return self._sld.win_start(), self._sld.win_stop()

    def __len__(self):
        return self._sld.num_sites()

    def __iter__(self):
        site = self._sld.first_site()
        while site is not None:
            yield _site.Site._from_site_holder(site.site(), alphabets.Alphabet._make(site.alphabet()) if site.alphabet() else alphabets.DNA)
            site = site.next()

    def __getitem__(self, idx):
        if idx < 0:
            idx = self._sld.num_sites() + idx
        if idx >= self._sld.num_sites() or idx < 0:
            raise ValueError('invalid site index')
        else:
            site = self._sld.get_site(idx)
            return _site.Site._from_site_holder(site.site(), alphabets.Alphabet._make(site.alphabet()) if site.alphabet() else alphabets.DNA)

class BED(object):
    """
    Class holding BED (Browser Extensible Data) data.

    :param fname: name of the BED-formatted input file. By default,
        create an empty instance.

    BED is a flexible format representing
    genomic annotation. In the current implementation, only the
    chromosome/scaffold, start, and end positions (the first three
    fields of each lines, which are the only ones to be required) are
    processed. If incorrectly formed fields are provided besides the
    first three fields, the behaviour is undefined (that is, it is not
    guaranteed that are exception is raised).

    Supported operations:

    +-------------------+----------------------------+-------+
    | Operation         | Result                     | Notes |
    +===================+============================+=======+
    | ``len(bed)``      | Number of annotation items |       |
    +-------------------+----------------------------+-------+
    | ``bed[i]``        | Get an annotation          | (1)   |
    +-------------------+----------------------------+-------+
    | ``for i in bed:`` | Iterate over annotations   | (1)   |
    +-------------------+----------------------------+-------+

    Notes:

    #. Annotation items are represented by dictionaries containing the
       following keys: ``"chrom"``, ``"start"``, and ``"end"``.
    """

    def __init__(self, fname=None):
        self._obj = _eggwrapper.BedParser()
        if fname is not None:
            self._obj.get_bed_file(fname)

    def __len__(self):
        return self._obj.n_bed_data()

    def __getitem__(self, i):
        if i < 0:
            i = self._obj.n_bed_data() + i
        if i < 0 or i >= self._obj.n_bed_data():
            raise IndexError('invalid BED index')
        return {'chrom': self._obj.get_chrom(i),
                'start': self._obj.get_start(i),
                'end': self._obj.get_end(i)}

    def extend(self, values):
        """
        Append items from an iterable. All items of *values*
        must be a sequence containing a
        value for *chrom*, *start*, and *end* (in that order).
        """
        for item in values:
            self.append(* item)

    def append(self, chrom, start, end):
        """
        Add an item at the end of the BED data.
        """
        self._obj.append(chrom, start, end)
