/*
    Copyright 2015-2025 Stéphane De Mita, Mathieu Siol

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

#ifndef EGGLIB_STRUCTURE_HPP
#define EGGLIB_STRUCTURE_HPP

#include "egglib.hpp"

namespace egglib {

    class DataHolder;
    class StructureCluster;
    class StructurePopulation;
    class StructureIndiv;

   /** \brief Manage hierarchical group structure.
    *
    * \ingroup core
    *
    */
    class StructureHolder {
        private:
            StructureHolder(const StructureHolder& src) {}
            StructureHolder& operator=(const StructureHolder& src) { return *this; }
            void init();
            void free();
            unsigned int _ni;
            unsigned int _no;
            unsigned int _required;
            unsigned int _ploidy;
            signed _outgroup_haploid; // true if and only if outgroup is represented by a single haploid individual, regardless of ploidy
            unsigned int _num_clust;
            unsigned int _num_pop;
            unsigned int _num_indiv_i;
            unsigned int _num_indiv_o;
            StructureCluster ** _clusters;
            StructurePopulation ** _pops;
            StructureIndiv ** _indivs_i;
            StructureIndiv ** _indivs_o;
            unsigned int _num_clust_c;
            unsigned int _num_pop_c;
            unsigned int _num_indiv_i_c;
            unsigned int _num_indiv_o_c;
            unsigned int _iter_i_clu;
            unsigned int _iter_i_pop;
            unsigned int _iter_i_idv;
            unsigned int _iter_i_sam;
            unsigned int _iter_o_idv;
            unsigned int _iter_o_sam;
            unsigned int * _shuffle_pool_samples;
            bool * _shuffle_avail_samples;
            unsigned int _shuffle_avail_samples_n;
            unsigned int _shuffle_avail_samples_c;
            bool * _shuffle_avail_pops;
            unsigned int _shuffle_avail_pops_n;
            unsigned int _shuffle_avail_pops_c;
            bool * _shuffle_avail_indivs;
            unsigned int _shuffle_avail_indivs_n;
            unsigned int _shuffle_avail_indivs_c;
            int _shuffle_mode;
            bool _shuffle_lock;
            unsigned int _shuffle_pick_sample();
            StructureIndiv * _shuffle_pick_indiv();
            StructurePopulation * _shuffle_pick_pop();

        public:
            StructureHolder();
            ~StructureHolder();
            void reset(); ///< \brief Reset to defaults.
            unsigned int get_ploidy() const; ///< \brief Get ploidy. Default is UNKNOWN.
            bool outgroup_haploid() const; ///< \brief 1 if outgroup is haploid. Haploid outgroup means only 1 sample overall. Default is 0.

           /** \brief Ensure ploidy is consistent and optionally equal to passed value.
            *
            * Automatically called by get_structure(). Need to be called
            * if process_ingroup() and/or process_outgroup() is used.
            *
            * Value must be >0.
            *
            * Since 3.6, the outgroup is allowed to bypass this check if
            * it is represented by a single sample.
            *
            */
            void check_ploidy(unsigned int value=UNKNOWN);

           /** \brief Process labels from a DataHolder.
            *
            * Use UNKNOWN for any level to skip (but skipping
            * individuals is not the same as skipping clusters/pops).
            *
            */
            void get_structure(DataHolder& data, unsigned int lvl_clust, unsigned int lvl_pop, unsigned int lvl_indiv, unsigned int ploidy, bool skip_outgroup, const char * label_outgroup);
            void mk_dummy_structure(unsigned int ns, unsigned int ploidy); ///< \brief Make a structure with a single cluster/population (structure must be reset!)
            void dummy_add_pop(unsigned int ns); ///< \brief Add a population (can be called several times, but mk_dummy_structure first is required)
            StructureCluster * add_cluster(const char * label); ///< \brief Add a cluster with no samples in it
            StructurePopulation * add_population(const char * label, StructureCluster * cluster); ///< Add a population with no samples in it
            StructureIndiv * add_individual_ingroup(const char * label, StructurePopulation * population); ///< \brief Add an ingroup individual with no samples in it
            StructureIndiv * add_individual_outgroup(const char * label); ///< \brief Add an outgroup individual with no samples in it
            void add_sample_ingroup(unsigned int sam_idx, StructureIndiv * indiv); ///< \brief Add one ingroup sample
            void add_sample_outgroup(unsigned int sam_idx, StructureIndiv * indiv); ///< \brief Add one outgroup sample
            void process_ingroup(unsigned int idx, const char * lbl_clust, const char * lbl_pop, const char * lbl_indiv); ///< \brief Process one sample.
            void process_outgroup(unsigned int idx, const char * lbl_indiv); ///< \brief Process one sample.
            unsigned int num_clust() const; ///< \brief Number of clusters.
            unsigned int num_pop() const; ///< \brief Number of populations (total).
            unsigned int num_indiv_ingroup() const; ///< \brief Number of ingroup individuals (total).
            unsigned int num_indiv_outgroup() const; ///< \brief Number of outgroup individuals.
            const StructureCluster& get_cluster(unsigned int idx) const; ///< \brief Get a cluster.
            const StructurePopulation& get_population(unsigned int idx) const; ///< \brief Get a population.
            const StructureIndiv& get_indiv_ingroup(unsigned int idx) const; ///< \brief Get an ingroup individual.
            const StructureIndiv& get_indiv_outgroup(unsigned int idx) const; ///< \brief Get an outgroup individual.
            unsigned int get_ni() const; ///< \brief Get number of ingroup samples.
            unsigned int get_no() const; ///< \brief Get number of outgroup samples.
            unsigned int get_req() const; ///< \brief Get required number of samples.
            unsigned int get_pop_index(unsigned int) const; ///< \brief Index of the population containing this sample (default: MISSING).
            void copy(const StructureHolder& source); ///< \brief Copy data from source object
            const char * subset(const StructureHolder& source, char * popstring, char * cluststring, bool outgroup); ///< \brief Copy data from source object, only from specified populations and clusters (in \x1f-separated strings of labels) return empty string if success, otherwise first unknown label
            unsigned int init_i(); ///< \brief Reset the sample iterator for ingroup and iterate (UNKNOWN if iteration completed)
            unsigned int init_o(); ///< \brief Reset the sample iterator for outgroup and iterate (UNKNOWN if iteration completed)
            unsigned int iter_i(); ///< \brief Get next ingroup sample index (UNKNOWN if iteration completed)
            unsigned int iter_o(); ///< \brief Get next outgroup sample index (UNKNOWN if iteration completed)
            void shuffle_init(int mode); ///< Initialize pools for shuffle
            void shuffle(); ///< Shuffle labels
            void shuffle_restore(); ///< restore object to initial state after shuffling
    };

   /** \brief Manage a cluster. */
    class StructureCluster {

        private:
            StructureCluster() {}
            StructureCluster(const StructureCluster& src) {}
            StructureCluster& operator=(const StructureCluster& src) { return *this; }
            void init();
            void free();
            char * _label;
            unsigned int _label_n;
            unsigned int _label_r;
            unsigned int _num_pop;
            unsigned int _num_pop_c;
            unsigned int _num_indiv;
            unsigned int _num_indiv_c;
            StructurePopulation ** _pops;
            StructurePopulation ** _shuffle_backup_pops;
            unsigned int _shuffle_backup_pops_c;
            unsigned int _shuffle_backup_indivs_c;
            StructureIndiv ** _shuffle_pool_indivs;
            bool * _shuffle_avail_indivs;
            unsigned int _shuffle_num_indiv;
            unsigned int _shuffle_avail_indivs_n;
            unsigned int _shuffle_avail_indivs_c;
            unsigned int * _shuffle_pool_samples;
            bool * _shuffle_avail_samples;
            unsigned int _shuffle_num_samples;
            unsigned int _shuffle_avail_samples_n;
            unsigned int _shuffle_avail_samples_c;

        public:
            StructureCluster(const char * label);
            ~StructureCluster();
            void reset(const char * label); ///< \brief Restore defaults.
            StructurePopulation * add_pop(const char * label); ///< \brief Add and create a population.
            unsigned int num_pop() const; ///< \brief Number of populations.
            StructurePopulation& get_population(unsigned int idx) const; ///< \brief Get a population.
            const char * get_label() const; ///< \brief Get label.
            void shuffle_backup(); ///< backup pops
            void shuffle_restore(); ///< restore pops from backup
            void shuffle_init_sample_pool(); ///< initialize sample pool
            void shuffle_init_indiv_pool(); ///< initialize indiv pool
            void shuffle_reset_samples(); ///< reset sample pool booleans
            void shuffle_reset_indivs(); ///< reset indiv pool booleans
            unsigned int shuffle_pick_sample(); ///< pick a random sample in pool
            StructureIndiv * shuffle_pick_indiv(); ///< pick a random indiv
            void shuffle_replace_pop(unsigned int, StructurePopulation *); ///< replace a given population
    };

   /** \brief Manage a population. */
    class StructurePopulation {

        private:
            StructurePopulation() {}
            StructurePopulation(const StructurePopulation& src) {}
            StructurePopulation& operator=(const StructurePopulation& src) { return *this; }
            void init();
            void free();
            char * _label;
            unsigned int _label_n;
            unsigned int _label_r;
            unsigned int _num_indiv;
            unsigned int _num_indiv_c;
            StructureIndiv ** _indivs;
            StructureIndiv ** _shuffle_backup_indivs;
            unsigned int _shuffle_backup_indivs_c;
            unsigned int * _shuffle_pool_samples;
            bool * _shuffle_avail_samples;
            unsigned int _shuffle_num_samples;
            unsigned int _shuffle_avail_samples_n;
            unsigned int _shuffle_avail_samples_c;

        public:
            StructurePopulation(const char * label);
            ~StructurePopulation();
            void reset(const char * label); ///< \brief Restore defaults.
            StructureIndiv * add_indiv(const char * label); ///< \brief Add and create an individual.
            unsigned int num_indiv() const; ///< \brief Number of individuals.
            StructureIndiv& get_indiv(unsigned int idx) const; ///< \brief Get an individual.
            const char * get_label() const; ///< \brief Get label.
            void shuffle_backup(); ///< backup individuals
            void shuffle_restore(); ///< restore individuals from backup
            void shuffle_init_sample_pool(); ///< initialize sample pool
            void shuffle_reset_samples(); ///< reset sample pool booleans
            unsigned int shuffle_pick_sample(); ///< pick a random sample
            void shuffle_replace_indiv(unsigned int, StructureIndiv *); ///< replace a given individual
    };

   /** \brief Manage an individual. */
    class StructureIndiv {
        private:
            StructureIndiv() {}
            StructureIndiv(const StructureIndiv& src) {}
            StructureIndiv& operator=(const StructureIndiv& src) { return *this; }
            void init();
            void free();
            char * _label;
            unsigned int _label_n;
            unsigned int _label_r;
            unsigned int _num_sam;
            unsigned int _num_sam_c;
            unsigned int * _samples;
            unsigned int * _shuffle_backup_samples;
            unsigned int _shuffle_backup_samples_c;

        public:
            StructureIndiv(const char * label);
            ~StructureIndiv();
            void reset(const char * label); ///< \brief Restore defaults.
            unsigned int num_samples() const; ///< \brief Number of samples.
            void add_sample(unsigned int sample); ///< \brief Add a sample.
            unsigned int get_sample(unsigned int idx) const; ///< \brief Get a sample.
            void shuffle_replace_sample(unsigned int idx, unsigned int sample); ///< replace a sample value (used for shuffling)
            const char * get_label() const; ///< \brief Get label.
            void shuffle_backup(); ///< backup samples
            void shuffle_restore(); ///< restore samples from backup
    };
}

#endif
