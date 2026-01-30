"""
    Copyright 2008-2021 Stephane De Mita, Mathieu Siol

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

from ._concat import concat
from ._code_tools import Translator, translate, orf_iter, \
                        longest_orf, backalign, BackalignError, \
                        trailing_stops, iter_stops, has_stop
from ._reading_frame import ReadingFrame
from ._to_codons import to_codons, to_bases
from ._seq_manip import rc, compare, regex, motif_iter, ungap, ungap_all
