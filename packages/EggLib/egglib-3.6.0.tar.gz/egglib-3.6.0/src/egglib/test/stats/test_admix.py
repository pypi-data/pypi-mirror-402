"""
    Copyright 2025 Stéphane De Mita

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

import egglib, unittest, random

class Admix_test(unittest.TestCase):
    def setUp(self):
        self.dsA = { 'n': (10, 10),
            'list': [ 'AAAAAAAAAACCCCCCCCCC',
                      'AAAAACCCCCAAAAACCCCC',
                      'TTTTTTTTTTTTTTTTTTTT',
                      'TTTT--TTTTTTT-TTTTTT',
                      'AAAAAAAACCACCCCCCCCC' ]}
        self.dsB = { 'n': (8, 6, 10),
            'list': [ 'AAAAAAAACCCCCCAAAAAAAAAA',
                      'AAAAAACCAACCCCCCCCCCCCCC',
                      'AAAACCCCAAAAAACCCCCCCCCC',
                      'AACACCCCAAACAACCCCCCCCCC',
                      'AAAAAAAAAAAAAAAAAAAAAAAA',
                      'GGGTTTGGGTGTGGGGGTTGGTGT',
                      'AAAAACAAAAAAAAAAAAAAAAAA',
                      'AAAAA-AAAAAAAAAAAAAAAAAA',
                      'TTTTTTCTTTTTTGGTTTTTTTTT',
                      'TTTTTTCTTTTTT--TTTTTTTTT',
                      'AAAAAACACCACCCA---------',
                      'AAAAAACACCACCCA----C----']}
        self.dsC = { 'n': (5, 8, 6, 10),
            'list': [ 'AAAAAAAAAAAAATTTTTTTTTTTTTTTT',
                      'AAAAAAAAAATAATTTTAATTTTTAAATA',
                      'AAAAAAAAAATAATTTAAATTTTTAAAAA',
                      'GGGGGGGGGRGGGGGGGGGGGGGGGGGGG',
                      'GGGGGTCCCCGTTTTTTTTTTTTTTTTTT',
                      'TTTTTTC--TCCCCCCCCCTTCTCTTTTT',
                      'CCCCCGGGGGGGGCCCCCCGGGGGGGGGG' ]}
        self.dsD = { 'n': (3,4,5,6,7),
            'list': [ 'AAAAAAAAAAAAAAAAAAAAAAAAA',
                      'AAAACCCCCCCCCCCCCCCCCCCCC',
                      'TCTCTCTCTCTCTCTCTCTCTCTCT',
                      'CCCCCCTTTCCCCCCCTTTCCCCCC',
                      'AAAAAAAAAATTTTAAAATATTTTT',
                      'GGGGGGGGGGGGGAGGGGGGGGGGG',
                      'CCCCCCCCACCCCCCCAACCCCCCC',
                      'AAAAAAAAAAATTTTTTTTTTTTTT',
                      'AAAAAAAAAATTTAATTTTTAAATA',
                      'AAAAAAAAATAAAAATTTTTAAAAA',
                      'GGGGGGGGGGGGGGGGGGGGGGGGG',
                      'GGGGGTCCCCTTTTTTTTTTTTTTT',
                      'TTTTTTC--TCCCCCTTCTCTTTTT',
                      'CCCCCGGGGGCCCCCGGGGGGGGGG' ]}

    @staticmethod
    def struct(ds):
        return egglib.struct_from_samplesizes(pops=ds['n'])

    @staticmethod
    def iter_sites(ds):
        for site in ds['list']:
            yield egglib.site_from_list(site, alphabet=egglib.alphabets.DNA)

    @staticmethod
    def iter_pops(ds, *trg):
        rng = []
        acc = 0
        for ni in ds['n']:
            rng.append((acc, acc+ni))
            acc += ni
        k = len(trg)
        rng = [rng[i] for i in trg]

        # remove duplicates
        uniq = []
        for i in trg:
            if i not in uniq:
                uniq.append(i)
        idx = [trg.index(i) for i in uniq]
        rng = [rng[i] for i in idx]

        for site in ds['list']:
            pops = []
            n = []
            alls = set()
            for a, b in rng:
                pops.append([])
                n.append(0)
                for x in site[a:b]:
                    if x in {'A', 'C', 'G', 'T'}:
                        alls.add(x)
                        pops[-1].append(x)
                        n[-1] += 1
            alls = list(sorted(alls))
            if len(rng) < 2 or min(n) < 2 or len(alls) not in {1, 2}:
                yield None, None, None
            else:
                ref = alls[0]
                P = [pops[i].count(ref) for i in range(k)]
                p = [v/n for n,v in zip(n, P, strict=True)]
                h = [P[i]*(n[i]-P[i])/(n[i]*(n[i]-1)) for i in range(k)]
                yield p, h, n

    def ctrl_f2(self, ds, i, j):
        res = []
        for p, h, n in self.iter_pops(ds, i, j):
            if p is None: res.append(None)
            else: res.append((p[0]-p[1])**2 - h[0]/n[0] - h[1]/n[1])
        return res

    def ctrl_f3(self, ds, i, j, k):
        res = []
        for p, h, n in self.iter_pops(ds, i, j, k):
            if p is None: res.append(None)
            else: res.append((p[0]-p[1]) * (p[0]-p[2]) - h[0]/n[0])
        return res

    def ctrl_f4(self, ds, i, j, m, n):
        res = []
        for p, *_ in self.iter_pops(ds, i, j, m, n):
            if p is None:
                res.append(None)
            else:
                res.append((p[0]-p[1])*(p[2]-p[3]))
        return res

    def ctrl_Dp(self, ds, i, j, m, n):
        res = []
        for p, *_ in self.iter_pops(ds, i, j, m, n):
            if p is None: res.append(None)
            else:
                N = (p[0]-p[1])*(p[2]-p[3])
                D = (p[0]+p[1]-2*p[0]*p[1])*(p[2]+p[3]-2*p[2]*p[3])
                res.append((N, D))
        return res

    def cmp(self, ds, struct, key, ctrl, focus=None):
        # test values per site
        cs = egglib.stats.ComputeStats(struct, f3_focus=focus)
        cs.add_stats(key)
        for i, site in enumerate(self.iter_sites(ds)):
            test = cs.process_site(site)[key]
            ref = ctrl[i]
            if key == 'Dp':
                if ref is not None:
                    if ref[1] == 0: ref = None
                    else: ref = ref[0] / ref[1]
            if ref is None:
                self.assertIsNone(test, msg=f'site={"".join(site.as_list())}')
            else:
                self.assertIsNotNone(test, msg=f'site={"".join(site.as_list())}')
                self.assertAlmostEqual(test, ref, msg=f'site={"".join(site.as_list())}')
        self.assertEqual(len(ctrl), i+1)

        # test global value
        cs = egglib.stats.ComputeStats(struct, multi=True, f3_focus=focus)
        cs.add_stats(key)
        for site in self.iter_sites(ds):
            self.assertIsNone(cs.process_site(site))
        test = cs.results()[key]
        if key == 'Dp':
            N = sum(i[0] for i in ctrl if i is not None)
            D = sum(i[1] for i in ctrl if i is not None)
            if D > 0: ref = N/D
            else: ref = None
        else:
            ctrl_nnone = list(filter(lambda x: x is not None, ctrl))
            ref = sum(ctrl_nnone) / len(ctrl_nnone) if len(ctrl_nnone) > 0 else None
        if ref is None:
            self.assertIsNone(test)
        else:
            self.assertIsNotNone(test)
            self.assertAlmostEqual(test, ref)

    def test_f2(self):
        # first dataset (with 2 pops)
        ctrl = self.ctrl_f2(self.dsA, 0, 1)
        self.cmp(self.dsA, self.struct(self.dsA).subset(['pop1', 'pop2']), 'f2', ctrl)
        self.cmp(self.dsA, self.struct(self.dsA).subset(['pop2', 'pop1']), 'f2', ctrl)

        # second dataset (with 3 pops)
        struct = self.struct(self.dsB)
        self.cmp(self.dsB, struct.subset(['pop1', 'pop2']), 'f2', self.ctrl_f2(self.dsB, 0, 1))
        self.cmp(self.dsB, struct.subset(['pop2', 'pop1']), 'f2', self.ctrl_f2(self.dsB, 0, 1))
        self.cmp(self.dsB, struct.subset(['pop1', 'pop3']), 'f2', self.ctrl_f2(self.dsB, 0, 2))
        self.cmp(self.dsB, struct.subset(['pop2', 'pop3']), 'f2', self.ctrl_f2(self.dsB, 1, 2))

        # third dataset (with 4 pops)
        struct = self.struct(self.dsC)
        self.cmp(self.dsC, struct.subset(['pop1', 'pop2']), 'f2', self.ctrl_f2(self.dsC, 0, 1))
        self.cmp(self.dsC, struct.subset(['pop1', 'pop3']), 'f2', self.ctrl_f2(self.dsC, 0, 2))
        self.cmp(self.dsC, struct.subset(['pop1', 'pop4']), 'f2', self.ctrl_f2(self.dsC, 0, 3))
        self.cmp(self.dsC, struct.subset(['pop2', 'pop3']), 'f2', self.ctrl_f2(self.dsC, 1, 2))
        self.cmp(self.dsC, struct.subset(['pop2', 'pop4']), 'f2', self.ctrl_f2(self.dsC, 1, 3))
        self.cmp(self.dsC, struct.subset(['pop3', 'pop4']), 'f2', self.ctrl_f2(self.dsC, 2, 3))
        
        # artificially set to None (considered as one pop)
        self.cmp(self.dsC, struct.subset(['pop1']), 'f2', self.ctrl_f2(self.dsC, 0, 0))
        self.cmp(self.dsC, struct.subset(['pop2']), 'f2', self.ctrl_f2(self.dsC, 1, 1))
        self.cmp(self.dsC, struct.subset(['pop3']), 'f2', self.ctrl_f2(self.dsC, 2, 2))
        self.cmp(self.dsC, struct.subset(['pop4']), 'f2', self.ctrl_f2(self.dsC, 3, 3))

    def test_f3(self):
        # second dataset (with 3 pops)
        struct = self.struct(self.dsB)
        self.cmp(self.dsB, struct.subset(['pop1', 'pop2', 'pop3']), 'f3', self.ctrl_f3(self.dsB, 0, 1, 2), focus='pop1')
        self.cmp(self.dsB, struct.subset(['pop1', 'pop3', 'pop2']), 'f3', self.ctrl_f3(self.dsB, 0, 1, 2), focus='pop1')
        self.cmp(self.dsB, struct.subset(['pop2', 'pop1', 'pop3']), 'f3', self.ctrl_f3(self.dsB, 1, 0, 2), focus='pop2')
        self.cmp(self.dsB, struct.subset(['pop2', 'pop3', 'pop1']), 'f3', self.ctrl_f3(self.dsB, 1, 0, 2), focus='pop2')
        self.cmp(self.dsB, struct.subset(['pop3', 'pop1', 'pop2']), 'f3', self.ctrl_f3(self.dsB, 2, 0, 1), focus='pop3')
        self.cmp(self.dsB, struct.subset(['pop3', 'pop2', 'pop1']), 'f3', self.ctrl_f3(self.dsB, 2, 0, 1), focus='pop3')

        # third dataset (with 4 pops)
        struct = self.struct(self.dsC)
        self.cmp(self.dsC, struct.subset(['pop1', 'pop2', 'pop3']), 'f3', self.ctrl_f3(self.dsC, 0, 1, 2), focus='pop1')
        self.cmp(self.dsC, struct.subset(['pop1', 'pop2', 'pop4']), 'f3', self.ctrl_f3(self.dsC, 0, 1, 3), focus='pop1')
        self.cmp(self.dsC, struct.subset(['pop1', 'pop3', 'pop4']), 'f3', self.ctrl_f3(self.dsC, 0, 2, 3), focus='pop1')
        self.cmp(self.dsC, struct.subset(['pop1', 'pop3', 'pop2']), 'f3', self.ctrl_f3(self.dsC, 0, 2, 1), focus='pop1')
        self.cmp(self.dsC, struct.subset(['pop1', 'pop4', 'pop3']), 'f3', self.ctrl_f3(self.dsC, 0, 3, 2), focus='pop1')

        self.cmp(self.dsC, struct.subset(['pop2', 'pop1', 'pop3']), 'f3', self.ctrl_f3(self.dsC, 1, 0, 2), focus='pop2')
        self.cmp(self.dsC, struct.subset(['pop2', 'pop3', 'pop1']), 'f3', self.ctrl_f3(self.dsC, 1, 2, 0), focus='pop2')
        self.cmp(self.dsC, struct.subset(['pop2', 'pop1', 'pop4']), 'f3', self.ctrl_f3(self.dsC, 1, 0, 3), focus='pop2')
        self.cmp(self.dsC, struct.subset(['pop2', 'pop4', 'pop1']), 'f3', self.ctrl_f3(self.dsC, 1, 3, 0), focus='pop2')
        self.cmp(self.dsC, struct.subset(['pop2', 'pop3', 'pop4']), 'f3', self.ctrl_f3(self.dsC, 1, 2, 3), focus='pop2')

        self.cmp(self.dsC, struct.subset(['pop3', 'pop1', 'pop2']), 'f3', self.ctrl_f3(self.dsC, 2, 0, 1), focus='pop3')
        self.cmp(self.dsC, struct.subset(['pop3', 'pop2', 'pop1']), 'f3', self.ctrl_f3(self.dsC, 2, 1, 0), focus='pop3')
        self.cmp(self.dsC, struct.subset(['pop3', 'pop2', 'pop1']), 'f3', self.ctrl_f3(self.dsC, 2, 1, 0), focus='pop3')
        self.cmp(self.dsC, struct.subset(['pop3', 'pop1', 'pop4']), 'f3', self.ctrl_f3(self.dsC, 2, 0, 3), focus='pop3')
        self.cmp(self.dsC, struct.subset(['pop3', 'pop4', 'pop2']), 'f3', self.ctrl_f3(self.dsC, 2, 3, 1), focus='pop3')

        self.cmp(self.dsC, struct.subset(['pop4', 'pop1', 'pop2']), 'f3', self.ctrl_f3(self.dsC, 3, 0, 1), focus='pop4')
        self.cmp(self.dsC, struct.subset(['pop4', 'pop1', 'pop3']), 'f3', self.ctrl_f3(self.dsC, 3, 0, 2), focus='pop4')
        self.cmp(self.dsC, struct.subset(['pop4', 'pop2', 'pop1']), 'f3', self.ctrl_f3(self.dsC, 3, 1, 0), focus='pop4')
        self.cmp(self.dsC, struct.subset(['pop4', 'pop2', 'pop3']), 'f3', self.ctrl_f3(self.dsC, 3, 1, 2), focus='pop4')
        self.cmp(self.dsC, struct.subset(['pop4', 'pop3', 'pop1']), 'f3', self.ctrl_f3(self.dsC, 3, 2, 0), focus='pop4')
        self.cmp(self.dsC, struct.subset(['pop4', 'pop3', 'pop2']), 'f3', self.ctrl_f3(self.dsC, 3, 2, 1), focus='pop4')

    def test_f4_Dp(self):
        def group(ds, a, b, c, d):
            struct = self.struct(ds)
            dstruct = struct.as_dict()[0][None]
            k1 = {}
            k2 = {}
            k1[a] = dstruct[a] # I want to make sure that the order of a/b and c/d is preserved in the dictionary
            k1[b] = dstruct[b]
            k2[c] = dstruct[c]
            k2[d] = dstruct[d]
            struct = egglib.struct_from_dict({'k1': k1, 'k2': k2}, None)
            return struct
        self.cmp(self.dsC, group(self.dsC, 'pop1', 'pop2', 'pop3', 'pop4'), 'f4', self.ctrl_f4(self.dsC, 0, 1, 2, 3))
        self.cmp(self.dsC, group(self.dsC, 'pop1', 'pop2', 'pop3', 'pop4'), 'Dp', self.ctrl_Dp(self.dsC, 0, 1, 2, 3))
        self.cmp(self.dsC, group(self.dsC, 'pop2', 'pop1', 'pop3', 'pop4'), 'f4', self.ctrl_f4(self.dsC, 1, 0, 2, 3))
        self.cmp(self.dsC, group(self.dsC, 'pop2', 'pop1', 'pop3', 'pop4'), 'Dp', self.ctrl_Dp(self.dsC, 1, 0, 2, 3))
        self.cmp(self.dsC, group(self.dsC, 'pop1', 'pop3', 'pop2', 'pop4'), 'f4', self.ctrl_f4(self.dsC, 0, 2, 1, 3))
        self.cmp(self.dsC, group(self.dsC, 'pop1', 'pop3', 'pop2', 'pop4'), 'Dp', self.ctrl_Dp(self.dsC, 0, 2, 1, 3))
        self.cmp(self.dsC, group(self.dsC, 'pop3', 'pop1', 'pop4', 'pop2'), 'f4', self.ctrl_f4(self.dsC, 2, 0, 3, 1))
        self.cmp(self.dsC, group(self.dsC, 'pop3', 'pop1', 'pop4', 'pop2'), 'Dp', self.ctrl_Dp(self.dsC, 2, 0, 3, 1))

        # datset with 5 pops
        self.cmp(self.dsD, group(self.dsD, 'pop1', 'pop2', 'pop3', 'pop4'), 'f4', self.ctrl_f4(self.dsD, 0, 1, 2, 3))
        self.cmp(self.dsD, group(self.dsD, 'pop1', 'pop2', 'pop3', 'pop4'), 'Dp', self.ctrl_Dp(self.dsD, 0, 1, 2, 3))
        self.cmp(self.dsD, group(self.dsD, 'pop1', 'pop2', 'pop3', 'pop5'), 'f4', self.ctrl_f4(self.dsD, 0, 1, 2, 4))
        self.cmp(self.dsD, group(self.dsD, 'pop1', 'pop2', 'pop3', 'pop5'), 'Dp', self.ctrl_Dp(self.dsD, 0, 1, 2, 4))
        self.cmp(self.dsD, group(self.dsD, 'pop2', 'pop5', 'pop3', 'pop4'), 'f4', self.ctrl_f4(self.dsD, 1, 4, 2, 3))
        self.cmp(self.dsD, group(self.dsD, 'pop2', 'pop5', 'pop3', 'pop4'), 'Dp', self.ctrl_Dp(self.dsD, 1, 4, 2, 3))
        self.cmp(self.dsD, group(self.dsD, 'pop5', 'pop2', 'pop1', 'pop4'), 'f4', self.ctrl_f4(self.dsD, 4, 1, 0, 3))
        self.cmp(self.dsD, group(self.dsD, 'pop5', 'pop2', 'pop1', 'pop4'), 'Dp', self.ctrl_Dp(self.dsD, 4, 1, 0, 3))
