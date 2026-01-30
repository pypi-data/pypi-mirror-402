/*
    Copyright 2016-2021 Thomas Coudoux, Stéphane De Mita, Mathieu Siol

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

#ifndef EGGLIB_BED_HPP
#define EGGLIB_BED_HPP
#include <fstream>

namespace egglib {

    class BedParser {
        private:
            unsigned int _num;
            unsigned int _res;
            unsigned int * _res_chrom;
            char ** _chrom;
            unsigned long * _start;
            unsigned long * _end;
            char * _fname;
            unsigned int _res_fname;
            std::ifstream _stream;
            unsigned int _currline;
            void _open_file(const char * filename); ///< open file
            void _next_line(); ///< go to end of line
            void _add_one(); ///< allocate a new record

        public:
            BedParser(); ///< constructor
            ~BedParser(); ///< destructor
            void get_bed_file(const char * filename); ///< load data (increment if data already present)
            unsigned int n_bed_data() const; ///< number of entries
            const char * get_chrom(unsigned int) const; ///< get a chromosome
            unsigned int get_start(unsigned int) const; ///< get a start bound
            unsigned int get_end(unsigned int) const; ///< get an end bound
            void append(const char *, unsigned long, unsigned long); ///< add an item at the end
    };
}

#endif
