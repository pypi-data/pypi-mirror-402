********************************
Integration of external software
********************************

---------
Principle
---------

EggLib provides wrappers of external programs in order to extend its
functionalities besides its own population genetics and sequence
management tools (although providing a wide array of external tools
is not one of the primary aims of EggLib).

The available tools are presented through an integrated interface: once
configured, they can be used as any regular EggLib function, using
objects from EggLib class as argument and/or return values.

Currently, the :ref:`wrappers <wrappers>` module provides:

* Multiple sequence alignment using `Clustal Omega <http://www.clustal.org/>`_ and `MUSCLE <https://www.drive5.com/muscle/>`_.
* Maximum-likelihood phylogeny using `PhyML <http://www.atgc-montpellier.fr/phyml/>`_.
* Maximum-likelihood fitting and testing of coding sequence evolution
  using ``CodeML`` from the `PAML <http://abacus.gene.ucl.ac.uk/software/paml.html>`_ package.
* Distance-based phylogeny using ``dnadist``, ``protdist`` and ``neighbor`` from the `PHYLIP <https://evolution.genetics.washington.edu/phylip.html>`_ package.
* Basic Local Alignment using  ``blastn``, ``blastp``, ``blastx``, ``tblastn``, ``tblastx`` and ``makeblastdb``
  from the `BLAST+ <https://blast.ncbi.nlm.nih.gov/Blast.cgi>`_ standalone package.

The requested programs must be installed separately.

-----
Usage
-----

Configuration of application paths
==================================

By default, all applications are disabled. Any attempt to use any :ref:`wrappers <wrappers>`
function will cause a :exc:`RuntimeError` as in the example below::

    >>> import egglib
    >>> cnt = egglib.io.from_fasta('sequences3.fas', cls=egglib.Container, alphabet=egglib.alphabets.DNA)
    >>> aln = egglib.wrappers.clustal(cnt)
    [traceback omitted]
    RuntimeError: Clustal Omega program not available -- please configure path

There is a :ref:`paths <paths>` object in the :ref:`wrappers <wrappers>` module
which is responsible for holding the command executing the external applications.
The applications are identified by these keys:

+---------------+-----------------------+
| Key           | Application           |
+===============+=======================+
| ``clustal``   | Clustal Omega         |
+---------------+-----------------------+
| ``muscle``    | MUSCLE                |
+---------------+-----------------------+
| ``phyml``     | PhyML                 |
+---------------+-----------------------+
| ``codeml``    | CodeML (PAML package) |
+---------------+-----------------------+
| ``dnasdist``  | dnadist (PHYLIP)      |
+---------------+-----------------------+
| ``protdist``  | protdist (PHYLIP)     |
+---------------+-----------------------+
| ``neighbor``  | neighbor (PHYLIP)     |
+---------------+-----------------------+
| ``blastn``    | blastn (BLAST+)       |
+---------------+-----------------------+
| ``blastp``    | blastp (BLAST+)       |
+---------------+-----------------------+
| ``blastx``    | blastx (BLAST+)       |
+---------------+-----------------------+
| ``tblastn``   | tblastn (BLAST+)      |
+---------------+-----------------------+
| ``tblastx``   | tblastx (BLAST+)      |
+---------------+-----------------------+
|``makeblastdb``| makeblastdb (BLAST+)  |
+---------------+-----------------------+


We can see that the default value is ``None``::

    >>> print(egglib.wrappers.paths['clustal'])
    None

This object can be configured using the command-line tools ``egglib-config``,
as described in :ref:`paths`. The approach for editing paths from Python
scripts is described below.

Auto-detection of applications
******************************

The method :meth:`~.wrappers.paths.autodetect` tries a set of
pre-defined commands and, if any works, set it as the command to run the
corresponding application::

    >>> egglib.wrappers.paths.autodetect(verbose=True)
    > codeml: codeml --> ok
    > phyml: phyml --> fail ("No such file or directory")
    > clustal: clustalo --> fail ("No such file or directory")
    > muscle: muscle --> ok

This method has a *verbose* option which provide you with information (success
or failure, and message error in case of failure). In case of a failure, the
corresponding application is disabled but this is not treated as an error.

In this example, the default commands ``codeml`` and ``muscle`` succeeded, so the
two applications are now available. But the command for Clustal Omega was
not successful, either because the program is not installed, or not installed under
this name. As a result, it is still not available::

    >>> print(egglib.wrappers.paths['clustal'])
    None

Of course, this result is dependent on system configuration and properties.

Setting application paths manually
**********************************

It is possible to specify a command string (including the full path of
the program executable) for any application. Assume that we have compiled
Clustal Omega, but did not install it in the binary search path (the
executable remains in the user's home directory). We can set the path as
follows::

    >>> egglib.wrappers.paths['clustal'] = '/home/user/data/software/clustal-omega-1.2.1/src/clustalo'
    >>> print(egglib.wrappers.paths['clustal'])
    /home/user/data/software/clustal-omega-1.2.1/src/clustalo

If the path is incorrect, or if the specified command does not run as
expected for this software, an error will be caused.

Saving and loading paths
************************

Once paths have been set satisfactorily, it is possible to save them in
a system file in order to have them available for the next session. When
EggLib is imported again, the saved paths will be loaded and the
properly configured application will be immediately usable. In case a
program has been removed, it will cause an error when attempting to run it.
The command to save paths is::

    >>> egglib.wrappers.paths.save()

If the paths has been modified during a session, it is still possible 
to reset the paths from the saved configuration, discarding any changes 
that have been applied since EggLib has been imported, by running::

    >>> egglib.wrappers.paths.load()

Using applications in scripts
=============================

This manual and the reference manual explain how to use the functions
calling the external applications
and they are aimed at users who are already experienced with these programs.
It can be necessary to refer their own documentation to understand the
meaning of available options and returned data.

Note that, for all wrappers, there is a ``verbose`` option to control
whether or not the program output should be displayed on screen or deleted.

PhyML
*****

PhyML is a software for maximum-likelihood phylogenetic reconstruction
using amino acid or nucleotide sequences. It is available through the
function :func:`.wrappers.phyml` (reference included in the documentation).
The usage is fairly straightforward: it takes an :class:`.Align` object
as argument and returns a :class:`tuple` with two items (the phylogenetic
tree as a :class:`.Tree` object and a dictionary of statistics, respectively)::

    >>> aln = egglib.io.from_fasta('align8.fas',alphabet=egglib.alphabets.DNA)
    >>> tree, stats = egglib.wrappers.phyml(aln, model='HKY85')
    >>> print(stats)
    {'freqs': [0.2844, 0.19657, 0.22759, 0.29143], 'ti/tv': 4.0, 'pars': 6983, 'lk': -33416.88715, 'size': 5.44449}
    >>> print(tree.newick())
    (CasLYK3:0.01237505,CasLYK2:0.0,((FvLYK2:0.09853004,(MdLYK3:0.10732566,PpLYK3:0.05300631):0.02447224):0.05989021,(PtLYK3:0.15268966,((MtLYK8:0.14003722,(LjLYS7:0.08155174,(GmLYK3:0.04846372,CacLYK3:0.05809886):0.04392275):0.02845355):0.11447351,((VvLYK3:0.11542039,VvLYK2:0.08334382):0.06445392,(VvLYK1:0.12763572,((PtLYK2:0.05871896,PtLYK1:0.03968281):0.11719099,((((CacLYK1:0.0760468,(GmNFR1a:0.03511832,GmNFR1b:0.0287519):0.02035824):0.03344143,(LjNFR1a:0.07231443,(MtLYK2:0.04784824,(MtLYK3:0.07366331,PsSYM37:0.06907117):0.01683888):0.05128711):0.02178421):0.14129609,((CecLYK1:0.1342407,((MtLYK7:0.11288812,(CacLYK4:0.05284059,GmLYK2:0.048187):0.05687575):0.04162164,((MtLYK1:0.13291815,LjNFR1b:0.11749646):0.06448685,(MtLYK6:0.13391465,LjNFR1c:0.11699053):0.03439881):0.02680216):0.04837524):0.03794071,(CecLYK2:0.07421816,((GmLYK2b:0.05222029,CacLYK2:0.07144586):0.05212459,(LjLYS6:0.05742719,MtLYK9:0.10847179):0.02814181):0.06743708):0.01846505):0.02443726):0.05441246,(CasLYK1:0.10100211,(AtCERK1:0.35336624,(FvLYK1:0.12483414,((MdLYK2:0.05670659,MdLYK1:0.03964285):0.04192224,(PpLYK1:0.06030315,PpLYK2:0.05194511):0.02388192):0.03157062):0.04509856):0.01641018):0.02078968):0.02797866):0.04205346):0.06152622):0.05814891):0.02685265):0.02416823):0.14995695);

Besides the input sequence alignment, this function takes an array of option.
Only one is required (``model``, the model name). See the reference manual
for the function for details. Most of the options are passed to the software.

The phylogenetic tree is returned as the first item of the return value.
It is an object of the EggLib class :class:`.Tree`, which supports a wide
a range of editing operation (management of internal nodes, subtree extraction,
search for phylogenetic clades). The second item is a dictionary of statistics
including maximum-likelihood estimates of model parameters. See the function
manual for details.

CodeML
******

CodeML is one of the program included in the PAML software package, a widely use
collection of tools for the analysis of the evolution of biological sequences.
The :func:`.wrappers.codeml` function of EggLib focuses on the tools describing
the evolution of coding sequences.

To be used, this tools requires an alignment of coding sequences (in particular
with an alignment length which is a multiple of 3), and a phylogenetic tree whose
leaves names match the sequence names. Let us assume that this is what we
have with the alignment imported in the previous example. We also have built
the phylogenetic with PhyML already. Let us check that the number of samples
matches and that the alignment length is a multiple of 3::

    >>> print(aln.ns, tree.num_leaves)
    17 17
    >>> print(aln.ls)
    270

Note that it is also necessary to ensure that there are no stop codons in the
alignment and that the list of names match exactly. In addition, the tree must
not be rooted (the base must be a trifurcation, which is the standard for
trees reconstructed by maximum likelihood). This being said, to
run PhyML, we only need an :class:`!Align` object, a :class:`!Tree` object,
and the name of one of the models::
    
    >>> aln = egglib.tools.to_codons(aln)
    >>> results = egglib.wrappers.codeml(aln, tree, 'M1a')
    >>> print(results['lnL'])
    -2081.576434
    >>> print(results['omega'])
    [0.0905, 1.0]
    >>> print(results['freq'])
    [0.84535, 0.15465]
    >>> print(results['site_w']['postw'])
    [0.091, 0.091, 0.091, 1.0, 0.092, 0.094, 0.091, 0.091, 0.092, 0.107, 0.158, 0.092, 0.112, 0.091, 0.311, 0.091, 0.091, 0.091, 0.091, 0.091, 0.093, 0.136, 0.753, 0.092, 0.603, 0.939, 0.091, 0.091, 0.38, 0.093, 0.091, 0.1, 0.093, 0.097, 0.091, 0.092, 1.0, 0.091, 0.091, 0.091, 0.997, 0.091, 0.093, 0.091, 0.322, 0.092, 0.091, 0.091, 0.091, 0.092, 0.092, 0.091, 0.092, 0.093, 0.091, 0.091, 0.092, 0.091, 0.091, 0.091, 0.129, 0.092, 0.127, 0.091, 0.091, 0.091, 0.092, 0.987, 0.091, 0.168, 0.092, 0.213, 0.689, 0.989, 0.399, 0.997, 0.992, 0.093, 0.134, 0.985, 0.092, 0.099, 0.925, 0.091, 0.104, 0.102, 0.091, 0.091, 0.092, 0.091]

Please refer to the manual of the :func:`.wrappers.codeml` function for
a detailed list of options (including the list of available models), and
the list of returned data. The return value is a :class:`!dict` containing
a large number of entries exposing most of the contents of CodeML output.

In this example we displayed the log-likelihood of the model (``lnL``), the
non-synonymous to synonymous rate ratio, or :math:`\omega` for the two rate
categories (``omega``), the corresponding category frequencies (``freq``),
and the list of posterior :math:`\omega` per-site estimates for the
amino acid sites (since the DNA alignment length is 270, there are 90
amino acid sites).

In the specific case of branch- and clade-models (with or without site
variability), CodeML expects that the phylogenetic tree contains internal
node labels to identify branches (``#x``, where ``x`` is an integer) and
clades (``$x``) that should have a different :math:`\omega` rate. If these
labels are present in a Newick-formatted tree file, they will be imported
properly by the constructor of :class:`.Tree`. Otherwise, it is also
possible to add them dynamically using the methods of :class:`.Tree` objects
(such as :meth:`~.Tree.find_clade` and the property :py:obj:`~.Node.label` of :class:`.Node` instances).

Clustal Omega and Muscle
************************

These are two multiple sequence alignment programs both supporting nucleotide
and amino acid sequences. In both cases, alignment of sequences provided as
a :class:`.Container` object to a resulting :class:`.Align` object is fairly
straightforward::

    >>> aln1 = egglib.wrappers.clustal(cnt)
    >>> aln2 = egglib.wrappers.muscle(cnt)

These examples leave all other options to default values. Actually, both
wrappers provide a lot of options, thereby exposing the flexibility of these
two software tools. The options differ significantly between them, reflecting
their different paradigms. Please refer to the manual of the two functions
:func:`.wrappers.clustal` and :func:`.wrappers.muscle` (and of course the
user's guide of the two programs) for a detailed list of the available
options.

.. note::

    There are separate wrappers for ``MUSCLE`` version 3 and version 5,
    named :func:`~.wrappers.muscle3` and :func:`~.wrappers.muscle5`. They
    have different sets of options because the versions of the program
    are different. ``MUSCLE`` 5 is the current, improved version, but the
    wrapper for version 3 is maintained in hope it might be useful. Only
    one can be configured, based on the version of the ``MUSCLE`` program
    provided. The generic-named function :func:`!muscle` is an alias for
    the available version.
