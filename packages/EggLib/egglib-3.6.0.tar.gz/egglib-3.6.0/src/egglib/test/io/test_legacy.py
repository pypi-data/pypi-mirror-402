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

class Legacy_test(unittest.TestCase):
    def test_from_clustal_T(self):
        fname='align.aln'
        string = open(path / fname).read()
        aln=egglib.io.from_clustal(string, egglib.alphabets.protein)
        self.assertIsInstance(aln, egglib._interface.Align)

    def test_from_clustal_E(self):
        fname='clustal_error1.aln'
        string = open(path / fname).read()
        with self.assertRaises(ValueError): #file with an error at the first line: without CLUSTAL...
            aln=egglib.io.from_clustal(string, egglib.alphabets.protein)

        fname='clustal_error2.aln'
        string = open(path / fname).read()
        with self.assertRaises(ValueError): #file with space before each lines
            aln=egglib.io.from_clustal(string, egglib.alphabets.protein)

        fname='clustal_error3.aln'
        string = open(path / fname).read()
        with self.assertRaises(ValueError): #file without conservation line for the first alignment
            aln=egglib.io.from_clustal(string, egglib.alphabets.protein)

        fname='clustal_error4.aln'
        string = open(path / fname).read()
        with self.assertRaises(ValueError): #file with more than 3 blocks
            aln=egglib.io.from_clustal(string, egglib.alphabets.protein)

        fname='clustal_error5.aln'
        string = open(path / fname).read()
        with self.assertRaises(ValueError): #file with fakes base numbers .
            aln=egglib.io.from_clustal(string, egglib.alphabets.protein)

        fname='clustal_error6.aln'
        string = open(path / fname).read()
        with self.assertRaises(ValueError): #file with string like base numbers .
            aln=egglib.io.from_clustal(string, egglib.alphabets.protein)

        fname='clustal_error7.aln'
        string = open(path / fname).read()
        with self.assertRaises(ValueError): #file with string like base numbers .
            aln=egglib.io.from_clustal(string, egglib.alphabets.protein)

        fname='clustal_error8.aln'
        string = open(path / fname).read()
        with self.assertRaises(ValueError): #error on next line.
            aln=egglib.io.from_clustal(string, egglib.alphabets.protein)

        with self.assertRaises(ValueError):
            aln=egglib.io.from_clustal(string, egglib.alphabets.codons)
        bidon = egglib.alphabets.Alphabet('char', '01', 'N', name='binary')
        with self.assertRaises(ValueError):
            aln=egglib.io.from_clustal(string, bidon)
        with self.assertRaises(ValueError):
            aln=egglib.io.from_clustal(string, egglib.alphabets.DNA)

    def test_clustal_ania(self):
        # I don't remember where we picked this file - ania is the first sequence
        string = open(path / 'ania.clu').read()
        aln = egglib.io.from_clustal(string, egglib.alphabets.protein)


    def test_from_staden_T(self):
        fname='example.sta'
        string = open(path / fname).read()
        stn=egglib.io.from_staden(string,keep_consensus=True)
        stn2=egglib.io.from_staden(string,keep_consensus=False)
        self.assertIsInstance(stn, egglib._interface.Align)
        self.assertIn("CONSENSUS", stn)
        self.assertNotIn("CONSENSUS", stn2)

    def test_from_staden_E(self):
        fname='example_E.sta'
        string = open(path / fname).read()
        with self.assertRaises(ValueError): #file with an error at the first line: without CLUSTAL...
            stn=egglib.io.from_staden(string,keep_consensus=True)

    def test_from_genalys_T(self):
        fname='example.gnl'
        string = open(path / fname).read()
        gnl=egglib.io.from_genalys(string)
        self.assertEqual(str(type(gnl)), "<class 'egglib._interface.Align'>")
        self.assertEqual(gnl.get_name(0),'L0738D_HM55_Leg196F_F10_070.ab1')
        self.assertTrue(gnl.ns >0)
    
    def test_get_fgenesh_T(self):
        fname='example.fg'
        string = open(path / fname).read()
        fgh=egglib.io.get_fgenesh(string)
        self.assertIsInstance(fgh, list)
        self.assertTrue (len(fgh)>0) #1522 
        
    def test_get_fgenesh_E(self):
        fname='example_E.fg'
        string = open(path / fname).read()
        with self.assertRaises(ValueError): 
            fgh=egglib.io.get_fgenesh(string)

        fname='example_E2.fg'
        string = open(path / fname).read()
        with self.assertRaises(ValueError): 
            fgh=egglib.io.get_fgenesh(string)

        fname='example_E3.fg'
        string = open(path / fname).read()
        with self.assertRaises(ValueError): 
            fgh=egglib.io.get_fgenesh(string)
