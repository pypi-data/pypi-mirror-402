/*
    Copyright 2008-2021 Stéphane De Mita, Mathieu Siol

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

#ifndef EGGLIB_RD_HPP
#define EGGLIB_RD_HPP

namespace egglib {

    class SiteHolder;
    class StructureHolder;

   /** \brief Compute the bar{r_d} (or rD) statistic
    *
    * \ingroup diversity
    *
    * Rd instances cannot be copied. The procedure is:
    * * Call configure() and pass a structure giving the individual
    *   structure of the ingroup (the rest is ignored).
    * * Load as many sites as needed. They are analysed on the fly. The
    *   number of samples is expected to match (as well as the order of
    *   individuals and the phase if relevant). If there is a mismatch
    *   in number of samples, the Rd value will be UNDEF.
    * * Compute the Rd value (resets the instance).
    *
    */
    class Rd {

        private:
            Rd(const Rd& src) {}
            Rd& operator=(const Rd& src) {return *this;}
            unsigned int _num_loci;
            unsigned int _res_loci;
            unsigned int _num_indiv;
            unsigned int _npt; // maximum number of pairs of indivs
            unsigned int _res_pairs;
            double _Ve;
            double * _var; // variance per locus
            unsigned int * _diff; // size: _res_pairs
            unsigned int * _diff_n; // size: _res_pairs
            bool * _flags; // size: _res_ploidy
            bool _invalid; // true if ns/pl mismatch
            bool _no_data; // true until data is loaded (even if the site is not retained)
            const StructureHolder* _struct;
            unsigned int _ploidy;
            unsigned int _res_ploidy;
            unsigned int _cmp_diff(const SiteHolder&, unsigned int i, unsigned int j);
            void _configure_helper();

        public:
            Rd(); ///< Constructor
            ~Rd(); ///< Destructor
            void configure(const StructureHolder&); ///< Load individual structure
            void reset(); ///< Reset to initial state (equivalent to configure without stats)
            void reset_stats(); ///< Reset statistics
            unsigned int num_loci() const; ///< Get number of processed loci (some loci may be skipped)
            unsigned int ploidy() const; ///< Get ploidy as provided to configure()
            unsigned int num_indiv() const; ///< Get number of individuals as provided to configure()
            void load(const SiteHolder&); ///< Load a site
            double compute(); ///< Compute rD (UNDEF if not computable)
    };
}

#endif
