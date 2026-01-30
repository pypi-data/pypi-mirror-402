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
path = pathlib.Path(__file__).parent / '..' / 'data'

class EHH_test(unittest.TestCase):
    def test_EHH_T(self):
        ehh=egglib.stats.EHH()
        self.assertEqual(str(type(ehh)), "<class 'egglib.stats._ehh.EHH'>")

    def test_set_core_T(self): # unfinished test 
        ehh=egglib.stats.EHH()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        site = egglib.site_from_align(aln, 2213)
        site.position = 0
        ehh.set_core(site)
        sites = []
        alph = egglib.alphabets.Alphabet('range', (1, 99), (0, ))
        idx = 1
        for site in (([1,1, 1,0, 1,1, 1,1, 2,1, 1,2, 2,0, 2,2, 2,2, 2,2, 0,0, 3,3, 3,3]),
                     ([1,0, 0,0, 1,2, 1,1, 2,1, 2,2, 2,0, 2,2, 2,2, 2,2, 0,0, 3,3, 1,3]),
                     ([4,2, 4,3, 3,1, 3,2, 1,2, 1,4, 1,2, 3,2, 1,3, 2,4, 3,1, 2,2, 3,1]),
                     ([4,2, 4,3, 3,1, 3,2, 1,1, 3,4, 1,2, 3,2, 1,3, 2,4, 3,1, 2,2, 3,1]),
                     ([4,2, 4,3, 3,1, 3,2, 2,2, 1,1, 1,2, 3,2, 1,3, 2,4, 3,1, 2,2, 3,1])):
            site = egglib.site_from_list(site, alphabet=alph)
            site.position = idx
            sites.append(site)
            idx += 1
        ehh.set_core(sites[0], struct=2, EHHS_thr=0.5, min_freq=None)
        for site in sites[1:]: ehh.load_distant(site)

    def test_structure(self):
        core =  '00000111111111122222222223'
        dist1 = '00000000111111111111111111'
        dist2 = '00010110000011111101100000'
        dist3 = '01110000000111000000111100'
        dist4 = '00111111011101111111111111'
        site_core = egglib.site_from_list(core, alphabet=egglib.alphabets.Alphabet('char', '0123', []))
        site_core.position = 0
        alph = egglib.alphabets.Alphabet('char', '01', [])
        site1 = egglib.site_from_list(dist1, alphabet=alph)
        site2 = egglib.site_from_list(dist2, alphabet=alph)
        site3 = egglib.site_from_list(dist3, alphabet=alph)
        site4 = egglib.site_from_list(dist4, alphabet=alph)
        site1.position = 1
        site2.position = 2
        site3.position = 3
        site4.position = 4

        ehh = egglib.stats.EHH()

        ehh.set_core(site_core)
        self.assertAlmostEqual(ehh.num_haplotypes, 4)
        self.assertAlmostEqual(ehh.get_EHH(0), 20/20.0, places=6)
        self.assertAlmostEqual(ehh.get_EHH(1), 90/90.0, places=6)
        self.assertAlmostEqual(ehh.get_EHH(2), 90/90.0, places=6)
        self.assertIsNone(ehh.get_EHH(3))

        ehh.load_distant(site1)
        self.assertAlmostEqual(ehh.get_EHH(0), 20/20.0, places=6)
        self.assertAlmostEqual(ehh.get_EHH(1), 48/90.0, places=6) 
        self.assertAlmostEqual(ehh.get_EHH(2), 90/90.0, places=6)
        self.assertIsNone(ehh.get_EHH(3))

        ehh.load_distant(site2)
        self.assertAlmostEqual(ehh.get_EHH(0), 12/20.0, places=6)
        self.assertAlmostEqual(ehh.get_EHH(1), 20/90.0, places=6)
        self.assertAlmostEqual(ehh.get_EHH(2), 40/90.0, places=6)
        self.assertIsNone(ehh.get_EHH(3))

        ehh.load_distant(site3)
        self.assertAlmostEqual(ehh.get_EHH(0), 4/20.0, places=6)
        self.assertAlmostEqual(ehh.get_EHH(1), 10/90.0, places=6)
        self.assertAlmostEqual(ehh.get_EHH(2), 20/90.0, places=6)
        self.assertIsNone(ehh.get_EHH(3))

        ehh.load_distant(site4)
        self.assertAlmostEqual(ehh.get_EHH(0), 0/20.0, places=6)
        self.assertAlmostEqual(ehh.get_EHH(1), 4/90.0, places=6)
        self.assertAlmostEqual(ehh.get_EHH(2), 20/90.0, places=6)
        self.assertIsNone(ehh.get_EHH(3))

        struct = egglib.struct_from_dict(
            {None: {None: {'0': (0, 1), '1': (2, 3), '2': (4, 5), '3': (6, 7), '4': (8, 9), '5': (10, 11),  '6': (12, 13),
                     '7': (14, 15), '8': (16, 17), '9': (18, 19), '10': (20, 21), '11': (22, 23), '12': (24, 25)}}}, None)

        ehh.set_core(site_core, struct=struct)
        self.assertEqual(ehh.get_EHHG(), 1.0)
        ehh.load_distant(site1)
        self.assertEqual(ehh.get_EHHG(), 1.0)
        ehh.load_distant(site2)
        self.assertEqual(ehh.get_EHHG(), 0.6)
        ehh.load_distant(site3)
        self.assertEqual(ehh.get_EHHG(), 0.4)
        ehh.load_distant(site4)
        self.assertEqual(ehh.get_EHHG(), 0.2)

        ehh.set_core(site_core, struct=2)
        self.assertEqual(ehh.get_EHHG(), 1.0)
        ehh.load_distant(site1)
        self.assertEqual(ehh.get_EHHG(), 1.0)
        ehh.load_distant(site2)
        self.assertEqual(ehh.get_EHHG(), 0.6)
        ehh.load_distant(site3)
        self.assertEqual(ehh.get_EHHG(), 0.4)
        ehh.load_distant(site4)
        self.assertEqual(ehh.get_EHHG(), 0.2)
