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

import unittest, os
import egglib
path = os.path.dirname(__file__)
path_T=os.path.join(path, '..', 'data')

class Alphabet_test(unittest.TestCase):

    def test_IntAlphabet(self):
        alph = egglib._eggwrapper.IntAlphabet()
        alph.set_name("test")
        alph.set_type("int")
        self.assertEqual(alph.get_name(), "test")
        self.assertEqual(alph.get_type(), "int")
        self.assertEqual(alph.case_insensitive(), False)
        self.assertEqual(alph.num_exploitable(), 0)
        self.assertEqual(alph.num_missing(), 0)
        alph.add_exploitable(10)
        alph.add_exploitable(11)
        alph.add_missing(-1)
        alph.add_exploitable(22)
        self.assertEqual(alph.num_exploitable(), 3)
        self.assertEqual(alph.num_missing(), 1)
        with self.assertRaises(ValueError):
            alph.add_missing(10)
        self.assertEqual(alph.get_value(0), 10)
        self.assertEqual(alph.get_value(1), 11)
        self.assertEqual(alph.get_value(2), 22)
        self.assertEqual(alph.get_value(-1), -1)
        self.assertEqual(alph.get_code(10), 0)
        self.assertEqual(alph.get_code(11), 1)
        self.assertEqual(alph.get_code(22), 2)
        self.assertEqual(alph.get_code(-1), -1)
        with self.assertRaises(ValueError):
            alph.get_code(100)

    def test_CharAlphabet(self):
        alph = egglib._eggwrapper.CharAlphabet()
        alph.set_name("test alphabet")
        alph.set_type("char")
        self.assertEqual(alph.get_name(), "test alphabet")
        self.assertEqual(alph.get_type(), "char")
        self.assertEqual(alph.case_insensitive(), False)
        self.assertEqual(alph.num_exploitable(), 0)
        self.assertEqual(alph.num_missing(), 0)
        alph.add_missing('-')
        alph.add_exploitable('A')
        alph.add_exploitable('C')
        alph.add_exploitable('G')
        alph.add_exploitable('T')
        alph.add_missing('N')
        self.assertEqual(alph.num_exploitable(), 4)
        self.assertEqual(alph.num_missing(), 2)
        with self.assertRaises(ValueError): alph.add_exploitable('T')
        with self.assertRaises(ValueError): alph.add_exploitable('-')
        with self.assertRaises(ValueError): alph.add_missing('T')
        with self.assertRaises(ValueError): alph.add_missing('-')
        self.assertEqual(alph.get_value(-1), '-')
        self.assertEqual(alph.get_value(0), 'A')
        self.assertEqual(alph.get_value(1), 'C')
        self.assertEqual(alph.get_value(2), 'G')
        self.assertEqual(alph.get_value(3), 'T')
        self.assertEqual(alph.get_value(-2), 'N')
        self.assertEqual(alph.get_code('-'), -1)
        self.assertEqual(alph.get_code('A'), 0)
        self.assertEqual(alph.get_code('C'), 1)
        self.assertEqual(alph.get_code('G'), 2)
        self.assertEqual(alph.get_code('T'), 3)
        self.assertEqual(alph.get_code('N'), -2)
        with self.assertRaises(ValueError): alph.get_code('Z')
        with self.assertRaises(ValueError): alph.get_code('a')
        with self.assertRaises(ValueError): alph.get_value(-3)
        with self.assertRaises(ValueError): alph.get_value(4)

    def test_CaseInsensitiveCharAlphabet(self):
        alph = egglib._eggwrapper.CaseInsensitiveCharAlphabet()
        alph.set_name("AlPhaBet")
        alph.set_type("char")
        self.assertEqual(alph.get_name(), "AlPhaBet")
        self.assertEqual(alph.get_type(), "char")
        self.assertEqual(alph.case_insensitive(), True)
        self.assertEqual(alph.num_exploitable(), 0)
        self.assertEqual(alph.num_missing(), 0)
        alph.add_exploitable('a')
        alph.add_exploitable('C')
        alph.add_exploitable('g')
        alph.add_exploitable('t')
        alph.add_missing('n')
        alph.add_missing('-')
        alph.add_missing('R')
        self.assertEqual(alph.num_exploitable(), 4)
        self.assertEqual(alph.num_missing(), 3)
        with self.assertRaises(ValueError): alph.add_missing('T')
        with self.assertRaises(ValueError): alph.add_exploitable('N')
        with self.assertRaises(ValueError): alph.add_missing('N')
        self.assertEqual(alph.get_value(0), 'A')
        self.assertEqual(alph.get_value(1), 'C')
        self.assertEqual(alph.get_value(2), 'G')
        self.assertEqual(alph.get_value(3), 'T')
        self.assertEqual(alph.get_value(-1), 'N')
        self.assertEqual(alph.get_value(-2), '-')
        self.assertEqual(alph.get_value(-3), 'R')
        self.assertEqual(alph.get_code('A'), 0)
        self.assertEqual(alph.get_code('a'), 0)
        self.assertEqual(alph.get_code('C'), 1)
        self.assertEqual(alph.get_code('c'), 1)
        self.assertEqual(alph.get_code('G'), 2)
        self.assertEqual(alph.get_code('g'), 2)
        self.assertEqual(alph.get_code('T'), 3)
        self.assertEqual(alph.get_code('t'), 3)
        self.assertEqual(alph.get_code('N'), -1)
        self.assertEqual(alph.get_code('n'), -1)
        self.assertEqual(alph.get_code('-'), -2)
        self.assertEqual(alph.get_code('R'), -3)
        self.assertEqual(alph.get_code('r'), -3)
        with self.assertRaises(ValueError): alph.get_code('Z')
        with self.assertRaises(ValueError): alph.get_code('*')
        for i in -4, -5, -10, 4, 5, 6:
            with self.assertRaises(ValueError): alph.get_value(i)

    def test_DNAAlphabet(self):
        alph = egglib._eggwrapper.DNAAlphabet()
        self.assertEqual(alph.get_name(), "DNA")
        self.assertEqual(alph.get_type(), "DNA")
        self.assertEqual(alph.case_insensitive(), True)
        self.assertEqual(alph.num_exploitable(), 4)
        self.assertEqual(alph.num_missing(), 13)
        with self.assertRaises(ValueError): alph.add_exploitable('Z')
        with self.assertRaises(ValueError): alph.add_missing('Z')
        for i,v in enumerate('-N?RYSWKMBDHV'):
            self.assertEqual(alph.get_value(-i-1), v)
        self.assertEqual(alph.get_value(0), 'A')
        self.assertEqual(alph.get_value(1), 'C')
        self.assertEqual(alph.get_value(2), 'G')
        self.assertEqual(alph.get_value(3), 'T')
        self.assertEqual(alph.get_code('A'), 0)
        self.assertEqual(alph.get_code('a'), 0)
        self.assertEqual(alph.get_code('C'), 1)
        self.assertEqual(alph.get_code('c'), 1)
        self.assertEqual(alph.get_code('G'), 2)
        self.assertEqual(alph.get_code('g'), 2)
        self.assertEqual(alph.get_code('T'), 3)
        self.assertEqual(alph.get_code('t'), 3)
        self.assertEqual(alph.get_code('-'), -1)
        self.assertEqual(alph.get_code('N'), -2)
        self.assertEqual(alph.get_code('n'), -2)
        self.assertEqual(alph.get_code('?'), -3)
        for i,v in enumerate('RYSWKMBDHV'):
            self.assertEqual(alph.get_code(v), -4-i)
        with self.assertRaises(ValueError): alph.get_code('Z')
        for i in 4, 5, 6, 7, 8, 10, 15, 123, 148, 230, -14, -15, -16, -17:
            with self.assertRaises(ValueError): alph.get_value(i)

    def test_StringAlphabet(self):
        alph = egglib._eggwrapper.StringAlphabet()
        alph.set_name("specific indel alphabet");
        alph.set_type("string")
        self.assertEqual(alph.get_name(), "specific indel alphabet")
        self.assertEqual(alph.get_type(), "string")
        self.assertEqual(alph.case_insensitive(), False)
        self.assertEqual(alph.num_exploitable(), 0)
        self.assertEqual(alph.num_missing(), 0)
        alph.add_exploitable('TA')
        alph.add_exploitable('TAAA')
        alph.add_missing('.')
        alph.add_exploitable('TAAAAAA')
        alph.add_exploitable('TAAAAAa')
        self.assertEqual(alph.num_exploitable(), 4)
        self.assertEqual(alph.num_missing(), 1)
        with self.assertRaises(ValueError):
            alph.add_exploitable('.')
        self.assertEqual(alph.get_value(0), 'TA')
        self.assertEqual(alph.get_value(1), 'TAAA')
        self.assertEqual(alph.get_value(-1), '.')
        self.assertEqual(alph.get_value(2), 'TAAAAAA')
        self.assertEqual(alph.get_value(3), 'TAAAAAa')
        self.assertEqual(alph.get_code('TA'), 0)
        self.assertEqual(alph.get_code('TAAA'), 1)
        self.assertEqual(alph.get_code('.'), -1)
        self.assertEqual(alph.get_code('TAAAAAA'), 2)
        self.assertEqual(alph.get_code('TAAAAAa'), 3)
        with self.assertRaises(ValueError):
            alph.get_code('TAAAAaa')
        with self.assertRaises(ValueError): alph.get_value(5)
        with self.assertRaises(ValueError): alph.get_value(-2)

    def test_CustomStringAlphabet(self):
        alph = egglib._eggwrapper.CustomStringAlphabet()
        alph.set_name("specific indel alphabet");
        alph.set_type("custom")
        self.assertEqual(alph.get_name(), "specific indel alphabet")
        self.assertEqual(alph.get_type(), "custom")
        self.assertEqual(alph.case_insensitive(), False)
        self.assertEqual(alph.num_exploitable(), 0)
        self.assertEqual(alph.num_missing(), 0)
        alph.add_exploitable('TA')
        alph.add_exploitable('TAAA')
        alph.add_missing('.')
        alph.add_exploitable('TAAAAAA')
        alph.add_exploitable('TAAAAAa')
        self.assertEqual(alph.num_exploitable(), 4)
        self.assertEqual(alph.num_missing(), 1)
        with self.assertRaises(ValueError): alph.add_exploitable('.')
        with self.assertRaises(ValueError): alph.add_missing('.')
        with self.assertRaises(ValueError): alph.add_exploitable('TA')
        with self.assertRaises(ValueError): alph.add_missing('TA')
        self.assertEqual(alph.get_value(0), 'TA')
        self.assertEqual(alph.get_value(1), 'TAAA')
        self.assertEqual(alph.get_value(-1), '.')
        self.assertEqual(alph.get_value(2), 'TAAAAAA')
        self.assertEqual(alph.get_value(3), 'TAAAAAa')
        self.assertEqual(alph.get_code('TA'), 0)
        self.assertEqual(alph.get_code('TAAA'), 1)
        self.assertEqual(alph.get_code('.'), -1)
        self.assertEqual(alph.get_code('TAAAAAA'), 2)
        self.assertEqual(alph.get_code('TAAAAAa'), 3)
        with self.assertRaises(ValueError): alph.get_code('TAAAAaa')
        with self.assertRaises(ValueError): alph.get_value(4)
        with self.assertRaises(ValueError): alph.get_value(5)
        with self.assertRaises(ValueError): alph.get_value(-2)

    def test_CaseInsensitiveStringAlphabet(self):
        alph = egglib._eggwrapper.CaseInsensitiveStringAlphabet()
        alph.set_name("case insensitive, specific indel alphabet");
        alph.set_type("string")
        self.assertEqual(alph.get_name(), "case insensitive, specific indel alphabet")
        self.assertEqual(alph.get_type(), "string")
        self.assertEqual(alph.case_insensitive(), True)
        self.assertEqual(alph.num_exploitable(), 0)
        self.assertEqual(alph.num_missing(), 0)
        alph.add_exploitable('TA')
        alph.add_exploitable('taaa')
        alph.add_missing('.')
        alph.add_exploitable('TAAAAAA')
        with self.assertRaises(ValueError): alph.add_exploitable('TAAAAAa')
        with self.assertRaises(ValueError): alph.add_missing('tA')
        self.assertEqual(alph.num_exploitable(), 3)
        self.assertEqual(alph.num_missing(), 1)
        with self.assertRaises(ValueError): alph.add_exploitable('.')
        self.assertEqual(alph.get_value(0), 'TA')
        self.assertEqual(alph.get_value(1), 'TAAA')
        self.assertEqual(alph.get_value(-1), '.')
        self.assertEqual(alph.get_value(2), 'TAAAAAA')
        self.assertEqual(alph.get_code('TA'), 0)
        self.assertEqual(alph.get_code('tA'), 0)
        self.assertEqual(alph.get_code('ta'), 0)
        self.assertEqual(alph.get_code('TAAA'), 1)
        self.assertEqual(alph.get_code('TaAa'), 1)
        self.assertEqual(alph.get_code('.'), -1)
        self.assertEqual(alph.get_code('TAAAAAA'), 2)
        self.assertEqual(alph.get_code('TAAAAAa'), 2)
        self.assertEqual(alph.get_code('taaaaaA'), 2)
        with self.assertRaises(ValueError): alph.get_value(-2)
        with self.assertRaises(ValueError): alph.get_value(-3)
        with self.assertRaises(ValueError): alph.get_value(3)
        with self.assertRaises(ValueError): alph.get_value(4)

    def test_RangeAlphabet(self):
        alph = egglib._eggwrapper.RangeAlphabet()
        self.assertEqual(alph.get_name(), '')
        alph.set_type("range")
        alph.set_name('some SSR alphabet')
        self.assertEqual(alph.get_name(), 'some SSR alphabet')
        self.assertEqual(alph.get_type(), "range")
        self.assertEqual(alph.case_insensitive(), False)
        self.assertEqual(alph.num_exploitable(), 0)
        self.assertEqual(alph.num_missing(), 0)
        self.assertEqual(alph.first_exploitable(), 0)
        self.assertEqual(alph.end_exploitable(), 0)
        self.assertEqual(alph.first_missing(), 0)
        self.assertEqual(alph.end_missing(), 0)
        self.assertEqual(alph.min_value(), 0)
        self.assertEqual(alph.max_value(), 0)

        alph.set_exploitable(0, 1000)
        alph.set_missing(-1, 0)
        self.assertEqual(alph.num_exploitable(), 1000)
        self.assertEqual(alph.num_missing(), 1)
        self.assertEqual(alph.first_exploitable(), 0)
        self.assertEqual(alph.end_exploitable(), 1000)
        self.assertEqual(alph.first_missing(), -1)
        self.assertEqual(alph.end_missing(), 0)
        self.assertEqual(alph.min_value(), -1)
        self.assertEqual(alph.max_value(), 999)
        self.assertEqual(alph.get_value(-1), -1)
        self.assertEqual(alph.get_value(0), 0)
        self.assertEqual(alph.get_value(154), 154)
        self.assertEqual(alph.get_value(999), 999)
        with self.assertRaises(ValueError): alph.get_value(1001)
        with self.assertRaises(ValueError): alph.get_value(1000)
        with self.assertRaises(ValueError): alph.get_value(-2)
        with self.assertRaises(ValueError): alph.get_value(-5)
        self.assertEqual(alph.get_code(-1), -1)
        self.assertEqual(alph.get_code(0), 0)
        self.assertEqual(alph.get_code(5), 5)
        self.assertEqual(alph.get_code(145), 145)
        self.assertEqual(alph.get_code(999), 999)
        with self.assertRaises(ValueError): alph.get_code(-2)
        with self.assertRaises(ValueError): alph.get_code(1000)

        alph.set_exploitable(10, 14)
        alph.set_missing(-5, 2)
        self.assertEqual(alph.num_exploitable(), 4)
        self.assertEqual(alph.num_missing(), 7)
        self.assertEqual(alph.first_exploitable(), 10)
        self.assertEqual(alph.end_exploitable(), 14)
        self.assertEqual(alph.first_missing(), -5)
        self.assertEqual(alph.end_missing(), 2)
        self.assertEqual(alph.min_value(), -5)
        self.assertEqual(alph.max_value(), 13)
        self.assertEqual(alph.get_value(0), 10)
        self.assertEqual(alph.get_value(1), 11)
        self.assertEqual(alph.get_value(2), 12)
        self.assertEqual(alph.get_value(3), 13)
        self.assertEqual(alph.get_value(-1), -5)
        self.assertEqual(alph.get_value(-2), -4)
        self.assertEqual(alph.get_value(-3), -3)
        self.assertEqual(alph.get_value(-4), -2)
        self.assertEqual(alph.get_value(-5), -1)
        self.assertEqual(alph.get_value(-6), 0)
        self.assertEqual(alph.get_value(-7), 1)
        for i in -8, -9, -10, -12, 4, 5, 10, 12, 14, 18:
            with self.assertRaises(ValueError): alph.get_value(i)
        self.assertEqual(alph.get_code(10), 0)
        self.assertEqual(alph.get_code(11), 1)
        self.assertEqual(alph.get_code(12), 2)
        self.assertEqual(alph.get_code(13), 3)
        self.assertEqual(alph.get_code(-5), -1)
        self.assertEqual(alph.get_code(-4), -2)
        self.assertEqual(alph.get_code(-3), -3)
        self.assertEqual(alph.get_code(-2), -4)
        self.assertEqual(alph.get_code(-1), -5)
        self.assertEqual(alph.get_code(0), -6)
        self.assertEqual(alph.get_code(1), -7)
        for i in [-6, -7, -8, -10, -12, -14, -15, 2, 3, 4, 5, 6, 7, 8, 9,
                    14, 15, 16, 22, 52, 63, 70, 125, 156]:
            with self.assertRaises(ValueError):
                alph.get_code(i)
        alph2 = egglib._eggwrapper.RangeAlphabet()
        alph2.set_exploitable(-5, 12)
        alph2.set_missing(44, 46)
        self.assertEqual(alph2.min_value(), -5)
        self.assertEqual(alph2.max_value(), 45)

    def test_Alphabet(self):

        # testing category/insensitive combinations
        egglib.alphabets.Alphabet('int', [], [], False)
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('int', [], [], True)
        egglib.alphabets.Alphabet('char', [], [], False)
        egglib.alphabets.Alphabet('char', [], [], True)
        egglib.alphabets.Alphabet('string', [], [], False)
        egglib.alphabets.Alphabet('string', [], [], True)
        egglib.alphabets.Alphabet('custom', [], [], False)
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('custom', [], [], True)
        egglib.alphabets.Alphabet('range', None, None, False)
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('range', None, None, True)
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('invalid', [], [], False)

        # testing name and identity properties
        alph = egglib.alphabets.Alphabet('int', [], [], False, "a name")
        self.assertEqual(alph.name, "a name")
        self.assertEqual(alph.type, 'int')
        self.assertEqual(alph.case_insensitive, False)
        alph = egglib.alphabets.Alphabet('int', [], [], False, None)
        self.assertEqual(alph.name, "IntAlphabet")
        self.assertEqual(alph.type, 'int')
        self.assertEqual(alph.case_insensitive, False)
        alph = egglib.alphabets.Alphabet('char', [], [], False, None)
        self.assertEqual(alph.name, "CharAlphabet")
        self.assertEqual(alph.type, 'char')
        self.assertEqual(alph.case_insensitive, False)
        alph = egglib.alphabets.Alphabet('char', [], [], True)
        self.assertEqual(alph.name, "CaseInsensitiveCharAlphabet")
        self.assertEqual(alph.type, 'char')
        self.assertEqual(alph.case_insensitive, True)
        alph = egglib.alphabets.Alphabet('string', [], [], False, None)
        self.assertEqual(alph.type, 'string')
        self.assertEqual(alph.case_insensitive, False)
        self.assertEqual(alph.name, "StringAlphabet")
        alph = egglib.alphabets.Alphabet('string', [], [], True)
        self.assertEqual(alph.type, 'string')
        self.assertEqual(alph.case_insensitive, True)
        self.assertEqual(alph.name, "CaseInsensitiveStringAlphabet")
        alph = egglib.alphabets.Alphabet('custom', [], [], False)
        self.assertEqual(alph.type, 'custom')
        self.assertEqual(alph.case_insensitive, False)
        self.assertEqual(alph.name, "CustomStringAlphabet")
        alph = egglib.alphabets.Alphabet('range', None, None, False)
        self.assertEqual(alph.type, 'range')
        self.assertEqual(alph.case_insensitive, False)
        self.assertEqual(alph.name, "RangeAlphabet")
        alph.name = "a new name"
        self.assertEqual(alph.name, 'a new name')

        # testing alleles for int alphabet
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('int', [1], [1], False)
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('int', [1,1], [0], False)
        with self.assertRaises(TypeError): egglib.alphabets.Alphabet('int', [0, '1'], [2], False)
        alph = egglib.alphabets.Alphabet('int', [], [], False)
        self.assertEqual(alph.get_alleles(), ([], []))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (0, 0, 0))
        alph = egglib.alphabets.Alphabet('int', [1,2,7,5,0], [-4, 12, 3])
        self.assertEqual(alph.get_alleles(), ([1,2,7,5,0], [-4, 12, 3]))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (8, 5, 3))
        for i,v in enumerate(alph.get_alleles()[0]):
            self.assertEqual(alph.get_code(v), i)
            self.assertEqual(alph.get_value(i), v)
        for i,v in enumerate(alph.get_alleles()[1]):
            self.assertEqual(alph.get_code(v), -i-1)
            self.assertEqual(alph.get_value(-i-1), v)
        alph.add_exploitable(15)
        alph.add_exploitable(18)
        alph.add_missing(-999)
        alph.add_missing(-9999)
        alph.add_missing(-100)
        with self.assertRaises(ValueError): alph.add_exploitable(12)
        with self.assertRaises(TypeError): alph.add_exploitable('A')
        with self.assertRaises(TypeError): alph.add_exploitable('AAA')
        self.assertEqual(alph.get_alleles(), ([1,2,7,5,0,15,18], [-4, 12, 3,-999,-9999,-100]))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (13, 7, 6))
        for i,v in enumerate(alph.get_alleles()[0]):
            self.assertEqual(alph.get_code(v), i)
            self.assertEqual(alph.get_value(i), v)
        for i,v in enumerate(alph.get_alleles()[1]):
            self.assertEqual(alph.get_code(v), -i-1)
            self.assertEqual(alph.get_value(-i-1), v)

        # testing alleles for char alphabet
        with self.assertRaises(TypeError): egglib.alphabets.Alphabet('char', ['A', 'AA'], ['0'], False)
        with self.assertRaises(TypeError): egglib.alphabets.Alphabet('char', [0, '1'], [2], False)
        alph = egglib.alphabets.Alphabet('char', 'ACGTt', ['N', '?'], False)
        self.assertEqual(alph.get_alleles(), (['A', 'C', 'G', 'T', 't'], ['N', '?']))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (7, 5, 2))
        for i,v in enumerate(alph.get_alleles()[0]):
            self.assertEqual(alph.get_code(v), i)
            self.assertEqual(alph.get_value(i), v)
        for i,v in enumerate(alph.get_alleles()[1]):
            self.assertEqual(alph.get_code(v), -i-1)
            self.assertEqual(alph.get_value(-i-1), v)
        alph.add_exploitable('a')
        alph.add_exploitable('c')
        alph.add_missing('n')
        self.assertEqual(alph.get_alleles(), (['A', 'C', 'G', 'T', 't', 'a', 'c'], ['N', '?', 'n']))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (10, 7, 3))
        for i,v in enumerate(alph.get_alleles()[0]):
            self.assertEqual(alph.get_code(v), i)
            self.assertEqual(alph.get_value(i), v)
        for i,v in enumerate(alph.get_alleles()[1]):
            self.assertEqual(alph.get_code(v), -i-1)
            self.assertEqual(alph.get_value(-i-1), v)
        with self.assertRaises(ValueError): alph.add_exploitable('n')
        with self.assertRaises(TypeError): alph.add_exploitable(1)
        with self.assertRaises(TypeError): alph.add_exploitable('AAA')

        # testing alleles for char alphabet (case insensitive)
        alph = egglib.alphabets.Alphabet('char', 'ACgT', 'n?', True)
        self.assertEqual(alph.get_alleles(), (['A', 'C', 'G', 'T'], ['N', '?']))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (6, 4, 2))
        for i,v in enumerate(alph.get_alleles()[0]):
            self.assertEqual(alph.get_code(v), i)
            self.assertEqual(alph.get_value(i), v)
        for i,v in enumerate(alph.get_alleles()[1]):
            self.assertEqual(alph.get_code(v), -i-1)
            self.assertEqual(alph.get_value(-i-1), v)
        alph.add_exploitable('U')
        alph.add_missing('r')
        alph.add_missing('V')
        self.assertEqual(alph.get_alleles(), (['A', 'C', 'G', 'T', 'U'], ['N', '?', 'R', 'V']))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (9, 5, 4))
        for i,v in enumerate(alph.get_alleles()[0]):
            self.assertEqual(alph.get_code(v), i)
            self.assertEqual(alph.get_value(i), v)
        for i,v in enumerate(alph.get_alleles()[1]):
            self.assertEqual(alph.get_code(v), -i-1)
            self.assertEqual(alph.get_value(-i-1), v)
        with self.assertRaises(ValueError): alph.add_exploitable('u')
        with self.assertRaises(ValueError): alph.add_missing('u')
        with self.assertRaises(ValueError): alph.add_exploitable('R')
        with self.assertRaises(ValueError): alph.add_missing('R')
        with self.assertRaises(ValueError): alph.add_exploitable('r')
        with self.assertRaises(ValueError): alph.add_missing('r')
        with self.assertRaises(TypeError): alph.add_exploitable(1)
        with self.assertRaises(TypeError): alph.add_exploitable('AAA')
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('char', 'ACGTt', 'n?', True)

        # testing alleles for string alphabet
        with self.assertRaises(TypeError): egglib.alphabets.Alphabet('string', [0, '1'], [2], False)
        alph = egglib.alphabets.Alphabet('string', 'TACG', ['n?'], False)
        self.assertEqual(alph.get_alleles(), (['T', 'A', 'C', 'G'], ['n?']))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (5, 4, 1))
        for i,v in enumerate(alph.get_alleles()[0]):
            self.assertEqual(alph.get_code(v), i)
            self.assertEqual(alph.get_value(i), v)
        for i,v in enumerate(alph.get_alleles()[1]):
            self.assertEqual(alph.get_code(v), -i-1)
            self.assertEqual(alph.get_value(-i-1), v)
        alph.add_exploitable('TAAA')
        alph.add_exploitable('Taaa')
        alph.add_missing('NNNN')
        self.assertEqual(alph.get_alleles(), (['T', 'A', 'C', 'G', 'TAAA', 'Taaa'], ['n?', 'NNNN']))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (8, 6, 2))
        for i,v in enumerate(alph.get_alleles()[0]):
            self.assertEqual(alph.get_code(v), i)
            self.assertEqual(alph.get_value(i), v)
        for i,v in enumerate(alph.get_alleles()[1]):
            self.assertEqual(alph.get_code(v), -i-1)
            self.assertEqual(alph.get_value(-i-1), v)
        with self.assertRaises(ValueError): alph.add_missing('Taaa')
        with self.assertRaises(TypeError): alph.add_exploitable(1)

        # testing alleles for case insensitive string alphabet
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('string', ['AA', 'AAA', 'AAa'], ['.'], True)
        alph = egglib.alphabets.Alphabet('string', ['AA', 'AaA'], 'n?.', True)
        self.assertEqual(alph.get_alleles(), (['AA', 'AAA'], ['N', '?', '.']))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (5, 2, 3))
        for i,v in enumerate(alph.get_alleles()[0]):
            self.assertEqual(alph.get_code(v), i)
            self.assertEqual(alph.get_value(i), v)
        for i,v in enumerate(alph.get_alleles()[1]):
            self.assertEqual(alph.get_code(v), -i-1)
            self.assertEqual(alph.get_value(-i-1), v)
        alph.add_exploitable('AAAAAA')
        alph.add_exploitable('AAAAAAAAaaaa')
        alph.add_missing('NNNN')
        self.assertEqual(alph.get_alleles(), (['AA', 'AAA', 'AAAAAA', 'AAAAAAAAAAAA'], ['N', '?', '.', 'NNNN']))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (8, 4, 4))
        for i,v in enumerate(alph.get_alleles()[0]):
            self.assertEqual(alph.get_code(v), i)
            self.assertEqual(alph.get_value(i), v)
        for i,v in enumerate(alph.get_alleles()[1]):
            self.assertEqual(alph.get_code(v), -i-1)
            self.assertEqual(alph.get_value(-i-1), v)
        with self.assertRaises(ValueError): alph.add_missing('nnnn')
        with self.assertRaises(TypeError): alph.add_exploitable(1)

        # testing alleles for custom alphabet
        with self.assertRaises(TypeError): egglib.alphabets.Alphabet('custom', ['allele1', 2], ['0'])
        with self.assertRaises(TypeError): egglib.alphabets.Alphabet('custom', ['allele1', '2'], [0])
        alph = egglib.alphabets.Alphabet('custom', ['allele1', 'allele2'], ['.'])
        self.assertEqual(alph.get_alleles(), (['allele1', 'allele2'], ['.']))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (3, 2, 1))
        for i,v in enumerate(alph.get_alleles()[0]):
            self.assertEqual(alph.get_code(v), i)
            self.assertEqual(alph.get_value(i), v)
        for i,v in enumerate(alph.get_alleles()[1]):
            self.assertEqual(alph.get_code(v), -i-1)
            self.assertEqual(alph.get_value(-i-1), v)
        with self.assertRaises(TypeError): alph.add_exploitable(1)
        alph.add_exploitable('ALLELE1')
        alph.add_missing('ALLELE2')
        alph.add_missing('?')
        self.assertEqual(alph.get_alleles(), (['allele1', 'allele2', 'ALLELE1'], ['.',  'ALLELE2', '?']))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (6, 3, 3))
        for i,v in enumerate(alph.get_alleles()[0]):
            self.assertEqual(alph.get_code(v), i)
            self.assertEqual(alph.get_value(i), v)
        for i,v in enumerate(alph.get_alleles()[1]):
            self.assertEqual(alph.get_code(v), -i-1)
            self.assertEqual(alph.get_value(-i-1), v)
        alph = egglib.alphabets.Alphabet('custom', ['allele1', '2'], ['0', '1'])
        self.assertEqual(alph.get_alleles(), (['allele1', '2'], ['0', '1']))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (4, 2, 2))
        for i,v in enumerate(alph.get_alleles()[0]):
            self.assertEqual(alph.get_code(v), i)
            self.assertEqual(alph.get_value(i), v)
        for i,v in enumerate(alph.get_alleles()[1]):
            self.assertEqual(alph.get_code(v), -i-1)
            self.assertEqual(alph.get_value(-i-1), v)

        # testing alleles for range alphabet
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('range', [0, 1, 2], None)
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('range', [0], [1, 4])
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('range', [0, 10], [5, 4])
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('range', [0, 10], [1])
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('range', [0, 10], [1,2,3])
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('range', [0, 10], [9, 15])
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('range', [0, 10], [-5, 2])
        alph = egglib.alphabets.Alphabet('range', [0, 1000], [-1, 0])
        self.assertEqual(alph.get_alleles(), ((0, 1000), (-1, 0)))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (1001, 1000, 1))
        self.assertEqual(alph.get_code(0), 0)
        self.assertEqual(alph.get_value(0), 0)
        self.assertEqual(alph.get_code(1), 1)
        self.assertEqual(alph.get_value(1), 1)
        self.assertEqual(alph.get_code(999), 999)
        self.assertEqual(alph.get_value(999), 999)
        self.assertEqual(alph.get_code(-1), -1)
        self.assertEqual(alph.get_value(-1), -1)
        with self.assertRaises(TypeError): alph.get_code('A')
        with self.assertRaises(ValueError): alph.get_code(1000)
        with self.assertRaises(ValueError): alph.get_code(-2)

        alph = egglib.alphabets.Alphabet('range', (3,3), [0, 4])
        self.assertEqual(alph.get_alleles(), (None, (0, 4)))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (4, 0, 4))
        alph = egglib.alphabets.Alphabet('range', [17, 28], None)
        self.assertEqual(alph.get_alleles(), ((17, 28), None))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (11, 11, 0))
        alph = egglib.alphabets.Alphabet('range', [0, 0], [0, 4])
        self.assertEqual(alph.get_alleles(), (None, (0, 4)))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (4, 0, 4))
        alph = egglib.alphabets.Alphabet('range', [17, 28], (4,4))
        self.assertEqual(alph.get_alleles(), ((17, 28), None))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (11, 11, 0))
        with self.assertRaises(ValueError): egglib.alphabets.Alphabet('range', [0, 10], [-10, -11])
        alph = egglib.alphabets.Alphabet('range', None, None)
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (0, 0, 0))
        alph = egglib.alphabets.Alphabet('range', (0, 10), (10, 12))
        alph = egglib.alphabets.Alphabet('range', (0, 10), (-10, 0))

        # testing the _make utility
        a = egglib._eggwrapper.IntAlphabet()
        a.set_type('int')
        a.add_exploitable(0)
        a.add_exploitable(1)
        a.add_missing(-1)
        alph = egglib.alphabets.Alphabet._make(a)
        self.assertEqual(alph.case_insensitive, False)
        self.assertEqual(alph.type, 'int')
        self.assertEqual(alph.name, '')
        self.assertEqual(alph.get_alleles(), ([0, 1], [-1]))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (3, 2, 1))
        a = egglib._eggwrapper.CharAlphabet()
        a.set_type('char')
        alph = egglib.alphabets.Alphabet._make(a)
        self.assertEqual(alph.case_insensitive, False)
        self.assertEqual(alph.type, 'char')
        self.assertEqual(alph.name, '')
        self.assertEqual(alph.get_alleles(), ([], []))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (0, 0, 0))
        alph = egglib.alphabets.Alphabet._make(egglib._eggwrapper.CaseInsensitiveCharAlphabet())
        alph._obj.set_type('char')
        self.assertEqual(alph.case_insensitive, True)
        self.assertEqual(alph.type, 'char')
        self.assertEqual(alph.name, '')
        alph.add_exploitable('a')
        alph.add_exploitable('g')
        self.assertEqual(alph.get_alleles(), (['A', 'G'], []))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (2, 2, 0))
        alph = egglib.alphabets.Alphabet._make(egglib._eggwrapper.StringAlphabet())
        alph._obj.set_type('string')
        self.assertEqual(alph.case_insensitive, False)
        self.assertEqual(alph.type, 'string')
        self.assertEqual(alph.name, '')
        alph = egglib.alphabets.Alphabet._make(egglib._eggwrapper.CaseInsensitiveStringAlphabet())
        alph._obj.set_type('string')
        self.assertEqual(alph.case_insensitive, True)
        self.assertEqual(alph.type, 'string')
        self.assertEqual(alph.name, '')
        alph = egglib.alphabets.Alphabet._make(egglib._eggwrapper.CustomStringAlphabet())
        alph._obj.set_type('custom')
        self.assertEqual(alph.case_insensitive, False)
        self.assertEqual(alph.type, 'custom')
        self.assertEqual(alph.name, '')
        alph = egglib.alphabets.Alphabet._make(egglib._eggwrapper.RangeAlphabet())
        alph._obj.set_type('range')
        self.assertEqual(alph.case_insensitive, False)
        self.assertEqual(alph.type, 'range')
        self.assertEqual(alph.name, '')
        self.assertEqual(alph.get_alleles(), (None, None))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (0, 0, 0))
        alph._obj.set_missing(-1, 0) # not allowed by the user!
        self.assertEqual(alph.get_alleles(), (None, (-1, 0)))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (1, 0, 1))
        alph._obj.set_exploitable(0, 100) # not allowed by the user!
        self.assertEqual(alph.get_alleles(), ((0, 100), (-1, 0)))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (101, 100, 1))
        alph._obj.set_name('name1')
        self.assertEqual(alph.name, 'name1')
        alph.name = 'name2'
        self.assertEqual(alph.name, 'name2')
        alph = egglib.alphabets.Alphabet._make(egglib._eggwrapper.DNAAlphabet())
        alph._obj.set_type('DNA')
        self.assertEqual(alph.name, 'DNA')
        self.assertEqual(alph.get_alleles(), (list('ACGT'), list('-N?RYSWKMBDHV')))
        self.assertEqual((alph.num_alleles, alph.num_exploitable, alph.num_missing), (17, 4, 13))
        with self.assertRaises(ValueError): alph.add_exploitable('Z')
        self.assertEqual(alph._obj.get_code('a'), alph._obj.get_code('A'))
        self.assertTrue(alph._obj.get_code('G') > 0)
        self.assertTrue(alph._obj.get_code('N') < 0)

    def test_predefined_alphabets(self):
        self.assertEqual(egglib.alphabets.DNA.get_alleles(), (list('ACGT'), list('-N?RYSWKMBDHV')))
        self.assertEqual(egglib.alphabets.positive_infinite.get_alleles(), ((0, None), (-1, 0)))
        self.assertEqual(egglib.alphabets.protein.get_alleles(), (list('ACDEFGHIKLMNPQRSTVWY*'), list('-X?')))
        self.assertEqual(egglib.alphabets.binary.get_alleles(), ([0, 1], [-9, -1, 999]))

    def test_DataBase(self):
        alph = egglib.alphabets.Alphabet('int', [0, 1], [-1])
        aln = egglib.Align(alph)
        cnt = egglib.Container(alph)
        self.assertEqual(aln.alphabet.get_alleles(), ([0, 1], [-1]))
        aln2 = egglib.Align._create_from_data_holder(aln._obj, alph)
        self.assertEqual(aln2.alphabet.get_alleles(), ([0, 1], [-1]))

    def test_all(self):
        # test alphabet lock
        self.assertTrue(egglib.alphabets.DNA.locked)
        self.assertTrue(egglib.alphabets.codons.locked)
        self.assertTrue(egglib.alphabets.protein.locked)
        self.assertTrue(egglib.alphabets.positive_infinite.locked)
        with self.assertRaises(ValueError): egglib.alphabets.DNA.add_exploitable('Z')
        with self.assertRaises(ValueError): egglib.alphabets.protein.add_exploitable('*')
        with self.assertRaises(ValueError): egglib.alphabets.codons.add_exploitable('ZZZ')
        alph = egglib.alphabets.Alphabet('range', [0, 99], [-10, 0])
        with self.assertRaises(ValueError): alph.add_exploitable((100, 150))
        with self.assertRaises(ValueError): alph.add_missing((-20, -10))
        alph = egglib.alphabets.Alphabet('int', [0, 1, 2, 3], [-1])
        alph.add_exploitable(4)
        alph.add_exploitable(5)
        alph.add_missing(-2)
        alph.lock()
        with self.assertRaises(ValueError): alph.add_exploitable(6)
        with self.assertRaises(ValueError): alph.add_missing(-3)

        # test new CodonAlphabet
        cnd = egglib.alphabets.codons
        with self.assertRaises(ValueError): cnd.get_code('ZAG')
        self.assertEqual(cnd.get_code('AAA'), 0)
        self.assertGreater(cnd.get_code('ATG'), 0)
        self.assertLess(cnd.get_code('NNN'), 0)
        self.assertLess(cnd.get_code('???'), 0)
        self.assertLess(cnd.get_code('---'), 0)
        self.assertEqual(cnd.get_value(-1), 'AA-')
        self.assertTrue(cnd.locked)
        with self.assertRaises(ValueError): cnd.add_exploitable('ZZZ')

        # test new version of ReadingFrame
        frame = egglib.tools.ReadingFrame(None, keep_truncated=True)
        self.assertEqual(frame.num_needed_bases, 0)
        self.assertEqual(frame.num_tot_bases, 0)
        self.assertEqual(frame.num_exon_bases, 0)
        self.assertEqual(frame.num_exons, 0)
        self.assertEqual(frame.num_codons, 0)
        self.assertEqual(frame.exon_index(0), None)
        self.assertEqual(frame.codon_index(0), None)
        self.assertEqual(frame.codon_position(0), None)
        self.assertEqual(frame.codon_bases(0), None)
        self.assertEqual(list(frame.iter_exon_bounds()), [])
        self.assertEqual(list(frame.iter_codons()), [])

        frame.process([], keep_truncated=False)
        self.assertEqual(frame.num_needed_bases, 0)
        self.assertEqual(frame.num_tot_bases, 0)
        self.assertEqual(frame.num_exon_bases, 0)
        self.assertEqual(frame.num_exons, 0)
        self.assertEqual(frame.num_codons, 0)
        self.assertEqual(frame.exon_index(0), None)
        self.assertEqual(frame.codon_index(0), None)
        self.assertEqual(frame.codon_position(0), None)
        self.assertEqual(frame.codon_bases(0), None)
        self.assertEqual(list(frame.iter_exon_bounds()), [])
        self.assertEqual(list(frame.iter_codons()), [])
        with self.assertRaises(ValueError): frame.process([(5, 16), (14, 22)], keep_truncated=True)
        with self.assertRaises(ValueError): frame.process([(5, 16), (22, 20)], keep_truncated=True)

        #            1         2         3         4         5
        #  012345678901234567890123456789012345678901234567890123456
        # [     00000000000      11111111            22222222       ]
        # [     00011122233      34445556            66777888       ]
        # [     01201201201      20120120            12012012       ]
         
        frame.process([(5, 16), (22, 30), (42, 50)], keep_truncated=False)
        self.assertEqual(frame.num_needed_bases, 50)
        self.assertEqual(frame.num_tot_bases, 45)
        self.assertEqual(frame.num_exon_bases, 27)
        self.assertEqual(frame.num_exons, 3)
        self.assertEqual(frame.num_codons, 9)
        self.assertEqual([frame.exon_index(i) for i in range(57)], [None]*5 + [0]*11 + [None]*6 + [1]*8 + [None]*12 + [2]*8 + [None]*7)
        self.assertEqual([frame.codon_index(i) for i in range(57)], [None]*5 + [0,0,0,1,1,1,2,2,2,3,3] + [None]*6 + [3,4,4,4,5,5,5,6] + [None]*12 + [6,6,7,7,7,8,8,8] + [None]*7)
        self.assertEqual([frame.codon_position(i) for i in range(57)], [None]*5 + [0,1,2,0,1,2,0,1,2,0,1] + [None]*6 + [2,0,1,2,0,1,2,0] + [None]*12 + [1,2,0,1,2,0,1,2] + [None]*7)
        self.assertEqual([frame.codon_bases(i) for i in range(10)], [(5,6,7),(8,9,10),(11,12,13),(14,15,22),(23,24,25),(26,27,28),(29,42,43),(44,45,46),(47,48,49),None])
        self.assertEqual(list(frame.iter_exon_bounds()), [(5,16),(22,30),(42,50)])
        self.assertEqual(list(frame.iter_codons()), [(5,6,7),(8,9,10),(11,12,13),(14,15,22),(23,24,25),(26,27,28),(29,42,43),(44,45,46),(47,48,49)])

        #            1         2         3         4         5
        #  012345678901234567890123456789012345678901234567890123456
        # [     00000000000      11111111            22222222       ]
        # [     00011122233      45556667            88999000       ]
        # [     01201201201      20120120            12012012       ]
         
        frame.process([(5, 16, 1), (22, 30, 3), (42, 50, 2)], keep_truncated=True)
        self.assertEqual(frame.num_needed_bases, 50)
        self.assertEqual(frame.num_tot_bases, 45)
        self.assertEqual(frame.num_exon_bases, 27)
        self.assertEqual(frame.num_exons, 3)
        self.assertEqual(frame.num_codons, 11)
        self.assertEqual([frame.exon_index(i) for i in range(57)], [None]*5 + [0]*11 + [None]*6 + [1]*8 + [None]*12 + [2]*8 + [None]*7)
        self.assertEqual([frame.codon_index(i) for i in range(57)], [None]*5 + [0,0,0,1,1,1,2,2,2,3,3] + [None]*6 + [4,5,5,5,6,6,6,7] + [None]*12 + [8,8,9,9,9,10,10,10] + [None]*7)
        self.assertEqual([frame.codon_position(i) for i in range(57)], [None]*5 + [0,1,2,0,1,2,0,1,2,0,1] + [None]*6 + [2,0,1,2,0,1,2,0] + [None]*12 + [1,2,0,1,2,0,1,2] + [None]*7)
        self.assertEqual([frame.codon_bases(i) for i in range(11)], [(5,6,7),(8,9,10),(11,12,13),(14,15,None), (None,None,22),(23,24,25),(26,27,28),(29,None,None),(None,42,43),(44,45,46),(47,48,49)])
        self.assertEqual(list(frame.iter_exon_bounds()), [(5,16),(22,30),(42,50)])
        self.assertEqual(list(frame.iter_codons()), [(5,6,7),(8,9,10),(11,12,13),(14,15,None), (None,None,22),(23,24,25),(26,27,28),(29,None,None),(None,42,43),(44,45,46),(47,48,49)])

        #            1         2         3         4         5
        #  012345678901234567890123456789012345678901234567890123456
        # [     00000000000      11111111            22222222       ]
        # [     000111222xx      x333444x            xx555666       ]
        # [     01201201201      20120120            12012012       ]
         
        frame.process([(5, 16, 1), (22, 30, 3), (42, 50, 2)], keep_truncated=False)
        self.assertEqual(frame.num_needed_bases, 50)
        self.assertEqual(frame.num_tot_bases, 45)
        self.assertEqual(frame.num_exon_bases, 27)
        self.assertEqual(frame.num_exons, 3)
        self.assertEqual(frame.num_codons, 7)
        self.assertEqual([frame.exon_index(i) for i in range(57)], [None]*5 + [0]*11 + [None]*6 + [1]*8 + [None]*12 + [2]*8 + [None]*7)
        self.assertEqual([frame.codon_index(i) for i in range(57)], [None]*5 + [0,0,0,1,1,1,2,2,2,None,None] + [None]*6 + [None,3,3,3,4,4,4,None] + [None]*12 + [None,None,5,5,5,6,6,6] + [None]*7)
        self.assertEqual([frame.codon_position(i) for i in range(57)], [None]*5 + [0,1,2,0,1,2,0,1,2,None,None] + [None]*6 + [None,0,1,2,0,1,2,None] + [None]*12 + [None,None,0,1,2,0,1,2] + [None]*7)
        self.assertEqual([frame.codon_bases(i) for i in range(7)], [(5,6,7),(8,9,10),(11,12,13),(23,24,25),(26,27,28),(44,45,46),(47,48,49)])
        self.assertEqual(list(frame.iter_exon_bounds()), [(5,16),(22,30),(42,50)])
        self.assertEqual(list(frame.iter_codons()), [(5,6,7),(8,9,10),(11,12,13),(23,24,25),(26,27,28),(44,45,46),(47,48,49)])

        #            1         2         3         4         5
        #  012345678901234567890123456789012345678901234567890
        # [          00000000000             1111111111      ]
        # [          01112223334             5566677788      ]
        # [          20120120120             1201201201      ]
         
        frame.process([(10, 21, 3), (34, 44, 2)], keep_truncated=True)
        self.assertEqual(frame.num_needed_bases, 44)
        self.assertEqual(frame.num_tot_bases, 34)
        self.assertEqual(frame.num_exon_bases, 21)
        self.assertEqual(frame.num_exons, 2)
        self.assertEqual(frame.num_codons, 9)
        self.assertEqual([frame.exon_index(i) for i in range(50)], [None]*10 + [0]*11 + [None]*13 + [1]*10 + [None]*6)
        self.assertEqual([frame.codon_index(i) for i in range(50)], [None]*10 + [0,1,1,1,2,2,2,3,3,3,4] + [None]*13 + [5,5,6,6,6,7,7,7,8,8] + [None]*6)
        self.assertEqual([frame.codon_position(i) for i in range(50)], [None]*10 + [2,0,1,2,0,1,2,0,1,2,0] + [None]*13 + [1,2,0,1,2,0,1,2,0,1] + [None]*6)
        self.assertEqual([frame.codon_bases(i) for i in range(10)], [(None,None,10),(11,12,13),(14,15,16),(17,18,19),(20,None,None),(None,34,35),(36,37,38),(39,40,41),(42,43,None), None])
        self.assertEqual(list(frame.iter_exon_bounds()), [(10,21),(34,44)])
        self.assertEqual(list(frame.iter_codons()), [(None,None,10),(11,12,13),(14,15,16),(17,18,19),(20,None,None),(None,34,35),(36,37,38),(39,40,41),(42,43,None)])

        #            1         2         3         4         5
        #  012345678901234567890123456789012345678901234567890
        # [          00000000000             1111111111      ]
        # [          x000111222x             xx333444xx      ]
        # [          20120120120             1201201201      ]
         
        frame.process([(10, 21, 3), (34, 44, 2)], keep_truncated=False)
        self.assertEqual(frame.num_needed_bases, 44)
        self.assertEqual(frame.num_tot_bases, 34)
        self.assertEqual(frame.num_exon_bases, 21)
        self.assertEqual(frame.num_exons, 2)
        self.assertEqual(frame.num_codons, 5)
        self.assertEqual([frame.exon_index(i) for i in range(50)], [None]*10 + [0]*11 + [None]*13 + [1]*10 + [None]*6)
        self.assertEqual([frame.codon_index(i) for i in range(50)], [None]*10 + [None,0,0,0,1,1,1,2,2,2,None] + [None]*13 + [None,None,3,3,3,4,4,4,None,None] + [None]*6)
        self.assertEqual([frame.codon_position(i) for i in range(50)], [None]*10 + [None,0,1,2,0,1,2,0,1,2,None] + [None]*13 + [None,None,0,1,2,0,1,2,None,None] + [None]*6)
        self.assertEqual([frame.codon_bases(i) for i in range(6)], [(11,12,13),(14,15,16),(17,18,19),(36,37,38),(39,40,41),None])
        self.assertEqual(list(frame.iter_exon_bounds()), [(10,21),(34,44)])
        self.assertEqual(list(frame.iter_codons()), [(11,12,13),(14,15,16),(17,18,19),(36,37,38),(39,40,41)])

        # genetic codes
        T = egglib.tools.Translator(1)
        self.assertEqual(T.translate_codon('ATG'), 'M')
        self.assertEqual(T.translate_codon('AAA'), 'K')
        self.assertEqual(T.translate_codon('AAC'), 'N')
        self.assertEqual(T.translate_codon('GAA'), 'E')
        self.assertEqual(T.translate_codon('CTA'), 'L')
        self.assertEqual(T.translate_codon('CCC'), 'P')
        self.assertEqual(T.translate_codon('TGT'), 'C')
        self.assertEqual(T.translate_codon('ATH'), 'I')
        self.assertEqual(T.translate_codon('ATM'), 'I')
        self.assertEqual(T.translate_codon('ATW'), 'I')
        self.assertEqual(T.translate_codon('ATY'), 'I')
        self.assertEqual(T.translate_codon('ATN'), 'X')
        self.assertEqual(T.translate_codon('ATV'), 'X')
        self.assertEqual(T.translate_codon('TTR'), 'L')
        self.assertEqual(T.translate_codon('CTN'), 'L')
        self.assertEqual(T.translate_codon('CTM'), 'L')
        self.assertEqual(T.translate_codon('CTR'), 'L')
        self.assertEqual(T.translate_codon('CTW'), 'L')
        self.assertEqual(T.translate_codon('CTS'), 'L')
        self.assertEqual(T.translate_codon('CTH'), 'L')
        self.assertEqual(T.translate_codon('CTD'), 'L')
        self.assertEqual(T.translate_codon('CTB'), 'L')
        self.assertEqual(T.translate_codon('TGA'), '*')

        T2 = egglib.tools.Translator(2)
        self.assertEqual(T2.translate_codon('AGA'), '*')
        self.assertEqual(T2.translate_codon('AGA'), '*')
        self.assertEqual(T2.translate_codon('ATA'), 'M')
        self.assertEqual(T2.translate_codon('TGA'), 'W')
        self.assertEqual(T2.translate_codon('CTN'), 'L')
        self.assertEqual(T2.translate_codon('ATN'), 'X')
        self.assertEqual(T2.translate_codon('GAA'), 'E')

        T5 = egglib.tools.Translator(5)
        self.assertEqual(T5.translate_codon('AGA'), 'S')
        self.assertEqual(T5.translate_codon('AGG'), 'S')
        self.assertEqual(T5.translate_codon('ATA'), 'M')
        self.assertEqual(T5.translate_codon('TGA'), 'W')
        self.assertEqual(T5.translate_codon('CTN'), 'L')
        self.assertEqual(T5.translate_codon('CTM'), 'L')
        self.assertEqual(T5.translate_codon('ATV'), 'X')
        self.assertEqual(T5.translate_codon('CCC'), 'P')

        # import an alignment with exon/intron sequences and its frame
        seq = egglib.io.from_fasta(os.path.join(path_T, 'FTLa.fas'), egglib.alphabets.DNA, labels=True)
        framepos = [(122, 323), (451, 513), (749, 789)]
        frame = egglib.tools.ReadingFrame(framepos) # remove 1 base of last exon to make
        positions = [i for (a,b) in frame.iter_exon_bounds() for i in range(a, b)]
        cds0 = seq.extract(positions)

        # convert it to exons
        test1 = egglib.io.from_fasta_string(""">one @0
ATGTTTTCTTGA
>two @#
CTGTGAATATAA
>three @0
GTGAGG
""", egglib.alphabets.DNA, labels=True)
        test1.to_codons()
        self.assertEqual(test1.alphabet.name, 'codons')
        self.assertEqual([list(sam.sequence) for sam in test1], [['ATG','TTT','TCT','TGA'], ['CTG','TGA','ATA','TAA'], ['GTG','AGG']])
        self.assertEqual(test1.ls(0), 4)
        self.assertEqual(test1.ls(1), 4)
        self.assertEqual(test1.ls(2), 2)

        test2 = egglib.io.from_fasta_string(""">one
ATGTTTTCTTGA
>two
CTGTGAATATAA
>three @#0
GTGAGGCAGTCC
>four
GTGCGGTTAGGC
""", egglib.alphabets.DNA, labels=True)
        test2.to_codons()
        self.assertEqual(test2.alphabet.name, 'codons')
        self.assertEqual([list(sam.sequence) for sam in test2], [['ATG','TTT','TCT','TGA'], ['CTG','TGA','ATA','TAA'], ['GTG','AGG','CAG','TCC'], ['GTG','CGG','TTA','GGC']])
        self.assertEqual(test2.ls, 4)
        with self.assertRaises(ValueError): test2.to_codons()

        test3 = egglib.io.from_fasta_string(""">one
ATGTTTTCTTGA
>two
CTGTGAATATAA
>three @#0
GTGAGGCAGTCC
>four
GTGCGGTTAGGC
""", egglib.alphabets.DNA, labels=True)
        test4 = egglib.tools.to_codons(test3)
        self.assertEqual(test4.alphabet.name, 'codons')
        self.assertEqual(test4.fasta(labels=True), test2.fasta(labels=True))

        cds1 = egglib.tools.to_codons(seq, frame=frame)
        self.assertEqual(cds1.ns, cds0.ns)
        self.assertEqual(cds1.ls * 3, cds0.ls)
        self.assertEqual(cds1.fasta(linelength=60), cds0.fasta(linelength=60))
        with self.assertRaises(ValueError): egglib.tools.to_codons(seq) # not a multiple of 3
        egglib.tools.to_codons(seq.extract(0, 1809))

        # to_bases
        testA = egglib.io.from_fasta_string(
""">one
ATGTTTTCTTGA
>two
CTGTGAATATAA
>three @#0
GTGAGGCAGTCC
>four
GTGCGGTTAGGC
""", egglib.alphabets.DNA, labels=True)
        testB = egglib.tools.to_codons(testA)
        self.assertEqual([j for i in testB for j in i.sequence], ['ATG','TTT','TCT','TGA', 'CTG','TGA','ATA','TAA', 'GTG','AGG','CAG','TCC', 'GTG','CGG', 'TTA','GGC'])
        testB.to_bases()
        self.assertEqual([j for i in testB for j in i.sequence], ['A','T','G','T','T','T','T','C','T','T','G','A', 'C','T','G','T','G','A','A','T','A','T','A','A', 'G','T','G','A','G','G','C','A','G','T','C','C', 'G','T','G','C','G','G', 'T','T','A','G','G','C'])

        testA = egglib.io.from_fasta_string(
""">one
ATGTTTTCT
>two
CTGTGA
>three @#0
GTGAGGCAGTCC
>four
GTGCGGTTA
""", egglib.alphabets.DNA, labels=True)
        testB = egglib.tools.to_codons(testA)
        self.assertEqual([j for i in testB for j in i.sequence], ['ATG','TTT','TCT','CTG','TGA','GTG','AGG','CAG','TCC','GTG','CGG','TTA'])
        testB.to_bases()
        self.assertEqual([j for i in testB for j in i.sequence], ['A','T','G','T','T','T','T','C','T','C','T','G','T','G','A','G','T','G','A','G','G','C','A','G','T','C','C','G','T','G','C','G','G','T','T','A'])

        cds2 = seq.extract([i for (a,b) in framepos for i in range(a,b)])
        cds3 = egglib.tools.to_bases(cds1)
        self.assertEqual(cds3.fasta(labels=True), cds2.fasta(labels=True))
        cds4 = egglib.Container.create(cds1)
        cds4.to_bases()
        self.assertEqual(cds4.fasta(labels=True), cds2.fasta(labels=True))

        # translate functions
        trans = egglib.tools.Translator(1)
        self.assertEqual(trans.translate_codon('TTT'), 'F')
        self.assertEqual(trans.translate_codon('TCA'), 'S')
        self.assertEqual(trans.translate_codon('TAG'), '*')
        trans = egglib.tools.Translator(22)
        self.assertEqual(trans.translate_codon('TTT'), 'F')
        self.assertEqual(trans.translate_codon('TCA'), '*')
        self.assertEqual(trans.translate_codon('TAG'), 'L')

        seq = ''.join(list(cds1[0].sequence))
        egglib.tools.translate(seq)
        self.assertEqual(egglib.tools.translate('gcktgcgaygartty'), 'ACDEF')
        self.assertEqual(egglib.tools.translate('ggwgggggaggtggcgaggaagatgacgtggtagttgtcgcggcagctgccaggagaagtagcaagaaaaataacatgataattatcacgacaactacctggtgatgttgctagtaatattacttgttatttttctcgtcatcttcccggcgacgtcgccagcaacatcacctgctacttctcccgccacctccc'), 'GGGGGEEDDVVVVAAAARRSSKKNNMIIITTTTW*CC**YYLLFFSSSSRRRRQQHHLLLLPPPP')
        self.assertEqual(egglib.tools.translate('AGAGTTACCAAAAACTAA'), 'RVTKN*')
        self.assertEqual(egglib.tools.translate('AGAGTTACCAAAAACTAA', code=14), 'SVTNNY')
        with self.assertRaises(ValueError): egglib.tools.translate('AGAGTTACCAAAAACTAA', in_place=True)
        self.assertEqual(egglib.tools.translate('ATGGTTACCAAAAACTAA'), 'MVTKN*')
        self.assertEqual(egglib.tools.translate('TTGGTTACCAAAAACTAA'), 'LVTKN*')
        self.assertEqual(egglib.tools.translate('ATGGTTACCAAAAACTAA', allow_alt=True), 'MVTKN*')
        self.assertEqual(egglib.tools.translate('TTGGTTACCAAAAACTAA', allow_alt=True), 'MVTKN*')
        self.assertEqual(egglib.tools.translate('---TTGGTTACCAAAAACTAA', allow_alt=True), '-MVTKN*')
        self.assertEqual(egglib.tools.translate('???TTGGTTACCAAAAACTAA', allow_alt=True), 'XLVTKN*')
        self.assertEqual(egglib.tools.translate('GTTACCAAAAACTAA', allow_alt=True), 'VTKN*')
        self.assertEqual(egglib.tools.translate('WTGGTTACCAAAAACTAA', allow_alt=False), 'XVTKN*')
        self.assertEqual(egglib.tools.translate('WTGGTTACCAAAAACTAA', allow_alt=True), 'MVTKN*')

        # translate align
        aln = egglib.io.from_fasta_string(string=
'''>@0
ATGGTTACCAAAAACTAA---
>@0
TTGGTTACCAAAAACTAA---
>@0
ATGGTTACCAAAAACTAA---
>@0
TTGGTTACCAAAAACTAA---
>@0
---TTGGTTACCAAAAACTAA
>@0
GTTACCAAAAACTAA------
>@#
WTGGTTACCAAAAACTAA---
>@#
WTGGTTACCAAAAACTAA---
''', alphabet=egglib.alphabets.DNA, labels=True)
        aln.to_codons()

        prot =     egglib.io.from_fasta_string(string='>@0\nMVTKN*-\n>@0\nLVTKN*-\n>@0\nMVTKN*-\n>@0\nLVTKN*-\n>@0\n-LVTKN*\n>@0\nVTKN*--\n>@#\nXVTKN*-\n>@#\nXVTKN*-\n', alphabet=egglib.alphabets.protein, labels=True)
        prot_alt = egglib.io.from_fasta_string(string='>@0\nMVTKN*-\n>@0\nMVTKN*-\n>@0\nMVTKN*-\n>@0\nMVTKN*-\n>@0\n-MVTKN*\n>@0\nVTKN*--\n>@#\nMVTKN*-\n>@#\nMVTKN*-\n''', alphabet=egglib.alphabets.protein, labels=True)

        prot1 = egglib.tools.translate(aln)
        self.assertEqual(prot1.fasta(labels=True), prot.fasta(labels=True))

        prot2 = egglib.tools.translate(aln, allow_alt=True)
        self.assertEqual(prot2.fasta(labels=True), prot_alt.fasta(labels=True))

        self.assertEqual(aln.alphabet, egglib.alphabets.codons)
        self.assertEqual(egglib.tools.translate(aln, in_place=True), None)
        self.assertEqual(aln.alphabet, egglib.alphabets.protein)
        self.assertEqual(aln.fasta(labels=True), prot.fasta(labels=True))

        # translate container
        cnt = egglib.io.from_fasta_string(string=
'''>@0
ATGGTTACCAAAAACTAA
>@0
TTGGTTACCAAAAACTAA
>@0
ATGGTTACCAAAAACTAA
>@0
TTGGTTACCAAAAACTAA
>@0
---TTGGTTACCAAAAACTAA
>@0
???TTGGTTACCAAAAACTAA
>@0
GTTACCAAAAACTAA
>@#
WTGGTTACCAAAAACTAA
>@#
WTGGTTACCAAAAACTAA
''', alphabet=egglib.alphabets.DNA, labels=True)
        cnt.to_codons()

        prot_ref = egglib.io.from_fasta_string(string='>@0\nMVTKN*\n>@0\nLVTKN*\n>@0\nMVTKN*\n>@0\nLVTKN*\n>@0\n-LVTKN*\n>@0\nXLVTKN*\n>@0\nVTKN*\n>@#\nXVTKN*\n>@#\nXVTKN*\n', alphabet=egglib.alphabets.protein, labels=True)
        prot_alt = egglib.io.from_fasta_string(string='>@0\nMVTKN*\n>@0\nMVTKN*\n>@0\nMVTKN*\n>@0\nMVTKN*\n>@0\n-MVTKN*\n>@0\nXLVTKN*\n>@0\nVTKN*\n>@#\nMVTKN*\n>@#\nMVTKN*\n''', alphabet=egglib.alphabets.protein, labels=True)

        prot3 = egglib.tools.translate(cnt)
        self.assertEqual(prot3.fasta(labels=True), prot_ref.fasta(labels=True))
        prot4 = egglib.tools.translate(cnt, allow_alt=True)
        self.assertEqual(prot4.fasta(labels=True), prot_alt.fasta(labels=True))

        self.assertEqual(cnt.alphabet, egglib.alphabets.codons)
        self.assertEqual(egglib.tools.translate(cnt, in_place=True, allow_alt=True), None)
        self.assertEqual(cnt.alphabet, egglib.alphabets.protein)
        self.assertEqual(cnt.fasta(labels=True), prot_alt.fasta(labels=True))

        # translate align with alternative code
        aln = egglib.io.from_fasta_string(string=
'''>
AGAAGGTTGTGA
>
ATGCGGAGATAA
''', alphabet=egglib.alphabets.DNA, labels=True)
        aln.to_codons()

        prot1 = egglib.io.from_fasta_string(string=
'''>
RRL*
>
MRR*
''', alphabet=egglib.alphabets.protein, labels=True)

        prot2 = egglib.io.from_fasta_string(string=
'''>
SKLW
>
MRS*
''', alphabet=egglib.alphabets.protein, labels=True)

        self.assertEqual(egglib.tools.translate(aln, code=1).fasta(), prot1.fasta())
        self.assertEqual(egglib.tools.translate(aln, code=24).fasta(), prot2.fasta())

        # orf_iter
        seq = 'TCAACATTGCCAATTACCTGAAACCG'
        #          S  T  L  P  I  T  *  N  X                                      F1
        #           Q  H  C  Q  L  P  E  T  X                                     F2
        #            N  I  A  N  Y  L  K  P                                       F3
        #        1 TCAACATTGCCAATTACCTGAAACCG 26
        #          ----:----|----:----|----:-
        #        1 AGTTGTAACGGTTAATGGACTTTGGC 26
        #           X  V  N  G  I  V  Q  F  R                                     F6
        #          X  L  M  A  L  *  R  F  G                                      F5
        #            *  C  Q  W  N  G  S  V                                       F4

        self.assertEqual(list(egglib.tools.orf_iter(seq)), [])
        check = []
        for start, stop, ln, frame in egglib.tools.orf_iter(seq, allow_alt=True):
            check.append((frame, ln, egglib.tools.translate(seq[start:stop]) if frame>=0 else egglib.tools.translate(egglib.tools.rc(seq[start:stop]))))
        self.assertEqual(check, [(+1, 4, 'LPIT*')])

        check = set()
        for start, stop, ln, frame in egglib.tools.orf_iter(seq, force_start=False, force_stop=False, forward_only=True):
            check.add((frame, ln, egglib.tools.translate(seq[start:stop]) if frame>=0 else egglib.tools.translate(egglib.tools.rc(seq[start:stop]))))
        self.assertEqual(check, {(+1, 6, 'STLPIT*'), (+1, 1, 'N'), (+2, 8, 'QHCQLPET'), (+3, 8, 'NIANYLKP')})

        check = set()
        for start, stop, ln, frame in egglib.tools.orf_iter(seq, force_start=False, force_stop=False):
            check.add((frame, ln, egglib.tools.translate(seq[start:stop]) if frame>=0 else egglib.tools.translate(egglib.tools.rc(seq[start:stop]))))
        self.assertEqual(check, {(-2, 4, 'LAML'), (+1, 6, 'STLPIT*'), (+1, 1, 'N'), (+2, 8, 'QHCQLPET'), (+3, 8, 'NIANYLKP'), (-3, 7, 'VSGNWQC*'), (-2, 3, 'GFR*'), (-1, 8, 'RFQVIGNV')})

        seq = 'AAATTAAATGAAAAAAAAAAAAAAAAACATAAAATGAAAA'
        #          K  L  N  E  K  K  K  K  K  H  K  M  K  X                       F1
        #           N  *  M  K  K  K  K  K  N  I  K  *  K                         F2
        #            I  K  *  K  K  K  K  K  T  *  N  E  X                        F3
        #        1 AAATTAAATGAAAAAAAAAAAAAAAAACATAAAATGAAAA 40
        #          ----:----|----:----|----:----|----:----|
        #        1 TTTAATTTACTTTTTTTTTTTTTTTTTGTATTTTACTTTT 40
        #           X  N  F  S  F  F  F  F  F  C  L  I  F                         F6
        #          X  I  L  H  F  F  F  F  F  V  Y  F  S  F                       F5
        #            F  *  I  F  F  F  F  F  F  M  F  H  F                        F4

        check = []
        for start, stop, ln, frame in egglib.tools.orf_iter(seq, force_start=True, force_stop=True, forward_only=False):
            check.append((frame, start, stop, ln, egglib.tools.translate(seq[start:stop]) if frame>=0 else egglib.tools.translate(egglib.tools.rc(seq[start:stop]))))
        self.assertEqual(check, [(+2, 7, 37, 9, 'MKKKKKNIK*'), (-2, 3, 30, 8, 'MFFFFFFI*')])

        # longest_orf
        seq = egglib.tools.rc('TCAACATTGCCAATTACCTGAAACCG')
        start, stop, ln, frame = egglib.tools.longest_orf(seq, force_start=False, force_stop=False, forward_only=True)
        self.assertEqual(egglib.tools.translate(seq[start:stop]), 'RFQVIGNV')
        self.assertEqual(ln, 8)
        self.assertEqual(frame, 1)

        # backalign
        cnt = egglib.io.from_fasta_string(string=
'''>@0
ATGGTTACCAAAAACTAA
>@0
TTGGTTACCAAAAACTAA
>@0
ATGGTTACCAAAAACTAA
>@0
TTGGTTACCAAAAACTAA
>@0
TTGGTTACCAAAAACTAA
>@0
GTTACCAAAAACTAA
>@#
WTGGTTACCAAAAAC
>@#
WTGGTTACCAAAAACTAA
''', alphabet=egglib.alphabets.DNA, labels=True, cls=egglib.Container)

        prot = egglib.io.from_fasta_string(string=
'''>@0
MVTKN*-
>@0
LVTKN*-
>@0
MV-TKN-
>@0
LV--TKN
>@0
-LVTKN*
>@0
VTKN---
>@#
XVTKN--
>@#
XVTKN*-
''', alphabet=egglib.alphabets.protein, labels=True, cls=egglib.Align)

        prot_check = egglib.io.from_fasta_string(string=
'''>@0
MVTKN*--
>@0
LVTKN*--
>@0
MV-TKN*-
>@0
LV--TKN*
>@0
-LVTKN*-
>@0
VTKN*---
>@#
XVTKN---
>@#
XVTKN*--
''', alphabet=egglib.alphabets.protein, labels=True, cls=egglib.Align)

        cnt.to_codons()
        aln = egglib.tools.backalign(nucl=cnt, aln=prot, fix_stop=True, allow_alt=True, ignore_names=True)
        self.assertEqual(egglib.tools.translate(aln).fasta(labels=True), prot_check.fasta(labels=True))

        # iter_stops and has_stop
        self.assertEqual(list(egglib.tools.iter_stops(aln, 1)), [ (0, 5), (1, 5), (2, 6), (3, 7), (4, 6), (5, 4), (7, 5) ])
        self.assertEqual(list(egglib.tools.iter_stops(cnt, 1)), [ (0, 5), (1, 5), (2, 5), (3, 5), (4, 5), (5, 4), (7, 5) ])

        test = egglib.io.from_fasta_string(string='''>@0
ATGGTTACCAAAAAC
>@0
TTGGTTACCAAAAAC
>@0
ATGGTTACCAAAAAC
>@0
TTGGTTACCAAAAAC
>@0
TTGGTTACCAAAAAC
>@0
GTTACCAAAAAC
>@#
WTGGTTACCAAAAAC
>@#
WTGGTTACCAAAAACTAA
''', alphabet=egglib.alphabets.DNA, labels=True, cls=egglib.Container)
        test.to_codons()
        self.assertEqual(egglib.tools.has_stop(cnt), True)
        self.assertEqual(egglib.tools.has_stop(aln), True)
        self.assertEqual(egglib.tools.has_stop(test), True)
        del test[-1]
        del test[-1]
        self.assertEqual(egglib.tools.has_stop(test), False)

        # trailing_stops
        self.assertEqual(egglib.tools.trailing_stops(aln), 7)
        self.assertEqual(egglib.tools.trailing_stops(aln, action=2, replacement='???'), 7)
        self.assertEqual(aln.fasta(), '''>
ATGGTTACCAAAAAC???------
>
TTGGTTACCAAAAAC???------
>
ATGGTT---ACCAAAAAC???---
>
TTGGTT------ACCAAAAAC???
>
---TTGGTTACCAAAAAC???---
>
GTTACCAAAAAC???---------
>
WTGGTTACCAAAAAC---------
>
WTGGTTACCAAAAAC???------
''')


    def test_insensitivity(self):
        a = egglib.alphabets.Alphabet('char', 'ACgT', 'NxX', case_insensitive=False)
        self.assertEqual(a.get_alleles(), (['A', 'C', 'g', 'T'], ['N', 'x', 'X']))
        self.assertEqual(a.get_code('A'), 0)
        self.assertEqual(a.get_code('C'), 1)
        self.assertEqual(a.get_code('g'), 2)
        self.assertEqual(a.get_code('T'), 3)
        self.assertEqual(a.get_code('N'), -1)
        self.assertEqual(a.get_code('x'), -2)
        self.assertEqual(a.get_code('X'), -3)
        for x in 'acGtn':
            with self.assertRaises(ValueError):
                a.get_code(x)

        a = egglib.alphabets.Alphabet('char', 'ACgT', 'Nx', case_insensitive=True)
        self.assertEqual(a.get_alleles(), (['A', 'C', 'G', 'T'], ['N', 'X']))
        self.assertEqual(a.get_code('A'), 0)
        self.assertEqual(a.get_code('C'), 1)
        self.assertEqual(a.get_code('G'), 2)
        self.assertEqual(a.get_code('T'), 3)
        self.assertEqual(a.get_code('N'), -1)
        self.assertEqual(a.get_code('X'), -2)
        self.assertEqual(a.get_code('a'), 0)
        self.assertEqual(a.get_code('c'), 1)
        self.assertEqual(a.get_code('g'), 2)
        self.assertEqual(a.get_code('t'), 3)
        self.assertEqual(a.get_code('n'), -1)
        self.assertEqual(a.get_code('x'), -2)

        a = egglib.alphabets.Alphabet('string', ['A', 'aaa', 'Nnn'], ['X', 'Xx'], case_insensitive=True)
        self.assertEqual(a.get_alleles(), (['A', 'AAA', 'NNN'], ['X', 'XX']))
        self.assertEqual(a.get_code('A'), 0)
        self.assertEqual(a.get_code('a'), 0)
        self.assertEqual(a.get_code('aaa'), 1)
        self.assertEqual(a.get_code('AAA'), 1)
        self.assertEqual(a.get_code('AaA'), 1)
        self.assertEqual(a.get_code('aAA'), 1)
        self.assertEqual(a.get_code('NNN'), 2)
        self.assertEqual(a.get_code('nnn'), 2)
        self.assertEqual(a.get_code('nNN'), 2)
        self.assertEqual(a.get_code('nnN'), 2)
        self.assertEqual(a.get_code('X'), -1)
        self.assertEqual(a.get_code('x'), -1)
        self.assertEqual(a.get_code('XX'), -2)
        self.assertEqual(a.get_code('xx'), -2)
        self.assertEqual(a.get_code('xX'), -2)
        self.assertEqual(a.get_code('Xx'), -2)

        a = egglib.alphabets.Alphabet('string', ['A', 'aaa', 'Nnn'], ['X', 'Xx', 'xx'], case_insensitive=False)
        self.assertEqual(a.get_alleles(), (['A', 'aaa', 'Nnn'], ['X', 'Xx', 'xx']))
        self.assertEqual(a.get_code('A'), 0)
        self.assertEqual(a.get_code('aaa'), 1)
        self.assertEqual(a.get_code('Nnn'), 2)
        self.assertEqual(a.get_code('X'), -1)
        self.assertEqual(a.get_code('Xx'), -2)
        self.assertEqual(a.get_code('xx'), -3)

        for x in ['a', 'AAA', 'AaA', 'aAA', 'NNN', 'nnn', 'nNN', 'nnN', 'x', 'XX', 'xX']:
            with self.assertRaises(ValueError):
                a.get_code(x)

    def test_genepop_alphabet(self):
        expl, miss = egglib.alphabets.genepop.get_alleles()
        self.assertTupleEqual(expl, (1, 1000))
        self.assertTupleEqual(miss, (0, 1))
