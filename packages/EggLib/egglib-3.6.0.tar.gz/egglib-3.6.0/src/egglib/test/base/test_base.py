"""
    Copyright 2024 Thomas Coudoux, Stéphane De Mita, Mathieu Siol

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

import os, egglib, sys, unittest, random, re, gc, time, collections, time, tempfile
path = os.path.dirname(__file__)
path_T=os.path.join(path, '..', 'data')

list_smpl_I0=[('name1',   'AAAAAAAAAAAAA', ['1','1']), ('name2', 'AGCGTTGAGCGTG',     ['0','0']), ('name3', 'AAGCTTGCGAGTG',     ['0','0'])]
list_smpl_I1=[('name1',   'GAAAAAAAAGGAA', ['0','0']), ('name2', 'AAGAAAGCGAGTG',     ['0','0']), ('name3', 'AAGCTTGCGGGTG',     ['0','1']), ('name4', 'CCCAAAGCGAGTG',     ['0','1']), ('name5', 'AAGCTTGCGAGTG',     ['0','1']), ('name6', 'GAAAAAGTCAAAA',     ['1','2'])]
list_smpl_I2=[('name1',   'GAAAAAAAAGGAA', ['0','0']), ('name2', 'AAGAAAGCGAGTG',     ['0','0']), ('name3', 'AAGCTTGCGGGTG',     ['0','1']), ('name4', 'CCCAAAGCGAGTG',     ['0','1']), ('name5', 'AAGCTTGCGAGTG',     ['0','1']), ('name6', 'GAAAAAGGGAAAA',     ['1','2'])]
list_smpl_I3=[('name1',   'GAAAAAAAAGGAA', ['0','0']), ('name2', 'AAGAAAGCGAGTG',     ['0','0']), ('name3', 'AAGCTTGCGGGTG',     ['0','1']), ('name4', 'CCCAAAGCGAGTG',     ['0','1']), ('name5', 'AAGCTTGCGAGTG',     ['0','1']), ('name6', 'GAAAAAGTCAAAA',     ['1','2']), ('name7', 'GAAAAAAAAAAAG',     ['1','2']), ('name8', 'GAAACCCAAAAAA', ['1','2']), ('name9', 'AGCGTTTTGCGTG', ['1','2']), ('name10', 'CAGCGTTGAGCGT', ['1','2']),('name11', 'AGCGTCCGGTCGT',     ['1','1'])]
list_smpl_I4=[('name1',   'GAAA---AAGGAA', ['0','0']), ('name2', 'AAGAAAGCGAGTG',     ['0','0']), ('name3', 'AAGCTTGCGGGTG',     ['0','1']), ('name4', 'CCCAAAGCGAGTG',     ['0','1']), ('name5', 'AAGCTTGCGAGTG',     ['0','1']), ('name6', 'GAAAAAGTCAAAA',     ['1','2']), ('name7', 'GAAAAAAAAAAAG',     ['1','2']), ('name8', 'GAAACCCAAAAAA', ['1','2']), ('name9', '----TTTTGCG--', ['1','2']), ('name10','CAGCGTTGAGCGT',  ['1','2']), ('name11','AGCGTCCGGTCGT',     ['1','1']), ('name12','AGGGG---CCCAA',   ['1','0']), ('name13','ANGGAAAAACCA?', ['2','1']), ('100%',  'AAAAAAAAAAAAA' , ['0','0']), ('090%',  'AAAAAAAAAAAA-',           ['0','0']), ('060%',  'AA--AANR-A--A', ['0','0']), ('020%',  '???????ASNAN-', ['0','0']), ('000%',  '---??????-?--', ['0','0'])]
list_out_1=[('outgroup1', 'AGGGGR---C--G', ['#','1']), ('outgroup2', 'SGGGGG---CCA?', ['#','0']), ('outgroup3', 'AGGGGR---C--G', ['#','0']), ('outgroup4', 'SGGGGG---CCA?', ['#','0']), ('outgroup5', 'GTAAGGGGCAATT', ['#','1']),  ('outgroup6', 'AAAAAAAAAAAAA', ['#','1']), ('outgroup7', 'GTAAAGGGGCATT', ['#','0']), ('A100%', 'AAAAAAAAAAAAA', ['#','1']), ('A090%', 'AAAAAAAAAAA--', ['#','1']), ('A060%', 'AANA-ARAAAA--',  ['#','0']), ('A020%',     '????AAAARNA?-', ['#','1']), ('A000%',     '---??-????-?-',['#','0']), ('B100%',     'AAAAAAAAAAAAA',['#','1']), ('B090%',     'AAAAAAAAAAA-A',['#','0']), ('B060%',     'AANA-ARAAAA-R', ['#','0']), ('B020%',     'AAA---ARNAT-A',['#','1']), ('B000%',     '---AAAG--A-AA',['#','1'])]
list_prot_I1=[('prot1',   'HYSCICQEPHVM',  ['1','1']),  ('prot2','LHVMTLRVYSAF',      ['1','2']), ('prot2','WDCHKEAIVMGG',       ['1','0']), ('prot4','IYGNGQLSAKMP',       ['0','0']), ('prot5','YDSYTSGNETFP',       ['1','0']), ('prot6','APPASGVLMTAM',       ['0','2']), ('prot7','LTEPLTDFHDVE',       ['0','1']), ('prot8','VRSPYMRYMPQP',   ['2','2'])]
list_prot_O1=[('o_prot1','FFVDMCGDITHY',   ['#','0']),  ('o_prot2','VYLRRQNWKNTP',    ['#','1'])]

class SampleView_test(unittest.TestCase):
    def setUp(self):
        self.aln = egglib.Align(egglib.alphabets.DNA)
        self.cnt = egglib.Container(egglib.alphabets.DNA)
        self.aln.add_samples(list_smpl_I0)
        self.cnt.add_samples(list_smpl_I1)
        self.aln.add_sample('name1',   'AAAAAAAAAAAAA')
        self.cnt.add_sample('outgroup', '?', ['0'])
        self.sAI0=self.aln.get_sample(0)   #sample aln
        self.sAO0=self.aln.get_sample(len(list_smpl_I0)) #outgroup aln
        self.sCI0=self.cnt.get_sample(0)   #sample cnt
        self.sCO0=self.cnt.get_sample(len(list_smpl_I1)) ##outgroup cnt

    def tearDown(self):
        self.aln.reset()
        self.cnt.reset()

    def test_object_aln_T(self):
        self.assertIsInstance(self.aln, egglib.Align)

    def test_object_aln_F(self):
        self.assertNotIsInstance(self.cnt, egglib.Align)

    def test_object_cnt_T(self):
        self.assertIsInstance(self.cnt, egglib.Container)

    def test_object_cnt_F(self):
        self.assertNotIsInstance(self.aln, egglib.Container)

    def test_ls_aln_T(self):
        self.assertEqual(self.sAI0.ls,13)
        self.assertNotEqual(self.sAI0.ls,11)
        self.assertEqual(self.sAO0.ls,13)
        self.assertNotEqual(self.sAO0.ls,11)

    def test_ls_cnt_T(self):
        self.assertEqual(self.sCI0.ls,13)
        self.assertNotEqual(self.sCI0.ls,11)
        self.assertEqual(self.sCO0.ls,1)
        self.assertNotEqual(self.sCO0.ls,13)

    def test_index_aln_T(self):
        self.assertEqual(self.sAI0.index, 0)
        self.assertEqual(self.sAO0.index, len(list_smpl_I0))

    def test_index_cnt_T(self):
        self.assertEqual(self.sCI0.index,0)
        self.assertEqual(self.sCO0.index,len(list_smpl_I1))

    def test_parent_aln_T(self):
        self.assertIsInstance(self.sAI0.parent, egglib.Align)
        self.assertNotIsInstance(self.sAO0.parent, egglib.Container)

    def test_parent_cnt_T(self):
        self.assertIsInstance(self.sCI0.parent, egglib.Container)
        self.assertNotIsInstance(self.sCO0.parent, egglib.Align)

    def test_name_aln_T(self):
        self.assertEqual(self.sAI0.name, 'name1')
        self.assertNotEqual(self.sAO0.name, 'outgroup')
        self.sAI0.name='nom1'
        self.sAO0.name='outgroup'
        self.assertEqual(self.sAI0.name, 'nom1')
        self.assertEqual(self.sAO0.name, 'outgroup')

    def test_name_cnt_T(self):
        self.assertEqual(self.sCI0.name, 'name1')
        self.assertNotEqual(self.sCO0.name, 'name1')
        self.sCI0.name='nom1'
        self.sCO0.name='outgroup1'
        self.assertEqual(self.sCI0.name, 'nom1')
        self.assertEqual(self.sCO0.name, 'outgroup1')

    def test_sequence_aln_T(self):
        self.assertEqual(self.sAI0.sequence.string(), 'AAAAAAAAAAAAA')
        self.assertNotEqual(self.sAO0.sequence.string(), 'AAGCTTGCGAGTG')
        self.sAI0.sequence='CCCCCCCCCCCCC'
        self.sAO0.sequence='AAGCTTGCGAGTG'
        self.assertEqual(self.sAI0.sequence.string(), 'CCCCCCCCCCCCC')
        self.assertEqual(self.sAO0.sequence.string(), 'AAGCTTGCGAGTG')

    def test_sequence_cnt_T(self):
        self.assertEqual(self.sCI0.sequence.string(), 'GAAAAAAAAGGAA')
        self.assertNotEqual(self.sCO0.sequence.string(), 'AAGCTTGCGAGTG')
        self.sCI0.sequence=['C','C','C','C','C','C','C','C','C','C','C','C','C']
        self.sCO0.sequence='GTAGGGGCATTCC'
        self.assertEqual(self.sCO0.sequence.string(), 'GTAGGGGCATTCC')
        self.assertEqual(self.sCI0.sequence.string(), 'CCCCCCCCCCCCC')

    def test_group_aln_T(self):
        self.assertIsInstance(self.sAI0.labels, egglib.LabelView)
        self.assertIsInstance(self.sAO0.labels, egglib.LabelView)
        self.sAI0.labels=['1','2']
        self.sAO0.labels=['1']
        self.assertEqual(self.aln.get_label(0,1), '2')
        self.assertEqual(self.aln.get_label(self.sAO0._index,0), '1')

    def test_labels_cnt_T(self):
        self.assertIsInstance(self.sCI0.labels, egglib.LabelView)
        self.assertIsInstance(self.sCO0.labels, egglib.LabelView)
        self.sCI0.labels=['1','1']
        self.sCO0.labels=['1']
        self.assertEqual(self.cnt.get_label(0,1), '1')
        self.assertEqual(self.cnt.get_label(self.sCO0._index,0), '1')

    def test_labels_cnt_E(self):
        with self.assertRaises(TypeError):
            self.sCO0.labels=[1]

    def test__getitem__aln_T(self):
        self.assertIsInstance(self.sAI0, egglib.SampleView)
        self.assertEqual(self.sAI0[0], 'name1')
        self.assertIsInstance(self.sAI0[1], egglib.SequenceView)
        self.assertIsInstance(self.sAI0[2], egglib.LabelView)
        self.assertIsInstance(self.sAO0, egglib.SampleView)
        self.assertEqual(self.sAO0[0], 'name1')
        self.assertIsInstance(self.sAO0[1], egglib.SequenceView)
        self.assertIsInstance(self.sAO0[2], egglib.LabelView)

    def test__getitem__aln_E(self):
        with self.assertRaises(IndexError):
            self.sAI0[3]
            self.sAO0[3]

    def test__getitem__cnt_T(self):
        self.assertIsInstance(self.sCI0, egglib.SampleView)
        self.assertEqual(self.sCI0[0], 'name1')
        self.assertIsInstance(self.sCI0[1], egglib.SequenceView)
        self.assertIsInstance(self.sCI0[2], egglib.LabelView)
        self.assertIsInstance(self.sCO0, egglib.SampleView)
        self.assertEqual(self.sCO0[0], 'outgroup')
        self.assertIsInstance(self.sCO0[1], egglib.SequenceView)
        self.assertIsInstance(self.sCO0[2], egglib.LabelView)

    def test__getitem__cnt_E(self):
        with self.assertRaises(IndexError):
            self.sCI0[3]
            self.sCO0[3]

    def test__iter__aln_T(self):
        self.assertIsInstance(self.sAI0, collections.abc.Iterable)
        self.assertIsInstance(self.sAO0, collections.abc.Iterable)

    def test__iter__cnt_T(self):
        self.assertIsInstance(self.sCI0, collections.abc.Iterable)
        self.assertIsInstance(self.sCO0, collections.abc.Iterable)

    def test_slices(self):
        for sam in self.cnt:
            sam.name, sam.sequence[:], sam.labels[0], sam.sequence[:50]
        for name, seq, lbl in self.cnt:
            seq[:]
        self.assertEqual(self.cnt[1].sequence[:], 'AAGAAAGCGAGTG')
        self.assertEqual(self.cnt[1].sequence[2:-2], 'GAAAGCGAG')
        for sam in self.cnt:
            sam[0], sam[1], sam[2]
        for name, seq, lbl in self.cnt:
            name, seq[:], sam.labels[0]

        name, seq, lbl = self.cnt[0]
        self.cnt[0][0], self.cnt[1], self.cnt[2]
        with self.assertRaisesRegex(ValueError, 'slices are not supported'):
            self.cnt[0][:]
        with self.assertRaisesRegex(ValueError, 'slices are not supported'):
            self.cnt[0][:2]
        with self.assertRaisesRegex(ValueError, 'slices are not supported'):
            self.cnt[0][:1]

class SequenceView_test(unittest.TestCase):
    def setUp(self):
        self.aln = egglib.Align(egglib.alphabets.DNA)
        self.cnt = egglib.Container(egglib.alphabets.DNA)
        self.aln.add_samples(list_smpl_I2)
        self.cnt.add_samples(list_smpl_I2)

        self.aln.add_sample('outgroup1', 'GTAGGGGCATTCC')
        self.aln.add_sample('outgroup2', 'GTAGGCCAAACAT')
        self.aln.add_sample('outgroup3', 'GTAGGGGCATTCC')

        self.cnt.add_sample('outgroup1', 'AAAAAAAAAAAAA')
        self.cnt.add_sample('outgroup2', 'CCGCGTTGAGCGT')
        self.cnt.add_sample('outgroup3', 'AGCGTTTTGCGTG')

        self.seqAI0=self.aln.get_sequence(0)
        self.seqAO1=self.aln.get_sequence(len(list_smpl_I2)+1)
        self.seqCI2=self.cnt.get_sequence(1)
        self.seqCO1=self.cnt.get_sequence(len(list_smpl_I2)+1)

    def tearDown(self):
        self.aln.reset()
        self.cnt.reset()

    def test_lower_upper_char(self):

        # generate random sequences
        num = 10 # number of sequences
        ls = 20  # ls of Align
        arrays = [], []
        for array in arrays:
            for i in range(num):
                seq = []
                for j in range(ls):
                    r = random.random()
                    if r < 0.85: seq.append(random.choice('ACGTacgt'))
                    else: seq.append(random.choice('Nn?-'))
                array.append(('', ''.join(seq)))
        alph = egglib.alphabets.Alphabet('char', 'ACGTacgt', '-Nn?', case_insensitive=False)
        aln = egglib.Align.create(arrays[0], alph)
        cnt = egglib.Container.create(arrays[1], alph)  # 16

        # aln / full sequence
        aln.get_sequence(0).lower(); self.assertEqual(aln.get_sequence(0).string(), arrays[0][0][1].lower())
        aln.get_sequence(1).upper(); self.assertEqual(aln.get_sequence(1).string(), arrays[0][1][1].upper())

        # aln / beginning of sequence
        STOP = random.randint(5, 18)
        aln.get_sequence(2).lower(stop=STOP); self.assertEqual(aln.get_sequence(2).string(), arrays[0][2][1][:STOP].lower()+arrays[0][2][1][STOP:])
        aln.get_sequence(3).upper(stop=STOP); self.assertEqual(aln.get_sequence(3).string(), arrays[0][3][1][:STOP].upper()+arrays[0][3][1][STOP:])

        # aln / end of sequence
        START = random.randint(2, 15)
        aln.get_sequence(4).lower(start=START); self.assertEqual(aln.get_sequence(4).string(), arrays[0][4][1][:START]+arrays[0][4][1][START:].lower())
        aln.get_sequence(5).upper(start=START); self.assertEqual(aln.get_sequence(5).string(), arrays[0][5][1][:START]+arrays[0][5][1][START:].upper())

        # aln / middle of sequence
        START = random.randint(2, 12)
        STOP = random.randint(START, 18)
        aln.get_sequence(6).lower(START, STOP); self.assertEqual(aln.get_sequence(6).string(), arrays[0][6][1][:START]+arrays[0][6][1][START:STOP].lower()+arrays[0][6][1][STOP:])
        aln.get_sequence(7).upper(START, STOP); self.assertEqual(aln.get_sequence(7).string(), arrays[0][7][1][:START]+arrays[0][7][1][START:STOP].upper()+arrays[0][7][1][STOP:])

        # aln / outgroup
        aln.get_sample(8).sequence.lower(); self.assertEqual(aln.get_sample(8).sequence.string(), arrays[0][8][1].lower())
        aln.get_sample(9).sequence.upper(); self.assertEqual(aln.get_sample(9).sequence.string(), arrays[0][9][1].upper())

        # from object
        aln.upper(0); self.assertEqual(aln.get_sequence(0).string(), arrays[0][0][1].upper())
        aln.upper(8); self.assertEqual(aln.get_sample(8).sequence.string(), arrays[0][8][1].upper())

        # cnt / full sequence
        cnt.get_sequence(0).lower(); self.assertEqual(cnt.get_sequence(0).string(), arrays[1][0][1].lower())
        cnt.get_sequence(1).upper(); self.assertEqual(cnt.get_sequence(1).string(), arrays[1][1][1].upper())

        # cnt / beginning of sequence
        STOP = random.randint(5, 18)
        cnt.get_sequence(2).lower(stop=STOP); self.assertEqual(cnt.get_sequence(2).string(), arrays[1][2][1][:STOP].lower()+arrays[1][2][1][STOP:])
        cnt.get_sequence(3).upper(stop=STOP); self.assertEqual(cnt.get_sequence(3).string(), arrays[1][3][1][:STOP].upper()+arrays[1][3][1][STOP:])

        # cnt / end of sequence
        START = random.randint(2, 15)
        cnt.get_sequence(4).lower(start=START); self.assertEqual(cnt.get_sequence(4).string(), arrays[1][4][1][:START]+arrays[1][4][1][START:].lower())
        cnt.get_sequence(5).upper(start=START); self.assertEqual(cnt.get_sequence(5).string(), arrays[1][5][1][:START]+arrays[1][5][1][START:].upper())

        # cnt / middle of sequence
        START = random.randint(2, 12)
        STOP = random.randint(START, 18)
        cnt.get_sequence(6).lower(START, STOP); self.assertEqual(cnt.get_sequence(6).string(), arrays[1][6][1][:START]+arrays[1][6][1][START:STOP].lower()+arrays[1][6][1][STOP:])
        cnt.get_sequence(7).upper(START, STOP); self.assertEqual(cnt.get_sequence(7).string(), arrays[1][7][1][:START]+arrays[1][7][1][START:STOP].upper()+arrays[1][7][1][STOP:])

        # cnt / outgroup
        cnt.get_sequence(8).lower(); self.assertEqual(cnt.get_sample(8).sequence.string(), arrays[1][8][1].lower())
        cnt.get_sequence(9).upper(); self.assertEqual(cnt.get_sample(9).sequence.string(), arrays[1][9][1].upper())

        # from object
        cnt.upper(0); self.assertEqual(cnt.get_sequence(0).string(), arrays[1][0][1].upper())
        cnt.upper(8); self.assertEqual(cnt.get_sample(8).sequence.string(), arrays[1][8][1].upper())

        # don't do anything
        cnt.lower(0, 18, 18); self.assertEqual(cnt.get_sequence(0).string(), arrays[1][0][1].upper())
        cnt.lower(0, 18, 0); self.assertEqual(cnt.get_sequence(0).string(), arrays[1][0][1].upper())

    def test_lower_upper_string(self):
        alleles = ['taa', 'TAA', 'Taa', 'tAA']
        missing = ['-', 'NNN', 'nnn']
        alph = egglib.alphabets.Alphabet('string', alleles, missing)

        aln = egglib.Align(alph)
        aln.add_sample('', [alleles[0], alleles[1], alleles[3], alleles[2]])   # taa TAA tAA Taa
        aln.add_sample('', [alleles[1], missing[0], missing[1], alleles[2]])   # TAA  -  NNN Taa
        aln.add_sample('', [alleles[2], missing[1], alleles[1], missing[1]]) # Taa NNN TAA NNN

        seq1 = aln.get_sequence(0)
        seq2 = aln.get_sequence(1)
        seq3 = aln.get_sequence(2)

        seq1.upper()
        seq2.lower()
        seq3.lower(1,3)

        self.assertEqual(seq1.string(), 'TAATAATAATAA')
        self.assertEqual(seq2.string(), 'taa-nnntaa')
        self.assertEqual(seq3.string(), 'TaannntaaNNN')

    def test_lower_upper_exceptions(self):
        # invalid type alphabet
        a1 = egglib.alphabets.Alphabet('int', [0, 1], [-1])
        aln1 = egglib.Align.create([('', [0,0,0,1]), ('', [0,0,1,1]), ('', [1,1,1,0]), ('', [1,0,1,1])], a1)
        with self.assertRaises(ValueError):
            aln1.get_sequence(0).lower()

        # case insensitive alphabet
        a2 = egglib.alphabets.Alphabet('string', ['ATG', 'GTA'], ['NNN'], case_insensitive=True)
        aln2 = egglib.Align.create([
            ('', ['ATG','ATG','ATG','GTA']), ('', ['ATG','ATG','GTA','GTA']), ('', ['GTA','GTA','GTA','ATG']), ('', ['GTA','ATG','GTA','GTA'])], a2)
        with self.assertRaises(ValueError):
            aln2.get_sequence(0).lower()

        # DNA (case insensitive)
        aln3 = egglib.Align.create([
           ('', 'ATGATGATGGTA'), ('', 'ATGATGGTAGTA'), ('', 'GTAGTAGTAATG'), ('', 'GTAATGGTAGTA')], egglib.alphabets.DNA)
        with self.assertRaises(ValueError):
            aln3.get_sequence(0).lower()

        # allele out of range
        a4 = egglib.alphabets.Alphabet('string', ['ATG', 'GTA', 'atg'], ['NNN', 'nnn'], case_insensitive=False)
        aln4 = egglib.Align.create([
            ('', ['ATG','ATG','ATG','GTA']), ('', ['ATG','ATG','GTA','GTA']), ('', ['GTA','GTA','GTA','ATG']), ('', ['GTA','ATG','GTA','GTA'])], a4)
        with self.assertRaises(ValueError):
            aln4.get_sequence(0).lower()

        # oob start / index / sample
        a5 = egglib.alphabets.Alphabet('string', ['ATG', 'GTA', 'atg', 'gta'], ['NNN', 'nnn'], case_insensitive=False)
        aln5 = egglib.Align.create([
            ('', ['ATG','ATG','ATG','GTA']), ('', ['ATG','ATG','GTA','GTA']), ('', ['GTA','GTA','GTA','ATG']), ('', ['GTA','ATG','GTA','GTA'])], a5)
        aln5.add_sample('', ['GTA', 'ATG', 'ATG', 'GTA'])
        with self.assertRaises(IndexError):
            aln5.get_sequence(0).lower(start=4)
        with self.assertRaises(IndexError):
            aln5.get_sequence(0).lower(start=-5)
        with self.assertRaises(IndexError):
            aln5.get_sequence(0).lower(stop=-5)
        with self.assertRaises(IndexError):
            aln5.lower(index=5)
        with self.assertRaises(IndexError):
            aln5.lower(index=-6)

        # positive control
        aln5.lower(index=0, start=-4, stop=18)
        aln5.lower(index=4)
        aln5.lower(index=-5)
        self.assertEqual(aln5.get_sequence(0).string(), 'atgatgatggta')
        self.assertEqual(aln5.get_sequence(4).string(), 'gtaatgatggta')

    def test_object_SequenceView_aln_T(self):
        self.assertIsInstance(self.seqAI0, egglib.SequenceView)
        self.assertIsInstance(self.seqAO1, egglib.SequenceView)

    def test_object_SequenceView_cnt_T(self):
        self.assertIsInstance(self.seqCI2, egglib.SequenceView)
        self.assertIsInstance(self.seqCO1, egglib.SequenceView)

    def test_string_aln_T(self):
        self.assertEqual(self.seqAI0.string(),'GAAAAAAAAGGAA')
        self.assertEqual(self.seqAO1.string(),'GTAGGCCAAACAT')

    def test_string_cnt_T(self):
        self.assertEqual(self.seqCI2.string(),'AAGAAAGCGAGTG')
        self.assertEqual(self.seqCO1.string(),'CCGCGTTGAGCGT')

    def test_insert_aln_E(self):
        with self.assertRaises(ValueError):
            self.seqAI0.insert(0,'GCGT')

    def test_insert_cnt_T(self):
        self.seqCI2.insert(0,'GCGT')
        self.assertEqual(self.seqCI2.string(),'GCGTAAGAAAGCGAGTG')
        self.seqCO1.insert(0,'GCGT')
        self.assertEqual(self.seqCO1.string(),'GCGTCCGCGTTGAGCGT')

    def test_find_aln_T(self):
        self.assertEqual(self.seqAI0.find('AG'),8)
        self.assertEqual(self.seqAO1.find('CC'),5)

    def test_find_cnt_T(self):
        self.assertEqual(self.seqCI2.find('GTG',6),10)
        self.assertEqual(self.seqCO1.find('TT',3,10),5)

    def test_strip_cnt_T(self):
        # test with standard DNA data
        cnt1 = egglib.Container(egglib.alphabets.DNA)
        cnt1.add_sample('', '--AA--CCGTGGCGCGA----ATTCCGG---AGANNN--')
        cnt1.add_sample('', '????A??-----nnnnCGCCCCGGAT----cccc-c-c?')
        cnt1.add_sample('', '??----N-GGGG--NN--')
        cnt1.add_sample('', '-----????----')
        cnt1.add_sample('', '?--GCC---TTA----???')
        cnt1.add_sample('', 'NnNGCC---TTAN')
        cnt1.add_sample('', '???GCC---TTA--')
        cnt1.add_sample('', 'NNNN---?')
        cnt1.get_sequence(0).strip(set('-n?'))
        cnt1.get_sequence(1).lstrip(set('-n?'))
        cnt1.get_sequence(2).rstrip(set('-N?'))
        cnt1.get_sequence(3).strip(set('-n?'))
        self.assertEqual(cnt1.get_sequence(0).string(), 'AA--CCGTGGCGCGA----ATTCCGG---AGA')
        self.assertEqual(cnt1.get_sequence(1).string(), 'A??-----NNNNCGCCCCGGAT----CCCC-C-C?')
        self.assertEqual(cnt1.get_sequence(2).string(), '??----N-GGGG')
        self.assertEqual(cnt1.get_sequence(3).string(), '')
        cnt1.get_sequence(4).strip('-n?')
        cnt1.get_sequence(5).lstrip('-n?')
        cnt1.get_sequence(6).rstrip('-N?')
        cnt1.get_sequence(7).strip('-n?')
        self.assertEqual(cnt1.get_sequence(4).string(), 'GCC---TTA')
        self.assertEqual(cnt1.get_sequence(5).string(), 'GCC---TTAN')
        self.assertEqual(cnt1.get_sequence(6).string(), '???GCC---TTA')
        self.assertEqual(cnt1.get_sequence(7).string(), '')

        # small test with integer values
        cnt2 = egglib.Container(egglib.alphabets.Alphabet('range', (1, 1000), (-10, 1)))
        cnt2.add_sample('', [0, 1, 5, 2, -1, 0])
        cnt2.add_sample('', [-2, 0, 3, 3, 0, -2])
        cnt2.get_sequence(0).lstrip([-2, -1, 0])
        cnt2.get_sequence(1).strip([-2, -1, 0])
        self.assertEqual(cnt2.get_sequence(0)[:], [1, 5, 2, -1, 0])
        self.assertEqual(cnt2.get_sequence(1)[:], [3, 3])

        # invalid type
        aln = egglib.Align(egglib.alphabets.DNA)
        aln.add_sample('', 'NNACCGTGTN')
        aln.add_sample('', 'NNACCGTGTN')
        with self.assertRaises(ValueError): aln.get_sequence(0).strip('N')
        with self.assertRaises(ValueError): aln.get_sequence(1).strip('N')

    def test__len__aln_T(self):
        self.assertEqual(len(self.seqAI0), 13)
        self.assertEqual(len(self.seqAO1), 13)

    def test__len__cnt_T(self):
        self.assertEqual(len(self.seqCI2), 13)
        self.assertEqual(len(self.seqCO1), 13)

    def test__getitem__aln_T(self):
        self.assertEqual(self.seqAI0[5], 'A')
        self.assertEqual(self.seqAI0[-2], 'A')
        self.assertEqual(self.seqAI0[1:10], 'AAAAAAAAG')
        self.assertEqual(self.seqAI0[1:-1],'AAAAAAAAGGA')
        self.assertEqual(self.seqAO1[5], 'C')
        self.assertEqual(self.seqAO1[-2], 'A')
        self.assertEqual(self.seqAO1[1:10],'TAGGCCAAA')
        self.assertEqual(self.seqAO1[1:-1],'TAGGCCAAACA')
        aln = egglib.Align(egglib.alphabets.codons)
        aln.add_sample('', ['ATG', 'CTA', 'GTA', 'TAG'])
        self.assertEqual(aln[0].sequence[:], 'ATGCTAGTATAG')
        aln = egglib.Align(egglib.alphabets.positive_infinite)
        aln.add_sample('', [400, 379, 272])
        self.assertEqual(aln[0].sequence[:], [400, 379, 272])

    def test__getitem__aln_E(self):
        with self.assertRaises(IndexError):
            self.seqAI0[100]
        with self.assertRaises(TypeError):
            self.seqAO1['FAIL']
        with self.assertRaises(IndexError):
            self.seqAI0[100]
        with self.assertRaises(TypeError):
            self.seqAO1['FAIL']

    def test__getitem__cnt_T(self):
        self.assertEqual(self.seqCI2[5],  'A')
        self.assertEqual(self.seqCI2[-2], 'T')
        self.assertEqual(self.seqCI2[1:10],'AGAAAGCGA')
        self.assertEqual(self.seqCI2[1:-1],'AGAAAGCGAGT')
        self.assertEqual(self.seqCO1[5],'T')
        self.assertEqual(self.seqCO1[-2], 'G')
        self.assertEqual(self.seqCO1[1:10],'CGCGTTGAG')
        self.assertEqual(self.seqCO1[1:-1],'CGCGTTGAGCG')

    def test__getitem__cnt_E(self):
        with self.assertRaises(IndexError):
            self.seqCI2[100]
        with self.assertRaises(TypeError):
            self.seqCO1['FAIL']
        with self.assertRaises(IndexError):
            self.seqCI2[100]
        with self.assertRaises(TypeError):
            self.seqCO1['FAIL']

    def test__setitem__aln__T(self):
        self.seqAI0[5]=    'C'
        self.assertEqual(self.seqAI0[5], 'C')
        self.seqAO1[5]= 'A'
        self.assertEqual(self.seqAO1[5], 'A')
        self.seqAI0[1:10]='AGCTTGCGG'
        self.assertEqual(self.seqAI0[1:10], 'AGCTTGCGG' )
        self.seqAO1[1:10]='CGCGTTGAG'
        self.assertEqual(self.seqAO1[1:10], 'CGCGTTGAG' )

    def test__setitem__aln_E(self):
        with self.assertRaises(ValueError):
            self.seqAI0[1:3]=['A','C','T']
        with self.assertRaises(TypeError):
            self.seqAO1['FAIL']='C'

    def test__setitem__cnt__T(self):
        self.assertEqual(self.seqCI2.string(), 'AAGAAAGCGAGTG')
        self.seqCI2[5]= 'C'
        self.assertEqual(self.seqCI2.string(), 'AAGAACGCGAGTG')
        self.seqCO1[5]= 'A'
        self.seqCI2[1:10]='AGCTTGCGG'
        self.assertEqual(self.seqCI2.string(), 'AAGCTTGCGGGTG')
        self.seqCI2[1:10]='AGCTTGCGTA'
        self.assertEqual(self.seqCI2.string(), 'AAGCTTGCGTAGTG')
        self.seqCI2[1:10]='AGCTTGC'
        self.assertEqual(self.seqCI2.string(), 'AAGCTTGCAGTG')
        self.seqCO1[1:10]='CGCGTTGAA'
        self.assertEqual(self.seqCO1[1:10], 'CGCGTTGAA' )
        self.seqCO1[1:10]='CGCGTTGACG'
        self.assertEqual(self.seqCO1[1:10], 'CGCGTTGAC' )
        self.seqCO1[1:10]='CGCGTTG'
        self.assertEqual(list(self.seqCO1[1:10]), list('CGCGTTGGC') )

    def test__setitem__cnt_E(self):
        with self.assertRaises(TypeError):
            self.seqAO1['FAIL']='C'

    def test__iter__aln__T(self):
        self.assertIsInstance(self.seqAI0, collections.abc.Iterable)
        self.assertIsInstance(self.seqAO1, collections.abc.Iterable)
        self.assertEqual(list(self.seqCI2), list('AAGAAAGCGAGTG'))

    def test__iter__cnt__T(self):
        self.assertIsInstance(self.seqCI2, collections.abc.Iterable)
        self.assertIsInstance(self.seqCO1, collections.abc.Iterable)

    def test__delitem__cnt__T(self):
        del self.seqCI2[0]
        self.assertEqual(self.seqCI2.string(),'AGAAAGCGAGTG')
        del self.seqCI2[0:3]
        self.assertEqual(self.seqCI2.string(),'AAGCGAGTG')
        del self.seqCI2[::2]
        self.assertEqual(self.seqCI2.string(),'ACAT')

    def test__delitem__cnt__E(self):
        with self.assertRaises(ValueError):
            del self.seqCO1[::-1]
        with self.assertRaises(TypeError):
            del self.seqCO1["ERROR"]

    def test__delitem__aln__E(self):
        with self.assertRaises(ValueError):
            del self.seqAI0[0]
        with self.assertRaises(ValueError):
            del self.seqAO1[0]

class LabelView_test(unittest.TestCase):
    def setUp(self):
        self.aln = egglib.Align(egglib.alphabets.DNA)
        self.cnt = egglib.Container(egglib.alphabets.DNA)

        self.aln.add_samples(list_smpl_I2)
        self.cnt.add_samples(list_smpl_I2)
        self.aln.add_sample('name1',   'AAAAAAAAAAAAA')
        self.cnt.add_sample('outgroup', '?', ['0'])

        self.gAI4=egglib.LabelView(self.aln,4)
        self.gCI5=egglib.LabelView(self.cnt,5)
        self.gAO0=egglib.LabelView(self.aln,-1)
        self.gCO0=egglib.LabelView(self.cnt,-1)

    def tearDown(self):
        self.aln.reset()
        self.cnt.reset()

    def test_object_LabelView_aln_T(self):
        self.assertIsInstance(self.gAO0, egglib.LabelView)
        self.assertIsInstance(self.gAI4, egglib.LabelView)
    def test_object_LabelView_cnt_T(self):
        self.assertIsInstance(self.gCO0, egglib.LabelView)
        self.assertIsInstance(self.gCI5, egglib.LabelView)

    def test__iter__aln_T(self):
        self.assertIsInstance(self.gAO0, collections.abc.Iterable)
        self.assertIsInstance(self.gAI4, collections.abc.Iterable)

    def test__iter__cnt_T(self):
        self.assertIsInstance(self.gCO0, collections.abc.Iterable)
        self.assertIsInstance(self.gCI5, collections.abc.Iterable)

    def test__len__aln_T(self):
        self.assertEqual(len(self.gAO0), 0)
        self.assertEqual(len(self.gAI4), 2)

    def test__len__cnt_T(self):
        self.assertEqual(len(self.gCO0), 1)
        self.assertEqual(len(self.gCI5), 2)

    def test__getitem__aln_T(self):
        self.assertEqual(list(self.gAO0), [])
        self.assertEqual(self.gAI4[1], '1')

    def test__getitem__cnt_T(self):
        self.assertEqual(self.gCO0[0], '0')
        self.assertEqual(self.gCI5[1], '2')

    def test__getitem__aln_T(self):
        self.gAO0.append('1')
        self.assertEqual(self.gAO0[0], '1')
        self.gAI4[1]='2'
        self.assertEqual(self.gAI4[1], '2')

    def test__getitem__cnt_T(self):
        self.gCO0[0]='2'
        self.assertEqual(self.gCO0[0], '2')
        self.gCI5[1]='1'
        self.assertEqual(self.gCI5[1], '1')

class Database_test(unittest.TestCase):
    def setUp(self):
        self.aln = egglib.Align(egglib.alphabets.DNA)
        self.cnt = egglib.Container(egglib.alphabets.DNA)
        self.aln.add_samples(list_smpl_I3)
        self.cnt.add_samples(list_smpl_I3)

        self.aln.add_sample('outgroup1', 'GTAGGGGCATTCC',['1'])
        self.aln.add_sample('outgroup2', 'GTAGGCCAAACAT',['2'])
        self.aln.add_sample('outgroup3', 'GTAGGGGCATTCC',['0'])

        self.cnt.add_sample('outgroup1', 'AAAAAAAAAAAAA',['2'])
        self.cnt.add_sample('outgroup2', 'CCGCGTTGAGCGT',['0'])
        self.cnt.add_sample('outgroup3', 'AGCGTTTTGCGTG',['1'])

        f, self.tmp = tempfile.mkstemp()
        os.close(f)

    def tearDown(self):
        self.aln.reset()
        self.cnt.reset()
        if os.path.isfile(self.tmp): os.remove(self.tmp)

    def test_create_aln_T(self):
        aln2=egglib.Align.create(self.aln)
        aln3=egglib.Align.create([('name1', 'GAAAAAAAAGGAA', ['0','0']), ('name2', 'AAGAAAGCGAGTG', ['0','0'])], egglib.alphabets.DNA)
        self.assertIsInstance(aln2, egglib.Align)
        self.assertNotIsInstance(aln2, egglib.Container)
        self.assertIsInstance(aln3, egglib.Align)
        self.assertNotIsInstance(aln3, egglib.Container)

    def test_create_cnt_T(self):
        cnt2=egglib.Container.create(self.cnt)
        cnt3=egglib.Container.create([('name1', 'GAAAAAAAAGGAA', ['0','0']), ('name2', 'AAGAAAGCGAG', ['0','0'])], alphabet = egglib.alphabets.DNA)
        self.assertIsInstance(cnt2, egglib.Container)
        self.assertNotIsInstance(cnt2, egglib.Align)
        self.assertIsInstance(cnt3, egglib.Container)
        self.assertNotIsInstance(cnt3, egglib.Align)

    def test_fasta_aln_T(self):
        self.aln.fasta(self.tmp)
        self.assertTrue(os.path.exists(self.tmp))
        self.assertTrue(os.path.getsize(self.tmp)>0)

    def test_fasta_aln_E(self):
        with self.assertRaises(ValueError): self.aln.fasta('')
        with self.assertRaises(ValueError):
            self.aln.fasta(self.tmp, linelength=0)

    def test_fasta_cnt_T(self):
        self.cnt.fasta(self.tmp)
        self.assertTrue(os.path.exists(self.tmp))
        self.assertTrue(os.path.getsize(self.tmp)>0)

    def test_fasta_cnt_E(self):
        with self.assertRaises(ValueError): self.cnt.fasta('')
        with self.assertRaises(ValueError):
            self.cnt.fasta(self.tmp, linelength=0)

    def test_clear_aln_T(self):
        self.aln.clear()
        self.assertEqual(self.aln.ns, 0)
        self.assertEqual(self.aln.ls, 0)

    def test_clear_cnt_T(self):
        self.cnt.clear()
        self.assertEqual(self.cnt.ns, 0)

    def test_reset_aln_T(self):
        self.aln.reset()
        self.assertEqual(self.aln.ns, 0)
        self.assertEqual(self.aln.ls, 0)

    def test_reset_cnt_T(self):
        self.cnt.reset()
        self.assertEqual(self.cnt.ns, 0)

    def test_is_matrix_aln_T(self):
        self.assertTrue(self.aln.is_matrix)

    def test_is_matrix_cnt_T(self):
        self.assertFalse(self.cnt.is_matrix)

    def test__len__aln_T(self):
        self.assertEqual(len(self.aln), self.aln.ns)
        self.assertEqual(len(self.aln), self.aln.ns)

    def test__len__cnt__T(self):
        self.assertEqual(len(self.cnt), self.cnt.ns)

    def test_ns_aln_T(self):
        self.assertEqual(self.aln.ns, len(list_smpl_I3)+3)

    def test_ns_cnt_T(self):
        self.assertEqual(self.cnt.ns, len(list_smpl_I3)+3)

    def test_add_sample_aln_T(self):
        ns_a=self.aln.ns
        self.aln.add_sample('new12', 'GAAACCCAAAAAA', ['1','2'])
        ns_b=self.aln.ns
        self.assertEqual(ns_a+1, ns_b)
        self.assertEqual(self.aln.get_name(ns_b-1), 'new12')

    def test_add_sample_cnt_T(self):
        ns_a=self.cnt.ns
        self.cnt.add_sample('new12', 'GAAACCCAAAAAA', ['1','2'])
        ns_b=self.cnt.ns
        self.assertEqual(ns_a+1, ns_b)
        self.assertEqual(self.cnt.get_name(ns_b-1), 'new12')

    def test_add_samples_aln_T(self):
        aln= egglib.Align(egglib.alphabets.DNA)
        aln.add_samples(list_smpl_I1)
        self.assertEqual(aln.ns,6)
        _aln=egglib.Align(egglib.alphabets.DNA)
        _aln.add_samples(self.aln)
        self.assertEqual(_aln.ns,self.aln.ns)

    def test_add_samples_aln_E(self):
        self.aln.reset()
        with self.assertRaises(ValueError):
            self.aln.add_samples([('name1', 'GAAAAAAAAGGAA', ['0','0']), ('name2', 'AAGAAAGCGAGTG', ['0','0']), ('name3', 'AAGCTTGCGGGTG', ['0','1']), ('name4', 'CCCAAAGCGAGTG', ['0','1']), ('Error5', 'AAGCTTGCGAGTG', ['0','1'], 'Error')])
        with self.assertRaises(ValueError):
            self.aln.add_samples([('name1', 'GAAAAAAAAGGAA', ['0','0']), ('Error', 'AAGGCGAGTG', ['0','0'])])

    def test_add_samples_cnt_T(self):
        cnt= egglib.Container(egglib.alphabets.DNA)
        cnt.add_samples(list_smpl_I1)
        self.assertEqual(cnt.ns,6)
        _cnt=egglib.Container(egglib.alphabets.DNA)
        _cnt.add_samples(self.cnt)
        self.assertEqual(_cnt.ns,self.cnt.ns)

    def test_add_samples_cnt_E(self):
        self.cnt.reset()
        with self.assertRaises(ValueError):
            self.cnt.add_samples([('name1', 'GAAAAAAAAGGAA', ['0','0']), ('name2', 'AAGAAAGCGAGTG', ['0','0']), ('name3', 'AAGCTTGCGGGTG', ['0','1']), ('name4', 'CCCAAAGCGAGTG', ['0','1']), ('Error5', 'AAGCTTGCGAGTG', ['0','1'], 'Error')])

    def test__iter__aln_T(self):
        self.assertIsInstance(self.aln, collections.abc.Iterable)

    def test__iValueter__cnt_T(self):
        self.assertIsInstance(self.cnt, collections.abc.Iterable)

    def test_iter_samples_aln_T(self):
        self.assertIsInstance(self.aln, collections.abc.Iterable)

    def test_iter_samples_cnt_T(self):
        self.assertIsInstance(self.cnt, collections.abc.Iterable)

    def test_get_name_aln_T(self):
        self.assertEqual(self.aln.get_name(0),'name1')

    def test_get_name_cnt_T(self):
        self.assertEqual(self.cnt.get_name(1),'name2')

    def test_set_name_aln_T(self):
        self.aln.set_name(0, 'nom1')
        self.assertEqual(self.aln.get_name(0),'nom1')

    def test_set_name_aln_E(self):
        with self.assertRaises(TypeError):
            self.aln.set_name(0, [5,18,18,15,18] )

    def test_set_name_cnt_T(self):
        self.cnt.set_name(1, 'nom2')
        self.assertEqual(self.cnt.get_name(1),'nom2')

    def test_set_name_cnt_E(self):
        with self.assertRaises(TypeError):
            self.cnt.set_name(1, [5,18,18,15,18] )

    def test_get_sequence_aln_T(self):
        self.assertEqual(self.aln.get_sequence(0).string(),'GAAAAAAAAGGAA')

    def test_get_sequence_cnt_T(self):
        self.assertEqual(self.cnt.get_sequence(2).string(),'AAGCTTGCGGGTG')

    def test_set_sequence_aln_T(self):
        self.aln.set_sequence(0, self.aln.get_sequence(3))
        self.assertEqual(self.aln.get_sequence(0).string(),'CCCAAAGCGAGTG')
        self.aln.set_sequence(1, 'ACGTGTTACGGGC')
        self.assertEqual(self.aln.get_sequence(1).string(),'ACGTGTTACGGGC')
        self.aln.set_sequence(1, ['T', 'A', 'G', 'G', 'C', 'C', 'A', 'A', 'A', 'C', 'C' , 'T', 'G' ])
        self.assertEqual(self.aln.get_sequence(1).string(),'TAGGCCAAACCTG')

    def test_set_sequence_aln_E(self):
        with self.assertRaises(ValueError):
            self.aln.set_sequence(0, 'ACGTGTTACGGTAGCTAGC')

    def test_set_sequence_cnt_T(self):
        self.cnt.set_sequence(0, self.cnt.get_sequence(2))
        self.assertEqual(self.cnt.get_sequence(0).string(),'AAGCTTGCGGGTG')
        self.cnt.set_sequence(1, 'ACGTGTTACGGGC')
        self.assertEqual(self.cnt.get_sequence(1).string(),'ACGTGTTACGGGC')
        self.cnt.set_sequence(1, ['T', 'A', 'G', 'G', 'C', 'C', 'A', 'A', 'A', 'C', 'C' , 'T', 'G' ])
        self.assertEqual(self.cnt.get_sequence(1).string(),'TAGGCCAAACCTG')

    def test_get_sample_aln_T(self):
        sAI4=self.aln.get_sample(4)
        self.assertIsInstance(sAI4, egglib.SampleView)
        self.assertEqual(sAI4.name, 'name5')

    def test_get_sample_cnt_T(self):
        sCI4=self.cnt.get_sample(4)
        self.assertIsInstance(sCI4, egglib.SampleView)
        self.assertEqual(sCI4.name, 'name5')

    def test__getitem__aln_T(self):
        sAI4=self.aln[4]
        self.assertIsInstance(sAI4, egglib.SampleView)
        self.assertEqual(sAI4.name, 'name5')

    def test__getitem__cnt_T(self):
        sCI4=self.cnt[4]
        self.assertIsInstance(sCI4, egglib.SampleView)
        self.assertEqual(sCI4.name, 'name5')

    def test_get_sample_aln_T(self):
        sAO1=self.aln.get_sample(len(list_smpl_I3))
        self.assertIsInstance(sAO1, egglib.SampleView)
        self.assertEqual(sAO1.name, 'outgroup1')

    def test_get_sample_cnt_T(self):
        sCO1=self.cnt.get_sample(len(list_smpl_I3))
        self.assertIsInstance(sCO1, egglib.SampleView)
        self.assertEqual(sCO1.name, 'outgroup1')

    def test__delitem__aln_T(self):
        a=self.aln.ns
        del self.aln[4]
        self.assertTrue(a > self.aln.ns )

    def test__delitem__cnt_T(self):
        a=self.cnt.ns
        del self.cnt[4]
        self.assertTrue(a > self.cnt.ns )

    def test_del_sample_aln_T(self):
        a=self.aln.ns
        self.aln.del_sample(4)
        self.assertTrue(a > self.aln.ns )

    def test_del_sample_cnt_T(self):
        a=self.cnt.ns
        self.cnt.del_sample(4)
        self.assertTrue(a > self.cnt.ns )

    def test__setitem__aln_T(self):
        self.aln[0]=self.aln[1]
        self.assertEqual(self.aln.get_name(0),self.aln.get_name(1))
        self.aln[2]=('new12', 'GAAACCCAAAAAA', ['1','2'])
        self.assertEqual(self.aln.get_name(2), 'new12')

    def test__setitem__cnt_T(self):
        self.cnt[0]=self.cnt[1]
        self.assertEqual(self.cnt.get_name(0),self.cnt.get_name(1))
        self.cnt[2]=('new12', 'GAAACCCAAAAAA', ['1','2'])
        self.assertEqual(self.cnt.get_name(2), 'new12')

    def test_set_sample_aln_T(self):
        self.aln.set_sample(2, 'new12', 'GAAACCCAAAAAA', ['1','2'])
        self.assertEqual(self.aln.get_name(2), 'new12')

    def test_set_sample_aln_E(self):
        with self.assertRaises(ValueError):
            self.aln.set_sample(2, 'new12', 'GAAACCERRORCAAAAAA', ['1','2'])
        with self.assertRaises(TypeError):
            self.aln.set_sample(2, 'new12', 'GAAACCCAAAAAA', 'ERROR')

    def test_set_sample_cnt_T(self):
        self.cnt.set_sample(2,'new12', 'GAAACCCAAAAAA', ['1','2'])
        self.assertEqual(self.cnt.get_name(2), 'new12')

    def test_set_sample_cnt_E(self):
        with self.assertRaises(TypeError):
            self.cnt.set_sample(2, 'new12', 'GAAACCCAAAAAA', 'ERROR')
        with self.assertRaises(TypeError):
            self.cnt.set_sample(2, 'new12', 'GAAACCCAAAAAA', [-1,2])

    def test_get_i_aln_T(self):
        self.assertEqual(self.aln.get(0,0),'G')

    def test_get_cnt_T(self):
        self.assertEqual(self.cnt.get(0,1),'A')

    def test_get_aln_T(self):
        self.aln.set(0,5 , 'T')
        self.assertEqual(self.aln.get(0,5),'T')

    def test_get_cnt_T(self):
        self.cnt.set(0,5, 'G')
        self.assertEqual(self.cnt.get(0,5),'G')

    def test_get_label_aln_T(self):
        self.assertEqual(self.aln.get_label(6,1),'2')

    def test_get_label_cnt_T(self):
        self.assertEqual(self.cnt.get_label(10,1),'1')

    def test_set_label_aln_T(self):
        self.aln.set_label(6,1,'1')
        self.assertEqual(self.aln.get_label(6,1),'1')

    def test_set_label_cnt_T(self):
        self.cnt.set_label(10,1,'2')
        self.assertEqual(self.cnt.get_label(10,1),'2')

    def test_reserve(self):
        T1 = 0
        for i in range(10):
            t0 = time.process_time()
            aln = egglib.Align(alphabet=egglib.alphabets.DNA)
            aln.reserve(nsam=100, nsit=100)
            for i in range(100):
                aln.add_sample('', 'A'*100, [])
            t1 = time.process_time()
            T1 += t1-t0

        T2 = 0
        for i in range(10):
            t0 = time.process_time()
            aln = egglib.Align(alphabet=egglib.alphabets.DNA)
            for i in range(100):
                aln.add_sample('', 'A'*100, [])
            t1 = time.process_time()
            T2 += t1-t0
        #self.assertLess(T1, T2) # not always better

    def test_reserve_cnt_T(self):
        T1 = 0
        for i in range(10):
            t0 = time.process_time()
            cnt = egglib.Container(alphabet=egglib.alphabets.DNA)
            cnt.reserve(nsam=100, nsit=100)
            for i in range(100):
                cnt.add_sample('', 'A'*100, [])
            t1 = time.process_time()
            T1 += t1-t0

        T2 = 0
        for i in range(10):
            t0 = time.process_time()
            aln = egglib.Container(alphabet=egglib.alphabets.DNA)
            for i in range(100):
                cnt.add_sample('', 'A'*100, [])
            t1 = time.process_time()
            T2 += t1-t0
        #self.assertLess(T1, T2) # not always better

    def test_find_aln_T(self):
        result1=self.aln.find('name1')
        self.assertIsInstance(result1, egglib.SampleView)
        self.assertEqual(self.aln.find('name1', index=True),0)
        result2=self.aln.find('nam.*',regex=True, multi=True)
        self.assertIsInstance(result2, list)
        self.assertIsInstance(result2[0], egglib.SampleView)
        result3=self.aln.find('outgroup1')
        self.assertIsInstance(result3, egglib.SampleView)
        result4=self.aln.find('outgroup11')
        self.assertIsNone(result4)
        result5=self.aln.find('NAME1', regex=True, flags=[re.IGNORECASE])
        self.assertIsInstance(result5, egglib.SampleView)
        self.assertIsNone(self.aln.find('name1 bla'))

    def test_find_cnt_T(self):
        result1=self.cnt.find('name1')
        self.assertIsInstance(result1, egglib.SampleView)
        self.assertEqual(self.cnt.find('name1', index=True),0)
        result2=self.cnt.find('nam.*',regex=True, multi=True)
        self.assertIsInstance(result2, list)
        self.assertIsInstance(result2[0], egglib.SampleView)
        result3=self.cnt.find('outgroup1')
        self.assertIsInstance(result3, egglib.SampleView)
        result4=self.cnt.find('outgroup1111')
        self.assertIsNone(result4)
        result5=self.cnt.find('NAME1', regex=True, flags=[re.IGNORECASE])
        self.assertIsInstance(result5, egglib.SampleView)
        self.assertIsNone(self.aln.find('name1 bla', index=True))

    def test_find_motif_aln_T(self):
        self.aln.add_sample('name12', 'AAGATAAAGATAA')
        self.assertEqual(self.aln.find_motif(-1, 'GAT') , 2)
        self.assertEqual(self.aln.find_motif(-1, 'GAT', stop=5) , 2)
        self.assertEqual(self.aln.find_motif(-1, 'GAT', stop=4) , None )
        self.assertEqual(self.aln.find_motif(-1, 'GAT', start=3) ,8 )
        self.assertEqual(self.aln.find_motif(-1, 'GAT', start=3, stop=7) , None )

    def test_find_motif_aln_E(self):
        with self.assertRaises(IndexError):
            self.aln.find_motif(25, 'GAT', start=-5)

    def test_find_motif_cnt_T(self):
        self.cnt.add_sample('name12', 'AAAAAGATAAAGATAA')
        self.assertEqual(self.cnt.find_motif(-1, 'GAT') , 5)
        self.assertEqual(self.cnt.find_motif(-1, 'GAT', stop=8) , 5 )
        self.assertEqual(self.cnt.find_motif(-1, 'GAT', stop=7) , None )
        self.assertEqual(self.cnt.find_motif(-1, 'GAT', start=5) ,5 )
        self.assertEqual(self.cnt.find_motif(-1, 'GAT', start=6) , 11 )
        self.assertEqual(self.cnt.find_motif(-1, 'GAT', start=6, stop=10) , None)
        self.assertEqual(self.cnt.find_motif(-1, 'GAT', start=-5) ,11 )

    def test_names_aln_T(self):
        list_names_aln=self.aln.names()
        list_names_I3=[smpl[0] for smpl in list_smpl_I3]
        list_names_I3.extend(['outgroup1', 'outgroup2', 'outgroup3'])
        self.assertIsInstance(list_names_aln, list)
        self.assertListEqual(list_names_aln,list_names_I3)

    def test_names_cnt_T(self):
        list_names_cnt=self.cnt.names()
        list_names_I3=[smpl[0] for smpl in list_smpl_I3]
        list_names_I3.extend(['outgroup1', 'outgroup2', 'outgroup3'])
        self.assertIsInstance(list_names_cnt, list)
        self.assertListEqual(list_names_cnt,list_names_I3 )

    def test__contains__aln_T(self):
        self.assertTrue('name4' in self.aln)
        self.assertFalse('name15' in self.aln)

    def test__contains__cnt_T(self):
        self.assertTrue('name4' in self.cnt)
        self.assertFalse('name15' in self.cnt)

    def test_name_mapping_aln_T(self):
        dict_aln=self.aln.name_mapping()
        self.assertEqual(len(dict_aln), len(list_smpl_I3)+3)
        self.assertIsInstance(dict_aln, dict)
        obj=str(dict_aln['name1'])
        obj_type=re.sub(r' object.*>]', "'>",obj)
        obj_type=re.sub(r"\[<", "<class '", obj_type)
        self.assertEqual(obj_type, str(egglib.SampleView))

    def test_name_mapping_cnt_T(self):
        dict_cnt=self.cnt.name_mapping()
        self.assertEqual(len(dict_cnt), len(list_smpl_I3)+3)
        self.assertIsInstance(dict_cnt, dict)
        obj=str(dict_cnt['name1'])
        obj_type=re.sub(r' object.*>]', "'>",obj)
        obj_type=re.sub(r"\[<", "<class '", obj_type)
        self.assertEqual(obj_type, str(egglib.SampleView))

    def test_group_mapping_aln_T(self):
        grp_map_aln_0 = self.aln.group_mapping(0)
        self.assertEqual(len(grp_map_aln_0), 3)
        self.assertSetEqual(set(map(len, grp_map_aln_0.values())), set([6, 7, 1]))
        with self.assertRaises(IndexError):
            grp_map_aln_1 = self.aln.group_mapping(1)
        grp_map_aln_1 = self.aln.group_mapping(1, liberal=True)
        self.assertEqual(len(grp_map_aln_1), 3)
        self.assertSetEqual(set(map(len, grp_map_aln_1.values())), set([2, 4, 5]))

        grp_map_aln_0 = self.aln.group_mapping(0, as_position=True)
        self.assertEqual(len(grp_map_aln_0), 3)
        self.assertSetEqual(set(map(len, grp_map_aln_0.values())), set([6, 7, 1]))
        with self.assertRaises(IndexError):
            grp_map_aln_1 = self.aln.group_mapping(1, as_position=True)
        grp_map_aln_1 = self.aln.group_mapping(1, liberal=True, as_position=True)
        self.assertEqual(len(grp_map_aln_1), 3)
        self.assertSetEqual(set(map(len, grp_map_aln_1.values())), set([2, 4, 5]))

    def test_group_mapping_cnt_T(self):
        grp_map_cnt_0 = self.cnt.group_mapping(0)
        self.assertEqual(len(grp_map_cnt_0), 3)
        self.assertSetEqual(set(map(len, grp_map_cnt_0.values())), set([6, 7, 1]))
        with self.assertRaises(IndexError):
            grp_map_cnt_1 = self.cnt.group_mapping(1)
        grp_map_cnt_1 = self.cnt.group_mapping(1, liberal=True)
        self.assertEqual(len(grp_map_cnt_1), 3)
        self.assertSetEqual(set(map(len, grp_map_cnt_1.values())), set([2, 4, 5]))

        grp_map_cnt_0 = self.cnt.group_mapping(0, as_position=True)
        self.assertEqual(len(grp_map_cnt_0), 3)
        self.assertSetEqual(set(map(len, grp_map_cnt_0.values())), set([6, 7, 1]))
        with self.assertRaises(IndexError):
            grp_map_cnt_1 = self.cnt.group_mapping(1, as_position=True)
        grp_map_cnt_1 = self.cnt.group_mapping(1, liberal=True, as_position=True)
        self.assertEqual(len(grp_map_cnt_1), 3)
        self.assertSetEqual(set(map(len, grp_map_cnt_1.values())), set([2, 4, 5]))

    def test_remove_duplicates_aln_T(self):
        self.aln.add_sample('name1', 'GAAAAAAAAGGAA', ['0','0'])
        n_b=self.aln.ns
        self.aln.remove_duplicates()
        n_a=self.aln.ns
        self.assertTrue(n_b>n_a)

    def test_remove_duplicates_cnt_T(self):
        self.cnt.add_sample('name1', 'GAAAAAAAAGGAA', ['0','0'])
        n_b=self.cnt.ns
        self.cnt.remove_duplicates()
        n_a=self.cnt.ns
        self.assertTrue(n_b>n_a)

    def test_encode_aln_T(self):
        names1 = self.aln.names()
        code1 = self.aln.encode()
        names2 = self.aln.names()
        self.assertNotEqual(names2, names1)
        self.aln.rename(code1)
        self.assertListEqual(self.aln.names(), names1)
        code2 = self.aln.encode()
        self.assertNotEqual(self.aln.names(), names1)
        self.assertNotEqual(self.aln.names(), names2)
        self.aln.rename(code2)
        self.assertListEqual(self.aln.names(), names1)

    def test_encode_aln_E(self):
        with self.assertRaises(ValueError):
            code1 = self.aln.encode(nbits=2)
        with self.assertRaises(ValueError):
            code1 = self.aln.encode(nbits=300)

    def test_encode_cnt_T(self):
        names1 = self.cnt.names()
        code1 = self.cnt.encode()
        names2 = self.cnt.names()
        self.assertNotEqual(names2, names1)
        self.cnt.rename(code1)
        self.assertListEqual(self.cnt.names(), names1)
        code2 = self.cnt.encode()
        self.assertNotEqual(self.cnt.names(), names1)
        self.assertNotEqual(self.cnt.names(), names2)
        self.cnt.rename(code2)
        self.assertListEqual(self.cnt.names(), names1)

    def test_encode_cnt_E(self):
        with self.assertRaises(ValueError):
            code1 = self.cnt.encode(nbits=2)
        with self.assertRaises(ValueError):
            code1 = self.cnt.encode(nbits=300)

    def test_rename_aln_T(self):
        mapping = {'name1':'nom1', 'name2':'nom2', 'name3':'nom3', 'name4':'nom4',
               'name5':'nom5', 'name6':'nom6', 'name7':'nom7', 'name8':'nom8',
               'name9':'nom9', 'name10':'nom10', 'name11':'nom11',
               'outgroup1': 'horsgroupe1', 'outgroup2': 'horsgroupe2', 'outgroup3': 'horsgroupe3'}
        self.aln.rename(mapping)
        l_names=self.aln.names()
        l_names_=['nom1','nom2','nom3','nom4', 'nom5', 'nom6', 'nom7', 'nom8', 'nom9', 'nom10', 'nom11',
                  'horsgroupe1', 'horsgroupe2', 'horsgroupe3']
        self.assertListEqual(l_names, l_names_)

    def test_rename_aln_E(self):
        mapping = {'name1': 'nom1', 'name2': 'nom2', 'name3': 'nom3', '':'nom3',
               'ERROR4': 'nom4', 'name5':'nom5', 'name6':'nom6', 'name7':'nom7',
               'name8': 'nom8', 'name9':'nom9', 'name10':'nom10', 'name11':'nom11',
               'outgroup1': 'horsgroupe1', 'outgroup2': 'horsgroupe2', 'outgroup3': 'horsgroupe3'}
        with self.assertRaises(ValueError):
            self.aln.rename(mapping)

    def test_rename_cnt_T(self):
        mapping = {'name1': 'nom1', 'name2': 'nom2', 'name3': 'nom3', '':'nom3',
               'name4': 'nom4', 'name5':'nom5', 'name6':'nom6', 'name7':'nom7',
               'name8': 'nom8', 'name9':'nom9', 'name10':'nom10', 'name11':'nom11',
               'outgroup1': 'horsgroupe1', 'outgroup2': 'horsgroupe2', 'outgroup3': 'horsgroupe3'}
        self.cnt.rename(mapping)
        l_names=self.cnt.names()
        l_names_=['nom1','nom2','nom3','nom4', 'nom5', 'nom6', 'nom7', 'nom8', 'nom9', 'nom10', 'nom11',
              'horsgroupe1', 'horsgroupe2', 'horsgroupe3']
        self.assertListEqual(l_names, l_names_)

    def test_rename_cnt_E(self):
        mapping = {'name1': 'nom1', 'name2': 'nom2', 'name3': 'nom3', '':'nom3',
               'ERROR4': 'nom4', 'name5':'nom5', 'name6':'nom6', 'name7':'nom7',
               'name8': 'nom8', 'name9':'nom9', 'name10':'nom10', 'name11':'nom11',
               'outgroup1': 'horsgroupe1', 'outgroup2': 'horsgroupe2', 'outgroup3': 'horsgroupe3'}
        with self.assertRaises(ValueError):
            self.cnt.rename(mapping)

    def test_subset_aln_T(self):
        extr = self.aln.subset([0, 2, 4])
        self.assertEqual(extr.ns, 3)

    def test_subset_cnt_T(self):
        extr = self.cnt.subset([0, 2, 4])
        self.assertEqual(extr.ns, 3)

    def test_fasta(self):
        cnt1 = egglib.Container(egglib.alphabets.DNA)
        cnt1.add_sample('', '--AA--CCGTGGCGCGA----ATTCCGG---AGANNN--')
        cnt1.add_sample('', '????A??-----nnnnCGCCCCGGAT----cccc-c-c?')
        cnt1.add_sample('bah', '??----N-GGGG--NN--', ['one', 'two'])
        cnt1.add_sample('', '-----????----')
        cnt1.add_sample('', '?--GCC---TTA----???')
        cnt1.add_sample('name', 'NnNGCC---TTAN')
        cnt1.add_sample('', '???GCC---TTA--')
        cnt1.add_sample('', 'NNNN---?', ['yeek'])
        self.assertEqual(cnt1.fasta(labels=True), '''>
--AA--CCGTGGCGCGA----ATTCCGG---AGANNN--
>
????A??-----NNNNCGCCCCGGAT----CCCC-C-C?
>bah@one,two
??----N-GGGG--NN--
>
-----????----
>
?--GCC---TTA----???
>name
NNNGCC---TTAN
>
???GCC---TTA--
>@yeek
NNNN---?
''')

        alph2 = egglib.alphabets.Alphabet('string', ['A', 'GG'], [])
        aln2 = egglib.Align(alph2)
        aln2.add_sample('one', ['A', 'A', 'GG'])
        aln2.add_sample('two', ['A', 'GG', 'A'])
        aln2.add_sample('three', ['GG', 'GG', 'GG'])
        self.assertEqual(aln2.fasta(), '''>one
AAGG
>two
AGGA
>three
GGGGGG
''')

        alph3 = egglib.alphabets.Alphabet('int', [10, 20], [])
        aln3 = egglib.Align(alph3)
        aln3.add_sample('one', [10, 10, 20])
        aln3.add_sample('two', [10, 20, 10])
        aln3.add_sample('three', [20, 20, 20])
        with self.assertRaises(ValueError):
            aln3.fasta()
        self.assertEqual(aln3.fasta(alphabet=alph2), '''>one
AAGG
>two
AGGA
>three
GGGGGG
''')

    def test_subset_structure(self):
        data = [ ('name1', 'ACCCGGTGGC', ['flag']),     # 0
                 ('name2', 'GTCGCGATCT', ['otg']),      # 1 (outgroup)
                 ('name3', 'CCTGAGCGGC', ['alt']),      # 2 (alt pop)
                 ('name4', 'GCCAC-CGAC', ['alt']),      # 3 (alt pop)
                 ('name5', '???CCAAAA?', ['flag']),     # 4
                 ('name6', 'TCGCGAARDD', ['flag']),     # 5
                 ('name7', '----AC----', ['otg']),      # 6 (outgroup)
                 ('name8', 'ACGTGTGCGA', ['alt']),      # 7 (alt pop)
                 ('name9', '????AACCGC', ['flag'])]     # 8

        string1 = \
""">name1@flag
ACCCGGTGGC
>name5@flag
???CCAAAA?
>name6@flag
TCGCGAARDD
>name9@flag
????AACCGC
>name3@alt
CCTGAGCGGC
>name4@alt
GCCAC-CGAC
>name8@alt
ACGTGTGCGA
>name2@otg
GTCGCGATCT
>name7@otg
----AC----
"""

        string2 = \
""">name3@alt
CCTGAGCGGC
>name4@alt
GCCAC-CGAC
>name8@alt
ACGTGTGCGA
>name2@otg
GTCGCGATCT
>name7@otg
----AC----
"""

        idx1 = [0, 4, 5, 8, 2, 3, 7, 1, 6]
        idx2 = [2, 3, 7, 1, 6]

        # make source objects
        aln = egglib.Align.create(data, alphabet=egglib.alphabets.DNA)
        cnt = egglib.Container.create(data, alphabet=egglib.alphabets.DNA)

        # get full list (but ordered by pop)
        aln1 = aln.subset(idx1)
        self.assertIsInstance(aln1, egglib.Align)
        self.assertEqual(aln1.fasta(labels=True), string1)
        cnt1 = cnt.subset(idx1)
        self.assertIsInstance(cnt1, egglib.Container)
        self.assertEqual(cnt1.fasta(labels=True), string1)

        # get sublist (without pop `flag`)
        aln2 = aln.subset(idx2)
        self.assertEqual(aln2.fasta(labels=True), string2)
        cnt2 = cnt.subset(idx2)
        self.assertEqual(cnt2.fasta(labels=True), string2)

        # extract structure
        struct1 = egglib.struct_from_labels(aln, lvl_pop=0, outgroup_label='otg')
        di, do = struct1.as_dict()
        del di[None]['flag']
        d = collections.OrderedDict()
        for k in sorted(di[None]['alt']): d[k] = di[None]['alt'][k]
        di[None]['alt'] = d
        struct2 = egglib.struct_from_dict(di, do)

        # subset using structure
        aln1s = aln.subset(struct1)
        self.assertIsInstance(aln1s, egglib.Align)
        self.assertEqual(aln1s.fasta(labels=True), string1)

        cnt1s = cnt.subset(struct1)
        self.assertIsInstance(cnt1s, egglib.Container)
        self.assertEqual(cnt1s.fasta(labels=True), string1)

        aln2s = aln.subset(struct2)
        self.assertIsInstance(aln2s, egglib.Align)
        self.assertEqual(aln2s.fasta(labels=True), string2)

        cnt2s = cnt.subset(struct2)
        self.assertIsInstance(cnt2s, egglib.Container)
        self.assertEqual(cnt2s.fasta(labels=True), string2)

class Align_test(unittest.TestCase):

    def setUp(self):
        self.aln = egglib.Align(egglib.alphabets.DNA)
        self.aln.add_samples(list_smpl_I4)
        for name,seq,grp in list_out_1:
            self.aln.add_sample(name,seq,grp)

    def tearDown(self):
        self.aln.reset()

    def test_object_aln_T(self):
        self.assertIsInstance(self.aln, egglib.Align)

    def test_object_aln_F(self):
        self.assertNotIsInstance(self.aln, egglib.Container)

    def test_ls_aln_T(self):
        self.assertEqual(self.aln.ls, 13)

    def test_del_column_aln_T(self):
        ls_a=self.aln.ls
        self.aln.del_columns(3, 3)
        ls_b=self.aln.ls
        self.assertTrue(ls_a>ls_b)
        self.assertEqual(self.aln.ls, 10)
        aln = egglib.Align.create(
            [['', 'ABCDE'],
            ['', 'abcde'],
            ['', '12345']], alphabet=egglib.Alphabet('char', 'ABCDEabcde12345', ''))
        aln.del_columns(1)
        self.assertEqual(aln.ls, 4)
        self.assertEqual(aln[0].sequence[:], 'ACDE')
        self.assertEqual(aln[1].sequence[:], 'acde')
        self.assertEqual(aln[2].sequence[:], '1345')

    def test_del_column_aln_E(self):
        with self.assertRaises(ValueError):
            self.aln.del_columns(3,-1)

    def test_insert_columns_aln_T(self):
        aln = egglib.Align(egglib.alphabets.DNA)
        aln.add_sample('', 'GTAAAA')
        aln.add_sample('', 'GTAACT')
        aln.add_sample('', 'TTACCG')
        ls_a=aln.ls
        aln.insert_columns(3, 'ATG')
        ls_b=aln.ls
        self.assertEqual(ls_a, 6)
        self.assertEqual(ls_b, 9)
        self.assertEqual(aln.get_sequence(0)[:], 'GTAATGAAA')
        self.assertEqual(aln.get_sequence(1)[:], 'GTAATGACT')
        self.assertEqual(aln.get_sequence(2)[:], 'TTAATGCCG')

    def test_insert_columns_aln_E(self):
        with self.assertRaises(IndexError):
            self.aln.insert_columns(-56,'ACT')

    def test_extract_aln_T(self):
        aln_ext=self.aln.extract(1, 4)
        self.assertIsInstance(aln_ext, egglib.Align)
        self.assertEqual(aln_ext.ls,3)
        aln_ext2=self.aln.extract([4,2,1,1,1,3,3]) #Test with a list like parameter
        self.assertEqual(aln_ext2.ls,7)
        self.assertIsInstance(aln_ext2, egglib.Align)

        aln = egglib.Align(egglib.alphabets.DNA)
        aln.add_sample('', 'GTAAAAGCA')
        aln.add_sample('', 'GTAACTCGT')
        aln.add_sample('', 'TTACCGGGA')
        sub1 = aln.extract(2, 6)
        self.assertEqual(sub1.ls, 4)
        self.assertEqual(sub1.get_sequence(1).string(), 'AACT')

        sub1 = aln.extract([5, 4, 2, 0, 8, 5])
        self.assertEqual(sub1.ls, 6)

    def test_extract_aln_E(self):
        with self.assertRaises(IndexError):
            self.aln.extract(1, -54)
        with self.assertRaises(ValueError):
            self.aln.extract()

    def test_extract_fix_ends_T(self):
        self.aln.fix_ends()
        seq_9=self.aln.get_sequence(8).string()
        self.assertRegex(seq_9,'^\?.*\?$')
        seq_1=self.aln.get_sequence(0).string()
        self.assertNotRegex(seq_1,'^\?.*\?$')

    def test_extract_reading_frame_T(self):
        # simulate a phony dataset
        aln = egglib.Align.create([(f'seq{i:0>2}', ''.join(random.choices('ACGT', k=1800))) for i in range(15)], alphabet=egglib.alphabets.DNA)

        # define bounds
        rf = egglib.tools.ReadingFrame([(144, 873), (1206, 1279), (1542, 1733)])
        pos = [j for i in rf.iter_codons() for j in i]

        # extract from positions
        sub1 = aln.extract(pos)

        # extract from ReadingFrame
        sub2 = aln.extract(rf)
        self.assertEqual(sub1.fasta(), sub2.fasta())

        # test with truncated codons
        rf2 = egglib.tools.ReadingFrame([(500, 650, 2), (800, 1000, 3)], keep_truncated=False)
        rf3 = egglib.tools.ReadingFrame([(500, 650, 2), (800, 1000, 3)], keep_truncated=True)
        A = list(range(502, 650))
        B = list(range(801, 1000))
        while len(A)%3 > 0: del A[-1]
        while len(B)%3 > 0: del B[-1]
        pos2 = A + B
        pos3 = list(range(500, 650)) + list(range(800, 1000))

        sub3 = aln.extract(pos2)
        sub4 = aln.extract(rf2)
        sub5 = aln.extract(pos3)
        sub6 = aln.extract(rf3)

        self.assertEqual(sub3.fasta(), sub4.fasta())
        self.assertEqual(sub5.fasta(), sub6.fasta())

    def test_column_aln_T(self):
        check = ['A','A','C','A','C','A','A','A','-','C','G','G','G','A','A','-','?','?',
                 'G','G','G','G','A','A','A','A','A','A','?','?','A','A','A','-','A']
        spl_col = self.aln.column(3)
        self.assertListEqual(spl_col, check)

    def test_nexus_aln_T(self):
        nex_D=self.aln.nexus()
        nex_P=self.aln.nexus(True)
        self.assertTrue(nex_D != -1)
        self.assertTrue(nex_P !=-1)
        self.assertIsInstance(nex_D,str)
        self.assertIsInstance(nex_P,str)

    def test_filter_aln_T(self):
        string = """>
AAACGCGCGGCCGCGGCGCGTGNN
>
AA-SGCGNGGCCGC-GCGCG--CA
>
--ACGCGCGGCCGCGGCGCGTG-A
>
AAAC---CGGNNNCGGCGCG-AAC
>
AAACG?????CCGCGGCGCGRTC-
>
-----CGNGNNCGCGG--------
>
???CGCGCGGCCG???????????
>
AASCGCRCGGCCGCGGCGCGG---
>
AAACRMNCGGCCVVVGCGCG????
>
AAACGCG----CGCGGCGCG?---
>@#
AA?CGC?CGG??GCGGCG?GRSSG
>@#
AAAC-------------GCGTACG
>@#
AA--GCGCGGCCGCGGCGCGTGA-
>@#
AAAC??GCGGSSSCG---CG-AA-
"""

        aln = egglib.io.from_fasta_string(string, labels=True, alphabet=egglib.alphabets.DNA)
        self.assertEqual(aln.ns, 14)

        aln.filter(0.5)
        self.assertEqual(aln.ns, 11)

        aln.filter(0.6)
        self.assertEqual(aln.ns, 9)

        aln.filter(0.9)
        self.assertEqual(aln.ns, 1)

        aln = egglib.io.from_fasta_string(string, labels=True, alphabet=egglib.alphabets.DNA)
        aln.filter(0.75, relative=True)
        self.assertEqual(aln.ns, 7)

        aln.filter(0.98, relative=True)
        self.assertEqual(aln.ns, 1)

    def test_filter_aln_E(self):
        with self.assertRaises(ValueError):
            self.aln.filter(-1)
        with self.assertRaises(ValueError):
            self.aln.filter(50)

    def test_phyml_aln_T(self):
        list_smpl_I3
        self.assertIsInstance(self.aln.phyml(), str)
        self.assertRegex(self.aln.phyml(), '^[0-9]*\s[0-9]*\n([a-z0-9A-Z%]*\s*[-?AGTCUMRINXWS]*\n)*')
        self.assertIsInstance(self.aln.phyml(), str)
        self.assertRegex(self.aln.phyml(), '^[0-9]*\s[0-9]*\n([a-z0-9A-Z%]*\s*[-?AGTCUMRINXWS]*\n)*')
        self.aln.reset(egglib.alphabets.protein)
        self.aln.add_samples(list_prot_I1)
        for name, seq, grp in list_prot_O1:
            self.aln.add_sample(name, seq, grp)
        self.assertIsInstance(self.aln.phyml(), str)
        self.aln.reset()
        self.aln.add_samples(list_smpl_I3)
        self.assertIsInstance(self.aln.phyml(), str)

    def test_phyml_aln_E(self):
        self.aln.add_sample('(Error)', 'GTAAGGGGCAATT') #name sample with "("
        with self.assertRaises(ValueError):
            self.aln.phyml()

        self.aln.add_sample('', 'GTAAGGGGCAATT') #empty name "
        with self.assertRaises(ValueError):
            self.aln.phyml()

    def test_phylip_aln_T(self):
        self.assertIsInstance(self.aln.phylip('s'), str)
        self.assertRegex(self.aln.phylip('S'), '^\s*([0-9]*\s[0-9]*)(\s*[IisS]\n|\n)(([a-z0-9A-Z%]){1,10}\s*([AGTCUMRWSNIX?-]*(\s|))*\n)*') #this line which uses a regex takes much time to be executed
        self.assertIsInstance(self.aln.phylip('i'), str)
        self.assertRegex(self.aln.phylip('I'), '^\s*([0-9]*\s[0-9]*)(\s*[IisS]\n|\n)(([a-z0-9A-Z%]){1,10}\s*([AGTCUMRWSNIX?-]*(\s|))*\n)*')

    def test_phylip_aln_E(self):
        self.aln.add_sample('naaaammmmee1', 'GTAAGGGGCAATT')
        self.aln.add_sample('100%]', 'GTAAGGGGCAATT')
        with self.assertRaises(ValueError):
            self.aln.phylip('I')
        with self.assertRaises(ValueError):
            self.aln.phylip('S')
        with self.assertRaises(ValueError):
            self.aln.phylip('A')

        self.aln.del_sample(18)
        self.aln.add_sample('100%]', 'GTAAGGGGCAATT')
        self.aln.add_sample('naaaammmmee1', 'GTAAGGGGCAATT')
        with self.assertRaises(ValueError):
            self.aln.phylip('S')
        with self.assertRaises(ValueError):
            self.aln.phylip('I')

    def test_slider_aln_T(self):
        self.aln.reset()
        list_sample=[('100%', 'AAAAAAAAAA'),('090%', 'AAAAAAAAA-'),('060%', 'AANA-ARAA-'),('020%', '????ASNAN-'),('000%', '---????-?-')]
        list_outgrp=[('100%', 'AAAAAAAAAA'),('090%', 'AAAAAAAAA-'),('060%', 'AANA-ARAA-'),('020%', '????ASNAN-'),('000%', '---????-?-')]
        self.aln.add_samples(list_sample)
        for name,seq in list_outgrp:
            self.aln.add_sample(name,seq)
        n=0
        for i in self.aln.slider(9,5):
            self.assertIsInstance(i, egglib.Align)
            n+=1
        self.assertEqual(n,2)
        self.assertIsInstance(self.aln.slider(9, 5), collections.abc.Iterable)

    def test_random_missing_T(self):
        self.aln.reset()
        list_sample=[('', 'AGGG---CCAA', ['1']),('',   'A-GGAAACCA?', ['2'])]
        list_outgrp=[('', 'AGGR---C--G'),('', 'SGGG---CCA?')]
        self.aln.add_samples(list_sample)
        self.aln.add_samples(list_outgrp)
        self.aln.filter(0.5)
        self.assertEqual(self.aln.ns, 3)
        self.assertRegex(self.aln.get_sequence(0).string(), '[ACGT]')
        self.assertRegex(self.aln.get_sequence(0).string(), '-')
        self.assertNotRegex(self.aln.get_sequence(0).string(), 'N')
        self.aln.random_missing(1.0, missing='N')
        self.assertNotRegex(self.aln.get_sequence(0).string(), '[ACGT]')
        self.assertRegex(self.aln.get_sequence(0).string(), '-')
        self.assertRegex(self.aln.get_sequence(0).string(), 'N')

    def test_random_missing_E(self):
        with self.assertRaises(ValueError):
            self.aln.filter(41)

    def test_consensus_T(self):
        self.aln.reset()
        list_sample=[('', 'AGGG---CCAA', ['1'])
                    ,('', 'ANGGAAACCA?', ['2'])]
        self.aln.add_samples(list_sample)
        self.assertEqual(self.aln.consensus(), 'ANGG???CCA?')
        self.aln.reset()
        list_outgrp=[('', 'AGGR---C--G'),
                     ('', 'SGGG---CCA?')]
        self.aln.add_samples(list_outgrp)
        self.assertEqual(self.aln.consensus(), 'VGGR---C???')
        aln = egglib.Align(egglib.alphabets.DNA, 0, 10)
        self.assertEqual(aln.consensus(), '?' * 10)
        aln = egglib.Align(egglib.alphabets.protein, 0, 10)
        with self.assertRaises(ValueError):
            aln.consensus()

    def test_intersperse_T(self):
        self.aln.intersperse(20, alleles='-', positions=[0,1,2,3,4,5,6,7,8,9,10,11,12])
        self.assertEqual(self.aln.get_sequence(9).string(),'CAGCGTTGAGCGT-------')
        self.setUp()
        self.aln.intersperse(20, alleles='-', positions=[0.08,0.15,0.23,0.31,0.38,0.46,0.54,0.62,0.69,0.77,0.85,0.92,1.0])
        self.assertEqual(self.aln.get_sequence(8).string(),'-------T-TT-TG-CG---')

    def test_intersperse_E(self):
        with self.assertRaises(ValueError):
            self.aln.intersperse(20, alleles='-', positions=[ 3, 10, 18])
        with self.assertRaises(TypeError):
            self.aln.intersperse(20, alleles='-', positions=['0','1','2','3','4','5','6','7','8','9','10','11','12'])
        with self.assertRaises(ValueError):
            self.aln.intersperse(20, alleles='-', positions=[0,1,2,3,-4,5,6,7,8,9,10,11,12])
        with self.assertRaises(ValueError):
            self.aln.intersperse(20, alleles='-', positions=[0.2,1.3,2.5,3.7,4.9,5.1,6.3,7.5,8.7,9.9,10.2,11.4,12.5])
        with self.assertRaises(ValueError):
            self.aln.intersperse(20, alleles='-', positions=[0,1,2,3,4,5,6,7,8,9,10,11,50])

    def test_iter_sites(self):
        aln = egglib.Align.create(
            [ ('name1', 'AAGT'),
              ('name2', 'TAGT'),
              ('name3', 'AAGT'),
              ('name4', 'TCCT'),
              ('name5', 'ACCT'),
              ('name6', 'TCCA')], egglib.alphabets.DNA)

        for i, site in enumerate(aln.iter_sites()):
            self.assertListEqual(site.as_list(), aln.column(i))

        self.assertListEqual(
            [site.as_list() for site in aln.iter_sites(1, 3)],
            [['A', 'A', 'A', 'C', 'C', 'C'],
             ['G', 'G', 'G', 'C', 'C', 'C']])

        self.assertListEqual(
            [site.as_list() for site in aln.iter_sites(2)],
            [['G', 'G', 'G', 'C', 'C', 'C'],
             ['T', 'T', 'T', 'T', 'T', 'A']])

    def test_del_sample(self):
        ref = [ ('sam1', 'AAGTTGGCCCGGA', ['lbl1']),
                ('sam2', 'AAGTTGGCCCCTA', ['lbl2']),
                ('sam3', 'AAAAAGGCCCGGA', ['lbl3']),
                ('sam4', 'AAGTATATATGGA', ['lbl4']),
                ('sam5', 'CCCCCGGCCCGGA', ['lbl5']),
                ('sam6', 'AGGGTGGGGCGGA', ['lbl6']),
                ('sam7', 'TAATTGGCCATTA', ['lbl7']),
                ('sam8', 'CCCGCATATATAT', ['lbl8']), ]
        aln = egglib.Align.create(ref, alphabet=egglib.alphabets.DNA)
        self.assertEqual([(sam.name, sam.sequence.string(), list(sam.labels)) for sam in aln], ref)
        del ref[2]
        del aln[2]
        self.assertEqual([(sam.name, sam.sequence.string(), list(sam.labels)) for sam in aln], ref)
        del ref[4]
        aln.del_sample(4)
        self.assertEqual([(sam.name, sam.sequence.string(), list(sam.labels)) for sam in aln], ref)

class  Container_test(unittest.TestCase):
    def setUp(self):
        self.cnt = egglib.Container(egglib.alphabets.DNA)
        self.cnt.add_samples(list_smpl_I4)
        for name,seq,grp in list_out_1:
            self.cnt.add_sample(name,seq,grp)

    def tearDown(self):
        self.cnt.reset()

    def test_object_cnt_T(self):
        self.assertIsInstance(self.cnt, egglib.Container)

    def test_object_cnt_F(self):
        self.assertNotIsInstance(self.cnt, egglib.Align)

    def test_ls_cnt_T(self):
        self.assertEqual(self.cnt.ls(6), 13)

    def test_del_sites_cnt_T(self):
        self.cnt.del_sites(2, 0, 3)
        self.cnt.del_sites(0, 2, 3)
        self.assertEqual(self.cnt.get_sequence(2).string(), 'CTTGCGGGTG')
        self.assertEqual(self.cnt.get_sequence(0).string(),'GA--AAGGAA')

    def test_del_sites_cnt_E(self):
        with self.assertRaises(ValueError):
            self.cnt.del_sites(2, 0, -5)

    def test_insert_sites_cnt_T(self):
        self.cnt.insert_sites(0, 0, 'ACCT')
        self.cnt.insert_sites(4, None, 'A')
        self.assertEqual(self.cnt.get_sequence(4).string(), 'AAGCTTGCGAGTGA')
        self.assertEqual(self.cnt.get_sequence(0).string(), 'ACCTGAAA---AAGGAA')

    def test_equalize_cnt_T(self):
        self.cnt.insert_sites(0, 0, 'ACCTA')
        self.cnt.insert_sites(4, None, 'A')
        self.cnt.insert_sites(9, 8, 'CT')
        self.cnt.insert_sites(5, None, 'ACG')
        self.cnt.equalize('N')
        self.assertEqual(self.cnt.ls(6),18)
        self.assertRegex(self.cnt.get_sequence(3).string(), 'N*$')

    def test_del_sample(self):
        ref = [ ('sam1', 'AAGTTGGCCCGGA', ['lbl1']),
                ('sam2', 'AAGTTGGCCCCTAA', ['lbl2']),
                ('sam3', 'AAAAAGGCCCGGAAC', ['lbl3']),
                ('sam4', 'AAGTATATATGGAACG', ['lbl4']),
                ('sam5', 'CCCCCGGCCCGGAACGT', ['lbl5']),
                ('sam6', 'AGGGTGGGGCGGAACGTA', ['lbl6']),
                ('sam7', 'TAATTGGCCATTAACGTAC', ['lbl7']),
                ('sam8', 'CCCGCATATATATACGTACG', ['lbl8']), ]

        aln = egglib.Container.create(ref, alphabet=egglib.alphabets.DNA)
        self.assertEqual([(sam.name, sam.sequence.string(), list(sam.labels)) for sam in aln], ref)
        del ref[2]
        del aln[2]
        self.assertEqual([(sam.name, sam.sequence.string(), list(sam.labels)) for sam in aln], ref)
        del ref[4]
        aln.del_sample(4)
        self.assertEqual([(sam.name, sam.sequence.string(), list(sam.labels)) for sam in aln], ref)
