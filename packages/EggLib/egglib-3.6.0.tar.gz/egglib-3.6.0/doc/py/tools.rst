.. _tools:

---------------------------
Sequence manipulation tools
---------------------------

This module provides a number of standalone tools for manipulating sequences.

.. autosummary::
    egglib.tools.ReadingFrame
    egglib.tools.to_codons
    egglib.tools.to_bases
    egglib.tools.concat
    egglib.tools.ungap
    egglib.tools.ungap_all
    egglib.tools.rc
    egglib.tools.compare
    egglib.tools.regex
    egglib.tools.motif_iter
    egglib.tools.translate
    egglib.tools.Translator
    egglib.tools.orf_iter
    egglib.tools.longest_orf
    egglib.tools.backalign
    egglib.tools.trailing_stops
    egglib.tools.iter_stops
    egglib.tools.has_stop

.. autoclass:: egglib.tools.ReadingFrame
    :members:

.. autofunction:: egglib.tools.to_codons
.. autofunction:: egglib.tools.to_bases
.. autofunction:: egglib.tools.concat
.. autofunction:: egglib.tools.ungap
.. autofunction:: egglib.tools.ungap_all
.. autofunction:: egglib.tools.rc
.. autofunction:: egglib.tools.compare
.. autofunction:: egglib.tools.regex
.. autofunction:: egglib.tools.motif_iter
.. autofunction:: egglib.tools.translate
.. autoclass:: egglib.tools.Translator
    :members:

.. autofunction:: egglib.tools.orf_iter
.. autofunction:: egglib.tools.longest_orf

.. autofunction:: egglib.tools.backalign

.. autoclass:: egglib.tools.BackalignError
    :members:
    :show-inheritance:
    :exclude-members: args, with_traceback
    

.. autofunction:: egglib.tools.trailing_stops
.. autofunction:: egglib.tools.iter_stops
.. autofunction:: egglib.tools.has_stop

