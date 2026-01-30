/*
    Copyright 2012-2025 Stéphane De Mita, Mathieu Siol

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

#ifndef EGGLIB_SITE_HOLDER_HPP
#define EGGLIB_SITE_HOLDER_HPP

namespace egglib {

    class DataHolder;
    class VcfParser;
    class StructureHolder;
    class Alphabet;

   /** \brief Holds data for a site for diversity analysis
    *
    * Either load data from an alignment or data from a VCF, or
    * individuals manually. Before loading individuals manually, it is
    * required to pre-set the number such as the indexes will exist. Note: the
    * instance is not reset unless you ask it. Data will add up.
    *
    * \ingroup diversity
    *
    */
    class SiteHolder {

        private:
            SiteHolder(SiteHolder& src) {}
            SiteHolder& operator=(SiteHolder& src) { return * this; }

        protected:
            unsigned int _ns;
            unsigned int _ns_c;
            int * _data;
            unsigned int _missing;
            double _position;
            char * _chrom;
            unsigned int _chrom_sz;

        public:

            SiteHolder(); ///< Constructor
            virtual ~SiteHolder(); ///< Destructor
            void reset(); ///< Reset all to defaults
            double get_position() const; ///< get site's position
            void set_position(double); ///< set site's position
            void add(unsigned int num); ///< Add individuals
            void set_sample(unsigned int sam, int allele); ///< Set an allele
            unsigned int get_ns() const; ///< Get number of samples
            int get_sample(unsigned int sam) const; ///< Get a sample
            unsigned int get_missing() const; ///< Get number of missing alleles
            void del_sample(unsigned int); ///< delete a sample
            void append(int); ///< add an allele to the end
            const char * get_chrom() const; ///< get chrom
            void set_chrom(const char *); ///< set chrom

           /** \brief Process an alignment.
            *
            * Does not reset instance!
            *
            * \param data an alignment.
            * \param idx index of the site to process.
            * \param struc an optional structure object
            *
            * \return Number of non-missing ingroup samples processed by this call.
            *
            */
            unsigned int process_align(const DataHolder& data, unsigned int idx,
                    StructureHolder * struc=NULL);

           /** \brief Import allelic data and compute frequencies from VCF data
            *
            * Beware: this method does not reset the instance.
            *
            * \param data a VcfParser reference containing data and
            *        having the GT format field filled.
            * \param start index of the first sample to consider.
            * \param stop index of the last sample to consider.
            *
            * \return Number of valid data (excluding missing data)
            *
            */
            unsigned int process_vcf(VcfParser& data,
                             unsigned int start, unsigned int stop);
    };
}

#endif
