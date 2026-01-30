"""
    Copyright 2025-2026 Thomas Coudoux, Stéphane De Mita, Mathieu Siol

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

import egglib, unittest, re, random, pathlib
path = pathlib.Path(__file__).parent / '..' / 'data'
SSR = egglib.alphabets.Alphabet('range', (1, 999), (0, 1))
INT = egglib.alphabets.Alphabet('range', (0, 31), (-1, 0))

def get_genepop(fname):
    f = open(str(path / fname))
    title = f.readline()
    n = 0
    while True:
        line = f.readline()
        if line.strip().upper() == 'POP':
            break
        if line == '': raise ValueError('not GenePop data: ' + fname)
        # locus name ignored
        n += len(line.split(','))
    sites = [[] for i in range(n)]
    ns = []
    pl = set()
    while True:
        ns.append(0)
        while True:
            line = f.readline()
            if line == '' or line.strip().upper() == 'POP':
                break
            genotypes = line.split(',')[1].split()
            for i, idv in enumerate(genotypes):
                if len(idv) in (2,3): pl.add(1)
                else: pl.add(2)
                if len(idv) == 4: item = list(map(int, (idv[:2], idv[2:])))
                elif len(idv) == 6: item = list(map(int, (idv[:3], idv[3:])))
                elif len(idv) in (2,3): item = (int(idv),)
                else: raise ValueError('invalid genotype: {0}'.format(idv))
                item = [v if v != 0 else 0 for v in item]
                sites[i].extend(item)
            ns[-1] += 1
        if line == '':
            break
    assert len(pl) == 1
    pl = pl.pop()
    return [egglib.site_from_list(site, SSR) for site in sites], ns, pl

class ComputeStats_test(unittest.TestCase):
    def test_ComputeStats_T(self):
        CS = egglib.stats.ComputeStats()
        self.assertIsInstance(CS, egglib.stats.ComputeStats)

    def test_list_stats_T(self):
        CS = egglib.stats.ComputeStats()
        self.assertIsNotNone(CS.list_stats())

    def test_configure_T(self):
        CS = egglib.stats.ComputeStats()
        CS.configure()

    def test_configure_E(self):
        CS = egglib.stats.ComputeStats()
        CS.configure()
        with self.assertRaises(ValueError):
            CS.configure(LD_min_n=-10)
        with self.assertRaises(ValueError):
            CS.configure(LD_max_maj=-10)
        with self.assertRaises(ValueError):
            CS.configure(LD_max_maj=10)
        with self.assertRaises(ValueError):
            CS.configure(LD_multiallelic=-10)
        with self.assertRaises(ValueError):
            CS.configure(LD_multiallelic=460)
        with self.assertRaises(ValueError):
            CS.configure(LD_min_freq=-10)

    def test_add_stats_T(self):
        CS = egglib.stats.ComputeStats()
        CS.add_stats('Atot', 'Aing', 'R', 'He', 'Dj', 'FstWC', 'V')
        self.assertEqual(len(CS.results()),7)

    def test_add_stats_E(self):
        CS = egglib.stats.ComputeStats()
        with self.assertRaises(ValueError):
            CS.add_stats('FAIL')
        
    def test_all_stats_T(self):
        CS = egglib.stats.ComputeStats()
        CS.all_stats()
        self.assertEqual(len(CS.results()), len(CS.list_stats()))

    def test_clear_stats_T(self):
        CS = egglib.stats.ComputeStats()
        CS.add_stats('Atot', 'Aing', 'R', 'He', 'Dj', 'FstWC', 'V')
        n_b=len(CS.results())
        CS.clear_stats()
        n_a=len(CS.results())
        self.assertTrue(n_b>n_a)

    def test_reset_T(self):
        CS = egglib.stats.ComputeStats()
        CS.add_stats('Atot', 'Aing', 'R', 'He', 'Dj', 'FstWC')
        site = egglib.Site()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        real_struct = egglib.struct_from_labels(aln, lvl_pop=0, lvl_indiv=None, lvl_clust=None)
        CS.configure(multi=True)
        site.from_align(aln, 2213)
        for i in range(aln.ls):
            site.from_align(aln, i)
            frq = egglib.freq_from_site(site, struct=real_struct)
            CS.process_freq(frq)
        stats_r=CS.results()
        for key in sorted(stats_r):self.assertIsNotNone(stats_r[key])  
        CS.reset()
        stats_r=CS.results()
        for key in sorted(stats_r):self.assertIsNone(stats_r[key])

    def test_process_freq_T(self):
        CS = egglib.stats.ComputeStats()
        CS.add_stats('Atot', 'Aing', 'R', 'He', 'Dj', 'FstWC')
        site = egglib.Site()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        real_struct = egglib.struct_from_labels(aln, lvl_pop=0, lvl_indiv=None, lvl_clust=None)
        site.from_align(aln, 2213)
        frq = egglib.freq_from_site(site, struct=real_struct)
        frq_results=CS.process_freq(frq)
        self.assertIsInstance(frq_results, dict)
        CS.configure(multi=True)
        for key in sorted(frq_results):self.assertIsNotNone(frq_results[key])  
        frq_results_2=CS.process_freq(frq)
        self.assertIsNone(frq_results_2)

    def test_process_site_T(self):
        CS = egglib.stats.ComputeStats()
        CS.add_stats('Atot', 'Aing', 'R', 'He')
        site = egglib.Site()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        real_struct = egglib.struct_from_labels(aln, lvl_pop=0, lvl_indiv=None, lvl_clust=None)
        CS.configure(struct=real_struct)
        site.from_align(aln, 2213)
        ste_results=CS.process_site(site)
        self.assertIsInstance(ste_results,dict)
        CS.configure(multi=True)
        for key in sorted(ste_results):self.assertIsNotNone(ste_results[key])  
        ste_results=CS.process_site(site)
        self.assertIsNone(ste_results)

    def test_process_site_E(self):
        CS = egglib.stats.ComputeStats()
        CS.add_stats('Atot', 'Aing', 'R', 'He', 'FstH')
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        struct = egglib.struct_from_labels(aln, lvl_pop=None, lvl_indiv=None, lvl_clust=None)
        sub = aln.subset(range(10))
        site = egglib.Site()
        site.from_align(sub, 2213)
        CS.configure(multi=True, struct=struct)
        with self.assertRaises(ValueError):
            CS.process_site(site)

    def test_process_sites_T(self):
        CS = egglib.stats.ComputeStats()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        ssr = egglib.coalesce.Simulator(1, num_chrom=[40], num_sites=1, mut_model='TPM', theta=5.0)
        sites = [egglib.site_from_align(aln, 0) for aln in ssr.iter_simul(100)]
        CS.add_stats('Atot', 'Aing', 'R', 'He')
        results_sites=CS.process_sites(sites)
        self.assertIsInstance(results_sites,dict)
        for key in sorted(results_sites):self.assertIsNotNone(results_sites[key])  
        CS.configure(multi=True)
        results_sites=CS.process_sites(sites)
        self.assertIsNone(results_sites)

        coal = egglib.coalesce.Simulator(2, num_chrom=[46, 28], theta=2.5, migr=0.2)
        aln1 = coal.simul()
        coal.params['num_chrom'] = 44, 32
        aln2 = coal.simul()
        coal.params['num_chrom'] = 52, 30
        aln3 = coal.simul()

        cs = egglib.stats.ComputeStats()
        cs.add_stats('S', 'D', 'thetaW', 'Pi', 'FstWC', 'Snn')
        stats1 = cs.process_align(aln1)
        stats2 = cs.process_align(aln2)
        stats3 = cs.process_align(aln3)

        sites1 = [egglib.site_from_align(aln1, i) for i in range(aln1.ls)]
        sites2 = [egglib.site_from_align(aln2, i) for i in range(aln2.ls)]
        sites3 = [egglib.site_from_align(aln3, i) for i in range(aln3.ls)]
        self.assertEqual(cs.process_sites(sites1), stats1)
        self.assertEqual(cs.process_sites(sites2), stats2)
        self.assertEqual(cs.process_sites(sites3), stats3)

    def test_process_sites_E(self):
        CS = egglib.stats.ComputeStats()
        CS.add_stats('Atot', 'Aing', 'R', 'He', 'FstH')
        site = egglib.Site()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        real_struct = egglib.struct_from_labels(aln, lvl_pop=None, lvl_indiv=None, lvl_clust=None)
        ssr = egglib.coalesce.Simulator(1, num_chrom=[20], num_sites=1, mut_model='TPM', theta=5.0)
        sites = [egglib.site_from_align(aln, 0) for aln in ssr.iter_simul(99)]
        pos=list(range(0, 100))
        CS.configure(multi=True, struct=real_struct)
        with self.assertRaises(ValueError): #number of positions must match the number of sites	
            CS.process_sites(sites,positions=pos)

    def test_process_align_T(self):
        CS = egglib.stats.ComputeStats()
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        CS.add_stats('Atot', 'Aing', 'R', 'He')
        results_align=CS.process_align(aln)
        self.assertIsInstance(results_align,dict)
        for key in sorted(results_align):self.assertIsNotNone(results_align[key])  
        CS.configure(multi=True)
        results_align=CS.process_align(aln)
        self.assertIsNone(results_align)
        with self.assertRaises(ValueError):
            CS.process_align(aln, max_missing=-10)
        with self.assertRaises(ValueError):
            CS.process_align(aln, max_missing=10)

    def test_process_align_E(self):
        CS = egglib.stats.ComputeStats()
        aln = egglib.io.from_fasta(str(path / 'c_file_1.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        CS.add_stats('Atot', 'Aing', 'R', 'He')
        with self.assertRaises(ValueError):
            pos=list(range(0, 100))
            CS.process_align(aln, positions=pos)

        aln_e= egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        real_struct = egglib.struct_from_labels(aln_e, lvl_pop=None, lvl_indiv=None, lvl_clust=None)
        with self.assertRaises(ValueError):	
            CS.configure(struct=real_struct)
            CS.process_align(aln)
        
    def test_results_T(self):
        CS = egglib.stats.ComputeStats(multi=True)
        CS.add_stats('Atot', 'Aing', 'R', 'He')
        aln = egglib.io.from_fasta(str(path / 'dmi3.fas'), labels=True, alphabet=egglib.alphabets.DNA)
        CS.process_align(aln)
        results=CS.results()
        for key in sorted(results):self.assertIsNotNone(results[key])  
        self.assertIsInstance(results,dict)

    def test_MAF(self):
        alph = egglib.alphabets.Alphabet('range', (0, 4), None)
        NS = 100
        for pl in 1,2,4:
            cs = egglib.stats.ComputeStats()
            cs.add_stats('maf')
            for rep in range(100):
                nall = random.choice([2,3,4])
                alleles = range(nall)
                array = [random.choice(alleles) for i in range(NS) for j in range(pl)]
                if random.random() < 0.5:
                    for i in range(NS):
                        if random.random() < 0.1: array[i*pl:i*pl+pl] = [0] * pl
                site = egglib.site_from_list(array, alphabet=alph)
                freq = [array.count(i) for i in range(nall)]
                freq.sort()
                MAF = freq[0]
                stats = cs.process_site(site)
                self.assertAlmostEqual(1.0*MAF/sum(freq), stats['maf'], places=5)

    def test_MAF_filter(self):
        alph = egglib.alphabets.Alphabet('range', (1, 1001), (0, 1))

        aln = egglib.Align.create(
           [('', [21, 20,  4, 47, 59,  0, 29, 21, 51,  4,  4, 14, 57]),
            ('', [21, 20,  4, 47, 59, 50, 29,  2, 51,  4,  4, 14, 57]),
            ('', [21, 20,  4, 47, 59, 50, 29,  2, 51,  4,  4, 14, 57]),
            ('', [21, 20,  4,  4, 38, 26,  5, 21, 51,  4, 82, 14, 57]),
            ('', [21, 20,  4, 47, 59,  0, 29, 21, 51,  4,  0,  0, 35]),
            ('', [21, 20,  4, 47, 59, 50, 29,  2, 51,  4,  4, 14, 57]),
            ('', [21, 20,  4, 47, 59, 50, 29,  2, 51,  4,  4, 14, 57]),
            ('', [21, 20,  4,  4, 38, 26,  5, 21, 51,  4, 82, 14, 57]),
            ('', [21, 20,  4,  4, 38, 26,  5, 21, 51,  0, 82, 14, 57]),
            ('', [21, 20,  4, 47, 59, 50, 29, 21, 51,  4,  4, 14, 35]),
            ('', [ 0, 20,  4, 47, 59, 50, 29, 21, 51,  4,  4, 14, 35]),
            ('', [21, 20,  4, 47, 59, 50, 29,  2, 51,  4,  4, 14, 57]),
            ('', [21, 20,  0, 47,  0, 50, 29,  0, 51,  4,  4, 14, 57]),
            ('', [21, 20, 73, 47, 59, 50, 29, 21, 51,  4,  4, 14, 57]),
            ('', [21, 20,  4,  4, 38, 26,  5, 21, 13,  4,  0, 75, 57]),
            ('', [21, 20,  4,  0, 38, 26,  5, 21, 51,  0, 82, 14, 57]),
            ('', [21, 20,  4, 47, 59, 50, 29,  2,  0,  4,  4, 14, 57]),
            ('', [21, 20, 73, 47, 59, 50, 29, 21, 51,  4,  4, 14, 57]),
            ('', [21, 39,  4, 47,  0, 50, 29,  2,  0,  4,  4, 14, 57]),
            ('', [99,  0,  4, 47, 59,  0, 29,  0, 51, 95,  4, 14, 57])], alph)

        sites0 = [6, 12] # sites with 0 missing data
        sites1 = [0, 1, 2, 3, 11] # sites 1 missing datum
        sites2 = [4, 7, 8, 9, 10] # sites 2 missing data
        sites3 = [5]  # sites 3 missing data

        aln_0 = aln.extract(sites0) # sites with 0 missing data
        aln_1 = aln.extract(sites0 + sites1) # 0 or 1 missing
        aln_2 = aln.extract(sites0 + sites1 + sites2) # 0, 1, 2 missing
        aln_3 = aln.extract(sites0 + sites1 + sites2 + sites3) # 0, 1, 2, 3 missing
        self.assertEqual(sorted(sites0 + sites1 + sites2 + sites3), list(range(aln.ls)))

        keystats = 'lseff', 'nseff', 'S', 'D', 'Pi', 'Ki', 'maf', 'V', 'Aing'
        cs = egglib.stats.ComputeStats()
        cs.add_stats(* keystats)

        stats0 = cs.process_align(aln_0)
        stats1 = cs.process_align(aln_1)
        stats2 = cs.process_align(aln)
        stats3 = cs.process_align(aln)

        cs.configure(maf=0.0)
        for key, value in cs.process_align(aln).items():
            self.assertEqual(value, stats0[key])

        cs.configure(maf=1/20.0)
        for key, value in cs.process_align(aln).items():
            self.assertEqual(value, stats1[key])

        cs.configure(maf=2/20.0)
        for key, value in cs.process_align(aln).items():
            self.assertEqual(value, stats2[key])

        cs.configure(maf=3/20.0)
        for key, value in cs.process_align(aln).items():
            self.assertEqual(value, stats3[key])

    def test_ns_others(self):
        coal = egglib.coalesce.Simulator(2, num_chrom=[20, 20], theta=5.0, migr=2.0)
        struct = coal.params.mk_structure()
        aln1 = coal.simul()
        aln2 = coal.simul()

        cs = egglib.stats.ComputeStats(struct=struct)
        cs.add_stats('rD', 'D', 'Ki', 'Kt', 'FstH', 'Kst', 'Snn', 'Fs',
            'Rmin', 'RminL', 'Rintervals', 'nPairs', 'nPairsAdj',
            'ZnS', 'Z*nS', 'Z*nS*', 'Za', 'ZZ')

        # load sites as Align
        res = cs.process_align(aln1)
        for i in res: self.assertIsNotNone(res[i], msg=i)

        cs.configure(multi=True, struct=struct)
        cs.process_align(aln1)
        cs.process_align(aln2)
        res = cs.results()
        for i in res: self.assertIsNotNone(res[i], msg=i)

        # load sites as list of sites
        sites = []
        for i in range(aln1.ls):
            sites.append(egglib.site_from_align(aln1, i))
        for i in range(aln2.ls):
            sites.append(egglib.site_from_align(aln2, i))
        cs.configure(struct=struct)
        res = cs.process_sites(sites)
        for i in res: self.assertIsNotNone(res[i], msg=i)
            # currently not possible to compute LD statistics using process_site(), or process_sites() + multi

        coal.params['num_chrom'][1] = 19
        aln3 = coal.simul()
        cs.configure(multi=True, struct=None)
        cs.process_align(aln1)
        cs.process_align(aln2)
        cs.process_align(aln3) # supports different ns
        stats = cs.results()
        self.assertIsNone(stats['Ki'])
        self.assertIsNotNone(stats['D'])

        sites = []
        for i in range(aln1.ls):
            sites.append(egglib.site_from_align(aln1, i))
        for i in range(aln2.ls):
            sites.append(egglib.site_from_align(aln2, i))
        for i in range(aln3.ls):
            sites.append(egglib.site_from_align(aln3, i))
        cs.configure()
        #with self.assertRaises(ValueError): cs.process_sites(sites)
        cs.process_sites(sites)

        # test also that change of ploidy causes a problem
        coal.params['num_chrom'] = 0, 0
        coal.params['num_indiv'] = 20, 20 # same number of indiv
        aln4 = coal.simul()

        cs.configure(multi=True)
        cs.process_align(aln1)
        #with self.assertRaises(ValueError): cs.process_align(aln4)
        cs.process_align(aln4)

        sites = []
        for i in range(aln1.ls):
            sites.append(egglib.site_from_align(aln1, i))
        for i in range(aln4.ls):
            sites.append(egglib.site_from_align(aln4, i))
        cs.configure()
        #with self.assertRaises(ValueError): cs.process_sites(sites)
        cs.process_sites(sites)

    def test_varying_ns(self):
        coal = egglib.coalesce.Simulator(2, num_chrom=[25, 2], theta=5.0, migr=0.0)
        coal.params.add_event('merge', T=3.0, src=0, dst=1)
        aln1 = coal.simul()
        self.assertEqual(aln1.ns, 25+2)

        coal.params['num_chrom'] = 27, 1
        aln2 = coal.simul()
        self.assertEqual(aln2.ns, 27+1)

        coal.params['num_chrom'] = 24, 2
        aln3 = coal.simul()
        self.assertEqual(aln3.ns, 24+2)

        cs = egglib.stats.ComputeStats()
        cs.add_stats('S', 'Pi', 'D', 'So', 'lseff', 'lseffo', 'nseff', 'nseffo', 'thetaH', 'thetaL', 'nsmaxo', 'R2', 'B')

        cs.configure(multi=True)
        self.assertIsNone(cs.process_align(aln1))
        self.assertIsNone(cs.process_align(aln2))
        self.assertIsNone(cs.process_align(aln3))
        cs.results()

    def test_M_Rst(self):
        # raw data
        orientalis = [
            [(81, 91, 167, 220, 197, 142, 183, 145, 216, 134, 112, 165, 99, 94, 105, 168),
             (94, 111, 169, 220, 203, 146, 183, 156, 224, 136, 112, 179, 101, 131, 109, 170)],
            [(81, 87, 169, 220, 197, 136, 183, 149, 222, 134, 94, 165, 101, 100, 105, 166),
             (81, 91, 169, 232, 201, 142, 194, 156, 224, 134, 94, 177, 113, 125, 109, 172)],
            [(94, 99, 163, 220, 197, 136, 185, 145, 218, 134, 94, 165, 101, 94, 109, 168),
             (94, 99, 169, 220, 201, 140, 194, 152, 218, 134, 112, 179, 101, 118, 115, 170)],
            [(81, 93, 175, 220, 197, 144, 185, 149, 218, 134, 94, 165, 101, 106, 109, 168),
             (96, 99, 175, 220, 199, 146, 195, 152, 222, 136, 112, 173, 109, 110, 117, 170)],
            [( 81, 91, 169, 220, 197, 136, 185, 150, 222, 134, 94, 165, 109, 86, 109, 166),
             (89, 93, 169, 220, 197, 140, 195, 150, 224, 136, 112, 177, 111, 141, 123, 168)],
            [(81, 91, 159, 220, 195, 136, 195, 146, 218, 136, 112, 171, 101, 86, 109, 170),
             (94, 107, 165, 223, 197, 146, 195, 150, 220, 138, 112, 171, 103, 92, 109, 174)],
            [(81, 93, 167, 220, 195, 136, 183, 149, 220, 134, 94, 173, 0, 118, 99, 166),
             (81, 109, 167, 220, 211, 142, 190, 149, 224, 136, 112, 173, 0, 129, 129, 168)],
            [(81, 91, 169, 226, 195, 136, 185, 152, 214, 134, 112, 165, 101, 92, 119, 158),
             (94, 99, 169, 226, 197, 140, 195, 156, 224, 134, 112, 177, 115, 94, 129, 166)]]

        sylvatica = [
            [(89, 95, 159, 217, 195, 142, 190, 146, 216, 138, 118, 169, 97, 112, 129, 166),
             (89, 97, 159, 226, 195, 146, 195, 154, 216, 138, 119, 169, 97, 114, 131, 166)],
            [(89, 97, 159, 217, 199, 144, 192, 146, 216, 138, 116, 167, 103, 114, 129, 166),
             (94, 107, 159, 226, 199, 150, 195, 150, 216, 138, 119, 185, 109, 133, 131, 166)],
            [(89, 97, 161, 211, 195, 144, 192, 150, 212, 132, 116, 175, 97, 114, 119, 166),
             (89, 97, 163, 226, 197, 150, 192, 150, 220, 138, 125, 179, 97, 121, 131, 166)],
            [(89, 97, 159, 217, 195, 148, 191, 146, 203, 138, 116, 173, 97, 112, 131, 164),
             (96, 99, 163, 229, 195, 148, 192, 146, 218, 138, 125, 183, 105, 121, 133, 174)],
            [(87, 97, 159, 217, 195, 142, 191, 146, 205, 138, 116, 167, 97, 112, 117, 164),
             (89, 99, 163, 226, 195, 144, 192, 146, 216, 140, 116, 173, 97, 121, 127, 168)],
            [(87, 97, 159, 217, 199, 142, 192, 146, 212, 138, 125, 171, 97, 118, 0, 166),
             (89, 111, 163, 226, 199, 144, 192, 146, 216, 138, 129, 173, 109, 133, 0, 166)],
            [(89, 97, 161, 211, 195, 146, 190, 150, 216, 138, 110, 173, 97, 112, 121, 162),
             (94, 105, 163, 220, 195, 148, 192, 152, 220, 138, 116, 173, 101, 119, 131, 170)],
            [(87, 101, 161, 211, 195, 148, 191, 150, 214, 132, 116, 167, 97, 112, 129, 166),
             (89, 109, 167, 229, 195, 148, 192, 150, 222, 140, 116, 173, 99, 114, 129, 166)],
            [(89, 95, 159, 211, 195, 150, 192, 150, 212, 138, 119, 171, 103, 112, 129, 166),
             (89, 111, 163, 217, 195, 152, 195, 154, 218, 138, 125, 173, 109, 121, 129, 166)],
            [(89, 97, 161, 211, 177, 142, 190, 146, 214, 138, 114, 173, 0, 112, 131, 166),
             (91, 97, 165, 226, 195, 148, 194, 150, 218, 138, 125, 177, 0, 119, 133, 168)],
            [(87, 95, 159, 211, 177, 146, 192, 154, 203, 138, 112, 173, 97, 0, 129, 166),
             (89, 99, 159, 226, 195, 148, 192, 154, 214, 138, 119, 175, 101, 0, 129, 168)],
            [(89, 97, 161, 211, 177, 142, 195, 150, 212, 138, 114, 173, 97, 104, 129, 168),
             (94, 97, 161, 217, 195, 152, 195, 150, 214, 140, 116, 173, 103, 110, 129, 172)],
            [(89, 97, 161, 217, 195, 142, 190, 150, 216, 138, 118, 171, 97, 0, 117, 166),
             (89, 97, 161, 226, 195, 148, 195, 150, 216, 140, 119, 173, 109, 0, 135, 168)],
            [(87, 97, 163, 211, 195, 148, 195, 146, 214, 132, 116, 177, 97, 104, 117, 164),
             (89, 111, 167, 226, 195, 152, 195, 154, 214, 138, 125, 183, 101, 121, 129, 166)],
            [(87, 95, 161, 211, 195, 148, 190, 146, 211, 138, 108, 171, 97, 112, 129, 164),
             (94, 113, 161, 211, 195, 150, 192, 150, 216, 140, 116, 173, 109, 114, 131, 164)],
            [(89, 97, 159, 211, 195, 146, 191, 146, 212, 138, 118, 173, 97, 116, 127, 164),
             (94, 113, 161, 217, 195, 150, 192, 146, 220, 138, 125, 183, 109, 116, 133, 166)],
            [(89, 97, 161, 211, 195, 142, 192, 150, 212, 132, 119, 167, 97, 110, 131, 168),
             (94, 99, 161, 226, 197, 146, 192, 150, 214, 138, 129, 173, 101, 112, 131, 168)],
            [(77, 95, 161, 226, 195, 148, 194, 146, 212, 138, 114, 175, 103, 112, 131, 166),
             (89, 97, 161, 229, 195, 150, 195, 156, 216, 140, 119, 183, 103, 112, 133, 168)],
            [(89, 97, 159, 211, 0, 146, 190, 150, 212, 132, 116, 173, 97, 119, 129, 166),
             (94, 105, 161, 217, 0, 148, 194, 150, 220, 138, 125, 177, 101, 121, 131, 168)],
            [(89, 97, 159, 220, 199, 146, 192, 150, 214, 138, 108, 173, 97, 119, 131, 166),
             (89, 111, 161, 226, 199, 148, 192, 154, 216, 138, 116, 175, 97, 121, 131, 166)],
            [(89, 105, 159, 211, 195, 148, 192, 154, 216, 138, 116, 177, 97, 112, 127, 166),
             (89, 117, 163, 217, 199, 150, 195, 154, 216, 138, 127, 183, 105, 114, 129, 168)],
            [(89, 97, 159, 217, 195, 148, 191, 146, 205, 138, 116, 167, 97, 112, 117, 164),
             (96, 99, 163, 229, 195, 148, 192, 146, 216, 140, 116, 173, 97, 121, 127, 168)],
            [(77, 97, 161, 211, 195, 146, 192, 146, 211, 138, 116, 169, 97, 104, 119, 166),
             (89, 111, 163, 217, 195, 148, 192, 146, 216, 138, 119, 173, 97, 121, 127, 168)],
            [(77, 95, 159, 211, 195, 144, 190, 150, 216, 138, 125, 167, 97, 114, 121, 164),
             (89, 111, 161, 226, 195, 146, 191, 150, 216, 138, 125, 169, 103, 121, 129, 166)],
            [(77, 97, 159, 217, 195, 146, 192, 146, 216, 138, 116, 165, 97, 98, 119, 166),
             (89, 111, 159, 226, 199, 148, 195, 154, 220, 138, 125, 171, 97, 114, 131, 168)],
            [(87, 111, 161, 211, 195, 142, 192, 150, 212, 138, 116, 165, 97, 112, 119, 164),
             (94, 111, 161, 226, 199, 142, 194, 154, 212, 138, 116, 171, 103, 114, 129, 166)],
            [(89, 95, 161, 211, 195, 144, 190, 146, 205, 138, 125, 171, 97, 119, 129, 166),
             (91, 111, 161, 226, 197, 144, 191, 150, 214, 138, 125, 171, 103, 121, 129, 168)],
            [(87, 97, 161, 211, 195, 142, 190, 146, 212, 138, 119, 173, 97, 96, 0, 168),
             (89, 97, 161, 226, 195, 142, 195, 146, 216, 138, 125, 181, 99, 121, 0, 168)],
            [(89, 111, 163, 211, 195, 142, 192, 146, 209, 138, 116, 167, 97, 112, 119, 166),
             (94, 111, 163, 226, 195, 146, 192, 146, 212, 138, 119, 173, 109, 112, 127, 168)],
            [(89, 97, 161, 211, 195, 142, 194, 146, 212, 138, 118, 173, 103, 114, 119, 166),
             (89, 101, 161, 226, 199, 146, 195, 156, 214, 140, 125, 175, 107, 121, 129, 174)],
            [(87, 97, 159, 220, 197, 148, 192, 146, 218, 138, 116, 175, 99, 114, 129, 164),
             (89, 97, 161, 226, 199, 150, 192, 156, 218, 138, 119, 177, 103, 114, 129, 166)]]

        progeny = [
            [(81, 91, 165, 214, 197, 140, 183, 156, 216, 134, 94, 165, 109, 92, 105, 170),
             (94, 99, 169, 220, 199, 144, 183, 156, 218, 134, 94, 186, 109, 102, 121, 174)],
            [(81, 97, 161, 220, 0, 136, 190, 149, 216, 134, 94, 173, 101, 96, 99, 166),
             (89, 109, 167, 226, 0, 146, 195, 150, 232, 136, 112, 175, 101, 102, 99, 172)],
            [(81, 91, 167, 220, 195, 136, 183, 149, 209, 134, 112, 171, 99, 94, 109, 170),
             (94, 109, 169, 220, 195, 136, 185, 152, 211, 134, 112, 181, 101, 119, 123, 172)],
            [(81, 91, 165, 220, 197, 136, 183, 146, 216, 134, 94, 165, 99, 102, 121, 166),
             (81, 91, 167, 220, 199, 136, 190, 156, 224, 138, 112, 179, 103, 118, 127, 174)],
            [(81, 99, 167, 220, 195, 136, 185, 149, 216, 134, 112, 171, 99, 94, 109, 166),
             (94, 109, 169, 220, 195, 136, 190, 152, 232, 134, 112, 173, 103, 100, 119, 172)],
            [(81, 93, 167, 220, 195, 136, 185, 149, 212, 134, 112, 173, 101, 86, 125, 170),
             (81, 99, 169, 226, 211, 140, 190, 156, 216, 134, 118, 179, 101, 92, 125, 172)],
            [(94, 97, 159, 226, 195, 148, 192, 146, 218, 138, 114, 171, 0, 112, 119, 164),
             (94, 101, 161, 226, 199, 148, 194, 154, 220, 138, 125, 173, 0, 116, 129, 168)],
            [(89, 97, 161, 217, 195, 148, 192, 146, 216, 138, 116, 167, 97, 112, 109, 166),
             (94, 97, 161, 217, 199, 148, 195, 150, 218, 140, 116, 177, 107, 121, 129, 166)],
            [(89, 97, 159, 226, 195, 146, 191, 146, 216, 138, 118, 169, 97, 112, 129, 164),
             (89, 111, 161, 226, 195, 148, 195, 150, 218, 138, 119, 173, 97, 112, 129, 166)],
            [(89, 91, 163, 220, 195, 142, 183, 145, 216, 136, 112, 165, 97, 114, 105, 164),
             (94, 111, 169, 226, 197, 142, 195, 154, 216, 138, 125, 175, 99, 131, 117, 168)],
            [(89, 97, 159, 220, 197, 142, 183, 150, 214, 134, 112, 165, 99, 112, 109, 168),
             (94, 111, 169, 226, 197, 150, 192, 156, 224, 138, 125, 169, 109, 131, 129, 170)],
            [(81, 97, 161, 220, 199, 142, 183, 146, 216, 136, 112, 173, 99, 94, 109, 166),
             (89, 111, 169, 229, 203, 150, 191, 156, 224, 138, 118, 179, 109, 121, 127, 168)],
            [(81, 95, 161, 220, 195, 142, 183, 146, 212, 134, 112, 165, 101, 94, 109, 168),
             (89, 111, 169, 226, 197, 148, 191, 156, 224, 138, 125, 173, 103, 110, 129, 168)],
            [(81, 97, 161, 220, 195, 146, 183, 145, 214, 134, 112, 165, 97, 94, 105, 168),
             (89, 111, 169, 226, 197, 152, 194, 154, 216, 138, 116, 171, 99, 94, 131, 170)],
            [(89, 91, 161, 217, 199, 142, 183, 145, 212, 136, 112, 165, 99, 94, 109, 166),
             (94, 111, 167, 220, 203, 142, 194, 150, 216, 140, 127, 177, 109, 119, 129, 170)],
            [(81, 91, 167, 220, 197, 142, 183, 145, 216, 134, 94, 165, 101, 129, 109, 166),
             (94, 93, 167, 220, 211, 142, 190, 149, 220, 136, 112, 173, 101, 129, 129, 170)],
            [(89, 91, 167, 220, 195, 146, 183, 145, 214, 132, 112, 165, 101, 121, 105, 164),
             (94, 111, 169, 226, 197, 152, 195, 146, 216, 134, 125, 177, 101, 131, 117, 168)],
            [(77, 91, 159, 217, 177, 142, 183, 145, 203, 132, 112, 173, 101, 131, 109, 170),
             (81, 95, 167, 220, 203, 150, 194, 150, 224, 134, 125, 179, 107, 131, 127, 172)],
            [(81, 91, 169, 220, 197, 142, 183, 145, 224, 134, 94, 165, 99, 100, 105, 166),
             (94, 91, 169, 220, 197, 142, 183, 156, 224, 136, 112, 177, 101, 131, 109, 168)],
            [(89, 91, 159, 220, 195, 144, 183, 150, 214, 136, 112, 177, 97, 114, 109, 166),
             (94, 111, 167, 226, 203, 146, 195, 156, 224, 138, 125, 179, 99, 131, 127, 170)],
            [(89, 91, 161, 211, 195, 142, 183, 145, 214, 136, 112, 177, 99, 114, 105, 168),
             (94, 95, 167, 220, 203, 146, 194, 146, 216, 138, 125, 179, 101, 131, 127, 170)],
            [(81, 97, 161, 220, 199, 142, 183, 146, 216, 134, 112, 167, 101, 131, 109, 166),
             (89, 111, 167, 226, 203, 142, 190, 156, 224, 138, 119, 179, 103, 131, 131, 170)],
            [(81, 97, 163, 211, 177, 142, 183, 146, 218, 132, 112, 165, 101, 116, 109, 166),
             (94, 111, 169, 220, 197, 148, 192, 156, 224, 134, 125, 173, 101, 131, 129, 168)],
            [(81, 91, 159, 220, 195, 146, 183, 146, 216, 134, 112, 165, 101, 110, 109, 168),
             (89, 97, 169, 226, 197, 146, 194, 156, 224, 138, 116, 167, 103, 131, 127, 168)],
            [(89, 95, 161, 217, 199, 142, 183, 146, 216, 134, 112, 173, 97, 121, 105, 168),
             (94, 111, 167, 220, 203, 148, 190, 156, 218, 138, 125, 179, 101, 131, 129, 170)],
            [(77, 97, 159, 220, 197, 142, 183, 154, 212, 136, 112, 173, 99, 94, 109, 170),
             (81, 111, 167, 226, 203, 150, 192, 156, 224, 138, 121, 179, 105, 94, 129, 172)],
            [(81, 91, 161, 211, 197, 146, 183, 145, 212, 132, 112, 165, 99, 94, 105, 168),
             (89, 111, 169, 220, 197, 148, 192, 150, 224, 134, 119, 173, 101, 94, 121, 168)],
            [(89, 97, 159, 217, 195, 146, 190, 146, 214, 138, 116, 167, 97, 112, 129, 166),
             (94, 97, 163, 217, 197, 148, 195, 150, 216, 138, 118, 169, 99, 119, 131, 166)],
            [(87, 111, 161, 217, 177, 144, 192, 146, 209, 132, 108, 167, 99, 112, 119, 166),
             (89, 111, 163, 226, 195, 152, 192, 150, 216, 138, 116, 185, 109, 112, 129, 168)],
            [(89, 101, 159, 211, 195, 142, 192, 150, 212, 138, 116, 167, 97, 98, 129, 166),
             (89, 111, 167, 217, 195, 148, 195, 150, 214, 140, 125, 175, 103, 112, 133, 168)],
            [(87, 97, 161, 211, 195, 148, 192, 150, 212, 138, 116, 171, 101, 112, 127, 166),
             (89, 99, 163, 220, 199, 150, 192, 150, 216, 140, 125, 173, 109, 119, 129, 168)],
            [(87, 97, 161, 211, 195, 142, 191, 146, 220, 138, 119, 173, 97, 114, 119, 166),
             (89, 109, 161, 226, 195, 150, 195, 150, 220, 138, 125, 177, 97, 114, 131, 166)],
            [(89, 97, 159, 211, 195, 148, 192, 150, 212, 138, 116, 171, 97, 0, 127, 166),
             (89, 97, 163, 220, 195, 148, 192, 156, 218, 138, 125, 173, 101, 0, 129, 168)],
            [(87, 97, 161, 217, 195, 146, 190, 146, 205, 138, 119, 167, 97, 0, 0, 166),
             (89, 111, 163, 217, 199, 146, 192, 156, 216, 138, 125, 177, 109, 0, 0, 166)],
            [(87, 97, 159, 226, 195, 142, 190, 150, 214, 138, 119, 173, 97, 121, 129, 162),
             (89, 111, 161, 226, 199, 146, 195, 156, 214, 138, 125, 173, 105, 121, 133, 166)],
            [(89, 95, 159, 211, 177, 144, 195, 150, 209, 138, 116, 171, 97, 110, 129, 162),
             (94, 97, 163, 226, 199, 148, 195, 156, 220, 138, 125, 173, 101, 110, 129, 166)],
            [(81, 97, 163, 220, 195, 135, 185, 149, 214, 134, 112, 173, 105, 91, 105, 166),
             (91, 111, 169, 226, 197, 148, 192, 150, 216, 138, 116, 185, 105, 91, 129, 170)],
            [(89, 111, 161, 211, 177, 144, 192, 146, 209, 138, 116, 169, 99, 0, 117, 166),
             (94, 111, 163, 217, 195, 150, 192, 146, 212, 138, 118, 185, 105, 0, 119, 166)],
            [(94, 95, 161, 211, 195, 144, 191, 149, 212, 138, 119, 171, 101, 96, 127, 164),
             (94, 111, 163, 226, 195, 148, 195, 150, 216, 138, 125, 173, 105, 96, 131, 166)],
            [(87, 95, 159, 211, 177, 146, 192, 146, 205, 132, 116, 165, 105, 110, 131, 166),
             (89, 97, 163, 229, 195, 150, 192, 146, 218, 132, 119, 177, 109, 110, 137, 168)],
            [(87, 97, 161, 211, 195, 148, 192, 146, 216, 132, 116, 173, 105, 110, 131, 162),
             (87, 97, 163, 229, 197, 148, 192, 154, 218, 132, 116, 177, 109, 110, 137, 164)],
            [(87, 109, 159, 211, 197, 142, 192, 150, 205, 132, 116, 171, 105, 121, 131, 166),
             (89, 111, 161, 211, 199, 142, 195, 150, 212, 138, 119, 173, 109, 121, 131, 168)],
            [(81, 97, 163, 211, 195, 142, 185, 146, 214, 134, 112, 173, 99, 91, 99, 164),
             (89, 99, 169, 220, 197, 146, 190, 149, 216, 138, 125, 185, 109, 110, 129, 170)],
            [(81, 99, 159, 211, 195, 142, 185, 146, 214, 134, 112, 171, 109, 91, 105, 164),
             (89, 111, 169, 226, 197, 148, 195, 149, 218, 138, 125, 185, 109, 116, 129, 170)],
            [(81, 111, 161, 217, 197, 135, 192, 149, 214, 134, 112, 177, 103, 121, 99, 164),
             (87, 115, 169, 220, 197, 142, 198, 154, 218, 138, 116, 185, 103, 129, 129, 170)],
            [(87, 111, 159, 217, 195, 148, 192, 149, 214, 138, 116, 167, 97, 98, 129, 166),
             (89, 111, 167, 217, 195, 150, 195, 150, 220, 140, 125, 175, 105, 112, 129, 168)],
            [(94, 87, 159, 220, 197, 144, 183, 150, 214, 134, 112, 173, 101, 0, 99, 161),
             (94, 91, 165, 220, 203, 144, 194, 150, 216, 134, 112, 173, 101, 0, 99, 172)],
            [(81, 91, 169, 220, 197, 140, 183, 145, 216, 134, 112, 171, 99, 86, 105, 168),
             (94, 91, 169, 226, 203, 144, 198, 146, 222, 136, 112, 181, 101, 96, 105, 172)],
            [(81, 97, 163, 211, 195, 142, 185, 149, 214, 134, 112, 165, 99, 91, 99, 166),
             (87, 99, 167, 220, 197, 152, 195, 154, 214, 138, 125, 177, 101, 104, 117, 166)],
            [(81, 91, 161, 217, 195, 144, 183, 150, 209, 136, 94, 167, 97, 112, 123, 161),
             (89, 97, 169, 220, 197, 144, 192, 152, 212, 138, 116, 171, 101, 129, 127, 168)],
            [(89, 97, 159, 211, 195, 136, 194, 145, 209, 132, 94, 173, 97, 110, 115, 170),
             (94, 99, 169, 220, 197, 142, 195, 146, 218, 134, 125, 179, 101, 118, 129, 170)],
            [(89, 97, 161, 220, 197, 136, 194, 146, 209, 134, 112, 173, 101, 118, 109, 166),
             (94, 99, 169, 226, 199, 146, 195, 152, 218, 138, 125, 179, 109, 118, 129, 168)],
            [(81, 91, 159, 226, 197, 140, 183, 146, 212, 132, 112, 173, 101, 100, 109, 168),
             (89, 97, 161, 226, 199, 150, 192, 150, 218, 136, 121, 173, 105, 100, 129, 172)],
            [(94, 95, 163, 217, 195, 140, 185, 145, 218, 134, 112, 173, 97, 118, 109, 168),
             (94, 99, 169, 220, 197, 148, 194, 150, 222, 138, 127, 179, 101, 118, 119, 168)],
            [(87, 0, 0, 0, 0, 140, 0, 146, 218, 134, 94, 165, 97, 0, 109, 164),
             (94, 0, 0, 0, 0, 148, 0, 152, 222, 138, 125, 173, 101, 0, 129, 170)],
            [(89, 95, 161, 220, 195, 136, 194, 145, 0, 0, 94, 0, 0, 112, 109, 0),
             (94, 99, 169, 226, 197, 146, 195, 150, 0, 0, 119, 0, 0, 112, 109, 0)],
            [(89, 97, 163, 217, 195, 140, 194, 145, 216, 134, 112, 165, 101, 119, 109, 168),
             (94, 99, 163, 220, 197, 146, 194, 150, 218, 138, 125, 177, 105, 119, 129, 170)],
            [(77, 97, 163, 211, 195, 136, 192, 146, 216, 0, 112, 0, 0, 94, 129, 168),
             (94, 99, 163, 220, 197, 150, 194, 152, 218, 0, 116, 0, 0, 94, 129, 170)],
            [(81, 93, 167, 220, 197, 136, 185, 145, 0, 0, 94, 0, 0, 94, 99, 168),
             (94, 99, 169, 220, 211, 136, 190, 149, 0, 0, 94, 0, 0, 129, 109, 168)],
            [(89, 99, 163, 220, 195, 136, 194, 146, 0, 0, 112, 0, 0, 0, 0, 0),
             (94, 111, 169, 226, 197, 152, 195, 152, 0, 0, 125, 0, 0, 0, 0, 0)],
            [(87, 97, 161, 220, 195, 136, 194, 150, 216, 134, 94, 165, 101, 119, 109, 164),
             (94, 99, 163, 226, 197, 148, 195, 152, 218, 140, 108, 171, 103, 119, 133, 170)],
            [(89, 97, 163, 217, 195, 140, 194, 145, 0, 0, 112, 0, 0, 0, 109, 0),
             (94, 99, 163, 220, 197, 142, 195, 146, 0, 0, 119, 0, 0, 0, 117, 0)],
            [(77, 95, 159, 211, 197, 146, 194, 149, 216, 134, 94, 173, 97, 110, 109, 164),
             (81, 99, 175, 220, 197, 148, 195, 154, 222, 138, 108, 173, 101, 112, 129, 168)],
            [(81, 97, 163, 220, 195, 142, 195, 146, 216, 134, 112, 173, 97, 91, 99, 166),
             (89, 99, 169, 220, 197, 148, 198, 149, 216, 140, 125, 185, 111, 91, 129, 166)],
            [(81, 111, 161, 220, 195, 136, 190, 146, 209, 134, 112, 165, 97, 121, 105, 168),
             (87, 111, 169, 226, 197, 142, 198, 149, 216, 138, 116, 183, 97, 129, 129, 170)],
            [(81, 97, 159, 220, 177, 142, 195, 146, 0, 0, 112, 0, 0, 106, 0, 0),
             (87, 99, 175, 226, 197, 144, 195, 149, 0, 0, 125, 0, 0, 114, 0, 0)],
            [(94, 97, 165, 217, 199, 144, 185, 149, 212, 134, 112, 167, 101, 106, 109, 168),
             (96, 99, 175, 220, 199, 146, 192, 150, 222, 138, 125, 173, 101, 119, 121, 170)],
            [(81, 99, 161, 217, 197, 146, 185, 146, 218, 134, 94, 173, 103, 106, 109, 166),
             (87, 111, 175, 220, 197, 148, 192, 152, 220, 138, 116, 173, 109, 118, 129, 170)],
            [(87, 93, 161, 220, 195, 142, 185, 146, 220, 136, 0, 165, 101, 0, 109, 166),
             (96, 95, 175, 226, 199, 146, 195, 149, 222, 138, 0, 169, 105, 0, 119, 168)],
            [(94, 93, 163, 220, 195, 142, 192, 146, 209, 136, 94, 165, 97, 106, 117, 168),
             (96, 111, 175, 229, 199, 144, 195, 149, 218, 138, 125, 171, 109, 119, 125, 170)],
            [(81, 99, 161, 220, 195, 144, 195, 146, 209, 134, 112, 173, 101, 106, 109, 164),
             (87, 111, 175, 226, 197, 150, 195, 149, 218, 138, 121, 173, 109, 119, 129, 170)],
            [(81, 93, 159, 211, 195, 144, 185, 149, 212, 134, 94, 173, 97, 106, 109, 168),
             (87, 97, 175, 220, 197, 148, 194, 150, 218, 138, 116, 175, 109, 127, 127, 170)],
            [(89, 97, 163, 220, 195, 142, 0, 146, 0, 0, 0, 0, 0, 0, 0, 0),
             (96, 99, 175, 226, 197, 146, 0, 152, 0, 0, 0, 0, 0, 0, 0, 0)],
            [(81, 91, 167, 220, 197, 146, 183, 145, 222, 134, 112, 173, 101, 94, 105, 168),
             (81, 99, 175, 220, 203, 146, 185, 152, 224, 136, 112, 179, 109, 110, 117, 170)],
            [(81, 97, 161, 220, 197, 142, 185, 146, 209, 136, 112, 173, 97, 0, 109, 166),
             (89, 99, 175, 226, 199, 146, 192, 152, 218, 140, 116, 173, 109, 0, 123, 170)],
            [(81, 97, 161, 220, 197, 146, 195, 146, 209, 134, 94, 173, 101, 106, 109, 164),
             (87, 99, 175, 226, 199, 146, 195, 149, 218, 138, 125, 173, 109, 114, 125, 168)],
            [(0, 0, 0, 0, 0, 144, 0, 146, 0, 0, 0, 0, 0, 0, 0, 0),
             (0, 0, 0, 0, 0, 148, 0, 149, 0, 0, 0, 0, 0, 0, 0, 0)],
            [(81, 99, 161, 226, 177, 136, 190, 149, 0, 0, 108, 0, 0, 116, 0, 0),
             (89, 105, 169, 226, 197, 152, 198, 150, 0, 0, 112, 0, 0, 129, 0, 0)],
            [(81, 97, 161, 211, 195, 136, 194, 146, 214, 134, 112, 169, 97, 116, 99, 164),
             (89, 99, 169, 226, 197, 146, 198, 149, 220, 138, 125, 185, 99, 129, 131, 170)],
            [(89, 97, 159, 211, 195, 148, 192, 150, 205, 138, 116, 171, 107, 104, 129, 164),
             (89, 97, 161, 217, 195, 148, 195, 154, 209, 138, 125, 173, 109, 114, 129, 168)],
            [(89, 95, 159, 211, 195, 144, 192, 150, 216, 134, 94, 173, 101, 92, 99, 166),
             (89, 99, 159, 226, 197, 148, 194, 150, 224, 134, 112, 179, 117, 118, 121, 174)],
            [(89, 97, 159, 211, 0, 142, 192, 146, 212, 138, 119, 173, 97, 112, 127, 166),
             (94, 113, 163, 217, 0, 152, 192, 150, 216, 138, 123, 177, 103, 112, 129, 166)],
            [(81, 91, 165, 220, 195, 142, 183, 145, 216, 134, 94, 173, 97, 92, 109, 166),
             (94, 93, 167, 220, 197, 144, 183, 149, 216, 138, 125, 179, 101, 112, 119, 168)],
            [(89, 97, 161, 226, 195, 142, 195, 146, 212, 132, 125, 167, 97, 114, 129, 164),
             (94, 111, 161, 226, 199, 150, 195, 150, 212, 138, 125, 171, 107, 121, 131, 164)],
            [(87, 95, 161, 211, 195, 142, 192, 150, 220, 134, 112, 165, 115, 94, 129, 158),
             (94, 97, 161, 217, 195, 146, 192, 150, 224, 134, 112, 173, 117, 118, 129, 166)],
            [(89, 87, 163, 211, 197, 140, 192, 146, 214, 134, 94, 165, 101, 118, 119, 158),
             (89, 95, 165, 220, 199, 144, 192, 154, 220, 134, 112, 173, 117, 118, 129, 168)],
            [(81, 91, 163, 211, 195, 136, 194, 150, 216, 134, 108, 173, 0, 121, 129, 168),
             (94, 97, 171, 223, 195, 150, 195, 150, 220, 138, 112, 173, 0, 121, 131, 168)],
            [(89, 97, 159, 211, 197, 146, 192, 146, 214, 134, 112, 165, 101, 92, 99, 166),
             (94, 97, 163, 226, 199, 148, 192, 150, 224, 136, 112, 173, 117, 118, 119, 166)],
            [(89, 91, 161, 220, 197, 146, 183, 145, 216, 132, 112, 173, 99, 131, 109, 164),
             (94, 97, 169, 226, 199, 148, 192, 154, 224, 136, 125, 179, 103, 131, 127, 170)],
            [(81, 91, 165, 214, 197, 140, 183, 156, 212, 136, 112, 173, 99, 110, 105, 164),
             (94, 99, 169, 220, 199, 144, 183, 156, 216, 138, 119, 179, 99, 131, 131, 170)],
            [(81, 91, 165, 220, 197, 136, 183, 146, 214, 138, 112, 175, 97, 114, 117, 166),
             (81, 91, 167, 220, 199, 136, 190, 156, 216, 140, 119, 175, 97, 114, 129, 166)],
            [(81, 91, 167, 220, 201, 144, 183, 150, 216, 138, 116, 173, 99, 114, 119, 164),
             (81, 107, 171, 232, 201, 144, 194, 152, 216, 140, 125, 177, 105, 121, 131, 168)],
            [(85, 91, 165, 220, 195, 136, 195, 146, 216, 138, 119, 175, 97, 114, 117, 164),
             (94, 109, 167, 220, 205, 140, 195, 150, 220, 140, 119, 175, 101, 114, 131, 172)],
            [(81, 93, 165, 220, 195, 136, 183, 145, 212, 138, 116, 173, 97, 121, 119, 164),
             (81, 99, 167, 229, 197, 144, 194, 146, 214, 138, 119, 175, 107, 121, 131, 166)],
            [(81, 87, 169, 220, 197, 142, 183, 145, 222, 134, 94, 165, 99, 125, 105, 168),
             (94, 91, 169, 220, 201, 142, 194, 149, 224, 136, 112, 177, 101, 131, 109, 172)],
            [(81, 91, 161, 220, 177, 146, 183, 145, 212, 134, 112, 165, 97, 94, 105, 164),
             (89, 111, 169, 226, 197, 148, 194, 154, 224, 138, 116, 171, 101, 94, 131, 170)]]

        # per-population stats computed with Arlequin
        arlequin_stats =  [{
             1: {'ns_site':  16, 'Aing':  4, 'Ho': 0.62500, 'He': 0.61667, 'Ar': 15, 'M': 0.25000},
             2: {'ns_site':  16, 'Aing':  7, 'Ho': 0.87500, 'He': 0.84167, 'Ar': 24, 'M': 0.28000},
             3: {'ns_site':  16, 'Aing':  6, 'Ho': 0.37500, 'He': 0.73333, 'Ar': 16, 'M': 0.35294},
             4: {'ns_site':  16, 'Aing':  4, 'Ho': 0.25000, 'He': 0.44167, 'Ar': 12, 'M': 0.30769},
             5: {'ns_site':  16, 'Aing':  6, 'Ho': 0.87500, 'He': 0.73333, 'Ar': 16, 'M': 0.35294},
             6: {'ns_site':  16, 'Aing':  5, 'Ho': 1.00000, 'He': 0.80000, 'Ar': 10, 'M': 0.45455},
             7: {'ns_site':  16, 'Aing':  5, 'Ho': 0.75000, 'He': 0.80833, 'Ar': 12, 'M': 0.38462},
             8: {'ns_site':  16, 'Aing':  6, 'Ho': 0.75000, 'He': 0.86667, 'Ar': 11, 'M': 0.50000},
             9: {'ns_site':  16, 'Aing':  6, 'Ho': 0.87500, 'He': 0.83333, 'Ar': 10, 'M': 0.54545},
            10: {'ns_site':  16, 'Aing':  3, 'Ho': 0.62500, 'He': 0.54167, 'Ar':  4, 'M': 0.60000},
            11: {'ns_site':  16, 'Aing':  2, 'Ho': 0.50000, 'He': 0.50000, 'Ar': 18, 'M': 0.10526},
            12: {'ns_site':  16, 'Aing':  5, 'Ho': 0.75000, 'He': 0.80833, 'Ar': 14, 'M': 0.33333},
            13: {'ns_site':  14, 'Aing':  7, 'Ho': 0.85714, 'He': 0.75824, 'Ar': 16, 'M': 0.41176},
            14: {'ns_site':  16, 'Aing': 11, 'Ho': 1.00000, 'He': 0.95000, 'Ar': 55, 'M': 0.19643}},

          {
             1: {'ns_site':  62, 'Aing':  6, 'Ho': 0.77419, 'He': 0.62454, 'Ar': 19, 'M': 0.30000},
             2: {'ns_site':  62, 'Aing': 10, 'Ho': 0.74194, 'He': 0.74617, 'Ar': 22, 'M': 0.43478},
             3: {'ns_site':  62, 'Aing':  5, 'Ho': 0.54839, 'He': 0.67425, 'Ar':  8, 'M': 0.55556},
             4: {'ns_site':  62, 'Aing':  5, 'Ho': 0.96774, 'He': 0.73559, 'Ar': 18, 'M': 0.26316},
             5: {'ns_site':  60, 'Aing':  4, 'Ho': 0.36667, 'He': 0.47740, 'Ar': 22, 'M': 0.17391},
             6: {'ns_site':  62, 'Aing':  6, 'Ho': 0.80645, 'He': 0.80592, 'Ar': 10, 'M': 0.54545},
             7: {'ns_site':  62, 'Aing':  5, 'Ho': 0.67742, 'He': 0.72343, 'Ar':  5, 'M': 0.83333},
             8: {'ns_site':  62, 'Aing':  5, 'Ho': 0.45161, 'He': 0.68059, 'Ar': 10, 'M': 0.45455},
             9: {'ns_site':  62, 'Aing': 10, 'Ho': 0.74194, 'He': 0.82126, 'Ar': 19, 'M': 0.50000},
            10: {'ns_site':  62, 'Aing':  3, 'Ho': 0.38710, 'He': 0.35801, 'Ar':  8, 'M': 0.33333},
            11: {'ns_site':  62, 'Aing': 10, 'Ho': 0.80645, 'He': 0.78741, 'Ar': 21, 'M': 0.45455},
            12: {'ns_site':  62, 'Aing': 11, 'Ho': 0.87097, 'He': 0.82972, 'Ar': 20, 'M': 0.52381},
            13: {'ns_site':  60, 'Aing':  7, 'Ho': 0.73333, 'He': 0.67458, 'Ar': 12, 'M': 0.53846},
            14: {'ns_site':  58, 'Aing': 11, 'Ho': 0.86207, 'He': 0.83061, 'Ar': 37, 'M': 0.28947}},

          {
             1: {'ns_site': 174, 'Aing':  8, 'Ho': 0.80460, 'He': 0.75709, 'Ar': 19, 'M': 0.40000},
             2: {'ns_site': 174, 'Aing': 12, 'Ho': 0.83908, 'He': 0.82367, 'Ar': 28, 'M': 0.41379},
             3: {'ns_site': 174, 'Aing':  8, 'Ho': 0.87356, 'He': 0.83842, 'Ar': 16, 'M': 0.47059},
             4: {'ns_site': 174, 'Aing':  8, 'Ho': 0.74713, 'He': 0.72905, 'Ar': 21, 'M': 0.36364},
             5: {'ns_site': 170, 'Aing':  8, 'Ho': 0.77647, 'He': 0.72725, 'Ar': 34, 'M': 0.22857},
             6: {'ns_site': 174, 'Aing':  9, 'Ho': 0.73563, 'He': 0.84891, 'Ar': 17, 'M': 0.50000},
             7: {'ns_site': 174, 'Aing':  8, 'Ho': 0.77011, 'He': 0.82945, 'Ar': 15, 'M': 0.50000},
             8: {'ns_site': 174, 'Aing':  7, 'Ho': 0.87356, 'He': 0.82327, 'Ar': 11, 'M': 0.58333},
             9: {'ns_site': 174, 'Aing': 12, 'Ho': 0.89655, 'He': 0.85875, 'Ar': 29, 'M': 0.40000},
            10: {'ns_site': 172, 'Aing':  5, 'Ho': 0.73256, 'He': 0.70345, 'Ar':  8, 'M': 0.55556},
            11: {'ns_site': 172, 'Aing': 11, 'Ho': 0.86047, 'He': 0.79621, 'Ar': 33, 'M': 0.32353},
            12: {'ns_site': 172, 'Aing': 12, 'Ho': 0.87209, 'He': 0.83075, 'Ar': 21, 'M': 0.54545},
            13: {'ns_site': 168, 'Aing': 10, 'Ho': 0.80952, 'He': 0.82542, 'Ar': 20, 'M': 0.47619},
            14: {'ns_site': 162, 'Aing': 21, 'Ho': 0.61728, 'He': 0.93298, 'Ar': 45, 'M': 0.45652}}]

        # import data to an Align object
        names = []
        seqs = []
        groups = []
        accj = 0
        acck = 0
        for i, array in enumerate([orientalis, sylvatica, progeny]):
            for j, genos in enumerate(array):
                if list(zip(*genos)).count((0,0)) > 3: continue
                for k, geno in enumerate(genos):
                    names.append('pop_{0}_indiv_{1}_geno{2}'.format(i+1, j+1, k+1))
                    seqs.append(geno)
                    groups.append(list(map(str, [i, accj, acck])))
                    acck += 1
                accj += 1
        aln = egglib.Align.create(list(zip(names, seqs, groups)), alphabet=egglib.alphabets.Alphabet('range', [1,999], [0, 1]))
        struct = egglib.struct_from_labels(aln, lvl_pop=0, lvl_indiv=1)
        cs = egglib.stats.ComputeStats()
        cs.add_stats('Aing', 'He', 'Ho', 'ns_site', 'Ar', 'M')

        # test Arlequin statistics
        for idx, pop_stats in enumerate(arlequin_stats):
            pop_struct = egglib.struct_from_dict({None: {None: struct.as_dict()[0][None][str(idx)]}}, None)
            cs.configure(struct=pop_struct, multi_hits=True)
            for i in range(aln.ls):
                site = egglib.site_from_align(aln, i)
                stats = cs.process_site(site)
                if i+1 in pop_stats:
                    for k in stats:
                        ref = round(pop_stats[i+1][k], 5)
                        calc = round(stats[k], 5)
                        self.assertEqual(calc, ref, msg='pop={0} locus={1} stats={2} arlequin={3} egglib={4}'.format(idx+1, i+1, k, ref, calc))

        # compute by hand reference statistics for whole sample
        structd = struct.as_dict()[0][None]
        ds = len(structd)
        pops = []
        for i in range(ds):
            pops.append([])
            for k, (i1, i2) in structd[str(i)].items():
                pops[i].append(i1)
                pops[i].append(i2)

        ref_stats = {}
        for idx in range(aln.ls):
            site = egglib.site_from_align(aln, idx)
            site = site.as_list()
            Sw = 0.0
            ntot = 0

            Stot = 0.0
            n = 0
            all_pops = [i for pop in pops for i in pop]
            for i in range(len(all_pops)):
                for j in range(i+1, len(all_pops)):
                    a1 = site[all_pops[i]]
                    a2 = site[all_pops[j]]
                    if a1!=0 and a2!=0:
                        n += 1
                        Stot += (a1-a2)**2
            Stot /= n

            for j in range(ds):
                accW = 0.0
                n = 0
                for i,x in enumerate(pops[j]):
                    if site[x] == 0: continue
                    ntot += 1
                    for xx in pops[j][i+1:]:
                        if site[xx] == 0: continue
                        accW += (site[x] - site[xx]) ** 2
                        n += 1
                Sw += accW / n
            Sw /= ds

            Rst = (Stot - Sw) / Stot

            site = [site[i] for pop in pops for i in pop]
            while 0 in site: site.remove(0)
            k = len(set(site))
            Ar = max(site) - min(site)
            M = k / (Ar + 1.0)

            m = 0.0
            n = 0
            for i in range(ntot):
                m += site[i]
                n += 1
            m /= n
            V = 0.0
            for i in range(ntot):
                if site[i] != 0:
                    V += (site[i] - m) ** 2
            V /= (n-1)

            ref_stats[idx] = {'Aing': k,  'Ar': Ar, 'M': M, 'V': V, 'Rst': Rst, 'Stot': Stot, 'Sw': Sw}

        average = {'Aing': 0.0,  'Ar': 0.0, 'M': 0.0, 'V': 0.0, 'Stot': 0.0, 'Sw': 0.0}

        for k in average:
            average[k] = 1.0 * sum([i[k] for i in ref_stats.values()])
            if k not in ['Stot', 'Sw']: average[k]/= aln.ls

        average['Rst'] = (average['Stot'] - average['Sw']) / average['Stot']
        del average['Stot']
        del average['Sw']

        # check match per site
        cs.reset()
        cs.configure(struct=struct)
        cs.add_stats('V', 'Rst')
        for idx in range(aln.ls):
            site = egglib.site_from_align(aln, idx)
            stats = cs.process_site(site)
            for k, v in ref_stats[idx].items():
                if k not in ['Stot', 'Sw']:
                    self.assertEqual(round(v, 5), round(stats[k], 5), msg='locus {0} stats {1} = {2} (ref: {3})'.format(idx+1, k, stats[k], v))

        # also check match for average
        stats = cs.results()
        for k, v in average.items():
            assert round(v, 5) == round(stats[k], 5), 'average stats {0} = {1} (ref: {2})'.format(k, stats[k], v)

    def test_diff_stats(self):
        """ test cases where there are populations with <2 samples """

        # simulate an alignment with 6 populations including 2 with only one sample
        chrom = [10, 12, 1, 10, 1, 8]
        indiv = [0, 0, 0, 0, 0, 0]
        coal = egglib.coalesce.Simulator(num_pop=6, num_chrom=chrom, num_indiv=indiv, theta=2.0, migr=1.0, num_sites=1, mut_model='IAM')
        aln1 = coal.simul()

        # introduce missing data
        num_miss = 0
        alph = egglib.alphabets.Alphabet('range', (0, None), (-1, 0))
        aln1 = egglib.Align.create(list(aln1), alphabet=alph)
        for i in range(0, aln1.ns, 2):
            if random.random() < 0.2:
                num_miss += 1
                aln1.set(i+random.randint(0, 1), 0, -1)

        # add cluster labels
        for sam in aln1:
            if int(sam.labels[0]) < 3: sam.labels.append('1')
            else: sam.labels.append('2')

        # make a copy of the alignment with the 1-sample populations
        samples = list(aln1)
        del samples[22]
        del samples[32]
        aln2 = egglib.Align.create(samples, alphabet=aln1.alphabet)

        # get structures
        str1a = egglib.struct_from_labels(aln1, lvl_clust=2, lvl_pop=0, lvl_indiv=1)
        str2 = egglib.struct_from_labels(aln2, lvl_clust=2, lvl_pop=0, lvl_indiv=1)
        str1b = str1a.as_dict()[0]
        del str1b['1']['2']
        del str1b['2']['4']
        str1b = egglib.struct_from_dict(str1b, None)

        # compute stats
        list_stats = ['Dj', 'FstH', 'Kst', 'Snn', 'Hst', 'Gst', 'Gste', 'Rst', 'FstWC', 'FistWC', 'FisctWC']
        cs = egglib.stats.ComputeStats()
        cs.add_stats(* list_stats)
        cs.configure(struct=str1a, multi_hits=True)
        stats1a = cs.process_align(aln1, max_missing=0.999)
        cs.configure(struct=str1b, multi_hits=True)
        stats1b = cs.process_align(aln1, max_missing=0.999)
        cs.configure(struct=str2, multi_hits=True)
        stats2 = cs.process_align(aln2, max_missing=0.999)
        for stats in stats1a, stats1b, stats2:
            self.assertIsNone(stats['FistWC'])
            del stats['FistWC']
            self.assertIsNone(stats['FisctWC'])
            del stats['FisctWC']
        del list_stats[-2:]
        for k in list_stats:
            self.assertTrue(abs(stats1a[k] - stats1b[k]) + abs(stats1a[k] - stats2[k]) < 0.0000001)

    def test_Fs(self):
        """ test that Fs is None when it should be """
        cs = egglib.stats.ComputeStats()
        cs.add_stats('Fs', 'Pi', 'Ki')
        coal = egglib.coalesce.Simulator(num_pop=1, num_chrom=[20], num_mut=15)

        aln = coal.simul()
        self.assertEqual(aln.ns, 20)
        self.assertEqual(aln.ls, 15)
        self.assertNotIn(None, cs.process_align(aln).values())

        coal.params['num_chrom'] = [2]
        aln = coal.simul()
        self.assertEqual(aln.ns, 2)
        self.assertEqual(aln.ls, 15)
        self.assertNotIn(None, cs.process_align(aln).values())

        aln = egglib.Align.create(list(aln)[:1], alphabet=aln.alphabet)
        self.assertEqual(aln.ns, 1)
        self.assertEqual(aln.ls, 15)
        stats = cs.process_align(aln)
        self.assertIsNone(stats['Fs'])
        self.assertIsNone(stats['Pi'])
        self.assertIsNone(stats['Ki'])

    def test_subpop(self):
        aln = egglib.Align.create(
            [('name1', 'AANAANAAAN', ['0', '0']),
             ('name1', 'AANAAGAAGN', ['0', '0']),
             ('name1', 'NNACAAAAAN', ['1', '1']),
             ('name1', 'ACACAGATAN', ['1', '1']),
             ('name1', 'AAACAAATAN', ['1', '2']),
             ('name1', 'AAACAAATAN', ['1', '2']),
             ('name1', 'AANCAAAAAA', ['0', '3']),
             ('name1', 'AANCAAAAAA', ['0', '3']),
             ('name1', 'AAAAAGATAA', ['1', '4']),
             ('name1', 'AAAAAAAAAC', ['1', '4']),
             ('name1', 'AANAAAAAAC', ['0', '5']),
             ('name1', 'AANAAAAAAC', ['0', '5'])],
            alphabet=egglib.alphabets.DNA)

        struct = egglib.struct_from_dict(
            {None: {'p1': {'i0': [2, 3], 'i1': [4, 5], 'i2': [8, 9]}}}, None)

        cs = egglib.stats.ComputeStats(struct=struct)
        cs.add_stats('lseff', 'S', 'nseff')
        stats1 = cs.process_align(aln)
        stats2 = cs.process_align(aln, max_missing=0.2)
        stats3 = cs.process_align(aln, max_missing=0.99)
        self.assertEqual(stats1['lseff'], 7)
        self.assertEqual(stats1['S'], 3)
        self.assertEqual(stats2['lseff'], 9)
        self.assertEqual(stats2['S'], 4)
        self.assertEqual(stats3['lseff'], 10)
        self.assertEqual(stats3['S'], 5)

    def test_alphabet_V(self):
        # testing that int/range alphabet are used for computing V
        data1 = [
            ('sample 01', ( 1,  1,  5,  3,  4)),
            ('sample 02', ( 1,  2,  5,  3,  2)),
            ('sample 03', ( 1,  2,  5,  2,  5)),
            ('sample 04', ( 2,  2,  1,  2,  5)),
            ('sample 05', ( 2,  2,  3,  2,  1)),
            ('sample 06', ( 2,  2,  3,  2,  1)),
            ('sample 07', ( 3,  3,  1,  2,  3)),
            ('sample 08', ( 3,  3,  2,  1,  3)),
            ('sample 09', ( 3,  1,  1,  1,  4)),
            ('sample 10', ( 4,  1,  2,  1,  6))]
        aln1 = egglib.Align.create(data1, alphabet=egglib.alphabets.positive_infinite)
        aln2 = egglib.Align.create(data1, egglib.alphabets.Alphabet('int', [1,2,3,4,5,6], []))
        data3 = [
            ('sample 01', 'AACCAG'),
            ('sample 02', 'AGATAG'),
            ('sample 03', 'AGCCAG'),
            ('sample 04', 'AAGCAG'),
            ('sample 05', 'TAGCCC'),
            ('sample 06', 'TAGTCC'),
            ('sample 07', 'TCCTGC'),
            ('sample 08', 'TCCTGC'),
            ('sample 09', 'TCTCGC'),
            ('sample 10', 'TCTCGC')]
        aln3 = egglib.Align.create(data3, alphabet=egglib.alphabets.DNA)
        cs = egglib.stats.ComputeStats(multi_hits=True)
        cs.add_stats('V')
        self.assertDictEqual(cs.process_align(aln1), cs.process_align(aln2))
        with self.assertRaisesRegex(ValueError, 'cannot compute V, Ar, M, and Rst with this alphabet'):
            cs.process_align(aln3)
        cs.all_stats()
        self.assertDictEqual(cs.process_align(aln1), cs.process_align(aln2))

        cs.clear_stats()
        cs.add_stats('Rst')
        with self.assertRaisesRegex(ValueError, 'cannot compute V, Ar, M, and Rst with this alphabet'):
            cs.process_align(aln3)

        stats = [i for (i, j) in cs.list_stats()]
        stats.remove('V')
        stats.remove('Ar')
        stats.remove('M')
        stats.remove('Rst')
        cs.clear_stats()
        cs.add_stats(*stats)
        cs.process_align(aln3)

    def test_sites(self):
        data1 = [
            ("sam1", 'ACCGTAGGGCCGGCTTGAGTMTGCCGGCCGAAGAAACGAACCGCGGTTTTTTGGGTCCAATTGNGCCGGAGAA', ['otg']),
            ("sam2", 'ACCGTCGGGCCGGCCAGAGTTTGCCGGCCGAAGAAAGGAACCGCGGTATTTTGGG?CCAATTGTGCCGGAGAA', ['pop1']),
            ("sam3", 'ACCGTCGGGCCGGCCAGAGTTTGCCGGCCGAAGAAAGGAACCGCGGTTTTTTGGGTCCAATTGTGCCGGAGAA', ['pop1']),
            ("sam4", 'ACCGTCGGGCCGGCCAGAGT-TGCCGCCCGAAGAAAGGAACCGCGGTTTTTTGGGCCCAATTGTGCCGGAGAA', ['pop1']),
            ("sam5", 'ACCGTCGGGCCGGCCAGAGT-TGCCGCCCGAAGAAAGGAACCGCGGTTTTTTGGGCCCAATTGTGCCGGAGAA', ['pop1']),
            ("sam6", 'ACCGTGGGGCCGGCCAGAGT-TGCCGGCCGAAGAAATGAACCGCGGTTTTTTGGGCCCAATTGTGCCGGAGAA', ['pop2']),
            ("sam7", 'ACCGTGGGGCCG-CCAGAGTCTGCCGGCCGAAGAAATGAACCGCGGTATTTTGGGTCCAATTGTGCCGGAGAA', ['pop2']),
            ("sam8", 'ACCGTTGGGCCGGCC-GAGTCTGCCGGCCGAAGAAATGAACCGCGGTATTTTGGGTCCAATTGTGCCGGAGAA', ['pop2']),
            ("sam9", 'ACCGTTGGGCCGGCC-GAGTCTGCCGGCCGAAGAAA-GAACCGCGGTATTTTGGGGCCAATTGCGCCGGAGAA', ['pop2'])
        ]

        aln = egglib.Align.create(data1, alphabet=egglib.alphabets.DNA)
        struct = egglib.struct_from_labels(aln, lvl_pop=0, outgroup_label='otg')
        cs = egglib.stats.ComputeStats(struct=struct)
        cs.add_stats('S', 'nall', 'frq', 'frqp')
        self.assertEqual(cs.process_align(aln, max_missing=0),
            {'S': 3,
             'nall': [2, 2, 2],
             'frq':  [[6, 2], [4, 4], [7, 1]],
             'frqp': [[[2,4], [2,0]],
                      [[1,3], [3,1]],
                      [[4,3], [0,1]]]
            })
        self.assertEqual(cs.process_align(aln, max_missing=0.4),
            {'S': 5,
             'nall': [2, 2, 2, 2, 2],
             'frq':  [[2, 3], [6, 2], [4, 3], [4, 4], [7, 1]],
             'frqp': [[[2,0], [0,3]],
                      [[2,4], [2,0]],
                      [[4,0], [0,3]],
                      [[1,3], [3,1]],
                      [[4,3], [0,1]]]
            })
        cs.configure(multi_hits=True, struct=struct)
        self.assertEqual(cs.process_align(aln, max_missing=0),
            {'S': 4,
             'nall': [3, 2, 2, 2],
             'frq':  [[4, 2, 2], [6, 2], [4, 4], [7, 1]],
             'frqp': [[[4,0], [0,2], [0,2]],
                      [[2,4], [2,0]],
                      [[1,3], [3,1]],
                      [[4,3], [0,1]]]
            })
        self.assertEqual(cs.process_align(aln, max_missing=0.4),
            {'S': 7,
             'nall': [3, 2, 2, 2, 2, 3, 2],
             'frq':  [[4, 2, 2], [2, 3], [6, 2], [4, 3], [4, 4], [3, 3, 1], [7, 1]],
             'frqp': [[[4,0], [0,2], [0,2]],
                      [[2,0], [0,3]],
                      [[2,4], [2,0]],
                      [[4,0], [0,3]],
                      [[1,3], [3,1]],
                      [[1,2], [2,1], [0,1]],
                      [[4,3], [0,1]]]
            })

    def test_defaults(self):

        ##### structure #####

        struct1 = {}
        struct2 = {None: {}}
        struct3 = {None: {None: {}}}
        c = 0
        for C in 'AB':
            struct1[C] = {}
            struct2[None][C] = {}
            for p in range(2):
                P = f'{C}{p+1}'
                struct1[C][P] = {}
                for i in range(5):
                    I = f'{C}{p+1}i{i+1}'
                    struct1[C][P][I] = (c, c + 1)
                    struct2[None][C][I] = (c, c + 1)
                    struct3[None][None][I] = (c, c + 1)
                    c += 2
        structo = {'O': (c, c +1)}
        struct1 = egglib.struct_from_dict(struct1, structo)
        struct2 = egglib.struct_from_dict(struct2, structo)
        struct3 = egglib.struct_from_dict(struct3, structo)

        ##### function to generate an alignment #####

        alph = egglib.Alphabet(cat='range', expl=[1, 10], miss=[0, 1])

        def mk_align(ds, alph=alph):
            return egglib.Align.create([('', seq) for seq in ds], alphabet=alph)

        ds_empty = [[] for _ in range(42) ]

        ds_missing = [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], 
                      [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], 
                      [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], 
                      [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], 
                      [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], 
                      [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], 
                      [0, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], 
                      [0, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], 
                      [1, 0, 0], [1, 1, 1], [1, 1, 1], [1, 1, 1], 
                      [1, 0, 0], [1, 1, 1], [1, 1, 1], [1, 1, 1], 
                      [1, 1, 1], [1, 1, 1]]

        ds_no_outgroup = [[1, 1, 2, 6, 6],
                          [1, 1, 2, 6, 6],
                          [1, 1, 2, 5, 6],
                          [1, 1, 2, 5, 6],
                          [1, 1, 2, 5, 6],
                          [1, 1, 2, 5, 6],
                          [1, 5, 2, 6, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 2, 6, 6],
                          [1, 5, 2, 6, 6],
                          [1, 5, 2, 6, 6],
                          [1, 5, 2, 6, 6],
                          [2, 5, 4, 6, 6],
                          [2, 5, 4, 6, 6],
                          [2, 5, 2, 6, 3],
                          [2, 5, 2, 6, 3],
                          [2, 5, 2, 5, 3],
                          [2, 5, 2, 5, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 4, 6, 6],
                          [1, 5, 4, 6, 6],
                          [1, 5, 2, 5, 3],
                          [1, 5, 2, 5, 3],
                          [1, 5, 2, 5, 3],
                          [1, 5, 2, 5, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 2, 6, 3],
                          [1, 5, 4, 6, 3],
                          [1, 5, 4, 6, 3],
                          [0, 0, 0, 0, 0],
                          [0, 0, 0, 0, 0]]

        ds_dna = ['AAAAATCG', 'AAAAATCG', 'AAAAATCG', 'AAAAATCG', 'AAAAATCG',
                  'AAAAATCG', 'AAAAATCG', 'AAAAATCG', 'AAAAATCG', 'AAAAATCG',
                  'AAAAATCG', 'AAAAATCG', 'AAAAATCG', 'AATAACCG', 'AATAACCG',
                  'AATAACCG', 'AATAACCG', 'AATAACCG', 'AATAACCG', 'AATAACCG',
                  'AATAACCG', 'AATAACCG', 'AATAATCG', 'AATAATCG', 'AATAATCG',
                  'AATAATCG', 'AATAATCG', 'AATAATCG', 'AATAATCG', 'AATAATCG',
                  'AATAATCG', 'AATAATCG', 'AATAATCG', 'AATAATCG', 'AATAATCG',
                  'AATAATCG', 'AATAATCG', 'AATAATCG', 'AATAATCG', 'AATAATCG',
                  'AAAAAAAA', 'AAAAAAAA']

        ds_no_pol = [[1] * 10 for _ in range(42)]

        ds_one_pol = [[1] * 10 for _ in range(42)]
        for i in range(0, 40, 3):
            ds_one_pol[i][4] = 2

        ds_all_diff = [[1],[2],[3],[4],[5],[6],[7],[8],[9]]

        ##### stats computer #####

        cs = egglib.stats.ComputeStats(struct=struct1)
        cs.all_stats()

        ##### empty dataset / dataset without exploitable data #####

        for ds in ds_empty, ds_missing:
            stats = cs.process_align(mk_align(ds))
            for k, v in stats.items():
                if k in ['lseff', 'lseffo', 'nPairs', 'nPairsAdj', 'RminL']: self.assertEqual(v, 0)
                elif k == 'triconfig': self.assertEqual(v, [0]*13)
                else: self.assertIsNone(v)

        ##### no exploitable data in outgroup #####

        stats = cs.process_align(mk_align(ds_no_outgroup))
        for k, v in stats.items():
            if k in ['lseffo', 'ns_site_o']: self.assertEqual(v, 0)
            elif k in [ 'Aotg', 'Asd', 'numSpd', 'numSpd*',
                        'nseffo', 'nsmaxo', 'sites_o', 'singl_o',
                        'So', 'Sso', 'nsingld', 'etao', 'Dfl', 'F', 'nM', 'pM',
                        'thetaPi', 'thetaH', 'thetaL', 'Hns', 'Hsd', 'E',
                        'R2E', 'R3E', 'R4E', 'ChE',
                        'Da', 'Dxy',
                        'f2', 'f3']: self.assertIsNone(v, k)
            elif k == 'triconfig': self.assertEqual(v, [0]*13)
            else: self.assertIsNotNone(v, k)

        ##### with outgroup #####

        ds_outgroup = ds_no_outgroup[:]
        ds_outgroup[-2] = ds_outgroup[-3]
        ds_outgroup[-1] = ds_outgroup[-3]
        stats = cs.process_align(mk_align(ds_outgroup))
        for k, v in stats.items():
            if k in [ 'Da', 'Dxy', 'f2', 'f3' ]: self.assertIsNone(v, k)
            else: self.assertIsNotNone(v, k)

        ##### no cluster, 2 populations (Da, Dxy, but no Fisct) #####

        cs.configure(struct=struct2)
        stats = cs.process_align(mk_align(ds_outgroup))
        for k, v in stats.items():
            if k in [ 'FisctWC', 'f3', 'f4', 'Dp' ]: self.assertIsNone(v, k)
            else: self.assertIsNotNone(v, k)

        ##### DNA with clusters and > 2 pops #####

        cs.configure(struct=struct1)
        with self.assertRaisesRegex(ValueError, 'cannot compute V, Ar, M, and Rst with this alphabet'):
            stats = cs.process_align(mk_align(ds_dna, alph=egglib.alphabets.DNA))

        #### only triallelic sites ####

        cs.configure(struct=struct1, multi_hits=True)
        ds_triallelic = ds_outgroup[:]
        ds_triallelic[0] = [3, 3, 3, 3, 4]
        stats = cs.process_align(mk_align(ds_triallelic))
        for k, v in stats.items():
            if k == 'RminL': self.assertEqual(v, 0)
            elif k in [ 'Da', 'Dxy', 'f2', 'f3', 'f4', 'Dp',
                      'Rmin', 'Rintervals', 'Za', 'ZZ', 'ZnS', 'Z*nS', 'Z*nS*',
                      'Q', 'B' ]: self.assertIsNone(v, k)
            else: self.assertIsNotNone(v, k)

        cs.configure(struct=struct1, multi_hits=True, LD_multiallelic=1)
        stats = cs.process_align(mk_align(ds_triallelic))
        for k, v in stats.items():
            if k == 'RminL': self.assertEqual(v, 0)
            elif k in [ 'Da', 'Dxy', 'f2', 'f3', 'f4', 'Dp',
                        'Rmin', 'Rintervals', 'Q', 'B']: self.assertIsNone(v, k)
            else: self.assertIsNotNone(v, k)

        ### no polymorphism (2 pops) ###

        cs.configure(struct=struct2)
        stats = cs.process_align(mk_align(ds_no_pol))

        for k, v in stats.items():
            if k in [ 'FisctWC',
                'Fis', 'Hst', 'Gst', 'Gste', 'FstWC', 'FistWC',
                'FstH', 'Kst', 'Snn',
                'D', 'Deta', 'Dfl', 'F', 'D*', 'F*', 'pM', 'Hsd', 'E', 'B', 'Q',
                'Fst', 'Kst', 'Snn', 'rD',
                'R2', 'R2E', 'R3', 'R3E', 'R4', 'R4E', 'Ch', 'ChE',
                'Za', 'ZZ', 'ZnS', 'Z*nS', 'Z*nS*', 'Fs', 'Rst', 'M',
                'numSp', 'numSpd', 'numFxA', 'numFxD', 'numShA', 'numShP',
                'numSp*', 'numSpd*', 'numFxA*', 'numFxD*', 'numShA*', 'numShP*',
                'Rmin', 'Rintervals', 'maf', 'maf_pop', 'Ki', 'Kt', 'f3', 'f4', 'Dp'
                        ]: self.assertIsNone(v, k)
            else: self.assertIsNotNone(v, k) # including Dj

        ### one polymorphism ###

        stats = cs.process_align(mk_align(ds_one_pol))
        for k, v in stats.items():
            if k in [ 'FisctWC', 'f3', 'f4', 'Dp',
                'B', 'Q', 'Rmin', 'Rintervals', 'Za', 'ZZ', 'ZnS', 'Z*nS', 'Z*nS*',
                    'rD', 'pM' ]: self.assertIsNone(v, k)
            else: self.assertIsNotNone(v, k)

        ### no structure ###

        cs.configure(struct=struct3)
        stats = cs.process_align(mk_align(ds_outgroup))
        for k, v in stats.items():
            if k == 'Snn': self.assertEqual(v, 1, k)
            elif k == 'Kst': self.assertAlmostEqual(v, 0)
            elif k in [ 'FisctWC',
                'Da', 'Dxy', 'FstWC', 'FistWC', 'FicstWC', 'FstH',
                'Hst', 'Gst', 'Gste', 'Dj', 'Fst', 'Kst',  'Rst',
                'numSp', 'numSpd', 'numShA', 'numShP', 'numFxA', 'numFxD',
                'numSp*', 'numSpd*', 'numShA*', 'numShP*', 'numFxA*', 'numFxD*',
                'f2', 'f3', 'f4', 'Dp']: self.assertIsNone(v, k)
            else: self.assertIsNotNone(v, k)

        ### He = 1 ###

        cs.configure(multi_hits=True)
        cs.clear_stats()
        cs.add_stats('He', 'thetaIAM', 'thetaSMM', 'Aing')
        stats = cs.process_align(mk_align(ds_all_diff))
        self.assertEqual(stats['Aing'], 9)
        self.assertEqual(stats['He'], 1)
        self.assertIsNone(stats['thetaSMM'])

    def test_fs_with_missing_data(self):
        alph = egglib.Alphabet('int', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [-1])

        def test(sites):
            sites = [egglib.site_from_list(array, alphabet=alph) for array in sites]
            cs = egglib.stats.ComputeStats()
            cs.add_stats('nseff', 'S', 'Ki', 'Fs')
            cs.process_sites(sites)

        # 8 available samples
        #       A   B   A   A   B   C   C   D
        test([[ 0,  0,  0,  0,  0,  1,  1,  1],
              [ 0,  0,  0,  0,  0,  1,  1,  1],
              [ 0,  0,  0,  0,  0,  0,  0,  1],
              [ 0,  1,  0,  0,  1,  1,  1,  1]])

        # 3 available samples
        #       A   B   x   x   B   x   x   x
        test([[ 0,  0,  0,  0,  0, -1, -1,  1],
              [ 0,  0,  0,  0,  0,  1,  1, -1],
              [ 0,  0,  0, -1,  0,  0,  0,  1],
              [ 0,  1, -1,  0,  1,  1,  1,  1]])

        # no available samples
        #       x   x   x   x   x   x   x   x
        test([[-1,  0,  0,  0,  0, -1, -1,  1],
              [ 0,  0,  0,  0,  0,  1,  1, -1],
              [ 0,  0,  0, -1, -1,  0,  0,  1],
              [ 0, -1, -1,  0,  1,  1,  1,  1]])

        # 1 available sample
        #       x   x   x   x   A   x   x   x
        test([[-1,  0,  0,  0,  0, -1, -1,  1],
              [ 0,  0,  0,  0,  0,  1,  1, -1],
              [ 0,  0,  0, -1,  0,  0,  0,  1],
              [ 0, -1, -1,  0,  1,  1,  1,  1]])

    def test_haploid_outgroup(self):
        data = [
            ('', 'AAAAAAAAAA', ['idv01', 'pop1', 'clust1']), # haplotype 0
            ('', 'AAAAAAAAAA', ['idv01', 'pop1', 'clust1']),
            ('', 'AAAAAAAAAA', ['idv02', 'pop1', 'clust1']),
            ('', 'AAAAAAAAAA', ['idv02', 'pop1', 'clust1']),
            ('', 'AAAAAAAAAA', ['idv03', 'pop1', 'clust1']),
            ('', 'AAAAAAAAAA', ['idv03', 'pop1', 'clust1']),
            ('', 'AAACAAACAA', ['idv04', 'pop1', 'clust1']), # haplotype 1
            ('', 'AAACAAACAA', ['idv04', 'pop1', 'clust1']),
            ('', 'AAACAAACAA', ['idv05', 'pop2', 'clust1']),
            ('', 'AAACAAACAA', ['idv05', 'pop2', 'clust1']),
            ('', 'AAAAAAAAAA', ['idv06', 'pop2', 'clust1']),
            ('', 'AAAAAAAAAA', ['idv06', 'pop2', 'clust1']),
            ('', 'AAAAAAAAAA', ['idv07', 'pop2', 'clust1']),
            ('', 'AAAAAAAAAA', ['idv07', 'pop2', 'clust1']),
            ('', 'AAAAAAAAAA', ['idv08', 'pop2', 'clust1']),
            ('', 'AAAAAAAAAA', ['idv08', 'pop2', 'clust1']),
            ('', 'AAAAAAAAAA', ['idv09', 'pop3', 'clust2']),
            ('', 'AAAAAAAAAA', ['idv09', 'pop3', 'clust2']),
            ('', 'AAAAAAAAAA', ['idv10', 'pop3', 'clust2']),
            ('', 'AAAAAAAAAA', ['idv10', 'pop3', 'clust2']),
            ('', 'AAAAAACTGA', ['idv11', 'pop3', 'clust2']), # haplotype 2
            ('', 'AAAAAACTGA', ['idv11', 'pop3', 'clust2']),
            ('', 'AAAAAACTGA', ['idv12', 'pop3', 'clust2']),
            ('', 'AAAAAACTGA', ['idv12', 'pop3', 'clust2']),
            ('', 'AAAAAACTGA', ['idv13', 'pop4', 'clust2']),
            ('', 'AAAAAACTGA', ['idv13', 'pop4', 'clust2']),
            ('', 'AAAAAAAAAA', ['idv14', 'pop4', 'clust2']),
            ('', 'AAAAAAAAAA', ['idv14', 'pop4', 'clust2']),
            ('', 'AAGAATTAAA', ['idv15', 'pop4', 'clust2']), # haplotype 3
            ('', 'AAGAATTAAA', ['idv15', 'pop4', 'clust2']),
            ('', 'AAGAATTAAA', ['idv16', 'pop4', 'clust2']),   # last indiv heterozygote
            ('', 'AAAAAAAAAA', ['idv16', 'pop4', 'clust2']),
            ('', 'AAAAAATCAA', ['#', 'idv17'])]              # outgroupe haplotype 4

        aln = egglib.Align.create(data, egglib.alphabets.DNA)

        # struct with indivs
        struct1 = egglib.struct_from_labels(aln, lvl_indiv=0, lvl_pop=1, lvl_clust=2)
        self.assertEqual(struct1.get_clusters(), ['clust1', 'clust2'])
        self.assertEqual(struct1.get_populations(), ['pop1', 'pop2', 'pop3', 'pop4'])

        cs = egglib.stats.ComputeStats(struct=struct1, multi_hits=True)
        cs.add_stats('nseff', 'lseff', 'lseffo', 'ns_site', 'ns_site_o', 'FstWC', 'FisctWC', 'Ki', 'Kt')
        stats = cs.process_align(aln)
        self.assertEqual(stats['nseff'], 32)
        self.assertEqual(stats['lseff'], aln.ls)
        self.assertEqual(stats['lseffo'], aln.ls)
        self.assertEqual(stats['ns_site'], 32)
        self.assertEqual(stats['ns_site_o'], 1)
        self.assertIsNotNone(stats['FisctWC'])
        self.assertNotIn(None, stats['FisctWC'])
        self.assertIsNotNone(stats['FstWC'])
        self.assertEqual(stats['Ki'], 5) # heterozygote is new haplotype
        self.assertEqual(stats['Kt'], 5) # outgroup is not considered

        # struct without indivs
        struct2 = egglib.struct_from_labels(aln, lvl_pop=1, lvl_clust=2)
        self.assertEqual(struct2.get_clusters(), ['clust1', 'clust2'])
        self.assertEqual(struct2.get_populations(), ['pop1', 'pop2', 'pop3', 'pop4'])

        cs.set_structure(struct2)
        stats = cs.process_align(aln)
        self.assertEqual(stats['nseff'], 32)
        self.assertEqual(stats['lseff'], aln.ls)
        self.assertEqual(stats['lseffo'], aln.ls)
        self.assertEqual(stats['ns_site'], 32)
        self.assertEqual(stats['ns_site_o'], 1)
        self.assertIsNone(stats['FisctWC'])
        self.assertIsNotNone(stats['FstWC'])
        self.assertEqual(stats['Ki'], 4)
        self.assertEqual(stats['Kt'], 5)

    def test_phased(self):
        aln = egglib.Align.create([
            ('idv1/1', 'AAAAAAAAA'), ('idv1/2', 'AAAAAAAAC'),
            ('idv2/1', 'AAAAAAACC'), ('idv2/2', 'AAAAAACCC'),
            ('idv3/1', 'AAAAACCCC'), ('idv3/2', 'AAAACCCCC'),
            ('idv4/1', 'AAACCCCCC'), ('idv4/2', 'AACCCCCCC'),
            ('idv5/1', 'ACCCCCCCC'), ('idv5/2', 'CCCCCCCCC')
            ], egglib.alphabets.DNA)
        struct = egglib.struct_from_samplesizes([5], ploidy=2)
        cs = egglib.stats.ComputeStats(struct=struct)
        cs.add_stats('Ki')
        self.assertEqual(cs.process_align(aln), {'Ki': 5})
        cs.set_structure(None)
        self.assertEqual(cs.process_align(aln), {'Ki': 10})
        cs.configure(struct=struct, phased=True)
        self.assertEqual(cs.process_align(aln), {'Ki': 10})

        data = [                            # phased        unphased
            ('', 'AAAAAAAA', ['idv1', 'pop1']),        # HAP1=AAA      HAP1=AA,AA,AA
            ('', 'AAAAAAAA', ['idv1', 'pop1']),        # HAP1          /
            ('', 'AAAACCAA', ['idv2', 'pop1']),        # HAP2=AAC      HAP2=AA,AA,CC
            ('', 'AAAACCAA', ['idv2', 'pop1']),        # HAP2          /
            ('', 'AAAACCAA', ['idv3', 'pop1']),        # HAP2          HAP2
            ('', 'AAAACCAA', ['idv3', 'pop1']),        # HAP2          /
            ('', 'AAAACCAA', ['idv4', 'pop2']),        # HAP2          HAP3=AT,AA,CC
            ('', 'AATACCAT', ['idv4', 'pop2']),        # HAP3=TAC      /
            ('', 'AATACCAT', ['idv5', 'pop2']),        # HAP3          HAP4=TT,AA,CC
            ('', 'AATACCAT', ['idv5', 'pop2']),        # HAP3          /
            ('', 'AATACCAT', ['idv6', 'pop2']),        # HAP3          HAP5=TT,AC,CC
            ('', 'AATTCCTT', ['idv6', 'pop2'])]        # HAP4=TTC      /

        random.shuffle(data)
        aln1 = egglib.Align.create(data, egglib.alphabets.DNA)
        struct1 = egglib.struct_from_labels(aln1, lvl_pop=1)

        random.shuffle(data)
        aln2 = egglib.Align.create(data, egglib.alphabets.DNA)
        struct2 = egglib.struct_from_labels(aln2, lvl_indiv=0, lvl_pop=1)

        stats_equal = ['Aing', 'S', 'thetaW', 'D', 'Pi', 'Hst', 'Dxy']
        stats_diff = ['Ki', 'R2', 'Q', 'Za', 'Kst', 'Snn']
        stats_diff_never_phased = ['rD']
        stats_with_indivs = ['Fis']

        cs = egglib.stats.ComputeStats()
        cs.add_stats('Ki')
        cs.add_stats(*stats_equal)
        cs.add_stats(*stats_with_indivs)
        cs.add_stats(*stats_diff)
        cs.add_stats(*stats_diff_never_phased)

        cs.set_structure(struct1)
        stats1 = cs.process_align(aln1)

        cs.set_structure(struct2)
        stats2 = cs.process_align(aln2)

        self.assertEqual(stats1['Ki'], 4)
        self.assertEqual(stats2['Ki'], 5)
        for key in stats_equal:
            self.assertIsNotNone(stats1[key])
            self.assertEqual(stats1[key], stats2[key])
        for key in stats_diff + stats_diff_never_phased:
            self.assertIsNotNone(stats1[key])
            self.assertNotEqual(stats1[key], stats2[key])
        for key in stats_with_indivs:
            self.assertIsNone(stats1[key])
            self.assertIsNotNone(stats2[key])

        # with phased option
        cs.configure(struct=struct2, phased=True)
        stats3 = cs.process_align(aln2)
        self.assertEqual(stats3['Ki'], 4)
        for key in stats_equal:
            self.assertAlmostEqual(stats1[key], stats3[key])
        for key in stats_diff:
            self.assertAlmostEqual(stats1[key], stats3[key])
        for key in stats_diff_never_phased:
            self.assertAlmostEqual(stats2[key], stats3[key])
        for key in stats_with_indivs:
            self.assertIsNotNone(stats3[key])

# validate statistics against a list of pre-computed values
class my_file_reader(object):
    def __init__(self, fname):
        self._f = open(fname)
        self._buffer = []

    def readline(self):
        while True:
            line = self._f.readline()
            if line == '': return None
            line = line.split()
            if len(line) == 0: continue
            return line

    def readword(self):
        if len(self._buffer) == 0:
            self._buffer = self._f.readline().split()
        return self._buffer.pop(0)

class Statistics_test(unittest.TestCase):

    def setUp(self):

        f = my_file_reader(str(path / 'stats.txt'))
        self.files = []
        while True:
            line = f.readline()
            if line is None: break
            if line[0][0] == '#': continue
            if len(line) == 2:
                fname, type_ = line
                args = {}
            else:
                fname, type_, args = line
                args = dict([i.split('=') for i in args.split(',')])
            stats = {}
            word = f.readword()
            while True:
                if word == '::': break
                if word[-1] != ':': raise ValueError('expect a stat name: {0}'.format(word))
                key = word[:-1]
                values = []
                flag = False
                while True:
                    word = f.readword()
                    if word[-1] == ':': break
                    obj = re.match('X(\d+)L$', word)
                    if obj is not None:
                        for i in range(int(obj.group(1))):
                            values.append(list(map(float, f.readline())))
                            if len(values[-1]) == 1: values[-1] = values[-1][0]
                        flag = True
                    else:
                        try:
                            v = list(map(int, re.match('\((\d+),(\d+)\)', word).groups()))
                        except AttributeError:
                            if word == 'None': v = None
                            else:
                                try: v = int(word)
                                except ValueError: v = float(word)
                        values.append(v)
                if not flag:
                    if len(values) == 1 and key not in ['Pib']: values = values[0]
                    elif type_ == 'LD': values = list(map(abs, values))
                    elif key in ['singl', 'sites', 'Rintervals', 'sites', 'sites_o']: values.sort()
                stats[key] = values
            self.files.append({'fname': fname, 'type': type_, 'stats': stats})
            self.files[-1]['max_missing'] = 0.0
            self.files[-1]['haplotypes'] = False
            self.files[-1]['multiple'] = False
            self.files[-1]['multiple_hits'] = False
            self.files[-1]['multiple_alleles'] = False
            self.files[-1]['pop_filter'] = None
            self.files[-1]['frame'] = None
            self.files[-1]['consider_stop'] = False
            self.files[-1]['core'] = None
            self.files[-1]['chr'] = None
            self.files[-1]['triconfig_min'] = 2
            self.files[-1]['phased'] = True
            self.files[-1]['EHH_binary'] = True
            self.files[-1]['thr'] = None
            self.files[-1]['thrS'] = None
            self.files[-1]['thrG'] = None
            self.files[-1]['left'] = None
            self.files[-1]['right'] = None
            self.files[-1]['EHH_crop'] = False
            self.files[-1]['NA'] = False
            for k, v in args.items():
                if k == 'max_missing': self.files[-1]['max_missing'] = float(v)
                elif k == 'thr': self.files[-1]['thr'] = float(v)
                elif k == 'thrG': self.files[-1]['thrG'] = float(v)
                elif k == 'thrS': self.files[-1]['thrS'] = float(v)
                elif k == 'left': self.files[-1]['left'] = int(v)
                elif k == 'right': self.files[-1]['right'] = int(v)
                elif k == 'lvl_pop': self.files[-1]['lvl_pop'] = int(v)
                elif k == 'core': self.files[-1]['core'] = int(v) - 1
                elif k == 'chr': self.files[-1]['chr'] = int(v)
                elif k == 'triconfig_min': self.files[-1]['triconfig_min'] = int(v)
                elif k == 'EHH_crop':
                    if v == 'True': self.files[-1]['EHH_crop'] = True
                    elif v == 'False': self.files[-1]['EHH_crop'] = False
                    else: raise ValueError('invalid value for EHH_crop option: {0}'.format(v))
                elif k == 'phased':
                    if v == 'True': self.files[-1]['phased'] = True
                    elif v == 'False': self.files[-1]['phased'] = False
                    else: raise ValueError('invalid value for phased option: {0}'.format(v))
                elif k == 'EHH_binary':
                    if v == 'True': self.files[-1]['EHH_binary'] = True
                    elif v == 'False': self.files[-1]['EHH_binary'] = False
                    else: raise ValueError('invalid value for EHH_binary option: {0}'.format(v))
                elif k == 'haplotypes':
                    if v == 'True': self.files[-1]['haplotypes'] = True
                    elif v == 'False': self.files[-1]['haplotypes'] = False
                    else: raise ValueError('invalid value for haplotypes option: {0}'.format(v))
                elif k == 'multiple':
                    if v == 'True': self.files[-1]['multiple'] = True
                    elif v == 'False': self.files[-1]['multiple'] = False
                    else: raise ValueError('invalid value for multiple option: {0}'.format(v))
                elif k == 'multiple_hits':
                    if v == 'True': self.files[-1]['multiple_hits'] = True
                    elif v == 'False': self.files[-1]['multiple_hits'] = False
                    else: raise ValueError('invalid value for multiple_hits option: {0}'.format(v))
                elif k == 'multiple_alleles':
                    if v == 'True': self.files[-1]['multiple_alleles'] = True
                    elif v == 'False': self.files[-1]['multiple_alleles'] = False
                    else: raise ValueError('invalid value for multiple_alleles option: {0}'.format(v))
                elif k == 'pop_filter':
                    self.files[-1]['pop_filter'] = [i-1 for i in map(int, v.split(';'))]
                elif k == 'frame':
                    self.files[-1]['frame'] = egglib.tools.ReadingFrame([list(map(int, i.split('-'))) for i in v.split(';')])
                elif k == 'consider_stop':
                    if v == 'True': self.files[-1]['consider_stop'] = True
                    elif v == 'False': self.files[-1]['consider_stop'] = False
                    else: raise ValueError('invalid value for consider_stop option: {0}'.format(v))
                elif k == 'NA':
                    if v == 'True': self.files[-1]['NA'] = True
                    elif v == 'False': self.files[-1]['NA'] = False
                    else: raise ValueError('invalid value for NA option: {0}'.format(v))
                else: raise ValueError('unknown option: {0}'.format(k))
        self.longMessage = True

    def runTest(self):
        self._run_test(None)

    def _run_test(self, output):
        cnt = {'OK': 0, '??': 0, 'FAIL': 0}

        for filedata in self.files:
            if filedata['type'] == 'LD':
                statkeys = 'd', 'D', 'Dp', 'r', 'rsq'
                aln = egglib.io.from_fasta(str(path / filedata['fname']), labels=True, alphabet=egglib.alphabets.DNA)
                sites, matrix = egglib.stats.matrix_LD(aln, statkeys)
                stats = {}
                for i in statkeys: stats[i] = []
                for i in range(len(sites)):
                    for j in range(i+1, len(sites)):
                        for k, key in enumerate(statkeys):
                            stats[key].append(abs(round(matrix[j][i][k], 4)))
                for i in stats['d']: assert i.is_integer()
                stats['d'] = list(map(int, stats['d']))

                if output:
                    output.write('-----------------------------------------------------------------------------------------------------\n')
                    output.write('{0[fname]:<18} {0[type]:<10}\n'.format(filedata))
                    output.write('-----------------------------------------------------------------------------------------------------\n')

            elif filedata['type'] == 'Innan':
                aln = egglib.io.from_fasta(str(path / filedata['fname']), labels=True, alphabet=egglib.alphabets.DNA)
                struct_p = egglib.struct_from_labels(aln, lvl_pop = 0)
                struct_i = egglib.struct_from_labels(aln, lvl_pop = 1)
                pp = egglib.stats.paralog_pi(aln, struct_p, struct_i, max_missing=filedata['max_missing'])
                L = struct_p.num_pop
                stats = {
                    'num_tot': pp.num_sites(),
                    'num_pop': [pp.num_sites(i) for i in range(L)],
                    'num_pair': [pp.num_sites(i,j) for i in range(L-1) for j in range(i+1, L)],
                    'Piw': [pp.Piw(i) for i in range(L)],
                    'Pib': [pp.Pib(i, j) for i in range(L-1) for j in range(i+1, L)]
                }

                if output:
                    output.write('-----------------------------------------------------------------------------------------------------\n')
                    output.write('{0[fname]:<18} {0[type]:<10}\n'.format(filedata))
                    output.write('-----------------------------------------------------------------------------------------------------\n')

            elif filedata['type'] == 'codon':
                aln = egglib.io.from_fasta(str(path / filedata['fname']), labels=True, alphabet=egglib.alphabets.DNA)
                aln.to_codons(frame=filedata['frame'])
                cs = egglib.stats.CodingDiversity(aln,
                            max_missing=filedata['max_missing'],
                            skipstop= not filedata['consider_stop'],
                            multiple_alleles=filedata['multiple_alleles'],
                            multiple_hits=filedata['multiple_hits'])
                stats = {}
                for i in ['num_codons_tot', 'num_codons_eff',
                          'num_codons_stop', 'num_pol_NS',
                          'num_pol_S', 'num_multiple_alleles',
                          'num_multiple_hits', 'num_pol_single',
                          'num_sites_S', 'num_sites_NS']:
                    stats[i] = cs.__getattribute__(i)

                if output:
                    output.write('-----------------------------------------------------------------------------------------------------\n')
                    output.write('{0[fname]:<18} {0[type]:<10} missing:{0[max_missing]} stop:{0[consider_stop]} mhits:{0[multiple_alleles]} mall:{0[multiple_hits]}\n'.format(filedata))
                    output.write('-----------------------------------------------------------------------------------------------------\n')

            elif filedata['type'] == 'EHH':
                idx = []
                sites = []

                f = open(str(path / filedata['fname']) + '.hap')
                for line in f:
                    line = [int(i) if i != 'N' else -1 for i in line.split()]
                    idx.append(line[0] - 1)
                    sites.append(line[1:])
                f.close()
                assert idx == list(range(len(idx)))
                sites = [egglib.site_from_list(site, alphabet=INT) for site in zip(*sites)]

                if filedata['left'] is None and filedata['right'] is None:
                    filedata['left'] = 0
                    filedata['right'] = len(sites) - 1

                info = []
                f = open(str(path / filedata['fname']) + '.inp')
                for line in f:
                    name, ch, pos, all1, all2 = line.split()
                    ch = int(ch)
                    pos = float(pos) - 1
                    if ch == filedata['chr']: info.append((name, pos))
                f.close()
                assert len(sites) == len(info)

                core = filedata['core']
                struct = 0 if filedata['phased'] else 2

                for site, (name, pos) in zip(sites, info):
                    site.position = pos

                # compute EHH/EHHS
                num = set(map(len, 
                    [v for (k,v) in filedata['stats'].items()
                        if k in ['EHH', 'EHHc', 'EHHS'] or re.match('EHHc?\d$', k) != None]))
                if filedata['phased']:
                    assert len(num) == 1
                    num = num.pop()
                    assert num == filedata['left'] + filedata['right'] + 1
                    del num
                EHH = egglib.stats.EHH()
                EHH.set_core(sites[core], struct=struct, EHH_thr=filedata['thr'], EHHc_thr=filedata['thr'], EHHS_thr=filedata['thrS'], EHHG_thr=filedata['thrG'], crop_EHHS=filedata['EHH_crop'])

                kcore =  EHH.num_haplotypes
                stats = {}
                stats['EHHS'] = []
                stats['EHHG'] = []
                stats['iEG'] = []
                stats['Kcore'] = kcore
                stats['Kcur'] = []
                stats['nsam'] = EHH.nsam
                stats['ncur'] = []
                if filedata['EHH_binary']:
                    frq = egglib.freq_from_site(sites[core])
                    alleles = [frq.allele(i) for i in range(frq.num_alleles)]
                    assert kcore == 2 and sorted(alleles) == [1, 2]
                    der = alleles.index(2)
                    stats['frq'] = 1.0 * EHH.nsam_core(der) / EHH.nsam
                    stats['EHH'] = []
                    stats['EHHc'] = []
                    stats['rEHH'] = []
                else:
                    stats['frq'] = [1.0 * EHH.nsam_hap(i) / EHH.nsam for i in range(kcore)]
                    for i in range(kcore):
                        stats['EHH{0}'.format(i+1)] = []
                        stats['EHHc{0}'.format(i+1)] = []
                        stats['rEHH{0}'.format(i+1)] = []
                stats['num'] = [EHH.nsam_core(i) for i in range(kcore)]

                for i in range(filedata['right']+1):
                    EHH.load_distant(sites[core+i])
                    if filedata['EHH_binary']:
                        stats['EHH'].append(EHH.get_EHH(der))
                        stats['EHHc'].append(EHH.get_EHHc(der))
                        stats['rEHH'].append(EHH.get_rEHH(der))
                    else:
                        for j in range(kcore):
                            stats['EHH{0}'.format(j+1)].append(EHH.get_EHH(j))
                            stats['EHHc{0}'.format(j+1)].append(EHH.get_EHHc(j))
                            stats['rEHH{0}'.format(j+1)].append(EHH.get_rEHH(j))
                    stats['EHHS'].append(EHH.get_EHHS())
                    stats['EHHG'].append(EHH.get_EHHG())
                    stats['ncur'].append(EHH.nsam)
                    stats['Kcur'].append(EHH.cur_haplotypes)
                stats['davg'] = EHH.get_dEHH_mean()
                stats['dmax'] = EHH.get_dEHH_max()
                stats['decay'] = [EHH.get_dEHH(i) for i in range(kcore)]
                stats['decayS'] = EHH.get_dEHHS()
                stats['decayG'] = EHH.get_dEHHG()
                stats['iEG'].append(EHH.get_iEG())

                # left side
                EHH.set_core(sites[core], struct=struct, EHH_thr=filedata['thr'], EHHc_thr=filedata['thr'], EHHS_thr=filedata['thrS'], EHHG_thr=filedata['thrG'], crop_EHHS=filedata['EHH_crop'])
                for i in range(filedata['left']):
                    EHH.load_distant(sites[core-1-i])
                    if filedata['EHH_binary']:
                        stats['EHH'].insert(0, EHH.get_EHH(der))
                        stats['EHHc'].insert(0, EHH.get_EHHc(der))
                    stats['EHHS'].insert(0, EHH.get_EHHS())

                EHH.set_core(sites[core], struct=struct, EHH_thr=filedata['thr'], EHHc_thr=filedata['thr'], EHHS_thr=filedata['thrS'], EHHG_thr=filedata['thrG'], crop_EHHS=filedata['EHH_crop'])
                i = core
                while i < len(sites):
                    EHH.load_distant(sites[i])
                    i += 1
                stats['iHH'] = [EHH.get_iHH(i) for i in range(stats['Kcore'])]
                stats['iHHc'] = [EHH.get_iHHc(i) for i in range(stats['Kcore'])]
                stats['iHS'] = [EHH.get_iHS(i) for i in range(stats['Kcore'])]
                stats['iES'] = EHH.get_iES()
                stats['iEG'] = EHH.get_iEG()

                EHH.set_core(sites[core], struct=struct, EHH_thr=filedata['thr'], EHHc_thr=filedata['thr'], EHHS_thr=filedata['thrS'], EHHG_thr=filedata['thrG'], crop_EHHS=filedata['EHH_crop'])
                i = core
                while i > 0:
                    EHH.load_distant(sites[i])
                    i -= 1
                for i in range(stats['Kcore']): stats['iHH'][i] += EHH.get_iHH(i)
                stats['iES'] += EHH.get_iES()
                stats['iEG'] += EHH.get_iEG()

                if output:
                    output.write('-----------------------------------------------------------------------------------------------------\n')
                    output.write('{0[fname]:<18} {0[type]:<10} chr:{0[chr]} core:{0[core]} phased:{0[phased]} binary:{0[EHH_binary]} thr:{0[thr]}\n'.format(filedata))
                    output.write('-----------------------------------------------------------------------------------------------------\n')

            else:
                cs = egglib.stats.ComputeStats()
                for k in filedata['stats']:
                    if k != 'ls' and k != 'ns': cs.add_stats(k)
                if output:
                    output.write('-----------------------------------------------------------------------------------------------------\n')
                    output.write('{0[fname]:<18} {0[type]:<10} hapl: {0[haplotypes]:<2} max_missing: {0[max_missing]} multiple: {0[multiple]}\n'.format(filedata))
                    output.write('-----------------------------------------------------------------------------------------------------\n')

                if filedata['type'] == 'Align':
                    cs.add_stats('lseff', 'nseff')
                    aln = egglib.io.from_fasta(str(path / filedata['fname']), labels=True, alphabet=egglib.alphabets.DNA)
                    if 'lvl_pop' in filedata:
                        struct = egglib.struct_from_labels(aln, lvl_pop=filedata['lvl_pop'])
                        if filedata['pop_filter'] is not None:
                            clust, otg = struct.as_dict()
                            assert len(clust) == 1
                            pops = clust[None]
                            pops2 = {}
                            for k in filedata['pop_filter']:
                                k = str(k)
                                pops2[k] = pops[k]
                            struct = egglib.struct_from_dict({None: pops2}, otg)
                    else:
                        struct = egglib.struct_from_labels(aln)
                    if filedata['haplotypes']:
                        hapls = egglib.stats.haplotypes_from_align(aln, struct=struct, max_missing=filedata['max_missing'], multiple=filedata['multiple'])
                        cs.configure(multi_hits=filedata['multiple'], struct=struct.make_auxiliary(), triconfig_min=filedata['triconfig_min'])
                        stats = cs.process_site(hapls)
                    else:
                        cs.configure(multi_hits=filedata['multiple'], struct=struct, triconfig_min=filedata['triconfig_min'])
                        stats = cs.process_align(aln, max_missing=filedata['max_missing'])
                    if 'ns' in filedata['stats']: stats['ns'] = aln.ns
                    if 'ls' in filedata['stats']: stats['ls'] = aln.ls

                elif filedata['type'] == 'Site':
                    ing = []
                    otg = []
                    ns = []
                    no = 0
                    if ':' in filedata['fname']:
                        fname, lineno = filedata['fname'].split(':')
                        lineno = int(lineno) - 1
                    else:
                        fname = filedata['fname']
                        lineno = 0
                    f = open(str(path / fname))
                    lines = f.readlines()
                    line = lines[lineno]
                    pl = set()
                    for pop in line.split():
                        if pop[0] == '#':
                            outgroup = True
                            pop = pop[1:]
                        else:
                            outgroup = False
                            ns.append(0)
                        for idv in pop.split(','):
                            idv = list(map(int, idv.split('/')))
                            pl.add(len(idv))
                            if outgroup:
                                otg.extend(idv)
                                no += 1
                            else: ing.extend(idv)
                            if not outgroup: ns[-1] += 1
                    site = egglib.site_from_list(ing+otg, alphabet=INT)
                    assert len(pl) == 1
                    pl = pl.pop()
                    structdict = {None: {}}
                    c = 0
                    idx = 0
                    for i, n in enumerate(ns):
                        structdict[None][str(i+1)] = {}
                        for j in range(n):
                            structdict[None][str(i+1)][str(c)] = [idx + k for k in range(pl)]
                            idx += pl
                            c += 1
                    structout = {}
                    for i in range(no):
                        structout[str(c+i)] = [idx + k for k in range(pl)]
                        idx += pl
                    struct = egglib.struct_from_dict(structdict, structout)
                    cs.set_structure(struct)
                    stats = cs.process_site(site)

                elif filedata['type'] == 'GenePop':
                    sites, ns, pl = get_genepop(filedata['fname'])
                    structdict = {None: {}}
                    c = 0
                    for i, n in enumerate(ns):
                        structdict[None][str(i)] = {}
                        for j in range(n):
                            structdict[None][str(i)][str(c)] = [c*pl+k for k in range(pl)]
                            c += 1
                    struct = egglib.struct_from_dict(structdict, None)
                    cs.set_structure(struct)
                    stats = [cs.process_site(site) for site in sites]

                elif filedata['type'] == 'rD':
                    sites, ns, pl = get_genepop(filedata['fname'])
                    structdict = {None: {}}
                    c = 0
                    for i, n in enumerate(ns):
                        structdict[None][str(i)] = {}
                        for j in range(n):
                            structdict[None][str(i)][str(c)] = [c*pl+k for k in range(pl)]
                            c += 1
                    struct = egglib.struct_from_dict(structdict, None)
                    cs.set_structure(struct)
                    stats = cs.process_sites(sites)

                elif filedata['type'] == 'sites':
                    f = open(str(path / filedata['fname']))
                    sites = []
                    pl = set()
                    for line in f:
                        hier = None
                        pops = line.split()
                        ns = []
                        sites.append([])
                        for pop in pops:
                            if pop[0] == 'H':
                                assert hier is None
                                hier = [[int(j)-1 for j in i.split(',')] for i in pop[1:].split(';')]
                                continue
                            ns.append(0)
                            for idv in pop.split(','):
                                ns[-1] += 1
                                idv = list(map(int, idv.split('/')))
                                sites[-1].extend(idv)
                                pl.add(len(idv))
                    sites = [egglib.site_from_list(site, alphabet=INT) for site in sites]
                    self.assertEqual(len(pl), 1)
                    pl = pl.pop()

                    if hier is None:
                        clusters = [0]
                        mapping = dict.fromkeys(range(len(ns)), 0)
                    else:
                        clusters = range(len(hier))
                        mapping = {}
                        for i, v in enumerate(hier):
                            for j in v:
                                mapping[j] = i

                    structdict = {}
                    for i in clusters: structdict[str(i)] = {}
                    for i,k in mapping.items(): structdict[str(k)][str(i)] = {}
                    c = 0
                    for i, n in enumerate(ns):
                        for j in range(n):
                            structdict[str(mapping[i])][str(i)][str(c)] = [c*pl+k for k in range(pl)]
                            c += 1
                    struct = egglib.struct_from_dict(structdict, None)
                    cs.configure(struct=struct)
                    stats = [cs.process_site(site) for site in sites]

                else:
                    raise ValueError('unknown file type: {0}'.format(filedata['type']))

            if filedata['type'] not in ('GenePop', 'sites'):
                stats = [stats]

            for k in sorted(filedata['stats']):
                values = filedata['stats'][k]
                if filedata['type'] not in ('GenePop', 'sites'):
                    values = [values]

                for v, stats_dict in zip(values, stats):
                    msg = 'file: {0}, stat: {1}'.format(filedata['fname'], k)
                    if filedata['haplotypes']: msg += ' [hapls]'

                    # perform ad hoc modifications of computed statistics
                    if k in ('sites', 'sites_o', 'singl', 'Rintervals') and isinstance(v, int): v = [v]
                    if k in ('sites', 'singl', 'sites_o'): v = [i-1 for i in v]
                    elif k == 'Rintervals': v = [(i-1, j-1) for i,j in v]
                    elif k in ('thetaW', 'Pi'): stats_dict[k] = round(stats_dict[k], 2)
                    elif k == 'ks': stats_dict[k] = round(stats_dict[k], 3)

                    # check statistics
                    if not output:
                        if v is None: self.assertIsNone(stats_dict[k], msg=msg)
                        else:
                            self.assertIsNotNone(stats_dict[k], msg=msg)
                            if isinstance(v, int): self.assertEqual(stats_dict[k], v, msg=msg)
                            elif isinstance(v, float): self.assertAlmostEqual(stats_dict[k], v, msg=msg, places=3)
                            elif k in ('FstWC', 'FistWC', 'FisctWC'):
                                self.assertEqual(len(stats_dict[k]), len(v), msg='invalid length of F-stats_dict array')
                                for x,y in zip(stats_dict[k], v):
                                    self.assertAlmostEqual(x, y, msg=msg, places=3)
                            elif isinstance(v, list):
                                self.assertEqual(len(stats_dict[k]), len(v), msg=msg + ' - invalid length for {0}'.format(k))
                                pl = 2 if k in ('D', 'r', 'rsq', 'Dp') else 3
                                for x, y in zip(stats_dict[k], v):
                                    if isinstance(x, int): self.assertEqual(x, y, msg=msg)
                                    else: self.assertAlmostEqual(x, y, msg=msg, places=pl)
                            else:
                                raise ValueError('I am not prepared for testing this type of stats_dict: {0}'.format(type(v)))
                    else:
                        flag = False
                        if k in ('FistWC', 'FisctWC'):
                            rep1 = ' '.join(['{0:.3f}'.format(i) for i in v])
                        elif len(str(v)) >= 20:
                            rep1 = '<...>'
                            flag = True
                        else: rep1 = str(v)

                        if k in ('FistWC', 'FisctWC'):
                            rep2 = ' '.join(['{0:.3f}'.format(i) for i in stats_dict[k]])
                        elif isinstance(stats_dict[k], float): rep2 = '{0:.6f}'.format(stats_dict[k])
                        elif len(str(stats_dict[k])) >= 20:
                            rep2 = '<...>'
                            flag = True
                        else: rep2 = str(stats_dict[k])

                        if stats_dict[k] is None and v is None: msg = 'OK'
                        elif stats_dict[k] is None: msg = 'FAIL'
                        elif stats_dict[k] == v: msg = 'OK'
                        else:
                            if isinstance(v, list):
                                if len(v) != len(stats_dict[k]): diff = 999
                                else: diff = max([abs(x-y) for (x,y) in zip(v, stats_dict[k])])
                            else: diff = abs(v - stats_dict[k])
                            if k in ('Fs', 'He') and diff < 0.001: msg = 'OK'
                            elif k in ('thetaIAM', 'thetaSMM') and diff < 0.001: msg = 'OK'
                            elif k in ('D', 'Dp', 'r', 'rsq') and diff < 0.002: msg = 'OK'
                            elif diff == 0.0: msg = 'OK'
                            elif diff < 0.0001: msg = '~OK'
                            elif diff < 0.001: msg = '??'
                            else: msg = 'FAIL'
                        output.write('    {0:<20} ctlr: {1:<25} egglib: {3:<25} --> {2:>5}\n'.format(k, rep1, msg, rep2))
                        if flag and 'OK' not in msg:
                            output.write(f'    -> {v} {len(v)}\n')
                            output.write(f'    -> {stats_dict[k]} {len(stats_dict[k])}\n')
                            output.write(' DIFF:' + ' '.join(['{0}!={1}'.format(i, j) for i,j in zip(v, stats_dict[k]) if i!=j]) + '\n')
                        cnt[msg.lstrip('~')] += 1

        if output:
            output.write('-----------------------------------------------------------------------------------------------------\n')
            output.write('counts:\n')
            output.write('    OK:   {0:>3}\n'.format(cnt['OK']))
            output.write('    ??:   {0:>3}\n'.format(cnt['??']))
            output.write('    FAIL: {0:>3}\n'.format(cnt['FAIL']))
            print('statistics validation:')
            print('    OK:   {0:>3}'.format(cnt['OK']))
            print('    ??:   {0:>3}'.format(cnt['??']))
            print('    FAIL: {0:>3}'.format(cnt['FAIL']))

class StatsGroups_test(unittest.TestCase):
    def setUp(self):
        self.list_stats_site = ['ns_site', 'ns_site_o', 'Aing', 'Aotg',
            'Atot', 'As', 'Asd', 'R', 'He', 'thetaIAM', 'thetaSMM',
            'Ho', 'Fis', 'maf', 'maf_pop', 'Hst', 'Gst', 'Gste', 'Dj',
            'FstWC', 'FistWC', 'FisctWC', 'f2', 'f3', 'f4', 'Dp',
            'numSp', 'numSpd', 'numShA', 'numShP', 'numFxA', 'numFxD',
            'numSp*', 'numSpd*', 'numShA*', 'numShP*', 'numFxA*',
            'numFxD*', 'triconfig']
        self.list_stats_unphased = ['nseff', 'lseff', 'nsmax', 'S',
            'Ss', 'eta', 'sites', 'singl', 'nall', 'frq', 'frqp',
            'thetaW', 'Pi', 'lseffo', 'nseffo', 'nsmaxo', 'sites_o',
            'singl_o', 'So', 'Sso', 'nsingld', 'etao', 'D', 'Deta',
            'Dfl', 'F', 'D*', 'F*', 'nM', 'pM', 'thetaPi', 'thetaH',
            'thetaL', 'Hns', 'Hsd', 'E', 'Dxy', 'Da']
        self.list_stats_phased = ['R2', 'R3', 'R4', 'Ch', 'R2E', 'R3E',
            'R4E', 'ChE', 'B', 'Q', 'Ki', 'Kt', 'FstH', 'Kst', 'Snn',
            'rD', 'Rmin', 'RminL', 'Rintervals', 'nPairs', 'nPairsAdj',
            'ZnS', 'Z*nS', 'Z*nS*', 'Za', 'ZZ', 'Fs']
        self.list_stats_allelesize = ['V', 'Ar', 'M', 'Rst']

    def test_group_list(self):
        cs = egglib.stats.ComputeStats()
        self.assertCountEqual(cs.stats_group('site'), self.list_stats_site)
        self.assertCountEqual(cs.stats_group('unphased'), self.list_stats_unphased)
        self.assertCountEqual(cs.stats_group('phased'), self.list_stats_phased)
        self.assertCountEqual(cs.stats_group('allelesize'), self.list_stats_allelesize)

        # non-existent group
        with self.assertRaises(KeyError):
            cs.stats_group('LD')

        # test that the returned list is a deep copy
        lst = cs.stats_group('site')
        lst.remove('As')
        lst.append('_phony_')
        self.assertCountEqual(cs.stats_group('site'), self.list_stats_site)
        self.assertCountEqual(cs.stats_group('unphased'), self.list_stats_unphased)

    def test_group_usage(self):
        cs = egglib.stats.ComputeStats()
        cs.add_stats('+site', 'D')
        aln1 = egglib.Align(egglib.alphabets.DNA, 10, 10, 'A')
        stats = cs.process_align(aln1)
        self.assertCountEqual(stats, self.list_stats_site + ['D'])

        aln2 = egglib.Align(egglib.Alphabet('range', (10,9999), [0]), 10, 10, 100) # integer alphabet required for allele size stats
        cs.clear_stats()
        cs.add_stats('+allelesize')
        stats = cs.process_align(aln2)
        self.assertCountEqual(stats, self.list_stats_allelesize)

        cs.add_stats('+site')
        stats = cs.process_align(aln2)
        self.assertCountEqual(stats, self.list_stats_site  + self.list_stats_allelesize)
