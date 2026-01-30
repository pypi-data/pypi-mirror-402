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
from operator import truediv
import collections

mk_dict1=({None: {'0': {'0': [0, 1], '1': [2, 3], '2': [4, 5], '3': [6, 7]}}}, {})
mk_dict2=({None: {'0': {'0': [0], '1': [1], '2': [2], '3': [3], '4': [4], '5': [5], '6': [6], '7': [7]}}}, {})
mk_dict3=({None: {'0': {'0': [0], '1': [1], '2': [2], '3': [3], '4': [4], '5': [5], '6': [6], '7': [7], '8': [8], '9': [9], '10': [10], '11': [11], '12': [12], '13': [13], '14': [14], '15': [15], '16': [16], '17': [17], '18': [18], '19': [19]},
                        '1': {'32': [32], '33': [33], '34': [34], '35': [35], '36': [36], '37': [37], '38': [38], '39': [39], '20': [20], '21': [21], '22': [22], '23': [23], '24': [24], '25': [25], '26': [26], '27': [27], '28': [28], '29': [29], '30': [30], '31': [31]},
                        '2': {'40': [40], '41': [41], '42': [42], '43': [43], '44': [44], '45': [45], '46': [46], '47': [47], '48': [48], '49': [49], '50': [50], '51': [51], '52': [52], '53': [53], '54': [54], '55': [55], '56': [56], '57': [57], '58': [58], '59': [59]},
                        '3': {'64': [64], '65': [65], '66': [66], '67': [67], '68': [68], '69': [69], '70': [70], '71': [71], '72': [72], '73': [73], '74': [74], '75': [75], '76': [76], '77': [77], '78': [78], '79': [79], '60': [60], '61': [61], '62': [62], '63': [63]},
                        '4': {'80': [80], '91': [91], '92': [92]},
                        '5': {'81': [81], '82': [82], '83': [83], '84': [84], '85': [85], '86': [86], '87': [87], '88': [88], '89': [89], '90': [90]}}}, {})

class ParamDict_test(unittest.TestCase):

    def setUp(self):
        self.coal= egglib.coalesce.Simulator(num_pop=4)
        self.params = self.coal.params

    def tearDown(self):
            del self.coal

    def test_ParamDict_T(self):
        self.assertIsInstance(self.params, egglib.coalesce._param_helpers.ParamDict)

    def test_ParamDict_E(self):
        with self.assertRaises(TypeError):
            egglib.coalesce.Simulator(None)

    def test_disable_trans_matrix_T(self):
        self.params.update(num_sites=10, theta=5.0, recomb=5.0, num_mut=0,mut_model='IAM', num_alleles=4, rand_start=True)
        self.params['trans_matrix'][0, 1] = 1.2
        self.params['trans_matrix'][1, 0] = 1.2
        self.params['trans_matrix'][2, 3] = 1.2
        self.params['trans_matrix'][3, 2] = 1.2
        self.params.disable_trans_matrix()
        self.assertEqual(self.params['trans_matrix'][0,2],1.0)
        self.assertEqual(self.params['trans_matrix'][1,1], None)

    def test_get_values_T(self):
        coal2 =egglib.coalesce.Simulator(num_pop=4)
        params2=coal2.params
        params2.update(num_sites=4)
        params2.update(num_chrom=[1,2,4,5],site_pos=[0.1,0.2,0.3,0.4])
        self.params.get_values(params2)
        self.assertEqual(self.params.summary(), params2.summary())

    def test_get_values_E(self):
        coal =egglib.coalesce.Simulator(num_pop=4)
        cnt= egglib.Container(egglib.alphabets.DNA)
        params=coal.params
        with self.assertRaises(TypeError):
            params.get_values(cnt)

    def test_summary_T(self):
        summ= self.params.summary()
        self.assertIn('Number of populations:', summ)

    def test_set_migr_T(self):
        self.params.set_migr(10)
        self.assertEqual(self.params['migr_matrix'][0,2], truediv(10,(4-1)))

    def test_set_migr_E(self):
        with self.assertRaises(ValueError):
            self.params.set_migr(-10)

    def test_mk_structure_T(self):
        coal = egglib.coalesce.Simulator(1, num_indiv=[2])
        coal.params['events'].add(T=0.5, cat='sample', num_chrom=0, num_indiv=2, idx=0, label='0')
        self.assertIsInstance(coal.params.mk_structure(), egglib.Structure)
        self.assertEqual(coal.params.mk_structure().as_dict(), mk_dict1)
        self.assertEqual(coal.params.mk_structure(skip_indiv=True).as_dict(), mk_dict2)

        coal2 = egglib.coalesce.Simulator(6, num_chrom=[20, 20, 20, 20, 1, 10],
                                                 num_sites=1000, num_alleles=4,
                                             theta=1.5, migr=0.0,
                                             rand_start=True)

        coal2.params['migr_matrix'] = [ [None, 0.75, 0.75, 0.75, 0.00, 0.75],
                            [0.75, None, 0.75, 0.75, 0.00, 0.75],
                            [0.75, 0.75, None, 0.75, 0.00, 0.75],
                            [0.75, 0.75, 0.75, None, 0.00, 0.75],
                            [0.00, 0.00, 0.00, 0.00, None, 0.00],
                            [0.75, 0.75, 0.75, 0.75, 0.00, None] ]
        coal2.params['N'][4] = 4.0
        coal2.params['events'].add(T=4.0, cat='merge', src=5, dst=0)
        coal2.params['events'].add(T=4.0, cat='merge', src=4, dst=0)
        coal2.params['events'].add(T=4.0, cat='merge', src=3, dst=0)
        coal2.params['events'].add(T=4.0, cat='merge', src=2, dst=0)
        coal2.params['events'].add(T=4.0, cat='merge', src=1, dst=0)
        coal2.params['events'].add(T=1.0, cat='sample', idx=4, label='4', num_chrom=2, num_indiv=0)
        self.assertEqual(coal2.params.mk_structure().as_dict(), mk_dict3)

    def test_mk_structure_E(self):
        coal = egglib.coalesce.Simulator(1)
        coal.params.mk_structure()
        coal.params['num_chrom'] = [10]
        coal.params.mk_structure()
        coal.params['num_indiv'] = [2]
        with self.assertRaises(ValueError):
            coal.params.mk_structure()

    def test_keys_T(self):
        list_keys_check=['num_pop', 'num_sites', 'recomb', 'theta', 'num_mut', 'mut_model', 'TPM_proba', 'TPM_param', 'num_alleles', 'rand_start', 'num_chrom', 'num_indiv', 'N', 'G', 's', 'site_pos', 'site_weight', 'migr_matrix', 'trans_matrix', 'events', 'max_iter']
        self.assertEqual(list(self.params.keys()), list_keys_check)

    def test_values_T(self):
        self.assertEqual(len(self.params.values()),21 )

    def test_items_T(self):
        match=('TPM_proba', 0.5)
        self.assertIn(match, self.params.items())
        self.assertEqual(len(self.params), 21)

    def test_has_key_T(self):
        self.assertTrue(self.params.has_key('num_chrom'))
        self.assertFalse(self.params.has_key('FAIL'))

    def test_get_T(self):
        self.assertEqual(self.params.get('TPM_proba'),0.5)
        self.assertIsNone(self.params.get('FAIL'))

    def test_iterkeys_T(self):
        self.assertIsInstance(self.params.keys(), collections.abc.Iterable)

    def test_values_T(self):
        self.assertIsInstance(self.params.values(), collections.abc.Iterable)

    def test__iter__T(self):
        self.assertIsInstance(self.params, collections.abc.Iterable)

    def test_copy_T(self):
        copy=self.params.copy()
        self.assertIsInstance(copy, egglib.coalesce._param_helpers.ParamDict)
        for key in self.params.keys():
            self.assertEqual(str(self.params.get(key)), str(copy.get(key)))

    def test_update_T(self):
        n_mut=self.params.get('num_mut')
        self.params.update({'theta': 7.5, 'mut_model': 'IAM'}, theta=0.0, num_mut=15)
        self.assertNotEqual(self.params.get('num_mut'), n_mut)
        
    def test_update_E(self):
        coal=egglib.coalesce.Simulator(num_pop=4)
        params=coal.params
        with self.assertRaises(KeyError):
            params.update(egglib=4)
        with self.assertRaises(ValueError):
            params.update(other='FAIL', num_sites=4)

    def test__len__T(self):
        self.assertEqual(len(self.params), 21)

    def test__reversed__T(self):
        self.assertIsInstance(reversed(self.params), collections.abc.Iterable)

    def test__contains__T(self):
        self.assertTrue('site_pos' in self.params)

    def test__str__T(self):
        self.assertIsInstance(str(self.params), str)

    def test__getitem__T(self):
        self.assertEqual(self.params['num_pop'],4)

    def test__getitem__E(self):
        with self.assertRaises(KeyError):
            self.params['ERROR']

    def test__setitem__T(self):
        n_all1=self.params['num_alleles']
        self.params['num_alleles']=4
        self.assertNotEqual(n_all1, self.params['num_alleles'])

    def test__setitem__E(self):
        with self.assertRaises(KeyError):
            self.params['ERROR']=100
        with self.assertRaises(ValueError):
            self.params['num_pop']=10
        with self.assertRaises(ValueError):
            self.params['num_sites']=-10
        with self.assertRaises(ValueError):
            self.params['recomb']=-10
        with self.assertRaises(ValueError):
            self.params['theta']=-10
        with self.assertRaises(ValueError):
            self.params['num_mut']=-15
        with self.assertRaises(ValueError):
            self.params['num_mut']=10
            self.params['theta']=10

        with self.assertRaises(ValueError):
            self.params['mut_model']='ERR'
        with self.assertRaises(ValueError):
            self.params['TPM_proba']=150
        with self.assertRaises(ValueError):
            self.params['TPM_param']=-10
        with self.assertRaises(ValueError):
            self.params['num_alleles']=1
        with self.assertRaises(ValueError):
            self.params['max_iter']=-150
        with self.assertRaises(ValueError):
            self.params['events']='error'

    def test_add_event_T(self):
        ne1=len(self.params._events)
        self.params.add_event('sample', T=1.0, idx=0, label='0', num_chrom=5, num_indiv=0)
        ne2=len(self.params._events)
        self.assertTrue(ne1<ne2)

    def test_add_event_E(self):
        with self.assertRaises(ValueError):
            self.params.add_event('error', T=1.0, idx=0, label=0, num_chrom=5, num_indiv=0)
        with self.assertRaises(ValueError):
            self.params.add_event('sample', T=1.0, label=0, num_chrom=5, num_indiv=0)
        with self.assertRaises(ValueError):
            self.params.add_event('merge', T=1.0, src=-150, dst=3)
            self.params.add_event('merge', T=1.0, src=2, dst=10)
            self.params.add_event('merge', T=1.0, src=2, dst=2)

class ParamList_test(unittest.TestCase):
        
    def setUp(self):
        self.coal= egglib.coalesce.Simulator(num_pop=4,num_sites=3, theta=5.0, recomb=5.0, num_mut=0,mut_model='IAM', num_alleles=4, rand_start=True, site_pos=[0.3, 0.5, 0.7])
        self.params = self.coal.params

    def tearDown(self):
            del self.coal

    def test_ParamList_T(self):
        num_chrom=self.params['site_pos']
        self.assertIsInstance(num_chrom, egglib.coalesce._param_helpers.ParamList)

    def test__getitem__T(self):
        self.params['site_pos'][0]
        self.assertEqual(self.params['site_pos'][0],0.3)

    def test__setitem__T(self):
        self.params['site_pos'][0]=0.4
        self.assertEqual(self.params['site_pos'][0],0.4)

    def test__iter__T(self):
        self.assertIsInstance(self.params['site_pos'], collections.abc.Iterable)

    def test__add__T(self):
        sum_sites=self.params['site_pos'][0]+self.params['site_pos'][1]
        self.assertEqual(sum_sites, 0.8)

    def test__radd__T(self):
        sum_sites=self.params['site_pos'][0]+0.6
        self.assertEqual(round(sum_sites,1), 0.9)

    def test__mul__T(self):
        sum_sites=self.params['site_pos'][0]*self.params['site_pos'][1]
        self.assertEqual(sum_sites, 0.15)

    def test__rmul__T(self):
        sum_sites=self.params['site_pos'][0]*0.6
        self.assertEqual(round(sum_sites,1), 0.2)

    def test__contains__T(self):
        self.assertTrue('site_pos' in self.params)

    def test__len__T(self):
        self.assertEqual(len(self.params['site_pos']), 3)

    def test__str__T(self):
        self.assertEqual(str(self.params['site_pos']), '[0.3, 0.5, 0.7]')

    def test__repr__T(self):
        self.assertEqual(repr(self.params['site_pos']), '[0.3, 0.5, 0.7]')

    def test__reversed__T(self):
        self.assertIsInstance(reversed(self.params['site_pos']), collections.abc.Iterable)

    def test_count_T(self):
        self.params.update(num_sites=4, num_chrom=[19,1,2,4],site_pos=[0.4,0.2,0.3,0.1])
        self.assertEqual(self.params['num_chrom'].count(2), 1 )

    def test_index_T(self):
        self.params.update(num_sites=4, num_chrom=[19,1,2,4],site_pos=[0.4,0.2,0.3,0.1])
        self.assertEqual(self.params['site_pos'].index(0.2), 1)

    def test_index_E(self):
        self.params.update(num_sites=4, num_chrom=[19,1,2,4],site_pos=[0.4,0.2,0.3,0.1])
        with self.assertRaises(ValueError):
            self.params['num_chrom'].index(10)

class ParamMatrix_test(unittest.TestCase):

    def setUp(self):
        self.coal= egglib.coalesce.Simulator(6, num_chrom=[20, 20, 20, 20, 1, 10],num_sites=1000, num_alleles=4,
                                                 theta=1.5, migr=0.0, rand_start=True)
        self.params = self.coal.params
        self.params['migr_matrix'] = [[None, 0.75, 0.65, 0.15, 0.00, 0.45],
                           [0.95, None, 0.65, 0.85, 0.00, 0.75],
                           [0.55, 0.75, None, 0.75, 0.00, 0.75],
                           [0.5, 0.56, 0.55, None, 0.00, 0.15],
                           [0.00, 0.00, 0.00, 0.00, None, 0.00],
                           [0.05, 0.78, 0.72, 0.77, 0.00, None]]

    def tearDown(self):
        del self.coal

    def test_ParamMatrix_T(self):
        self.assertIsInstance(self.params['migr_matrix'],  egglib.coalesce._param_helpers.ParamMatrix)

    def test_count_T(self):
        self.assertEqual(self.params['migr_matrix'].count(2.0),0)

    def test_index_T(self):
            self.assertEqual(self.params['migr_matrix'].index(0.77 ),(5, 3))

    def test_index_E(self):
        with self.assertRaises(ValueError):
            self.params['migr_matrix'].index(1)

    def test_get_value_T(self):
        m1=self.params['migr_matrix']
        coal= egglib.coalesce.Simulator(6, num_chrom=[20, 20, 20, 20, 1, 10],num_sites=1000, num_alleles=4,
                                                 theta=1.5, migr=0.0, rand_start=True)
        coal.params['migr_matrix'].get_values(self.params['migr_matrix'])
        m2=coal.params['migr_matrix']
        self.assertNotEqual(m1,m2)

    def test_get_value_E(self):
        coal= egglib.coalesce.Simulator(num_pop=4)
        params = coal.params
        params.update(num_sites=4)
        params.update(num_chrom=[19,1,2,4],site_pos=[0.4,0.2,0.3,0.1], num_alleles=2)
        params['migr_matrix'][0,1] = 0.5
        params['migr_matrix'][1,0] = 1.0 

        with self.assertRaises(ValueError):
            params['migr_matrix'].get_values(self.params['migr_matrix'])

        with self.assertRaises(ValueError):
            self.params['migr_matrix'].get_values(((None, 1.0, 1.0),(0.5, None, 0.5),(0.5,1.0,None)))
        
        with self.assertRaises(ValueError):
            self.params['migr_matrix'].get_values([[None, 1.5],[1.0, None,0.5]])
        

    def test__getitem__T(self):
        self.assertEqual(self.params['migr_matrix'][3,2],0.55)

    def test__setitem__T(self):
        self.params['migr_matrix'][3,2]=0.4
        self.assertEqual(self.params['migr_matrix'][3,2],0.4)

    def test__iter__T(self):
        self.assertIsInstance(self.params['migr_matrix'], collections.abc.Iterable)

    def test__add__T(self):
        sum_mirg=self.params['migr_matrix'][3,2]+self.params['migr_matrix'][3,1]
        self.assertEqual(sum_mirg,  1.11)

    def test__radd__T(self):
        sum_mirg=self.params['migr_matrix'][3,2]+0.2
        self.assertEqual(round(sum_mirg,1), 0.8)

    def test__mul__T(self):
        mul_mrg=self.params['migr_matrix'][3,2]*self.params['migr_matrix'][3,1]
        self.assertEqual(round(mul_mrg,1), 0.3)

    def test__rmul__T(self):
        mul_mrg=self.params['migr_matrix'][3,2]*0.6
        self.assertEqual(round(mul_mrg,1), 0.3)

    def test__contains__T(self):
        self.assertTrue(0.85 in self.params['migr_matrix'])
        self.assertFalse(0.18 in self.params['migr_matrix'])

    def test__len__T(self):
        self.assertEqual(len(self.params['migr_matrix']), 6)

    def test__str__T(self):
        self.assertEqual(str(self.params['migr_matrix']), '[[None, 0.75, 0.65, 0.15, 0.0, 0.45], [0.95, None, 0.65, 0.85, 0.0, 0.75], [0.55, 0.75, None, 0.75, 0.0, 0.75], [0.5, 0.56, 0.55, None, 0.0, 0.15], [0.0, 0.0, 0.0, 0.0, None, 0.0], [0.05, 0.78, 0.72, 0.77, 0.0, None]]')

    def test__repr__T(self):
        self.assertEqual(repr(self.params['migr_matrix']), '<matrix of 6*6 values>')

    def test__reversed__T(self):
        self.assertIsInstance(reversed(self.params['migr_matrix']), collections.abc.Iterable)

class EventsList_test(unittest.TestCase):

    def setUp(self):
        self.coal = egglib.coalesce.Simulator(3, num_chrom=(20, 2, 2), migr=0, theta=0.0)
        self.params=self.coal.params

        self.params['events'].add(cat='size', T=0.8, N=1, idx=0)
        self.params['events'].add(cat='migr', T=0.8, M=1)
        self.params['events'].add(cat='pair_migr', T=0.8, M=1, src=1, dst=0)
        self.params['events'].add(cat='growth', T=0.8, G=1, idx=0)
        self.params['events'].add(cat='selfing', T=0.8, s=1, idx=0)
        self.params['events'].add(cat='recombination', T=0.8, R=1)
        self.params['events'].add(cat='admixture', T=0.8, proba=1, dst=0, src=1)
        self.params['events'].add(cat='sample', T=0.8, idx=1, label='0', num_chrom=2, num_indiv=3)

    def tearDown(self):
        del self.coal

    def test_EventsList_T(self):
        self.assertIsInstance(self.params['events'], egglib.coalesce._param_helpers.EventList)

    def test_replace_T(self):
        coal = egglib.coalesce.Simulator(3, num_chrom=(20, 2, 2), migr=0, theta=0.0)
        coal.params['events'].add(cat='bottleneck', T=0.5, idx=0, S=1.0)
        coal.params['events'].add(cat='merge', T=0.8, src=1, dst=0)
        ncat0=len(self.params['events'])
        self.params['events'].replace(coal.params['events'])
        ncat1=len(self.params['events'])
        self.assertTrue(ncat0>ncat1)

    def test_clear_T(self):
        ncat0=len(self.params['events'])
        self.params['events'].clear()
        ncat1=len(self.params['events'])
        self.assertEqual(len(self.params['events']),0)
        self.assertTrue(ncat0>ncat1)

    def test__len__T(self):
        self.assertEqual(len(self.params['events']), 8)

    def test__iter__T(self):
        self.assertIsInstance(self.params['events'], collections.abc.Iterable)

    def test__str__T(self):
        string = str(self.params['events'])
        self.assertIsInstance(string, str)
        mo = re.match('\[<(.+?)>, <(.+?)>, <(.+?)>, <(.+?)>, <(.+?)>, <(.+?)>, <(.+?)>, <(.+?)>\]', string)
        self.assertIsNotNone(mo)
        groups = mo.groups()
        groups = [dict([i.split('=') for i in g.split(';')]) for g in groups]
        self.assertDictEqual(groups[0], {'event_index': '0', 'T': '0.8', 'idx': '0', 'N': '1', 'cat': 'size'})
        self.assertDictEqual(groups[1], {'event_index': '1', 'M': '1', 'T': '0.8', 'cat': 'migr'})
        self.assertDictEqual(groups[2], {'event_index': '2', 'src': '1', 'dst': '0', 'M': '1', 'cat': 'pair_migr', 'T': '0.8'})
        self.assertDictEqual(groups[3], {'event_index': '3', 'G': '1', 'T': '0.8', 'idx': '0', 'cat': 'growth'})
        self.assertDictEqual(groups[4], {'event_index': '4', 's': '1', 'T': '0.8', 'idx': '0', 'cat': 'selfing'})
        self.assertDictEqual(groups[5], {'event_index': '5', 'R': '1', 'T': '0.8', 'cat': 'recombination'})
        self.assertDictEqual(groups[6], {'event_index': '6', 'src': '1', 'dst': '0', 'cat': 'admixture', 'T': '0.8', 'proba': '1'})
        self.assertDictEqual(groups[7], {'event_index': '7', 'idx': '1', 'cat': 'sample', 'num_indiv': '3', 'T': '0.8', 'label': '0', 'num_chrom': '2'})

    def test__repr__T(self):
        string = repr(self.params['events'])
        self.assertIsInstance(string, str)
        mo = re.match('\[<(.+?)>, <(.+?)>, <(.+?)>, <(.+?)>, <(.+?)>, <(.+?)>, <(.+?)>, <(.+?)>\]', string)
        self.assertIsNotNone(mo)
        groups = mo.groups()
        groups = [dict([i.split('=') for i in g.split(';')]) for g in groups]
        self.assertDictEqual(groups[0], {'event_index': '0', 'T': '0.8', 'idx': '0', 'N': '1', 'cat': 'size'})
        self.assertDictEqual(groups[1], {'event_index': '1', 'M': '1', 'T': '0.8', 'cat': 'migr'})
        self.assertDictEqual(groups[2], {'event_index': '2', 'src': '1', 'dst': '0', 'M': '1', 'cat': 'pair_migr', 'T': '0.8'})
        self.assertDictEqual(groups[3], {'event_index': '3', 'G': '1', 'T': '0.8', 'idx': '0', 'cat': 'growth'})
        self.assertDictEqual(groups[4], {'event_index': '4', 's': '1', 'T': '0.8', 'idx': '0', 'cat': 'selfing'})
        self.assertDictEqual(groups[5], {'event_index': '5', 'R': '1', 'T': '0.8', 'cat': 'recombination'})
        self.assertDictEqual(groups[6], {'event_index': '6', 'src': '1', 'dst': '0', 'cat': 'admixture', 'T': '0.8', 'proba': '1'})
        self.assertDictEqual(groups[7], {'event_index': '7', 'idx': '1', 'cat': 'sample', 'num_indiv': '3', 'T': '0.8', 'label': '0', 'num_chrom': '2'})

    def test__getitem__T(self):
        self.assertEqual(self.params['events'][2],  {'src': 1, 'dst': 0, 'M': 1, 'T': 0.8, 'cat': 'pair_migr'})

    def test_add_T(self):
        ncat0=len(self.params['events'])
        self.params['events'].add(cat='bottleneck', T=0.5, idx=0, S=1.0)
        ncat1= len(self.params['events'])
        self.assertTrue(ncat0 < ncat1)

    def test_add_E(self):
        with self.assertRaises(ValueError):
            self.params['events'].add(cat='FAIL', T=0.5, idx=0, S=1.0)
        with self.assertRaises(ValueError):
            self.params['events'].add(cat='bottleneck', T=0.5, idx=0)
        with self.assertRaises(ValueError):
            self.params.add_event('merge', T=1.0, src=-150, dst=3)
            self.params.add_event('merge', T=1.0, src=2, dst=10)
            self.params.add_event('merge', T=1.0, src=2, dst=2)

    def test_update_T(self):
        self.params['events'].add(cat='bottleneck', T=0.5, idx=0, S=1.0)
        self.params['events'].add(cat='merge', T=0.8, src=1, dst=0)
        btlnk0=str(self.params['events'][8])
        self.params['events'].update(8, T=1, idx=2, S=0.5)
        btlnk1=str(self.params['events'][8])
        self.assertNotEqual(btlnk0,btlnk1)

        mrg0=str(self.params['events'][9])
        self.params['events'].update(9, T=1, idx=3, S=1)
        mrg1=str(self.params['events'][9])
        self.assertNotEqual(mrg0,mrg1)

        self.params['events'].add(cat='sample', T=1.44, num_chrom=0, num_indiv=10, label='NorwegianBlue', idx=0)
        self.params['events'].update(10, T=2.88)
        self.assertEqual(self.params['events'][10]['T'], 2.88)

        self.params['events'].add(cat='bottleneck', T=0.72, idx=0, S=0.1)
        self.params['events'].update(11, S=0.247)
        self.assertEqual(self.params['events'][11]['S'], 0.247)

    def test_update_E(self):
        self.params['events'].add(cat='bottleneck', T=0.5, idx=0, S=1.0)
        self.params['events'].add(cat='merge', T=0.8, src=1, dst=0)

        with self.assertRaises(IndexError): #invalid event index
            self.params['events'].update(12, T=1, src=-3, dst=0)
        with self.assertRaises(ValueError): #src: population index out of range <0
            self.params['events'].update(9, T=1, src=-3, dst=0) 
        with self.assertRaises(ValueError): #src: population index out of range >self._npop
            self.params['events'].update(9, T=1, src=4, dst=0)
        with self.assertRaises(ValueError): #dst: population index out of range <0
            self.params['events'].update(9, T=1, src=3, dst=-10)
        with self.assertRaises(ValueError): #dst: population index out of range >self._npop
            self.params['events'].update(9, T=1, src=3, dst=4)

        with self.assertRaises(ValueError): #T
            self.params['events'].update(8, T=-0.5, idx=0, S=1.0) 
        with self.assertRaises(ValueError): #S
            self.params['events'].update(8, T=0.5, idx=0, S=-1.0) 
        with self.assertRaises(ValueError): #idx
            self.params['events'].update(8, T=0.5, idx=-10, S=1.0) 
        with self.assertRaises(ValueError): #N
            self.params['events'].update(0, T=1, N=-1, idx=0)
        with self.assertRaises(ValueError): #M
            self.params['events'].update(1, T=0.8, M=-0.5)
        with self.assertRaises(ValueError):#src
            self.params['events'].update(2, T=1, src=-3, dst=0) 
        with self.assertRaises(ValueError):#s
            self.params['events'].update(4, T=0.8, s=-1, idx=0)
        with self.assertRaises(ValueError):#R
            self.params['events'].update(5, T=0.8, R=-1)
        with self.assertRaises(ValueError):#proba
            self.params['events'].update(6, T=0.8, proba=-1, dst=0, src=1)
        with self.assertRaises(ValueError): #src
            self.params['events'].update(6, T=0.8, proba=1, dst=0, src=-1)
        with self.assertRaises(ValueError): #dst
            self.params['events'].update(6, T=0.8, proba=1, dst=41, src=1)
        with self.assertRaises(TypeError): #label
            self.params['events'].update(7, T=0.8, idx=1, label=0, num_chrom=2, num_indiv=3)
        with self.assertRaises(ValueError):#num_chrom
            self.params['events'].update(7, T=0.8, idx=1, label='1', num_chrom=-2, num_indiv=3)
        with self.assertRaises(ValueError): #num_indiv
            self.params['events'].update(7, T=0.8, idx=1, label='1', num_chrom=2, num_indiv=-3)
