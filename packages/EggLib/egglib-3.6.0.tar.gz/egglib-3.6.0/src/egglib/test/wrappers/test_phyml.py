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

class Phyml_test(unittest.TestCase):

    def test_Phyml_T(self):
        tree = egglib.Tree(string='(Spider:0.01257025,Woolly:0.02023601,(Howler:0.03625789,((Titi:0.02002846,Saki:0.02646824):0.01312676,((Owl:0.02467454,(((Gorilla:0.00570008,(Human:0.00467442,Chimp:0.00218595):0.00198277):0.00803251,(Gibbon:0.02031871,Orangutan:0.01428695):0.00052501):0.01497214,(Colobus:0.00134948,(DLangur:0.00479108,(Patas:0.01038680,((AGM_cDNA:0.00067736,Tant_cDNA:0.00000006):0.00511480,(Baboon:0.00531400,Rhes_cDNA:0.00519922):0.00433750):0.00200495):0.00621549):0.00134574):0.02864316):0.11226732):0.00500924,(Squirrel:0.04657578,(PMarmoset:0.02254897,Tamarin:0.01990484):0.01687811):0.00000008):0.00119894):0.01464801):0.01145931);')

        aln = egglib.io.from_fasta(str(path / 'example.fas'), egglib.alphabets.DNA, labels=True)
        tree, stats = egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                start_tree=tree,
                fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                use_median=True, free_rates=True)
        self.assertIsInstance(tree, egglib.Tree)
        self.assertIsInstance(stats, dict)

        aln.to_codons()
        prot = egglib.tools.translate(aln)
        tree, stats = egglib.wrappers.phyml(prot, model='LG', verbose=False,
                start_tree='pars',
                alpha=None, rates=4, pinv=0.3, use_median=False, freq='m',
                free_rates=False)
        self.assertIsInstance(tree, egglib.Tree)
        self.assertIsInstance(stats, dict)

    def test_Phyml_E(self):
        tree = egglib.Tree(string='(Spider:0.01257025,Woolly:0.02023601,(Howler:0.03625789,((Titi:0.02002846,Saki:0.02646824):0.01312676,((Owl:0.02467454,(((Gorilla:0.00570008,(Human:0.00467442,Chimp:0.00218595):0.00198277):0.00803251,(Gibbon:0.02031871,Orangutan:0.01428695):0.00052501):0.01497214,(Colobus:0.00134948,(DLangur:0.00479108,(Patas:0.01038680,((AGM_cDNA:0.00067736,Tant_cDNA:0.00000006):0.00511480,(Baboon:0.00531400,Rhes_cDNA:0.00519922):0.00433750):0.00200495):0.00621549):0.00134574):0.02864316):0.11226732):0.00500924,(Squirrel:0.04657578,(PMarmoset:0.02254897,Tamarin:0.01990484):0.01687811):0.00000008):0.00119894):0.01464801):0.01145931);')

        cache = egglib.wrappers.paths['phyml']
        egglib.wrappers.paths['phyml'] = None
        aln = egglib.io.from_fasta(str(path / 'example.fas'), egglib.alphabets.DNA, labels=True)
        with self.assertRaises(RuntimeError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                    start_tree=tree,
                    fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                    use_median=True, free_rates=True)
        egglib.wrappers.paths.get('phyml').set_path_force(cache)

        with self.assertRaises(TypeError):
            egglib.wrappers.phyml('aln', model='TN93', verbose=False,
                    start_tree=tree,
                    fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                    use_median=True, free_rates=True)

        alne0 = egglib.io.from_fasta(str(path / 'cds_e.fas'), egglib.alphabets.DNA, labels=True)
        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(alne0, model='TN93', verbose=False,
                    fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                    use_median=True, free_rates=True)

        alne1 = egglib.io.from_fasta(str(path / 'example_Els.fas'), egglib.alphabets.DNA, labels=True)
        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(alne1, model='TN93', verbose=False,
                    fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                    use_median=True, free_rates=True)

        with self.assertRaises(TypeError):
            egglib.wrappers.phyml(aln, model=1500, verbose=False,
                    start_tree=tree,
                    fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                    use_median=True, free_rates=True)

        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='eerroorr', verbose=False,
                    start_tree=tree,
                    fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                    use_median=True, free_rates=True)

        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='FAaIiL', verbose=False,
                    start_tree=tree,
                    fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                    use_median=True, free_rates=True)

        with self.assertRaises(TypeError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                    boot='error', start_tree=tree,
                    fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                    use_median=True, free_rates=True)

        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                    boot=-10, start_tree=tree,
                    fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                    use_median=True, free_rates=True)

        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                    start_tree=tree,
                    fixed_brlens=True,  alpha=None, TiTv=-150 ,  rates=2, pinv=None, freq='m',
                    use_median=True, free_rates=True)

        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                    start_tree=tree,
                    fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='error',
                    use_median=True, free_rates=True)

        with self.assertRaises(TypeError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                start_tree=tree,
                    fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='ACTG',
                    use_median=True, free_rates=True)

        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                start_tree=tree,
                    fixed_brlens=True,  alpha=None, rates=2, pinv=150, freq='m',
                use_median=True, free_rates=True)

        with self.assertRaises(TypeError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                start_tree=tree,
                    fixed_brlens=True,  alpha=None, rates='ERROR', pinv=None, freq='m',
                use_median=True, free_rates=True)

        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                start_tree=tree,
                    fixed_brlens=True,  alpha=None, rates=0, pinv=None, freq='m',
                use_median=True, free_rates=True)

        with self.assertRaises(TypeError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                start_tree=tree,
                    fixed_brlens=True,  alpha='ERROR', rates=2, pinv=None, freq='m',
                use_median=True, free_rates=True)

        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                start_tree=tree,
                    fixed_brlens=True,  alpha=-150.0, rates=2, pinv=None, freq='m',
                use_median=True, free_rates=True)


        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                start_tree=tree,
                    fixed_brlens=True,  alpha=None, rates=1, pinv=None, freq='m',
                use_median=True, free_rates=True)


        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                start_tree='tree',
                    fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                use_median=True, free_rates=True)

        alne2 = egglib.io.from_fasta(str(path / 'example_edpl.fas'), egglib.alphabets.DNA, labels=True)
        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(alne2, model='TN93', verbose=False,
                start_tree=tree,
                fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                use_median=True, free_rates=True)

        tree0 = egglib.Tree(string='(Hello:0.01257025,Iam:0.02023601,(An:0.03625789,((Phyml:0.02002846,Error:0.02646824):0.00119894):0.01464801):0.01145931);')
        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                start_tree=tree0,
                fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                use_median=True, free_rates=True)

        aln = egglib.io.from_fasta(str(path / 'example_Els.fas'), egglib.alphabets.DNA, labels=True)	
        tree1 = egglib.Tree(string='(Hello:0.01257025,Iam:0.02023601,(An:0.03625789,((Phyml:0.02002846,Error:0.02646824):0.00119894):0.01464801):0.01145931);')
        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                start_tree=tree1,
                fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                use_median=True, free_rates=True)
    
        aln = egglib.io.from_fasta(str(path / 'example.fas'), egglib.alphabets.DNA, labels=True)	
        tree2 = egglib.Tree(string='(Spider:0.01257025,Woolly:0.02023601,(Howler:0.03625789):0.01145931);')
        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                start_tree=tree2,
                fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                use_median=True, free_rates=True)

        tree4 = egglib.Tree(string='(Spider:0.01257025,Woolly:0.02023601,(Howler:0.03625789,((Titi:0.02002846,Saki:0.02646824):0.01312676,((Owl:0.02467454,(((Gorilla:0.00570008,(Human:0.00467442,Chimp:0.00218595):0.00198277):0.00803251,(Gibbon:0.02031871,Orangutan:0.01428695):0.00052501):0.01497214,(Colobus:0.00134948,(DLangur:0.00479108,(Patas:0.01038680,((AGM_cDNA:0.00067736,Tant_cDNA:0.00000006):0.00511480,(Baboon:0.00531400,Rhes_cDNA:0.00519922):0.00433750):0.00200495):0.00621549):0.00134574):0.02864316):0.11226732):0.00500924,(Squirrel:0.04657578,(PMarmoset,Tamarin):0.01687811):0.00000008):0.00119894):0.01464801):0.01145931);')
        aln = egglib.io.from_fasta(str(path / 'example.fas'), egglib.alphabets.DNA, labels=True)	
        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                start_tree=tree4,
                fixed_brlens=True,  alpha=None, rates=2, pinv=None, freq='m',
                use_median=True, free_rates=True)
        
        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                fixed_brlens=True,  alpha=None, rates=2, pinv=None,
                freq='m', use_median=True, free_rates=True)

        with self.assertRaises(TypeError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                    fixed_brlens=False,  alpha=None, 
                rates=2, pinv=None, freq='m', use_median=True, free_rates=True, seed='error')

        with self.assertRaises(ValueError):
            egglib.wrappers.phyml(aln, model='TN93', verbose=False,
                    start_tree=tree, fixed_brlens=True,  alpha=None, 
                rates=2, pinv=None, freq='m', use_median=True, free_rates=True, seed=-10)

    def test_alphabet(self):
        dna = egglib.Align.create(
               [('one',   'GGCGAGCGACGCCCCTGGCGA'),
                ('two',   'GGCGAGAGACTCCTCTGGCGA'),
                ('three', 'GGCGTGAGACGGCTCTGCCTA'),
                ('four',  'GGCGTGAGACGGCACTGCCTA')], egglib.alphabets.DNA)
        tree, stats = egglib.wrappers.phyml(dna, 'HKY85')
        with self.assertRaises(ValueError):
            tree, stats = egglib.wrappers.phyml(dna, 'JTT')

        cod = egglib.Align.create(
               [('one',   ['GGC','GAG','CGA','CGC','CCC','TGG','CGA']),
                ('two',   ['GGC','GAG','AGA','CTC','CTC','TGG','CGA']),
                ('three', ['GGC','GTG','AGA','CGG','CTC','TGA','CTA']),
                ('four',  ['GGC','GTG','AGA','CGG','CAC','TGA','CTA'])], egglib.alphabets.codons)
        tree, stats = egglib.wrappers.phyml(cod, 'HKY85')
        with self.assertRaises(ValueError):
            tree, stats = egglib.wrappers.phyml(cod, 'JTT')

        dna.to_codons()
        prot = egglib.tools.translate(dna)
        tree, stats = egglib.wrappers.phyml(prot, 'JTT')
        with self.assertRaises(ValueError):
            tree, stats = egglib.wrappers.phyml(prot, 'GTR')

        char = egglib.Align.create(
               [('one',   'GGCGAGCGACGCCCCTGGCGA'),
                ('two',   'GGCGAGAGACTCCTCTGGCGA'),
                ('three', 'GGCGTGAGACGGCTCTGACTA'),
                ('four',  'GGCGTGAGACGGCACTGACTA')], egglib.alphabets.Alphabet('char', 'ACGT', None))
        with self.assertRaises(ValueError):
            tree, stats = egglib.wrappers.phyml(char, 'HKY85')

    def test_labels(self):
        cs = egglib.coalesce.Simulator(2, num_chrom=[4, 4], migr=0.01, theta=4, num_alleles=4)
        aln = cs.simul()
        dna = egglib.Align(egglib.alphabets.DNA)
        for i, seq in enumerate(aln):
            dna.add_sample('seq{0}'.format(i+1), ['ACGT'[i] for i in seq.sequence], seq.labels)

        tree, lk = egglib.wrappers.phyml(dna, 'HKY85', labels=False, verbose=False)
        T = egglib.Tree(string=tree.newick())
        self.assertListEqual(sorted([n.label for n in T.iter_leaves()]), sorted(dna.names()))

        tree, lk = egglib.wrappers.phyml(dna, 'HKY85', labels=True)
        ctrl = [seq.name + '@' + ','.join(seq.labels) for seq in dna]
        self.assertListEqual(sorted([n.label for n in tree.iter_leaves()]), sorted(ctrl))
        tree.newick()
