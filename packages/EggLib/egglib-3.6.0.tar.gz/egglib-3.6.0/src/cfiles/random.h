/*
    Copyright 2023 Stéphane De Mita

    This file is part of the EggLib library.

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
*/

#ifndef EGGLIB_CLIB_RANDOM_H
#define EGGLIB_CLIB_RANDOM_H

int egglib_random_init(); ///< initialise with default seed (client code is required to call this) return -1 on memory error, 0 otherwise

/// set the pseudorandom number generator seed
void egglib_random_set_seed(unsigned long s);

/// get the seed used to configure the pseudorandom number generator
unsigned long egglib_random_get_seed();

double egglib_random_uniform(); ///< uniform real (32-bit precision)
unsigned long egglib_random_integer_32bit(); ///< uniform integer
int egglib_random_bernoulli(double p); ///< draw in bernoulli
int egglib_random_brand(); ///< draw a boolean
double egglib_random_uniformcl(); ///< uniform on closed interval 
double egglib_random_uniformop(); ///< uniform on open interval
double egglib_random_uniform53(); ///< uniform with increased precision
double egglib_random_erand(double expect); ///< exponential distribution
unsigned int egglib_random_irand(unsigned int ncards); ///< integer with defined range
unsigned int egglib_random_prand(double mean); ///< poisson distribution
unsigned int egglib_random_grand(double param); ///< geometric distribution
double egglib_random_nrand(); ///< normal distribution
double egglib_random_nrandb(double m, double sd, double min, double max); ///< bounded normal
unsigned long egglib_random_binomrand(long n, double p); ///< binomial distribution

#endif
