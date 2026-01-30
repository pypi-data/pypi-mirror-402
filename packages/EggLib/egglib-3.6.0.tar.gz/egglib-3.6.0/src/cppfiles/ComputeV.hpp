/*
    Copyright 2016-2021 Stéphane De Mita

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

#ifndef EGGLIB_COMPUTEV_HPP
#define EGGLIB_COMPUTEV_HPP

#include "Alphabet.hpp"

namespace egglib {

    class FreqSet;
    class FreqHolder;

   /** \brief Compute allele size variance
    *
    * \ingroup diversity
    *
    */
    class ComputeV {

        private:
            unsigned int _num_sites;
            unsigned int _num_sites_m;
            unsigned int _num_sites_rst;
            double _acc_V;
            double _acc_Ar;
            double _acc_M;
            double _cur_V;
            double _cur_Ar;
            double _cur_M;
            double _cur_Rst;
            double _Sw;
            double _Sbar;
            double _maf;

        public:
            ComputeV(); ///< Constructor
            ~ComputeV(); ///< Destructor
            void reset(); ///< Reset
            bool compute(const FreqHolder&, AbstractTemplateAlphabet<int>&); ///< Compute V, Ar, and M (false if V and Ar not computable)
            double curr_V() const; ///< Get V for last site (UNDEF if no computed values)
            double curr_Ar() const; ///< Get Ar for last site (UNDEF if no computed values)
            double curr_M() const; ///< Get M for last site (UNDEF if no computed values)
            double curr_Rst() const; ///< Get Rst for last site (UNDEF if no computed values)
            double average_V() const; ///< Get average V (UNDEF if no computed values)
            double average_Ar() const; ///< Get average Ar (UNDEF if no computed values)
            double average_M() const; ///< Get average M (UNDEF if no computed values)
            double average_Rst() const; ///< Get average Rst (UNDEF if no computed values)
            unsigned int num_sites() const; ///< Number of sites with computed V and Ar
            unsigned int num_sites_m() const; ///< Number of sites with computed M
            unsigned int num_sites_rst() const; ///< Number of sites with computed Rst
            void set_maf(double); ///< Set the minimum minority allele frequency
    };
}

#endif
