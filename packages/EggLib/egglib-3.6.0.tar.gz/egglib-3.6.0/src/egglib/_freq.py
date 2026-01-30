"""
    Copyright 2016-2023 Stephane De Mita, Mathieu Siol

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

import numbers
from . import eggwrapper as _eggwrapper
from . import alphabets, _interface

def freq_from_site(site, struct=None):
    """
    Compute allele frequencies from a site.

    :param site: a :class:`.Site` instance.
    :param struct: this argument can be:

        * A :class:`.Structure` instance , allowing to select a subset
          of samples and/or define the structure.
        * A :class:`list` (or compatible) of at least one integer
          providing the sample size (as numbers of samples) of all
          populations, assuming the individuals are organized in the
          corresponding order (all samples of a given population
          grouped together). Samples are grouped in haploid
          individuals.
        * ``None`` (no structure, all samples placed in haploid
          individuals and in a single population).

    :return: A new :class:`.Freq` instance.
    """
    obj = Freq()
    obj.from_site(site, struct)
    return obj

def freq_from_list(ingroup, outgroup, geno_list=None, alphabet=None):
    """
    Import allele frequencies.

    :param ingroup: a list of genotype or allele frequencies (based
        on the value of *geno_list*). There must be one item for each
        allele. If there is a single list, a unique population is
        assumed. To specify multiple populations, the user must pass a
        list of lists (each inner list containing the same number of
        items representing allele frequencies). To specify multiple
        clusters, the user must pass a list of lists of lists of allele
        frequencies. There may also be single-item lists when necessary.
        The frequencies must be null or positive integers. The number of
        frequencies per population is required to be constant for all
        populations (corresponding to the number of alleles or genotypes).
        If *geno_list* is defined, data must be the frequencies of the
        provided genotypes, in the same order. Otherwise, data must be
        allelic frequencies, in the order of increasing allele index (in
        the latter case, data will be loaded as haploid).
    :param outgroup: a list of allele/genotype frequencies for the
        outgroup. The number of alleles or genotypes is also required to
        match. If ``None``, no outgroup samples (equivalent to a list of
        zeros).
    :param geno_list: list of genotypes. Genotypes must be provided as
        tuples or lists. Their length is equal to the ploidy and is
        required to be at least one and constant for all genotypes. For
        haploid data, it is still required to passed allelic values as
        one-item lists (with a ploidy of one). Order
        of alleles within genotypes is significant. If ``None``, data are
        loaded as haploid alleles and the index of alleles is taken as
        allelic value.
    :param alphabet: alphabet to be used to describe alleles. Required
        if *geno_list* is used. By default, use a 

    :return: A new :class:`.Freq` instance.

    .. note::
    
        It is required that there is at least one cluster and one
        population.
    """
    obj = Freq()
    obj.from_list(ingroup, outgroup, geno_list, alphabet)
    return obj

def freq_from_vcf(vcf):
    """
    Import allelic frequencies from a VCF parser. The VCF parser
    must have processed a variant and the variant is required to have
    frequency data available as the AC format field along with the AN
    field. An exception is raised otherwise.

    This function only imports haploid allele frequencies in the ingroup
    (without structure). The first allele is the reference, by
    construction, then all the alternate alleles in the order in which
    they are provided in the VCF file.

    :param vcf: a :class:`.VcfParser` instance containing data. There
        must at least one sample and the AN/AC format fields must be
        available. It is not required to extract variant data manually.
    """
    obj = Freq()
    obj.from_vcf(vcf)
    return obj

class Freq(object):
    """
    Hold allelic and genotypic frequencies for a single site.
    Instances can be created using the three functions :func:`.freq_from_site`,
    :func:`.freq_from_list`, and :func:`.freq_from_vcf`, or using the
    default constructor. After it is created by any way, instances can be
    re-used (which is faster), using their methods :meth:`~.Freq.from_site`,
    :meth:`~.Freq.from_list`, and :meth:`~.Freq.from_vcf`.

    .. _compartments:

    :cvar ingroup: whole ingroup.
    :cvar outgroup: outgroup.
    :cvar cluster: a specific cluster (identified by its index).
    :cvar population: a specific population (identified by its index).

    The variables above specify what subset of data should be
    considered. You should never try to modify them. For clusters and
    populations, an index should be provided as well.

    They can be used as::

        >>> freq.freq_allele(allele_index, cpt=egglib.Freq.ingroup)
        >>> freq.freq_allele(allele_index, cpt=egglib.Freq.population, idx=pop_index)

    or::

        >>> freq.freq_allele(allele_index, cpt=freq.ingroup)
        >>> freq.freq_allele(allele_index, cpt=freq.population, idx=pop_index)

    """
    ingroup = 0
    outgroup = 1
    cluster = 2
    population = 3

    def __init__(self):
        self._obj = _eggwrapper.FreqHolder()
        self._alphabet = None

    def from_site(self, site, struct=None):
        """
        Import frequencies from a site.
        Reset the instance as if it was created using
        :func:`.freq_from_site`. Arguments are identical to this function.
        """
        if struct is None:
            struct = _eggwrapper.StructureHolder()
            struct.mk_dummy_structure(site._obj.get_ns(), 1)
        elif isinstance(struct, _interface.Structure):
            struct = struct._obj
            if struct.get_req() > site._obj.get_ns(): raise ValueError('invalid structure (sample index out of range)')
        else:
            if len(struct) < 1: raise ValueError('there must be at least one population size')
            if sum(struct) != site._obj.get_ns(): raise ValueError('invalid structure (sample size is required to match)')
            struct = _eggwrapper.StructureHolder()
            struct.mk_dummy_structure(struct[0], 1)
            for i in struct[1:]: struct.dummy_add_pop(i)
        self._obj.setup_structure(struct)
        self._obj.process_site(site._obj)
        self._alphabet = site._alphabet

    def from_list(self, ingroup, outgroup, geno_list=None, alphabet=None):
        """ Import frequencies from lists.
        Reset the instance as if it was created using :func:`.freq_from_list`.
        Arguments are identical to this function.
        """

        # reformat ingroup argument
        if all([isinstance(i, numbers.Integral) for i in ingroup]):
            ingroup = [[ingroup]]
        elif all([isinstance(j, numbers.Integral) for i in ingroup for j in i]):
            ingroup = [ingroup]
        else:
            if not all([isinstance(k, numbers.Integral) for i in ingroup for j in i for k in j]):
                raise ValueError('invalid form for the `ingroup` argument')

        # get structure properties
        nc = len(ingroup)
        ns = [sum(pop) for clu in ingroup for pop in clu]
        np = len(ns)
        ni = sum(ns)

        # get number of genotypes
        ng = set(map(len, [j for i in ingroup for j in i]))
        if outgroup is not None: ng.add(len(outgroup))
        if len(ng) != 1: raise ValueError('number of frequencies must be the same for all populations and outgroup')
        ng = ng.pop()
        if ng < 1: raise ValueError('there must be at least one allele')
        if outgroup is None: outgroup = [0] * ng
        no = sum(outgroup)
        if geno_list is None:
            pl = 1
            geno_list = [[i,] for i in range(ng)]
            if alphabet is None:
                self._alphabet = alphabets.positive_infinite
            else:
                self._alphabet = alphabet
                try: [self._alphabet.get_value(i) for i in range(ng)]
                except ValueError:
                    raise ValueError('alphabet does not have enough values')

        else:
            if ng != len(geno_list): raise ValueError('invalid number of genotypes')
            pl = set(map(len, geno_list))
            if len(pl) != 1: raise ValueError('ploidy is not constant in genotypes')
            pl = pl.pop()
            if pl < 1: raise ValueError('ploidy must be at least 1')
            geno_set = set()
            for g in geno_list:
                if g in geno_set: raise ValueError('genotype {0} is repeated'.format(g))
                geno_set.add(g)
            if alphabet is None: raise ValueError('alphabet must be specified')
            self._alphabet = alphabet

        # list with allele index (not code!) instead of allele value from geno_list
        geno_indexes = [[None for j in i] for i in geno_list]

        # setup the instance
        self._obj.setup_raw(nc, np, pl)
        idx = 0
        for i, clu in enumerate(ingroup):
            for j, pop in enumerate(clu):
                self._obj.setup_pop(idx, i, j, sum(pop))
                idx += 1
        self._obj.set_ngeno(ng)
        for i, g in enumerate(geno_list):
            for j, v in enumerate(g):
                v = self._alphabet.get_code(v)
                if v < 0: raise ValueError('missing data found in genotypes')
                self._obj.set_genotype_item(i, j, v)
                geno_indexes[i][j] = self._obj.find_allele(v)

        # load data
        pop_idx = 0
        ing_frq = self._obj.frq_ingroup()
        for clu_idx, clu_data in enumerate(ingroup):
            clu_frq = self._obj.frq_cluster(clu_idx)
            for pop_data in clu_data:
                pop_frq = self._obj.frq_population(pop_idx)
                for i, n in enumerate(pop_data):
                    ing_frq.incr_genotype(i, n)
                    clu_frq.incr_genotype(i, n)
                    pop_frq.incr_genotype(i, n)
                    for j in geno_indexes[i]:
                        ing_frq.incr_allele(j, n)
                        clu_frq.incr_allele(j, n)
                        pop_frq.incr_allele(j, n)
                pop_idx += 1

        otg_frq = self._obj.frq_outgroup()
        for i, n in enumerate(outgroup):
            otg_frq.incr_genotype(i, n)
            for j in geno_indexes[i]:
                otg_frq.incr_allele(j, n)

        # load heterozygote genotypes
        if pl > 1:
            for i, g in enumerate(geno_indexes):
                g = set(g)
                if len(g) > 1:
                    for j in g:
                        self._obj.frq_ingroup().tell_het(i, j)
                        self._obj.frq_outgroup().tell_het(i, j)
                        for k in range(self._obj.num_clusters()):
                            self._obj.frq_cluster(k).tell_het(i, j)
                        for k in range(self._obj.num_populations()):
                            self._obj.frq_population(k).tell_het(i, j)

    def from_vcf(self, vcf):
        """ Import frequencies from a VCF file.
        Reset the instance as if it was created using :func:`.freq_from_vcf`.
        Argument is identical to this function.
        """
        if vcf._parser.has_data() == False: raise ValueError('data must have been read from VCF parser')
        if vcf._parser.has_AC() == False or vcf._parser.has_AN() == False: raise ValueError('VCF data must have AC and AN info fields')
        self._obj.process_vcf(vcf._parser)
        self._alphabet = alphabets.positive_infinite

    @property
    def ploidy(self):
        """ Ploidy. """
        return self._obj.ploidy()

    @property
    def num_alleles(self):
        """ Number of alleles in the whole site. """
        return self._obj.num_alleles()

    @property
    def num_genotypes(self):
        """ Number of genotypes in the whole site. """
        return self._obj.num_genotypes()

    @property
    def num_clusters(self):
        """ Number of clusters. """
        return self._obj.num_clusters()

    @property
    def num_populations(self):
        """ Number of populations. """
        return self._obj.num_populations()

    def allele(self, idx):
        """Get an allele."""
        if idx<0 or idx>=self._obj.num_alleles():
            raise IndexError('invalid allele index')
        return self._alphabet.get_value(self._obj.allele(idx))

    def genotype(self, idx):
        """ Get a genotype, as a tuple of alleles. """
        if idx<0 or idx>=self._obj.num_genotypes():
            raise IndexError('invalid genotype index')
        return tuple(self._alphabet.get_value(self._obj.genotype_item(idx, i)) for i in range(self._obj.ploidy()))

    def _getter(self, cpt, idx):
        if cpt == self.ingroup: return self._obj.frq_ingroup()
        elif cpt == self.outgroup: return self._obj.frq_outgroup()
        elif cpt == self.cluster:
            if idx is None:
                raise ValueError('cluster index is required')
            if idx<0 or idx>= self._obj.num_clusters():
                raise IndexError('invalid cluster index')
            return self._obj.frq_cluster(idx)
        elif cpt == self.population:
            if idx is None:
                raise ValueError('population index is required')
            if idx<0 or idx>= self._obj.num_populations():
                raise IndexError('invalid population index')
            return self._obj.frq_population(idx)
        else: raise ValueError('invalid compartment identifier')

    def freq_allele(self, allele, cpt=ingroup, idx=None):
        """
        Get the frequency of an allele.

        :param allele: allele index.
        :param cpt: :ref:`compartment <compartments>` identifier.
        :param idx: compartment index (required for clusters and
            populations, ignored otherwise).
        """
        if allele<0 or allele>=self._obj.num_alleles(): raise IndexError('invalid allele index')
        return self._getter(cpt, idx).frq_all(allele)

    def freq_genotype(self, genotype, cpt=ingroup, idx=None):
        """
        Get the frequency of an genotype.

        :param genotype: genotype index.
        :param cpt: :ref:`compartment <compartments>` identifier.
        :param idx: compartment index (required for clusters and
            populations, ignored otherwise).
        """
        if genotype<0 or genotype>=self._obj.num_genotypes(): raise IndexError('invalid genotype index')
        return self._getter(cpt, idx).frq_gen(genotype)

    def nieff(self, cpt=ingroup, idx=None):
        """
        Get the number of individuals within a given compartment. In
        the haploid case, this method is identical to :meth:`.nseff`.

        :param cpt: :ref:`compartment <compartments>` identifier.
        :param idx: compartment index (required for clusters and
            populations, ignored otherwise).
        """
        return self._getter(cpt, idx).nieff()

    def nseff(self, cpt=ingroup, idx=None):
        """
        Get the number of samples within a given compartment.

        :param cpt: :ref:`compartment <compartments>` identifier.
        :param idx: compartment index (required for clusters and
            populations, ignored otherwise).
        """
        return self._getter(cpt, idx).nseff()
