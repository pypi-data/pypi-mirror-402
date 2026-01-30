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

import egglib, unittest, random, time
from random import *
from scipy.stats import bernoulli, binom, expon, geom, ttest_ind, zmap, ttest_ind, norm, poisson, binomtest
import numpy as np

class Random_test(unittest.TestCase):
    def test_bernoulli_T(self):
        size = 10000
        res = [egglib.random.bernoulli(0.5) for i in range(size)]
        self.assertSetEqual(set(res), {True, False})
        self.assertGreater(res.count(True), 200)
        self.assertGreater(res.count(False), 200)
        self.assertListEqual([egglib.random.bernoulli(0) for i in range(size)], [False] * size)
        self.assertListEqual([egglib.random.bernoulli(1) for i in range(size)], [True] * size)

    def test_bernoulli_E(self):
        with self.assertRaises(ValueError):
            egglib.random.bernoulli(-10)
        with self.assertRaises(ValueError):
            egglib.random.bernoulli(10)

    def test_binomial_T(self):

        for rep in range(10):
            distribution1=[]
            distribution2=[]
            k=2
            for i in range(1000):
                rb=binom.rvs(6, 0.5, size=20).tolist()
                distribution1.append(rb.count(k))
                rb2=[egglib.random.binomial(6, 0.5) for i in range(20)]
                distribution2.append(rb2.count(k))
            T=ttest_ind(distribution1, distribution2)
            if T.pvalue > 0.05:
                break
        else:
            self.assertTrue(False, 'test of binomial distribution failed too many times')

    def test_binomial_E(self):
        with self.assertRaises(ValueError):
            egglib.random.binomial(-10,0.2)
        with self.assertRaises(ValueError):
            egglib.random.binomial(10, -0.2)
        with self.assertRaises(ValueError):
            egglib.random.binomial(10, 10)

    def test_exponential_T(self):
        distribution1=[]
        distribution2=[]
        j=0
        while (j==0):
            for i in range(1000):
                re=[egglib.random.exponential(1/0.2) for i in range(20)]
                distribution1.append(sum(re)/20)
                re2=expon.rvs(scale=(1/0.2), size=20)
                distribution2.append(sum(re2)/20)
            #T-ttest
            T=ttest_ind(distribution1, distribution2)
            try:
                self.assertTrue(T[1]>0.05)
                j=1 
            except:
                j=0

    def test_exponential_E(self):
        with self.assertRaises(ValueError):
            egglib.random.exponential(-10)

    def test_geometric_T(self):
        distribution1=[]
        distribution2=[]
        j=0
        while (j==0):
            for i in range(1000):
                rg=[egglib.random.geometric(0.2) for i in range(10)]
                rg2=geom.rvs(0.2, size=10)
                distribution1.append(sum(rg)/10)
                distribution2.append(sum(rg2)/10)
            T=ttest_ind(distribution1, distribution2)
            try:
                self.assertTrue(T[1]>0.05) 
                j=1
            except:
                j=0

    def test_geometrie_E(self):
        with self.assertRaises(ValueError):
            egglib.random.geometric(-10)
        with self.assertRaises(ValueError):
            egglib.random.geometric(10)

    def test_normal_T(self):
        #source: http://wwwf.imperial.ac.uk/~naheard/C245/hypothesis_testing_article.pdf
        j=0
        while (j==0): 
            distribution1=[egglib.random.normal() for i in range(1000)]
            distribution2 = norm.rvs(size=1000)
            T=ttest_ind(distribution1, distribution2)
            try:
                self.assertTrue(T[1]>0.05)
                j=1
            except: 
                j=0

        j=0
        while (j==0): 
            distribution1=[egglib.random.normal_bounded(1, 2, -1000, +1000) for i in range(1000)]
            distribution2 = norm.rvs(loc=1, scale=2, size=1000)
            T=ttest_ind(distribution1, distribution2)
            try:
                self.assertTrue(T[1]>0.05)
                j=1
            except: 
                j=0


        for i in range(100):
            x = egglib.random.normal_bounded(1, 1, 0.9, 3)
            self.assertGreaterEqual(x, 0.9)
            self.assertLessEqual(x, 3)


    def test_poisson_T(self):
        distribution1=[egglib.random.poisson(0.2) for i in range(1000)]
        distribution2=[]
        for i in range (1000):
            r=poisson.rvs(0.2)
            distribution2.append(r)

        nzero1=distribution1.count(0)
        ntrue1=1000-nzero1
        nzero2=distribution2.count(0)
        ntrue2=1000-nzero2

        #C-test
        x = ntrue1
        n = ntrue1+ntrue2
        p = len(distribution1)/(len(distribution1)+len(distribution2))
        P = binomtest(x,n,p).pvalue
        self.assertGreater(P, 0.05)

    def test_poisson_E(self):
        with self.assertRaises(ValueError):
            egglib.random.poisson(0)
        with self.assertRaises(ValueError):
            egglib.random.poisson(-10)

    def test_integer_T(self):
        distribution1=[]
        distribution2=[]
        j=0
        while (j==0):
            for i in range (1000):
                ri1=egglib.random.integer(20)
                distribution1.append(ri1)
                ri2=np.random.randint(20,size=1)  # , dtype='int' [disabled because not available before numpy 1.11 ; int is the default]
                distribution2.append(ri2[0])

            T=ttest_ind(distribution1, distribution2)
            try:
                self.assertTrue(T[1]>0.05)
                j=1 
            except:
                j=0

    def test_integer_E(self):
        with self.assertRaises(ValueError):
            egglib.random.integer(0)
        with self.assertRaises(ValueError):
            egglib.random.integer(-10)

    def test_integer_32bit_T(self):
        distribution1=[]
        distribution2=[]
        j=0
        while (j==0):
            for i in range (1000):
                ri1=egglib.random.integer_32bit()
                distribution1.append(ri1)
                ri2=getrandbits(32)
                distribution2.append(ri2)
            T=ttest_ind(distribution1, distribution2)
            try:
                self.assertTrue(T[1]>0.05)
                j=1 
            except:
                j=0
        
    def test_uniform_T(self):
        distribution1=[]
        distribution2=[]
        j=0
        while (j==0):
            for i in range (1000):
                ri1=egglib.random.uniform()
                distribution1.append(ri1)
                ri2=uniform(0,1)
                distribution2.append(ri2)
            T=ttest_ind(distribution1, distribution2)
            try:
                self.assertTrue(T[1]>0.05)
                j=1 
            except:
                j=0

    def test_uniform_53bit_T(self):
        distribution1=[]
        distribution2=[]
        j=0
        while (j==0):
            for i in range (1000):
                ri1=egglib.random.uniform_53bit()
                distribution1.append(ri1)
                ri2=uniform(0,1) #Random, produces 53-bit precision floats and has a period of 2**19937-1.
                distribution2.append(ri2)
            T=ttest_ind(distribution1, distribution2)
            try:
                self.assertTrue(T[1]>0.05)
                j=1 
            except:
                j=0
            
    def test_uniform_closed_T(self):
        distribution1=[]
        distribution2=[]
        j=0
        while (j==0):
            for i in range (1000):
                ri1=egglib.random.uniform_closed()
                distribution1.append(ri1)
                ri2=np.float32(uniform(0.0000000, 1.0000001))
                distribution2.append(ri2)
            T=ttest_ind(distribution1, distribution2)
            try:
                self.assertTrue(T[1]>0.05)
                j=1 
            except:
                j=0

    def test_uniform_open_T(self):
        distribution1=[]
        distribution2=[]
        j=0
        while (j==0):
            for i in range (1000):
                ri1=egglib.random.uniform_open()
                distribution1.append(ri1)
                ri2=np.float32(uniform(0.0000001, 1.0000000))
                distribution2.append(ri2)
            T=ttest_ind(distribution1, distribution2)
            try:
                self.assertTrue(T[1]>0.05)
                j=1 
            except:
                j=0

    def test_get_seed_T(self):
        time.sleep(1)
        egglib.random.set_seed(1500000000)
        self.assertEqual(egglib.random.get_seed(),1500000000)

    def test_set_seed_T(self):
        time.sleep(1)
        egglib.random.set_seed(1500000000)
        self.assertEqual(egglib.random.get_seed(),1500000000)

    def test_set_seed_E(self):
        with self.assertRaises(TypeError):
            egglib.random.set_seed(100.002)

    def test_seed(self):
        egglib.random.set_seed(593291034)
        X1 = tuple(egglib.random.uniform() for i in range(10))
        egglib.random.set_seed(593291034)
        X2 = tuple(egglib.random.uniform() for i in range(10))
        egglib.random.set_seed(593291034)
        X3 = tuple(egglib.random.uniform() for i in range(10))
        egglib.random.set_seed(593291034)
        X4 = tuple(egglib.random.uniform() for i in range(10))
        egglib.random.set_seed(593291034)
        X5 = tuple(egglib.random.uniform() for i in range(10))

        self.assertEqual(len(set([X1, X2, X3, X4, X5])), 1)

        X6 = tuple(egglib.random.uniform() for i in range(10))
        X7 = tuple(egglib.random.uniform() for i in range(10))
        X8 = tuple(egglib.random.uniform() for i in range(10))
        X9 = tuple(egglib.random.uniform() for i in range(10))
        Xa = tuple(egglib.random.uniform() for i in range(10))

        self.assertEqual(len(set([X5, X6, X7, X8, X9, Xa])), 6)
