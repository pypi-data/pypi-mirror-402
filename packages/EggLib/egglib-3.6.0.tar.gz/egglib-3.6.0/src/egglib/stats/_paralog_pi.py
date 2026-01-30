"""
    Copyright 2016-2021 Stéphane De Mita, Mathieu Siol

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

def paralog_pi(align, struct_p, struct_i, max_missing=0.0):
    """
    Compute diversity statistics for a gene family. Based on
    Innan (*Genetics* 2003 **163**:803-810). An
    estimate of genetic diversity is provided for every paralog and for
    every pair of paralogs, provided that enough non-missing data is
    available (at least 2 samples are required). Note that sites with
    more than two alleles are always considered.

    :param align: an :class:`.Align` containing the sequence of all
        available paralog for all samples. The outgroup is ignored.

    :param struct_p: a :class:`.Structure` providing the organisation of
        sequences in paralogs. This structure must have a ploidy of 1 (no
        individual structure). Clusters, if defined, are ignored. The
        sequences of all individuals for a given paralog should be grouped
        together in that structure. There might be a different number of
        sequences per paralog due to missing data.

    :param struct_i: a :class:`.Structure` providing the organisation of
        sequences in individuals. This structure must have a ploidy of 1
        (no individual structure). Clusters, if defined, are ignored. The
        sequences of all paralogs for a given individual should be grouped
        together in that structure. There might be a different number of
        sequences per individual due to missing data.

    :param max_missing: maximum relative proportion of missing data (if there are
        more missing data at a site, the site is ignored altogether).

        .. note::
            Here, *max_missing* is a relative proportion to allow
            using the same value for different alignments that might
            not have the same number of samples (to avoid reevaluating
            *max_missing* if the user wants the same maximum rate
            of missing data). In other functions, *max_missing* is
            the maximum *number* of missing and is an integer.

    :return: A new :class:`.ParalogPi` instance which provides methods
        to access the number of used sites and the diversity for each
        paralog/paralog pair.
    """
    pp = ParalogPi()
    pp.setup(struct_p, struct_i, max_missing)
    pp.process_align(align)
    return pp

class ParalogPi(object):
    """
    Compute diversity statistics for a gene family.
    See :func:`.paralog_pi` for more details. This class
    can be used directly (1) to analyse data with more efficiency (by
    reusing the same instance) or (2) to combine data from different
    alignments, or (3) for pass individual sites. Do first call
    :meth:`.setup`.
    """
    def __init__(self):
        self._obj = _eggwrapper.ParalogPi()
        self._req = 0

    def setup(self, struct_p, struct_i, max_missing=0.0):
        """
        Specify the structure in paralog and individuals. The arguments
        are as as described for :func:`.paralog_pi`.
        Only this method resets the instance.
        """
        if struct_p.ploidy != 1: raise ValueError('ploidy is required to be 1')
        if struct_i.ploidy != 1: raise ValueError('ploidy is required to be 1')
        if max_missing < 0 or max_missing > 1: raise ValueError('max_missing out of bound')
        self._req = struct_p.req_ns
        self._obj.reset(struct_p._obj, struct_i._obj, max_missing)

    def process_align(self, aln):
        """
        Process an alignment. The alignment must match the structure
        passed to :meth:`.setup`.
        Diversity estimates are incremented (no reset).

        :param aln: an :class:`.Align` instance.
        """
        if not isinstance(aln, _interface.Align): raise TypeError('expect an Align instance')
        if aln.ns < 2: return
        if aln.ns > self._req: raise ValueError('unsufficient number of samples in alignment')
        for site in aln.iter_sites():
            self._obj.load(site._obj)

    def process_site(self, site):
        """
        Process a site. The site must match the structure passed to
        :meth:`.setup`. Diversity estimates are incremented (no reset).

        :param site: a :class:`.Site` instance.
        """
        if site.ns < 2: return
        if site.ns > self._req: raise ValueError('unsufficient number of samples in site')
        self._obj.load(site._obj)

    def num_sites(self, *args):
        """
        num_sites([i[, j]])

        Number of sites with data. Number of sites: with any data
        (without arguments), with data for
        paralog *i* (if only *i* specified), with data for the pair
        of paralogs *i* and *j* (if both specified). This counts the number
        of sites which have not been excluded based on the *num_missing* argument,
        and which have at least one pair of samples for the considered sample.
        """
        if len(args) == 0:
            return self._obj.num_sites_tot()
        elif len(args) == 1:
            if args[0] < 0 or args[0] >= self._obj.num_paralogs(): raise IndexError('invalid paralog index')
            return self._obj.num_sites_paralog(args[0])
        elif len(args) == 2:
            if args[0] < 0 or args[0] >= self._obj.num_paralogs(): raise IndexError('invalid paralog index')
            if args[1] < 0 or args[1] >= self._obj.num_paralogs() or args[1] == args[0]: raise IndexError('invalid paralog index')
            return self._obj.num_sites_pair(args[0], args[1])
        else:
            raise ValueError('invalid number of arguments')

    def Piw(self, i):
        """
        Within-paralog diversity for paralog *i*.
        """
        if i<0 or i>=self._obj.num_paralogs(): raise IndexError('invalid paralog index')
        if self._obj.num_sites_paralog(i) < 1: return None
        return self._obj.Piw(i)

    def Pib(self, i, j):
        """
        Between-paralog diversity for paralogs *i* and *j*.
        """
        if i<0 or i>=self._obj.num_paralogs(): raise IndexError('invalid paralog index')
        if j<0 or j>=self._obj.num_paralogs() or j==i: raise IndexError('invalid paralog index')
        if self._obj.num_sites_pair(i, j) < 1: return None
        return self._obj.Pib(i, j)
