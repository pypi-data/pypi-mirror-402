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

import egglib, unittest, tempfile

ms_binary_no_spacer_header = """Example ms output

// <you may add stuff here>
segsites: 4
positions: 0.00000 0.33333 0.66667 1.00000
0100
0010
0101
1113

"""

ms_binary_no_spacer = """//
segsites: 4
positions: 0.00000 0.33333 0.66667 1.00000
0100
0010
0101
1113

"""

ms_binary_no_spacer_without_last = """//
segsites: 4
positions: 0.00000 0.33333 0.66667 1.00000
0100
0010
0101

"""

ms_binary_spacer = """//
segsites: 4
positions: 0.00000 0.33333 0.66667 1.00000
0 1 0 0
0 0 1 0
0 1 0 1
1 1 1 3

"""
ms_binary_no_spacer_shift = """//
segsites: 4
positions: 0.00000 0.33333 0.66667 1.00000
1211
1121
1212
2224

"""

ms_binary_spacer_shift = """//
segsites: 4
positions: 0.00000 0.33333 0.66667 1.00000
1 2 1 1
1 1 2 1
1 2 1 2
2 2 2 4

"""

ms_binary_spacer_shift_down = """//
segsites: 4
positions: 0.00000 0.33333 0.66667 1.00000
-1 0 -1 -1
-1 -1 0 -1
-1 0 -1 0
0 0 0 2

"""

ms_binary_alt_pos = """//
segsites: 4
positions: 0.00000 0.10000 0.50000 0.90000
0100
0010
0101
1113

"""

class MS_test(unittest.TestCase):

    def setUp(self):
        self.alph_binary = egglib.alphabets.Alphabet('int', [0, 1, 2, 3], [])
        self.align_binary = egglib.Align.create([('', [0, 1, 0, 0]), ('', [0, 0, 1, 0]),
                         ('', [0, 1, 0, 1]), ('', [1, 1, 1, 3])],
                            alphabet=self.alph_binary)
        self.align_DNA = egglib.Align.create([('', 'ACAA'), ('', 'AACA'),
                         ('', 'ACAC'), ('', 'CCCT')], alphabet=egglib.alphabets.DNA)
        self.assertEqual(self.align_DNA._obj.get_sample(0, 0), egglib.alphabets.DNA.get_code('A'))
        self.assertEqual(self.align_DNA._obj.get_sample(0, 1), egglib.alphabets.DNA.get_code('C'))
        self.assertEqual(self.align_DNA._obj.get_sample(3, 3), egglib.alphabets.DNA.get_code('T'))
        charalphabet = egglib.alphabets.Alphabet('char', 'ACGT', [])
        stringalphabet = egglib.alphabets.Alphabet('string', 'ACGT', [])
        customalphabet = egglib.alphabets.Alphabet('custom', 'ACGT', [])
        self.char_aln = egglib.Align.create([('', 'ACAA'), ('', 'AACA'), ('', 'ACAC'), ('', 'CCCT')], alphabet=charalphabet)
        self.string_aln = egglib.Align.create([('', 'ACAA'), ('', 'AACA'), ('', 'ACAC'), ('', 'CCCT')], alphabet=stringalphabet)
        self.custom_aln = egglib.Align.create([('', 'ACAA'), ('', 'AACA'), ('', 'ACAC'), ('', 'CCCT')], alphabet=customalphabet)

    def test_ms_errors(self):
        with self.assertRaises(TypeError):
            egglib.io.to_ms(egglib.Container(self.alph_binary), None) # invalid type of object
        egglib.io.to_ms(egglib.Align(self.alph_binary), None) # control
        with self.assertRaises(TypeError):
            egglib.io.to_ms([], None) # invalid type of object
        with self.assertRaises(ValueError):
            egglib.io.to_ms(self.align_binary, None, positions=[0.0, 0.1]) # invalid number of positions
        with self.assertRaises(TypeError):
            egglib.io.to_ms(self.align_binary, alphabet=egglib.alphabets.DNA) # invalid alphabet
        with self.assertRaises(ValueError):
            egglib.io.to_ms(self.align_binary, None, converter=lambda x:x+10, spacer=False) # unavailable spacer

    def test_as_string(self):
        # check string output and output format
        self.assertEqual(egglib.io.to_ms(self.align_binary, None), ms_binary_no_spacer)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, spacer=False), ms_binary_no_spacer)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, spacer=True), ms_binary_spacer)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, converter=lambda x:x+1), ms_binary_spacer_shift)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, converter=lambda x:x+1, spacer=False), ms_binary_no_spacer_shift)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, positions=[0, 0.1, 0.5, 0.9]), ms_binary_alt_pos)
        alph_base_1 = egglib.alphabets.Alphabet('int', [1,2,3,4,10], None)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=alph_base_1), ms_binary_spacer_shift)

        # check header
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, header='Example ms output\n\n// <you may add stuff here>\n'), ms_binary_no_spacer_header)

    def test_to_file(self):
        with tempfile.NamedTemporaryFile() as tp:
            tp.close()
            # write to file
            egglib.io.to_ms(self.align_binary, tp.name)
            with open(tp.name) as f:
                self.assertEqual(f.read(), ms_binary_no_spacer)
            with open(tp.name, 'w') as f:
                egglib.io.to_ms(self.align_binary, f)
                egglib.io.to_ms(self.align_binary, f, converter=lambda x: x+1, spacer=False)
            with open(tp.name) as f:
                self.assertEqual(f.read(), ms_binary_no_spacer + ms_binary_no_spacer_shift)

            # check header
            with open(tp.name, 'w') as f:
                egglib.io.to_ms(self.align_binary, f, header='// without spacer\n')
                egglib.io.to_ms(self.align_binary, f, header='// with spacer\n', spacer=True)
            string = ms_binary_no_spacer.replace('//', '// without spacer') + ms_binary_spacer.replace('//', '// with spacer')
            with open(tp.name) as f:
                self.assertEqual(f.read(), string)


    def test_alphabet(self):
        # testing int alphabet
        A1 = egglib.alphabets.Alphabet('int', range(0, 10), [])
        A2 = egglib.alphabets.Alphabet('int', range(-1, 10), [])
        A3 = egglib.alphabets.Alphabet('int', range(0, 11), [])
        A4 = egglib.alphabets.Alphabet('int', range(0, 10), [10])
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=A1), ms_binary_no_spacer)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=A1, spacer=True), ms_binary_spacer)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=A2), ms_binary_spacer_shift_down)
        with self.assertRaises(ValueError):
            egglib.io.to_ms(self.align_binary, None, alphabet=A2, spacer=False)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=A3), ms_binary_spacer)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=A3, spacer=False), ms_binary_no_spacer)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=A4), ms_binary_spacer)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=A4, spacer=False), ms_binary_no_spacer)

        # DNA alphabet
        with self.assertRaises(ValueError):
            egglib.io.to_ms(self.align_DNA, None)
        self.assertEqual(egglib.io.to_ms(self.align_DNA, None, converter=lambda x: x, spacer=False), ms_binary_no_spacer)

        # range alphabets
        R1 = egglib.alphabets.Alphabet('range', (0, 10), None)
        R2 = egglib.alphabets.Alphabet('range', (-1, 10), None)
        R3 = egglib.alphabets.Alphabet('range', (0, 11), None)
        R4 = egglib.alphabets.Alphabet('range', (0, 10), (10, 11))
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=R1), ms_binary_no_spacer)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=R1, spacer=True), ms_binary_spacer)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=R2), ms_binary_spacer_shift_down)
        with self.assertRaises(ValueError):
            egglib.io.to_ms(self.align_binary, None, alphabet=R2, spacer=False)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=R3), ms_binary_spacer)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=R3, spacer=False), ms_binary_no_spacer)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=R4), ms_binary_spacer)
        self.assertEqual(egglib.io.to_ms(self.align_binary, None, alphabet=R4, spacer=False), ms_binary_no_spacer)

        # tests that char/string/custom alphabets don't work
        with self.assertRaises(ValueError): egglib.io.to_ms(self.char_aln, None)
        with self.assertRaises(ValueError): egglib.io.to_ms(self.string_aln, None)
        with self.assertRaises(ValueError): egglib.io.to_ms(self.custom_aln, None)

    def test_as_codes(self):
        # show that values and codes are different for an int alphabet
        alph_binary2 = egglib.alphabets.Alphabet('int', [5, 6, 1, 2], [3])
        aln = egglib.Align.create([('', [1, 5, 1, 3]),
                                   ('', [1, 5, 5, 1]),
                                   ('', [2, 6, 3, 2]),
                                   ('', [2, 5, 5, 2])], alphabet=alph_binary2)
        str1 = '//\nsegsites: 4\npositions: 0.00000 0.33333 0.66667 1.00000\n1513\n1551\n2632\n2552\n\n'
        str2 = '//\nsegsites: 4\npositions: 0.00000 0.33333 0.66667 1.00000\n2 0 2 -1\n2 0 0 2\n3 1 -1 3\n3 0 0 3\n\n'
        self.assertEqual(egglib.io.to_ms(aln, None), str1)
        self.assertEqual(egglib.io.to_ms(aln, None, as_codes=True), str2)
        with self.assertRaises(ValueError):
            egglib.io.to_ms(aln, None, as_codes=True, spacer=False)

        # show that it is possible to print DNA/char/string/custom alphabets by codes
        self.assertEqual(egglib.io.to_ms(self.align_DNA, None, as_codes=True), ms_binary_spacer)
        self.assertEqual(egglib.io.to_ms(self.align_DNA, None, as_codes=True, spacer=False), ms_binary_no_spacer)
        self.assertEqual(egglib.io.to_ms(self.char_aln, None, as_codes=True), ms_binary_no_spacer)
        self.assertEqual(egglib.io.to_ms(self.string_aln, None, as_codes=True), ms_binary_no_spacer)
        self.assertEqual(egglib.io.to_ms(self.custom_aln, None, as_codes=True), ms_binary_no_spacer)

        # effect of code range
        str3 = '//\nsegsites: 4\npositions: 0.00000 0.33333 0.66667 1.00000\n2024\n2002\n3143\n3003\n\n'
        str4 = '//\nsegsites: 4\npositions: 0.00000 0.33333 0.66667 1.00000\n2 0 2 4\n2 0 0 2\n3 1 4 3\n3 0 0 3\n\n'
        alph_binary3 = egglib.alphabets.Alphabet('int', [5, 6, 1, 2, 3], [])
        aln = egglib.Align.create([('', [1, 5, 1, 3]),
                                   ('', [1, 5, 5, 1]),
                                   ('', [2, 6, 3, 2]),
                                   ('', [2, 5, 5, 2])], alphabet=alph_binary3)
        self.assertEqual(egglib.io.to_ms(aln, None, as_codes=True), str3)
        self.assertEqual(egglib.io.to_ms(aln, None, as_codes=True), str3)
        self.assertEqual(egglib.io.to_ms(aln, None, as_codes=True, spacer=False), str3)
        self.assertEqual(egglib.io.to_ms(aln, None, as_codes=True, spacer=True), str4)
        rng1 = egglib.alphabets.Alphabet('range', (100, 110), None)
        rng2 = egglib.alphabets.Alphabet('range', (100, 111), None)
        rng3 = egglib.alphabets.Alphabet('range', (99, 111), None)
        rng4 = egglib.alphabets.Alphabet('range', (100, 110), (0, 1))
        data = [('', [100, 104, 103, 108, 100]),
                ('', [102, 104, 106, 108, 101]),
                ('', [106, 106, 105, 108, 101])]
        aln1 = egglib.Align.create(data, alphabet=rng1)
        aln2 = egglib.Align.create(data, alphabet=rng2)
        aln3 = egglib.Align.create(data, alphabet=rng3)
        aln4 = egglib.Align.create(data, alphabet=rng4)
        strA = '//\nsegsites: 5\npositions: 0.00000 0.25000 0.50000 0.75000 1.00000\n04380\n24681\n66581\n\n'
        strB = '//\nsegsites: 5\npositions: 0.00000 0.25000 0.50000 0.75000 1.00000\n0 4 3 8 0\n2 4 6 8 1\n6 6 5 8 1\n\n'
        strC = '//\nsegsites: 5\npositions: 0.00000 0.25000 0.50000 0.75000 1.00000\n1 5 4 9 1\n3 5 7 9 2\n7 7 6 9 2\n\n'
        self.assertEqual(egglib.io.to_ms(aln1, None, as_codes=True), strA)
        self.assertEqual(egglib.io.to_ms(aln2, None, as_codes=True), strB)
        self.assertEqual(egglib.io.to_ms(aln3, None, as_codes=True), strC)
        self.assertEqual(egglib.io.to_ms(aln4, None, as_codes=True), strB)
        with self.assertRaises(ValueError):
            self.assertEqual(egglib.io.to_ms(aln2, None, as_codes=True, alphabet=rng2), strB)
