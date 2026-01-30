"""
    Copyright 2025 Mathieu Siol, Stéphane De Mita

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

from .. import _freq
from .. import _site

def SFS(sites, struct=None, max_missing=0.0, mode='auto', nbins=None, skip_fixed=False):
    """
    Compute the site frequency spectrum. This function processes an
    list of sites (or any iterator yielding :class:`.Site` instances)
    and computes the distribution of frequencies of either the minority
    or the derived allele of diallelic sites.

    :param sites: an iterator over :class:`.Site` instances. Unless
        *nbins* is specified, all sites are required to have the same
        number of samples.
    :param struct: a :class:`.Structure` instance defining the samples
        to process and/or the outgroup samples (necessary for the 
        unfolded spectrum).
    :param max_missing: maximum relative proportion of missing data in 
        the ingroup to process a site. Warning: when using this option
        without binarization (absolute frequencies), the results might
        be unreliable as sites with missing data have less samples.
    :param mode: indicate whether the SFS should be folded or unfolded
        (possible only when outgroup is present in struct). ``auto``: as
        implied by the outgroup; ``folded``: folded (even if there is an
        outgroup); ``unfolded``: unfolded (causing an error if no
        outgroup is present).
    :params nbins: number of bins on which to calculate the SFS. If
        ``None``, the full SFS is returned as a list.
    :params skip_fixed: boolean indicating whether fixed sites should be
        counted of not. If set to ``True`` with a full, folded SFS
        (``nbins=None`` with no outgroup used), the first and last count
        values are set to ``None`` but kept in the returned list.
    :return: If bins are specified: a list of ``(bound, count)`` tuples
        where *bound* is the top limit of each bin, which is inclusive,
        and *count* is the number of sites falling in this category.
        Otherwise (``nbins=None``): a list containing the absolute SFS,
        giving the number of sites corresponding to all possible
        frequencies ranging from 0 to ``n/2+1`` (if folded) or ``n-1``
        (unfolded), inclusive.

    .. versionadded:: 3.4
    """

    if max_missing < 0 or max_missing > 1: raise ValueError('max_missing out of bound')
    max_missing += 1e-12 # guard against rounding errors

    # create an internal variable to determine if folded or not (once and for all)
    if mode == "auto":
        if struct is None:
            folded = True
        else:
            if struct.num_indiv_outgroup != 0:
                folded = False
            else:
                folded = True
    elif mode == 'folded':
        folded = True
    elif mode == 'unfolded':
        if struct is None or struct.num_indiv_outgroup == 0:
            raise ValueError('cannot process unfolded SFS with no outgroup information')
        folded = False
    else: raise ValueError('invalid value for option mode')

    _ns = None
    freq = _freq.Freq()

    # absolute SFS
    if nbins is None:
        for site in sites:
            if not isinstance(site, _site.Site):
                raise TypeError('expect a Site instance')

            if _ns is None:
                _ns = site.ns
                nseff = _ns if struct is None else struct.ns
                if folded == False:
                    counts = [0] * (nseff+1)
                elif folded == True:
                    counts = [0] * (nseff//2+1)
            else:
                if site.ns != _ns:
                    raise ValueError('inconsistent number of samples between sites')        

            freq.from_site(site, struct)

            if freq.num_alleles > 2: continue
            if freq.nseff() == 0: continue
            if 1-freq.nseff()/nseff > max_missing: continue
            if freq.num_alleles == 1:
                if not skip_fixed: counts[0] += 1
            elif folded:
                p = min(freq.freq_allele(0, cpt = _freq.Freq.ingroup), freq.freq_allele(1, cpt = _freq.Freq.ingroup))
                if not skip_fixed or p > 0:
                    counts[p] += 1
            else:
                # get derived allele if outgroup present
                l = (freq.freq_allele(0, cpt = _freq.Freq.outgroup), freq.freq_allele(1, cpt = _freq.Freq.outgroup))
                if 0 not in l: # polymorphic in outgroup (cannot orientate site)
                    continue
                derived = 1 - l.index(max(l))
                p = freq.freq_allele(derived, cpt = _freq.Freq.ingroup)
                if not skip_fixed or (p > 0 and p < nseff):
                    counts[p] += 1

        if skip_fixed:
            if counts[0] != 0:
                raise RuntimeError('zero-frequency category unexceptedly non-empty')
            counts[0] = None
            if not folded:
                if counts[-1] != 0:
                    raise RuntimeError('last frequency category unexceptedly non-empty')
                counts[-1] = None

        return counts

    # binarized SFS
    else:
        if nbins < 2: raise ValueError('invalid number of bins')
        if folded:
            step = 0.5/nbins
        else:
            step = 1/nbins
        bounds = [i*step for i in range(1, nbins+1)]
        counts = [0 for i in range(len(bounds))]
        
        for site in sites:
            if not isinstance(site, _site.Site):
                raise TypeError('expect a Site instance')

            nseff = site.ns if struct is None else struct.ns
            freq.from_site(site, struct)
            if freq.nseff() == 0: continue
            if freq.num_alleles > 2: continue
            if skip_fixed and freq._obj.frq_ingroup().num_alleles_eff() == 1: continue
            if 1-freq.nseff()/nseff > max_missing: continue

            if folded:
                if freq.num_alleles == 1:
                    counts[0] += 1
                else:
                    minor = min(freq.freq_allele(0, cpt = _freq.Freq.ingroup), freq.freq_allele(1, cpt = _freq.Freq.ingroup))/freq.nseff()
                    if minor > 1e-12 or not skip_fixed:
                        c = 0
                        while True:
                            if minor > bounds[c]:
                                c += 1
                            else:
                                break
                        counts[c] += 1
            else:
                if freq.num_alleles == 1:
                    counts[0] += 1
                else:
                    lst = (freq.freq_allele(0, cpt = _freq.Freq.outgroup), freq.freq_allele(1, cpt = _freq.Freq.outgroup))
                    if 0 not in lst: # polymorphic in outgroup (cannot orientate site)
                        continue
                    derived = 1 - lst.index(max(lst))
                    rel = freq.freq_allele(derived, cpt = _freq.Freq.ingroup)/freq.nseff()
                    if not skip_fixed or not (rel < 1e-12 or rel > (1-1e-12)):
                        c = 0
                        while True:
                            if rel > bounds[c]:
                                c += 1
                            else:
                                break
                        counts[c] += 1

        return list(zip(bounds, counts))
