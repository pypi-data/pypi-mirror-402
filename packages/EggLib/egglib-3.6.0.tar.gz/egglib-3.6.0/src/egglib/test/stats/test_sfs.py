"""
    Copyright 2025 Stéphane De Mita, Mathieu Siol

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

import egglib, unittest

class SFS_test(unittest.TestCase):
    def setUp(self):
        # standard sites
        self.sites1 = [egglib.site_from_list(site, alphabet=egglib.alphabets.DNA)
                    for site in [
                        'AAAACAAAAACAAAA',  # 2         p=0.133 (3)
                        'TTTTTTATTTTTTTT',  # 1         p=0.067 (3)
                        'GGGCGGGGGGCGGGG',  # 2         p=0.133
                        'GGCGGCCCCGCGGCG',  # 7         p=0.467 (2)
                        'GGGGGGGGGGGGGGG',  # 0         p=0.000 (4)
                        'TTTTTCTTTTTTTTT',  # 1         p=0.067
                        'CCCCCCCCCCCCCCC',  # 0         p=0.000
                        'CCCCCACCCCAACCC',  # 3         p=0.2   (1)
                        'AAAAACAAAAAAAAA',  # 1         p=0.067
                        'TTTTTTTTTTTTTTT',  # 0         p=0.000
                        'AAAAAAAAAAAAAAA',  # 0         p=0.000
                        'AAACAACCCACCCCC',  # 6         p=0.4   (1)
                        'TTTTCTTTTTTTTTC',  # 2         p=0.133
                        'CGCCGGGGCGCCGGC']] # 7         p=0.467

        # sites1 as an Align
        self.align1 = egglib.Align.create([
            ('name 1',  'ATGGGTCCATAATC'),
            ('name 2',  'ATGGGTCCATAATG'),
            ('name 3',  'ATGCGTCCATAATC'),
            ('name 4',  'ATCGGTCCATACTC'),
            ('name 5',  'CTGGGTCCATAACG'),
            ('name 6',  'ATGCGCCACTAATG'),
            ('name 7',  'AAGCGTCCATACTG'),
            ('name 8',  'ATGCGTCCATACTG'),
            ('name 9',  'ATGCGTCCATACTC'),
            ('name 10', 'ATGGGTCCATAATG'),
            ('name 11', 'CTCCGTCAATACTC'),
            ('name 12', 'ATGGGTCAATACTC'),
            ('name 13', 'ATGGGTCCATACTG'),
            ('name 14', 'ATGCGTCCATACTG'),
            ('name 15', 'ATGGGTCCATACCC')], alphabet=egglib.alphabets.DNA)

        # sites with outgroup
        self.sites2 = [egglib.site_from_list(site, alphabet=egglib.alphabets.DNA)
                    for site in [
                        'AAAACAAAAACAAAAA',  # 2
                        'TTTTTTATTTTTTTTT',  # 1
                        'GGGCGGGGGGCGGGGG',  # 2
                        'GGCGGCCCCGCGGCGG',  # 7
                        'GGGGGGGGGGGGGGGG',  # 0
                        'TTTTTCTTTTTTTTTC',  # 14 (reverted)
                        'CCCCCCCCCCCCCCCG',  # 15 (reverted)
                        'CCCCCACCCCAACCCC',  # 3
                        'AAAAACAAAAAAAAAA',  # 1
                        'TTTTTTTTTTTTTTTT',  # 0
                        'AAAAAAAAAAAAAAAA',  # 0
                        'AAACAACCCACCCCCA',  # 9 (reverted)
                        'TTTTCTTTTTTTTTCT',  # 2
                        'CGCCGGGGCGCCGGCG']] # 7
        self.struct1 = egglib.struct_from_samplesizes([15], outgroup=0)
        self.struct2 = egglib.struct_from_samplesizes([15], outgroup=1)

        # same as sites1 but with additional (ignored) samples
        self.sites3 = [egglib.site_from_list(site, alphabet=egglib.alphabets.DNA)
                    for site in [
                        #110111111011111110
                        'AAAAACAAAAAACAAAAC',  # 2
                        'TTTTTTTATCTTTTTTTT',  # 1
                        'GGGGCGGGGGGGCGGGGG',  # 2
                        'GGGCGGCCCCCGCGGCGG',  # 7
                        'GGGGGGGGGGGGGGGGGG',  # 0
                        'TTTTTTCTTTTTTTTTTT',  # 1
                        'CCCCCCCCCCCCCCCCCC',  # 0
                        'CCCCCCACCCCCAACCCC',  # 3
                        'AACAAACAAAAAAAAAAA',  # 1
                        'TTTTTTTTTTTTTTTTTT',  # 0
                        'AAAAAAAAA-AAAAAAAA',  # 0
                        'AAAACAACC-CACCCCCC',  # 6
                        'TTCTTCTTTTTTTTTTCC',  # 2
                        'CGCCCGGGGGCGCCGGCC']] # 7
        self.struct3 = egglib.struct_from_dict({None: {None: {str(i): (i,) for i in [0,1,3,4,5,6,7,8,10,11,12,13,14,15,16]}}}, None)

        # sites with missing data
        self.sites4 = [egglib.site_from_list(site, alphabet=egglib.alphabets.DNA)
                    for site in [
                        'AAAACAAAAACAAAA',  # 2
                        'TTTTTTATTTTTTTT',  # 1
                        'AAAACCCGAAAAAAA',  # three alleles: always ignored
                        'AA-AACCACAAA-AA',  # 3/13 (missing: 0.133)
                        'GGGCGGGGGGCGGGG',  # 2
                        'GGCGGCCCCGCGGCG',  # 7
                        'GGGGGGGGGGGGGGG',  # 0
                        'TTTTTCTTTTTTTTT',  # 1
                        'CCCCCCCCCCCCCCC',  # 0
                        'CCCCCACCCCAACCC',  # 3
                        'CCCCC-CCCCGCCCC',  # 1/14 (missing: 0.067)
                        'GGGGGGGGGNCGGGG',  # 1/14 (missing: 0.067)
                        'AAAAACAAAAAAAAA',  # 1
                        'TTTTTTTTTTTTTTT',  # 0
                        'AAAAAAAAAAAAAAA',  # 0
                        'AAACAACCCACCCCC',  # 6
                        'TTTTCTTTTTTTTTC',  # 2
                        'CGCCGGGGCGCCGGC']] # 7

        self.sites5 = [egglib.site_from_list(site, alphabet=egglib.alphabets.DNA)
                    for site in [
                    #    0+++++ ++   +++       miss  Nder  Pder   Nmin  Pmin
                        'AAAAAACCCCCCCCC',   # 0     5     0.5    5     0.5
                        'AAAAAAGAACCCCCC',   # 0     3     0.3    3     0.3
                        'AAACCAAA--AAAAA',   # 0.1   2     0.222  2     0.222
                        'CGGCCCCCGGCCCCC',   # 0     3     0.3    3     0.3
                        'CCCCCCCCCGCCCCC',   # 0     0     0      0     0
                        'CCMTTTATTAMCTTT',   # 0.1   8     0.889  1     0.111
                        'GGGTGGGGGGGGGGG',   # 0     1     0.1    1     0.1
                        'GCGGRRGGGGGGGGG',   # 0.2   1     0.125  1     0.125
                        'GGGGTTGGGGGGGGG',   # 0     2     0.2    2     0.2
                        'TTTTTTTGATTTTTT',   # 0     NA    NA     NA    NA
                        'TCRCCCCCCTTTTTT',   # 0.1   6     0.667  3     0.333
                        'TTTCTNCTTNNTTTT',   # 0.1   1     0.111  1     0.111
                        'TCCCCCCCCCCCCCC',   # 0     10    1      0     0
                        'TCCCCGCGGGGGGGG' ]] # 0     NA    NA     NA    NA
        self.struct5 = egglib.struct_from_dict({None: {None: {str(i): (i,) for i in [1,2,3,4,5,7,8,12,13,14]}}}, {'otg': (0,)})


    def test_standard(self):
        res = egglib.stats.SFS(self.sites1)
        self.assertEqual(res, [4, 3, 3, 1, 0, 0, 1, 2])

        res = egglib.stats.SFS(self.align1.iter_sites())
        self.assertEqual(res, [4, 3, 3, 1, 0, 0, 1, 2])

    def test_mode(self):
        res = egglib.stats.SFS(self.sites1, mode='auto')
        self.assertEqual(res, [4, 3, 3, 1, 0, 0, 1, 2])

        res = egglib.stats.SFS(self.sites1, mode='folded')
        self.assertEqual(res, [4, 3, 3, 1, 0, 0, 1, 2])

        with self.assertRaisesRegex(ValueError, "^cannot process unfolded SFS with no outgroup information$"):
            egglib.stats.SFS(self.sites1, mode='unfolded')

        with self.assertRaisesRegex(ValueError, "^cannot process unfolded SFS with no outgroup information$"):
            egglib.stats.SFS(self.sites1, struct=self.struct1, mode='unfolded')

        res = egglib.stats.SFS(self.sites2, struct=self.struct2, mode='unfolded')
        self.assertEqual(res, [3, 2, 3, 1, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 1, 1])

        res = egglib.stats.SFS(self.sites2, struct=self.struct2, mode='auto')
        self.assertEqual(res, [3, 2, 3, 1, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 1, 1])

        res = egglib.stats.SFS(self.sites2, struct=self.struct2, mode='folded')
        self.assertEqual(res, [4, 3, 3, 1, 0, 0, 1, 2])

    def test_struct(self):
        res = egglib.stats.SFS(self.sites3, struct=self.struct3)
        self.assertEqual(res, [4, 3, 3, 1, 0, 0, 1, 2])

    def test_missing(self):
        # by default, sites with missing data ignored (also: one site with 3 alleles)
        res = egglib.stats.SFS(self.sites4)
        self.assertEqual(res, [4, 3, 3, 1, 0, 0, 1, 2])

        # allow one additional site
        res = egglib.stats.SFS(self.sites4, max_missing = 0.1)
        self.assertEqual(res, [4, 5, 3, 1, 0, 0, 1, 2])

        # allow two more sites
        res = egglib.stats.SFS(self.sites4, max_missing = 0.2)
        self.assertEqual(res, [4, 5, 3, 2, 0, 0, 1, 2])

    def compare_sfs(self, a, b):
        self.assertEqual(len(a), len(b), msg=f'{a} vs. {b}')
        for x, y in zip(a, b):
            self.assertEqual(len(x), 2, msg=f'{a} vs. {b}')
            self.assertEqual(len(y), 2, msg=f'{a} vs. {b}')
            self.assertAlmostEqual(x[0], y[0], places=6, msg=f'{a} vs. {b}')
            self.assertEqual(x[1], y[1], msg=f'{a} vs. {b}')

    def test_bins(self):
        res = egglib.stats.SFS(self.sites1, nbins=10)
        self.compare_sfs(res, [(0.05, 4), (0.10, 3), (0.15, 3), (0.20, 1),
                               (0.25, 0), (0.30, 0), (0.35, 0), (0.40, 1),
                               (0.45, 0), (0.50, 2)]) # there might be a rounding error

        # test without binning

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded')
        self.assertEqual(res, [1, 1, 1, 2, 0, 1, 0, 0, 0, 0, 1])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', max_missing=0.15)
        self.assertEqual(res, [1, 2, 2, 2, 0, 1, 1, 0, 1, 0, 1])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', max_missing=0.55)
        self.assertEqual(res, [1, 3, 2, 2, 0, 1, 1, 0, 1, 0, 1])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='folded')
        self.assertEqual(res, [2, 1, 1, 2, 0, 1])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='folded', max_missing=0.15)
        self.assertEqual(res, [2, 3, 2, 3, 0, 1])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='folded', max_missing=0.55)
        self.assertEqual(res, [2, 4, 2, 3, 0, 1])

        # test with binning

        with self.assertRaisesRegex(ValueError, '^invalid number of bins$'):
            res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=-1)

        with self.assertRaisesRegex(ValueError, '^invalid number of bins$'):
            res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=0)

        with self.assertRaisesRegex(ValueError, '^invalid number of bins$'):
            res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=1)

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=2)
        self.compare_sfs(res, [(0.5, 6), (1.0, 1)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=2, max_missing=0.15)
        self.compare_sfs(res, [(0.5, 8), (1.0, 3)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=2, max_missing=0.25)
        self.compare_sfs(res, [(0.5, 9), (1.0, 3)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=4)
        self.compare_sfs(res, [(0.25, 3), (0.5, 3), (0.75, 0), (1.0, 1)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=4, max_missing=0.12)
        self.compare_sfs(res, [(0.25, 5), (0.5, 3), (0.75, 1), (1.0, 2)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=4, max_missing=0.2)
        self.compare_sfs(res, [(0.25, 6), (0.5, 3), (0.75, 1), (1.0, 2)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=12)
        self.compare_sfs(res, [(0.0833333, 1), (0.1666667, 1), (0.25, 1), (0.3333333, 2),
                               (0.4166667, 0), (0.5, 1), (0.5833333, 0), (0.6666667, 0),
                               (0.75, 0), (0.8333333, 0), (0.9166667, 0), (1.0, 1)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=12, max_missing=0.1)
        self.compare_sfs(res, [(0.0833333, 1), (0.1666667, 2), (0.25, 2), (0.3333333, 2),
                               (0.4166667, 0), (0.5, 1), (0.5833333, 0), (0.6666667, 1),
                               (0.75, 0), (0.8333333, 0), (0.9166667, 1), (1.0, 1)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=12, max_missing=0.2)
        self.compare_sfs(res, [(0.0833333, 1), (0.1666667, 3), (0.25, 2), (0.3333333, 2),
                               (0.4166667, 0), (0.5, 1), (0.5833333, 0), (0.6666667, 1),
                               (0.75, 0), (0.8333333, 0), (0.9166667, 1), (1.0, 1)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='folded', nbins=4)
        self.compare_sfs(res, [(0.125, 3), (0.25, 1), (0.375, 2), (0.5, 1)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='folded', nbins=4, max_missing=0.199)
        self.compare_sfs(res, [(0.125, 5), (0.25, 2), (0.375, 3), (0.5, 1)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='folded', nbins=4, max_missing=1)
        self.compare_sfs(res, [(0.125, 6), (0.25, 2), (0.375, 3), (0.5, 1)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=16)
        self.compare_sfs(res, [(0.0625, 1), (0.125, 1), (0.1875, 0), (0.25, 1),
                               (0.3125, 2), (0.375, 0), (0.4375, 0), (0.50, 1),
                               (0.5625, 0), (0.625, 0), (0.6875, 0), (0.75, 0),
                               (0.8125, 0), (0.875, 0), (0.9375, 0), (1.00, 1)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=16, max_missing=0.1)
        self.compare_sfs(res, [(0.0625, 1), (0.125, 2), (0.1875, 0), (0.25, 2),
                               (0.3125, 2), (0.375, 0), (0.4375, 0), (0.50, 1),
                               (0.5625, 0), (0.625, 0), (0.6875, 1), (0.75, 0),
                               (0.8125, 0), (0.875, 0), (0.9375, 1), (1.00, 1)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=16, max_missing=0.2)
        self.compare_sfs(res, [(0.0625, 1), (0.125, 3), (0.1875, 0), (0.25, 2),
                               (0.3125, 2), (0.375, 0), (0.4375, 0), (0.50, 1),
                               (0.5625, 0), (0.625, 0), (0.6875, 1), (0.75, 0),
                               (0.8125, 0), (0.875, 0), (0.9375, 1), (1.00, 1)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='folded', nbins=16)
        self.compare_sfs(res, [(0.03125, 2), (0.0625, 0), (0.09375, 0), (0.125, 1),
                               (0.15625, 0), (0.1875, 0), (0.21875, 1), (0.250, 0),
                               (0.28125, 0), (0.3125, 2), (0.34375, 0), (0.375, 0),
                               (0.40625, 0), (0.4375, 0), (0.46875, 0), (0.500, 1)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='folded', nbins=16, max_missing=0.1)
        self.compare_sfs(res, [(0.03125, 2), (0.0625, 0), (0.09375, 0), (0.125, 3),
                               (0.15625, 0), (0.1875, 0), (0.21875, 1), (0.250, 1),
                               (0.28125, 0), (0.3125, 2), (0.34375, 1), (0.375, 0),
                               (0.40625, 0), (0.4375, 0), (0.46875, 0), (0.500, 1)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='folded', nbins=16, max_missing=0.2)
        self.compare_sfs(res, [(0.03125, 2), (0.0625, 0), (0.09375, 0), (0.125, 4),
                               (0.15625, 0), (0.1875, 0), (0.21875, 1), (0.250, 1),
                               (0.28125, 0), (0.3125, 2), (0.34375, 1), (0.375, 0),
                               (0.40625, 0), (0.4375, 0), (0.46875, 0), (0.500, 1)])

    def test_fixed(self):
        res = egglib.stats.SFS(self.sites1, skip_fixed=True)
        self.assertEqual(res, [None, 3, 3, 1, 0, 0, 1, 2])

        res = egglib.stats.SFS(self.sites1, mode='folded', skip_fixed=True)
        self.assertEqual(res, [None, 3, 3, 1, 0, 0, 1, 2])

        res = egglib.stats.SFS(self.sites2, struct=self.struct2, mode='unfolded', skip_fixed=True)
        self.assertEqual(res, [None, 2, 3, 1, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 1, None])

        res = egglib.stats.SFS(self.sites1, nbins=10, skip_fixed=True)
        self.compare_sfs(res, [(0.05, 0), (0.10, 3), (0.15, 3), (0.20, 1),
                               (0.25, 0), (0.30, 0), (0.35, 0), (0.40, 1),
                               (0.45, 0), (0.50, 2)])

        res = egglib.stats.SFS(self.sites5, struct=self.struct5, mode='unfolded', nbins=4, max_missing=0.2, skip_fixed=True)
        self.compare_sfs(res, [(0.25, 5), (0.5, 3), (0.75, 1), (1.0, 1)])
