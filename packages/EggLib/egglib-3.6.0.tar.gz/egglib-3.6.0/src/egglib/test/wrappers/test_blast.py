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

import egglib, os, re, unittest, tempfile, shutil, pathlib

path = pathlib.Path(__file__).parent / '..' / 'data'

fname1 = str(path / 'nucl_data.fas')
fname2 = str(path / 'prot_data.fas')
fname3 = str(path / 'simul-cds.fas')
mask1 = str(path / 'mask_nucl_dustmasker.asnb')
mask2 = str(path / 'mask_nucl_windowmasker.asnb')

class makeblastdb_test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.dnadb = egglib.io.from_fasta(fname1, alphabet=egglib.alphabets.DNA)
        self.protdb = egglib.io.from_fasta(fname2, alphabet=egglib.alphabets.protein)

    def tmpf(self, fname):
        return pathlib.Path(self.tmp) / fname

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_dbtype(self):
        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(self.protdb, dbtype='nucl')
        self.assertIn('alphabet/dbtype mismatch', str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(self.dnadb, dbtype='prot')
        self.assertIn('alphabet/dbtype mismatch', str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(self.dnadb, dbtype='prout')
        self.assertIn('alphabet/dbtype mismatch', str(cm.exception))

    def test_out(self):
        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(self.dnadb)
        self.assertIn('`out` is required', str(cm.exception))
        with self.assertRaises(TypeError):
            egglib.wrappers.makeblastdb(self.dnadb, out=100)

        # successfull database creation
        egglib.wrappers.makeblastdb(self.dnadb, out=self.tmpf('test1'))
        self.assertTrue(self.tmpf('test1.nhr').is_file())
        self.assertTrue(self.tmpf('test1.nsq').is_file())
        self.assertTrue(self.tmpf('test1.nin').is_file())

        egglib.wrappers.makeblastdb(self.protdb, out=self.tmpf('test2'))
        self.assertTrue(self.tmpf('test2.phr').is_file())
        self.assertTrue(self.tmpf('test2.psq').is_file())
        self.assertTrue(self.tmpf('test2.pin').is_file())

        shutil.copy(fname1, self.tmpf('a.fas'))
        egglib.wrappers.makeblastdb(self.tmpf('a.fas'), dbtype='nucl')
        self.assertTrue(self.tmpf('a.fas.nhr').is_file())
        self.assertTrue(self.tmpf('a.fas.nsq').is_file())
        self.assertTrue(self.tmpf('a.fas.nin').is_file())

        # error in case blastdb is used: must be different name
        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(self.tmpf('a.fas'), dbtype='nucl', input_type='blastdb')
        self.assertIn('a different database name is required for input type `blastdb`', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(self.tmpf('a.fas'), dbtype='nucl', input_type='blastdb', out=self.tmpf('a.fas'))
        self.assertIn('a different database name is required for input type `blastdb`', str(cm.exception))

        egglib.wrappers.makeblastdb(self.tmpf('a.fas'), dbtype='nucl', input_type='blastdb', out=self.tmpf('b.fas'))
        self.assertTrue(self.tmpf('b.fas.nhr').is_file())
        self.assertTrue(self.tmpf('b.fas.nsq').is_file())
        self.assertTrue(self.tmpf('b.fas.nin').is_file())

    def test_source(self):
        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb('non-existent')
        self.assertIn('file not found', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1)
        self.assertIn('`dbtype` is required', str(cm.exception))

        egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'))
        self.assertTrue(self.tmpf('test1.nhr').is_file())
        self.assertTrue(self.tmpf('test1.nsq').is_file())
        self.assertTrue(self.tmpf('test1.nin').is_file())

        egglib.wrappers.makeblastdb(fname2, dbtype='prot', out=self.tmpf('test2'))
        self.assertTrue(self.tmpf('test2.phr').is_file())
        self.assertTrue(self.tmpf('test2.psq').is_file())
        self.assertTrue(self.tmpf('test2.pin').is_file())

    def test_input_type(self):
        egglib.wrappers.makeblastdb(self.dnadb, out=self.tmpf('test1'))
        self.assertTrue(self.tmpf('test1.nhr').is_file())
        self.assertTrue(self.tmpf('test1.nsq').is_file())
        self.assertTrue(self.tmpf('test1.nin').is_file())

        egglib.wrappers.makeblastdb(self.dnadb, out=self.tmpf('test2'), input_type='fasta')
        self.assertTrue(self.tmpf('test2.nhr').is_file())
        self.assertTrue(self.tmpf('test2.nsq').is_file())
        self.assertTrue(self.tmpf('test2.nin').is_file())

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(self.dnadb, out=self.tmpf('test1'), input_type='asn1_bin')
        self.assertIn('`input_type` must be "fasta"', str(cm.exception))

        with self.assertRaises(RuntimeError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', input_type='asn1_bin')
        self.assertIn('error while running makeblastdb', str(cm.exception))

        with self.assertRaises(RuntimeError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', input_type='asn1_txt')
        self.assertIn('error while running makeblastdb', str(cm.exception))

        with self.assertRaises(RuntimeError) as cm:
            egglib.wrappers.makeblastdb(self.tmpf('test_non_existent'), dbtype='nucl', input_type='blastdb', out=self.tmpf('prout'))
        self.assertIn('error while running makeblastdb', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', input_type='confuse_a_cat')
        self.assertIn('invalid value for `input_type`', str(cm.exception))

    def test_title(self):
        stdout = egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'))
        self.assertIsNotNone(re.search('New DB title: +' + re.escape(fname1), stdout))

        stdout = egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), title='A Database Title')
        self.assertIsNotNone(re.search('New DB title: +A Database Title', stdout))

        stdout = egglib.wrappers.makeblastdb(self.protdb, out=self.tmpf('test1'))
        self.assertIsNotNone(re.search('New DB title: +prot database from an EggLib Container', stdout))

    def test_parse_seqids(self):
        for i in self.dnadb: i.name = 'seq'
        with self.assertRaises(RuntimeError) as cm:
            egglib.wrappers.makeblastdb(self.dnadb, dbtype='nucl', out=self.tmpf('test1'), parse_seqids=True)
        self.assertIn('Duplicate seq_ids are found', str(cm.exception))
        egglib.wrappers.makeblastdb(self.dnadb, dbtype='nucl', out=self.tmpf('test1'), parse_seqids=False)

    def test_hash_index(self):
        egglib.wrappers.makeblastdb(self.dnadb, dbtype='nucl', out=self.tmpf('test2'), hash_index=True)
        self.assertTrue(self.tmpf('test2.nhi').is_file())

    def test_mask_data(self):
        egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'))
        with self.assertRaises(TypeError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_data=mask1)
        self.assertIn('`mask_data` must be a list or a tuple', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_data=[])
        self.assertIn('there must be at least one item in `mask_data`', str(cm.exception))

        egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_data=[mask1], parse_seqids=True)
        egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_data=[mask1, mask2], parse_seqids=True)
            # it is required to use parse_seqids because it has been used for creating masks

    def test_mask_id(self):
        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_id=[])
        self.assertIn('`mask_id` requires `mask_data`', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_id=['dustmasker', 'windowmasker'])
        self.assertIn('`mask_id` requires `mask_data`', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_data=[mask1, mask2], mask_id=[])
        self.assertIn('`mask_id` must have the same length than `mask_data`', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_data=[mask1, mask2], mask_id=['dustmasker'])
        self.assertIn('`mask_id` must have the same length than `mask_data`', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_data=[mask1, mask2], mask_id=['dustmasker', 'windowmasker', 'napolmasker'])
        self.assertIn('`mask_id` must have the same length than `mask_data`', str(cm.exception))

        egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_data=[mask1], mask_id=['dustmasker'], parse_seqids=True)
        egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_data=[mask1, mask2], mask_id=['dustmasker', 'windowmasker'], parse_seqids=True)

    def test_mask_desc(self):
        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_desc=[])
        self.assertIn('`mask_desc` requires `mask_id`', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_id=['a'], mask_desc=['a'])
        self.assertIn('`mask_id` requires `mask_data`', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_data=[mask1, mask2], mask_id=['dustmasker', 'windowmasker'], mask_desc=[])
        self.assertIn('`mask_desc` must have the same length than `mask_data`', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_data=[mask1, mask2], mask_id=['dustmasker', 'windowmasker'], mask_desc=['dustmasker'])
        self.assertIn('`mask_desc` must have the same length than `mask_data`', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_data=[mask1, mask2], mask_id=['dustmasker', 'windowmasker'], mask_desc=['dustmasker', 'windowmasker', 'napolmasker'], parse_seqids=True)
        self.assertIn('`mask_desc` must have the same length than `mask_data`', str(cm.exception))

        egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_data=[mask1], mask_id=['dustmasker'], mask_desc=['a mask based on dust'], parse_seqids=True)
        egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), mask_data=[mask1, mask2], mask_id=['dustmasker', 'windowmasker'], mask_desc=['a mask based on dust', 'a mask based on windows'], parse_seqids=True)

    def test_blastdb_version(self):
        with self.assertRaises(TypeError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), blastdb_version='4')
        self.assertIn('must be an integer', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), blastdb_version=1)
        self.assertIn('supported values for `blastdb_version` are 4 and 5 only', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), blastdb_version=3)
        self.assertIn('supported values for `blastdb_version` are 4 and 5 only', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), blastdb_version=6)
        self.assertIn('supported values for `blastdb_version` are 4 and 5 only', str(cm.exception))

        egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test.v4'), blastdb_version=4)
        egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test.v5'), blastdb_version=5)

    def test_max_file_sz(self):
        with self.assertRaises(TypeError) as cm:
            egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), max_file_sz=10)
        self.assertIn('must be a string', str(cm.exception))

        egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test1'), max_file_sz="150MB")
        egglib.wrappers.makeblastdb(fname1, dbtype='nucl', out=self.tmpf('test2'), max_file_sz="2GB")

    def test_taxid(self):
        cnt = egglib.Container.create(alphabet=egglib.alphabets.protein, source=[
            ('seq1', 'MSFSTKPLDMATWPDFAALVERHNGVWGGCWCMAFHAKGSGAVGNREAKEARVREGSTHAALVFDGSACVGWCQFGPTGELPRIKHLRAYEDGQAVLPDWRITCFFSDKAFRGKGVAAAALAGALAEIGRLGGGTVESYPEDAQGRTVAGAFLHNGTLAM'),
            ('seq2', 'MKAIDLKAEEKKRLIEGIQDFFYEERNEEIGIIAAEKALDFFLSGVGKLIYNKALDESKIWFSRRLEDISLDYELLYK'),
            ('seq3', 'MTLAAAAQSATWTFIDGDWYEGNVAILGPRSHAMWLGTSVFDGARWFEGVAPDLELHAARVNASAIALGLAPNMTPEQIVGLTWDGLKKFDGKTAVYIRPMYWAEHGGYMGVPADPASTRFCLCLYESPMISPTGFSVTVSPFRRPTIETMPTNAKAGCLYPNNGRAILEAKARGFDNALVLDMLGNVAETGSSNIFLVKDGHVLTPAPNGTFLSGITRSRTMTLLGDYGFRTTEKTLSVRDFLEADEIFSTGNHSKVVPITRIEGRDLQPGPVAKKARELYWDWAHSASVG'),
            ('seq4', 'MRSFFHHVAAADPASFGVAQRVLTIPIKRAHIEVTHHLTKAEVDALIAAPNPRTSRGRRDRTFLLFLARTGARVSEATGVNANDLQLERSHPQVLLRGKGRRDRVIPIPQDLARALTALLAEHGIANHEPRPIFIGARQERLTRFGATHIVRRAAAQAVTIKPALAHKPISPHIFRHSLAMKLLQSGVDLLTIQAWLGHAQVATTHRYAAADVEMMRKGLEKAGVSGDLGLRFRPNDAVLQLLTSI'),
            ('seq5', 'MTISRVCGSRTEAMLTNGQEIAMTSILKSTGAVALLLLYTLTANATSLMISPSSIERVAPDRAAVFHLRNQMDRPISIKVRVFRWSQKGGVEKLEPTGDVVASPISAQLSPNGNRAVRVVRVSKEPLRSEEGYRVVIDEADPTRNTPEAESLSARHVLPVLFRPPDVLGPEIELSLTRSDGWLMLVVENKGASRLRRSDVTLAQGSAGIARREGFVGYVLPGLTRHWRVGREDSYSGGIVTVSANSSGGAIGEQLVVSGR'),
            ('seq6', 'TTLLLQVPIGWGVLHQGGALVVLGFAIAHWRGFVGTYTRDTAIEMRD')])

        f = open(self.tmpf('test_map.txt'), 'w')
        f.write("""lcl|seq1 68287
lcl|seq2 2382161
lcl|seq3 68287
lcl|seq4 382
lcl|seq5 382
lcl|seq6 382
""")
        f.close()

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(cnt, out=self.tmpf('test1'), taxid_map=self.tmpf('test_map.txt'))
        self.assertIn('`taxid_map` requires `parse_seqids`', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(cnt, out=self.tmpf('test1'), taxid_map=self.tmpf('prout.txt'), parse_seqids=True)
        self.assertIn('file passed for `taxid_map` not found', str(cm.exception))

        egglib.wrappers.makeblastdb(cnt, out=self.tmpf('test1'), taxid_map=self.tmpf('test_map.txt'), parse_seqids=True)
        egglib.wrappers.makeblastdb(self.tmpf('test1'), input_type='blastdb', dbtype= 'prot', out=self.tmpf('test2'), taxid_map=self.tmpf('test_map.txt'))

        with self.assertRaises(TypeError) as cm:
            egglib.wrappers.makeblastdb(cnt, parse_seqids=True, out=self.tmpf('test1'), taxid='382')
        self.assertIn('must be an integer', str(cm.exception))

        with self.assertRaises(TypeError) as cm:
            egglib.wrappers.makeblastdb(cnt, parse_seqids=True, out=self.tmpf('test1'), taxid=382.0)
        self.assertIn('`taxid` must be an integer', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(cnt, parse_seqids=True, out=self.tmpf('test1'), taxid=-1)
        self.assertIn('`taxid` must be >= 0', str(cm.exception))

        with self.assertRaises(ValueError) as cm:
            egglib.wrappers.makeblastdb(cnt, parse_seqids=True, out=self.tmpf('test1'), taxid_map=self.tmpf('test_map.txt'), taxid=382)
        self.assertIn('`taxid` and `taxid_map` are incompatible', str(cm.exception))

        egglib.wrappers.makeblastdb(cnt, out=self.tmpf('test3'), taxid=382)

class blastn_test(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.nucl = egglib.io.from_fasta(fname1, alphabet=egglib.alphabets.DNA)
        self.nucldb = str(self.tmp / 'nucl')
        egglib.wrappers.makeblastdb(self.nucl, out=self.nucldb)
        self.cnt = egglib.Container.create([
            ('name1', 'ACCGCGGAGCGCCGGAGAGCCCGCGGAGCTAGAGCTCTAGGAGCCT'),
            ('name2', 'ACGGTtgcccgcgaagcccgaagtgcgcgaGAGCGCCGGAGA'),
            ('name3', 'ATTGCAGTTGAGCCGCGAGTTGCGCATTGTTGCCGAGAGCGCGCCCGCGAAA'),
            ('name4', 'TTtgcccgcgaagcccgaagtgcgcgaAACCCGGAAAGtgcccgcgaagcccgaagtgcgcgaAG'),
            ('name5', 'TTGAGCCGAGAGCCGCGCGAGGAAGCGCCGCCGGTTGGCCGAGAGAGAAAGG')],
                    alphabet=egglib.alphabets.DNA)
        self.cntdb = str(self.tmp / 'cnt')
        egglib.wrappers.makeblastdb(self.cnt, out=self.cntdb)

        self.seq1 = 'ACCGCGGAGCGCCGGAGAGCCCGCGGAGCTAGAGCTCTAGGAGCCT'
        self.seq2 = 'ATTGCAGTTGAGCCGCGAGTTGCGCATTGTTGCCGAGAGCGCGCCCGCGAAA'
        self.query_align = egglib.Align.create([('q1', self.seq1[:40]), ('q2', self.seq2[:40])], alphabet=egglib.alphabets.DNA)
        self.query_cont = egglib.Container.create([('q1', self.seq1), ('q2', self.seq2)], alphabet=egglib.alphabets.DNA)
        self.init_path = pathlib.Path.cwd()

    def tearDown(self):
        os.chdir(self.init_path)
        shutil.rmtree(self.tmp)

    def test_blastn(self):
        res = egglib.wrappers.blastn(self.nucl[0], subject=self.nucl[0], parse_deflines=True,
                    query_loc=[0, 1000], subject_loc=[0, 500], evalue=1e-10,
                    num_threads=1, word_size=7, reward=2, penalty=-3, gapopen=4, gapextend=4,
                    no_dust=True, no_soft_masking=True)

        self.assertEqual(res.program, 'blastn')
        self.assertIsNone(res.db)
        self.assertEqual(res.query_ID, self.nucl.get_name(0))
        self.assertEqual(res.query_def, 'No definition line')
        self.assertEqual(res.query_len, 1000)
        self.assertEqual(res.params['expect'], 1e-10)
        self.assertEqual(res.params['sc-match'], 2)
        self.assertEqual(res.params['sc-mismatch'], -3)
        self.assertEqual(res.params['gap-open'], 4)
        self.assertEqual(res.params['gap-extend'], 4)
        self.assertEqual(res.params['filter'], 'F')
        self.assertNotIn('matrix', res.params)
        self.assertEqual(len(res), 1)
        [query] = res[:]
        self.assertEqual(query.num, 0)
        self.assertEqual(query.query_ID, self.nucl.get_name(0))
        self.assertEqual(query.query_def, 'No definition line')
        self.assertEqual(query.query_len, 1000)
        self.assertEqual(query.db_num, 0)
        self.assertEqual(query.db_len, 0)
        self.assertEqual(len(query), 1)
        [hit] = query[:]
        self.assertEqual(hit.num, 0)
        self.assertEqual(hit.id, self.nucl.get_name(0))
        self.assertEqual(hit.descr, 'No definition line')
        self.assertEqual(hit.accession, self.nucl.get_name(0))
        self.assertEqual(hit.len, self.nucl.get_sample(0).ls)
        self.assertEqual(len(hit), 1)
        [Hsp] = hit[:]
        self.assertEqual(Hsp.num, 0)
        self.assertLess(Hsp.evalue, 1e-20)
        self.assertEqual(Hsp.query_start, 0)
        self.assertEqual(Hsp.query_stop, 500)
        self.assertEqual(Hsp.query_frame, 1)
        self.assertEqual(Hsp.hit_start, 0)
        self.assertEqual(Hsp.hit_stop, 500)
        self.assertEqual(Hsp.hit_frame, 1)
        self.assertEqual(Hsp.identity, 500)
        self.assertEqual(Hsp.positive, 500)
        self.assertEqual(Hsp.gaps, 0)
        self.assertEqual(Hsp.align_len, 500)
        self.assertEqual(Hsp.qseq, self.nucl.get_sequence(0)[:500])
        self.assertEqual(Hsp.midline, '|' * 500)
        self.assertEqual(Hsp.hseq, self.nucl.get_sequence(0)[:500])

    def test_megablast_reverse(self):
        seq = egglib.tools.rc(self.nucl[0].sequence)
        ls = len(seq)
        res = egglib.wrappers.megablast(seq, subject=self.nucl[0], parse_deflines=True,
                    evalue=1e-10, num_threads=1, word_size=7,
                    reward=2, penalty=-3, gapopen=4, gapextend=4,
                    no_dust=False, no_soft_masking=False)
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res[0]), 1)
        self.assertEqual(len(res[0][0]), 1)
        Hsp = res[0][0][0]
        self.assertEqual(Hsp.query_start, 0)
        self.assertEqual(Hsp.query_stop, ls)
        self.assertEqual(Hsp.hit_start, 0)
        self.assertEqual(Hsp.hit_stop, ls)
        self.assertEqual(Hsp.query_frame, 1)
        self.assertEqual(Hsp.hit_frame, -1)

    def test_blastn_short(self):
        q = 'tgcccgcgaagcccgaagtgcgcga'
        res = egglib.wrappers.blastn_short(q, db=self.cntdb, evalue=1e-10)
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res[0]), 2)
        if res[0][0].descr == 'name2':
            hit1 = res[0][0]
            hit2 = res[0][1]
        else:
            hit1 = res[0][1]
            hit2 = res[0][0]
        self.assertEqual(hit1.descr, 'name2')
        self.assertEqual(hit2.descr, 'name4')
        self.assertEqual(len(hit1), 1)
        self.assertEqual(len(hit2), 2)
        Hsp1 = hit1[0]
        Hsp2 = hit2[0]
        Hsp3 = hit2[1]
        self.assertEqual(Hsp1.query_start, 0)
        self.assertEqual(Hsp1.query_stop, 25)
        self.assertEqual(Hsp1.hit_start, 5)
        self.assertEqual(Hsp1.hit_stop, 30)
        self.assertEqual(Hsp1.query_frame, 1)
        self.assertEqual(Hsp1.hit_frame, 1)
        self.assertEqual(Hsp2.query_start, 0)
        self.assertEqual(Hsp2.query_stop, 25)
        self.assertEqual(Hsp2.hit_start, 2)
        self.assertEqual(Hsp2.hit_stop, 27)
        self.assertEqual(Hsp2.query_frame, 1)
        self.assertEqual(Hsp2.hit_frame, 1)
        self.assertEqual(Hsp3.query_start, 0)
        self.assertEqual(Hsp3.query_stop, 25)
        self.assertEqual(Hsp3.hit_start, 38)
        self.assertEqual(Hsp3.hit_stop, 63)
        self.assertEqual(Hsp3.query_frame, 1)
        self.assertEqual(Hsp3.hit_frame, 1)
        for Hsp in [Hsp1, Hsp2, Hsp3]:
            self.assertEqual(Hsp.identity, 25)
            self.assertEqual(Hsp.positive, 25)
            self.assertEqual(Hsp.gaps, 0)
            self.assertEqual(Hsp.align_len, 25)
            self.assertEqual(Hsp.qseq, q.upper())
            self.assertEqual(Hsp.midline, '|' * 25)
            self.assertEqual(Hsp.hseq, q.upper())

    def test_query(self):
        for fun in [egglib.wrappers.blastn, egglib.wrappers.blastn_short,
                    egglib.wrappers.megablast, egglib.wrappers.dc_megablast]:

            # pass a string
            res = fun(query=self.seq1, db=self.cntdb, evalue=1e-15)
            self.assertIsInstance(res, egglib.wrappers._blast.BlastOutput)
            self.assertEqual(len(res), 1)
            self.assertEqual(len(res[0]), 1)
            self.assertEqual(res[0][0].descr, 'name1')

            # pass a SampleView
            res = fun(query=self.query_align[0], db=self.cntdb, evalue=1e-15)
            self.assertIsInstance(res, egglib.wrappers._blast.BlastOutput)
            self.assertEqual(len(res), 1)
            self.assertEqual(len(res[0]), 1)
            self.assertEqual(res[0][0].descr, 'name1')

            # pass a SequenceView
            res = fun(query=self.query_align[0].sequence, db=self.cntdb, evalue=1e-15)
            self.assertIsInstance(res, egglib.wrappers._blast.BlastOutput)
            self.assertEqual(len(res), 1)
            self.assertEqual(len(res[0]), 1)
            self.assertEqual(res[0][0].descr, 'name1')

            # pass an Align
            res = fun(query=self.query_align, db=self.cntdb, evalue=1e-15)
            self.assertIsInstance(res, egglib.wrappers._blast.BlastOutput)
            self.assertEqual(len(res), 2)
            self.assertEqual(len(res[0]), 1)
            self.assertEqual(len(res[1]), 1)
            self.assertEqual(res[0][0].descr, 'name1')
            self.assertEqual(res[1][0].descr, 'name3')

            # pass a Container
            res = fun(query=self.query_cont, db=self.cntdb, evalue=1e-10)
            self.assertIsInstance(res, egglib.wrappers._blast.BlastOutput)
            self.assertEqual(len(res), 2)
            self.assertEqual(len(res[0]), 1)
            self.assertEqual(len(res[1]), 1)
            self.assertEqual(res[0][0].descr, 'name1')
            self.assertEqual(res[1][0].descr, 'name3')

            # errors
            with self.assertRaises(TypeError):
                fun(query=list(self.seq1), db=self.cntdb)

    def test_subject(self):
        for fun in [egglib.wrappers.blastn, egglib.wrappers.blastn_short,
                    egglib.wrappers.megablast, egglib.wrappers.dc_megablast]:

            # pass a database
            res = fun(query=self.query_align, db=self.cntdb, evalue=1e-10)
            self.assertIsInstance(res, egglib.wrappers._blast.BlastOutput)
            self.assertEqual(len(res), 2)
            self.assertEqual(len(res[0]), 1)
            self.assertEqual(len(res[1]), 1)
            self.assertEqual(res[0][0].descr, 'name1')
            self.assertEqual(res[1][0].descr, 'name3')

            # cannot pass both
            with self.assertRaises(ValueError):
                fun(query=self.seq1, db=self.cntdb, subject=self.seq1, evalue=1e-10)

            # pass a string
            res = fun(query=self.seq1, subject=self.seq1)
            self.assertEqual(res[0][0][0].identity, len(self.seq1))

            # pass a SampleView
            res = fun(query=self.seq1, subject=self.query_cont[0])
            self.assertEqual(res[0][0][0].identity, len(self.seq1))

            # pass a SequenceView
            res = fun(query=self.seq1, subject=self.query_cont[0].sequence)
            self.assertEqual(res[0][0][0].identity, len(self.seq1))

    def test_loc(self):
        seq = self.nucl[0].sequence

        for fun in [egglib.wrappers.blastn, egglib.wrappers.blastn_short,
                    egglib.wrappers.megablast, egglib.wrappers.dc_megablast]:

            # use query_loc
            res = fun(seq, subject=seq, query_loc=(2000, 2500), evalue=1e-20)
            self.assertEqual(res[0][0][0].qseq, seq[2000:2500])

            res = fun(seq, subject=seq, query_loc=(2000, 150000), evalue=1e-20)
            self.assertEqual(res[0][0][0].qseq, seq[2000:])

            res = fun(self.nucl[0], subject=seq, query_loc=(2000, 150000), evalue=1e-20)
            self.assertEqual(res[0][0][0].qseq, seq[2000:])

            res = fun(self.nucl[0].sequence, subject=seq, query_loc=(2000, 150000), evalue=1e-20)
            self.assertEqual(res[0][0][0].qseq, seq[2000:])

            # invalid values
            with self.assertRaises(ValueError):
                res = fun(seq, subject=seq, query_loc=(-2000, 150000), evalue=1e-20)
            with self.assertRaises(ValueError):
                res = fun(seq, subject=seq, query_loc=(2000, 1000), evalue=1e-20)
            with self.assertRaises(ValueError):
                res = fun(self.nucl[0].sequence, subject=seq, query_loc=(200000, 300000), evalue=1e-20)

            # query must be a string
            with self.assertRaises(ValueError):
                res = fun(self.nucl, subject=seq, query_loc=(2000, 1000), evalue=1e-20)

            # use subject_loc
            res = fun(seq, subject=seq, subject_loc=(2000, 2500), evalue=1e-20)
            self.assertEqual(res[0][0][0].qseq, seq[2000:2500])

            res = fun(seq, subject=seq, subject_loc=(2000, 150000), evalue=1e-20)
            self.assertEqual(res[0][0][0].qseq, seq[2000:])

            res = fun(self.nucl[0], subject=seq, subject_loc=(2000, 150000), evalue=1e-20)
            self.assertEqual(res[0][0][0].qseq, seq[2000:])

            res = fun(self.nucl[0].sequence, subject=seq, subject_loc=(2000, 150000), evalue=1e-20)
            self.assertEqual(res[0][0][0].qseq, seq[2000:])

            res = fun(seq, subject=self.nucl[0], query_loc=(1000, 2500), subject_loc=(1500, 2000), evalue=1e-20)
            self.assertEqual(res[0][0][0].qseq, seq[1500:2000])

            # invalid values
            with self.assertRaises(ValueError):
                res = fun(seq, subject=seq, subject_loc=(-2000, 150000), evalue=1e-20)
            with self.assertRaises(ValueError):
                res = fun(seq, subject=seq, subject_loc=(2000, 1000), evalue=1e-20)
            with self.assertRaises(ValueError):
                res = fun(seq, subject=seq, subject_loc=(200000, 300000), evalue=1e-20)

            # subject must be a string
            with self.assertRaises(ValueError):
                res = fun(seq, subject=self.cntdb, subject_loc=(2000, 1000), evalue=1e-20)

    def test_evalue(self):
        res = egglib.wrappers.blastn_short(query=self.nucl[0], db=self.nucldb)
        self.assertEqual(res.params['expect'], 1000)
        for fun in [egglib.wrappers.blastn, egglib.wrappers.megablast,
                    egglib.wrappers.dc_megablast]:
            res = fun(query=self.nucl[0], db=self.nucldb)
            self.assertEqual(res.params['expect'], 10)

        res = egglib.wrappers.blastn_short(query=self.nucl[0], db=self.nucldb, evalue=1e-10)
        self.assertEqual(res.params['expect'], 1e-10)

        with self.assertRaises(ValueError):
            egglib.wrappers.blastn_short(query=self.nucl[0], db=self.nucldb, evalue=0)

        with self.assertRaises(ValueError):
            egglib.wrappers.blastn_short(query=self.nucl[0], db=self.nucldb, evalue=-1.0)

    def test_parse_deflines(self):
        for fun in [egglib.wrappers.blastn, egglib.wrappers.blastn_short,
                    egglib.wrappers.megablast, egglib.wrappers.dc_megablast]:
            res = egglib.wrappers.blastn_short(query=self.cnt[0], db=self.cntdb, parse_deflines=True)
            self.assertEqual(res.query_ID, self.cnt[0].name)
            res = egglib.wrappers.blastn_short(query=self.cnt[0], db=self.cntdb, parse_deflines=False)
            self.assertNotEqual(res.query_ID, self.cnt[0].name)

    def test_num_threads(self):
        for fun in [egglib.wrappers.blastn, egglib.wrappers.blastn_short,
                    egglib.wrappers.megablast, egglib.wrappers.dc_megablast]:
            res = fun(query=self.nucl[0], db=self.nucldb, num_threads=4)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.blastn_short(query=self.nucl[0], subject=self.nucl[0], num_threads=4)

    def test_word_size(self):
        with self.assertRaises(ValueError):
            res = egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb, word_size=3)
        res = egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb, word_size=4)

        with self.assertRaises(ValueError):
            res = egglib.wrappers.blastn_short(query=self.cnt[0], db=self.cntdb, word_size=3)
        res = egglib.wrappers.blastn_short(query=self.cnt[0], db=self.cntdb, word_size=4)

        with self.assertRaises(ValueError):
            res = egglib.wrappers.megablast(query=self.cnt[0], db=self.cntdb, word_size=3)
        res = egglib.wrappers.megablast(query=self.cnt[0], db=self.cntdb, word_size=4)

        with self.assertRaises(ValueError):
            res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, word_size=4)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, word_size=10)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, word_size=13)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, word_size=28)
        res = egglib.wrappers.megablast(query=self.cnt[0], db=self.cntdb, word_size=11)
        res = egglib.wrappers.megablast(query=self.cnt[0], db=self.cntdb, word_size=12)

    def test_costs(self):
        res = egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb)
        self.assertEqual(res.params['sc-match'], 2)
        self.assertEqual(res.params['sc-mismatch'], -3)
        self.assertEqual(res.params['gap-open'], 5)
        self.assertEqual(res.params['gap-extend'], 2)

        res = egglib.wrappers.blastn_short(query=self.cnt[0], db=self.cntdb)
        self.assertEqual(res.params['sc-match'], 1)
        self.assertEqual(res.params['sc-mismatch'], -3)
        self.assertEqual(res.params['gap-open'], 5)
        self.assertEqual(res.params['gap-extend'], 2)

        res = egglib.wrappers.megablast(query=self.cnt[0], db=self.cntdb)
        self.assertEqual(res.params['sc-match'], 1)
        self.assertEqual(res.params['sc-mismatch'], -2)

        res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb)
        self.assertEqual(res.params['sc-match'], 2)
        self.assertEqual(res.params['sc-mismatch'], -3)
        self.assertEqual(res.params['gap-open'], 5)
        self.assertEqual(res.params['gap-extend'], 2)

        res = egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb, reward=4, penalty=-5)
        self.assertEqual(res.params['sc-match'], 4)
        self.assertEqual(res.params['sc-mismatch'], -5)
        self.assertEqual(res.params['gap-open'], 12)
        self.assertEqual(res.params['gap-extend'], 8)

        res = egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb,
                    reward=1, penalty=-3, gapopen=2, gapextend=2)
        self.assertEqual(res.params['sc-match'], 1)
        self.assertEqual(res.params['sc-mismatch'], -3)
        self.assertEqual(res.params['gap-open'], 2)
        self.assertEqual(res.params['gap-extend'], 2)

        with self.assertRaises(ValueError):
            egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb,
                    reward=1, penalty=-3, gapopen=3, gapextend=2)

    def test_strand(self):
        res = egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb, strand='both', evalue=1e-20)
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res[0]), 1)
        self.assertEqual(res[0][0].descr, 'name1')
        self.assertEqual(res[0][0][0].query_frame, 1)
        self.assertEqual(res[0][0][0].hit_frame, 1)

        res = egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb, strand='plus', evalue=1e-20)
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res[0]), 1)
        self.assertEqual(res[0][0].descr, 'name1')
        self.assertEqual(res[0][0][0].query_frame, 1)
        self.assertEqual(res[0][0][0].hit_frame, 1)

        res = egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb, strand='minus', evalue=1e-20)
        self.assertEqual(len(res[0]), 0)

        res = egglib.wrappers.blastn(query=egglib.tools.rc(self.cnt[0].sequence), db=self.cntdb, strand='both', evalue=1e-20)
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res[0]), 1)
        self.assertEqual(res[0][0].descr, 'name1')
        self.assertEqual(res[0][0][0].query_frame, 1)
        self.assertEqual(res[0][0][0].hit_frame, -1)

        res = egglib.wrappers.blastn(query=egglib.tools.rc(self.cnt[0].sequence), db=self.cntdb, strand='plus', evalue=1e-20)
        self.assertEqual(len(res[0]), 0)

        res = egglib.wrappers.blastn(query=egglib.tools.rc(self.cnt[0].sequence), db=self.cntdb, strand='minus', evalue=1e-20)
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res[0]), 1)
        self.assertEqual(res[0][0].descr, 'name1')
        self.assertEqual(res[0][0][0].query_frame, 1)
        self.assertEqual(res[0][0][0].hit_frame, -1)

    def test_filters(self):
        res = egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb, strand='both', evalue=1e-20)
        self.assertEqual(res.params['filter'], 'L;m;')

        res = egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb, strand='both', evalue=1e-20, no_dust=True)
        self.assertEqual(res.params['filter'], 'm;')

        res = egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb, strand='both', evalue=1e-20, no_soft_masking=True)
        self.assertEqual(res.params['filter'], 'L;')

        res = egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb, strand='both', evalue=1e-20, lcase_masking=True)
        self.assertEqual(res.params['filter'], 'L;m;')

        s1 = 'GTGCTACACCTCAACCCGGTAGGCTGACAGGGGCTCGGCCTCgccgttttaaatcctgagtacatccttagtctgcatttcgcctaggtgcccgcagcattgggctagGTGGGCGTATTGACTAAGAATTACAGATTGGGAAATTGAGAATCACATGGAGGTAGTGGAGAAACTAAAAAGCGGGTAATATCGGTGTAGTT'
        s2 = 'GACTAAGAGTGCCAAGGGAGCTCGTAGGAATTCAGAACAAGATTTACCAGGTATATGCATACCCGTGAAATGGGCCATATCTTCAGATTGAGAGATTGTCTGCCTCTTCAATATCCCACTATCTCATCTAGCCGTTTTAAATCCTGAGTACATCCTTAGTCTGCATTTCGCCTAGGTGCCCGCAGCATTGGGCTAGAACG'
        res = egglib.wrappers.blastn(query=s1, subject=s2, evalue=1e-20)
        self.assertEqual(len(res[0]), 1)
        res = egglib.wrappers.blastn(query=s1, subject=s2, evalue=1e-20, lcase_masking=True)
        self.assertEqual(len(res[0]), 0)

    def test_perc_identity(self):
        s1 = 'GACTAAGAGTGCCAAGGGAGCTCGTAGGAATTCAGAACAAGATTTACCAGGTATATGCATACCCGTGAAATGGGCCATATCTTCAGATTGAGAGATTGTCTGCCTCTTCAATATCCCACTATCTCATCTAGCCGTTTTAAATCCTGAGTACATCCTTAGTCTGCA'
        s2 = 'GACTAAGAGTGCCAAGGGAGCTCGTAGGAATTCAGAACAAGATTTACCAGGTATATGCATACCCGTGAAATGGGCCATATCTTCAGATTGAGAGATTGTCTGCCTCTTCAATATCCCACTATCTCATCTAGCCGTTTTAAATCCTGAGTACATCCTTAGTCTGCA'
        res = egglib.wrappers.blastn(query=s1, subject=s2, evalue=1e-20)
        self.assertEqual(len(res[0]), 1)
        self.assertEqual(res[0][0][0].query_start, 0)
        self.assertEqual(res[0][0][0].query_stop, len(s1))
        res = egglib.wrappers.blastn(query=s1, subject=s2, evalue=1e-20, perc_identity=100)
        self.assertEqual(len(res[0]), 1)
        self.assertEqual(res[0][0][0].query_start, 0)
        self.assertEqual(res[0][0][0].query_stop, len(s1))
        #                                                                    C                                                                         T
        s1 = 'GACTAAGAGTGCCAAGGGAGCTCGTAGGAATTCAGAACAAGATTTACCAGGTATATGCATACCGGTGAAATGGGCCATATCTTCAGATTGAGAGATTGTCTGCCTCTTCAATATCCCACTATCTCATCTAGCCGTTTAAAATCCTGAGTACATCCTTAGTCTGCA'
        res = egglib.wrappers.blastn(query=s1, subject=s2, evalue=1e-20)
        self.assertEqual(len(res[0]), 1)
        self.assertEqual(res[0][0][0].query_start, 0)
        self.assertEqual(res[0][0][0].query_stop, len(s1))
        res = egglib.wrappers.blastn(query=s1, subject=s2, evalue=1e-20, perc_identity=100)
        self.assertEqual(len(res[0]), 0)

    def test_template_params(self):
        res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, template_type='coding', template_length=18)
        with self.assertRaises(TypeError):
            res = egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb, template_type='coding', template_length=18)
        with self.assertRaises(TypeError):
            res = egglib.wrappers.blastn_short(query=self.cnt[0], db=self.cntdb, template_type='coding', template_length=18)
        with self.assertRaises(TypeError):
            res = egglib.wrappers.megablast(query=self.cnt[0], db=self.cntdb, template_type='coding', template_length=18)
        res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, template_type='coding', template_length=16)
        res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, template_type='coding', template_length=21)
        res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, template_type='optimal', template_length=18)
        res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, template_type='coding_and_optimal', template_length=18)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, template_type='xxx', template_length=18)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, template_type='coding', template_length=15)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, template_type='coding', template_length=17)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, template_type='coding', template_length=19)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, template_type='coding', template_length=20)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, template_type='coding', template_length=22)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, template_type='coding', template_length=0)

    def test_greedy(self):
        res = egglib.wrappers.megablast(query=self.cnt[0], db=self.cntdb, no_greedy=True)
        with self.assertRaises(TypeError):
            res = egglib.wrappers.blastn(query=self.cnt[0], db=self.cntdb, no_greedy=True)
        with self.assertRaises(TypeError):
            res = egglib.wrappers.blastn_short(query=self.cnt[0], db=self.cntdb, no_greedy=True)
        with self.assertRaises(TypeError):
            res = egglib.wrappers.dc_megablast(query=self.cnt[0], db=self.cntdb, no_greedy=True)

    def test_relative_path(self):
        os.chdir(self.tmp)
        res = egglib.wrappers.blastn(query=self.seq1, db='cnt', evalue=1e-15)
        self.assertIsInstance(res, egglib.wrappers.BlastOutput)
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res[0]), 1)
        self.assertEqual(res[0][0].descr, 'name1')

        os.chdir('..')
        res = egglib.wrappers.blastn(query=self.seq1, db=str(self.tmp / 'cnt'), evalue=1e-15)
        self.assertIsInstance(res, egglib.wrappers.BlastOutput)
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res[0]), 1)
        self.assertEqual(res[0][0].descr, 'name1')
        
        os.chdir(self.tmp)
        pathlib.Path('test_relative_path_subdir').mkdir()
        os.chdir('test_relative_path_subdir')
        res = egglib.wrappers.blastn(query=self.seq1, db=str(pathlib.Path('..') / 'cnt'), evalue=1e-15)
        self.assertIsInstance(res, egglib.wrappers.BlastOutput)
        self.assertEqual(len(res), 1)
        self.assertEqual(len(res[0]), 1)
        self.assertEqual(res[0][0].descr, 'name1')


class blastp_test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.prot = egglib.io.from_fasta(fname2, alphabet=egglib.alphabets.protein)
        self.protdb = os.path.join(self.tmp, 'prot')
        egglib.wrappers.makeblastdb(self.prot, out=self.protdb)
 
    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_blastp(self):
        res = egglib.wrappers.blastp(self.prot[0], subject=self.prot[0],
                    parse_deflines=True, evalue=1e-5, num_threads=1, word_size=7)

        self.assertEqual(res.program, 'blastp')
        self.assertIsNone(res.db)
        self.assertEqual(res.query_ID, self.prot.get_name(0).split()[0])
        self.assertEqual(res.query_def, ' '.join(self.prot.get_name(0).split()[1:]))
        self.assertEqual(res.query_len, self.prot[0].ls)
        self.assertEqual(res.params['expect'], 1e-5)
        self.assertNotIn('sc-match', res.params)
        self.assertNotIn('sc-mismatch', res.params)
        self.assertEqual(res.params['gap-open'], 11)
        self.assertEqual(res.params['gap-extend'], 1)
        self.assertEqual(res.params['filter'], 'F')
        self.assertEqual(len(res), 1)
        [query] = res[:]
        self.assertEqual(query.num, 0)
        self.assertEqual(query.query_ID, self.prot.get_name(0).split()[0])
        self.assertEqual(query.query_def, ' '.join(self.prot.get_name(0).split()[1:]))
        self.assertEqual(query.query_len, self.prot[0].ls)
        self.assertEqual(query.db_num, 0)
        self.assertEqual(query.db_len, 0)
        self.assertEqual(len(query), 1)
        [hit] = query[:]
        self.assertEqual(hit.num, 0)
        self.assertEqual(hit.id, self.prot.get_name(0).split()[0])
        self.assertEqual(hit.descr, ' '.join(self.prot.get_name(0).split()[1:]))
        self.assertEqual(hit.accession, self.prot.get_name(0).split()[0])
        self.assertEqual(hit.len, self.prot[0].ls)
        self.assertEqual(len(hit), 1)
        [Hsp] = hit[:]
        self.assertEqual(Hsp.num, 0)
        self.assertLess(Hsp.evalue, 1e-20)
        self.assertEqual(Hsp.query_start, 0)
        self.assertEqual(Hsp.query_stop, self.prot[0].ls)
        self.assertEqual(Hsp.query_frame, 0)
        self.assertEqual(Hsp.hit_start, 0)
        self.assertEqual(Hsp.hit_stop, self.prot[0].ls)
        self.assertEqual(Hsp.hit_frame, 0)
        self.assertEqual(Hsp.identity, self.prot[0].ls)
        self.assertEqual(Hsp.positive, self.prot[0].ls)
        self.assertEqual(Hsp.gaps, 0)
        self.assertEqual(Hsp.align_len, self.prot[0].ls)
        self.assertEqual(Hsp.qseq, self.prot.get_sequence(0).string())
        self.assertEqual(Hsp.midline, self.prot.get_sequence(0).string())
        self.assertEqual(Hsp.hseq, self.prot.get_sequence(0).string())

    def test_word_size(self):
        for fun in egglib.wrappers.blastp, egglib.wrappers.blastp_short, egglib.wrappers.blastp_fast:
            with self.assertRaises(ValueError):
                fun(self.prot[0], db=self.protdb, word_size=0)
            with self.assertRaises(ValueError):
                fun(self.prot[0], db=self.protdb, word_size=1)
            fun(self.prot[0], db=self.protdb, word_size=2)
            fun(self.prot[0], db=self.protdb, word_size=3)
            fun(self.prot[0], db=self.protdb, word_size=4)
            fun(self.prot[0], db=self.protdb, word_size=5)
            fun(self.prot[0], db=self.protdb, word_size=6)
            fun(self.prot[0], db=self.protdb, word_size=7)
            with self.assertRaises(ValueError):
                fun(self.prot[0], db=self.protdb, word_size=8)

    def test_gap_costs(self):
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='PAM30', gapopen=0, gapextend=0)
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='PAM30', gapopen=8, gapextend=2)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='PAM30', gapopen=32767, gapextend=32767)
        self.assertEqual(res.params['gap-open'], 32767)
        self.assertEqual(res.params['gap-extend'], 32767)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='PAM30', gapopen=10, gapextend=1)
        self.assertEqual(res.params['gap-open'], 10)
        self.assertEqual(res.params['gap-extend'], 1)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='PAM30', gapopen=8, gapextend=1)
        self.assertEqual(res.params['gap-open'], 8)
        self.assertEqual(res.params['gap-extend'], 1)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='PAM30')
        self.assertEqual(res.params['gap-open'], 9)
        self.assertEqual(res.params['gap-extend'], 1)

        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='PAM70', gapopen=0, gapextend=0)
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='PAM70', gapopen=10, gapextend=2)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='PAM70', gapopen=32767, gapextend=32767)
        self.assertEqual(res.params['gap-open'], 32767)
        self.assertEqual(res.params['gap-extend'], 32767)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='PAM70', gapopen=8, gapextend=2)
        self.assertEqual(res.params['gap-open'], 8)
        self.assertEqual(res.params['gap-extend'], 2)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='PAM70', gapopen=12, gapextend=3)
        self.assertEqual(res.params['gap-open'], 12)
        self.assertEqual(res.params['gap-extend'], 3)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='PAM70')
        self.assertEqual(res.params['gap-open'], 10)
        self.assertEqual(res.params['gap-extend'], 1)

        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='BLOSUM62', gapopen=0, gapextend=0)
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='BLOSUM62', gapopen=8, gapextend=1)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='BLOSUM62', gapopen=32767, gapextend=32767)
        self.assertEqual(res.params['gap-open'], 32767)
        self.assertEqual(res.params['gap-extend'], 32767)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='BLOSUM62', gapopen=8, gapextend=2)
        self.assertEqual(res.params['gap-open'], 8)
        self.assertEqual(res.params['gap-extend'], 2)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='BLOSUM62', gapopen=11, gapextend=1)
        self.assertEqual(res.params['gap-open'], 11)
        self.assertEqual(res.params['gap-extend'], 1)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='BLOSUM62')
        self.assertEqual(res.params['gap-open'], 11)
        self.assertEqual(res.params['gap-extend'], 1)

        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='BLOSUM80', gapopen=0, gapextend=0)
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='BLOSUM80', gapopen=10, gapextend=2)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='BLOSUM80', gapopen=32767, gapextend=32767)
        self.assertEqual(res.params['gap-open'], 32767)
        self.assertEqual(res.params['gap-extend'], 32767)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='BLOSUM80', gapopen=8, gapextend=2)
        self.assertEqual(res.params['gap-open'], 8)
        self.assertEqual(res.params['gap-extend'], 2)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='BLOSUM80', gapopen=11, gapextend=1)
        self.assertEqual(res.params['gap-open'], 11)
        self.assertEqual(res.params['gap-extend'], 1)
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='BLOSUM80', gapopen=10, gapextend=1)
        self.assertEqual(res.params['gap-open'], 10)
        self.assertEqual(res.params['gap-extend'], 1)

    def test_matrix(self):
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='BLOSUM62')
        self.assertEqual(res.params['matrix'], 'BLOSUM62')
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='BLOSUM80')
        self.assertEqual(res.params['matrix'], 'BLOSUM80')
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='PAM30')
        self.assertEqual(res.params['matrix'], 'PAM30')
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='PAM70')
        self.assertEqual(res.params['matrix'], 'PAM70')
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, matrix='prout')
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb)
        self.assertEqual(res.params['matrix'], 'BLOSUM62')
        res = egglib.wrappers.blastp_short(self.prot[0], db=self.protdb)
        self.assertEqual(res.params['matrix'], 'PAM30')

    def test_threshold(self):
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, threshold=2)
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, threshold=10)
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, threshold=100)
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, threshold=0)
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, threshold=-1)
        with self.assertRaises(TypeError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, threshold=0.5)

    def test_comp_based_stats(self):
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, comp_based_stats=0)
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, comp_based_stats=1)
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, comp_based_stats=2)
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, comp_based_stats=3)
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, comp_based_stats=-1)
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, comp_based_stats=4)

    def test_seg(self):
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, seg=0)
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, seg=1)
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, seg=(12, 2.2, 2.5))
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, seg=-1)
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, seg=3)
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, seg=(0, 2.2, 2.5))
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, seg=(1, 2.2, 2.5))
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, seg=(10, 0, 2.5))
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, seg=(10, 0.1, 2.5))
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, seg=(10, 2.2, 2.1))
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, seg=(10, 1, 10))

    def test_filters(self):
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb)
        self.assertEqual(res.params['filter'], 'F')
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, lcase_masking=True)
        self.assertEqual(res.params['filter'], 'F')
        res = egglib.wrappers.blastp(self.prot[0], db=self.protdb, soft_masking=True)
        self.assertEqual(res.params['filter'], 'm;')

    def test_sw(self):
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, use_sw_tback=True)
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, use_sw_tback=False)

    def test_window_size(self):
        with self.assertRaises(ValueError):
            egglib.wrappers.blastp(self.prot[0], db=self.protdb, window_size=-1)
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, window_size=0)
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, window_size=50)
        egglib.wrappers.blastp(self.prot[0], db=self.protdb, window_size=1000)

class blastx_test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cds = egglib.io.from_fasta(fname3, alphabet=egglib.alphabets.DNA)
        self.prot = egglib.tools.translate(egglib.tools.to_codons(self.cds))
        self.protdb = os.path.join(self.tmp, 'prot')
        egglib.wrappers.makeblastdb(self.prot, out=self.protdb)
 
    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_blastx(self):
        ls = self.cds[0].ls

        for f in egglib.wrappers.blastx, egglib.wrappers.blastx_fast:
            res = f(self.cds[0], subject=self.prot[0],
                        evalue=1e-5, num_threads=1, word_size=None, seg=0)

            self.assertEqual(res.program, 'blastx')
            self.assertIsNone(res.db)
            self.assertEqual(res.query_ID, 'Query_1')
            self.assertEqual(res.query_def, 'lcl|' + self.cds.get_name(0))
            self.assertEqual(res.query_len, ls)
            self.assertEqual(res.params['expect'], 1e-5)
            self.assertEqual(res.params['filter'], 'F')
            self.assertEqual(len(res), 1)
            [query] = res[:]
            self.assertEqual(query.num, 0)
            self.assertEqual(query.query_ID, 'Query_1')
            self.assertEqual(query.query_def, 'lcl|' + self.cds.get_name(0))
            self.assertEqual(query.query_len, ls)
            self.assertEqual(query.db_num, 0)
            self.assertEqual(query.db_len, 0)
            self.assertEqual(len(query), 1)
            [hit] = query[:]
            self.assertEqual(hit.num, 0)
            self.assertEqual(hit.id, 'lcl|' + self.cds.get_name(0))
            self.assertEqual(hit.descr, 'lcl|' + self.cds.get_name(0))
            self.assertEqual(hit.accession, 'Subject_1')
            self.assertEqual(hit.len, ls//3)
            self.assertEqual(len(hit), 1)
            [Hsp] = hit[:]
            self.assertEqual(Hsp.num, 0)
            self.assertLess(Hsp.evalue, 1e-20)
            self.assertEqual(Hsp.query_start, 0)
            self.assertEqual(Hsp.query_stop, ls)
            self.assertEqual(Hsp.query_frame, 1)
            self.assertEqual(Hsp.hit_start, 0)
            self.assertEqual(Hsp.hit_stop, ls//3)
            self.assertEqual(Hsp.hit_frame, 0)
            self.assertEqual(Hsp.identity, ls//3)
            self.assertEqual(Hsp.positive, ls//3)
            self.assertEqual(Hsp.gaps, 0)
            self.assertEqual(Hsp.align_len, ls//3)
            self.assertEqual(Hsp.qseq, self.prot.get_sequence(0).string())
            self.assertEqual(Hsp.midline, self.prot.get_sequence(0).string())
            self.assertEqual(Hsp.hseq, self.prot.get_sequence(0).string())

    def test_strand(self):
        for f in egglib.wrappers.blastx, egglib.wrappers.blastx_fast:
            res = f(query=self.cds[0], db=self.protdb, strand='both', evalue=1e-20)
            self.assertEqual(len(res), 1)
            self.assertEqual(len(res[0]), 1)
            self.assertEqual(res[0][0].descr, 'name1')
            self.assertEqual(res[0][0][0].query_frame, 1)
            self.assertEqual(res[0][0][0].hit_frame, 0)

            res = f(query=self.cds[0], db=self.protdb, strand='plus', evalue=1e-20)
            self.assertEqual(len(res), 1)
            self.assertEqual(len(res[0]), 1)
            self.assertEqual(res[0][0].descr, 'name1')
            self.assertEqual(res[0][0][0].query_frame, 1)
            self.assertEqual(res[0][0][0].hit_frame, 0)

            res = f(query=self.cds[0], db=self.protdb, strand='minus', evalue=1e-20)
            self.assertEqual(len(res[0]), 0)

            res = f(query=egglib.tools.rc(self.cds[0].sequence), db=self.protdb, strand='both', evalue=1e-20)
            self.assertEqual(len(res), 1)
            self.assertEqual(len(res[0]), 1)
            self.assertEqual(res[0][0].descr, 'name1')
            self.assertEqual(res[0][0][0].query_frame, -1)
            self.assertEqual(res[0][0][0].hit_frame, 0)

            res = f(query=egglib.tools.rc(self.cds[0].sequence), db=self.protdb, strand='plus', evalue=1e-20)
            self.assertEqual(len(res[0]), 0)

            res = f(query=egglib.tools.rc(self.cds[0].sequence), db=self.protdb, strand='minus', evalue=1e-20)
            self.assertEqual(len(res), 1)
            self.assertEqual(len(res[0]), 1)
            self.assertEqual(res[0][0].descr, 'name1')
            self.assertEqual(res[0][0][0].query_frame, -1)
            self.assertEqual(res[0][0][0].hit_frame, 0)

    def test_genetic_code(self):
        with self.assertRaises(ValueError):
            res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=0)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=1)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=2)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=3)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=4)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=5)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=6)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=7)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=8)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=9)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=10)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=12)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=15)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=16)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=17)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=19)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=20)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=21)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=22)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=23)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=24)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=25)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=25)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=26)
        with self.assertRaises(ValueError):
            res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, query_genetic_code=30)

    def test_max_intron_length(self):
        with self.assertRaises(TypeError):
            res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, max_intron_length='a')
        with self.assertRaises(ValueError):
            res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, max_intron_length=-1)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, max_intron_length=0)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, max_intron_length=20)
        res = egglib.wrappers.blastx(query=self.cds[0], db=self.protdb, max_intron_length=5000)

class tblastn_test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cds = egglib.io.from_fasta(fname3, alphabet=egglib.alphabets.DNA)
        self.prot = egglib.tools.translate(egglib.tools.to_codons(self.cds))
        self.cdsdb = os.path.join(self.tmp, 'cds')
        egglib.wrappers.makeblastdb(self.cds, out=self.cdsdb)
 
    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_tblastn(self):
        ls = self.prot[0].ls

        for f in egglib.wrappers.tblastn, egglib.wrappers.tblastn_fast:
            res = f(self.prot[0], subject=self.cds[0],
                        evalue=1e-5, num_threads=1, word_size=None, seg=0)

            self.assertEqual(res.program, 'tblastn')
            self.assertIsNone(res.db)
            self.assertEqual(res.query_ID, 'Query_1')
            self.assertEqual(res.query_def, 'lcl|' + self.prot.get_name(0))
            self.assertEqual(res.query_len, ls)
            self.assertEqual(res.params['expect'], 1e-5)
            self.assertEqual(res.params['filter'], 'F')
            self.assertEqual(len(res), 1)
            [query] = res[:]
            self.assertEqual(query.num, 0)
            self.assertEqual(query.query_ID, 'Query_1')
            self.assertEqual(query.query_def, 'lcl|' + self.prot.get_name(0))
            self.assertEqual(query.query_len, ls)
            self.assertEqual(query.db_num, 0)
            self.assertEqual(query.db_len, 0)
            self.assertEqual(len(query), 1)
            [hit] = query[:]
            self.assertEqual(hit.num, 0)
            self.assertEqual(hit.id, 'lcl|' + self.prot.get_name(0))
            self.assertEqual(hit.descr, 'lcl|' + self.prot.get_name(0))
            self.assertEqual(hit.accession, 'Subject_1')
            self.assertEqual(hit.len, ls*3)
            self.assertEqual(len(hit), 1)
            [Hsp] = hit[:]
            self.assertEqual(Hsp.num, 0)
            self.assertLess(Hsp.evalue, 1e-20)
            self.assertEqual(Hsp.query_start, 0)
            self.assertEqual(Hsp.query_stop, ls)
            self.assertEqual(Hsp.query_frame, 0)
            self.assertEqual(Hsp.hit_start, 0)
            self.assertEqual(Hsp.hit_stop, ls*3)
            self.assertEqual(Hsp.hit_frame, 1)
            self.assertEqual(Hsp.identity, ls)
            self.assertEqual(Hsp.positive, ls)
            self.assertEqual(Hsp.gaps, 0)
            self.assertEqual(Hsp.align_len, ls)
            self.assertEqual(Hsp.qseq, self.prot.get_sequence(0).string())
            self.assertEqual(Hsp.midline, self.prot.get_sequence(0).string())
            self.assertEqual(Hsp.hseq, self.prot.get_sequence(0).string())

    def test_soft_masking(self):
        res = egglib.wrappers.tblastn(self.prot[0], subject=self.cds[0],
                    evalue=1e-5, num_threads=1, word_size=None, seg=0)
        self.assertEqual(res.params['filter'], 'F')

        res = egglib.wrappers.tblastn(self.prot[0], subject=self.cds[0],
                    evalue=1e-5, num_threads=1, word_size=None, seg=0,
                    soft_masking=True)
        self.assertEqual(res.params['filter'], 'm;')

    def test_db_genetic_code(self):
        for i in [1,2,3,4,5,6,9,10,11,12,13,14,15,16,21,22,23,24,25]:
            egglib.wrappers.tblastn(self.prot[0], subject=self.cds[0],
                db_genetic_code=i)
        for i in [-1, 0, 7, 8, 17, 18, 19, 20, 26, 27, 28, 30, 50, 100]:
            with self.assertRaises(ValueError):
                egglib.wrappers.tblastn(self.prot[0], subject=self.cds[0],
                    db_genetic_code=i)

    def test_max_intron_length(self):
        with self.assertRaises(TypeError):
            egglib.wrappers.tblastn(query=self.prot[0], db=self.cdsdb, max_intron_length='a')
        with self.assertRaises(ValueError):
            egglib.wrappers.tblastn(query=self.prot[0], db=self.cdsdb, max_intron_length=-1)
        egglib.wrappers.tblastn(query=self.prot[0], db=self.cdsdb, max_intron_length=0)
        egglib.wrappers.tblastn(query=self.prot[0], db=self.cdsdb, max_intron_length=20)
        egglib.wrappers.tblastn(query=self.prot[0], db=self.cdsdb, max_intron_length=5000)

class tblastx_test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cds = egglib.io.from_fasta(fname3, alphabet=egglib.alphabets.DNA)
        self.cdsdb = os.path.join(self.tmp, 'cds')
        egglib.wrappers.makeblastdb(self.cds, out=self.cdsdb)
 
    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_tblastx(self):
        ls = self.cds[0].ls

        res = egglib.wrappers.tblastx(self.cds[0], subject=self.cds[0],
                    evalue=1e-20, num_threads=1, word_size=None)

        self.assertEqual(res.program, 'tblastx')
        self.assertIsNone(res.db)
        self.assertEqual(res.query_ID, 'Query_1')
        self.assertEqual(res.query_def, 'lcl|' + self.cds.get_name(0))
        self.assertEqual(res.query_len, ls)
        self.assertEqual(res.params['expect'], 1e-20)
        self.assertEqual(res.params['filter'], 'L;')
        self.assertEqual(len(res), 1)
        [query] = res[:]
        self.assertEqual(query.num, 0)
        self.assertEqual(query.query_ID, 'Query_1')
        self.assertEqual(query.query_def, 'lcl|' + self.cds.get_name(0))
        self.assertEqual(query.query_len, ls)
        self.assertEqual(query.db_num, 0)
        self.assertEqual(query.db_len, 0)
        self.assertEqual(len(query), 1)
        [hit] = query[:]
        self.assertEqual(hit.num, 0)
        self.assertEqual(hit.id, 'lcl|' + self.cds.get_name(0))
        self.assertEqual(hit.descr, 'lcl|' + self.cds.get_name(0))
        self.assertEqual(hit.accession, 'Subject_1')
        self.assertEqual(hit.len, ls)
        self.assertEqual(len(hit), 6)
        self.assertEqual([Hsp.num for Hsp in hit], list(range(6)))
        for Hsp in hit: self.assertLess(Hsp.evalue, 1e-20)
        self.assertEqual(set([Hsp.query_start for Hsp in hit]), set([0, 1, 2]))
        self.assertEqual(set([Hsp.query_stop for Hsp in hit]), set([ls-2, ls-1, ls]))
        self.assertEqual(set([Hsp.query_frame for Hsp in hit]), set([-3, -2, -1, 1, 2, 3]))
        self.assertEqual(set([Hsp.hit_start for Hsp in hit]), set([0, 1, 2]))
        self.assertEqual(set([Hsp.hit_stop for Hsp in hit]), set([ls-2, ls-1, ls]))
        self.assertEqual(set([Hsp.hit_frame for Hsp in hit]), set([-3, -2, -1, 1, 2, 3]))
        self.assertEqual(set([Hsp.identity for Hsp in hit]), set([ls//3, ls//3-1]))
        self.assertEqual(set([Hsp.positive for Hsp in hit]), set([ls//3, ls//3-1]))
        self.assertEqual(set([Hsp.gaps for Hsp in hit]), set([0]))
        self.assertEqual(set([Hsp.align_len for Hsp in hit]), set([ls//3, ls//3-1]))
        self.assertEqual(hit[0].qseq, egglib.tools.translate(self.cds.get_sequence(0).string()))
        self.assertEqual(hit[0].midline, egglib.tools.translate(self.cds.get_sequence(0).string()))
        self.assertEqual(hit[0].hseq, egglib.tools.translate(self.cds.get_sequence(0).string()))

    def test_soft_masking(self):
        res = egglib.wrappers.tblastx(self.cds[0], subject=self.cds[0],
                    evalue=1e-5, num_threads=1, word_size=None)
        self.assertEqual(res.params['filter'], 'L;')

        res = egglib.wrappers.tblastx(self.cds[0], subject=self.cds[0],
                    evalue=1e-5, num_threads=1, word_size=None,
                    soft_masking=True)
        self.assertEqual(res.params['filter'], 'L;m;')

    def test_db_genetic_code(self):
        for i in [1,2,3,4,5,6,9,10,11,12,13,14,15,16,21,22,23,24,25]:
            egglib.wrappers.tblastx(self.cds[0], subject=self.cds[0],
                db_genetic_code=i)
        for i in [-1, 0, 7, 8, 17, 18, 19, 20, 26, 27, 28, 30, 50, 100]:
            with self.assertRaises(ValueError):
                egglib.wrappers.tblastx(self.cds[0], subject=self.cds[0],
                    db_genetic_code=i)
