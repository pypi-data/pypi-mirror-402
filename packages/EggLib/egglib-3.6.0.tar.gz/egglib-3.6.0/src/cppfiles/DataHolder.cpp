/*
    Copyright 2012-2023 Stéphane De Mita, Mathieu Siol

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

#include "egglib.hpp"
#include "DataHolder.hpp"
extern "C" {
    #include "random.h"
}
#include "Coalesce.hpp"
#include "Alphabet.hpp"
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <cctype>

namespace egglib {

    void VectorInt::copy(const VectorInt& src) {
        set_num_values(src._num);
        for (unsigned int i=0; _num; i++) _values[i] = src._values[i];
    }

    VectorInt::VectorInt() {
        _num = 0;
        _res = 0;
        _values = NULL;
    }

    VectorInt::~VectorInt() {
        if (_values) free(_values);
    }

    VectorInt::VectorInt(const VectorInt& src) {
        _res = 0;
        _values = NULL;
        copy(src);
    }

    VectorInt& VectorInt::operator=(const VectorInt& src) {
        copy(src);
        return * this;
    }

    void VectorInt::set_num_values(unsigned int n) {
        _num = n;
        if (_num > _res) {
            _values = (int *) realloc(_values, _num * sizeof(int));
            if (!_values) throw EGGMEM;
        }
    }

    unsigned int VectorInt::get_num_values() const {
        return _num;
    }

    void VectorInt::set_item(unsigned int i, int value) {
        _values[i] = value;
    }

    int VectorInt::get_item(unsigned int i) const {
        return _values[i];
    }

    void VectorInt::clear() {
        if (_values) free(_values);
        _res = 0;
        _num = 0;
        _values = NULL;
    }

    void DataHolder::_init() {
        _ns = 0;
        _ns_r = 0;
        _nlabels = NULL;
        _nlabels_r = NULL;
        _labels_r = NULL;
        _labels_l = NULL;
        _ls_all = 0;
        _ls_sample = NULL;
        _ls_r = NULL;
        _ln = NULL;
        _ln_r = NULL;
        _data = NULL;
        _names = NULL;
        _labels = NULL;
        _n_temp_string = 0;
        _temp_string = NULL;
        _strip_list_n = 0;
        _strip_list_c = 0;
        _strip_list = NULL;
    }

    void DataHolder::_free() {

        // clean data table and names
        for (unsigned int i=0; i<_ns_r; i++) {
            if (_data[i]) free(_data[i]);
            if (_names[i]) free(_names[i]);
        }
        if (_data) free(_data);
        if (_names) free(_names);

        // clean labels
        for (unsigned int i=0; i<_ns_r; i++) {
            for (unsigned int j=0; j<_nlabels_r[i];j++){
                if (_labels[i][j]) free(_labels[i][j]);
            }
            if (_labels[i]) free(_labels[i]);
            if (_labels_r[i]) free(_labels_r[i]);
            if (_labels_l[i]) free(_labels_l[i]);
        }
        if (_labels) free(_labels);
        if (_labels_r) free(_labels_r);
        if (_labels_l) free(_labels_l);

        // clean 1-dimensional tables
        if (_ln) free(_ln);
        if (_ln_r) free(_ln_r);
        if (_ls_sample) free(_ls_sample);
        if (_ls_r) free(_ls_r);
        if (_nlabels) free(_nlabels);
        if (_nlabels_r) free(_nlabels_r); // needed to clean labels
        if (_temp_string) free(_temp_string);
        if (_strip_list) free(_strip_list);
    }

    void DataHolder::_alloc_ns(unsigned int ns) {
        if (ns > _ns_r) {
            _ls_sample = (unsigned int * ) realloc(_ls_sample, ns * sizeof(unsigned int));
            if (!_ls_sample) throw EGGMEM;
            _ln = (unsigned int * ) realloc(_ln, ns * sizeof(unsigned int));
            if (!_ln) throw EGGMEM;
            _data = (int ** ) realloc(_data, ns * sizeof(int * ));
            if (!_data) throw EGGMEM;
            _names = (char ** ) realloc(_names, ns * sizeof(char * ));
            if (!_names) throw EGGMEM;
            _labels = (char *** ) realloc(_labels, ns * sizeof(char ** ));
            if (!_labels) throw EGGMEM;
            _nlabels = (unsigned int * ) realloc(_nlabels, ns * sizeof(unsigned int));
            if (!_nlabels) throw EGGMEM;

            _ls_r = (unsigned int * ) realloc(_ls_r, ns * sizeof(unsigned int));
            if (!_ls_r) throw EGGMEM;
            _ln_r = (unsigned int * ) realloc(_ln_r, ns * sizeof(unsigned int));
            if (!_ln_r) throw EGGMEM;
            _nlabels_r = (unsigned int * ) realloc(_nlabels_r, ns * sizeof(unsigned int));
            if (!_nlabels_r) throw EGGMEM;
            _labels_r = (unsigned int ** ) realloc(_labels_r, ns * sizeof(unsigned int *));
            if (!_labels_r) throw EGGMEM;
            _labels_l = (unsigned int ** ) realloc(_labels_l, ns * sizeof(unsigned int *));
            if (!_labels_l) throw EGGMEM;

            for (unsigned int i=_ns_r; i<ns; i++) {
                _data[i] = NULL;
                _ls_r[i] = 0;
                _names[i] = NULL;
                _ln_r[i] = 0;
                _labels[i] = NULL;
                _labels_r[i] = NULL;
                _labels_l[i] = NULL;
                _nlabels_r[i] = 0;
            }
            _ns_r = ns;
        }
    }

    void DataHolder::_alloc_nlabels_sample(unsigned int sam, unsigned int nlabels) {
        if (nlabels > _nlabels_r[sam]) {
            _labels[sam] = (char ** ) realloc(_labels[sam], nlabels * sizeof(char *));
            if (!_labels[sam]) throw EGGMEM;
            _labels_r[sam] = (unsigned int *) realloc(_labels_r[sam], nlabels * sizeof(unsigned int));
            if (!_labels_r[sam]) throw EGGMEM;
            _labels_l[sam] = (unsigned int *) realloc(_labels_l[sam], nlabels * sizeof(unsigned int));
            if (!_labels_l[sam]) throw EGGMEM;
            for (unsigned int j=_nlabels_r[sam]; j<nlabels; j++) {
                _labels[sam][j] = (char *) malloc(10 * sizeof(char));
                if (!_labels[sam][j]) throw EGGMEM;
                _labels[sam][j][0] = '\0';
                _labels_r[sam][j] = 10;
                _labels_l[sam][j] = 1;
            }
            _nlabels_r[sam] = nlabels;
        }
    }

    void DataHolder::_alloc_nlabels_all(unsigned int nlabels) {
        for (unsigned int i=0; i<_ns; i++) _alloc_nlabels_sample(i, nlabels);
    }

    void DataHolder::_alloc_ls_all(unsigned int ls) {
        for (unsigned int i=0; i<_ns; i++) _alloc_ls_sample(i, ls);
    }

    void DataHolder::_alloc_ls_sample(unsigned int i, unsigned int ls) {
        if (ls > _ls_r[i]) {
            _data[i] = (int * ) realloc(_data[i], ls * sizeof(int));
            if (!_data[i]) throw EGGMEM;
            _ls_r[i] = ls;
        }
    }

    void DataHolder::_alloc_ln(unsigned int i, unsigned int ln) {
        if (ln > _ln_r[i]) {
            _names[i] = (char * ) realloc(_names[i], ln * sizeof(char));
            if (!_names[i]) throw EGGMEM;
            _ln_r[i] = ln;
        }
    }

    void DataHolder::_copy(const DataHolder& src) {
        _is_matrix = src._is_matrix;

        // allocate arrays
        _ns = src._ns;
        _alloc_ns(_ns);

        // get names and labels
        for (unsigned int i=0; i<_ns; i++) {
            set_name(i, src._names[i]);
            set_nlabels(i, src._nlabels[i]);
            for (unsigned int j=0; j<src._nlabels[i]; j++) set_label(i, j, src._labels[i][j]);
        }

        // get data
        if (_is_matrix) {
            _ls_all = src._ls_all;
            _alloc_ls_all(_ls_all);
            for (unsigned int j=0; j<_ls_all; j++) {
                for (unsigned int i=0; i<_ns; i++) _data[i][j] = src._data[i][j];
            }
        }
        else {
            for (unsigned int i=0; i<_ns; i++) {
                _ls_sample[i] = src._ls_sample[i];
                _alloc_ls_sample(i, src._ls_sample[i]);
                for (unsigned int j=0; j<_ls_sample[i]; j++) _data[i][j] = src._data[i][j];
            }
        }
    }

    DataHolder::DataHolder(bool is_matrix) {
        _init();
        _is_matrix = is_matrix;
    }

    DataHolder::DataHolder(const DataHolder& src) {
        _init();
        _copy(src);
    }

    DataHolder& DataHolder::operator=(const DataHolder& src) {
        _copy(src);
        return *this;
    }

    DataHolder::~DataHolder() {
        _free();
    }

    void DataHolder::set_is_matrix(bool flag) {

        // matrix -> non-matrix
        if (_is_matrix == true && flag == false) {
            for (unsigned int i=0; i<_ns; i++) _ls_sample[i] = _ls_all;
            _is_matrix = false;
        }

        // non-matrix -> matrix
        if (_is_matrix == false && flag == true) {
            if (_ns > 0) _ls_all = _ls_sample[0];
            else _ls_all = 0;
            _is_matrix = true;
        }

        // nothing to do otherwise
    }

    bool DataHolder::get_is_matrix() const {
        return _is_matrix;
    }

    void DataHolder::reserve(unsigned int ns, unsigned int ln, unsigned int nlabels, unsigned int ls) {
        _alloc_ns(ns);
        _alloc_nlabels_all(nlabels);
        _alloc_ls_all(ls);
        for (unsigned int i=0; i<ns; i++) _alloc_ln(i, ln);
    }

    unsigned int DataHolder::get_nsam() const {
        return _ns;
    }

    void DataHolder::set_nsam(unsigned int nsam) {
        _alloc_ns(nsam);
        for (unsigned int i=_ns; i<nsam; i++) {
            set_name(i, "");
            if (_is_matrix) {
                _alloc_ls_sample(i, _ls_all);
                _ls_sample[i] = _ls_all;
            }
            else {
                _ls_sample[i] = 0;
            }
            _nlabels[i] = 0;
        }
        _ns = nsam;
    }

    unsigned int DataHolder::get_nsit_all() const {
        return _ls_all;
    }

    unsigned int DataHolder::get_nsit_sample(unsigned int sam) const {
        return _ls_sample[sam];
    }

    void DataHolder::set_nsit_all(unsigned int val) {
        _ls_all = val;
        _alloc_ls_all(_ls_all);
    }

    void DataHolder::set_nsit_sample(unsigned int sam, unsigned int val) {
        _ls_sample[sam] = val;
        _alloc_ls_sample(sam, val);
    }

    void DataHolder::insert_sites_all(unsigned int pos, unsigned int num) {
        if (num == 0) return;          // nothing to do (prevents side effect with j iterator)

        // increase the data table (add num to all arrays)
        if (_is_matrix) {
            _ls_all += num;
            _alloc_ls_all(_ls_all);
        }
        else {
            for (unsigned int i=0; i<_ns; i++) {
                _ls_sample[i] += num;
                _alloc_ls_sample(i, _ls_sample[i]);
            }
        }

        // shift sites (only if pos is not MAX)
        if (pos != MAX) {
            unsigned int ls = _ls_all; // changed if not matrix
            for (unsigned int i=0; i<_ns; i++) {
                if (!_is_matrix) ls = _ls_sample[i];
                for (unsigned int j=ls-1; j>=pos+num; j--) {
                    _data[i][j] =  _data[i][j-num];
                }
            }
        }
    }

    void DataHolder::insert_sites_sample(unsigned int sam, unsigned int pos, unsigned int num) {
        if (num == 0) return;
        _ls_sample[sam] += num;
        _alloc_ls_sample(sam, _ls_sample[sam]);
        for (unsigned int i=_ls_sample[sam]; i>pos+num; i--) _data[sam][i-1] = _data[sam][i-1-num];
    }

    unsigned int DataHolder::get_nlabels(unsigned int sam) const {
        return _nlabels[sam];
    }

    void DataHolder::set_nlabels(unsigned int sam, unsigned int nlabels) {
        _nlabels[sam] = nlabels;
        _alloc_nlabels_sample(sam, nlabels);
    }

    void DataHolder::set_all_nlabels(unsigned int nlabels) {
        for (unsigned int sam=0; sam<_ns; sam++) {
            _nlabels[sam] = nlabels;
            _alloc_nlabels_sample(sam, nlabels);
        }
    }

    int DataHolder::get_sample(unsigned int sam, unsigned int sit) const {
        return _data[sam][sit];
    }

    void DataHolder::set_sample(unsigned int sam, unsigned int sit, int value) {
        #ifdef DEBUG
        ostringstream stream;
        if (sam >= _ns) stream << " sample index out of range (ns: " << _ns << " got: " << sam << ")";
        if (_is_matrix && sit >= _ls_all) stream << " site index out of range (ls: " << _ls_all << " got: " << sit << ")";
        if (!_is_matrix && sit >= _ls_sample[sam]) stream << " site index out of range (ls[" << sam << "]: " << _ls_sample[sam] << " got: " << sit << ")";
        if (stream.str() != "") throw EggArgumentValueError(("out of range error:" + stream.str()).c_str());
        #endif
        _data[sam][sit] = value;
    }

    const char * DataHolder::get_label(unsigned int sam, unsigned int lvl) const {
        return _labels[sam][lvl];
    }

    void DataHolder::set_label(unsigned int sam, unsigned int lvl, const char * label) {
        #ifdef DEBUG
        ostringstream stream;
        if (sam >= _ns) stream << " sample index out of range (ns: " << _ns << " got: " << sam << ")";
        if (lvl >= _nlabels[sam]) stream << " label index out of range (nlabels[" << sam << "]: " << _nlabels[sam] << " got: " << lvl << ")";
        if (stream.str() != "") throw EggArgumentValueError(("out of range error:" + stream.str()).c_str());
        #endif
        if (strlen(label) == 0) throw EggArgumentValueError("empty labels are not accepted");
        _labels_l[sam][lvl] = strlen(label) + 1;
        if (_labels_l[sam][lvl] > _labels_r[sam][lvl]) {
            _labels[sam][lvl] = (char *) realloc(_labels[sam][lvl], _labels_l[sam][lvl] * sizeof(char));
            if (!_labels[sam][lvl]) throw EGGMEM;
            _labels_r[sam][lvl] = _labels_l[sam][lvl];
        }
        strcpy(_labels[sam][lvl], label);
    }

    void DataHolder::append_label(unsigned int sam, unsigned int lvl, char ch) {
        _labels_l[sam][lvl]++;
        if ((_labels_l[sam][lvl] + 10) > _labels_r[sam][lvl]) {
            _labels[sam][lvl] = (char *) realloc(_labels[sam][lvl], (_labels_l[sam][lvl] + 10) * sizeof(char));
            if (!_labels[sam][lvl]) throw EGGMEM;
            _labels_r[sam][lvl] = _labels_l[sam][lvl] + 10;
        }
        _labels[sam][lvl][_labels_l[sam][lvl] - 2] = ch;
        _labels[sam][lvl][_labels_l[sam][lvl] - 1] = '\0';
    }

    void DataHolder::add_label(unsigned int sam, const char * label) {
        set_nlabels(sam, _nlabels[sam] + 1);
        set_label(sam, _nlabels[sam] - 1, label);
    }

    void DataHolder::add_uninit_label(unsigned int sam) {
        set_nlabels(sam, _nlabels[sam] + 1);
    }

    const char * DataHolder::get_name(unsigned int sam) const {
        return _names[sam];
    }

    void DataHolder::set_name(unsigned int sam, const char * name) {
        _ln[sam] = strlen(name) + 1; // be careful, at some point we check empty names by _lni[i]==1 (valid_phyml_names)
        _alloc_ln(sam, _ln[sam]);
        strcpy(_names[sam], name);
    }

    void DataHolder::name_appendch(unsigned int sam, char ch) {
        _ln[sam]++;
        _alloc_ln(sam, _ln[sam]);
        _names[sam][_ln[sam]-2] = ch;
        _names[sam][_ln[sam]-1] = '\0';
    }

    void DataHolder::name_append(unsigned int sam, const char * str) {
        unsigned int cur = _ln[sam];
        _ln[sam] += strlen(str);          // might overflow because strlen returns a size_t
        _alloc_ln(sam, _ln[sam]);
        strcpy(_names[sam]+cur-1, str);
        _names[sam][_ln[sam]-1] = '\0';
    }

    void DataHolder::del_sample(unsigned int sam) {
        if (sam == _ns-1) {
            _ns--;
        }
        else {
            char * name = _names[sam];
            int * data = _data[sam];
            char ** labels = _labels[sam];
            unsigned int ls = _ls_sample[sam]; // only used if not matrix
            unsigned int ln_r = _ln_r[sam];
            unsigned int ls_r = _ls_r[sam];
            unsigned int nlabels_r = _nlabels_r[sam];
            unsigned int * labels_r = _labels_r[sam];
            unsigned int * labels_l = _labels_l[sam];

            for (unsigned int i=sam; i<_ns-1; i++) {
                _names[i] = _names[i+1];
                _data[i] = _data[i+1];
                if (!_is_matrix) _ls_sample[i] = _ls_sample[i+1];
                _labels[i] = _labels[i+1];
                _ln[i] = _ln[i+1];
                _ln_r[i] = _ln_r[i+1];
                _ls_r[i] = _ls_r[i+1];
                _nlabels_r[i] = _nlabels_r[i+1];
                _labels_r[i] = _labels_r[i+1];
                _labels_l[i] = _labels_l[i+1];
            }

            _ns--;

            _names[_ns] = name;
            _data[_ns] = data;
            _labels[_ns] = labels;
            _ln_r[_ns] = ln_r;
            _ls_r[_ns] = ls_r;
            _nlabels_r[_ns] = nlabels_r;
            _labels_r[_ns] = labels_r;
            _labels_l[_ns] = labels_l;
            if (!_is_matrix) _ls_sample[_ns] = ls;
        }

        if (_ns == 0) _ls_all = 0;
    }

    void DataHolder::del_sites_all(unsigned int start, unsigned int stop) {
        if (start>=stop) return;
        if (_is_matrix) {
            unsigned int ls = _ls_all;
            if (start >= ls) return;
            if (stop > ls) stop = ls;
            for (unsigned int i=0; i<_ns; i++) {
                for (unsigned int j=0; stop+j<_ls_all; j++) {
                    _data[i][start+j] = _data[i][stop+j];
                }
            }
            _ls_all -= (stop-start); // do it after because of the stop condition
        }
        else {
            for (unsigned int i=0; i<_ns; i++) {
                del_sites_sample(i, start, stop);
            }
        }
    }

    void DataHolder::del_sites_sample(unsigned int sam, unsigned int start, unsigned int stop) {
        unsigned int ls = _ls_sample[sam];
        if (start >= ls) return;
        if (stop > ls) stop = ls;
        _ls_sample[sam] -= (stop-start);
        for (unsigned int i=0; stop+i<ls; i++) { // use old ls (similar to del_sites_all where _ls_all is updated last)
            _data[sam][start+i] = _data[sam][stop+i];
        }
    }

    void DataHolder::reset(bool is_matrix) {
        _ns = 0;
        if (is_matrix) _ls_all = 0;
        _is_matrix = is_matrix;
    }

    void DataHolder::clear(bool is_matrix) {
        _free();
        _init();
        _is_matrix = is_matrix;
    }

    unsigned int DataHolder::find(unsigned int sam, VectorInt& motif, unsigned int start, unsigned int stop) const {
        if (_is_matrix) {
            if (stop > _ls_all) stop = _ls_all;
        }
        else {
            if (stop > _ls_sample[sam]) stop = _ls_sample[sam];
        }

        unsigned int n = motif.get_num_values();

        if (start >= stop || n==0) return MAX;

        unsigned int i=start;
        unsigned int j;

        while (true) {
            j = 0;
            while (true) {
                if (i+j == stop) return MAX;
                if (_data[sam][i+j] != motif.get_item(j)) break;
                j++;
                if (j==n) return i;
            }
            i++;
        }
        throw EggRuntimeError("this point should not be reached (DataHolder::find)");
        return MAX;
    }

    bool DataHolder::is_equal() const {
        for (unsigned int i=1; i<_ns; i++) if (_ls_sample[i] != _ls_sample[0]) return false;
        return true;
    }

    bool DataHolder::valid_phyml_names() const {
        for (unsigned int i=0; i<_ns; i++) {
            if (_ln[i] == 1) return false;
            for (unsigned int j=0; j<_ln[i]; j++) {
                switch (_names[i][j]) {
                    case ' ': case '\t': case '\r': case '\n':
                    case ',': case ':': case '(': case ')':
                        return false;
                }
            }
        }
        return true;
    }

    void DataHolder::change_case(bool lower, int index, int start, int stop, AbstractBaseAlphabet& alph) {
        // set the function pointer
        int (*fconvert)(int) = lower ? (int(*)(int))&tolower : (int(*)(int))&toupper;
            // the above code is rather unfriendly but only picks up the right function between tolower and toupper
            // the & is to get the function's address (it can be ommitted with GCC)
            // int(*)(int) is the function's signature: it has to be included
                // because we are within a ternary and the compiler doesn't know the type of the destination variable (fconvert)

        // check index values
        if (index < 0) index += _ns;
        if (index < 0) throw EggIndexError("ingroup sample index out of range");
        unsigned int uindex = index;
        if (uindex >= _ns) throw EggIndexError("ingroup sample index out of range");
        if (start < 0) {
            if (_is_matrix) start += _ls_all;
            else start += _ls_sample[index];
        }
        if (start < 0) throw EggIndexError("site index out of range");
        unsigned int ustart = start;
        unsigned int ls;
        if (_is_matrix) {
            if (ustart >= _ls_all) throw EggIndexError("site index out of range");
            ls = _ls_all;
        }
        else {
            if (ustart >= _ls_sample[uindex]) throw EggIndexError("site index out of range");
            ls = _ls_sample[uindex];
        }
        if (stop < 0) {
            if (_is_matrix) stop += _ls_all;
            else stop += _ls_sample[uindex];
        }
        if (stop < 0) throw EggIndexError("site index out of range");
        unsigned int ustop = stop;

        // check alphabet and perform conversion
        if (alph.case_insensitive() == true) throw EggArgumentValueError("cannot change case: alphabet is case insensitive");
        if (strcmp(alph.get_type(), "char")==0) {
            FiniteAlphabet<char> * alph_C = static_cast<FiniteAlphabet<char> *>(&alph);
            for (unsigned int i=ustart; i<ustop && i<ls; i++) {
                _data[uindex][i] = alph_C->get_code((*fconvert)(alph_C->get_value(_data[uindex][i])));
            }
        }
        else {
            if (strcmp(alph.get_type(), "string")==0) {
                StringAlphabet * alph_S = static_cast<StringAlphabet *>(&alph);
                if (alph_S->longest_length() > _n_temp_string) {
                    _temp_string = (char *) realloc(_temp_string, alph_S->longest_length() * sizeof(char));
                    if (!_temp_string) throw EGGMEM;
                }
                for (unsigned int i=ustart; i<ustop && i<ls; i++) {
                    strcpy(_temp_string, alph_S->get_value(_data[uindex][i]));
                    char * c = _temp_string;
                    while (*c != '\0') {
                        *c = (*fconvert)(*c);
                        c++;
                    }
                    _data[uindex][i] = alph_S->get_code(_temp_string);
                }
            }
            else {
                throw EggArgumentValueError("cannot change case: invalid alphabet");
            }
        }
    }

    void DataHolder::strip_clear() {
        _strip_list_n = 0;
    }

    void DataHolder::strip_add(int v) {
        _strip_list_n++;
        if (_strip_list_n > _strip_list_c) {
            _strip_list = (int *) realloc(_strip_list, _strip_list_n * sizeof(int));
            if (!_strip_list) throw EGGMEM;
        }
        _strip_list[_strip_list_n - 1] = v;
    }

    void DataHolder::strip(unsigned int index, bool left, bool right) {
        if (_is_matrix == true) throw EggArgumentValueError("cannot strip sequences of an Align");
        if (index >= _ns) throw EggIndexError("sample index out of range");

        if (left) {
            unsigned int i=0;
            unsigned int j;
            while (i < _ls_sample[index]) {
                for (j=0; j<_strip_list_n; j++) if (_strip_list[j] == _data[index][i]) break;
                if (j == _strip_list_n) break;
                i++;
            }
            del_sites_sample(index, 0, i);
        }

        if (right && _ls_sample[index] > 0) {
            unsigned int i=_ls_sample[index] - 1;
            unsigned int j;
            while (i >= 0) {
                for (j=0; j<_strip_list_n; j++) if (_strip_list[j] == _data[index][i]) break;
                if (j == _strip_list_n) break;
                i--;
            }
            del_sites_sample(index, i+1, _ls_sample[index]);
        }
    }

    IntersperseAlign::IntersperseAlign() {
        _alleles = (int *) malloc(1 * sizeof(int));
        if (!_alleles) throw EGGMEM;
        _alleles[0] = static_cast<int>('A');
        _num_alleles = 1;
        _res_alleles = 1;

        _positions = NULL;
        _round_positions = NULL;
        _offset = NULL;
        _res_positions = 0;

        _data = NULL;
        _nsites = 0;
        _length = 0;
    }

    IntersperseAlign::~IntersperseAlign() {
        if (_alleles) free(_alleles); // in principle, test is not needed
        if (_positions) free(_positions);
        if (_round_positions) free(_round_positions);
        if (_offset) free(_offset);
    }

    void IntersperseAlign::load(DataHolder& data) {
        _data = & data;
        _nsites = data.get_nsit_all();
        if (_nsites > _res_positions) {
            _positions = (double *) realloc(_positions, _nsites * sizeof(double));
            if (!_positions) throw EGGMEM;
            _round_positions = (unsigned int *) realloc(_round_positions, _nsites * sizeof(unsigned int));
            if (!_round_positions) throw EGGMEM;
            _offset = (unsigned int *) realloc(_offset, (_nsites + 1) * sizeof(unsigned int));
            if (!_offset) throw EGGMEM;
            _res_positions = _nsites;
        }
    }

    void IntersperseAlign::set_length(unsigned int length) {
        _length = length;
    }

    void IntersperseAlign::set_position(unsigned int index, double position) {
        _positions[index] = position;
    }

    void IntersperseAlign::set_round_position(unsigned int index, unsigned int position) {
        _round_positions[index] = position;
    }

    void IntersperseAlign::get_positions(const Coalesce& coalesce) {
        for (unsigned int i=0; i<_nsites; i++) {
            _positions[i] = coalesce.site_position(i); // positions are guaranteed to be increasing
        }
    }

    void IntersperseAlign::set_num_alleles(unsigned int num) {
        if (num > _res_alleles) {
            _alleles = (int *) realloc(_alleles, num * sizeof(int));
            if (!_alleles) EGGMEM;
            _res_alleles = num;
        }
        _num_alleles = num;
    }

    void IntersperseAlign::set_allele(unsigned int index, int allele) {
        _alleles[index] = allele;
    }

    void IntersperseAlign::intersperse(bool round_positions) {

        // don't do anything if no sites need to be inserted
        if (_nsites >= _length) return;

        // convert positions to integers
        if (round_positions) {
            for (unsigned int i=0; i<_nsites; i++) {
                _round_positions[i] = floor(0.5 + _positions[i] * (_length-1));
            }
        }

        // determines offsets
        unsigned int tot_insert = 0;

        // first site (if any)
        if (_nsites > 0) {
            _offset[0] = _round_positions[0];
            tot_insert += _offset[0];
        }

        // other sites
        for (unsigned int i=1; i<_nsites; i++) {
            _offset[i] =  (_round_positions[i] == _round_positions[i-1]) ? 0 : _round_positions[i] - _round_positions[i-1] - 1;
            tot_insert += _offset[i];
        }

        // after last site
        if (_nsites > 0) _offset[_nsites] = _length - _round_positions[_nsites-1] - 1;
        else _offset[_nsites] = _length;
        tot_insert += _offset[_nsites];

        // correct error randomly (not enough or too many inserted sites)
        int error = tot_insert + _nsites - _length;

        double X;
        while (error != 0) {

            // pick a random interval
            X = egglib_random_uniform() * tot_insert;

            unsigned int i;
            unsigned int acc = 0;
            for (i=0; i<_nsites+1; i++) {
                acc += _offset[i];
                if (X < acc) break;
            }

            // remove/add a site there
            if (error > 0) {
                _offset[i]--;
                tot_insert--;
                error--;
            }

            else {
               _offset[i]++;
               tot_insert++; 
               error++;
           }
        }

        // insert sites in the alignment
        unsigned int pos = 0;
        int allele;
        for (unsigned int site=0; site<_nsites+1; site++) {
            _data->insert_sites_all(pos, _offset[site]);
            for (unsigned int y=pos; y<pos+_offset[site]; y++) {
                if (_num_alleles == 1) allele = _alleles[0];
                else allele = _alleles[egglib_random_irand(_num_alleles)];
                for (unsigned int x=0; x<_data->get_nsam(); x++)  _data->set_sample(x, y, allele);
            }
            pos += _offset[site] + 1;
        }
    }
}
