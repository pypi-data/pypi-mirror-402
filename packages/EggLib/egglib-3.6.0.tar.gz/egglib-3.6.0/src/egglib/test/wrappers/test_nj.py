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

import unittest, egglib, pathlib
path = pathlib.Path(__file__).parent / '..' / 'data'

class nj_test(unittest.TestCase):

    def setUp(self):
        self.aln1 = egglib.io.from_fasta(str(path / 'example.fas'), alphabet=egglib.alphabets.DNA, cls=egglib.Align, labels=True)
        cds = egglib.Align.create(self.aln1)
        cds.to_codons()
        self.prot1 = egglib.tools.translate(cds)

        self.prot2 = egglib.Align(alphabet=egglib.alphabets.protein)
        self.prot2.add_sample('A', 'MVTLISRTKLVS')
        self.prot2.add_sample('B', 'MVTLISLTKLVS')
        self.prot2.add_sample('C', 'MVTLIKNSRIWT')
        self.prot2.add_sample('D', 'MVTIIMNSRIWT')
        self.prot2.add_sample('E', 'MVTIIMNSRIWT')
        self.prot2.add_sample('out', 'MGWALKRSKIVT')

        self.aln2 = egglib.Align(alphabet=egglib.alphabets.DNA)
        self.aln2.add_sample('A', 'AATCACATAAGTAGAGCTAAAAAAAAAAAAAAAAAACCCCCCCCGGGGGGGG')
        self.aln2.add_sample('B', 'AATCGCATAAGTAGAGCTAAAAAAAAAAAAAAAAAACCCCCCCCGGGGGGGG')
        self.aln2.add_sample('C', 'ACACGCATAAGTATACAGAAAAAAAAAAAAAAAAAACCCCCCCCGGGGGGGG')
        self.aln2.add_sample('D', 'ACACGAGTAAGCATACAGAAAAAAAAAAAAAAAAAACCCCCCCCGGGGGGGG')
        self.aln2.add_sample('E', 'ACACGAGTAAGTATACAGAAAAAAAAAAAAAAAAAACCCCCCCCGGGGGGGG')
        self.aln2.add_sample('out', 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACCCCCCCCGGGGGGGG')

    def test_default(self):
        self.assertIsInstance(egglib.wrappers.nj(self.aln1, model='LD'), egglib.Tree)
        self.assertIsInstance(egglib.wrappers.nj(self.prot1, model='JTT'), egglib.Tree)
        self.assertIsInstance(egglib.wrappers.nj(self.aln1, model='K80'), egglib.Tree)
        self.assertIsInstance(egglib.wrappers.nj(self.aln1, model='K80', kappa=2.5, randomize=True, outgroup='Spider'), egglib.Tree)

    def test_simple(self):
        for aln, models in [(self.aln2, ['JC69', 'K80', 'F84', 'LD']), (self.prot2, ['PAM', 'JTT', 'PMB'])]:
            for model in models:
                for upgma in False, True:
                    tree = egglib.wrappers.nj(aln, upgma=upgma, model=model)
                    self.assertEqual(set([leaf.label for leaf in tree.iter_leaves()]), set(['A', 'B', 'C', 'D', 'E', 'out']))
                    self.assertEqual(set(tree.base.leaves_down()), set(['A', 'B', 'C', 'D', 'E', 'out']))

                tree = egglib.wrappers.nj(aln, model=model, outgroup='out')
                self.assertEqual(set([leaf.label for leaf in tree.iter_leaves()]), set(['A', 'B', 'C', 'D', 'E', 'out']))
                self.assertEqual(set(tree.base.leaves_down()), set(['A', 'B', 'C', 'D', 'E', 'out']))
                n1, n2, n3 = tree.base.children()
                L1 = n1.leaves_down()
                L2 = n2.leaves_down()
                L3 = n3.leaves_down()
                self.assertEqual(set((frozenset(L1), frozenset(L2), frozenset(L3))),
                    set([frozenset(['out']), frozenset(['A', 'B']), frozenset(['C', 'D', 'E'])]))

    def test_options(self):

        # error if invalid alphabet
        aln3 = egglib.Align.create(list(self.aln2), alphabet = egglib.alphabets.Alphabet('char', case_insensitive=True, expl='ACGT', miss=[]))
        with self.assertRaises(ValueError) as exp: tree = egglib.wrappers.nj(aln3)
        self.assertIn('invalid alphabet', str(exp.exception))

        # error if alphabet is not match (correct alphabets all testing in test_simple)
        for aln, models in [(self.prot2, ['JC69', 'K80', 'F84', 'LD']), (self.aln2, ['PAM', 'JTT', 'PMB'])]:
            for model in models:
                with self.assertRaises(ValueError) as exp: tree = egglib.wrappers.nj(aln, model=model)
                self.assertIn('invalid model', str(exp.exception))

        # kappa not supported for protein models
        for model in ['PAM', 'JTT', 'PMB']:
            with self.assertRaises(ValueError) as exp: tree = egglib.wrappers.nj(self.prot2, model=model, kappa=2.5)
            self.assertIn('kappa argument not supported', str(exp.exception))

        # kappa not supported for some DNA models
        for model in ['JC69', 'LD']:
            with self.assertRaises(ValueError) as exp: tree = egglib.wrappers.nj(self.aln2, model=model, kappa=2.5)
            self.assertIn('kappa argument not supported', str(exp.exception))

        # outgroup must be valid name and outgroup is not supported with it
        tree = egglib.wrappers.nj(self.aln2, outgroup='out')
        tree = egglib.wrappers.nj(self.aln2, outgroup='A')
        with self.assertRaises(ValueError) as exp:
            tree = egglib.wrappers.nj(self.aln2, outgroup='Z')
        self.assertEqual('invalid name for outgroup: Z', str(exp.exception))
        tree = egglib.wrappers.nj(self.aln2, upgma=True)
        with self.assertRaises(ValueError) as exp:
            tree = egglib.wrappers.nj(self.aln2, upgma=True, outgroup='out')
        self.assertIn('outgroup cannot be set', str(exp.exception))

        # randomize
        tree1 = egglib.wrappers.nj(self.aln2, randomize=False)
        tree2 = egglib.wrappers.nj(self.aln2, randomize=True)

        # include_outgroup
        tree1 = egglib.wrappers.nj(self.aln2)
        tree2 = egglib.wrappers.nj(self.aln2)
        tree3 = egglib.wrappers.nj(self.aln2)
        self.assertEqual(set(self.aln2.names()), set(tree1.base.leaves_down()))
        self.assertEqual(set(self.aln2.names()), set(tree2.base.leaves_down()))
        self.assertEqual(set(self.aln2.names()), set(tree3.base.leaves_down()))
