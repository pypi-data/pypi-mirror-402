"""
    Copyright 2023-2024 Thomas Coudoux, Stéphane De Mita, Mathieu Siol

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

import egglib, unittest, pathlib, collections, random, re
path = pathlib.Path(__file__).parent / '..' / 'data'

class Translator_test(unittest.TestCase):
    def test_translator_T(self):
        trans=egglib.tools.Translator(code=5)
        self.assertIsInstance(trans, egglib.tools._code_tools.Translator)

    def test_translator_E(self):
        with self.assertRaises(ValueError):
            trans=egglib.tools.Translator(code=50) #<-----

    def test_translate_codon_T(self):
        trans=egglib.tools.Translator(code=5)
        codon=trans.translate_codon('AGT')
        self.assertEqual(codon,'S') #<-----

    def test_translate_align_T(self):
        trans=egglib.tools.Translator(code=1)
        aln=egglib.Align(egglib.alphabets.DNA)
        aln.ng = 2
        aln.add_samples([('CDS1', 'ATGGACCCCCTTGGGGACACGCTGCGC', ['0','0']),
                 ('CDS2', 'GCGACTGCGGGAGGCCTTCCACGCGGA', ['0','0']),
                 ('CDS3', 'CCTGGTTCCGCTACTTCAACGCCGGCG', ['0','1']),
                 ('CDS4', 'TGCTGCCTGCCCTGCAGAGCACCATCT', ['0','1']),
                 ('CDS5', 'GAAGCTCAACGCCCTCCGCTACCCGCC', ['1','2'])])
        aln.to_codons()
        aln_prot=trans.translate_align(aln)
        self.assertIsInstance(aln_prot, egglib._interface.Align) #<-----

        prot_seq=['MDPLGDTLR','ATAGGLPRG','PGSATSTPA','CCLPCRAPS']
        for i in range(0,4):
            seq=aln_prot.get_sequence(i).string()
            self.assertEqual(seq, prot_seq[i])

        f_name='sequence.fas'
        aln2 = egglib.io.from_fasta(str(path / f_name), alphabet=egglib.alphabets.DNA, labels=False, cls=egglib._interface.Align)
        aln2.to_codons(frame=egglib.tools.ReadingFrame([(0, 11), (30, 63, 1)], keep_truncated=True))
        aln2_prot=trans.translate_align(aln2)
        prot_seq2=['IVDXEVPPSSRIFFP', 'FEDXLLTPNLPYLHP', 'MAAXS-PSPN--YFP', 'MGTXSSASSSSSLES', 'MAAXSTPSPSNSCFL', 'MAAXECPSSTPSILS', 'MTTX-SPSNDSSAFA', 'LEEXKCSVSFPFYLP', 'MAAXSSPSSSSAASA', 'FDEXKSLEAFPFSLD', 'LEDXPHIFPFAYEAS', '---X-----------', 'MSLXAVSLSLARAAN', 'AANXKRRDALLAYAR', 'MAAXEEPFIRDASGS', 'MDRXALPPLPMALGG', 'MTAXPAEASFGSLVA', 'MAAXNPSMSQDSYMP', 'PPSXKRRALLLRYHR', 'MATXGAAMYDMVVDS', 'MAAX-APSPQMQKIA', 'MDAXASAVSSLLLSP']
        for i in range(0,22):
            self.assertIn(aln2_prot.get_sequence(i).string(),prot_seq2) #<-----

    def test_translate_align_E(self):
        trans=egglib.tools.Translator(code=1)
        cnt=egglib.Container(egglib.alphabets.DNA)
        cnt.ng = 2
        cnt.add_samples([('CDS1', 'ATGGACCCCCTTGGGGACACGCTGCGC', ['0','0']),
                 ('CDS2', 'GCGACTGCGGGAGGCCTTCCACGCGGA', ['0','0']),
                 ('CDS3', 'CCTGGTTCCGCTACTTCAACGCCGGCG', ['0','1']),
                 ('CDS4', 'TGCTGCCTGCCCTGCAGAGCACCATCT', ['0','1']),
                 ('CDS5', 'GAAGCTCAACGCCCTCCGCTACCCGCC', ['1','2'])])
        cnt.to_codons()
        with self.assertRaises(TypeError):
            aln_prot=trans.translate_align(cnt)

    def test_translate_container_T(self):
        trans=egglib.tools.Translator(code=1)
        cnt=egglib.Container(egglib.alphabets.DNA)
        cnt.ng = 2
        cnt.add_samples([('CDS1', 'ATGGACCCCCTTGGGGACACGCTGCGC', ['0','0']),
                 ('CDS2', 'GCGACTGCGGGAGGCCTTCCACGCGGA', ['0','0']),
                 ('CDS3', 'CCTGGTTCCGCTACTTCAACGCCGGCG', ['0','1']),
                 ('CDS4', 'TGCTGCCTGCCCTGCAGAGCACCATCT', ['0','1']),
                 ('CDS5', 'GAAGCTCAACGCCCTCCGCTACCCGCC', ['1','2'])])
        cnt.to_codons()
        cnt_prot=trans.translate_container(cnt)
        self.assertIsInstance(cnt_prot, egglib._interface.Container) #<-----

        prot_seq=['MDPLGDTLR','ATAGGLPRG','PGSATSTPA','PGSATSTPA','CCLPCRAPS']
        for i in range(0,4):
            seq=cnt_prot.get_sequence(i).string()
            self.assertIn(seq,prot_seq)

        f_name='sequence.fas'
        cnt2 = egglib.io.from_fasta(str(path / f_name), alphabet=egglib.alphabets.DNA, labels=False, cls=egglib._interface.Container)
        cnt2.to_codons()
        cnt2_prot=trans.translate_container(cnt2)

        f_name='results_prot.txt'
        file_ = open(path / f_name, 'r').read()
        for i in range(0,23):
            seq=cnt2_prot.get_sequence(i).string()
            r=file_.find(seq)
            self.assertTrue(r >= 0) #<-----

    def test_translate_container_E(self):
        trans=egglib.tools.Translator(code=1)
        aln=egglib.Align(egglib.alphabets.DNA)
        aln.ng = 2
        aln.add_samples([('CDS1', 'ATGGACCCCCTTGGGGACACGCTGCGC', ['0','0']),
                 ('CDS2', 'GCGACTGCGGGAGGCCTTCCACGCGGA', ['0','0']),
                 ('CDS3', 'CCTGGTTCCGCTACTTCAACGCCGGCG', ['0','1']),
                 ('CDS4', 'TGCTGCCTGCCCTGCAGAGCACCATCT', ['0','1']),
                 ('CDS5', 'GAAGCTCAACGCCCTCCGCTACCCGCC', ['1','2'])])
        aln.to_codons()

        with self.assertRaises(TypeError):
            cnt_prot=trans.translate_container(aln) #<-----

    def test_translate_sequence_T(self):
        trans=egglib.tools.Translator(code=1)
        seq_nuc="ATGCAGCGATTGCTCTTTCCGCCGTTGAGGGCCTTGAAGGGGAGGTGGTGTCTTTGGCTGATGAATGAACTCCGAAGAGTCCCAAAATGA"
        seq_prot=trans.translate_sequence(seq_nuc)
        self.assertEqual(seq_prot, "MQRLLFPPLRALKGRWCLWLMNELRRVPK*") #<-----
        self.assertIsInstance(seq_prot, str) #<-----

        aln=egglib.Align(egglib.alphabets.DNA)
        aln.ng=2
        aln.add_samples([('CDS1', 'ATGGACCCCCTTGGGGACACGCTGCGC', ['0','0'])])
        aln.to_codons()
        seq_prot3=trans.translate_sequence(aln.get_sequence(0))
        self.assertEqual(seq_prot3, 'MDPLGDTLR') #<-----

    def test_translate_sequence_E(self):
        trans=egglib.tools.Translator(code=1)
        seq_nuc="ATGCAGCGATTGCTCTTTCCGCCGTTGAGGGCCTTGAAGGGGAGGTGGTGTCTTTGGCTGATGAATGAACTCCGAAGAGTCCCAAAATGA"
        with self.assertRaises(ValueError):
            seq_prot=trans.translate_sequence(seq_nuc, frame= egglib.tools.ReadingFrame([(0,11),(0, 800)])) #<-----

class BackalignError_test(unittest.TestCase):
    def test_name_T(self):
        translator= egglib.tools.Translator(code=1)
        cds = egglib.io.from_fasta(str(path / 'LYK.E2.cds'), alphabet=egglib.alphabets.DNA)
        prot_aln = egglib.io.from_fasta(str(path / 'LYK.prot.aln'), alphabet=egglib.alphabets.protein)
        ns=prot_aln.ns
        ls=prot_aln.ls
        nucl = cds._obj
        aln = prot_aln._obj
        names_i = [nucl.get_name(i) for i in range(ns)]

        B_error=egglib.tools.BackalignError(names_i[0], nucl.get_sample, aln.get_sample, 0, 0, ls, nucl.get_nsit_sample(0), translator)
        self.assertEqual(B_error.name,'VvLYK2') #<-----

    def test_alignment_T(self):
        translator= egglib.tools.Translator(code=1)
        cds = egglib.io.from_fasta(str(path / 'LYK.E2.cds'), alphabet=egglib.alphabets.DNA)
        prot_aln = egglib.io.from_fasta(str(path / 'LYK.prot.aln'), alphabet=egglib.alphabets.protein)
        ns=prot_aln.ns
        ls=prot_aln.ls
        nucl = cds._obj
        aln = prot_aln._obj
        names_i = [nucl.get_name(i) for i in range(ns)]
        B_error=egglib.tools.BackalignError(names_i[9], nucl.get_sample, aln.get_sample, 9, 9, ls, nucl.get_nsit_sample(0), translator)
        self.assertRegex(B_error.alignment, '[~,#,-]')

    def test_fix_stop(self):
        # regression test relative to issue #266
        cds = egglib.Container.create([('', 'ATGATGATG'), ('', 'ATGATGATG'), ('', 'ATGATGATG'), ('', 'ATGATGATG')], egglib.alphabets.DNA)
        cds.to_codons()
        aln = egglib.Align.create([('', '-MM-M'), ('', 'MMM--'), ('', '-M-MM'), ('', '--MMM')], egglib.alphabets.protein)
        res = egglib.tools.backalign(cds, aln, ignore_names=True, fix_stop=False)
        res = egglib.tools.backalign(cds, aln, ignore_names=True, fix_stop=True)


class orf_iter_test(unittest.TestCase):
    # other tests are in Outclass_tools_test

    def helper(self, seq):
        frame1 = egglib.tools.translate(seq[:len(seq)// 3 * 3])
        frame2 = egglib.tools.translate(seq[1:(len(seq)-1)// 3 * 3 + 1])
        frame3 = egglib.tools.translate(seq[2:(len(seq)-2)// 3 * 3 + 2])
        rc = egglib.tools.rc(seq)
        frame4 = egglib.tools.translate(rc[:len(seq)// 3 * 3])
        frame5 = egglib.tools.translate(rc[1:(len(seq)-1)// 3 * 3 + 1])
        frame6 = egglib.tools.translate(rc[2:(len(seq)-2)// 3 * 3 + 2])


        orf_MS = []
        orf_xx = []
        orf_Mx = []
        orf_xS = []
        orf_MS_F = []
        orf_xx_F = []
        orf_Mx_F = []
        orf_xS_F = []
        for frame in [frame1, frame2, frame3]:
            orf_MS.extend(re.findall('M[A-Z]*\*', frame))
            orf_xx.extend(re.findall('[A-Z]+\*?', frame))
            orf_Mx.extend(re.findall('M[A-Z]*\*?', frame))
            orf_xS.extend(re.findall('[A-Z]+\*', frame))
            orf_MS_F.extend(re.findall('M[A-Z]*\*', frame))
            orf_xx_F.extend(re.findall('[A-Z]+\*?', frame))
            orf_Mx_F.extend(re.findall('M[A-Z]*\*?', frame))
            orf_xS_F.extend(re.findall('[A-Z]+\*', frame))
        for frame in [frame4, frame5, frame6]:
            orf_MS.extend(re.findall('M[A-Z]*\*', frame))
            orf_xx.extend(re.findall('[A-Z]+\*?', frame))
            orf_Mx.extend(re.findall('M[A-Z]*\*?', frame))
            orf_xS.extend(re.findall('[A-Z]+\*', frame))
        orf_MS.sort()
        orf_xx.sort()
        orf_Mx.sort()
        orf_xS.sort()
        orf_MS_F.sort()
        orf_xx_F.sort()
        orf_Mx_F.sort()
        orf_xS_F.sort()

        def get(**kwargs):
            res = []
            for start, stop, length, frame in egglib.tools.orf_iter(seq, **kwargs):
                orf = seq[start:stop]
                if frame > 0: aa = egglib.tools.translate(orf)
                else: aa = egglib.tools.translate(egglib.tools.rc(orf))
                ln = len(aa)
                if aa[-1] == '*': ln -= 1
                self.assertEqual(ln, length, msg=seq)
                res.append(aa)
            res.sort()
            return res

        def f(array, mini):
            return [orf for orf in array if len(orf.rstrip('*')) >= mini]

        for mini in 1, 10, 20, 50, 100, 200, 500, 1000:
            self.assertEqual(f(orf_MS, mini), get(min_length=mini), msg=seq)
            self.assertEqual(f(orf_xS, mini), get(force_start=False, min_length=mini), msg=seq)
            a = f(orf_Mx, mini)
            b = get(force_stop=False, min_length=mini)

            self.assertEqual(a, b, msg=seq)
            self.assertEqual(f(orf_xx, mini), get(force_start=False, force_stop=False, min_length=mini), msg=seq)
            self.assertEqual(f(orf_MS_F, mini), get(forward_only=True, min_length=mini), msg=seq)
            self.assertEqual(f(orf_xS_F, mini), get(force_start=False, forward_only=True, min_length=mini), msg=seq)
            self.assertEqual(f(orf_Mx_F, mini), get(force_stop=False, forward_only=True, min_length=mini), msg=seq)
            self.assertEqual(f(orf_xx_F, mini), get(force_start=False, force_stop=False, forward_only=True, min_length=mini), msg=seq)

    def test_orf_iter(self):

        # generate a sequence with one big ORF

        dna = ''.join(random.choices('ACGT', k=random.randint(1000, 10000)))
        self.helper(dna)

        codons = ['AAA', 'AAC', 'AAG', 'AAT', 'ACA', 'ACC', 'ACG', 'ACT', 'AGA', 'AGC',
                  'AGG', 'AGT', 'ATA', 'ATC', 'ATG', 'ATT', 'CAA', 'CAC', 'CAG', 'CAT',
                  'CCA', 'CCC', 'CCG', 'CCT', 'CGA', 'CGC', 'CGG', 'CGT', 'CTA', 'CTC',
                  'CTG', 'CTT', 'GAA', 'GAC', 'GAG', 'GAT', 'GCA', 'GCC', 'GCG', 'GCT',
                  'GGA', 'GGC', 'GGG', 'GGT', 'GTA', 'GTC', 'GTG', 'GTT', 'TAC', 'TAT',
                  'TCA', 'TCC', 'TCG', 'TCT', 'TGC', 'TGG', 'TGT', 'TTA', 'TTC', 'TTG',
                  'TTT']
        stops = ['TAA', 'TAG', 'TGA']
        miss = egglib.alphabets.codons.get_alleles()[1]

        L = 100
        cds = ''.join(random.choices(codons, k=L))
        offset = random.choice([0, 1, 2]) # pick a frame randomly +1, +2 or +3
        rc = random.choice([True, False]) # + frame or - frame

        header = ''.join(random.choices('ACGT', k=3+offset)) + random.choice(stops) # add 3 bases + frame offset and a stop codon at beginning
        footer = random.choice(stops) + ''.join(random.choices('ACGT', k=6+offset))  # add a stop and 6 bases + frame offset at the end (symetrical)

        # test with standard sequence 
        seq = header + 'ATG' + cds + footer
        if rc: seq = egglib.tools.rc(seq)
        start = 6+offset
        stop = 6+offset+3*(L+2)
        frame = offset + 1
        if rc: frame = -frame
        res = list(egglib.tools.orf_iter(seq, min_length=100))
        self.assertIn((start, stop, L+1, frame), res, msg=seq)

        # test without start codon
        seq = header + cds + footer
        if rc: seq = egglib.tools.rc(seq)
        start = 6+offset
        stop = 6+offset+3*(L+1)
        res = list(egglib.tools.orf_iter(seq, min_length=100, force_start=False))
        self.assertIn((start, stop, L, frame), res, msg=seq)

        # insert missing data within sequence
        cds = [cds[i:i+3] for i in range(0, len(cds), 3)]
        for i in range(1, len(cds)):
            if random.random() < 0.1:
                cds[i] = random.choice(miss)
        cds = ''.join(cds)

        seq = header + cds + footer
        if rc: seq = egglib.tools.rc(seq)

        res = list(egglib.tools.orf_iter(seq, min_length=100, force_start=False))
        self.assertIn((start, stop, L, frame), res, msg=seq)

class Outclass_tools_test(unittest.TestCase):

    def test_translate_T(self):
        f_name='sequence.fas'
        aln = egglib.io.from_fasta(str(path / f_name), labels=False, cls=egglib._interface.Align, alphabet=egglib.alphabets.DNA)
        cnt = egglib.io.from_fasta(str(path / f_name), labels=False, cls=egglib._interface.Container, alphabet=egglib.alphabets.DNA)
        seq='ATGGACCCCCTTGGGGACACGCTGCGC'
        aln.to_codons()
        cnt.to_codons()
        aln_prot=egglib.tools.translate(aln, code=1, in_place=False)
        cnt_prot=egglib.tools.translate(cnt, code=1, in_place=False)
        seq_prot=egglib.tools.translate(seq, code=1, in_place=False)
        aln0_prot=egglib.tools.translate(aln.get_sequence(0), code=1, in_place=False)
        file_ = open(path / 'results_prot.txt', 'r').read()
        for i in range(0,4):
            seq_cnt=cnt_prot.get_sequence(i).string()
            seq_aln=aln_prot.get_sequence(i).string()
            r=file_.find(seq_cnt)
            r2=file_.find(seq_aln)
            self.assertTrue(r >= 0) #<-----
            self.assertTrue(r2 >= 0) #<-----
        self.assertEqual(seq_prot, "MDPLGDTLR") #<-----
        self.assertEqual(aln0_prot, aln_prot.get_sequence(0).string()) #<-----

    def test_translate_E(self):
        seq=1510
        with self.assertRaises(ValueError):
            seq_prot=egglib.tools.translate(seq, code=1, in_place=True) #<-----

    def test_orf_iter_T(self):
        #>ENSG00000000457|1|169818772|169819672|ENSP00000356744;ENSP00000356746;ENSP00000407993;ENSP00000356745
        sequence=(
            "GCACCTCTACTGTTTGCTACAAGTGGCCAGCAGCCATTTTGGATTTGGGCGGAAATGAAA"
            "TTAAAACTGTGCTGTTAAAAGCCTAAAAATTCAAGTCAAGACAAACTTAAGCATTCGACC"
            "AACACATCTAGAAAGGGGGCATCTTCGTGGACTAACTAGACCACTGGGGCAGTGAGTGAA"
            "ACTCGGTATCGTCGCGGCGCCCACACTTAAGATGGCACCGGCCTGAGACTCAGCTGTGCG"
            "GCCTCTCTACCTCGGTTCCTGGTTAGTTGGCCTCATTGGTGGCGTCGGAGGGAGGAAGGT"
            "GGGCCTTCTGTCCCGTTTCCGGACCCGTCTCTATGGTGTAGGAGAAACCCGGCCCCCAGA"
            "AGATTGTGGGTGTAGTGGCCACAGCCTTACAGGCAGGCAGGGGTGGTTGGTGTCAACAGG"
            "GGGGCCAACAGGGTACCAGAGCCAAGACCCTCGGCCTCCTCCCCCGCCGCCTTCCTGCAG"
            "GTAACAGGGAGCCCTGCGCTGCGCCCCCAGTCCTTGCAGGACTGCGCCGTGGGGGAAGGG"
            "GCCGGGCGGGGAGGAGGCGGCGGGCGCGCGCCCCGCTCGCGGGTCTGCGCTCTGGGGCCC"
            "GCGCGGGAGCGAGCTCGGCGCGGCGCCGGCGGCCGGTTGAGCTGTGCTCTCAGCTTCGGA"
            "GCAGCCTCCCCTTGCTGATTGTGGGGCGCCCTGTAATCTGCGCTTCGCGGGCGGCCCCCG"
            "ACGGGTGAGGCGCCCGCGGCCAGAGCTCTCCAAGGCGGCCGCGGAGTCGGTCCTCGCAGG"
            "GAGGTGTGGAAGGTGAGGGGCCAGCGAAGCGAGAGCGGCGCCTCGGCCCTTCAGTGACCC"
            "CGCGGGGTCGCGGCAAGCAGGGCGAGGGTGCTCGGCTGGGCGGGTCACTGTCCCGGGGCG")

        ORFs = [] # code to generate the list of ORFs (slightly different algorithm than in EggLib)
        for fr in 1, 2, 3:
            i = fr-1
            orf = None
            while i+4 < len(sequence):
                aa = egglib.tools.translate(sequence[i:i+3], allow_alt=True)
                if orf is None and aa == 'M':
                    orf = i
                if orf is not None and aa == '*':
                    tr = egglib.tools.translate(sequence[orf:i+3])
                    assert tr.count('*') == 1
                    assert tr[-1] == '*'
                    ORFs.append((orf, i+3, len(tr)-1, fr))
                    orf = None
                i += 3
        rc = egglib.tools.rc(sequence)
        def cpos(i): return len(sequence) - i - 1
        for fr in -1, -2, -3:
            i = -fr-1
            orf = None
            while i+4 < len(sequence):
                aa = egglib.tools.translate(rc[i:i+3], allow_alt=True)
                if orf is None and aa == 'M':
                    orf = i
                if orf is not None and aa == '*':
                    tr = egglib.tools.translate(rc[orf:i+3])
                    assert tr.count('*') == 1
                    assert tr[-1] == '*'
                    ORFs.append((cpos(i+2), cpos(orf)+1, len(tr)-1, fr))
                    orf = None
                i += 3

        orf=egglib.tools.orf_iter(sequence,  code=1, min_length=1, forward_only=False, force_start=True, allow_alt=True, force_stop=True)
        self.assertIsInstance(orf, collections.abc.Iterable)
        for i in orf:
            self.assertIn(i, ORFs)

    def test_orf_iter_E(self):
        sequence=("GCACCTCTACTGTTTGCTACAAGTGGCCAGCAGCCATTTTGGATTTGGGCGGAAATGAAA"
              "TTAAAACTGTGCTGTTAAAAGCCTAAAAATTCAAGTCAAGACAAACTTAAGCATTCGACC")
        with self.assertRaises(ValueError):
            orf = egglib.tools.orf_iter(sequence, code=10000)
        with self.assertRaises(ValueError):
            orf2 = egglib.tools.orf_iter(sequence, code=1, min_length=-10)

    def test_longest_orf_T(self):
        #>ENSG00000000457|1|169818772|169819672|ENSP00000356744;ENSP00000356746;ENSP00000407993;ENSP00000356745
        sequence=("GCACCTCTACTGTTTGCTACAAGTGGCCAGCAGCCATTTTGGATTTGGGCGGAAATGAAA"
            "TTAAAACTGTGCTGTTAAAAGCCTAAAAATTCAAGTCAAGACAAACTTAAGCATTCGACC"
            "AACACATCTAGAAAGGGGGCATCTTCGTGGACTAACTAGACCACTGGGGCAGTGAGTGAA"
            "ACTCGGTATCGTCGCGGCGCCCACACTTAAGATGGCACCGGCCTGAGACTCAGCTGTGCG"
            "GCCTCTCTACCTCGGTTCCTGGTTAGTTGGCCTCATTGGTGGCGTCGGAGGGAGGAAGGT"
            "GGGCCTTCTGTCCCGTTTCCGGACCCGTCTCTATGGTGTAGGAGAAACCCGGCCCCCAGA"
            "AGATTGTGGGTGTAGTGGCCACAGCCTTACAGGCAGGCAGGGGTGGTTGGTGTCAACAGG"
            "GGGGCCAACAGGGTACCAGAGCCAAGACCCTCGGCCTCCTCCCCCGCCGCCTTCCTGCAG"
            "GTAACAGGGAGCCCTGCGCTGCGCCCCCAGTCCTTGCAGGACTGCGCCGTGGGGGAAGGG"
            "GCCGGGCGGGGAGGAGGCGGCGGGCGCGCGCCCCGCTCGCGGGTCTGCGCTCTGGGGCCC"
            "GCGCGGGAGCGAGCTCGGCGCGGCGCCGGCGGCCGGTTGAGCTGTGCTCTCAGCTTCGGA"
            "GCAGCCTCCCCTTGCTGATTGTGGGGCGCCCTGTAATCTGCGCTTCGCGGGCGGCCCCCG"
            "ACGGGTGAGGCGCCCGCGGCCAGAGCTCTCCAAGGCGGCCGCGGAGTCGGTCCTCGCAGG"
            "GAGGTGTGGAAGGTGAGGGGCCAGCGAAGCGAGAGCGGCGCCTCGGCCCTTCAGTGACCC"
            "CGCGGGGTCGCGGCAAGCAGGGCGAGGGTGCTCGGCTGGGCGGGTCACTGTCCCGGGGCG")
        orf_l = egglib.tools.longest_orf(sequence, code=1, min_length=1, forward_only=False, force_start=True, allow_alt=True, force_stop=True)
        self.assertEqual(orf_l, (330, 834, 167, -1))

    def test_backalign_T(self):
        cds = egglib.io.from_fasta(str(path / 'LYK.cds'), alphabet=egglib.alphabets.DNA)
        cds.to_codons()
        prot_aln1 = egglib.io.from_fasta(str(path / 'LYK.prot.aln'), alphabet=egglib.alphabets.protein)
        cds_aln = egglib.tools.backalign(cds, prot_aln1)
        self.assertIsInstance(cds_aln, egglib.Align)
        self.assertEqual(''.join(cds.get_sequence(0)[:]), ''.join(cds_aln.get_sequence(0)[:]).replace("-",""))

    def test_backalign_E(self):
        cds = egglib.io.from_fasta(str(path / 'LYK.cds'), alphabet=egglib.alphabets.DNA)
        prot_aln1 = egglib.io.from_fasta(str(path / 'LYK.prot.E.aln'), alphabet=egglib.alphabets.protein)
        with self.assertRaises(ValueError):
            cds_aln = egglib.tools.backalign(cds, prot_aln1)

        cds2 = egglib.io.from_fasta(str(path / 'LYK.E.cds'), alphabet=egglib.alphabets.DNA)
        prot_aln2 = egglib.io.from_fasta(str(path / 'LYK.prot.aln'), alphabet=egglib.alphabets.protein)
        with self.assertRaises(ValueError):
            cds_aln2 = egglib.tools.backalign(cds2, prot_aln2, ignore_names=False)
        with self.assertRaises(ValueError):
            cds_aln2 = egglib.tools.backalign(cds2, prot_aln2, ignore_names=True)

        cds3 = egglib.io.from_fasta(str(path / 'LYK.E2.cds'), alphabet=egglib.alphabets.DNA)
        prot_aln3 = egglib.io.from_fasta(str(path / 'LYK.prot.aln'), alphabet=egglib.alphabets.protein)
        with self.assertRaises(ValueError):
            cds_aln3 = egglib.tools.backalign(cds3, prot_aln3, ignore_names=False)
        with self.assertRaises(ValueError):
            cds_aln3 = egglib.tools.backalign(cds3, prot_aln3, ignore_names=True)

    def test_trailingstop_T(self):
        aln = egglib.io.from_fasta(str(path / 'align_generate.fas'), labels=False, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([(0, 10),(50,70),(120,180),(240,270), (300, 360)])
        aln.to_codons(frame=frame)
        n1_stop=egglib.tools.trailing_stops(aln, action=0)
        n2_stop= egglib.tools.trailing_stops(aln, action=0)
        n3_stop= egglib.tools.trailing_stops(aln, action=0)
        n4_stop= egglib.tools.trailing_stops(aln, action=2, replacement='NNN')
        self.assertEqual(n1_stop, 7)
        self.assertEqual(n2_stop, 7)
        self.assertEqual(n3_stop, 7)
        self.assertEqual(n4_stop, 7)

    def test_trailingstop_E(self):
        aln = egglib.io.from_fasta(str(path / 'align_generate.fas'), labels=False, alphabet=egglib.alphabets.DNA)
        cnt = egglib.io.from_fasta(str(path / 'align_generate.fas'), labels=False, cls=egglib._interface.Container, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([(0, 10),(50,70),(120,180),(240,270), (300, 360)])
        with self.assertRaises(ValueError):
            n1_stop = egglib.tools.trailing_stops(aln, action=0)
        aln.to_codons(frame=frame)
        with self.assertRaises(ValueError):
            n2_stop = egglib.tools.trailing_stops(aln, action=0, code=1000)
        with self.assertRaises(TypeError):
            n3_stop = egglib.tools.trailing_stops(cnt, action=0) # include outgroup was used here
        with self.assertRaises(TypeError):
            n4_stop = egglib.tools.trailing_stops(aln, action=2, replacement=0)

    def test_iter_stops_T(self):
        aln = egglib.io.from_fasta(str(path / 'align_generate.fas'), labels=False, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([(0, 10),(50,70),(120,180),(240,270), (300, 360)])
        aln.to_codons(frame=frame)
        l_stop=list(egglib.tools.iter_stops(aln))
        r_stop=[(1, 9), (1, 20), (1, 59), (2, 55), (3, 14), (3, 59), (4, 33), (4, 58), (4, 59), (5, 3), (5, 23), (6, 16), (6, 59), (7, 28), (7, 57), (7, 59), (8, 46), (8, 57), (8, 59), (9, 24), (9, 54), (9, 56), (9, 59)]
        self.assertEqual(l_stop, r_stop)

    def test_iter_stops_E(self):
        aln = egglib.io.from_fasta(str(path / 'align_generate.fas'), labels=False, alphabet=egglib.alphabets.DNA)
        cnt = egglib.io.from_fasta(str(path / 'align_generate.fas'), labels=False, cls=egglib._interface.Container, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([(0, 10),(50,70),(300, 360)])
        cnt1 = egglib.tools.to_codons(cnt)
        aln1 = egglib.tools.to_codons(aln)
        aln2 = egglib.tools.to_codons(aln, frame=frame)

        with self.assertRaises(ValueError):
            for i in egglib.tools.iter_stops(aln1, code=1000): pass

    def test_has_stop_T(self):
        aln = egglib.io.from_fasta(str(path / 'align_generate.fas'), labels=False, alphabet=egglib.alphabets.DNA)
        aln1 = egglib.tools.to_codons(aln)
        self.assertTrue(egglib.tools.has_stop(aln1, code=1))
        frame = egglib.tools.ReadingFrame([(0, 10)])
        aln2 = egglib.tools.to_codons(aln, frame=frame)
        self.assertFalse(egglib.tools.has_stop(aln2, code=1))
