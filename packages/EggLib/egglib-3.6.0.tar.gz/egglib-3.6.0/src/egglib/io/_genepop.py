"""
    Copyright 2023 Stéphane De Mita, Mathieu Siol

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

import os, re
from .. import _interface, alphabets

def from_genepop(fname):
    """
    Import Genepop-formatted genotypic data. The format is described
    `here <https://genepop.curtin.edu.au/help_input.html>`_.

    :param fname: Genepop-formatted file name.

    :return: A new :class:`.Align` instance.

    The returned object contains data mapped to an *ad hoc* alphabet,
    with two samples per individuals. Group labels are used to indicate
    the structure (first level: populations, second level: individuals).
    In addition to normal :class:`.Align` instance, the returned object
    has two attributes: :attr:`!title` and :attr:`!loci`, which contain
    the information read from the Genepop file.
    """

    with open(fname) as f:
        # read title
        title = f.readline().strip()
        if len(title) == 0: raise ValueError('title cannot be empty')

        # read locus names
        loci = []
        for line in f:
            if line == '': raise ValueError('unexpected end of line')
            line = line.strip()
            if line in {'POP', 'Pop', 'pop'}: break
            loci.extend(map(str.strip, re.split(', ?', line)))

        # initialise data
        res = _interface.Align(alphabets.genepop)

        # read pops
        pop_idx = 0
        while True:
            for line in f:
                line = line.strip()
                if line in {'POP', 'Pop', 'pop'}:
                    pop_idx += 1
                    break

                # read indiv
                hit = re.match('(.+),(.+)', line)
                if hit is None: raise ValueError('invalid line: {0}'.format(line))
                name, genos = hit.groups()
                name = name.strip()
                genos = list(map(str.strip, genos.split()))
                if len(genos) != len(loci): raise ValueError('inconsistent number of loci')

                # read genotypes and import
                lens = set(map(len, genos))
                if lens == {4}:
                    res.add_sample(name+'_1', [int(geno[:2]) for geno in genos], ['pop{0}'.format(pop_idx+1), name])
                    res.add_sample(name+'_2', [int(geno[2:]) for geno in genos], ['pop{0}'.format(pop_idx+1), name])
                elif lens == {6}:
                    res.add_sample(name+'_1', [int(geno[:3]) for geno in genos], ['pop{0}'.format(pop_idx+1), name])
                    res.add_sample(name+'_2', [int(geno[3:]) for geno in genos], ['pop{0}'.format(pop_idx+1), name])
                else:
                    raise ValueError('invalid number of characters in genotype')
            else:
                break

        # return alignment
        res.title = title
        res.loci = loci
        return res
