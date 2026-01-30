-------------------------------
Extended haplotype homozygosity
-------------------------------

Extended haplotype homozygosity (EHH) is a method designed to detect
unusually long haplotypes resulting from recent selective sweeps. A
dedicated class, :class:`.stats.EHH`, is provided to compute those
statistics.

The statistics listed in the table below are available as methods or
attributes of this class. The documentation provides more information
regarding the usage.

.. table::
    :widths: 15 40 10 10

    +--------------------------------------+---------------------------------------------+------------+-----------+
    | Accessor                             | Description                                 | Equation   | Reference |
    +======================================+=============================================+============+===========+
    | :meth:`~.stats.EHH.get_EHH`          | EHH                                         | :eq:`EHH`  | 1         |
    +--------------------------------------+---------------------------------------------+------------+-----------+
    | :meth:`~.stats.EHH.get_EHHc`         | Complementary EHH                           | :eq:`EHH`  | 1         |
    +--------------------------------------+---------------------------------------------+------------+-----------+
    | :meth:`~.stats.EHH.get_rEHH`         | Relative EHH                                | :eq:`rEHH` | 1         |
    +--------------------------------------+---------------------------------------------+------------+-----------+
    | :meth:`~.stats.EHH.get_iHH`          | Integrated EHH                              | :eq:`iHH`  | 2         |
    +--------------------------------------+---------------------------------------------+------------+-----------+
    | :meth:`~.stats.EHH.get_iHHc`         | Integrated EHHc                             | :eq:`iHH`  | 2         |
    +--------------------------------------+---------------------------------------------+------------+-----------+
    | :meth:`~.stats.EHH.get_iHS`          | Integrated haplotype score (unstandardized) | :eq:`iHS`  | 2         |
    +--------------------------------------+---------------------------------------------+------------+-----------+
    | :meth:`~.stats.EHH.get_EHHS`         | Site-level EHH                              | :eq:`EHHS` | 3         |
    +--------------------------------------+---------------------------------------------+------------+-----------+
    | :meth:`~.stats.EHH.get_iES`          | Integrated EHHS                             | :eq:`iES`  | 3         |
    +--------------------------------------+---------------------------------------------+------------+-----------+
    | :meth:`~.stats.EHH.get_EHHG`         | EHHS for genotypic data                     | :eq:`EHHG` | 3         |
    +--------------------------------------+---------------------------------------------+------------+-----------+
    | :meth:`~.stats.EHH.get_iEG`          | Integrated EHHG                             | :eq:`iEG`  | 3         |
    +--------------------------------------+---------------------------------------------+------------+-----------+

**References**

#. Sabeti *et al.* (*Nature* 2002 **419**:832-837).
#. Voight *et al.* (*PLoS Biol.* 2006 **4**:e772).
#. Tang *et al.* (*PLoS Biol.* 2007 **5**:e171).

Raw EHH statistics
------------------

If haplotype :math:`i` is present in :math:`n_{i, 0}` copies at the core
site, and if this haplotype has been split in :math:`k` haplotypes
at distant site :math:`s`, each present in :math:`n_{j, 0}` copies, 
the EHH for haplotype :math:`i` at distant site :math:`s` is given by:

.. math::
    EHH_{i,s} = \frac{\sum_j n_{j,s} (n_{j,s} - 1)} {n_{i,0} (n_{i,0} - 1)}
    :label: EHH

:math:`EHHc_{i,s}` is computed like :math:`EHH_{i,s}` but considering
the complement of haplotype :math:`i` instead of haplotype :math:`i`
itself.

:math:`rEHH_{i,s}` is computed as:

.. math::
    rEHH_{i,s} = \frac{EHH_{i,s}}{EHHc_{i,s}}
    :label: rEHH

Integrated EHH statistics
-------------------------

Denoting the core site as :math:`s=0` and the first site for which
:math:`EHH_{i,s}` is below the threshold :math:`EHH_t` as :math:`s=s^*`,
and :math:`d_s` the distance of site :math:`s` to the core,
the integrated statistic :math:`iHH_{i,s^*}` is computed as:

.. math::
    iHH_{i,s*} = \sum_{s=0}^{s^*-1} \left[ (d_s - d_{s-1}) \frac{(EHH_{i,s-1}-EHH_t) + (EHH_{i,s}-EHH_t)}{2} \right]
        + (d_{s^*} - d_{s^*-1}) \frac{(EHH_{i,s^*-1}-EHH_t)^2}{2(EHH_{i,s^*-1}-EHH_{i,s^*})}
    :label: iHH

As long as no site has an EHH value below the threshold, the statistic
is computed without the last term.

The complementary :math:`iHHc` is computed using :math:`EHHc` instead of
:math:`EHH`.

The integrated haplotype score iHS is not standardized:

.. math::
    iHS_{i,s} = \log \frac{iHHc}{iHH}
    :label: iHS

Site-level EHH statistics
-------------------------

If :math:`n` is the total number of available samples at the core sites,
the whole-site :math:`EHH` is computed as:

.. math::
    EHHS_s = 1 - \frac{n}{n-1} \left( 1 -\frac{\sum_i n_{i,s}^2}{n^2} \right)
    :label: EHHS

The integrated :math:`EHHS` (:math:`iES`) is computed similarly as
:math:`iHH` based on a given threshold :math:`EHHS_t` and :math:`s^*`
being the first site for which :math:`EHHS` is below this threshold
(see above):

.. math::
    iES_{s^*} = \sum_{s=0}^{s^*-1} \left[ (d_s - d_{s-1}) \frac{EHHS_s + EHHS_{s-1} - 2 EHHS_t}{2} \right]
        + (d_{s^*} - d_{s^*-1}) \frac{(EHHS_{s^*-1}-EHHS_t)^2}{2(EHHS_{s^*-1}-EHHS_{s^*})}
    :label: iES

EHHS for genotypic data
-----------------------

Defining :math:`H_s` as the proportion of heterozygote individuals at 
site :math:`s`, and :math:`H_{0s}` the proportion of individuals 
heterozygote as the core site among those which are non-missing at site 
:math:`s`, :math:`EHHG` is computed as:

.. math::
    EHHG_s = \frac{H_s}{H_{0s}}
    :label: EHHG

The integrated :math:`EHHG`, :math:`iEG`, is computed just as :math:`iHH`
and :math:`iES`, based on a given threshold :math:`EHHG_t`:

.. math::
    iEG_s = \sum_{s=0}^{s^*-1} \left[ (d_s - d_{s-1}) \frac{EHHG_s + EHHG_{s-1} - 2 EHHG_t}{2} \right]
        + (d_{s^*} - d_{s^*-1}) \frac{(EHHG_{s^*-1}-EHHG_t)^2}{2(EHHG_{s^*-1}-EHHG_{s^*})}
    :label: iEG

