.. _pycoalesce:

--------------------
Coalescent simulator
--------------------

EggLib includes in this module a simulator based on the standard
coalescent for diploid individuals with partial, and optional,
self-fertilization. More details are given in a :ref:`section <manual-coal>`
of the manual.

The class :class:`.coalesce.Simulator` manages all parameters and lets
the user run coalescence simulations. The other classes defined in this
module help managing parameters.

.. autosummary::
    egglib.coalesce.Simulator
    egglib.coalesce.ParamDict
    egglib.coalesce.ParamList
    egglib.coalesce.ParamMatrix
    egglib.coalesce.EventList


.. autoclass:: egglib.coalesce.Simulator
    :members:

.. autoclass:: egglib.coalesce.ParamDict
    :members:

.. autoclass:: egglib.coalesce.ParamList
    :members:

.. autoclass:: egglib.coalesce.ParamMatrix
    :members:

.. autoclass:: egglib.coalesce.EventList
    :members:

