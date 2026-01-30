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

import os, egglib, unittest, pathlib
path = pathlib.Path(__file__).parent / '..' / 'data'

class Seq_Manip_test(unittest.TestCase):
    def test_rc_T(self):
        sequence='AATTGGCCACGACG'
        rc_sequence=egglib.tools.rc(sequence)
        self.assertEqual(rc_sequence, 'CGTCGTGGCCAATT')
        seq = 'AGGCGaCGCGCATATTAGAGACCGCGatccg'
        self.assertEqual(egglib.tools.rc(seq), 'cggatCGCGGTCTCTAATATGCGCGtCGCCT')
        aln = egglib.Align.create([('no name', seq)], egglib.alphabets.DNA)
        self.assertEqual(egglib.tools.rc(aln.get_sequence(0)), 'CGGATCGCGGTCTCTAATATGCGCGTCGCCT')
        aln2 = egglib.Align.create([('no name', seq)], egglib.alphabets.Alphabet('char', 'ACGT', [], case_insensitive=True))
        self.assertEqual(egglib.tools.rc(aln2.get_sequence(0)), 'CGGATCGCGGTCTCTAATATGCGCGTCGCCT')
        aln4 = egglib.Align.create([('no name', ['A', 'CT', 'A', 'A', 'GGG', 'CT', 'A', 'GGG', 'A'])], egglib.alphabets.Alphabet('string', ['A', 'CT', 'GGG'], []))
        self.assertEqual(egglib.tools.rc(aln4.get_sequence(0)), 'TCCCTAGCCCTTAGT')

    def test_rc_E(self):
        sequence='AAROPGGCCACGACG'
        with self.assertRaises(ValueError):
            rc_sequence=egglib.tools.rc(sequence)

        aln3 = egglib.Align.create([('no name', [12, 14, 31, 62, 12, 14])], egglib.alphabets.Alphabet('range', [0, 100], [-1, 0]))
        with self.assertRaises(ValueError):
            egglib.tools.rc(aln3.get_sequence(0))

        aln5 = egglib.Align.create([('no name', ['A', 'CT', 'A', 'A', 'CT', 'A', 'A'])], egglib.alphabets.Alphabet('custom', ['A', 'CT'], []))
        with self.assertRaises(ValueError):
            egglib.tools.rc(aln5.get_sequence(0))

    def test_compare_T(self):
        sequence1='AATTGGCCACGACG'
        sequence2='CGTCGTGGCCAATT'
        sequence3='AATTGGCCACGACG'
        self.assertFalse(egglib.tools.compare(sequence1, sequence2))
        self.assertTrue(egglib.tools.compare(sequence1, sequence3))
        seq1 = egglib.Align.create([('', sequence1)], egglib.alphabets.DNA)[0].sequence
        seq2 = egglib.Align.create([('', sequence2)], egglib.alphabets.DNA)[0].sequence
        seq3 = egglib.Align.create([('', sequence3)], egglib.alphabets.DNA)[0].sequence
        self.assertFalse(egglib.tools.compare(seq1, seq2))
        self.assertTrue(egglib.tools.compare(seq1, seq3))
        seq4 = egglib.Align.create([('', sequence1)], egglib.alphabets.Alphabet('string', ['A', 'C', 'G', 'T'], []))[0].sequence
        seq6 = egglib.Align.create([('', sequence3)], egglib.alphabets.DNA)[0].sequence
        self.assertFalse(egglib.tools.compare(seq4, sequence2))
        self.assertTrue(egglib.tools.compare(seq4, seq6))

    def test_compare_E(self):
        sequence1='AATTGGCCACGACG'
        sequence2='***rz*dzrfer*f'
        with self.assertRaises(ValueError):
            egglib.tools.compare(sequence1, sequence2)
        seq1a = egglib.Align.create([('', sequence1)], egglib.alphabets.DNA)[0].sequence
        seq1b = egglib.Align.create([('', sequence1)], egglib.alphabets.Alphabet('custom', ['A', 'C', 'G', 'T'], ''))[0].sequence
        with self.assertRaises(ValueError):
            egglib.tools.compare(seq1a, seq1b)


    def test_regex_T(self):
        sequence1='AATTGGCCACGACG'
        self.assertEqual(egglib.tools.regex(sequence1),'(AATTGGCCACGACG)')

    def test_regex_E(self):
        sequence1='***rz*dzrfer*f'
        with self.assertRaises(ValueError):
            egglib.tools.regex(sequence1)

    def test_motif_iter_T(self):
        sequence= 'GGTTCA-T-CTAAGAAC-TG-AC--GCATC-CCT---CG-T--C-T-TTCGA-GTA-GCGTCACTTCTG--TGTTAGG-GG-A--CGCAAG-C--\
CGAGTG--CGTGA--GG-GCGGTCGGC-CCGCGAAATTAACTCCA-GG-TGTACG-AT-GGTGCGT--GACCG-TAG--A--AGGAGA-CCCGTC\
GGGGCCTCT-G-TCGCA-CTAG-GCACT-ATCAG--CCCGTGCCGTGGGG-AAAGG-GCAAGACT--ACCTGGAACGACA-ACT-TCGTGGACTGTCT-\
TA--GC-C-TGGT--ATAGGAATG-T-C---CCCAGGCCCGACG-GCAGGTC-GTT-CTAATATGATGTAG'

        motifs=egglib.tools.motif_iter(sequence, 'GTC',mismatches=0, both_strands=False, case_independent=True, only_base=True)
        l_start=[59,116,187,284,338]
        l_stop=[62,119,190,287,341]
        i=0
        motifs = list(motifs)
        self.assertEqual(len(motifs), len(l_start))
        for hit, start, stop in zip(motifs, l_start, l_stop):
            self.assertEqual(hit[0], start)
            self.assertEqual(hit[1], stop)
            self.assertEqual(hit[2], '+')
            self.assertEqual(hit[3], 0)
            i=+1

        aln = egglib.Container.create([('', 'ATGATGATGATG')], alphabet=egglib.alphabets.DNA)
        motifs = egglib.tools.motif_iter(aln[0].sequence, 'CAT', both_strands=True)
        c = 0
        for start, stop, strand, num in motifs:
            self.assertEqual(start, c*3)
            self.assertEqual(stop, c*3+3)
            self.assertEqual(strand, '-')
            self.assertEqual(num, 0)
            c += 1
        self.assertEqual(c, 4)


    def test_motif_iter_E(self):
        sequence= "GGTTCAGTTCTAAGAACGTGAACAAGCATCTCCTAGTCGGTGTCGTGTTCGAT"
        mtf='GGTTCAGTTCTAAGAACGT'
        
        """
        motifs= egglib.tools.motif_iter(sequence, mtf ,mismatches=0, both_strands=False, case_independent=True,only_base=True)
        with self.assertRaises(ValueError):
            for a,b,c,d in motifs :print a,b,c,d
        """
        
        motifs=egglib.tools.motif_iter(sequence,"")
        with self.assertRaises(ValueError):
            for a,b,c,d in motifs: pass

        motifs=egglib.tools.motif_iter(sequence,'fdez5')
        with self.assertRaises(ValueError):
            for a,b,c,d in motifs: pass

    def test_ungap_T(self):
        f_name='sequence.fas'
        aln = egglib.io.from_fasta(str(path / f_name), labels=False, cls=egglib._interface.Align, alphabet=egglib.alphabets.DNA)
        aln_ugp=egglib.tools.ungap(aln, freq=0.2)
        self.assertIsInstance(aln_ugp, egglib.Align)
        self.assertNotEqual(aln.get_sequence(0).string(),aln_ugp.get_sequence(0).string())
        cnt_ugp=egglib.tools.ungap_all(aln, gaps=['-'])
        self.assertIsInstance(cnt_ugp, egglib.Container)
        self.assertNotEqual(aln.get_sequence(0).string(),cnt_ugp.get_sequence(0).string())
        self.assertRegex(aln.get_sequence(0).string(), '-')
        self.assertNotRegex(cnt_ugp.get_sequence(0).string(), '-')
        aln_ugp=egglib.tools.ungap(aln, freq=0.0, gaps=['-'])
        self.assertIsInstance(aln_ugp, egglib.Align)
        self.assertNotEqual(aln.get_sequence(0).string(),aln_ugp.get_sequence(0).string())
        self.assertRegex(aln.get_sequence(0).string(), '-')
        self.assertNotRegex(aln_ugp.get_sequence(0).string(), '-')
        aln_ugp=egglib.tools.ungap(aln, freq=1.0, gaps=['-'])
        self.assertIsInstance(aln_ugp, egglib.Align)
        self.assertEqual(aln.get_sequence(0).string(),aln_ugp.get_sequence(0).string())

    def test_ungap_E(self):
        f_name='sequence.fas'
        aln = egglib.io.from_fasta(str(path / f_name), labels=False, cls=egglib._interface.Align, alphabet=egglib.alphabets.DNA)
        cnt = egglib.io.from_fasta(str(path / f_name), labels=False, cls=egglib._interface.Container, alphabet=egglib.alphabets.DNA)
        with self.assertRaises(TypeError):
            aln_ugp=egglib.tools.ungap_all(aln, gaps='-')
        with self.assertRaises(ValueError):
            aln_ugp=egglib.tools.ungap_all(aln, gaps=[])
        with self.assertRaises(TypeError):
            aln_ugp=egglib.tools.ungap_all(cnt)
        with self.assertRaises(ValueError):
            aln_ugp=egglib.tools.ungap_all(aln, gaps=['X'])
        with self.assertRaises(ValueError):
            aln_ugp=egglib.tools.ungap(aln, freq=-10, gaps=['-'])
        with self.assertRaises(ValueError):
            aln_ugp=egglib.tools.ungap(aln, freq=10, gaps=['-'])
        aln.reset()
        with self.assertRaises(ValueError):
            aln_ugp=egglib.tools.ungap(aln, freq=0.5)

    def test_ungap(self):
        sequences = [
            ('name1', 'AGTGTAACGCCACCGTG-'),
            ('name2', 'AG-GTAAC-CCAC-GTG-'),
            ('name3', 'AG-GTAA--CCACCGTG-'),
            ('name4', 'AG-GTAA--CCACC-TGC')]

        aln = egglib.Align.create(sequences, alphabet=egglib.alphabets.DNA)
        self.assertEqual(aln.get_sequence(0).string(), 'AGTGTAACGCCACCGTG-')
        self.assertEqual(aln.get_sequence(1).string(), 'AG-GTAAC-CCAC-GTG-')
        self.assertEqual(aln.get_sequence(2).string(), 'AG-GTAA--CCACCGTG-')
        self.assertEqual(aln.get_sequence(3).string(), 'AG-GTAA--CCACC-TGC')

        cds = egglib.tools.to_codons(aln)
        self.assertEqual(cds.get_sequence(0).string(), 'AGTGTAACGCCACCGTG-')
        self.assertEqual(cds.get_sequence(1).string(), 'AG-GTAAC-CCAC-GTG-')
        self.assertEqual(cds.get_sequence(2).string(), 'AG-GTAA--CCACCGTG-')
        self.assertEqual(cds.get_sequence(3).string(), 'AG-GTAA--CCACC-TGC')

        aln2 = egglib.tools.ungap(aln, freq=0.5)
        self.assertEqual(aln2.get_sequence(0).string(), 'AGGTAACCCACCGTG')
        self.assertEqual(aln2.get_sequence(1).string(), 'AGGTAACCCAC-GTG')
        self.assertEqual(aln2.get_sequence(2).string(), 'AGGTAA-CCACCGTG')
        self.assertEqual(aln2.get_sequence(3).string(), 'AGGTAA-CCACC-TG')

        cds2 = egglib.tools.ungap(cds, freq=0.5)
        self.assertEqual(cds2.get_sequence(0).string(), 'GTACCACCG')
        self.assertEqual(cds2.get_sequence(1).string(), 'GTACCAC-G')
        self.assertEqual(cds2.get_sequence(2).string(), 'GTACCACCG')
        self.assertEqual(cds2.get_sequence(3).string(), 'GTACCACC-')

        sequences = [
            ('name1', [ 1, 2, 3, 4, 5, 0, 7, 0, 0]),
            ('name2', [-1, 0, 3, 4,-1, 6, 7, 8, 0]),
            ('name3', [-1, 0, 3, 4, 0, 0, 7, 8, 0]),
            ('name4', [-1, 0, 3, 4, 0, 6, 7, 8, 9])]

        alph = egglib.alphabets.Alphabet('range', [1, 100], [None, 1])
        aln = egglib.Align.create(sequences, alphabet=alph)
        self.assertEqual(list(aln.get_sequence(0)), [ 1, 2, 3, 4, 5, 0, 7, 0, 0])
        self.assertEqual(list(aln.get_sequence(1)), [-1, 0, 3, 4,-1, 6, 7, 8, 0])
        self.assertEqual(list(aln.get_sequence(2)), [-1, 0, 3, 4, 0, 0, 7, 8, 0])
        self.assertEqual(list(aln.get_sequence(3)), [-1, 0, 3, 4, 0, 6, 7, 8, 9])

        with self.assertRaises(ValueError):
            res = egglib.tools.ungap(aln, freq=0.5)

        res = egglib.tools.ungap(aln, freq=0.5, gaps=[0])
        self.assertEqual(list(res.get_sequence(0)), [ 1, 3, 4, 5, 0, 7, 0])
        self.assertEqual(list(res.get_sequence(1)), [-1, 3, 4,-1, 6, 7, 8])
        self.assertEqual(list(res.get_sequence(2)), [-1, 3, 4, 0, 0, 7, 8])
        self.assertEqual(list(res.get_sequence(3)), [-1, 3, 4, 0, 6, 7, 8])

        res = egglib.tools.ungap(aln, freq=0.5, gaps=[0, -1])
        self.assertEqual(list(res.get_sequence(0)), [3, 4, 0, 7, 0])
        self.assertEqual(list(res.get_sequence(1)), [3, 4, 6, 7, 8])
        self.assertEqual(list(res.get_sequence(2)), [3, 4, 0, 7, 8])
        self.assertEqual(list(res.get_sequence(3)), [3, 4, 6, 7, 8])
