/*
    Copyright 2017-2021 Thomas Coudoux, Stéphane De Mita, Mathieu Siol

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

#ifndef EGGLIB_VCFINDEX_HPP
#define EGGLIB_VCFINDEX_HPP

namespace egglib {
    class VcfParser;

    class VcfIndex {
        private:
            bool _has_data;
            unsigned int _num_contigs;
            unsigned int _res_contigs;
            unsigned int _num_variants;
            unsigned int _res_variants;
            unsigned int * _res_contig_name; // _res_contigs
            char ** _contig_name; // _res_contigs × res_contig_name[i]
            unsigned int * _contig_first_variant; // _res_variants
            unsigned int * _contig_last_variant; // _rst_variants
            unsigned int * _variant_contig; // _res_variants
            unsigned long * _variant_position; // _res_variants
            std::streampos * _variant_filepos; // _res_variants
            VcfParser * _vcf;

        public:
            VcfIndex(); ///< constructor
            ~VcfIndex(); ///< Destructor
            void load_data(VcfParser& ref, const char * fname); ///< load/reload index file
            void go_to(const char * contig, unsigned long pos); ///< move VcfParser to specified position
            std::streampos contig_first(const char * contig_name) const; ///< first line of a given chromosome (0 if not found)
            std::streampos contig_last(const char * contig_name) const; ///< last line of a given chromosome (0 if not found)
            std::streampos by_coordinates(const char * contig_name, unsigned long position) const; ///< find a given position (0 if not found)
            std::streampos by_index(unsigned int rank); ///< find index of a line by its rank
            unsigned long num() const; ///< number of indexes 
            bool has_data() const;
    };

    void make_vcf_index(VcfParser& VCF, const char * output); ///< creates an index file from a VCF file that has been just created
        /* format of index file
         * 
         * file_end (std::streampos)    | once
         * 1                            |˥
         * len_name (size_t)            | whenever new contig
         * name (char × len_name)       |˩
         * 2                            |˥
         * position (unsigned long)     | for all variants of current contig
         * filepos (std::streampos)     |˩
         * 0                            |˥
         * num_contigs (unsigned int)   | once
         * num_variants (unsigned int)  |˩
         * 
         */

}

#endif
