"""
    Copyright 2008-2023 Stephane De Mita, Mathieu Siol

    This file is part of EggLib.

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
"""

import re, sys
from io import StringIO
_staden_table = str.maketrans(' -*', '?N-')
from .. import eggwrapper as _eggwrapper
from .. import _interface, alphabets

special_DNA = alphabets.Alphabet('char', alphabets.DNA.get_alleles()[0], alphabets.DNA.get_alleles()[1], case_insensitive=True, name='DNA with dot')
special_DNA.add_missing('.')
special_DOT = special_DNA._obj.get_code('.')
special_MISSING = special_DNA._obj.get_code('?')
MISSING = alphabets.DNA._obj.get_code('?')

def from_clustal(string, alphabet):
    """
    Import a clustal-formatted alignment. The input format is the one
    generated and used by `ClustalW <http://www.clustal.org/clustal2/>`_.

    :param string: clustal-formatted sequence alignment.
    :param alphabet: an :class:`.Alphabet` instance.
    :return: A new :class:`.Align` instance.
    """

    if not isinstance(alphabet._obj, _eggwrapper.CharAlphabet):
        raise ValueError('invalid alphabet for parsing fasta data: {0}'.format(alphabet.name))
    stream = StringIO(string)

    # the first line must start by CLUSTAL W or CLUSTALW
    line = stream.readline()
    c = 1
    if (line[:8] != 'CLUSTALW' and
        line[:9] != 'CLUSTAL W' and
        line.strip() != 'CLUSTAL'): raise ValueError('invalid clustalw string (line: {0})'.format(c))

    # start reading blocks
    cnt = _eggwrapper.DataHolder(False)
    line = stream.readline()

    # initialize names list
    names = []

    while True:
        
        # skip empty lines
        while line != '' and line.strip() == '':
            line = stream.readline()
            c += 1

        # detect end of file
        if line == '': break

        # read a block
        block_length = None

        # read sequences
        while True:

            # conservation line
            if line[0] == ' ':
                if block_length is None: raise ValueError('invalid clustalw string (line: {0})'.format(c))
                line = stream.readline()
                c += 1
                if line == '': break # end of file
                if line.strip() != '': raise ValueError('invalid clustalw string (line: {0})'.format(c))
                break

            # reads sequence
            bits = line.split()

            # sequence line
            if len(bits) < 2 or len(bits) > 3:
                raise ValueError('invalid clustalw string (line: {0})'.format(c))

            name = bits[0]
            seq = bits[1]
            if block_length is None:
                block_length = len(seq)
            elif block_length != len(seq):
                raise ValueError('invalid clustalw string (line: {0})'.format(c))

            # adds the sequence to the container (new sequence)
            if name not in names:
                pos = len(names)
                cnt.set_nsam(pos + 1)
                cnt.set_name(pos, name)
                cnt.set_nsit_sample(pos, len(seq))
                for i, v in enumerate(seq):
                    cnt.set_sample(pos, i, alphabet._obj.get_code(v))
                names.append(name)

            # adds the sequence (continuing old sequence)
            else:
                pos = names.index(name)
                cur = cnt.get_nsit_sample(pos)
                cnt.set_nsit_sample(pos, cur + len(seq))
                for i, v in enumerate(seq):
                    cnt.set_sample(pos, cur+i, alphabet._obj.get_code(v))

            if len(bits) == 3:
                try:
                    i = int(bits[2])
                except ValueError:
                    raise ValueError('invalid clustalw string (line: {0})'.format(c))
                if cnt.get_nsit_sample(pos) != i:
                    raise ValueError('invalid clustalw string (line: {0})'.format(c))

            # checks next line
            line = stream.readline()
            c += 1
              
            # empty (or absent) conservation line is caught by this line
            if line.strip() == '': break

    if not cnt.is_equal(): raise ValueError('invalid clustalw string (unequal sequences)')
    return _interface.Align._create_from_data_holder(cnt, alphabet)

def from_staden(string, keep_consensus=False):
    """
    Import data from the Staden assembly package.
    Process the output file of the GAP4 program of the
    `Staden <http://staden.sourceforge.net/>`_ package.

    :param string: input string.
    :param keep_consensus: don't delete consensus sequence.
    :return: An :class:`.Align` instance.

    The input string should have been generated from a contig alignment by
    the GAP4 contig editor, using the command "dump contig to file". The
    sequence named ``CONSENSUS``, if present, is automatically removed
    unless the option *keep_consensus* is used.

    Staden's default convention is followed:

    * ``-`` codes for an unknown base and is replaced by ``N``.
    * ``*`` codes for an alignment gap and is replaced by ``-``.
    * ``.`` represents the same sequence than the consensus at that
      position.
    * White space represents missing data and is replaced by ``?``.
    """

    # get shift from the first CONSENSUS line
    mo = re.search(r'(        CONSENSUS +)[A-Za-z\-\*]', string)
    if mo is None: raise ValueError('invalid staden contig dump file')
    shift = len(mo.group(1))

    # split lines and identify blocks (based on empty lines)
    lines = string.splitlines()
    empty_lines = [i for i, v in enumerate(lines) if v == '']
    empty_lines.insert(0, -1) # emulate a white line immediately before first line
    empty_lines.append(len(lines))
    blocks = [lines[empty_lines[i]+2 : empty_lines[i+1]] for i in range(len(empty_lines) - 1)]
        # +1 to read after each blank line
        # +2 to skip the first line of each block

    # initialize variables
    align = _eggwrapper.DataHolder(False)
    ns = 0
    currpos = 0
    IDs = []

    # process all blocks
    for block in blocks:
        for line in block:
            ID = line[:7].strip()
            name = line[8:shift].strip()
            sequence = line[shift:]
            sequence = sequence.translate(_staden_table)
            block_length = len(sequence)

            if ID not in IDs:
                ns += 1
                align.set_nsam(ns)
                align.set_name(ns-1, name)
                align.set_nsit_sample(ns-1, currpos)
                for i in range(currpos): align.set_sample(ns-1, i, special_MISSING)
                pos = ns - 1
                IDs.append(ID)
            else:
                pos = IDs.index(ID)

            align.set_nsit_sample(pos, currpos + len(sequence))
            for i, v in enumerate(sequence):
                align.set_sample(pos, currpos + i, special_DNA._obj.get_code(v))

        currpos += block_length

    # equalize
    for i in range(ns):
        n = align.get_nsit_sample(i)
        align.set_nsit_sample(i, currpos)
        for j in range(n, currpos): align.set_sample(i, j, special_MISSING)
    align.set_is_matrix(True)

    # undot
    idx = IDs.index('')
    for i in range(ns):
        if i != idx:
            for j in range(currpos):
                if align.get_sample(i, j) == special_DOT:
                    align.set_sample(i, j, align.get_sample(idx, j))

    # remove consensus
    if not keep_consensus:
        align.del_sample(idx)

    # return
    return _interface.Align._create_from_data_holder(align, alphabets.DNA)

def from_genalys(string):
    """
    Import Genalys data.
    Genalys was a proprietary program to process sequencing reads, perform
    assembly and detect polymorphism.
    Convert Genalys-formatted sequence alignment files to fasta. This
    function imports files generated through the option "Save SNPs" of
    Genalys 2.8.

    :param string: input data as a Genalys-formatted string.
    :return: An :class:`.Align` instance.
    """

    stream = StringIO(string)

    insertions = []
    flag = False

    for line in stream:
        line = line.split("\t")

        if len(line) > 1 and line[0] == "Polymorphism":
            flag = True

        if len(line) > 1 and line[0] == "IN" and flag:
            insertions.extend(line[1].split("/"))

    if len(insertions) > 0:
        tp = insertions[0].split("_")
        if len(tp) == 1:
            tp = tp[0].split(".")
            if len(tp) == 1:
                tp.append("1")
        finsertions = [tp]

    for i in insertions:
        i = i.split("_")
        if len(i) == 1:
            tp = tp[0].split(".")
            if len(tp) == 1:
                i.append("1")
        if i[0] != finsertions[-1][0]:
            finsertions.append(i)
        finsertions[-1][1] = i[1]
    
    if len(insertions) > 0:
        insertions = finsertions

    stream.close()
    stream = StringIO(string)

    names = []
    sequences = []
    maxlen = 0

    for line in stream:
        line = line.split("\t")
            
        if len(line) > 1:
            bidon = re.match(r".+\.ab1$", line[1])
            if bidon != None:
                names.append(line[1])
                sequences.append("")
                index = 6
                for i in range(10):
                    if line[i] == "F" or line[i] == "R":
                        index = i+1
                        break
                if line[index] != "":
                    beginning = int(line[index]) - 1
                    for i in insertions:
                        if int(i[0]) <= beginning:
                            beginning = beginning + int(i[1])
                        else:
                            break
                    for i in range(beginning):
                        sequences[-1]= sequences[-1] + "?"
                sequences[-1] = sequences[-1] + line[-1].rstrip("\n")
                if len(sequences[-1]) > maxlen:
                    maxlen = len(sequences[-1])

    data = _eggwrapper.DataHolder(True)
    data.set_nsam(len(sequences))
    data.set_nsit_all(maxlen)

    for i in range(len(sequences)):
        data.set_name(i, names[i])
        sequences[i] = sequences[i].replace("_", "-")
        for j, v in enumerate(sequences[i]): data.set_sample(i, j, alphabets.DNA._obj.get_code(v))
        for j in range(len(sequences[i]), maxlen): data.set_sample(i, j, MISSING)

    return _interface.Align._create_from_data_holder(data, alphabets.DNA)

def get_fgenesh(string, locus='locus'):
    """
    Import fgenesh data.

    :param fname: a string containing fgenesh ouput.
    :parma locus: locus name.
    :return: A list of gene and CDS features
        represented by dictionaries. Note that 5' partial features
        might not be in the appropriate frame and that it can be
        necessary to add a ``codon_start`` qualifier.
    """

    # supports for mac/windows files
    string = '\n'.join(string.splitlines())

    # gets the feature table
    try:
        data_sub = string.split('   G Str   Feature   Start        End    Score           ORF           Len\n')[1].split('Predicted protein(s):\n')[0]
    except IndexError:
        raise ValueError('invalid fgenesh format')
    data_sub = data_sub.split('\n\n')

    # edit
    del data_sub[-1]
    data_sub[0]= '\n'.join(data_sub[0].split('\n')[1:])

    # iteratively grabs the features
    features = {}
    for i in data_sub:
        pos = []
        start = 1
        rank = '---'
        strand = '---'
        for j in i.split('\n'):
            a = re.search(r' ?[0-9]+ ([+|-])      (TSS|PolA) +([0-9]+)', j)
            b = re.search(r' ?([0-9]+) ([+|-]) + ([0-9])+ CDS(o|f|i|l) +([0-9]+) - +([0-9]+) +[-\.0-9]+ + ([0-9]+)', j)
            if b:
                if b.group(3) == "1":
                    if int(b.group(5)) == int(b.group(7)): start= 1
                    elif int(b.group(5)) == (int(b.group(7))-1): start= 2
                    elif int(b.group(5)) == (int(b.group(7))-2): start= 3
                    else: raise ValueError('invalid fgenesh format')
                pos.append( [int(b.group(5))-1, int(b.group(6))-1 ] )
                rank = b.group(1)
                if b.group(2) == '+': strand = 'plus'
                else: strand = 'minus'

        features['cds'+rank] ={
            'gene': locus+'_'+rank,
            'strand': strand,
            'pos': pos,
            'type': 'CDS',
            'note': 'fgenesh prediction'
        }

        features['gene'+rank] ={
            'gene': locus+'_'+rank,
            'strand': strand,
            'pos': [[ pos[0][0], pos[-1][1] ]],
            'type': 'gene',
            'note': 'fgenesh prediction'
        }
        
    # gets the sequence section
    try:
        data_sub = string.split('   G Str   Feature   Start        End    Score           ORF           Len\n')[1].split('Predicted protein(s):\n')[1].split('>')
    except IndexError:
        raise ValueError('invalid fgenesh format')
    del data_sub[0]

    if ( (2*len(data_sub) != len(features)) and
           (len(data_sub) != len(features)) ) : raise ValueError('invalid fgenesh format')

    # returns the sequences as a table
    return list([features[i] for i in features])
