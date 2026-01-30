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

import os, egglib, sys, unittest, random, re, gc, time
import collections

class Simulator_test(unittest.TestCase):
    #test on the creation of an object of the class "Simulator"
    def test_Simulator_T(self):
        sim = egglib.coalesce.Simulator(num_pop=4)
        self.assertIsInstance(sim,egglib.coalesce._simulator.Simulator)

    def test_Simulator_E(self):
        with self.assertRaises(TypeError):
            sim =egglib.coalesce.Simulator()

    #Test on the method "params" of the class "Simulator"
    def test_params_T(self):
        sim = egglib.coalesce.Simulator(num_pop=4)
        self.assertIsInstance(sim.params, egglib.coalesce._param_helpers.ParamDict)

    #Test on the method "simul" of the class "Simulator"
    def test_simul_T(self):
        sim = egglib.coalesce.Simulator(2, migr=0.1, theta=2.0, num_chrom=(40,40))
        aln=sim.simul()
        self.assertIsInstance(aln, egglib._interface.Align)
    
    def test_simul_E(self):
        sim = egglib.coalesce.Simulator(2)
        with self.assertRaises(ValueError):
            aln=sim.simul()

    #Test on the method "iter_simul" of the class "Simulator"
    def test_iter_simul_T(self):
        sim = egglib.coalesce.Simulator(2, migr=0.1, theta=2.0, num_chrom=(40,40))
        self.assertIsInstance(sim.iter_simul(10000), collections.abc.Iterable)


    def test_iter_simul_T2(self):
        egglib.random.set_seed(304059594)
        sim = egglib.coalesce.Simulator(2, migr=0.1, theta=2.0, num_chrom=(40,40))
        pi=[4.141455696202532,17.020886075949363,10.81455696202532,12.924683544303793,33.9405063291139,20.88607594936709,16.693354430379742,3.620569620253164,30.46993670886073,15.046835443037972]
        thetaw=[4.845568424245371,9.287339479803627,5.8550618459631565,6.8645552676809425,15.949996063141013,11.104427638895642,8.681643426772956,3.634176318184028,14.334806588392556,7.470251320711614]
        d=[-0.4431286862903224,2.6965022453054894,2.63744693521985,2.7910450471752473,3.7636271400744246,2.8855818820313806,2.9739780411465353,-0.010992404265106911,3.737735546441633,3.230129104396626]
        cs = egglib.stats.ComputeStats()
        cs.configure()
        cs.add_stats('Pi')
        cs.add_stats('thetaW')
        cs.add_stats('D')
        for items in sim.iter_simul(10, cs=cs):
            self.assertIn(items['Pi'], pi)
            self.assertIn(items['thetaW'], thetaw)
            self.assertIn(items['D'], d)

    #test on the creation of an object of the class "Align" with the class "Simulator"
    def test_sim_aln_T(self):
        coal = egglib.coalesce.Simulator(1, num_chrom=(20,), migr=0, theta=5.0)
        aln = coal.align
        self.assertIsInstance(aln, egglib.Align)

    def check(self, aln, ns, ls):
        self.assertEqual(aln.ns, ns)
        self.assertEqual(aln.ls, ls)

    def test_align_num_samples_outgroup(self):
        coal = egglib.coalesce.Simulator(1, num_chrom=(20,), num_mut=10)
        self.check(coal.simul(), 20, 10)
        self.check(coal.align, 20, 10)
        for aln in coal.iter_simul(1):
            self.check(aln, 20, 10)
        cs = egglib.stats.ComputeStats()
        cs.add_stats('nseff', 'lseff')
        for stats in coal.iter_simul(1, cs=cs):
            self.assertEqual(stats['nseff'], 20)
            self.assertEqual(stats['lseff'], 10)
            self.check(coal.align, 20, 10)

        coal.params.add_event('sample', 0.1, idx=0, num_chrom=20, num_indiv=0, label='1')
        coal.params.add_event('sample', 0.2, idx=0, num_chrom=12, num_indiv=0, label='64')
        self.check(coal.simul(), 52, 10)
        self.check(coal.align, 52, 10)
        for aln in coal.iter_simul(1):
            self.check(aln, 52, 10)
            self.check(coal.align, 52, 10)
        for stats in coal.iter_simul(1, cs=cs):
            self.assertEqual(stats['nseff'], 52)
            self.assertEqual(stats['lseff'], 10)
            self.check(coal.align, 52, 10)

        coal = egglib.coalesce.Simulator(2, num_chrom=(20,10), migr=1, num_mut=7)
        self.check(coal.simul(), 30, 7)
        self.check(coal.align, 30, 7)

    def test_alphabets(self): # just executing some code, not actually testing anything
        coal = egglib.coalesce.Simulator(1, theta=2, num_chrom=[20])
        aln = coal.simul()
        aln.alphabet.name
        for i in aln:
            i.sequence[:]
        aln.fasta(alphabet=egglib.alphabets.DNA)

        coal.params['mut_model'] = 'IAM'
        aln = coal.simul()
        aln.alphabet.name
        for i in aln:
            i.sequence[:]

        coal.params['mut_model'] = 'TPM'
        aln = coal.simul()
        aln.alphabet.name
        for i in aln:
            i.sequence[:]
