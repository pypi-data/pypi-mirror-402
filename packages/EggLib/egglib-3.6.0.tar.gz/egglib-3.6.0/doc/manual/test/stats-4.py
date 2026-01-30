import egglib

print(egglib.config.htslib)

vcf = egglib.io.VcfParser('example.vcf')
print([vcf.get_sample(i) for i in range(vcf.num_samples)])

meta = dict([vcf.get_meta(i) for i in range(vcf.num_meta)])
print(meta)

print('----')

for ret in vcf:
  print(ret)

print('----')

vcf.rewind()
while vcf.good:
    print(next(vcf))

print('----')

vcf = egglib.io.VcfParser('example.vcf')
print(next(vcf))
site = egglib.site_from_vcf(vcf)
print(site.as_list())
print(next(vcf))
site.from_vcf(vcf)
print(site.as_list())

print('----')

vcf = egglib.io.VcfParser('example.vcf')
for chrom, pos, nall in vcf:
    v = vcf.get_variant()
    if 'HQ' in v.format_fields:
        print([i['HQ'] for i in v.samples])
    else:
        print('no data')

print('----')

vcf = egglib.io.VCF('example.vcf')
print(vcf.get_samples())
print(vcf.get_pos())

print('----')
while vcf.read():
    print(vcf.get_chrom(), vcf.get_pos())

print('----')

egglib.io.index_vcf('data.bcf')
vcf = egglib.io.VCF('data.bcf')
print(vcf.has_index)

egglib.io.index_vcf('data.bcf', outname='another_name.csi')
vcf = egglib.io.VCF('data.bcf', index='another_name.csi')
print(vcf.has_index)

print('----')

egglib.io.index_vcf('data.bcf')
vcf.read()
print(vcf.get_chrom(), vcf.get_pos())

vcf.goto('ctg2', 1019)
print(vcf.get_chrom(), vcf.get_pos())
vcf.goto('ctg1', 1009)
print(vcf.get_chrom(), vcf.get_pos())

vcf.goto('ctg2')
print(vcf.get_chrom(), vcf.get_pos())

print('----')

#vcf.goto('ctg4')

#vcf.goto('ctg3', 1000)

vcf.goto('ctg3', 1000, limit=1100)
print(vcf.get_chrom(), vcf.get_pos())

print('----')

print(vcf.get_infos())
print(vcf.get_info('AA'))

print('----')

print(vcf.get_formats())

print('----')

print(vcf.is_snp())
genotypes = vcf.get_genotypes()
print(genotypes)
site = egglib.site_from_list([j for i in genotypes for j in i],
    alphabet = egglib.alphabets.DNA)
struct = egglib.struct_from_samplesizes([4], ploidy=3)
print(struct.as_dict())

