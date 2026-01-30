"""
    Copyright 2025 Thomas Coudoux, Stéphane De Mita, Mathieu Siol

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

class Codeml_test(unittest.TestCase):

    def setUp(self):
        self.tre1 = egglib.Tree(string='(D6076jpYM1:0.01436447,D8GDCiy9Ov:0.01518359,(UEOg7RZXzI:1e-08,(GVj_VDpGcX:0.01468032,(Cx5JVJRSVu:0.01482948,Sg4P4pwoAD:0.01482948):1e-08):1e-08):0.03077879);')
        self.tre2 = egglib.Tree(string='(lfgek:1e-08,:1e-08,(:0.00236318,((:1e-08,:1e-08):0.00236318,(:0.00235964,((:1e-08,:1e-08):0.00235964,(:0.00235959,((:1e-08,(:1e-08,(:1e-08,(:1e-08,:1e-08):1e-08):1e-08):1e-08):1e-08,((:1e-08,:1e-08):0.01197396,((((:1e-08,(:1e-08,(:1e-08,(:1e-08,:1e-08):1e-08):1e-08):1e-08):1e-08,(:0.00472843,((:0.00712594,(((:1e-08,:1e-08):1e-08,:0.00236068):0.00236493,(:0.00474365,:1e-08):0.02405602):1e-08):1e-08,((:1e-08,:1e-08):0.0071132,((:1e-08,:1e-08):1e-08,(:0.00236304,((:1e-08,:1e-08):0.00236585,:0.00713767):1e-08):1e-08):0.00474411):1e-08):1e-08):1e-08):0.08889392,((((:1e-08,(:1e-08,(:1e-08,(:1e-08,:1e-08):1e-08):1e-08):1e-08):1e-08,((:1e-08,:1e-08):0.00236447,(:1e-08,:1e-08):0.00236788):1e-08):0.01938084,((:1e-08,(:1e-08,(:1e-08,(:1e-08,:1e-08):1e-08):1e-08):1e-08):1e-08,:0.00713047):0.00960445):0.00886263,(:1e-08,(:0.00236294,(:0.00236497,(:1e-08,:1e-08):1e-08):0.00236576):1e-08):0.01508331):0.16952718):0.0649419,((:1e-08,(:1e-08,:1e-08):1e-08):1e-08,:0.00473416):0.00949746):0.00483123):0.0023273):1e-08):1e-08):1e-08):1e-08):1e-08):0.00236305);')
        self.tre3 = egglib.Tree(string='(Howler @2:0.03720737,(Spider @#:0.01148628,Woolly @#:0.0196596):0.00886448,((Squirrel @2:0.04743603,(Owl @2:0.02941486,(Tamarin @2:0.01801996,PMarmoset @1:0.01838315):0.01386822):0.00294979):0.0016907,((Saki @2:0.02083769,Titi @2:0.01950322):0.00961786,((( :0.00546402,(Chimp @1:0.00209035,Human @1:0.00662945):0.00131108):0.00695997,(Orangutan @1:0.01227939,Gibbon @1:0.02326558):0.00166244):0.01407,(Colobus @1:0.00272338,(DLangur @1:0.00474174,(:0.01088422,((AGM_cDNA @1:0.00133703,Tant_cDNA @1:0.00133438):0.00510737,(Baboon @1:0.00301189,Rhes_cDNA @1:0.00591659):0.00416175):0.00258487):0.01210951):0.00128701):0.02812975):0.11352434):0.00225187):0.01523892);')
        self.tre4 = egglib.Tree(string='(AGM_cDNA @1:0.00133706,Tant_cDNA @1:0.0013344,((Patas @1:0.01088443,(DLangur @1:0.00474181,(Colobus @1:0.00272347,(((Orangutan @1:0.01227967,Gibbon @1:0.02326609):0.00166273,(Gorilla @1:0.0054641,(Chimp @1:0.00209034,(Human @1:1e-08,Human @1:1e-08):0.0066297):0.00131111):0.00696052):0.01407059,((Titi @2:0.01950413,Saki @2:0.02083775):0.009619,((Squirrel @2:0.04743748,(Owl @2:0.02941571,(PMarmoset @1:0.01838309,Tamarin @2:0.01802051):0.01386846):0.0029497):0.00169063,(Howler @2:0.03720813,(Spider @#:0.01148671,Woolly @#:0.01965979):0.00886472):0.01523911):0.00225183):0.11352698):0.02812977):0.00128702):0.01210976):0.00258495,(Baboon @1:0.00301197,Rhes_cDNA @1:0.00591669):0.00416192):0.0051072);')
        self.tre5 = egglib.Tree(string='(:0.00236382,(lfgek:1e-08,:1e-08):0.0023637,((:1e-08,:1e-08):0.00236382,((:1e-08,:1e-08):0.00236028,(:0.00236023,(((:1e-08,(:1e-08,(:1e-08,(:1e-08,:1e-08):1e-08):1e-08):1e-08):1e-08,((((:0.00472963,((:0.00712763,((:0.0023613,(:1e-08,:1e-08):1e-08):0.00236553,(:0.0047445,:1e-08):0.02406107):1e-08):1e-08,((:1e-08,:1e-08):1e-08,(:0.00236355,((:1e-08,:1e-08):0.00236639,:0.00713926):1e-08):1e-08):0.00474523):1e-08):1e-08,((:1e-08,:1e-08):0.00711499,(:1e-08,(:1e-08,(:1e-08,(:1e-08,:1e-08):1e-08):1e-08):1e-08):1e-08):1e-08):0.08889918,((((:1e-08,(:1e-08,(:1e-08,(:1e-08,:1e-08):1e-08):1e-08):1e-08):1e-08,((:1e-08,:1e-08):0.00236489,(:1e-08,:1e-08):0.00236831):1e-08):0.01938478,(:0.00713189,(:1e-08,(:1e-08,(:1e-08,(:1e-08,:1e-08):1e-08):1e-08):1e-08):1e-08):0.00960648):0.00886328,(:1e-08,(:0.00236344,(:0.00236554,(:1e-08,:1e-08):1e-08):0.00236629):1e-08):0.01508798):0.16958977):0.06517117,((:1e-08,(:1e-08,:1e-08):1e-08):1e-08,:0.00473536):0.00955783):0.00713782):1e-08,(:0.00471835,(:0.0023612,:1e-08):0.01437424):0.00237957):1e-08):1e-08):1e-08):1e-08);')
        self.tre6 = egglib.Tree(string='(Vitis:0.10644819,((Papaya:1e-08,Papaya:1e-08):0.32858369,((Brachypodium:1e-08,Brachypodium:1e-08):0.07585498,Oryza:0.07980803):0.19411513):0.08333201,(((Medicago:0.13933746,Lotus:0.06463897):0.02217157,((Glycine_113:1e-08,Glycine_113:1e-08):0.02332516,(Glycine_55:1e-08,Glycine_55:1e-08):0.02118077):0.04569707):0.11860624,(Poplar_LG_VIII_pseudogene:0.04479187,Poplar_LG_X:0.02155466):0.10073976):0.04727693);')
        self.tre0 = egglib.Tree(string='(Brachypodium @#);')

    def test_codeml_T(self):
        cds = egglib.Align.create([
            ('UEOg7RZXzI', 'TGCTCAAAAATCATGAAAAAACGTAAATCTAGAGTTGGTCCAATTGATCTCAGGCATAGGAATTTGCCC'),
            ('Cx5JVJRSVu', 'TGCTCCAAAATCATGAAAAAACGTAAATCTAGAGTTGGTCCAATTGATCTCAGGCATAGGAATTTGCCC'),
            ('D6076jpYM1', 'TGCTCAGAAATCATGAAAAAAAGGAAATCTAGAGTTGGTCCAATTGATCTCAGGCATAGGAATTTGCCC'),
            ('D8GDCiy9Ov', 'TGCTCAACAATCATGAAAAAAAGGAAATCTAGAGTTGGTCCAATTGATCTCAGGCATAGGAATTTGCCC'),
            ('Sg4P4pwoAD', 'TGCTCAAATATCATGAAAAAACGTAAATCTAGAGTTGGTCCAATTGATCTCAGGCATAGGAATTTGCCC'),
            ('GVj_VDpGcX', 'TGCTCAAAAGTCATGAAAAAACGTAAATCTAGAGTTGGTCCAATTGATCTCAGGCATAGGAATTTGCCC')],
            egglib.alphabets.DNA)
        cds.to_codons()
        CML_results=egglib.wrappers.codeml(align=cds, tree=self.tre1, model='M0', verbose=False)
        self.assertIsInstance(CML_results, dict)
        self.assertEqual(CML_results['np'], 11)
        CML_resultsT = egglib.wrappers.codeml(align=cds, tree=self.tre1, model='M0')
        self.assertIsInstance(CML_resultsT['tree'], egglib._tree.Tree)

    def test_codeml_E(self):
        cache = egglib.wrappers.paths['codeml']
        egglib.wrappers.paths['codeml'] = None
        cds = egglib.io.from_fasta(str(path / 'codon_align.fas'), egglib.alphabets.DNA)
        cds = cds.subset(range(6))
        cds = cds.extract(0, 69)
        cds.encode() # this simulated fasta has no names
        with self.assertRaises(RuntimeError):
            egglib.wrappers.codeml(align=cds, tree=self.tre2, model='M0')
        egglib.wrappers.paths['codeml'] = cache

        cnt=egglib.io.from_fasta(str(path / 'codon_align.fas'), egglib.alphabets.DNA, cls=egglib.Container)
        with self.assertRaises(TypeError):
            egglib.wrappers.codeml(align=cnt, tree=self.tre2, model='M0')

        cds = egglib.io.from_fasta(str(path / 'cds_e.fas'), egglib.alphabets.DNA)
        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=self.tre0, model='M0')

        cds = egglib.io.from_fasta(str(path / 'codon_align.fas'), egglib.alphabets.DNA)
        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=self.tre2, model='M0', code=12)
        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=self.tre3, model='M0', code='error')

        cds = egglib.io.from_fasta(str(path / 'example_ename.fas'), egglib.alphabets.DNA)
        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=self.tre4, model='M0')

        cds = egglib.io.from_fasta(str(path / 'example_edpl.fas'), egglib.alphabets.DNA)
        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=self.tre5, model='M0')

        cds = egglib.io.from_fasta(str(path / 'codon_align_cstop.fas'), egglib.alphabets.DNA)
        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=self.tre6, model='M0')

        cds = egglib.io.from_fasta(str(path / 'cds_clust.fas'), egglib.alphabets.DNA)
        cds = cds.subset(range(6))
        cds = cds.extract(0, 69)
        mp = cds.encode()
        tre = egglib.Tree(string='(Poplar_LG_VIII_pseudogene:0.04684715,Poplar_LG_X:0.01936129,((Oryza:0.3367697,Vitis:0.09984833):0.05076269,(Medicago:0.13367357,Lotus:0.07016893):0.11364541):0.10061363);')
        rmp = {v: k for (k,v) in mp.items()}
        for node in tre.iter_leaves():
            node.label = rmp[node.label]
        cds.to_codons()

        tree_e1 = egglib.Tree(string='(Spider:0.01257025,Woolly:0.02023601,(Howler:0.03625789,((Titi:0.02002846,Saki:0.02646824):0.01312676)));')
        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=tree_e1, model='M0')
        tree_e2 = egglib.Tree()
        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=tree_e2, model='M0')
        tree_e3 =egglib.Tree(string='(Poplar_LG_VIII_pseudogene:0.30137798,Oryza:0.45654019,(Lotus:0.2258327,(Medicago:0.05478729,(Vitis:0.12466652,Poperrorlar_LG_X:0.00790383)1:0.07276364)1:0.07673733)1:0.13170743);')
        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=tree_e3, model='M0')

        #Test on error with the tree parameter is not finished

        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=tre, model='error')

        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=tre, model='D', ncat=5)

        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=tre, model='M7', ncat=None)

        with self.assertRaises(TypeError):
            egglib.wrappers.codeml(align=cds, tree=tre, model='M7', ncat='error')

        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=tre, model='M7', ncat=1)

        #Test on error with the req_tags and tags parameter is not finished

        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=tre, model='M0', codon_freq=8)

        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=tre, model='M0', kappa=-10)

        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=tre, model='M0', omega=-10)

        with self.assertRaises(ValueError):
            egglib.wrappers.codeml(align=cds, tree=tre, model='M7', omega=0.90)

    def test_alphabets(self):
        base = egglib.Align.create([
            ('UEOg7RZXzI', ['TGC','TCA','AAA','ATC','ATG','AAA','AAA','CGT','AAA','TCT','AGA','GTT','GGT','CCA','ATT','GAT','CTC','AGG','CAT','AGG','AAT','TTG','CCC']),
            ('Cx5JVJRSVu', ['TGC','TCC','AAA','ATC','ATG','AAA','AAA','CGT','AAA','TCT','AGA','GTT','GGT','CCA','ATT','GAT','CTC','AGG','CAT','AGG','AAT','TTG','CCC']),
            ('D6076jpYM1', ['TGC','TCA','GAA','ATC','ATG','AAA','AAA','AGG','AAA','TCT','AGA','GTT','GGT','CCA','ATT','GAT','CTC','AGG','CAT','AGG','AAT','TTG','CCC']),
            ('D8GDCiy9Ov', ['TGC','TCA','ACA','ATC','ATG','AAA','AAA','AGG','AAA','TCT','AGA','GTT','GGT','CCA','ATT','GAT','CTC','AGG','CAT','AGG','AAT','TTG','CCC']),
            ('Sg4P4pwoAD', ['TGC','TCA','AAT','ATC','ATG','AAA','AAA','CGT','AAA','TCT','AGA','GTT','GGT','CCA','ATT','GAT','CTC','AGG','CAT','AGG','AAT','TTG','CCC']),
            ('GVj_VDpGcX', ['TGC','TCA','AAA','GTC','ATG','AAA','AAA','CGT','AAA','TCT','AGA','GTT','GGT','CCA','ATT','GAT','CTC','AGG','CAT','AGG','AAT','TTG','CCC'])],
            egglib.alphabets.codons)

        CML_results=egglib.wrappers.codeml(align=base, tree=self.tre1, model='M0', verbose=False, get_files=False)
        self.assertIsInstance(CML_results, dict)
        self.assertEqual(CML_results['np'], 11) # number of branch in tree + 2

    def test_rst(self):
        # functionality test for get_files and rst helper
        # also regression for issue #267
        cds = egglib.Align.create([
            ('UEOg7RZXzI', 'TGCTCAAAAATCATGAAAAAACGTAAATCTAGAGTTGGTCCAATTGATCTCAGGCATAGGAATTTGCCC'),
            ('Cx5JVJRSVu', 'TGCTCCAAAATCATGAAAAAACGTAAATCTAGAGTTGGTCCAATTGATCTCAGGCATAGGAATTTGCCC'),
            ('D6076jpYM1', 'TGCTCAGAAATCATGAAAAAAAGGAAATCTAGAGTTGGTCCAATTGATCTCAGGCATAGGAATTTGCCC'),
            ('D8GDCiy9Ov', 'TGCTCAACAATCATGAAAAAAAGGAAATCTAGAGTTGGTCCAATTGATCTCAGGCATAGGAATTTGCCC'),
            ('Sg4P4pwoAD', 'TGCTCAAATATCATGAAAAAACGTAAATCTAGAGTTGGTCCAATTGATCTCAGGCATAGGAATTTGCCC'),
            ('GVj_VDpGcX', 'TGCTCAAAAGTCATGAAAAAACGTAAATCTAGAGTTGGTCCAATTGATCTCAGGCATAGGAATTTGCCC')],
            egglib.alphabets.DNA)
        tre = egglib.Tree(string='(D6076jpYM1:0.01436447,D8GDCiy9Ov:0.01518359,(UEOg7RZXzI:1e-08,(GVj_VDpGcX:0.01468032,(Cx5JVJRSVu:0.01482948,Sg4P4pwoAD:0.01482948):1e-08):1e-08):0.03077879);')
        cds.to_codons()
        res = egglib.wrappers.codeml(align=cds, tree=tre, model='M8', ncat=10, verbose=False, get_files=True)

    def test_candidates(self): # test contributed by Florent Marchal
        file = path / "Mx_aln_short.fas"
        tree = egglib.Tree(path / "Mx_unroot.tree")
        Ali = egglib.io.from_fasta(file, alphabet=egglib.alphabets.DNA)
        Ali.to_codons()

        print('*', end='', flush=True)
        result = egglib.wrappers.codeml(Ali, tree, model="M8", ncat=10,
                                        omega=0.5, codon_freq=3)
        self.assertIsInstance(result['candidates'], list)

        print('*', end='', flush=True)
        result = egglib.wrappers.codeml(Ali, tree, model="M2a",
                                        omega=0.5, codon_freq=3)
        self.assertIsInstance(result['candidates'], list)

        print('*', end='', flush=True)
        result = egglib.wrappers.codeml(Ali, tree, model="M7", ncat=10,
                                        omega=0.5, codon_freq=3)
        self.assertIsNone(result['candidates'])

    def test_debug(self):
        # create data
        aln = egglib.Align(egglib.alphabets.codons)
        aln.add_sample('A', ['ATG', 'CAT', 'TTC', 'AGT', 'GGC', 'TTC'])
        aln.add_sample('B', ['ATG', 'CAT', 'TTC', 'TGT', 'GGC', 'TCC'])
        aln.add_sample('C', ['ATG', 'CAA', 'TAC', 'AGC', 'GGC', 'CCC'])
        aln.add_sample('D', ['ATG', 'CAA', 'TAC', 'AGG', 'GGC', 'TTT'])
        aln.add_sample('E', ['ATG', 'CAT', 'AAC', 'AGG', 'GGC', 'TTC'])
        tre = egglib.Tree(string='(A, (B,C), (D,E));')

        # test possibility of disabling codeml
        codeml = egglib.wrappers.paths['codeml']
        egglib.wrappers.paths['codeml'] = None
        with self.assertRaises(RuntimeError):
            res = egglib.wrappers.codeml(aln, tre, 'M2a', verbose=False)
        egglib.wrappers.paths['codeml'] = codeml

        def test_archive_name(fname):
            # generate archive
            p = pathlib.Path(fname)
            if p.exists(): p.unlink()
            res1 = egglib.wrappers.codeml(aln, tre, 'M2a', debug=p)
            self.assertTrue(p.exists())
            codeml = egglib.wrappers.paths['codeml']
            egglib.wrappers.paths['codeml'] = None
            res2 = egglib.wrappers.codeml(aln, tre, 'M2a', debug=p)
            egglib.wrappers.paths['codeml'] = codeml

            # compare results
            self.assertEqual(set(res1), set(res2))
            for k in res1:
                if k == 'tree': self.assertEqual(res1[k].newick(), res2[k].newick()) # egglib.Tree doesn't support comparison
                else: self.assertEqual(res1[k], res2[k])
            p.unlink()

        # test with compressed archive
        test_archive_name('_debug_.tar.gz')

        # test with uncompressed archive
        test_archive_name('_debug_.tar')

        # .zip doesn't work
        with self.assertRaisesRegex(ValueError, '^debug option must be a \[compressed\] tarfile$'):
            egglib.wrappers.codeml(aln, tre, 'M2a', debug='_debug_.zip')
