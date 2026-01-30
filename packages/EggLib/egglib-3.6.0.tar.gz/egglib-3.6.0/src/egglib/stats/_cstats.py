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

import math
from .. import eggwrapper as _eggwrapper
from .. import _interface
from .. import _freq
from .. import _site
from .. io import _vcf

class ComputeStats(object):
    """ComputeStats(...)

    Customizable and efficient analysis of diversity
    data. This class is designed to minimize redundancy of underlying analyses
    so it is best to compute as many statistics as possible with a
    single instance. It also takes advantage of the object reuse policy,
    improving the efficiency of analyses when several (and especially
    many) datasets are examined in a row by the same instance of
    :class:`~.ComputeStats`.

    The constructor takes arguments that are automatically passed to the
    :meth:`configure` method.

    Statistics to compute are set using the method :meth:`~.ComputeStats.add_stats`
    which allows specifying several statistics at once and which can
    also be called several times to add more statistics to compute. It
    is possible to set at once all statistics of four pre-defined groups
    by passing the following codes (including the leading ``+``:
    ``+site`` (:ref:`stats_site`) and/or ``+unphased``
    (:ref:`stats_unphased`) and/or ``+phased`` (:ref:`stats_phased`),
    and/or ``+allelesize`` (:ref:`stats_allelesize`).

    .. warning::
        When an individual level is specified in the provided structure,
        it is by default assumed that the individual sequences are not
        phased. When computing statistics from the *phased* group,
        individuals are automatically (and silently) collapsed into
        genotypes (each individual is represented by a single allele
        representing the whole genotype), leading to information loss.
        If the data is actually phased, a workaround consists in
        skipping the individual in the structure for computing phased
        statistics. Starting with version 3.6, it is possible to use the
        *phased* argument

    .. versionchanged:: 3.3
        Added three-population site configuration statistic
        (``triconfig``) and argument *triconfig_min*.

    .. versionchanged:: 3.4
        Added admixture statistics (``f2``, ``f3``, ``f4`` and ``Dp``)
        and argument *f3_focus*.

    .. versionchanged:: 3.5
        Added groups of statistics.

    .. versionchanged:: 3.6
        Added *phased* argument.
        
    """

    def list_stats(self):
        """
        List of available statistics. Returns a list of tuples giving, for each
        available statistic, its code and a short description.
        """
        return [(k, v[0]) for (k, v) in self._stats.items()]

    def stats_group(self, grp):
        """
        Statistics of a group.
        Return a copy of the list of names of statistics belonging to a
        given group. If the group name is invalid, raise a
        :class:`KeyError`.

        .. versionadded:: 3.5
        """
        return list(self._groups[grp])

    def _get_genosite_from_store(self):
        if len(self._genosite_store): return self._genosite_store.pop()
        else: return _eggwrapper.Genotypes()

    def __init__(self, *args, **kwargs):
        self._sd = _eggwrapper.SiteDiversity()
        self._sd2 = _eggwrapper.SiteDiversity()
        self._as = _eggwrapper.AlleleStatus()
        self._d1 = _eggwrapper.Diversity1()
        self._d2 = _eggwrapper.Diversity2()
        self._h = _eggwrapper.Haplotypes()
        self._rd = _eggwrapper.Rd()
        self._ld = _eggwrapper.MatrixLD()
        self._cv = _eggwrapper.ComputeV()
        self._frq = _eggwrapper.FreqHolder()
        self._frq2 = _eggwrapper.FreqHolder()
        self._site = _eggwrapper.SiteHolder()
        self._genosite = _eggwrapper.Genotypes()
        self._genosite_cache = []
        self._genosite_store = []
        self._struct = None # structure (C++) passed as argument to configure()
        self._struct_auto = True
        self._triconfig = _eggwrapper.Triconfigurations()
        self._f3focuslabel = None
        self._phased = False

        self._stats = {
            # code        # description                                                 # flag  # toggler
            'ns_site':    ('Number of analyzed samples per site',                       'sd',   []), 
            'ns_site_o':  ('Number of analyzed outgroup samples per site',              'sd',   []), 
            'Aing':       ('Number of alleles in ingroup',                              'sd',   []),
            'Aotg':       ('Number of alleles in outgroup',                             'sd',   []),
            'Atot':       ('Number of alleles in whole dataset',                        'sd',   []),
            'As':         ('Number of singleton alleles',                               'sd',   []),
            'Asd':        ('Number of singleton alleles (derived)',                     'sd',   []),
            'R':          ('Allelic richness',                                          'sd',   []),
            'thetaIAM':   ('Theta estimator based on He & IAM model',                   'sd',   []),
            'thetaSMM':   ('Theta estimator based on He & SMM model',                   'sd',   []),
            'He':         ('Expected heterozygosity',                                   'sd',   []),
            'Ho':         ('Observed heterozygosity',                                   'sd',   []),
            'Fis':        ('Inbreeding coefficient',                                    'sd',   []),
            'maf':        ('Relative frequency of the minority allele',                 'sd',   []),
            'maf_pop':    ('maf per population (minority allele overall)',              'sd',   []),

            'FstWC':      ('Weir and Cockerham for haploid data',                       'sd',   [self._sd.toggle_fstats_haplo]),
            'FistWC':     ('Weir and Cockerham for diploid data',                       'sd',   [self._sd.toggle_fstats_diplo]),
            'FisctWC':    ('Weir and Cockerham for hierarchical structure',             'sd',   [self._sd.toggle_fstats_hier]),

            'f2':         ('Patterson et al\'s f2',                                     'sd',   []),
            'f3':         ('Patterson et al\'s f3',                                     'sd',   []),
            'f4':         ('Patterson et al\'s f4',                                     'sd',   []),
            'Dp':         ('Patterson et al\'s D',                                      'sd',   []),

            'Dj':         ('Jost\'s D',                                                 'sd',   [self._sd.toggle_hstats]),
            'Hst':        ('Hudson\'s Hst',                                             'sd',   [self._sd.toggle_hstats]),
            'Gst':        ('Nei\'s Gst',                                                'sd',   [self._sd.toggle_hstats]),
            'Gste':       ('Hedrick\'s Gst\'',                                          'sd',   [self._sd.toggle_hstats]),

            'numSp':      ('Number of population-specific alleles',                     'as',   []),
            'numSpd':     ('Number of population-specific derived alleles',             'as',   []),
            'numShA':     ('Number of shared alleles',                                  'as',   []),
            'numShP':     ('Number of shared segregating alleles',                      'as',   []),
            'numFxA':     ('Number of fixed alleles',                                   'as',   []),
            'numFxD':     ('Number of fixed differences',                               'as',   []),
            'numSp*':     ('Sites with at least 1 pop-specific allele',                 'as',   []),
            'numSpd*':    ('Sites with at least 1 pop-specific derived allele',         'as',   []),
            'numShA*':    ('Sites with at least 1 shared allele',                       'as',   []),
            'numShP*':    ('Sites with at least 1 shared segregating allele',           'as',   []),
            'numFxA*':    ('Sites with at least 1 fixed allele',                        'as',   []),
            'numFxD*':    ('Sites with at least 1 fixed difference',                    'as',   []),
            'triconfig':  ('Site configurations with three populations',                'tf',   []),

            'lseff':      ('Number of analysed sites',                                  'd1',   []),
            'nsmax':      ('Maximal number of available samples per site',              'd1',   []),
            'S':          ('Number of segregating sites',                               'd1',   []),
            'Ss':         ('Number of sites with only one singleton allele',            'd1',   []),
            'eta':        ('Minimal number of mutations',                               'd1',   []),
            'Pi':         ('Nucleotide diversity',                                      'd1',   []),

            'sites':      ('Index of polymorphic sites',                                'd1',   [self._d1.toggle_site_lists]),
            'singl':      ('Index of sites with at least one singleton allele',         'd1',   [self._d1.toggle_site_lists]),
            'nall':       ('Number of ingroup alleles at polymorphic sites',            'd1',   [self._d1.toggle_site_lists]),
            'frq':        ('Allelic frequencies at polymorphic sites',                  'd1',   [self._d1.toggle_site_lists]),
            'frqp':       ('Population allelic frequencies at polymorphic sites',       'd1',   [self._d1.toggle_site_lists]),

            'lseffo':     ('Number of analysed orientable sites',                       'd1',   [self._d1.toggle_ori_site]),
            'nsmaxo':     ('Maximal number of available samples per orientable site',   'd1',   [self._d1.toggle_ori_site]),
            'sites_o':    ('Index of orientable polymorphic sites',                     'd1',   [self._d1.toggle_site_lists, self._d1.toggle_ori_site]),
            'singl_o':    ('Index of sites with at least one singleton allele',         'd1',   [self._d1.toggle_site_lists, self._d1.toggle_ori_site]),
            'So':         ('Number of segregating orientable sites',                    'd1',   [self._d1.toggle_ori_site]),
            'Sso':        ('Number of orientable sites with only one singleton allele', 'd1',   [self._d1.toggle_ori_site]),
            'nsingld':    ('Number of derived singletons',                              'd1',   [self._d1.toggle_ori_site]),
            'etao':       ('Minimal number of mutations are orientable sites',          'd1',   [self._d1.toggle_ori_site]),
            'nM':         ('Number of sites available for MFDM test',                   'd1',   [self._d1.toggle_ori_site]),
            'pM':         ('P-value of MDFM test',                                      'd1',   [self._d1.toggle_ori_site]),

            'nseffo':     ('Average number of exploitable samples at orientable sites', 'd1',   [self._d1.toggle_ori_div]),
            'thetaPi':    ('Pi using orientable sites',                                 'd1',   [self._d1.toggle_ori_div]),
            'thetaH':     ('Fay and Wu\'s estimator of theta',                          'd1',   [self._d1.toggle_ori_div]),
            'thetaL':     ('Zeng et al.\'s estimator of theta',                         'd1',   [self._d1.toggle_ori_div]),
            'Hns':        ('Fay and Wu\'s H (unstandardized)',                          'd1',   [self._d1.toggle_ori_div]),
            'Hsd':        ('Fay and Wu\'s H (standardized)',                            'd1',   [self._d1.toggle_ori_div]),
            'E':          ('Zeng et al.\'s E',                                          'd1',   [self._d1.toggle_ori_div]),
            'Dfl':        ('Fu and Li\'s D',                                            'd1',   [self._d1.toggle_ori_div]),
            'F':          ('Fu and Li\'s F',                                            'd1',   [self._d1.toggle_ori_div]),

            'nseff':      ('Average number of exploitable samples',                     'd1',   [self._d1.toggle_basic]),
            'thetaW':     ('Watterson\'s estimator of theta',                           'd1',   [self._d1.toggle_basic]),
            'Dxy':        ('Pairwise distance (if two populations)',                    'd1',   [self._d1.toggle_basic]),
            'Da':         ('Net pairwise distance (if two populations)',                'd1',   [self._d1.toggle_basic]),
            'D':          ('Tajima\'s D',                                               'd1',   [self._d1.toggle_basic]),
            'Deta':       ('Tajima\'s D using eta instead of S',                        'd1',   [self._d1.toggle_basic]),
            'D*':         ('Fu and Li\'s D*',                                           'd1',   [self._d1.toggle_basic]),
            'F*':         ('Fu and Li\'s F*',                                           'd1',   [self._d1.toggle_basic]),
            'R2':         ('Ramos-Onsins and Rozas\'s R2 (using singletons)',           'd2',   [self._d2.toggle_singletons]),
            'R3':         ('Ramos-Onsins and Rozas\'s R3 (using singletons)',           'd2',   [self._d2.toggle_singletons]),
            'R4':         ('Ramos-Onsins and Rozas\'s R4 (using singletons)',           'd2',   [self._d2.toggle_singletons]),
            'Ch':         ('Ramos-Onsins and Rozas\'s Ch (using singletons)',           'd2',   [self._d2.toggle_singletons]),

            'R2E':        ('Ramos-Onsins and Rozas\'s R2E (using external singletons)', 'd2',   [self._d2.toggle_singletons]),
            'R3E':        ('Ramos-Onsins and Rozas\'s R3E (using external singletons)', 'd2',   [self._d2.toggle_singletons]),
            'R4E':        ('Ramos-Onsins and Rozas\'s R4E (using external singletons)', 'd2',   [self._d2.toggle_singletons]),
            'ChE':        ('Ramos-Onsins and Rozas\'s ChE (using external singletons)', 'd2',   [self._d2.toggle_singletons]),

            'B':          ('Wall\'s B statistic',                                       'd2',   [self._d2.toggle_partitions]),
            'Q':          ('Wall\'s Q statistic',                                       'd2',   [self._d2.toggle_partitions]),

            'Kt':         ('Number of haplotypes',                                      'h',    []),
            'Ki':         ('Number of haplotypes (only ingroup)',                       'h',    []),
            'FstH':       ('Hudson\'s Fst',                                             'h',    [self._toggle_haplotype_stats]),
            'Kst':        ('Hudson\'s Kst',                                             'h',    [self._toggle_haplotype_stats]),
            'Snn':        ('Hudson\'s nearest nearest neighbour statistic',             'h',    [self._toggle_haplotype_stats]),

            'rD':         ('R_bar{d} statistic',                                        'rD',   []),

            'Rmin':       ('Minimal number of recombination events',                    'LD',   [self._ld.toggle_Rmin]),
            'RminL':      ('Number of sites used to compute Rmin',                      'LD',   [self._ld.toggle_Rmin]),
            'Rintervals': ('List of start/end positions of recombination intervals',    'LD',   [self._ld.toggle_Rmin]),
            'nPairs':     ('Number of allele pairs used for ZnS, Z*nS, and Z*nS*',      'LD',   [self._ld.toggle_stats]),
            'nPairsAdj':  ('Allele pairs at adjacent sites (used for ZZ and Za)',       'LD',   [self._ld.toggle_stats]),
            'ZnS':        ('Kelly et al.\'s ZnS',                                       'LD',   [self._ld.toggle_stats]),
            'Z*nS':       ('Kelly et al.\'s Z*nS',                                      'LD',   [self._ld.toggle_stats]),
            'Z*nS*':      ('Kelly et al.\'s Z*nS*',                                     'LD',   [self._ld.toggle_stats]),
            'Za':         ('Rozas et al.\'s Za',                                        'LD',   [self._ld.toggle_stats]),
            'ZZ':         ('Rozas et al.\'s ZZ',                                        'LD',   [self._ld.toggle_stats]),

            'Fs':         ('Fu\'s Fs',                                                  'Fs',   []),

            'V':          ('Allele size variance',                                      'V',    []),
            'Ar':         ('Allele range',                                              'V',    []),
            'M':          ('Garza and Williamson (2001)\'s M',                          'V',    []),
            'Rst':        ('Slatkin (1995)\'s Rst',                                     'V',    [])
        }

        self._groups = {'site': [],
                        'unphased': [],
                        'phased': [],
                        'allelesize': []}
        for code, infos in self._stats.items():
            match infos[1]:
                case 'sd' |  'as' | 'tf':
                    self._groups['site'].append(code)
                case 'd1':
                    self._groups['unphased'].append(code)
                case 'd2' | 'h' | 'rD' | 'LD' | 'Fs':
                    self._groups['phased'].append(code)
                case 'V':
                    self._groups['allelesize'].append(code)
                case _:
                    raise RuntimeError(f'internal bug (flag {infos[1]} is not handled)')

        self.clear_stats()
        self.configure(*args, **kwargs)

    def reset(self):
        """
        Reset all currently computed statistics. Keep the list of
        statistics to compute.
        """
        self._sd.reset()
        self._sd2.reset()
        self._as.reset()
        self._d1.reset_stats()
        self._d2.reset_stats()
        self._h.reset_stats()
        self._rd.reset_stats()
        self._ld.reset()
        self._cv.reset()
        self._triconfig.reset()
        self._site_index = 0
        self._static_sites = True # set to False if sites cannot be considered to be static (required for LD stats)
        self._genosite_store.extend(self._genosite_cache)
        del self._genosite_cache[:]
        if self._struct_auto: self._struct = None

    def configure(self,
                  struct = None,
                  multi = False,
                  multi_hits = False,
                  maf = 0.0,
                  LD_min_n = 2,
                  LD_max_maj = 1.0,
                  LD_multiallelic = 0,
                  LD_min_freq = 0,
                  Rmin_oriented = False,
                  triconfig_min = 2,
                  f3_focus = None,
                  phased = False):
        """
        Configure the instance. The values provided for parameters will
        affect all subsequent analyses. Calling this method resets all
        statistics.

        :param struct: a :class:`.Structure` instance describing the
            structure of objects that will be passed. If individuals are
            specified, see warning in class description.

        :param multi: process several alignments, set of sites, or sites
            in a row and only yield statistics when :meth:`.results` is
            called (each of the method considered will return ``None``).

        :param multi_hits: allow multiple mutations at the same site
            (some statistics, like Rmin or Wall's B and Q, never
            consider multiple mutations regardless of this option).

        :param maf: minimum minor allele frequency (sites for which the
            relative minority allele frequency is lower than this will
            be excluded).

        :param LD_min_n: Minimal number of non-missing samples. Allows to
            specify a more stringent filter than *max_missing*.
            Only considered for calculating Rozas *et al.*'s and Kelly's
            statistics (the most stringent of the two criteria applies).

        :param LD_max_maj: Maximal relative frequency of the main allele.
            Only considered for calculating Rozas *et al.*'s and Kelly's
            statistics.

        :param LD_multiallelic: One of 0 (ignore them), 1 (use main
            allele only), and 2 (use all possible pairs of alleles).
            Defines what is done for pairs of sites of which one or
            both have more than two alleles (while computing linkage
            disequilibrium). In case of option 2, a filter can be
            applied with option *LD_min_freq*. Only considered for
            calculating Rozas *et al.*'s and Kelly's statistics.

        :param LD_min_freq: Only considered if option 2 is used for
            *LD_multiallelic*. Only consider alleles that are in
            absolute frequency equal to or larger than the given value.
            Only considered for calculating Rozas *et al.*'s and Kelly's
            statistics

        :param Rmin_oriented: Only for computing Rmin: use only
            orientable sites.

        :param triconfig_min: Only for site configurations with three
            populations: minimal number of available sample per
            population.

        :param f3_focus: Specify the label of the focal population
            (required for computing ``f3``).

        :param phased: ``True`` if ploidy is above 1 and individuals are
            phased (alleles at a given index within individuals
            constitute a haplotype). By default, individuals are
            supposed to be unphased. Note that this option has no effect
            on the standardized association index ``rD``, which does not
            consider the phase of alleles within of individuals.
        """

        self._phased = phased # BEFORE set_structure
        self.set_structure(struct) # also resets
        if LD_min_n < 0: raise ValueError('LD_min_n is too small')
        self._LD_min_n = LD_min_n
        if LD_max_maj <= 0.0 or LD_max_maj > 1.0: raise ValueError('LD_max_maj out of range')
        self._LD_max_maj = LD_max_maj
        if LD_multiallelic < 0: raise ValueError('LD_multiallelic cannot be negative')
        try: self._LD_multiallelic = [_eggwrapper.MatrixLD.ignore,
                                      _eggwrapper.MatrixLD.use_main,
                                      _eggwrapper.MatrixLD.use_all][LD_multiallelic]
        except IndexError: raise ValueError('LD_multiallelic out of range')
        if LD_min_freq < 0: raise ValueError('LD_min_freq out of range')
        self._LD_min_freq = LD_min_freq
        self._Rmin_oriented = Rmin_oriented
        self._multi_hits = bool(multi_hits)
        self._multi = bool(multi)
        self._d1.set_option_multiple(multi_hits)
        self._d2.set_option_multiple(multi_hits)
        self._sd.set_maf(maf)
        self._sd2.set_maf(maf)
        self._cv.set_maf(maf)
        if triconfig_min < 2: raise ValueError("triconfig_min must be at least 2")
        self._triconfig.set_min(triconfig_min)
        self._f3focuslabel = f3_focus

    def set_structure(self, struct):
        """
        Set the structure object. Reset statistics but don't change the
        list of statistics to compute and don't change other parameter
        values.

        If individuals are specified, see warning in class description.
        """
        self.reset()
        if struct is None:
            self._struct_auto = True
            self._struct = None
            self._aux = None
            self._phased_aux = None
        else:
            self._struct_auto = False
            self._struct = struct._obj
            self._aux = struct.make_auxiliary()._obj
            self._aux_sorted = struct.make_sorted_auxiliary()._obj
            if self._phased:
                d1, d2 = struct.as_dict()
                cnt = 0
                for K in d1:
                    for P in d1[K]:
                        d = {}
                        for I in d1[K][P]:
                            for S in d1[K][P][I]:
                                d[f'idv{cnt+1}'] = [S]
                                cnt += 1
                        d1[K][P] = d
                d = {}
                for I in d2:
                    for S in d2[I]:
                        d[f'idv{cnt+1}'] = [S]
                        cnt += 1
                phasedstruct = _interface.struct_from_dict(d1, d)
                self._phased_struct = phasedstruct._obj
                self._phased_aux = phasedstruct.make_auxiliary()._obj
            else:
                self._phased_struct = self._struct
                self._phased_aux = self._aux
            self._h.setup(self._phased_aux)
            self._d2.set_structure(self._phased_aux)
            self._ld.set_structure(self._phased_aux)
            self._rd.configure(struct._obj) # doesn't use genosite

    def _check_struct(self, ns):
        if self._struct_auto or self._struct is None:
            struct = _eggwrapper.StructureHolder()
            struct.mk_dummy_structure(ns, 1)
            if self._struct is None: self._h.setup(struct)
            else: self._h.set_structure(struct) # does not reset stats
            self._d2.set_structure(struct)
            self._rd.configure(struct)
            self._ld.set_structure(struct) # no difference between struct and aux
            self._struct = struct
            self._aux = struct # identical because no actual structure
            self._phased_aux = struct # idem
            self._aux_sorted = struct # idem
            self._sd.f4flag(False)
        else:
            if self._struct.get_req() > ns: raise ValueError('structure does not match number of samples')
            if self._f3focuslabel:
                for i in range(self._struct.num_pop()):
                    if self._f3focuslabel == self._struct.get_population(i).get_label():
                        if i not in range(3):
                            raise ValueError('structure must have three populations')
                        self._sd.f3focus(i)
                        break
                else:
                    raise ValueError(f'invalid population label: {self._f3focuslabel}')
            else:
                self._sd.f3focus(3) # if auto struct: irrelevant
            if self._struct.num_clust() == 2 and self._struct.get_cluster(0).num_pop() == 2 and self._struct.get_cluster(1).num_pop() == 2:
                self._sd.f4flag(True)
            else:
                self._sd.f4flag(False)

    def add_stats(self, *stats):
        """
        add_stats(stat, ...)

        Add one or more statistics to compute. Every statistic
        identifier must be among the list of available statistics or
        one of the four statistics group identifiers (which start with
        a ``+`` character), regardless of what data is to be analyzed.
        If statistics cannot be computed, they will be returned as
        ``None``.

        .. versionchanged:: 3.5
            Support stats groups.
        """
        for stat in stats:
            if len(stat) > 1 and stat[0] == '+':
                try: self.add_stats(*self._groups[stat[1:]])
                except KeyError: raise ValueError(f'invalid group: {stat}')
            else:
                if stat not in self._stats:
                    raise ValueError('invalid statistic: {0}'.format(stat))
                self._wanted_stats.add(stat)
                self._flags[self._stats[stat][1]] = True;
                for f in self._stats[stat][2]: f()
        if self._flags['Fs']:
            self._flags['d1'] = True
            self._flags['h'] = True
        if (self._flags['as'] or self._flags['d1'] or self._flags['d2']
                              or self._flags['rD'] or self._flags['LD']
                              or self._flags['h']):
            self._flags['sd'] = True

    def all_stats(self):
        """
        Add all possible statistics. Those who cannot be computed will
        be reported as ``None``. Also reset all currently computed statistics (if any).
        Note that allele size statistics require integer alleles, so use
        of this method would result in an error if DNA-alphabet data
        are loaded. It is preferable to use ``add_stats('+site', '+unphased', '+phased')``
        for adding all statistics compatible with all types of data.
        """
        self.add_stats(*self._stats)

    def clear_stats(self):
        """
        Clear the list of statistics to compute.
        """
        self._wanted_stats = set()
        self._flags = dict.fromkeys([self._stats[k][1] for k in self._stats], False)
        self._sd.toggle_off()
        self._sd2.toggle_off()
        self._d1.toggle_off()
        self._ld.toggle_off()
        self._toggle_off()

    def _toggle_off(self):
        self._flag_haplotype_stats = False

    def _toggle_haplotype_stats(self):
        self._flag_haplotype_stats = True

    def process_freq(self, frq, position=None):
        """
        Analyze already computed frequencies.

        :param frq: a :class:`.Freq` instance.
        :param position: position of the site. Must be an integer value.
            By default, use the site loading index.
        :return: A dictionary of statistics, unless *multi* is set.
        """

        self._sd.f4flag(False)

        if not self._multi:
            stats = dict.fromkeys(self._wanted_stats, None)

        if position is None: position = self._site_index

        if self._flags['tf'] == True:
            self._triconfig.process(frq._obj)

        if self._flags['sd'] == True:
            res = self._sd.process(frq._obj)
            if not self._multi: self._get_sd_stats(res, stats)

        if self._flags['as'] == True and (res & 1024) != 0 and self._sd.npop_eff1() > 1:
            self._as.process(frq._obj)
            if not self._multi: self._get_as_stats(stats)

        if self._flags['d1'] == True and (res & 2) != 0:
            self._d1.load(frq._obj, self._sd, position)

        if self._flags['V'] == True:
            if frq._alphabet.type not in ['int', 'range']: raise ValueError('cannot compute V, Ar, M, and Rst with this alphabet')
            b = self._cv.compute(frq._obj, frq._alphabet._obj)
            if not self._multi and b:
                if 'V' in stats: stats['V'] = self._cv.curr_V()
                if 'Ar' in stats: stats['Ar'] = self._cv.curr_Ar()
                if 'M' in stats and self._cv.curr_M() != _eggwrapper.UNDEF: stats['M'] = self._cv.curr_M()
                if 'Rst' in stats and self._cv.curr_Rst() != _eggwrapper.UNDEF: stats['Rst'] = self._cv.curr_Rst()

        self._site_index += 1
        if not self._multi: return stats

    def process_site(self, site, position=None):
        """
        Analyze a site.

        :param site: a :class:`.Site` instance.
        :param position: position of the site. Must be an integer value.
            By default, use the site index.
        :return: A dictionary of statistics, unless *multi* is set.
        """

        self._check_struct(site._obj.get_ns())
        if position is None: position = self._site_index
        if not self._multi: stats = dict.fromkeys(self._wanted_stats, None)
        if self._flags['d2'] or self._flags['h']: # add LD for process_sites/process_align
            self._genosite.process(site._obj, self._struct, self._phased)
            if self._flags['d2']:
                self._frq2.setup_structure(self._phased_aux)
                self._frq2.process_site(self._genosite.site())
                self._sd2.process(self._frq2)
        self._frq.setup_structure(self._struct)
        self._frq.process_site(site._obj)
        if self._flags['tf'] == True:
            self._triconfig.process(self._frq)
        if self._flags['sd'] == True:
            res = self._sd.process(self._frq)
            if not self._multi: self._get_sd_stats(res, stats)
        if self._flags['as'] == True and (res & 1024) != 0 and self._sd.npop_eff1() > 1:
            self._as.process(self._frq)
            if not self._multi: self._get_as_stats(stats)
        if self._flags['d1'] == True and (res & 2) != 0:
            self._d1.load(self._frq, self._sd, position)
        if self._flags['d2'] == True and (res & 2) != 0:
            self._d2.load(self._genosite.site(), self._sd2, self._frq2)
        if self._flags['h'] == True and self._sd.Aglob() > 1 and (self._sd.Aing() == 2 or self._multi_hits == True):
            self._h.load(self._genosite)
        if self._flags['rD'] == True:
            self._rd.load(site._obj)
        if self._flags['V'] == True:
            if site._alphabet.type not in ['int', 'range']: raise ValueError('cannot compute V, Ar, M, and Rst with this alphabet')
            b = self._cv.compute(self._frq, site._alphabet._obj)
            if not self._multi and b:
                if 'V' in stats: stats['V'] = self._cv.curr_V()
                if 'Ar' in stats: stats['Ar'] = self._cv.curr_Ar()
                if 'M' in stats and self._cv.curr_M() != _eggwrapper.UNDEF: stats['M'] = self._cv.curr_M()
                if 'Rst' in stats and self._cv.curr_Rst() != _eggwrapper.UNDEF: stats['Rst'] = self._cv.curr_Rst()
        self._site_index += 1
        if self._multi: self._static_sites = False
        else: return stats

    def process_sites(self, sites, positions=None):
        """
        Analyze a list of sites.

        :param sites: a list, or other sequence of :class:`.Site`
            instance. (:class:`.VcfWindow` instances
            with a number of sites greater than 0 are also supported.)
        :param positions: a list, or other sequence of positions for all
            sites, or ``None``. If ``None``, use the index of each site. Otherwise,
            must be a sequences of integer values (length matching the
            length of *sites*).
        :return: A dictionary of statistics, unless *multi* is set.
        """

        if positions is None:
            positions = (self._site_index + i for i in range(len(sites)))
        elif len(positions) != len(sites):
            raise ValueError('number of positions must match the number of sites')
        if len(sites) > 0:
            for site, pos in zip(sites, positions):
                self._check_struct(site._obj.get_ns())
                self._frq.setup_structure(self._struct)
                self._frq.process_site(site._obj)
                keep = False
                if self._flags['d2'] or self._flags['h'] or self._flags['LD']:
                    self._genosite.process(site._obj, self._struct, self._phased)
                    if self._flags['d2']:
                        self._frq2.setup_structure(self._phased_aux)
                        self._frq2.process_site(self._genosite.site())
                        self._sd2.process(self._frq2)
                if self._flags['tf'] == True:
                    self._triconfig.process(self._frq)
                if self._flags['sd'] == True: res = self._sd.process(self._frq)  # don't require consistency
                if self._flags['as'] == True and (res & 1024) != 0 and self._sd.npop_eff1() > 1: self._as.process(self._frq)  # don't require consistency
                if self._flags['d1'] == True and (res & 2) != 0: self._d1.load(self._frq, self._sd, pos)  # don't require consistency
                if self._flags['d2'] == True and (res & 2) != 0:
                    self._d2.load(self._genosite.site(), self._sd2, self._frq2)
                if self._flags['h'] == True and self._sd.Aglob() > 1 and (self._multi_hits == True or self._sd.Aing() < 3):
                    self._h.load(self._genosite)
                    keep |= True
                if self._flags['rD'] == True and (res & 2) != 0 and self._sd.Aing() > 1: self._rd.load(site._obj)
                if self._flags['LD'] == True and (res & 2) != 0 and (self._sd.Aing() == 2 or (self._sd.Aing() > 2 and self._LD_multiallelic != _eggwrapper.MatrixLD.ignore)):
                    keep |= True
                    self._ld.load(self._genosite, pos)
                if self._flags['V'] == True:
                    if site._alphabet.type not in ['int', 'range']: raise ValueError('cannot compute V, Ar, M, and Rst with this alphabet')
                    self._cv.compute(self._frq, site._alphabet._obj)

                # if need to keep site, put it in cache and claim new
                if keep:
                    self._genosite_cache.append(self._genosite)
                    self._genosite = self._get_genosite_from_store()

        self._site_index += len(sites)
        if self._multi: self._static_sites = False # prevent attempting using sites (which may be invalidated)
        else: return self.results()

    def process_align(self, align, positions=None, max_missing=0.0):
        """
        Analyze an alignment.

        :param align: an :class:`.Align` instance.
        :param positions: a list, or other sequence of positions for all
            sites, or ``None``. If ``None``, use the index of each site. Otherwise,
            must be a sequences of integer values (length matching the
            number of sites).
        :param max_missing: Maximum relative proportion of missing data (excluding
            outgroup). The default is to exclude all sites with missing data. Missing
            data include all ambiguity characters and alignment gaps.
            Sites not passing this threshold are ignored for all
            analyses.

            .. note::
                Here, *max_missing* is a relative proportion to allow
                using the same value for different alignments that might
                not have the same number of samples (to avoid reevaluating
                *max_missing* if the user wants the same maximum rate
                of missing data). In other functions, *max_missing* is
                the maximum *number* of missing and is an integer.

        :return: A dictionary of statistics, unless *multi* is set.
        """
        if not isinstance(align, _interface.Align): raise TypeError('expect an Align instance')

        # check max_missing
        max_missing = float(max_missing)
        if max_missing < 0.0 or max_missing > 1.0:
            raise ValueError('invalid value for `max_missing` argument: {0}'.format(max_missing))

        # get number of sites and positions
        ls = align._obj.get_nsit_all()
        if positions is None:
            positions = (self._site_index + i for i in range(ls))
        elif len(positions) != ls:
            raise ValueError('number of positions must match the number of sites')

        self._check_struct(align._obj.get_nsam())
        ns = self._struct.get_ni()
        no = self._struct.get_no()

        # get max_missing number
        min_valid = math.floor(ns - max_missing * ns)

        # process sites
        for idx, pos in enumerate(positions):
            self._site.reset()
            if self._site.process_align(align._obj, idx, self._struct) < min_valid:
                continue

            if self._flags['d2'] or self._flags['h'] or self._flags['LD']:
                self._genosite.process(self._site, self._aux_sorted, self._phased)
                if self._flags['d2']:
                    self._frq2.setup_structure(self._phased_aux)
                    self._frq2.process_site(self._genosite.site())
                    self._sd2.process(self._frq2)

            self._frq.setup_structure(self._aux_sorted)
            self._frq.process_site(self._site)

            keep = False
            if self._flags['tf'] == True: self._triconfig.process(self._frq)
            if self._flags['sd'] == True: res = self._sd.process(self._frq)
            if self._flags['as'] == True and (res & 1024) != 0 and self._sd.npop_eff1() > 1: self._as.process(self._frq)

            if self._flags['d1'] == True and (res & 2) != 0: self._d1.load(self._frq, self._sd, pos)
            if self._flags['d2'] == True and (res & 2) != 0:
                self._d2.load(self._genosite.site(), self._sd2, self._frq2)
            if self._flags['h'] == True and self._sd.Aglob() > 1 and (self._multi_hits == True or self._sd.Aing() < 3):
                self._h.load(self._genosite)
                keep |= True
            if self._flags['rD'] == True and (res & 2) != 0 and self._sd.Aing() > 1:
                self._rd.load(self._site) # Rd does not assume that data are phased
            if self._flags['LD'] == True and (res & 2) != 0 and (self._sd.Aing() == 2 or (self._sd.Aing() > 2 and self._LD_multiallelic != _eggwrapper.MatrixLD.ignore)):
                self._ld.load(self._genosite, pos)
                keep |= True
            if self._flags['V'] == True:
                if align._alphabet.type not in ['int', 'range']: raise ValueError('cannot compute V, Ar, M, and Rst with this alphabet')
                self._cv.compute(self._frq, align._alphabet._obj)

            # if need to keep site, put it in cache and claim new
            if keep:
                self._genosite_cache.append(self._genosite)
                self._genosite = self._get_genosite_from_store()

        self._site_index += ls
        if not self._multi: return self.results()

    def results(self):
        """
        Get computed statistics.
        Return the value of statistics for all sites since the last call
        to this method, to :meth:`reset`, or any addition of statistics,
        or the object creation,
        whichever is most recent. For statistics that can not be
        computed, ``None`` is returned.
        """

        stats = dict.fromkeys(self._wanted_stats, None)
        if self._flags['tf'] == True:
            stats['triconfig'] = [self._triconfig.cnt(i) for i in range(13)]
        if self._flags['sd'] == True:
            res = self._sd.average()
            self._get_sd_stats(res, stats)
        if self._flags['as'] == True:
            self._as.total()
            if (res & 1024) != 0 and self._sd.npop_eff1() > 1:
                self._get_as_stats(stats)
                if self._as.nsites() > 0:
                    if 'numSp*' in stats: stats['numSp*'] = self._as.Sp_T1()
                    if 'numSpd*' in stats and self._as.nsites_o() > 0: stats['numSpd*'] = self._as.Spd_T1()
                    if 'numShP*' in stats: stats['numShP*'] = self._as.ShP_T1()
                    if 'numShA*' in stats: stats['numShA*'] = self._as.ShA_T1()
                    if 'numFxD*' in stats: stats['numFxD*'] = self._as.FxD_T1()
                    if 'numFxA*' in stats: stats['numFxA*'] = self._as.FxA_T1()

        if self._flags['d1'] == True:
            res = self._d1.compute()
            if 'lseff'  in stats: stats['lseff'] =  self._d1.ls()
            if 'lseffo'  in stats: stats['lseffo'] =   self._d1.lso()
            if (res & 1) != 0:
                if 'nsmax'   in stats: stats['nsmax'] =    self._d1.nsmax()
                if 'S'       in stats: stats['S'] =        self._d1.S()
                if 'Ss'      in stats: stats['Ss'] =       self._d1.Ss()
                if 'sites'   in stats: stats['sites'] =    [self._d1.site(i) for i in range(self._d1.S())]
                if 'singl'   in stats: stats['singl'] =    [self._d1.singl(i) for i in range(self._d1.Ss())]
                if 'nall'    in stats: stats['nall'] =     [self._d1.nall(i) for i in range(self._d1.S())]
                if 'frq'     in stats: stats['frq'] =      [[self._d1.frq(i, j) for j in range(self._d1.nall(i))] for i in range(self._d1.S())]
                if 'frqp'    in stats: stats['frqp'] =     [[[self._d1.frqp(i, j, k) for k in range(self._struct.num_pop())] for j in range(self._d1.nall(i))] for i in range(self._d1.S())]
                if 'eta'     in stats: stats['eta'] =      self._d1.eta()
                if 'Pi'      in stats: stats['Pi'] =       self._d1.Pi()
            if (res & 8) != 0:
                if 'nsmaxo'  in stats: stats['nsmaxo'] =   self._d1.nsmaxo()
                if 'So'      in stats: stats['So'] =       self._d1.So()
                if 'Sso'     in stats: stats['Sso'] =      self._d1.Sso()
                if 'nsingld' in stats: stats['nsingld'] =  self._d1.nsingld()
                if 'sites_o' in stats: stats['sites_o'] =  [self._d1.site_o(i) for i in range(self._d1.So())]
                if 'singl_o' in stats: stats['singl_o'] =  [self._d1.singl_o(i) for i in range(self._d1.Sso())]
                if 'etao'    in stats: stats['etao'] =     self._d1.etao()
                if 'nM'      in stats: stats['nM'] =       self._d1.nM()
            if (res & 16) != 0:
                if 'pM'      in stats: stats['pM'] =       self._d1.pM()
            if (res & 32) != 0:
                if 'nseffo'  in stats: stats['nseffo'] =   self._d1.nseffo()
                if 'thetaPi' in stats: stats['thetaPi'] =  self._d1.thetaPi()
                if 'thetaH'  in stats: stats['thetaH'] =   self._d1.thetaH()
                if 'thetaL'  in stats: stats['thetaL'] =   self._d1.thetaL()
                if 'Hns'     in stats: stats['Hns'] =      self._d1.Hns()
            if (res & 1024) != 0:
                if 'Hsd'     in stats: stats['Hsd'] =      self._d1.Hsd()
            if (res & 2048) != 0:
                if 'E'       in stats: stats['E'] =        self._d1.E()
            if (res & 4096) != 0:
                if 'Dfl'     in stats: stats['Dfl'] =      self._d1.Dfl()
            if (res & 8192) != 0:
                if 'F'       in stats: stats['F'] =        self._d1.F()
            if (res & 128) != 0:
                if 'nseff'   in stats: stats['nseff'] =    self._d1.nseff()
                if 'thetaW'  in stats: stats['thetaW'] =   self._d1.thetaW()
            if (res & 16384) != 0:
                if 'Dxy'     in stats: stats['Dxy'] =      self._d1.Dxy()
                if 'Da'      in stats: stats['Da'] =       self._d1.Da()
            if (res & 256) != 0:
                if 'F*'      in stats: stats['F*'] =       self._d1.Fstar()
            if (res & 512) != 0:
                if 'D'       in stats: stats['D'] =        self._d1.D()
                if 'Deta'    in stats: stats['Deta'] =     self._d1.Deta()
                if 'D*'      in stats: stats['D*'] =       self._d1.Dstar()

        if self._flags['d2'] == True:
            res = self._d2.compute()
            if (res & 1) == 0:
                if (res & 256) != 0:
                    if 'R2' in stats: stats['R2'] = self._d2.R2()
                    if 'R3' in stats: stats['R3'] = self._d2.R3()
                    if 'R4' in stats: stats['R4'] = self._d2.R4()
                    if 'Ch' in stats: stats['Ch'] = self._d2.Ch()
                if (res & 512) != 0:
                    if 'R2E' in stats: stats['R2E'] = self._d2.R2E()
                    if 'R3E' in stats: stats['R3E'] = self._d2.R3E()
                    if 'R4E' in stats: stats['R4E'] = self._d2.R4E()
                    if 'ChE' in stats: stats['ChE'] = self._d2.ChE()
                if (res & 1024) != 0:
                    if 'B' in stats: stats['B'] = self._d2.B()
                    if 'Q' in stats: stats['Q'] = self._d2.Q()

        if self._flags['h'] == True and self._h.n_sites() > 0 and not self._h.invalid():
            self._h.cp_haplotypes()
            if 'Kt' in stats and (self._h.ne_ing() > 0 or self._h.ne_otg() > 0): stats['Kt'] = self._h.ng_hapl()
            if self._h.ne_ing() > 0 and 'Ki' in stats: stats['Ki'] = self._h.ni_hapl()
            if self._flag_haplotype_stats:
                self._h.cp_dist()
                res = self._h.cp_stats()
                if 'FstH' in stats and res & 1 != 0: stats['FstH'] = self._h.Fst()
                if 'Kst' in stats and res & 2 != 0: stats['Kst'] = self._h.Kst()
                if 'Snn' in stats:
                    stats['Snn'] = self._h.Snn()
                    if stats['Snn'] == _eggwrapper.UNDEF: stats['Snn'] = None

        if 'Fs' in stats and self._h.n_sites() and self._h.ne_ing() > 1:
            stats['Fs'] = _eggwrapper.Fs(self._h.ne_ing(), self._h.ni_hapl(), self._d1.Pi())

        if self._static_sites == True and 'rD' in stats:
            stats['rD'] = self._rd.compute()
            if stats['rD'] == _eggwrapper.UNDEF: stats['rD'] = None

        if self._static_sites == True and self._flags['LD'] == True:
            flag = self._ld.process(self._LD_min_n, self._LD_max_maj,
                                    self._LD_multiallelic, self._LD_min_freq,
                                    self._Rmin_oriented)
            if 'nPairs' in stats: stats['nPairs'] = self._ld.num_allele_pairs()
            if 'nPairsAdj' in stats: stats['nPairsAdj'] = self._ld.num_allele_pairs_adj()
            if 'RminL' in stats: stats['RminL'] = self._ld.Rmin_num_sites()
            if (flag&1) != 0:
                if 'ZnS' in stats: stats['ZnS'] = self._ld.ZnS()
                if 'Z*nS' in stats: stats['Z*nS'] = self._ld.ZnS_star1()
                if 'Z*nS*' in stats: stats['Z*nS*'] = self._ld.ZnS_star2()
            if (flag&2) != 0:
                if 'Za' in stats: stats['Za'] = self._ld.Za()
                if 'ZZ' in stats: stats['ZZ'] = self._ld.ZZ()
            if (flag&4) != 0:
                if 'Rmin' in stats: stats['Rmin'] = self._ld.Rmin()
                if 'Rintervals' in stats: stats['Rintervals'] = [(self._ld.Rmin_left(i), self._ld.Rmin_right(i)) for i in range(self._ld.Rmin())]

        if self._flags['V']:
            if self._cv.num_sites() > 0:
                if 'V' in stats: stats['V'] = self._cv.average_V()
                if 'Ar' in stats: stats['Ar'] = self._cv.average_Ar()
                if 'M' in stats and self._cv.num_sites_m() > 0: stats['M'] = self._cv.average_M()
                if 'Rst' in stats and self._cv.average_Rst() != _eggwrapper.UNDEF: stats['Rst'] = self._cv.average_Rst()

        self.reset()
        return stats

    def _get_sd_stats(self, flag, stats):
        if (flag & 1) != 0 and 'ns_site' in stats:
            if (flag & 512) != 0: stats['ns_site'] = int(self._sd.ns())
            else: stats['ns_site'] = self._sd.ns()
        if (flag & 1) != 0 and 'ns_site_o' in stats:
            if (flag & 512) != 0: stats['ns_site_o'] = int(self._sd.nso())
            else: stats['ns_site_o'] = self._sd.nso()
        if (flag & 2) != 0:
            if 'Aing' in stats:
                if (flag & 512) != 0: stats['Aing'] = int(self._sd.Aing())
                else: stats['Aing'] = self._sd.Aing()
            if 'Atot' in stats:
                if (flag & 512) != 0: stats['Atot'] = int(self._sd.Aglob())
                else: stats['Atot'] = self._sd.Aglob()
            if 'As' in stats:
                if (flag & 512) != 0: stats['As'] = int(self._sd.S())
                else: stats['As'] = self._sd.S()
            if 'R' in stats: stats['R'] = self._sd.R()
            if 'He' in stats: stats['He'] = self._sd.He()

        if (flag & 4) != 0:
            if 'thetaIAM' in stats: stats['thetaIAM'] = self._sd.thetaIAM()
            if 'thetaSMM' in stats: stats['thetaSMM'] = self._sd.thetaSMM()

        if (flag & 8) != 0:
            if 'Ho' in stats: stats['Ho'] = self._sd.Ho()
            if 'Fis' in stats and self._sd.He() > 0.0:
                stats['Fis'] = 1 - self._sd.Ho() / self._sd.He()

        if (flag & 16) != 0:
            if 'Asd' in stats:
                if (flag & 512) != 0: stats['Asd'] = int(self._sd.Sd())
                else: stats['Asd'] = self._sd.Sd()

        if (flag & 16384) != 0:
            if 'Aotg' in stats:
                if (flag & 512) != 0: stats['Aotg'] = int(self._sd.Aout())
                else: stats['Aotg'] = self._sd.Aout()

        if (flag & 32) != 0 and 'FstWC' in stats:
            n = self._sd.n()
            d = self._sd.d()
            stats['FstWC'] = n/d if d > 0.0 else None

        if (flag & 64) != 0 and 'FistWC' in stats and self._struct.get_ploidy() > 1:
            a = self._sd.a()
            b = self._sd.b()
            c = self._sd.c()
            stats['FistWC'] = ( 1.0 - c/(b+c) if (b+c) > 0.0 else None,
                a/(a+b+c), 1.0 - c/(a+b+c)) if (a+b+c) > 0.0 else None

        if (flag & 128) != 0 and 'FisctWC' in stats and self._struct.get_ploidy() > 1:
            a0 = self._sd.a0()
            b2 = self._sd.b2()
            b1 = self._sd.b1()
            c0 = self._sd.c0()
            stats['FisctWC'] = ( 1.0 - c0/(b1+c0) if (b1+c0) > 0.0 else None,
                    (a0+b2) / (a0+b2+b1+c0), a0/(a0+b2+b1+c0),
                    1.0 - c0/(a0+b2+b1+c0)) if (a0+b2+b1+c0) > 0.0 else None

        if (flag & 256) != 0:
            if 'Dj' in stats: stats['Dj'] = self._sd.D()
            if 'Hst' in stats and (flag & 2048) != 0: stats['Hst'] = self._sd.Hst()
            if 'Gst' in stats and (flag & 4096) != 0: stats['Gst'] = self._sd.Gst()
            if 'Gste' in stats and (flag & 8192) != 0: stats['Gste'] = self._sd.Gste()

        if (flag & 1024) != 0:
            if 'maf' in stats: stats['maf'] = self._sd.maf()
            if 'maf_pop' in stats: stats['maf_pop'] = [self._sd.maf_pop(i) for i in range(self._sd.num_pop())]

        if (flag & (1<<15)) and 'f2' in stats:
            stats['f2'] = self._sd.f2()

        if (flag & (1<<16)) and 'f3' in stats:
            stats['f3'] = self._sd.f3()

        if (flag & (1<<17)) and 'f4' in stats:
            stats['f4'] = self._sd.f4()

        if (flag & (1<<18)) and 'Dp' in stats:
            stats['Dp'] = self._sd.Dp()

    def _get_as_stats(self, stats):
        if self._as.nsites() > 0:
            if 'numSp' in stats: stats['numSp'] = self._as.Sp()
            if 'numSpd' in stats and self._as.nsites_o() > 0: stats['numSpd'] = self._as.Spd()
            if 'numShP' in stats: stats['numShP'] = self._as.ShP()
            if 'numShA' in stats: stats['numShA'] = self._as.ShA()
            if 'numFxD' in stats: stats['numFxD'] = self._as.FxD()
            if 'numFxA' in stats: stats['numFxA'] = self._as.FxA()
