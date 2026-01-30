/*
    Copyright 2013-2021 Stéphane De Mita, Mathieu Siol

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

#ifndef EGGLIB_GENETICCODE_HPP
#define EGGLIB_GENETICCODE_HPP

#include "Alphabet.hpp"

namespace egglib {

    class SiteHolder;

   /** \brief Hold genetic code tables
    *
    * \ingroup core
    *
    * Handle genetic codes. All genetic codes defined by the National
    * Center for Biotechnology Information are supported.
    *
    * Header: <egglib-cpp/GeneticCode.hpp>
    *
    */
    class GeneticCode {

        public:
            GeneticCode(unsigned int index=1); ///< \brief Constructor
            unsigned int get_code() const; ///< \brief Get genetic code
            void set_code(unsigned int index); ///< \brief Set genetic code
            int translate(int codon); ///< \brief Translate a codon
            bool start(int codon) const; ///< \brief Tell if codon is start (or alternative start)
            bool stop(int codon) const; ///< \brief Tell if codon is stop
            bool is_stop_unsmart(int codon) const; ///< \brief Tell if codon is stop (only >=0 values)
            double NSsites(int codon, bool ignorestop = true) const; ///< \brief Number (0-3) of non-synonymous sites (if ignorestop: changes to stop codons are ignored and stop codons yield 0)
            double Ssites(int codon, bool ignorestop = true) const; ///< \brief Like NSsites equivalent
            const char * name() const; ///< \brief Genetic code name

           /** \brief Give the number of non-synonymous sites of a codon
            * site.
            *
            * The number is in the range 0-3 (3 is all changes at all of
            * the three positions would lead to a non-synonymous
            * change). This is the same as NSistes(unsigned int, bool),
            * but averaged over all samples based on provided Site
            * instance.
            *
            * \param site codon site.
            * \param num_samples variable used to provide the number of
            * samples analyzed by the method (that is, number of samples
            * minus number of samples containing at least one missing
            * data). The original value of the variable is ignored and
            * is modified by the instance. If 0, the return value should
            * be ignored.
            * \param ignorestop if true, potential changes to stop codons
            * are excluded and all stop codons are treated as missing
            * data; if false, changes to stop codons are considered to
            * be non-synonymous.
            *
            */
            double NSsites(const SiteHolder& site, unsigned int& num_samples, bool ignorestop = true) const;
            double Ssites(const SiteHolder& site, unsigned int& num_samples, bool ignorestop = true) const; ///< \brief Like NNsites equivalent

            static inline unsigned int ndiff(int codon1, int codon2) {
                return diff1(codon1, codon2) + diff2(codon1, codon2) + diff3(codon1, codon2);
            } ///< \brief Number of differences between two codons

            static inline bool diff1(int codon1, int codon2) {
                return get_static_CodonAlphabet().get_value(codon1)[0] != get_static_CodonAlphabet().get_value(codon2)[0];
            } ///< \brief Check first base of two codons

            static inline bool diff2(int codon1, int codon2) {
                return get_static_CodonAlphabet().get_value(codon1)[1] != get_static_CodonAlphabet().get_value(codon2)[1];
            } ///< \brief Check second base of two codons

            static inline bool diff3(unsigned int codon1, unsigned int codon2) {
                return get_static_CodonAlphabet().get_value(codon1)[2] != get_static_CodonAlphabet().get_value(codon2)[2];
            } ///< \brief Check third base of two codons

            static unsigned int num_codes(); ///< \brief Number of available codes

        private:

            GeneticCode(GeneticCode& src) {}
            GeneticCode& operator=(GeneticCode& src) { return *this; }

            static const int _aa[];
            static const char _start[];
            static const char _stop[];
            static const double _NS1[]; // stop codons considered
            static const double _NS2[]; // ignorestop
            static const double _S1[];
            static const double _S2[];
            static const char * _names[];
            static const unsigned int _codes[];
            unsigned int _code;
            unsigned int _index;
            int _shift;
    };
}

#endif
