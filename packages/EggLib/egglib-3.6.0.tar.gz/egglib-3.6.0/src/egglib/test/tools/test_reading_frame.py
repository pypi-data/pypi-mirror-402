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

import egglib, unittest, collections

class ReadingFrame_test(unittest.TestCase):
    def test_readingframe_T(self):
        RF=egglib.tools.ReadingFrame()
        self.assertEqual(str(type(RF)),"<class 'egglib.tools._reading_frame.ReadingFrame'>")

    def test_process_T(self):
        RF=egglib.tools.ReadingFrame()	
        RF.process([(10, 24), (55, 144), (255, 315), (974, 1222, 3)])
        self.assertEqual(str(type(RF)),"<class 'egglib.tools._reading_frame.ReadingFrame'>")
        self.assertEqual(RF.num_exons,4)

    def test_process_E(self):
        RF=egglib.tools.ReadingFrame()
        with self.assertRaises(ValueError):
            RF.process([(974, 1222, 17)])
        with self.assertRaises(ValueError):
            RF.process([(-10, 24)])
        with self.assertRaises(ValueError):
            RF.process([(24, 24)])
        with self.assertRaises(ValueError):
            RF.process([(24, 4)])
    
    def test_num_needed_bases_T(self):
        RF=egglib.tools.ReadingFrame()
        RF.process([(10, 24), (55, 144), (255, 315), (974, 1222, 3)])
        self.assertEqual(RF.num_needed_bases, 1222)

    def test_num_tot_bases_T(self):
        RF=egglib.tools.ReadingFrame()	
        RF.process([(10, 24), (55, 144), (255, 315), (974, 1222, 3)])
        self.assertEqual(RF.num_tot_bases,1212)

    def test_num_exon_bases_T(self):
        RF=egglib.tools.ReadingFrame()	
        RF.process([(10, 24), (55, 144), (255, 315), (974, 1222, 3)])
        self.assertEqual(RF.num_exon_bases,411)

    def test_num_exons_T(self):
        RF=egglib.tools.ReadingFrame()	
        RF.process([(10, 24), (55, 144), (255, 315), (974, 1222, 3)])
        self.assertEqual(RF.num_exons,4)

    def test_num_full_codons_T(self):
        RF=egglib.tools.ReadingFrame()
        RF.process([(10, 24), (55, 144), (255, 315), (974, 1222, 3)])
        self.assertEqual(RF.num_codons, 136)
        RF.process([(10, 24), (55, 144), (255, 315), (974, 1222, 3)], keep_truncated=True)
        self.assertEqual(RF.num_codons, 139)

    def test_exon_index_T(self):
        RF=egglib.tools.ReadingFrame()	
        RF.process([(10, 24), (55, 144), (255, 315), (974, 1222, 3)])
        self.assertEqual(RF.exon_index(1150),3)

    def test_codon_index_T(self):
        RF=egglib.tools.ReadingFrame()
        RF.process([(10, 24), (55, 144), (255, 315), (974, 1222, 3)])
        self.assertEqual(RF.codon_index(1150), 112)

    def test_codon_position_T(self):
        RF=egglib.tools.ReadingFrame()	
        RF.process([(10, 24), (55, 144), (255, 315), (974, 1222, 3)])
        self.assertEqual(RF.codon_position(1150),1)

    def test_codon_bases_T(self):
        RF=egglib.tools.ReadingFrame()	
        RF.process([(10, 24), (55, 144), (255, 315), (974, 1222, 3)])
        self.assertEqual(RF.codon_bases(1),(13, 14, 15))

    def test_codon_bases_E(self):
        RF=egglib.tools.ReadingFrame()	
        RF.process([(10, 24), (55, 144), (255, 315), (974, 1222, 3)])
        self.assertEqual(RF.codon_bases(4000),None)

    def test_iter_exon_bounds_T(self):
        RF=egglib.tools.ReadingFrame()	
        RF.process([(10, 24), (55, 144), (255, 315), (974, 1222, 3)])
        l_ex=[10,55,255,974,24,144,315,1222]
        i=0
        self.assertIsInstance(RF.iter_exon_bounds(), collections.abc.Iterable)
        for a, b in RF.iter_exon_bounds(): 
            self.assertIn(a, l_ex)
            self.assertIn(a, l_ex)
            i=+1

    def test_iter_codons_T(self):
        RF=egglib.tools.ReadingFrame()	
        RF.process([(10, 24), (55, 144), (255, 315), (974, 1222, 3)])
        self.assertIsInstance(RF.iter_codons(), collections.abc.Iterable)
