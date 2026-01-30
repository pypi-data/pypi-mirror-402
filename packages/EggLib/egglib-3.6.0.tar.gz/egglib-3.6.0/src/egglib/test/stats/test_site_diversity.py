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

import egglib, unittest

class SiteDiversity_test(unittest.TestCase):
    def test_return_value(self): # not all cases covered
        alph = egglib.alphabets.Alphabet('int', [0, 1], [-1])
        site = egglib.Site()
        frq = egglib.Freq()
        sd = egglib._eggwrapper.SiteDiversity()

        site.from_list([-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1], alphabet=alph)
        frq.from_site(site)
        self.assertEqual(sd.process(frq._obj), 1)
        self.assertEqual(sd.ns(), 0)

        site.from_list([0,1,0,0,1,1,0,0,0,1,1,1,0,0,0,1,1,1,1,0,1,1,0,1], alphabet=alph)
        frq.from_site(site)
        self.assertEqual(sd.process(frq._obj), 1+2+4+512+1024)
        self.assertEqual(sd.ns(), 24)

        site.from_list([0,1,0,0,-1,-1,0,-1,-1,1,1,1,0,0,-1,1,1,1,1,0,-1,1,0,1], alphabet=alph)
        frq.from_site(site)
        self.assertEqual(sd.process(frq._obj), 1+2+4+512+1024)
        self.assertEqual(sd.ns(), 18)

        site.from_list([0,-1,0,0,-1,-1,0,-1,-1,-1,-1,-1,0,0,-1,-1,-1,-1,-1,0,-1,-1,0,-1], alphabet=alph)
        frq.from_site(site)
        self.assertEqual(sd.process(frq._obj), 1+2+4+512)
        self.assertEqual(sd.ns(), 8)



    def test_Fis(self):
        # simulation model
        NR = 200
        struct = [55, 32, 65, 58]
        sim = egglib.coalesce.Simulator(len(struct), num_indiv=struct,
                                        theta=5, num_sites=1, mut_model='SMM')
        sim.params['events'].add(T=0.2, cat='merge', src=1, dst=0)
        sim.params['events'].add(T=0.2, cat='merge', src=2, dst=0)
        sim.params['events'].add(T=0.2, cat='merge', src=3, dst=0)

        # stats calculator
        cs = egglib.stats.ComputeStats(struct=sim.params.mk_structure(), multi_hits=True)
        cs.add_stats('Fis', 'Ho', 'He')
        cs_tot = egglib.stats.ComputeStats(struct=sim.params.mk_structure(), multi_hits=True, multi=True)
        cs_tot.add_stats('Fis', 'Ho', 'He')

        # simulate datasets and compute Fis with EggLib
        alph = egglib.Alphabet('range', (-999999, None), (-1000000, -999999))
        He_tot = 0.0
        Ho_tot = 0.0
        for aln in sim.iter_simul(NR):
            aln = egglib.Align.create(list(aln), alphabet=alph)
            aln.random_missing(0.05, missing=-1000000)
            stats = cs.process_align(aln, max_missing=1)
            cs_tot.process_align(aln, max_missing=1)
            Fis = stats['Fis']
            Ho = stats['Ho']
            He = stats['He']

            # compute Fis manually
            alleles = {}
            heter = 0
            nind = 0
            for indiv in range(sum(struct)):
                a = aln[indiv*2].sequence[0]
                b = aln[indiv*2+1].sequence[0]
                if alph.get_code(a) >= 0:
                    if a not in alleles: alleles[a] = 0
                    alleles[a] += 1
                if alph.get_code(b) >= 0:
                    if b not in alleles: alleles[b] = 0
                    alleles[b] += 1
                if alph.get_code(a) >= 0 and alph.get_code(b) >= 0:
                    nind += 1
                    if a != b:
                        heter += 1

            He_check = 1.0
            nseff = sum(alleles.values())
            if nseff < 2: continue
            for a in alleles:
                He_check -= (alleles[a]/nseff) ** 2
            He_check *= nseff / (nseff - 1)
            Ho_check = heter / nind
            Fis_check = 1 - Ho_check / He_check
            He_tot += He_check
            Ho_tot += Ho_check

            self.assertAlmostEqual(Fis, Fis_check, places=6)
            self.assertAlmostEqual(He, He_check, places=6)
            self.assertAlmostEqual(Ho, Ho_check, places=6)

        stats = cs_tot.results()
        Fis_tot = 1 - Ho_tot / He_tot
        self.assertAlmostEqual(stats['He'], He_tot/NR, places=6)
        self.assertAlmostEqual(stats['Ho'], Ho_tot/NR, places=6)
        self.assertAlmostEqual(stats['Fis'], Fis_tot, places=6)
