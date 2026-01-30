"""
    Copyright 2015-2026 Stephane De Mita, Mathieu Siol

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
from .. import _interface, alphabets
from .. import _site

alphabet_genotypes = alphabets.Alphabet('range', (0, None), (-1, 0),
    case_insensitive=False, name='genotypes')

def haplotypes_from_align(aln, max_missing=0.0, impute_threshold=0, struct=None, dest=None, multiple=False):
    """
    Identification of haplotypes from an alignment.
    Identify haplotypes an :class:`.Align` instance and return data as a
    single :class:`.Site` instance containing one sample for each sample
    of the original data. Alleles in the returned site are representing
    all identified haplotypes (or missing data when the haplotypes could
    not be derived).

    .. note::
        There must be at least one site with at least two alleles (overall,
        including the outgroup), otherwise the produced site only contains
        missing data.

    :param aln: an :class:`.Align` instance.

    :param impute_threshold: by default, all samples with a least one
        occurrence of missing data will be treated as missing data. If
        this argument is more than 0, the provided value will be used as
        maximum number of missing data. All samples with as many or less
        missing data will be processed to determine which extant of
        haplotype they might belong (to which they are identical save
        for missing data). If there is only one such haplotype, the
        corresponding samples will be treated as a repetition of this
        haplotype. This option will never allow detecting new
        haplotypes. Only small values of this option make sense.

    :param struct: a :class:`.Structure` instance defining the samples
        to process. The population and cluster structures are not used.
        If the ploidy is larger than 1, the individuals are used, and
        sites are assumed to be phased.

    :param max_missing: maximum relative proportion of missing data in the ingroup
        to process a site.

        .. note::
            Here, *max_missing* is a relative proportion to allow
            using the same value for different alignments that might
            not have the same number of samples (to avoid reevaluating
            *max_missing* if the user wants the same maximum rate
            of missing data). In other functions, *max_missing* is
            the maximum *number* of missing and is an integer.

    :param dest: a :class:`.Site` instance that will be reset and in
        which data will be placed. If specified, this function returns
        nothing. By default, the function returns a new :class:`.Site`
        instance.

    :param multiple: allow sites with more than two alleles in the
        ingroup.

    :return: A :class:`.Site` instance, (if *dest* is ``None``) or ``None``
        (otherwise).

    .. note::
        If an empty list of sites is provided and no structure is provided,
        a :exc:`ValueError` is raised. To support smoothly possibly empty lists,
        the used is prompted to provide a structure.
    """
    if not isinstance(aln, _interface.Align): raise TypeError('expect an Align instance')
    return _haplotypes(aln, max_missing, impute_threshold, struct, dest, multiple)

def haplotypes_from_sites(sites, impute_threshold=0, struct=None, dest=None, multiple=False):
    """
    Identification of haplotypes from a list of sites.
    Similar to :meth:`haplotypes_from_align` but takes a list of :class:`.Site`
    instances. No option *max_missing* is available; all sites are always considered.
    """
    if not isinstance(sites, list): raise TypeError('expect a list of Site instances')
    if set(map(type, sites)) != set([_site.Site]): raise TypeError('expect a list of Site instances')
    return _haplotypes(sites, 1.0, impute_threshold, struct, dest, multiple)

def _haplotypes(sites, max_missing=0.0, impute_threshold=0, struct=None, dest=None, multiple=False):

    # check arguments / init
    if max_missing < 0.0 or max_missing > 1.0: raise ValueError('max_missing argument out of range')
    if impute_threshold < 0: raise ValueError('invalid value for impute_threshold argument')
    obj = _eggwrapper.Haplotypes()
    frq = _eggwrapper.FreqHolder()
    if struct is None:
        if isinstance(sites, _interface.Align):
            ni = sites._obj.get_nsam()
        else:
            if len(sites) == 0: raise ValueError('cannot process an empty list of sites')
            ni = sites[0]._obj.get_ns()
        struct_obj = _eggwrapper.StructureHolder()
        struct_obj.mk_dummy_structure(ni, 1)
        struct2_obj = struct_obj # used only with haplotypes_from_align
        pl = 1
        no = 0
    else:
        struct_obj = struct._obj
        struct2_obj = struct.make_sorted_auxiliary()._obj # used only with haplotypes_from_align
        pl = struct_obj.get_ploidy()
        ni = struct_obj.num_indiv_ingroup()
        no = struct_obj.num_indiv_outgroup()
    obj.setup(struct_obj)
    impute_idx = []
    min_exploitable = ni * pl - int(max_missing * pl * ni)

    # pass sites if they come from an alignment
    genosite = _eggwrapper.Genotypes()
    if isinstance(sites, _interface.Align):
        if struct_obj.get_req() > sites._obj.get_nsam(): raise ValueError('structure object does not match alignment')
        site = _eggwrapper.SiteHolder()
        for i in range(sites._obj.get_nsit_all()):
            site.reset()
            if site.process_align(sites._obj, i, struct_obj) < min_exploitable: # process_align returns number of valid ingroup samples
                continue
            frq.setup_structure(struct2_obj)
            frq.process_site(site)
            genosite.process(site, struct2_obj, False)
            nall = frq.frq_ingroup().num_alleles_eff()
            if frq.num_alleles() > 1 and (multiple == True or nall < 3):
                obj.load(genosite)
                if impute_threshold > 0: impute_idx.append(i)

        if obj.n_sites() == 0:
            if dest is None:
                return _site.site_from_list([-1 for i in range(ni+no) for j in range(pl)],
                                                alphabet = alphabet_genotypes)
            else:
                dest.process_list([-1 for i in range(ni+no) for j in range(pl)],
                                        alphabet = alphabet_genotypes, reset=True)
                return None

    # process list of Site
    else:
        if len(sites) > 0: ns = sites[0]._obj.get_ns()
        for i, site in enumerate(sites):
            if site._obj.get_ns() != ns: raise ValueError('number of samples must be consistent between sites')
            frq.setup_structure(struct_obj)
            frq.process_site(site._obj)
            if frq.frq_ingroup().nseff()+frq.frq_outgroup().nseff() < min_exploitable:
                continue
            genosite.process(site._obj, struct_obj, False)
            nall = frq.frq_ingroup().num_alleles_eff()
            if frq.num_alleles() > 1 and (multiple == True or nall < 3):
                obj.load(genosite)
                if impute_threshold > 0: impute_idx.append(i)

    # complete haplotype detection
    obj.cp_haplotypes()

    # impute if requested
    if impute_threshold > 0:
        obj.prepare_impute(impute_threshold)
        site = _eggwrapper.SiteHolder()
        for i in impute_idx:
            if isinstance(sites, _interface.Align):
                site.reset()
                site.process_align(sites._obj, i, struct_obj)
                genosite.process(site, struct2_obj, False)
                obj.resolve(genosite)
            else:
                genosite.process(sites[i]._obj, struct_obj, False)
                obj.resolve(genosite)
        obj.impute()

    # generate site
    if dest is None:
        dest = _site.Site()
        dest._alphabet = alphabet_genotypes
        obj.get_site(dest._obj)
        return dest
    else:
        dest._alphabet = alphabet_genotypes
        obj.get_site(dest._obj)
