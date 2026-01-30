"""
    Copyright 2018-2023 Stephane De Mita, Mathieu Siol

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

import sys
from io import StringIO
from .. import _interface

def to_ms(aln, outfile, positions=None, alphabet=None, as_codes=False,
    converter=None, spacer='auto',  header='//\n'):
    """
    Export data in the ``ms`` program format. The program is described in
    Hudson (2002 [*Bioinformatics* **18**: 337-338]).
    The format is as follows:

    * One header line with two slashes (can be extended/replaced).
    * One line with the number of sites
    * One line with the positions, only if the number of sites is larger
      than zero.
    * The matrix of genotypes (one line per sample), only if the number
      of sites is larger than zero.
    * One empty line.

    ``ms`` generates binary data (0/1). This function may export any
    integer values depending on the data contained in the input object.

    :param data: :class:`.Align` instance.

    :param outfile: where to write data. This argument can be (i) a file
        (or file-like) object open for writing, (ii) the name of a file
        (which will be created) as a string, or (iii) `None` (in which
        case the resulting string will be returned).

    :param positions: list of site positions, with length matching
        the alignment length. Positions are required to be in the [0,1]
        range but the order is not checked. By default (if the argument
        value is ``None``), sites are supposed to be evenly spread over
        the [0,1] interval.

    :param alphabet: an :class:`.Alphabet` instance to use
        instead of the alphabet attached to the input alignment. When
        using this argument, alleles are transformed using the alphabet
        provided as argument using a direct mapping of the input alignment
        alphabet to the provided alphabet.

    :param as_codes: use the internal alphabet codes for
        exporting. Useful if a non-int alphabet is used. Ignored if
        *converter* is used. Not allowed if *alphabet* is used.

    :param converter: a user-provided function generating the appropriate
        allelic value based on an input alphabet code. The simple inline
        example below shows how to convert any missing data to 0 and shift all
        valid alleles of one unit: ``converter=lambda x: 0 if x<0 else x+1``.

    :param spacer: insert a space between all genotypes
        (to separate each locus/site). By default, all genotypes are
        concatenated as in the standard ``ms`` format.
        In this case, it is required that all allelic
        values (or codes if *as_codes* is specified) are >=0 and <10. By
        default (``"auto"``), the spacer is automatically inserted if
        the alphabet defines alleles or codes outside the [0, 9] range,
        or if *converter* is specified.

    :param header: string to print instead of the two slashes line.
        Must contain the final new line.

    :return: A ``ms``-formatted string if *outfile* is ``None``,
        otherwise ``None``.
    """

    # error checking
    if not isinstance(aln, _interface.Align): raise TypeError('an Align instance is expected')
    ls = aln.ls
    if positions is not None:
        if len(positions) != ls: raise ValueError('invalid number of items in the positions list')
        if min(positions) < 0.0 or max(positions) > 1.0: raise ValueError('out of range item in the positions list')
    if alphabet is None: alph = aln.alphabet
    else:
        if as_codes:
            raise ValueError('options `as_codes` and `alphabet` are incompatible')
        alph = alphabet
    if alph.type not in ['int', 'range'] and converter is None and as_codes == False: raise ValueError('unsupported alphabet type: {0}'.format(alph.type))
    if converter is not None and as_codes:
        raise ValueError('options `as_codes` and `converter` are incompatible')

    # manage output file
    if outfile is None:
        out = StringIO()
    elif isinstance(outfile, str): out = open(outfile, 'w')
    else: out = outfile
    out.write(header)

    # shows number of sites and site
    out.write('segsites: {0}\n'.format(ls))
    if positions is None:
        if ls == 0: positions = []
        elif ls == 1: positions = [0.5]
        else: positions = [i / (ls-1) for i in range(ls)]
    if ls > 0:
        out.write('positions: {0}\n'.format(' '.join(['{0:.5f}'.format(i) for i in positions])))
    else:
        out.write('\n')

    # spacer
    if spacer == 'auto':
        if converter is not None: spacer = True
        else:
            if as_codes:
                if alph._obj.num_missing() > 0 or alph._obj.num_exploitable() > 10: spacer = True
                else: spacer = False
            else:
                if alph.type == 'range':
                    if alph._obj.min_value() < 0 or alph._obj.max_value() > 9: spacer = True
                    else: spacer = False
                else:
                    exp, mis = alph.get_alleles()
                    alls = exp + mis
                    if min(alls) < 0 or max(alls) > 9: spacer = True
                    else: spacer = False

    # export data
    if converter is not None: f = converter
    elif as_codes: f = lambda x: x
    else: f = alph.get_value
    for i in range(aln.ns):
        values = tuple(map(f, [aln._obj.get_sample(i, j) for j in range(ls)]))
        if not spacer and (min(values) < 0 or max(values) > 9): raise ValueError('not printable allele for ms format (you should insert a spacer)')
        if spacer: out.write(' '.join(map(str, values)) + '\n')
        else: out.write(''.join(map(str, values)) + '\n')

    # close file or return string as necessary
    out.write('\n')
    if isinstance(outfile, str): out.close()
    elif outfile is None: return out.getvalue()
