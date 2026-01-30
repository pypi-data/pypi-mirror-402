import egglib, pathlib

aln1 = egglib.io.from_fasta('align1.fas', labels=True, alphabet = egglib.alphabets.DNA)
struct = egglib.struct_from_labels(aln1, lvl_pop=0, lvl_indiv=1)
cs = egglib.stats.ComputeStats()
cs.set_structure(struct)
cs.add_stats('S', 'thetaW', 'Pi', 'D', 'lseff', 'nseff')
stats = cs.process_align(aln1)
print(aln1.ns, aln1.ls)
print(stats)

alnA = aln1.extract(0, 4500)
alnB = aln1.extract(4500, None)
cs.configure(multi=True)
cs.process_align(alnA)
cs.process_align(alnB)
stats = cs.results()
print(stats)

site = egglib.site_from_list(['AA', 'AA', 'AG', 'AA', 'GG'], egglib.Alphabet('string', ['AA', 'AG', 'GG'], ['NN']))

cs.clear_stats()
cs.configure(multi=False)
cs.add_stats('Aing', 'He', 'R')
site = egglib.site_from_align(aln1, 66)
stats = cs.process_site(site)
print(stats)

cs.add_stats('D', 'Pi')
for i in range(aln1.ls):
    site = egglib.site_from_align(aln1,i)
    stats = cs.process_site(site)
    print(stats)

site = egglib.Site()
for i in range(aln1.ls):
    site.from_align(aln1,i)
    stats = cs.process_site(site)
    print(stats)

cs.clear_stats()
cs.add_stats('ZnS')
print('process_align:', cs.process_align(aln1))

alnA = aln1.extract(0, 4500)
alnB = aln1.extract(4500, None)
cs.configure(multi=True)
cs.set_structure(struct)
cs.process_align(alnA)
cs.process_align(alnB)
print(cs.results())
        
site = egglib.site_from_list(['C', 'G', 'G', 'C', 'T', 'T', 'G', 'T', 'G', 'G', 'G', 'G'], alphabet=egglib.alphabets.DNA)

cs.clear_stats()
cs.configure(multi=False)
cs.add_stats('Aing', 'He', 'R')
site = egglib.site_from_align(aln1, 66)
stats = cs.process_site(site)
print(stats)

cs.add_stats('D', 'Pi')
for i in range(aln1.ls):
    site = egglib.site_from_align(aln1,i)
    stats = cs.process_site(site)
    print(stats)

site = egglib.Site()
for i in range(aln1.ls):
    site.from_align(aln1, i)
    stats = cs.process_site(site)
    print(stats)

cs.clear_stats()
cs.add_stats('ZnS')
print(cs.process_align(aln1))

alnA = aln1.extract(0, 4500)
alnB = aln1.extract(4500, None)
cs.configure(multi=True)
cs.set_structure(struct)
cs.process_align(alnA)
cs.process_align(alnB)
print(cs.results())

sites = []
for i in range(aln1.ls):
    site = egglib.site_from_align(aln1, i)
    if site.num_missing == 0:
        sites.append(site)

for site in sites:
    cs.process_site(site)
print(cs.results())

print(cs.process_sites(sites))

site = egglib.site_from_list(['C', 'G', 'G', 'C', 'T', 'T', 'G', 'T', 'G', 'G', 'G', 'G'], alphabet=egglib.alphabets.DNA)
freq = egglib.freq_from_site(site)
for i in range(freq.num_alleles):
    print(freq.freq_allele(i))

freq = egglib.freq_from_list([[[3, 3, 2, 1, 1]]], [1, 0, 0, 0, 0])
freq = egglib.freq_from_list([[[1, 1, 1, 1, 1]]], [1, 0, 0, 0, 0], geno_list=[(0, 0), (0, 1), (2, 2), (3, 1), (1, 4)],alphabet=egglib.alphabets.positive_infinite)

cs.clear_stats()
cs.add_stats('Aing', 'He', 'R')
site = egglib.site_from_align(aln1, 66)
freq = egglib.freq_from_site(site)
print(cs.process_freq(freq))

cs.add_stats('D', 'Pi')
cs.configure(multi=True)
cs.set_structure(struct)
site = egglib.Site()
freq = egglib.Freq()
for i in range(aln1.ls):
    site.from_align(aln1,i)
    freq.from_site(site)
    cs.process_freq(freq)
print(cs.results())

#test stats2
aln = egglib.io.from_fasta('align5.fas', alphabet=egglib.alphabets.DNA, labels=True)
struct = egglib.struct_from_labels(aln, lvl_clust=0, lvl_pop=1, lvl_indiv=2)
print(struct.as_dict())

struct2 = egglib.struct_from_labels(aln, lvl_pop=0)
print(struct2.as_dict())

cs = egglib.stats.ComputeStats()
cs.add_stats('Fis', 'FistWC', 'FisctWC', 'Snn')
print(cs.process_align(aln))

cs.set_structure(struct)
print(cs.process_align(aln))
cs.set_structure(struct2)
print(cs.process_align(aln))

#test stats3
cs = egglib.stats.ComputeStats()
cs.add_stats('lseff', 'nseff', 'S', 'sites')
alnA = egglib.io.from_fasta('align6A.fas',egglib.alphabets.DNA)
print(cs.process_align(alnA))

alnB = egglib.io.from_fasta('align6B.fas',egglib.alphabets.DNA)
print(cs.process_align(alnB))

print(cs.process_align(alnB, max_missing=0.1))
print(cs.process_align(alnB, max_missing=0.3))

site1 = egglib.site_from_list('AAAAAAAACCCCCCCC', egglib.alphabets.DNA)
site2 = egglib.site_from_list('GGGGGGGGGGGTTTTT', egglib.alphabets.DNA)
site3 = egglib.site_from_list('CCCCCCAAAAAAAAAA', egglib.alphabets.DNA)
site4 = egglib.site_from_list('TTTTAAAAAAATTTTT', egglib.alphabets.DNA)
site5 = egglib.site_from_list('CCGGGGGGGGGGCCCG', egglib.alphabets.DNA)
site6 = egglib.site_from_list('AATTAAAAAAAAAAAT', egglib.alphabets.DNA)
sites = site1, site2, site3, site4, site5, site6

cs = egglib.stats.ComputeStats()
cs.add_stats('Rmin', 'Rintervals', 'ZnS', 'Ki')
print(cs.process_sites(sites))

print(egglib.stats.pairwise_LD(site1, site2))
print(egglib.stats.pairwise_LD(site1, site4))

aln = egglib.io.from_fasta('align7.fas',egglib.alphabets.DNA)
print(egglib.stats.matrix_LD(aln, ('d', 'rsq')))

pos, mat = egglib.stats.matrix_LD(aln, ('d', 'rsq'))
n = len(pos)
for i in range(n):
    for j in range(i):
        p1 = pos[i]
        p2 = pos[j]
        d = mat[i][j][0]
        r2 = mat[i][j][1]
        print('pos:', p1, p2, 'd:', d, 'r2:', r2)

print(egglib.stats.matrix_LD(aln, ['rsq']))
print(egglib.stats.matrix_LD(aln, 'rsq'))

ehh = egglib.stats.EHH()

site = egglib.Site()
f = open('sites1.txt')
core = list(map(int,f.readline().strip()))
site.from_list(core, egglib.alphabets.positive_infinite)
site.position = 0
ehh.set_core(site)
print(ehh.num_haplotypes)
print(ehh.nsam)
print([ehh.nsam_core(i) for i in range(ehh.num_haplotypes)])
print(ehh.cur_haplotypes)
print(ehh.get_EHH(0))
print(ehh.get_rEHH(0))
print(ehh.get_iHH(0))
print(ehh.get_iHS(0))
print(ehh.get_EHHS())
print(ehh.get_iES())

site.from_list(list(map(int,f.readline().strip())), egglib.alphabets.positive_infinite)
site.position = 0.1
ehh.load_distant(site)
print(ehh.cur_haplotypes)
print(ehh.get_EHH(0))
print(ehh.get_rEHH(0))
print(ehh.get_iHH(0))
print(ehh.get_iHS(0))
print(ehh.get_EHHS())
print(ehh.get_iES())

for i, line in enumerate(f):
    site.from_list(list(map(int,line.strip())), egglib.alphabets.positive_infinite)
    site.position = 0.2 + i / 10.0
    ehh.load_distant(site)
    
print(ehh.cur_haplotypes)
print(ehh.get_EHH(0))
print(ehh.get_rEHH(0))
print(ehh.get_iHH(0))
print(ehh.get_iHS(0))
print(ehh.get_EHHS())
print(ehh.get_iES())

#test stats4
vcf = egglib.io.VcfParser('example.vcf')
print([vcf.get_sample(i) for i in range(vcf.num_samples)])
print(dict([vcf.get_meta(i) for i in range(vcf.num_meta)]))

for ret in vcf:
    print(ret)

vcf = egglib.io.VcfParser('example.vcf')
print(next(vcf))
site = egglib.site_from_vcf(vcf)
print(site.as_list())
print(next(vcf))
print(next(vcf))
print(next(vcf))
print(next(vcf))
site.from_vcf(vcf)
print(site.as_list())

vcf = egglib.io.VcfParser('example.vcf')
print(next(vcf))
frq = egglib.freq_from_vcf(vcf)
print(frq.freq_allele(0), frq.freq_allele(1))
print(next(vcf))
print(next(vcf))
print(next(vcf))
print(next(vcf))
frq.from_vcf(vcf)
print(frq.freq_allele(0), frq.freq_allele(1), frq.freq_allele(2))

### 
vcf = egglib.io.VcfParser('example.vcf')
for chrom, pos, nall in vcf:
    v = vcf.get_variant()
    if 'HQ' in v.format_fields:
        print([i['HQ'] for i in v.samples])
    else:
        print('no data')

import gzip
f = gzip.open('example.vcf.gz')
cache = []
while True:
    line = f.readline()
    if line[:2] == b'##': cache.append(line)
    elif line[:1] == b'#':
        cache.append(line)
        break
    else: raise IOError('invalid file')

header = b''.join(cache)
vcf = egglib.io.VcfStringParser(header.decode())
for line in f:
    print(vcf.readline(line.decode()))
    site.from_vcf(vcf)
    print(site.as_list())

ln = egglib.io.from_fasta('align5.fas', labels=True, cls=egglib.Align, alphabet=egglib.alphabets.DNA)

struct = egglib.struct_from_labels(aln, lvl_clust=0, lvl_pop=1, lvl_indiv=2)
print(struct.as_dict())

struct2 = egglib.struct_from_labels(aln, lvl_pop=0)
print(struct2.as_dict())

cs = egglib.stats.ComputeStats()
cs.add_stats('Fis', 'FistWC', 'FisctWC', 'Snn')
print(cs.process_align(aln))
cs.set_structure(struct)
print(cs.process_align(aln))
cs.set_structure(struct)
print(cs.process_align(aln))

coal = egglib.coalesce.Simulator(1, num_chrom=[40], theta=5.0)
aln = coal.simul()
cs = egglib.stats.ComputeStats()
cs.add_stats('S', 'Pi', 'thetaW', 'D', 'Ki')
cs.process_align(aln)

print(cs.process_align(aln))

cs = egglib.stats.ComputeStats()
cs.add_stats('lseff', 'nseff', 'S', 'sites')
alnA = egglib.io.from_fasta('align6A.fas', alphabet=egglib.alphabets.DNA)
print(cs.process_align(alnA))

alnB = egglib.io.from_fasta('align6B.fas', alphabet=egglib.alphabets.DNA)
print(cs.process_align(alnB))
print(cs.process_align(alnB, max_missing=0.1))
print(cs.process_align(alnB, max_missing=0.3))

site1 = egglib.site_from_list('AAAAAAAACCCCCCCC', egglib.alphabets.DNA)
site2 = egglib.site_from_list('GGGGGGGGGGGTTTTT', egglib.alphabets.DNA)
site3 = egglib.site_from_list('CCCCCCAAAAAAAAAA', egglib.alphabets.DNA)
site4 = egglib.site_from_list('TTTTAAAAAAATTTTT', egglib.alphabets.DNA)
site5 = egglib.site_from_list('CCGGGGGGGGGGCCCG', egglib.alphabets.DNA)
site6 = egglib.site_from_list('AATTAAAAAAAAAAAT', egglib.alphabets.DNA)
sites = site1, site2, site3, site4, site5, site6

cs = egglib.stats.ComputeStats()
cs.add_stats('Rmin', 'Rintervals', 'ZnS', 'Kt')
print(cs.process_sites(sites))

print(egglib.stats.pairwise_LD(site1, site2))
print(egglib.stats.pairwise_LD(site1, site4))

aln = egglib.io.from_fasta('align7.fas', egglib.alphabets.DNA)
print(egglib.stats.matrix_LD(aln, ('d', 'rsq')))

pos, mat = egglib.stats.matrix_LD(aln, ('d', 'rsq'))
n = len(pos)
for i in range(n):
    for j in range(i):
        p1 = pos[i]
        p2 = pos[j]
        d = mat[i][j][0]
        r2 = mat[i][j][1]
        print('pos:', p1, p2, 'd:', d, 'r2:', r2)

print(egglib.stats.matrix_LD(aln, ['rsq']))
print(egglib.stats.matrix_LD(aln, 'rsq'))

print('EHH')
ehh = egglib.stats.EHH()

site = egglib.Site()
alph = egglib.Alphabet('char', '012', '')
f = open('sites1.txt')
site.from_list(f.readline().strip(), alphabet=alph)
site.position = 0
ehh.set_core(site)
print(ehh.num_haplotypes)
print(ehh.nsam)
print([ehh.nsam_hap(i) for i in range(ehh.num_haplotypes)])
print(ehh.cur_haplotypes)
print(ehh.get_EHH(0))
print(ehh.get_rEHH(0))
print(ehh.get_iHH(0))
print(ehh.get_iHS(0))
print(ehh.get_EHHS())
print(ehh.get_iES())

site.from_list(f.readline().strip(), alphabet=alph)
site.position = 0.1
ehh.load_distant(site)
print(ehh.cur_haplotypes)
print(ehh.get_EHH(0))
print(ehh.get_rEHH(0))
print(ehh.get_iHH(0))
print(ehh.get_iHS(0))
print(ehh.get_EHHS())
print(ehh.get_iES())

for i, line in enumerate(f):
    site.from_list(line.strip(), alphabet=alph)
    site.position = 0.2 + i / 10.0
    ehh.load_distant(site)

print(ehh.cur_haplotypes)
print(ehh.get_EHH(0))
print(ehh.get_rEHH(0))
print(ehh.get_iHH(0))
print(ehh.get_iHS(0))
print(ehh.get_EHHS())
print(ehh.get_iES())

print('VCF')

vcf = egglib.io.VcfParser('example.vcf')
print(vcf.file_format)
print([vcf.get_sample(i) for i in range(vcf.num_samples)])
print(dict([vcf.get_meta(i) for i in range(vcf.num_meta)]))

for line in vcf:
    print(line)

vcf = egglib.io.VcfParser('example.vcf')
print(next(vcf))
site = egglib.site_from_vcf(vcf)
print(site.as_list())

print(next(vcf))
print(next(vcf))
print(next(vcf))
print(next(vcf))
site.from_vcf(vcf)
print(site.as_list())

vcf = egglib.io.VcfParser('example.vcf')
print(next(vcf))
frq = egglib.freq_from_vcf(vcf)
print(frq.freq_allele(0), frq.freq_allele(1))

print(next(vcf))
print(next(vcf))
print(next(vcf))
print(next(vcf))
frq.from_vcf(vcf)
print(frq.freq_allele(0), frq.freq_allele(1), frq.freq_allele(2))

vcf = egglib.io.VcfParser('example.vcf')
for chrom, pos, nall in vcf:
    v = vcf.get_variant()
    if 'HQ' in v.format_fields:
        print([i['HQ'] for i in v.samples])
    else:
        print('no data')

try: vcf = egglib.io.VcfParser('example.vcf.gz')
except IOError: print('expected error caught')
else: raise RuntimeError

import gzip
f = gzip.open('example.vcf.gz')
cache = []
while True:
    line = f.readline()
    if line[:2] == b'##':
        cache.append(line.decode())
    elif line[:1] == b'#':
        cache.append(line.decode())
        break
    else:
        raise IOError('invalid file')

header = ''.join(cache)
vcf = egglib.io.VcfStringParser(header)

for line in f:
    print(vcf.readline(line.decode()))
    site.from_vcf(vcf)
    print(site.as_list())

print(egglib.tools.translate('CCATTGGTAATGGCC'))

containers = [egglib.io.from_fasta(str(i), alphabet=egglib.alphabets.DNA, cls=egglib.Container)
            for i in pathlib.Path('fas-261').glob('*')]
[c.to_codons() for c in containers]

trans = egglib.tools.Translator(code=1)
for cnt in containers:
    trans.translate_container(cnt, in_place=True)
    print(cnt.fasta())
