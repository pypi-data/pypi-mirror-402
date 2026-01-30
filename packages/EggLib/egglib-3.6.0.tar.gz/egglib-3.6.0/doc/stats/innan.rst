-----------------
Paralog diversity
-----------------

Following Innan (*Genetics* 2003 **163**:803-810), these statistics are
specifically designed to compute nucleotide diversity for each paralog
in a multigene family (:math:`\pi_w`), as well as between-paralog
divergence for all pairs (:math:`\pi_b`). They are availabled from the
function :func:`.stats.paralog_pi`.

For a given paralog, we have:

.. math::
    \pi_w = \sum_i^L \frac{2}{n_i (n_i-1)}k_i

with :math:`L` the number of sites, :math:`n_i` the number of
exploitable samples for this paralog at site :math:`i` and
:math:`k_i` the number of pairwise differences at this site.

And for a given pair of paralogs:

.. math::
    \pi_b = \sum_i^L \frac{d_i}{n_{ai} n_{bi}}

with :math:`d_i` the number of differences between the two paralogs and
:math:`n_{ai}` and :math:`n_{bi}` the respective numbers of exploitable
samples for the two paralogs at site :math:`i`.
