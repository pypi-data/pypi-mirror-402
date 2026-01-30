import egglib

cs = egglib.stats.ComputeStats()
cs.add_stats('lseff', 'nseff', 'S', 'sites')
alnA = egglib.io.from_fasta('align6A.fas',egglib.alphabets.DNA)
print(cs.process_align(alnA))

print('~ ~ ~')
alnB = egglib.io.from_fasta('align6B.fas',egglib.alphabets.DNA)
print(cs.process_align(alnB))

print('~ ~ ~')
print(cs.process_align(alnB, max_missing=0.1))

print('~ ~ ~')
print(cs.process_align(alnB, max_missing=0.3))

print('~ ~ ~')

site1 = egglib.site_from_list('AAAAAAAACCCCCCCC', egglib.alphabets.DNA)
site2 = egglib.site_from_list('GGGGGGGGGGGTTTTT', egglib.alphabets.DNA)
site3 = egglib.site_from_list('CCCCCCAAAAAAAAAA', egglib.alphabets.DNA)
site4 = egglib.site_from_list('TTTTAAAAAAATTTTT', egglib.alphabets.DNA)
site5 = egglib.site_from_list('CCGGGGGGGGGGCCCG', egglib.alphabets.DNA)
site6 = egglib.site_from_list('AATTAAAAAAAAAAAT', egglib.alphabets.DNA)
cs = egglib.stats.ComputeStats()
cs.add_stats('Rmin', 'Rintervals', 'ZnS', 'Ki')
print(cs.process_sites([site1, site2, site3, site4, site5, site6]))

print('~ ~ ~')

print(egglib.stats.pairwise_LD(site1, site2))
print(egglib.stats.pairwise_LD(site1, site4))

print('~ ~ ~')

aln = egglib.io.from_fasta('align7.fas', egglib.alphabets.DNA)
print(egglib.stats.matrix_LD(aln, ('d', 'rsq')))

print('~ ~ ~')

pos, mat = egglib.stats.matrix_LD(aln, ('d', 'rsq'))
n = len(pos)
for i in range(n):
    for j in range(i):
        p1 = pos[i]
        p2 = pos[j]
        d = mat[i][j][0]
        r2 = mat[i][j][1]
        print('pos:', p1, p2, 'd:', d, 'r2:', r2)

print('~ ~ ~')

print(egglib.stats.matrix_LD(aln, ['rsq']))
print(egglib.stats.matrix_LD(aln, 'rsq'))

print('~ ~ ~')

ehh = egglib.stats.EHH()

f = open('sites1.txt')
core = list(map(int,f.readline().strip()))
site = egglib.Site()
site.from_list(core, egglib.alphabets.positive_infinite)
site.position = 0
ehh.set_core(site)

print(ehh.num_haplotypes)
print(ehh.nsam)
print([ehh.nsam_core(i) for i in range(ehh.num_haplotypes)])

print(ehh.cur_haplotypes)
print(ehh.get_EHH(0))
print(ehh.get_EHH(1))
print(ehh.get_EHH(2))
print(ehh.get_rEHH(0))
print(ehh.get_iHH(0))
print(ehh.get_iHS(0))
print(ehh.get_EHHS())
print(ehh.get_iES())

print('~ ~ ~')

site.from_list(list(map(int,f.readline().strip())), egglib.alphabets.positive_infinite)
site.position = 0.1
ehh.load_distant(site)
print(ehh.cur_haplotypes)
print(ehh.get_EHH(0))
print(ehh.get_EHH(1))
print(ehh.get_EHH(2))
print(ehh.get_rEHH(0))
print(ehh.get_iHH(0))
print(ehh.get_iHS(0))
print(ehh.get_EHHS())
print(ehh.get_iES())

print('~ ~ ~')

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
