"""
    Copyright 2025 Thomas Coudoux, Stéphane De Mita, Mathieu Siol

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

import unittest, egglib, pathlib, os, collections, tempfile, shutil
path = pathlib.Path(__file__).parent / '..' / 'data'

HEADER="""##fileformat=VCFv4.0
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##FORMAT=<ID=AD,Number=.,Type=Integer,Description="Allelic depths for the ref and alt alleles in the order listed">
##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read Depth (only filtered reads used for calling)">
##FORMAT=<ID=GQ,Number=1,Type=Float,Description="Genotype Quality">
##FORMAT=<ID=PL,Number=3,Type=Float,Description="Normalized, Phred-scaled likelihoods for AA,AB,BB genotypes where A=ref and B=alt; not applicable if site is not biallelic">
##INFO=<ID=NS,Number=1,Type=Integer,Description="Number of Samples With Data">
##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">
##INFO=<ID=AF,Number=.,Type=Float,Description="Allele Frequency">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	100:D2E25ACXX:4:250229753	101:D2E25ACXX:4:250229754	102:D2E25ACXX:4:250229755	103:D2E25ACXX:4:250229756	104:D2E25ACXX:4:250229757	105:D2E25ACXX:4:250229758	106:D2E25ACXX:4:250229759	107:D2E25ACXX:4:250229760	108:D2E25ACXX:4:250229761	109:D2E25ACXX:4:250229762	10:C2BWMACXX:6:250229503	110:D2E25ACXX:4:250229763	111:D2E25ACXX:4:250229764	112:D2E25ACXX:4:250229765	113:C2BWMACXX:6:250229542	114:C2BWMACXX:6:250229543	115:C2BWMACXX:6:250229544	116:C2BWMACXX:6:250229545	117:C2BWMACXX:6:250229546	118:C2BWMACXX:6:250229547	119_2:D2E25ACXX:4:250229841	11:C2BWMACXX:6:250229504	120:C2BWMACXX:6:250229549	121:C2BWMACXX:6:250229550	122:C2BWMACXX:6:250229551	123_2:D2E25ACXX:4:250229842	125:C2BWMACXX:6:250229553	126:C2BWMACXX:6:250229554	127:C2BWMACXX:6:250229555	128:C2BWMACXX:6:250229556	129:C2BWMACXX:6:250229557	12:C2BWMACXX:6:250229505	130:C2BWMACXX:6:250229558	131:C2BWMACXX:6:250229559	132:C2BWMACXX:6:250229560	133:C2BWMACXX:6:250229561	134:C2BWMACXX:6:250229562	135:C2BWMACXX:6:250229563	137:C2BWMACXX:6:250229564	138:C2BWMACXX:6:250229565	139:C2BWMACXX:6:250229566	13:C2BWMACXX:6:250229506	140_2:D2E25ACXX:4:250229833	141:C2BWMACXX:6:250229568	142:C2BWMACXX:6:250229569	143:C2BWMACXX:6:250229570	144:C2BWMACXX:6:250229571	145:C2BWMACXX:6:250229572	146:C2BWMACXX:6:250229573	147:C2BWMACXX:6:250229574	148:C2BWMACXX:6:250229575	149:C2BWMACXX:6:250229576	14:C2BWMACXX:6:250229507	150:C2BWMACXX:6:250229577	151:C2BWMACXX:6:250229578	152:C2BWMACXX:6:250229579	153:C2BWMACXX:6:250229580	154:C2BWMACXX:6:250229581	155:C2BWMACXX:6:250229582	157:C2BWMACXX:6:250229583	158:C2BWMACXX:6:250229584	159:C2BWMACXX:6:250229585	15:C2BWMACXX:6:250229508	160:C2BWMACXX:6:250229586	161:C2BWMACXX:6:250229587	164:C2BWMACXX:6:250229588	165:C2BWMACXX:6:250229589	166:C2HA1ACXX:6:250229621	167:C2HA1ACXX:6:250229622	169:C2HA1ACXX:6:250229623	16:C2BWMACXX:6:250229509	170:C2HA1ACXX:6:250229624	171:C2HA1ACXX:6:250229625	172:C2HA1ACXX:6:250229626	175:C2HA1ACXX:6:250229627	176:C2HA1ACXX:6:250229628	177:C2HA1ACXX:6:250229629	178:C2HA1ACXX:6:250229630	179:C2HA1ACXX:6:250229631	17:C2BWMACXX:6:250229510	180:C2HA1ACXX:6:250229632	181:C2HA1ACXX:6:250229633	182:C2HA1ACXX:6:250229634	183:C2HA1ACXX:6:250229635	184:C2HA1ACXX:6:250229636	185:C2HA1ACXX:6:250229637	186:C2HA1ACXX:6:250229638	187_2:D2E25ACXX:4:250229835	188:C2HA1ACXX:6:250229640	189:C2HA1ACXX:6:250229641	18:C2BWMACXX:6:250229511	190:C2HA1ACXX:6:250229642	191:C2HA1ACXX:6:250229643	192:C2HA1ACXX:6:250229644	193:C2HA1ACXX:6:250229645	195:C2HA1ACXX:6:250229646	196:C2HA1ACXX:6:250229647	197:C2HA1ACXX:6:250229648	198:C2HA1ACXX:6:250229649	199:C2HA1ACXX:6:250229650	19:C2BWMACXX:6:250229512	1:C2BWMACXX:6:250229494	200:C2HA1ACXX:6:250229651	201:C2HA1ACXX:6:250229652	202:C2HA1ACXX:6:250229653	203:C2HA1ACXX:6:250229654	204:C2HA1ACXX:6:250229655	205:C2HA1ACXX:6:250229656	206:C2HA1ACXX:6:250229657	207:C2HA1ACXX:6:250229658	208:C2HA1ACXX:6:250229659	209:C2HA1ACXX:6:250229660	20:C2BWMACXX:6:250229514	210:C2HA1ACXX:6:250229661	211:C2HA1ACXX:6:250229662	212_2:D2E25ACXX:4:250229837	213:C2HA1ACXX:6:250229664	214:C2HA1ACXX:6:250229665	215:C2HA1ACXX:6:250229666	216:C2HA1ACXX:6:250229667	217:C2HA1ACXX:6:250229668	218:D2E25ACXX:4:250229766	219:D2E25ACXX:4:250229767	21:C2BWMACXX:6:250229515	221:D2E25ACXX:4:250229768	222:D2E25ACXX:4:250229769	223:D2E25ACXX:4:250229770	224:D2E25ACXX:4:250229771	225:D2E25ACXX:4:250229772	226:D2E25ACXX:4:250229773	227:D2E25ACXX:4:250229774	228:D2E25ACXX:4:250229775	229:D2E25ACXX:4:250229776	22:C2BWMACXX:6:250229516	231_2:D2E25ACXX:4:250229843	232:D2E25ACXX:4:250229778	233_2:D2E25ACXX:4:250229839	234:D2E25ACXX:4:250229780	235:D2E25ACXX:4:250229781	236:D2E25ACXX:4:250229782	237:D2E25ACXX:4:250229783	238:D2E25ACXX:4:250229784	239:D2E25ACXX:4:250229785	23_2:D2E25ACXX:4:250229820	240:D2E25ACXX:4:250229786	242:D2E25ACXX:4:250229787	243:D2E25ACXX:4:250229788	244:D2E25ACXX:4:250229789	245:D2E25ACXX:4:250229790	246:D2E25ACXX:4:250229791	247:D2E25ACXX:4:250229792	248:D2E25ACXX:4:250229793	249_2:D2E25ACXX:4:250229840	24:C2BWMACXX:6:250229518	250:D2E25ACXX:4:250229795	251:D2E25ACXX:4:250229796	252:D2E25ACXX:4:250229797	253:D2E25ACXX:4:250229798	254:D2E25ACXX:4:250229799	255:D2E25ACXX:4:250229800	256:D2E25ACXX:4:250229801	257:D2E25ACXX:4:250229802	258:D2E25ACXX:4:250229803	259:D2E25ACXX:4:250229804	25:C2BWMACXX:6:250229519	260:D2E25ACXX:4:250229805	261:D2E25ACXX:4:250229806	262:D2E25ACXX:4:250229807	263:D2E25ACXX:4:250229808	264:D2E25ACXX:4:250229809	265:D2E25ACXX:4:250229810	266:D2E25ACXX:4:250229811	267:D2E25ACXX:4:250229812	268:D2E25ACXX:4:250229813	269:D2E25ACXX:4:250229814	26:C2BWMACXX:6:250229520	270:D2E25ACXX:4:250229815	271:D2E25ACXX:4:250229816	272:D2E25ACXX:4:250229817	273:D2E25ACXX:4:250229818	27:C2BWMACXX:6:250229521	28:C2BWMACXX:6:250229522	29:C2BWMACXX:6:250229523	2:C2BWMACXX:6:250229495	30:C2BWMACXX:6:250229524	31:C2BWMACXX:6:250229525	32:C2BWMACXX:6:250229526	33:C2BWMACXX:6:250229527	34:C2BWMACXX:6:250229528	35:C2BWMACXX:6:250229529	36:C2BWMACXX:6:250229530	37:C2BWMACXX:6:250229531	38_2:D2E25ACXX:4:250229823	39:C2BWMACXX:6:250229533	3:C2BWMACXX:6:250229496	40_2:D2E25ACXX:4:250229824	41:C2BWMACXX:6:250229535	42:C2BWMACXX:6:250229536	43:C2BWMACXX:6:250229537	44:C2BWMACXX:6:250229538	45:C2BWMACXX:6:250229539	46:C2BWMACXX:6:250229540	47:C2BWMACXX:6:250229541	48:C2HA1ACXX:6:250229669	49:C2HA1ACXX:6:250229671	4:C2BWMACXX:6:250229497	50:C2HA1ACXX:6:250229672	51:C2HA1ACXX:6:250229673	52:C2HA1ACXX:6:250229674	53:C2HA1ACXX:6:250229675	54:C2HA1ACXX:6:250229676	55:C2HA1ACXX:6:250229677	56:C2HA1ACXX:6:250229678	57:C2HA1ACXX:6:250229679	58:C2HA1ACXX:6:250229680	59:C2HA1ACXX:6:250229681	5:C2BWMACXX:6:250229498	60:C2HA1ACXX:6:250229682	61:C2HA1ACXX:6:250229683	62:C2HA1ACXX:6:250229684	63:C2HA1ACXX:6:250229685	64:C2HA1ACXX:6:250229686	65:C2HA1ACXX:6:250229687	66:C2HA1ACXX:6:250229688	67:C2HA1ACXX:6:250229689	68:C2HA1ACXX:6:250229690	69:C2HA1ACXX:6:250229691	6:C2BWMACXX:6:250229499	70:C2HA1ACXX:6:250229692	71:C2HA1ACXX:6:250229693	72_2:D2E25ACXX:4:250229825	73_2:D2E25ACXX:4:250229826	74:C2HA1ACXX:6:250229696	75:C2HA1ACXX:6:250229697	76:C2HA1ACXX:6:250229698	77:C2HA1ACXX:6:250229699	78:C2HA1ACXX:6:250229700	79_2:D2E25ACXX:4:250229828	7:C2BWMACXX:6:250229500	80:C2HA1ACXX:6:250229702	81:C2HA1ACXX:6:250229703	82:C2HA1ACXX:6:250229704	83:C2HA1ACXX:6:250229705	84:C2HA1ACXX:6:250229706	85:C2HA1ACXX:6:250229707	86:C2HA1ACXX:6:250229708	87:C2HA1ACXX:6:250229709	88:C2HA1ACXX:6:250229710	89:C2HA1ACXX:6:250229711	8:C2BWMACXX:6:250229501	90_2:D2E25ACXX:4:250229829	91:C2HA1ACXX:6:250229713	92:C2HA1ACXX:6:250229714	93:C2HA1ACXX:6:250229715	94:C2HA1ACXX:6:250229716	95:D2E25ACXX:4:250229748	96:D2E25ACXX:4:250229749	97:D2E25ACXX:4:250229750	98:D2E25ACXX:4:250229751	99_2:D2E25ACXX:4:250229830	9:C2BWMACXX:6:250229502"""

# helper functions
def get_vcf_positions(fname, chromosome):
    vcf_positions = []
    with open(fname, "r") as f:
        for line in f:
            if (    line[0] != "#" and  # not a header line
                    line.split("\t")[0] == chromosome and # is right chromosome
                    len(line.split('\t')[3]) == 1 and # not an indel
                    set(map(len, line.split('\t')[4].split(','))) == set([1])): # not an indel (alternate allele(s))
                vcf_positions.append((int(line.split("\t")[1])-1)) #-1 for variant
    return vcf_positions

def get_slider_bounds(wdw):
    return [win.bounds for win in wdw]

def get_slider_extremes(wdw):
    return [(win[0].position, win[-1].position) if len(win) > 0 else None for win in wdw]

def get_bounds(size, step, num):
    ret = []
    i = 0
    while True:
        ret.append((i, i+size))
        if i+size >= num:
            break
        i += step
    return ret

def get_bounds_as_variants(pos, size, step):
    ret = []
    i = 0
    while True:
        ret.append((pos[i], pos[min(i+size-1, len(pos)-1)]+1))
        if i+size >= len(pos):
            break
        i += step
        if i >= len(pos):
            break
    return ret

def get_extremes(positions, size, step):
    bounds = get_bounds(size, step, positions[-1]+1)
    res = [[] for b in bounds]
    i = 0
    j = 0
    for i in range(len(res)):
        assert positions[j] >= bounds[i][0]
        first = positions[j]
        last = None
        while j < len(positions) and positions[j] < bounds[i][1]:
            last = positions[j]
            j += 1
        if last is None: res[i] = None
        else: res[i] = first, last
        if j == len(positions): break
    assert j == len(positions)
    return res

def get_extremes_as_variants(positions, size, step):
    return [(a, b-1) for (a, b) in get_bounds_as_variants(positions, size, step)]

class VCF_legacy_test(unittest.TestCase):
    def setUp(self):
        fname = path / 'merged_filt_depth_75_200_ssduplicateindANDsnp-ssblanck_DEF_for_structure.vcf'
        f, self.vcff = tempfile.mkstemp(suffix='.vcf')
        os.close(f)
        f, self.index1 = tempfile.mkstemp()
        os.close(f)
        f, self.index2 = tempfile.mkstemp()
        os.close(f)
        egglib.io.make_vcf_index(str(fname), self.index1)
        self.vcf = egglib.io.VcfParser(str(fname))
        fname1 = path / 'human_fragment.vcf'
        fname_i = path / 'human_fragment.vcfi'
        self.vcf_h = egglib.io.VcfParser(str(fname1))
        self.vcf_h.load_index(str(fname_i))

    def tearDown(self):
        if os.path.isfile(self.index1): os.remove(self.index1)
        if os.path.isfile(self.index2): os.remove(self.index2)
        if os.path.isfile(self.vcff): os.remove(self.vcff)

    def test_VCF_T(self):
        self.assertIsInstance(self.vcf, egglib.io.VcfParser)

    def test_PLGL_missing(self):
        fname = path / 'fragment_PL_missing.vcf'
        vcf = egglib.io.VcfParser(str(fname))
        ctrl = [[(0,10,100), (0,10,100), (50,0,100), (None, None, None)],
                [(0,10,100), (0,10,100), None, (100, 0, 100)],
                [(0,-10,-100), (0.001,-10,-4.37), (-7.32,-0.05,-17.334), None],
                [None, (0,1,2), None, (0, 1, 2)]]
        c = 0
        for ch, pos, na in vcf:
            var = vcf.get_variant()
            if 'PL' in var.samples[0]: check = [sample['PL'] for sample in var.samples]
            else: check = [sample['GL'] for sample in var.samples]
            self.assertEqual(check, ctrl[c])                
            c += 1

    def test_invalid_fname(self):
        with self.assertRaisesRegex(OSError, 'error while opening this file'):
            vcf = egglib.io.VcfParser('not.exist')
        with self.assertRaisesRegex(TypeError, 'invalid fname'):
            vcf = egglib.io.VcfParser(None)
        with self.assertRaisesRegex(TypeError, 'invalid fname'):
            vcf = egglib.io.VcfParser(4)

    def test_from_header_T(self):
        global HEADER
        vcf = egglib.io.VcfStringParser(HEADER)
        self.assertIsInstance(vcf, egglib.io.VcfStringParser)

    def test_properties_T(self):
        self.assertEqual(self.vcf.file_format , 'VCFv4.0')
        self.assertEqual(self.vcf.num_info ,41)
        self.assertEqual(self.vcf.num_format ,20)
        self.assertEqual(self.vcf.num_filter ,1)
        self.assertEqual(self.vcf.num_alt ,8)
        self.assertEqual(self.vcf.num_meta ,4)
        self.assertEqual(self.vcf.num_samples ,261)

    def test_get_sample_T(self):
        self.assertEqual(self.vcf.get_sample(0),'100:D2E25ACXX:4:250229753')

    def test_get_sample_E(self):
        with self.assertRaises(IndexError):
            self.vcf.get_sample(10000)

    def test_get_info_T(self):
        information=self.vcf.get_info(0)
        self.assertEqual(information, {'type': 'String', 'extra': [], 'number': 1, 'id': 'AA', 'description': 'ancestral allele'})
        self.assertIsInstance(information,dict)
        self.assertTrue(len(information)>0)

    def test_get_info_E(self):
        with self.assertRaises(IndexError):
            self.vcf.get_info(10000)

    def test_get_format_T(self):
        format_0=self.vcf.get_format(0)
        self.assertEqual(format_0, {'type': 'String', 'extra': [], 'number': 1, 'id': 'GT', 'description': 'Genotype'})
        self.assertIsInstance(format_0,dict)
        self.assertTrue(len(format_0)>0)

    def test_get_format_E(self):
        with self.assertRaises(IndexError):
            self.vcf.get_format(10000)

    def test_get_filter_T(self):
        filt=self.vcf.get_filter(0)
        self.assertEqual(filt, {'extra': [], 'id': 'q10', 'description': 'Quality below 10'})
        self.assertIsInstance(filt,dict)
        self.assertTrue(len(filt)>0)

    def test_get_filter_E(self):
        with self.assertRaises(IndexError):
            self.vcf.get_filter(10000)

    def test_get_alt_T(self):
        self.assertIsInstance(self.vcf.get_alt(0),dict)
        self.assertEqual(self.vcf.get_alt(0), {'extra': [], 'id': 'DEL', 'description': 'deletion relative to the reference'})
        self.assertTrue(len(self.vcf.get_alt(0))>0)

    def test_get_alt_E(self):
        with self.assertRaises(IndexError):
            self.vcf.get_alt(10000)

    def test_get_meta_T(self):
        fname = path / 'human_fragment.vcf'
        vcf = egglib.io.VcfParser(str(fname))    
        self.assertIsInstance(vcf.get_meta(0), tuple)
        self.assertEqual(vcf.get_meta(0), ('reference', 'GRCh37'))
        self.assertTrue(len(vcf.get_alt(0))>0)

    def test_get_meta_E(self):
        with self.assertRaises(IndexError):
            self.vcf.get_alt(10000)

    def test__iter__T(self):
        self.assertIsInstance(self.vcf, collections.abc.Iterable)

    def test_next_T(self):
        self.assertIsInstance(next(self.vcf), tuple)
        self.assertEqual(next(self.vcf)[1], 30715)
    
    def test_readline_T(self):
        fname = path / 'human_fragment.vcf'
        my_file = open(str(fname))
        header = []
        for line in my_file:
                header.append(line)
                if line.split()[0] == '#CHROM': break    

        header = ''.join(header)
        vcf = egglib.io.VcfStringParser(header)
        for line in my_file:        
            self.assertIsInstance(vcf.readline(line +'\n'),tuple)
        self.assertIsInstance(vcf, egglib.io.VcfStringParser)
        variant0=vcf.get_variant()
        self.assertEqual(variant0.position, 245679)
        my_file.close()

    def test_get_variant_T(self):
        next(self.vcf)
        l_var = self.vcf.get_variant()
        self.assertIsInstance(l_var, egglib.io.VcfVariant)

    def test_get_genotypes_T(self):
        next(self.vcf_h)
        self.vcf_h.get_variant()    
        gg=egglib.io.VcfParser.get_genotypes(self.vcf_h)
        gg1=self.vcf_h.get_genotypes()
        self.assertIsInstance(gg, egglib.Site)
        self.assertIsInstance(gg1, egglib.Site)

    def test_get_genotypes_E(self):
        aln = egglib.Align(egglib.alphabets.DNA)
        fname_g = path / 'human_fragment.vcf'
        vcf_g=egglib.io.VcfParser(str(fname_g))

        fname_e = path / 'example_E2.vcf'
        vcf_e = egglib.io.VcfParser(str(fname_e))
        
        with self.assertRaises(ValueError):
            vcf_e.get_genotypes() #no arguments in parameter

        with self.assertRaises(AttributeError):
            egglib.io.VcfParser.get_genotypes(aln) # 'Align doesn't have a [random VcfParser member] member'

        with self.assertRaises(ValueError):
            egglib.io.VcfParser.get_genotypes(vcf_e) #exemple_E2 is a file without GT data
        
    def test_load_index_T(self):
        self.vcf.load_index(self.index1)
        self.assertTrue(self.vcf.has_index)

    def test_load_index_E(self):
        fname = path / 'human_fragment.vcfi'
        fname_e = path / 'error.vcfi'
        with self.assertRaises(ValueError):        
            self.vcf.load_index(str(fname))
        
        with self.assertRaises(IOError):        
            self.vcf.load_index(fname_e)

    def test_n_index_T(self):
        self.assertEqual(self.vcf_h.num_index, 106-30)
        vcf = egglib.io.VcfParser(str(path / 'human_fragment.vcf'))
        self.assertEqual(vcf.num_index, 0)

    def test_has_index_T(self):
        self.assertTrue(self.vcf_h.has_index)
        vcf = egglib.io.VcfParser(str(path / 'human_fragment.vcf'))
        self.assertFalse(vcf.has_index)

    def test_index(self):
        # import a VCF without index
        vcf = egglib.io.VcfParser(str(path / 'scaffold_285.vcf'))
        self.assertFalse(vcf.has_index)
        with self.assertRaises(IOError):
            vcf.load_index()

        # create and load default index
        shutil.copy(path / 'scaffold_285.vcf', self.vcff)
        vcf = egglib.io.VcfParser(self.vcff)
        egglib.io.make_vcf_index(self.vcff)
        vcf.load_index()
        self.assertTrue(vcf.has_index)
        self.assertTrue(pathlib.Path(self.vcff + 'i').is_file())

        # create and load non-default index
        egglib.io.make_vcf_index(str(path / 'scaffold_285.vcf'), self.index2)
        vcf = egglib.io.VcfParser(str(path / 'scaffold_285.vcf'))
        vcf.load_index(self.index2)
        self.assertTrue(vcf.has_index, True)
        self.assertEqual(vcf.num_index, 2785-24) # check number of variants

        # navigate in VCF
        vcf.goto('scaffold_285', 244)
        self.assertTupleEqual(vcf.readline(), ('scaffold_285', 244, 4))
        vcf.goto('scaffold_285', egglib.io.FIRST) # go to 1st contig position
        self.assertTupleEqual(vcf.readline(), ('scaffold_285', 0, 2))
        vcf.goto('scaffold_285', egglib.io.LAST) # last contig position
        self.assertTupleEqual(vcf.readline(), ('scaffold_285', 2753, 3))
        vcf.goto('scaffold_285a', egglib.io.FIRST) # 1st contig position (another contig)
        self.assertTupleEqual(vcf.readline(), ('scaffold_285a', -1, 2)) # position is "before 1st"
        vcf.goto('scaffold_285a', -1) # go to this position
        self.assertTupleEqual(vcf.readline(), ('scaffold_285a', -1, 2))

    def test_goto_T(self):
        self.vcf_h.goto('19')
        with self.assertRaises(ValueError):
            variant = self.vcf_h.get_variant()
        self.vcf_h.goto('19', 213708)
        self.vcf_h.readline()
        variant0 = self.vcf_h.get_variant()

    def test_goto_E(self):
        self.vcf.load_index(self.index1)
        with self.assertRaises(TypeError):
            self.vcf.goto(5)
        with self.assertRaises(ValueError):
            self.vcf.goto('2', 1929641)
        with self.assertRaises(ValueError):
            self.vcf.goto('20')
        self.vcf.goto('2', 2847600)

    def test_unread(self):
        self.vcf_h.goto('19', 213708)
        with self.assertRaises(ValueError): self.vcf_h.unread()
        self.vcf_h.readline()
        self.vcf_h.unread()
        with self.assertRaises(ValueError): self.vcf_h.unread()

    def test_rewind_T(self):
        self.vcf_h.goto('19', 244888)
        self.vcf_h.rewind()

    def test_navigation_supp(self):
        # check currline
        vcf = egglib.io.VcfParser(str(path / 'scaffold_285.vcf'))
        self.assertEqual(vcf.currline, 24)
        vcf.readline()
        self.assertEqual(vcf.currline, 25)
        vcf.unread() # go back one line
        self.assertEqual(vcf.currline, 24)

        # cannot go back several time
        vcf.readline()
        vcf.readline()
        vcf.readline()
        vcf.unread()
        try: vcf.unread()
        except ValueError: pass
        else: raise AssertionError

        # cannot use goto without index
        try: vcf.goto('scaffold_285a')
        except ValueError: pass
        else: raise AssertionError

        # can use goto with index
        egglib.io.make_vcf_index(str(path / 'scaffold_285.vcf'), self.index2)
        vcf = egglib.io.VcfParser(str(path / 'scaffold_285.vcf'))
        vcf.load_index(self.index2)
        vcf.goto('scaffold_285a')
        self.assertEqual(vcf.currline, 2778)

        # go back to beginning
        vcf.rewind()
        self.assertEqual(vcf.currline, 24)

    def test_slider_T(self):
        sw_vcf = self.vcf_h.slider(100, 10, max_missing=0)
        self.assertIsInstance(sw_vcf, egglib.io.VcfSlidingWindow)
        win = next(sw_vcf)
        self.assertIsInstance(win, egglib.io.VcfWindow)

    def test_VcfVariant_properties_method(self):
        self.vcf_h.goto('19', 238433)
        self.vcf_h.readline()
        var = self.vcf_h.get_variant()
        self.assertIsInstance(var, egglib.io.VcfVariant) 
        self.assertEqual(var.chromosome, '19')
        self.assertEqual(var.position, 238433)
        self.assertEqual(var.ID[0], 'rs145111147')
        self.assertEqual(var.num_alleles, 2)
        self.assertEqual(var.num_alternate, 1)
        self.assertEqual(var.alleles, ('C', 'G'))
        self.assertEqual(var.alternate_types[0], 0)
        self.assertEqual(var.quality, 100.0)
        self.assertEqual(var.failed_tests, ())
        self.assertEqual(var.AA, '\x7f')
        self.assertEqual(var.AN, 2184)
        self.assertEqual(var.AC, None)
        self.assertEqual(var.AF, None)
        self.assertEqual(var.info, {'ERATE': 0.0004, 'AN': 2184, 'THETA': 0.0040, 'RSQ': 0.9228, 'AC': (100,), 'LDAF': 0.0472, 'VT': 'SNP', 'AA': None, 'SNPSOURCE': ('LOWCOV',), 'AVGPOST': 0.9910, 'AF': 0.05, 'ASN_AF': 0.08, 'AMR_AF': 0.15, 'AFR_AF': 0.0020, 'EUR_AF': 0.0013})
        self.assertEqual(var.format_fields, frozenset(['GL', 'GT', 'DS']))
        self.assertEqual(var.num_samples, 1092)
        self.assertEqual(var.samples[229], {'GT': ('1|0',), 'DS': (1.0,), 'GL': (-1.96,-0.01,-2.65)})
        self.assertEqual(var.ploidy, 2)
        self.assertEqual(var.GT_phased[100], True)
        self.assertEqual(var.GT[229], ('G', 'C'))

    def test_bed_slider_T(self):
        bed_file = path / 'human_fragment.bed'
        bed = egglib.io.BED(str(bed_file))
        bsw = self.vcf_h.bed_slider(egglib.io.BED(str(bed_file)), 0)
        self.assertIsInstance(bsw, egglib.io.VcfSlidingWindow)

    def test_PL_to_GT_T(self):
        PL_file = path / 'tmp_MFD75200_PL.vcf' #'tmp_MFD75200_PL.vcf' is vcf file from 'merged_filt_depth_75_200_ssduplicateindANDsnp-ssblanck_DEF_for_structure.vcf' without GT field and only PL field as genotype data 
        egglib.io.make_vcf_index(str(PL_file), self.index2)
        vcf_pl = egglib.io.VcfParser(str(PL_file), threshold_PL = 30)
        vcf_pl.load_index(self.index2)
        self.vcf.load_index(self.index1)
        self.vcf.goto("1", 30699)
        next(self.vcf)
        var_GT = self.vcf.get_variant()
        vcf_pl.goto("1", 30699)
        next(vcf_pl)
        var_PL = vcf_pl.get_variant()
        for i in range(var_PL.num_samples):  
            if(var_PL.GT[i][0] != None) :  self.assertEqual(var_GT.GT[i], var_PL.GT[i])#self.assertTrue(gt == gt_gl)

    def test_GL_to_GT_T(self):
        GL_file = path / 'tmp_HF_GL.vcf' #'tmp_HF_GL.vcvf' is vcf file from 'human_fragment.vcf' without GT field and only GL field as genotype data 
        egglib.io.make_vcf_index(str(GL_file), self.index2)
        vcf_gl = egglib.io.VcfParser(str(GL_file), threshold_GL = 30)
        vcf_gl.load_index(self.index2)
        self.vcf_h.goto("19", 238433)
        next(self.vcf_h)
        var_GT = self.vcf_h.get_variant()
        vcf_gl.goto("19", 238433)
        next(vcf_gl)
        var_GL = vcf_gl.get_variant()
        for i in range(var_GL.num_samples):  
            if(var_GL.GT[i][0] != None) :  self.assertEqual(sorted(var_GT.GT[i]), sorted(var_GL.GT[i]))

class Sliding_Window_test(unittest.TestCase):
    def setUp(self):
        self.fname1 = path / 'human_fragment.vcf'
        self.vcf = egglib.io.VcfParser(str(self.fname1))
        self.vcf.load_index()
        self.vcf.goto('19')
        self.vcf_positions = get_vcf_positions(self.fname1, "19")
        self.wdw = self.vcf.slider(100, 10, max_missing=0, as_variants=True)
        f, self.fname2 = tempfile.mkstemp()
        os.close(f)
        f, self.fname3 = tempfile.mkstemp()
        os.close(f)

    def tearDown(self):
        if os.path.isfile(self.fname2): os.unlink(self.fname2)
        if os.path.isfile(self.fname3): os.unlink(self.fname3)

    def test_Sliding_Window_T(self):
        vcf = egglib.io.VcfParser(str(self.fname1))
        vcf.load_index()
        vcf.goto('19')
        wdw = vcf.slider(10000, 10000)
        self.assertListEqual(get_slider_bounds(wdw), get_bounds(10000, 10000, self.vcf_positions[-1]))
        vcf.goto('19')
        wdw = vcf.slider(10000, 10000)
        self.assertListEqual(get_slider_extremes(wdw), get_extremes(self.vcf_positions, 10000, 10000))

        self.assertListEqual(get_slider_bounds(self.vcf.slider(10000, 10000)), get_bounds(10000, 10000, 245679))
        self.vcf.rewind()
        self.assertListEqual(get_slider_extremes(self.vcf.slider(10000, 10000)), get_extremes(self.vcf_positions, 10000, 10000))
        self.vcf.rewind()
        self.assertListEqual(get_slider_bounds(self.vcf.slider(10000, 5000)), get_bounds(10000, 5000, 245679))
        self.vcf.rewind()
        self.assertListEqual(get_slider_bounds(self.vcf.slider(1000, 500)), get_bounds(1000, 500, 245679))
        self.vcf.rewind()
        self.assertListEqual(get_slider_bounds(self.vcf.slider(5, 10, max_missing=0, as_variants=True)), get_bounds_as_variants(self.vcf_positions, 5, 10))
        self.vcf.rewind()
        self.assertListEqual(get_slider_extremes(self.vcf.slider(5, 10, max_missing=0, as_variants=True)), get_extremes_as_variants(self.vcf_positions, 5, 10))
        self.vcf.rewind()
        self.assertListEqual(get_slider_bounds(self.vcf.slider(10, 10, max_missing=0, as_variants=True)), get_bounds_as_variants(self.vcf_positions, 10, 10))
        self.vcf.rewind()
        self.assertListEqual(get_slider_extremes(self.vcf.slider(10, 10, max_missing=0, as_variants=True)), get_extremes_as_variants(self.vcf_positions, 10, 10))
        self.vcf.rewind()
        self.assertListEqual(get_slider_bounds(self.vcf.slider(10, 5, max_missing=0, as_variants=True)), get_bounds_as_variants(self.vcf_positions, 10, 5))
        self.vcf.rewind()
        self.assertListEqual(get_slider_extremes(self.vcf.slider(10, 5, max_missing=0, as_variants=True)), get_extremes_as_variants(self.vcf_positions, 10, 5))
        self.vcf.rewind()
        self.assertListEqual(get_slider_bounds(self.vcf.slider(50, 100, max_missing=0, as_variants=True)), get_bounds_as_variants(self.vcf_positions, 50, 100))
        self.vcf.rewind()
        self.assertListEqual(get_slider_extremes(self.vcf.slider(50, 100, max_missing=0, as_variants=True)), get_extremes_as_variants(self.vcf_positions, 50, 100))

        good = ['AAATAATT', 'GGCGGCTT', 'GGGTGGTT', 'CCCACCAA']
        vcf = egglib.io.VcfParser(str(path / 'a.vcf'))
        for win in vcf.slider(2, 2, as_variants=True):
            for site in win:
                self.assertEqual(''.join(site.as_list()), good.pop(0))

    def test_Sliding_WIndow_E(self):
        self.vcf.goto('19', 245679)
        next(self.vcf)
        with self.assertRaises(ValueError):
            self.vcf.slider(10, 5, as_variants=True)

        fname=path / 'human_fragment.vcf'
        my_file = open(fname)
        header = []
        for line in my_file:
                header.append(line)
                if line.split()[0] == '#CHROM': break
        header = ''.join(header)
        vcf_e = egglib.io.VcfStringParser(header)

    def test_good_T(self):
        self.assertTrue(self.wdw.good)
        fname=path / 'human_fragment.vcf'
        vcf = egglib.io.VcfParser(str(fname))
        vcf.load_index()
        vcf.goto('19', 186581)
        wdw=self.vcf.slider(10, 5, as_variants=True)
        self.assertTrue(self.wdw.good)

    def test_SW_properties_T(self):
        self.wdw = self.vcf.slider(10, 5, max_missing=0, as_variants=True)
        win = next(self.wdw)
        self.assertEqual(win[0].position, 90973)
        self.assertEqual(win[-1].position, 107986)
        self.assertEqual(win.num_sites, 10)
        self.assertEqual(win.chromosome, "19")

    def test_next_T(self):
        self.wdw = self.vcf.slider(10, 5, max_missing=0, as_variants=True)
        win = next(self.wdw)
        pos_0 = win[0].position
        win = next(self.wdw)
        pos_1 = win[0].position
        self.assertNotEqual(pos_0, pos_1)
        self.assertEqual(pos_0, 90973)
        self.assertEqual(pos_1, 107865)

    def test__getitem__T(self):
        self.wdw=self.vcf.slider(100, 10, max_missing=0, as_variants=True)
        win = next(self.wdw)
        self.assertIsInstance(win[50], egglib.Site) 

    def test__getitem__E(self):
        win = next(self.wdw)
        with self.assertRaises(ValueError):
            win[10000]
        
    def test__iter__T(self):
        self.assertIsInstance(self.wdw, collections.abc.Iterable)

    def test__len__T(self):
        self.wdw = self.vcf.slider(10, 5, max_missing=0, as_variants=True)
        win = next(self.wdw)
        self.assertEqual(win.num_sites, 10)

    def test_size_T(self):
        self.wdw = self.vcf.slider(10, 5, max_missing=0, as_variants=True)
        win = next(self.wdw)
        self.assertTupleEqual(win.bounds, (90973, 107986+1))

    def test_next_E(self):
        for win in self.wdw:
            pass
        with self.assertRaises(StopIteration):
            next(self.wdw)

    def test_misc1(self):
        # sliding window (missing GT)
        vcf = egglib.io.VcfParser(str(path / 'scaffold_285.vcf'))
        try: vcf.slider(1000, 1000)
        except ValueError: pass
        else: raise AssertionError

        # sliding window
        vcf = egglib.io.VcfParser(str(path / 'scaffold_285.vcf'), threshold_PL=30) # check if sites with <4 alleles (that is, with * allele) are not skipped
        sld = vcf.slider(1000, 1000, allow_custom=True)
        for win in sld:
            for site in win:
                pass

        # make a test VCF
        s = \
"""##fileformat=VCFv4.2
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	sample1	sample2	sample3	sample4
chr1	1	.	A	G	0	.	.	GT	0/0	0/0	0/0	0/0
chr1	2	.	A	G	0	.	.	GT	0/1	0/0	1/1	0/0
chr1	4	.	C	G,T	0	.	.	GT	0/0	1/1	0/2	1/2
chr1	5	.	C	G,A	0	.	.	GT	1/1	1/1	2/2	2/2
chr1	6	.	A	AA	0	.	.	GT	0/0	0/1	1/1	./.
chr1	12	.	T	G	0	.	.	GT	./.	1/1	0/0	./.
chr1	13	.	T	G	0	.	.	GT	0/0	0/1	0/1	./.
chr1	13	.	TT	TTT,T,TTTTTT	0	.	.	GT	1/2	0/2	3/3	2/3
chr1	16	.	A	C	0	.	.	GT	1/0	0/0	1/0	0/1
chr1	17	.	A	T	0	.	.	GT	0/0	1/1	./0	0/1
chr1	20	.	A	G,C	0	.	.	GT	0/0	1/1	0/2	2/2
chr1	21	.	C	G	0	.	.	GT	./.	0/0	1/1	0/0
chr2	1	.	G	GG	0	.	.	GT	./.	0/0	1/1	0/0
chr2	2	.	T	C,<huh>	0	.	.	GT	0/0	0/0	0/2	1/1
chr2	3	.	T	CC,<huh>	0	.	.	GT	0/0	0/0	0/2	1/1
chr2	4	.	A	C	0	.	.	GT	0/0	1/1	0/0	1/0
chr2	21	.	C	T	0	.	.	GT	0/0	1/1	0/0	1/0
chr2	22	.	A	T	0	.	.	GT	0/0	1/1	0/0	1/0
chr3	1	.	T	TT	0	.	.	GT	0/0	0/0	1/1	1/1
chr3	2	.	CCC	C	0	.	.	GT	0/0	0/0	1/1	1/1
chr3	3	.	T	TATATATATAT	0	.	.	GT	0/0	0/0	1/1	1/1
"""
        f = open(self.fname2, 'w')
        f.write(s)
        f.close()
        egglib.io.make_vcf_index(self.fname2, self.fname3)

        vcf = egglib.io.VcfParser(str(self.fname2))
        vcf.readline()
        site = vcf.get_genotypes()
        self.assertEqual(''.join(site.as_list()), 'AAAAAAAA')
        self.assertEqual(site.alphabet, egglib.alphabets.DNA)

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertEqual(''.join(site.as_list()), 'AGAAGGAA')
        self.assertEqual(site.alphabet, egglib.alphabets.DNA)

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertEqual(''.join(site.as_list()), 'CCGGCTGT')
        self.assertEqual(site.alphabet, egglib.alphabets.DNA)

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertEqual(''.join(site.as_list()), 'GGGGAAAA')
        self.assertEqual(site.alphabet, egglib.alphabets.DNA)

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertListEqual(site.as_list(), ['A', 'A', 'A', 'AA', 'AA', 'AA', '?', '?'])
        self.assertEqual(site.alphabet.name, 'CaseInsensitiveStringAlphabet')
        self.assertTupleEqual(site.alphabet.get_alleles(), (['A', 'AA'], ['?']))

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertEqual(''.join(site.as_list()), '??GGTT??')
        self.assertEqual(site.alphabet, egglib.alphabets.DNA)

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertEqual(''.join(site.as_list()), 'TTTGTG??')
        self.assertEqual(site.alphabet, egglib.alphabets.DNA)

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertListEqual(site.as_list(), ['TTT', 'T', 'TT', 'T', 'TTTTTT', 'TTTTTT', 'T', 'TTTTTT'])
        self.assertEqual(site.alphabet.name, 'CaseInsensitiveStringAlphabet')
        self.assertTupleEqual(site.alphabet.get_alleles(), (['TT', 'TTT', 'T', 'TTTTTT'], ['?']))

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertEqual(''.join(site.as_list()), 'CAAACAAC')
        self.assertEqual(site.alphabet, egglib.alphabets.DNA)

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertEqual(''.join(site.as_list()), 'AATT?AAT')
        self.assertEqual(site.alphabet, egglib.alphabets.DNA)

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertEqual(''.join(site.as_list()), 'AAGGACCC')
        self.assertEqual(site.alphabet, egglib.alphabets.DNA)

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertEqual(''.join(site.as_list()), '??CCGGCC')
        self.assertEqual(site.alphabet, egglib.alphabets.DNA)

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertListEqual(site.as_list(), ['?', '?', 'G', 'G', 'GG', 'GG', 'G', 'G'])
        self.assertEqual(site.alphabet.name, 'CaseInsensitiveStringAlphabet')
        self.assertTupleEqual(site.alphabet.get_alleles(), (['G', 'GG'], ['?']))

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertListEqual(site.as_list(), ['T', 'T', 'T', 'T', 'T', '<huh>', 'C', 'C'])
        self.assertEqual(site.alphabet.name, 'CustomStringAlphabet')
        self.assertTupleEqual(site.alphabet.get_alleles(), (['T', 'C', '<huh>'], ['?']))

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertListEqual(site.as_list(), ['T', 'T', 'T', 'T', 'T', '<huh>', 'CC', 'CC'])
        self.assertEqual(site.alphabet.name, 'CustomStringAlphabet')
        self.assertTupleEqual(site.alphabet.get_alleles(), (['T', 'CC', '<huh>'], ['?']))

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertEqual(''.join(site.as_list()), 'AACCAACA')
        self.assertEqual(site.alphabet, egglib.alphabets.DNA)

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertEqual(''.join(site.as_list()), 'CCTTCCTC')
        self.assertEqual(site.alphabet, egglib.alphabets.DNA)

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertEqual(''.join(site.as_list()), 'AATTAATA')
        self.assertEqual(site.alphabet, egglib.alphabets.DNA)

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertListEqual(site.as_list(), ['T', 'T', 'T', 'T', 'TT', 'TT', 'TT', 'TT'])
        self.assertEqual(site.alphabet.name, 'CaseInsensitiveStringAlphabet')
        self.assertTupleEqual(site.alphabet.get_alleles(), (['T', 'TT'], ['?']))

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertListEqual(site.as_list(), ['CCC', 'CCC', 'CCC', 'CCC', 'C', 'C', 'C', 'C'])
        self.assertEqual(site.alphabet.name, 'CaseInsensitiveStringAlphabet')
        self.assertTupleEqual(site.alphabet.get_alleles(), (['CCC', 'C'], ['?']))

        vcf.readline()
        site = vcf.get_genotypes()
        self.assertListEqual(site.as_list(), ['T', 'T', 'T', 'T', 'TATATATATAT', 'TATATATATAT', 'TATATATATAT', 'TATATATATAT'])
        self.assertEqual(site.alphabet.name, 'CaseInsensitiveStringAlphabet')
        self.assertTupleEqual(site.alphabet.get_alleles(), (['T', 'TATATATATAT'], ['?']))

        self.assertFalse(vcf.good)

        # sliding window, force empty window
        n = 0
        vcf.load_index(self.fname3)
        vcf.goto('chr3')
        for win in vcf.slider(size=5, step=2, as_variants=True, allow_indel=False, allow_custom=False):
            n += 1
        self.assertEqual(n, 0)

        # sliding window, including all (site-based)
        vcf.rewind()
        ns = 5, 5, 5, 5, 4
        pos = [ [0, 1, 3, 4, 5],
                [3, 4, 5, 11, 12],
                [5, 11, 12, 12, 15],
                [12, 12, 15, 16, 19],
                [15, 16, 19, 20]]
        i = 0
        for win in vcf.slider(size=5, step=2, as_variants=True, allow_indel=True, allow_custom=True):
            self.assertEqual(win.num_sites, ns[i])
            self.assertListEqual([site.position for site in win], pos[i])
            self.assertListEqual([win[x].position for x in range(len(win))], pos[i])
            self.assertTupleEqual(win.bounds, (pos[i][0], pos[i][-1] + 1))
            i += 1
        self.assertEqual(i, len(ns))

        # sliding window, no indels (site-based)
        vcf.rewind()
        ns = 5, 5, 5, 4
        pos = [ [0, 1, 3, 4, 11],
                [3, 4, 11, 12, 15],
                [11, 12, 15, 16, 19],
                [15, 16, 19, 20]]
        i = 0
        for win in vcf.slider(size=5, step=2, as_variants=True, allow_indel=False, allow_custom=True):
            self.assertEqual(win.num_sites, ns[i])
            self.assertListEqual([site.position for site in win], pos[i])
            self.assertListEqual([win[x].position for x in range(len(win))], pos[i])
            self.assertTupleEqual(win.bounds, (pos[i][0], pos[i][-1] + 1))
            i += 1
        self.assertEqual(i, len(ns))

        # sliding window, all included (site-based), next chromosome
        ns = 3, 3, 2
        pos = [ [0, 1, 2], [2, 3, 20], [20, 21]]
        alph = [ ['VCF_alphabet_indels', 'VCF_alphabet_custom', 'VCF_alphabet_custom'],
                 ['VCF_alphabet_custom', 'DNA', 'DNA'],
                 ['DNA', 'DNA']]
        i = 0
        for win in vcf.slider(size=3, step=2, as_variants=True, allow_indel=True, allow_custom=True):
            self.assertEqual(win.num_sites, ns[i])
            self.assertListEqual([site.position for site in win], pos[i])
            self.assertListEqual([win[x].position for x in range(len(win))], pos[i])
            self.assertTupleEqual(win.bounds, (pos[i][0], pos[i][-1] + 1))
            self.assertListEqual([site.alphabet.name for site in win], alph[i])
            i += 1
        self.assertEqual(i, len(ns))

        # sliding window, no indels (site-based)
        vcf.goto('chr2')
        ns = 3, 2
        pos = [ [1, 3, 20], [20, 21]]
        i = 0
        for win in vcf.slider(size=3, step=2, as_variants=True, allow_custom=True):
            self.assertEqual(win.num_sites, ns[i])
            self.assertListEqual([site.position for site in win], pos[i])
            self.assertListEqual([win[x].position for x in range(len(win))], pos[i])
            self.assertTupleEqual(win.bounds, (pos[i][0], pos[i][-1] + 1))
            i += 1
        self.assertEqual(i, len(ns))

        # sliding window, no custom (site-based)
        vcf.goto('chr2')
        ns = 3, 2
        pos = [ [0, 3, 20], [20, 21]]
        i = 0
        for win in vcf.slider(size=3, step=2, as_variants=True, allow_indel=True):
            self.assertEqual(win.num_sites, ns[i])
            self.assertListEqual([site.position for site in win], pos[i])
            self.assertListEqual([win[x].position for x in range(len(win))], pos[i])
            self.assertTupleEqual(win.bounds, (pos[i][0], pos[i][-1] + 1))
            i += 1
        self.assertEqual(i, len(ns))

        # bp based sliding window
        vcf.rewind()
        pos = [[0, 1, 3, 4, 5], [5, 11, 12, 12], [11, 12, 12, 15, 16, 19], [15, 16, 19, 20]]
        bounds = [(0, 10), (5, 15), (10, 20), (15, 25)]
        i = 0
        for win in vcf.slider(size=10, step=5, allow_custom=True, allow_indel=True):
            self.assertEqual(win.num_sites, len(pos[i]))
            self.assertListEqual([site.position for site in win], pos[i])
            self.assertListEqual([win[x].position for x in range(len(win))], pos[i])
            self.assertTupleEqual(win.bounds, bounds[i])
            i += 1
        self.assertEqual(i, len(pos))

        # chr2
        pos = [[0, 1, 2, 3], [], [], [20, 21]]
        bounds = [(0, 10), (5, 15), (10, 20), (15, 25)]
        i = 0
        for win in vcf.slider(size=10, step=5, allow_custom=True, allow_indel=True):
            self.assertEqual(win.num_sites, len(pos[i]))
            self.assertListEqual([site.position for site in win], pos[i])
            self.assertListEqual([win[x].position for x in range(len(win))], pos[i])
            self.assertTupleEqual(win.bounds, bounds[i])
            i += 1
        self.assertEqual(i, len(pos))

        # chr3
        pos = [[0, 1, 2]]
        bounds = [(0, 10)]
        i = 0
        for win in vcf.slider(size=10, step=5, allow_custom=True, allow_indel=True):
            self.assertEqual(win.num_sites, len(pos[i]))
            self.assertListEqual([site.position for site in win], pos[i])
            self.assertListEqual([win[x].position for x in range(len(win))], pos[i])
            self.assertTupleEqual(win.bounds, bounds[i])
            i += 1
        self.assertEqual(i, len(pos))

        # only SNP
        vcf.rewind()
        pos = [[0, 1, 3, 4], [11, 12], [11, 12, 15, 16, 19], [15, 16, 19, 20]]
        bounds = [(0, 10), (5, 15), (10, 20), (15, 25)]
        i = 0
        for win in vcf.slider(size=10, step=5):
            self.assertEqual(win.num_sites, len(pos[i]))
            self.assertListEqual([site.position for site in win], pos[i])
            self.assertListEqual([win[x].position for x in range(len(win))], pos[i])
            self.assertTupleEqual(win.bounds, bounds[i])
            i += 1
        self.assertEqual(i, len(pos))

        pos = [[3], [], [], [20, 21]]
        bounds = [(0, 10), (5, 15), (10, 20), (15, 25)]
        i = 0
        for win in vcf.slider(size=10, step=5):
            self.assertEqual(win.num_sites, len(pos[i]))
            self.assertListEqual([site.position for site in win], pos[i])
            self.assertListEqual([win[x].position for x in range(len(win))], pos[i])
            self.assertTupleEqual(win.bounds, bounds[i])
            i += 1
        self.assertEqual(i, len(pos))

        pos = []
        bounds = []
        i = 0
        for win in vcf.slider(size=10, step=5):
            self.assertEqual(win.num_sites, len(pos[i]))
            self.assertListEqual([site.position for site in win], pos[i])
            self.assertListEqual([win[x].position for x in range(len(win))], pos[i])
            self.assertTupleEqual(win.bounds, bounds[i])
            i += 1
        self.assertEqual(i, len(pos))

        # SNP+indels
        vcf.rewind()
        pos = [[0, 1, 3, 4, 5], [5, 11, 12, 12], [11, 12, 12, 15, 16, 19], [15, 16, 19, 20]]
        bounds = [(0, 10), (5, 15), (10, 20), (15, 25)]
        i = 0
        for win in vcf.slider(size=10, step=5, allow_indel=True):
            self.assertEqual(win.num_sites, len(pos[i]))
            self.assertListEqual([site.position for site in win], pos[i])
            self.assertListEqual([win[x].position for x in range(len(win))], pos[i])
            self.assertTupleEqual(win.bounds, bounds[i])
            i += 1
        self.assertEqual(i, len(pos))

        pos = [[0, 3], [], [], [20, 21]]
        bounds = [(0, 10), (5, 15), (10, 20), (15, 25)]
        i = 0
        for win in vcf.slider(size=10, step=5, allow_indel=True):
            self.assertEqual(win.num_sites, len(pos[i]))
            self.assertListEqual([site.position for site in win], pos[i])
            self.assertListEqual([win[x].position for x in range(len(win))], pos[i])
            self.assertTupleEqual(win.bounds, bounds[i])
            i += 1
        self.assertEqual(i, len(pos))

        pos = [[0, 1, 2]]
        bounds = [(0, 10)]
        i = 0
        for win in vcf.slider(size=10, step=5, allow_indel=True):
            self.assertEqual(win.num_sites, len(pos[i]))
            self.assertListEqual([site.position for site in win], pos[i])
            self.assertListEqual([win[x].position for x in range(len(win))], pos[i])
            self.assertTupleEqual(win.bounds, bounds[i])
            i += 1
        self.assertEqual(i, len(pos))

    def test_misc2(self):

        try:
            tf1 = tempfile.NamedTemporaryFile()
            tf2 = tempfile.NamedTemporaryFile()
            tf3 = tempfile.NamedTemporaryFile()
            tf4 = tempfile.NamedTemporaryFile()
            tf5 = tempfile.NamedTemporaryFile()

            tf1.close()
            tf2.close()
            tf3.close()
            tf4.close()
            tf5.close()

            # test VCF file
            vcf_string = \
"""##fileformat=VCFv4.2
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	sample1	sample2	sample3	sample4
chr1	1	.	A	C	0	.	.	GT	0/0/0/0	0/0/0/0	0/0/0/0	0/0/0/1
chr1	2	.	C	G	0	.	.	GT	0/0/0/0	0/0/0/0	0/0/0/0	1/1/1/1
chr1	3	.	G	T	0	.	.	GT	0/0/0/0	0/0/1/1	0/0/1/1	0/1/1/1
chr1	4	.	T	A	0	.	.	GT	0/0/0/0	0/1/1/1	0/0/0/1	1/1/1/1
chr1	5	.	A	C	0	.	.	GT	0/0/0/1	1/1/1/1	1/1/1/1	1/1/1/1
chr1	6	.	C	G	0	.	.	GT	0/0/1/1	0/1/1/1	0/0/0/0	0/0/0/1
chr1	7	.	G	T	0	.	.	GT	0/0/0/0	1/1/1/1	1/1/1/1	1/1/1/1
chr1	8	.	T	A	0	.	.	GT	0/0/0/0	0/0/0/1	0/0/1/1	0/0/0/0
chr1	9	.	A	C	0	.	.	GT	0/0/0/0	0/0/0/0	0/0/1/1	0/0/0/1
chr1	10	.	C	G	0	.	.	GT	0/1/1/1	0/0/0/0	0/0/0/1	0/0/0/0
chr2	1	.	A	T	0	.	.	GT	0/0/0/0	0/0/0/1	0/1/1/1	0/0/0/0
chr2	2	.	C	A	0	.	.	GT	0/0/0/0	0/0/0/0	1/1/1/1	0/0/1/1
chr2	3	.	G	C	0	.	.	GT	0/0/1/1	0/0/0/1	0/0/0/0	0/1/1/1
chr2	4	.	T	G	0	.	.	GT	0/0/0/0	1/1/1/1	0/1/1/1	0/0/1/1
chr2	5	.	A	T	0	.	.	GT	0/1/1/1	0/1/1/1	1/1/1/1	0/0/1/1
chr2	6	.	C	A	0	.	.	GT	0/0/0/1	0/0/0/0	0/1/1/1	0/0/0/0
chr2	7	.	G	C	0	.	.	GT	1/1/1/1	0/0/0/0	0/0/0/1	0/0/0/0
chr2	8	.	T	G	0	.	.	GT	0/0/0/0	0/0/0/1	0/0/0/0	0/0/0/1
chr2	9	.	A	T	0	.	.	GT	0/0/1/1	0/0/0/0	0/0/0/1	0/0/0/0
chr2	10	.	C	A	0	.	.	GT	0/0/0/0	0/1/1/1	0/0/0/0	0/0/0/1
chr2	11	.	G	C	0	.	.	GT	0/0/0/0	0/0/1/1	0/0/0/0	0/1/1/1
chr2	12	.	T	G	0	.	.	GT	0/0/0/1	0/0/0/0	0/0/0/1	0/0/1/1
"""

            # test BED file
            bed_string0 = \
"""chr1	0	4
chr1	1	5
chr1	2	6
chr1	3	7
chr1	4	8
chr1	5	9
chr1	6	10
"""

            bed_string1 = \
"""browser this is a header line
browser this one also
track this one can be treated as a header line
#comment
chr1	0	4
chr1	6	8
chr1	8	10
# chromosome 2
chr2	2	8
chr2	4	10
chr2	6	12
#riendutout
"""

            # test BED file with additional stuff beyond the three required fields
            bed_string2 = \
"""browser this is a header line
browser this one also
track this one can be treated as a header line
#this is a comment: header line as well
chr1   0	4	win1	0	+	blah
chr1   6	8	win2	0	+	blah
chr1   8	10	win3	0	+	blah
chr1  25	65   win+   0    +   nope
chr2   2	8	win4	0	+	blah
chr2   4	10	win5	0	+	blah
chr2   6	12	win6	0	+	blah
"""

            # write down the VCF file
            with open(tf1.name, 'w') as f:
                f.write(vcf_string)

            # test that VCF slider works properly
            vcf = egglib.io.VcfParser(tf1.name)
            self.assertListEqual(list([win.bounds for win in vcf.slider(4, 6)]), [(0, 4), (6, 10)])
            vcf.rewind()

            # write down two BED files
            with open(tf2.name, 'w') as f:
                f.write(bed_string1)

            with open(tf3.name, 'w') as f:
                f.write(bed_string2)

            # check empy BED object
            bed1 = egglib.io.BED()
            self.assertEqual(len(bed1), 0)

            # check first BED file
            bed2 = egglib.io.BED(tf2.name)
            self.assertEqual(len(bed2), 6)

            self.assertDictEqual(bed2[0], {'chrom': 'chr1', 'start': 0, 'end': 4})
            self.assertListEqual(list(bed2), [
                {'chrom': 'chr1', 'start': 0, 'end': 4},
                {'chrom': 'chr1', 'start': 6, 'end': 8},
                {'chrom': 'chr1', 'start': 8, 'end': 10},
                {'chrom': 'chr2', 'start': 2, 'end': 8},
                {'chrom': 'chr2', 'start': 4, 'end': 10},
                {'chrom': 'chr2', 'start': 6, 'end': 12}])

            # check second BED files (with additional fields)
            bed3 = egglib.io.BED(tf3.name)
            self.assertEqual(len(bed2), 6)

            self.assertDictEqual(bed3[4], {'chrom': 'chr2', 'start': 2, 'end': 8})
            self.assertListEqual(list(bed3), [
                {'chrom': 'chr1', 'start': 0, 'end': 4},
                {'chrom': 'chr1', 'start': 6, 'end': 8},
                {'chrom': 'chr1', 'start': 8, 'end': 10},
                {'chrom': 'chr1', 'start': 25, 'end': 65},
                {'chrom': 'chr2', 'start': 2, 'end': 8},
                {'chrom': 'chr2', 'start': 4, 'end': 10},
                {'chrom': 'chr2', 'start': 6, 'end': 12}])

            bed3.append(chrom='chrX', start=0, end=1000000)
            self.assertListEqual(list(bed3), [
                {'chrom': 'chr1', 'start': 0, 'end': 4},
                {'chrom': 'chr1', 'start': 6, 'end': 8},
                {'chrom': 'chr1', 'start': 8, 'end': 10},
                {'chrom': 'chr1', 'start': 25, 'end': 65},
                {'chrom': 'chr2', 'start': 2, 'end': 8},
                {'chrom': 'chr2', 'start': 4, 'end': 10},
                {'chrom': 'chr2', 'start': 6, 'end': 12},
                {'chrom': 'chrX', 'start': 0, 'end': 1000000}])

            # fill empty BED object
            bed1.append('chr1', 0, 1000)
            bed1.append('chr1', 1000, 2000)
            bed1.extend([('chr2', 0, 500),
                         ('chr2', 500, 1000),
                         ('chr2', 1000, 1500),
                         ('chr2', 1500, 2000),
                         ('chr2', 2000, 2500),
                         ('chr2', 2500, 3000)])
            bed1.append('chr3', 0, 5000)
            bed1.append('chr3', 5000, 10000)
            self.assertEqual(len(bed1), 10)
            self.assertListEqual(list(bed1), [
                {'chrom': 'chr1', 'start': 0, 'end': 1000},
                {'chrom': 'chr1', 'start': 1000, 'end': 2000},
                {'chrom': 'chr2', 'start': 0, 'end': 500},
                {'chrom': 'chr2', 'start': 500, 'end': 1000},
                {'chrom': 'chr2', 'start': 1000, 'end': 1500},
                {'chrom': 'chr2', 'start': 1500, 'end': 2000},
                {'chrom': 'chr2', 'start': 2000, 'end': 2500},
                {'chrom': 'chr2', 'start': 2500, 'end': 3000},
                {'chrom': 'chr3', 'start': 0, 'end': 5000},
                {'chrom': 'chr3', 'start': 5000, 'end': 10000}])

            # test BED slider
            with open(tf5.name, 'w') as f:
                f.write(bed_string0)
            bed0 = egglib.io.BED(tf5.name)

            check = [('chr1', 0, 4),
                     ('chr1', 1, 5),
                     ('chr1', 2, 6),
                     ('chr1', 3, 7),
                     ('chr1', 4, 8),
                     ('chr1', 5, 9),
                     ('chr1', 6, 10)]
            c = 0
            for win in vcf.bed_slider(bed0):
                self.assertEqual(win.chromosome, check[c][0])
                self.assertTupleEqual(win.bounds, (check[c][1], check[c][2]))
                self.assertEqual(win.num_sites, 4)
                self.assertEqual(len(win), 4)
                c += 1

            # create a non contiguous BED object
            bed4 = egglib.io.BED()
            self.assertEqual(len(bed4), 0)
            bed4.append('chr1', 3, 8)
            bed4.append('chr1', 5, 100)
            bed4.append('chr1', 0, 5)
            vcf.rewind()
            with self.assertRaisesRegex(ValueError, 'BED windows must be sorted'):
                vcf.bed_slider(bed4)

            bed5 = egglib.io.BED()
            self.assertEqual(len(bed5), 0)
            bed5.append('chr1', 3, 8)
            bed5.append('chr1', 5, 100)
            bed5.append('chr2', 0, 5)
            bed5.append('chr1', 0, 5)
            with self.assertRaisesRegex(ValueError, 'cannot jump to a different chromosome'):
                vcf.bed_slider(bed5)

            check = [('chr1', 3, 8, 5),
                     ('chr1', 5, 100, 5),
                     ('chr2', 0, 5, 5),
                     ('chr1', 0, 5, 5),
                     ('chr1', 2, 9, 7)]
            c = 0
            egglib.io.make_vcf_index(tf1.name)
            vcf.load_index()
            for win in vcf.bed_slider(bed5):
                self.assertEqual(win.chromosome, check[c][0])
                self.assertTupleEqual(win.bounds, (check[c][1], check[c][2]))
                self.assertEqual(win.num_sites, check[c][3])
                c += 1
            vcf.close()
        finally:
            for tf in [tf1, tf2, tf3, tf4, tf5]:
                if os.path.isfile(tf.name):
                    os.unlink(tf.name)

class Bed_Sliding_Window_test(unittest.TestCase):
    def setUp(self):
        fname = path / 'human_fragment.vcf'
        bed_file = path / 'human_fragment.bed'
        self.vcf = egglib.io.VcfParser(str(fname))
        self.bsw = self.vcf.bed_slider(egglib.io.BED(str(bed_file)), 0)

    def tearDown(self):
        del self.vcf
        del self.bsw

    def test_Bed_Slinding_WIndow_T(self):
        self.assertIsInstance(self.bsw, egglib.io.VcfSlidingWindow)

    def test__iter__T(self):
        next(self.bsw)
        self.assertIsInstance(self.bsw, collections.abc.Iterable)

    def test__len__T(self):
        win = next(self.bsw)
        self.assertEqual(len(win), 10)

    def test_Bed_Sliding_Window_properties_method(self):
        win = next(self.bsw)
        win = next(self.bsw)
        self.assertEqual(win[0].position, 107865)
        self.assertEqual(win[-1].position, 108093)
        self.assertEqual(win.num_sites, 10 )
        self.assertEqual(len(win), 10 )
        self.assertEqual(win.chromosome, "19" )

    def test_next_T(self):
        BED_bounds = []
        while self.bsw.good:
            win = next(self.bsw)
            BED_bounds.append((win[0].position, win[-1].position+1)) # BED returns first/last at the moment
        self.vcf.rewind()
        wdw = self.vcf.slider(10, 5, max_missing=0, as_variants=True)
        VCF_bounds = []
        while wdw.good:
            win = next(wdw)
            VCF_bounds.append(win.bounds)
        self.assertListEqual(BED_bounds, VCF_bounds)

    def test_good_T(self):
        next(self.bsw)
        self.assertTrue(self.bsw.good)

