"""
    Copyright 2020-2021 Stephane De Mita, Mathieu Siol

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

from .. import _interface

def to_codons(src, frame=None):
    """
    Converts a DNA object to the codon alphabet.
    In the output alignment, there is one site per codon. The number of
    provided sites must be a multiple of 3.

    :param aln: input alignment as an :class:`.Align`  or :class:`.Container`
        instance. The alphabet must be :py:obj:`.alphabets.DNA`.

    :param frame: a :class:`.tools.ReadingFrame` instance providing the
        exon positions in the correct frame. By default, a
        non-segmented frame covering all sequences is assumed (in
        case the provided alignment is the coding region; in such case
        the length must be a multiple of 3).

    :return: A new instance of type matching the input instance. The
        alphabet will be :py:obj:`.alphabets.codons`.
    """
    if isinstance(src, _interface.Container):
        if frame is not None: raise ValueError('cannot pass a frame with a Container')
        dst = _interface.Container.create(src)
        dst.to_codons()
        return dst
    elif isinstance(src, _interface.Align):
        dst = _interface.Align.create(src)
        dst.to_codons(frame)
        return dst
    else:
        raise TypeError('expect an Align or Container')

def to_bases(src):
    """
    Converts a codon object to the DNA alphabet.
    In the output object, there are three sites per codon.

    :param aln: input object as an :class:`.Align` or :class:`.Container`
        instance. The alphabet must be :py:obj:`.alphabets.codons`.

    :return: A new instance of type matching the input instance. The
        alphabet will be :py:obj:`.alphabets.DNA`.
    """
    dst = type(src).create(src)
    dst.to_bases()
    return dst
