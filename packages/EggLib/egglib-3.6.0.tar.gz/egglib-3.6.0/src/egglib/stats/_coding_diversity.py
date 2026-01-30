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
from ..tools import _code_tools
from .. import _site

class CodingDiversity(object):
    r"""
    Detection of synonymous and non-synonymous sites.
    This class processes alignments with a reading frame specification
    in order to detect synonymous and non-synonymous variable positions.
    It provides basic statistics, but it can also filter data to let the
    user compute all other statistics on synonymous-only, or
    non-synonymous-only variation (e.g. :math:`\pi` or ``D``).

    The constructor takes optional arguments. By default, build an empty
    instance. If arguments are passed, they must match the signature of
    :meth:`~.CodingDiversity.process` that will be called.

    Note that codons with missing data are never considered, even if the
    resolution of all possibilities consistent translate to the same
    nucleotide. This applies to stop and start codons. Alternative start
    codons are not considered either.
    """

    def _get_site(self):
        if len(self._site_pool) > 0: return self._site_pool.pop(0)
        else: return _site.Site(alphabets.codons)

    def _defaults(self):
        self._num_tot = 0
        self._num_eff = 0
        self._num_NS = 0.0
        self._num_S = 0.0
        self._num_pol_single = 0
        self._num_multiple_hits = 0
        self._num_multiple_alleles = 0
        self._num_pol_NS = 0
        self._num_pol_S = 0
        self._num_stop = 0

    def __init__(self, *args, **kwargs):
        # internal processing helpers
        self._site_pool = []
        self._sites_S = []
        self._sites_NS = []
        self._alleles_S = []
        self._alleles_NS = []
        self._positions_S = []
        self._positions_NS = []

        # run process
        if len(args) + len(kwargs) > 0: self.process(*args, **kwargs)

        # set internal variables to default values
        else: self._defaults()

    def process(self, align, code=1, 
            struct=None, max_missing=0.0,
            skipstop=True, raise_stop=False,
            multiple_alleles=False, multiple_hits=False):
        """
        Process an alignment. It this instance already had data in
        memory, they will all be erased.

        :param align: an :class:`.Align` instance containing the coding
            sequence to process. The alphabet must be codons.

        :param code: genetic code identifier (see :ref:`here <genetic-codes>`).
            Required to be an integer among the valid values. The
            default value is the standard genetic code.

        :param struct: a class:`Structure` object specifying samples to
            include and outgroup samples to skip for analysis (outgroup
            samples are ignored to determine if site is polymorphic,
            coding, or non-coding, but included in generated sites).
            By default, use all samples.

        :param max_missing: maximum relative proportion of missing data (per
            coding site) to allow (including stop codons if *skipstop* if
            ``true``). By default, all coding sites with any missing data
            are excluded. Outgroup is not considered.

            .. note::
                Here, *max_missing* is a relative proportion to allow
                using the same value for different alignments that might
                not have the same number of samples (to avoid reevaluating
                *max_missing* if the user wants the same maximum rate
                of missing data). In other functions, *max_missing* is
                the maximum *number* of missing and is an integer.

        :param skipstop: if ``True``, stop codons are treated as missing
            data and skipped. If so, potential mutations to stop codons
            are not taken into account when estimating the number of
            non-synonymous sites. Warning (this may be
            counter-intuitive): it actually assumes that stop codons are
            not biologically plausible and considers them as missing
            data. On the other hand, if *skipstop* is ``False``, it
            considers stop codons as if they were valid amino acids.
            This option has no effect if *raise_stop* is ``True``.

        :param raise_stop: raise a :exc:`ValueError` if a
            stop codon is met. If ``True``, *skipstop* has no effect.
            Outgroup is not considered.

        :param multiple_alleles: include coding sites with more than
            two alleles (regardless of whether mutations hit the same
            position within the triplet). If there are more than two
            different codons, they must either encode for the same amino acid
            or all encode for different amino acids (otherwise the site is
            rejected). If more than one of the three codon position are
            mutated, the option *multiple_hits* is considered.

        :param multiple_hits: include coding sites for which more than
           one of the three positions has changed (regardless of the
           number of alleles). If there are more than two alleles, the
           option *multiple_alleles* is also considered.
        """
        if not isinstance(align, _interface.Align): raise TypeError('an Align instance is required')
        if align._alphabet._obj.get_type() != 'codons': raise ValueError('alphabet must be codons')
        if code not in _code_tools._codes: raise ValueError('unknown genetic code: {0}'.format(code))
        code = _code_tools._codes[code]
        if struct is None:
            struct = _eggwrapper.StructureHolder()
            struct.mk_dummy_structure(align.ns, 1)
        else: struct = struct._obj

        # if raise_stop is on: force skipstop to be false to make them appear
        if raise_stop and skipstop: skipstop = False

        # return all CodingSite's to stock
        self._site_pool.extend(self._sites_S)
        self._site_pool.extend(self._sites_NS)
        del self._sites_S[:]
        del self._sites_NS[:]
        del self._alleles_S[:]
        del self._alleles_NS[:]
        del self._positions_S[:]
        del self._positions_NS[:]

        # get the first coding site
        current = self._get_site()

        # initialize variables
        self._num_tot = align.ls
        self._num_eff = 0
        self._num_stop = 0
        self._num_NS = 0.0
        self._num_S = 0.0
        self._num_pol_single = 0
        self._num_multiple_hits = 0
        self._num_multiple_alleles = 0
        self._num_pol_NS = 0
        self._num_pol_S = 0
        ns = struct.get_ni()
        max_missing = int(max_missing * ns)

        # process all coding sites
        for idx in range(self._num_tot):
            # process site (don't care about missing data)
            current._obj.reset()
            current._obj.process_align(align._obj, idx, struct)
                # WE ASSUME HERE THAT INGROUP SAMPLES ARE PACKED AT THE FRONT OF THE SITE

            # count the number of stop codon and missing data
            nstop = 0
            nmiss = 0
            for i in range(ns):
                if current._obj.get_sample(i) < 0: nmiss += 1
                elif code.is_stop_unsmart(current._obj.get_sample(i)):
                    if raise_stop: raise ValueError('stop codon found in sequences')
                    nstop += 1
            if skipstop: nmiss += nstop

            # check stop codon
            if nstop > 0: self._num_stop += 1 # incremented even if skipstop is False

            # skip if too many missing data (but still count stop codon)
            if nmiss > max_missing: continue
            good = True

            # check number of alleles (exclude if no alleles)
            alleles = set()
            for i in range(ns):
                a = current._obj.get_sample(i)
                if a >= 0 and (not skipstop or not code.is_stop_unsmart(a)):
                    alleles.add(a)
            na = len(alleles)
            if na < 1:
                continue

            if na == 2:
                self._num_pol_single += 1 # decremented below if the two alleles differ at more than one position

            if na > 2:
                self._num_multiple_alleles += 1
                good &= multiple_alleles

            # check for multiple hits
            na1, na2, na3 = map(len, map(set, zip(* map(alphabets.codons.get_value, alleles))))
            if (na1 > 1) + (na2 > 1) + (na3 > 1) > 1:
                self._num_multiple_hits += 1
                good &= multiple_hits
                if na == 2: self._num_pol_single -= 1

            # exclude site if too multiple alleles/hits
            if not good: continue

            # process alleles
            if na > 1:
                aas = set(map(code.translate, alleles))
                if len(aas) == 1: SYN = True
                elif len(aas) == na: SYN = False
                elif len(aas) < na: continue # skip because ambiguous syn/non-syn
                else: raise RuntimeError('unexpected error in CodingDiversity')

                if SYN:
                    self._num_pol_S += 1
                    self._sites_S.append(current)
                    self._alleles_S.append(alleles)
                    self._positions_S.append(idx)
                else:
                    self._num_pol_NS += 1
                    self._sites_NS.append(current)
                    self._alleles_NS.append(alleles)
                    self._positions_NS.append(idx)

            # count site as exploitable
            self._num_eff += 1
            num_NS = 0.0
            num_S = 0.0
            c = 0
            for i in range(ns):
                codon = current._obj.get_sample(i)
                if codon >= 0 and (not skipstop or not code.is_stop_unsmart(current._obj.get_sample(i))):
                    num_NS += code.NSsites(codon, skipstop)
                    num_S += code.Ssites(codon, skipstop)
                    c += 1
            if c > 0:
                self._num_NS += num_NS / c
                self._num_S += num_S / c

            if na > 1:
                # generate a new `current` site
                current = self._get_site()

    @property
    def num_codons_tot(self):
        """
        Total number of considered coding sites. Only
        complete codons have been considered, but this value includes
        codons that have been rejected because of missing data.
        """
        return self._num_tot

    @property
    def num_codons_eff(self):
        """
        Number of analysed coding sites. Like
        :attr:`.num_codons_tot` but excluding sites rejected because of
        missing data.
        """
        return self._num_eff

    @property
    def num_codons_stop(self):
        """
        Number of coding sites with at least one codon stop.
        """
        return self._num_stop

    @property
    def num_sites_NS(self):
        """
        Estimated number of non-synonymous sites. Should be interpreted
        as the number of nucleotide sites where a mutation would cause a
        non-synonymous polymorphism. Note that the total number of sites
        per codon is always 3.

        The numbers of non-synonymous and synonymous sites are estimated
        using the method of Nei & Gojobori (*Mol. Biol. Evol.* 1986
        **3**:418-426).
        """
        return self._num_NS

    @property
    def num_sites_S(self):
        """
        Estimated number of synonymous sites. Should be interpreted as
        the number of nucleotide sites where a mutation would cause a
        synonymous polymorphism. Note that the total number of sites per
        codon is always 3.

        The numbers of non-synonymous and synonymous sites are estimated
        using the method of Nei & Gojobori (*Mol. Biol. Evol.* 1986
        **3**:418-426).
        """
        return self._num_S

    @property
    def num_pol_single(self):
        """
        Number of polymorphic coding sites with only one mutation. All these
        sites are always included.
        """
        return self._num_pol_single

    @property
    def num_multiple_alleles(self):
        """
        Number of polymorphic coding sites with more than two alleles. These
        sites are included only if *multiple_alleles* is ``True`` except those
        who mix synonymous and non-synonymous changes (they can be rejected
        if there are more than two alleles in total as well).
        """
        return self._num_multiple_alleles

    @property
    def num_multiple_hits(self):
        """
        Number of polymorphic coding sites for which more than one position is
        changed. These sites are included only if *multiple_hits* is ``True``
        and depdenting on the total number of alleles.
        """
        return self._num_multiple_hits

    @property
    def num_pol_NS(self):
        """
        Number of polymorphic coding sites with only non-synonymous variation.
        """
        return self._num_pol_NS

    @property
    def num_pol_S(self):
        """
        Number of polymorphic coding sites with only synonymous variation.
        """
        return self._num_pol_S

    @property
    def sites_S(self):
        """
        List of coding sites with only synonymous variation.
        """
        return self._sites_S

    @property
    def positions_S(self):
        """
        List of positions of coding sites with only synonymous variation.
        The positions are respective to the predicted protein sequence
        (index of an amino residue, 0 being the first position of the
        provided alignment).
        """
        return [site.position for site in self._sites_S]

    @property
    def sites_NS(self):
        """
        List of coding sites with only non-synonymous variation.
        """
        return self._sites_NS

    @property
    def positions_NS(self):
        """
        List of positions of coding sites with only non-synonymous
        variation. The positions are respective to the predicted protein
        sequence (index of an amino residue, 0 being the first position
        of the provided alignment).
        """
        return [site.position for site in self._sites_NS]
