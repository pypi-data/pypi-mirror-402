.. _random:

-----------------------------
Pseudorandom number generator
-----------------------------

This module implements the Mersenne Twister algorithm for
pseudo-random number generation. It is based on now-defunct
projects by Makoto Matsumoto and Takuji Nishimura
and Jasper Bedaux for the core generator, and on Egglib version 2 for
conversion to other laws than uniform.
All non-uniform distribution laws generators are based either on the
:func:`.random.integer_32bit` or the standard (half-open, 32 bit)
:func:`.random.uniform` methods.

Note that the pseudo-random number generator is seeded, by
default, using the system clock and that it will yield the
exact same sequence of random numbers (regardless of the
distribution law used) if the seed is identical. This means
that different processes started have the same time will
be based on the same sequence of random number. It is possible
to get and set the seed at any time (see the corresponding methods
below).

The content of the module is listed below:

.. autosummary::
    egglib.random.get_seed
    egglib.random.set_seed
    egglib.random.uniform
    egglib.random.uniform_53bit
    egglib.random.uniform_closed
    egglib.random.uniform_open
    egglib.random.integer
    egglib.random.integer_32bit
    egglib.random.boolean
    egglib.random.bernoulli
    egglib.random.binomial
    egglib.random.exponential
    egglib.random.geometric
    egglib.random.normal
    egglib.random.normal_bounded
    egglib.random.poisson

.. autofunction:: egglib.random.get_seed
.. autofunction:: egglib.random.set_seed
.. autofunction:: egglib.random.uniform
.. autofunction:: egglib.random.uniform_53bit
.. autofunction:: egglib.random.uniform_closed
.. autofunction:: egglib.random.uniform_open
.. autofunction:: egglib.random.integer
.. autofunction:: egglib.random.integer_32bit
.. autofunction:: egglib.random.boolean
.. autofunction:: egglib.random.bernoulli
.. autofunction:: egglib.random.binomial
.. autofunction:: egglib.random.exponential
.. autofunction:: egglib.random.geometric
.. autofunction:: egglib.random.normal
.. autofunction:: egglib.random.normal_bounded
.. autofunction:: egglib.random.poisson
