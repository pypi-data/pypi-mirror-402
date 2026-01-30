.. _generic:

-------------------------
Top level components
-------------------------

The top-level ``EggLib`` namespace contains the most useful classes and
functions, as well as items that are not specialised to a particular
task. They can be grouped in several categories according to the task
they are aimed to fulfill:

    * :ref:`egglib_datasets`
    * :ref:`egglib_site`
    * :ref:`egglib_alphabet`
    * :ref:`egglib_structure`
    * :ref:`egglib_tree`

.. _egglib_datasets:

Holding multi-site data
-----------------------

The two classes :class:`!Align` and :class:`!Container` (and their helpers)
allow to store data sequence data for multiple samples
as well as any form of genetic data as long as there can be several data
items for multiple samples.

.. autosummary::
    egglib.Align
    egglib.Container
    egglib.SampleView
    egglib.SequenceView
    egglib.LabelView
    egglib.encode

.. _egglib_site:

Holding single-site data
------------------------

The class :class:`!Site` allows to store any kind of data at a single site. There
are three independent functions to create instances of this class.
:class:`!Freq` only holds frequencies.

.. autosummary::
    egglib.Site
    egglib.site_from_align
    egglib.site_from_list
    egglib.site_from_vcf
    egglib.Freq
    egglib.freq_from_site
    egglib.freq_from_list
    egglib.freq_from_vcf

.. _egglib_alphabet:

Representing data with alphabets
--------------------------------

Alphabets are described in their specific :ref:`module <alphabets>`. The class
for creating custom alphabets is available in the top EggLib namespace.

.. autosummary::
    egglib.Alphabet

.. _egglib_structure:

Describing sample structure
---------------------------

Sample structure is described by a specific class. There are four methods
allowing to generate instances.

.. autosummary::

    egglib.Structure
    egglib.struct_from_labels
    egglib.struct_from_samplesizes
    egglib.struct_from_iterable
    egglib.struct_from_dict
    egglib.struct_from_mapping

.. _egglib_tree:

Trees
---------------------------

Trees are described by a specific class, with a companion class
representing a particular node of a tree.

.. autosummary::

    egglib.Tree
    egglib.Node

Module content documentation
----------------------------

.. autoclass:: egglib.Align
    :members:
    :inherited-members:

.. autoclass:: egglib.Container
    :members:
    :inherited-members:
    
.. autoclass:: egglib.SampleView
    :members:

.. autoclass:: egglib.SequenceView
    :members:

.. autoclass:: egglib.LabelView
    :members:

.. autoclass:: egglib.encode
    :members:

.. autoclass:: egglib.Site
    :members:

.. autofunction:: egglib.site_from_align
.. autofunction:: egglib.site_from_list
.. autofunction:: egglib.site_from_vcf

.. autoclass:: egglib.Freq
    :members:

.. autofunction:: egglib.freq_from_site
.. autofunction:: egglib.freq_from_list
.. autofunction:: egglib.freq_from_vcf

.. autoclass:: egglib.Alphabet
    :members:

.. autoclass:: egglib.Structure
    :members:

.. autofunction:: egglib.struct_from_labels
.. autofunction:: egglib.struct_from_samplesizes
.. autofunction:: egglib.struct_from_iterable
.. autofunction:: egglib.struct_from_dict
.. autofunction:: egglib.struct_from_mapping

.. autoclass:: egglib.Tree
    :members:

.. autoclass:: egglib.Node
    :members:
