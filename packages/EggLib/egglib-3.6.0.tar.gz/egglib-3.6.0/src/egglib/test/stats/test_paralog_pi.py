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

class Paralog_pi_test(unittest.TestCase):
    def test_ParalogPi_T(self):
        prlpi=egglib.stats.ParalogPi()
        self.assertIsInstance(prlpi, egglib.stats.ParalogPi)
        
    def test_setup_T(self):
        prlpi=egglib.stats.ParalogPi()
        ns = 15
        sim = egglib.coalesce.Simulator(4, num_indiv=[ns]*4, migr=1.0, theta=8.0)
        paralogs_aln = sim.simul()
        pstruct = egglib.struct_from_labels(paralogs_aln, lvl_pop=0)
        istruct = {}
        for i in range(ns*2):
                istruct[str(i)] = dict([(str(i+j*ns*2), (i+j*ns*2,)) for j in range(4)])
        istruct = egglib.struct_from_dict({None: istruct}, None)
        prlpi.setup(pstruct, istruct)
        self.assertEqual(prlpi.num_sites(),0)
        self.assertEqual(pstruct.req_ns,120)
        self.assertEqual(istruct.req_ns,120)
        self.assertIsInstance(prlpi, egglib.stats.ParalogPi)


    def test_process_align_T(self):
        prlpi=egglib.stats.ParalogPi()
        ns = 15
        sim = egglib.coalesce.Simulator(4, num_indiv=[ns]*4, migr=1.0, theta=8.0)
        paralogs_aln = sim.simul()
        pstruct = egglib.struct_from_labels(paralogs_aln, lvl_pop=0)
        istruct = {}
        for i in range(ns*2):
                istruct[str(i)] = dict([(str(i+j*ns*2), (i+j*ns*2,)) for j in range(4)])
        istruct = egglib.struct_from_dict({None: istruct}, None)
        prlpi.setup(pstruct, istruct)
        num_sites_b=prlpi.num_sites(0)
        self.assertIsInstance(prlpi, egglib.stats.ParalogPi)
        prlpi.process_align(paralogs_aln)
        num_sites_a=prlpi.num_sites(0)
        self.assertTrue(num_sites_a>num_sites_b)
    
    
    def test_process_align_E(self):
        prlpi=egglib.stats.ParalogPi()
        ns = 15
        sim = egglib.coalesce.Simulator(4, num_indiv=[ns]*4, migr=1.0, theta=8.0)
        paralogs_aln = sim.simul()
        pstruct = egglib.struct_from_labels(paralogs_aln, lvl_pop=0)
        aln = egglib.io.from_fasta(str(path / '125_seqs_300_300_bp.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        istruct = {}
        for i in range(ns*2):
                istruct[str(i)] = dict([(str(i+j*ns*2), (i+j*ns*2,)) for j in range(4)])
        istruct = egglib.struct_from_dict({None: istruct}, None)
        prlpi.setup(pstruct, istruct)
        with self.assertRaises(ValueError):
            prlpi.process_align(aln)


    def test_process_site_T(self):
        prlpi=egglib.stats.ParalogPi()
        ns = 50
        sim = egglib.coalesce.Simulator(4, num_indiv=[ns]*4, migr=1.0, theta=8.0)
        paralogs_aln = sim.simul()
        pstruct = egglib.struct_from_labels(paralogs_aln, lvl_pop=0)
        istruct = {}
        for i in range(ns*2):
                istruct[str(i)] = dict([(str(i+j*ns*2), (i+j*ns*2,)) for j in range(4)])
        istruct = egglib.struct_from_dict({None: istruct}, None)
        prlpi.setup(pstruct, istruct)
        num_sites_b=prlpi.num_sites(0)
        self.assertIsInstance(prlpi, egglib.stats.ParalogPi)

        num_sites_a=prlpi.num_sites(0)
        aln=egglib.io.from_fasta(str(path / '50_seqs_100_100_bp.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        sites_aln=egglib.Site()
        for i in range(aln.ls): sites_aln.from_align(aln, i)
        sites_aln.ns
        sites_aln.num_missing
        sites_aln.as_list()

        #prlpi.process_site(sites_aln)
        #sites_aln.process_align(aln,10)
        #num_sites_b=prlpi.num_sites(0)
        #prlpi.process_site(sites_aln)

        #num_sites_a=prlpi.num_sites(0)
        #self.assertTrue(num_sites_a>num_sites_b)
    
    def test_process_site_E(self):
        prlpi=egglib.stats.ParalogPi()
        ns = 15
        sim = egglib.coalesce.Simulator(4, num_indiv=[ns]*4, migr=1.0, theta=8.0)
        paralogs_aln = sim.simul()
        pstruct = egglib.struct_from_labels(paralogs_aln, lvl_pop=0)
        istruct = {}
        for i in range(ns*2):
                istruct[str(i)] = dict([(str(i+j*ns*2), (i+j*ns*2,)) for j in range(4)])
        istruct = egglib.struct_from_dict({None: istruct}, None)
        prlpi.setup(pstruct, istruct)
        num_sites_b=prlpi.num_sites(0)
        self.assertIsInstance(prlpi, egglib.stats.ParalogPi)

        num_sites_a=prlpi.num_sites(0)
        aln=egglib.io.from_fasta(str(path / '125_seqs_300_300_bp.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        sites_aln=egglib.Site()
        for i in range(aln.ns): sites_aln.from_align(aln, i)
        with self.assertRaises(ValueError):
            prlpi.process_site(sites_aln)
