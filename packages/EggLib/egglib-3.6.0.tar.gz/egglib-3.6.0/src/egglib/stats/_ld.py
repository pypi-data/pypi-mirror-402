"""
    Copyright 2015-2023 Stephane De Mita, Mathieu Siol

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

from .. import eggwrapper as _eggwrapper
from .. import _interface
from .. import _site

def _get_stats(pld, multiple_policy, min_freq):
    if pld.num_alleles1() > 2 or pld.num_alleles2() > 2:
        if multiple_policy == 'forbid':
            raise ValueError('at least one locus has more than two alleles and this is not allowed')
        elif multiple_policy == 'main':
            freq1 = [pld.freq1(i) for i in range(pld.num_alleles1())]
            freq2 = [pld.freq2(i) for i in range(pld.num_alleles2())]
            a1 = [freq1.index(max(freq1))]
            a2 = [freq2.index(max(freq2))]
        elif multiple_policy == 'average':
            a1 = [i for i in range(pld.num_alleles1()) if pld.freq1(i) >= min_freq]
            a2 = [i for i in range(pld.num_alleles2()) if pld.freq2(i) >= min_freq]
        else:
            raise ValueError('invalid value for `multiple_policy` option: {0}'.format(multiple_policy))
    else:
        a1 = [0]
        a2 = [0]

    n = 0
    D = 0.0
    Dp = 0.0
    r = 0.0
    rsq = 0.0
    for i in a1:
        for j in a2:
            n += 1
            pld.compute(i, j)
            D += pld.D()
            Dp += pld.Dp()
            r += pld.r()
            rsq += pld.rsq()
    if n == 0:
        return {'D': None, 'Dp': None, 'r': None, 'rsq': None}
    if n > 1:
        D /= n
        Dp /= n
        r /= n
        rsq /= n
    return {'D': D, 'Dp': Dp, 'r': r, 'rsq': rsq, 'n': n}

def pairwise_LD(locus1, locus2, struct=None, multiple_policy='main', min_freq=0):
    """
    Linkage disequilibium between a pair of loci.
    
    :class:`.Site` instances must be used to describe loci. Only the order of
    samples is considered and both loci must have the same number of
    samples.

    :param locus1: A :class:`.Site` instance.

    :param locus2: A :class:`.Site` instance.

    :param struct: A :class:`.Structure` object used to describe the
        individual level. If specified, genotypes are automatically
        described and genotypic linkage is processed. By default, consider
        all samples as originating from haploid individuals.

    :param multiple_policy: Determine what is done if either input locus
        has more than two alleles. Possible values are, ``"forbid"``
        (raise an exception if this occurs), ``"main"`` (take
        the most frequent allele of each locus) and ``"average"`` (
        compute the unweighted average over all possible pair of
        alleles). More options might be added in future versions. This
        option is ignored if both loci have less than three alleles. If
        ``"main"`` and there are several equally most frequent alleles,
        the first-occurring one is used (arbitrarily).

    :param min_freq: Only used if at least one site has more than two
        alleles and *multiple_policy* is set to *average*. Set the
        minimum absolute frequency to consider an allele.

    :return: A :class:`dict` of linkage disequilibrium statistics. In case
        statistics cannot be computed (either site fixed, or less than
        two samples with non-missing data at both sites), computed
        values are replaced by ``None``. ``n`` gives the number of pairs
        of alleles considered (0 if statistics are not computed at all).
    """

    if locus1.ns != locus2.ns: raise ValueError('the number of samples must match in the two loci')
    if locus1.ns < 2: raise ValueError('the number of samples must be at least 2')

    if struct is None:
        struct = _eggwrapper.StructureHolder()
        struct.mk_dummy_structure(locus1.ns, 1)
        struct2 = struct
    else:
        if struct.req_ns > locus1.ns: raise ValueError('mismatch with structure')
        struct2 = struct.make_auxiliary()._obj
        struct = struct._obj

    site1 = _eggwrapper.Genotypes()
    site2 = _eggwrapper.Genotypes()
    site1.process(locus1._obj, struct, False)
    site2.process(locus2._obj, struct, False)
    frq1 = _eggwrapper.FreqHolder()
    frq1.setup_structure(struct2)
    frq1.process_site(site1.site())
    frq2 = _eggwrapper.FreqHolder()
    frq2.setup_structure(struct2)
    frq2.process_site(site2.site())
    ld = _eggwrapper.PairwiseLD()
    if not ld.process(site1.site(), site2.site(), frq1, frq2, struct2, 0, 1.0):
        return {'D': None, 'Dp': None, 'r': None, 'rsq': None, 'n': 0}
    return _get_stats(ld, multiple_policy, min_freq)

def matrix_LD(align, stats, struct=None, multiple_policy='main',
        min_freq=0, min_n=2, max_maj=1.0, positions=None):
    r"""
    Linkage disequilibrium statistics between all
    pairs of sites. The computed statistics
    are selected by an argument of this function. Return a matrix (as a
    nested :class:`list`) of the requested statistics. In all cases, all
    pairs of sites are present in the returned matrices. If statistics
    cannot be computed, they are replaced by :data:`None`.

    The available statistics are:

    * ``d`` -- Distance between sites of the pairs.
    * ``D`` -- Standard linkage disequilibrium.
    * ``Dp`` -- Lewontin's D'.
    * ``r`` -- Correlation coefficient.
    * ``rsq`` -- Equivalent to r\ :sup:`2`.

    :param align: An :class:`.Align` instance.

    :param stats: Requested statistic or statistics (see list of
        available statistics above, as a single string or as a list of
        one or more of these statistics (in any order).

    :param struct: A :class:`.Structure` object used to describe the
        individual level. If specified, genotypes are automatically
        described and genotypic linkage is processed. By default, consider
        all samples as originating from haploid individuals.

    :param multiple_policy: Specify what is done for pairs of sites for
        which at least one locus has only one allele. See
        :func:`pairwise_LD` for further description.

    :param min_freq: Only used if at least one site has more than two
        alleles and depending on the value of *multiple_policy*.  See
        :func:`pairwise_LD` for further description.

    :param min_n: Minimum number of samples used (this value must
        always be larger than 1). Sites not fulfilling this criterion
        will be dropped.

    :param max_maj: Maximum relative frequency of the majority allele.
        Sites not fulfilling this criterion will be dropped.

    :param positions: A sequence of positions, whose length must match
        the number of sites of the provided alignment. Used in the
        return value to describe the used sites, and, if requested, to
        compute the distance between sites. By default, the position of
        sites in the original alignment is used.

    :return: A :class:`tuple` with two items: first is the :class:`list` of
        positions of sites used in the matrix (a subset of the sites of
        the provided alignment), with positions provided by the
        corresponding argument (by default, the index of sites); second
        is the matrix, as the nested lower half matrix. The matrix
        contains items for all i and j indexes with 0 <= j <= i < n
        where n is the number of retained sites. The content of the
        matrix is represented by a single value (if a single statistic
        has been requested) or as a list of 1 or more values (if a list
        of 1 or more, accordingly, statistics have been requested), or
        ``None`` for the diagonal or if the pairwise comparison was
        dropped for any reason.
    """

    # initialize local variables
    mLD = _eggwrapper.MatrixLD()
    retained = []
    if struct is None:
        struct = _eggwrapper.StructureHolder()
        struct.mk_dummy_structure(align.ns, 1)
    else:
        struct = struct._obj
    mLD.set_structure(struct)

    # check arguments
    min_n = int(min_n)
    if min_n < 2: raise ValueError('too small value for `min_n` argument: {0}'.format(min_n))
    max_maj = float(max_maj)
    if max_maj < 0.5 or max_maj > 1.0: raise ValueError('invalid value for `max_maj` argument: {0}'.format(max_maj))

    if positions is None:
        positions = list(map(float, range(align.ls)))
    elif len(positions) != (struct.get_ni() + struct.get_no()):
        raise ValueError('list of positions does not have the right number of items')

    if stats in ['D', 'Dp', 'r', 'rsq']:
        multi = False
        stats = [stats]
    else:
        multi = True

    # make a list of variable sites
    genosite = _eggwrapper.Genotypes()
    genosites = [] # need to be kept to perform calculations
    site = _site.Site()
    final_positions = []
    sd = _eggwrapper.SiteDiversity()
    frq = _eggwrapper.FreqHolder()
    frq.setup_structure(struct)
    for i in range(align.ls):
        site.from_align(align, i)
        genosite.process(site._obj, struct, False)
        frq.process_site(genosite.site())
        if (sd.process(frq)&2) != 0 and sd.Aing() > 1.0:
            final_positions.append(positions[i])
            mLD.load(genosite, positions[i])
            genosites.append(genosite)
            genosite = _eggwrapper.Genotypes()

    matrix = [[None for j in range(i+1)] for i in range(len(genosites))]

    # compute LD
    mLD.computeLD(min_n, max_maj)

    # extract requested values
    for i in range(mLD.num_pairs()):
        pld = mLD.pairLD(i)
        idx2 = mLD.index1(i)
        idx1 = mLD.index2(i) # reverse indexes
        computed_stats = _get_stats(pld, multiple_policy, min_freq)
        matrix[idx1][idx2] = []
        for stat in stats:
            if stat == 'd': matrix[idx1][idx2].append( final_positions[idx1] - final_positions[idx2] )
            elif stat == 'D': matrix[idx1][idx2].append( computed_stats['D'] )
            elif stat == 'Dp': matrix[idx1][idx2].append( computed_stats['Dp'] )
            elif stat == 'r': matrix[idx1][idx2].append( computed_stats['r'] )
            elif stat == 'rsq': matrix[idx1][idx2].append( computed_stats['rsq'] )
            else: raise ValueError('invalid statistic code: `{0}`'.format(stat))
        if not multi:
            matrix[idx1][idx2] = matrix[idx1][idx2][0]

    # return
    return final_positions, matrix
