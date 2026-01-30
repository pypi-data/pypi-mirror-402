import egglib

aln = egglib.io.from_fasta('align1.fas',alphabet=egglib.alphabets.DNA)
print(aln.ns, aln.ls)

cnt = egglib.io.from_fasta('sequences1.fas',alphabet=egglib.alphabets.DNA)
print(type(cnt))

aln2 = egglib.io.from_fasta('align1.fas', cls=egglib.Align, alphabet=egglib.alphabets.DNA)
cnt2 = egglib.io.from_fasta('align1.fas', cls=egglib.Container, alphabet=egglib.alphabets.DNA)

aln.fasta('align_out.fas')
print(aln.fasta())

aln2 = egglib.io.from_fasta('align2.fas', alphabet=egglib.alphabets.DNA, labels=True)
print(aln2.get_name(0), aln2.get_label(0, 0))

aln2 = egglib.io.from_fasta('align2.fas', alphabet=egglib.alphabets.DNA)
try: print(aln2.get_label(0, 0))
except IndexError: pass
else: raise AssertionError

aln3 = egglib.io.from_fasta('align3.fas', alphabet = egglib.alphabets.DNA, labels=True)
print(aln3.get_name(0))
print(aln3.get_label(0, 0))
print(aln3.get_label(0, 1))

aln4 = egglib.io.from_fasta('align4.fas', alphabet=egglib.alphabets.DNA, labels=True)
print(aln4.ns)
for item in aln4:
    print(item.name)

print(aln4[0].name)
print(aln4.get_sample(0).name)

item = aln4.get_sample(0)
print(item.name)
print(aln4.get_name(0))
aln4.set_name(0, 'another name')
print(item.name)

item = aln4.get_sample(0)
item.sequence = 'ACCGTGGAGAGCGCGTTGCA'

aln5 = egglib.Align(alphabet=egglib.alphabets.DNA)
print(aln5.ns, aln5.ls)

aln6 = egglib.Align(nsam=6, nsit=4, init='N',alphabet=egglib.alphabets.DNA)
print(aln6.ns, aln6.ls)
print(aln6.fasta())


aln = egglib.io.from_fasta('align4.fas', alphabet=egglib.alphabets.DNA, labels=True)
copy = aln
aln.set_sequence(0, 'CCTCCTCCTCCTCCTCCTCT')
print(copy.get_sequence(0).string())

aln = egglib.io.from_fasta('align4.fas', alphabet=egglib.alphabets.DNA, labels=True)
copy = egglib.Align.create(aln)
aln.set_sequence(0, 'CCTCCTCCTCCTCCTCCTCT')
print(copy.get_sequence(0).string())

cnt = egglib.Container.create(aln)

cnt = egglib.io.from_fasta('sequences2.fas', alphabet=egglib.alphabets.DNA)
print(type(cnt))
print(cnt.is_matrix)
print(cnt.ls(0))
print(cnt.ls(2))

cnt.del_sites(2, 20, 7)
aln = egglib.Align.create(cnt)
print(aln.fasta())

aln = egglib.Align.create([('sample1', 'ACCGTGGAGAGCGCGTTGCA'),
                           ('sample2', 'ACCGTGGAGAGCGCGTTGCA'),
                           ('sample3', 'ACCGTGGAGAGCGCGTTGCA'),
                           ('sample4', 'ACCGTGGAGAGCGCGTTGCA')], alphabet = egglib.alphabets.DNA)
print(aln.fasta())

aln = egglib.io.from_fasta('align1.fas',alphabet=egglib.alphabets.DNA)

aln = egglib.io.from_fasta('align4.fas', alphabet=egglib.alphabets.DNA)
print(aln.get_sequence(0).string())

aln = egglib.io.from_fasta('align4.fas', alphabet=egglib.alphabets.DNA)
seq =  aln.get_sequence(0)
print(seq[:])
print(aln.get_sequence(0)[:])

coal = egglib.coalesce.Simulator(1, num_chrom=[10], theta=2.0)
aln = coal.simul()
try: print(aln.get_sequence(0).string())
except ValueError: pass
else: raise AssertionError

seq =  aln.get_sequence(0)
print(seq[:])

print(aln.fasta(alphabet=egglib.alphabets.DNA))

aln = egglib.Align.create([
        ('sample1',  'TTGCTAGGTGTATAG'),
        ('sample2',  'TTCCTAGATGAATAG'),
        ('sample3',  'ATGCTAGATGAATAG')],
        alphabet=egglib.alphabets.DNA)
aln.to_codons()
prot = egglib.tools.translate(aln)
print(prot.fasta())

aln = egglib.Align.create([
        ('sample1',  'TTGCTAGGTGTATAG'),
        ('sample2',  'TTCCTAGATGAATAG'),
        ('sample3',  'ATGCTAGATGAATAG')],
        alphabet = egglib.alphabets.DNA)
aln.to_codons()
egglib.tools.translate(aln, in_place=True) # returns None
print(aln.fasta())
