import egglib

print(egglib.wrappers.paths['clustal'])
#None

cnt = egglib.io.from_fasta('sequences3.fas', cls=egglib.Container, alphabet=egglib.alphabets.DNA)
aln = egglib.wrappers.clustal(cnt)

egglib.wrappers.paths.autodetect(True)
#> codeml: codeml --> ok
#> phyml: phyml --> fail ("No such file or directory")
#> clustal: clustalo --> fail ("No such file or directory")
#> muscle: muscle --> ok

print(egglib.wrappers.paths['clustal'])
# None

#egglib.wrappers.paths['clustal'] = '/home/stephane/Documents/software/clustal-omega-1.2.1/src/clustalo'
print(egglib.wrappers.paths['clustal'])

#egglib.wrappers.paths.save()

#egglib.wrappers.paths['phyml'] = '/home/stephane/Documents/software/phyml-master/src/phyml'

aln = egglib.io.from_fasta('align8.fas', alphabet=egglib.alphabets.DNA)
tree, stats = egglib.wrappers.phyml(aln, model='HKY85')
print(stats)
#{'freqs': [0.2844, 0.19657, 0.22759, 0.29143], 'ti/tv': 4.0, 'pars': 6983, 'lk': -33416.88715, 'size': 5.44449}
print(tree.newick())
#(CasLYK3:0.01237505,CasLYK2:0.0,((FvLYK2:0.09853004,(MdLYK3:0.10732566,PpLYK3:0.05300631):0.02447224):0.05989021,(PtLYK3:0.15268966,((MtLYK8:0.14003722,(LjLYS7:0.08155174,(GmLYK3:0.04846372,CacLYK3:0.05809886):0.04392275):0.02845355):0.11447351,((VvLYK3:0.11542039,VvLYK2:0.08334382):0.06445392,(VvLYK1:0.12763572,((PtLYK2:0.05871896,PtLYK1:0.03968281):0.11719099,((((CacLYK1:0.0760468,(GmNFR1a:0.03511832,GmNFR1b:0.0287519):0.02035824):0.03344143,(LjNFR1a:0.07231443,(MtLYK2:0.04784824,(MtLYK3:0.07366331,PsSYM37:0.06907117):0.01683888):0.05128711):0.02178421):0.14129609,((CecLYK1:0.1342407,((MtLYK7:0.11288812,(CacLYK4:0.05284059,GmLYK2:0.048187):0.05687575):0.04162164,((MtLYK1:0.13291815,LjNFR1b:0.11749646):0.06448685,(MtLYK6:0.13391465,LjNFR1c:0.11699053):0.03439881):0.02680216):0.04837524):0.03794071,(CecLYK2:0.07421816,((GmLYK2b:0.05222029,CacLYK2:0.07144586):0.05212459,(LjLYS6:0.05742719,MtLYK9:0.10847179):0.02814181):0.06743708):0.01846505):0.02443726):0.05441246,(CasLYK1:0.10100211,(AtCERK1:0.35336624,(FvLYK1:0.12483414,((MdLYK2:0.05670659,MdLYK1:0.03964285):0.04192224,(PpLYK1:0.06030315,PpLYK2:0.05194511):0.02388192):0.03157062):0.04509856):0.01641018):0.02078968):0.02797866):0.04205346):0.06152622):0.05814891):0.02685265):0.02416823):0.14995695);

#print(aln.ns, tree.num_leaves)
#print(aln.ls)

aln = egglib.tools.to_codons(aln)
results = egglib.wrappers.codeml(aln, tree, 'M1a')
print(results['freq'])
print(results['omega'])
print(results['lnL'])
print(results['site_w']['postw'])
