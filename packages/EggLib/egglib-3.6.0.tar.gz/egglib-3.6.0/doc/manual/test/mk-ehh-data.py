import egglib

pos = [0.0] * 5
pos += [(i+1)/1000.0 for i in range(80)]
pos += [0.08+(i*0.92)/119 for i in range(120)]

c = egglib.coalesce.Simulator(
    num_pop=1,
    num_chrom=[100],
    theta=25.0,
    recomb=5.0,
    num_sites=205,
    num_alleles=2,
    site_pos=pos)

aln = c.simul()
aln1 = aln.extract(0, 5)
aln2 = aln.extract(5, 205)

core = egglib.stats.haplotypes(aln1, filtr=egglib.stats.filter_default)
core = core.as_list(True, True)

f = open('sites1.txt', 'w')
f.write(''.join(map(str, core)) + '\n')

print [core.count(i) for i in sorted(set(core))]

site = egglib.stats.Site()
c = 0
for i in xrange(aln2.ls):
    site.process_align(aln2, i, egglib.stats.filter_default)
    sitestr = ''.join(map(str, site.as_list(True, True)))
    if len(set(sitestr)) > 1:
        f.write(sitestr + '\n')
        c += 1
f.close()
print c
