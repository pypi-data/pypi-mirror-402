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

from .. import eggwrapper as _eggwrapper
from .. import alphabets
from .. import _site
from .. import _freq

class ProbaMisoriented(object):
    r"""
    Error rate of polymorphism orientation using an outgroup.

    :param align: an :class:`.Align` containing the sites to analyse.
    :param struct: a :class:`.Structure` instance.

    Only sites that are either variable
    within the ingroup or have a fixed difference with respect to the
    outgroup are considered. Sites with more than two different alleles
    in the ingroup, or more than one allele in the outgroup, are
    ignored.

    This function is an implementation of the method mentioned in Baudry
    and Depaulis (2003), allowing to estimate the probability that a
    site oriented using the provided outgroup have be misoriented due to
    a homoplasic mutation in the branch leading to the outgroup. Note
    that this estimation neglects the probability of shared
    polymorphism.

    If the instance is created with an alignment as constructor argument,
    then the statistics are computed. The method :meth:`.load_align`
    does the same from an existing :class:`!ProbaMisoriented` instance.
    Otherwise, individual sites can be loaded with :meth:`.load_site`,
    and then the statistics can be computed using :meth:`.compute` (the
    latter is preferable if generate :class:`.Freq` instances for an
    other use).

    .. admonition:: Reference

        Baudry, E. & F. Depaulis. 2003. Effect of misoriented
        sites on neutrality tests with outgroup.
        *Genetics* **165**\ : 1619-1622.

    .. versionadded:: 3.0.0
    """

    def __init__(self, align=None, struct=None):
        self._A = alphabets.DNA.get_code('A')
        self._C = alphabets.DNA.get_code('C')
        self._G = alphabets.DNA.get_code('G')
        self._T = alphabets.DNA.get_code('T')
        self._sd = _eggwrapper.SiteDiversity()
        self._site = _site.Site()
        self._freq = _freq.Freq()
        self.reset()
        if align is not None: self.load_align(align, struct)

    def reset(self):
        """
        Clear all loaded or computed data.
        """
        self._S = 0
        self._D = 0
        self._Ti = 0
        self._Ti_cnt = 0
        self._TiTv = None
        self._pM = None
        self._M = 0
        self._M_cnt = 0

    def load_align(self, align, struct):
        """
        Load all sites of align that meet criteria. If there are previously
        loaded data, they are discarded. This method computes statistics.
        Data are required to be DNA sequences.

        :param align: an :class:`.Align` instance.
        :param struct: a :class:`.Structure` instance.
        """
        if align._alphabet._obj.get_type() != 'DNA': raise ValueError('data must be DNA sequences')
        self.reset()
        for i in range(align._obj.get_nsit_all()):
            self._site.from_align(align, i)
            self._freq.from_site(self._site, struct)
            self.load_site(self._freq)
        self.compute()

    def load_site(self, freq):
        """
        Load a single site. If there are previously loaded data, they
        are retained. To actually compute the misorientation
        probability, the user must call :meth:`.compute`.

        :param freq: a :class:`.Freq` instance.

        .. warning::
            The origin of data must be DNA sequences. This is currently
            not checked here.
        """
        flag = self._sd.process(freq._obj)
        if (flag&2) == 0: return
        if self._sd.Aglob() < 2: return # skip sites that are fixed overall
        if self._sd.Aing() > 2: return # skip sites with 3+ alleles ingroup
        if self._sd.Aout() > 1: return # skip sites with 2+ alleles outgroup
        if self._sd.Aing() == 2:
            self._S += 1
            if freq._obj.frq_outgroup().nseff() > 0:
                self._M_cnt += 1
                if self._sd.Aglob() > self._sd.Aing():
                    self._M += 1
        else:
            self._D += 1
        if self._sd.Aglob() == 2:
            self._Ti_cnt += 1
            if self._sd.global_allele(0) == self._A :
                if self._sd.global_allele(1) == self._G: self._Ti += 1
            elif self._sd.global_allele(0) == self._G:
                if self._sd.global_allele(1) == self._A:  self._Ti += 1
            elif self._sd.global_allele(0) == self._C:
                if self._sd.global_allele(1) == self._T: self._Ti += 1
            elif self._sd.global_allele(0) == self._T:
                if self._sd.global_allele(1) == self._C:  self._Ti += 1

    def compute(self):
        """
        Compute :obj:`.pM` and :obj:`.TiTv` statistics. Requires that
        sites have been loaded using :meth:`.load_site`. This method
        does not reset the instance.
        """
        self._pM = None
        self._TiTv = None
        if self._Ti_cnt > 0 and self._M_cnt > 0:
            Ti = self._Ti / self._Ti_cnt
            a = Ti / 4
            b = (1-Ti) / 8
            if b > 0:
                self._TiTv = a/b
                self._pM = ((self._M/self._M_cnt) * a**2 + 2*b**2) / (2*b*(2*a+b))

    @property
    def S(self):
        """ Number of loaded polymorphic sites. Only the ingroup is
            considered to classify a site as polymorphic. """
        return self._S

    @property
    def D(self):
        """
        Number of loaded sites with a fixed difference to the outgroup.
        """
        return self._D

    @property
    def TiTv(self):
        """
        Transition and transversion rate ratio. ``None`` if
        the value cannot be computed (no loaded data or null
        transversion rate). Requires that :meth:`.compute` has been
        called.
        """
        return self._TiTv

    @property
    def pM(self):
        """
        Probability of misorientation. ``None`` if the value cannot be
        computed (no loaded data, no valid polymorphism, null
        transversion rate). Requires that :meth:`.compute` has been
        called.
        """
        return self._pM
