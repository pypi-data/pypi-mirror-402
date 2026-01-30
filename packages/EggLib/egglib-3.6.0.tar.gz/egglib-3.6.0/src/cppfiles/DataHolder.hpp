/*
    Copyright 2012-2021 Stéphane De Mita, Mathieu Siol

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

#ifndef EGGLIB_DATAHOLDER_HPP
#define EGGLIB_DATAHOLDER_HPP

#include "egglib.hpp"

namespace egglib {

    class Coalesce;
    class AbstractBaseAlphabet;

   /** \brief Minimal reimplementation of a vector<int>
    * \ingroup core
    */
    class VectorInt {
        private:
            int * _values;
            unsigned int _num;
            unsigned int _res;
            void copy(const VectorInt& src);

        public:
            VectorInt(); ///< Constructor (default: 0 values)
            virtual ~VectorInt(); ///< Destructor
            VectorInt(const VectorInt& src); ///< Copy constructor
            VectorInt& operator=(const VectorInt& src); ///< Copy assignment operator
            void set_num_values(unsigned int n); ///< Set the number of vqlues (values are not initialized)
            unsigned int get_num_values() const; ///< Get the number of values
            void set_item(unsigned int i, int value); ///< Set a value
            int get_item(unsigned int i) const; ///< Get a value
            void clear(); ///< Release memory
    };

   /** \brief Integer data set
    * \ingroup core
    */
    class DataHolder {
        protected:
            void _init();
            void _alloc_ns(unsigned int ns);
            void _alloc_nlabels_all(unsigned int nlabels);
            void _alloc_nlabels_sample(unsigned int sam, unsigned int nlabels);
            void _alloc_ls_all(unsigned int ls);
            void _alloc_ls_sample(unsigned int i, unsigned int ls);
            void _alloc_ln(unsigned int i, unsigned int ln);
            void _free();
            void _copy(const DataHolder& src);
            void _nsam_helper(unsigned int nsam);
            bool _is_matrix;
            unsigned int _ns;
            unsigned int _ns_r;
            unsigned int _ls_all;
            unsigned int * _ls_sample;     // size: _ns_r
            unsigned int * _ls_r;          // size: _ns_r
            unsigned int * _ln;            // size: _ns_r
            unsigned int * _ln_r;          // size: _ns_r
            unsigned int * _nlabels;            // size: _ns_r
            unsigned int * _nlabels_r;          // size: _ns_r
            unsigned int ** _labels_l;        // size: _ns_r * _nlabels_r[i]
            unsigned int ** _labels_r;        // size: _ns_r * _nlabels_r[i]
            int ** _data;                  // size: _ns_r x _ls_r[i]
            char ** _names;                // size: _ns_r x _ln_r[i]
            char *** _labels;      // size: _ns_r x _nlabels_r[i]
            unsigned int _n_temp_string;
            char * _temp_string;
            unsigned int _strip_list_n;
            unsigned int _strip_list_c;
            int * _strip_list;

        public:
            DataHolder(bool is_matrix = false); ///< resizers must be called
            DataHolder(const DataHolder& src);  ///< reserved memory not copied
            DataHolder& operator=(const DataHolder& src); ///< reserved memory not copied
            virtual ~DataHolder(); ///< destructor
            bool valid_phyml_names() const; ///< check if names valid for phyml
            void set_is_matrix(bool flag); ///< if flag is True, the user must ensure that all ls are the same
            bool get_is_matrix() const; ///< check is_matrix flag
            void reserve(unsigned int ns, unsigned int ln, unsigned int nlabels, unsigned int ls); ///< allocate memory (0 is allowed)
            unsigned int get_nsam() const; ///< get ns
            void set_nsam(unsigned int nsam); ///< new data not initialised (except names)
            unsigned int get_nsit_all() const; ///< only for matrix objects
            unsigned int get_nsit_sample(unsigned int sam) const; ///< only for non-matrix objects
            void set_nsit_all(unsigned int val); ///< for all objects
            void set_nsit_sample(unsigned int sam, unsigned int val); ///< only for non-matrix objects
            void insert_sites_all(unsigned int pos, unsigned int num); ///< insert sites before pos (new sites not initialised) use egglib::MAX for the end
            void insert_sites_sample(unsigned int sam, unsigned int pos, unsigned int num); ///< for one sample of a non-matrix object
            unsigned int get_nlabels(unsigned int) const; ///< number of labels of sample
            void set_nlabels(unsigned int, unsigned int); ///< new values are empty
            void set_all_nlabels(unsigned int); ///< set_nlabels() for all samples
            int get_sample(unsigned int sam, unsigned int sit) const; ///< get a datum
            void set_sample(unsigned int sam, unsigned int sit, int value); ///< set a datum
            const char * get_label(unsigned int sam, unsigned int lvl) const; ///< get a label
            void set_label(unsigned int sam, unsigned int lvl, const char * label); ///< set a label
            void add_label(unsigned int sam, const char * label); ///< add a sample and set it
            void add_uninit_label(unsigned int sam); ///< add an uninitialized label (for FASTA parsing) [not API]
            void append_label(unsigned int sam, unsigned int lvl, char ch); ///< add a character to a label
            const char * get_name(unsigned int sam) const; ///< get a name
            void set_name(unsigned int sam, const char * name); ///< set a name
            void name_appendch(unsigned int sam, char ch); ///< append a character to a name
            void name_append(unsigned int sam, const char * ch); ///< add a string to a name
            void del_sample(unsigned int sam); ///< delete a sample (if last sample, set ls to 0)
            void del_sites_all(unsigned int start, unsigned int stop); ///< delete a range of sites (stop position is not removed) oob values are supported
            void del_sites_sample(unsigned int sam, unsigned int start, unsigned int stop); ///< for one sample of a non-matrix
            void reset(bool is_matrix); ///< reset data
            void clear(bool is_matrix); ///< clear memory and re-initialise
            unsigned int find(unsigned int sam, VectorInt& motif, unsigned int start=0, unsigned int stop=MAX) const; ///< find start position of a motif (the hit cannot overlap with stop), egglib::MAX if not found
            bool is_equal() const; ///< for non-matrix objects
            void change_case(bool lower, int index_i, int start_i, int stop_i, AbstractBaseAlphabet& alph); ///< \brief Upper/lower case conversion
            void strip_clear(); ///< \brief Clear the list of strip codes
            void strip_add(int); ///< \brief Add a code to the list of strip codes
            void strip(unsigned int, bool, bool); ///< \brief Strip a sequence
    };

   /** \brief Insert non-varying sites within alignments
    *
    * \ingroup core
    *
    * This class allows to add non-varying sites within an alignment at
    * given positions. The following method must be called in that order
    * after building the object: (i) load(), (ii) set_length(), (iii)
    * either set_position(), set_round_position(), or get_positions() (without mixing them),
    * (iv) optionally set_allele(), (iv) set_random(), and (v) intersperse().
    */
    class IntersperseAlign {
        public:
            IntersperseAlign(); ///< constructor
            ~IntersperseAlign(); ///< destructor
            void load(DataHolder& data); ///< load data set
            void set_length(unsigned int length); ///< desired length of the final alignment
            void set_position(unsigned int index, double position); ///< set the position of a site of the original alignment (between 0 and 1 and >= previous position)
            void set_round_position(unsigned int index, unsigned int position); ///< set the position of a site of the original alignment (between 0 and size of the final alignment minus one and >= previous position)
            void get_positions(const Coalesce& coalesce); ///< get positions of the alignment from the Coalesce object that generated it
            void set_num_alleles(unsigned int num); ///< set number of possible alleles (>0)
            void set_allele(unsigned int index, int allele); ///< set an allele
            void intersperse(bool round_positions = true); ///< perform interspersing

        protected:
            DataHolder * _data;
            unsigned int _nsites;
            unsigned int _length;
            unsigned int _res_positions;
            double * _positions;
            unsigned int * _round_positions;
            unsigned int * _offset;
            unsigned int _final_offset;
            unsigned int _num_alleles;
            unsigned int _res_alleles;
            int * _alleles;

        private:
            IntersperseAlign(const IntersperseAlign& src) {}
            IntersperseAlign& operator=(const IntersperseAlign& src) { return * this; }
    };
}

#endif
