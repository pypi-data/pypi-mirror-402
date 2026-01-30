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

from .. import _interface

def concat(*aligns, **kwargs):
    """ egglib.tools.concat(align1, align2, ..., spacer=0, ch='?', group_check=True, no_missing=False, ignore_names=False, dest=None)

    Concatenates sequence alignments. A unique
    :class:`.Align` is generated. All different sequences from all passed
    alignments are represented in the final alignment. Sequences whose
    name match are concatenated. In case several sequences
    have the same name in a given segment, the first one is considered
    and others are discarded. In case a sequence is missing for a
    particular segment, a stretch of non-varying characters is inserted
    to replace the unknown sequence.

    All options (excluding the alignements to be concatenated) must be
    specified as keyword arguments, otherwise they will be treated as
    part of the list of alignments.

    :param align1:
    :param align2: two or more :class:`!Align` instances (their
        order is used for concatenation). It is not allowed to specify
        them using the keyword syntax. All instances must be configured to
        use the same alphabet.

    :param spacer: length of unsequenced stretches (represented by
        non-varying characters) between concatenated alignments. If
        *spacer* is a positive integer, the length of all stretches will
        be identical. If *spacer* is an iterable containing integers,
        each specifying the interval between two consecutive alignments
        (if there are ``n`` alignments, *spacer* must be of
        length ``n-1``).

    :param ch: character to used for conserved stretches and for missing
        segments. This character must be valid for the alphabet considered.

    :param group_check: if ``True``, an exception will be raised in case
        of a mismatch between group labels of different sequence
        segments bearing the same name. Otherwise, the group labels of the
        first segment found will be used as group labels of the final
        sequence.

    :param no_missing: if ``True``, an exception will be raised in case
        the list of samples differs between :class:`!Align` instances.
        Then, the number of samples must always be the same and all
        samples must always be present (although it is possible that
        they consist in missing data only). Ignored if *ignore_names*
        is ``True``.

    :param ignore_names: don't consider sample names and concatenate
        sequences based on they order in the instance. If used, the value of
        the option *no_missing* is ignored and the number of samples is
        required to be constant over alignments.

    :param dest: an optional :class:`!Align` instance to recycle and 
        to use to store the
        result. This instance is automatically reset, ignoring all
        data previously loaded. If this argument is not ``None``, the
        function returns nothing and the passed instance is modified.
        Allows to recycle the same object in intensive applications.

    :return: If *dest* is ``None``, a new :class:`!Align` instance.
        If *dest* is ``None``, this function returns ``None``.
    """

    # import default value of options
    spacer = kwargs.get('spacer', 0)
    ch = kwargs.get('ch', '?')
    group_check = kwargs.get('group_check', True)
    no_missing = kwargs.get('no_missing', False)
    ignore_names = kwargs.get('ignore_names', False)
    dest = kwargs.get('dest', None)
    for key in kwargs:
        if key not in ['spacer', 'ch', 'group_check', 'no_missing',
                       'ignore_names', 'dest']:
            raise ValueError('invalid argument: `{0}`'.format(key))

    # process arguments
    if len(aligns) == 0:
        raise ValueError('there must be at least one alignment')
    for aln in aligns:
        if not isinstance(aln, _interface.Align):
            raise TypeError('expect an Align instance')
    for aln in aligns[1:]:
        if aln._alphabet._obj != aligns[0]._alphabet._obj:
            raise ValueError('all alignments must have the same alphabet')
    nloc = len(aligns)
    if isinstance(spacer, int):
        if spacer < 0: raise ValueError('`spacer` argument must not be negative')
        spacer = [spacer] * (nloc -1) # supports nloc==0
    elif min(spacer) < 0: raise ValueError('`spacer` argument must not be negative')
    elif len(spacer) == 0 and nloc == 0:
        pass
    elif len(spacer) != nloc-1:
        raise ValueError('`spacer` does not have the right number of items')
    spacer.append(0) # convenience to avoid having an "if" in the main loop
    if len(ch) != 1:
        raise ValueError('`ch` must be a single character')

    # get the total length
    ls = sum([aln.ls for aln in aligns]) + sum(spacer)

    # get the list of samples
    if not ignore_names:

        # get the list of names of each alignment
        names = list(map(_interface.Align.names, aligns))

        # get the total list of names (as a dict without values)
        samples = dict.fromkeys(set().union(*names))

        # number of samples
        ns = len(samples)

        # check that list is constant if requested
        if no_missing:
            for aln in aligns:
                if aln.ns != ns:
                    raise ValueError('inconsistent list of samples')

        # get the index of each sample
        for name in samples:
            samples[name] = []
            for aln, lnames in zip(aligns, names):
                if name in lnames: samples[name].append(lnames.index(name))
                else: samples[name].append(None)

    else:
        ns = set([aln.ns for aln in aligns])
        if len(ns) != 1:
            raise ValueError('inconsistent list of samples')
        ns = ns.pop()
        samples = dict([(i, [i]*nloc) for i in range(ns)])

    # create or reset destination
    if dest is None:
        conc = _interface.Align(nsam=ns, nsit=0, alphabet=aligns[0]._alphabet)
        if not ignore_names:
            for i, v in enumerate(samples): conc.set_name(i, v)
    else:
        dest.reset()
        dest._alphabet = aligns[0]._alphabet
        conc = dest
        if ignore_names:
            for v in samples: conc.add_sample('', [])
        else:
            for v in samples: conc.add_sample(v, [])

    conc._obj.set_nsit_all(ls) # this doesn't initialize new values

    # set names
    names = sorted(samples)

    if not ignore_names:
        for i, name in enumerate(names): conc.set_name(i, name)

    # process groups
    group_mapping = {}
    for name in samples:
        groups = [aligns[i].get_sample(j).labels for (i,j) in enumerate(samples[name]) if j != None]
        if len(groups) > 0:
            if group_check:
                for i in range(len(groups)-1):
                    if len(groups[0]) != len(groups[i+1]):
                        raise ValueError('inconsistent labels')
                    for a, b in zip(groups[0], groups[i+1]):
                        if a != b:
                            raise ValueError('inconsistent labels')
            group_mapping[name] = groups[0]
        else:
            group_mapping[name] = []

    for idx, name in enumerate(names):
        conc._obj.set_nlabels(idx, len(group_mapping[name]))
        for i, g in enumerate(group_mapping[name]):
            conc._obj.set_label(idx, i, g)

    # process the sequences themselves
    curr = 0

    for align_idx, (align, spc) in enumerate(zip(aligns, spacer)):

        # add sequence of this align + spacer
        ls = align.ls

        for main_idx, name in enumerate(names):
            sample_idx = samples[name][align_idx]
            if sample_idx != None:
                conc.get_sample(main_idx).sequence[curr:curr+ls] = align.get_sample(sample_idx).sequence
                conc.get_sample(main_idx).sequence[curr+ls:curr+ls+spc] = ch * spc
            else:
                conc.get_sample(main_idx).sequence[curr:curr+ls+spc] = ch * (ls+spc)

        curr += ls + spc

    # return if needed
    if dest is None: return conc
