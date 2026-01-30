import sys, urllib.request, re, inspect, os, datetime, egglib
url = 'http://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi'

# manual
def manual():
    sys.exit("""usage:
    python update-genetic-code.py <check|update>
""")

# function to determine all possible codons based on code redundancy
expand_table = {
    'A': ['A'],
    'C': ['C'],
    'G': ['G'],
    'T': ['T'],
    'R': ['A', 'G'],
    'Y': ['C', 'T'],
    'S': ['G', 'C'],
    'W': ['A', 'T'],
    'K': ['G', 'T'],
    'M': ['A', 'C'],
    'B': ['C', 'G', 'T'],
    'D': ['A', 'G', 'T'],
    'H': ['A', 'C', 'T'],
    'V': ['A', 'C', 'G'],
    'N': ['A', 'C', 'G', 'T']}

def expand_codon(c):
    bases = []
    for i in range(3):
        if c[i] not in expand_table: return None
        else: bases.append(expand_table[c[i]])
    ret = []
    for b1 in bases[0]:
        for b2 in bases[1]:
            for b3 in bases[2]:
                ret.append(b1+b2+b3)
    return ret

# compute number of NS sites for a codon
def NS_sites(code, codon):
    # number of (non-)synonymous sites for the codon
    # NS1, S1: taking stop as an amino acid (NS1 + S1 = 3)
    # NS2, S2: excluding stops (NS1 + S1 rarely < 3; NS2=S2=0 from stop codons)

    aa = code[codon][0]
    NS1 = 0.0
    NS2 = 0.0
    S1 = 0.0
    S2 = 0.0
    for i in range(3):
        nsyn_changes = 0
        syn_changes = 0
        stop_changes = 0
        for x in 'TCAG':
            if x == codon[i]: continue
            alt = list(codon)
            alt[i] = x
            alt_aa = code[''.join(alt)][0]
            if alt_aa == '*': stop_changes += 1
            if aa != alt_aa: nsyn_changes += 1
            else: syn_changes += 1
        NS1 += nsyn_changes / 3.0
        S1 += syn_changes / 3.0
        if aa != '*' and stop_changes < 3:
            NS2 += (nsyn_changes - stop_changes) / (3.0 - stop_changes)
            S2 += syn_changes / (3.0 - stop_changes)
    if aa == '*': assert NS2 == 0.0 and S2 == 0.0
    assert abs((NS1 + S1) - 3) < 0.0000000001
    return NS1, S1, NS2, S2

# import genetic code from NCBI site
def NCBIcodes(fname):
    print('reading', fname)
    r = urllib.request.urlopen(fname)
    page = r.read()

    codes = re.findall(b'(\d+)\. ([A-Za-z0-9/\, -]+) \(transl_table\=(\d+)\)', page)
    for i in codes:print(i)
    AA = re.findall(b'AAs  = ([A-Z*]{64})', page)
    start = re.findall(b'Starts = ([M\-*]{64})', page)
    base1 = re.findall(b'Base1  = ([ACGT]{64})', page)
    base2 = re.findall(b'Base2  = ([ACGT]{64})', page)
    base3 = re.findall(b'Base3  = ([ACGT]{64})', page)

    codes = [[j.decode(encoding='ASCII') for j in i] for i in codes]
    AA = [i.decode(encoding='ASCII') for i in AA]
    start = [i.decode(encoding='ASCII') for i in start]
    base1 = [i.decode(encoding='ASCII') for i in base1]
    base2 = [i.decode(encoding='ASCII') for i in base2]
    base3 = [i.decode(encoding='ASCII') for i in base3]

    # consistency of NCBI codes
    lens = set([len(codes), len(AA), len(start), len(base1), len(base2), len(base3)])
    if len(lens)!=1:
        print('lens:', [len(codes), len(AA), len(start), len(base1), len(base2), len(base3)])
        sys.exit('error: cannot parse NCBI page (inconsistent number of items)')
    for i in base1:
        if i != 'T'*16+'C'*16+'A'*16+'G'*16: sys.exit('error: cannot parse NCBI page (invalid Base1 string)')
    for i in base2:
        if i != ('T'*4+'C'*4+'A'*4+'G'*4)*4: sys.exit('error: cannot parse NCBI page (invalid Base1 string)')
    for i in base3:
        if i != 'TCAG'*16: sys.exit('error: cannot parse NCBI page (invalid Base1 string)')

    # create dict
    ret = {}
    for (num, name, tt), aa, st, b1, b2, b3 in zip(codes, AA, start, base1, base2, base3):
        if num != tt: sys.exit('error: cannot parser NCBI page (unmatching trans_table code)')
        k = int(num)
        if k in ret: sys.exit('error: cannot parser NCBI page (duplicated code)')
        ret[k] = [name, {}]
        for B1,B2,B3,m,n in zip(b1, b2, b3, aa, st):
            ret[k][1][B1+B2+B3] = m,n
    return ret

# check if current implementation is consistent with NCBI website
def check():
    import egglib
    eggcodes = dict([(i, j.name()) for (i, j) in egglib.tools._code_tools._codes.items()])
    ncbicodes = NCBIcodes(url)

    flag = False
    if len(eggcodes) != len(ncbicodes):
        print('number of codes (EggLib: {0}; NCBI: {1})'.format(len(eggcodes), len(ncbicodes)))
        flag = True

    d = set(eggcodes).difference(ncbicodes)
    if len(d):
        print('not anymore in NCBI: {0}'.format(', '.join(map(str, sorted(d)))))
        flag = True

    d = set(ncbicodes).difference(eggcodes)
    if len(d):
        print('new in NCBI: {0}'.format(', '.join(map(str, sorted(d)))))
        flag = True

    for k in sorted(eggcodes):
        if k in ncbicodes:
            a = egglib.tools._code_tools._codes[k].name()
            b = ncbicodes[k][0]
            if a != b:
                print('name of {0} has changed\n    from {1}\n    to {2}'.format(k, a, b))
                flag = True

    if not flag:
        print('no difference detected')

# generate a new GeneticCode.epp file from NCBI web site
def update():
    today = datetime.date.today()
    codes = NCBIcodes(url)
    ids = sorted(codes)
    expl, miss = egglib.alphabets.codons.get_alleles()
    NUM = len(expl+miss)

    with open(os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())), 'GeneticCode.epp'), 'w') as f:

        f.write(u"""// Autogenerated by {2}: {1}

    /*
        Copyright {0} St\xe9phane De Mita, Mathieu Siol

        This file is part of the EggLib library.

        EggLib is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        EggLib is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with EggLib.  If not, see <http://www.gnu.org/licenses/>.
    */

    """.format(today.year, today.isoformat(), os.path.basename(__file__)))

        # number and list of codes
        f.write("""
        unsigned int GeneticCode::num_codes() {{ return {0}; }}

        const unsigned int GeneticCode::_codes[] = {{ {1} }};

    """.format(len(ids), ', '.join(map(str, ids))))
        f.write('    const char * GeneticCode::_names[] = {\n')

        names = []
        for i in ids:
            names.append(codes[i][0])
        f.write(',\n'.join(['        "{0}"'.format(name) for name in names]))
        f.write('    };\n\n\n')

        # aa translations
        AA = []
        for id in ids:
            for c in expl:
                AA.append('{0:>3}'.format(egglib.alphabets.protein.get_code(codes[id][1][c][0])))
            for c in miss:
                if c == '---': aa = '-'
                else:
                    cs = expand_codon(c)
                    if cs is None:
                        if c == '---': aa = '-'
                        else: aa = 'X'
                    else:
                        aas = set()
                        for ci in cs:
                            aas.add(codes[id][1][ci][0])
                        if len(aas) == 0: raise RuntimeError('what?')
                        elif len(aas) > 1: aa = 'X'
                        else: aa = aas.pop()
                AA.append('{0:>3}'.format(egglib.alphabets.protein.get_code(aa)))
        f.write('    const int GeneticCode::_aa[] = {\n        ')
        f.write(',\n        '.join([', '.join(AA[i:i+NUM]) for i in range(0, len(AA), NUM)]))
        f.write(' };\n\n')

        # start status
        START = []
        for id in ids:
            for c in expl:
                print(id, c, codes[id][1][c])
                START.append('\'' + codes[id][1][c][1] + '\'')
            for c in miss:
                cs = expand_codon(c)
                if cs is None: start = '?'
                else:
                    starts = set()
                    for ci in cs: starts.add(codes[id][1][ci][1])
                    if len(starts) == 0: raise RuntimeError('what?')
                    elif len(starts) > 1: start = '?'
                    else: start = starts.pop()
                START.append('\'' + start + '\'')
        f.write('\n    const char GeneticCode::_start[] = {\n        ')
        f.write(',\n        '.join([', '.join(START[i:i+NUM]) for i in range(0, len(START), NUM)]))
        f.write(' };\n\n')

        # number of NS/S sites
        NS1 = []
        NS2 = []
        S1 = []
        S2 = []
        for id in ids:
            for c in expl:
                ns1, s1, ns2, s2 = NS_sites(codes[id][1], c)
                NS1.append('{0:.12f}'.format(ns1))
                S1.append('{0:.12f}'.format(s1))
                NS2.append('{0:.12f}'.format(ns2))
                S2.append('{0:.12f}'.format(s2))

        f.write('\n    const double GeneticCode::_NS1[] = {\n        ')
        f.write(',\n        '.join([', '.join(NS1[i:i+len(expl)]) for i in range(0, len(NS1), len(expl))]))
        f.write(' };\n\n')

        f.write('\n    const double GeneticCode::_S1[] = {\n        ')
        f.write(',\n        '.join([', '.join(S1[i:i+len(expl)]) for i in range(0, len(S1), len(expl))]))
        f.write(' };\n\n')

        f.write('\n    const double GeneticCode::_NS2[] = {\n        ')
        f.write(',\n        '.join([', '.join(NS2[i:i+len(expl)]) for i in range(0, len(NS2), len(expl))]))
        f.write(' };\n\n')

        f.write('\n    const double GeneticCode::_S2[] = {\n        ')
        f.write(',\n        '.join([', '.join(S2[i:i+len(expl)]) for i in range(0, len(S2), len(expl))]))
        f.write(' };\n\n')

########################################################################

if len(sys.argv) != 2: manual()
if sys.argv[1] == 'check': check()
elif sys.argv[1] == 'update': update()
else: manual()
