.. _manual-vcf:

---------------
Using VCF files
---------------

Short description of the format
===============================

The Variant Call Format is designed to store information relative to genome-wide
diversity data. The format consists in a header containing meta-information
(in lines prefixed by ``##``) followed by a single header providing the list of
samples included in the file, and by the body of the file which consists in,
typically, a very large number of lines each describing variation for a given
*variant* (a variant can be a single nucleotide polymorphism, an insertion/deletion,
a microsatellite, or any form of genomic variation, including large rearrangements.

An example appears below:

.. code-block:: none

    ##fileformat=VCFv4.4
    ##fileDate=20090805
    ##source=myImputationProgramV3.1
    ##reference=file:///seq/references/1000GenomesPilot-NCBI36.fasta
    ##contig=<ID=20,length=62435964,assembly=B36,md5=f126cdf8a6e0c7f379d618ff66beb2da,species="Homo sapiens",taxonomy=x>
    ##phasing=partial
    ##INFO=<ID=NS,Number=1,Type=Integer,Description="Number of Samples With Data">
    ##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">
    ##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">
    ##INFO=<ID=AA,Number=1,Type=String,Description="Ancestral Allele">
    ##INFO=<ID=DB,Number=0,Type=Flag,Description="dbSNP membership, build 129">
    ##INFO=<ID=H2,Number=0,Type=Flag,Description="HapMap2 membership">
    ##FILTER=<ID=q10,Description="Quality below 10">
    ##FILTER=<ID=s50,Description="Less than 50% of samples have data">
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##FORMAT=<ID=GQ,Number=1,Type=Integer,Description="Genotype Quality">
    ##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read Depth">
    ##FORMAT=<ID=HQ,Number=2,Type=Integer,Description="Haplotype Quality">
    #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT NA00001 NA00002 NA00003
    20 14370 rs6054257 G A 29 PASS NS=3;DP=14;AF=0.5;DB;H2 GT:GQ:DP:HQ 0|0:48:1:51,51 1|0:48:8:51,51 1/1:43:5:.,.
    20 17330 . T A 3 q10 NS=3;DP=11;AF=0.017 GT:GQ:DP:HQ 0|0:49:3:58,50 0|1:3:5:65,3 0/0:41:3
    20 1110696 rs6040355 A G,T 67 PASS NS=2;DP=10;AF=0.333,0.667;AA=T;DB GT:GQ:DP:HQ 1|2:21:6:23,27 2|1:2:0:18,2 2/2:35:4
    20 1230237 . T . 47 PASS NS=3;DP=13;AA=T GT:GQ:DP:HQ 0|0:54:7:56,60 0|0:48:4:51,51 0/0:61:2
    20 1234567 microsat1 GTC G,GTCT 50 PASS NS=3;DP=9;AA=G GT:GQ:DP 0/1:35:4 0/2:17:2 1/1:40:3

Pieces of information are attached to each variant (site) and, within a variant,
to each sample. The former are denoted ``INFO`` and the latter ``FORMAT``. In the
example above, an example of ``INFO`` field is ``NS`` (whose value is 3 for the first
site), and an exemple of ``FORMAT`` field is ``GT`` (whose value for the samples of
the first sites are: ``0|0``, ``1|0``, and ``1|1``).

The description of the VCF format is available `here <https://samtools.github.io/hts-specs/>`_.

Reading VCF files
=================

EggLib provides two alternative parsers in the :ref:`io <io>` module: 
:class:`~.io.VcfParser` and :class:`~.io.VCF`. 

The former is essentially there as a fallback solution in case the,
latter, which depends on the C library ``htslib``, is not available. Refer
to the installation :ref:`install` for installation. If the dependency
is fulfilled at installation, the :class:`!VCF` class will be available.
If not, attempting to use it will cause an exception.

It can be tested using a variable exposed in EggLib::

    >>> print(egglib.config.htslib)
    1

(This will return 0 or 1.). It can be also tested from the command line:

.. code-block:: none
    :emphasize-lines: 5

    $ EggLib version 3.2.0
    Installation path: /home/stephane/.local/lib/python3.9/site-packages/egglib/wrappers
    External application configuration file: /home/stephane/.config/EggLib/apps.conf
    debug flag: 0
    htslib flag: 1
    version of muscle: 5

The :class:`!VCF` class offers a number of advantages:

* It is based on htslib, the underlying library of the ``samtools`` and
  ``bcftools`` programs, making it the *de facto* standard for parsing
  VCF/BCF files. :class:`!VcfParser` is based on a native implementation
  which can differ occasionally (often by being more restrictive and
  complaining about the format).

* It can import both compressed and uncompressed VCF and BCF files. With
  :class:`!VcfParser`, the user is required to provide uncompressed VCF
  file, which can be a huge bottleneck.

* It is expected to be significantly more efficient, especially for
  direct reading of BCF data.


Using default parser :class:`!VCF`
==================================

Opening a file
--------------

To open a file with the :class:`~.io.VCF` class, pass the name of a
compressed or uncompressed VCF or BCF file as in::

    >>> vcf = egglib.io.VCF('example.vcf')
    >>> print(vcf.get_samples())
    ['NA00001', 'NA00002', 'NA00003']

Immediately after opening the file, no data has been accessed; all
accessors will return ``None`` (except header data)::

    >>> print(vcf.get_pos())
    None

Iterating on positions
----------------------

The next position (or variant) is read using the :meth:`~.io.VCF.read`
method, which returns a boolean. If the boolean if ``True``, data has
been read and can be accessed. If (and only if) the end of file is
reached, :meth:`!read` returns ``False``. To loop over the whole content
of the file, just write::

    >>> while vcf.read():
    ...     print(vcf.get_chrom(), vcf.get_pos())
    ...
    20 14369
    20 17329
    20 1110695
    20 1230236
    20 1234566

Iterating on sites
------------------

It is possible to iterate over all sites of a VCF using the iterator
returned by the method :meth:`.VCF.iter_sites`. This iterator returns
:class:`.Site` instances which can be used directly for diversity
analyses. This allows, for example, to iteratively compute statistics
over the whole genome. A desirable property of this approach is to allow
computing site-level and unphased sites statistics at the genomic scale
without loading all sites in memory. The option *multi=True* allows
processing all sites iteratively while the final computation of
statistics is performed by :meth:`.ComputeStats.results`::

    >>> cs = egglib.stats.ComputeStats(multi=True)
    >>> cs.add_stats('S', 'lseff', 'D')
    >>> vcf = egglib.io.VCF('LG15.bcf')
    >>> for site in vcf.iter_sites():
    ...     cs.process_site(site)
    ...
    >>> print(cs.results())
    {'S': 2784, 'D': 0.6822884476500767, 'lseff': 2784}

The returned sites have two properties allowing to trace back their
coordinates, :attr:`.Site.chrom` and :attr:`.Site.position`.

By default, only SNPs are considered, excluding variants with indels or
structural variants, but also positions without polymorphism. This
explains why ``lseff`` and ``S`` are equal. This can be a problem
because, for normalization purpose, one may want to have an idea of the
number of sites that were included in the analysis (which might be
significantly smaller than the reference genome length). In case
invariant positions (that is, genomic position where no differences with
the reference were found) are included in the VCF, one can force
:meth:`.VCF.iter_sites` to consider these sites along with genuine SNP
sites using the option ``mode=1``. Note that the analysis is then
significant longer::

    >>> vcf = egglib.io.VCF('../poster/boxes/LG15.bcf')
    >>> for site in vcf.iter_sites(mode=1):
    ...     cs.process_site(site)
    ...
    >>> print(cs.results())
    {'D': 0.6822884476500767, 'S': 2784, 'lseff': 159237}

So we know that 159,237 sites passed the threshold along the included
region. Note also that the VCF file has be reopened because, by default,
:meth:`.VCF.iter_sites` starts from the current file position. There is
also a mode allowing to include all sites (including indels, structural
variants and MNPs). This mode can be activated with the option
``mode=2``.

By default, :meth:`.VCF.iter_sites` excludes sites with any missing
data. Sometimes this is way too stringent and many polymorphisms might
be missed. This behaviour can be controlled by the *max_missing*
argument::

    >>> vcf = egglib.io.VCF('../poster/boxes/LG15.bcf')
    >>> for site in vcf.iter_sites(max_missing=10):
    ...     cs.process_site(site)
    ...
    >>> print(cs.results())
    {'S': 3670, 'D': 0.5097537454504543, 'lseff': 3670}

It is also possible to analyse a specific chromosome, either in full or
partially::

    >>> for site in vcf.iter_sites(chrom='LG15', start=2100000, stop=2200000, max_missing=10):
    ...     cs.process_site(site)
    ...
    >>> print(cs.results())
    {'lseff': 1913, 'D': 1.1986717246694527, 'S': 1913}

There is no need to reopen the file because as soon as the ``chrom``
option is used the position is shift to the appropriate location.

Extracting a single site
------------------------

It is possible to extract the current variant as a :class:`.Site`
instance using the method :meth:`.VCF.as_site`. The alphabet is
automatically set based on the alleles present in the current variant
(the DNA alphabet for SNPs or invariant positions, an ad hoc string
alphabet for indels and an ad hoc custom alphabet for other type of
alleles such as structural variants which are encoded following a
special syntax). In the below example, we screen the VCF using the first
SNP found (which of course is a singleton)::

    >>> vcf = egglib.io.VCF('../poster/boxes/LG15.bcf')
    >>> while vcf.read():
    ...     if vcf.is_snp():
    ...         break
    ... 
    >>> site = vcf.as_site()
    >>> print(site.chrom, site.position)
    LG15 2100177.0
    >>> print(site.alphabet.name)
    DNA
    >>> print(site.as_list())
    ['A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
     'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
     'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
     'G', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
     'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
     'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
     'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
     'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
     'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
     'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
     'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
     'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A', 'A',
     'A', 'A']

We know screen for the first indel and see how the result looks like::

    >>> while vcf.read():
    ...     if 'INDEL' in vcf.get_types():
    ...         break
    ...
    >>> site = vcf.as_site()
    >>> print(site.chrom, site.position)
    LG15 2100489.0
    >>> print(site.alphabet.name)
    StringAlphabet
    >>> print(site.alphabet.get_alleles())
    (['TTA', 'TTATGTA'], ['?'])
    >>> print(site.as_list())
    ['TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTATGTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTATGTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA', 'TTA',
     'TTA', 'TTA', 'TTA', 'TTA', 'TTA']

Sliding window
--------------

Sliding windows can be performed using the class :class:`.io.VcfSlider`.
The class is flexible and allows both overlapping and non-overlapping
windows and even discontinuous windows (when *step* is larger than
*size*). It is possible to express the window parameters in either
genomic coordinates or as counts of variants. The first example shows a
sliding window with windows of 20 Kbp with a step of 10 Kbp. The option
*mode=1* specifies that only SNPs and invariant positions are
considered. We can see that the number of considered sites (``lseff``)
varies significant between windows due to the amount of missing data::

    >>> cs.configure(multi=False)
    >>> sld = egglib.io.VcfSlider(vcf, size=20000, step=10000, chrom='LG15', start=2100000, mode=1)
    >>> while sld.move():
    ...     print(sld.chromosome, sld.bounds, cs.process_sites(sld))
    ...
    LG15 (2100000, 2120000) {'S': 285, 'lseff': 19673, 'D': -1.0208469703204108}
    LG15 (2110000, 2130000) {'S': 257, 'lseff': 19655, 'D': -0.7551741358079189}
    LG15 (2120000, 2140000) {'S': 246, 'lseff': 18149, 'D': -0.4450237844997452}
    LG15 (2130000, 2150000) {'S': 200, 'lseff': 18408, 'D': -0.5661162829943361}
    LG15 (2140000, 2160000) {'S': 221, 'lseff': 18238, 'D': 0.147134234059163}
    LG15 (2150000, 2170000) {'S': 254, 'lseff': 17798, 'D': 2.0379904662805406}
    LG15 (2160000, 2180000) {'S': 359, 'lseff': 19145, 'D': 3.715536736918846}
    LG15 (2170000, 2190000) {'S': 436, 'lseff': 17702, 'D': 3.37076934332993}
    LG15 (2180000, 2200000) {'S': 620, 'lseff': 17235, 'D': 1.1254052272878594}
    LG15 (2190000, 2210000) {'S': 586, 'lseff': 16967, 'D': 0.6470978965482322}
    LG15 (2200000, 2220000) {'S': 422, 'lseff': 15437, 'D': 0.7504282417996326}
    LG15 (2210000, 2230000) {'S': 505, 'lseff': 16313, 'D': 0.7930504761137561}
    LG15 (2220000, 2240000) {'S': 255, 'lseff': 9104, 'D': 1.1704366928271137}
    LG15 (2230000, 2250000) {'S': 65, 'lseff': 4175, 'D': -0.5158671365838988}
    LG15 (2240000, 2260000) {'S': 54, 'lseff': 4181, 'D': -1.0894125044884786}
    LG15 (2250000, 2270000) {'S': 109, 'lseff': 8780, 'D': -1.0577477958801875}
    LG15 (2260000, 2280000) {'S': 163, 'lseff': 18271, 'D': -0.8043678712771385}
    LG15 (2270000, 2290000) {'S': 143, 'lseff': 19762, 'D': -0.6812477489850655}
    LG15 (2280000, 2300000) {'S': 159, 'lseff': 19803, 'D': -1.2375421915306923}

The second example uses the option *as_variants=True* to perform a
non-overlapping sliding window analysis of 100 SNPs each. The option
*multi_hits=True* is added because sites with more that 2 alleles are
skipped by default by :class:`.ComputeStats`::

    >>> cs.configure(multi=False, multi_hits=True)
    >>> sld = egglib.io.VcfSlider(vcf, size=100, step=100, as_variants=True, chrom='LG15', start=2100000, mode=0)
    >>> while sld.move():
    ...     print(sld.chromosome, sld.bounds, cs.process_sites(sld))
    ...
    LG15 (2100177, 2108246) {'S': 100, 'lseff': 100, 'D': -0.6497976147696085}
    LG15 (2108289, 2112536) {'S': 100, 'lseff': 100, 'D': -1.455995331069099}
    LG15 (2112618, 2121223) {'S': 100, 'lseff': 100, 'D': -0.716451135366233}
    LG15 (2121330, 2129731) {'S': 100, 'lseff': 100, 'D': -0.8467454259513761}
    LG15 (2129780, 2136627) {'S': 100, 'lseff': 100, 'D': -0.476134061859107}
    LG15 (2136642, 2148637) {'S': 100, 'lseff': 100, 'D': -0.522272185457637}
    LG15 (2148700, 2156899) {'S': 100, 'lseff': 100, 'D': -0.4731643505453989}
    LG15 (2156919, 2164718) {'S': 100, 'lseff': 100, 'D': 2.9531508374723763}
    LG15 (2164806, 2171594) {'S': 100, 'lseff': 100, 'D': 3.455978913966385}
    LG15 (2171609, 2174831) {'S': 100, 'lseff': 100, 'D': 4.735307593622778}
    LG15 (2174915, 2179458) {'S': 100, 'lseff': 100, 'D': 3.068180524976409}
    LG15 (2179473, 2183555) {'S': 100, 'lseff': 100, 'D': 4.314139405040087}
    LG15 (2183565, 2189753) {'S': 100, 'lseff': 100, 'D': 1.1635339369590245}
    LG15 (2189875, 2192316) {'S': 100, 'lseff': 100, 'D': -0.9278171101725392}
    LG15 (2192367, 2194541) {'S': 100, 'lseff': 100, 'D': -0.20784144699093848}
    LG15 (2194544, 2196869) {'S': 100, 'lseff': 100, 'D': 0.4650635745467691}
    LG15 (2196880, 2199315) {'S': 100, 'lseff': 100, 'D': 2.063915975840712}
    LG15 (2199319, 2203950) {'S': 100, 'lseff': 100, 'D': 1.4714227026766764}
    LG15 (2203961, 2210188) {'S': 100, 'lseff': 100, 'D': 0.696485860544226}
    LG15 (2210189, 2213581) {'S': 100, 'lseff': 100, 'D': 0.6996994611928781}
    LG15 (2213589, 2217464) {'S': 100, 'lseff': 100, 'D': -0.17432818308355094}
    LG15 (2217651, 2221038) {'S': 100, 'lseff': 100, 'D': 1.1060764789328794}
    LG15 (2221053, 2225235) {'S': 100, 'lseff': 100, 'D': 1.5098567925773168}
    LG15 (2225251, 2230038) {'S': 100, 'lseff': 100, 'D': 0.8932328216854516}
    LG15 (2230041, 2262595) {'S': 100, 'lseff': 100, 'D': -0.934861208022937}
    LG15 (2262706, 2272995) {'S': 100, 'lseff': 100, 'D': -0.6168151688265049}
    LG15 (2272996, 2284788) {'S': 100, 'lseff': 100, 'D': -0.8841896120807741}
    LG15 (2284811, 2299991) {'S': 91, 'lseff': 91, 'D': -1.4494467086616505}

Indexing
--------

Indexing allows arbitrary and linear-time navigation within BCF files.
(not available for VCF files). Index files generated by ``bcftools`` are
supported, while the function :func:`.io.index_vcf` can be used to
generate a BCF index.

To demonstrate the use of indexes, we will use a BCF file which we will
index before importing it::

    >>> egglib.io.index_vcf('data.bcf')
    >>> vcf = egglib.io.VCF('data.bcf')
    >>> print(vcf.has_index)
    True

The index file is named after the BCF file (with a ".csi" suffix). By
default, :func:`!index_vcf` and :class:`!VCF` use the same format. If
the index is named differently (e.g. located in a different directory),
its name can be specified as the *index* option of the :class:`!VCF`
constructor::

    >>> egglib.io.index_vcf('data.bcf', outname='another_name.csi')
    >>> vcf = egglib.io.VCF('data.bcf', index='another_name.csi')
    >>> print(vcf.has_index)
    True

Navigation with :meth:`!goto`
-----------------------------

Provided that an index is loaded, the :meth:`~.io.VCF.goto` method
allows to move anywhere in the file. To demonstrate the use of
:meth:`!goto`, consider the table of positions actually available in
``data.bcf``:

+------+------+
| ctg1 | 1000 |
+------+------+
| ctg1 | 1001 |
+------+------+
| ctg1 | 1010 |
+------+------+
| ctg1 | 1011 |
+------+------+
| ctg2 | 1015 |
+------+------+
| ctg2 | 1016 |
+------+------+
| ctg2 | 1020 |
+------+------+
| ctg2 | 1030 |
+------+------+
| ctg2 | 1050 |
+------+------+
| ctg3 | 1060 |
+------+------+
| ctg3 | 1100 |
+------+------+

When we open the file, reading it will extract the first line::

    >>> egglib.io.index_vcf('data.bcf')
    >>> vcf.read()
    >>> print(vcf.get_chrom(), vcf.get_pos())
    ctg1 999

Remember about the 1-position offset caused by the conversion of
genomic positions to pythonic indexes applied by EggLib.

:meth:`!goto` can be used to navigate, either back or forth, within the
same contig::

    >>> vcf.goto('ctg2', 1019)
    >>> print(vcf.get_chrom(), vcf.get_pos())
    ctg2 1019
    >>> vcf.goto('ctg1', 1009)
    >>> print(vcf.get_chrom(), vcf.get_pos())
    ctg1 1009

If the position is omitted, the first available position of the contig
is picked:

    >>> vcf.goto('ctg2')
    >>> print(vcf.get_chrom(), vcf.get_pos())
    ctg2 1014

If the contig does not exist, the move fails and an :class:`ValueError`
is raised::

    >>> vcf.goto('ctg4')
    Traceback (most recent call last):
      File "/home/stephane/data/devel/egglib/project/doc/manual/test/stats-4.py", line 78, in <module>
        vcf.goto('ctg4', 1000)
    ValueError: unknown target name: ctg4

And also if the position does not exist in the specified contig::

    >>> vcf.goto('ctg3', 1000)
    Traceback (most recent call last):
      File "/home/stephane/data/devel/egglib/project/doc/manual/test/stats-4.py", line 80, in <module>
        vcf.goto('ctg3', 1000)
    ValueError: position not found: 1000

However, it is possible to let :meth:`!goto` move to the first available
position within a specified range by using the option *limit*:

    >>> vcf.goto('ctg3', 1000, limit=1100)
    >>> print(vcf.get_chrom(), vcf.get_pos())
    ctg3 1059

Extracting data
---------------

There a number of accessors allowing to extract data from the current
position or variant. 

To get the dictionary of all ``INFO`` fields attached to the current
position, one can use :meth:`~.io.VCF.get_infos`, and
:meth:`~.io.VCF.get_info` to get a specific field::

    >>> print(vcf.get_infos())
    {'AA': 'A', 'TRI': [1.0, 2.0], 'ALT': 'C,G,T', 'GOOD': True}
    >>> print(vcf.get_info('AA'))
    A

To get the values of all ``FORMAT`` fields for all samples, the method
:meth:`~.io.VCF.get_formats` can be used. It returns a :class:`!list`
(one item per sample) of :class:`!dict` which all share the same set of
keys. The following gives an example which might betray the lack of
imagination of the author of the test file::

    >>> print(vcf.get_formats())
    [{'TEST5': '.', 'TEST1': 702}, {'TEST5': 'nothing', 'TEST1': 703}, {'TEST5': 'not more', 'TEST1': 704}, {'TEST5': 'something!', 'TEST1': 705}]

Another crucial accessor method is :meth:`~.io.VCF.get_genotypes`, which
returns a :class:`!list` of genotypes. In this :class:`!list`, each
sample is represented by a :class:`!list` of alleles, based on its
ploidy. To transfer this structure to an EggLib's :class:`.Site`, one
must flatten the list and subsequently generate a :class:`.Structure`
object to analyse the object with its ploidy with the :ref:`stats <stats>` module::

    >>> print(vcf.is_snp())
    True
    >>> genotypes = vcf.get_genotypes()
    [['A', 'A', 'A'], ['A', 'A', 'A'], ['A', 'A', 'C'], ['A', 'C', 'C']]
    >>> print(genotypes)
    >>> site = egglib.site_from_list([j for i in genotypes for j in i],
    ...     alphabet = egglib.alphabets.DNA)
    >>> struct = egglib.struct_from_samplesizes([4], ploidy=3)

The code uses the :meth:`~.io.VCF.is_snp` method to check if the current
site is a proper SNP, guaranteeing that the :obj:`~.alphabets.DNA` can
be used. Next the site is extracted and converted to a :class:`!Site`
object. The list comprehension with two ``for`` statements
(``[j for i in genotypes for j in i]``) is the way to flatten a sequence
is Python. The last line is a reminder how a :class:`!Structure` object
with known sample size and known (and constant) ploidy can be created.

Analysis of synonymous and non-synonymous variants
--------------------------------------------------

Assuming an indexed VCF file is available as ``data.bcf``, and the
corresponding annotation is available in the GFF3 format as
``annot.gff3``, it is possible to classify variants are synonymous or
non-synonymous using the class :class:`.io.CodonVCF`. However, this
analysis isn't as trivial as it sounds, and in most case it is simpler
to limit the analysis to codons which have only one mutation. The code
below will illustrate how this is done.

We start by creating an instance bound to the VCF file and which has the
annotation loaded::

    >>> cVCF = egglib.io.CodonVCF('data.bcf', 'annot.gff3')

There are two ways to use this class. The first method consists in
analysing a given position. One must first specify which CDS feature
should be considered. Note that a given gene might have several
different CDS features due to alternative splicing. Assume the ID of the
CDS feature is ``cds410``::

    >>> cVCF.set_cds('cds410')

Now, say we wish to extract the coding site corresponding to position
811943. It is possible to obtain an instance of a class named
:class:`~.CodingSite` using the method :meth:`~.io.CodonVCF.from_position`::

    >>> site = cVCF.from_position(811943)

:class:`!CodingSite` is a subclass of :class:`.Site` and thus can be
used with all functions that expect a :class:`!Site` (including
:meth:`.ComputeStats.process_site`. In addition, :class:`!CodingSite`
instances have a :attr:`~.CodingSite.flag` attribute that summarizes
their status. For example, if the position doesn't fall within any
segment of ``cds410`` (that is, belongs is out of bounds or falls within
an intron or in UTRs), the flag will be equal to the :attr:`~.CodingSite.NCOD` constant
(which is available as a class or instance attribute)::

    >>> if site.flag == site.NCOD:
    ...     skip_site()

The flag uses bitwise encoding to store several boolean indicators,
allowing testing for a combination of flags. The list is available in
the :class:`~.CodingSite` class description. For example, to select
sites that only have the non-synonymous flag on (i.e. that have only one
mutation which is non-synonymous and no stop codon), use::

    >>> if site.flag == site.NSYN:
    ...     process_nonsynonymous()

This test will be ``False`` if there are more than one mutation. To
include all sites that have at least one non-synonymous mutation
regardless of whether there more than one mutation and any stop codon
(stop codons are not counted as synonymous or non-synonymous variation)::

    >>> if (site.flag & site.NSYN) != 0:
    ...     process_nonsynonymous()

It is also possible to be interested in sites that have two different
codons encoding different amino acid, even if the two codons have more
than one differing positions (only two alleles at the codon level, but
more than one codon position changed)::

    >>> if (site.flag & (~site.MHIT)) == site.NSYN:
    ...     process_nonsynonymous()

The alternative of ``NSYN`` is ``SYN``. There can be both types of
variation at a single coding site if there are more than two alleles
(in such case, the ``MMUT``, for *multiple mutations*, will be set).

Alternatively, it is possible to process all possible codons of a given
CDS. This is done with a function which returns an iterator,
:meth:`.CodonVCF.iter_codons`. Let's start all over again and count the
number of coding sites with non-synonymous and synonymous variation,
skipping sites with a stop codon and more than two different codon
alleles::

    >>> cVCF = egglib.io.CodonVCF('data.bcf', 'annot.gff3')
    >>> cVCF.set_cds('cds410')
    >>> L = 0
    >>> V = 0
    >>> NS = 0
    >>> S = 0
    >>> for site in cVCF.iter_codons():
    ...     if (site.flag & (site.STOP | site.MMUT)) == 0:
    ...         L += 1
    ...         if (site.flag & site.VAR) != 0: V += 1
    ...         if (site.flag & site.NSYN) != 0: NS += 1
    ...         if (site.flag & site.SYN) != 0: S += 1
    >>> assert NS + S == V and V <= L
    >>> print(L, V, NS, S)

Using the fallback parser :class:`!VcfParser`
=============================================

Opening a file
--------------

Assuming the example VCF file above has been saved in an uncompressed 
file named ``example.vcf``, you need to provide the class's constructor 
with the name of the file. As a result, only the meta-information 
present in the header and the list of samples will be known to the 
instance at this point. The property 
:py:obj:`~.io.VcfParser.num_samples` and the method 
:meth:`~.io.VcfParser.get_sample` let you get the list of sample 
names::

    >>> vcf = egglib.io.VcfParser('example.vcf')
    >>> print([vcf.get_sample(i) for i in range(vcf.num_samples)])
    ['NA00001', 'NA00002', 'NA00003']

The meta-information properties attached to the file can be accessed using the
same model as the sample names (one property and one getter method taking
an index), as listed below for the different categories of meta-information:

+---------------+----------------------------+-------------------------------------+-----------------------------------+
| Code          | Type of meta-information   | Counter property                    | Accessor method                   |
+===============+============================+=====================================+===================================+
| ``ALT``       | Alternative allele code    | :py:obj:`~.io.VcfParser.num_alt`    | :meth:`~.io.VcfParser.get_alt`    |
+---------------+----------------------------+-------------------------------------+-----------------------------------+
| ``FILTER``    | Test used to filter files  | :py:obj:`~.io.VcfParser.num_filter` | :meth:`~.io.VcfParser.get_filter` |
+---------------+----------------------------+-------------------------------------+-----------------------------------+
| ``FORMAT``    | Descriptor of sample data  | :py:obj:`~.io.VcfParser.num_format` | :meth:`~.io.VcfParser.get_format` |
+---------------+----------------------------+-------------------------------------+-----------------------------------+
| ``INFO``      | Descriptor of variant data | :py:obj:`~.io.VcfParser.num_info`   | :meth:`~.io.VcfParser.get_info`   |
+---------------+----------------------------+-------------------------------------+-----------------------------------+
| ``META``      | Other meta-information     | :py:obj:`~.io.VcfParser.num_meta`   | :meth:`~.io.VcfParser.get_meta`   |
+---------------+----------------------------+-------------------------------------+-----------------------------------+

The last category, ``META``, represents all meta-information lines with a custom key (other
than ``ALT``, ``FILTER``, ``FORMAT``, and ``INFO``). To collect all user-defined
``META`` entries as a dictionary, use the following expression::

    >>> meta = dict([vcf.get_meta(i) for i in range(vcf.num_meta)])
    >>> print(meta)
    {'fileDate': '20090805', 'source': 'myImputationProgramV3.1', 'reference': 'file:///seq/referen
    ces/1000GenomesPilot-NCBI36.fasta', 'contig': '<ID=20,length=62435964,assembly=B36,md5=f126cdf8
    a6e0c7f379d618ff66beb2da,species="Homo sapiens",taxonomy=x>', 'phasing': 'partial'}

Reading variants
----------------

Due to the potentially large size of VCF files, the VCF parser follows 
an iterative scheme where lines are read one after another, only 
keeping the current one in memory. When iterating over a 
:class:`.io.VcfParser` instance, the returned values are  the 
chromosome name, the position (0 being the first position of the 
chromosome), and the number of alleles (including the reference 
allele)::

    >>> for ret in vcf:
    ...     print(ret)
    ...
    ('20', 14369, 2)
    ('20', 17329, 2)
    ('20', 1110695, 3)
    ('20', 1230236, 1)
    ('20', 1234566, 3)

It is also possible to iterate manually (reading variants one by one
without a ``for`` loop) using the global function :func:`next`::

    >>> vcf.rewind()
    >>> while vcf.good:
    ...     print(next(vcf))
    ... 
    ('20', 14369, 2)
    ('20', 17329, 2)
    ('20', 1110695, 3)
    ('20', 1230236, 1)
    ('20', 1234566, 3)

(:meth:`~.io.VcfParser.rewind` is a method to go back at the beginning 
of the file.) If ``next(vcf)`` is called again when ``vcf.good`` is 
``False``, then a :exc:`StopIteration` iteration is thrown (which is 
the standard behaviour for the implementation of iterable types in 
Python).

Importing a site
----------------

Data for the current site of a :class:`!VcfParser` instance can be 
extracted as a :class:`.Site` instance using either the function 
:func:`.site_from_vcf` or the instance method :meth:`.Site.from_vcf`, 
provided that the VCF file has called genotypes encoded using the 
``GT`` FORMAT field::

    >>> vcf = egglib.io.VcfParser('example.vcf')
    >>> print(next(vcf))
    ('20', 14369, 2)
    >>> site = egglib.site_from_vcf(vcf)
    >>> print(site.as_list())
    ['G', 'G', 'A', 'G', 'A', 'A']
    >>> print(next(vcf))
    ('20', 17329, 2)
    >>> site.from_vcf(vcf)
    >>> print(site.as_list())
    ['T', 'T', 'T', 'A', 'T', 'T']

Importing frequencies
---------------------

For your information, one can extract allelic frequencies as a 
:class:`.Freq` instance using :func:`.freq_from_vcf` or 
:meth:`.Freq.from_vcf`, provided that the VCF file has frequency 
information encoded using the ``AN`` and ``AC`` INFO fields, which is 
not the case for our example file.

Getting a variant as an object
------------------------------

To extract data manually for a given site, it is also possible to get 
all data at once. There is a :meth:`~.io.VcfParser.get_variant` method 
that returns an instance of a special type (:class:`.io.VcfVariant`). 
This is a proxy class, just like :class:`.SampleView`. Objects of the 
class :class:`!VcfVariant` provide a number of properties and methods 
that allow to read all desired data. We will just show a single 
example. The VCF file we use has a ``HQ`` FORMAT field (haplotype 
quality). We will extract it for each sample in a loop::

    >>> vcf = egglib.io.VcfParser('example.vcf')
    >>> for chrom, pos, nall in vcf:
    ...     v = vcf.get_variant()
    ...     if 'HQ' in v.format_fields:
    ...         print([i['HQ'] for i in v.samples])
    ...     else:
    ...         print('no data')
    ...
    [(51, 51), (51, 51), (None, None)]
    [(58, 50), (65, 3), None]
    [(23, 27), (18, 2), None]
    [(56, 60), (51, 51), None]
    no data

For each variant, we first tested that ``HQ`` is present in the FORMAT
fields for this variant (in one instance, it is not the case). If so,
it is extracted from the list of dictionaries provided as the property
:py:attr:`~.io.VcfVariant.samples`.
