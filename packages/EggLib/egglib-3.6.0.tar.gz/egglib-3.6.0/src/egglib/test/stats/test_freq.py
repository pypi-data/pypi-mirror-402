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

class Freq_test(unittest.TestCase):
    def test_Freq_T(self):
        freq=egglib.Freq()
        self.assertEqual(str(type(freq)), "<class 'egglib._freq.Freq'>")
        
    def test_process_site_T(self):
        freq=egglib.Freq()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        site=egglib.Site()
        site.from_align(aln, 2213)
        na_b= freq.num_alleles
        freq.from_site(site)
        na_a= freq.num_alleles
        self.assertTrue(na_a>na_b)

    def test_from_site_E(self):
        freq=egglib.Freq()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        sub = aln.subset(range(10,20))
        struct=egglib.struct_from_labels(aln)
        site=egglib.Site()
        site.from_align(sub, 20)

        with self.assertRaises(ValueError):
            freq.from_site(site, struct=struct)

        site.from_align(aln, 2213)
        freq.from_site(site, struct=struct)

        a, b = struct.as_dict()
        a[None][None]['ERROR'] = (100,)
        struct = egglib.struct_from_dict(a, b)
        with self.assertRaises(ValueError):
            freq.from_site(site, struct=struct)

    def test_from_list_T(self):
        freq=egglib.Freq()
        self.assertEqual(freq.num_alleles, 0)
        my_list=[[[84, 16, 32],[ 7, 28,  0],[ 0,  0, 14],[12, 64,  5]]]
        freq.from_list(my_list, None)
        self.assertEqual(freq.num_alleles, 3)
        self.assertEqual(str(type(freq)), "<class 'egglib._freq.Freq'>")

    def test_from_list_E(self):
        freq=egglib.Freq()
        my_list=[[[84, 16, 32],[ 7, 28,  0],[ 0,  0, 14]]]
        freq.from_list(my_list, None)
        with self.assertRaises(ValueError):
            freq.from_list(my_list, [])
        with self.assertRaises(ValueError):
            my_list=[[[2, 5, 3], [1, 1, 8,5,6], [2, 5, 1]],[[11, 1, 0,10], [4, 0, 0]]]
            freq.from_list(my_list, None)
        with self.assertRaises(ValueError):
            my_list=[]
            freq.from_list(my_list, None)
        with self.assertRaises(ValueError):
            my_list=[[[84, 16, 32],[ 7, 28,  0],[ 0,  0, 14]]]
            freq.from_list(my_list, None, geno_list=[(0, 0), (0, 2), (2, 0), (2, 2)])
        with self.assertRaises(ValueError):
            my_list=[[[2, 5, 3], [1, 1, 8], [2, 5, 1]],[[11, 1, 0], [4, 0, 0]]]
            geno_lst=[(0,0), (0,2,0), (2,0,2)]
            freq.from_list(my_list, None, geno_list=geno_lst)
        with self.assertRaises(ValueError):
            my_list=[[[2, 5, 3], [1, 1, 8], [2, 5, 1]],[[11, 1, 0], [4, 0, 0]]]
            geno_lst=[(), (), ()]
            freq.from_list(my_list, None, geno_list=geno_lst)
        with self.assertRaises(ValueError):
            geno_lst=[(0,2), (0,2), (0,2)]
            freq.from_list(my_list, None, geno_list=geno_lst)

    def test_from_vcf_T(self):
        freq=egglib.Freq()
        vcf = egglib.io.VcfParser(str(path / 'example1.vcf'))
        na_b= freq.num_alleles
        for i, v in enumerate(vcf):
            freq.from_vcf(vcf)
            na_a= freq.num_alleles
        self.assertEqual(str(type(freq)), "<class 'egglib._freq.Freq'>")
        self.assertTrue(na_a>na_b)

    def test_from_vcf_E(self):
        freq=egglib.Freq()
        vcf = egglib.io.VcfParser(str(path / 'exemple1_F.vcf'))
        na_b= freq.num_alleles
        with self.assertRaises(ValueError):
            for i, v in enumerate(vcf):
                freq.from_vcf(vcf)

    def test_ploidy_T(self):
        freq=egglib.Freq()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        site=egglib.Site()
        site.from_align(aln, 2213)
        freq.from_site(site)
        self.assertEqual(freq.ploidy,1)

    def test_num_alleles_T(self):
        freq=egglib.Freq()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        site=egglib.Site()
        site.from_align(aln, 2213)
        freq.from_site(site)
        self.assertEqual(freq.num_alleles,2)

    def test_num_genotypes_T(self):
        freq=egglib.Freq()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        site=egglib.Site()
        site.from_align(aln, 2213)
        freq.from_site(site)
        self.assertEqual(freq.num_genotypes, 2)

    def test_num_clusters_T(self):
        freq=egglib.Freq()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        site=egglib.Site()
        site.from_align(aln, 2213)
        freq.from_site(site)
        self.assertEqual(freq.num_clusters, 1)
    
    def test_num_populations_T(self):
        freq=egglib.Freq()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        site=egglib.Site()
        site.from_align(aln, 2213)
        freq.from_site(site)
        self.assertEqual(freq.num_populations, 1)
        
    def test_genotype_T(self):
        my_list=[[[2, 5, 3], [1, 1, 8], [2, 5, 1]],[[11, 1, 0], [4, 0, 0]]]
        freq = egglib.freq_from_list(my_list, [7, 4, 1], geno_list=[(0, 0), (0, 2), (2, 2)], alphabet=egglib.alphabets.positive_infinite)
        self.assertEqual(freq.genotype(2), (2,2))

    def test_genotype_E(self):
        my_list=[[[2, 5, 3], [1, 1, 8], [2, 5, 1]],[[11, 1, 0], [4, 0, 0]]]
        freq = egglib.freq_from_list(my_list, [7, 4, 1],geno_list=[(0, 0), (0, 2), (2, 2)], alphabet=egglib.alphabets.positive_infinite)
        with self.assertRaises(IndexError):
            freq.genotype(100)

    def test_freq_allele_T(self):
        my_list=[[[2, 5, 3], [1, 1, 8], [2, 5, 1]],[[11, 1, 0], [4, 0, 0]]]
        freq = egglib.freq_from_list(my_list, [7, 4, 1],geno_list=[(0, 0), (0, 2), (2, 2)], alphabet=egglib.alphabets.positive_infinite)
        self.assertEqual(freq.freq_allele(0),52)
        
    def test_freq_allele_E(self):
        my_list=[[[2, 5, 3], [1, 1, 8], [2, 5, 1]],[[11, 1, 0], [4, 0, 0]]]
        freq = egglib.freq_from_list(my_list, [7, 4, 1],geno_list=[(0, 0), (0, 2), (2, 2)], alphabet=egglib.alphabets.positive_infinite)
        with self.assertRaises(IndexError):
            freq.freq_allele(100)
        
    def test_freq_genotype_T(self):
        my_list=[[[2, 5, 3], [1, 1, 8], [2, 5, 1]],[[11, 1, 0], [4, 0, 0]]]
        freq = egglib.freq_from_list(my_list, [7, 4, 1],geno_list=[(0, 0), (0, 2), (2, 2)], alphabet=egglib.alphabets.positive_infinite)
        self.assertEqual(freq.freq_genotype(0),20)

    def test_freq_genotype_E(self):
        my_list=[[[2, 5, 3], [1, 1, 8], [2, 5, 1]],[[11, 1, 0], [4, 0, 0]]]
        freq = egglib.freq_from_list(my_list, [7, 4, 1],geno_list=[(0, 0), (0, 2), (2, 2)], alphabet=egglib.alphabets.positive_infinite)
        with self.assertRaises(IndexError):
            freq.freq_genotype(100)

    def test_eff_samples_T(self):
        freq = egglib.Freq()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        site = egglib.Site()
        site.from_align(aln, 2213)
        freq.from_site(site, struct=egglib.struct_from_labels(aln))
        self.assertEqual(freq.nseff(), 44)
        self.assertEqual(freq.nieff(), 44)
        self.assertEqual(freq.ploidy, 1)
        d = {}
        for i in range(28):
            d[str(i)] = [i*2, i*2+1]
        struct = egglib.struct_from_dict({None: {None: d}}, {})
        freq.from_site(site, struct=struct)
        self.assertEqual(freq.nseff(), 43)
        self.assertEqual(freq.nieff(), 16)
        self.assertEqual(freq.ploidy, 2)

    def test_freq(self):
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        site = egglib.site_from_align(aln, 360)
        frq = egglib.freq_from_site(site)
        alleles = []
        array = site.as_list()
        for i in array:
            if i not in alleles: alleles.append(i)

        self.assertEqual(frq.num_alleles, len(alleles))
        self.assertEqual(frq.num_genotypes, len(alleles))
        self.assertEqual(frq.ploidy, 1)
        self.assertEqual([frq.freq_allele(i) for i in range(frq.num_alleles)], [array.count(i) for i in alleles])
        self.assertEqual([frq.freq_genotype(i) for i in range(frq.num_genotypes)], [array.count(i) for i in alleles])
        self.assertEqual([frq.allele(i) for i in range(frq.num_alleles)], alleles)
        self.assertEqual([frq.genotype(i) for i in range(frq.num_genotypes)], list(map(tuple, alleles)))

        frq = egglib.freq_from_list(
            [24, 12, 6],
            [1, 0, 0],
            geno_list = [('A', 'A'), ('A', 'C'), ('C', 'C')],
            alphabet = egglib.alphabets.DNA)

        try:
            frq = egglib.freq_from_list(
                [[[14, 6], [3, 46]]],
                [0, 0], alphabet=egglib.alphabets.Alphabet('int', [0], []))
        except ValueError:
            pass
        else:
            raise AssertionError

        frq = egglib.freq_from_list(
            [[[24, 12, 6], [5, 15, 7]]],
            [1, 0, 0],
            geno_list = [('A', 'A'), ('A', 'C'), ('C', 'C')],
            alphabet = egglib.alphabets.DNA)

        self.assertEqual(frq.num_alleles, 2)
        self.assertEqual(frq.num_genotypes, 3)
        self.assertEqual(frq.ploidy, 2)
        self.assertEqual([frq.freq_allele(i) for i in range(frq.num_alleles)], [(24+5)*2 + (12+15), (12+15) + (6+7)*2])
        self.assertEqual([frq.freq_genotype(i) for i in range(frq.num_genotypes)], [24+5, 12+15, 6+7])
        self.assertEqual([frq.allele(i) for i in range(frq.num_alleles)], ['A', 'C'])
        self.assertEqual([frq.genotype(i) for i in range(frq.num_genotypes)], [('A', 'A'), ('A', 'C'), ('C', 'C')])
