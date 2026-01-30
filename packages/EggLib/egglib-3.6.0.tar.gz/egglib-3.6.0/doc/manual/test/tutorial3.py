import egglib

coal = egglib.coalesce.Simulator(1, num_chrom=[20], theta=4.0)

coal = egglib.coalesce.Simulator(2, num_chrom=[20, 20], theta=4.0)
coal.params.add_event('merge', T=0.1, src=1, dst=0)

coal = egglib.coalesce.Simulator(num_pop=1)
print(dict(coal.params))
print(coal.params.summary())

coal = egglib.coalesce.Simulator(num_pop=4, num_chrom=[20,20,20,20], N=[1,1,1,0.2])

print(coal.params['N'][3])
coal.params['N'][2] = 0.5
print(coal.params['N'])

coal.params['G'] = 1.0, 2.0, 3.0, 4.0
coal.params['G'][2:4] = 2.5, 2.7
print(coal.params['G'])

coal = egglib.coalesce.Simulator(num_pop=4, migr=6.0)
print(coal.params['migr_matrix'])

coal.params.set_migr(1.5)
print(coal.params['migr_matrix'])

coal.params['migr_matrix'][0, 1] = 4.0
print(coal.params['migr_matrix'])

print('diag:', coal.params['migr_matrix'][0, 0])
coal.params['migr_matrix'][0, 0] = None

print(coal.params['migr_matrix'])

coal.params['migr_matrix'] = [[None, 1.0, 0.1, 0.1],
                              [1.0, None, 1.0, 0.1], 
                              [0.1, 1.0, None, 1.0],
                              [0.1, 0.1, 1.0, None]]

print(coal.params.summary())

coal = egglib.coalesce.Simulator(num_pop=4, num_chrom=[10, 10, 10, 10], theta=1)
print(coal.params['events'])

coal.params.add_event(cat='size', T=0.4, idx=0, N=0.1)
coal.params.add_event(cat='size', T=0.5, idx=0, N=1.0)
print(coal.params['events'])

print(coal.params['events'])
coal.params.add_event('size', T=1.0, idx=0, N=2.0)
coal.params.add_event('migr', T=1.8, M=1.5)
coal.params.add_event('size', T=1.2, N=1.0)
print(coal.params['events'])


coal = egglib.coalesce.Simulator(num_pop=4, num_chrom=[10, 10, 10, 10], theta=1)
print(coal.params['events'])

coal.params.add_event('size', 0.4, idx=0, N=0.1)
coal.params.add_event('size', 0.5, idx=0, N=1.0)
print(coal.params['events'])

print(coal.params['events'][0])

coal.params['events'].update(0, N=0.05)
print(coal.params['events'])

c = egglib.coalesce.Simulator(num_pop=1, num_chrom=[50], theta=5.0)
c.params.add_event(cat='size', T=0.2, N=0.01)
c.params.add_event(cat='size', T=0.21, N=1.0)

c.params['events'].clear()
c.params.add_event(cat='bottleneck', T=0.2, S=1.0)

c = egglib.coalesce.Simulator(num_pop=2)
c.params.add_event(cat='admixture', T=0.5, src=0, dst=1, proba=0.5)

c = egglib.coalesce.Simulator(num_pop=2, num_chrom=[20, 0], migr=0)
c.params.add_event(cat='admixture', T=0.5, src=0, dst=1, proba=0.5)
c.params.add_event(cat='pair_migr', T=0.5, src=0, dst=1, M=0.1)
c.params.add_event(cat='pair_migr', T=0.5, src=1, dst=0, M=0.1)

c = egglib.coalesce.Simulator(num_pop=2, num_chrom=[20, 20])
c.params.add_event(cat='admixture', T=0.5, src=1, dst=0, proba=1)

c = egglib.coalesce.Simulator(num_pop=2, num_chrom=[20, 20], migr=1)
c.params.add_event(cat='merge', T=0.5, src=1, dst=0)
print(c.params['events'])

c = egglib.coalesce.Simulator(num_pop=3, num_chrom=[20, 0, 0])
c.params['migr_matrix'] = [[None, 1, 0],
                           [1, None, 0],
                           [0, 0, None]]

c = egglib.coalesce.Simulator(num_pop=2, num_chrom=[1, 1])
try: c.simul()
except RuntimeError: print('error caught')
else: raise AssertionError

c = egglib.coalesce.Simulator(num_pop=3, num_chrom=[20, 0, 0])
c.params['migr_matrix'] = [[None, 1, 0],
                           [1, None, 0],
                           [0, 0, None]]
c.params.add_event(cat='admixture', T=0.3, src=1, dst=2, proba=0.2)
c.params.add_event(cat='merge', T=0.5, src=0, dst=1)
try:
    for x in c.iter_simul(1000):
        print('done')
except RuntimeError: print('error caught')
else: raise AssertionError


c = egglib.coalesce.Simulator(num_pop=3, num_chrom=[20, 0, 0])
c.params['migr_matrix'] = [[None, 1, 0],
                           [1, None, 0],
                           [0, 0, None]]
c.params.add_event(cat='admixture', T=0.5, src=1, dst=2, proba=0.2)
try:
    for x in c.iter_simul(1000):
        print('done')
except RuntimeError: print('error caught')
else: raise AssertionError

c = egglib.coalesce.Simulator(num_pop=1, num_chrom=[20])
c.params.add_event(cat='sample', T=0.5, idx=0, label='1', num_chrom=20, num_indiv=0)
print(c.params.summary())
c.simul()

c = egglib.coalesce.Simulator(num_pop=2, num_chrom=[20, 0])
c.params.add_event(cat='sample', T=0.5, idx=0, label='1', num_chrom=20, num_indiv=0)
c.params.add_event(cat='merge', T=1.0, src=1, dst=0)
print(c.params.summary())
c.simul()

c = egglib.coalesce.Simulator(num_pop=1, num_chrom=[5], theta=5.0)
aln = c.simul()
print(aln.ns, aln.ls)
print(aln.fasta(alphabet=egglib.alphabets.DNA))
aln = c.simul()
print(aln.ns, aln.ls)

c.params['theta'] = 1.0
c.params['num_alleles'] = 4
c.params['num_sites'] = 50
aln = c.simul()
print(aln.ns, aln.ls)
print(aln.fasta(alphabet=egglib.alphabets.DNA))


c = egglib.coalesce.Simulator(num_pop=3, num_indiv=[4, 4, 1], theta=5.0)
c.params.add_event(cat='merge', T=0.5, src=0, dst=1)
c.params.add_event(cat='merge', T=3, src=2, dst=1)
aln = c.simul()
print(aln.ns, aln.ls)
print(aln.fasta(alphabet=egglib.alphabets.DNA, labels=True))

aln_list = []
for i in range(5):
    aln = c.simul()
    aln_list.append(aln)
print(list(map(hash, aln_list)))

del aln_list[:]
for aln in c.iter_simul(5):
    aln_list.append(aln)
print(list(map(hash, aln_list)))

cs = egglib.stats.ComputeStats()
cs.add_stats('D', 'Hsd', 'S')
for stats in c.iter_simul(10, cs=cs):
    print(stats)

c = egglib.coalesce.Simulator(num_pop=1, num_chrom=[20])
theta_values = [2.5645, 4.4111, 6.5677, 1.8904, 2.1915, 0.9696, 2.8418, 5.221, 4.9423, 9.0793]
for aln in c.iter_simul(10, theta=theta_values):
    print(aln.ls)

print('trees')
c = egglib.coalesce.Simulator(num_pop=1, num_chrom=[10], recomb=1.0, theta=0.0)
trees = []
for aln in c.iter_simul(100, dest_trees=trees):
    pass

print(len(trees[0]))
for tree, start, stop in trees[0]:
    print('segment')
    print('  ', start)
    print('  ', stop)
    print('  ', tree.newick())

c = egglib.coalesce.Simulator(num_pop=3, num_indiv=[4, 4, 1], theta=5.0)
c.params.add_event(cat='merge', T=0.5, src=0, dst=1)
c.params.add_event(cat='merge', T=3, src=2, dst=1)
struct = c.params.mk_structure(outgroup_label='2')
print(struct.as_dict())

cs = egglib.stats.ComputeStats()
cs.add_stats('FstWC', 'Fis')
cs.set_structure(struct)
for stats in c.iter_simul(10, cs=cs):
    print(stats)
