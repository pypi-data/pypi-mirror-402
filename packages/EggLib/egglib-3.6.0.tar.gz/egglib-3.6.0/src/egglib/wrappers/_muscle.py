"""
    Copyright 2009-2023 Stephane De Mita, Mathieu Siol

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

import subprocess, re, os
from .. import _interface, alphabets
from ..io import _fasta
from . import _utils

class _Muscle(_utils._App):

    @_utils._protect_run
    def _check_path(self, path, cfg):

        # test the "help" option to ensure that software exists
        cmd = (path, '-version')
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = p.communicate()
            if len(stderr): return stderr
        except OSError as e:
            return e.strerror

        if re.match(r'MUSCLE v3\.8\.\d+', stdout):
            cfg['version'] = 3
        elif re.match(r'muscle 5\.\d+\.', stdout):
            cfg['version'] = 5
        else:
            return 'MUSCLE: invalid version'
        return None

_app = _Muscle(key='muscle', default='muscle')
_app.add_option(name='version', f_convert=int, default=None, f_set_missing=lambda: 5, f_load_missing=lambda: 5)
_utils.paths._add(_app)

# dynamic caller who redirected call to the correct version of the wrapper
def muscle(*args, **kwargs):
    """ muscle(...)
    Perform multiple alignment using `Muscle <http://www.drive5.com/muscle/>`_.

    Depending of the version of MUSCLE detected at configuration, the
    call will be forwarded to either :func:`.wrappers.muscle3` or
    :func:`.wrappers.muscle5`.

    .. versionchanged:: 3.2.0

        Dynamically use the new :func:`!muscle5` method if MUSCLE
        version 5 is present.
    """

    if _app.config['version'] == 5: return muscle5(*args, **kwargs)
    elif _app.config['version'] == 3: return muscle3(*args, **kwargs)
    else: raise RuntimeError('muscle program not available -- please configure path')

##### muscle 3 stuff ###################################################

_args = {
    # these ones cannot passed as is to muscle
    'diags':           (bool,  None),
    'diags1':          (bool,  None),
    'diags2':          (bool,  None),
    'anchors':         (bool,  None),
    'dimer':           (bool,  None),
    'brenner':         (bool,  None),
    'cluster':         (bool,  None),
    'teamgaps4':       (bool,  lambda x: x is True),
    'nt_profile':      (str,   ['spn']),
    'aa_profile':      (str,   ['le', 'sp', 'sv']),

    # these ones should be able to be passed as is
    'anchorspacing':   (int,   lambda x: x>0),
    'center':          (float, lambda x: x<0),
    'cluster1':        (str,   ['upgma', 'upgmb', 'neighborjoining']),
    'diagbreak':       (int,   lambda x: x>0),
    'diaglength':      (int,   lambda x: x>0),
    'diagmargin':      (int,   lambda x: x>0),
    'diagmargin':      (int,   lambda x: x>0),
    'distance1':       (str,   ['kmer6_6', 'kmer20_3', 'kmer20_4', 'kbit20_3', 'kmer4_6']),
    'distance2':       (str,   ['pctidkimura', 'pctidlog']),
    'gapopen':         (float, lambda x: x<0),
    'hydro':           (int,   lambda x: x>0),
    'hydrofactor':     (float, lambda x: x>0),
    'maxiters':        (int,   lambda x: x>0),
    'maxtrees':        (int,   lambda x: x>0),
    'minbestcolscore': (float, lambda x: x>=0),
    'minsmoothscore':  (float, lambda x: x>=0),
    'objscore':        (str,   ['sp', 'ps', 'dp', 'xp', 'spf', 'spm']),
    'refinewindow':    (int,   lambda x: x>0),
    'root1':           (str,   ['pseudo', 'midlongestspan', 'minavgleafdist']),
    'seqtype':         (str,   ['protein', 'dna', 'auto']),
    'smoothscoreceil': (float, lambda x: x>0),
    'SUEFF':           (float, lambda x: x>=0.0 and x<=1.0),
    'weight1':         (str,   ['none', 'henikoff', 'henikoffpb', 'gsc', 'clustalw', 'threeway']),
    'weight2':         (str,   ['none', 'henikoff', 'henikoffpb', 'gsc', 'clustalw', 'threeway'])
}

@_utils._protect_run
def muscle3(source, ref=None, verbose=False, **kwargs):

    """ muscle(source, ref=None, verbose=False, \
                **kwargs)

    Perform multiple alignment using `Muscle <http://www.drive5.com/muscle/>`_.

    This wrapper is designed to run version 3 of MUSCLE. To use MUSCLE
    version 5, configure the application path using the
    ``egglib-config apps`` command.

    MUSCLE's default options tend to produce high-quality alignments but
    may be long to run on large data sets. Muscle's author recommends
    using the option ``maxiters=2`` for large data sets, and, for fast
    alignment (in particular of closely related sequences):
    ``maxiters=1 diags=True aa_profile='sv' distance1='kbit20_3'`` (for
    amino acid sequences) and ``maxiters=1 diags=True`` (for nucleotide
    sequences).

    :param source: a :class:`.Container` or :class:`.Align` containing
        sequences to align. If an :class:`!Align` is provided, sequences
        are assumed to be already aligned and alignment will be refined
        (using the ``-refine`` option of Muscle), unless an alignment is
        also provided as *ref*. In the latter case,  the two alignments
        are preserved (their columns are left unchanged), and they are
        aligned with respect to each other.

    :param ref: an :class:`!Align` instance providing an alignement that
        should be aligned with respect to the alignment provided as
        *source*. If *ref* is provided, it is required both *source* and
        *ref* are :class:`!Align` instances.

    :param verbose: display Muscle's console output.

    :param kwargs: other keyword arguments are passed to Muscle. The
        available options are listed below:

        .. include:: muscle_arguments.txt

        For a description of options, see the `Muscle manual <http://www.drive5.com/muscle/manual/options.html>`_.
        Most of Muscle's options are available. Note that function takes
        no flag option, and Muscle's flag options are passed as boolean
        keyword arguments (except options relative to the amino acid or
        nucleotide profile score options, that are passed as string as
        ``aa_profile`` and ``nt_profile``, respectively. The order of
        options is preserved.

    :return: An :class:`.Align` containing aligned sequences.

    .. versionchanged:: 3.0.0

        Added support for most options.

    .. versionchanged:: 3.2.0

        Renamed as :func:`!muscle3`. Available as :func:`!muscle` if
        MUSCLE version 3 is available
    """

    # check that program is available
    if _app.config['version'] != 3:
        raise RuntimeError('muscle version 3 not available -- please configure path')
    command_line = [_app.get_path(), '-out', 'o']
    if not verbose: command_line.append('-quiet')

    # mapping for sample reference
    mapping = {}

    # write source
    if not isinstance(source, (_interface.Container, _interface.Align)): raise TypeError('invalid type for `source` argument')
    _utils._write(source, 'source', mapping)

    # then save ref
    if ref != None:
        if not isinstance(ref, _interface.Align): raise TypeError('`ref` must be an Align')
        if not isinstance(source, _interface.Align): raise TypeError('if `ref` is provided, `source` must be an Align')
        if ref._alphabet not in [alphabets.DNA, alphabets.protein]: raise ValueError('alphabet must be DNA or protein')
        _utils._write(ref, 'ref', mapping)
        command_line.extend(['-profile', '-in1', 'ref', '-in2', 'source'])

    elif isinstance(source, _interface.Align):
        command_line.extend(['-in', 'source', '-refine'])

    else: # the default case
        command_line.extend(['-in', 'source'])

    # check data type
    if ref != None and ref.alphabet != source.alphabet: raise ValueError('`source` and `ref` must have the same alphabet')
    if 'seqtype' not in kwargs:
        if source.alphabet == alphabets.DNA: kwargs['seqtype'] = 'dna'
        elif source.alphabet == alphabets.protein: kwargs['seqtype'] = 'protein'
        else: raise ValueError('unsupported alphabet')
    else:
        if kwargs['seqtype'] == 'dna' and source.alphabet != alphabets.DNA: raise ValueError('source does not have a proper alphabet for seqtype `{0}`'.format(kwargs['seqtype']))
        if kwargs['seqtype'] == 'protein' and source.alphabet != alphabets.protein: raise ValueError('source does not have a proper alphabet for seqtype `{0}`'.format(kwargs['seqtype']))

    # process kwargs
    for opt, value in kwargs.items():
        if opt not in _args: raise ValueError('invalid option: {0}'.format(opt))
        type_, test = _args[opt]
        try: value = type_(value)
        except (TypeError, ValueError): raise ValueError('invalid value for argument {0}'.format(opt))
        if type_ == str:
            if value not in test: raise ValueError('invalid value for argument {0}'.format(opt))
        elif test is not None and not test(value): raise ValueError('invalid value for argument {0}'.format(opt))

        if opt == 'diags':
            if value == True: command_line.append('-diags')
        elif opt == 'diags1':
            if value == True: command_line.append('-diags1')
        elif opt == 'diags2':
            if value == True: command_line.append('-diags2')
        elif opt == 'anchors':
            if value == True: command_line.append('-anchors')
            else: command_line.append('-noanchors')
        elif opt == 'dimer':
            if value == True: command_line.append('-dimer')
        elif opt == 'brenner':
            if value == True: command_line.append('-brenner')
        elif opt == 'cluster':
            if value == True: command_line.append('-cluster')
        elif opt == 'teamgaps4':
            if value == True: command_line.append('-teamgaps4')
        elif opt == 'nt_profile':
            command_line.append('-' + value)
        elif opt == 'aa_profile':
            command_line.append('-' + value)
        else:
            command_line.extend(['-' + opt, str(value)])

    # run the program
    p = subprocess.Popen(command_line, stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=(None if verbose else subprocess.PIPE), universal_newlines=True)
    stdout, stderr = p.communicate('Y\n')

    # check error
    if not os.path.isfile('o'):
        if stderr is not None:
            lines = stderr.splitlines()
            if len(lines) and 'ERROR' in lines[-1]:
                raise RuntimeError('error while running muscle: {0}'.format(lines[-1].strip()))
        raise RuntimeError('unknown error while running muscle (try verbose mode)')

    # get alignment
    aln = _fasta.from_fasta('o', source.alphabet, labels=False, cls=_interface.Align)

    # set proper names and groups
    for sam in aln:
        ref = mapping[sam.name]
        sam.name = ref.name
        sam.labels = ref.labels

    # return
    return aln

##### muscle 5 stuff ###################################################

@_utils._protect_run
def muscle5(source, super5=False, perm='none', perturb=0, consiters=2,
                        refineiters=100, threads=None, verbose=False):

    """ muscle5(source, super5=False, perm='none', perturb=0, consiters=2, \
                        refineiters=100, threads=None, verbose=False)

    Perform multiple alignment using `Muscle <http://www.drive5.com/muscle/>`_ version 5.

    :param source: a :class:`.Container` instance contain sequences to
        align. :class:`.Align` is supported but will be treated as if it
        was a :class:`!Container`. The alphabet must be DNA or protein.

    :param super5: use the `Super5 algorithm <https://drive5.com/muscle5/manual/super5_algo.html>`_
        (recommended for datasets of more than a few hundred sequences).

    :param perm: guide tree permutation mode. Available values are
        ``none``, ``abc``, ``acb``, and ``bca``. More information
        `here <https://drive5.com/muscle5/manual/guide_tree_permutations.html>`_.

    :param perturb: if different of 0, the value is a random number
        generator seed used to perform `hidden Markov model perturbations <https://drive5.com/muscle5/manual/hmm_perturbations.html>`_.

    :param consiter: number of consistency iterations.

    :param refineiters: number of refinement iterations.

    :param threads: number of threads. By default, let MUSCLE pick the
        value.

    :param verbose: show MUSCLE's output in stdout.

    .. note::
        The *ensemble fasta* features of muscle5 are currently not
        available through this wrapper.
    
    :return: An :class:`.Align` containing aligned sequences.

    .. versionadded:: 3.2.0
    """

    # check version (implies presence of program)
    if _app.config['version'] != 5:
        raise RuntimeError('muscle version 5 not available -- please configure path')

    # initialize command line
    command_line = [_app.get_path(),
                    '-super5' if super5 else '-align',
                    'i', '-output', 'o']

    # check input object
    if not isinstance(source, (_interface.Container, _interface.Align)):
        raise TypeError('`source\' must be a Container')
    if source._alphabet == alphabets.DNA: pass
    elif source._alphabet == alphabets.protein: pass
    else: raise ValueError('alphabet must be DNA or protein')
    _utils._write(source, 'i', mapping:={})

    # permutation mode
    if perm != 'none':
        if perm not in muscle5_perm_values:
            raise ValueError('invalid value for `perm\'')
        command_line.extend(['-perm', perm])

    # HMM perturbations
    if not isinstance(perturb, int): raise TypeError('`perturb\' must be an integer')
    if perturb != 0:
        if perturb < 0: raise ValueError('invalid value for `perturb\'')
        command_line.extend(['-perturb', str(perturb)])

    # consiters / refineiters
    if not isinstance(consiters, int): raise TypeError('`consiters\' must be an integer')
    if not isinstance(refineiters, int): raise TypeError('`refineiters\' must be an integer')
    if consiters < 1: raise ValueError('`consiters\' must be strictly positive')
    if refineiters < 1: raise ValueError('`refineiters\' must be strictly positive')
    command_line.extend(['-consiters', str(consiters), '-refineiters', str(refineiters)])

    # threads
    if threads is not None:
        if not isinstance(threads, int): raise TypeError('`threads\' must be an integer')
        if threads < 1: raise ValueError('`threads\' must be strictly positive')
        command_line.extend(['-threads', str(threads)])

    # run the program
    p = subprocess.Popen(command_line, stdin=subprocess.PIPE,
                        stdout=(None if verbose else subprocess.PIPE),
                        stderr=(None if verbose else subprocess.PIPE), universal_newlines=True)
    stdout, stderr = p.communicate('Y\n')

    # check error
    if not os.path.isfile('o'):
        if stderr is not None:
            lines = stderr.splitlines()
            if len(lines) and 'ERROR' in lines[-1]:
                raise RuntimeError('error while running muscle: {0}'.format(lines[-1].strip()))
        raise RuntimeError('unknown error while running muscle (try verbose mode)')

    # get alignment
    aln = _fasta.from_fasta('o', source.alphabet, labels=False, cls=_interface.Align)

    # restore original names and groups
    for sam in aln:
        ref = mapping[sam.name]
        sam.name = ref.name
        sam.labels = ref.labels

    # return
    return aln

muscle5_perm_values = {'abc', 'acb', 'bca'}
