.. _alphabets:

---------------------
Pre-defined alphabets
---------------------

Alphabets are used to map any kind of genetic data to values stored inside
EggLib objects (:class:`.Align`, :class:`.Container`, and :class:`.Site`
instances). The type of data can be single characters (e.g. DNA or proteins),
or strings with free length (e.g. insertion/deletion polymorphisms), or
symbolic strings (alleles note represented by their sequences), or
integers (e.g microsatellites, or polymorphisms that have been encoded
beforehand). The character case can be considered or not.

The alphabet determines which values are valid and can be considered as
alleles in polymorphisms and which values should be treated as missing data,
while any other values will be rejected and cause an error.

The class :class:`.Alphabet` (available in the global namespace), allows to
define custom alphabets, while this module contains pre-defined alphabets.
For many functions accepting a particular type of data, the use of the
correct alphabet among this list is mandatory. Furthermore, data processing
will be faster, especially with DNA sequences.

.. autodata:: egglib.alphabets.DNA
    :annotation:

.. autodata:: egglib.alphabets.protein
    :annotation:

.. autodata:: egglib.alphabets.codons
    :annotation:

.. autodata:: egglib.alphabets.positive_infinite
    :annotation:

.. autodata:: egglib.alphabets.binary
    :annotation:

.. autodata:: egglib.alphabets.genepop
    :annotation:
