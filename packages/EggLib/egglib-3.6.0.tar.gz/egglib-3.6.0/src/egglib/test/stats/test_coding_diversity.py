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

class CodingDiversity_test(unittest.TestCase):
    def test_CodingDiversity_T(self):
        cdiv = egglib.stats.CodingDiversity()
        self.assertEqual(str(type(cdiv)), "<class 'egglib.stats._coding_diversity.CodingDiversity'>")

    def test_process_T(self):
        cdiv= egglib.stats.CodingDiversity()
        frame_aln = egglib.tools.ReadingFrame([[0, 698, 3], [1264, 1318, None], [1403, 1513, None], [3431, 3663, None], [4267, 4474, None], [5733, 5792, None], [5882, 6039, None]])
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        aln.to_codons(frame=frame_aln)
        v_a=cdiv.num_codons_tot
        cdiv.process(aln, struct=egglib.struct_from_labels(aln), max_missing=0)
        v_b=cdiv.num_codons_tot
        self.assertTrue(v_b>v_a)
        self.assertEqual(str(type(cdiv)), "<class 'egglib.stats._coding_diversity.CodingDiversity'>")

    def test_process_E(self):
        cdiv= egglib.stats.CodingDiversity()
        frame_aln = egglib.tools.ReadingFrame([[0, 698, 3], [1264, 1318, None], [1403, 1513, None], [3431, 3663, None], [4267, 4474, None], [5733, 5792, None], [5882, 6039, None]])
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        aln.to_codons(frame=frame_aln)
        with self.assertRaises(ValueError):
            cdiv.process(aln, struct=egglib.struct_from_labels(aln), max_missing=0, code=1000)
        cdiv.process(aln, max_missing=0, code=1)

    def test_num_codons_tot_T(self):
        cdiv= egglib.stats.CodingDiversity()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([[0, 6039]])
        aln.to_codons(frame)
        cdiv.process(aln, struct=egglib.struct_from_labels(aln), max_missing=0)
        nct=cdiv.num_codons_tot
        self.assertEqual(nct, 2013)

    def test_num_codons_eff_T(self):
        cdiv= egglib.stats.CodingDiversity()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([[0, 6039]])
        aln.to_codons(frame)
        cdiv.process(aln, struct=egglib.struct_from_labels(aln), max_missing=0)
        nce=cdiv.num_codons_eff
        self.assertEqual(nce, 472)

    def test_num_codons_stop_T(self):
        cdiv= egglib.stats.CodingDiversity()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([[0, 698, 3], [1264, 1318, None], [1403, 1513, None], [3431, 3663, None], [4267, 4474, None], [5733, 5792, None], [5882, 6039, None]])
        aln.to_codons(frame=frame)
        cdiv.process(aln, struct=egglib.struct_from_labels(aln), max_missing=0)
        ncs=cdiv.num_codons_stop
        self.assertEqual(ncs, 14)

    def test_num_sites_NS_T(self):
        cdiv= egglib.stats.CodingDiversity()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([[0, 6039]])
        aln.to_codons(frame)
        cdiv.process(aln, struct=egglib.struct_from_labels(aln), max_missing=0)
        nsN=cdiv.num_sites_NS
        self.assertEqual(round(nsN,8),1133.14327485)

    def test_num_sites_S_T(self):
        cdiv= egglib.stats.CodingDiversity()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([[0, 6039]])
        aln.to_codons(frame)
        cdiv.process(aln, struct=egglib.struct_from_labels(aln), max_missing=0)
        nsS=cdiv.num_sites_S
        self.assertEqual(round(nsS,9),282.856725146)

    def test_num_pol_single_T(self):
        cdiv= egglib.stats.CodingDiversity()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([[0, 6039]])
        aln.to_codons(frame)
        cdiv.process(aln, struct=egglib.struct_from_labels(aln), max_missing=0)
        nps=cdiv.num_pol_single
        self.assertEqual(nps, 37)

    def test_num_pol_multi_T(self):
        cdiv= egglib.stats.CodingDiversity()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([[0, 698, 3], [1264, 1318, None], [1403, 1513, None], [3431, 3663, None], [4267, 4474, None], [5733, 5792, None], [5882, 6039, None]])
        aln.to_codons(frame=frame)
        cdiv.process(aln, struct=egglib.struct_from_labels(aln), max_missing=999)
        npm=cdiv.num_multiple_hits
        self.assertEqual(npm, 2)

    def test_num_pol_NS_T(self):
        cdiv= egglib.stats.CodingDiversity()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([[0, 698, 3], [1264, 1318, None], [1403, 1513, None], [3431, 3663, None], [4267, 4474, None], [5733, 5792, None], [5882, 6039, None]])
        aln.to_codons(frame=frame)
        cdiv.process(aln, struct=egglib.struct_from_labels(aln), max_missing=999)
        npNS=cdiv.num_pol_NS
        self.assertEqual(npNS,5)

    def test_num_pol_S_T(self):
        cdiv= egglib.stats.CodingDiversity()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([[0, 698, 3], [1264, 1318, None], [1403, 1513, None], [3431, 3663, None], [4267, 4474, None], [5733, 5792, None], [5882, 6039, None]])
        aln.to_codons(frame=frame)
        cdiv.process(aln, struct=egglib.struct_from_labels(aln), max_missing=999)
        npS=cdiv.num_pol_S
        self.assertEqual(npS, 16)

    def test_iter_S_T(self):
        cdiv= egglib.stats.CodingDiversity()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([[0, 698, 3], [1264, 1318, None], [1403, 1513, None], [3431, 3663, None], [4267, 4474, None], [5733, 5792, None], [5882, 6039, None]])
        aln.to_codons(frame=frame)
        cdiv.process(aln, struct=egglib.struct_from_labels(aln), max_missing=999)
        self.assertIsInstance(cdiv.sites_S, list)
        self.assertEqual(len(cdiv.sites_S), 16)

    def test_iter_NS_T(self):
        cdiv= egglib.stats.CodingDiversity()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        frame = egglib.tools.ReadingFrame([[0, 698, 3], [1264, 1318, None], [1403, 1513, None], [3431, 3663, None], [4267, 4474, None], [5733, 5792, None], [5882, 6039, None]])
        aln.to_codons(frame=frame)
        cdiv.process(aln, struct=egglib.struct_from_labels(aln), max_missing=999)
        self.assertIsInstance(cdiv.sites_NS, list)
        self.assertEqual(len(cdiv.sites_NS), 5)

    def test_codon_diversity(self):
        aln = egglib.Align.create([
        # SYN              +                    +
        # NON-SYN                 +      +       
            ('', ['ATG', 'ACG', 'TAC', 'GAT', 'CCC', 'TAA']),
            ('', ['ATG', 'ACA', 'TAC', 'GTT', 'CCC', 'TAA']),
            ('', ['ATG', 'ACA', 'TCC', 'GTT', 'CCC', 'TAA']),
            ('', ['AT?', 'ACA', 'TCC', 'GAT', 'CCA', 'TAA'])], egglib.alphabets.codons)

        cd = egglib.stats.CodingDiversity(aln)
        cs = egglib.stats.ComputeStats()
        cs.add_stats('Ki', 'D', 'S')
        statsS = cs.process_sites(cd.sites_S)
        statsNS = cs.process_sites(cd.sites_NS)
        self.assertEqual(statsS['S'], 2)
        self.assertEqual(statsNS['S'], 2)
        self.assertEqual(statsS['Ki'], 3)
        self.assertEqual(statsNS['Ki'], 4)

    def test_raise_stop(self):
        aln = egglib.Align.create([
        # SYN              +                    +
        # NON-SYN                 +      +       
        # STOP                                         +
            ('', ['ATG', 'ACG', 'TAC', 'GAT', 'CCC', 'TCA']),
            ('', ['ATG', 'ACA', 'TAC', 'GTT', 'CCC', 'TCA']),
            ('', ['ATG', 'ACA', 'TCC', 'GTT', 'CCC', 'TCA']),
            ('', ['AT?', 'ACA', 'TCC', 'GAT', 'CCA', 'TAA'])], egglib.alphabets.codons)

        with self.assertRaises(ValueError):
            cd = egglib.stats.CodingDiversity(aln, raise_stop=True, skipstop=True)

        with self.assertRaises(ValueError):
            cd = egglib.stats.CodingDiversity(aln, raise_stop=True, skipstop=False)

        cd = egglib.stats.CodingDiversity(aln, skipstop=True)
        self.assertListEqual(cd.positions_S, [1, 4])
        self.assertListEqual(cd.positions_NS, [2, 3])

        cd = egglib.stats.CodingDiversity(aln, skipstop=False)
        self.assertListEqual(cd.positions_S, [1, 4])
        self.assertListEqual(cd.positions_NS, [2, 3, 5])
