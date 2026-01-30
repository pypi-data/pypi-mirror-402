.. _io:

-----------------------
Import/export utilities
-----------------------

.. autosummary::
    egglib.io.to_ms
    egglib.io.from_fasta
    egglib.io.from_fasta_string
    egglib.io.fasta_iter
    egglib.io.from_genepop
    egglib.io.GFF3
    egglib.io.VCF
    egglib.io.index_vcf
    egglib.io.hts_set_log_level
    egglib.io.VcfSlider
    egglib.io.CodonVCF
    egglib.io.BED
    egglib.io.from_clustal
    egglib.io.from_staden
    egglib.io.from_genalys
    egglib.io.get_fgenesh
    egglib.io.GenBank

In case the :class:`!VCF` class is not available, the following
alternative tools are maintained:

.. autosummary::
    egglib.io.VcfParser
    egglib.io.VcfStringParser

Below are components that do not need to be manipulated directly but are
referred to by the documentation of the above items.

.. autosummary::
    egglib.io.Gff3Feature
    egglib.io.GenBankFeature
    egglib.io.GenBankFeatureLocation

.. _fasta-format:

Here is the description of the fasta format used in EggLib:

* Each sequence is preceded by a header limited to a single line and
  starting by a ``>`` character.
    
* The header length is not limited and all characters are allowed, but
  white spaces and special characters are discouraged. The header is
  terminated by a newline character.

* Group labels are specified a special markup system placed at the end
  of the header line. The labels are specified by an at sign (``@``)
  followed by any string (``@pop1``, ``@pop2``, ``@pop3`` and so on). It
  is allowed to define several group labels for any sequence. In that
  case, integer values must be enter consecutively after the at sign,
  separated by commas, as in ``@cluster1,pop3,indiv2`` for a sequence belonging to
  a given group in three different grouping levels. Multiple
  grouping levels can be used to specify hierarchical structure, but
  not only (several independent grouping structures can be specified). The
  markup ``@#`` (at sign and hash sign) specifies an outgroup sequence.
  The hash sign may be followed by an additional label as in ``@#``,
  Multiple grouping levels are not allowed for the
  outgroup.

* The sequence itself continues on following lines until the next ``>``
  character or the end of the file. Each allele is represented by a
  single character.

* White spaces, tab and carriage returns are allowed at any position.
  They are ignored unless for terminating the header line. There is no
  limitation in length and different sequences can have different
  lengths.

* Allowed characters and significance of character case is determined
  but the alphabet specified at time of parsing. For example, the
  :py:obj:`.alphabets.DNA` supports the characters listed below, and
  case is ignored (all characters are turned into upper-case).

.. _iupac-nomenclature:

Ambiguity characters in DNA sequences are processed by several functions.
The IUPAC nomenclature is followed, as described below:

+-------+------------------+------------+
| Code  | Meaning          | Complement |
+=======+==================+============+
| ``A`` | ``A``            | ``T``      |
+-------+------------------+------------+
| ``C`` | ``C``            | ``G``      |
+-------+------------------+------------+
| ``G`` | ``G``            | ``C``      |
+-------+------------------+------------+
| ``T`` | ``T``            | ``A``      |
+-------+------------------+------------+
| ``M`` | ``A`` or ``C``   | ``K``      |
+-------+------------------+------------+
| ``R`` | ``A`` or ``G``   | ``Y``      |
+-------+------------------+------------+
| ``W`` | ``A`` or ``T``   | ``W``      |
+-------+------------------+------------+
| ``S`` | ``C`` or ``G``   | ``S``      |
+-------+------------------+------------+
| ``Y`` | ``C`` or ``T``   | ``R``      |
+-------+------------------+------------+
| ``K`` | ``G`` or ``T``   | ``M``      |
+-------+------------------+------------+
| ``V`` | ``A``, ``C``,    | ``B``      |
|       | or ``G``         |            |
+-------+------------------+------------+
| ``H`` | ``A``, ``C``,    |            |
|       | or ``T``         | ``D``      |
+-------+------------------+------------+
| ``D`` | ``A``, ``G``,    |            |
|       | or ``T``         | ``H``      |
+-------+------------------+------------+
| ``B`` | ``C``, ``G``,    | ``V``      |
|       | or ``T``         |            |
+-------+------------------+------------+
| ``N`` | ``G``, ``A``,    | ``N``      |
|       | ``T``, or ``C``  |            |
+-------+------------------+------------+
| ``-`` | alignment gap    | ``-``      |
+-------+------------------+------------+
| ``?`` | ``G``, ``A``,    | ``?``      |
|       | ``T``, ``C``, or |            |
|       | alignment gap    |            |
+-------+------------------+------------+

Positions with ``?`` are supposed to be non-characterized, so it
is unknown whether they have a valid base or an alignment gap.

.. autofunction:: egglib.io.to_ms

.. autofunction:: egglib.io.from_fasta
.. autofunction:: egglib.io.from_fasta_string
.. autoclass:: egglib.io.fasta_iter
    :members:
    :exclude-members: next

.. autofunction:: egglib.io.from_genepop

.. autoclass:: egglib.io.GFF3
    :members:

.. autoclass:: egglib.io.Gff3Feature
    :members:

.. autoclass:: egglib.io.VCF
    :members:
    :inherited-members:

.. autofunction:: egglib.io.index_vcf
.. autofunction:: egglib.io.hts_set_log_level

.. autoclass:: egglib.io.VcfSlider
    :members:

.. autoclass:: egglib.io.CodonVCF
    :members:

.. autoclass:: egglib.io._vcfcodon.CodingSite
    :members:

.. autofunction:: egglib.io.from_clustal
.. autofunction:: egglib.io.from_staden
.. autofunction:: egglib.io.from_genalys
.. autofunction:: egglib.io.get_fgenesh

.. autoclass:: egglib.io.GenBank
    :members:

.. autoclass:: egglib.io.GenBankFeature
    :members:

.. autoclass:: egglib.io.GenBankFeatureLocation
    :members:

Alternative VCF parser
----------------------

.. autoclass:: egglib.io.VcfParser
    :members:
    :inherited-members:
    :exclude-members: next

.. autofunction:: egglib.io.make_vcf_index

.. autoclass:: egglib.io.VcfStringParser
    :members:
    :inherited-members:

.. autoclass:: egglib.io.VcfVariant
    :members:
    :exclude-members: alt_type_default, alt_type_referred, alt_type_breakend

    .. autoattribute:: alt_type_default
        :annotation:

    .. autoattribute:: alt_type_referred
        :annotation:

    .. autoattribute:: alt_type_breakend
        :annotation:

.. autoclass:: egglib.io.VcfSlidingWindow
    :members:
    :exclude-members: next

.. autoclass:: egglib.io.VcfWindow
    :members:

.. autodata:: egglib.io.FIRST
    :annotation:

.. autodata:: egglib.io.LAST
    :annotation:

.. autoclass:: egglib.io.BED
    :members:
