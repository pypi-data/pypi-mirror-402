"""
    Copyright 2008-2026 Stephane De Mita, Mathieu Siol

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

from . import tools
from . import random
from . import stats
from . import io
from . import coalesce
from . import wrappers
from ._interface import Align, Container, SampleView, SequenceView, LabelView, encode, Structure, struct_from_labels, struct_from_dict, struct_from_samplesizes, struct_from_iterable, struct_from_mapping
from ._site import Site, site_from_align, site_from_list, site_from_vcf
from ._tree import Tree, Node
from .alphabets import Alphabet
from ._freq import Freq, freq_from_site, freq_from_list, freq_from_vcf
from importlib.metadata import version
__version__ = version('egglib')
