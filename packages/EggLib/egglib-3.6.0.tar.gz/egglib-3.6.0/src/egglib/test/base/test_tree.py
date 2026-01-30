"""
    Copyright 2023-2025 Thomas Coudoux, Stéphane De Mita, Mathieu Siol

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

import os, egglib, sys, unittest, random, re, gc
import collections

TREE_STRING = '(((VvLYK2:0.09020761,VvLYK3:0.13588809)1000:0.0759631,(PtLYK3:0.17773083,((FvLYK2:0.1079844,(PpLYK3:0.0532316,MdLYK3:0.11516319)1000:0.02510313)1000:0.07250312,((((CacLYK3:0.06016158,GmLYK3:0.04988316)998:0.04732511,LjLYS7:0.08887798)598:0.01845951,MtLYK8:0.17283636)1000:0.15093267,(CasLYK2:0.00284497,CasLYK3:0.00922375)1000:0.16983704)341:0.01703062)492:0.02813366)999:0.06833724)999:0.03856292,(VvLYK1:0.14879144,((PtLYK1:0.03931642,PtLYK2:0.06215206)1000:0.13921412,((CasLYK1:0.16961626,(AtCERK1:0.49326411,(FvLYK1:0.1453431,((PpLYK1:0.06109585,PpLYK2:0.07592721)933:0.02843438,(MdLYK1:0.0383793,MdLYK2:0.05889107)1000:0.04350185)924:0.02731021)999:0.05725737)294:0.00688996)430:0.02167592,(((CacLYK1:0.08167788,(GmNFR1a:0.03699912,GmNFR1b:0.02880309)677:0.01953081)998:0.0365518,(LjNFR1a:0.07999007,(MtLYK2:0.05186283,(MtLYK3:0.07978386,PsSYM37:0.07493097)822:0.014712)1000:0.05694231)832:0.0215714)1000:0.18063742,((CecLYK1:0.1680513,(((LjNFR1b:0.13030045,MtLYK1:0.15554318)1000:0.07303159,(LjNFR1c:0.13766267,MtLYK6:0.16025718)982:0.03580008)990:0.02671666,((GmLYK2:0.04933436,CacLYK4:0.05585385)1000:0.06029768,MtLYK7:0.1292539)997:0.04581387)1000:0.05564467)998:0.03954658,(CecLYK2:0.07693512,((CacLYK2:0.07392427,GmLYK2b:0.05439578)1000:0.05710725,(LjLYS6:0.06218823,MtLYK9:0.12383649)905:0.02507435)1000:0.08050891)794:0.01706889)820:0.01986008)999:0.06770856)577:0.02895946)942:0.04476039)999:0.03856292);'
TREE_STRING_R ='((((((((((LjNFR1b:0.13030045,MtLYK1:0.15554318)1000:0.07303159,(LjNFR1c:0.13766267,MtLYK6:0.16025718)982:0.03580008)990:0.02671666,((GmLYK2:0.04933436,CacLYK4:0.05585385)1000:0.06029768,MtLYK7:0.1292539)997:0.04581387)1000:0.05564467,CecLYK1:0.1680513)998:0.03954658,(((CacLYK2:0.07392427,GmLYK2b:0.05439578)1000:0.05710725,(LjLYS6:0.06218823,MtLYK9:0.12383649)905:0.02507435)1000:0.08050891,CecLYK2:0.07693512)794:0.01706889)820:0.01986008,((((MtLYK3:0.07978386,PsSYM37:0.07493097)822:0.014712,MtLYK2:0.05186283)1000:0.05694231,LjNFR1a:0.07999007)832:0.0215714,((GmNFR1a:0.03699912,GmNFR1b:0.02880309)677:0.01953081,CacLYK1:0.08167788)998:0.0365518)1000:0.18063742)999:0.06770856,(((((PpLYK1:0.06109585,PpLYK2:0.07592721)933:0.02843438,(MdLYK1:0.0383793,MdLYK2:0.05889107)1000:0.04350185)924:0.02731021,FvLYK1:0.1453431)999:0.05725737,AtCERK1:0.49326411)294:0.00688996,CasLYK1:0.16961626)430:0.02167592)577:0.02895946,(PtLYK1:0.03931642,PtLYK2:0.06215206)1000:0.13921412)942:0.04476039,VvLYK1:0.14879144)999:0.03856292,(((((((CacLYK3:0.06016158,GmLYK3:0.04988316)998:0.04732511,LjLYS7:0.08887798)598:0.01845951,MtLYK8:0.17283636)1000:0.15093267,(CasLYK2:0.00284497,CasLYK3:0.00922375)1000:0.16983704)341:0.01703062,((PpLYK3:0.0532316,MdLYK3:0.11516319)1000:0.02510313,FvLYK2:0.1079844)1000:0.07250312)492:0.02813366,PtLYK3:0.17773083)999:0.06833724,(VvLYK2:0.09020761,VvLYK3:0.13588809)1000:0.0759631)999:0.03856292);'

class Node_test(unittest.TestCase):
    def setUp(self):
        self.tree= egglib.Tree(string=TREE_STRING)

    def tearDown(self):
        del self.tree

    def test_Node_T(self):
        node= self.tree.find_clade(['VvLYK2'], ancestral=True)
        self.assertIsInstance(node, egglib._tree.Node)
    
    def test_newick_T(self):
        node = self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        self.assertEqual(node.newick(), '(PtLYK3:0.17773083,((FvLYK2:0.1079844,(PpLYK3:0.0532316,MdLYK3:0.11516319)1000:0.02510313)1000:0.07250312,((((CacLYK3:0.06016158,GmLYK3:0.04988316)998:0.04732511,LjLYS7:0.08887798)598:0.01845951,MtLYK8:0.17283636)1000:0.15093267,(CasLYK2:0.00284497,CasLYK3:0.00922375)1000:0.16983704)341:0.01703062)492:0.02813366)999;')

    def test_leaves_down_T(self):
        node = self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        self.assertEqual(node.leaves_down(), ['PtLYK3', 'FvLYK2', 'PpLYK3', 'MdLYK3', 'CacLYK3', 'GmLYK3', 'LjLYS7', 'MtLYK8', 'CasLYK2', 'CasLYK3'])


    def test_leaves_up_T(self):
        node = self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        self.assertEqual(node.leaves_up(), ['VvLYK2', 'VvLYK3', 'VvLYK1', 'PtLYK1', 'PtLYK2', 'CasLYK1', 'AtCERK1', 'FvLYK1', 'PpLYK1', 'PpLYK2', 'MdLYK1', 'MdLYK2', 'CacLYK1', 'GmNFR1a', 'GmNFR1b', 'LjNFR1a', 'MtLYK2', 'MtLYK3', 'PsSYM37', 'CecLYK1', 'LjNFR1b', 'MtLYK1', 'LjNFR1c', 'MtLYK6', 'GmLYK2', 'CacLYK4', 'MtLYK7', 'CecLYK2', 'CacLYK2', 'GmLYK2b', 'LjLYS6', 'MtLYK9'])

    def test_has_descendant_T(self):
        node = self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        node_c = self.tree.find_clade(['LjLYS7'],ancestral=True)
        node_c1 = self.tree.find_clade(['GmNFR1a'],ancestral=True)
        self.assertTrue(node.has_descendant(node_c))
        self.assertFalse(node.has_descendant(node_c1))

    def test_is_parent_T(self):
        node = self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        node_c = self.tree.find_clade(['LjLYS7'],ancestral=True)
        self.assertFalse(node.is_parent(node_c))

    def test_parent_T(self):
        node = self.tree.find_clade(['LjNFR1a'],ancestral=True)
        self.assertEqual(node.parent.newick(), '(LjNFR1a:0.07999007,(MtLYK2:0.05186283,(MtLYK3:0.07978386,PsSYM37:0.07493097)822:0.014712)1000:0.05694231)832;')

    def test_child_T(self):
        node = self.tree.find_clade(['LjNFR1a', 'PsSYM37'], ancestral=True)
        self.assertEqual(node.child(0).newick(), 'LjNFR1a;')

    def test_child_E(self):
        node = self.tree.find_clade(['LjNFR1a', 'PsSYM37'], ancestral=True)
        with self.assertRaises(IndexError):
            node.child(1000)

    def test_set_branch_to_T(self):
        node = self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        A = node.branch_to(0)
        node.set_branch_to(0, 0.7734) 
        B = node.branch_to(0)
        self.assertEqual(B, 0.7734)
        self.assertNotEqual(A,B)

    def test_set_branch_to_E(self):
        node = self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        with self.assertRaises(ValueError):
            node.set_branch_to(1500, 0.7734) 
        node_e = self.tree.find_clade(['LjNFR1a'],ancestral=True)
        with self.assertRaises(ValueError):
            node.set_branch_to(node_e, 0.7734)

    def test_branch_to_T(self):
        node = self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        A = node.branch_to(0)
        self.assertEqual(A, 0.17773083)
        node1= node.child(1)
        B = node.branch_to(node1)
        self.assertEqual(B, 0.02813366)

    def test_branch_to_E(self):
        node = self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        with self.assertRaises(ValueError):
            node.branch_to(1500)
        node_e = self.tree.find_clade(['LjNFR1a'],ancestral=True)
        with self.assertRaises(ValueError):
            node.branch_to(node_e)

    def test_parent_branch_getter_T(self):
        node = self.tree.find_clade(['LjNFR1a'],ancestral=True)
        self.assertEqual(node.parent_branch, 0.07999007)
    
    def test_parent_branch_getter_E(self):
        node = self.tree._base
        with self.assertRaises(ValueError):
            node.parent_branch

    def test_parent_branch_setter_T(self):
        node = self.tree.find_clade(['LjNFR1a'],ancestral=True)
        node.parent_branch=0.05
        self.assertEqual(node.parent_branch, 0.05)
    
    def test_parent_branch_setter_E(self):
        node = self.tree._base
        with self.assertRaises(ValueError):
            node.parent_branch=0.5
    
    def test_label_getter_T(self):
        node = self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        self.assertEqual(node.label, 999)

    def test_label_setter_T(self):
        node = self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        node.label= 'new_label'
        self.assertEqual(node.label, 'new_label')

    def test_num_children_T(self):
        node = self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        self.assertEqual(node.num_children, 2)

class Tree_test(unittest.TestCase):
    def setUp(self):
        self.tree= egglib.Tree(string=TREE_STRING)

    def tearDown(self):
        del self.tree

    def test_Tree_T(self):
        self.assertIsInstance(self.tree, egglib.Tree)

    def test_copy_T(self):
        tree0=self.tree.copy()
        self.assertIsInstance(tree0, egglib.Tree)
        self.assertEqual(str(self.tree), str(tree0))

    def test_copy_E(self):
        node0 = self.tree.find_clade(['VvLYK2'], ancestral=True)
        with self.assertRaises(ValueError):
            tree0=self.tree.copy(node0)
        with self.assertRaises(ValueError):
            tree1=self.tree.copy(self.tree.find_clade(['error'], ancestral=True))
    
    def test_extract_T(self):
        node0 = self.tree.find_clade(names=['CacLYK1', 'MtLYK9'], ancestral=True)
        tree0=self.tree.extract(node0, 'clade-A')
        self.assertNotEqual(str(tree0), str(self.tree)) 

    def test_extract_E(self):
        with self.assertRaises(ValueError):
            tree0= self.tree.extract(self.tree.find_clade(['error']))
        with self.assertRaises(ValueError):
            node0 = self.tree.find_clade(['VvLYK3'], ancestral=True)
            tree0=self.tree.extract(node0)
        with self.assertRaises(ValueError):
            node0 = self.tree.base
            tree0=self.tree.extract(node0)

    def test__del__T(self):
        tree= egglib.Tree(string=TREE_STRING)
        del tree
        with self.assertRaises(NameError):
            tree

    def test__str__T(self):
        tree_s=str(self.tree)
        self.assertIsInstance(tree_s, str)
    
    def test_num_nodes_T(self):
        self.assertEqual(self.tree.num_nodes, 83)
    
    def test_num_leaves(self):
        self.assertEqual(self.tree.num_leaves, 42)
    
    def test_newick_T(self):
        n0=str(self.tree.newick())
        n1=str(self.tree.newick(skip_labels=True, skip_brlens=True))
        self.assertEqual(n1, '(((VvLYK2,VvLYK3),(PtLYK3,((FvLYK2,(PpLYK3,MdLYK3)),((((CacLYK3,GmLYK3),LjLYS7),MtLYK8),(CasLYK2,CasLYK3))))),(VvLYK1,((PtLYK1,PtLYK2),((CasLYK1,(AtCERK1,(FvLYK1,((PpLYK1,PpLYK2),(MdLYK1,MdLYK2))))),(((CacLYK1,(GmNFR1a,GmNFR1b)),(LjNFR1a,(MtLYK2,(MtLYK3,PsSYM37)))),((CecLYK1,(((LjNFR1b,MtLYK1),(LjNFR1c,MtLYK6)),((GmLYK2,CacLYK4),MtLYK7))),(CecLYK2,((CacLYK2,GmLYK2b),(LjLYS6,MtLYK9)))))))));')
        self.assertEqual(n0, str(self.tree))

    def test_base_T(self):
        node_b=self.tree.base
        self.assertIsInstance(node_b, egglib._tree.Node)

    def test_add_node_T(self):
        node = self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        self.tree.add_node(node, 'new_node', 0.54)
        new_node = self.tree.find_clade(['new_node'], ancestral=True)
        self.assertIsNotNone(new_node)

    def test_add_node_E(self):
        node0 = self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        tree0 = self.tree.extract(node0)
        with self.assertRaises(ValueError):
            self.tree.add_node(node0, 'new_node' , 0.54)

    def test_iter_leaves_T(self):
        self.assertIsInstance(self.tree.iter_leaves(), collections.abc.Iterable)
        
    def test_get_leaf_T(self):
        leaf=self.tree.get_leaf('CasLYK1')
        self.assertIsInstance(leaf, egglib._tree.Node)
        self.assertEqual(str(leaf.newick()), 'CasLYK1;')

    def test_depth_iter_T(self):
        self.assertIsInstance(self.tree.depth_iter(), collections.abc.Iterable)
        node=self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        i=1
        for n in self.tree.depth_iter(node):
            self.assertIsInstance(n, egglib._tree.Node)
            i+=1
        self.assertEqual(i, 20)

    def test_depth_iter_E(self):
        node= self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        self.tree.extract(node)
        with self.assertRaises(ValueError):
            self.tree.depth_iter(node)

    def test_total_length_T(self):
        L=self.tree.total_length()
        self.assertEqual(L, 6.25127455)

    def test_total_length_E(self):
        tree= egglib.Tree(string='(((VvLYK2,VvLYK3),(PtLYK3,((FvLYK2,(PpLYK3,MdLYK3)),((((CacLYK3,GmLYK3),LjLYS7),MtLYK8),(CasLYK2,CasLYK3))))),(VvLYK1,((PtLYK1,PtLYK2),((CasLYK1,(AtCERK1,(FvLYK1,((PpLYK1,PpLYK2),(MdLYK1,MdLYK2))))),(((CacLYK1,(GmNFR1a,GmNFR1b)),(LjNFR1a,(MtLYK2,(MtLYK3,PsSYM37)))),((CecLYK1,(((LjNFR1b,MtLYK1),(LjNFR1c,MtLYK6)),((GmLYK2,CacLYK4),MtLYK7))),(CecLYK2,((CacLYK2,GmLYK2b),(LjLYS6,MtLYK9)))))))));')
        with self.assertRaises(ValueError):
            tree.total_length()
        
    def test_find_clade_T(self):
        node = self.tree.find_clade(names=['CacLYK1', 'MtLYK9'], ancestral=True)
        self.assertIsInstance(node, egglib._tree.Node)

    def test_fin_clade_E(self):
        with self.assertRaises(ValueError):
            self.tree.find_clade(names=['CacLYK1', 'MtLYK9'], ancestral=True, both_sides=True)
        with self.assertRaises(ValueError):
            self.tree.find_clade(names=[], ancestral=True)

        tree= egglib.Tree(string='(((VvLYK2,VvLYK3),(PtLYK3,((FvLYK2,(PpLYK3,MdLYK3)),((((CacLYK3,GmLYK3),LjLYS7),MtLYK8),(CasLYK2,CasLYK3))))));')
        with self.assertRaises(ValueError):
            tree.find_clade(names=['VvLYK2','VvLYK3','PtLYK3','FvLYK2','PpLYK3','MdLYK3','CacLYK3','GmLYK3','LjLYS7','MtLYK8','CasLYK2','CasLYK3','VvLYK1','PtLYK1','PtLYK2','CasLYK1','AtCERK1','FvLYK1','PpLYK1','PpLYK2','MdLYK1','MdLYK2','CacLYK1','GmNFR1a','GmNFR1b','LjNFR1a','MtLYK2','MtLYK3','PsSYM37','CecLYK1','LjNFR1b','MtLYK1','LjNFR1c','MtLYK6','GmLYK2','CacLYK4','MtLYK7','CecLYK2','CacLYK2','GmLYK2b','LjLYS6','MtLYK9'])

    def test_collapse_T(self):
        node = self.tree.find_clade(['MtLYK3', 'GmNFR1a'], ancestral=True)
        self.assertEqual(self.tree.num_nodes, 83)
        self.tree.collapse(node)
        self.assertEqual(self.tree.num_nodes, 82)

    def test_collapse_E(self):
        node_b = self.tree.find_clade(['VvLYK2', 'PsSYM37'], ancestral=True)
        node_t = self.tree.find_clade(['AtCERK1'])
        tree= egglib.Tree(string='(((VvLYK2,VvLYK3),(PtLYK3,((FvLYK2,(PpLYK3,MdLYK3)),((((CacLYK3,GmLYK3),LjLYS7),MtLYK8),(CasLYK2,CasLYK3))))),(VvLYK1,((PtLYK1,PtLYK2),((CasLYK1,(AtCERK1,(FvLYK1,((PpLYK1,PpLYK2),(MdLYK1,MdLYK2))))),(((CacLYK1,(GmNFR1a,GmNFR1b)),(LjNFR1a,(MtLYK2,(MtLYK3,PsSYM37)))),((CecLYK1,(((LjNFR1b,MtLYK1),(LjNFR1c,MtLYK6)),((GmLYK2,CacLYK4),MtLYK7))),(CecLYK2,((CacLYK2,GmLYK2b),(LjLYS6,MtLYK9)))))))));')
        node_l = tree.find_clade(['MtLYK9'])
        with self.assertRaises(ValueError):
            self.tree.collapse(node_b)
        with self.assertRaises(ValueError):
            self.tree.collapse(node_t)
        with self.assertRaises(ValueError):
            tree.collapse(node_l)
        with self.assertRaises(ValueError):
            tree.collapse(node_l)
        node_m= self.tree.find_clade(['PtLYK3', 'CasLYK3'], ancestral=True)
        self.tree.extract(node_m)
        with self.assertRaises(ValueError):
            tree.collapse(node_m)
        
    def test_root_T(self):
        self.tree.collapse(self.tree.base.child(0))
        A=self.tree.num_nodes
        node = self.tree.find_clade(['MtLYK3', 'GmNFR1a'], ancestral=True)
        self.tree.root(node, 0.2)
        B=self.tree.num_nodes
        self.assertNotEqual(A, B)
        self.assertEqual(A, 82)
        self.assertEqual(B, 83)

    def test_root_E(self):
        node_b = self.tree.find_clade(['VvLYK2', 'PsSYM37'], ancestral=True)
        node = self.tree.find_clade(['MtLYK3', 'GmNFR1a'], ancestral=True)
        node_t = self.tree.find_clade(['AtCERK1'])
        with self.assertRaises(ValueError):
            self.tree.root(node_b, 0.2, reoriente=True)
        with self.assertRaises(ValueError):
            self.tree.root(node_t, 0.2, reoriente=True)
        with self.assertRaises(ValueError):
            self.tree.root(node_t, 0.2, reoriente=False)
        with self.assertRaises(ValueError):
            self.tree.root(node, 0.2, reoriente=False)

        tree= egglib.Tree(string='(((VvLYK2,VvLYK3),(PtLYK3,((FvLYK2,(PpLYK3,MdLYK3)),((((CacLYK3,GmLYK3),LjLYS7),MtLYK8),(CasLYK2,CasLYK3))))),(VvLYK1,((PtLYK1,PtLYK2),((CasLYK1,(AtCERK1,(FvLYK1,((PpLYK1,PpLYK2),(MdLYK1,MdLYK2))))),(((CacLYK1,(GmNFR1a,GmNFR1b)),(LjNFR1a,(MtLYK2,(MtLYK3,PsSYM37)))),((CecLYK1,(((LjNFR1b,MtLYK1),(LjNFR1c,MtLYK6)),((GmLYK2,CacLYK4),MtLYK7))),(CecLYK2,((CacLYK2,GmLYK2b),(LjLYS6,MtLYK9)))))))));')
        node_n =tree.find_clade(['MtLYK3', 'GmNFR1a'], ancestral=True)
        with self.assertRaises(ValueError):
            tree.root(node_n, 0.2, reoriente=True)

    def test_map_descendants_T(self):
        for node, labels in self.tree.map_descendants().items():
            self.assertIsInstance(node, egglib._tree.Node)
            self.assertIsInstance(labels, tuple)
    
    def test_frequency_node_T(self):
        tree0=str(self.tree)
        copies = [self.tree.copy() for i in range(1000)]
        for copy in copies:
            leaves = [i.label for i in copy.iter_leaves()]
            random.shuffle(leaves)
            for node, leaf in zip(copy.iter_leaves(), leaves): node.label = leaf
        self.tree.frequency_nodes(copies)
        tree1=str(self.tree)
        self.tree.frequency_nodes(copies, relative=True)
        tree2=str(self.tree)
        self.assertNotEqual(tree0, tree1)
        self.assertNotEqual(tree1, tree2)

    def test_frequency_node_E(self):
        tree_e=egglib.Tree(string='(Spider:0.01257025,Woolly:0.02023601,(Howler:0.03625789,((Titi:0.02002846,Saki:0.02646824):0.01312676,((Owl:0.02467454,(((Gorilla:0.00570008,(Human:0.00467442,Chimp:0.00218595):0.00198277):0.00803251,(Gibbon:0.02031871,Orangutan:0.01428695):0.00052501):0.01497214,(Colobus:0.00134948,(DLangur:0.00479108,(Patas:0.01038680,((AGM_cDNA:0.00067736,Tant_cDNA:0.00000006):0.00511480,(Baboon:0.00531400,Rhes_cDNA:0.00519922):0.00433750):0.00200495):0.00621549):0.00134574):0.02864316):0.11226732):0.00500924,(Squirrel:0.04657578,(PMarmoset:0.02254897,Tamarin:0.01990484):0.01687811):0.00000008):0.00119894):0.01464801):0.01145931);')
        tree_d=egglib.Tree(string='(((VvLYK2:0.09020761,VvLYK3:0.13588809)1000:0.0759631,(PtLYK3:0.17773083,((FvLYK2:0.1079844,(PpLYK3:0.0532316,MdLYK3:0.11516319)1000:0.02510313)1000:0.07250312,((((CacLYK3:0.06016158,GmLYK3:0.04988316)998:0.04732511,VvLYK2:0.08887798)598:0.01845951,MtLYK8:0.17283636)1000:0.15093267,(CasLYK2:0.00284497,CasLYK3:0.00922375)1000:0.16983704)341:0.01703062)492:0.02813366)999:0.06833724)999:0.03856292,(VvLYK1:0.14879144,((PtLYK1:0.03931642,PtLYK2:0.06215206)1000:0.13921412,((CasLYK1:0.16961626,(AtCERK1:0.49326411,(VvLYK2:0.1453431,((PpLYK1:0.06109585,VvLYK2:0.07592721)933:0.02843438,(MdLYK1:0.0383793,MdLYK2:0.05889107)1000:0.04350185)924:0.02731021)999:0.05725737)294:0.00688996)430:0.02167592,(((CacLYK1:0.08167788,(VvLYK2:0.03699912,GmNFR1b:0.02880309)677:0.01953081)998:0.0365518,(LjNFR1a:0.07999007,(MtLYK2:0.05186283,(MtLYK3:0.07978386,PsSYM37:0.07493097)822:0.014712)1000:0.05694231)832:0.0215714)1000:0.18063742,((CecLYK1:0.1680513,(((LjNFR1b:0.13030045,VvLYK2:0.15554318)1000:0.07303159,(LjNFR1c:0.13766267,MtLYK6:0.16025718)982:0.03580008)990:0.02671666,((GmLYK2:0.04933436,CacLYK4:0.05585385)1000:0.06029768,MtLYK7:0.1292539)997:0.04581387)1000:0.05564467)998:0.03954658,(CecLYK2:0.07693512,((CacLYK2:0.07392427,GmLYK2b:0.05439578)1000:0.05710725,(LjLYS6:0.06218823,MtLYK9:0.12383649)905:0.02507435)1000:0.08050891)794:0.01706889)820:0.01986008)999:0.06770856)577:0.02895946)942:0.04476039)999:0.03856292);')
        copies_e = [tree_e.copy() for i in range(1000)]
        for copy in copies_e:
            leaves = [i.label for i in copy.iter_leaves()]
            random.shuffle(leaves)
            for node, leaf in zip(copy.iter_leaves(), leaves): node.label = leaf
        with self.assertRaises(ValueError):
            self.tree.frequency_nodes(copies_e)

        copies_d = [tree_d.copy() for i in range(1000)]
        for copy in copies_d:
            leaves = [i.label for i in copy.iter_leaves()]
            random.shuffle(leaves)
            for node, leaf in zip(copy.iter_leaves(), leaves): node.label = leaf
        with self.assertRaises(ValueError):
            self.tree.frequency_nodes(copies_d)

        copies_n = []
        with self.assertRaises(ValueError):
            self.tree.frequency_nodes(copies_n, relative=True)

    def test_clean_internal_labels_T(self):
        self.tree.clean_internal_labels()
        self.assertEqual(str(self.tree), "(((VvLYK2:0.09020761,VvLYK3:0.13588809):0.0759631,(PtLYK3:0.17773083,((FvLYK2:0.1079844,(PpLYK3:0.0532316,MdLYK3:0.11516319):0.02510313):0.07250312,((((CacLYK3:0.06016158,GmLYK3:0.04988316):0.04732511,LjLYS7:0.08887798):0.01845951,MtLYK8:0.17283636):0.15093267,(CasLYK2:0.00284497,CasLYK3:0.00922375):0.16983704):0.01703062):0.02813366):0.06833724):0.03856292,(VvLYK1:0.14879144,((PtLYK1:0.03931642,PtLYK2:0.06215206):0.13921412,((CasLYK1:0.16961626,(AtCERK1:0.49326411,(FvLYK1:0.1453431,((PpLYK1:0.06109585,PpLYK2:0.07592721):0.02843438,(MdLYK1:0.0383793,MdLYK2:0.05889107):0.04350185):0.02731021):0.05725737):0.00688996):0.02167592,(((CacLYK1:0.08167788,(GmNFR1a:0.03699912,GmNFR1b:0.02880309):0.01953081):0.0365518,(LjNFR1a:0.07999007,(MtLYK2:0.05186283,(MtLYK3:0.07978386,PsSYM37:0.07493097):0.014712):0.05694231):0.0215714):0.18063742,((CecLYK1:0.1680513,(((LjNFR1b:0.13030045,MtLYK1:0.15554318):0.07303159,(LjNFR1c:0.13766267,MtLYK6:0.16025718):0.03580008):0.02671666,((GmLYK2:0.04933436,CacLYK4:0.05585385):0.06029768,MtLYK7:0.1292539):0.04581387):0.05564467):0.03954658,(CecLYK2:0.07693512,((CacLYK2:0.07392427,GmLYK2b:0.05439578):0.05710725,(LjLYS6:0.06218823,MtLYK9:0.12383649):0.02507435):0.08050891):0.01706889):0.01986008):0.06770856):0.02895946):0.04476039):0.03856292);")

    def test_clean_branch_lengths_T(self):
        self.tree.clean_branch_lengths()
        with self.assertRaises(ValueError):
            self.tree.total_length()

    def test_remove_node_T(self):
        node = self.tree.find_clade(['VvLYK2', 'CasLYK3'], ancestral=True)
        self.tree.remove_node(node)
        with self.assertRaises(ValueError):
            self.tree.find_clade(['VvLMK2', 'CasLYK3'], ancestral=True)

    def test_remove_node_E(self):
        node_b = self.tree.find_clade(['VvLYK2', 'PsSYM37'], ancestral=True)
        node = self.tree.find_clade(['VvLYK2', 'CasLYK3'], ancestral=True)
        with self.assertRaises(ValueError):
            self.tree.remove_node(node_b)
        self.tree.remove_node(node)
        with self.assertRaises(ValueError):
            self.tree.remove_node(node)

    def test_lateralize_T(self):
        self.tree.lateralize(reverse=True)
        self.assertEqual(str(self.tree),TREE_STRING_R) 

    def test_midroot_T(self):
        tree=egglib.Tree(string='(Spider:0.01257025,Woolly:0.02023601,(Howler:0.03625789,((Titi:0.02002846,Saki:0.02646824):0.01312676,((Owl:0.02467454,(((Gorilla:0.00570008,(Human:0.00467442,Chimp:0.00218595):0.00198277):0.00803251,(Gibbon:0.02031871,Orangutan:0.01428695):0.00052501):0.01497214,(Colobus:0.00134948,(DLangur:0.00479108,(Patas:0.01038680,((AGM_cDNA:0.00067736,Tant_cDNA:0.00000006):0.00511480,(Baboon:0.00531400,Rhes_cDNA:0.00519922):0.00433750):0.00200495):0.00621549):0.00134574):0.02864316):0.11226732):0.00500924,(Squirrel:0.04657578,(PMarmoset:0.02254897,Tamarin:0.01990484):0.01687811):0.00000008):0.00119894):0.01464801):0.01145931);')
        self.assertEqual(tree.num_nodes, 40)
        tree.midroot()
        self.assertEqual(tree.num_nodes, 41)

    def test_midroot_E(self):
        with self.assertRaises(ValueError):
            self.tree.midroot()
        tree_l=egglib.Tree(string='(Spider,Woolly,(Howler,((Titi,Saki),((Owl,(((Gorilla,(Human,Chimp)),(Gibbon,Orangutan)),(Colobus,(DLangur,(Patas,((AGM_cDNA,Tant_cDNA),(Baboon,Rhes_cDNA))))))),(Squirrel,(PMarmoset,Tamarin))))));')
        with self.assertRaises(ValueError):
            tree_l.midroot()
    
        tree_n=egglib.Tree(string='(Spider:0.01257025,Woolly:0.02023601);')
        with self.assertRaises(ValueError):
            tree_n.midroot()

    def test_unroot_T(self):
        tree=egglib.Tree(string='(Spider:0.01257025,Woolly:0.02023601,(Howler:0.03625789,((Titi:0.02002846,Saki:0.02646824):0.01312676,((Owl:0.02467454,(((Gorilla:0.00570008,(Human:0.00467442,Chimp:0.00218595):0.00198277):0.00803251,(Gibbon:0.02031871,Orangutan:0.01428695):0.00052501):0.01497214,(Colobus:0.00134948,(DLangur:0.00479108,(Patas:0.01038680,((AGM_cDNA:0.00067736,Tant_cDNA:0.00000006):0.00511480,(Baboon:0.00531400,Rhes_cDNA:0.00519922):0.00433750):0.00200495):0.00621549):0.00134574):0.02864316):0.11226732):0.00500924,(Squirrel:0.04657578,(PMarmoset:0.02254897,Tamarin:0.01990484):0.01687811):0.00000008):0.00119894):0.01464801):0.01145931);')
        self.assertEqual(tree.num_nodes, 40)
        tree.midroot()
        self.assertEqual(tree.num_nodes, 41)
        tree.unroot()
        self.assertEqual(tree.num_nodes, 40)

    def test_unroot_E(self):
        tree=egglib.Tree(string='(Spider:0.01257025,Woolly:0.02023601,(Howler:0.03625789,((Titi:0.02002846,Saki:0.02646824):0.01312676,((Owl:0.02467454,(((Gorilla:0.00570008,(Human:0.00467442,Chimp:0.00218595):0.00198277):0.00803251,(Gibbon:0.02031871,Orangutan:0.01428695):0.00052501):0.01497214,(Colobus:0.00134948,(DLangur:0.00479108,(Patas:0.01038680,((AGM_cDNA:0.00067736,Tant_cDNA:0.00000006):0.00511480,(Baboon:0.00531400,Rhes_cDNA:0.00519922):0.00433750):0.00200495):0.00621549):0.00134574):0.02864316):0.11226732):0.00500924,(Squirrel:0.04657578,(PMarmoset:0.02254897,Tamarin:0.01990484):0.01687811):0.00000008):0.00119894):0.01464801):0.01145931);')
        with self.assertRaises(ValueError):
            tree.unroot()
        
        tree=egglib.Tree(string='((((Gorilla:0.00570008,(Human:0.00467442,Chimp:0.00218595):0.00198277):0.00803251,(Gibbon:0.02031871,Orangutan:0.01428695):0.00052501):0.01497214,(Colobus:0.00134948,(DLangur:0.00479108,(Patas:0.0103868,((AGM_cDNA:0.00067736,Tant_cDNA:6e-08):0.0051148,(Baboon:0.005314,Rhes_cDNA:0.00519922):0.0043375):0.00200495):0.00621549):0.00134574):0.02864316),(Owl:0.02467454,((Squirrel:0.04657578,(PMarmoset:0.02254897,Tamarin:0.01990484):0.01687811):8e-08,((Titi:0.02002846,Saki:0.02646824):0.01312676,(Howler:0.03625789,(Spider:0.01257025,Woolly:0.02023601):0.01145931):0.01464801):0.00119894):0.00500924):0.05150704);')
        with self.assertRaises(ValueError):
            tree.unroot()

class Tree_midroot_test(unittest.TestCase):
    def compare_trees(self, tree1, tree2):
        tree1.lateralize()
        tree2.lateralize()
        return self.r_compare(tree1.base, tree2.base)

    def r_compare(self, node1, node2):
        self.assertEqual(node1.num_children, node2.num_children, 'different structure / different number of children')
        if node1.num_children > 0:
            for child1, child2 in zip(node1.children(), node2.children()):
                self.assertAlmostEqual(child1.parent_branch, child2.parent_branch, msg='difference in branch length')
                self.r_compare(child1, child2)
        else:
            self.assertEqual(node1.label, node2.label, msg='label mismatch')

    def f_test(self, tree, expect):
        tree = egglib.Tree(string=tree)
        expect = egglib.Tree(string=expect)
        tree.midroot()
        self.compare_trees(tree, expect)

    def test_root_away(self):
        self.f_test(tree='((A:2.0,B:1.0):3.0,(C:1.0,D:1.0):3.0,(E:1.0,F:2.0):5.0);',
                    expect='((E:1.0,F:2.0):4.0,((A:2.0,B:1.0):3.0,(C:1.0,D:1.0):3.0):1.0);')

    def test_multiple_paths(self):
        self.f_test(tree='((A:2.0,B:1.0):3.0,(C:2.0,D:1.0):3.0,(E:1.0,F:2.0):5.0);',
                    expect='((E:1.0,F:2.0):4.0,((A:2.0,B:1.0):3.0,(C:2.0,D:1.0):3.0):1.0);')

    def test_root_proxi(self):
        self.f_test(tree='((A:2.0,B:1.0):5.0,(C:1.0,D:1.0):3.0,(E:1.0,F:2.0):3.0);',
                    expect='((A:2.0,B:1.0):4.0,((C:1.0,D:1.0):3.0,(E:1.0,F:2.0):3.0):1.0);')
