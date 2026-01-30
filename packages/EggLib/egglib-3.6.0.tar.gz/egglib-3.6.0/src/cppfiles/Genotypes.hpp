/*
    Copyright 2018-2025 Stéphane De Mita

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

#ifndef EGGLIB_GENOTYPES_HPP
#define EGGLIB_GENOTYPES_HPP

#include "egglib.hpp"
#include "SiteHolder.hpp"

namespace egglib {

   /** \brief Class processing a SiteHolder and analyzing genotypes */
    class Genotypes {
        private:
            Genotypes(const Genotypes& src) {}
            Genotypes& operator=(const Genotypes& src) { return *this; }
            SiteHolder _site;
            unsigned int _n_genot;
            unsigned int _pl;
            bool * _heter;              // size: _genot_c
            int ** _genot;              // size: _genot_c x _pl_c[i]
            int * _array;               // size: _array_c
            bool * _flags;              // size: _array_c
            unsigned int _array_c;
            unsigned int _genot_c;
            unsigned int * _pl_c;       // size: _genot_c
            int _find_genotype();

        public:
            Genotypes(); ///< \brief Empty instance
            ~Genotypes(); ///< \brief Destructor
            void process(const SiteHolder&, StructureHolder&, bool phased); ///< \brief Analyse a site
            unsigned int ploidy() const; ///< \brief Get ploidy
            const SiteHolder& site() const; ///< \brief Get site (alleles are genotype indexes)
            bool heter(unsigned int) const; ///< \brief Tell if a given genotype is heterozygote
            const int * const genot(unsigned int) const; ///< \brief Get pointer to a genotype
            unsigned int num_genotypes() const; ///< \brief Number of genotypes
    };
}

#endif
