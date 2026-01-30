# compute Gst'

import egglib

def comp(site):
    x1 = [site[i] for i in pop1]
    x2 = [site[i] for i in pop2]
    alleles = set(x1) | set(x2)
    p1 = [x1.count(i) / n1 for i in alleles]
    p2 = [x2.count(i) / n2 for i in alleles]
    Hs = ((1 - sum([i**2 for i in p1])) + (1 - sum([i**2 for i in p2]))) / 2
    Ht = 1 - sum([((p1[i]+p2[i])/2)**2 for i in range(len(alleles))])
    return ((1+Hs)/(1-Hs))*(1-Hs/Ht)

for fname in ['FTLa.fas', 'simul001.fas', 'simul002.fas', 'eIF4E.fas']:
    aln = egglib.io.from_fasta('test/test_modules/test_stats/control_stats/' + fname, alphabet=egglib.alphabets.DNA, labels=True)
    struct = egglib.get_structure(aln, lvl_pop=0)
    pop1 = [i[0] for i in struct.as_dict()[0][None]['0'].values()]
    pop2 = [i[0] for i in struct.as_dict()[0][None]['1'].values()]
    n1 = len(pop1)
    n2 = len(pop2)

    cs = egglib.stats.ComputeStats(struct=struct)
    cs.add_stats('ns_site', 'Aing')
    Gste = 0.0
    n = 0
    haplos = [[] for i in range(aln.ns)]
    for site in aln.iter_sites():
        stats = cs.process_site(site)
        if stats['ns_site'] == struct.ns and stats['Aing'] > 1:
            site = site.as_list()
            for i,v in enumerate(site): haplos[i].append(v)
            Gste += comp(site)
            n += 1
    Gste /= n
    haplos = [''.join(i) for i in haplos]
    print(fname, n, Gste, comp(haplos))

