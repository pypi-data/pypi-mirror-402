import egglib, os

indent = 8

opts = []

# get flag options
for code in sorted(egglib.wrappers._muscle._args):
    type_, test = egglib.wrappers._muscle._args[code]
    code = '``{0}``'.format(code)
    if type_ == bool:
        opts.append((code, 'a boolean'))

# get value options
for code in sorted(egglib.wrappers._muscle._args):
    type_, test = egglib.wrappers._muscle._args[code]
    code = '``{0}``'.format(code)
    if type_ == bool:
        pass
    elif type_ == int:
        opts.append((code, 'an integer'))
    elif type_ == float:
        opts.append((code, 'a float'))
    elif type_ == str:
        opts.append((code, 'one of: {0}'.format(', '.join(['``{0}``'.format(i) for i in test]))))
    else:
        raise TypeError(str(type_))

# get column size
header = 'option', 'value'
n = max(map(len, [i for i,j in opts]))
n = max((n, len(header[0])))
m = max(map(len, [j for i,j in opts]))
m = max((m, len(header[1])))

# write file
f = open(os.path.join('py', 'muscle_arguments.txt'), 'w')
f.write(' '*indent + '='*n + ' ' + '='*m + '\n')
f.write(' '*indent + ' '.join(header) + '\n')
f.write(' '*indent + '='*n + ' ' + '='*m + '\n')
for i, j in opts:
    f.write(' '*indent + i.ljust(n) + ' ' + j.ljust(m) + '\n')
f.write(' '*indent + '='*n + ' ' + '='*m + '\n')
f.close()
