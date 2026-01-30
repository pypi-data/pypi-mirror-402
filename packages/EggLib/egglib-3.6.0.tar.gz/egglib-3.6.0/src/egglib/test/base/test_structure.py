"""
    Copyright 2025-2026 Thomas Coudoux, Stéphane De Mita, Mathieu Siol

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

import os, egglib, sys, unittest, tempfile
from collections.abc import Iterable

class Structure_test(unittest.TestCase):
    def test_get_samples(self):
        d = {
            '1000': { # cluster
                '1100': {    # pop
                    '1110': (0, 1),  # indiv
                    '1120': (2, 3),
                    '1130': (4, 6),
                    '1140': (8, 10)
                },
                '1200': {
                    '1210': (15, 16),
                    '1230': (17, 18),
                    '1240': (19, 20)
                }
            },
            '2000': {
                '2100': {
                    '2110': (21, 22),
                    '2120': (23, 24),
                    '2130': (25, 27),
                    '2140': (26, 28)
                },
                    '2200': {
                    '2210': (29, 30),
                    '2220': (31, 32),
                    '2230': (33, 34)
                }
            }
        }
        do = {
            '910': (55, 56),
            '920': (57, 12)
        }

        s = egglib.struct_from_dict(d, do)
        self.assertSetEqual(s.get_samples(),
            set([0,1,2,3,4,6,8,10,15,16,17,18,19,20,21,22,23,24,25,27,26,28,29,30,31,32,33,34]))

    def test_subsetting(self):
        coal = egglib.coalesce.Simulator(4, num_chrom=[5, 2, 5, 4], theta=5.0, migr=0.2)
        cs = egglib.stats.ComputeStats()
        cs.add_stats('nseff', 'S', 'thetaW', 'Pi', 'D', 'FstWC')
        for aln in coal.iter_simul(200):
            sub = aln.subset([5, 6, 12, 13, 14, 15])
            cs.configure(struct=egglib.struct_from_labels(sub, lvl_pop=0))
            ctrl = cs.process_align(sub)
            struct = egglib.struct_from_labels(aln, lvl_pop=0)
            struct = struct.as_dict()[0]
            del struct[None]['0']
            del struct[None]['2']
            struct = egglib.struct_from_dict(struct, None)
            cs.configure(struct=struct)
            test = cs.process_align(aln)
            self.assertDictEqual(ctrl, test)
            if ctrl['S'] > 0:
                self.assertEqual(ctrl['nseff'], 6)

    def test_subset(self):
        struct = egglib.struct_from_dict(
            {'clu1': {
                'pop1': {
                    'idv1': (0, 1), 'idv2': (2, 3), 'idv3': (4, 5), 'idv4': (6, 7)},
                'pop2': {
                    'idv5': (8, 9), 'idv6': (10, 11), 'idv7': (12, 13), 'idv8': (14, 15)},
                'pop3': {
                    'idv9': (16, 17), 'idv10': (18, 19), 'idv11': (20, 21), 'idv12': (22, 23)}
                },
            'clu2': {
                'pop4': {
                    'idv13': (24, 25), 'idv14': (26, 27), 'idv15': (28, 29), 'idv6': (30, 31)},
                'pop5': {
                    'idv17': (32, 33), 'idv18': (34, 35), 'idv19': (36, 37), 'idv20': (38, 39)},
                'pop6': {
                    'idv21': (40, 41), 'idv22': (42, 43), 'idv23': (44, 45), 'idv24': (46, 47)},
                'pop7': {
                    'idv25': (48, 49), 'idv26': (50, 51), 'idv27': (52, 53), 'idv28': (54, 55)}
                }}, 
                    {'otg1': (56, 57), 'otg2': (58, 59), 'otg3': (60, 61), 'otg4': (62, 63)}
        )

        site = [0, 0, 0, 0, 0, 0, 0, 0, # pop1
                1, 1, 1, 1, 2, 2, 2, 2, # pop2
                3, 3, 3, 3, 3, 3, 3, 3, # pop3
                3, 3, 3, 3, 3, 3, 3, 3, # pop4
                4, 4, 4, 5, 5, 5, 6, 6, # pop5
                7, 7, 7, 7, 7, 7, 7, 7, # pop6
                7, 7, 7, 7, 8, 8, 8, 8, # pop7
                8, 8, 8, 8, 9, 9, 9, 9] # otg

        site = egglib.site_from_list(site, alphabet=egglib.alphabets.positive_infinite)

        cs = egglib.stats.ComputeStats(struct=struct)
        cs.add_stats('Aing', 'ns_site', 'Atot', 'Aotg')
        stats = cs.process_site(site)
        self.assertEqual(stats['Aing'], 9)
        self.assertEqual(stats['Aotg'], 2)
        self.assertEqual(stats['Atot'], 10)

        cs.configure(struct=None)
        self.assertEqual(cs.process_site(site)['Aing'], 10)

        self.assertRaisesRegex(ValueError, 'there must be at least one population', struct.subset)
        self.assertRaisesRegex(ValueError, 'invalid population label: prout', struct.subset, ['prout'])

        cs.configure(struct=struct.subset(['pop1', 'pop5']))
        stats = cs.process_site(site)
        self.assertEqual(stats['Aing'], 4)
        self.assertEqual(stats['Aotg'], 2)
        self.assertEqual(stats['Atot'], 6)

        cs.configure(struct=struct.subset(['pop5'], outgroup=False))
        stats = cs.process_site(site)
        self.assertEqual(stats['Aing'], 3)
        self.assertIsNone(stats['Aotg'])
        self.assertEqual(stats['Atot'], 3)

        cs.configure(struct=struct.subset(['pop1', 'pop6', 'pop6', 'pop7'], outgroup=True))
        stats = cs.process_site(site)
        self.assertEqual(stats['Aing'], 3)
        self.assertEqual(stats['Aotg'], 2)
        self.assertEqual(stats['Atot'], 4)

        cs.configure(struct=struct.subset(pops=['pop5'], clusters=['clu1'], outgroup=True))
        stats = cs.process_site(site)
        self.assertEqual(stats['Aing'], 7)
        self.assertEqual(stats['Aotg'], 2)
        self.assertEqual(stats['Atot'], 9)

    def test_shuffle(self):
        struct = {}
        struct['c1'] = {}
        struct['c1']['p1'] = {}
        struct['c1']['p1']['i1'] = (0, 1)
        struct['c1']['p1']['i2'] = (2, 3)
        struct['c1']['p1']['i3'] = (4, 5)
        struct['c1']['p2'] = {}
        struct['c1']['p2']['i4'] = (6, 7)
        struct['c1']['p2']['i5'] = (8, 9)
        struct['c1']['p2']['i6'] = (10, 11)
        struct['c1']['p2']['i7'] = (12, 13)
        struct['c1']['p3'] = {}
        struct['c1']['p3']['i8'] = (14, 15)
        struct['c1']['p3']['i9'] = (16, 17)
        struct['c1']['p3']['i10'] = (18, 19)
        struct['c2'] = {}
        struct['c2']['p4'] = {}
        struct['c2']['p4']['i11'] = (20, 21)
        struct['c2']['p4']['i12'] = (22, 23)
        struct['c2']['p4']['i13'] = (24, 25)
        struct['c2']['p4']['i14'] = (26, 27)
        struct['c2']['p5'] = {}
        struct['c2']['p5']['i15'] = (28, 29)
        struct['c2']['p5']['i16'] = (30, 31)
        struct['c2']['p5']['i17'] = (32, 33)
        struct['c2']['p5']['i18'] = (34, 35)
        struct = egglib.struct_from_dict(struct, {'i19': (36, 37)})

        def f(x): return int(x[1:])
        def show(s):
            ret = [[],[]]
            ing, otg = struct.as_dict()
            for c in sorted(ing, key=f):
                for p in sorted(ing[c], key=f):
                    for i in sorted(ing[c][p], key=f):
                        ret[0].extend(ing[c][p][i])
            for i in sorted(otg, key=f):
                ret[1].extend(otg[i])
            return ret

        # original structure fingerprint
        original = show(struct)

        # default mode (single shuffling)
        for i in 'it', 'ic', 'is', 'st', 'sc', 'ct':
            n = 0
            for rep in range(20):
                with struct.shuffle(i):
                    ret = show(struct)
                    if ret[0] != original[0]: n += 1
                    self.assertListEqual(ret[1], original[1])
            self.assertGreater(n, 5)
            ret = show(struct)
            self.assertListEqual(ret[0], original[0])
            self.assertListEqual(ret[1], original[1])

        # show that iteration not possible in default mode
        n = 0
        for i in range(10):
            with struct.shuffle() as shuffler:
                ret = show(struct)
                if ret[0] != original[0]: n += 1
                assert ret[1] == original[1]
                with self.assertRaises(TypeError) as cm:
                    for i in shuffler: pass # should not be iterable
                self.assertIn('is not iterable', str(cm.exception))
        self.assertGreater(n, 5) # check at least 5 times different
        ret = show(struct)
        self.assertListEqual(ret[0], original[0])
        self.assertListEqual(ret[1], original[1])

        # test iteration
        with struct.shuffle(nr=100) as shuffler:
            c = 0
            n = 0
            for i in shuffler:
                self.assertEqual(i, c)
                ret = show(struct)
                if ret[0] != original[0]: n += 1
                self.assertListEqual(ret[1], original[1])
                c += 1
            self.assertEqual(c, 100)
            self.assertGreater(n, 5) # check at least 5 times different
        ret = show(struct)
        self.assertListEqual(ret[0], original[0])
        self.assertListEqual(ret[1], original[1])

    def test_labels(self):

        # check that empty labels are forbidden
        fas = """\
>sam1@pop1
AAAAAAAAAA
>sam2@pop1
AAAAAAAAAA
>sam3@pop1,pop2,pop3
AAAAAAAAAA
>sam4
AAAAAAAAAA
>sam5@pop1,
AAAAAAAAAA
>sam6@pop1
AAAAAAAAAA
>sam7@pop1,,pop3
AAAAAAAAAA
>sam8@pop1
AAAAAAAAAA
"""

        with self.assertRaises(IOError):
            aln = egglib.io.from_fasta_string(fas, alphabet=egglib.alphabets.DNA, labels=True)

        # repair the fasta
        fas = fas.replace(',\n', '\n')
        fas = fas.replace(',,', ',pop2,')

        # import repaired fasta
        aln = egglib.io.from_fasta_string(fas, alphabet=egglib.alphabets.DNA, labels=True)
        check = [ ('sam1', ['pop1']),
                  ('sam2', ['pop1']),
                  ('sam3', ['pop1','pop2','pop3']),
                  ('sam4', []),
                  ('sam5', ['pop1']),
                  ('sam6', ['pop1']),
                  ('sam7', ['pop1','pop2','pop3']),
                  ('sam8', ['pop1'])]
        self.assertListEqual([(seq.name, list(seq.labels)) for seq in aln], check)

        # attempt to set 0-length label
        with self.assertRaises(ValueError):
            aln[0].labels.append('')

        with self.assertRaises(ValueError):
            aln[0].labels[0] = ''

        # test None (automatic if level not specified / allowed in structure input only if only one item)
        d = {None: {None: {'i1': [0, 1], 'i2': [2, 3], 'i3': [6, 7], 'i4': [8, 9]}}}, {'i1': [10, 11]}
        struct = egglib.struct_from_dict(*d)
        dx = struct.as_dict()
        self.assertDictEqual(dx[0], d[0])
        self.assertDictEqual(dx[1], d[1])

        d = {'c1': {}, 'c2': {None: {'i1': [0, 1], 'i2': [2, 3], 'i3': [6, 7], 'i4': [8, 9]}}}, {'i1': [10, 11]}
        with self.assertRaises(ValueError):
            struct = egglib.struct_from_dict(*d)

        d = ({'c1': {None: {'i1': [0, 1], 'i2': [2, 3]}}}, {'i1': [4,5]})
        with self.assertRaises(ValueError):
            struct = egglib.struct_from_dict(*d)

        # check that non-represented levels are automatically set to a single None item
        aln = egglib.io.from_fasta_string("""\
>sam1@pop1
AAAAAAAAAA
>sam2@pop1
AAAAAAAAAA
>sam3@pop2
AAAAAAAAAA
>sam4@pop2
AAAAAAAAAA
>sam5@#
AAAAAAAAAA
>sam6@#
AAAAAAAAAA
""", alphabet=egglib.alphabets.DNA, labels=True)

        dx = egglib.struct_from_labels(aln, lvl_pop=0).as_dict()
        self.assertDictEqual(dx[0], {None: {'pop1': {'0': [0], '1': [1]}, 'pop2': {'2': [2], '3': [3]}}})
        self.assertDictEqual(dx[1], {'4': [4], '5': [5]})

        aln = egglib.io.from_fasta_string("""\
>sam1@i1
AAAAAAAAAA
>sam2@i1
AAAAAAAAAA
>sam3@i2
AAAAAAAAAA
>sam4@i2
AAAAAAAAAA
>sam5@#,i1
AAAAAAAAAA
>sam6@#,i1
AAAAAAAAAA
""", alphabet=egglib.alphabets.DNA, labels=True)

        dx = egglib.struct_from_labels(aln, lvl_indiv=0).as_dict()
        self.assertDictEqual(dx[0], {None: {None: {'i1': [0, 1], 'i2': [2, 3]}}})
        self.assertDictEqual(dx[1], {'i1': [4,5]})

        aln = egglib.io.from_fasta_string("""\
>sam1@c1,i1
AAAAAAAAAA
>sam2@c1,i1
AAAAAAAAAA
>sam3@c1,i2
AAAAAAAAAA
>sam4@c1,i2
AAAAAAAAAA
>sam5@#,i1
AAAAAAAAAA
>sam6@#,i1
AAAAAAAAAA
""", alphabet=egglib.alphabets.DNA, labels=True)

        dx = egglib.struct_from_labels(aln, lvl_clust=0, lvl_indiv=1).as_dict()
        self.assertDictEqual(dx[0], {'c1': {'c1': {'i1': [0, 1], 'i2': [2, 3]}}})
        self.assertDictEqual(dx[1], {'i1': [4,5]})

        # check outgroup sample
        dx = egglib.struct_from_labels(aln, lvl_clust=0, lvl_indiv=1, skip_outgroup=True).as_dict()
        self.assertDictEqual(dx[0], {'c1': {'c1': {'i1': [0, 1], 'i2': [2, 3]}}})
        self.assertDictEqual(dx[1], {})

        # support missing samples
        aln = egglib.io.from_fasta_string("""\
>sam1@idv1,pop1
AAAAAAAAAA
>sam2@idv2,pop1
AAAAAAAAAA
>sam3@idv3,pop1
AAAAAAAAAA
>sam4
AAAAAAAAAA
>sam5@idv4
AAAAAAAAAA
>sam6@idv5,pop2
AAAAAAAAAA
>sam7@idv6,pop2
AAAAAAAAAA
>sam8@#
AAAAAAAAAA
""", alphabet=egglib.alphabets.DNA, labels=True)

        dx = egglib.struct_from_labels(aln, lvl_indiv=0, lvl_pop=1).as_dict()
        self.assertDictEqual(dx[0], {None: {'pop1': {'idv1': [0], 'idv2': [1], 'idv3': [2]}, 'pop2': {'idv5': [5], 'idv6': [6]}}})
        self.assertDictEqual(dx[1], {})

        aln = egglib.io.from_fasta_string("""\
>sam1@idv1,pop1
AAAAAAAAAA
>sam2@idv2,pop1
AAAAAAAAAA
>sam3@idv3,pop1
AAAAAAAAAA
>sam4
AAAAAAAAAA
>sam5@idv4
AAAAAAAAAA
>sam6@idv5,pop2
AAAAAAAAAA
>sam7@idv6,pop2
AAAAAAAAAA
>sam8@#,idv1
AAAAAAAAAA
""", alphabet=egglib.alphabets.DNA, labels=True)

        dx = egglib.struct_from_labels(aln, lvl_indiv=0, lvl_pop=1).as_dict()
        self.assertDictEqual(dx[0], {None: {'pop1': {'idv1': [0], 'idv2': [1], 'idv3': [2]}, 'pop2': {'idv5': [5], 'idv6': [6]}}})
        self.assertDictEqual(dx[1], {'idv1': [7]})

    def test_outgroup_label(self):

        # structure with 2 pops + 1 `outgroup` single-indiv pop
        coal = egglib.coalesce.Simulator(3, num_indiv=[5, 5, 1], migr_matrix=[[None, 1, 0], [1, None, 0], [0, 0, None]])
        coal.params.add_event('merge', T=3, src=2, dst=0)
        coal.params.add_event('merge', T=3, src=1, dst=0)

        # perform a simulation
        aln = coal.simul()

        # shows the labels
        self.assertListEqual(list(aln[0].labels), ['0', '0'])
        self.assertListEqual(list(aln[1].labels), ['0', '0'])
        self.assertListEqual(list(aln[2].labels), ['0', '1'])
        self.assertListEqual(list(aln[3].labels), ['0', '1'])
        self.assertListEqual(list(aln[4].labels), ['0', '2'])
        self.assertListEqual(list(aln[5].labels), ['0', '2'])
        self.assertListEqual(list(aln[6].labels), ['0', '3'])
        self.assertListEqual(list(aln[7].labels), ['0', '3'])
        self.assertListEqual(list(aln[8].labels), ['0', '4'])
        self.assertListEqual(list(aln[9].labels), ['0', '4'])
        self.assertListEqual(list(aln[10].labels), ['1', '5'])
        self.assertListEqual(list(aln[11].labels), ['1', '5'])
        self.assertListEqual(list(aln[12].labels), ['1', '6'])
        self.assertListEqual(list(aln[13].labels), ['1', '6'])
        self.assertListEqual(list(aln[14].labels), ['1', '7'])
        self.assertListEqual(list(aln[15].labels), ['1', '7'])
        self.assertListEqual(list(aln[16].labels), ['1', '8'])
        self.assertListEqual(list(aln[17].labels), ['1', '8'])
        self.assertListEqual(list(aln[18].labels), ['1', '9'])
        self.assertListEqual(list(aln[19].labels), ['1', '9'])
        self.assertListEqual(list(aln[20].labels), ['2', '10'])
        self.assertListEqual(list(aln[21].labels), ['2', '10'])

        # make structure with three populations ignoring individual level
        ing, otg = egglib.struct_from_labels(aln, lvl_pop=0).as_dict()
        self.assertDictEqual(ing, {None: {
            '0': {    '0': [0],  '1': [1],   '2': [2],   '3': [3],   '4': [4],   '5': [5],   '6': [6],   '7': [7],   '8': [8],   '9': [9]},
            '1': {  '10': [10], '11': [11], '12': [12], '13': [13], '14': [14], '15': [15], '16': [16], '17': [17], '18': [18], '19': [19]},
            '2': {  '20': [20], '21': [21]}}})
        self.assertDictEqual(otg, {})

        # make structure with three populations
        ing, otg = egglib.struct_from_labels(aln, lvl_pop=0, lvl_indiv=1).as_dict()
        self.assertDictEqual(ing, {None: {
            '0': {  '0': [ 0, 1], '1': [ 2, 3], '2': [ 4, 5], '3': [ 6, 7], '4': [ 8, 9]},
            '1': {  '5': [10,11], '6': [12,13], '7': [14,15], '8': [16,17], '9': [18,19]},
            '2': { '10': [20,21]}}})
        self.assertDictEqual(otg, {})

        # two populations + outgroup ignoring individual level
        ing, otg = egglib.struct_from_labels(aln, lvl_pop=0, outgroup_label='2').as_dict()
        self.assertDictEqual(ing, {None: {
            '0': {    '0': [0],  '1': [1],   '2': [2],   '3': [3],   '4': [4],   '5': [5],   '6': [6],   '7': [7],   '8': [8],   '9': [9]},
            '1': {  '10': [10], '11': [11], '12': [12], '13': [13], '14': [14], '15': [15], '16': [16], '17': [17], '18': [18], '19': [19]}}})
        self.assertDictEqual(otg, {'20': [20], '21': [21]})

        # two populations + outgroup
        ing, otg = egglib.struct_from_labels(aln, lvl_pop=0, lvl_indiv=1, outgroup_label='2').as_dict()
        self.assertDictEqual(ing, {None: {
            '0': {  '0': [ 0, 1], '1': [ 2, 3], '2': [ 4, 5], '3': [ 6, 7], '4': [ 8, 9]},
            '1': {  '5': [10,11], '6': [12,13], '7': [14,15], '8': [16,17], '9': [18,19]}}})
        self.assertDictEqual(otg, {'10': [20,21]})

    def test_from_samplesizes(self):
        struct = egglib.struct_from_samplesizes([5, 5], ploidy=2, outgroup=1)
        ref = ({None:
                {'pop1': {'idv1': [0, 1], 'idv2': [2, 3], 'idv3': [4, 5],
                          'idv4': [6, 7], 'idv5': [8, 9]},
                 'pop2': {'idv6': [10, 11], 'idv7': [12, 13],
                          'idv8': [14, 15], 'idv9': [16, 17],
                          'idv10': [18, 19]}}}, {'idv11': [20, 21]})
        self.assertTupleEqual(struct.as_dict(), ref)

        self.assertTupleEqual(egglib.struct_from_samplesizes([6], ploidy=1, outgroup=0).as_dict(), ({
            None: {'pop1': {'idv1': [0], 'idv2': [1], 'idv3': [2], 'idv4': [3], 
                    'idv5': [4], 'idv6': [5]}}}, {}))

        self.assertTupleEqual(egglib.struct_from_samplesizes([], ploidy=4, outgroup=2).as_dict(), ({
            None: {}}, {'idv1': [0, 1, 2, 3], 'idv2': [4, 5, 6, 7]}))

        self.assertTupleEqual(egglib.struct_from_samplesizes([4, 1, 0, 2], ploidy=3, outgroup=2).as_dict(), (
            {None: {
                'pop1': {'idv1': [0, 1, 2], 'idv2': [3, 4, 5], 'idv3': [6, 7, 8], 'idv4': [9, 10, 11]},
                'pop2': {'idv5': [12, 13, 14]},
                'pop3': {},
                'pop4': {'idv6': [15, 16, 17], 'idv7': [18, 19, 20]}}},
            {'idv8': [21, 22, 23], 'idv9': [24, 25, 26]}))

        self.assertTupleEqual(egglib.struct_from_samplesizes([0], ploidy=1, outgroup=0).as_dict(), ({None: {'pop1': {}}}, {}))

        self.assertTupleEqual(egglib.struct_from_samplesizes([], ploidy=1, outgroup=0).as_dict(), ({None: {}}, {}))

    def test_from_iterable(self):

        ### development test ###
        aln = egglib.Align(alphabet=egglib.alphabets.DNA)
        aln.add_samples([
            ('name1', 'AAAAAA', ['pop1', 'idv1']),
            ('name2', 'AAAAAA', ['pop1', 'idv1']),
            ('name3', 'AAAAAA', ['pop1', 'idv2']),
            ('name4', 'AAAAAA', ['pop1', 'idv2']),
            ('name5', 'AAAAAA', ['pop2', 'idv3']),
            ('name6', 'AAAAAA', ['pop2', 'idv3']),
            ('name7', 'AAAAAA', ['pop2', 'idv4']),
            ('name8', 'AAAAAA', ['pop2', 'idv4']),
            ('nameA', 'AAAAAA', ['#', 'idv5']),
            ('nameB', 'AAAAAA', ['#', 'idv5'])])


        struct1 = egglib.struct_from_labels(aln, lvl_pop=0, lvl_indiv=1)
        assert struct1.as_dict() == (
            {None: {'pop1': {'idv1': [0, 1], 'idv2': [2, 3]},
                    'pop2': {'idv3': [4, 5], 'idv4': [6, 7]}}},
                                                    {'idv5': [8, 9]})

        labels = ['pop1'] * 4 + ['pop2'] * 4 + [None] * 2
        struct2 = egglib.struct_from_iterable(labels)
        assert struct2.as_dict() == (
            {None: {'pop1': {'idv1': [0], 'idv2': [1], 'idv3': [2], 'idv4': [3]},
                    'pop2': {'idv5': [4], 'idv6': [5], 'idv7': [6], 'idv8': [7]}}}, {})


        labels = [['pop1'], ['pop1'], ['pop1'], ['pop1'], ['pop2'], ['pop2'], ['pop2'], ['pop2'], [None], [None]]
        struct3 = egglib.struct_from_iterable(labels, fmt='P')
        assert struct3.as_dict() == (
            {None: {'pop1': {'idv1': [0], 'idv2': [1], 'idv3': [2], 'idv4': [3]},
                    'pop2': {'idv5': [4], 'idv6': [5], 'idv7': [6], 'idv8': [7]}}}, {})

        labels = [['name1', 'pop1'], ['name2', 'pop1'], ['name3', 'pop1'],
                  ['name4', 'pop1'], ['name5', 'pop2'], ['name6', 'pop2'],
                  ['name7', 'pop2'], ['name8', 'pop2'], ['nameA', None], ['nameB', None]]
        struct4 = egglib.struct_from_iterable(labels, fmt='NP', data=aln)
        assert struct4.as_dict() == (
            {None: {'pop1': {'name1': [0], 'name2': [1], 'name3': [2], 'name4': [3]},
                    'pop2': {'name5': [4], 'name6': [5], 'name7': [6], 'name8': [7]}}}, {})

        ### iterable ###
        # pass a list
        labels = ['pop1', 'pop1', 'pop1', 'pop1', 'pop2', 'pop2', 'pop2', 'pop2']
        ctrl = {None: {'pop1': {'idv1': [0], 'idv2': [1], 'idv3': [2], 'idv4': [3]},
                       'pop2': {'idv5': [4], 'idv6': [5], 'idv7': [6], 'idv8': [7]}}}
        struct = egglib.struct_from_iterable(labels)
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        # pass a file/map
        try:
            f, fname = tempfile.mkstemp()
            os.write(f, b'\n'.join(map(str.encode, labels)))
            os.close(f)
            with open(fname) as f:
                struct = egglib.struct_from_iterable(f, function=str.strip)
            ing, otg = struct.as_dict()
            self.assertDictEqual(ing, ctrl)
            self.assertDictEqual(otg, {})
        finally:
            if os.path.isfile(fname): os.unlink(fname)

        # pass an invalid type
        with self.assertRaises(TypeError):
            error = egglib.struct_from_iterable(142)

        with self.assertRaises(TypeError):
            error = egglib.struct_from_iterable('strings not supported')

        # empty string
        labels[3] = ''
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels)

        # pass a list if a string is expected
        labels = [['pop1'], ['pop1'], ['pop1'], ['pop1'], ['pop2'], ['pop2'], ['pop2'], ['pop2']]
        with self.assertRaises(TypeError):
            error = egglib.struct_from_iterable(labels, fmt=None)

        # opposite
        labels = ['pop1', 'pop1', 'pop1', 'pop1', 'pop2', 'pop2', 'pop2', 'pop2']
        with self.assertRaises(TypeError):
            error = egglib.struct_from_iterable(labels, fmt='P')

        ### fmt ###
        # just P
        labels = [['pop1'], ['pop1'], ['pop1'], ['pop1'], ['pop2'], ['pop2'], ['pop2'], ['pop2']]
        ctrl = {None: {'pop1': {'idv1': [0], 'idv2': [1], 'idv3': [2], 'idv4': [3]},
                       'pop2': {'idv5': [4], 'idv6': [5], 'idv7': [6], 'idv8': [7]}}}
        struct = egglib.struct_from_iterable(labels, fmt='P')
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        # just C (error)
        labels = [['clu1'], ['clu1'], ['clu1'], ['clu1'], ['clu2'], ['clu2'], ['clu2'], ['clu2']]
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='C')

        # C and I (error)
        labels = [['clu1', 'idv1'],
                  ['clu1', 'idv1'],
                  ['clu1', 'idv2'],
                  ['clu1', 'idv2'],
                  ['clu2', 'idv3'],
                  ['clu2', 'idv3'],
                  ['clu2', 'idv4'],
                  ['clu2', 'idv4']]
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='CI')

        # C and P
        labels = [['clu1', 'pop1'],
                  ['clu1', 'pop1'],
                  ['clu1', 'pop1'],
                  ['clu1', 'pop1'],
                  ['clu2', 'pop2'],
                  ['clu2', 'pop2'],
                  ['clu2', 'pop3'],
                  ['clu2', 'pop3']]
        ctrl = {'clu1': {'pop1': {'idv1': [0], 'idv2': [1], 'idv3': [2], 'idv4': [3]}},
                'clu2': {'pop2': {'idv5': [4], 'idv6': [5]},
                         'pop3': {'idv7': [6], 'idv8': [7]}}}
        struct = egglib.struct_from_iterable(labels, fmt='CP')
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        # P and I
        labels = [['p1', '1'],
                  ['p1', '1'],
                  ['p1', '2'],
                  ['p1', '2'],
                  ['p2', '3'],
                  ['p2', '3'],
                  ['p2', '4'],
                  ['p2', '4']]
        ctrl = {None: {'p1': {'1': [0, 1], '2': [2, 3]},
                       'p2': {'3': [4, 5], '4': [6, 7]}}}
        struct = egglib.struct_from_iterable(labels, fmt='PI')
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        # I
        labels = [['north'], ['north'], ['north'], ['west'], ['west'], ['west'], ['south'], ['south'], ['south'], ['east'], ['east'], ['east']]
        ctrl = {None: {None: {'north': [0, 1, 2], 'west': [3, 4, 5], 'south': [6, 7, 8], 'east': [9, 10, 11]}}}
        struct = egglib.struct_from_iterable(labels, fmt='I')
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        # CPI
        labels = [['x1', 'clu1', 'pop1'],
                  ['x2', 'clu1', 'pop1'],
                  ['x3', 'clu1', 'pop1'],
                  ['x4', 'clu1', 'pop1'],
                  ['x5', 'clu2', 'pop2'],
                  ['x6', 'clu2', 'pop2'],
                  ['x7', 'clu2', 'pop3'],
                  ['x8', 'clu2', 'pop3']]
        ctrl = {'clu1': {'pop1': {'x1': [0], 'x2': [1], 'x3': [2], 'x4': [3]}},
                'clu2': {'pop2': {'x5': [4], 'x6': [5]},
                         'pop3': {'x7': [6], 'x8': [7]}}}
        struct = egglib.struct_from_iterable(labels, fmt='ICP')
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        # invalid ploidy
        labels = [['x1', 'clu1', 'pop1'],
                  ['x1', 'clu1', 'pop1'],
                  ['x3', 'clu1', 'pop1'],
                  ['x4', 'clu1', 'pop1'],
                  ['x5', 'clu2', 'pop2'],
                  ['x6', 'clu2', 'pop2'],
                  ['x7', 'clu2', 'pop3'],
                  ['x8', 'clu2', 'pop3']]
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='ICP')

        # missing CPI
        labels = [['A'], ['B'], ['C'], ['D']]
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='N')

        labels = [['A'], ['B'], ['C'], ['D']]
        struct = egglib.struct_from_iterable(labels, fmt='I')
        ctrl = {None: {None: {'A': [0], 'B': [1], 'C': [2], 'D': [3]}}}
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        # repeated CPIN
        labels = [['A', 'A', 'A', 'A', 'A']]
        aln = egglib.Align(alphabet=egglib.Alphabet('char', ['Z'], []))
        aln.add_sample('A', 'Z')
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='NNIPC', data=aln)
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='NIIPC', data=aln)
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='NIPPC', data=aln)
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='NIPCC', data=aln)

        # (positive control)
        struct = egglib.struct_from_iterable(labels, fmt='*NIPC', data=aln)
        ctrl = {'A': {'A': {'A': [0]}}}
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        # invalid number of items
        labels = [['x1', 'clu1', 'pop1'],
                  ['x2', 'clu1', 'pop1', 'x'],
                  ['x3', 'clu1', 'pop1'],
                  ['x4', 'clu1', 'pop1']]
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='ICP')

        labels = [['x1', 'clu1', 'pop1'],
                  ['x2', 'clu1', 'pop1'],
                  ['x3', 'clu1'],
                  ['x4', 'clu1', 'pop1']]
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='ICP')

        labels = [['A', 'A', 'A', '-'],
                  ['A', 'A', 'A', '-'],
                  ['A', 'A', 'A', '-'],
                  ['A', 'A', 'A', '-']]
        ctrl = {'A': {'A': {'A': [0, 1, 2, 3]}}}
        struct = egglib.struct_from_iterable(labels, fmt='ICP*')
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        labels = [['A', 'A', 'A', '-'],
                  'AAA-',
                  ['A', 'A', 'A', '-'],
                  ['A', 'A', 'A', '-']]
        with self.assertRaises(TypeError):
            error = egglib.struct_from_iterable(labels, fmt='ICP*')

        # comments
        labels = [['g', 'A', 'k', 'x'],
                  ['h', 'B', 'l', 'y'],
                  ['i', 'A', 'm', 'w'],
                  ['j', 'B', 'n', 'z']]
        ctrl = {None: {None: {'A': [0, 2], 'B': [1, 3]}}}
        struct = egglib.struct_from_iterable(labels, fmt='*I**')
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        ### data ###

        # name + data
        aln = egglib.Align(alphabet=egglib.Alphabet('int', [0,1], []))
        aln.add_sample('human', [0, 1, 1])
        aln.add_sample('cow', [0, 0, 1])
        aln.add_sample('pig', [0, 1, 1])
        aln.add_sample('dog', [1, 0, 0])
        aln.add_sample('cat', [1, 1, 0])

        labels = [['dog', 'house', 'eat bones'],
                  ['cat', 'house', 'eat mice'],
                  ['pig', 'farm', 'eat corn'],
                  ['human', 'house', 'eat burgers'],
                  ['cow', 'farm', 'eat grass']]
        ctrl = {None: {'house': {'human': [0], 'dog': [3], 'cat': [4]},
                       'farm': {'cow': [1], 'pig': [2]}}}
        struct = egglib.struct_from_iterable(labels, fmt='NP*', data=aln) # NB: names are taken as individual labels
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        # name without data, data without name
        struct = egglib.struct_from_iterable(labels, fmt='NP*', data=aln) # control
        with self.assertRaises(ValueError):
            struct = egglib.struct_from_iterable(labels, fmt='NP*')
        struct = egglib.struct_from_iterable(labels, fmt='*P*') # control
        with self.assertRaises(ValueError):
            struct = egglib.struct_from_iterable(labels, fmt='*P*', data=aln)

        # name in labels but not in data
        labels = [['dog', 'house', 'eat bones'],
                  ['cat', 'house', 'eat mice'],
                  ['pig', 'farm', 'eat corn'],
                  ['velociraptor', 'jurassic park', 'eat goats'],
                  ['human', 'house', 'eat burgers'],
                  ['cow', 'farm', 'eat grass']]
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='NP*', data=aln)
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='NP*', data=aln, skip_missing_names=False)
        struct = egglib.struct_from_iterable(labels, fmt='NP*', data=aln, skip_missing_names=True)
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        # name in data but not in labels
        labels = [['dog', 'house', 'eat bones'],
                  ['cat', 'house', 'eat mice'],
                  ['pig', 'farm', 'eat corn'],
                  ['velociraptor', 'jurassic park', 'eat goats'],
                  ['cow', 'farm', 'eat grass']]
        ctrl = {None: {'house': {'dog': [3], 'cat': [4]},
                       'farm': {'cow': [1], 'pig': [2]}}}
        struct = egglib.struct_from_iterable(labels, fmt='NP*', data=aln, skip_missing_names=True)
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        # duplicate in data
        aln.add_sample('cat', [1, 1, 1])
        del labels[3]
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='NP*', data=aln)

        labels.append(['cat', 'house', 'eat birds'])
        del aln[aln.ns-1]
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='NP*', data=aln)

        ### missing ###
        labels = [['a comment', 'demeA', 'mussel1'],
                  ['a comment', 'demeA', 'mussel2'],
                  ['a comment', 'demeB', 'mussel3'],
                  ['a comment', 'demeB', 'mussel4'],
                  ['a comment', 'demeA', 'mussel5'],
                  ['a comment', 'demeB', 'mussel6']]
        ctrl = {None: {'demeA': {'mussel1': [0], 'mussel2': [1], 'mussel5': [4]},
                       'demeB': {'mussel3': [2], 'mussel4': [3], 'mussel6': [5]}}}
        struct = egglib.struct_from_iterable(labels, fmt='*PI')
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        labels = [['a comment', 'demeA', 'mussel1'],
                  ['a comment', 'demeA', 'mussel2'],
                  ['a comment', 'demeB', 'mussel3'],
                  ['a comment', None, None],
                  ['a comment', 'demeA', 'mussel5'],
                  ['a comment', None, None]]
        ctrl = {None: {'demeA': {'mussel1': [0], 'mussel2': [1], 'mussel5': [4]},
                       'demeB': {'mussel3': [2]}}}
        struct = egglib.struct_from_iterable(labels, fmt='*PI')
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        aln = egglib.Align(alphabet=egglib.Alphabet('int', [0,1], []))
        aln.add_sample('mussel1', [0])
        aln.add_sample('mussel2', [0])
        aln.add_sample('mussel3', [0])
        aln.add_sample('mussel4', [1])
        aln.add_sample('mussel5', [1])
        aln.add_sample('mussel6', [1])
        aln.add_sample('mussel7', [1])
        struct = egglib.struct_from_iterable(labels, fmt='*PN', data=aln)
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})

        labels = [['a comment', 'demeA', 'mussel1'],
                  ['a comment', 'demeA', 'mussel2'],
                  ['a comment', 'demeB', 'mussel3'],
                  ['a comment', None, 'mussel4'],
                  ['a comment', 'demeA', 'mussel5'],
                  ['a comment', None, None]]
        struct = egglib.struct_from_iterable(labels, fmt='*PN', data=aln)
        ing, otg = struct.as_dict()
        self.assertDictEqual(ing, ctrl)
        self.assertDictEqual(otg, {})
        with self.assertRaises(ValueError):
            error = egglib.struct_from_iterable(labels, fmt='*PI')

        # str
        try:
            f, fname = tempfile.mkstemp()
            for row in labels:
                os.write(f, b'\t'.join([str(i).encode() for i in row]) + b'\n')
            os.close(f)
            with open(fname) as f:
                struct = egglib.struct_from_iterable(f, function=lambda x: x.strip().split('\t'), fmt='*PN', data=aln, missing='None')
            ing, otg = struct.as_dict()
            self.assertDictEqual(ing, ctrl)
            self.assertDictEqual(otg, {})
        finally:
            if os.path.isfile(fname): os.unlink(fname)

        ### start/stop ###
        # skip parts of list/file
        try:
            f, fname = tempfile.mkstemp()
            os.write(f, b'''\
#01 An example file
#02 This is a comment line
#03 Below header line
#04 Number,Individual name,pop,
#05,sample #01,pop 1,
#06,sample #02,pop 1,
#07,sample #03,pop 1,
#08,sample #04,pop 1,
#09,sample #05,pop 2,
#10,sample #06,pop 2,
#11,sample #07,pop 3,
#12,sample #08,pop 3,
#13,sample #09,pop 3,
#14,sample #10,pop 3,
''')
            os.close(f)
            ctrl = {None: {'pop 1': {'sample #01': [0], 'sample #02': [1],
                                     'sample #03': [2], 'sample #04': [3]},
                'pop 2': {'sample #05': [4], 'sample #06': [5]},
                'pop 3': {'sample #07': [6], 'sample #08': [7],
                          'sample #09': [8], 'sample #10': [9]}}}

            # start
            with open(fname) as f:
                struct = egglib.struct_from_iterable(f, function=lambda x: x.split(','), fmt='*IP*', start=4)
            ing, otg = struct.as_dict()
            self.assertDictEqual(ing, ctrl)
            self.assertDictEqual(otg, {})

            # out of bounds values supported
            with open(fname) as f:
                struct = egglib.struct_from_iterable(f, function=lambda x: x.split(','), fmt='*IP*', start=4, stop=28)
            ing, otg = struct.as_dict()
            self.assertDictEqual(ing, ctrl)
            self.assertDictEqual(otg, {})

            # stop
            ctrl = {None: {'pop 1': {'sample #02': [0], 'sample #03': [1], 'sample #04': [2]},
                'pop 2': {'sample #05': [3], 'sample #06': [4]},
                'pop 3': {'sample #07': [5], 'sample #08': [6]}}}
            with open(fname) as f:
                struct = egglib.struct_from_iterable(f, function=lambda x: x.split(','), fmt='*IP*', start=5, stop=12)
            ing, otg = struct.as_dict()
            self.assertDictEqual(ing, ctrl)
            self.assertDictEqual(otg, {})
        finally:
            if os.path.isfile(fname): os.unlink(fname)

    def test_from_iterable_outgroup(self):

        # default value for fmt
        ctrl = ({None: {'A': {'idv1': [0], 'idv2': [1],
            'idv3': [2], 'idv4': [3], 'idv9': [8], 'idv10': [9]}, 
            'B': {'idv5': [4], 'idv6': [5], 'idv7': [6], 'idv8': [7]}}},
                {'idv11': [10], 'idv12': [11]})

        # load with outgroup
        struct2 = egglib.struct_from_iterable(list('AAAABBBBAA##'), outgroup='#')
        self.assertEqual(struct2.as_dict(), ctrl)

        # change outgroup label
        struct2 = egglib.struct_from_iterable(list('AAAABBBBAA$$'), outgroup='$')
        self.assertEqual(struct2.as_dict(), ctrl)

        # treat outgroup as missing
        struct2 = egglib.struct_from_iterable(list('AAAABBBBAA##'), missing='#')
        self.assertEqual(struct2.as_dict(), (ctrl[0], {}))

        # load a structure without ougroup
        labels = [
            ('North', 'St.James', 'René'),
            ('North', 'St.James', 'René'),
            ('North', 'St.James', 'Elwire'),
            ('North', 'St.James', 'Elwire'),
            ('North', 'St.James', 'Sebastian'),
            ('North', 'St.James', 'Sebastian'),
            ('North', 'Crimson Road', 'Julius'),
            ('North', 'Crimson Road', 'Julius'),
            ('North', 'Crimson Road', 'Robert'),
            ('North', 'Crimson Road', 'Robert'),
            ('North', 'Crimson Road', 'Nicolas'),
            ('North', 'Crimson Road', 'Nicolas'),
            ('South', 'Tarenta', 'Maria'),
            ('South', 'Tarenta', 'Maria'),
            ('South', 'Tarenta', 'Ali'),
            ('South', 'Tarenta', 'Ali'),
            ('South', 'Zeckberg', 'Ivan'),
            ('South', 'Zeckberg', 'Ivan'),
            ('South', 'Zeckberg', 'Elena'),
            ('South', 'Zeckberg', 'Elena'),
            ('South', 'Zeckberg', 'Ton'),
            ('South', 'Zeckberg', 'Ton')]
        struct1 = egglib.struct_from_iterable(labels, fmt='CPI')
        self.assertEqual(struct1.as_dict(), ({
            'North': {
                'St.James': {
                    'René': [0, 1],
                    'Elwire': [2, 3],
                    'Sebastian': [4, 5] },
                'Crimson Road': {
                    'Julius': [6, 7],
                    'Robert': [8, 9],
                    'Nicolas': [10, 11] } },
            'South': {
                'Tarenta': {
                    'Maria': [12, 13],
                    'Ali': [14, 15] },
                'Zeckberg': {
                    'Ivan': [16, 17],
                    'Elena': [18, 19],
                    'Ton': [20, 21] } } }, {}))

        # add an outgroup
        labels.append(('NA', '#', 'Zac001'))
        struct3 = egglib.struct_from_iterable(labels, fmt='CPI', outgroup='#')
        self.assertEqual(struct3.as_dict(), ({
            'North': {
                'St.James': {
                    'René': [0, 1],
                    'Elwire': [2, 3],
                    'Sebastian': [4, 5] },
                'Crimson Road': {
                    'Julius': [6, 7],
                    'Robert': [8, 9],
                    'Nicolas': [10, 11] } },
            'South': {
                'Tarenta': {
                    'Maria': [12, 13],
                    'Ali': [14, 15] },
                'Zeckberg': {
                    'Ivan': [16, 17],
                    'Elena': [18, 19],
                    'Ton': [20, 21] } } }, { 'Zac001': [22] }))

        # change order, remove clusters and make only 1 population
        labels = [[k, 'otg' if j == '#' else 'ing'] for (i,j,k) in labels]
        struct4 = egglib.struct_from_iterable(labels, fmt='IP', outgroup='otg')
        self.assertEqual(struct4.as_dict(), ({
            None: {
                'ing': {
                    'René': [0, 1],
                    'Elwire': [2, 3],
                    'Sebastian': [4, 5],
                    'Julius': [6, 7],
                    'Robert': [8, 9],
                    'Nicolas': [10, 11],
                    'Maria': [12, 13],
                    'Ali': [14, 15],
                    'Ivan': [16, 17],
                    'Elena': [18, 19],
                    'Ton': [20, 21]}}}, { 'Zac001': [22] }))

    def test_getters(self):
        data = [
            ('', 'TTGGAACAGG', ['idv01', 'pop1', 'clust1']),
            ('', 'TTGGAACAGG', ['idv01', 'pop1', 'clust1']),
            ('', 'TTGGAACAGG', ['idv02', 'pop1', 'clust1']),
            ('', 'TTGGAACAGG', ['idv02', 'pop1', 'clust1']),
            ('', 'TTGGAACAGG', ['idv03', 'pop1', 'clust1']),
            ('', 'TTGGAACAGG', ['idv03', 'pop1', 'clust1']),
            ('', 'TTGGAAGAGG', ['idv04', 'pop1', 'clust1']),
            ('', 'TTGGAAGAGG', ['idv04', 'pop1', 'clust1']),
            ('', 'TGGCAAGGTG', ['idv05', 'pop2', 'clust1']),
            ('', 'TGGCAAGGTG', ['idv05', 'pop2', 'clust1']),
            ('', 'TGGGAAGGTG', ['idv06', 'pop2', 'clust1']),
            ('', 'TGGGAAGGTG', ['idv06', 'pop2', 'clust1']),
            ('', 'TGGGAAGGTG', ['idv07', 'pop2', 'clust1']),
            ('', 'TGGGAAGGTG', ['idv07', 'pop2', 'clust1']),
            ('', 'TGGGAAGGTG', ['idv08', 'pop2', 'clust1']),
            ('', 'TGGGAAGGTG', ['idv08', 'pop2', 'clust1']),
            ('', 'GGGGATCGGC', ['idv09', 'pop3', 'clust2']),
            ('', 'GCGGATCGGC', ['idv09', 'pop3', 'clust2']),
            ('', 'GGGGAACGGC', ['idv10', 'pop3', 'clust2']),
            ('', 'GGGGATCGGC', ['idv10', 'pop3', 'clust2']),
            ('', 'GGGGAACGGC', ['idv11', 'pop3', 'clust2']),
            ('', 'GGGGAACGGC', ['idv11', 'pop3', 'clust2']),
            ('', 'GGGGAACGGC', ['idv12', 'pop3', 'clust2']),
            ('', 'GGGGAACGGC', ['idv12', 'pop3', 'clust2']),
            ('', 'GGGGAACGGC', ['idv13', 'pop4', 'clust2']),
            ('', 'GGGGTACGGC', ['idv13', 'pop4', 'clust2']),
            ('', 'GCGGTACGGC', ['idv14', 'pop4', 'clust2']),
            ('', 'GCGGAACGGC', ['idv14', 'pop4', 'clust2']),
            ('', 'GCGGAACGGC', ['idv15', 'pop4', 'clust2']),
            ('', 'GGGGAACGGC', ['idv15', 'pop4', 'clust2']),
            ('', 'GCGGAACGGC', ['idv16', 'pop4', 'clust2']),
            ('', 'GGGGAACGGC', ['idv16', 'pop4', 'clust2']),
            ('', 'GCGGTTCGTC', ['#', 'idv17']),
            ('', 'GGGGTTCGTC', ['#', 'idv17'])]

        aln = egglib.Align.create(data, egglib.alphabets.DNA)
        struct = egglib.struct_from_labels(aln, lvl_indiv=0, lvl_pop=1, lvl_clust=2)
        self.assertEqual(struct.get_clusters(), ['clust1', 'clust2'])
        self.assertEqual(struct.get_populations(), ['pop1', 'pop2', 'pop3', 'pop4'])

    def test_from_mapping(self):

        ### development tests ###

        # configuration    0     2     4     6     8    10    12    14    16    18    20    22
        #                  0     1     2     3     4     5     6     7     8     9    10    11
        names =         ['A1', 'A2', 'A3', 'B1', 'B2', 'A4', 'C1', 'C2', 'C3', 'B3', 'B4', 'C4']
        pops = {'A': ['A1', 'A2', 'A3', 'A4'],
                'B': ['B1', 'B2', 'B3', 'B4'],
                'C': ['C1', 'C2', 'C3', 'C4']}
        clusters = {'K1': ['A', 'B'], 'K2': ['C']}

        # struct with clusters and pops
        struct1 = egglib.struct_from_mapping(names, clust=clusters, pop=pops, ploidy=2)
        self.assertEqual(struct1.as_dict(),
            ({'K1': {'A': {'A1': [0, 1], 'A2': [2, 3], 'A3': [4, 5], 'A4': [10, 11]},
                     'B': {'B1': [6, 7], 'B2': [8, 9], 'B3': [18, 19], 'B4': [20, 21]}},
              'K2': {'C': {'C1': [12, 13], 'C2': [14, 15], 'C3': [16, 17], 'C4': [22,23]}}}, {}))

        # struct with indivs
        indiv = {'A1': ['A1', 'A2'], 'A3': ['A3', 'A4'], 
                 'B1': ['B1', 'B2'], 'B3': ['B3', 'B4'], 
                 'C1': ['C1', 'C2'], 'C3': ['C3', 'C4']}
        struct2 = egglib.struct_from_mapping(names, indiv=indiv)
        self.assertEqual(struct2.as_dict(),
            ({None: {None: 
                {'A1': [0, 1], 'A3': [2, 5], 'B1': [3, 4], 'B3': [9, 10],
                 'C1': [6, 7], 'C3': [8, 11]}}}, {}))

        # struct with clusters, pops, and outgroup
        pops['B'].remove('B3')
        pops['B'].remove('B4')
        struct3 = egglib.struct_from_mapping(names, pop=pops, clust=clusters,
                                             outgroup=['B3', 'B4'], ploidy=2)
        self.assertEqual(struct3.as_dict(),
            ({'K1': {'A': {'A1': [0, 1], 'A2': [2, 3], 'A3': [4, 5], 'A4': [10, 11]},
                     'B': {'B1': [6, 7], 'B2': [8, 9]}},
              'K2': {'C': {'C1': [12, 13], 'C2': [14, 15], 'C3': [16, 17], 'C4': [22,23]}}},
             {'B3': [18, 19], 'B4': [20, 21]}))

        # struct with clusters, pops, and outgroup + indivs
        pops = {'A': ['A1'], 'B': ['B1', 'B3'], 'C': ['C1', 'C3']}
        clusters = {'K1': ['A', 'C'], 'K2': ['B']}
        struct4 = egglib.struct_from_mapping(names, indiv=indiv, pop=pops,
                                        clust=clusters, outgroup=['A3'])
        self.assertEqual(struct4.as_dict(),
            ( {'K1': {
                  'A': {'A1': [0, 1]},
                  'C': {'C1': [6, 7], 'C3': [8, 11]}},
               'K2': {
                  'B': {'B1': [3, 4], 'B3': [9, 10]}}},
               {'A3': [2, 5]}))

        # triploid data with outgroup (pops)
            #      0     1     2     3     4     5     6     7     8     9    10    11    12    13    14
        names = ['A1', 'D3', 'B1', 'B2', 'D1', 'A2', 'B3', 'C3', 'A3', 'O1', 'C1', 'O3', 'D2', 'O2', 'C2']
        idv = {'A': ['A1', 'A2', 'A3'], 'B': ['B1', 'B2', 'B3'],
               'C': ['C1', 'C2', 'C3'], 'D': ['D1', 'D2', 'D3'],
               'O': ['O1', 'O2', 'O3']}
        pops = {'BC': ['B', 'C'], 'DA': ['D', 'A']}
        struct4.from_mapping(names, indiv=idv, pop=pops, outgroup=['O'])
        self.assertEqual(struct4.as_dict(),
            ({None: {
                'BC': {
                    'B': [2, 3, 6],
                    'C': [10, 14, 7]},
                'DA': {
                    'A': [0, 5, 8],
                    'D': [4, 12, 1]}}},
            {'O': [9, 13, 11]}))

        # flat data
        names = 'ABCDEF'
        struct5 = egglib.struct_from_mapping(names)
        self.assertEqual(struct5.as_dict(),
            ({None: {None: {'A': [0], 'B': [1], 'C': [2], 'D': [3], 'E': [4], 'F': [5]}}}, {}))

        struct6 = egglib.struct_from_mapping(names, ploidy=2)
        self.assertEqual(struct6.as_dict(),
            ({None: {None: {'A': [0, 1], 'B': [2, 3], 'C': [4, 5],
                            'D': [6, 7], 'E': [8, 9], 'F': [10, 11]}}}, {}))

        # outgroup
        struct7 = egglib.struct_from_mapping(names, outgroup=['A'])
        self.assertEqual(struct7.as_dict(),
            ({None: {None: {'B': [1], 'C': [2], 'D': [3], 'E': [4], 'F': [5]}}}, {'A': [0]}))

        struct8 = egglib.struct_from_mapping(names, ploidy=2, outgroup=['B'])
        self.assertEqual(struct8.as_dict(),
            ({None: {None: {'A': [0, 1], 'C': [4, 5], 'D': [6, 7],
                            'E': [8, 9], 'F': [10, 11]}}}, {'B': [2, 3]}))

        # haploid outgroup
        struct9 = egglib.struct_from_mapping(names, ploidy=2, outgroup=['C'], outgroup_haploid=True)
        self.assertEqual(struct9.as_dict(),
            ({None: {None: {'A': [0, 1], 'B': [2, 3], 'D': [5, 6],
                            'E': [7, 8], 'F': [9, 10]}}}, {'C': [4]}))

        ### errors ###

        # ploidy
        with self.assertRaisesRegex(ValueError, '^ploidy must be at least 1$'):
            egglib.struct_from_mapping('ABCD', ploidy=0)
        with self.assertRaisesRegex(ValueError, '^ploidy must be at least 1$'):
            egglib.struct_from_mapping('ABCD', ploidy=-1)
        with self.assertRaisesRegex(ValueError, '^if indiv is specified, ploidy must be 1$'):
            egglib.struct_from_mapping('ABCD', indiv={'1': ['A', 'B'], '2': ['C', 'D']}, ploidy=2)

        # clust
        with self.assertRaisesRegex(ValueError, '^cannot specify clusters without populations$'):
            egglib.struct_from_mapping('ABCD', clust={'K': ['P1', 'P2'], 'L': ['P3', 'P4']})
        pops = {'P1': ['A', 'B'], 'P2': ['C', 'D', 'E'],
                'P3': ['F', 'G'], 'P4': ['H', 'I', 'J']}
        clusters = {'K1': ['P1', 'Px'], 'K2': ['P3', 'P4']}
        with self.assertRaisesRegex(ValueError, '^population not found: Px$'):
            egglib.struct_from_mapping('ABCDEFGHIJ', pop=pops, clust=clusters)
        clusters['K1'][1] = 'P3'
        with self.assertRaisesRegex(ValueError, '^population P3 is duplicated in clusters$'):
            egglib.struct_from_mapping('ABCDEFGHIJ', pop=pops, clust=clusters)
        clusters['K1'][1] = 'P2'
        egglib.struct_from_mapping('ABCDEFGHIJ', pop=pops, clust=clusters)

        # pop
        pops = {'P1': ['A', 'B'], 'P2': ['X', 'D'],
                'P3': ['E', 'F'], 'P4': ['G', 'H']}
        with self.assertRaisesRegex(ValueError, '^individual not found: X$'):
            egglib.struct_from_mapping('ABCDEFGH', pop=pops)
        pops['P2'][0] = 'B'
        with self.assertRaisesRegex(ValueError, '^individual B is duplicated in populations$'):
            egglib.struct_from_mapping('ABCDEFGH', pop=pops)
        pops['P2'][0] = 'C'
        egglib.struct_from_mapping('ABCDEFGH', pop=pops)

        idv = {'I1': ['A', 'B'], 'I2': ['C', 'D'],
                'I3': ['E', 'F'], 'I4': ['G', 'H']}
        pops = {'P1': ['I1', 'I2'], 'P2': ['I3', 'Ix']}
        with self.assertRaisesRegex(ValueError, '^individual not found: Ix$'):
            egglib.struct_from_mapping('ABCDEFGH', pop=pops, indiv=idv)
        pops['P2'][1] = 'I4'
        egglib.struct_from_mapping('ABCDEFGH', pop=pops, indiv=idv)
        pops['P2'][1] = 'I2'
        with self.assertRaisesRegex(ValueError, '^individual I2 is duplicated in populations$'):
            egglib.struct_from_mapping('ABCDEFGH', pop=pops, indiv=idv)

        # outgroup
        with self.assertRaisesRegex(ValueError, '^outgroup indiv X not found$'):
            egglib.struct_from_mapping('ABCDEFGH', outgroup='X')
        with self.assertRaisesRegex(ValueError, '^outgroup indiv E is duplicated$'):
            egglib.struct_from_mapping('ABCDEFGH', outgroup=['D', 'E', 'E'])
        idv = {'X': 'AB', 'Y': 'CD', 'W': 'EF', 'Z': 'GH'}
        with self.assertRaisesRegex(ValueError, '^outgroup indiv A not found$'):
            egglib.struct_from_mapping('ABCDEFGH', indiv=idv, outgroup='A')
        egglib.struct_from_mapping('ABCDEFGH', outgroup='A')
        egglib.struct_from_mapping('ABCDEFGH', indiv=idv, outgroup='X')
        pops = {'X': ['A', 'B', 'C', 'D'], 'Y': ['E', 'F', 'G', 'H']}
        with self.assertRaisesRegex(ValueError, '^individual both in ingroup and outgroup: H$'):
            egglib.struct_from_mapping('ABCDEFGH', pop=pops, outgroup='H')
        pops['Y'].remove('H')
        egglib.struct_from_mapping('ABCDEFGH', pop=pops, outgroup='H')

        # outgroup_haploid
        egglib.struct_from_mapping('ABCDEFGH', ploidy=1, outgroup_haploid=True, outgroup=['G'])
        egglib.struct_from_mapping('ABCDEFGH', ploidy=2, outgroup_haploid=True, outgroup=['G'])
        with self.assertRaisesRegex(ValueError, '^if indiv is specified, ploidy must be 1$'):
            egglib.struct_from_mapping('ABCDEFGH', ploidy=2, indiv=idv, outgroup_haploid=True, outgroup='X')
        with self.assertRaisesRegex(ValueError, '^with outgroup_haploid option, there must be only one outgroup sample$'):
            egglib.struct_from_mapping('ABCDEFGH', ploidy=2, outgroup_haploid=True, outgroup=['G', 'H'])

        # indiv
        idv = {'X': 'AB', 'Y': 'CX', 'W': 'EF'}
        with self.assertRaisesRegex(ValueError, '^indiv item X not in names$'):
            egglib.struct_from_mapping('ABCDEFGH', indiv=idv)
        idv['Y'] = 'CB'
        with self.assertRaisesRegex(ValueError, '^name B is duplicated in indiv$'):
            egglib.struct_from_mapping('ABCDEFGH', indiv=idv)
        idv['Y'] = 'CD'
        egglib.struct_from_mapping('ABCDEFGH', indiv=idv)
