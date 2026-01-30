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

#include "egglib.hpp"
#include "Fasta.hpp"
#include "Alphabet.hpp"
#include <cstdlib>
#include <sstream>
#include <cstring>

namespace egglib {

    //////
    // constructors helpers and memory management
    FastaParser::FastaParser() {
        _init();
    }

    FastaParser::~FastaParser() {
        close();
        _free();
    }

    void FastaParser::clear() {
        _free();
        _init();
    }

    void FastaParser::_init() {
        _lname = 1;
        _lname_r = 1;
        _name = (char *) malloc(1 * sizeof(char));
        if (!_name) throw EGGMEM;
        _name[0] = '\0';
        _lseq = 0;
        _lseq_r = 0;
        _seq = NULL;
        _nlabels = 0;
        _nlabels_r = 0;
        _labels = NULL;
        _labels_r = NULL;
        _labels_n = NULL;
        _good = false;
        _stream = NULL;
        _lfname_r = 1;
        _fname = (char *) malloc(1 * sizeof(char));
        if (!_fname) throw EGGMEM;
        _fname[0] = '\0';
        _currline = 0;
        _alph = NULL;
    }

    void FastaParser::_free() {
        if (_name) free(_name);
        if (_seq) free(_seq);
        if (_labels) free(_labels);
        if (_labels_r) free(_labels_r);
        if (_labels_n) free(_labels_n);
        if (_fname) free(_fname);
    }

    void FastaParser::_reset_sequence() {
        _lname = 1;
        _name[0] = '\0';
        _lseq = 0;
        _nlabels = 0;
    }

    void FastaParser::reserve(unsigned int ln, unsigned int ls, unsigned int ng, unsigned int lf) {
        if ((ln+1) > _lname_r) {
            _name = (char *) realloc(_name, (ln+1) * sizeof(char));
            if (!_name) throw EGGMEM;
            _lname_r = ln+1;
        }

        if (ls > _lseq_r) {
            _seq = (char *) realloc(_seq, ls * sizeof(char));
            if (!_seq) throw EGGMEM;
            _lseq_r = ls;
        }

        if (ng > _nlabels_r) {
            _labels = (char **) realloc(_labels, ng * sizeof(char *));
            if (!_labels) throw EGGMEM;
            _labels_r = (unsigned int *) realloc(_labels_r, ng * sizeof(unsigned int *));
            if (!_labels_r) throw EGGMEM;
            _labels_n = (unsigned int *) realloc(_labels_n, ng * sizeof(unsigned int *));
            if (!_labels_n) throw EGGMEM;
            for (unsigned int i=_nlabels_r; i<ng; i++) {
                _labels[i] = (char *) malloc(10 * sizeof(char));
                if (!_labels[i]) throw EGGMEM;
                _labels_r[i] = 10;
                _labels_n[i] = 0;
            }
            _nlabels_r = ng;
        }

        if ((lf+1) > _lfname_r) {
            _fname = (char *) realloc(_fname, (lf+1) * sizeof(char));
            if (!_fname) throw EGGMEM;
            _lfname_r = lf+1;
        }
    }

    //////
    // stream management
    void FastaParser::open_file(const char * fname, FiniteAlphabet<char>& a, unsigned int offset) {

        // reset memory
        close();

        // save file name
        unsigned int lfname = strlen(fname);
        if ((lfname+1) > _lfname_r) {
            _fname = (char *) realloc(_fname, (lfname+1) * sizeof(char));
            if (!_fname) throw EGGMEM;
            _lfname_r = lfname+1;
        }
        strcpy(_fname, fname);

        // open stream
        _stream = &_fstream;
        _fstream.open(fname);
        if (!_fstream.is_open()) {
            throw EggOpenFileError(fname);
        }

        // apply offset
        if (offset > 0) {
            _fstream.seekg(offset);
        }

        // set alphabet
        _alph = &a;

        // check that first character is '>'
        _check();
    }

    void FastaParser::set_stream(std::istream& stream, FiniteAlphabet<char>& a) {

        // reset memory
        close();

        // save file name
        if (9 > _lfname_r) {
            _fname = (char *) realloc(_fname, 9 * sizeof(char));
            if (!_fname) throw EGGMEM;
            _lfname_r = 9;
        }
        strcpy(_fname, "<stream>");

        // check stream
        _stream = &stream;
        if (! _stream->good()) {
            throw EggArgumentValueError("FastaParser: invalid stream (not good for reading)");
        }

        // set alphabet
        _alph = &a;

        // check that first character is '>'
        _check();
    }

    void FastaParser::set_string(const char * str, FiniteAlphabet<char>& a) {

        // reset memory
        close();

        // save file name
        if (9 > _lfname_r) {
            _fname = (char *) realloc(_fname, 9 * sizeof(char));
            if (!_fname) throw EGGMEM;
            _lfname_r = 9;
        }
        strcpy(_fname, "<string>");

        // check stream
        _sstream.clear();
        _sstream.str(str);
        _stream = & _sstream;
        if (! _stream->good()) {
            throw EggArgumentValueError("FastaParser: invalid stream (cannot read string for some reasong)");
        }

        // set alphabet
        _alph = &a;

        // check that first character is '>'
        _check();
    }

    void FastaParser::_check() {
        char c;
        _stream->get(c);
        if (_stream->eof()) {
            _good = false;
            return;
        }
        if (_stream->fail()) {
            throw EggFormatError(_fname, _currline+1, "fasta", "cannot read data from file");
        }
        if (c!='>') {
            throw EggFormatError(_fname, _currline+1, "fasta", "a '>' character is expected here");
        }
        _good = true;
    }

    void FastaParser::close() {
        _reset_sequence();
        _stream = NULL;
        if (_fstream.is_open()) _fstream.close();
        _fstream.clear();
        _good = false;
        _fname[0] = '\0';
        _currline = 0;
    }

    bool FastaParser::good() const {
        return _good;
    }

    //////
    // reading data
    void FastaParser::read_sequence(bool groups, DataHolder * dest, char label_marker, char label_separator) {

        // add a sequence
        unsigned int index = 0;

        if (dest) {
            index = dest->get_nsam();
            dest->set_nsam(index + 1);
        }
        else _reset_sequence();

        // gets the name until a group mark or the end of the line is met
        char ch;
        bool readinglabel = false;

        while (true) {
            _stream->get(ch);
            if (_stream->eof()) throw EggFormatError(_fname, _currline+1, "fasta", "unexpected end of file - file might be truncated");
            if (_stream->fail()) throw EggFormatError(_fname, _currline+1, "fasta", "invalid header (stream error)");

            if (ch=='\n') {
                _currline++;
                break;
            }
            if (ch=='\r') continue;
            if (ch==label_marker && groups) {
                readinglabel = true;
                break;
            }
            if (ch != '\r') {
                if (dest) dest->name_appendch(index, ch);
                else _name_append(ch);
            }
        }

        // process group labels
        if (readinglabel) {
            unsigned int num_labels = 0;
            bool read_one;

            // read all items
            while (true) {
                if (dest) {
                    dest->add_uninit_label(index);
                    num_labels++;
                }
                else _add_label();
                read_one = false;

                while (true) {
                    _stream->get(ch);
                    read_one |= true;
                    if (ch == '\r') continue;
                    if (ch == '\n') {
                        if (!read_one) throw EggFormatError(_fname, _currline+1, "fasta", "empty group label");
                        _currline++;
                        break;
                    }
                    if (ch == label_separator) {
                        if (!read_one) throw EggFormatError(_fname, _currline+1, "fasta", "empty group label");
                        break;
                    }
                    if (dest) dest->append_label(index, num_labels-1, ch);
                    else _append_last_label(ch);
                }
                if (ch == '\n') break;
            }

            // check that there are no empty labels
            
            for (unsigned int i=0; i<num_labels; i++) {
                if (dest) {
                    if (strlen(dest->get_label(index, i)) == 0) {
                        throw EggFormatError(_fname, _currline+1, "fasta", "empty group label");
                    }
                }
            }
        }

        // gets the sequence
        unsigned int ls = 0;
        while (true) {
            _stream->get(ch);
            if (_stream->eof()) { _good = false; break; }
            if (_stream->fail()) throw EggFormatError(_fname, _currline+1, "fasta", "sequence (stream error)");
            if (ch == '>') break;
            if (ch != '\n' && ch != '\r') {
                ls++;
                if (dest) {
                    dest->set_nsit_sample(index, ls);
                    dest->set_sample(index, ls-1, _alph->get_code(ch));
                }
                else _seq_append(ch);
            }
            if (ch == '\n') _currline++;
        }
    }

    void FastaParser::read_all(bool groups, DataHolder& dest, char label_marker, char label_separator) {
        while (_good) {
            read_sequence(groups, &dest, label_marker, label_separator);
        }
    }

    void FastaParser::_name_append(char c) {
        _lname++;
        if (_lname > _lname_r) {
            _name = (char *) realloc(_name, _lname * sizeof(char));
            if (!_name) throw EGGMEM;
            _lname_r = _lname;
        }
        _name[_lname-2] = c;
        _name[_lname-1] = '\0';
    }

    void FastaParser::_seq_append(char c) {
        _lseq++;
        if (_lseq > _lseq_r) {
            _seq = (char *) realloc(_seq, _lseq * sizeof(char));
            if (!_seq) throw EGGMEM;
            _lseq_r = _lseq;
        }
        _seq[_lseq-1] = c;
    }

    void FastaParser::_add_label() {
        _nlabels++;
        if (_nlabels > _nlabels_r) {
            _labels = (char **) realloc(_labels, _nlabels * sizeof(char *));
            if (!_labels) throw EGGMEM;
            _labels_n = (unsigned int *) realloc(_labels_n, _nlabels * sizeof(unsigned int));
            if (!_labels_n) throw EGGMEM;
            _labels_r = (unsigned int *) realloc(_labels_r, _nlabels * sizeof(unsigned int));
            if (!_labels_r) throw EGGMEM;
            _nlabels_r = _nlabels;

            _labels[_nlabels-1] = (char *) malloc(10 * sizeof(char));
            if (!_labels[_nlabels-1]) throw EGGMEM;
            _labels_r[_nlabels-1] = 10;
            _labels_n[_nlabels-1] = 0;
        }
        _labels[_nlabels-1][0] = '\0';
    }

    void FastaParser::_append_last_label(char ch) {
        _labels_n[_nlabels-1]++;
        if (_labels_n[_nlabels-1] > _labels_r[_nlabels-1]) {
            _labels[_nlabels-1] = (char *) realloc(_labels[_nlabels-1], (_labels_r[_nlabels-1] + 10) * sizeof(char));
            if (!_labels[_nlabels-1]) throw EGGMEM;
            _labels_r[_nlabels-1] += 10;
        }
        _labels[_nlabels-1][_labels_n[_nlabels-1]-1] = ch;
        _labels[_nlabels-1][_labels_n[_nlabels-1]] = '\0';
    }

    //////
    // Accessors

    const char * FastaParser::name() const {
        return _name;
    }

    unsigned int FastaParser::ls() const {
        return _lseq;
    }

    char FastaParser::ch(unsigned int index) const {
        return _seq[index];
    }

    unsigned int FastaParser::nlabels() const {
        return _nlabels;
    }

    const char * FastaParser::label(unsigned int index) const {
        return _labels[index];
    }

    //////
    // Independent parsing functions

    void read_fasta_file(const char * fname, bool groups, DataHolder& dest, FiniteAlphabet<char>& a) {
        FastaParser fp;
        fp.open_file(fname, a);
        fp.read_all(groups, dest);
    }

    void read_fasta_string(const std::string str, bool groups, DataHolder& dest, FiniteAlphabet<char>& a) {
        std::istringstream stream(str);
        FastaParser fp;
        fp.set_stream(stream, a);
        fp.read_all(groups, dest);
    }

    // Formatting class

    FastaFormatter::FastaFormatter() : BaseFormatter() {
        defaults(); // load default config parameters
    }

    void FastaFormatter::defaults() {
        set_first();
        set_last();
        set_labels();
        set_linelength();
    }

    FastaFormatter::~FastaFormatter() {
    }

    void FastaFormatter::set_first(unsigned int first) {
        _first = first;
    }

    void FastaFormatter::set_last(unsigned int last) {
        _last = last;
    }

    void FastaFormatter::set_labels(bool labels) {
        _labels = labels;
    }

    void FastaFormatter::set_linelength(unsigned int linelength) {
        _linelength = linelength;
    }

    std::string FastaFormatter::write_string(const DataHolder& src, AbstractBaseAlphabet& alph) {
        _cache_stream = _stream;
        _stream = & _sstream;
        _sstream.str("");
        write(src, alph);
        _stream = _cache_stream;
        return _sstream.str();
    }

    void FastaFormatter::write(const DataHolder& src, AbstractBaseAlphabet& alph) {

        if (!_stream->good()) {
            throw EggRuntimeError("cannot export data data: invalid stream (not good for writing)");
        }
        FiniteAlphabet<char> * alph_C = NULL;
        StringAlphabet * alph_S = NULL;
        if (!strcmp(alph.get_type(), "char") | !strcmp(alph.get_type(), "DNA")) {
            alph_C = static_cast<FiniteAlphabet<char>*>(&alph);
        }
        else {
            if (!strcmp(alph.get_type(), "string") | !strcmp(alph.get_type(), "codons")) {
                alph_S = static_cast<StringAlphabet*>(&alph);
            }
            else throw EggArgumentValueError("alphabet not supported for fasta exporting");
        }

        // variables
        unsigned int nsam = src.get_nsam();
        unsigned int ls = 0;
        bool is_matrix = src.get_is_matrix();
        if (is_matrix) ls = src.get_nsit_all();

        // export specified sequences
        for (unsigned int i=_first; i<nsam && i<=_last; i++) {
            // export header
            (*_stream) << ">" << src.get_name(i);
            if (_labels) {
                if (src.get_nlabels(i) > 0) {
                    (*_stream) << "@";
                    if (strchr(src.get_label(i, 0), ',')) throw EggArgumentValueError("cannot export data data: label contains label separator");
                    (*_stream) << src.get_label(i, 0);
                    for (unsigned int j=1; j<src.get_nlabels(i); j++) {
                        if (strchr(src.get_label(i, j), ',')) throw EggArgumentValueError("cannot export data data: label contains label separator");
                        (*_stream) << "," << src.get_label(i, j);
                    }
                }
            }
            (*_stream) << std::endl;

            // export sequence
            std::streampos c0 = _stream->tellp(), c1;
            if (!is_matrix) ls = src.get_nsit_sample(i);

            for (unsigned int j=0; j<ls; j++) {
                if (alph_C != NULL) (*_stream) << alph_C->get_value(src.get_sample(i, j));
                else (*_stream) << alph_S->get_value(src.get_sample(i, j));
                if (_linelength!=0) {
                    if (_stream->tellp() - c0 >= _linelength) {
                        (*_stream) << std::endl;
                        c0 = _stream->tellp();
                    }
                }
            }
            if (_stream->tellp() - c0 != 0 || _linelength == 0) (*_stream) << std::endl;
        }

        if (!_stream->good()) {
            throw EggRuntimeError("error while writing fasta data");
        }
    }
}
