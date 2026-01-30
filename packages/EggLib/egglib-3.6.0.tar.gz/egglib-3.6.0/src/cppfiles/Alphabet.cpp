/*
    Copyright 2018-2021 Stéphane De Mita, Mathieu Siol

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

#include <cctype>
#include <cstring>
#include "Alphabet.hpp"
#include "egglib.hpp"

namespace egglib {
    static DNAAlphabet __DNAAlphabet;
    static CodonAlphabet __CodonAlphabet;

    void CaseInsensitiveCharAlphabet::add_exploitable(const char value) {
        FiniteAlphabet<char>::add_exploitable(toupper(value));
    }

    void CaseInsensitiveCharAlphabet::add_missing(const char value) {
        FiniteAlphabet<char>::add_missing(toupper(value));
    }

    int CaseInsensitiveCharAlphabet::_lookup(const char value) {
        return FiniteAlphabet<char>::_lookup(toupper(value));
    }

    bool CaseInsensitiveCharAlphabet::case_insensitive() const {
        return true;
    }

    StringAlphabet::StringAlphabet() {
        _max_len = 0;
        _res_exploitable = 0;
        _res_missing = 0;
        _res_len_exploitable = NULL;
        _res_len_missing = NULL;
    }

    void StringAlphabet::reset() {
        _max_len = 0;
        _num_exploitable = 0;
        _num_missing = 0;
    }

    StringAlphabet::~StringAlphabet() {
        for (unsigned int i=0; i<_res_exploitable; i++) if (_exploitable[i]) free(_exploitable[i]);
        for (unsigned int i=0; i<_res_missing; i++) if (_missing[i]) free(_missing[i]);
        if (_res_len_exploitable) free(_res_len_exploitable);
        if (_res_len_missing) free(_res_len_missing);
    }

    unsigned int StringAlphabet::longest_length() const {
        return _max_len;
    }

    int StringAlphabet::get_code(const char * value) {
        int code = _lookup(value);
        if (code == MISSINGDATA) throw EggAlphabetError<const char *>(this->_name, value);
        return code;
    }

    int StringAlphabet::_lookup(const char * value) {
        if (_num_missing > 0 && strcmp(value, _missing[0]) == 0) return -1; // try first the first missing allele
        for (unsigned int i=0; i<_num_exploitable; i++) {
            if (strcmp(value, _exploitable[i]) == 0) return i; // try exploitable alleles
        }
        for (unsigned int i=1; i<_num_missing; i++) if (strcmp(value, _missing[i]) == 0) return -i-1; // try other missing alleles
        return MISSINGDATA;
    }

    void StringAlphabet::add_exploitable(const char * const value) {
        _add(value, _num_exploitable, _res_exploitable, _res_len_exploitable, _exploitable);
    }

    void StringAlphabet::add_missing(const char * const value) {
        _add(value, _num_missing, _res_missing, _res_len_missing, _missing);
    }

    void StringAlphabet::_add(const char * const value, unsigned int& num,
                              unsigned int& res, unsigned int *& res_len, char **& list) {
        if (_lock) throw EggArgumentValueError("alphabet is locked");
        if (_lookup(value) != MISSINGDATA) throw EggArgumentValueError("allele already exists");
        num++;
        if (num > res) {
            list = (char **) realloc(list, num * sizeof(char *));
            if (!list) throw EGGMEM;
            res_len = (unsigned int *) realloc(res_len, num * sizeof(unsigned int));
            if (!res_len) throw EGGMEM;
            res_len[num-1] = 0;
            list[num-1] = NULL;
            res = num;
        }
        unsigned int n = strlen(value) + 1;
        if (n > res_len[num-1]) {
            list[num-1] = (char *) realloc(list[num-1], n * sizeof(char));
            if (!list[num-1]) throw EGGMEM;
            res_len[num-1] = n;
        }
        if (n > _max_len) _max_len = n + 1;
        strcpy(list[num-1], value);
    }

    void CaseInsensitiveStringAlphabet::add_exploitable(const char * const value) {
        _add(value, _num_exploitable, _res_exploitable, _res_len_exploitable, _exploitable);
        strcpy(_exploitable[_num_exploitable-1], _cache); // overwrite with upper case version
    }

    void CaseInsensitiveStringAlphabet::add_missing(const char * const value) {
        _add(value, _num_missing, _res_missing, _res_len_missing, _missing);
        strcpy(_missing[_num_missing-1], _cache); // overwrite with upper case version
    }

    CaseInsensitiveStringAlphabet::CaseInsensitiveStringAlphabet() {
        _sz_cache = 0;
        _cache = NULL;
    }

    CaseInsensitiveStringAlphabet::~CaseInsensitiveStringAlphabet() {
        if (_cache) free(_cache);
    }

    int CaseInsensitiveStringAlphabet::_lookup(const char * value) {
        if (strlen(value) > _sz_cache) {
            _cache = (char *) realloc(_cache, (strlen(value)+1) * sizeof(char));
            if (!_cache) throw EGGMEM;
        }
        const char * s = value;
        unsigned int i = 0;
        while (*s != '\0') {
            _cache[i++] = toupper((unsigned char) *s);
            s++;
        }
        _cache[i] = '\0';
        return StringAlphabet::_lookup(_cache);
    }

    bool CaseInsensitiveStringAlphabet::case_insensitive() const {
        return true;
    }

    RangeAlphabet::RangeAlphabet() {
        _expl_beg = 0;
        _expl_end = 0;
        _miss_beg = 0;
        _miss_end = 0;
        _expl_num = 0;
        _miss_num = 0;
    }

    unsigned int RangeAlphabet::num_exploitable() const {
        return _expl_num;
    }

    unsigned int RangeAlphabet::num_missing() const {
        return _miss_num;
    }

    const int RangeAlphabet::get_value(int code) {
        // if we check using _expl_num and _miss_num we can have an overflow
        // because if the limits are exhausting int, then the range is 2X
        if (code < 0) {
            code = _miss_beg - code - 1;
            if (code < _miss_beg || code >= _miss_end) throw EggArgumentValueError("allele code out of range");
        }
        else {
            code += _expl_beg;
            if (code < _expl_beg || code >= _expl_end) throw EggArgumentValueError("allele code out of range");
        }
        return code;
    }

    int RangeAlphabet::first_exploitable() const {
        return _expl_beg;
    }

    int RangeAlphabet::end_exploitable() const {
        return _expl_end;
    }

    int RangeAlphabet::first_missing() const {
        return _miss_beg;
    }

    int RangeAlphabet::end_missing() const {
        return _miss_end;
    }

    void RangeAlphabet::set_exploitable(int beg, int end) {
        if (end < beg) throw EggArgumentValueError("invalid exploitable alleles range");
        // review all cases where exploitable and missing ranges are non-overlapping
        if (beg == end ||             // no exploitable alleles
            _miss_num == 0 ||         // no missing alleles
            end <= _miss_beg ||       // exploitable before missing
            beg >= _miss_end) {       // exploitable after missing
                _expl_beg = beg;
                _expl_end = end;
                _expl_num = static_cast<unsigned int>(end - beg);
        }
        else {
            throw EggArgumentValueError("overlap between exploitable and missing alleles ranges");
        }
    }

    void RangeAlphabet::set_missing(int beg, int end) {
        if (end < beg) throw EggArgumentValueError("invalid missing alleles range");
        // review all cases where exploitable and missing ranges are non-overlapping
        if (beg == end ||             // no missing alleles
            _expl_num == 0 ||         // no exploitable alleles
            end <= _expl_beg ||       // missing before exploitable
            beg >= _expl_end) {       // missing after exploitable
                _miss_beg = beg;
                _miss_end = end;
                _miss_num = static_cast<unsigned int>(end - beg);
        }
        else {
            throw EggArgumentValueError("overlap between exploitable and missing alleles ranges");
        }
    }

    int RangeAlphabet::get_code(const int value) {
        if (value >= _expl_beg && value < _expl_end) return value - _expl_beg;
        if (value >= _miss_beg && value < _miss_end) return - (value - _miss_beg) - 1;
        throw EggAlphabetError<int>(this->_name, value);
    }

    int RangeAlphabet::min_value() const {
        if (_expl_beg == _expl_end) {
            if (_miss_beg < _miss_end) return _miss_beg;
            return 0;
        }
        if (_miss_beg == _miss_end) return _expl_beg;
        if (_miss_beg < _expl_beg) return _miss_beg;
        return _expl_beg;
    }

    int RangeAlphabet::max_value() const {
        if (_expl_beg == _expl_end) {
            if (_miss_beg < _miss_end) return _miss_end - 1;
            return 0;
        }
        if (_miss_beg == _miss_end) return _expl_end - 1;
        if (_miss_end > _expl_end) return _miss_end - 1;
        return _expl_end - 1;
    }

    DNAAlphabet::DNAAlphabet() {
        _lock = true;
        set_name("DNA");
        set_type("DNA");
        _num_missing = 13;
        _num_exploitable = 4;
        _missing = (char *) realloc(_missing, 13 * sizeof(char));
        if (!_missing) throw EGGMEM;
        _exploitable = (char *) realloc(_exploitable, 4 * sizeof(char));
        if (!_exploitable) throw EGGMEM;
        _codes = (int *) malloc(77 * sizeof(int));
        if (!_codes) throw EGGMEM;
        _exploitable[0] = 'A';
        _exploitable[1] = 'C';
        _exploitable[2] = 'G';
        _exploitable[3] = 'T';
        _missing[0] = '-';
        _missing[1] = 'N';
        _missing[2] = '?';
        _missing[3] = 'R';
        _missing[4] = 'Y';
        _missing[5] = 'S';
        _missing[6] = 'W';
        _missing[7] = 'K';
        _missing[8] = 'M';
        _missing[9] = 'B';
        _missing[10] = 'D';
        _missing[11] = 'H';
        _missing[12] = 'V';
        _codes[0] = -1;
        _codes[1] = MISSINGDATA;
        _codes[2] = MISSINGDATA;
        _codes[3] = MISSINGDATA;
        _codes[4] = MISSINGDATA;
        _codes[5] = MISSINGDATA;
        _codes[6] = MISSINGDATA;
        _codes[7] = MISSINGDATA;
        _codes[8] = MISSINGDATA;
        _codes[9] = MISSINGDATA;
        _codes[10] = MISSINGDATA;
        _codes[11] = MISSINGDATA;
        _codes[12] = MISSINGDATA;
        _codes[13] = MISSINGDATA;
        _codes[14] = MISSINGDATA;
        _codes[15] = MISSINGDATA;
        _codes[16] = MISSINGDATA;
        _codes[17] = MISSINGDATA;
        _codes[18] = -3;
        _codes[19] = MISSINGDATA;
        _codes[20] = 0;
        _codes[21] = -10;
        _codes[22] = 1;
        _codes[23] = -11;
        _codes[24] = MISSINGDATA;
        _codes[25] = MISSINGDATA;
        _codes[26] = 2;
        _codes[27] = -12;
        _codes[28] = MISSINGDATA;
        _codes[29] = MISSINGDATA;
        _codes[30] = -8;
        _codes[31] = MISSINGDATA;
        _codes[32] = -9;
        _codes[33] = -2;
        _codes[34] = MISSINGDATA;
        _codes[35] = MISSINGDATA;
        _codes[36] = MISSINGDATA;
        _codes[37] = -4;
        _codes[38] = -6;
        _codes[39] = 3;
        _codes[40] = MISSINGDATA;
        _codes[41] = -13;
        _codes[42] = -7;
        _codes[43] = MISSINGDATA;
        _codes[44] = -5;
        _codes[45] = MISSINGDATA;
        _codes[46] = MISSINGDATA;
        _codes[47] = MISSINGDATA;
        _codes[48] = MISSINGDATA;
        _codes[49] = MISSINGDATA;
        _codes[50] = MISSINGDATA;
        _codes[51] = MISSINGDATA;
        _codes[52] = 0;
        _codes[53] = -10;
        _codes[54] = 1;
        _codes[55] = -11;
        _codes[56] = MISSINGDATA;
        _codes[57] = MISSINGDATA;
        _codes[58] = 2;
        _codes[59] = -12;
        _codes[60] = MISSINGDATA;
        _codes[61] = MISSINGDATA;
        _codes[62] = -8;
        _codes[63] = MISSINGDATA;
        _codes[64] = -9;
        _codes[65] = -2;
        _codes[66] = MISSINGDATA;
        _codes[67] = MISSINGDATA;
        _codes[68] = MISSINGDATA;
        _codes[69] = -4;
        _codes[70] = -6;
        _codes[71] = 3;
        _codes[72] = MISSINGDATA;
        _codes[73] = -13;
        _codes[74] = -7;
        _codes[75] = MISSINGDATA;
        _codes[76] = -5;
    }

    DNAAlphabet::~DNAAlphabet() {
        if (_codes) free(_codes);
    }

    void DNAAlphabet::add_exploitable(const char value) {
        throw EggArgumentValueError("DNAAlphabet is locked");
    }

    void DNAAlphabet::add_missing(const char value) {
        throw EggArgumentValueError("DNAAlphabet is locked");
    }

    int DNAAlphabet::_lookup(const char value) {
        unsigned int v = static_cast<unsigned int>(value);
        if (v < 45 || v > 121) return MISSINGDATA;
        return _codes[v-45];
    }

    DNAAlphabet& get_static_DNAAlphabet() {
        return __DNAAlphabet;
    }

    CodonAlphabet::CodonAlphabet() {
        _lock = true;
        set_name("codons");
        set_type("codons");
        _max_len = 3;

        _num_exploitable = 64;
        _res_exploitable = 64;
        _exploitable = (char **) realloc(_exploitable, _num_exploitable * sizeof(char *));
        if (!_exploitable) throw EGGMEM;
        for (unsigned int i=0; i<_num_exploitable; i++) {
            _exploitable[i] = (char *) malloc(4 * sizeof(char));
            if (!_exploitable[i]) throw EGGMEM;
        }
        _num_missing = 4849;
        _res_missing = 4849;
        _missing = (char **) realloc(_missing, _num_missing * sizeof(char *));
        if (!_missing) throw EGGMEM;
        for (unsigned int i=0; i<_num_missing; i++) {
            _missing[i] = (char *) malloc(4 * sizeof(char));
            if (!_missing[i]) throw EGGMEM;
        }

        _codon_table = (int ***) malloc(17 * sizeof(int **));
        if (!_codon_table) throw EGGMEM;
        for (unsigned int i=0; i<17; i++) {
            _codon_table[i] = (int **) malloc(17 * sizeof(int *));
            if (!_codon_table[i]) throw EGGMEM;
            for (unsigned int j=0; j<17; j++) {
                _codon_table[i][j] = (int *) malloc(17 * sizeof(int));
                if (!_codon_table[i][j]) throw EGGMEM;
            }
        }

        #include "Alphabet.epp"
    }

    CodonAlphabet::~CodonAlphabet() {
        if (_codon_table) {
            for (unsigned int i=0; i<17; i++) {
                if (_codon_table[i]) {
                    for (unsigned int j=0; j<17; j++) {
                        if (_codon_table[i][j]) free(_codon_table[i][j]);
                    }
                    if (_codon_table[i]) free(_codon_table[i]);
                }
            }
            if (_codon_table) free(_codon_table);
        }
    }

    int CodonAlphabet::get_code(const char * value) {
        if (strlen(value) != 3) throw EggArgumentValueError("codon must have 3 bases");
        int b1 = __DNAAlphabet.get_code(static_cast<int>(value[0]));
        int b2 = __DNAAlphabet.get_code(static_cast<int>(value[1]));
        int b3 = __DNAAlphabet.get_code(static_cast<int>(value[2]));
        if (b1 < 0) b1 = 3 - b1;
        if (b2 < 0) b2 = 3 - b2;
        if (b3 < 0) b3 = 3 - b3;
        return _codon_table[b1][b2][b3];
    }

    int CodonAlphabet::get_code_from_bases(int b1, int b2, int b3) {
        if (b1 < -13 || b1 > 3) throw EggAlphabetError<int>(this->_name, b1);
        if (b2 < -13 || b2 > 3) throw EggAlphabetError<int>(this->_name, b2);
        if (b3 < -13 || b3 > 3) throw EggAlphabetError<int>(this->_name, b3);
        if (b1 < 0) b1 = 3 - b1;
        if (b2 < 0) b2 = 3 - b2;
        if (b3 < 0) b3 = 3 - b3;
        return _codon_table[b1][b2][b3];
    }

    CodonAlphabet& get_static_CodonAlphabet() {
        return __CodonAlphabet;
    }
}
