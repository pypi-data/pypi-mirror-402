"""
    Copyright 2009-2023 Stephane De Mita, Mathieu Siol, Thomas Coudoux

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

# cf: https://www.ncbi.nlm.nih.gov/books/NBK279684/
# see also: https://doctorlib.info/medical/blast/7.html (checked for strands)

import subprocess, os, collections, sys
import xml.etree.ElementTree
from .. import _interface, alphabets
from ..tools import _code_tools
from . import _utils

class _BLAST_tool(_utils._App):
    def _check_path(self, path, cfg):
        cmd = (path, '-version')
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = p.communicate()
            if len(stderr): return stderr
        except OSError as e:
            return e.strerror

_blast_apps = {}
for k in 'makeblastdb', 'blastn', 'blastp', 'blastx', 'tblastn', 'tblastx':
    _blast_apps[k] = _BLAST_tool(key=k, default=k)
    _utils.paths._add(_blast_apps[k])

def makeblastdb(source, dbtype=None, out=None, input_type="fasta", verbose=False,
    title=None, parse_seqids=False, hash_index=False, mask_data=None, mask_id=None,
    mask_desc=None, blastdb_version=5,
    max_file_sz="1GB", taxid=None, taxid_map=None):
    """
    Create a BLAST database.

    :param source: name of an input file of the appropriate format.
        If not fasta, the format must be specified using the *input_type*
        option. Alternatively, *source* can be a :class:`.Container` or
        :class:`.Align` instance. If so, its alphabet must be DNA or protein
        and the *dbtype* argument, if specified, must match. Note that
        passing a :class:`!Container` or :class:`!Align` instance must be
        avoided for large databases.

    :param dbtype: database type: ``"nucl"`` or ``"prot"`` are acceptable. Can
        be omitted if a :class:`!Container` or an :class:`!Align` is provided
        as *source*.

    :param out: database name. Must be specified if a :class:`!Container`
        or an :class:`!Align` is provided as *source*, or if the *input_type*
        is "blastdb", otherwise the input file name is used as database name.

    :param input_type: format of input file. Must be ``"fasta"`` if
        a :class:`!Container` or an :class:`!Align` is provided as *source*.
        Otherwise must describe the format of *source*: ``"fasta"``, ``"asn1_bin"``,
        ``"asn1_txt"``, or ``"blastdb"``.

    :param verbose: display makeblastdb output (by default, it is returned
        by the function). Errors are always displayed.

    :param title: database title. A default title is inserted in case a
        :class:`!Container` or :class:`!Align` instance is passed as *source*.

    :parse_seqids: parse seqid from sequence names (considered if `input_type` is fasta,
        including if a :class:`!Container` or an :class:`!Align` is provided
        as *source*; argument ignored otherwise: seqid is always imported).

    :hash_index: create index of sequence hash values.

    :mask_data: list of input files containing masking data.

    :mask_id: list of strings to uniquely identify the masking algorithm,
              one for each mask file (requires *mask_data*).

    :mask_desc: list of free form strings to describe the masking algorithm
                details, one for each mask file (requires *mask_id*).

    :blastdb_version: version of BLAST database to be created (4 or 5).

    :max_file_sz: maximum file size for BLAST database files.

    :taxid: taxonomy ID to assign to all sequences as an integer
            (incompatible with *taxid_map*).

    :taxid_map: text file mapping sequence IDs to taxonomy IDs
            (requires *parse_seqids*, incompatible with *taxid*).

    :return: Standard output of the program (`None` if *verbose* was ``True``).

    Please refer to the manual of BLAST tools for more details.

    .. versionchanged 3.2::
        *blastdb_version* default value was previously 4. *gi_mask* and
        *gi_mask_name* options are removed.
    """

    # get command name
    path = _blast_apps['makeblastdb'].get_path()
    if path is None:
        raise RuntimeError('makeblastdb program not available -- please configure path')
    cmd = [path]

    # process main arguments arguments
    if isinstance(source, (_interface.Container, _interface.Align)):
        cmd.extend(['-in', '-'])
        if source.alphabet == alphabets.DNA and (dbtype is None or dbtype == 'nucl'): cmd.extend(['-dbtype', 'nucl'])
        elif source.alphabet == alphabets.protein and (dbtype is None or dbtype == 'prot'): cmd.extend(['-dbtype', 'prot'])
        else: raise ValueError('invalid alphabet, dbtype or alphabet/dbtype mismatch')
        if input_type != 'fasta': raise ValueError('`input_type` must be "fasta"')
        if out is None: raise ValueError('`out` is required if an object is passed as `source`')
        cmd.extend(['-input_type', 'fasta'])
        if title is None: title = '{0} database from an EggLib {1}'.format(cmd[4], 'Container' if isinstance(source, _interface.Container) else 'Align')
    else:
        if not isinstance(source, (os.PathLike, str)): raise TypeError('`source` must be a file name, a Container or an Align')
        if input_type != 'blastdb' and not os.path.isfile(source): raise ValueError('file not found: {0}'.format(source))
        if dbtype is None: raise ValueError('`dbtype` is required')
        if dbtype not in ['nucl', 'prot']: raise ValueError('invalid value for `dbtype`')
        if input_type not in ['fasta', 'asn1_bin', 'asn1_txt', 'blastdb']: raise ValueError('invalid value for `input_type`')
        if input_type == 'blastdb' and out is None or out == source: raise ValueError('a different database name is required for input type `blastdb`')
        cmd.extend(['-in', source, '-dbtype', dbtype, '-input_type', input_type])
    if out is not None:
        if not isinstance(out, (os.PathLike, str)): raise TypeError('`out` must be a string or a path-like object')
        cmd.extend(['-out', out])

    # check types of other arguments
    if not isinstance(blastdb_version, int): raise TypeError('`blastdb_version` must be an integer')
    if blastdb_version not in [4, 5]: raise ValueError('supported values for `blastdb_version` are 4 and 5 only')
    if not isinstance(max_file_sz, str): raise TypeError('`max_file_sz` must be a string')
    if title is not None and not isinstance(title, str): raise TypeError('`title` must be a string')
    if not isinstance(parse_seqids, bool): raise TypeError('`parse_seqids` must be a boolean')
    if input_type != 'fasta': parse_seqids = True
    if not isinstance(hash_index, bool): raise TypeError('`hash_index` must be a boolean')
    if mask_data is not None:
        if not isinstance(mask_data, (list, tuple)): raise TypeError('`mask_data` must be a list or a tuple')
        if not all([isinstance(item, str) for item in mask_data]): raise TypeError('`mask_data` items must be strings')
        if not all(map(os.path.isfile, mask_data)): raise ValueError('at least one file specified in `mask_data` does not exist')
        if len(mask_data) == 0: raise ValueError('there must be at least one item in `mask_data`')
    if mask_id is not None:
        if not isinstance(mask_id, (list, tuple)): raise TypeError('`mask_id` must be a list or a tuple')
        if not all([isinstance(item, str) for item in mask_id]): raise TypeError('`mask_id` items must be strings')
    if mask_desc is not None:
        if not isinstance(mask_desc, (list, tuple)): raise TypeError('`mask_desc` must be a list or a tuple')
        if not all([isinstance(item, str) for item in mask_desc]): raise TypeError('`mask_desc` items must be strings')
    if taxid is not None:
        if not isinstance(taxid, int): raise TypeError('`taxid` must be an integer')
        if taxid < 0: raise ValueError('`taxid` must be >= 0')
    if taxid_map is not None:
        if not isinstance(taxid_map, (str, os.PathLike)): raise TypeError('`taxid_map` must be a string or pathlike object')
        if not os.path.isfile(taxid_map): raise ValueError('file passed for `taxid_map` not found: {0}'.format(taxid_map))

    # check compatibility of other arguments
    if mask_id is not None:
        if mask_data is None: raise ValueError('`mask_id` requires `mask_data`')
        if len(mask_id) != len(mask_data): raise ValueError('`mask_id` must have the same length than `mask_data`')
    if mask_desc is not None:
        if mask_id is None: raise ValueError('`mask_desc` requires `mask_id`')
        if len(mask_desc) != len(mask_data): raise ValueError('`mask_desc` must have the same length than `mask_data`')
    if taxid is not None and taxid_map is not None: raise ValueError('`taxid` and `taxid_map` are incompatible')
    if taxid_map is not None and not parse_seqids: raise ValueError('`taxid_map` requires `parse_seqids`')

    # load the options
    if title is not None: cmd.extend(['-title', title])
    if parse_seqids: cmd.append('-parse_seqids')
    if hash_index: cmd.append('-hash_index')
    if mask_data is not None: cmd.extend(['-mask_data', ','.join(mask_data)])
    if mask_id is not None: cmd.extend(['-mask_id', ','.join(mask_id)])
    if mask_desc is not None: cmd.extend(['-mask_desc', ','.join(mask_desc)])
    cmd.extend(['-blastdb_version', str(blastdb_version), '-max_file_sz', max_file_sz])
    if taxid: cmd.extend(['-taxid', str(taxid)])
    if taxid_map: cmd.extend(['-taxid_map', taxid_map])

    # run the program
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
            stdout=None if verbose else subprocess.PIPE,
            stderr=subprocess.PIPE, universal_newlines=True)
    if isinstance(source, (_interface.Container, _interface.Align)): stdin = source.fasta()
    else: stdin = None
    stdout, stderr = p.communicate(stdin)
    if p.returncode != 0:
        raise RuntimeError('error while running makeblastdb (message below)\n' + stderr)
    return stdout

_blastn_costs = {
        # r/p     default, allowed
        (1,-2): ( (5,2),   [(5,2), (2,2), (1,2), (0,2), (3,1), (2,1), (1,1)] ),
        (1,-3): ( (5,2),   [(5,2), (2,2), (1,2), (0,2), (2,1), (1,1)] ),
        (1,-4): ( (5,2),   [(5,2), (1,2), (0,2), (2,1), (1,1)] ),
        (2,-3): ( (5,2),   [(4,4), (2,4), (0,4), (3,3), (6,2), (5,2), (4,2), (2,2)] ),
        (4,-5): ( (12,8),  [(12,8), (6,5), (5,5), (4,5), (3,5)] ),
        (1,-1): ( (5,2),   [(5,2), (3,2), (2,2), (1,2), (0,2), (4,1), (3,1), (2,1)] )}

_blastp_costs = {
    'BLOSUM62': [(32767, 32767), (11, 2), (10, 2), (9, 2), (8, 2), (7, 2),
                        (6, 2), (13, 1), (12, 1), (11, 1), (10, 1), (9, 1)],

    'BLOSUM80': [(32767, 32767), (25, 2), (13, 2), (9, 2), (8, 2), (7, 2),
                        (6, 2), (11, 1), (10, 1), (9, 1)],

    'PAM30': [(32767, 32767), (7, 2), (6, 2), (5, 2), (10, 1), (9, 1),
                        (8, 1), (15, 3), (14, 2), (14, 1), (13, 3)],

    'PAM70': [(32767, 32767), (8, 2), (7, 2), (6, 2), (11, 1), (10, 1),
                        (9, 1), (11, 2), (12, 3)]
}

_blastp_costs_defaults = {
    'BLOSUM62': (11, 1),
    'BLOSUM80': (10, 1),
    'PAM70': (10, 1),
    'PAM30': (9, 1)
}

def megablast(query, db=None, subject=None, query_loc=None,
        subject_loc=None, evalue=10, parse_deflines=False,
        num_threads=1, word_size=28, gapopen=5, gapextend=2, reward=1,
        penalty=-2, strand='both', no_dust=False, no_soft_masking=False,
        lcase_masking=False, perc_identity=0, no_greedy=False):
    """
    ``megablast`` similarity search. This is designed for strongly similar
    sequences using a nucleotide query on a nucleotide database.

    .. include:: blast_options_common
    .. include:: blast_options_blastn
    :return: A :class:`.BlastOutput` instance.

    """
    return _blastn(query, db, subject, 'megablast', query_loc,
                subject_loc, evalue, parse_deflines, num_threads,
                word_size, gapopen, gapextend, reward, penalty, strand,
                no_dust, no_soft_masking, lcase_masking, perc_identity,
                None, None, no_greedy)

def dc_megablast(query, db=None, subject=None, query_loc=None,
        subject_loc=None, evalue=10, parse_deflines=False,
        num_threads=1, word_size=11, gapopen=None, gapextend=None, reward=2,
        penalty=-3, strand='both', no_dust=False, no_soft_masking=False,
        lcase_masking=False, perc_identity=0, template_type='coding',
        template_length=18):
    """
    Dicontinuous ``megablast`` similarity search. This is designed for similar
    sequences (less similar than :func:`.megablast`) using a nucleotide
    query on a nucleotide database.

    .. include:: blast_options_common
    .. include:: blast_options_blastn
    :param template_type: template type for for dc-megablast. Possible
        values are ``"coding"`` (default), ``"optimal"``, and ``"coding_and_optimal"``.
    :param template_length: template length for dc-megablast. Possible
        values are 16, 18 (the default), and 21.
    """
    return _blastn(query, db, subject, 'dc-megablast', query_loc,
               subject_loc, evalue,parse_deflines, num_threads,
               word_size, gapopen, gapextend, reward, penalty, strand,
               no_dust, no_soft_masking, lcase_masking, perc_identity,
               template_type, template_length, False)

def blastn(query, db=None, subject=None, query_loc=None,
        subject_loc=None, evalue=10, parse_deflines=False,
        num_threads=1, word_size=11, gapopen=None, gapextend=None, reward=2,
        penalty=-3, strand='both', no_dust=False, no_soft_masking=False,
        lcase_masking=False, perc_identity=0):
    """
    ``blastn`` similarity search. This is designed for distant sequences using a
    nucleotide query on a nucleotide database.

    .. include:: blast_options_common
    .. include:: blast_options_blastn
    :return: A :class:`BlastOutput` instance.
    """
    return _blastn(query, db, subject, 'blastn', query_loc, subject_loc,
               evalue, parse_deflines, num_threads, word_size, gapopen,
               gapextend, reward, penalty, strand, no_dust,
               no_soft_masking, lcase_masking, perc_identity, None,
               None, False)

def blastn_short(query, db=None, subject=None, query_loc=None,
        subject_loc=None, evalue=1000, parse_deflines=False,
        num_threads=1, word_size=7, gapopen=None, gapextend=None, reward=1,
        penalty=-3, strand='both', no_dust=True, no_soft_masking=True,
        lcase_masking=False, perc_identity=0):
    """
    ``blastn`` for short sequences. This is optimised for query sequences
    up to 50 bp long. It automatically sets ``evalue=1000``, ``word_size=7``,
    ``no_dust=True``, ``no_soft_masking=True``, ``reward=1``, ``penalty=-3``,
    ``gapopen=5`` and ``gapextend=2``.

    .. include:: blast_options_common
    .. include:: blast_options_blastn
    :return: A :class:`BlastOutput` instance.
    """
    return _blastn(query, db, subject, 'blastn-short', query_loc,
               subject_loc, evalue, parse_deflines, num_threads,
               word_size, gapopen, gapextend, reward, penalty, strand,
               no_dust, no_soft_masking, lcase_masking, perc_identity,
               None, None, False)

@_utils._protect_run
def _blastn(query, db, subject, task, query_loc, subject_loc, evalue,
    parse_deflines, num_threads, word_size, gapopen, gapextend, reward,
    penalty, strand, no_dust, no_soft_masking, lcase_masking,
    perc_identity, template_type, template_length, no_greedy):

    cmd, stdin = _get_common_blast_options('blastn', query, db, subject,
                        query_loc, subject_loc, evalue, parse_deflines, num_threads)

    # process task
    cmd.extend(['-task', task])

    # word size
    if not isinstance(word_size, int): raise TypeError('`word_size` must be an integer')
    if task == 'megablast' and word_size < 4: raise ValueError('invalid value for `word_size`: must be >= 4 for megablast')
    if task == 'dc-megablast' and word_size not in [11, 12]: raise ValueError('invalid value for `word_size`: must be 11 or 12 for dc-megablast')
    if task == 'blastn' and word_size < 4: raise ValueError('invalid value for `word_size`: must be >= 4 for blastn')
    if task == 'blastn-short' and word_size < 4: raise ValueError('invalid value for `word_size`: must be >= 4 for blastn-short')
    cmd.extend(['-word_size', str(word_size)])

    # reward/penalty
    if not isinstance(reward, int): raise TypeError('`reward` must be an integer')
    if reward < 0: raise ValueError('`reward` must be >= 0')
    if not isinstance(penalty, int): raise TypeError('`penalty` must be an integer')
    if penalty > 0: raise ValueError('`penalty` must be <= 0')
    if (reward, penalty) not in _blastn_costs:
        raise ValueError('invalid set of values for reward/penalty: ({0},{1})'.format(reward, penalty))

    # gap costs
    if gapopen is None:
        if gapextend is not None: raise ValueError('if `gapopen` is ``None``, `gapextend` should be also')
        gapopen, gapextend = _blastn_costs[(reward, penalty)][0]
    elif gapextend is None:
        raise ValueError('if `gapextend` is ``None``, `gapopen` should be also')

    if not isinstance(gapopen, int): raise TypeError('`gapopen` must be an integer')
    if gapopen < 0: raise ValueError('`gapopen` must be >= 0')
    if not isinstance(gapextend, int): raise TypeError('`gapextend` must be an integer')
    if gapextend < 0: raise ValueError('`gapextend` must be >= 0')
    if (gapopen, gapextend) not in _blastn_costs[(reward, penalty)][1]:
        raise ValueError('invalid set of values for gapopen/gapextend: ({0},{1})'.format(gapopen, gapextend))
    cmd.extend(['-gapopen', str(gapopen), '-gapextend', str(gapextend),
                '-reward', str(reward), '-penalty', str(penalty)])

    # strand
    if not isinstance(strand, str): raise TypeError('`strand` must be a string')
    if strand not in ['both', 'minus', 'plus']: raise ValueError('`strand` must be either "both", "minus", or "plus"')
    cmd.extend(['-strand', strand])

    # filter/mask flags
    if no_dust: cmd.extend(['-dust', 'no'])
    if no_soft_masking: cmd.extend(['-soft_masking', 'false'])
    if lcase_masking: cmd.append('-lcase_masking')

    #  perc_identity
    if not isinstance(perc_identity, int): raise TypeError('`perc_identity` must be an integer')
    if perc_identity < 0 or perc_identity > 100: raise ValueError('`perc_identity` out of range')
    cmd.extend(['-perc_identity', str(perc_identity)])

    # template parameters
    if task == 'dc-megablast':
        if not isinstance(template_type, str): raise TypeError('`template_type` must be a string')
        if template_type not in ['coding', 'optimal', 'coding_and_optimal']: raise ValueError('invalid value for `template_type`')
        if not isinstance(template_length, int): raise TypeError('`template_length` must be an integer')
        if template_length not in [16, 18, 21]: raise ValueError('invalid value for `template_length`')
        cmd.extend(['-template_type', template_type])
        cmd.extend(['-template_length', str(template_length)])

    # aligment flags
    if no_greedy: cmd.append('-no_greedy')

    # run the program
    p = subprocess.Popen(cmd, stdin=None if stdin is None else subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = p.communicate(stdin)
    if p.returncode != 0:
        raise RuntimeError('error while running blastn (message below)\n' + stderr)
    return _parse_blast_output(stdout)

def blastp(query, db=None, subject=None, query_loc=None, subject_loc=None,
        evalue=10, parse_deflines=False, num_threads=1, word_size=None,
        gapopen=None, gapextend=None, matrix='BLOSUM62', threshold=11,
        comp_based_stats=2, seg=0, soft_masking=False,
        lcase_masking=False, window_size=40, use_sw_tback=False):
    """
    ``bastp`` similary search. This is designed for using a protein query
     on a protein database.

    .. include:: blast_options_common
    .. include:: blast_options_prot

    :param parse_deflines: parse query and subject bar delimited
        sequence identifiers.
    :param comp_based_stats: composition-based statistics, as an integer
        code: 0 (no composition-based statistics), 1 (composition-based
        statistics as in NAR 29:2994-3005, 2001), 2 (composition-based
        score adjustment as in Bioinformatics 21:902-911, 2005,
        conditioned on sequence properties), or 3 (composition-based
        score adjustment as in Bioinformatics 21:902-911, 2005,
        unconditionally).
    :param soft_masking: apply filtering locations as soft masks.
    :param lcase_masking: use lower case filtering in query and subject
        sequences.
    :param use_sw_tback: compute locally optimal Smith-Waterman
        alignments.

    :return: A :class:`BlastOutput` instance.
    """
    return _blastp(query, db, subject, 'blastp', query_loc, subject_loc,
        evalue, parse_deflines, num_threads, word_size, gapopen,
        gapextend, matrix, threshold, comp_based_stats, seg,
        soft_masking, lcase_masking, window_size, use_sw_tback)

def blastp_short(query, db=None, subject=None, query_loc=None,
        subject_loc=None, evalue=10, parse_deflines=False,
        num_threads=1, word_size=None, gapopen=None, gapextend=None,
        matrix='PAM30', threshold=16, comp_based_stats=0, seg=0,
        lcase_masking=False, window_size=15, use_sw_tback=False):
    """
    ``blastp`` similarity search for short sequences.

    .. include:: blast_options_common
    .. include:: blast_options_prot

    :param parse_deflines: parse query and subject bar delimited
        sequence identifiers.
    :param comp_based_stats: composition-based statistics, as an integer
        code: 0 (no composition-based statistics), 1 (composition-based
        statistics as in NAR 29:2994-3005, 2001), 2 (composition-based
        score adjustment as in Bioinformatics 21:902-911, 2005,
        conditioned on sequence properties), or 3 (composition-based
        score adjustment as in Bioinformatics 21:902-911, 2005,
        unconditionally).
    :param lcase_masking: use lower case filtering in query and subject
        sequences.
    :param use_sw_tback: compute locally optimal Smith-Waterman
        alignments.

    :return: A :class:`BlastOutput` instance.
    """
    return _blastp(query, db, subject, 'blastp-short', query_loc, subject_loc,
        evalue, parse_deflines, num_threads, word_size, gapopen,
        gapextend, matrix, threshold, comp_based_stats, seg, False,
        lcase_masking, window_size, use_sw_tback)

def blastp_fast(query, db=None, subject=None, query_loc=None,
        subject_loc=None, evalue=10, parse_deflines=False,
        num_threads=1, word_size=None, threshold=21, comp_based_stats=2,
        seg=0, lcase_masking=False, window_size=40, use_sw_tback=False):
    """
    Quick ``blastp`` similarity search.

    .. include:: blast_options_common

    :param threshold: minimum word score such that the word is added to
        the BLAST lookup table (>0).
    :param seg: filter query sequence with SEG as an integer (0 to
        disable, 1 to enable, or alternatively a tuple with the three
        parameters *window*, *locut*, and *hicut*).
    :param window_size: multiple hits window size (use 0 to specify
        1-hit algorithm).
    :param parse_deflines: parse query and subject bar delimited
        sequence identifiers.
    :param comp_based_stats: composition-based statistics, as an integer
        code: 0 (no composition-based statistics), 1 (composition-based
        statistics as in NAR 29:2994-3005, 2001), 2 (composition-based
        score adjustment as in Bioinformatics 21:902-911, 2005,
        conditioned on sequence properties), or 3 (composition-based
        score adjustment as in Bioinformatics 21:902-911, 2005,
        unconditionally).
    :param lcase_masking: use lower case filtering in query and subject
        sequences.
    :param use_sw_tback: compute locally optimal Smith-Waterman
        alignments.

    :return: A :class:`BlastOutput` instance.
    """
    return _blastp(query, db, subject, 'blastp-fast', query_loc, subject_loc,
        evalue, parse_deflines, num_threads, word_size, None,
        None, None, threshold, comp_based_stats, seg, False,
        lcase_masking, window_size, use_sw_tback)

@_utils._protect_run
def _blastp(query, db, subject, task, query_loc, subject_loc, evalue,
    parse_deflines, num_threads, word_size, gapopen, gapextend, matrix,
    threshold, comp_based_stats, seg, soft_masking, lcase_masking,
    window_size, use_sw_tback):

    cmd, stdin = _get_common_blast_options('blastp', query, db, subject,
                        query_loc, subject_loc, evalue, parse_deflines, num_threads)
    _get_common_protein_options(cmd, task, word_size, matrix, threshold,
        gapopen, gapextend, seg, window_size, comp_based_stats)

    # process task
    cmd.extend(['-task', task])

    # filter/mask flags
    if task == 'blastp':
        if soft_masking: cmd.extend(['-soft_masking', 'true'])
        else: cmd.extend(['-soft_masking', 'false'])
    if lcase_masking: cmd.append('-lcase_masking')

    # use_sw_tback
    if use_sw_tback:
        cmd.append('-use_sw_tback')

    # run the program
    p = subprocess.Popen(cmd, stdin=None if stdin is None else subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = p.communicate(stdin)
    if  p.returncode != 0:
        raise RuntimeError('error while running blastp (message below)\n' + stderr)
    return _parse_blast_output(stdout)

def blastx(query, db=None, subject=None, query_loc=None, subject_loc=None,
        evalue=10, num_threads=1, word_size=None, gapopen=None,
        gapextend=None, matrix='BLOSUM62', threshold=12,
        seg=(12, 2.2, 2.5), soft_masking=False, lcase_masking=False,
        window_size=40, strand='both', query_genetic_code=1,
        max_intron_length=0, comp_based_stats=2):
    """
    ``blastx`` similarity search. Designed for using a translated nucleotide
    query on a protein database.

    .. include:: blast_options_common
    .. include:: blast_options_prot
    :param soft_masking: apply filtering locations as soft masks.
    :param lcase_masking: use lower case filtering in query and subject
        sequences.
    :param query_genetic_code: genetic code to translate query. Allowed
        values are: 1-6, 9-16, 21-25.
    :param max_intron_length: length of the largest intron allowed in a
        translated nucleotide sequence when linking multiple distinct
        alignments (a negative value disables linking).
    :param strand: query strand(s) to search against database/subject.
        Choice of both, minus, or plus.
    :param comp_based_stats: composition-based statistics, as an integer
        code: 0 (no composition-based statistics), 1 (composition-based
        statistics as in NAR 29:2994-3005, 2001), 2 (composition-based
        score adjustment as in Bioinformatics 21:902-911, 2005,
        conditioned on sequence properties), or 3 (composition-based
        score adjustment as in Bioinformatics 21:902-911, 2005,
        unconditionally).

    :return: A :class:`BlastOutput` instance.

"""
    return _blastx('blastx', query, db, subject, query_loc, subject_loc,
        evalue, False, num_threads, word_size, gapopen,
        gapextend, matrix, threshold, seg, soft_masking, lcase_masking,
        window_size, strand, query_genetic_code, max_intron_length,
        comp_based_stats)

def blastx_fast(query, db=None, subject=None, query_loc=None,
        subject_loc=None, evalue=10,  num_threads=1, word_size=None,
        gapopen=None, gapextend=None, matrix='BLOSUM62', threshold=21,
        seg=(12, 2.2, 2.5), soft_masking=False, lcase_masking=False,
        window_size=40, strand='both', query_genetic_code=1,
        max_intron_length=0, comp_based_stats=2):
    """
    Quick ``blastx`` similarity search. Designed for using a translated nucleotide
    query on a protein database and optimised for faster execution.

    .. include:: blast_options_common
    .. include:: blast_options_prot
    :param soft_masking: apply filtering locations as soft masks.
    :param lcase_masking: use lower case filtering in query and subject
        sequences.
    :param query_genetic_code: genetic code to translate query. Allowed
        values are: 1-6, 9-16, 21-25.
    :param max_intron_length: length of the largest intron allowed in a
        translated nucleotide sequence when linking multiple distinct
        alignments (a negative value disables linking).
    :param strand: query strand(s) to search against database/subject.
        Choice of both, minus, or plus.
    :param comp_based_stats: composition-based statistics, as an integer
        code: 0 (no composition-based statistics), 1 (composition-based
        statistics as in NAR 29:2994-3005, 2001), 2 (composition-based
        score adjustment as in Bioinformatics 21:902-911, 2005,
        conditioned on sequence properties), or 3 (composition-based
        score adjustment as in Bioinformatics 21:902-911, 2005,
        unconditionally).

    :return: A :class:`BlastOutput` instance.
    """
    return _blastx('blastx-fast', query, db, subject, query_loc,
        subject_loc, evalue, False, num_threads, word_size,
        gapopen, gapextend, matrix, threshold, seg, soft_masking,
        lcase_masking, window_size, strand, query_genetic_code,
        max_intron_length, comp_based_stats)

@_utils._protect_run
def _blastx(task, query, db, subject, query_loc,
        subject_loc, evalue, parse_deflines, num_threads, word_size,
        gapopen, gapextend, matrix, threshold, seg, soft_masking,
        lcase_masking, window_size, strand, query_genetic_code,
        max_intron_length, comp_based_stats):

    cmd, stdin = _get_common_blast_options('blastx', query, db, subject,
        query_loc, subject_loc, evalue, parse_deflines, num_threads)
    cmd.extend(['-task', task])

    _get_common_protein_options(cmd, task, word_size, matrix, threshold,
        gapopen, gapextend, seg, window_size, comp_based_stats)

    if soft_masking: cmd.extend(['-soft_masking', 'true'])
    else: cmd.extend(['-soft_masking', 'false'])
    if lcase_masking: cmd.append('-lcase_masking')

    if not isinstance(strand, str): raise TypeError('`strand` must be a string')
    if strand not in ['both', 'minus', 'plus']: raise ValueError('`strand` must be either "both", "minus", or "plus"')
    cmd.extend(['-strand', strand])

    if query_genetic_code not in [1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 21, 22, 23, 24, 25]:
        raise ValueError('invalid genetic code: {0}'.format(query_genetic_code))
    cmd.extend(['-query_gencode', str(query_genetic_code)])

    if not isinstance(max_intron_length, int): raise TypeError('`max_intron_length` must be an integer')
    if max_intron_length < 0: raise ValueError('`max_intron_length` must be >= 0')
    cmd.extend(['-max_intron_length', str(max_intron_length)])

    # run the program
    p = subprocess.Popen(cmd, stdin=None if stdin is None else subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = p.communicate(stdin)
    if p.returncode != 0:
        raise RuntimeError('error while running blastx (message below)\n' + stderr)
    return _parse_blast_output(stdout)

def tblastn(query, db=None, subject=None, query_loc=None, subject_loc=None,
        evalue=10, num_threads=1, word_size=None, gapopen=None,
        gapextend=None, matrix='BLOSUM62', threshold=13,
        seg=(12, 2.2, 2.5), soft_masking=False, window_size=40,
        db_genetic_code=1, max_intron_length=0, comp_based_stats=2):
    """
    ``tblastn`` similary search. Designed for using a protein query on
    a translated nucleotide database.

    .. include:: blast_options_common
    .. include:: blast_options_prot

    :param soft_masking: apply filtering locations as soft masks.
    :param db_genetic_code: genetic code to translate subject sequences.
        Allowed values are: 1-6, 9-16, 21-25.
    :param max_intron_length: length of the largest intron allowed in a
        translated nucleotide sequence when linking multiple distinct
        alignments (a negative value disables linking).
    :param comp_based_stats: composition-based statistics, as an integer
        code: 0 (no composition-based statistics), 1 (composition-based
        statistics as in NAR 29:2994-3005, 2001), 2 (composition-based
        score adjustment as in Bioinformatics 21:902-911, 2005,
        conditioned on sequence properties), or 3 (composition-based
        score adjustment as in Bioinformatics 21:902-911, 2005,
        unconditionally).

    :return: A :class:`BlastOutput` instance.
    """
    return _tblastn('tblastn', query, db, subject, query_loc, subject_loc,
        evalue, num_threads, word_size, gapopen, gapextend, matrix,
        threshold, seg, soft_masking, window_size, db_genetic_code,
        max_intron_length, comp_based_stats)

def tblastn_fast(query, db=None, subject=None, query_loc=None, subject_loc=None,
        evalue=10, num_threads=1, word_size=None, gapopen=None,
        gapextend=None, matrix='BLOSUM62', threshold=21,
        seg=(12, 2.2, 2.5), soft_masking=False, window_size=40,
        db_genetic_code=1, max_intron_length=0, comp_based_stats=2):
    """
    Quich ``tblastn`` similary search. Designed for using a protein query on
    a translated nucleotide database and optimised for fast execution.

    .. include:: blast_options_common
    .. include:: blast_options_prot

    :param soft_masking: apply filtering locations as soft masks.
    :param db_genetic_code: genetic code to translate subject sequences.
        Allowed values are: 1-6, 9-16, 21-25.
    :param max_intron_length: length of the largest intron allowed in a
        translated nucleotide sequence when linking multiple distinct
        alignments (a negative value disables linking).
    :param comp_based_stats: composition-based statistics, as an integer
        code: 0 (no composition-based statistics), 1 (composition-based
        statistics as in NAR 29:2994-3005, 2001), 2 (composition-based
        score adjustment as in Bioinformatics 21:902-911, 2005,
        conditioned on sequence properties), or 3 (composition-based
        score adjustment as in Bioinformatics 21:902-911, 2005,
        unconditionally).

    :return: A :class:`BlastOutput` instance.
    """
    return _tblastn('tblastn-fast', query, db, subject, query_loc, subject_loc,
        evalue, num_threads, word_size, gapopen, gapextend, matrix,
        threshold, seg, soft_masking, window_size, db_genetic_code,
        max_intron_length, comp_based_stats)

@_utils._protect_run
def _tblastn(task, query, db, subject, query_loc, subject_loc,
        evalue, num_threads, word_size, gapopen, gapextend, matrix,
        threshold, seg, soft_masking, window_size, db_genetic_code,
        max_intron_length, comp_based_stats):

    # process common options
    cmd, stdin = _get_common_blast_options('tblastn', query, db, subject,
                        query_loc, subject_loc, evalue, False, num_threads)
    _get_common_protein_options(cmd, task, word_size, matrix, threshold,
        gapopen, gapextend, seg, window_size, comp_based_stats)

    # process task
    cmd.extend(['-task', task])

    # filter/mask flags
    if soft_masking: cmd.extend(['-soft_masking', 'true'])
    else: cmd.extend(['-soft_masking', 'false'])

    # db_genetic_code
    if db_genetic_code not in [1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 21, 22, 23, 24, 25]:
        raise ValueError('invalid genetic code: {0}'.format(db_genetic_code))
    cmd.extend(['-db_gencode', str(db_genetic_code)])

    # max_intron_length
    if not isinstance(max_intron_length, int): raise TypeError('`max_intron_length` must be an integer')
    if max_intron_length < 0: raise ValueError('`max_intron_length` must be >= 0')
    cmd.extend(['-max_intron_length', str(max_intron_length)])

    # run the program
    p = subprocess.Popen(cmd, stdin=None if stdin is None else subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = p.communicate(stdin)
    if p.returncode != 0:
        raise RuntimeError('error while running tblastn (message below)\n' + stderr)
    return _parse_blast_output(stdout)

@_utils._protect_run
def tblastx(query, db=None, subject=None, query_loc=None, subject_loc=None,
        evalue=10, num_threads=1, word_size=None, matrix='BLOSUM62',
        seg=(12, 2.2, 2.5), soft_masking=False, lcase_masking=False,
        window_size=40, db_genetic_code=1, query_genetic_code=1,
        strand='both'):
    """
    ``tblastx`` similary search. Designed for using a translated
    nucleotide query on a translated nucleotide database.

    .. include:: blast_options_common

    :param matrix: scoring matrix name. Available values are: PAM-30,
        PAM-70, BLOSUM-80, and BLOSUM-62.
    :param seg: filter query sequence with SEG as an integer (0 to
        disable, 1 to enable, or alternatively a tuple with the three
        parameters *window*, *locut*, and *hicut*).
    :param window_size: multiple hits window size (use 0 to specify
        1-hit algorithm).
    :param soft_masking: apply filtering locations as soft masks.
    :param lcase_masking: use lower case filtering in query and subject
        sequences.
    :param query_genetic_code: genetic code to translate query. Allowed
        values are: 1-6, 9-16, 21-25.
    :param db_genetic_code: genetic code to translate subject sequences.
        Allowed values are: 1-6, 9-16, 21-25.
    :param strand: query strand(s) to search against database/subject.
        Choice of both, minus, or plus.

    :return: A :class:`BlastOutput` instance.
    """

    # process common options
    cmd, stdin = _get_common_blast_options('tblastx', query, db, subject,
                        query_loc, subject_loc, evalue, False, num_threads)
    _get_common_protein_options(cmd, 'tblastx', word_size, matrix, None,
        None, None, seg, window_size, None)

    # filter/mask flags
    if soft_masking: cmd.extend(['-soft_masking', 'true'])
    else: cmd.extend(['-soft_masking', 'false'])
    if lcase_masking: cmd.append('-lcase_masking')

    # query_genetic_code
    if query_genetic_code not in [1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 21, 22, 23, 24, 25]:
        raise ValueError('invalid genetic code: {0}'.format(query_genetic_code))
    cmd.extend(['-query_gencode', str(query_genetic_code)])

    # db_genetic_code
    if db_genetic_code not in [1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 21, 22, 23, 24, 25]:
        raise ValueError('invalid genetic code: {0}'.format(db_genetic_code))
    cmd.extend(['-db_gencode', str(db_genetic_code)])

    # strand
    if not isinstance(strand, str): raise TypeError('`strand` must be a string')
    if strand not in ['both', 'minus', 'plus']: raise ValueError('`strand` must be either "both", "minus", or "plus"')
    cmd.extend(['-strand', strand])

    # run the program
    p = subprocess.Popen(cmd, stdin=None if stdin is None else subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = p.communicate(stdin)
    if p.returncode != 0:
        raise RuntimeError('error while running tblastx (message below)\n' + stderr)
    return _parse_blast_output(stdout)

def _get_common_blast_options(command, query, db, subject, query_loc,
                              subject_loc, evalue, parse_deflines,
                              num_threads):
    # get command name
    path = _blast_apps[command].get_path()
    if path is None:
        raise RuntimeError('{0} program not available -- please configure path'.format(command))
    cmd = [path, '-query', '-', '-outfmt', '5']

    # process query
    if isinstance(query, str):
        stdin = '>lcl|Query\n' + query + '\n'
        queryL = len(query)
    elif isinstance(query, _interface.SequenceView):
        if command in ['blastn', 'blastx', 'tblastx'] and query._parent._alphabet != alphabets.DNA: raise ValueError('query alphabet must be DNA')
        if command in ['blastp', 'tblastn'] and query._parent._alphabet != alphabets.protein: raise ValueError('query alphabet must be protein')
        stdin = '>lcl|Query\n' + query.string() + '\n'
        queryL = len(query)
    elif isinstance(query, _interface.SampleView):
        if command in ['blastn', 'blastx', 'tblastx'] and query._parent._alphabet != alphabets.DNA: raise ValueError('query alphabet must be DNA')
        if command in ['blastp', 'tblastn'] and query._parent._alphabet != alphabets.protein: raise ValueError('query alphabet must be protein')
        stdin = '>lcl|{0}\n{1}\n'.format(query.name, query.sequence.string())
        queryL = len(query.sequence)
    elif isinstance(query, (_interface.Align, _interface.Container)):
        if command in ['blastn', 'blastx', 'tblastx'] and query._alphabet != alphabets.DNA: raise ValueError('query alphabet must be DNA')
        if command in ['blastp', 'tblastn'] and query._alphabet != alphabets.protein: raise ValueError('query alphabet must be protein')
        stdin = query.fasta()
    else: raise TypeError('`query` must be an Align, a Container, a SampleView, a SequenceView, or a string')

    # process db/subject
    if db is not None and subject is not None:
        raise ValueError('only one of `db` and `subject` must be specified')
    if db is None and subject is None:
        raise ValueError('either `db` or `subject` must be specified')
    elif db is not None:
        if not isinstance(db, str): raise ValueError('`db` must be a string')
        if not os.path.isabs(db):
            db = os.path.normpath(os.path.join(_utils._protect_path_mapping[os.getcwd()], db))
        cmd.extend(['-db', db])
    else:
        f = open('in.fas', 'w')
        if isinstance(subject, str):
            f.write('>lcl|Subject\n{0}\n'.format(subject))
            subjectL = len(subject)
        elif isinstance(subject, _interface.SequenceView):
            if command in ['blastn', 'tblastn', 'tblastx'] and subject._parent._alphabet != alphabets.DNA: raise ValueError('subject alphabet must be DNA')
            if command in ['blastp', 'blastx'] and subject._parent._alphabet != alphabets.protein: raise ValueError('subject alphabet must be protein')
            f.write('>lcl|Subject\n{0}\n'.format(subject.string()))
            subjectL = len(subject)
        elif isinstance(subject, _interface.SampleView):
            if command in ['blastn', 'tblastn', 'tblastx'] and subject._parent._alphabet != alphabets.DNA: raise ValueError('subject alphabet must be DNA')
            if command in ['blastp', 'blastx'] and subject._parent._alphabet != alphabets.protein: raise ValueError('subject alphabet must be protein')
            f.write('>lcl|{0}\n{1}\n'.format(subject.name, subject.sequence.string()))
            subjectL = len(subject.sequence)
        else: raise TypeError('`subject` must be a SampleView, a SequenceView, or a string')
        cmd.extend(['-subject', 'in.fas'])

    # process query_loc
    if query_loc is not None:
        if isinstance(query, _interface.Container): raise ValueError('`query_loc` is not supported if `query` is a Container')
        if not isinstance(query_loc, (list, tuple)): raise TypeError('`query_loc` must be a list or a tuple')
        if len(query_loc) != 2: raise ValueError('`query_loc` must have two items')
        if not isinstance(query_loc[0], int) or not isinstance(query_loc[1], int): raise TypeError('`query_loc` must contain two integers')
        if query_loc[0] >= queryL or query_loc[0] < 0 or query_loc[1] < query_loc[0] + 1: raise ValueError('invalid values for `query_loc`')
        cmd.extend(['-query_loc', '{0}-{1}'.format(query_loc[0]+1, query_loc[1])])

    # process subject_loc
    if subject_loc is not None:
        if subject is None: raise ValueError('`subject_loc` cannot be specified if `subject` is not specified')
        if not isinstance(subject_loc, (list, tuple)): raise TypeError('`subject_loc` must be a list or a tuple')
        if len(subject_loc) != 2: raise ValueError('`subject_loc` must have two items')
        if not isinstance(subject_loc[0], int) or not isinstance(subject_loc[1], int): raise TypeError('`subject_loc` must contain two integers')
        if subject_loc[0] >= subjectL or subject_loc[0] < 0 or subject_loc[1] < subject_loc[0] + 1: raise ValueError('invalid values for `subject_loc`')
        cmd.extend(['-subject_loc', '{0}-{1}'.format(subject_loc[0]+1, subject_loc[1])])

    # process evalue
    if evalue is not None:
        if not isinstance(evalue, (int, float)): raise TypeError('`evalue` must be a real value')
        if evalue <= 0: raise ValueError('`evalue` must be > 0')
        cmd.extend(['-evalue', str(evalue)])

    # parse_deflines
    if parse_deflines: cmd.append('-parse_deflines')

    # num_threads
    if not isinstance(num_threads, int): raise TypeError('`num_threads` must be an integer')
    if num_threads < 1: raise ValueError('`num_threads` must be >= 1')
    if num_threads > 1 and subject is not None: raise ValueError('`num_threads cannot be > 1 if `subject` is used')
    cmd.extend(['-num_threads', str(num_threads)])

    return cmd, stdin

def _get_common_protein_options(cmd, task, word_size, matrix, threshold,
        gapopen, gapextend, seg, window_size, comp_based_stats):

    # word size
    if word_size is not None:
        if not isinstance(word_size, int): raise TypeError('`word_size` must be an integer')
        if word_size < 2 or word_size > 7: raise ValueError('invalid value for `word_size`: must be in range [2,7]')
        cmd.extend(['-word_size', str(word_size)])

    # matrix
    if matrix is not None:
        if matrix not in ['PAM30', 'PAM70', 'BLOSUM80', 'BLOSUM62']:
            raise ValueError('invalid value for `matrix`: {0}'.format(matrix))
        cmd.extend(['-matrix', matrix])

    # gap costs
    if task not in ['blastp-fast', 'tblastx']:
        if gapopen is None:
            if gapextend is not None: raise ValueError('if `gapopen is ``None``, `gapextend` must be also')
            gapopen, gapextend = _blastp_costs_defaults[matrix]
        else:
            if gapextend is None: raise ValueError('if `gapextend is ``None``, `gapopen` must be also')
            if not isinstance(gapopen, int): raise TypeError('`gapopen` must be an integer')
            if not isinstance(gapextend, int): raise TypeError('`gapextend` must be an integer')
            if (gapopen, gapextend) not in _blastp_costs[matrix]: raise ValueError('invalid gapopen/gapextend combination for {0}'.format(matrix))
        cmd.extend(['-gapopen', str(gapopen), '-gapextend', str(gapextend)])

    # threshold
    if threshold is not None:
        if not isinstance(threshold, int): raise TypeError('`threshold` must be an integer')
        if threshold <= 0: raise ValueError('invalid value for `treshold`: must be > 0')
        cmd.extend(['-threshold', str(threshold)])

    # seg
    if seg is not None:
        if seg == 0: seg = 'no'
        elif seg == 1: seg = 'yes'
        elif not isinstance(seg, (tuple, list)):
            raise ValueError('invalid value for `seg`: must be 0, 1, or a tuple/list of 3 items')
        else:
            try:
                window, locut, hicut = seg
                window = int(window)
            except ValueError:
                raise ValueError('invalid value for `seg`')
            if window < 1: raise ValueError('`window` (seg parameter) must be > 0')
            locut = float(locut)
            if locut <= 0: raise ValueError('`locut` (seg parameter) must be > 0')
            hicut = float(hicut)
            if hicut <= locut: raise ValueError('`hicut` (seg parameter) must be > `locut`')
            seg = '{0} {1} {2}'.format(window, locut, hicut)
        cmd.extend(['-seg', seg])

    # window_size
    if window_size is not None:
        if not isinstance(window_size, int): raise TypeError('`window_size` must be an integer')
        if window_size < 0: raise ValueError('invalid value for `window_size`: {0}'.format(window_size))
        cmd.extend(['-window_size', str(window_size)])

    # comp_based_stats
    if comp_based_stats is not None:
        if comp_based_stats not in [0, 1, 2, 3]:
            raise ValueError('invalid value for `comp_based_stats`')
        cmd.extend(['-comp_based_stats', str(comp_based_stats)])

def _xml_find(node, tag):
    res = node.find(tag)
    if res is None: raise ValueError('invalid format of BLAST XML output: cannot find `{0}` under `{1}`'.format(tag, node.tag))
    return res

def _xml_find_type(node, tag, type_):
    value = _xml_find(node, tag).text
    try: return type_(value)
    except ValueError:
        raise ValueError('invalid format of BLAST XML output: invalid value for `{0}`: {1}'.format(tag, value))

def _parse_blast_output(string):
    root = xml.etree.ElementTree.fromstring(string)
    if root.tag != 'BlastOutput': raise ValueError('invalid format of BLAST XML output: no `BlastOutput` at root')

    out = BlastOutput()
    out._program = _xml_find(root, 'BlastOutput_program').text
    out._version = _xml_find(root, 'BlastOutput_version').text
    out._reference = _xml_find(root, 'BlastOutput_reference').text
    out._db = _xml_find(root, 'BlastOutput_db').text
    out._query_ID = _xml_find(root, 'BlastOutput_query-ID').text
    out._query_def = _xml_find(root, 'BlastOutput_query-def').text
    out._query_len = _xml_find_type(root, 'BlastOutput_query-len',  int)

    node = _xml_find(root, 'BlastOutput_param')
    nodes = node.findall('Parameters')
    if len(nodes) != 1: raise ValueError('invalid format of BLAST XML output: expect one set of BLAST parameters')
    node = nodes[0]

    out._params = {}
    for child in node:
        if child.tag[:11] != 'Parameters_':
            raise ValueError('invalid parameter in BLAST output: {0}'.format(child.tag))
        tag = child.tag[11:]
        if tag in out._params:
            raise ValueError('parameter repeated in BLAST output: {0}'.format(child.tag))
        try: out._params[tag] = int(child.text)
        except ValueError:
            try: out._params[tag] = float(child.text)
            except ValueError:
                out._params[tag] = child.text

    iterations = _xml_find(root, 'BlastOutput_iterations')
    for query_node in iterations:
        if query_node.tag != 'Iteration': raise ValueError('invalid format of BLAST XML output: unexpected node under `BlastOutput_iterations`: {0}'.format(query_node.tag))
        query_hits = BlastQueryHits()
        i = _xml_find_type(query_node, 'Iteration_iter-num', int)
        if i != len(out._query_hits) + 1: raise ValueError('invalid format of BLAST XML output: unexpected value for `Iteration_iter-num`: {0}'.format(i))
        query_hits._num = i - 1
        query_hits._query_ID = _xml_find(query_node, 'Iteration_query-ID').text
        query_hits._query_def = _xml_find(query_node, 'Iteration_query-def').text
        query_hits._query_len = _xml_find_type(query_node, 'Iteration_query-len', int)
        node = _xml_find(query_node, 'Iteration_stat')
        nodes = node.findall('Statistics')
        if len(nodes) != 1: raise ValueError('invalid format of BLAST XML output: expect one set of iteration statistics')
        node = nodes[0]
        query_hits._db_num = _xml_find_type(node, 'Statistics_db-num', int)
        query_hits._db_len = _xml_find_type(node, 'Statistics_db-len', int)
        query_hits._hsp_len = _xml_find_type(node, 'Statistics_hsp-len', int)
        query_hits._eff_space = _xml_find_type(node, 'Statistics_eff-space', int)
        query_hits._kappa = _xml_find_type(node, 'Statistics_kappa', float)
        query_hits._lambda = _xml_find_type(node, 'Statistics_lambda', float)
        query_hits._entropy = _xml_find_type(node, 'Statistics_entropy', float)
        out._query_hits.append(query_hits)

        hits = _xml_find(query_node, 'Iteration_hits')
        for hit_node in hits:
            if hit_node.tag != 'Hit': raise ValueError('invalid format of BLAST XML output: unexpected node under `Iteration_hits`: {0}'.format(hit_node.tag))
            hit = BlastHit()
            i = _xml_find_type(hit_node, 'Hit_num', int)
            if i != len(query_hits._hits) + 1: raise ValueError('invalid format of BLAST XML output: unexpected value for `Hit_num`: {0}'.format(i))
            hit._num = i - 1
            hit._id = _xml_find(hit_node, 'Hit_id').text
            hit._def = _xml_find(hit_node, 'Hit_def').text
            hit._accession = _xml_find(hit_node, 'Hit_accession').text
            hit._len = _xml_find_type(hit_node, 'Hit_len', int)
            query_hits._hits.append(hit)

            Hsps = _xml_find(hit_node, 'Hit_hsps')
            for Hsp_node in Hsps:
                if Hsp_node.tag != 'Hsp': raise ValueError('invalid format of BLAST XML output: unexpected node under `Hit_hsps`: {0}'.format(Hsp_node.tag))
                Hsp = BlastHsp()
                i = _xml_find_type(Hsp_node, 'Hsp_num', int)
                if i != len(hit._hsp) + 1: raise ValueError('invalid format of BLAST XML output: unexpected value for `Hsp_num`: {0}'.format(i))
                Hsp._num = i - 1
                Hsp._bit_score = _xml_find_type(Hsp_node, 'Hsp_bit-score', float)
                Hsp._evalue = _xml_find_type(Hsp_node, 'Hsp_evalue', float)
                Hsp._identity = _xml_find_type(Hsp_node, 'Hsp_identity', int)
                Hsp._gaps = _xml_find_type(Hsp_node, 'Hsp_gaps', int)
                Hsp._positive = _xml_find_type(Hsp_node, 'Hsp_positive', int)
                Hsp._align_len = _xml_find_type(Hsp_node, 'Hsp_align-len', int)
                Hsp._qseq = _xml_find(Hsp_node, 'Hsp_qseq').text
                Hsp._midline = _xml_find(Hsp_node, 'Hsp_midline').text
                Hsp._hseq = _xml_find(Hsp_node, 'Hsp_hseq').text
                if len(Hsp._qseq) != Hsp._align_len: raise ValueError('invalid format of BLAST XML output: incompatibility between `qseq` and `align-len`')
                if len(Hsp._hseq) != Hsp._align_len: raise ValueError('invalid format of BLAST XML output: incompatibility between `hseq` and `align-len`')
                if len(Hsp._midline) != Hsp._align_len: raise ValueError('invalid format of BLAST XML output: incompatibility between `midline` and `align-len`')

                qfrom = _xml_find_type(Hsp_node, 'Hsp_query-from', int)
                qto = _xml_find_type(Hsp_node, 'Hsp_query-to', int)
                Hsp._query_frame = _xml_find_type(Hsp_node, 'Hsp_query-frame', int)
                if out._program in ['blastp', 'tblastn']:
                    if Hsp._query_frame != 0:  raise ValueError('invalid value for `Hsp_query-frame`: {0}'.format(Hsp._query_frame))
                    if qto <= qfrom: raise ValueError('invalid values for `Hsp_query-from/to`: {0} and {1} with positive frame'.format(qfrom, qto))
                    Hsp._query_start = qfrom - 1
                    Hsp._query_stop = qto
                else:
                    if Hsp._query_frame not in [-3, -2, -1, 1, 2, 3]: raise ValueError('invalid value for `Hsp_query-frame`: {0}'.format(Hsp._query_frame))
                    qfrom, qto = sorted([qfrom, qto])
                    Hsp._query_start = qfrom - 1
                    Hsp._query_stop = qto

                hfrom = _xml_find_type(Hsp_node, 'Hsp_hit-from', int)
                hto = _xml_find_type(Hsp_node, 'Hsp_hit-to', int)
                Hsp._hit_frame = _xml_find_type(Hsp_node, 'Hsp_hit-frame', int)
                if out._program in ['blastp', 'blastx']:
                    if Hsp._hit_frame != 0:  raise ValueError('invalid value for `Hsp_hit-frame`: {0}'.format(Hsp._hit_frame))
                    if hto <= hfrom: raise ValueError('invalid values for `Hsp_hit-from/to`: {0} and {1} with positive frame'.format(hfrom, hto))
                    Hsp._hit_start = hfrom - 1
                    Hsp._hit_stop = hto
                else:
                    if Hsp._hit_frame not in [-3, -2, -1, 1, 2, 3]: raise ValueError('invalid value for `Hsp_hit-frame`: {0}'.format(Hsp._hit_frame))
                    hfrom, hto = sorted([hfrom, hto])
                    Hsp._hit_start = hfrom - 1
                    Hsp._hit_stop = hto

                hit._hsp.append(Hsp)
    return out

class BlastOutput(object):
    """
    Full results of a BLAST run.
    """
    def __init__(self):
        self._program = None
        self._version = None
        self._reference = None
        self._db = None
        self._query_ID = None
        self._query_def = None
        self._query_len = None
        self._params = None
        self._query_hits = []

    @property
    def program(self):
        """ Name of the program used."""
        return self._program

    @property
    def version(self):
        """ Version of the program. """
        return self._version

    @property
    def reference(self):
        """ Bibliographic reference. """
        return self._reference

    @property
    def db(self):
        """ Name of the database used. """
        return self._db

    @property
    def query_ID(self):
        """ Identifier of the query. """
        return self._query_ID

    @property
    def query_def(self):
        """ Description of the query. """
        return self._query_def

    @property
    def query_len(self):
        """ Length of the query. """
        return self._query_len

    @property
    def params(self):
        """
        Search parameters.
        
        ``"expect"``: E-value, ``"reward"``:
        nucleotide match reward, ``"penalty"``: nucleotide
        mismatch reward, ``"gapopen"``: cost for opening a gap,
        ``"gapextend"``: cost for extending a gap.
        ``"filter"``: filter string.
        """
        return self._params

    @property
    def num_queries(self):
        """
        Number of queries used in the BLAST search. ``blast_output.num_queries``
        is also available as ``len(blast_output)``.
        """
        return len(self._query_hits)

    def __len__(self):
        return len(self._query_hits)

    def iter_queries(self):
        """
        Iterator over queries. Allows to iterate over
        :class:`.BlastQueryHits` instances for all queries.
        ``for query_hit in blast_output.iter_queries()`` is
        also available as ``for query_hit in blast_output``.
        """
        return self.__iter__()

    def __iter__(self):
        for i in self._query_hits: yield i

    def get_query(self, i):
        """
        Hits for a given query. An instance of :class:`.BlastQueryHits`
        is returned.
        ``blast_output.get_query(i)`` is also available as ``blast_output[i]``.
        """
        return self._query_hits[i]

    def __getitem__(self, i):
        return self._query_hits[i]

    @property
    def num_hits(self):
        """
        Total number of hits for all queries.
        """
        return sum(map(len, self._query_hits))

    def iter_hits(self):
        """
        Iterator over all hits of all queries. Iterates over
        :class:`.BlastHit` instances
        """
        for query in self._query_hits:
            for hit in query:
                yield hit

    @property
    def num_hsp(self):
        """
        Total number of Hsp's for all hits of all entries.
        """
        return sum([hit.num_hsp() for hit in self._query_hits])

    def iter_hsp(self):
        """
        Iterator over all Hsp's of all hits of all queries.
        """
        for query in self._query_hits:
            for hit in query:
                for Hsp in hit:
                    yield Hsp

class BlastQueryHits(object):
    """
    Results for a given query of a BLAST run.
    """
    def __init__(self):
        self._num = None
        self._query_ID = None
        self._query_def = None
        self._query_len = None
        self._db_num = None
        self._db_len = None
        self._hsp_len = None
        self._eff_space = None
        self._kappa = None
        self._lambda = None
        self._entropy = None
        self._hits = []

    @property
    def num(self):
        """ index of the query in the BLAST run. """
        return self._num

    @property
    def query_ID(self):
        """Identifier of the query."""
        return self._query_ID

    @property
    def query_len(self):
        """Length of the query."""
        return self._query_len

    @property
    def query_def(self):
        """Description of the query."""
        return self._query_def

    @property
    def db_num(self):
        """Number of sequence in the database."""
        return self._db_num

    @property
    def db_len(self):
        """Number of letters in the database."""
        return self._db_len

    @property
    def hsp_len(self):
        """Length adjustment."""
        return self._hsp_len

    @property
    def eff_space(self):
        """Effective space of the search."""
        return self._eff_space

    @property
    def K(self):
        """Karlin-Altschul kappa parameter."""
        return self._kappa

    @property
    def L(self):
        """Karlin-Altschul lambda parameter."""
        return self._lambda

    @property
    def H(self):
        """Karlin-Altschul entropy parameter."""
        return self._entropy

    @property
    def num_hits(self):
        """
        Number of hits for this query. ``query_hits.num_hits()`` is also
        available as ``len(query_hits)``.
        """
        return len(self._hits)

    def __len__(self):
        return len(self._hits)

    def iter_hits(self):
        """
        Iterator to the :class:`.BlastHit` instances of all
        hits. ``for hit in query_hits.iter_hits()`` is also available as
        ``for hit in query_hits``.
        """
        for i in self._hits: yield i

    def __iter__(self):
        for i in self._hits: yield i

    def get_hit(self, i):
        """
        Get a given hit, as a :class:`.BlastHit` instance. ``query_hits.get_hit(i)``
        is also available as ``query_hits[i]``.
        """
        return self._hits[i];

    def __getitem__(self, i):
        return self._hits[i]

    @property
    def num_hsp(self):
        """
        Total number of Hsp's for all hits.
        """
        return sum(map(len, self._hits))

    def iter_hsp(self):
        """
        Iterator over all Hsp's of all hits, as :class:`.BlastHsp`
        instances
        """
        for hit in self._hits:
            for hsp in hit:
                yield hsp

class BlastHit(object):
    """
    Results for a given hit of a BLAST run.
    """
    def __init__(self):
        self._num = None
        self._id = None
        self._def = None
        self._accession = None
        self._len = None
        self._hsp = []

    @property
    def num(self):
        """Index of the hit for the corresponding query."""
        return self._num

    @property
    def id(self):
        """Identifier of the subject."""
        return self._id

    @property
    def descr(self):
        """Description of the subject."""
        return self._def

    @property
    def accession(self):
        """Identifier of the subject."""
        return self._accession

    @property
    def len(self):
        """Length of subject."""
        return self._len

    @property
    def num_hsp(self):
        """
        Number of Hsp's in this hit. ``hit.num_Hsp()  is also available as
        ``len(hit)``.
        """
        return len(self._hsp)

    def __len__(self):
        return len(self._hsp)

    def iter_hsp(self):
        """
        Iterator to the :class:`.BlastHsp` instances for all
        Hsp's. ``for hsp in hit.iter_hsp()`` is also available as
        ``for hsp in hit``.
        """
        for i in self._hsp: yield i

    def __iter__(self):
        for i in self._hsp: yield i

    def get_hsp(self, i):
        """
        Get a given Hsp, as a :class:`.BlastHsp` instance. ``hit.get_hsp(i)``
        is also available as ``hit[i]``.
        """
        return self._hsp[i];

    def __getitem__(self, i):
        return self._hsp[i]

class BlastHsp(object):
    """
    Description of an Hsp of a BLAST run.

    Start and stop positions are always interpreted as range parameters (use
    `frame` to determine if the complement should be used)::

        >>> hit_sequence = seq[query_start:query_to]
    """
    def __init__(self):
        self._num = None
        self._bit_score = None
        self._evalue = None
        self._query_start = None
        self._query_stop = None
        self._query_frame = None
        self._hit_start = None
        self._hit_stop = None
        self._hit_frame = None
        self._identity = None
        self._positive = None
        self._gaps = None
        self._align_len = None
        self._qseq = None
        self._hseq = None
        self._midline = None

    @property
    def num(self):
        """Index of the Hsp in the corresponding hit."""
        return self._num

    @property
    def bit_score(self):
        """Bit score of the Hsp."""
        return self._bit_score

    @property
    def evalue(self):
        """Expectation value of the Hsp."""
        return self._evalue

    @property
    def query_start(self):
        """Start position on the query."""
        return self._query_start

    @property
    def query_stop(self):
        """Stop position on the query."""
        return self._query_stop

    @property
    def hit_start(self):
        """Start position on the subject."""
        return self._hit_start

    @property
    def hit_stop(self):
        """Stop position on the subject."""
        return self._hit_stop

    @property
    def query_frame(self):
        """Frame of the query."""
        return self._query_frame

    @property
    def hit_frame(self):
        """Frame of the hit."""
        return self._hit_frame

    @property
    def identity(self):
        """Number of identical positions."""
        return self._identity

    @property
    def positive(self):
        """Number of positions with positive score."""
        return self._positive

    @property
    def gaps(self):
        """Number of gap positions."""
        return self._gaps

    @property
    def align_len(self):
        """Length of the alignment."""
        return self._align_len

    @property
    def qseq(self):
        """Aligned query sequence."""
        return self._qseq

    @property
    def hseq(self):
        """Aligned subject sequence."""
        return self._hseq

    @property
    def midline(self):
        """Alignment midline."""
        return self._midline
