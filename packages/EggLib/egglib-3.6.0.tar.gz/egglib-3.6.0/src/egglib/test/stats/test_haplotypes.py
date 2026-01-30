"""
    Copyright 2023-2025 Thomas Coudoux, Stéphane De Mita, Mathieu Siol

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

import egglib, unittest, pathlib, collections
path = pathlib.Path(__file__).parent / '..' / 'data'

ALPH = egglib.alphabets.Alphabet('range', [0, None], [-1, 0], case_insensitive=False)
HAPLOS = [  ([ 0, 0, 0, 1, 1, 1, 2, 1, 1, 1,  0, 0, 1, 1]),
            ([ 0, 1, 1,-1, 0, 0, 0, 0, 0, 0,  2, 1, 0, 1]),
            ([ 0, 0, 1, 2, 2, 1,-1, 2,-1, 2,  3, 0, 0, 1])  ]

def copy(item):
    if isinstance(item, (list, tuple)):
        return list(map(copy, item))
    elif isinstance(item, (int, float, str)):
        return item
    else:
        raise ValueError(type(item))

class Haplotypes_test(unittest.TestCase):
    def test_Haplotypes_T(self):
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        hptp= egglib.stats.haplotypes_from_align(aln)
        self.assertIsInstance(hptp, egglib.Site)
        sites = [egglib.site_from_list(i, ALPH) for i in HAPLOS]
        hptp_2=egglib.stats.haplotypes_from_sites(sites)
        self.assertIsInstance(hptp_2, egglib.Site)

    def test_Haplotypes_E(self):
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        aln2 = egglib.io.from_fasta(str(path / 'At-Ia.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        sites = [egglib.site_from_list(i, ALPH) for i in HAPLOS]
        struct=egglib.struct_from_labels(aln)
        ns = [40, 40, 40, 40]
        sim = egglib.coalesce.Simulator(4, num_indiv=ns, migr=0.01, num_sites=1, mut_model='SMM', theta=2.0)
        ssr2 = sim.simul()
        struct2 = egglib.struct_from_labels(ssr2, lvl_pop=0, lvl_indiv=1)
        with self.assertRaises(TypeError):
            egglib.stats.haplotypes_from_align(sites)
        with self.assertRaises(ValueError):
            egglib.stats.haplotypes_from_align(aln, max_missing=10)
        with self.assertRaises(ValueError):
            egglib.stats.haplotypes_from_sites(sites, impute_threshold=-10)
        with self.assertRaises(ValueError):
            egglib.stats.haplotypes_from_align(aln, struct=struct2)
        with self.assertRaises(ValueError):
            struct2 = egglib.struct_from_labels(ssr2, lvl_pop=0, lvl_indiv=1)
            egglib.stats.haplotypes_from_align(aln, struct=struct2)
        HAPLOS2 = copy(HAPLOS)
        HAPLOS2[1].append(0)
        sites = [egglib.site_from_list(site, ALPH) for site in HAPLOS2]
        with self.assertRaises(ValueError): egglib.stats.haplotypes_from_sites(sites)
        HAPLOS2 = copy(HAPLOS)
        del HAPLOS2[1][:-1]
        sites = [egglib.site_from_list(site, ALPH) for site in HAPLOS2]
        with self.assertRaises(ValueError): egglib.stats.haplotypes_from_sites(sites)

    def test_structure(self):
        aln = egglib.Align.create([
                ('', '00000', ('pop1', 'idv1')),
                ('', '00000', ('pop1', 'idv1')),
                ('', '00010', ('pop1', 'idv2')),
                ('', '01011', ('pop1', 'idv2')),
                ('', '10001', ('pop1', 'idv3')),
                ('', '11011', ('pop1', 'idv3')),
                ('', '11111', ('pop2', 'idv4')),
                ('', '11121', ('pop2', 'idv4')),
                ('', '11021', ('pop2', 'idv5')),
                ('', '11121', ('pop2', 'idv5')),
                ('', '11201', ('otg', 'idv6')),
                ('', '10201', ('otg', 'idv6'))],
            alphabet=egglib.alphabets.Alphabet('char', '012', '.'))
        cs = egglib.stats.ComputeStats(multi_hits=True)
        cs.add_stats('Ki')

        # test with all samples and sites
        self.assertListEqual(egglib.stats.haplotypes_from_align(aln, multiple=True).as_list(), [0, 0, 7, 2, 1, 3, 4, 8, 9, 8, 5, 6])
        self.assertEqual(cs.process_align(aln)['Ki'], 10)

        # include only ingroup samples
        struct1 = collections.OrderedDict()
        struct1[None] = collections.OrderedDict()
        struct1[None]['pop1'] = collections.OrderedDict()
        struct1[None]['pop2'] = collections.OrderedDict()
        struct1[None]['pop1']['sam1'] = (0,)
        struct1[None]['pop1']['sam2'] = (1,)
        struct1[None]['pop1']['sam3'] = (2,)
        struct1[None]['pop1']['sam4'] = (3,)
        struct1[None]['pop1']['sam5'] = (4,)
        struct1[None]['pop1']['sam6'] = (5,)
        struct1[None]['pop2']['sam7'] = (6,)
        struct1[None]['pop2']['sam8'] = (7,)
        struct1[None]['pop2']['sam9'] = (8,)
        struct1[None]['pop2']['sam10'] = (9,)
        struct1 = egglib.struct_from_dict(struct1, None)
        self.assertListEqual(egglib.stats.haplotypes_from_align(aln, multiple=True, struct=struct1).as_list(), [0, 0, 5, 2, 1, 3, 4, 6, 7, 6])
        cs.configure(struct=struct1, multi_hits=True)
        self.assertEqual(cs.process_align(aln)['Ki'], 8)

        # include only ingroup individuals
        struct2 = collections.OrderedDict()
        struct2[None] = collections.OrderedDict()
        struct2[None]['pop1'] = collections.OrderedDict()
        struct2[None]['pop2'] = collections.OrderedDict()
        struct2[None]['pop1']['idv1'] = (0, 1)
        struct2[None]['pop1']['idv2'] = (2, 3)
        struct2[None]['pop1']['idv3'] = (4, 5)
        struct2[None]['pop2']['idv4'] = (6, 7)
        struct2[None]['pop2']['idv5'] = (8, 9)
        struct2 = egglib.struct_from_dict(struct2, None)
        self.assertListEqual(egglib.stats.haplotypes_from_align(aln, multiple=True, struct=struct2).as_list(), [0, 2, 1, 3, 4])
        cs.configure(struct=struct2, multi_hits=True)
        self.assertEqual(cs.process_align(aln)['Ki'], 5)

        # remove sites with multiple alleles
        self.assertListEqual(egglib.stats.haplotypes_from_align(aln, multiple=False).as_list(), [0, 0, 0, 2, 1, 3, 3, 3, 3, 3, 3, 1])
        cs.configure(struct=None, multi_hits=False)
        self.assertEqual(cs.process_align(aln)['Ki'], 4)

        # without outgroup
        self.assertListEqual(egglib.stats.haplotypes_from_align(aln, multiple=False, struct=struct1).as_list(), [0, 0, 0, 2, 1, 3, 4, 4, 3, 4])
        cs.configure(struct=struct1, multi_hits=False)
        self.assertEqual(cs.process_align(aln)['Ki'], 5)
        sites = [egglib.site_from_align(aln, i) for i in range(aln.ls)]
        self.assertListEqual(egglib.stats.haplotypes_from_sites(sites, multiple=False, struct=struct1).as_list(), [0, 0, 0, 2, 1, 3, 4, 4, 3, 4])
        self.assertEqual(cs.process_sites(sites)['Ki'], 5)

        # all missing data
        aln = egglib.Align.create([
                ('', '00000', ('pop1', 'idv1')),
                ('', '0.000', ('pop1', 'idv1')),
                ('', '00010', ('pop1', 'idv2')),
                ('', '01011', ('pop1', 'idv2')),
                ('', '10001', ('pop1', 'idv3')),
                ('', '11011', ('pop1', 'idv3')),
                ('', '11211', ('pop2', 'idv4')),
                ('', '.1121', ('pop2', 'idv4')),
                ('', '1102.', ('pop2', 'idv5')),
                ('', '11121', ('pop2', 'idv5')),
                ('', '11201', ('otg', 'idv6')),
                ('', '10201', ('otg', 'idv6'))],
            alphabet=egglib.alphabets.Alphabet('char', '012', '.'))
        self.assertListEqual(egglib.stats.haplotypes_from_align(aln, multiple=False, struct=struct1).as_list(), [-1] * 10)
        cs.configure(struct=struct1, multi_hits=False)
        self.assertIsNone(cs.process_align(aln)['Ki'])

        alncrap = egglib.Align.create([
                ('', '00000', ('pop1', 'idv1')),
                ('', '0.000', ('pop1', 'idv1')),
                ('', '00010', ('pop1', 'idv2')),
                ('', '01011', ('pop1', 'idv2')),
                ('', '10001', ('pop1', 'idv3')),
                ('', '11011', ('pop1', 'idv3')),
                ('', '11211', ('pop2', 'idv4')),
                ('', '.1121', ('pop2', 'idv4')),
                ('', '1102.', ('pop2', 'idv5')),
                ('', '11121', ('pop2', 'idv5')),
                ('', '11201', ('otg', 'idv6')),
                ('', '22222', ('otg', 'idv6'))],
            alphabet=egglib.alphabets.Alphabet('char', '012', '.'))
        sites = [egglib.site_from_align(alncrap, i) for i in range(alncrap.ls)]
        self.assertListEqual(egglib.stats.haplotypes_from_sites(sites, multiple=False).as_list(), [-1] * alncrap.ns)

        # test with weird structure
        aln = egglib.Align.create([
                ('', '0000000'),
                ('', '0010000'),
                ('', '0000000'),
                ('', '0100111'),
                ('', '011101.'),
                ('', '111111.'),
                ('', '1111121'),
                ('', '1001121'),
                ('', '1011021'),
                ('', '1001131')],
            alphabet=egglib.alphabets.Alphabet('char', '0123', '.'))
        struct3 = collections.OrderedDict()
        struct3[None] = collections.OrderedDict()
        struct3[None][None] = collections.OrderedDict()
        struct3[None][None]['idv1'] = (7,)
        struct3[None][None]['idv2'] = (8,)
        struct3[None][None]['idv3'] = (9,)
        struct3[None][None]['idv4'] = (2,)
        struct3[None][None]['idv5'] = (6,)
        struct3[None][None]['idv6'] = (4,)
        struct3[None][None]['idv7'] = (5,)
        struct3 = egglib.struct_from_dict(struct3, None)

        self.assertListEqual(egglib.stats.haplotypes_from_align(aln, struct=struct3).as_list(), [0, 4, 0, 1, 2, 3, 2])
        cs.configure(struct=struct3)
        self.assertEqual(cs.process_align(aln)['Ki'], 5)
        sites = [egglib.site_from_align(aln, i) for i in range(aln.ls)]
        del sites[-1]
        self.assertListEqual(egglib.stats.haplotypes_from_sites(sites, struct=struct3).as_list(), [0, 4, 0, 1, 2, 3, 2])

    def test_impute(self):
        aln = egglib.Align.create([
                                # skip missing  - with missing - impute
                ('', '0000'),   # 00.0            0000           0000
                ('', '00.0'),   # 00.0            00xx           00?0
                ('', '00.1'),   # 00.3            00xx           00??
                ('', '0100'),   # 02.2            0222           0222
                ('', '0100'),   # 02.2            0222           0222
                ('', '1100'),   # 11.1            1111           1111
                ('', '1100'),   # 11.1            1111           1111
                ('', '1110'),   # 11.1            1133           1133
                ('', '1111')],  # 11.4            1134           1134
            alphabet=egglib.alphabets.Alphabet('char', '01', '.'))

        haps1 = egglib.stats.haplotypes_from_align(aln)
        self.assertEqual(haps1.as_list(), [0, 0, 3, 2, 2, 1, 1, 1, 4])

        haps2 = egglib.stats.haplotypes_from_align(aln, max_missing=0.3)
        self.assertEqual(haps2.as_list(), [0, -1, -1, 2, 2, 1, 1, 3, 4])

        sites = [egglib.site_from_list(site, aln.alphabet) for site in aln.iter_sites()]
        haps3 = egglib.stats.haplotypes_from_sites(sites)
        self.assertEqual(haps3.as_list(), [0, -1, -1, 2, 2, 1, 1, 3, 4])

        haps4 = egglib.stats.haplotypes_from_align(aln, max_missing=0.3, impute_threshold=1)
        self.assertEqual(haps4.as_list(), [0, 0, -1, 2, 2, 1, 1, 3, 4])

        haps5 = egglib.stats.haplotypes_from_sites(sites, impute_threshold=1)
        self.assertEqual(haps5.as_list(), [0, 0, -1, 2, 2, 1, 1, 3, 4])


