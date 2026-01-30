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

import os, egglib, unittest, pathlib, tempfile
import collections
path = pathlib.Path(__file__).parent / '..' / 'data'

#GLOBAL VARIABLES FOR THE CLASS GENBANK:
positions=("1..1374,1528..2664,2756..3637,3647..3850,3948..4313,4381..5514,5672..6241,9785..10057,"
       "10535..11815,11816..13084,13092..13634,13656..15629,15967..16437,22900..23736,24287..25582,"
       "25685..26653,26740..27918,30050..30757,30761..34489,34492..35946,35987..37024,37582..39129,"
       "39255..40517,40543..41031,41180..42097,42141..42902,42975..44201,44203..45495,45902..46066,"
       "46411..47160,47170..47748,49838..51550,51652..51825,52120..53121,53869..54504,54736..55650,"
       "56055..57089,58268..59494,59519..59632,59685..61208,63302..63892,64533..65186,65187..66404,"
       "66456..67607,67843..68241,68341..68607,69038..69358")

positions_F=("1..1374,1528..2664,2756..3637,3647..3850,3948..4313,4381..5514,5672..6241,6241..9735,9785..10057,"
             "10044..10412,10409..10522,10535..11815,11816..13084,13092..13634,13656..15629,15967..16437,"
         "22900..23736,23726..24241,24287..25582,25685..26653,26740..27918,27905..28687,28684..29691,"
         "29684..29932,30050..30757,30761..34489,34492..35946,35987..37024,37021..37572,37582..39129,"
         "39255..40517,40543..41031,41180..42097,42141..42902,42975..44201,44203..45495,45902..46066,"
         "46411..47160,47170..47748,47709..48191,48184..49056,49056..49835,49838..51550,51652..51825,"
         "52120..53121,53121..53867,53869..54504,54736..55650,56055..57089,58268..59494,59519..59632,"
         "59685..61208,61205..61342,61323..63263,63302..63892,64533..65186,65187..66404,66456..67607,"
         "67843..68241,68341..68607,68607..69026,69038..69358")

position_MtChr2=("3644..5878,5950..5958,6182..6221,7110..7501,11376..11978,12092..12169,12561..12804,"
                "13200..13290,13753..13891,14477..14899,14987..15184,16128..16239,16346..16458,18831..18931,"
                "19048..19108,19221..19493,19881..19943,20032..20131,20443..20525,21480..21533,22105..22182,"
                "22276..22332,22407..22622,23909..24046,24214..24384,24917..25129,25566..26114,26840..26983,"
                "38765..39166,39230..39696,39903..40111,40332..40894,40955..41281,49014..49415,49513..49581,"
                "49668..50276,50445..50627,50722..50781,50882..51085,51246..51494,51710..51808,52984..53178,"
                "53552..53644,53752..54018,54215..54433,57408..57544,57959..57986,60428..61024,61175..61257,"
                "62081..62445,62872..62998,70784..70795,71844..72154,72647..72743,72826..72903,73553..74269,"
                "75534..75899,77481..78245,78305..78451,79456..79659,79770..80000,83525..83683,85767..86033,"
                "86109..86216,86314..86866,86961..87350,88883..88899,89974..90135,90383..90461,90651..90775,"
                "92092..92424,94554..94627,94699..94762,95107..95254,95459..95577,96925..97192,97270..97706,"
                "98016..98132,98231..98527")

position_MtChr2E=("3644..5878,5950..5958,6182..6221,7110..7501,11376..11978,12092..12169,12561..12804,"
                "13200..13290,13753..13891,14477..14899,14987..15184,16128..16239,16346..16458,18831..18931,"
                "19048..19108,19221..19493,19881..19943,20032..20131,20443..20525,21480..21533,22105..22182,"
                "22276..22332,22407..22622,23909..24046,24214..24384,24917..25129,25566..26114,26840..26983,"
                "38765..39166,39230..39696,39903..40111,40332..40894,40955..41281,49014..49415,49513..49581,"
                "49668..50276,50445..50627,50722..50781,50882..51085,51246..51494,51710..51808,52984..53178,"
                "53552..53644,53752..54018,54215..54433,57408..57544,57959..57986,60428..61024,61175..61257,"
                "62081..62445,62872..62998,70784..70795,71844..72154,72647..72743,72826..72903,73553..74269,"
                "75534..75899,77481..78245,78305..78451,79456..79659,79770..80000,83525..83683,85767..86033,"
                "86109..86216,86314..86866,86961..87350,88883..88899,89974..90135,90383..90461,90651..90775,"
                "92092..92424,94554..94627,94699..94762,95107..95254,95459..95577,96925..97192,97270..97706,"
                "98016..98132,98231..98527,110000..110504") #list of locations with an error: 110000..110504

def total_pb(positions):
    """
    This method indicate the number of bases covered by all segments

        :param positions: a string whicht contains all the positions
        """
    total=0
    list_pos=[]
    list_pos=positions.split(',')
    for i in list_pos:
        start,end=i.split('..')
        total += (int(end)-int(start))+1
    return total

class GenBankFeatureLocation_test(unittest.TestCase):

    def setUp(self):
        global positions
        self.gbfl= egglib.io.GenBankFeatureLocation(positions)

    def tearDown(self):
        del self.gbfl

    def test_GenbankFeature_T(self):
        self.assertIsInstance(self.gbfl, egglib.io._genbank.GenBankFeatureLocation)


    def test__len__T(self):
        global positions
        self.assertEqual(len(self.gbfl), 47)


    def test__getitem__T(self):
        self.assertEqual(self.gbfl[2], (2755, 3636))
    
    
    def test__str__T(self):
        self.assertIsInstance(str(self.gbfl), str)


    def test__str__E(self):
        gbfl= egglib.io.GenBankFeatureLocation()
        with self.assertRaises(RuntimeError):
            str(gbfl)

    def test_copy_T(self):
        c=self.gbfl.copy()
        self.assertEqual(str(self.gbfl[35]), str(c[35]))
        self.assertEqual(len(self.gbfl), len(c))

    def test_set_comp_T(self):
        self.assertFalse(self.gbfl.is_complement())
        self.gbfl.set_complement()
        self.assertTrue(self.gbfl.is_complement())

    def test_set_forw_T(self):
        self.gbfl.set_complement()
        self.assertTrue(self.gbfl.is_complement())
        self.gbfl.set_forward()
        self.assertFalse(self.gbfl.is_complement())

    def test_is_comp_T(self):
        self.gbfl.set_complement()
        self.assertTrue(self.gbfl.is_complement())

    def test_as_ord_T(self):
        self.gbfl.as_order()
        self.assertFalse(self.gbfl.is_range())

    def test_as_ran_T(self):
        self.gbfl.as_range()
        self.assertTrue(self.gbfl.is_range())

    def test_is_ran_T(self):
        self.gbfl.as_range()
        self.assertTrue(self.gbfl.is_range())
        self.gbfl.as_order()
        self.assertFalse(self.gbfl.is_range())

    def test_shift_T(self):
        self.assertEqual(self.gbfl[0],(0, 1373))
        self.gbfl.shift(1)
        self.assertEqual(self.gbfl[0],[1, 1374])
        self.assertNotEqual(self.gbfl[0],[0, 1373]) #with shitf gbfl[i] return a list not a tuple

    def test_add_single_base_T(self):
        ns_a=len(self.gbfl)
        positions_n=69370
        self.gbfl.add_single_base(positions_n)
        ns_b=len(self.gbfl)
        self.assertTrue(ns_a<ns_b)

    def test_add_single_base_E(self):
        positions_n='69370'
        with self.assertRaises(TypeError):
            self.gbfl.add_single_base(positions_n)
        positions_n2=65000
        with self.assertRaises(ValueError):
            self.gbfl.add_single_base(positions_n2)

    def test_add_between_base_T(self):
        ns_a=len(self.gbfl)
        positions_n=69370
        self.gbfl.add_between_base(positions_n)
        ns_b=len(self.gbfl)
        self.assertTrue(ns_a<ns_b)

    def test_add_between_base_E(self):
        positions_n='69370'
        with self.assertRaises(TypeError):
            self.gbfl.add_between_base(positions_n)
        positions_n2=65000
        with self.assertRaises(ValueError):
            self.gbfl.add_between_base(positions_n2)

    def test_add_base_range_T(self):
        ns_a=len(self.gbfl)
        start=69670
        end=69850
        self.gbfl.add_base_range(start,end)
        ns_b=len(self.gbfl)
        self.assertTrue(ns_a<ns_b)

    def test_add_base_range_E(self):
        start='69370'
        end='69850'
        with self.assertRaises(TypeError):
            self.gbfl.add_base_range(start,end)
        start_2=65000
        end_2=67350
        with self.assertRaises(ValueError):
            self.gbfl.add_base_range(start_2, end_2)
        start_3=70000
        end_3=69950
        with self.assertRaises(ValueError):
            self.gbfl.add_base_range(start_3, end_3)

    def test_add_base_choice_T(self):
        ns_a=len(self.gbfl)
        start=69670
        end=69850
        self.gbfl.add_base_choice(start,end)
        ns_b=len(self.gbfl)
        self.assertTrue(ns_a<ns_b)

    def test_add_base_choice_E(self):
        start='69370'
        end='69850'
        with self.assertRaises(TypeError):
            self.gbfl.add_base_choice(start,end)
        start_2=65000
        end_2=67350
        with self.assertRaises(ValueError):
            self.gbfl.add_base_choice(start_2, end_2)
        start_3=70000
        end_3=69950
        with self.assertRaises(ValueError):
            self.gbfl.add_base_choice(start_3, end_3)
        start_4=69650
        end_4=69650
        with self.assertRaises(ValueError):
            self.gbfl.add_base_choice(start_4, end_4)

    def test_rc_T(self):
        ns_a=len(self.gbfl)
        l1_loc=self.gbfl[ns_a-1]
        end_1=l1_loc[1]
        l_seq=70000
        self.gbfl.rc(l_seq)
        f2_loc=self.gbfl[0]
        start_2=f2_loc[0]
        self.assertEqual(((l_seq-1)-end_1),start_2)
    
class GenbankFeature_test(unittest.TestCase):
    def setUp(self):
        global positions
        self.gbfl= egglib.io.GenBankFeatureLocation(positions)
        self.gbf= egglib.io.GenBankFeature(self.gbfl)

    def tearDown(self):
        del self.gbfl
        del self.gbf

    def test_GenbankFeature_T(self):
        self.assertIsInstance(self.gbf, egglib.io._genbank.GenBankFeature)

    def test_type_T(self):
        global positions
        gbfl= egglib.io.GenBankFeatureLocation(positions)
        gbf= egglib.io.GenBankFeature(gbfl)
        self.assertEqual(gbf.get_type(), '')

    def test_qualifiers_T(self):
        dict_q=self.gbf.qualifiers()
        self.assertEqual(len(dict_q), 0)

    def test_add_qualifiers_T(self):
        dict_q1=self.gbf.qualifiers()
        self.gbf.add_qualifier('note', 'This is an example of "note" for the add_qualifer test')
        dict_q2=self.gbf.qualifiers()
        self.assertTrue(len(dict_q1)< len(dict_q2))

    def test_update_T(self):
        p1=self.gbf._parent
        q1=self.gbf._qualifiers
        positions_n='join(11376..11978,12092..12169,12561..12804,13200..13290,13753..13891,14477..14899,14987..15184)'
        gbfl= egglib.io.GenBankFeatureLocation(positions_n)
        qualifiers={'gene':'AC140550_58','label':'Bromodomain', 'note':'This is an example of set for the set test'}

        self.gbf.update("CDS", gbfl, ** qualifiers)
        p2=self.gbf._parent
        q2=self.gbf._qualifiers
                
        self.assertEqual(p1,p2)
        self.assertTrue(len(q1)<len(q2))
        self.assertEqual(self.gbf._type, 'CDS')
        self.assertIsNotNone(self.gbf._location)

    def test_update_E(self):
        positions_n='join(11376..11978,12092..12169,12561..12804,13200..13290,13753..13891,14477..14899,14987..15184)'
        qualifiers={'gene':'AC140550_58','type':'Bromodomain', 'note':'This is an example of set for the set test'}
        gbfl= egglib.io.GenBankFeatureLocation(positions_n)
        with self.assertRaises(ValueError):
            self.gbf.update("CDS" , gbfl, ** qualifiers)

    def test_parse_T(self):
        information=("     CDS             join(6182..6221,7110..7501)                     \n"
                     "/gene='AC140550_57'                     \n"
                     "/label=Protein kinase"
                )
        self.gbf.parse(information)
        self.assertEqual(self.gbf._type, 'CDS')
        self.assertEqual(str(self.gbf._location),'join(6182..6221,7110..7501)')
        self.assertTupleEqual(self.gbf._qualifiers[1], ('label', 'Protein kinase'))

    def test_parse_E(self):
        information=("CDSjoin(6182..6221,7110..7501)/gene: 'AC140550_57'/label: Protein kinase")
        with self.assertRaises(IOError):
            self.gbf.parse(information)
    
        information=("     CDS             join(6182..6221,7110..7501)                     \n"
                     "gene='AC140550_57'                     \n"
                     "label=Protein kinase"
                )
        with self.assertRaises(IOError):
            self.gbf.parse(information)
            information=("     CDS             join(6182..6221,7110..7501)                     \n"
                     "/gene: 'AC140550_57'                     \n"
                     "/label: Protein kinase"
                )
        with self.assertRaises(IOError):
            self.gbf.parse(information)

    def test_get_sequence_T(self):
        fname_s='MtChr2_315000-415000.gb'
        gb= egglib.io.GenBank(os.path.join(path, fname_s))
        gbf= egglib.io.GenBankFeature(gb)
        global position_MtChr2

        n= egglib.io.GenBankFeatureLocation(position_MtChr2)
        gbf.update("CDS",n)

        self.assertEqual(len(gbf.get_sequence()),total_pb(position_MtChr2)) #len: counts all bases in the sequence returned

    def test_get_sequence_E(self):
        fname_s='MtChr2_315000-415000.gb'
        gb= egglib.io.GenBank(os.path.join(path, fname_s))
        gbf= egglib.io.GenBankFeature(gb)
        global position_MtChr2E

        n= egglib.io.GenBankFeatureLocation(position_MtChr2E)
        gbf.update("CDS",n)
        with self.assertRaises(RuntimeError):
            gbf.get_sequence()

    def test_start_T(self):
        self.gbf.update("CDS",self.gbfl)
        self.assertEqual(self.gbf.get_start(),0)

    def test_stop_T(self):
        self.gbf.update("CDS",self.gbfl)
        self.assertEqual(self.gbf.get_stop(),69357)

    def test_copy_T(self):
        fname_s='MtChr2_315000-415000.gb'
        gb= egglib.io.GenBank(os.path.join(path, fname_s))
        gbf= egglib.io.GenBankFeature(gb)
        global position_MtChr2
        n= egglib.io.GenBankFeatureLocation(position_MtChr2)
        gbf.update("CDS",n)
        new=gbf.copy(gb)
        t_gbfn=str(type(new))

        self.assertEqual(t_gbfn, "<class 'egglib.io._genbank.GenBankFeature'>")
        self.assertEqual(new.get_sequence(), gbf.get_sequence())

    def test_shift_T(self):
        self.gbf.update("CDS",self.gbfl)
        self.gbf.shift(100) #shifting on 100 bases
        self.assertEqual(self.gbf.get_start(),100)
        self.assertEqual(self.gbf.get_stop(),69457)

    def test_rc_T(self):
        fname_s='MtChr2_315000-415000.gb'
        gb= egglib.io.GenBank(os.path.join(path, fname_s))
        gbf= egglib.io.GenBankFeature(gb)
        global position_MtChr2
        gbfl= egglib.io.GenBankFeatureLocation(position_MtChr2)
        gbf.update("CDS",gbfl)

        total_b=(100001-1) #-1, because there is 100001 bases but in the class 'gbf', bases are counted starting at 0 not 1
        end1=gbf.get_stop()
        gbf.rc()
        start2=gbf.get_start()
        self.assertEqual((total_b-end1),start2)


class Genbank_test(unittest.TestCase):
    def setUp(self):
        fname_s='MtChr2_315000-415000.gb'
        self.gb= egglib.io.GenBank(os.path.join(path, fname_s))
        f, self.fname = tempfile.mkstemp()
        os.close(f)

    def tearDown(self):
        del self.gb
        if os.path.isfile(self.fname):
            os.remove(self.fname)

    def test_Genbank_T(self):
        self.assertIsInstance(self.gb, egglib.io._genbank.GenBank)

    def test_add_feature_T(self):
        global position_MtChr2
        gbfl= egglib.io.GenBankFeatureLocation(position_MtChr2)
        gbf= egglib.io.GenBankFeature(gbfl)
        n_feat1= len(self.gb._features)
        information=("     CDSnew             join(0000..0000,0000..0000)                     \n"
                     "/gene='IDK00000'                     \n"
                     "/label=Protein IDK000"
                )
        gbf.parse(information)
        self.gb.add_feature(gbf)
        n_feat2= len(self.gb._features)
        self.assertTrue(n_feat1<n_feat2)
    
    def test_n_of_features_T(self):
        self.assertEqual(self.gb.number_of_features(),83)

    def test_get_sequence_T(self):
        l_seq= len(self.gb.sequence)
        self.assertEqual(l_seq,100001)

    def test_set_sequence_T(self):
        l_seq1= len(self.gb.sequence)
        self.gb.sequence='CATGTTGTGTGTTGTTGTCATTGAGGTAACAATTGATTCATATCGTTTCTGTGAGTTTACTGTTGTTGGAACAGAAATTTGGAATTTGTGATTAAACGTT'
        l_seq2= len(self.gb.sequence)
        self.assertEqual(l_seq2,100)
        self.assertTrue(l_seq1>l_seq2)

    def test__iter__T(self):
        self.assertIsInstance(self.gb, collections.abc.Iterable)

    def test_extract_T(self):
        l_gb= len(self.gb)
        gb_ss=self.gb.extract(3000,16000)
        l_gb_ss= len(gb_ss)
        n_ft_gb=self.gb.number_of_features()
        n_ft_gbss=gb_ss.number_of_features()
        self.assertTrue(l_gb>l_gb_ss)
        self.assertTrue(n_ft_gb>n_ft_gbss)

    def test_extract_E(self):
        l_gb= len(self.gb)
        with self.assertRaises(ValueError):
            gb_ss=self.gb.extract(3000,160000)
        with self.assertRaises(ValueError):
            gb_ss=self.gb.extract(-3000,160000)

    def test_write_T(self):
        self.gb.write(self.fname)
        self.assertTrue(os.path.exists(self.fname))
        self.assertTrue(os.path.getsize(self.fname)>0)

    def test__str__T(self):
        self.assertIsInstance(str(self.gb), str)

    def test_write_stream_T(self):
        gb_ss=self.gb.extract(3000,16000)
        f = open(self.fname, 'w')
        gb_ss.write_stream(f) 
        self.assertTrue(os.path.exists(self.fname))
        self.assertTrue(os.path.getsize(self.fname)>0)
        f.close()

    def test_write_stream_E(self):
        with self.assertRaises(TypeError):
            self.gb.write_stream(self.fname) #erreur avec fname
        seq='CATGTTGTGTGTTGTTGTCATTGAGGTAACAATTGATTCATATCGTTTCTGTGAGTTTACTGTTGTTGGAACAGAAATTTGGAATTTGTGATTAAACGTT'
        sequence= seq*10000000
        self.gb.sequence=sequence
        f = open(self.fname, 'w')
        with self.assertRaises(IOError):
            self.gb.write_stream(f)
        f.close()

    def test_rc_T(self):
        sequence=self.gb.sequence
        total_b=(100001-1)
        end1=self.gb._features[(83-1)].get_stop()
        dict_f1=self.gb._features[0].qualifiers()
        g1=dict_f1['gene']
        self.gb.rc()

        sequence_rc=self.gb.sequence
        start2=self.gb._features[0].get_start()
        dict_f2=self.gb._features[(83-1)].qualifiers()

        g2=dict_f1['gene']
    
        self.assertNotEqual(sequence, sequence_rc)
        self.assertEqual((total_b-end1),start2)
        self.assertEqual(g1,g2)



