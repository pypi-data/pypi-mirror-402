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


#include "BED.hpp"
#include "egglib.hpp"
#include <cstdlib>
#include <cstdio>
#include <cstring>

//const char MAXCHAR = std::numeric_limits<char>::max();

namespace egglib {

    BedParser::BedParser() {
        _num = 0;
        _res = 0;
        _res_chrom = NULL;
        _chrom = NULL;
        _start = NULL;
        _end = NULL;
        _fname = NULL;
        _res_fname = 0;
    }

    BedParser::~BedParser() {
        if (_res_chrom) free(_res_chrom);
        if (_chrom) {
            for (unsigned int i=0; i<_res; i++) {
                if (_chrom[i]) free(_chrom[i]);
            }
            free(_chrom);
        }
        if (_start) free(_start);
        if (_end) free(_end);
        if (_fname) free(_fname);
    }

    void BedParser::get_bed_file(const char * filename) {
        _open_file(filename);
        _stream.seekg(0, _stream.end);
        std::streampos eof = _stream.tellg();
        _stream.seekg(0, _stream.beg);
        _currline = 0;
        while (_stream.tellg() != eof) {
            // assume that there will be a new line
            _add_one();

            // get chromosome name
            unsigned int i=0;
            char c;
            while (true) {
                c = _stream.get();
                if (!_stream.good()) throw EggFormatError(filename, _currline+1, "BED", "reading error");
                if (c == ' ' || c == '\t' || c == '\n') break;
                if (c == '\r') {
                    if (_stream.get() != '\n') throw EggFormatError(_fname, _currline+1, "BED", "\r not followed by \n");
                    break;
                }
                i++;
                if (i > _res_chrom[_num-1]) {
                    _res_chrom[_num-1] += 10;
                    _chrom[_num-1] = (char *) realloc(_chrom[_num-1], _res_chrom[_num-1] * sizeof(char));
                    if (!_chrom[_num-1]) throw EGGMEM;
                }
                _chrom[_num-1][i-1] = c;
            }
            if (i==0) throw EggFormatError(filename, _currline+1, "BED", "empty chromosome name");
            _chrom[_num-1][i] = '\0';

            // detect header/comment/special lines
            if ((_chrom[_num-1][0] == '#') | (!strncmp(_chrom[_num-1], "browser", 7)) | (!strncmp(_chrom[_num-1], "track", 5))) {
                _num--;
                if (c == '\t' || c == ' ') _next_line(); // skip rest of line to newline
                else _currline++;
                continue;
            }

            // get bounds
            _stream >> _start[_num-1];
            _stream >> _end[_num-1];
            if (!_stream.good()) {
                _num--;
                throw EggFormatError(filename, _currline+1, "BED", "invalid start/stop value");
            }

            // ignore rest of line
            _next_line();
        }
        _stream.close();
    }

    void BedParser::_open_file(const char * filename) {
        _stream.open(filename);
        if (!_stream.is_open()) throw EggOpenFileError(filename);

        unsigned int ln = strlen(filename) + 1;
        if (ln > _res_fname) {
            _fname = (char *) realloc(_fname, ln * sizeof(char));
            if (!_fname) throw EGGMEM;
            _res_fname = ln;
        }
        strcpy(_fname, filename);
    }

    void BedParser::_next_line() {
        char ch;
        while (true) {
            ch = _stream.get();
            if (ch == '\n') {
                _currline++;
                break;
            }
            if (ch == '\r') {
                if (_stream.get() != '\n') throw EggFormatError(_fname, _currline+1, "BED", "\r not followed by \n");
                _currline++;
                break;
            }
            if (_stream.eof()) break;
            if (!_stream.good()) throw EggFormatError(_fname, _currline+1, "BED", "reading error");
        }
    }

    void BedParser::_add_one() {
        _num++;
        if (_num > _res) { // allocate per 100 records at once
            _chrom = (char **) realloc(_chrom, (_res+100) * sizeof(char *));
            if (!_chrom) throw EGGMEM;
            _res_chrom = (unsigned int *) realloc(_res_chrom, (_res+100) * sizeof(unsigned int));
            if (!_res_chrom) throw EGGMEM;
            _start = (unsigned long *) realloc(_start, (_res+100) * sizeof(unsigned long));
            if (!_start) throw EGGMEM;
            _end = (unsigned long *) realloc(_end, (_res+100) * sizeof(unsigned long));
            if (!_end) throw EGGMEM;
            for (unsigned int i=0; i<100; i++) {
                _chrom[_res+i] = (char *) malloc(1 * sizeof(char));
                if (!_chrom[_res+i]) throw EGGMEM;
                _res_chrom[_res+i] = 0; // always 1 additional for final /0
            }
            _res += 100;
        }
    }

    void BedParser::append(const char * chrom, unsigned long start, unsigned long end) {
        _add_one();
        unsigned int ln = strlen(chrom);
        if (ln > _res_chrom[_num-1]) {
            _chrom[_num-1] = (char *) realloc(_chrom[_num-1], (ln+1) * sizeof(char));
            if (!_chrom[_num-1]) throw EGGMEM;
            _res_chrom[_num-1] = ln;
        }
        strcpy(_chrom[_num-1], chrom);
        _start[_num-1] = start;
        _end[_num-1] = end;
    }

    const char * BedParser::get_chrom(unsigned int i) const {
        return _chrom[i];
    }

    unsigned int BedParser::get_start(unsigned int i) const {
        return _start[i];
    }

    unsigned int BedParser::get_end(unsigned int i) const {
        return _end[i];
    }

    unsigned int BedParser::n_bed_data() const {
        return _num;
    }
}
