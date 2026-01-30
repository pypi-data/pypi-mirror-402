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

#include "egglib.hpp"
#include "Structure.hpp"
#include "DataHolder.hpp"
extern "C" {
    #include "random.h"
}
#include <cstdlib>
#include <new>
#include <cstring>

namespace egglib {

    void StructureHolder::init() {
        _clusters = NULL;
        _pops = NULL;
        _indivs_i = NULL;
        _indivs_o = NULL;
        _num_clust_c = 0;
        _num_pop_c = 0;
        _num_indiv_i_c = 0;
        _num_indiv_o_c = 0;
        _shuffle_pool_samples = NULL;
        _shuffle_avail_samples = NULL;
        _shuffle_avail_samples_n = 0;
        _shuffle_avail_samples_c = 0;
        _shuffle_avail_pops = NULL;
        _shuffle_avail_pops_n = 0;
        _shuffle_avail_pops_c = 0;
        _shuffle_avail_indivs = NULL;
        _shuffle_avail_indivs_n = 0;
        _shuffle_avail_indivs_c = 0;
        _shuffle_lock = false;
        reset();
    }

    void StructureHolder::reset() {
        if (_shuffle_lock) throw EggArgumentValueError("cannot modify instance during shuffling");
        _ni = 0;
        _no = 0;
        _required = 0;
        _ploidy = UNKNOWN;
        _outgroup_haploid = 0;
        _num_clust = 0;
        _num_pop = 0;
        _num_indiv_i = 0;
        _num_indiv_o = 0;
    }

    void StructureHolder::free() {
        if (_pops) ::free(_pops);
        if (_indivs_i) ::free(_indivs_i);
        if (_indivs_o) {
            for (unsigned int i=0; i<_num_indiv_o_c; i++) if (_indivs_o[i]) delete(_indivs_o[i]);
            ::free(_indivs_o);
        }
        if (_clusters) {
            for (unsigned int i=0; i<_num_clust_c; i++) {
                if (_clusters[i]) delete _clusters[i];
            }
            ::free(_clusters);
        }
        if (_shuffle_pool_samples) ::free(_shuffle_pool_samples);
        if (_shuffle_avail_samples) ::free(_shuffle_avail_samples);
        if (_shuffle_avail_pops) ::free(_shuffle_avail_pops);
        if (_shuffle_avail_indivs) ::free(_shuffle_avail_indivs);
    }

    StructureHolder::StructureHolder() {
        init();
    }

    StructureHolder::~StructureHolder() {
        free();
    }

    void StructureHolder::copy(const StructureHolder& src) {
        reset();
        _ploidy = src._ploidy;
        _outgroup_haploid = src._outgroup_haploid;
        const StructureCluster * src_clu;
        const StructurePopulation * src_pop;
        const StructureIndiv * src_idv;
        StructureCluster * dst_clu;
        StructurePopulation * dst_pop;
        StructureIndiv * dst_idv;
        for (unsigned int i=0; i<src.num_clust(); i++) {
            src_clu = & src.get_cluster(i);
            dst_clu = add_cluster(src_clu->get_label());
            for (unsigned int j=0; j<src_clu->num_pop(); j++) {
                src_pop = & (src_clu->get_population(j));
                dst_pop = add_population(src_pop->get_label(), dst_clu);
                for (unsigned int k=0; k<src_pop->num_indiv(); k++) {
                    src_idv = & (src_pop->get_indiv(k));
                    dst_idv = add_individual_ingroup(src_idv->get_label(), dst_pop);
                    for (unsigned int m=0; m<_ploidy; m++) {
                        add_sample_ingroup(src_idv->get_sample(m), dst_idv);
                    }
                }
            }
        }
        for (unsigned int i=0; i<src.num_indiv_outgroup(); i++) {
            src_idv = & src.get_indiv_outgroup(i);
            dst_idv = add_individual_outgroup(src_idv->get_label());
            for (unsigned int j=0; j<src_idv->num_samples(); j++) { // use num_samples() instead of _ploidy to be generic with respect to _ploidy
                add_sample_outgroup(src_idv->get_sample(j), dst_idv);
            }
        }
    }

    const char * StructureHolder::subset(const StructureHolder& src, char * popstring, char * cluststring, bool outgroup) {
        bool flags[src._num_pop];
        memset(flags, 0, src._num_pop);
        char * str = strtok(popstring, "\x1f");
        unsigned int i, j, k, c, p;
        while (str) {
            for (c=0, i=0; c<src.num_clust(); c++) {
                for (p=0; p<src._clusters[c]->num_pop(); p++, i++) {
                    if (!strcmp(str, src._clusters[c]->get_population(p).get_label())) break;
                }
                if (p < src._clusters[c]->num_pop()) {
                    flags[i] |= 1;
                    break;
                }
            }
            if (c == src._num_clust) return str;
            str = strtok(NULL, "\x1f");
        }

        str = strtok(cluststring, "\x1f");
        while (str) {
            for (c=0, i=0; c<src.num_clust(); i+=src._clusters[c]->num_pop(), c++) {
                if (!strcmp(str, src._clusters[c]->get_label())) {
                    for (p=0; p<src._clusters[c]->num_pop(); p++, i++) flags[i] |= 1;
                    break;
                }
            }
            if (c == src._num_clust) return str;
            str = strtok(NULL, "\x1f");
        }

        reset();
        _ploidy = src._ploidy;

        StructureCluster * clu;
        StructurePopulation * pop;
        StructureIndiv * idv;
        for (c=0, i=0; c<src.num_clust(); c++) {
            clu = NULL;
            for (p=0; p<src._clusters[c]->num_pop(); p++, i++) {
                if (flags[i]) {
                    if (clu == NULL) clu = add_cluster(src._clusters[c]->get_label());
                    pop = add_population(src._clusters[c]->get_population(p).get_label(), clu);
                    for (j=0; j<src._clusters[c]->get_population(p).num_indiv(); j++) {
                        idv = add_individual_ingroup(src._clusters[c]->get_population(p).get_indiv(j).get_label(), pop);
                        for (k=0; k<_ploidy; k++) {
                            add_sample_ingroup(src._clusters[c]->get_population(p).get_indiv(j).get_sample(k), idv);
                        }
                    }
                }
            }
        }

        if (outgroup) {
            if (src._outgroup_haploid) _outgroup_haploid = 1;
            for (i=0; i<src._num_indiv_o; i++) {
                idv = add_individual_outgroup(src._indivs_o[i]->get_label());
                for (j=0; j<src._indivs_o[i]->num_samples(); j++) { // don't use _ploidy for the case of _outgroup_haploid
                    add_sample_outgroup(src._indivs_o[i]->get_sample(j), idv);
                }
            }
        }

        return "";
    }

    unsigned int StructureHolder::get_ploidy() const {
        return _ploidy;
    }

    bool StructureHolder::outgroup_haploid() const {
        return _outgroup_haploid;
    }

    void StructureHolder::mk_dummy_structure(unsigned int ns, unsigned int ploidy) {
        reset();
        _ploidy = ploidy;
        add_cluster("");
        dummy_add_pop(ns);
    }

    void StructureHolder::dummy_add_pop(unsigned int ns) {
        add_population(to_string(_num_pop), _clusters[0]);
        unsigned int i, j, c = 0;
        for (i=0; i<ns; i++) {
            add_individual_ingroup(to_string(_num_indiv_i), _pops[_num_pop-1]);
            for (j=0; j<_ploidy; j++) {
                add_sample_ingroup(c++, _indivs_i[_num_indiv_i-1]);
            }
        }
    }

    void StructureHolder::get_structure(DataHolder& data, unsigned int lvl_clust, unsigned int lvl_pop, unsigned int lvl_indiv, unsigned int ploidy, bool skip_outgroup, const char * outgroup_label) {
        const char * lbl_clust = "";
        const char * lbl_pop = "";
        const char * lbl_indiv = "";

        // process all samples
        for (unsigned int idx=0; idx<data.get_nsam(); idx++) {

            // check if sample is outgroup
            if (data.get_nlabels(idx) > 0 && !strcmp(data.get_label(idx, 0), outgroup_label)) {
                if (! skip_outgroup) {
                    if (data.get_nlabels(idx) > 2) throw EggArgumentValueError("too many labels for an outgroup sample");
                    if (lvl_indiv != UNKNOWN) {
                        if (data.get_nlabels(idx) < 2) continue; //throw EggArgumentValueError("an individual label is required for the outgroup");
                        lbl_indiv = data.get_label(idx, 1);
                        //if (!strcmp(lbl_indiv, outgroup_label)) throw EggArgumentValueError("outgroup label can only be used as first label");
                    }
                    else {
                        lbl_indiv = to_string(idx);
                    }
                    process_outgroup(idx, lbl_indiv);
                }
            }

            // process an ingroup sample
            else {
                if (lvl_clust != UNKNOWN) {
                    if (lvl_clust >= data.get_nlabels(idx)) continue; // throw EggArgumentValueError("not enough labels for sample");
                    lbl_clust = data.get_label(idx, lvl_clust);
                    //if (!strcmp(lbl_clust, outgroup_label)) throw EggArgumentValueError("outgroup label can only be used as first label");
                }
                else {
                    lbl_clust = "";
                }
                if (lvl_pop != UNKNOWN) {
                    if (lvl_pop >= data.get_nlabels(idx)) continue; // throw EggArgumentValueError("not enough labels for sample");
                    lbl_pop = data.get_label(idx, lvl_pop);
                    //if (!strcmp(lbl_pop, outgroup_label)) throw EggArgumentValueError("outgroup label can only be used as first label");
                }
                else {
                    lbl_pop = lbl_clust;
                }
                if (lvl_indiv != UNKNOWN) {
                    if (lvl_indiv >= data.get_nlabels(idx)) continue; // throw EggArgumentValueError("not enough labels for sample");
                    lbl_indiv = data.get_label(idx, lvl_indiv);
                    //if (!strcmp(lbl_indiv, outgroup_label)) throw EggArgumentValueError("outgroup label can only be used as first label");
                }
                else {
                    lbl_indiv = to_string(idx);
                }
                process_ingroup(idx, lbl_clust, lbl_pop, lbl_indiv);
            }
        }

        // check and set ploidy
        if (lvl_indiv == UNKNOWN) _ploidy = 1;
        else check_ploidy(ploidy);
    }

    void StructureHolder::process_ingroup(unsigned int sam_idx, const char * lbl_clust, const char * lbl_pop, const char * lbl_indiv) {
        // all iterator go backward for better performance if samples are sorted by groups

        // find cluster #############
        StructureCluster * clust = NULL;
        for (unsigned int idx_clust=_num_clust; idx_clust-- > 0; ) {
            if (!strcmp(lbl_clust, _clusters[idx_clust]->get_label())) {
                clust = _clusters[idx_clust];
                break;
            }
        }

        // if cluster not found, create it
        if (clust == NULL) {
            clust = add_cluster(lbl_clust);
        }

        // find pop #############
        StructurePopulation * pop = NULL;
        for (unsigned int idx_pop=clust->num_pop(); idx_pop-- > 0; ) {
            if (!strcmp(lbl_pop, clust->get_population(idx_pop).get_label())) {
                pop = & clust->get_population(idx_pop);
                break;
            }
        }

        // if pop not found, create it
        if (pop == NULL) {
            pop = add_population(lbl_pop, clust);
        }

        // find indiv #############
        // check all ingroup
        StructureIndiv * indiv = NULL;
        for (unsigned int idx_indiv=pop->num_indiv(); idx_indiv-- > 0; ) {
            if (!strcmp(pop->get_indiv(idx_indiv).get_label(), lbl_indiv)) {
                indiv = & pop->get_indiv(idx_indiv);
                break;
            }
        }

        // if not found, create it
        if (indiv == NULL) {
            indiv = add_individual_ingroup(lbl_indiv, pop);
        }

        // add sample
        add_sample_ingroup(sam_idx, indiv);
    }

    void StructureHolder::process_outgroup(unsigned int sam_idx, const char * lbl_indiv) {

        // find indiv
        StructureIndiv * indiv = NULL;
        for (unsigned int idx_indiv=_num_indiv_o; idx_indiv-- > 0; ) {
            if (!strcmp(_indivs_o[idx_indiv]->get_label(), lbl_indiv)) {
                indiv = _indivs_o[idx_indiv];
                break;
            }
        }

        // else create individual
        if (indiv == NULL) {
            indiv = add_individual_outgroup(lbl_indiv);
        }

        // add sample
        add_sample_outgroup(sam_idx, indiv);
    }

    void StructureHolder::add_sample_ingroup(unsigned int sam_idx, StructureIndiv * indiv) {
        _ni++;
        if (sam_idx+1 > _required) _required = sam_idx + 1;
        indiv->add_sample(sam_idx);
    }

    void StructureHolder::add_sample_outgroup(unsigned int sam_idx, StructureIndiv * indiv) {
        if (_no == 0) _outgroup_haploid = 1;
        else if (_no == 1) _outgroup_haploid = 0;
        _no++;
        if (sam_idx+1 > _required) _required = sam_idx + 1;
        indiv->add_sample(sam_idx);
    }

    StructureCluster * StructureHolder::add_cluster(const char * label) {
        _num_clust++;
        if (_num_clust > _num_clust_c) {
            _clusters = (StructureCluster **) realloc(_clusters, _num_clust * sizeof(StructureCluster *));
            if (!_clusters) throw EGGMEM;
            _clusters[_num_clust-1] = new(std::nothrow) StructureCluster(label);
            if (!_clusters[_num_clust-1]) throw EGGMEM;
            _num_clust_c = _num_clust;
        }
        else {
            _clusters[_num_clust-1]->reset(label);
        }
        return _clusters[_num_clust-1];
    }

    StructurePopulation * StructureHolder::add_population(const char * label, StructureCluster * cluster) {
        _num_pop++;
        if (_num_pop > _num_pop_c) {
            _pops = (StructurePopulation **) realloc(_pops, _num_pop * sizeof(StructurePopulation *));
            if (!_pops) throw EGGMEM;
            _num_pop_c = _num_pop;
        }
        _pops[_num_pop-1] = cluster->add_pop(label);
        return _pops[_num_pop-1];
    }

    StructureIndiv * StructureHolder::add_individual_ingroup(const char * label, StructurePopulation * population) {
        _num_indiv_i++;
        if (_num_indiv_i > _num_indiv_i_c) {
            _indivs_i = (StructureIndiv **) realloc(_indivs_i, _num_indiv_i * sizeof(StructureIndiv *));
            if (!_indivs_i) throw EGGMEM;
            _num_indiv_i_c = _num_indiv_i;
        }
        _indivs_i[_num_indiv_i-1] = population->add_indiv(label);
        return _indivs_i[_num_indiv_i-1];
    }

    StructureIndiv * StructureHolder::add_individual_outgroup(const char * label) {
        _num_indiv_o++;
        if (_num_indiv_o > _num_indiv_o_c) {
            _indivs_o = (StructureIndiv **) realloc(_indivs_o, _num_indiv_o * sizeof(StructureIndiv *));
            if (!_indivs_o) throw EGGMEM;
            _indivs_o[_num_indiv_o-1] = new(std::nothrow) StructureIndiv(label);
            if (!_indivs_o[_num_indiv_o-1]) throw EGGMEM;
            _num_indiv_o_c = _num_indiv_o;
        }
        else {
            _indivs_o[_num_indiv_o-1]->reset(label);
        }
        return _indivs_o[_num_indiv_o-1];
    }

    void StructureHolder::check_ploidy(unsigned int value) {
        _ploidy = value;
        if (_ploidy == UNKNOWN) {
            if (_num_indiv_i > 0) _ploidy = _indivs_i[0]->num_samples();
            else if (_num_indiv_o > 0) _ploidy = _indivs_o[0]->num_samples();
        }
        for (unsigned int i=0; i<_num_indiv_i; i++) {
            if (_indivs_i[i]->num_samples() != _ploidy) throw EggPloidyError();
        }
        if (!_outgroup_haploid) {
            for (unsigned int i=0; i<_num_indiv_o; i++) {
                if (_indivs_o[i]->num_samples() != _ploidy) throw EggPloidyError();
            }
        }
    }

    unsigned int StructureHolder::num_clust() const {
        return _num_clust;
    }

    unsigned int StructureHolder::num_pop() const {
        return _num_pop;
    }

    unsigned int StructureHolder::num_indiv_ingroup() const {
        return _num_indiv_i;
    }

    unsigned int StructureHolder::num_indiv_outgroup() const {
        return _num_indiv_o;
    }

    const StructureCluster& StructureHolder::get_cluster(unsigned int idx) const {
        return * _clusters[idx];
    }

    const StructurePopulation& StructureHolder::get_population(unsigned int idx) const {
        return * _pops[idx];
    }

    const StructureIndiv& StructureHolder::get_indiv_ingroup(unsigned int idx) const {
        return * _indivs_i[idx];
    }

    const StructureIndiv& StructureHolder::get_indiv_outgroup(unsigned int idx) const {
        return * _indivs_o[idx];
    }

    unsigned int StructureHolder::get_ni() const {
        return _ni;
    }

    unsigned int StructureHolder::get_no() const {
        return _no;
    }

    unsigned int StructureHolder::get_req() const {
        return _required;
    }

    unsigned int StructureHolder::get_pop_index(unsigned int idx) const {
        for (unsigned int i=0; i<_num_pop; i++) {
            for (unsigned int j=0; j<_pops[i]->num_indiv(); j++) {
                for (unsigned int k=0; k<_ploidy; k++) {
                    if (idx == _pops[i]->get_indiv(j).get_sample(k)) return i;
                }
            }
        }
        return MISSING;
    }

    unsigned int StructureHolder::init_i() {
        _iter_i_clu = 0;
        _iter_i_pop = 0;
        _iter_i_idv = 0;
        _iter_i_sam = 0;
        return iter_i();
    }

    unsigned int StructureHolder::iter_i() {
        if (_iter_i_clu == _num_clust) return UNKNOWN;
        if (_iter_i_pop == _clusters[_iter_i_clu]->num_pop()) {
            _iter_i_clu++;
            _iter_i_pop = 0;
            _iter_i_idv = 0;
            _iter_i_sam = 0;
            return iter_i();
        }
        if (_iter_i_idv == _clusters[_iter_i_clu]->get_population(_iter_i_pop).num_indiv()) {
            _iter_i_pop++;
            _iter_i_idv = 0;
            _iter_i_sam = 0;
            return iter_i();
        }
        if (_iter_i_sam == _ploidy) {
            _iter_i_idv++;
            _iter_i_sam = 0;
            return iter_i();
        }
        _iter_i_sam++;
        return _clusters[_iter_i_clu]->get_population(_iter_i_pop).get_indiv(_iter_i_idv).get_sample(_iter_i_sam-1);
    }

    unsigned int StructureHolder::init_o() {
        _iter_o_idv = 0;
        _iter_o_sam = 0;
        return iter_o();
    }

    unsigned int StructureHolder::iter_o() {
        if (_iter_o_sam == 1 && _outgroup_haploid) return UNKNOWN;
        if (_iter_o_idv == _num_indiv_o) return UNKNOWN;
        if (_iter_o_sam == _ploidy) {
            _iter_o_idv++;
            _iter_o_sam = 0;
            return iter_o();
        }
        _iter_o_sam++;
        return _indivs_o[_iter_o_idv]->get_sample(_iter_o_sam-1);
    }

    void StructureHolder::shuffle_init(int mode) {
        _shuffle_lock = true;
        switch (mode) {
            case 0: // it
                // create sample pool
                _shuffle_avail_samples_n = _ni;
                if (_ni > _shuffle_avail_samples_c) {
                    _shuffle_pool_samples = (unsigned int *) realloc(_shuffle_pool_samples, _ni * sizeof(unsigned int));
                    if (!_shuffle_pool_samples) throw EGGMEM;
                    _shuffle_avail_samples = (bool *) realloc(_shuffle_avail_samples, _ni * sizeof(bool));
                    if (!_shuffle_avail_samples) throw EGGMEM;
                    _shuffle_avail_samples_c = _ni;
                }
                // populate pool
                for (unsigned int i=0; i<_num_indiv_i; i++) {
                    for (unsigned int j=0; j<_ploidy; j++) {
                        _shuffle_pool_samples[i*_ploidy+j] = _indivs_i[i]->get_sample(j);
                    }
                    // backup samples
                    _indivs_i[i]->shuffle_backup();
                }
                break;

            case 1: // ic
                // create sample pools at cluster level
                for (unsigned int i=0; i<_num_clust; i++) _clusters[i]->shuffle_init_sample_pool();
                // backup samples
                for (unsigned int i=0; i<_num_indiv_i; i++) _indivs_i[i]->shuffle_backup();
                break;

            case 2: // is
                // create sample pools at population level
                for (unsigned int i=0; i<_num_pop; i++) _pops[i]->shuffle_init_sample_pool();
                // backup samples
                for (unsigned int i=0; i<_num_indiv_i; i++) _indivs_i[i]->shuffle_backup();
                break;

            case 3: // st
                // create indiv pool (only flags are needed, addresses already available)
                _shuffle_avail_indivs_n = _num_indiv_i;
                if (_num_indiv_i > _shuffle_avail_indivs_c) {
                    _shuffle_avail_indivs = (bool *) realloc(_shuffle_avail_indivs, _shuffle_avail_indivs_n * sizeof(bool));
                    if (!_shuffle_avail_indivs) throw EGGMEM;
                    _shuffle_avail_indivs_c = _num_indiv_i;
                }
                // ask populations to backup their individuals
                for (unsigned int i=0; i<_num_pop; i++) _pops[i]->shuffle_backup();
                break;

            case 4: // sc
                // create indiv pools at cluster level
                for (unsigned int i=0; i<_num_clust; i++) _clusters[i]->shuffle_init_indiv_pool();
                // ask populations to backup their individuals
                for (unsigned int i=0; i<_num_pop; i++) _pops[i]->shuffle_backup();

            case 5: // ct
                // create pop pool (only flags are needed, addresses already available)
                _shuffle_avail_pops_n = _num_pop;
                if (_num_pop > _shuffle_avail_pops_c) {
                    _shuffle_avail_pops = (bool *) realloc(_shuffle_avail_pops, _num_pop * sizeof(bool));
                    if (!_shuffle_avail_pops) throw EGGMEM;
                    _shuffle_avail_pops_c = _num_pop;
                }
                // ask clusters to backup their populations
                for (unsigned int i=0; i<_num_clust; i++) _clusters[i]->shuffle_backup();
                break;
            
            
            default:
                throw EggRuntimeError("invalid value for mode");
        }
        _shuffle_mode = mode;
    }

    void StructureHolder::shuffle() {
        // reset bools
        switch (_shuffle_mode) {
            case 0:
                _shuffle_avail_samples_n = _ni;
                for (unsigned int i=0; i<_ni; i++) _shuffle_avail_samples[i] = true;
                break;
            case 1:
                for (unsigned int i=0; i<_num_clust; i++) _clusters[i]->shuffle_reset_samples();
                break;
            case 2:
                for (unsigned int i=0; i<_num_pop; i++) _pops[i]->shuffle_reset_samples();
                break;
            case 3:
                _shuffle_avail_indivs_n = _num_indiv_i;
                for (unsigned int i=0; i<_num_indiv_i; i++) _shuffle_avail_indivs[i] = true;
                break;
            case 4:
                for (unsigned int i=0; i<_num_clust; i++) _clusters[i]->shuffle_reset_indivs();
                break;
            case 5:
                _shuffle_avail_pops_n = _num_pop;
                for (unsigned int i=0; i<_num_pop; i++) _shuffle_avail_pops[i] = true;
                break;
        }

        // shuffle samples
        switch (_shuffle_mode) {
            case 0: // it: shuffle samples in total
                for (unsigned int i=0; i<_num_indiv_i; i++) {
                    for (unsigned int j=0; j<_ploidy; j++) {
                        _indivs_i[i]->shuffle_replace_sample(j, _shuffle_pick_sample());
                    }
                }
                break;

            case 1: // ic: shuffle samples in clusters
                for (unsigned int i=0; i<_num_clust; i++) {
                    for (unsigned int j=0; j<_clusters[i]->num_pop(); j++) {
                        for (unsigned int k=0; k<_clusters[i]->get_population(j).num_indiv(); k++) {
                            for (unsigned int p=0; p<_ploidy; p++) {
                                _clusters[i]->get_population(j).get_indiv(k).shuffle_replace_sample(p, _clusters[i]->shuffle_pick_sample());
                            }
                        }
                    }
                }
                break;

            case 2: // is: shuffle samples in populations
                for (unsigned int i=0; i<_num_clust; i++) {
                    for (unsigned int j=0; j<_clusters[i]->num_pop(); j++) {
                        for (unsigned int k=0; k<_clusters[i]->get_population(j).num_indiv(); k++) {
                            for (unsigned int p=0; p<_ploidy; p++) {
                                _clusters[i]->get_population(j).get_indiv(k).shuffle_replace_sample(p, _clusters[i]->get_population(j).shuffle_pick_sample());
                            }
                        }
                    }
                }
                break;

            case 3: // st: shuffle individuals in total
                for (unsigned int i=0; i<_num_clust; i++) {
                    for (unsigned int j=0; j<_clusters[i]->num_pop(); j++) {
                        for (unsigned int k=0; k<_clusters[i]->get_population(j).num_indiv(); k++) {
                            _clusters[i]->get_population(j).shuffle_replace_indiv(k, _shuffle_pick_indiv());
                        }
                    }
                }
                break;

            case 4: // sc: shuffle individuals in clusters
                for (unsigned int i=0; i<_num_clust; i++) {
                    for (unsigned int j=0; j<_clusters[i]->num_pop(); j++) {
                        for (unsigned int k=0; k<_clusters[i]->get_population(j).num_indiv(); k++) {
                            _clusters[i]->get_population(j).shuffle_replace_indiv(k, _clusters[i]->shuffle_pick_indiv());
                        }
                    }
                }
                break;

            case 5: // ct: shuffle populations in clusters
                for (unsigned int i=0; i<_num_clust; i++) {
                    for (unsigned int j=0; j<_clusters[i]->num_pop(); j++) {
                        _clusters[i]->shuffle_replace_pop(j, _shuffle_pick_pop());
                    }
                }
                break;
        }
    }

    unsigned int StructureHolder::_shuffle_pick_sample() {
        #ifdef DEBUG
        if (_shuffle_avail_samples_n == 0) throw EggRuntimeError("no more samples to pick from structure");
        #endif
        unsigned int X = egglib_random_irand(_shuffle_avail_samples_n);
        for (unsigned int i=0; i<_ni; i++) {
            if (_shuffle_avail_samples[i]) {
                if (X == 0) {
                    _shuffle_avail_samples[i] = false;
                    _shuffle_avail_samples_n--;
                    return _shuffle_pool_samples[i];
                }
                X--;
            }
        }
        throw EggRuntimeError("bug in StructureHolder::_shuffle_pick_sample");
    }

    StructureIndiv * StructureHolder::_shuffle_pick_indiv() {
        #ifdef DEBUG
        if (_shuffle_avail_indivs_n == 0) throw EggRuntimeError("no more individuals to pick from structure");
        #endif
        unsigned int X = egglib_random_irand(_shuffle_avail_indivs_n);
        for (unsigned int i=0; i<_num_indiv_i; i++) {
            if (_shuffle_avail_indivs[i]) {
                if (X == 0) {
                    _shuffle_avail_indivs[i] = false;
                    _shuffle_avail_indivs_n--;
                    return _indivs_i[i];
                }
                X--;
            }
        }
        throw EggRuntimeError("bug in StructureHolder::_shuffle_pick_indiv");
    }

    StructurePopulation * StructureHolder::_shuffle_pick_pop() {
        #ifdef DEBUG
        if (_shuffle_avail_pops_n == 0) throw EggRuntimeError("no more populations to pick from structure");
        #endif
        unsigned int X = egglib_random_irand(_shuffle_avail_pops_n);
        for (unsigned int i=0; i<_num_pop; i++) {
            if (_shuffle_avail_pops[i]) {
                if (X == 0) {
                    _shuffle_avail_pops[i] = false;
                    _shuffle_avail_pops_n--;
                    return _pops[i];
                }
                X--;
            }
        }
        throw EggRuntimeError("bug in StructureHolder::_shuffle_pick_pop");
    }

    void StructureHolder::shuffle_restore() {
        _shuffle_lock = false;
        switch (_shuffle_mode) {
            case 0: // it: samples in total
            case 1: // ic: samples in clusters
            case 2: // is: samples in pops
                for (unsigned int i=0; i<_num_indiv_i; i++) _indivs_i[i]->shuffle_restore();
                break;
            case 3: // st: indivs in total
            case 4: // sc: indivs in clusters
                for (unsigned int i=0; i<_num_pop; i++) _pops[i]->shuffle_restore();
                break;
            case 5: // ct: pops in total
                for (unsigned int i=0; i<_num_clust; i++) _clusters[i]->shuffle_restore();
        }
    }

    // *** ///

    void StructureCluster::init() {
        _num_pop_c = 0;
        _num_indiv_c = 0;
        _pops = NULL;
        _label = (char *) malloc(1 * sizeof(char));
        if (!_label) throw EGGMEM;
        _label_n = 0;
        _label_r = 1;
        _label[0] = '\0';
        _shuffle_backup_pops = NULL;
        _shuffle_backup_pops_c = 0;
        _shuffle_pool_indivs = NULL;
        _shuffle_avail_indivs = NULL;
        _shuffle_avail_indivs_n = 0;
        _shuffle_avail_indivs_c = 0;
        _shuffle_pool_samples = NULL;
        _shuffle_avail_samples = NULL;
        _shuffle_avail_samples_n = 0;
        _shuffle_avail_samples_c = 0;
    }

    void StructureCluster::reset(const char * label) {
        _label_n = strlen(label) + 1;
        if (_label_n > _label_r) {
            _label = (char *) realloc(_label, _label_n * sizeof(char));
            if (!_label) throw EGGMEM;
            _label_r = _label_n;
        }
        strcpy(_label, label);
        _num_pop = 0;
        _num_indiv = 0;
    }

    void StructureCluster::free() {
        if (_pops) {
            for (unsigned int i=0; i<_num_pop_c; i++) {
                if (_pops[i]) delete _pops[i];
            }
            ::free(_pops);
        }
        if (_label) ::free(_label);
        if (_shuffle_backup_pops) ::free(_shuffle_backup_pops);
        if (_shuffle_pool_indivs) ::free(_shuffle_pool_indivs);
        if (_shuffle_avail_indivs) ::free(_shuffle_avail_indivs);
        if (_shuffle_pool_samples) ::free(_shuffle_pool_samples);
        if (_shuffle_avail_samples) ::free(_shuffle_avail_samples);
    }

    StructureCluster::StructureCluster(const char * label) {
        init();
        reset(label);
    }

    StructureCluster::~StructureCluster() {
        free();
    }

    StructurePopulation * StructureCluster::add_pop(const char * label) {
        _num_pop++;
        if (_num_pop > _num_pop_c) {
            _pops = (StructurePopulation **) realloc(_pops, _num_pop * sizeof(StructurePopulation *));
            if (!_pops) throw EGGMEM;
            _pops[_num_pop-1] = new(std::nothrow) StructurePopulation(label);
            if (!_pops[_num_pop-1]) throw EGGMEM;
            _num_pop_c = _num_pop;
        }
        else {
            _pops[_num_pop-1]->reset(label);
        }
        return _pops[_num_pop-1];
    }

    unsigned int StructureCluster::num_pop() const {
        return _num_pop;
    }

    StructurePopulation& StructureCluster::get_population(unsigned int idx) const {
        return * _pops[idx];
    }

    const char * StructureCluster::get_label() const {
        return _label;
    }

    void StructureCluster::shuffle_init_sample_pool() {
        unsigned int c = 0;
        _shuffle_num_samples = 0;
        for (unsigned int i=0; i<_num_pop; i++) {
            for (unsigned int j=0; j<_pops[i]->num_indiv(); j++) {
                _shuffle_num_samples += _pops[i]->get_indiv(j).num_samples();
                if (_shuffle_num_samples > _shuffle_avail_samples_c) {
                    _shuffle_pool_samples = (unsigned int *) realloc(_shuffle_pool_samples, _shuffle_num_samples * sizeof(unsigned int));
                    if (!_shuffle_pool_samples) throw EGGMEM;
                    _shuffle_avail_samples = (bool *) realloc(_shuffle_avail_samples, _shuffle_num_samples * sizeof(bool));
                    if (!_shuffle_avail_samples) throw EGGMEM;
                    _shuffle_avail_samples_c = _shuffle_num_samples;
                }
                // populating pool
                for (unsigned int k=0; k<_pops[i]->get_indiv(j).num_samples(); k++) {
                    _shuffle_pool_samples[c++] = _pops[i]->get_indiv(j).get_sample(k);
                }
            }
        }
    }

    void StructureCluster::shuffle_init_indiv_pool() {
        unsigned int c = 0;
        _shuffle_num_indiv = 0;
        for (unsigned int i=0; i<_num_pop; i++) {
            _shuffle_num_indiv += _pops[i]->num_indiv();
            if (_shuffle_num_indiv > _shuffle_avail_indivs_c) {
                _shuffle_pool_indivs = (StructureIndiv **) realloc(_shuffle_pool_indivs, _shuffle_num_indiv * sizeof(StructureIndiv *));
                if (!_shuffle_pool_indivs) throw EGGMEM;
                _shuffle_avail_indivs = (bool *) realloc(_shuffle_avail_indivs, _shuffle_num_indiv * sizeof(bool));
                if (!_shuffle_avail_indivs) throw EGGMEM;
                _shuffle_avail_indivs_c = _shuffle_num_indiv;
            }
            // populating pool
            for (unsigned int j=0; j<_pops[i]->num_indiv(); j++) {
                _shuffle_pool_indivs[c++] = & _pops[i]->get_indiv(j);
            }
        }
    }

    void StructureCluster::shuffle_backup() {
        if (_num_pop > _shuffle_backup_pops_c) {
            _shuffle_backup_pops = (StructurePopulation **) realloc(_shuffle_backup_pops, _num_pop * sizeof(StructurePopulation *));
            if (!_shuffle_backup_pops) throw EGGMEM;
            _shuffle_backup_pops_c = _num_pop;
        }
        for (unsigned int i=0; i<_num_pop; i++) _shuffle_backup_pops[i] = _pops[i];
    }

    void StructureCluster::shuffle_restore() {
        for (unsigned int i=0; i<_num_pop; i++) _pops[i] = _shuffle_backup_pops[i];
    }

    void StructureCluster::shuffle_reset_samples() {
        _shuffle_avail_samples_n = _shuffle_num_samples;
        for (unsigned int i=0; i<_shuffle_num_samples; i++) _shuffle_avail_samples[i] = true;
    }

    void StructureCluster::shuffle_reset_indivs() {
        _shuffle_avail_indivs_n = _shuffle_num_indiv;
        for (unsigned int i=0; i<_shuffle_num_indiv; i++) _shuffle_avail_indivs[i] = true;
    }

    unsigned int StructureCluster::shuffle_pick_sample() {
        #ifdef DEBUG
        if (_shuffle_avail_samples_n == 0) throw EggRuntimeError("no more samples to pick from cluster");
        #endif
        unsigned int X = egglib_random_irand(_shuffle_avail_samples_n);
        for (unsigned int i=0; i<_shuffle_num_samples; i++) {
            if (_shuffle_avail_samples[i]) {
                if (X == 0) {
                    _shuffle_avail_samples[i] = false;
                    _shuffle_avail_samples_n--;
                    return _shuffle_pool_samples[i];
                }
                X--;
            }
        }
        throw EggRuntimeError("bug in StructureCluster::shuffle_pick_sample");
    }

    StructureIndiv * StructureCluster::shuffle_pick_indiv() {
        #ifdef DEBUG
        if (_shuffle_avail_indivs_n == 0) throw EggRuntimeError("no more individuals to pick from cluster");
        #endif
        unsigned int X = egglib_random_irand(_shuffle_avail_indivs_n);
        for (unsigned int i=0; i<_shuffle_num_indiv; i++) {
            if (_shuffle_avail_indivs[i]) {
                if (X == 0) {
                    _shuffle_avail_indivs[i] = false;
                    _shuffle_avail_indivs_n--;
                    return _shuffle_pool_indivs[i];
                }
                X--;
            }
        }
        throw EggRuntimeError("bug in StructureHolder::_shuffle_pick_indiv");
    }

    void StructureCluster::shuffle_replace_pop(unsigned int idx, StructurePopulation * pop) {
        #ifdef DEBUG
        if (idx >= _num_pop) throw EggArgumentValueError("invalid population index");
        #endif
        _pops[idx] = pop;
    }

    // *** //

    void StructurePopulation::init() {
        _num_indiv_c = 0;
        _indivs = NULL;
        _label = (char *) malloc(1 * sizeof(char));
        if (!_label) throw EGGMEM;
        _label_n = 0;
        _label_r = 1;
        _label[0] = '\0';
        _shuffle_backup_indivs = NULL;
        _shuffle_backup_indivs_c = 0;
        _shuffle_pool_samples = NULL;
        _shuffle_avail_samples = NULL;
        _shuffle_avail_samples_n = 0;
        _shuffle_avail_samples_c = 0;
    }

    void StructurePopulation::reset(const char * label) {
        _label_n = strlen(label) + 1;
        if (_label_n > _label_r) {
            _label = (char *) realloc(_label, _label_n * sizeof(char));
            if (!_label) throw EGGMEM;
            _label_r = _label_n;
        }
        strcpy(_label, label);
        _num_indiv = 0;
    }

    void StructurePopulation::free() {
        if (_indivs) {
            for (unsigned int i=0; i<_num_indiv_c; i++) {
                if (_indivs[i]) delete _indivs[i];
            }
            ::free(_indivs);
        }
        if (_label) ::free(_label);
        if (_shuffle_backup_indivs) ::free(_shuffle_backup_indivs);
        if (_shuffle_pool_samples) ::free(_shuffle_pool_samples);
        if (_shuffle_avail_samples) ::free(_shuffle_avail_samples);
    }

    StructurePopulation::StructurePopulation(const char * label) {
        init();
        reset(label);
    }

    StructurePopulation::~StructurePopulation() {
        free();
    }

    StructureIndiv * StructurePopulation::add_indiv(const char * label) {
        _num_indiv++;
        if (_num_indiv > _num_indiv_c) {
            _indivs = (StructureIndiv **) realloc(_indivs, _num_indiv * sizeof(StructureIndiv *));
            if (!_indivs) throw EGGMEM;
            _indivs[_num_indiv-1] = new(std::nothrow) StructureIndiv(label);
            if (!_indivs[_num_indiv-1]) throw EGGMEM;
            _num_indiv_c = _num_indiv;
        }
        else {
            _indivs[_num_indiv-1]->reset(label);
        }
        return _indivs[_num_indiv-1];
    }

    unsigned int StructurePopulation::num_indiv() const {
        return _num_indiv;
    }

    StructureIndiv& StructurePopulation::get_indiv(unsigned int idx) const {
        return * _indivs[idx];
    }

    const char * StructurePopulation::get_label() const {
        return _label;
    }

    void StructurePopulation::shuffle_backup() {
        if (_num_indiv > _shuffle_backup_indivs_c) {
            _shuffle_backup_indivs = (StructureIndiv **) realloc(_shuffle_backup_indivs, _num_indiv * sizeof(StructureIndiv *));
            if (!_shuffle_backup_indivs) throw EGGMEM;
            _shuffle_backup_indivs_c = _num_indiv;
        }
        for (unsigned int i=0; i<_num_indiv; i++) _shuffle_backup_indivs[i] = _indivs[i];
    }

    void StructurePopulation::shuffle_restore() {
        for (unsigned int i=0; i<_num_indiv; i++) _indivs[i] = _shuffle_backup_indivs[i];
    }

    void StructurePopulation::shuffle_init_sample_pool() {
        unsigned int c = 0;
        _shuffle_num_samples = 0;
        for (unsigned int i=0; i<_num_indiv; i++) {
            _shuffle_num_samples += _indivs[i]->num_samples();
            if (_shuffle_num_samples > _shuffle_avail_samples_c) {
                _shuffle_pool_samples = (unsigned int *) realloc(_shuffle_pool_samples, _shuffle_num_samples * sizeof(unsigned int));
                if (!_shuffle_pool_samples) throw EGGMEM;
                _shuffle_avail_samples = (bool *) realloc(_shuffle_avail_samples, _shuffle_num_samples * sizeof(bool));
                if (!_shuffle_avail_samples) throw EGGMEM;
                _shuffle_avail_samples_c = _shuffle_num_samples;
            }
            // populating pool
            for (unsigned int j=0; j<_indivs[i]->num_samples(); j++) {
                _shuffle_pool_samples[c++] = _indivs[i]->get_sample(j);
            }
        }
    }

    void StructurePopulation::shuffle_reset_samples() {
        _shuffle_avail_samples_n = _shuffle_num_samples;
        for (unsigned int i=0; i<_shuffle_num_samples; i++) _shuffle_avail_samples[i] = true;
    }

    unsigned int StructurePopulation::shuffle_pick_sample() {
        #ifdef DEBUG
        if (_shuffle_avail_samples_n == 0) throw EggRuntimeError("no more samples to pick from population");
        #endif
        unsigned int X = egglib_random_irand(_shuffle_avail_samples_n);
        for (unsigned int i=0; i<_shuffle_num_samples; i++) {
            if (_shuffle_avail_samples[i]) {
                if (X == 0) {
                    _shuffle_avail_samples[i] = false;
                    _shuffle_avail_samples_n--;
                    return _shuffle_pool_samples[i];
                }
                X--;
            }
        }
        throw EggRuntimeError("bug in StructurePopulation::shuffle_pick_sample");
    }

    void StructurePopulation::shuffle_replace_indiv(unsigned int idx, StructureIndiv * indiv) {
        #ifdef DEBUG
        if (idx >= _num_indiv) throw EggArgumentValueError("invalid individual index");
        #endif
        _indivs[idx] = indiv;
    }

    // *** //

    void StructureIndiv::init() {
        _num_sam_c = 0;
        _samples = NULL;
        _label = (char *) malloc(1 * sizeof(char));
        if (!_label) throw EGGMEM;
        _label_n = 0;
        _label_r = 1;
        _label[0] = '\0';
        _shuffle_backup_samples = NULL;
        _shuffle_backup_samples_c = 0;
    }

    void StructureIndiv::reset(const char * label) {
        _label_n = strlen(label) + 1;
        if (_label_n > _label_r) {
            _label = (char *) realloc(_label, _label_n * sizeof(char));
            if (!_label) throw EGGMEM;
            _label_r = _label_n;
        }
        strcpy(_label, label);
        _num_sam = 0;
    }

    void StructureIndiv::free() {
        if (_samples) ::free(_samples);
        if (_label) ::free(_label);
        if (_shuffle_backup_samples) ::free(_shuffle_backup_samples);
    }

    StructureIndiv::StructureIndiv(const char * label) {
        init();
        reset(label);
    }

    StructureIndiv::~StructureIndiv() {
        free();
    }

    void StructureIndiv::add_sample(unsigned int index) {
        _num_sam++;
        if (_num_sam > _num_sam_c) {
            _samples = (unsigned int *) realloc(_samples, _num_sam * sizeof(unsigned int));
            if (!_samples) throw EGGMEM;
            _num_sam_c = _num_sam;
        }
        _samples[_num_sam-1] = index;
    }

    unsigned int StructureIndiv::num_samples() const {
        return _num_sam;
    }

    unsigned int StructureIndiv::get_sample(unsigned int idx) const {
        return _samples[idx];
    }

    const char * StructureIndiv::get_label() const {
        return _label;
    }

    void StructureIndiv::shuffle_backup() {
        if (_num_sam > _shuffle_backup_samples_c) {
            _shuffle_backup_samples = (unsigned int *) realloc(_shuffle_backup_samples, _num_sam * sizeof(unsigned int));
            if (!_shuffle_backup_samples) throw EGGMEM;
            _shuffle_backup_samples_c = _num_sam;
        }
        for (unsigned int i=0; i<_num_sam; i++) {
            _shuffle_backup_samples[i] = _samples[i];
        }
    }

    void StructureIndiv::shuffle_restore() {
        for (unsigned int i=0; i<_num_sam; i++) {
            _samples[i] = _shuffle_backup_samples[i];
        }
    }

    void StructureIndiv::shuffle_replace_sample(unsigned int idx, unsigned int sample) {
        #ifdef DEBUG
        if (idx >= _num_sam) throw EggRuntimeError("invalid sample index");
        #endif        
        _samples[idx] = sample;
    }
}
