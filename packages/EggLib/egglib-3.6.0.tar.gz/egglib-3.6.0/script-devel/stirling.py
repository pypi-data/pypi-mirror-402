#
# This script generates a fragment of C++ code hardcoding logs of the
# Stirling numbers of the first kinds for all n values from 2 to MAXI
# and tests the explicit function to be used for larger n's.
#

import math, os

MAXI = 1000

cache = {}

def stirling(n, k):
    if k == 0: return 0L
    if n == k: return 1L
    if (n, k) not in cache: 
        cache[(n,k)] = stirling(n-1, k-1) - (n-1) * stirling(n-1, k)
    return cache[(n,k)]

def fstr(x):
    return "{:.50f}".format(x).rjust(55)


stirlings = []
for n in range(2, MAXI+1):
    print n
    for k in range(1, n+1):
        stirlings.append(math.log(abs(stirling(n, k))))
nstirlings = len(stirlings)



f = open(os.path.join(os.path.dirname(__file__), 'cpp', 'stirling.hpp'), 'w')
f.write("""/*
    Copyright 2013 St\xc3\xa9phane De Mita, Mathieu Siol

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

#ifndef EGGLIB_STIRLING_HPP
#define EGGLIB_STIRLING_HPP

namespace egglib {{

   /** \\brief Maximal n values for pre-computed Stirling numbers
    *
    * \ingroup diversity
    *
    * Header: <egglib-cpp/stirling.hpp>
    *
    */
    const unsigned int MAX_N_STIRLING = {0};

   /** \\brief Size of the Stirling numbers table
    *
    * \ingroup diversity
    *
    * Header: <egglib-cpp/stirling.hpp>
    *
    */
    const unsigned int NUM_STIRLING = {1};

   /** \\brief Array of log(|S(n,k)|) (Stirling numbers of the 1st kind)
    *
    * \ingroup diversity
    *
    * The values must be accessed using the stirling_table() function.
    *
    * Header: <egglib-cpp/stirling.hpp>
    *
    */
    const double STIRLING_TABLE[{1}] = {{
""".format(MAXI, nstirlings))

for i in range(0, len(stirlings), 10):
    f.write('       ' + ', '.join(map(fstr, stirlings[i:i+10])))
    if i + 10 < len(stirlings): f.write(',')
    f.write('\n')

f.write("""    };

   /** \\brief Get a pre-computed Stirling number of the first kind
    *
    * \ingroup diversity
    *
    * The n parameter must be <= MAX_N_STIRLING and k must be > 0 and
    * <= n.
    *
    * Header: <egglib-cpp/stirling.hpp>
    *
    */
    double stirling_table(unsigned int n, unsigned int k) {
        return STIRLING_TABLE[(n-1)*n/2+k-2];
    }
}

#endif
""")


f.close()
