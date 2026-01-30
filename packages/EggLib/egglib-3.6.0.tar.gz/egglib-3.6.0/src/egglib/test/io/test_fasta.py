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

import os, egglib, sys, unittest, random, re, gc, time, tempfile, pathlib
import collections
path = pathlib.Path(__file__).parent / '..' / 'data'

class Fasta_test(unittest.TestCase):
    def test_from_fasta_T(self):
        fname_T='align1_T.fas'
        aln = egglib.io.from_fasta(os.path.join(path, fname_T), egglib.alphabets.DNA)
        self.assertIsInstance(aln, egglib.Align)
        self.assertEqual(aln.ns, 101)
        self.assertEqual(aln.ls, 8942)

    def test_from_fasta_E(self):
        fname_T='align1_T.fas'
        fname_F='align1_F.fas'
        with self.assertRaises(ValueError):
            aln = egglib.io.from_fasta(os.path.join(path, fname_T), egglib.alphabets.DNA, labels=False, cls='LOL') 
            #an error integrated in the "cls" parameter
        with self.assertRaises(ValueError):
            aln = egglib.io.from_fasta(os.path.join(path, fname_F), egglib.alphabets.DNA, labels=False, cls='Align') 
            #The file 'align1_E.fs', contains sequences of differents sizes

    def setUp(self):
        fname='align1_T.fas'
        self.iter_aln=egglib.io.fasta_iter(os.path.join(path, fname), egglib.alphabets.DNA)

    def tearDown(self):
        del self.iter_aln

    def test_fasta_iter_T(self):
        self.assertIsInstance(self.iter_aln, egglib.io.fasta_iter)
        self.assertIsInstance(self.iter_aln, collections.abc.Iterable)

    def test__enter__T(self):
        with self.iter_aln as iter_aln:
            self.assertIsInstance(iter_aln, egglib.io.fasta_iter)

    def test__exit__T(self):
        ext=self.iter_aln.__exit__(None, None, None)
        self.assertFalse(ext)
        with self.assertRaises(StopIteration):
            next(self.iter_aln)

    def test__iter__T(self):
        self.assertIsInstance(self.iter_aln, collections.abc.Iterable)

    def test_next_T(self):
        self.assertIsInstance(next(self.iter_aln), egglib._interface.SampleView)

    def test_next_E(self):
        fname_E='align1_E.fas'
        iter_alnE=egglib.io.fasta_iter(os.path.join(path, fname_E), egglib.alphabets.DNA, True)
        with self.assertRaises(StopIteration):
            next(iter_alnE)

    def test_separator_E(self):
        try:
            f, fname = tempfile.mkstemp()
            os.write(f, b'''\
>one@a,a
AAAAAAAAAAAAAAAAAAAA
>two@a,a
AAAAAAAAAAAAAAAAAAAA
>three@a,b
AAAAAAAAAAAAAAAAAAAA
>four@a,b
AAAAAAAAAAAAAAAAAAAA
>five@b,c
AAAAAAAAAAAAAAAAAAAA
>six@b,c
AAAAAAAAAAAAAAAAAAAA
>seven@b,d
AAAAAAAAAAAAAAAAAAAA
>eight@b,d
AAAAAAAAAAAAAAAAAAAA
>outgroup@#
AAAAAAAAAAAAAAAAAAAA
''')
            os.close(f)
            aln = egglib.io.from_fasta(fname, egglib.alphabets.DNA, True)
            aln2 = egglib.io.from_fasta(fname, egglib.alphabets.DNA, True)

            self.assertListEqual([list(sam[2]) for sam in aln], [list(sam[2]) for sam in aln2])

            aln2[0].labels[1] = 'a-x'
            aln2[1].labels[1] = 'a-x'

            aln2.fasta(fname, labels=True)
            aln3 = egglib.io.from_fasta(fname, egglib.alphabets.DNA, True)
            self.assertListEqual([list(sam[2]) for sam in aln2], [list(sam[2]) for sam in aln3])

            aln2[0].labels[1] = 'a,x'
            aln2[1].labels[1] = 'a,x'

            with self.assertRaises(ValueError):
                aln2.fasta(fname, labels=True)
        finally:
            if os.path.isfile(fname): os.unlink(fname)
