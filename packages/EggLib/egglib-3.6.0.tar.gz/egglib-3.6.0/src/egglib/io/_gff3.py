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

import re, operator, os, sys
from io import StringIO
from .. import eggwrapper as _eggwrapper
from .. import alphabets, _interface

_SOFA = {
    'SO:0000704': 'gene',
    'SO:0000234': 'mRNA',
    'SO:0000147': 'exon',
    'SO:0000316': 'cds',
    'SO:0000188': 'intron',
    'SO:0000610': 'polyA_sequence',
    'SO:0000553': 'polyA_site',
    'SO:0000204': 'five_prime_UTR',
    'SO:0000205': 'three_prime_UTR'
}

class GFF3(object):
    """
    Import GFF3 genome annotation data.
    Read General Feature Format (GFF)-formatted (version 3) genome
    annotation data from a file specified by name or from a provided
    string.

    See the description of the GFF3 format at `<http://www.sequenceontology.org/gff3.shtml>`_.

    All features are loaded into memory and can be processed interactively.

    :param source: name of a GFF3-formatted file. To pass a string,
        use the factory method :meth:`from_string`.
    :param strict: by default, apply strictly GFF3 requirements. See
        below.

    .. _gff3-strict:

    The ``strict`` argument can be set to ``False`` to support CDS
    features lacking a phase.

    Some observations regarding this implementation:

    * The validity of parent-child relationship with respect to the
      Sequence Ontology is not enforced, meaning that this parser
      allows any type of feature to be parent to any feature of any
      type.

    * The Sequence Ontology accession number of types of features related
      to genes are automatically mapped to the type name (such as
      "SO:0000704", which is translated as "gene").

    * Discontinuous features are required to have matching attributes
      (except start, stop, and phase for CDS features) but subsequent
      segments are allowed to skip attributes if the first
      segment defines them.

    * fasta-formatted sequences are imported but are currently not
      checked for consistency with annotations and defined sequence
      regions.

    :class:`.io.GFF3` instances are iterable. The expression:

    .. code-block:: python

        >>> for feat in GFF3:
        ...     ...

    is equivalent to:

    .. code-block:: python

        >>> for feat in GFF3.iter_features():
        ...     ...
    """

    @classmethod
    def from_string(cls, string, strict=True):
        """
        Import data from a GFF3-formatted string. This is a class method,
        which can be called as shown below to create a new object:

        .. code-block:: python

            >>> gff3 = egglib.io.GFF3.from_string(gff3_string)

        :param string: GFF3-formatted string.
        :param strict: apply strict GFF3 specifications (see :ref:`here <gff3-strict>`).
        :return: A new :class:`.io.GFF3` instance.

        """
        obj = cls.__new__(cls)
        obj._strict = strict
        obj._parse(StringIO(string))
        return obj

    def __init__(self, fname, strict=True):
        self._strict = strict
        f = open(fname, mode='r')
        self._parse(f)

    def _parse(self, f):  # read a file or file-like object
        # initialize parameters
        self._regions = {}
        self._feature_ontology = []
        self._attribute_ontology = []
        self._source_ontology = []
        self._species = None
        self._genome_build = None
        self._sequences = None
        self._seqid = []
        self._mapping = {}
        self._num_tot = 0
        self._num_top = 0
        self._IDs = set() # IDs of all features
        self._open_features = {} # only those with an ID
        self._version = None

        # read all lines
        self._lineno = 0
        self._f = f
        self._pos = self._f.tell()
        while True:
            self._line = f.readline()
            if self._line == '': break
            self._lineno += 1
            self._readline(self._line)
        self._close_objects()

        # sort features within seqid entries
        for key in self._mapping:
            self._mapping[key].sort(key=lambda feat: (feat.start, feat.end))
            for feat in self._mapping[key]:
                feat._descendants.sort(key=operator.attrgetter('start'))
                feat._all_parts.sort(key=operator.attrgetter('start'))

    def _readline(self, line): # process a line
        if line.rstrip() == '###': self._close_objects()
        elif line[0] == '>': self._get_sequences()
        elif line.rstrip() == '##FASTA':
            self._pos = self._f.tell()
            self._get_sequences()
        elif line[:2] == '##': self._get_directive()
        elif line[0] == '#': pass
        else: self._get_annotation()
        self._pos = self._f.tell()

    def _close_objects(self): # close all open features
        for ID, feat in self._open_features.items():
            feat._close()
        self._open_features.clear()

    def _process_text(self, text): # expand escape expressions
        for hit in set(re.findall('(%[0-9A-Fa-f]{2})', text)):
            text = text.replace(hit, chr(int('0x'+hit[1:], 16)))
        return text

    def _get_directive(self): # import a directive
        args = self._line.split()
        if args[0] == '##sequence-region':
            if len(args) != 4: raise ValueError('invalid sequence-region directive [line: {0}]'.format(self._lineno))
            seqid, start, end = args[1:]
            seqid = self._process_text(seqid)
            try:
                start = int(start) - 1
                end = int(end) - 1
            except ValueError: raise ValueError('invalid sequence-region directive [line: {0}]'.format(self._lineno))
            if start < 0 or end < start: raise ValueError('invalid sequence-region directive [line: {0}]'.format(self._lineno))
            if seqid in self._regions: raise ValueError('invalid sequence-region directive (seqid already defined) [line: {0}]'.format(self._lineno))
            self._regions[seqid] = start, end
        elif args[0] == '##feature-ontology':
            if len(args) != 2: raise ValueError('invalid feature-ontology directive [line: {0}]'.format(self._lineno))
            self._feature_ontology.append(self._process_text(args[1]))
        elif args[0] == '##attribute-ontology':
            if len(args) != 2: raise ValueError('invalid attribute-ontology directive [line: {0}]'.format(self._lineno))
            self._attribute_ontology.append(self._process_text(args[1]))
        elif args[0] == '##source-ontology':
            if len(args) != 2: raise ValueError('invalid source-ontology directive [line: {0}]'.format(self._lineno))
            self._source_ontology.append(self._process_text(args[1]))
        elif args[0] == '##species':
            if self._species is not None: raise ValueError('species directive repeateError(d [line: {0}]'.format(self._lineno))
            self._species = ' '.join(map(self._process_text, args[1:]))
        elif args[0] == '##genome-build':
            if len(args) != 3: raise ValueError('invalid genome-build directive [line: {0}]'.format(self._lineno))
            if self._genome_build is not None: raise ValueError('genome-build directive repeated [line: {0}]'.format(self._lineno))
            self._genome_build = tuple(map(self._process_text, args[1:]))
        elif args[0] == '##gff-version':
            if len(args) != 2: raise ValueError('invalid gff-version directive [line: {0}]'.format(self._lineno))
            if self._version is not None: raise ValueError('gff-version directive repeated [line: {0}]'.format(self._lineno))
            self._version = args[1]
        else:
            raise ValueError('invalid directive: {0} [line: {1}]'.format(args[0], self._lineno))

    def _get_annotation(self): # import an annotation feature

        # separate the 9 columns
        bits = self._line.rstrip().split('\t')
        if len(bits) != 9: raise ValueError('invalid annotation line [line: {0}]'.format(self._lineno))

        # seqid
        if bits[0] == '.': raise ValueError('invalid annotation line (seqid cannot be missing) [line: {0}]'.format(self._lineno))
        else: seqid = self._process_text(bits[0])

        # source
        if bits[1] == '.': source = None
        else: source = self._process_text(bits[1])

        # type
        if bits[2] == '.': raise ValueError('invalid annotation line: type must be defined [line: {0}]'.format(self._lineno))
        type_ = self._process_text(bits[2])
        type_ = _SOFA.get(type_, type_)

        # start and stop
        if bits[3] == '.': raise ValueError('invalid annotation line: start must be defined [line: {0}]'.format(self._lineno))
        if bits[4] == '.': raise ValueError('invalid annotation line: stop must be defined [line: {0}]'.format(self._lineno))
        try:
            start = int(bits[3]) - 1
            stop = int(bits[4]) - 1
        except ValueError: raise ValueError('invalid feature positions [line: {0}]'.format(self._lineno))
            # positions are checked later (after Is_circular can be detected)

        # score
        if bits[5] == '.': score = None
        else:
            try: score = float(bits[5])
            except ValueError: raise ValueError('invalid feature score [line: {0}]'.format(self._lineno))

        # strand
        strand = bits[6]
        if strand not in '+-.?': raise ValueError('invalid feature strand [line: {0}]'.format(self._lineno))
        if strand == '.': strand = None

        # phase
        phase = bits[7]
        if phase not in '.012': raise ValueError('invalid feature phase [line: {0}]'.format(self._lineno))
        if type_ == 'CDS':
            if phase == '.':
                if self._strict: raise ValueError('invalid feature: phase must be defined for CDS [line: {0}]'.format(self._lineno))
            else:
                phase = int(phase)
        else:
            if phase != '.' and type_ not in ['start_codon', 'stop_codon']:
                raise ValueError('invalid feature: phase must only be defined for CDS [line: {0}]'.format(self._lineno))
        if phase == '.': phase = None

        # attributes
        ID = None
        Name = None
        Alias = None
        Parent = None
        Target = None
        Gap = None
        Note = None
        Dbxref = None
        Ontology_term = None
        Derives_from = None
        Is_circular = None
        attributes = {}
        attrs = bits[8].split(';')
        for attr in attrs:
            if len(attr) == 0: continue
            if attr.count('=') != 1: raise ValueError('invalid attribute: {0} [line: {1}]'.format(attr, self._lineno))
            key, value = attr.split('=')
            if key[0].isupper():
                if key == 'ID':
                    if ID is not None: raise ValueError('invalid attribute: {0} (ID defined more than once) [line: {1}]'.format(attr, self._lineno))
                    ID = self._process_text(value)
                elif key == 'Name':
                    if Name is not None: raise ValueError('invalid attribute: {0} (Name defined more than once) [line: {1}]'.format(attr, self._lineno))
                    Name = self._process_text(value)
                elif key == 'Alias':
                    if Alias is not None: raise ValueError('invalid attribute: {0} (Alias defined more than once) [line: {1}]'.format(attr, self._lineno))
                    Alias = tuple(map(self._process_text, value.split(',')))
                elif key == 'Parent':
                    if Parent is not None: raise ValueError('invalid attribute: {0} (Parent defined more than once) [line: {1}]'.format(attr, self._lineno))
                    Parent = tuple(map(self._process_text, value.split(',')))
                elif key == 'Target':
                    if Target is not None: raise ValueError('invalid attribute: {0} (Target defined more than once) [line: {1}]'.format(attr, self._lineno))
                    bits = value.split()
                    if len(bits) < 3 or len(bits) > 4:
                        raise ValueError('invalid attribute: {0} [line: {1}]'.format(attr, self._lineno))
                    target_id = self._process_text(bits[0])
                    try:
                        target_start = int(bits[1]) - 1
                        target_end = int(bits[2]) - 1
                    except ValueError: raise ValueError('invalid attribute: {0} (invalid bounds) [line: {1}]'.format(attr, self._lineno))
                    if target_start < 0 or target_end < target_start:
                        raise ValueError('invalid attribute: {0} (invalid bounds) [line: {1}]'.format(attr, self._lineno))
                    if len(bits) == 3:
                        target_strand = '.'
                    else:
                        if bits[3] not in '+-':  raise ValueError('invalid attribute: {0} [line: {1}]'.format(attr, self._lineno))
                        target_strand = bits[3]
                    Target = (target_id, target_start, target_end, target_strand)
                elif key == 'Gap':
                    if Gap is not None: raise ValueError('invalid attribute: {0} (Gap defined more than once) [line: {1}]'.format(attr, self._lineno))
                    bits = value.split()
                    for bit in bits:
                        if re.match(r'[MIDFR]\d+$', bit) is None:
                            raise ValueError('invalid attribute: {0} (invalid CIGAR string) [line: {1}]'.format(attr, self._lineno))
                    Gap = value
                elif key == 'Derives_from':
                    if Derives_from is not None: raise ValueError('invalid attribute: {0} (Derives_from defined more than once) [line: {1}]'.format(attr, self._lineno))
                    Derives_from = self._process_text(value)
                elif key == 'Note':
                    if Note is not None: raise ValueError('invalid attribute: {0} (Note defined more than once) [line: {1}]'.format(attr, self._lineno))
                    Note = tuple(map(self._process_text, value.split(',')))
                elif key == 'Dbxref':
                    if Dbxref is not None: raise ValueError('invalid attribute: {0} (Dbxref defined more than once) [line: {1}]'.format(attr, self._lineno))
                    Dbxref = []
                    for v in value.split(','):
                        v = self._process_text(v)
                        if v.count(':') != 1: raise ValueError('invalid attribute: {0} [line: {1}]'.format(attr, self._lineno))
                        Dbxref.append(v)
                elif key == 'Ontology_term':
                    if Ontology_term is not None: raise ValueError('invalid attribute: {0} (Ontology_term defined more than once) [line: {1}]'.format(attr, self._lineno))
                    Ontology_term = []
                    for v in value.split(','):
                        v = self._process_text(v)
                        if v.count(':') != 1: raise ValueError('invalid attribute: {0} [line: {1}]'.format(attr, self._lineno))
                        Ontology_term.append(v)
                elif key == 'Is_circular':
                    if Is_circular is not None: raise ValueError('invalid attribute: {0} (Is_circular defined more than once) [line: {1}]'.format(attr, self._lineno))
                    if value.lower() == 'true': Is_circular = True
                    elif value.lower() == 'false': Is_circular = False
                    else: raise ValueError('invalid attribute: {0} [line: {1}]'.format(key, self._lineno))
                else:
                    raise ValueError('invalid attribute name: {0} [line: {1}]'.format(key, self._lineno))
            else:
                if key in attributes: raise ValueError('invalid attribute: {0} ({1} defined more than once) [line: {1}]'.format(attr, key, self._lineno))
                attributes[key] = self._process_text(value)

        # default value Is_circular
        if Is_circular is None: Is_circular = False

        # check bounds
        if stop < start: raise ValueError('invalid feature positions [line: {0}]'.format(self._lineno))
        if seqid in self._regions:
            if start < self._regions[seqid][0]: raise ValueError('invalid feature positions [line: {0}]'.format(self._lineno))
            if stop > self._regions[seqid][1] and not Is_circular: raise ValueError('invalid feature positions [line: {0}]'.format(self._lineno))

        if ID is not None:
            # check if new segment of an open feature
            if ID in self._open_features:
                f = self._open_features[ID]
                if seqid is not None and seqid != f._seqid: raise ValueError('invalid feature: mismatch of `seqid` between feature segments [line: {0}]'.format(self._lineno))
                if type_ is not None and type_ != f._type: raise ValueError('invalid feature: mismatch of `type` between feature segments [line: {0}]'.format(self._lineno))
                if score is not None and score != f._score: raise ValueError('invalid feature: mismatch of `score` between feature segments [line: {0}]'.format(self._lineno))
                if strand is not None and strand != f._strand: raise ValueError('invalid feature: mismatch of `strand` between feature segments [line: {0}]'.format(self._lineno))
                for k in attributes:
                    if k not in f.attributes or attributes[k] != f._attributes[k]:
                        if k in ['exon_number', 'exon_id']:
                            pass # ignore exon_number qualifier at the level of segment
                        else:
                            raise ValueError('invalid feature: mismatch of `{0}` between feature segments [line: {1}]'.format(k, self._lineno))
                f._add_segment(start, stop, phase)
                return

            # check that ID not duplicated
            if ID in self._IDs: raise ValueError('invalid feature: duplicated ID: {0} [line: {1}]'.format(ID, self._lineno))
            self._IDs.add(ID)

        # create new feature
        f = Gff3Feature._make(seqid=seqid, source=source, type_=type_,
            score=score, strand=strand, ID=ID, Name=Name, Alias=Alias,
            Parent=Parent, Target=Target, Gap=Gap,
            Derives_from=Derives_from, Note=Note, Dbxref=Dbxref,
            Ontology_term=Ontology_term, Is_circular=Is_circular,
            **attributes)
        f._add_segment(start, stop, phase)

        # connect to parents
        parents = []
        if Parent is not None:
            for p in Parent:
                if p not in self._open_features: raise ValueError('invalid feature: invalid parent ID: {0} (non-existing or closed feature) [line: {1}]'.format(p, self._lineno))
                parents.append(self._open_features[p])
        derives = []
        if Derives_from is not None:
            for d in Derives_from:
                if d not in self._open_features: raise ValueError('invalid feature: invalid `Derives_from` ID: {0} (non-existing or closed feature) [line: {1}]'.format(d, self._lineno))
                derives.append(self._open_features[d])
        f._connect(parents, derives)
        ultimate = []
        for parent in parents: parent._ultimate_parents(ultimate)
        for p in ultimate: p._all_parts.append(f)

        # add feature
        if ID is None: f._close()
        else: self._open_features[ID] = f
        self._num_tot += 1
        if len(parents) == 0:
            self._num_top += 1
            if seqid not in self._seqid:
                self._seqid.append(seqid)
                self._mapping[seqid] = []
            self._mapping[seqid].append(f)

    def _get_sequences(self): # import fasta-formatted sequences
        fp = _eggwrapper.FastaParser()
        try:
            fp.open_file(self._f.name, alphabets.DNA._obj, self._pos)
            self._f.seek(0, os.SEEK_END)
        except AttributeError:
            self._f.seek(self._pos)
            fp.set_string(self._f.read(), alphabets.DNA._obj)
        obj = _eggwrapper.DataHolder()
        fp.read_all(False, obj)
        self._sequences = _interface.Container._create_from_data_holder(obj, alphabets.DNA)

    @property
    def version(self):
        """GFF version."""
        return self._version

    @property
    def regions(self):
        """Dictionary with all sequence regions defined by directives."""
        return self._regions

    @property
    def feature_ontology(self):
        """Content of all feature-ontology directives."""
        return self._feature_ontology

    @property
    def attribute_ontology(self):
        """Content of all attribute-ontology directives."""
        return self._attribute_ontology

    @property
    def source_ontology(self):
        """Content of all source-ontology directives."""
        return self._source_ontology

    @property
    def species(self):
        """Species (if specified by a directive)."""
        return self._species

    @property
    def genome_build(self):
        """Genome build if specified by a directive."""
        return self._genome_build

    @property
    def sequences(self):
        """
        If specified, sequences as a :class:`.Container`. By default,
        this value is ``None``.
        """
        return self._sequences

    @property
    def num_seqid(self):
        """Number of seqid of features present in instance."""
        return len(self._seqid)

    @property
    def list_seqid(self):
        """List of seqid."""
        return self._seqid

    @property
    def num_top_features(self):
        """Number of features without parents."""
        return self._num_top

    @property
    def num_tot_features(self):
        """Total number of features."""
        return self._num_tot

    def __iter__(self):
        return Iterator(self, None, None, None, False)

    def iter_features(self, seqid=None, start=None, end=None, all_features=False):
        """
        Iterate over features.

        :param seqid: only iterates overs features of this contig (by
            default, consider all contigs). If the specified seqid is not
            present in the GFF3 file, iteration is empty (without error).
        :param start: start iteration at this position. By default,
            start with the first position.
        :param end: stop iteration at this position (does not include
            features whose end position is larger than this value). By
            default, process all features.
        :param all_features: whether iteration should also include
            features that are part of another (by default, only include
            features that don't have a parent). A given feature may be
            repeated if it has several unconnected parents.

        .. note::
            If *start* and/or *end* are specified, *seqid* is required.
        """
        return Iterator(self, seqid, start, end, all_features)

class Iterator(object):
    def __init__(self, obj, seqid, start, end, all_features):

        # check that bounds are used only for one seqid
        if (start is not None or end is not None) and seqid is None:
            raise ValueError('if start/end are specified, seqid must be specified')
        if start is None: start = 0
        if end is None: end = _eggwrapper.MAX
        self._obj = obj
        self._end = end

        # get list of seqid to process
        if seqid is None: self._seqid = obj._seqid
        elif seqid not in obj._seqid: self._seqid = []
        else: self._seqid = [seqid]
        self._idx_seq = 0
        if len(self._seqid) == 0:
            self._next = self._nextD
            return

        # set to the start position
        if start > 0:
            if all_features:
                for self._idx_top in range(len(obj._mapping[self._seqid[0]])):
                    for self._idx_part in range(len(obj._mapping[self._seqid[0]][self._idx_top].all_parts)):
                        if obj._mapping[self._seqid[0]][self._idx_top].all_parts[self._idx_part].start >= start: break
                    else: continue # no part has been found: check next top feature
                    break # a part has been found
                else: # no features found after the start position
                    self._next = self._nextD
            else:
                for self._idx_top in range(len(obj._mapping[self._seqid[0]])):
                    if obj._mapping[self._seqid[0]][self._idx_top].start >= start: break
                else: # no features found after the start position
                    self._next = self._nextD
        else:
            self._idx_top = 0
            self._idx_part = 0

        if all_features:
            self._next = self._nextAF
        else:
            self._next = self._nextTF

    def __iter__(self):
        return self

    def __next__(self):
        return self._next()

    next = __next__

    def _nextD(self):
        raise StopIteration

    def _nextAF(self):
        if self._idx_seq == len(self._seqid): raise StopIteration
        feats = self._obj._mapping[self._seqid[self._idx_seq]]
        if self._idx_top == len(feats):
            self._idx_seq += 1
            self._idx_top = 0
            return self._nextAF()
        if feats[self._idx_top].start > self._end: raise StopIteration
        if self._idx_part == len(feats[self._idx_top].all_parts):
            self._idx_top += 1
            self._idx_part = 0
            return self._nextAF()
        self._idx_part += 1
        if feats[self._idx_top].all_parts[self._idx_part-1].end <= self._end:
            return feats[self._idx_top].all_parts[self._idx_part-1]
        return self._nextAF()

    def _nextTF(self):
        if self._idx_seq == len(self._seqid): raise StopIteration
        feats = self._obj._mapping[self._seqid[self._idx_seq]]
        if self._idx_top == len(feats):
            self._idx_seq += 1
            self._idx_top = 0
            return self._nextTF()
        if feats[self._idx_top].end > self._end: raise StopIteration # necessarily finished because there must be only one seqid
        self._idx_top += 1
        return feats[self._idx_top-1]

class Gff3Feature(object):
    """
    Provide access to data of a feature. This class cannot be instanciated
    by the user.
    """
    def __init__(self):
        raise ValueError('Gff3Feature instances cannot be created directly')

    @classmethod
    def _make(cls, seqid, source, type_, score, strand, ID, Name,
                 Alias, Parent, Target, Gap, Derives_from, Note,
                 Dbxref, Ontology_term, Is_circular, **attrs):
        obj = Gff3Feature.__new__(cls)
        obj._seqid = seqid
        obj._type = type_
        obj._score = score
        obj._source = source
        obj._strand = strand
        obj._ID = ID
        obj._attributes = {'ID': ID, 'Name': Name, 'Alias': Alias,
            'Parent': Parent, 'Target': Target, 'Gap': Gap,
            'Derives_from': Derives_from, 'Note': Note,
            'Dbxref': Dbxref, 'Ontology_term': Ontology_term,
            'Is_circular': Is_circular}
        obj._attributes.update(attrs)
        obj._start = None
        obj._end = None
        obj._segments = []
        obj._descendants = []
        obj._all_parts = [obj]
        obj._derivers = []
        return obj

    @property
    def seqid(self):
        """Seqid on which this feature is located."""
        return self._seqid

    @property
    def type(self):
        """Feature type."""
        return self._type

    @property
    def score(self):
        """Feature score."""
        return self._score

    @property
    def source(self):
        """Feature source."""
        return self._source

    @property
    def strand(self):
        """Strand on which the feature is located."""
        return self._strand

    @property
    def ID(self):
        """Feature identifier."""
        return self._ID

    @property
    def attributes(self):
        """
        Dictionary of attributes attached to the feature.
        The list of attributes is:

        * ID
        * Name
        * Alias
        * Parent
        * Target
        * Gap
        * Derives_from
        * Note
        * Dbxref
        * Ontology_term
        * Is_circular
        * Other attributes as defined in the GFF3 file.
        """
        return self._attributes

    @property
    def start(self):
        """Feature start position."""
        return self._start

    @property
    def end(self):
        """Feature end position."""
        return self._end

    @property
    def segments(self):
        """List of segments of the feature."""
        return self._segments

    @property
    def parents(self):
        """List of features parent to this one."""
        return self._parents

    @property
    def descendants(self):
        """List of features descending from this one."""
        return self._descendants

    @property
    def all_parts(self):
        """All parts of this feature."""
        return self._all_parts

    @property
    def derivers(self):
        """List of features deriving from this one."""
        return self._derivers

    def _add_segment(self, start, end, phase):
        # Add a segment to the feature. Assume that start <= end. The
        # segments can be loaded in any order. Segments are not allowed to
        # overlap. They are sorted when _close() is called.
        self._segments.append((start, end, phase))

    def _connect(self, parents, derives):
        # Connect this feature to parents or other features from which it
        # derives.
        self._parents = parents
        self._derives_from = derives
        for i in self._parents: i._descendants.append(self)
        for i in self._derives_from: i._derivers.append(self)

    def _ultimate_parents(self, dest):
        # Return the list of ultimate parents.
        if len(self._parents) == 0: dest.append(self)
        else:
            for p in self._parents: p._ultimate_parents(dest)

    def _close(self):
        # Terminate loading of segments in the instance.
        if len(self._segments) == 0: raise ValueError('feature without segments')
        self._segments.sort(key=operator.itemgetter(0))
        for i in range(1, len(self._segments)):
            if self._segments[i-1][1] >= self._segments[i][0]: raise ValueError(f'feature segments are overlapping: {self._attributes["ID"]}')
        self._start = self._segments[0][0]
        self._end = self._segments[-1][1]
