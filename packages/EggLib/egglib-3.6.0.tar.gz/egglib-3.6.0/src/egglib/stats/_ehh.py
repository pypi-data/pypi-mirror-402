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
from .. import _interface
from .. import _site

class EHH(object):
    r"""
    Extended Haplotype Homozygosity statistics.
    Statistics can be computed for unphased genotypic data.

    The usage of this class is to: to first set the core haplotypes by
    passing a :class:`.Site` to :meth:`.set_core` and then to
    load repetitively distant sites (always with increasing distance
    from the core), through :meth:`.load_distant`, until the list of
    sites to process is exhausted or one of the thresholds has been
    reached.

    In order to process distant sites using the same core region to the
    opposite direction, or to use a different core region, it is always
    required to call :meth:`!set_core` again (this is the only way to
    reset the instance).

    After at least one distant site site is loaded, EHH statistics can
    be accessed using there accessors. EHH statistics fell into four
    categories:

    1. Raw EHH statistics, provided for each loaded distant sites and
       separately for each core haplotype. See the methods:
       :meth:`.get_EHH`, :meth:`.get_EHHc`, and :meth:`.get_rEHH`.

       .. admonition:: Reference

           Sabeti P.C., D.E. Reich, J.M. Higgins, H.Z.P. Levine,
           D.J. Richter, S.F. Schaffner, S.B. Gabriel, J.V. Platko, N.J.
           Patterson, G.J. McDonald, H.C. Ackerman, S.J. Campbell, D.
           Altshuler, R. Cooper, D. Kwiatkowski, R. Ward & E.S. Lander.
           2002. Detecting recent positive selection in the human genome
           from haplotype structure. *Nature* **419**\ : 832-837.

    2. Integrated EHH statistics, computed separately for each core
       haplotype and incremented at each provided sites until the EHH
       value reaches the thresholds provided as the *EHH_thr* and
       *EHHc_thr* arguments to :meth:`!set_core`. See the methods
       :meth:`.get_iHH`, :meth:`.get_iHHc`, and :meth:`.get_iHS`. The
       methods :meth:`.done_EHH` and :meth:`.done_EHHc` allow to check
       whether the threshold has been reached for all genotypes.

       .. admonition:: Reference

           Voight B.F., S. Kudaravalli, X. Wen & J.K. Pritchard.
           2006. A map of recent positive selection in the human genome.
           *PLoS Biol* **4**\ : e772.

    3. Whole-site EHHS statistic and its integrated version iES, which
       is incremented as long that the EHHS value is larger than or equal to
       the threshold provided as the *EHHS_thr* argument to
       :meth:`!set_core`. See the methods :meth:`.get_EHHS` and
       :meth:`.get_iES`. If data are unphased, a specific EHHS estimate
       based on homozygosity is provided (EHHG, with its iEG integrated
       counter-part).

       .. admonition:: Reference

           Tang K., K.R. Thornton & M. Stoneking. 2007. A new
           approach for using genome scans to detect recent positive
           selection in the human genome. *PLoS Biol.* **5**\ : e171.

    4. EHH, EHHS, and EHHG decay statistics, that give the minimal distance at
       which, respectively, EHH starts to be smaller than the threshold
       provided as the *EHH_thr* argument to :meth:`!set_core`, EHHS
       starts to be smaller than the threshold provided as the
       *EHHS_thr* argument to :meth:`!set_core`, and EHHG
       starts to be smaller than the threshold provided as the
       *EHHG_thr* argument to :meth:`!set_core`. EHH decay is computed
       separately for each core haplotype. See the methods
       :meth:`.get_dEHH`, :meth:`.get_dEHHS`, and :meth:`.get_dEHHG`. The values are not
       available until the respective threshold is reached (``None`` is
       returned). The method  :meth:`.done_EHH` allows to check whether
       the threshold for the EHH decay has been reached for all core
       haplotypes. The maximum and average value of the EHH decay across
       all core haplotypes can be accessed with :meth:`.get_dEHH_max`
       and :meth:`.get_dEHH_mean`, respectively.

       .. admonition:: Reference

           Ram\u00EDrez-Soriano A., S.E. Ramos-Onsins, J. Rozas,
           F. Calafell & A. Navarro. 2008. Statistical power analysis of
           neutrality tests under demographic expansions, contractions and
           bottlenecks with recombination. *Genetics* **179** \:
           555-567.

    In all cases,
    ``None`` is returned when the value is not available (no data
    loaded, division by zero in the case of ratios, or threshold not
    reached in the case of decay statistics).

    The thresholds must all be within the range between 0 and 1.
    """

    def __init__(self):
        self._obj = _eggwrapper.EHH()
        self._struct = _eggwrapper.StructureHolder()
        self._valid = False
        self._distance = 0.0
        self._K_core = None
        self._K_tot = None
        self._K_cur = None
        self._R = None

    def set_core(self, site, struct=None, min_freq=None, min_sam=2,
                    EHH_thr=None, EHHc_thr=None, EHHS_thr=None, EHHG_thr=None, crop_EHHS=False):
        """
        Specify the core site. If the
        instance already contains data, it will be reset.

        :param site: a :class:`.Site` instance. The site must have
            a specified :py:obj:`~.Site.position`. It is
            assumed that data are phased (samples should be phased; but
            it is possible to load genotypes whose phase is unknown, as
            long as the genotypes are phased at the individual level:
            see *indiv_struct*).

        :param struct: This argument must be set to a non-``None``
            value if genotypic data are provided and if unphased versions
            of statistics should be computed. If  not ``None``, this argument
            should either be a :class:`.Structure` object mapping samples
            to individuals (other structure levels are not considered),
            or an integer specifying the ploidy (in the latter case, samples
            of any individuals are supposed to be consecutive in the
            site. It is still required that individuals are phased (that
            is, that they are entered in the same order in all distant sites).
            The integer 0 is accepted as a synonym of ``None`` (data will be
            treated as haploid).

        :param min_freq: minimal absolute frequency for haplotypes
            (haplotypes with lower frequencies are ignored). By default,
            all haplotypes are considered.

        :param min_sam: minimal absolute number of non-missing samples to
            compute statistics or stop incrementing them (for statistics
            expressed per core haplotype, number of samples for this
            haplotype).

        :param EHH_thr: threshold determining when iHH should stop
            integrating and dEHH must be evaluated. By default (``None``), iHH is
            permanently incremented and dEHH is not evaluated at all.

        :param EHHc_thr: threshold determining when iHH should stop
            integrating and dEHH must be evaluated. By default (if ``None``), use the
            same value as for *EHH_thr*.

        :param EHHS_thr: threshold determining when iES should stop
            integrating and dEHHS must be evaluated. By default (``None``), iES is
            permanently incremented and dEHHS is not evaluated at all.

        :param EHHG_thr: threshold determining when iEG (iES computed for
            unphased data) should stop
            integrating and dEHHG (equivalent to dEHHS)
            must be evaluated. Must be ``None`` if
            *genotypes* is ``True``. By default (``None``), iEG is
            permanently incremented and dEHHG is not evaluated at all.
            By default: equal to EHHS_thr.

        :param crop_EHHS: if True, set values of EHHS that are below the
            threshold to 0 to emulate the behaviour of the R package
            rehh (also affects iES).
        """

        # check validity of instance
        if not isinstance(site, _site.Site): raise TypeError('a Site instance is expected')
        if min_freq is None: min_freq = 1
        elif min_freq < 1: raise ValueError('minimal frequency must be strictly larger than 0')
        if min_sam < 2: raise ValueError('minimal number of non-missing samples must be at least 2')
        if site.position is None: raise ValueError('core site must have a position')

        # load core site and get core statistics
        if EHH_thr is None: EHH_thr = 0.0
        elif EHH_thr < 0.0 or EHH_thr > 1.0: raise ValueError('invalid value for `EHH_thr`')
        if EHHc_thr is None: EHHc_thr = EHH_thr
        elif EHHc_thr < 0.0 or EHHc_thr > 1.0: raise ValueError('invalid value for `EHHc_thr`')
        if EHHS_thr is None: EHHS_thr = 0.0
        elif EHHS_thr < 0.0 or EHHS_thr > 1.0: raise ValueError('invalid value for `EHHS_thr`')
        if EHHG_thr is None: EHHG_thr = EHHS_thr
        elif EHHG_thr < 0.0 or EHHG_thr > 1.0: raise ValueError('invalid value for `EHHG_thr`')

        if struct == 0:
            struct = None
        elif struct is None:
            pass
        elif isinstance(struct, _interface.Structure):
            struct = struct._obj
            if struct.get_req() > site._obj.get_ns(): raise ValueError('structure does not match site')
        elif isinstance(struct, int):
            ns = site.ns
            pl = struct
            if ns % pl != 0: raise ValueError('number of samples is not a multiple of the specified ploidy')
            self._struct.mk_dummy_structure(ns//pl, pl)
            struct = self._struct
        else:
            raise TypeError('invalid type for `struct` argument')
        self._obj.set_core(site._obj, struct, EHH_thr, EHHc_thr, EHHS_thr, EHHG_thr, min_freq, min_sam, crop_EHHS)

        self._K_core = self._obj.K_core()
        if self._K_core == 0: raise ValueError('cannot analyse core site: no valid data')

        # initialize flags
        self._valid = True
        self._ns = site._obj.get_ns()

    def load_distant(self, site):
        """
        Process a distant site. The core site must have been specified.
        The site must have a specified :py:obj:`~.Site.position`.

        :param site: a :class:`.Site` instance containing data
            for the distant site. It must be consistent with the core
            site (same list of samples, and in the same order). Missing
            data are supported.
        """

        # check validity of argument
        if not self._valid: raise ValueError('no core site has been loaded')
        if site._obj.get_ns() != self._ns: raise ValueError('distant site must be consistent with core')
        if site.position is None: raise ValueError('distant site must have a position')

        # pass site
        self._obj.load_distant(site._obj)

    @property
    def num_haplotypes(self):
        """
        Number of core haplotypes. ``None`` if
        core has not been set.
        """
        return self._K_core

    @property
    def cur_haplotypes(self):
        """
        Current number of haplotypes. ``None`` if core has not been set,
        equal to :obj:`.num_haplotypes` if no distant site has been
        loaded.
        """
        return self._obj.K_cur()

    @property
    def nsam(self):
        """ Current number of non-missing samples. """
        if not self._valid: raise ValueError('cannot access statistics (no core site provided)')
        return self._obj.num_avail_tot()

    def nsam_core(self, hap):
        """ Number of samples for a core haplotype.
            Number of non-missing samples for one of the core haplotypes. """
        if not self._valid: raise ValueError('no data processed')
        if hap < 0 or hap >= self._K_core: raise IndexError('invalid haplotype index')
        return self._obj.num_avail_core(hap)

    def nsam_hap(self, hap):
        """ Number of samples for a haplotype.
            Number of non-missing samples for one of the current haplotypes. """
        if not self._valid: raise ValueError('no data processed')
        if hap < 0 or hap >= self._obj.K_cur(): raise IndexError('invalid haplotype index')
        return self._obj.num_avail_cur(hap)

    def get_EHH(self, i):
        """ Get an EHH value.
        Get the EHH value for the last processed distant site for core
        haplotype *i*. Return ``None`` if the value cannot be computed (no
        available samples).
        """
        if not self._valid: raise ValueError('no data processed')
        if i<0 or i>=self._K_core: raise IndexError('invalid haplotype index')
        value = self._obj.EHHi(i)
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def get_EHHc(self, i):
        """ Get an EHHc value.
        Get the EHHc value for the last processed distant site for core
        haplotype *i*. Return ``None`` if the value cannot be computed (no
        available samples).
        """
        if not self._valid: raise ValueError('no data processed')
        if i<0 or i>=self._K_core: raise IndexError('invalid haplotype index')
        value = self._obj.EHHc(i)
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def get_rEHH(self, i):
        """ Get a rEHH value.
        Get the rEHH value for the last processed distant site for core
        haplotype *i*. Return ``None`` if the ratio cannot be computed
        (no available sample or division by zero).
        """
        if not self._valid: raise ValueError('no data processed')
        if i<0 or i>=self._K_core: raise IndexError('invalid haplotype index')
        value = self._obj.rEHH(i)
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def get_iHH(self, i):
        """ Get an iHH value.
        Get the iHH value for the last processed distant site for core
        haplotype *i* . Return ``None`` if the value cannot be computed (no
        available samples).
        """
        if not self._valid: raise ValueError('no data processed')
        if i<0 or i>=self._K_core: raise IndexError('invalid haplotype index')
        value = self._obj.iHH(i)
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def get_iHHc(self, i):
        """ Get an iHHc value.
        Get the iHHc value for the last processed distant site for core
        haplotype *i*. Return ``None`` if the value cannot be computed (no
        available samples).
        """
        if not self._valid: raise ValueError('no data processed')
        if i<0 or i>=self._K_core: raise IndexError('invalid haplotype index')
        value = self._obj.iHHc(i)
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def get_iHS(self, i):
        """ Get an iHS value.
        Get the iHS value for the last processed distant site for core
        haplotype *i*. Return ``None`` if the ratio cannot be computed
        (no available sample or division by zero).
        """
        if not self._valid: raise ValueError('no data processed')
        if i<0 or i>=self._K_core: raise IndexError('invalid haplotype index')
        value = self._obj.iHS(i)
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def done_EHH(self):
        """Completed EHH calculation.
        Return ``True`` if the values of iHH for all core haplotypes
        have finished integrating (and all dEHH values have been
        evaluated).
        """
        if not self._valid: raise ValueError('no data processed')
        return self._obj.num_EHH_done() == self._K_core

    def done_EHHc(self):
        """ Completed EHHc calculation.
        Return ``True`` if the values of iHHc for all core haplotypes
        have finished integrating (and all dEHH values have been
        evaluated).
        """
        if not self._valid: raise ValueError('no data processed')
        return self._obj.num_EHHc_done() == self._K_core

    def get_EHHS(self):
        """ Get EHHS value.
        Get the EHHS value for the last processed distant site. Return ``None`` if
        the value cannot be computed (no available samples).
        """
        if not self._valid: raise ValueError('no data processed')
        value = self._obj.EHHS()
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def get_EHHG(self):
        """ Get EHHG value.
        Get the EHHS (computed with genotypes) value for the last processed distant site. Return ``None`` if
        the value cannot be computed (no available samples, no indiv_struct option used).
        """
        if not self._valid: raise ValueError('no data processed')
        value = self._obj.EHHG()
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def get_iES(self):
        """ Get iES value.
        Get the iES value for the last processed distant site. Return ``None`` if
        the value cannot be computed (no available samples).
        """
        if not self._valid: raise ValueError('no data processed')
        value = self._obj.iES()
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def get_iEG(self):
        """ Get iEG value.
        Get the iES (computed with genotypes) value for the last processed distant site. Return ``None`` if
        the value cannot be computed (no available samples or indiv_struct option was not used).
        """
        if not self._valid: raise ValueError('no data processed')
        value = self._obj.iEG()
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def get_dEHH(self, i):
        """ EHH decay.
        Get the EHH decay distance for core haplotype *i*. Return ``None`` if
        the EHH threshold has not been reached.
        """
        if not self._valid: raise ValueError('no data processed')
        if i<0 or i>=self._K_core: raise IndexError('invalid haplotype index')
        value = self._obj.dEHH(i)
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def get_dEHHc(self, i):
        """ EHHc decay.
        Get the EHHc decay distance for core haplotype *i*. Return ``None`` if
        the EHHc threshold has not been reached.
        """
        if not self._valid: raise ValueError('no data processed')
        if i<0 or i>=self._K_core: raise IndexError('invalid haplotype index')
        value = self._obj.dEHHc(i)
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def get_dEHH_max(self):
        """ Maximum EHH decay.
        Get the maximum EHH decay distance across core haplotypes. Return ``None`` if
        the EHH threshold has not been reached for at least one of the
        core haplotypes.
        """
        if not self._valid: raise ValueError('no data processed')
        value = self._obj.dEHH_max()
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def get_dEHH_mean(self):
        """ Average EHH decay.
        Get the average EHH decay distance across core haplotypes. Return ``None`` if
        the EHH threshold has not been reached for at least one of the
        core haplotypes.
        """
        if not self._valid: raise ValueError('no data processed')
        value = self._obj.dEHH_mean()
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def get_dEHHS(self):
        """ EHHS decay.
        Get the EHHS decay distance. Return ``None`` if the EHHS threshold has not
        been reached.
        """
        if not self._valid: raise ValueError('no data processed')
        value = self._obj.dEHHS()
        if value == _eggwrapper.UNDEF: return None
        else: return value

    def get_dEHHG(self):
        """ EHHG decay.
        Get the EHHS (computed with genotypes) decay distance. Return ``None`` if the EHHG threshold has not
        been reached.
        """
        if not self._valid: raise ValueError('no data processed')
        value = self._obj.dEHHG()
        if value == _eggwrapper.UNDEF: return None
        else: return value
