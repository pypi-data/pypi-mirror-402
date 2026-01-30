-------------------
Misorientation rate
-------------------

Based on Baudry & Depaulis (*Genetics* 2003 **165**:1619-1622), the
class :class:`.stats.ProbaMisoriented` estimates the rate of invalid
orientation of polymorphisms using an outgroup, accounting for parallel
mutations in the branch leading to the outgroup. Only diallelic sites
(with on maximum one additional allele in the outgroup) are considered.

The proportion of transitions among substitutions among diallelic (in
the ingroup) polymorphism is denoted :math:`T_i`. The proportion of
transversions is given by :math:`T_v = 1 - T_i`.

The transition rate is then :math:`\alpha = \frac{T_i}{4}` and the
transversion rate is :math:`\beta = \frac{T_v}{8}`

The transition to transversion rate ratio is computed as:

.. math::
    \kappa = \frac{\alpha}{\beta}

And the probability of misorienting a site is:

.. math::
    P_M = \frac{\alpha^2 + 2 \beta^2}{2 \beta (2 \alpha + \beta)}P_D

where :math:`P_D` is given by proportion of polymorphic sites where the
outgroup has a third allele.
