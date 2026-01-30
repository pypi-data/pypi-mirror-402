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

class Clustal_test(unittest.TestCase):
    def test_clustal_T(self):
        cnt = egglib.io.from_fasta(str(path / 'cds.fas'), egglib.alphabets.DNA, labels=True)
        aln = egglib.wrappers.clustal(cnt, verbose=False, threads=8, keep_order=True)
        Lts_cnt=cnt.find('Lotus')
        Lts_aln=aln.find('Lotus')
        seq_cnt=Lts_cnt.sequence.string()
        seq_aln=Lts_aln.sequence.string()
        seq_=seq_aln.replace("-","")
        n_miss=seq_aln.count('-')
            
        self.assertIsInstance(aln, egglib.Align)
        self.assertNotEqual(len(seq_cnt), len(seq_aln))
        self.assertEqual(len(seq_cnt), (len(seq_aln)-n_miss))
        self.assertEqual(seq_, seq_cnt)

    def test_clustal_E(self):
        cnt = egglib.io.from_fasta(str(path / 'cds.fas'), egglib.alphabets.DNA, labels=True)
        cache = egglib.wrappers.paths['clustal']
        egglib.wrappers.paths['clustal'] = None
        with self.assertRaises(RuntimeError):
            aln = egglib.wrappers.clustal(cnt, verbose=False, threads=8, keep_order=True)
        egglib.wrappers.paths['clustal'] = cache

        cnt_ref = egglib.io.from_fasta(str(path / 'cds.fas'), egglib.alphabets.DNA, cls=None)
        with self.assertRaises(TypeError):
            aln = egglib.wrappers.clustal(cnt, ref=cnt_ref, verbose=False, threads=8, keep_order=True)

        aln_e = egglib.io.from_fasta(str(path / 'error.fas'), egglib.alphabets.DNA, cls=egglib.Align) #empty file
        with self.assertRaises(ValueError):
            aln = egglib.wrappers.clustal(cnt_ref, ref=aln_e, verbose=False, threads=8, keep_order=True)
        
        cnt=egglib.io.from_fasta(str(path / 'cds_e.fas'), egglib.alphabets.DNA, labels=True)
        with self.assertRaises(ValueError):
            aln = egglib.wrappers.clustal(cnt, verbose=False, threads=8, keep_order=True)
        
        aln_e = egglib.io.from_fasta(str(path / 'error.fas'), egglib.alphabets.DNA, cls=egglib.Align) #empty file
        with self.assertRaises(ValueError):
            aln = egglib.wrappers.clustal(aln_e, verbose=False, threads=8, keep_order=True)

        aln_ref = egglib.io.from_fasta(str(path / 'cds_clust.fas'), egglib.alphabets.DNA, cls=egglib.Align) #empty file
        with self.assertRaises(ValueError):
            aln = egglib.wrappers.clustal(aln_e, ref=aln_ref, verbose=False, threads=8, keep_order=True)

        Lts_cnt=['e', 'r', 'r', 'o', 'r']
        with self.assertRaises(AttributeError):
            aln = egglib.wrappers.clustal(Lts_cnt,verbose=False, threads=8, keep_order=True)

        cnt = egglib.io.from_fasta(str(path / 'cds.fas'), egglib.alphabets.DNA, labels=True)

        with self.assertRaises(ValueError):
                aln= egglib.wrappers.clustal(cnt,verbose=False, threads=8, use_kimura=True, keep_order=True)
        
        with self.assertRaises(ValueError):
                aln= egglib.wrappers.clustal(cnt ,verbose=False, num_iter=-10, threads=8)

        with self.assertRaises(ValueError):
                aln= egglib.wrappers.clustal(cnt ,verbose=False, num_iter='100', threads=8)

        with self.assertRaises(ValueError):
                aln= egglib.wrappers.clustal(cnt ,verbose=False, threads=-8)


        aln_ref = egglib.io.from_fasta(str(path / 'codon_align.fas'), egglib.alphabets.DNA)
        with self.assertRaises(RuntimeError):
            aln = egglib.wrappers.clustal(cnt, ref=aln_ref, verbose=False, threads=8, keep_order=True)

    def test_clustal_prot(self):
        c1 = egglib.io.from_fasta(str(path / 'cds.fas'), egglib.alphabets.DNA, labels=True)
        c2 = egglib.io.from_fasta(str(path / 'prot_data.fas'), alphabet=egglib.alphabets.protein)
        a1 = egglib.wrappers.clustal(c1)
        a2 = egglib.wrappers.clustal(c2)
