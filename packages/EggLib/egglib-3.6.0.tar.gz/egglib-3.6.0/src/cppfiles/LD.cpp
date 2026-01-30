/*
    Copyright 2009-2021 Stéphane De Mita, Mathieu Siol

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
#include "LD.hpp"
#include "FreqHolder.hpp"
#include "Genotypes.hpp"
#include <cstdlib>
#include <cmath>

namespace egglib {

    PairwiseLD::PairwiseLD() {
        reset();
        _map1 = NULL;
        _map2 = NULL;
        _a1c = 0;
        _a2c = 0;
        _pc = NULL;
        _p1 = NULL;
        _p2 = NULL;
        _p = NULL;
    }

    PairwiseLD::~PairwiseLD() {
        for (unsigned int i=0; i<_a1c; i++) if (_p[i]) free(_p[i]);
        if (_pc) free(_pc);
        if (_p1) free(_p1);
        if (_p2) free(_p2);
        if (_p) free(_p);
        if (_map1) free(_map1);
        if (_map2) free(_map2);
    }

    void PairwiseLD::reset() {
        _D = 0.0;
        _Dp = 0.0;
        _r = 0.0;
        _rsq = 0.0;
        _a1 = 0;
        _a2 = 0;
        _a1e = 0;
        _a2e = 0;
        _neff = 0;
    }

    void PairwiseLD::_alloc(unsigned int a1i, unsigned int a2i) {
        _a1 = a1i;
        _a2 = a2i;
        if (_a1 > _a1c) {
            _p1 = (unsigned int *) realloc(_p1, _a1 * sizeof(unsigned int));
            if (!_p1) throw EGGMEM;

            _pc = (unsigned int *) realloc(_pc, _a1 * sizeof(unsigned int));
            if (!_pc) throw EGGMEM;

            _p = (unsigned int **) realloc(_p, _a1 * sizeof(unsigned int *));
            if (!_p) throw EGGMEM;

            _map1 = (unsigned int *) realloc(_map1, _a1 * sizeof(unsigned int));
            if (!_map1) throw EGGMEM;

            for (unsigned int i=_a1c; i<_a1; i++) {
                _pc[i] = 0;
                _p[i] = NULL;
            }
            _a1c = _a1;
        }
        if (_a2 > _a2c) {
            _p2 = (unsigned int *) realloc(_p2, _a2 * sizeof(unsigned int));
            if (!_p2) throw EGGMEM;
            _map2 = (unsigned int *) realloc(_map2, _a2 * sizeof(unsigned int));
            if (!_map2) throw EGGMEM;
            _a2c = _a2;
        }
        for (unsigned int i=0; i<_a1; i++) {
            if (_a2 > _pc[i]) {
                _p[i] = (unsigned int *) realloc(_p[i], _a2 * sizeof(unsigned int));
                if (!_p[i]) throw EGGMEM;
                _pc[i] = _a2;
            }
        }
    }

    bool PairwiseLD::process(const SiteHolder& site1, const SiteHolder& site2,
            const FreqHolder& frq1, const FreqHolder& frq2, 
            StructureHolder& struc, unsigned min_n, double max_maj) {

        reset();

        // initialize frequencies
        _alloc(frq1.num_alleles(), frq2.num_alleles());

        for (unsigned int i=0; i<_a1; i++) _p1[i] = 0;
        for (unsigned int i=0; i<_a2; i++) _p2[i] = 0;
        for (unsigned int i=0; i<_a1; i++) {
            for (unsigned int j=0; j<_a2; j++) _p[i][j] = 0;
        }

        // compute frequencies
        for (unsigned int i=struc.init_i(); i!=UNKNOWN; i=struc.iter_i()) {
            if (site1.get_sample(i) < 0 || site2.get_sample(i) < 0) continue;
            unsigned int a1 = frq1.get_allele_index(site1.get_sample(i));
            unsigned int a2 = frq2.get_allele_index(site2.get_sample(i));
            _p1[a1]++;
            _p2[a2]++;
            _p[a1][a2]++;
            _neff++;
        }

        // check enough samples
        if (_neff < min_n) return false;

        // get eff number of alleles site 1 and check not too unbalanced
        for (unsigned int i=0; i<_a1; i++) {
            if (_p1[i] > 0) {
                _map1[_a1e] = i;
                _a1e++;
                if (static_cast<double>(_p1[i]) / _neff > max_maj) return false;
            }
        }

        // check enough alleles at site 1
        if (_a1e < 2) return false;

        // get eff number of alleles site 2 and check not too unbalanced
        for (unsigned int i=0; i<_a2; i++) {
            if (_p2[i] > 0) {
                _map2[_a2e] = i;
                _a2e++;
                if (static_cast<double>(_p2[i]) / _neff > max_maj) return false;
            }
        }

        // check enough / not too many alleles site 2
        if (_a2e < 2) return false;

        return true;
    }

    unsigned int PairwiseLD::num_alleles1() const {
        return _a1e;
    }

    unsigned int PairwiseLD::num_alleles2() const {
        return _a2e;
    }

    unsigned int PairwiseLD::index1(unsigned int allele) const {
        return _map1[allele];
    }

    unsigned int PairwiseLD::index2(unsigned int allele) const {
        return _map2[allele];
    }

    unsigned int PairwiseLD::freq1(unsigned int allele) const {
        return _p1[_map1[allele]];
    }

    unsigned int PairwiseLD::freq2(unsigned int allele) const {
        return _p2[_map2[allele]];
    }

    unsigned int PairwiseLD::freq(unsigned int allele1, unsigned int allele2) const {
        return _p[_map1[allele1]][_map1[allele2]];
    }

    unsigned int PairwiseLD::nsam() const {
        return _neff;
    }

    void PairwiseLD::compute(unsigned int index1, unsigned int index2) {
        double x1 = (double) _p1[_map1[index1]] / _neff;
        double x2 = (double) _p2[_map2[index2]] / _neff;
        double x12 = (double) _p[_map1[index1]][_map2[index2]] / _neff;

        // compute classical D
        _D = x12 - x1 * x2;

        // compute D'
        if (_D < 0) {
            if (x1 * x2 < (1-x1) * (1-x2)) _Dp = _D / (x1 * x2);
            else _Dp = _D / ((1-x1) * (1-x2));
        }
        else {
            if (x1 * (1-x2) < (1-x1) * x2) _Dp = _D / (x1 * (1-x2));
            else _Dp = _D / ((1-x1) * x2);
        }

        // compute r and r2
        _r = _D / sqrt(x1 * x2 * (1-x1) * (1-x2));
        _rsq = _r * _r;
    }

    double PairwiseLD::D() const {
        return _D;
    }

    double PairwiseLD::Dp() const {
        return _Dp;
    }

    double PairwiseLD::r() const {
        return _r;
    }

    double PairwiseLD::rsq() const {
        return _rsq;
    }

//----------------------------------------------------------------------

    MatrixLD::MatrixLD() {
        _nsites_c = 0;
        _sites = NULL;
        _frq = NULL;
        _nseff = NULL;
        _positions = NULL;
        _linkage = NULL;
        _dist = NULL;
        _adjacent = NULL;
        _np_c = 0;
        _index1 = NULL;
        _index2 = NULL;
        _Rmin_res_sites = 0;
        _Rmin_res_intervals = 0;
        _Rmin_right = NULL;
        _Rmin_left = NULL;
        _Rmin_bool = NULL;
        _Rmin_sites = NULL;
        _all_flags = NULL;
        _flags_c = 0;
        reset();
        toggle_off();
    }

    MatrixLD::~MatrixLD() {
        for (unsigned int i=0; i<_np_c; i++) if (_linkage[i]) delete _linkage[i];
        if (_linkage) free(_linkage);
        if (_index1) free(_index1);
        if (_index2) free(_index2);
        if (_dist) free(_dist);
        if (_adjacent) free(_adjacent);
        if (_Rmin_sites) free(_Rmin_sites);
        if (_Rmin_left) free(_Rmin_left);
        if (_Rmin_right) free(_Rmin_right);
        if (_Rmin_bool) free(_Rmin_bool);
        if (_sites) free(_sites);
        for (unsigned int i=0; i<_nsites_c; i++) if (_frq[i]) delete _frq[i];
        if (_frq) free(_frq);
        if (_nseff) free(_nseff);
        if (_positions) free(_positions);
        if (_all_flags) free(_all_flags);
    }

    void MatrixLD::toggle_off() {
        _toggle_stats = false;
        _toggle_Rmin = false;
    }

    void MatrixLD::toggle_Rmin() {
        _toggle_Rmin = true;
    }

    void MatrixLD::toggle_stats() {
        _toggle_stats = true;
    }

    void MatrixLD::reset() {
        _num_allele_pairs = 0;
        _num_allele_pairs_adj = 0;
        _ZnS = 0.0;
        _ZnS_star1 = 0.0;
        _ZnS_star2 = 0.0;
        _Za = 0.0;
        _ZZ = 0.0;
        _ntot = 0;
        _npairs = 0;
        _nalls = 0;
        _nsites = 0;
        _Rmin = 0;
        _Rmin_num_sites = 0;
        _pl = 0;
        _mismatch = false;
        _nstot = UNKNOWN;
    }

    void MatrixLD::set_structure(StructureHolder& struc) {
        _struct = & struc;
    }

    void MatrixLD::load(const Genotypes& sitegeno, double position) {
        if (_mismatch) return;
        const SiteHolder& site = sitegeno.site();
        if (_nstot == UNKNOWN) {
            _nstot = site.get_ns();
            if (_nstot < _struct->get_req()) {
                throw EggArgumentValueError("structure does not match provided site");
            }
        }
        else if (_nstot != site.get_ns()) {
            _mismatch = true;
            _nsites = 0;
            return;
        }

        _nsites++;
        if (_nsites > _nsites_c) {
            _sites = (const SiteHolder **) realloc(_sites, _nsites * sizeof(const SiteHolder *));
            if (!_sites) throw EGGMEM;
            _nseff = (unsigned int *) realloc(_nseff, _nsites * sizeof(unsigned int));
            if (!_nseff) throw EGGMEM;
            _frq = (FreqHolder **) realloc(_frq, _nsites * sizeof(FreqHolder *));
            if (!_frq) throw EGGMEM;
            _frq[_nsites-1] = new(std::nothrow) FreqHolder;
            if (!_frq[_nsites-1]) throw EGGMEM;
            _positions = (double *) realloc(_positions, _nsites * sizeof(double));
            if (!_positions) throw EGGMEM;
            _nsites_c = _nsites;
        }
        _sites[_nsites-1] = &site;
        _frq[_nsites-1]->setup_structure(*_struct);
        _frq[_nsites-1]->process_site(site);
        _nseff[_nsites-1] = site.get_ns();
        _positions[_nsites-1] = position;
    }

    unsigned int MatrixLD::process(unsigned min_n, double max_maj,
                    MultiAllelic multiallelic, unsigned int min_freq, bool oriented) {

        if (_mismatch) return 0;
        unsigned int flag = 0;
        if (_toggle_stats) {
            computeLD(min_n, max_maj);
            computeStats(multiallelic, min_freq);
            if (_num_allele_pairs > 0) flag |= 1;
            if (_num_allele_pairs_adj > 0) flag |= 2;
        }
        if (_toggle_Rmin) {
            computeRmin(oriented);
            if (_Rmin_num_sites > 1) flag |= 4;
        }
        return flag;
    }

    void MatrixLD::computeLD(unsigned min_n, double max_maj) {

        if (_mismatch) return;
        if (_nsites == 0) return;
        _ntot = _nsites * (_nsites - 1) / 2;

        for (unsigned int i=0; i<_nsites-1; i++) {
            for (unsigned int j=i+1; j<_nsites; j++) {

                // add an item (if needed)
                if (_npairs+1 > _np_c) {
                    _linkage = (PairwiseLD **) realloc(_linkage, (_npairs+1) * sizeof(PairwiseLD *));
                    if (!_linkage) throw EGGMEM;
                    _linkage[_npairs] = new(std::nothrow) PairwiseLD;
                    if (!_linkage[_npairs]) throw EGGMEM;
                    _dist = (unsigned int *) realloc(_dist, (_npairs+1) * sizeof(unsigned int));
                    if (!_dist) throw EGGMEM;
                    _adjacent = (bool *) realloc(_adjacent, (_npairs+1) * sizeof(bool));
                    if (!_adjacent) throw EGGMEM;
                    _index1 = (unsigned int *) realloc(_index1, (_npairs+1) * sizeof(unsigned int));
                    if (!_index1) throw EGGMEM;
                    _index2 = (unsigned int *) realloc(_index2, (_npairs+1) * sizeof(unsigned int));
                    if (!_index2) throw EGGMEM;
                    _np_c = _npairs + 1;
                }
                // try compute the LD
                if (_linkage[_npairs]->process(*(_sites[i]), *(_sites[j]), *(_frq[i]), *(_frq[j]), *_struct, min_n, max_maj)) {
                    _npairs++;
                    _nalls += _linkage[_npairs-1]->num_alleles1() * _linkage[_npairs-1]->num_alleles2();
                    _dist[_npairs-1] = _positions[j] - _positions[i];
                    _adjacent[_npairs-1] = j == i+1;
                    _index1[_npairs-1] = i;
                    _index2[_npairs-1] = j;
                }
            }
        }
    }

    unsigned int MatrixLD::num_tot() const {
        return _ntot;
    }

    unsigned int MatrixLD::num_pairs() const {
        return _npairs;
    }

    unsigned int MatrixLD::num_alleles() const {
        return _nalls;
    }

    unsigned int MatrixLD::index1(unsigned int allele) const {
        return _index1[allele];
    }

    unsigned int MatrixLD::index2(unsigned int allele) const {
        return _index2[allele];
    }

    const PairwiseLD& MatrixLD::pairLD(unsigned int index) const {
        return *(_linkage[index]);
    }

    unsigned int MatrixLD::distance(unsigned int index) const {
        return _dist[index];
    }

    void MatrixLD::computeStats(MultiAllelic multiallelic, unsigned int min_freq) {

        if (_mismatch) return;

        double sum_Dprime2 = 0.0;
        double sum_r2 = 0.0;
        double sum_r2_adj = 0.0;
        _num_allele_pairs = 0;
        _num_allele_pairs_adj = 0;

        switch (multiallelic) {

            case ignore:
                for (unsigned int i=0; i<_npairs; i++) {
                    if (_linkage[i]->num_alleles1() > 2 || _linkage[i]->num_alleles2() > 2) continue;
                    _linkage[i]->compute(0, 0);
                    sum_r2 += _linkage[i]->rsq();
                    sum_Dprime2 += _linkage[i]->Dp() * _linkage[i]->Dp();
                    _num_allele_pairs+=1;

                    if (_adjacent[i]) {
                        sum_r2_adj += _linkage[i]->rsq();
                        _num_allele_pairs_adj++;
                    }
                }
                break;

            case use_main:
                for (unsigned int i=0; i<_npairs; i++) {

                    unsigned int i1 = 0;
                    for (unsigned int j=1; j<_linkage[i]->num_alleles1(); j++) {
                        if (_linkage[i]->freq1(j) > _linkage[i]->freq1(i1)) i1 = j;
                    }

                    unsigned int i2 = 0;
                    for (unsigned int j=1; j<_linkage[i]->num_alleles2(); j++) {
                        if (_linkage[i]->freq2(j) > _linkage[i]->freq2(i2)) i2 = j;
                    }

                    _linkage[i]->compute(i1, i2);
                    sum_r2 += _linkage[i]->rsq();
                    sum_Dprime2 += _linkage[i]->Dp() * _linkage[i]->Dp();
                    _num_allele_pairs+=1;

                    if (_adjacent[i]) {
                        sum_r2_adj += _linkage[i]->rsq();
                        _num_allele_pairs_adj++;
                    }
                }
                break;

            case use_all:
                for (unsigned int i=0; i<_npairs; i++) {
                    for (unsigned int i1=0; i1<_linkage[i]->num_alleles1(); i1++) {
                        for (unsigned int i2=0; i2<_linkage[i]->num_alleles2(); i2++) {
                            if (_linkage[i]->freq1(i1) >= min_freq && _linkage[i]->freq2(i2) >= min_freq) {
                                _linkage[i]->compute(i1, i2);
                                sum_r2 += _linkage[i]->rsq();
                                sum_Dprime2 += _linkage[i]->Dp() * _linkage[i]->Dp();
                                _num_allele_pairs+=1;

                                if (_adjacent[i]) {
                                    sum_r2_adj += _linkage[i]->rsq();
                                    _num_allele_pairs_adj++;
                                }
                            }
                        }
                    }
                }
                break;
        }

        if (_num_allele_pairs > 0) {
            _ZnS = sum_r2 / _num_allele_pairs;
            _ZnS_star1 = _ZnS + 1 - sum_Dprime2 / _num_allele_pairs;
            _ZnS_star2 = _ZnS * _num_allele_pairs / sum_Dprime2;

            if (_num_allele_pairs_adj > 0) {
                _Za = sum_r2_adj / _num_allele_pairs_adj;
                _ZZ = _Za - _ZnS;
            }
            else {
                _Za = 0.0;
                _ZZ = 0.0;
            }

        }
        else {
            _ZnS = 0.0;
            _ZnS_star1 = 0.0;
            _ZnS_star2 = 0.0;
        }
    }

    unsigned int MatrixLD::num_allele_pairs() const {
        return _num_allele_pairs;
    }

    unsigned int MatrixLD::num_allele_pairs_adj() const {
        return _num_allele_pairs_adj;
    }

    double MatrixLD::ZnS() const {
        return _ZnS;
    }

    double MatrixLD::ZnS_star1() const {
        return _ZnS_star1;
    }

    double MatrixLD::ZnS_star2() const {
        return _ZnS_star2;
    }

    double MatrixLD::Za() const {
        return _Za;
    }

    double MatrixLD::ZZ() const {
        return _ZZ;
    }

    void MatrixLD::computeRmin(bool oriented) {

        _Rmin = 0;
        _Rmin_num_sites = 0;
        if (_nsites < 2) return;
        unsigned int nintervals = 0;
        unsigned int i, n;

        // allocate array of booleans to identify valid sites
        if (_nsites > _Rmin_res_sites) {
            _Rmin_sites = (bool *) realloc(_Rmin_sites, _nsites * sizeof(bool));
            if (!_Rmin_sites) throw EGGMEM;
            _Rmin_res_sites = _nsites;
        }

        // make the count of sites with two alleles and, if requested, valid outgroup data
        for (unsigned int site=0; site<_nsites; site++) {

            // check no missing data
            if (_nseff[site] < _struct->get_ni()) {
                _Rmin_sites[site] = false;
                continue; // missing data
            }

            // check exactly 2 alleles
            unsigned int A0 = _frq[site]->num_alleles();
            if (A0 > _flags_c) {
                _all_flags = (bool *) realloc(_all_flags, A0 * sizeof(bool));
                if (!_all_flags) throw EGGMEM;
                _flags_c = A0;
            }
            for (unsigned int a=0; a<A0; a++) _all_flags[a] = false;

            unsigned int A1 = 0;
            for (i = _struct->init_i(); i != UNKNOWN; i = _struct->iter_i()) {
                if (_sites[site]->get_sample(i) >= 0) {
                    if (_all_flags[_sites[site]->get_sample(i)] == false) {
                        A1++;
                        _all_flags[_sites[site]->get_sample(i)] = true;
                        if (A1 > 2) break;
                    }
                }
            }

            if (A1 != 2) { // not counted after 3!
                _Rmin_sites[site] = false;
                continue;
            }

            // check orientable
            if (oriented == true) {
                n = 0;
                bool flag = true;
                for (i = _struct->init_o(); i != UNKNOWN; i = _struct->iter_o()) {
                    if (_sites[site]->get_sample(i) < 0) continue;
                    if (_sites[site]->get_sample(i) >= 0) {
                        if (_all_flags[_sites[site]->get_sample(i)]) n++;
                        else flag = false;
                        break;
                    }
                }

                if (n > 0 && flag) { // exactly two alleles, outgroup included, and >= 1 outgroup available
                    _Rmin_num_sites++;
                    _Rmin_sites[site] = true;
                }
                else {
                    _Rmin_sites[site] = false;
                }
            }
            else {
                _Rmin_num_sites++;
                _Rmin_sites[site] = true; // exactly two alleles, outgroup not requested
            }
        }

        if (_Rmin_num_sites < 2) return;

        //  identify all pairs of sites that break the four (or three) gametes rule
        bool good;
        unsigned int ngametes, gametes1[3], g;
        unsigned int otg_m1, otg_m2;

        for (unsigned int site1=0; site1<_nsites; site1++) {
            if (!_Rmin_sites[site1]) continue;

            // find first non-missing outgroup sample
            if (oriented) {
                for (otg_m1 = _struct->init_o(); otg_m1 != UNKNOWN; otg_m1 = _struct->iter_o()) {
                    if (_sites[site1]->get_sample(otg_m1) >= 0) break;
                }
            }

            for (unsigned int site2=site1+1; site2<_nsites; site2++) {
                if (!_Rmin_sites[site2]) continue;
                if (oriented) {
                    for (otg_m2 = _struct->init_o(); otg_m2 != UNKNOWN; otg_m2 = _struct->iter_o()) {
                        if (_sites[site2]->get_sample(otg_m2) >= 0) break;
                    }
                }

                ngametes = 0;
                good = true;
                for (unsigned int m = _struct->init_i(); m != UNKNOWN; m = _struct->iter_i()) {

                    // if oriented, ignore gametes with double ancestral alleles
                        // note, there may be >1 outgroup, but they all must be the same, so the first non-missing one is taken as reference for ancestral allele
                    if (oriented &&
                            _sites[site1]->get_sample(m) == _sites[site1]->get_sample(otg_m1) &&
                            _sites[site2]->get_sample(m) == _sites[site2]->get_sample(otg_m2)) continue; 

                    for (g=0; g<ngametes; g++) {
                        if (_sites[site1]->get_sample(m) == _sites[site1]->get_sample(gametes1[g]) &&
                            _sites[site2]->get_sample(m) == _sites[site2]->get_sample(gametes1[g])) break;
                    }

                    if (g == ngametes) {
                        ngametes++;
                        if (ngametes == 4 || (oriented && ngametes == 3)) {
                            good = false;
                            break;
                        }
                        gametes1[g] = m;
                    }
                    if (!good) break;
                }

                // if pair of sites breaks the rule of 3/4 gametes, create an interval
                if (good == false) {
                    nintervals++;
                    if (nintervals > _Rmin_res_intervals) {
                        _Rmin_left = (unsigned int *) realloc(_Rmin_left, nintervals * sizeof(unsigned int));
                        if (!_Rmin_left) throw EGGMEM;

                        _Rmin_right = (unsigned int *) realloc(_Rmin_right, nintervals * sizeof(unsigned int));
                        if (!_Rmin_right) throw EGGMEM;

                        _Rmin_bool = (bool *) realloc(_Rmin_bool, nintervals * sizeof(bool));
                        if (!_Rmin_bool) throw EGGMEM;

                        _Rmin_res_intervals = nintervals;
                    }
                    _Rmin_left[nintervals-1] = _positions[site1];
                    _Rmin_right[nintervals-1] = _positions[site2];
                    _Rmin_bool[nintervals-1] = true;
                }
            }
        }

        //  remove (using the array of booleans) all intervals that contain another one
        for (unsigned int i=0; i<nintervals; i++) {
            if (!_Rmin_bool[i]) continue;
            for (unsigned int j=i+1; j<nintervals; j++) {
                if (!_Rmin_bool[j]) continue;

                // we know that _Rmin_left[i] <= _Rmin_left[j]              //     i:     =============
                if (_Rmin_right[i] >= _Rmin_right[j]) {                     //     j:     --=========--
                    _Rmin_bool[i] = false;
                    break;
                }

                if (_Rmin_left[i] == _Rmin_left[j] && _Rmin_right[i] < _Rmin_right[j]) {            //   i:    ======--
                    _Rmin_bool[j] = false;                                                          //   j:    ===========
                }
            }
        }

        // remove (using the array of booleans) all intervals that are overlapping a previous one
        for (unsigned int i=0; i<nintervals; i++) {
            if (!_Rmin_bool[i]) continue;
            for (unsigned int j=i+1; j<nintervals; j++) {
                if (!_Rmin_bool[j]) continue;
                if (_Rmin_left[j] >= _Rmin_right[i]) break;
                if (_Rmin_left[j] < _Rmin_right[i]) _Rmin_bool[j] = false;              // i:       ============= 
                                                                                        // j:           --=============--
            }
        }

        // compact the list of intervals
        for (unsigned int i=0; i<nintervals; i++) {
            if (_Rmin_bool[i]) {
                if (_Rmin < i) {
                    _Rmin_left[_Rmin] = _Rmin_left[i];
                    _Rmin_right[_Rmin] = _Rmin_right[i];
                }
                _Rmin++;
            }
        }
    }

    unsigned int MatrixLD::Rmin() const {
        return _Rmin;
    }

    unsigned int MatrixLD::Rmin_num_sites() const {
        return _Rmin_num_sites;
    }

    unsigned int MatrixLD::Rmin_left(unsigned int i) const {
        return _Rmin_left[i];
    }

    unsigned int MatrixLD::Rmin_right(unsigned int i) const {
        return _Rmin_right[i];
    }
}
