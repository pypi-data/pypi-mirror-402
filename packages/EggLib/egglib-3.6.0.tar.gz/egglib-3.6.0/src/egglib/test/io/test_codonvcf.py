"""
    Copyright 2025 Stéphane De Mita

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

import itertools, egglib, unittest, tempfile, pathlib

class CodonVCF_test(unittest.TestCase):
    def create_temp(self, suffix):
        tp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tp.close()
        self.temp_files.append(tp.name)
        return tp.name

    def setUp(self):
        # create temporary files
        self.temp_files = []
        self.fas = self.create_temp('.fas')
        self.fas_shorter = self.create_temp('.fas')
        self.gff3 = self.create_temp('.gff3')
        self.gff3_with_ref = self.create_temp('.gff3')
        self.vcf = self.create_temp('.vcf')
        self.bcf = self.create_temp('.bcf')
        self.bcf_mism = self.create_temp('.bcf')
        self.bcf_snps = self.create_temp('.bcf')

        # define reference sequence and annotation
        ref = [
               'GGTTATTATTAC',  # intergenic
               'ATGCATGTTCAAC', # exon1 (4 codons + 1bp)
               'GTCAAATATAG',   # intron1
               'AAGCCTGG',      # exon2 (2bp + 2 codons)
               'GTCAAAAAAG',    # intron2
               'CAATGGTGA',     # exon3 (3 codons)
               'TTTCT'          # intergenic
               ]
        L = len(''.join(ref))

        # derive exon bounds automatically
        def get_cds(ref):
            cur = 0
            bounds = []
            for segment in ref:
                bounds.append((cur, cur+len(segment)))
                cur += len(segment)
            acc = 0
            cds = []
            for a, b in itertools.islice(bounds, 1, None, 2):
                cds.append((a, b, acc%3)) # third argument is codon_start-1 (not phase)
                acc += b-a
            return cds
        CDS1 = get_cds(ref)

        # add a reverse cds
        CDS2 = [(18, 22, 2), (26, 31, 0), (39, 41, 1), (44, 51, 0)]

        # export reference sequence
        ref_seq = ''.join(ref)
        with open(self.fas, 'w') as f:
            f.write('>ctg001\n' + ref_seq + '\n')
        with open(self.fas_shorter, 'w') as f:
            f.write('>ctg001\n' + ref_seq[:50] + '\n')

        # export GFF3 files
        phase = [0, 2, 1] # mapping of (codon_start-1) to phase

        with open(self.gff3, 'w') as f:
            f.write('##gff-version 3\n')
            f.write('ctg001\t')   # seqid
            f.write('.\t')        # source
            f.write('chromosome_part\t') # type
            f.write('1\t')        # start
            f.write(f'{L+1}\t')     # end (excluded)
            f.write('.\t')        # score
            f.write('.\t')        # strand
            f.write('.\t')        # phase
            f.write('ID=test;Note=ad hoc dataset') # attributes
            f.write('\n')

            def write_cds(cds, lbl, sign):
                f.write(f'ctg001\t.\tgene\t{cds[0][0]+1}\t{cds[-1][1]+1}\t.\t{sign}\t.\tID=gene{lbl};Name=gene\n')
                f.write(f'ctg001\t.\tmRNA\t{cds[0][0]+1}\t{cds[-1][1]+1}\t.\t{sign}\t.\tID=mRNA{lbl};Name=mRNA;Parent=gene{lbl}\n')
                for idx, exon in enumerate(cds):
                    f.write(f'ctg001\t.\texon\t{exon[0]+1}\t{exon[1]+1}\t.\t{sign}\t.\tID=exon{lbl}-{idx+1:0>2};Parent=mRNA{lbl}\n')
                    f.write(f'ctg001\t.\tCDS\t{exon[0]+1}\t{exon[1]+1}\t.\t{sign}\t{phase[exon[2]]}\tID=cds{lbl};Parent=mRNA{lbl}\n')
            write_cds(CDS1, '1', '+')
            write_cds(CDS2, '2', '-')

        with open(self.gff3_with_ref, 'w') as f:
            f.write(open(self.gff3).read())
            f.write('##FASTA\n')
            f.write(open(self.fas).read())

        # validate GFF3
        egglib.io.GFF3(self.gff3)
        egglib.io.GFF3(self.gff3_with_ref)

        # encoding of polymorphisms
        pols = [
            ( 8, ['T', 'C'],               ['1/1', '0/0', '0/0', '0/0']), # non-coding
            (17, ['T', 'C', 'A'],          ['0/0', '1/1', '0/2', '0/0']), # 1 hit / 3 alls syn+nsyn
            (20, ['T', 'C', 'A'],          ['0/0', '0/0', '1/2', '0/0']), # 1 hit / 3 alls syn
            (22, ['A', 'G'],               ['./.', './.', '1/1', '0/1']), # nsyn, missing data
            (24, ['CGTCAAATATAGAAG', 'C'], ['1/1', '1/1', '0/0', '0/0']), # deletion of an intron and part of two codons
            (25, ['G', '*'],               ['1/1', '0/0', '0/0', '0/0']),
            (26, ['T', '*'],               ['1/1', '0/0', '0/0', '0/0']),
            (27, ['C', '*'],               ['1/1', '0/0', '0/0', '0/0']),
            (28, ['A', '*'],               ['1/1', '0/0', '0/0', '0/0']),
            (29, ['A', '*'],               ['1/1', '0/0', '0/0', '0/0']),
            (30, ['A', '*'],               ['1/1', '0/0', '0/0', '0/0']),
            (31, ['T', '*'],               ['1/1', '0/0', '0/0', '0/0']),
            (32, ['A', '*'],               ['1/1', '0/0', '0/0', '0/0']),
            (33, ['T', '*'],               ['1/1', '0/0', '0/0', '0/0']),
            (34, ['A', '*'],               ['1/1', '0/0', '0/0', '0/0']),
            (35, ['G', '*'],               ['1/1', '0/0', '0/0', '0/0']),
            (36, ['A', '*'],               ['1/1', '0/0', '0/0', '0/0']),
            (37, ['A', 'G', '*'],          ['2/2', '0/1', '0/0', '1/1']), # syn, gap (= missing data)
            (38, ['G', '*'],               ['1/1', '0/0', '0/0', '0/0']),
            (43, ['G', 'A'],               ['0/0', '1/1', '1/1', '0/0']), # stop codon
            (54, ['C', 'T', 'G'],          ['0/0', '0/0', '1/2', '0/0']), # 3 alls: stop + 1 nsyn variation (not visible on subsample)
            (57, ['T', 'C'],               ['0/0', '1/1', '1/1', '0/0']), # 2 hits / 2 alls nsyn
            (59, ['G', 'C'],               ['0/0', '1/1', '1/1', '0/0']), # second hit
        ]

        # exporting VCF
        with open(self.vcf, 'w') as f:
            f.write('##fileformat=VCFv4.1\n')
            f.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')
            f.write('##contig=<ID=ctg001>\n')
            f.write('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsample1\tsample2\tsample3\tsample4\n')
            i = 0
            pos = 0
            while pos < len(ref_seq):
                done = False
                if i < len(pols) and pols[i][0] == pos:
                    while i < len(pols) and pols[i][0] == pos: # allow several polymorphism in same position
                        assert pols[i][1][0] == ref_seq[pos:pos+len(pols[i][1][0])]
                        f.write(f'ctg001\t{pos+1}\t.\t{pols[i][1][0]}\t{",".join(pols[i][1][1:])}\t.\tPASS\t.\tGT\t{"\t".join(pols[i][2])}\n')
                        if set(all[0] for all in pols[i][1]) != {ref_seq[pos]}: done = True
                        i += 1
                if not done:
                    f.write(f'ctg001\t{pos+1}\t.\t{ref_seq[pos]}\t.\t.\tPASS\t.\tGT\t{"\t".join(["0/0"] * 4)}\n')
                pos += 1

        # convert VCF to BCF
        def VCF2BCF(src, dst):
            VCF = egglib.io.VCF(src, dumpfile=dst)
            while VCF.read():
                VCF.dump_record()
            VCF.dump_close() # ensure the BCF file is flush
            egglib.io.index_vcf(dst)
        VCF2BCF(self.vcf, self.bcf)

        # create BCF with sample size mismatch
        with open(self.vcf) as f: vcf_lines = f.readlines()
        with open(self.vcf, 'w') as f:
            for line in vcf_lines:
                bits = line.rstrip().split('\t')
                if len(bits) > 1 and bits[1] == '13':
                    for i in range(9, 13):
                        if bits[i] != '0/0': raise RuntimeError('internal error')
                        bits[i] = '0'
                    f.write('\t'.join(bits) + '\n')
                else:
                    f.write(line)
        VCF2BCF(self.vcf, self.bcf_mism)

        # create BCF with only SNPs
        VCF = egglib.io.VCF(self.bcf, dumpfile=self.bcf_snps)
        while VCF.read():
            if VCF.is_snp(): VCF.dump_record()
        VCF.dump_close()
        egglib.io.index_vcf(self.bcf_snps)

        # create CodonVCF object
        self.cVCF = egglib.io.CodonVCF(self.bcf, self.gff3)

    def tearDown(self):
        for fname in self.temp_files:
            p = pathlib.Path(fname)
            if p.is_file(): p.unlink()

    def test_iter_codons_E(self):
        with self.assertRaisesRegex(ValueError, '^a CDS feature must be specified first$'):
            list(self.cVCF.iter_codons())

        with self.assertRaisesRegex(ValueError, '^cannot find CDS with ID: wrong$'):
            self.cVCF.set_cds('wrong')

    def test_iter_codons_(self):
        self.cVCF.set_cds('cds1')
        it = self.cVCF.iter_codons()
        for i in it: pass

    def test_check_iter(self):
        expect = [
        #    valid   stop    mhit    mmut    variable syn     nsyn   var    ns  miss index
            (True,   False,  False,  False,  False,   False,  False, False, 8,  0,       0),
            (True,   False,  False,  True,   True,    True,   True,  True,  8,  0,       1),
            (True,   False,  False,  True,   True ,   True,   False, True,  8,  0,       2),
            (True,   False,  False,  False,  True,    False,  True,  True,  8,  4,       3),
            (True,   False,  False,  False,  True,    True,   False, True,  8,  2,       4),
            (True,   False,  False,  False,  False,   False,  False, False, 8,  2,       5),
            (False,  True,   False,  False,  False,   False,  False, True , 8,  0,       6),
            (False,  True,   False,  True,   True,    False,  True,  True,  8,  0,       7),
            (True,   False,  True,   False,  True,    False,  True,  True,  8,  0,       8),
            (False,  True,   False,  False,  False,   False,  False, False, 8,  0,       9)
        ]
        self.cVCF.set_cds('cds1')
        it = self.cVCF.iter_codons()
        self.check(it, expect)

    def check(self, it, expect):
        it = self.cVCF.iter_codons()
        for item in it:
            valid, stop, mhit, mmut, variable, syn, nsyn, var, ns, miss, index = expect.pop(0)
            self.assertEqual((item.flag&(item.NCOD|item.MISM|item.UNAVAIL|item.STOP)==0), valid)
            self.assertEqual((item.flag&item.STOP != 0), stop)
            self.assertEqual((item.flag&item.MHIT != 0), mhit)
            self.assertEqual((item.flag&item.MMUT != 0), mmut)
            self.assertEqual((item.flag&item.VAR != 0), var)
            self.assertEqual((item.flag&(item.SYN|item.NSYN)!=0), variable)
            self.assertEqual(item.flag&item.SYN != 0, syn)
            self.assertEqual(item.flag&item.NSYN != 0, nsyn)
            self.assertEqual(len(item), ns)
            self.assertEqual(item.num_missing, miss)
            self.assertEqual(item.codon_index, index)
        self.assertEqual(len(expect), 0)

    def test_from_position(self):
        self.cVCF.set_cds('cds1')
        self.assertEqual(self.cVCF.from_position(8).codon_index, None)
        self.assertEqual(self.cVCF.from_position(50).codon_index, None)
        self.assertEqual(self.cVCF.from_position(12).codon_index, 0)
        site = self.cVCF.from_position(17)
        self.assertEqual(site.flag, site.MMUT | site.SYN | site.NSYN | site.VAR)
        self.assertEqual(site.codon_index, 1)

    def test_reverse(self):
        self.cVCF.set_cds('cds2')
        site = self.cVCF.from_position(20)
        self.assertEqual(site.as_list(), ['AAC', 'AAC', 'AAC', 'AAC', 'GAC', 'TAC', 'AAC', 'AAC'])
        self.assertEqual(site.flag, site.MMUT | site.NSYN | site.VAR)

        expect = [
        #    valid   stop    mhit    mmut    variable syn     nsyn   var     ns  miss  index
            (True,   False,  False,  False,  False,   False,  False, False,  8,  0,    0),
            (False,  True,   False,  False,  False,   False,  False, False,  8,  0,    1),
            (True,   False,  False,  False,  False,   False,  False, False,  8,  0,    2),
            (True,   False,  False,  False,  False,   False,  False, False,  8,  2,    3),
            (True,   False,  False,  False,  False,   False,  False, False,  8,  2,    4),
            (True,   False,  False,  True,   True,    False,  True,  True,   8,  0,    5)]

        it = self.cVCF.iter_codons()
        self.check(it, expect)

    def test_subsample(self):
        self.cVCF.set_cds('cds1', subset=[1,3])
        it = self.cVCF.iter_codons()

        expect = [
        #    valid   stop    mhit    mmut    variable syn     nsyn    var     ns  miss  index
            (True,   False,  False,  False,  False,   False,  False,  False,  4,  0,    0),
            (True,   False,  False,  False,  True,    True,   False,  True,   4,  0,    1),
            (True,   False,  False,  False,  False ,  False,  False,  False,  4,  0,    2),
            (True,   False,  False,  False,  True,    False,  True,   True,   4,  2,    3),
            (True,   False,  False,  False,  True,    True,   False,  True,   4,  0,    4),
            (True,   False,  False,  False,  False,   False,  False,  False,  4,  0 ,   5),
            (False,  True,   False,  False,  False,   False,  False,  False,  4,  0,    6),
            (True,   False,  False,  False,  False,   False,  False,  False,  4,  0,    7),
            (True,   False,  True,   False,  True,    False,  True,   True,   4,  0,    8),
            (False,  True,   False,  False,  False,   False,  False,  False,  4,  0,    9)
        ]

        self.check(it, expect)

    def test_constructor_errors(self):
        with self.assertRaisesRegex(ValueError, '^VCF file must be indexed$'):
            egglib.io.CodonVCF(self.vcf, self.gff3)
        with self.assertRaisesRegex(ValueError, '^a reference genome must be provided$'):
            egglib.io.CodonVCF(self.bcf, self.gff3, fill_with_ref=True)
        egglib.io.CodonVCF(self.bcf, self.gff3_with_ref, fill_with_ref=True)
        with self.assertRaisesRegex(TypeError, '^`ref` must be a Container instance$'):
            egglib.io.CodonVCF(self.bcf, self.gff3, fill_with_ref=True, ref=self.fas)
        ref = egglib.io.from_fasta(self.fas, cls=egglib.Container, alphabet=egglib.alphabets.DNA)
        egglib.io.CodonVCF(self.bcf, self.gff3, fill_with_ref=True, ref=ref)

    def test_ncod(self):
        self.cVCF.set_cds('cds1')
        site = self.cVCF.from_position(25)
        self.assertEqual(site.flag, site.NCOD)
        self.assertFalse(site.is_valid())
        site = self.cVCF.from_position(12)
        self.assertEqual(site.flag, 0)
        self.assertTrue(site.is_valid())

    def test_mism(self):
        cVCF = egglib.io.CodonVCF(self.bcf_mism, self.gff3)
        cVCF.set_cds('cds1')
        site = cVCF.from_position(12)
        self.assertEqual(site.flag, site.MISM)

    def test_unavail(self):
        cVCF = egglib.io.CodonVCF(self.bcf_snps, self.gff3)
        cVCF.set_cds('cds1')
        site = cVCF.from_position(12) # missing position
        self.assertEqual(site.flag, site.UNAVAIL)
        site = cVCF.from_position(16) # missing position in codon with SNP
        self.assertEqual(site.flag, site.UNAVAIL)
        site = cVCF.from_position(17) # SNP position with missing codon mates
        self.assertEqual(site.flag, site.UNAVAIL)

        cVCF = egglib.io.CodonVCF(self.bcf_snps, self.gff3_with_ref, fill_with_ref=True)
        cVCF.set_cds('cds1')
        site = cVCF.from_position(12)
        self.assertEqual(site.flag, site.UNAVAIL)
        site = cVCF.from_position(16) # missing position in codon with a SNP (filled by ref)
        self.assertEqual(site.flag, site.SYN | site.NSYN | site.MMUT | site.VAR)

        ref = egglib.io.from_fasta(self.fas, cls=egglib.Container, alphabet=egglib.alphabets.DNA)
        cVCF = egglib.io.CodonVCF(self.bcf_snps, self.gff3, fill_with_ref=True, ref=ref)
        cVCF.set_cds('cds1')
        site = cVCF.from_position(12)
        self.assertEqual(site.flag, site.UNAVAIL)
        site = cVCF.from_position(16) # missing position in codon with a SNP (filled by ref)
        self.assertEqual(site.flag, site.SYN | site.NSYN | site.MMUT | site.VAR)

    def test_stop(self):
        self.cVCF.set_cds('cds1')
        for i in range(41, 44):
            site = self.cVCF.from_position(i)
            self.assertEqual(site.flag, site.STOP | site.VAR)
            self.assertEqual(set(site.as_list()), {'TGG', 'TGA'})
            self.assertEqual(site.ns, 8)
            self.assertEqual(site.num_missing, 0)
        for i in range(60, 63):
            site = self.cVCF.from_position(i)
            self.assertEqual(site.flag, site.STOP)
            self.assertEqual(set(site.as_list()), {'TGA'})
            self.assertEqual(site.ns, 8)
            self.assertEqual(site.num_missing, 0)

    def test_shorter_ref(self):
        ref = egglib.io.from_fasta(self.fas_shorter, cls=egglib.Container, alphabet=egglib.alphabets.DNA)
        cVCF = egglib.io.CodonVCF(self.bcf_snps, self.gff3, fill_with_ref=True, ref=ref)
        cVCF.set_cds('cds1')
        site = cVCF.from_position(20) # within range of ref
        self.assertEqual(site.flag, site.SYN | site.MMUT | site.VAR)
        with self.assertRaisesRegex(ValueError, '^cannot find site in reference while filling a gap in VCF$'):
            site = cVCF.from_position(58) # out of range of ref

        ref = egglib.io.from_fasta(self.fas, cls=egglib.Container, alphabet=egglib.alphabets.DNA)
        cVCF = egglib.io.CodonVCF(self.bcf_snps, self.gff3, fill_with_ref=True, ref=ref)
        cVCF.set_cds('cds1')
        site = cVCF.from_position(58)
        self.assertEqual(site.flag, site.NSYN | site.MHIT | site.VAR)

    def test_manual_code(self):
        cVCF = egglib.io.CodonVCF(self.bcf, self.gff3)
        cVCF.set_cds('cds1')
        L = 0
        NS = 0
        S = 0
        V = 0
        for site in cVCF.iter_codons():
            if (site.flag & (site.STOP | site.MMUT)) == 0:
                L += 1
                if (site.flag & site.VAR) != 0: V += 1
                if (site.flag & site.NSYN) != 0: NS += 1
                if (site.flag & site.SYN) != 0: S += 1
        self.assertEqual(NS + S, V)
        self.assertLessEqual(V, L)
