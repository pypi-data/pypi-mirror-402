"""
    Copyright 2023 Thomas Coudoux, Stéphane De Mita, Mathieu Siol

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

import egglib, unittest, pathlib

ALPH = egglib.alphabets.Alphabet('range', [0, None], [-1, 0], case_insensitive=False)

class LD_test(unittest.TestCase):
    def test_pairwise_LD_T(self):
        sites = [egglib.site_from_list(i, ALPH) for i in 
                 [  [0,0,0,1,1,1,2,1,1,1],
                    [0,1,1,-1,0,0,0, 0,0,0],
                    [0,0,1,2, 2,1,-1,2,-1,2]]  ]
        ld=egglib.stats.pairwise_LD(sites[0], sites[1])
        self.assertIsInstance(ld, dict)

        # additional tests addressing the structure
        coal = egglib.coalesce.Simulator(num_pop=2, num_chrom=[25, 25], theta=5, migr=0.5)
        alnA = coal.simul()
        structA = egglib.struct_from_labels(alnA, lvl_pop=0)
        structB = egglib.struct_from_dict({None: {None: structA.as_dict()[0][None]['0']}}, None)
        alnB = egglib.Align.create([(sam.name, sam.sequence) for sam in alnA.group_mapping()['0']], alphabet=alnA.alphabet)

        stats1 = egglib.stats.matrix_LD(alnA, ['d', 'D', 'Dp', 'r'], struct=structA)
        stats2 = egglib.stats.matrix_LD(alnA, ['d', 'D', 'Dp', 'r'], struct=None)
        self.assertEqual(stats1, stats2)

        stats3 = egglib.stats.matrix_LD(alnA, ['d', 'D', 'Dp', 'r'], struct=structB)
        stats4 = egglib.stats.matrix_LD(alnB, ['d', 'D', 'Dp', 'r'], struct=structB) # should work also with None but order can be screwed and then r, D (Dp?) can be inverted
        self.assertEqual(stats3, stats4)
        self.assertNotEqual(stats1, stats3)

        siteA1 = egglib.site_from_align(alnA, 0)
        siteA2 = egglib.site_from_align(alnA, 1)
        siteAL = egglib.site_from_align(alnA, alnA.ls - 1)

        siteB1 = egglib.site_from_align(alnB, 0)
        siteB2 = egglib.site_from_align(alnB, 1)
        siteBL = egglib.site_from_align(alnB, alnB.ls - 1)

        statsA = egglib.stats.pairwise_LD(siteA1, siteA2), egglib.stats.pairwise_LD(siteA1, siteAL)
        statsAsA = egglib.stats.pairwise_LD(siteA1, siteA2, struct=structA), egglib.stats.pairwise_LD(siteA1, siteAL, struct=structA)
        statsAsB = egglib.stats.pairwise_LD(siteA1, siteA2, struct=structB), egglib.stats.pairwise_LD(siteA1, siteAL, struct=structB)
        statsB = egglib.stats.pairwise_LD(siteB1, siteB2), egglib.stats.pairwise_LD(siteB1, siteBL)

        for k in 'D', 'Dp', 'r':
            if statsA[0][k] is not None: statsA[0][k] = abs(statsA[0][k])
            if statsA[1][k] is not None: statsA[1][k] = abs(statsA[1][k])
            if statsAsA[0][k] is not None: statsAsA[0][k] = abs(statsAsA[0][k])
            if statsAsA[1][k] is not None: statsAsA[1][k] = abs(statsAsA[1][k])
            if statsAsB[0][k] is not None: statsAsB[0][k] = abs(statsAsB[0][k])
            if statsAsB[1][k] is not None: statsAsB[1][k] = abs(statsAsB[1][k])
            if statsB[0][k] is not None: statsB[0][k] = abs(statsB[0][k])
            if statsB[1][k] is not None: statsB[1][k] = abs(statsB[1][k])

        self.assertListEqual(sorted(statsA[0]), sorted(statsA[1]))
        self.assertListEqual(sorted(statsA[0]), sorted(statsAsA[0]))
        self.assertListEqual(sorted(statsA[0]), sorted(statsAsA[1]))
        self.assertListEqual(sorted(statsA[0]), sorted(statsAsB[0]))
        self.assertListEqual(sorted(statsA[0]), sorted(statsAsB[1]))
        self.assertListEqual(sorted(statsA[0]), sorted(statsB[0]))
        self.assertListEqual(sorted(statsA[0]), sorted(statsB[1]))

        for k in statsA[0]:
            self.assertAlmostEqual(statsA[0][k], statsAsA[0][k])
            self.assertAlmostEqual(statsA[1][k], statsAsA[1][k])
            self.assertAlmostEqual(statsB[0][k], statsAsB[0][k])
            self.assertAlmostEqual(statsB[1][k], statsAsB[1][k])

        alph1 = egglib.alphabets.Alphabet('int', [1,2], [])
        alph2 = egglib.alphabets.Alphabet('int', [111,112,122,222], [])
        site1 = egglib.site_from_list([1,1,1,1,2,1,1,2,2,2,2,2,1,1,2], alphabet=alph1)
        site2 = egglib.site_from_list([1,1,1,1,1,1,1,1,2,2,2,2,1,2,2], alphabet=alph1)
        site1g = egglib.site_from_list([111,112,122,222,112], alphabet=alph2)
        site2g = egglib.site_from_list([111,111,112,222,122], alphabet=alph2)
        struct = egglib.struct_from_dict({None: {None: {'a': (0,1,2), 'b': (3,4,5), 'c': (6,7,8), 'd': (9,10,11), 'e': (12,13,14)}}}, None)

        stats1 = egglib.stats.pairwise_LD(site1, site2, struct=struct)
        stats2 = egglib.stats.pairwise_LD(site1g, site2g)
        stats3 = egglib.stats.pairwise_LD(site1, site2)

        for k in 'D', 'Dp', 'r':
            stats1[k] = abs(stats1[k])
            stats2[k] = abs(stats2[k])
            stats3[k] = abs(stats3[k])
        self.assertListEqual(sorted(stats1), sorted(stats2))
        self.assertListEqual(sorted(stats1), sorted(stats3))
        diff = 0
        for k in stats1:
            self.assertAlmostEqual(stats1[k], stats2[k])
            if abs(stats1[k] - stats3[k]) > 0.000001: diff += 1
        self.assertNotEqual(diff, 0, msg="expect at least one difference between stats")

    def test_pairwise_LD_E(self):
        sites = [egglib.site_from_list(i, ALPH)for i in 
                 [  [ 0, 0, 0, 1, 1, 1, 2, 1, 1, 1],
                    [ 0, 1, 1,-1, 0, 0, 0, 0],      ]   ]
        with self.assertRaises(ValueError):
            egglib.stats.pairwise_LD(sites[0], sites[1])

    def test_matrix_LD_T(self):
        p3 = egglib._eggwrapper.Params(1)
        p3.set_n1(0, 60)
        p3.set_mutmodel(p3.KAM)
        p3.set_K(2)
        p3.set_R(0.1)
        p3.set_theta(5.0)
        p3.set_L(1000)
        p3.autoSitePos()
        p3.validate()
        coal = egglib._eggwrapper.Coalesce()
        coal.simul(p3, True)
        simdata5 = coal.data()
        aln = egglib.Align(egglib.alphabets.DNA)
        for i in range(simdata5.get_nsam()):
            n = 'sample_{0}'.format(str(i).rjust(3, '0'))
            s = ''.join(['ACGT'[simdata5.get_sample(i, j)] for j in range(simdata5.get_nsit_all())])
            aln.add_sample(n, s)
        MLD_D=egglib.stats.matrix_LD(aln, 'D')
        self.assertIsInstance(MLD_D, tuple)
        MLD_all=egglib.stats.matrix_LD(aln, ['d', 'Dp', 'rsq'])
        self.assertIsInstance(MLD_all, tuple)
        
    def test_matrix_LD_E(self):
        p3 = egglib._eggwrapper.Params(1)
        p3.set_n1(0, 60)
        p3.set_mutmodel(p3.KAM)
        p3.set_K(2)
        p3.set_R(0.1)
        p3.set_theta(5.0)
        p3.set_L(1000)
        p3.autoSitePos()
        p3.validate()
        coal = egglib._eggwrapper.Coalesce()
        coal.simul(p3, True)
        simdata5 = coal.data()
        aln = egglib.Align(egglib.alphabets.DNA)
        for i in range(simdata5.get_nsam()):
            n = 'sample_{0}'.format(str(i).rjust(3, '0'))
            s = ''.join(['ACGT'[simdata5.get_sample(i, j)] for j in range(simdata5.get_nsit_all())])
            aln.add_sample(n, s)

        with self.assertRaises(ValueError):
            egglib.stats.matrix_LD(aln, 'D', min_n=1)
        with self.assertRaises(ValueError):
            egglib.stats.matrix_LD(aln, 'D', max_maj=1.5)
        with self.assertRaises(ValueError):
            egglib.stats.matrix_LD(aln, 'D', positions=[1001,1002,1003])
        with self.assertRaises(ValueError):
            egglib.stats.matrix_LD(aln, ['FAIL', 'Dp', 'rsq'])
