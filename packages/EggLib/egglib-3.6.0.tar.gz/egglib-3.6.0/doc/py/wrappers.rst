.. _wrappers:

--------------------------
External application tools
--------------------------

This module contains functions that can run external programs within the
EggLib framework (taking as arguments and/or returning EggLib objects).
To use these functions, the underlying programs must be available in the
system. This is controlled by the application paths object as explained
in :ref:`paths`.

.. autosummary::
    egglib.wrappers.phyml
    egglib.wrappers.codeml
    egglib.wrappers.nj
    egglib.wrappers.clustal
    egglib.wrappers.muscle
    egglib.wrappers.makeblastdb
    egglib.wrappers.megablast
    egglib.wrappers.dc_megablast
    egglib.wrappers.blastn
    egglib.wrappers.blastn_short
    egglib.wrappers.blastp
    egglib.wrappers.blastp_short
    egglib.wrappers.blastp_fast
    egglib.wrappers.blastx
    egglib.wrappers.blastx_fast
    egglib.wrappers.tblastn
    egglib.wrappers.tblastn_fast
    egglib.wrappers.tblastx
    egglib.wrappers.BlastHit
    egglib.wrappers.BlastHsp
    egglib.wrappers.BlastOutput
    egglib.wrappers.BlastQueryHits

.. autofunction:: egglib.wrappers.phyml
.. autofunction:: egglib.wrappers.codeml
.. autofunction:: egglib.wrappers.nj
.. autofunction:: egglib.wrappers.clustal
.. autofunction:: egglib.wrappers.muscle
.. autofunction:: egglib.wrappers.muscle5
.. autofunction:: egglib.wrappers.muscle3
.. autofunction:: egglib.wrappers.makeblastdb
.. autofunction:: egglib.wrappers.megablast
.. autofunction:: egglib.wrappers.dc_megablast
.. autofunction:: egglib.wrappers.blastn
.. autofunction:: egglib.wrappers.blastn_short
.. autofunction:: egglib.wrappers.blastp
.. autofunction:: egglib.wrappers.blastp_short
.. autofunction:: egglib.wrappers.blastp_fast
.. autofunction:: egglib.wrappers.blastx
.. autofunction:: egglib.wrappers.blastx_fast
.. autofunction:: egglib.wrappers.tblastn
.. autofunction:: egglib.wrappers.tblastn_fast
.. autofunction:: egglib.wrappers.tblastx
.. autoclass:: egglib.wrappers.BlastOutput
    :members:
.. autoclass:: egglib.wrappers.BlastQueryHits
    :members:
.. autoclass:: egglib.wrappers.BlastHit
    :members:
.. autoclass:: egglib.wrappers.BlastHsp
    :members:

.. _paths:

Configuring paths
-----------------

Application paths can be set using the following syntax. A
:exc:`ValueError` is raised if the automatic test fails.
The change is valid for the current session only unless :meth:`.save` is
used::

    egglib.wrappers.paths[app] = path

And application paths are accessed as followed::

    egglib.wrappers.paths[app]

.. method:: egglib.wrappers.paths.autodetect(verbose=False)

    Auto-configure application paths based on default command names.

    :param verbose: if ``True``, print progress information.

    The function returns a ``(npassed, nfailed, failed_info)`` with:

    * ``npassed`` the number of applications which passed.
    * ``nfailed`` the number of applications which failed.
    * ``failed_info`` a :class:`dict` containing, for each failing
      application, the command which was used and the error message.

.. method:: egglib.wrappers.path.load

    Load values of application paths from the configuration file
    located within the package. All values currently set are discarded.

.. method:: egglib.wrappers.path.save

    Save current values of application paths in the configuration file
    located within the package. This action may require administrator
    rights. All values currently set will be reloaded at next import of
    the package.

.. _blastn-options:
