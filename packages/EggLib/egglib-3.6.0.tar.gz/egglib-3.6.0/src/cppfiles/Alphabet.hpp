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

#ifndef EGGLIB_ALPHABET_HPP
#define EGGLIB_ALPHABET_HPP

#include <cstdlib>
#include <cstring>
#include <typeinfo>
#include "egglib.hpp"

namespace egglib {

    /// \brief Abstract base class for all alphabets
    class AbstractBaseAlphabet {
        private:
            AbstractBaseAlphabet(AbstractBaseAlphabet& src) {} ///< \brief No copy allowed
            AbstractBaseAlphabet& operator=(AbstractBaseAlphabet& src) {return *this;} ///< \brief No copy allowed

        protected:
            bool _lock; // whether the alphabet can be extended
            char * _name; // name of the alphabet
            unsigned int _len_name;
            char * _type;

        public:
            AbstractBaseAlphabet() {
                _name = (char *) malloc(sizeof(char));
                if (!_name) throw EGGMEM;
                _name[0] = '\0';
                _len_name = 1;
                _lock = false;
                _type = (char *) malloc(sizeof(char)* 10);
                if (!_type) throw EGGMEM;
                strcpy(_type, "undefined");
            } ///< \brief Constructor
            virtual ~AbstractBaseAlphabet() {
                if (_name) free(_name);
                if (_type) free(_type);
            } ///< \brief Destructor
            void set_name(const char * name) {
                if (strlen(name) > _len_name) {
                    _name = (char *) realloc(_name, (strlen(name) + 1) * sizeof(char));
                    if (!_name) throw EGGMEM;
                    _len_name = strlen(name);
                }
                strcpy(_name, name);
            } ///< \brief Set alphabet name
            void lock() { _lock = true; } ///< Lock the alphabet (not reversible)
            bool is_locked() const { return _lock; } ///< Tell if alphabet is locked
            const char * get_name() const { return _name; } ///< \brief Get alphabet name
            virtual unsigned int num_exploitable() const = 0; ///< \brief Number of exploitable alleles
            virtual unsigned int num_missing() const = 0; ///< \brief Number of missing alleles
            virtual const char * get_type() const { return _type; } ///< \brief Tells type of alphabet (because DataHolder returns a AbstractBaseAlphabet * which we cannot identify and because it is difficult to downcast it automatically)
            void set_type(const char * s) {
                _type = (char *) realloc(_type, (strlen(s) + 1) * sizeof(char));
                if (!_type) throw EGGMEM;
                strcpy(_type, s);
            } ///< \brief set type of alphabet
            virtual bool case_insensitive() const { return false; } ///< \brief Tells if case-insensitive
    };

    /// \brief Abstract base template for all alphabets
    template <class TYPE> class AbstractTemplateAlphabet : public AbstractBaseAlphabet {
        public:
            /// \brief Constructor
            AbstractTemplateAlphabet() {} ///< \brief Constructor
            virtual ~AbstractTemplateAlphabet() {} ///< \brief Destructor
            virtual const TYPE get_value(int code) = 0; ///< \brief Get the value of a given allele (throws EggArgumentValueError if out of range)
            virtual int get_code(const TYPE value) = 0; ///< \brief Get the code of a given allele and set the boolean (throws EggAlphabetError)
    };

    /// \brief Abstract base class for alphabets with a finite list of alleles
    template <class TYPE> class FiniteAlphabet : public AbstractTemplateAlphabet<TYPE> {
        protected:
            TYPE * _exploitable; ///< \brief List of exploitable alleles
            TYPE * _missing; ///< \brief List of missing alleles
            unsigned int _num_exploitable; ///< \brief Sub-sum of exploitable alleles
            unsigned int _num_missing; ///< \brief Sub-sum of missing allelesz

            /// \brief Look for an allele within the list, returns MISSINGDATA if not found
            virtual int _lookup(const TYPE all) {
                if (_num_missing > 0 && all == _missing[0]) return -1; // try first the first missing allele
                for (unsigned int i=0; i<_num_exploitable; i++) if (all == _exploitable[i]) return i; // try exploitable alleles
                for (unsigned int i=1; i<_num_missing; i++) if (all == _missing[i]) return -i-1; // try other missing alleles
                return MISSINGDATA;
            }

        public:
            /// \brief Constructor
            FiniteAlphabet() {
                _exploitable = NULL;
                _missing = NULL;
                _num_exploitable = 0;
                _num_missing = 0;
            }

            /// \brief Destructor
            virtual ~FiniteAlphabet() {
                if (_exploitable) free(_exploitable);
                if (_missing) free(_missing);
            }

            virtual unsigned int num_exploitable() const {return _num_exploitable;} ///< \brief Number of exploitable alleles
            virtual unsigned int num_missing() const {return _num_missing;} ///< \brief Number of missing alleles

            /// \brief Get the value of a given allele (throws EggArgumentValueError if out of range)
            virtual const TYPE get_value(int code) {
                if (code >= static_cast<int>(_num_exploitable) || code < - static_cast<int>(_num_missing)) {
                    throw EggArgumentValueError("allele code out of range");
                }
                if (code < 0) return _missing[-code-1];
                else return _exploitable[code];
            }

            /// \brief Get the code of a given allele and set the boolean (throws EggAlphabetError)
            virtual int get_code(const TYPE value) {
                int code = _lookup(value);
                if (code == MISSINGDATA) throw EggAlphabetError<TYPE>(this->_name, value);
                return code;
            }

            /// \brief Add a new exploitable allele (EggArgumentValueError if allele already exists)
            virtual void add_exploitable(const TYPE value) {
                if (AbstractBaseAlphabet::_lock) throw EggArgumentValueError("alphabet is locked");
                if (_lookup(value) != MISSINGDATA) throw EggArgumentValueError("allele already exists");
                _num_exploitable++;
                _exploitable = (TYPE *) realloc(_exploitable, _num_exploitable * sizeof(TYPE));
                if (!_exploitable) throw EGGMEM;
                _exploitable[_num_exploitable-1] = value;
            }

            /// \brief Add a new missing allele (EggArgumentValueError if allele already exists)
            virtual void add_missing(const TYPE value) {
                if (AbstractBaseAlphabet::_lock) throw EggArgumentValueError("alphabet is locked");
                if (_lookup(value) != MISSINGDATA) throw EggArgumentValueError("allele already exists");
                _num_missing++;
                _missing = (TYPE *) realloc(_missing, _num_missing * sizeof(TYPE));
                if (!_missing) throw EGGMEM;
                _missing[_num_missing-1] = value;
            }
    };

    /// \brief Case-insensitive version of FiniteAlphabet<char>
    class CaseInsensitiveCharAlphabet : public FiniteAlphabet<char> {
        protected:
            virtual int _lookup(const char);
        public:
            CaseInsensitiveCharAlphabet() {} ///< \brief Constructor
            virtual ~CaseInsensitiveCharAlphabet() {} ///< \brief Destructor
            virtual void add_exploitable(const char value); ///< \brief Add a new exploitable allele (EggArgumentValueError if allele already exists)
            virtual void add_missing(const char value); ///< \brief Add a new missing allele (EggArgumentValueError if allele already exists)
            virtual bool case_insensitive() const; ///< \brief Tells if case-insensitive
    };

    /// \brief Specific reimplementation of CaseInsensitiveCharAlphabet for DNA
    class DNAAlphabet : public CaseInsensitiveCharAlphabet {
        private:
            int * _codes; ///< \brief Code values for 77 characters in range
        protected:
            virtual int _lookup(const char); ///< \brief Get the code
        public:
            DNAAlphabet(); ///< \brief Constructor
            virtual ~DNAAlphabet(); ///< \brief Destructor
            virtual void add_exploitable(const char value); ///< \brief Not allowed
            virtual void add_missing(const char value); ///< \brief Not allowed
    };

    /// \brief Implementation of FiniteAlphabet handling const char *
    class StringAlphabet: public FiniteAlphabet<char *> {
        protected:
            unsigned int _max_len;
            unsigned int _res_exploitable;
            unsigned int _res_missing;
            unsigned int * _res_len_exploitable;
            unsigned int * _res_len_missing;

            virtual int _lookup(const char * value); ///< \brief String-based comparison of alleles
            virtual void _add(const char * const value, unsigned int& num,
                              unsigned int& res, unsigned int *& res_len, char **& list);
        public:
            StringAlphabet(); ///< \brief Constructor
            virtual ~StringAlphabet(); ///< \brief Destructor
            virtual void reset(); ///< reset lists of alleles but not name (don't actually erase memory)
            virtual int get_code(const char * value); ///< \brief Get code (string version)
            virtual void add_exploitable(const char * const value); ///< \brief Add a new exploitable allele
            virtual void add_missing(const char * const value); ///< \brief Add a new missing allele
            unsigned int longest_length() const; ///< \brief Gets the length of the longest allele (default 0)
    };

    /// \brief Specific implementation for codons
    class CodonAlphabet : public StringAlphabet {
        protected:
            virtual int _lookup(const char * all) {throw EggRuntimeError("this method is not intended to be used in this class");}
            int *** _codon_table; // size: 17*17*17*4 (including \0)

        public:
            CodonAlphabet(); /// \brief Constructor
            virtual ~CodonAlphabet(); /// \brief Destructor
            virtual unsigned int num_exploitable() const {return 64;} ///< \brief Number of exploitable alleles
            virtual unsigned int num_missing() const {return 4849;} ///< \brief Number of missing alleles
            virtual int get_code(const char * value); /// \brief Get the code of a given allele and set the boolean (throws EggAlphabetError)
            int get_code_from_bases(int, int, int); /// \brief Get the code of a given allele from three base codes
            virtual void add_exploitable(const char * value) {throw EggArgumentValueError("codon alphabet is locked");} /// not allowed
            virtual void add_missing(const char * value) {throw EggArgumentValueError("codon alphabet is locked");} /// not allowed
    };

    /// \brief Case-insensitive version of StringAlphabet
    class CaseInsensitiveStringAlphabet: public StringAlphabet {
        private:
            char * _cache;
            unsigned int _sz_cache;
        protected:
            virtual int _lookup(const char *); ///< \brief String-based comparison of alleles
        public:
            CaseInsensitiveStringAlphabet(); ///< \brief Constructor
            virtual ~CaseInsensitiveStringAlphabet(); ///< \brief Destructor
            virtual bool case_insensitive() const; ///< \brief Tells if case-insensitive
            virtual void add_exploitable(const char * const value); /// add an allele (to upper case)
            virtual void add_missing(const char * const value); /// add an allele (to upper case)
    };

    /// \brief Identical in functionality to StringAlphabet
    class CustomStringAlphabet : public StringAlphabet {
        public:
            CustomStringAlphabet() {} ///< \brief Constructor
            virtual ~CustomStringAlphabet() {} ///< \brief Destructor
    };

    /// \brief Alphabet with ranges of alleles (both expl and missing)
    class RangeAlphabet : public AbstractTemplateAlphabet<int> {
        protected:
            int _expl_beg; ///< \brief First exploitable allele
            int _expl_end; ///< \brief One after last exploitable allele
            int _miss_beg; ///< \brief First missing allele
            int _miss_end; ///< \brief One after last missing allele
            unsigned int _expl_num; ///< \brief Number of exploitable alleles
            unsigned int _miss_num; ///< \brief Number of missing alleles
        public:
            RangeAlphabet(); ///< \brief Constructor
            virtual ~RangeAlphabet() {} ///< \brief Destructor
            virtual unsigned int num_exploitable() const; ///< \brief Number of exploitable alleles
            virtual unsigned int num_missing() const; ///< \brief Number of missing alleles
            virtual int get_code(const int value); ///< \brief Get the code of a given allele (throws EggAlphabetError)
            virtual const int get_value(int code); ///< \brief Get the value of a given allele
            int first_exploitable() const; ///< \brief First exploitable allele
            int end_exploitable() const; ///< \brief One after last exploitable allele
            int first_missing() const; ///< \brief First missing allele
            int end_missing() const; ///< \brief One after last missing allele
            void set_exploitable(int, int); ///< \brief Set exploitable alleles range (first, one after last)
            void set_missing(int, int); ///< \brief Set missing alleles range (first, one after last)
            int min_value() const; ///< \brief The minimal value of both exploitable/missing range (0 by default)
            int max_value() const; ///< \brief The maximal value of both exploitable/missing range (0 by default)
    };

    DNAAlphabet& get_static_DNAAlphabet(); ///< \brief Provide access to unique, static object of DNAAlphabet
    CodonAlphabet& get_static_CodonAlphabet(); ///< \brief Provide access to unique, static object of CodonAlphabet
}

#endif
