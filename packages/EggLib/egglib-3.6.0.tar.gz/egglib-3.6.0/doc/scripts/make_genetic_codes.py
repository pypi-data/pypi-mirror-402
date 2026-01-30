import egglib, os, sys

codes = egglib.tools._code_tools._codes
ids = sorted(codes)
names = [codes[i].name() for i in ids]

f = open(os.path.join('py', 'list_genetic_codes.txt'), 'w')

ln1 = 10
ln2 = 55

sep = '+' + '-' * (ln1+2) + '+' + '-' * (ln2 + 2) + '+\n'
f.write(sep)
f.write('| Identifier | ' + 'Code'.ljust(ln2) + ' |\n')
f.write('+' + '=' * (ln1+2) + '+' + '=' * (ln2 + 2) + '+\n')
for i, name in zip(ids, names):
    f.write('| ' + str(i).ljust(ln1) + ' | ')
    if len(name) <= ln2:
        f.write(name.ljust(ln2) + ' |\n')
    else:
        idx = name[:ln2].rfind(' ')
        f.write(name[:idx].ljust(ln2) + ' |\n')
        f.write('| ' + ' '*ln1 + ' | ')
        f.write(name[idx+1:].ljust(ln2) + ' |\n') # +1 to skip the space
    f.write(sep)

missing = [i+1 for i in range(ids[-1]) if i+1 not in ids]
f.write('\n')
f.write('Note that the following code identifiers do not exist: ')
assert len(missing) > 1
f.write(', '.join(map(str, missing[:-1])))
f.write(', and {0}'.format(missing[-1]))
f.write(', as well as 0 and values above {0}.\n'.format(ids[-1]))

f.close()

