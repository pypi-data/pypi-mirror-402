"""
    Copyright 2009-2025 Stephane De Mita, Mathieu Siol

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

import subprocess, re, os, warnings, pathlib, tarfile, pickle
from .. import _interface, _tree, alphabets
from ..tools import _code_tools
from . import _utils

_codeml_ctl_template = """
      seqfile = i
     treefile = t
      outfile = o
        noisy = 3
      verbose = 0
      runmode = 0
      seqtype = 1
    CodonFreq = {codon_freq}
        clock = 0
       aaDist = 0
        model = {model}
      NSsites = {ns_sites}
        icode = 0
        Mgene = 0
    fix_kappa = {fix_kappa}
        kappa = {kappa}
    fix_omega = {fix_omega}
        omega = {omega}
    fix_alpha = 1
        alpha = 0.0
       Malpha = 0
        ncatG = {ncatg}
        getSE = 0
 RateAncestor = 1
   Small_Diff = .5e-6
    cleandata = 0
       method = 0
"""

class _Codeml(_utils._App):

    @_utils._protect_run
    def _check_path(self, path, cfg):

        # test the "help" option to ensure that a phyml exist
        f = open('a', 'w')
        f.write('\n')
        f.close()
        cmd = (path, 'a')
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = p.communicate()
            mo = re.search(r'version (\d)\.(\d+)([a-z]?)', stdout)
            if not mo: return 'cannot read version number in CodeML output'
            M = int(mo.group(1))
            m = int(mo.group(2))
            r = mo.group(3)
        except OSError as e:
            return e.strerror

        if M != 4 or m < 8: return 'PAML version 4.8 or higher is required'
        return None

_app = _Codeml(key='codeml', default='codeml')
_utils.paths._add(_app)

_models = {

    # columns of the models table
        # description
        # value for `model` in codeml.ctl file
        # value for `NSsites` in codeml.ctl file
        # omega value fixed by model
        # required number of catgories
        # site omega: 0=none, 1=NEB, 2=BEB
        # dN and dS tree lengths
        # discrete ratios:
        #       0 (one ratio)
        #       1 (discrete)
        #       2 (branch-site A)
        #       3 (branch-site C/D)
        #       7 (beta models M7, M8)
        # require tags: 0=no, 1=yes, 2=exactly two
    # key    description             m  NS  omega ncat   w/s lens   dis tags
    'M0':   ('one ratio',            0, 0,  None, False, 0,  True,  0,  0),
    'free': ('one ratio per branch', 1, 0,  None, False, 0,  True,  0,  0),
    'nW':   ('sets of branches',     2, 0,  None, False, 0,  True,  0,  1),
    'M1a':  ('nearly neutral',       0, 1,  None, False, 1,  False, 1,  0),
    'M2a':  ('positive selection',   0, 2,  None, False, 2,  False, 1,  0),
    'M3':   ('discrete',             0, 3,  None, True,  1,  False, 1,  0),
    'M4':   ('freqs',                0, 4,  None, True,  1,  False, 1,  0),
    'M7':   ('beta',                 0, 7,  None, True,  1,  False, 7,  0),
    'M8a':  ('beta + omega=1',       0, 8,  1,    True,  1,  False, 7,  0),
    'M8':   ('beta + omega>1',       0, 8,  None, True,  2,  False, 7,  0),
    'A0':   ('null model for A',     2, 2,  1,    False, 1,  False, 2,  2),
    'A':    ('branch-site model',    2, 2,  None, False, 2,  False, 2,  2),
    'C0':   ('null model for C',     0, 22, None, False, 1,  False, 1,  0),
    'C':    ('clade model C',        3, 2,  None, False, 2,  False, 3,  1),
    'D':    ('clade model D',        3, 3,  None, True,  1,  False, 3,  1)
}

@_utils._protect_run
def codeml(align, tree, model, code=1, ncat=None, codon_freq=2,
    verbose=False, get_files=False, kappa=2.0, fix_kappa=False,
    omega=0.4, debug=None):

    r""" codeml(align, tree, model, code=1, ncat=None, codon_freq=2,
        verbose=False, get_files=False, kappa=2.0, fix_kappa=False,
        omega=0.4, debug=None)

    Fit nucleotide substitution models using `PAML <http://abacus.gene.ucl.ac.uk/software/paml.html>`_.

    This function uses the CodeML program only of the PAML package.

    :param align: an :class:`.Align` containing a coding sequence
        alignment. The number of sequences must be at least 3, the
        length of the alignment is required to be a multiple of 3
        (unless codons are provided). There must be no stop codons (even
        final stop codons) and there must not be any duplicated sequence
        name. The alphabet might be DNA of codon.

    :param tree: a :class:`.Tree` providing the phylogenetic
        relationships between samples. The name of the sequences in the
        :class:`.Align` and in the :class:`.Tree` are required to match.
        If *tree* is ``None``, a star topology is used (usage not
        recommended anymore and not supported by recent versions of
        PAML). If the tree
        contains branch length or node labels, they are discounted,
        except for PAML node tags (``#x`` and ``$x`` where ``x`` is an
        integer) that are allowed both as nodel labels. If one wants to
        label a terminal branch of the tree, they can add the label at
        the end of the sample name (with an optional separating white
        space). The tree must not be rooted (if there is a birfurcation
        at the base, an error will be caused).

    :param model: model. The list of model names appears below:

        * ``M0`` -- one-ratio model (1 parameter).
        * ``free`` -- all branches have a different ratio (1 parameter
          per branch).
        * ``nW`` -- several sets of branches. Requires labelling of
          branches of the tree (1 parameter per set of branches).
        * ``M1a`` -- nearly-neutral model (2 parameters).
        * ``M2a`` -- positive selection model (4 parameters).
        * ``M3`` -- discrete model. Requires setting *ncat*  (2 * *ncat*
          - 1 parameters).
        * ``M4`` -- frequencies model. Requires setting *ncat* (*ncat* -
          1 parameters).
        * ``M7`` -- beta-distribution model. Requires setting *ncat* (2
          parameters).
        * ``M8a`` -- beta + single ratio, additional ratio fixed to 1.
          Requires setting *ncat* (3 parameters).
        * ``M8`` -- beta + single ratio. Requires setting *ncat* (4
          parameters).
        * ``A0`` -- null branch-site model. Requires labelling of
          branches of the tree with two different labels (3 parameters).
        * ``A`` -- branch-site model with positive selection. Requires
          labelling of branches of the tree with two different labels (4
          parameters).
        * ``C0`` -- null model for model C (M2a_rel). Does not require
          branch labelling (4 parameters).
        * ``C`` -- branch-site model. Requires labelling of branches (5
          parameters).
        * ``D`` -- discrete branch-site model. Requires labelling of
          branches and requires setting *ncat* to either 2 or 3 (4 or
          6 parameters, respectively).

        The number of parameters given for each model concern the
        *dN/dS* ratios only. Refer to PAML documentation or the
        following references for more details and recommendations:
        Bielawski, J.P. & Z. Yang. 2004. A maximum likelihood method for
        detecting functional divergence at individual codon sites, with
        application to gene family evolution. *J. Mol. Evol.*
        **59**\ :121-132; Yang Z., R. Nielsen, N. Goldman & A.M.K.
        Pedersen. 2000; Codon-substitution models for heterogeneous
        selection pressure at amino acid sites. *Genetics*
        **155**\ :431-449. Yang, Z., and R. Nielsen. 2002.
        Codon-substitution models for detecting molecular adaptation at
        individual sites along specific lineages. *Mol. Biol. Evol.*
        **19**\ :908-917; Zhang, J., R. Nielsen & Z. Yang. 2005.
        Evaluation of an improved branch-site lieklihood method for
        detecting positive selection at the molecular level. *Mol. Biol.
        Evol.* **22**\ :472-2479.

    :param code: genetic code identifier (see :ref:`here <genetic-codes>`).
        Required to be an integer among the valid values. The default
        value is the standard genetic code. Only codes 1-11 are
        available.

    :param ncat: number of *dN/dS* categories. Only a subset of models
        require that the number of categories to be specified. See
        *models*.

    :param codon_freq: an integer specifying the model for codon
        frequencies. Must be one of:

         * 0 -- 1/61 each.
         * 1 -- F1X4.
         * 2 -- F3X4.
         * 3 -- codon table
         * 4 -- F1x4MG.
         * 5 -- F3x4MG.
         * 6 -- FMutSel0.
         * 7 --FMutSel.

    :param verbose: boolean indicating whether standard output of CodeML
        should be displayed.

    :param get_files: boolean indicating whether the raw content of
        CodeML output files should be included in the returned data.

    :param kappa: starting value for the transition/transversion
        rate ratio.

    :param fix_kappa: tell if the transition/transversion rate ratio
        should be fixed to its starting value (otherwise, it is
        estimated as a free parameter).

    :param omega: starting value for the *dN/dS* ratio (strictly
        positive value).

    :param debug: if not ``None``, name of a tarfile (potentially
        compressed) for CodeML's output files. If the archive doesn't
        exist, the program is executed and the output files needed for
        further processing are included in the the archive before
        attempting to analyse them (the analysis might result in a crash
        if there is unexpected formatting of output files). If the
        archive exists, the program is not executed; instead, output
        files are extracted from the archive and analysed.

    .. deprecated:: 3.3.1
        The star topology option is still supported but raise a
        UserWarning since it can cause an error with recent
        versions of PAML.

    :return: A :class:`dict` holding results. The keys defined in the
        returned dictionary are:

        * ``model`` -- model name.
        * ``lk`` -- log-likelihood.
        * ``np`` -- number of parameters of the model.
        * ``kappa`` -- fixed or estimated value of the
          transition/transversion rate ratio.
        * ``beta`` -- if model is ``M7``, ``M8a``, or ``M8``, a
          :class:`tuple` with the *p* and *q* parameters of the beta
          distribution of neutral dN/dS ratios; otherwise, ``None``.
        * ``K`` -- number of dN/dS ratio categories. Equals to 0 for the
          ``free`` model, to the number of branch categories for the
          ``nW`` model, and to the number of site categories otherwise.
          This value is not necessarily equal to the *ncat* argument
          because ``M8a`` and ``M8`` models add a category, and because
          it has a different meaning for model ``nW``.
        * ``num_tags`` -- number of branch categories detected from the
          imported tree (irrespective to the model that has been
          fitted). If the star topology has been used (``tree=None``),
          this value is 1.
        * ``omega`` -- estimated dN/dS ratio or ratios. The structure of
          the value depends on the model:

          * ``M0`` model -- a single value.
          * ``free`` model -- ``None`` (ratios are available as node
            labels in the tree available as ``tree_ratios``).
          * ``nW`` model -- a :class:`list` of dN/dS ratios for all
            branch categories (they are listed in the order
            corresponding to branch labels).
          * Discrete models (``M1a``, ``M2a``, ``M3``, ``M4``, ``C0``,
            ``M7``, ``M8a``, and ``M8``) -- a :class:`!list` of ``K``
            dN/dS ratios. The frequency of each dN/dS category is
            available is ``freq``.
          * ``A0`` and ``A`` models -- a :class:`!tuple` of two
            :class:`!list` of 4 items each, containing respectively the
            background and foreground dN/dS ratios. The frequency of
            each dN/dS category is available is ``freq``.
          * ``C`` and ``D`` models -- a :class:`!tuple` of ``num_tags``
            :class:`!list` (one :class:`!list` for each set of branches,
            as defined by branch labels found in the provided tree),
            each of them containing ``K`` dN/dS ratios.  The frequency
            of each dN/dS category is available is ``freq``.

        * ``freq`` -- the frequency of dN/dS ratio categories. If
          defined, it is a :class:`!list` of ``K`` values. This entry is
          ``None`` for models ``M0``, ``free``, and ``nW``.
        * ``length`` -- total length of tree after estimating branch
          lengths with the specified model.
        * ``tree`` -- the tree with fitted branch lengths, as a
          :class:`.Tree` instance. Branch lengths are expressed in terms
          of the model of codon evolution.
        * ``length_dS`` -- total length of tree in terms of synonymous
          substitutions. Only available with ``M0``, ``free``, and
          ``nW`` models.
        * ``length_dN`` -- total length of tree in terms of
          non-synonymous substitutions. Only available with ``M0``,
          ``free``, and ``nW`` models.
        * ``tree_dS`` -- a :class:`!Tree` instance with branch lengths
          expressed in terms of synonymous substitutions. Only available
          with ``free`` and ``nW`` models.
        * ``tree_dN`` -- a :class:`!Tree` instance with branch lengths
          expressed in terms of non-synonymous substitutions. Only
          available with ``free`` and ``nW`` models.
        * ``tree_ratios`` -- a :class:`!Tree` instance with the dN/dS
          ratios included as branch labels. Only available with ``free``
          and ``nW`` models.
        * ``site_w`` -- a :class:`!dict` containing posterior predictions
          of site dN/dS ratios. Not available for models ``M0``,
          ``free``, and ``nW`` (in that cases, the value is ``None``).
          The :class:`!dict` contains the following keys:

          * ``method`` -- on the strings ``NEB`` and ``BEB``.
          * ``aminoacid`` -- the list of reference amino acids for all
            amino acid sites of the alignment (they are taken from the
            first sequence in the original alignment).
          * ``proba`` -- the list of posterior probabilites of the dN/dS
            categories for all amino acid sites of the alignment. For
            each site, a :class:`!tuple` of ``K`` (the number of dN/dS
            categories) is provided.
          * ``best`` -- the index of the best category for each site.
          * ``postw`` -- list of the posterior dN/dS estimate for all
            sites (``None`` if not available).
          * ``postwsd`` -- list of the standard deviation of the dN/dS
            estimate for all sites (always available if ``postw`` is
            available and the method is ``BEB``, ``None`` otherwise).
          * ``P(w>1)`` -- probability that the dN/dS ratio is greater
            than 1 for all sites (``None`` if not available).

        * ``main_output`` -- raw content of the main CodeML output file.
          This key is not present if the option *get_files* is not set
          to ``True``.
        * ``rst_output`` -- raw content of the ``rst`` detailed CodeML
          output file. This key is not present if the option *get_files*
          is not set to ``True``.
        * ``candidates`` - list of positively selected sites. Each site
          is represented by a :class:`!dict` with keys ``pos`` (0-based
          position), ``aa`` (reference amino acid), ``P(w>1)``, ``test`
          (test result, either an empty string or a signification-level
          string), ``postw`` and ``stdev`` (standard deviation). If the
          block is not present in the output file, the list is replaced
          by None``.

    .. versionchanged:: 3.0.0

        Turned into a singe function, interface changes (more models,
        more options, more results).

    .. versionchanged:: 3.3.1

        Raise a warning if ``tree`` is set to ``None`` (star topology).

    .. versionchanged:: 3.3.4

        Support alignement gaps in reference sequence and export list of
        positively selected sites.

    .. versionadded:: 3.5.0

        *debug* option.
    """

    # check archive name
    if debug is not None:
        debug_p = pathlib.Path(debug)
        if not debug_p.is_absolute():
            debug_p  = pathlib.Path(
                _utils._protect_path_mapping[str(pathlib.Path.cwd())], debug_p)
        if '.tar' not in debug_p.suffixes:
            raise ValueError('debug option must be a [compressed] tarfile')

        # if archive is there, fetch files and skip program
        if debug_p.exists():
            if verbose: print(f'skip CodeML and get results from {debug}')
            if not tarfile.is_tarfile(debug_p):
                raise ValueError(f'cannot extract data from {debug}')
            f = tarfile.open(debug_p)
            f.extractall(members=['o', 'rst'], filter='data') # data filter will be default in Python 3.14
            f.close()

    # otherwise prepare to run the program
    if debug is None or not debug_p.exists():
        # check that program is available
        path = _app.get_path()
        if path is None:
            raise RuntimeError('PAML\'s codeml program not available -- please configure path')

    # process input alignment
    if not isinstance(align, _interface.Align): raise TypeError('`align` must be an Align instance')
    if len(align) < 3: raise ValueError('not enough sequences in alignment')
    if align._alphabet._obj.get_type() == 'DNA':
        if align.ls < 3 or align.ls % 3 != 0: raise ValueError('alignment length must be a multiple of 3')
        ls = align.ls // 3
    elif align._alphabet._obj.get_type() == 'codons':
        ls = align.ls
    else:
        raise ValueError('invalid alphabet for coding sequences')

    # get code
    if code not in _code_tools._codes: raise ValueError('unknown genetic code: {0}'.format(code))
    if code > 11: raise ValueError('unsupported genetic code: {0}'.format(code))
    _code = _code_tools._codes[code]

    # check for stop codons
    if _code_tools.has_stop(align, code=code): raise ValueError('stop codon found in sequences')

    # write down alignment
    mapping = {}
    _utils._write(align, 'i', mapping)

    # revert mapping
    rmapping = {}
    for key, sample in mapping.items():
        if sample.name == '':
            raise ValueError('alignment contains an empty-string name')
        if sample.name in rmapping:
            raise ValueError('alignment contains duplicates: {0}'.format(sample.name))
        rmapping[sample.name] = key

    # check and print tree
    tags = set()
    if tree is None:
        warnings.warn("star topology is discouraged and is likely to cause "
            "an error with recent versions of PAML", UserWarning)
        f = open('t', 'w')
        f.write(f' {len(mapping)} 1\n') 
        f.write('(' + ','.join(mapping) + ');\n')
        f.close()
        tags.add(0)
    else:
        tree = tree.copy() # make copy to allow modify it
        if tree.base.num_children < 3: raise ValueError('tree must not be rooted')
        if tree.num_leaves != len(rmapping): raise ValueError('number of sequences does not match with tree')
        for node in tree.depth_iter():
            # if terminal node, allow label to be: "name[[]#|$tag]"
            if node.num_children == 0:
                mo = re.match(r'(.+?)(?: ?([\#|\$])(\d+))?$', node.label)
                if mo is None: raise ValueError('invalid name in tree: {0}'.format(node.label))
                name, symb, tag = mo.groups()
                if name not in rmapping: raise ValueError('name in tree does not match with sequence names: {0}'.format(name))
                if tag is None: node.label = rmapping[name]
                else: node.label = rmapping[name] + ' ' + symb + tag

            # if internal node, allow None, an integer (that it deleted), or #|$tag
            elif node.num_children > 1:
                tag = None
                if node.label is None: pass
                elif isinstance(node.label, int): node.label = None
                else:
                    mo = re.match(r'[\#|\$](\d+)$', node.label)
                    if mo is None: raise ValueError('invalid internal node label: {0}'.format(node.label))
                    tag = mo.group(1)

            # safety check
            else: raise ValueError('invalid tree structure')

            # manage tag
            if tag is None: tags.add(0)
            else: tags.add(int(tag))

        if sorted(tags) != list(range(len(tags))): raise ValueError('invalid tree labels (labels must start from 0 and must be consecutive)')
        f = open('t', 'w')
        f.write(f' {len(mapping)} 1\n') 
        f.write(tree.newick(skip_brlens=True) + '\n')
        f.close()

    # check model
    if model not in _models: raise ValueError('invalid model name: {0}'.format(model))
    doc, mod, ns, w, req_ncat, has_beb, has_treelen, discrete, req_tags = _models[model]
    if model == 'D' and ncat != 2 and ncat != 3: raise ValueError('`ncat` must be set to 2 or 3 when used with model D')
    if req_ncat:
        if ncat is None: raise ValueError('required `ncat` not specified')
        if not isinstance(ncat, int): raise TypeError('`ncat` must be an integer')
        if ncat < 2: raise ValueError('`ncat` must be at least 1')
    else:
        ncat = 0 # should be ignored
    if req_tags > 0 and len(tags) < 2: raise ValueError('model {0} requires at least two different tags in tree'.format(model))
    if req_tags == 2 and len(tags) != 2: raise ValueError('model {0} requires exactly two different tags in tree'.format(model))

    # check other arguments
    if codon_freq not in {0, 1, 2, 3, 4, 5, 6, 7}: raise ValueError('invalid value for `codon_freq` argument')
    if kappa <= 0.0: raise ValueError('invalid value for `kappa` argument')
    if omega <= 0.0 or omega >= 89.0: raise ValueError('invalid value for `omega` argument')

    # run the program only if not debug file or debug not created
    if debug is None or not debug_p.exists():

        # create control file
        if w == None:
            w = omega
            fix_omega = 0
        else:
            fix_omega = 1

        ctl =  _codeml_ctl_template.format(codon_freq=codon_freq,
                                           model=mod,
                                           ns_sites=ns,
                                           fix_omega=fix_omega,
                                           omega=w,
                                           ncatg=ncat,
                                           fix_kappa=1 if fix_kappa else 0,
                                           kappa=kappa)

        f = open('codeml.ctl', 'w')
        f.write(ctl)
        f.close()

        # run codeml
        p = subprocess.Popen((path, 'codeml.ctl'), stdin=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdout=(None if verbose else subprocess.PIPE), universal_newlines=True)
        stdout, stderr = p.communicate()

        # check error
        stderr = stderr.strip()
        if len(stderr):
            raise RuntimeError('error while running codeml: {0}'.format(stderr))
        if not os.path.isfile('rst') or not os.path.isfile('o'):
            raise RuntimeError('unknown error while running codeml (try running in verbose mode)')

        # backup archive
        if debug is not None:
            f = tarfile.open(debug_p, 'w')
            f.add('o')
            f.add('rst')
            f.close()

    # get data from main output file
    final = {'model': model, 'num_tags': len(tags)}
    locals_d = locals()
    ret = _helper_main(locals_d, final)
    if ret != 0: raise ValueError('cannot read results from codeml output file (try running in verbose mode) [code: {0}]'.format(ret))

    # get data from rst file
    _helper_rst(locals_d, final)

    # return
    return final

def _helper_main(variables, res):
    f = open('o')
    main = f.read()
    f.close()
    if variables['get_files']: res['main_output'] = main

    # lnL & np
    mo = re.search(r'lnL\(ntime: ?.+  np: ?(.+)\): *(.+) +\+.+', main)
    if mo is None: return 1
    np, lnL = mo.groups()
    res['np'] = int(np)
    res['lnL'] = float(lnL)

    # kappa
    if not variables['fix_kappa']:
        mo = re.search(r'kappa \(ts/tv\) = +(.+)', main)
        if mo is None: return 2
        res['kappa'] = float(mo.group(1))
    else:
        mo = re.search(r'kappa = (.+) fixed', main)
        if mo is None: return 7
        res['kappa'] = float(mo.group(1))

    # dN and dS tree lengths
    if variables['has_treelen']:
        mo = re.search(r'tree length for dN: +(.+)', main)
        if mo is None: return 3
        res['length_dN'] = float(mo.group(1))

        mo = re.search(r'tree length for dS: +(.+)', main)
        if mo is None: return 4
        res['length_dS'] = float(mo.group(1))
    else:
        res['length_dN'] = None
        res['length_dS'] = None

    # omega or omega classes
    if variables['model'] == 'free':
        res['omega'] = None
        res['freq'] = None
        res['K'] = 0

    elif variables['model'] == 'nW':
        reg = r'^w \(dN/dS\) for branches:' + r' +([\.\dEe]+)' * len(variables['tags']) + '$'
        mo = re.search(reg, main, re.MULTILINE)
        if mo is None: return 12
        res['omega'] = tuple(map(float, mo.groups()))
        res['freq'] = None
        res['K'] = len(res['omega'])

    elif variables['discrete'] == 0:
        mo = re.search(r'omega \(dN/dS\) = +(.+)', main)
        if mo is None: return 5
        res['omega'] = float(mo.group(1))
        res['freq'] = None
        res['K'] = 1

    else:
        mo = re.search(r'dN/dS \(w\) for site classes \(K=(\d+)\)', main)
        if mo is None: return 6
        K = int(mo.group(1))
        res['K'] = K

        if variables['discrete'] == 1:
            reg = '^p:' + ''.join([r' +([\.\dEe]+)']*K) + '\\n' + 'w:' + ''.join([r' +([\.\dEe]+)']*K) + '$'
            mo = re.search(reg, main, re.MULTILINE)
            if mo is None: return 7
            grp = mo.groups()
            res['freq'] = tuple(map(float, grp[:K]))
            res['omega'] = tuple(map(float, grp[K:]))

        elif variables['discrete'] == 2:
            if K != 4: return 8
            reg = r"""^site class +0 +1 +2a +2b
proportion +([\.\dEe]+) +([\.\dEe]+) +([\.\dEe]+) +([\.\dEe]+)
background w +([\.\dEe]+) +([\.\dEe]+) +([\.\dEe]+) +([\.\dEe]+)
foreground w +([\.\dEe]+) +([\.\dEe]+) +([\.\dEe]+) +([\.\dEe]+)$"""
            mo = re.search(reg, main, re.MULTILINE)
            if mo is None: return 9
            grp = mo.groups()
            res['freq'] = tuple(map(float, grp[:4]))
            res['omega'] = tuple(map(float, grp[4:8]), map(float, grp[8:]))

        elif variables['discrete'] == 3:
            reg = []
            reg.append('^site class' + ''.join([' +{0}'.format(i) for i in range(K)]))
            reg.append('proportion' + ' +([\.\dEe]+)' * K)
            for i in range(len(variables['tags'])):
                reg.append('branch type {0}:'.format(i) + ' +([\.\dEe]+)' * K)
            reg = '\\n'.join(reg)
            reg += '$'
            mo = re.search(reg, main, re.MULTILINE)
            if mo is None: return 10
            grp = mo.groups()
            res['freq'] = tuple(map(float, grp[:K]))
            res['omega'] = tuple(tuple(map(float, grp[K+i*K:2*K+i*K])) for i in range(len(variables['tags'])))

        elif variables['discrete'] == 7:
            reg = '^p:' + r' +([\.\dEe]+)' * K + '\\n' + 'w:' + r' +([\.\dEe]+)' * K + '$'
            mo = re.search(reg, main, re.MULTILINE)
            if mo is None: return 11
            grp = mo.groups()
            res['freq'] = tuple(map(float, grp[:K]))
            res['omega'] = tuple(map(float, grp[K:]))

        else:
            return 99

    # beta distribution parameters
    if variables['model'] == 'M7':
        reg = r'^Parameters in M7 \(beta\):\n p = +([\.\dEe]+)  q = +([\.\dEe]+)$'
        mo = re.search(reg, main, re.MULTILINE)
        if mo is None: return 13
        res['beta'] = float(mo.group(1)), float(mo.group(2))
    elif variables['model'] == 'M8a' or variables['model'] == 'M8':
        reg = r"""^Parameters in M8 \(beta&w>1\):
  p0 = +[\.\dEe]+  p = +([\.\dEe]+) q = +([\.\dEe]+)
 \(p1 = +[\.\dEe]+\) w = +[\.\dEe]+$"""
        mo = re.search(reg, main, re.MULTILINE)
        if mo is None: return 14
        res['beta'] = float(mo.group(1)), float(mo.group(2))
    else:
        res['beta'] = None

    # tee length and tree with branch lengths
    reg = r"""^tree length = +([\.\dEe]+)

(\([ (),\-\.\d:eqs]+\);)

(\([ (),\-\.\d:eqs]+\);)$"""
    mo = re.search(reg, main, re.MULTILINE)
    if mo is None: return 15
    res['length'] = float(mo.group(1))
    res['tree'] = _tree.Tree(string=mo.group(3))
    for leaf in res['tree'].iter_leaves(): leaf.label = variables['mapping'][leaf.label].name

    # dN/dS and w-ratio-labelled trees
    if variables['model'] == 'nW' or variables['model'] == 'free':

        reg = r"""^dS tree:
(\([ (),\-\.\d:eqs]+\);)
dN tree:
(\([ (),\-\.\d:eqs]+\);)

w ratios as labels for TreeView:
(\([# (),\-\.\d:eqs]+\);)$"""
        mo = re.search(reg, main, re.MULTILINE)
        if mo is None: return 16
        res['tree_dS'] = _tree.Tree(string=mo.group(1))
        res['tree_dN'] = _tree.Tree(string=mo.group(2))
        for leaf in res['tree_dS'].iter_leaves(): leaf.label = variables['mapping'][leaf.label].name
        for leaf in res['tree_dN'].iter_leaves(): leaf.label = variables['mapping'][leaf.label].name
        res['tree_ratios'] = _tree.Tree(string=mo.group(3))

    else:
        res['tree_dS'] = None
        res['tree_dN'] = None
        res['tree_ratios'] = None

    return 0

def _helper_rst(variables, res):

    f = open('rst')
    rst = f.read()
    f.close()
    if variables['get_files']: res['rst_output'] = rst

    if variables['has_beb'] == 0:
        res['site_w'] = None

    else:

        # make the whole-block regular expression
        method_full = 'Naive' if variables['has_beb'] == 1 else 'Bayes'
        method = method_full[0] + 'EB'

        reg = [r'^{0} Empirical Bayes \({0[0]}EB\) probabilities for (\d+) classes( \(class\))?( & postmean_w)?( & P\(w>1\))?'.format(method_full)]
        reg.append(r'\(amino acids refer to 1st sequence: seq-1\)')
        reg.append('')

        nsites = variables['ls']
        for i in range(nsites):
            reg.append(' *{0} +[A-Z-].+'.format(i+1))

        # positively selected sites block (suggested by Florent Marchal)
        reg.append('(?:\nPositively selected sites\n\n\tProb\\(w>1\\) +mean w\n\n((?: +\\d+ +[A-Z-] +\\d\\.\\d+\\** +\\d+\\.\\d+(?: +\\+- +\\d+\\.\\d+)\n)*))?')
        reg = '\n'.join(reg)
        reg += '$'

        mo = re.search(reg, rst, re.MULTILINE)

        if not mo: raise ValueError('cannot find {0} results in rst file'.format(method))

        hit = mo.group(0)
        K = int(mo.group(1))
        if method == 'BEB' and mo.group(2) is None: raise ValueError('inconsistency in BEB output')
        post_mean = mo.group(3) is not None
        post_test = mo.group(4) is not None
        if post_test and not post_mean: raise ValueError('unexpected case in {0} output'.format(method))
        if post_test and post_mean and method=='BEB': raise ValueError('unexpected case in BEB output')
        candidates = mo.group(5)
        if candidates is not None:
            candidates = candidates.strip()

        # initialize the result dict
        res['site_w'] = {
            'method': method,
            'aminoacid': [],
            'proba': [],
            'best': [],
            'postw': None,
            'postwsd': None,
            'P(w>1)': None,
        }
        if post_mean:
            res['site_w']['postw'] = []
            if method == 'BEB': res['site_w']['postwsd'] = []
            if post_test: res['site_w']['P(w>1)'] = []

        # get the posterior predictions for each site
        templ = r'^ *{0} ([A-Z-])' + ' +([\.\dEe]+)' * K + ' \( *(\d+)\)'
        if post_mean:
            if method == 'NEB': templ += r' +([\.\dEe]+)'
            else: templ += r' +([\.\dEe]+) \+- +([\.\dEe]+)'
            if post_test: templ += r' +([\.\dEe]+)'
        templ += '$'

        for i in range(nsites):
            mo = re.search(templ.format(i+1), hit, re.MULTILINE)
            if mo is None: raise ValueError('cannot find {0} results for site {1}'.format(method, i+1))
            hits = mo.groups()
            base = hits[0]
            proba = tuple(map(float, hits[1:K+1]))
            best = int(hits[K+1]) - 1
            res['site_w']['aminoacid'].append(base)
            res['site_w']['proba'].append(tuple(proba))
            res['site_w']['best'].append(best)
            if post_mean:
                postw = float(hits[K+2])
                res['site_w']['postw'].append(postw)
                if method == 'BEB':
                    postwsd = float(hits[K+3])
                    res['site_w']['postwsd'].append(postwsd)
                    if len(hits) != K+4: raise ValueError('error while reading BEB result for site {0}'.format(i+1))
                elif post_test:
                    P = float(hits[K+3]) # we have tested that BEB must be false
                    res['site_w']['P(w>1)'].append(P)
                    if len(hits) != K+4: raise ValueError('error while reading {0} result for site {1}'.format(method, i+1))
                else:
                    if len(hits) != K+3: raise ValueError('error while reading {0} result for site {1}'.format(method, i+1))
            elif len(hits) != K+2: raise ValueError('error while reading {0} result for site {1}'.format(method, i+1))

        # get list of positively selected sites
        if candidates is None:
            res['candidates'] = None
        else:
            res['candidates'] = []
            for site in candidates.split('\n'):
                bits = site.split()
                if len(bits) == 6:
                    pos, aa, proba, postw, pm, stdev = bits
                    if pm != '+-': raise ValueError('error while reading list of positively selected sites')
                elif len(bits) == 4:
                    pos, aa, proba, postw = bits
                    stdev = None
                elif len(bits) == 0:
                    continue
                else:
                    raise ValueError('error while reading list of positively selected sites')
                proba, sign = re.match(r'(\d\.\d+)(\**)$', proba).groups()
                res['candidates'].append({
                    'pos': int(pos) - 1,
                    'aa': aa,
                    'P(w>1)': float(proba),
                    'significant': sign,
                    'site_w': float(postw),
                    'stdev': None if stdev is None else float(stdev) })
