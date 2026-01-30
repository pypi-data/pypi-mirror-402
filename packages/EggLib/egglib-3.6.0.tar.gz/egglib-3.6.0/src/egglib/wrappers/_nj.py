"""
    Copyright 2019-2021 Stephane De Mita, Mathieu Siol

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

import subprocess, os
from .. import _interface, alphabets, tools, _tree, random
from . import _utils

class _Dnadist(_utils._App):
    @_utils._protect_run
    def _check_path(self, path, cfg):
        cmd = (path,)
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = p.communicate('\n'*10)
            if len(stderr): return stderr
        except OSError as e:
            return e.strerror
        if 'dnadist' not in stdout or stdout.count('Please enter a new file name') != 10:
            return 'unexpected output from dnadist'

class _Protdist(_utils._App):
    @_utils._protect_run
    def _check_path(self, path, cfg):
        cmd = (path,)
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = p.communicate('\n'*10)
            if len(stderr): return stderr
        except OSError as e:
            return e.strerror
        if 'protdist' not in stdout or stdout.count('Please enter a new file name') != 10:
            return 'unexpected output from protdist'

class _Neighbor(_utils._App):
    @_utils._protect_run
    def _check_path(self, path, cfg):
        cmd = (path,)
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = p.communicate('\n'*10)
            if len(stderr): return stderr
        except OSError as e:
            return e.strerror
        if 'neighbor' not in stdout or stdout.count('Please enter a new file name') != 10:
            return 'unexpected output from neighbor'

_dnadist = _Dnadist(key='dnadist', default='dnadist')
_utils.paths._add(_dnadist)

_protdist = _Protdist(key='protdist', default='protdist')
_utils.paths._add(_protdist)

_neighbor = _Neighbor(key='neighbor', default='neighbor')
_utils.paths._add(_neighbor)

@_utils._protect_run
def nj(aln, model=None, kappa=None, upgma=False, outgroup=None,
    randomize=0, verbose=False):

    """ nj(aln, model=None, kappa=None, upgma=False, outgroup=None, \
           randomize=0, verbose=False)

    Neighbour-joining (or UPGMA) tree using `PHYLIP <http://evolution.genetics.washington.edu/phylip/>`_.

    The programs of PHYLIP used are ``dnadist`` (or ``protdist``) and ``neighbor``.

    :param aln: an :class:`.Align` instance containing source sequences.
        The alphabet must DNA or protein, matching the *model* argument.
        Note: outgroup is ignored.

    :param model: one of the models among the list
        below:

        For DNA sequences:
            * JC69: Jukes & Cantor's 1969 one-parameter model.
            * K80: Kimura's 1980 two-parameter model.
            * F84: like K80 with unequal base frequencies (default).
            * LD: LogDet (log-determinant of nucleotide occurence matrix).

        For protein sequences:
            * PAM: Dayoff PAM matrix.
            * JTT: Jones-Taylor-Thornton model (default).
            * PMB: probability matrix from blocks.

    :param kappa: transition/transversion ratio (default is 2.0).

    :param upgma: whether using the UPGMA method rather than the 
        neighbour-joining method.

    :param outgroup: name of the sample to use as outgroup for printing
        the tree (the root is based at the parent node of this sample;
        default is the first sample).

    :param randomize: whether to randomize samples.

    :param verbose: whether displaying console output of the PHYLIP programs.

    :return: A :class:`.Tree` instance containing the tree.

    .. versionadded:: 3.0.0
    """

    # check that program is available
    path_n = _neighbor.get_path()
    if path_n is None: raise RuntimeError('neighbor program not available -- please configure path')
    if aln.ns < 3: raise ValueError('not enough samples')

    # check parameters
    if aln.alphabet == alphabets.DNA:
        dt = 'n'
        if model is None:
            model = 0
        else:
            try: model = ['F84', 'K80', 'JC69', 'LD'].index(model)
            except ValueError: raise ValueError('invalid model for DNA sequence: {0}'.format(model))
    elif aln.alphabet == alphabets.protein:
        dt = 'p'
        if model is None:
            model = 0
        else:
            try: model = ['JTT', 'PMB', 'PAM'].index(model)
            except ValueError: raise ValueError('invalid model for protein sequence: {0}'.format(model))
    else:
        raise ValueError('invalid alphabet (must be DNA or protein)')
    if kappa is not None:
        if dt == 'p': raise ValueError('kappa argument not supported for proteins')
        if model > 1: raise ValueError('kappa argument not supported for this model')
        try: kappa = float(kappa)
        except ValueError: raise ValueError('invalid value for kappa: {0}'.format(kappa))
        if kappa <= 0.0: raise ValueError('invalid value for kappa: {0}'.format(kappa))
    if outgroup is not None:
        if upgma: raise ValueError('option outgroup cannot be set if method is UPGMA')
        sam = aln.find(outgroup)
        if sam is None: raise ValueError('invalid name for outgroup: {0}'.format(outgroup))
        outgroup = sam.index + 1
    if randomize:
        randomize = 4 * random.integer(1073741823) + 1 # PHYLIP requirement

    # write phylip files with renamed samples (only ingroup)
    with _interface.encode(aln) as name_mapping:
        f = open('infile', 'w')
        f.write(aln.phylip())
        f.close()

    # run dnadist/protdist
    if dt == 'n':
        args = ['D'] * model
        if kappa is not None: args.extend(['T', str(kappa)])
        args.append('Y')
        p = subprocess.Popen(_dnadist.get_path(), stdin=subprocess.PIPE, stdout=None if verbose else subprocess.PIPE, universal_newlines=True)
    else:
        args = ['P'] * model
        args.append('Y')
        p = subprocess.Popen(_protdist.get_path(), stdin=subprocess.PIPE, stdout=None if verbose else subprocess.PIPE, universal_newlines=True)
    p.communicate('\n'.join(args))
    if not os.path.isfile('outfile'): raise RuntimeError('an error occurred with {0}'.format('dnadist' if dt=='n' else 'protdist'))

    # run neighbor
    os.rename('outfile', 'infile')
    args = []
    if upgma: args.append('N')
    if outgroup is not None: args.extend(['O', str(outgroup)])
    if randomize != 0: args.extend(['J', str(randomize)])
    args.append('Y')
    p = subprocess.Popen(_neighbor.get_path(), stdin=subprocess.PIPE, stdout=None if verbose else subprocess.PIPE, universal_newlines=True)
    p.communicate('\n'.join(args))

    try:
        tree = _tree.Tree('outtree')
    except (ValueError, IOError):
        raise RuntimeError('cannot read neighbor output (try verbose mode)')
    for leaf in tree.iter_leaves():
        if leaf.label not in name_mapping: raise RuntimeError('unexpected error: invalid name in PHYLIP output')
        leaf.label = name_mapping[leaf.label]
    return tree
