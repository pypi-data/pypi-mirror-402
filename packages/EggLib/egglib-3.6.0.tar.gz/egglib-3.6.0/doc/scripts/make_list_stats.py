import egglib, os, operator

# get the table content
table = []
stats = egglib.stats.ComputeStats().list_stats()
stats.sort(key=operator.itemgetter(0))
for code, descr in stats:
    table.append([
        code,
        descr,
        'NA', 'NA', 'NA', 'NA', 'NA'])

# format the table
header = ['Code', 'Description', 'Per site', 'Per region', 'Whole sample', 'Per pop', 'Per pair']
len_cols = [max((len(header[i]), max([len(row[i]) for row in table]))) for i in range(len(header))]
separator = ' '.join(['='*i for i in len_cols])

# write file
f = open(os.path.join('py', 'list_stats.txt'), 'w')
f.write('\n.. _list_stats:\n\n')
f.write('List of statistics\n******************\n\n')
f.write(separator + '\n')
f.write(' '.join([i.ljust(j) for (i,j) in zip(header, len_cols)]) + '\n')
f.write(separator + '\n')
for row in table:
    f.write(' '.join([i.ljust(j) for (i,j) in zip(row, len_cols)]) + '\n')
f.write(separator + '\n')
f.write('\n')
f.close()
