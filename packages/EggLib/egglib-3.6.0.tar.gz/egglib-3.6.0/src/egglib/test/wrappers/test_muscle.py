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

class muscle5_test(unittest.TestCase):
    def setUp(self):
        self.dna = egglib.io.from_fasta(str(path / 'cds.fas'), alphabet=egglib.alphabets.DNA)
        del self.dna[self.dna.find('Poplar_LG_VIII_pseudogene', index=True)]
        cds = egglib.Container.create(self.dna)
        cds.to_codons()
        self.prot = egglib.tools.translate(cds)

    def test_shortcut(self):
        egglib.wrappers.muscle(self.dna)
        egglib.wrappers.muscle5(self.dna)

    def test_source_type(self):
        # Container
        egglib.wrappers.muscle5(self.dna)

        # Align
        self.dna.equalize()
        aln = egglib.Align.create(self.dna)
        egglib.wrappers.muscle5(aln)

        # protein
        egglib.wrappers.muscle5(self.prot)

        # list
        with self.assertRaisesRegex(TypeError, '`source\' must be a Container'):
            egglib.wrappers.muscle5(list(self.dna))

        # custom alphabet
        seq = egglib.Container.create([(sam.name, sam.sequence) for sam in self.dna], alphabet=egglib.Alphabet('char', expl='ACGT', miss='?'))
        with self.assertRaisesRegex(ValueError, 'alphabet must be DNA or protein'):
            egglib.wrappers.muscle5(seq)

        # invalid alphabet
        test = egglib.io.from_genepop(str(path / 'P93.gpop'))
        with self.assertRaisesRegex(ValueError, 'alphabet must be DNA or protein'):
            egglib.wrappers.muscle5(test)

    def test_perm(self):
        egglib.wrappers.muscle5(self.dna, perm='none')
        egglib.wrappers.muscle5(self.dna, perm='abc')
        egglib.wrappers.muscle5(self.dna, perm='acb')
        egglib.wrappers.muscle5(self.dna, perm='bca')
        egglib.wrappers.muscle5(self.prot, perm='none')
        egglib.wrappers.muscle5(self.prot, perm='abc')
        egglib.wrappers.muscle5(self.prot, perm='acb')
        egglib.wrappers.muscle5(self.prot, perm='bca')
        with self.assertRaisesRegex(ValueError, 'invalid value for `perm\''):
            egglib.wrappers.muscle5(self.dna, perm='tronc')
        with self.assertRaisesRegex(ValueError, 'invalid value for `perm\''):
            egglib.wrappers.muscle5(self.dna, perm=None)

    def test_perturb(self):
        egglib.wrappers.muscle5(self.dna, perturb=0)
        egglib.wrappers.muscle5(self.prot, perturb=0)
        egglib.wrappers.muscle5(self.dna, perturb=1)
        egglib.wrappers.muscle5(self.prot, perturb=1)
        egglib.wrappers.muscle5(self.dna, perturb=107143)
        egglib.wrappers.muscle5(self.prot, perturb=107143)
        with self.assertRaisesRegex(TypeError, '`perturb\' must be an integer'):
            egglib.wrappers.muscle5(self.dna, perturb=0.0)
        with self.assertRaisesRegex(TypeError, '`perturb\' must be an integer'):
            egglib.wrappers.muscle5(self.dna, perturb=None)
        with self.assertRaisesRegex(TypeError, '`perturb\' must be an integer'):
            egglib.wrappers.muscle5(self.dna, perturb='0')
        with self.assertRaisesRegex(ValueError, 'invalid value for `perturb\''):
            egglib.wrappers.muscle5(self.dna, perturb=-1)

    def test_consiters_refineiters(self):
        egglib.wrappers.muscle5(self.dna, consiters=1, refineiters=1)
        egglib.wrappers.muscle5(self.dna, consiters=3, refineiters=10)
        egglib.wrappers.muscle5(self.prot, consiters=3, refineiters=10)
        egglib.wrappers.muscle5(self.dna, consiters=4, refineiters=2)
        with self.assertRaisesRegex(TypeError, '`consiters\' must be an integer'):
            egglib.wrappers.muscle5(self.dna, consiters='2', refineiters=100)
        with self.assertRaisesRegex(TypeError, '`refineiters\' must be an integer'):
            egglib.wrappers.muscle5(self.dna, consiters=2, refineiters=None)
        with self.assertRaisesRegex(TypeError, '`refineiters\' must be an integer'):
            egglib.wrappers.muscle5(self.dna, consiters=2, refineiters=100.0)
        with self.assertRaisesRegex(ValueError, '`consiters\' must be strictly positive'):
            egglib.wrappers.muscle5(self.dna, consiters=0, refineiters=100)
        with self.assertRaisesRegex(ValueError, '`consiters\' must be strictly positive'):
            egglib.wrappers.muscle5(self.dna, consiters=-2, refineiters=100)
        with self.assertRaisesRegex(ValueError, '`refineiters\' must be strictly positive'):
            egglib.wrappers.muscle5(self.dna, consiters=2, refineiters=0)
        with self.assertRaisesRegex(ValueError, '`refineiters\' must be strictly positive'):
            egglib.wrappers.muscle5(self.dna, consiters=2, refineiters=-10)

    def test_threads(self):
        egglib.wrappers.muscle5(self.dna, threads=None)
        egglib.wrappers.muscle5(self.dna, threads=1)
        egglib.wrappers.muscle5(self.dna, threads=4)
        egglib.wrappers.muscle5(self.dna, threads=100000)
        with self.assertRaisesRegex(TypeError, '`threads\' must be an integer'):
            egglib.wrappers.muscle5(self.dna, threads='four')
        with self.assertRaisesRegex(ValueError, '`threads\' must be strictly positive'):
            egglib.wrappers.muscle5(self.dna, threads=0)

    def test_return(self):
        for ref in self.dna, self.prot:
            aln = egglib.wrappers.muscle5(ref, threads=100)
            self.assertTrue(isinstance(aln, egglib.Align))
            self.assertEqual(aln.ns, ref.ns)
            num_gaps = 0
            for sam in ref:
                res = aln.find(sam.name)
                seq = res.sequence.string()
                num_gaps += seq.count('-')
                self.assertEqual(seq.replace('-', ''), sam.sequence.string())
            self.assertGreater(num_gaps, 0)

class muscle3_test(unittest.TestCase):
    def setUp(self):
        self.seq = egglib.io.from_fasta(str(path / 'cds.fas'), egglib.alphabets.DNA, labels=True)
        self.codons = egglib.io.from_fasta(str(path / 'cds.fas'), egglib.alphabets.DNA, labels=True)
        for i in self.codons:
            if i.ls%3!=0: i.sequence = i.sequence[:i.ls//3*3]
        self.codons.to_codons()
        self.prot = egglib.tools.translate(self.codons)

    def test_muscle_T(self):
        aln0=egglib.wrappers.muscle(self.seq, verbose=False)
        aln1=egglib.wrappers.muscle(self.seq, verbose=False)
        aln2=egglib.wrappers.muscle(self.seq, verbose=False, maxiters=1, diags=True)
        aln3=egglib.wrappers.muscle(self.seq, maxiters=1, diags=True, seqtype='dna',
                        aa_profile='sv', distance1='kbit20_3')
        aln4=egglib.wrappers.muscle(self.prot, seqtype='protein', aa_profile='sv')
        aln5=egglib.wrappers.muscle(self.prot, seqtype='protein', aa_profile='le',
                    brenner=True, diags1=True, SUEFF=0.4, anchorspacing=5,
                    center=-1.9, diaglength=17, distance1='kmer20_4',
                    gapopen=-2.5, maxtrees=2, objscore='ps', smoothscoreceil=3.4,
                    weight1='henikoff')

        self.assertIsInstance(aln0, egglib.Align)
        self.assertIsInstance(aln1, egglib.Align)
        self.assertIsInstance(aln2, egglib.Align)
        self.assertIsInstance(aln3, egglib.Align)
        self.assertIsInstance(aln4, egglib.Align)
        self.assertIsInstance(aln5, egglib.Align)

    def test_shortcut(self):
        egglib.wrappers.muscle(self.seq)
        egglib.wrappers.muscle3(self.seq)

    def test_muscle_E(self):
        cache = egglib.wrappers.paths['muscle']
        egglib.wrappers.paths['muscle']=None
        with self.assertRaises(RuntimeError):
            aln0=egglib.wrappers.muscle(self.seq, verbose=False)
        egglib.wrappers.paths['muscle'] = cache

        aln0=egglib.wrappers.muscle(self.seq, verbose=False)
        with self.assertRaises(TypeError):
            aln0=egglib.wrappers.muscle('dna', verbose=False)

        with self.assertRaises(TypeError):
            aln0=egglib.wrappers.muscle(self.seq, ref='error', verbose=False)

        with self.assertRaises(TypeError):
            egglib.wrappers.muscle(self.seq, ref=aln0, verbose=False)

        with self.assertRaises(ValueError):
            egglib.wrappers.muscle(self.seq, verbose=False, error='error')

        with self.assertRaises(ValueError):
            egglib.wrappers.muscle(self.seq, verbose=False, anchorspacing='error')

        with self.assertRaises(ValueError):
            egglib.wrappers.muscle(self.seq, verbose=False, cluster1='error')

    def test_alphabet(self):
        dna_a = egglib.wrappers.muscle(self.seq ,verbose=False, seqtype='dna')
        prot_a = egglib.wrappers.muscle(self.prot ,verbose=False, seqtype='protein')
        with self.assertRaises(ValueError):
            codons_a = egglib.wrappers.muscle(self.codons ,verbose=False, seqtype='codon')
        with self.assertRaises(ValueError):
            codons_a = egglib.wrappers.muscle(self.codons ,verbose=False, seqtype='dna')
        egglib.wrappers.muscle(dna_a, ref=dna_a)
        egglib.wrappers.muscle(prot_a, ref=prot_a)
        egglib.wrappers.muscle(dna_a, ref=dna_a, seqtype='dna')
        egglib.wrappers.muscle(prot_a, ref=prot_a, seqtype='protein')

        with self.assertRaises(ValueError):
            prot_a = egglib.wrappers.muscle(self.prot ,verbose=False, seqtype='dna')
        with self.assertRaises(ValueError):
            dna_a = egglib.wrappers.muscle(self.seq ,verbose=False, seqtype='protein')

        with self.assertRaises(ValueError):
            egglib.wrappers.muscle(dna_a, ref=prot_a)
        with self.assertRaises(ValueError):
            egglib.wrappers.muscle(prot_a, ref=dna_a)

        with self.assertRaises(ValueError):
            egglib.wrappers.muscle(dna_a, ref=prot_a, seqtype='dna')
        with self.assertRaises(ValueError):
            egglib.wrappers.muscle(prot_a, ref=dna_a, seqtype='dna')

        with self.assertRaises(ValueError):
            egglib.wrappers.muscle(prot_a, ref=dna_a, seqtype='protein')
        with self.assertRaises(ValueError):
            egglib.wrappers.muscle(dna_a, ref=prot_a, seqtype='protein')
