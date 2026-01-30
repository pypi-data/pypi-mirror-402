import egglib

aln2 = egglib.io.from_fasta('align2.fas', alphabet=egglib.alphabets.DNA, labels=True)
print(aln2.get_name(0), aln2.get_label(0, 0))

print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

aln2 = egglib.io.from_fasta('align2.fas', alphabet=egglib.alphabets.DNA)
#print(aln2.get_label(0, 0)) -> IndexError

aln3 = egglib.io.from_fasta('align3.fas', alphabet=egglib.alphabets.DNA, labels=True)
print(aln3.get_name(0))
print(aln3.get_label(0, 0))
print(aln3.get_label(0, 1))

print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

aln = egglib.io.from_fasta('align5.fas', alphabet=egglib.alphabets.DNA, labels=True)
struct = egglib.struct_from_labels(aln, lvl_clust=0, lvl_pop=1, lvl_indiv=2)
print(struct.as_dict())

print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

struct2 = egglib.struct_from_labels(aln, lvl_pop=0)
print(struct2.as_dict())

print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

struct = egglib.struct_from_samplesizes([20, 20])
print(struct.as_dict())

struct = egglib.struct_from_samplesizes([10, 10], ploidy=2, outgroup=1)
print(struct.as_dict())

print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

labels = [
    ('c1', 'p1', 'i01'),
    ('c1', 'p1', 'i01'),
    ('c1', 'p1', 'i02'),
    ('c1', 'p1', 'i02'),
    ('c1', 'p1', 'i03'),
    ('c1', 'p1', 'i03'),
    ('c1', 'p2', 'i04'),
    ('c1', 'p2', 'i04'),
    ('c1', 'p2', 'i05'),
    ('c1', 'p2', 'i05'),
    ('c1', 'p2', 'i06'),
    ('c1', 'p2', 'i06'),
    ('c1', 'p2', 'i07'),
    ('c1', 'p2', 'i07'),
    ('c2', 'p3', 'i08'),
    ('c2', 'p3', 'i08'),
    ('c2', 'p3', 'i09'),
    ('c2', 'p3', 'i09'),
    ('c2', 'p3', 'i10'),
    ('c2', 'p3', 'i10'),
    ('c2', 'p4', 'i11'),
    ('c2', 'p4', 'i11'),
    ('c2', 'p4', 'i12'),
    ('c2', 'p4', 'i12'),
    ('c2', 'p5', 'i13'),
    ('c2', 'p5', 'i13'),
    ('c2', 'p5', 'i14'),
    ('c2', 'p5', 'i14'),
    ('c2', 'p5', 'i15'),
    ('c2', 'p5', 'i15')]
struct = egglib.struct_from_iterable(labels, fmt='CPI')
print(struct.as_dict())

print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

cs = egglib.stats.ComputeStats()
cs.add_stats('Fis', 'FistWC', 'FisctWC', 'Gst')
print(cs.process_align(aln))

print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

cs.configure(struct=struct)
print(cs.process_align(aln))

print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

cs.configure(struct=struct2)
print(cs.process_align(aln))
