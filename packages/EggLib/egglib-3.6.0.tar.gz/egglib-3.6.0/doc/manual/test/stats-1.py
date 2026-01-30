import egglib

cs = egglib.stats.ComputeStats()
cs.configure(multi_hits=True)

cs = egglib.stats.ComputeStats(multi_hits=True)

cs.add_stats('S', 'Pi')
cs.add_stats('D')

for stat, descr in cs.list_stats():
    print(stat + ': ' + descr)

cs.clear_stats()

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
cs.configure(multi=True, struct=struct)
cs.process_align(alnA)
cs.process_align(alnB)
stats = cs.results()
print(stats)

site = egglib.site_from_list(['C', 'G', 'G', 'C', 'T', 'T', 'G', 'T', 'G', 'G', 'G', 'G'], alphabet=egglib.alphabets.DNA)

cs.clear_stats()
cs.configure(multi=False, struct=struct)
cs.add_stats('Aing', 'He', 'R')
site = egglib.site_from_align(aln1, 66)
stats = cs.process_site(site)
print(stats)

cs.add_stats('D', 'Pi')
for i in range(aln1.ls):
    site = egglib.site_from_align(aln1,i)
    stats = cs.process_site(site)
    print(stats)

cs.configure(multi=True, struct=struct)
for i in range(aln1.ls):
    site.from_align(aln1,i)
    stats = cs.process_site(site)
print(cs.results())

cs.clear_stats()
cs.configure(multi=False, struct=struct)
cs.add_stats('ZnS', 'D', 'S')
print(cs.process_align(aln1))

alnA = aln1.extract(0, 4500)
alnB = aln1.extract(4500, None)
cs.configure(multi=True, struct=struct)
cs.process_align(alnA)
cs.process_align(alnB)
print(cs.results())

sites = []
frq = egglib.Freq()
for i in range(aln1.ls):
    site = egglib.site_from_align(aln1, i)
    frq.from_site(site, struct)
    if frq.nseff(frq.ingroup) == 99:
        sites.append(site)

for site in sites:
    cs.process_site(site)
print(cs.results())

cs.configure(multi=False, struct=struct)
print(cs.process_sites(sites))
print(cs.process_align(aln1))

site = egglib.site_from_list(['C', 'G', 'G', 'C', 'T', 'T', 'G', 'T', 'G', 'G', 'G', 'G'], alphabet=egglib.alphabets.DNA)
freq = egglib.freq_from_site(site)
for i in range(freq.num_alleles):
    print(freq.allele(i), freq.freq_allele(i))

freq = egglib.freq_from_list([[[3, 3, 2, 1, 1]]], [1, 0, 0, 0, 0])

freq = egglib.freq_from_list([[[1, 1, 1, 1, 1]]], [1, 0, 0, 0, 0],
            geno_list=[(0, 0), (0, 1), (2, 2), (3, 1), (1, 4)],
            alphabet=egglib.alphabets.positive_infinite)

print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

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
