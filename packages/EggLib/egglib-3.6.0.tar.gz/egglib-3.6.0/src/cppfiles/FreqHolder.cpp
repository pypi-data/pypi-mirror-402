/*
    Copyright 2016-2025 Stéphane De Mita, Mathieu Siol

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

#include <cstdlib>
#include <cstring>
#include "egglib.hpp"
#include "FreqHolder.hpp"
#include "SiteHolder.hpp"
#include "Structure.hpp"
#include "VCF.hpp"

namespace egglib {

    FreqSet::FreqSet() {
        init();
    }

    FreqSet::~FreqSet() {
        free();
    }

    void FreqSet::init() {
        _nall_c = 0;
        _ngen_c = 0;
        _frq_all = NULL;
        _frq_het = NULL;
        _frq_gen = NULL;
        _gen_het = NULL;
        setup();
    }

    void FreqSet::free() {
        if (_frq_all) ::free(_frq_all);
        if (_frq_het) ::free(_frq_het);
        if (_frq_gen) ::free(_frq_gen);
        if (_gen_het) ::free(_gen_het);
    }

    void FreqSet::setup() {
        _nall = 0;
        _nall_eff = 0;
        _ngen = 0;
        _ngen_eff = 0;
        _nsam = 0;
        _nind = 0;
        _nhet = 0;
    }

    void FreqSet::set_nall(unsigned int na) {
        if (na > _nall_c) {
            _frq_all = (unsigned int *) realloc(_frq_all, na * sizeof(unsigned int));
            if (!_frq_all) throw EGGMEM;
            _frq_het = (unsigned int *) realloc(_frq_het, na * sizeof(unsigned int));
            if (!_frq_het) throw EGGMEM;
            _nall_c = na;
        }
        for (unsigned int i=_nall; i<na; i++) {
            _frq_all[i] = 0;
            _frq_het[i] = 0;
        }
        _nall = na;
    }

    void FreqSet::add_genotypes(unsigned int num) {
        _ngen += num;
        if (_ngen > _ngen_c) {
            _frq_gen = (unsigned int *) realloc(_frq_gen, _ngen * sizeof(unsigned int));
            if (!_frq_gen) throw EGGMEM;
            _gen_het = (bool *) realloc(_gen_het, _ngen * sizeof(bool));
            if (!_gen_het) throw EGGMEM;
            _ngen = _ngen;
        }
        for (unsigned int i=0; i<num; i++) {
            _frq_gen[_ngen - 1 - i] = 0;
            _gen_het[_ngen - 1 - i] = false;
        }
    }

    void FreqSet::incr_allele(unsigned int all_idx, unsigned int num) {
        _nsam += num;
        if (_frq_all[all_idx] == 0 && num > 0) _nall_eff++;
        _frq_all[all_idx] += num;
    }

    void FreqSet::incr_genotype(unsigned int gen_idx, unsigned int num) {
        _nind += num;
        if (_frq_gen[gen_idx] == 0 && num > 0) _ngen_eff++;
        _frq_gen[gen_idx] += num;
    }

    void FreqSet::tell_het(unsigned int i, unsigned int a) {
        _frq_het[a] += _frq_gen[i];
        if (!_gen_het[i]) {
            _gen_het[i] = true;
            _nhet += _frq_gen[i];
        }
    }

    unsigned int FreqSet::num_alleles() const {
        return _nall;
    }

    unsigned int FreqSet::num_alleles_eff() const {
        return _nall_eff;
    }

    unsigned int FreqSet::num_genotypes() const {
        return _ngen;
    }

    unsigned int FreqSet::num_genotypes_eff() const {
        return _ngen_eff;
    }

    unsigned int FreqSet::nseff() const {
        return _nsam;
    }

    unsigned int FreqSet::nieff() const {
        return _nind;
    }

    unsigned int FreqSet::frq_all(unsigned int i) const {
        return _frq_all[i];
    }

    unsigned int FreqSet::frq_het(unsigned int all) const {
        return _frq_het[all];
    }

    unsigned int FreqSet::tot_het() const {
        return _nhet;
    }

    unsigned int FreqSet::frq_gen(unsigned int i) const {
        return _frq_gen[i];
    }

//----------------------------------------------------------------------

    FreqHolder::FreqHolder() {
        _npop_c = 0;
        _nclu_c = 0;
        _frq_clu = NULL;
        _frq_pop = NULL;
        _clu_idx = NULL;
        _rel_pop_idx = NULL;
        _pop_ns = NULL;
        _nall_c = 0;
        _ngen_c = 0;
        _gen_c2 = NULL;
        _genotypes = NULL;
        _matched_c = 0;
        _matched = NULL;
        _alleles = NULL;
        _gen_het = NULL;
        _structure = NULL;
        _npop = 0;
        _nclu = 0;
        _nall = 0;
        _pl = 0;
        _ngen = 0;
    }

    FreqHolder::~FreqHolder() {
        if (_frq_clu) {
            for (unsigned int i=0; i<_nclu_c; i++) {
                if (_frq_clu[i]) delete _frq_clu[i];
            }
            free(_frq_clu);
        }
        if (_frq_pop) {
            for (unsigned int i=0; i<_npop_c; i++) {
                if (_frq_pop[i]) delete _frq_pop[i];
            }
            free(_frq_pop);
        }
        if (_genotypes) {
            for (unsigned int i=0; i<_ngen_c; i++) {
                if (_genotypes[i]) free(_genotypes[i]);
            }
            free(_genotypes);
        }
        if (_gen_c2) free(_gen_c2);
        if (_matched) free(_matched);
        if (_alleles) free(_alleles);
        if (_gen_het) free(_gen_het);
        if (_clu_idx) free(_clu_idx);
        if (_rel_pop_idx) free(_rel_pop_idx);
        if (_pop_ns) free(_pop_ns);
    }

    void FreqHolder::_set_frq(unsigned int nc, unsigned int np) {
        _nclu = nc;
        if (_nclu > _nclu_c) {
            _frq_clu = (FreqSet **) realloc(_frq_clu, _nclu * sizeof(FreqSet *));
            if (!_frq_clu) throw EGGMEM;
            for (unsigned int i=_nclu_c; i<_nclu; i++) {
                _frq_clu[i] = new(std::nothrow) FreqSet;
                if (!_frq_clu[i]) throw EGGMEM;
            }
            _nclu_c = _nclu;
        }

        _npop = np;
        if (_npop > _npop_c) {
            _frq_pop = (FreqSet **) realloc(_frq_pop, _npop * sizeof(FreqSet *));
            if (!_frq_pop) throw EGGMEM;
            for (unsigned int i=_npop_c; i<_npop; i++) {
                _frq_pop[i] = new(std::nothrow) FreqSet;
                if (!_frq_pop[i]) throw EGGMEM;
            }
            _clu_idx = (unsigned int *) realloc(_clu_idx, _npop * sizeof(unsigned int));
            if (!_clu_idx) throw EGGMEM;
            _rel_pop_idx = (unsigned int *) realloc(_rel_pop_idx, _npop * sizeof(unsigned int));
            if (!_rel_pop_idx) throw EGGMEM;
            _pop_ns = (unsigned int *) realloc(_pop_ns, _npop * sizeof(unsigned int));
            if (!_pop_ns) throw EGGMEM;
            _npop_c = _npop;
        }
    }

    void FreqHolder::_set_nall(unsigned int na) {
        _nall = na;
        if (_nall > _nall_c) {
            _alleles = (int *) realloc(_alleles, _nall * sizeof(int));
            if (!_alleles) throw EGGMEM;
            _nall_c = _nall;
        }

        if (_nall > _matched_c) {
            _matched = (bool *) realloc(_matched, _nall * sizeof(bool));
            if (!_matched) throw EGGMEM;
            _matched_c = _nall;
        }
        _frq_ing.set_nall(na);
        _frq_otg.set_nall(na);
        for (unsigned int i=0; i<_nclu; i++) _frq_clu[i]->set_nall(na);
        for (unsigned int i=0; i<_npop; i++) _frq_pop[i]->set_nall(na);
    }

    void FreqHolder::_add_genotypes(unsigned int num) {
        _ngen += num;
        if (_ngen > _ngen_c) {
            _genotypes = (int **) realloc(_genotypes, _ngen * sizeof(int *));
            if (!_genotypes) throw EGGMEM;
            _gen_c2 = (unsigned int *) realloc(_gen_c2, _ngen * sizeof(unsigned int));
            if (!_gen_c2) throw EGGMEM;
            _gen_het = (bool *) realloc(_gen_het, _ngen * sizeof(bool));
            if (!_gen_het) throw EGGMEM;
            for (unsigned int i=_ngen_c; i<_ngen; i++) {
                _gen_c2[i] = 0;
                _genotypes[i] = NULL;
                _gen_het[i] = false;
            }
            _ngen_c = _ngen;
        }
        for (unsigned int i=0; i<num; i++) {
            if (_pl > _gen_c2[_ngen-1-i]) {
                _genotypes[_ngen-1-i] = (int *) realloc(_genotypes[_ngen-1-i], _pl * sizeof(int));
                if (!_genotypes[_ngen-1-i]) throw EGGMEM;
                _gen_c2[_ngen-1-i] = _pl;
            }
        }
        _frq_ing.add_genotypes(num);
        _frq_otg.add_genotypes(num);
        for (unsigned int i=0; i<_nclu; i++) _frq_clu[i]->add_genotypes(num);
        for (unsigned int i=0; i<_npop; i++) _frq_pop[i]->add_genotypes(num);
    }

    void FreqHolder::setup_structure(const StructureHolder & structure) {
        _pl = structure.get_ploidy();
        if (_pl == 0) throw EggArgumentValueError("ploidy cannot be 0");
        if (_pl > _matched_c) {
            _matched = (bool *) realloc(_matched, _pl * sizeof(bool));
            if (!_matched) throw EGGMEM;
            _matched_c = _pl;
        }

        _ngen = 0;
        _nall = 0;
        _structure = & structure;

        // setup global FreqSet objects
        _frq_ing.setup();
        _frq_otg.setup();

        // create needed FreqSet objects
        _set_frq(structure.num_clust(), structure.num_pop());

        // setup FreqSet objects
        unsigned int cur = 0;
        for (unsigned int i=0; i<_nclu; i++) {
            _frq_clu[i]->setup();
            for (unsigned int j=0; j<structure.get_cluster(i).num_pop(); j++) {
                _frq_pop[cur]->setup();
                _clu_idx[cur] = i;
                _rel_pop_idx[cur] = j;
                _pop_ns[cur] = structure.get_cluster(i).get_population(j).num_indiv();
                cur++;
            }
        }
    }

    void FreqHolder::setup_raw(unsigned int nc, unsigned int np, unsigned int ploidy) {
        _pl = ploidy;
        if (_pl > _matched_c) {
            _matched = (bool *) realloc(_matched, _pl * sizeof(bool));
            if (!_matched) throw EGGMEM;
            _matched_c = _pl;
        }
        _ngen = 0;
        _nall = 0;
        _structure = NULL;
        _set_frq(nc, np);
        _frq_ing.setup();
        _frq_otg.setup();
        for (unsigned int i=0; i<nc; i++) _frq_clu[i]->setup();
    }

    void FreqHolder::setup_pop(unsigned int idx, unsigned int cluster, unsigned int rel_idx, unsigned int ns) {
        _frq_pop[idx]->setup();
        _clu_idx[idx] = cluster;
        _rel_pop_idx[idx] = rel_idx;
        _pop_ns[idx] = ns;
    }

    void FreqHolder::set_ngeno(unsigned int ng) {
        _ngen = 0;
        _nall = 0;
        _add_genotypes(ng);
    }

    unsigned int FreqHolder::find_allele(int allele) {
        for (unsigned int i=0; i<_nall; i++) {
            if (allele == _alleles[i]) {
                return i;
            }
        }
        _set_nall(_nall+1);
        _alleles[_nall-1] = allele;
        return _nall-1;
    }

    unsigned int FreqHolder::_find_genotype(const StructureIndiv& indiv, const SiteHolder& site) {
        for (unsigned int i=0; i<_pl; i++) {
            if (site.get_sample(indiv.get_sample(i)) < 0) return MISSING;
        }
        unsigned int idx, all_idx, all_idx2;
        int allele;
        for (idx=0; idx<_ngen; idx++) {
            for (all_idx=0; all_idx<_pl; all_idx++) {
                _matched[all_idx] = false;
            }
            for (all_idx=0; all_idx<_pl; all_idx++) {
                allele = site.get_sample(indiv.get_sample(all_idx));
                for (all_idx2=0; all_idx2<_pl; all_idx2++) {
                    if (_matched[all_idx2] == false && _genotypes[idx][all_idx2] == allele) {
                        _matched[all_idx2] = true;
                        break; // found this allele
                    }
                }
                if (all_idx2 == _pl) break; // did not find a match for allele all_idx
            }
            if (all_idx == _pl) break; // all alleles are matching
        }
        if (idx == _ngen) { // no genotype is matching
            _add_genotypes(1);
            for (all_idx=0; all_idx<_pl; all_idx++) {
                _genotypes[idx][all_idx] = site.get_sample(indiv.get_sample(all_idx));
            }
        }
        return idx;
    }

    void FreqHolder::process_site(const SiteHolder& site) {

        // set ingroup freq
        _ngen = 0;
        _nall = 0;
        unsigned int i, j, k, all, gen_idx;
        unsigned int idx = 0; // initialize to avoid warning (might be unitialized if _pl is 0, which is excluded)
        for (unsigned int p=0; p<_npop; p++) {


            for (i=0; i<_pop_ns[p]; i++) {
                const StructureIndiv& indiv = _structure->get_cluster(_clu_idx[p]).get_population(_rel_pop_idx[p]).get_indiv(i);

                // process all alleles of the genotype
                for (j=0; j<_pl; j++) {
                    idx = indiv.get_sample(j);
                    if (site.get_sample(idx) >= 0) {
                        all = find_allele(site.get_sample(idx));
                        _frq_ing.incr_allele(all, 1);
                        _frq_clu[_clu_idx[p]]->incr_allele(all, 1);
                        _frq_pop[p]->incr_allele(all, 1);
                    }
                    else {
                        all = MISSING;
                    }
                }

                // process genotype
                if (_pl == 1) {
                    // ad hoc code to use allele index as genotype index
                    gen_idx = all;
                    if (gen_idx == _ngen) { // new genotype
                        _add_genotypes(1);
                        _genotypes[gen_idx][0] = site.get_sample(indiv.get_sample(0));
                    }
                }
                else {
                    // general genotype screening
                    gen_idx = _find_genotype(indiv, site);
                }
                if (gen_idx != MISSING) {
                    _frq_ing.incr_genotype(gen_idx, 1);
                    _frq_clu[_clu_idx[p]]->incr_genotype(gen_idx, 1);
                    _frq_pop[p]->incr_genotype(gen_idx, 1);
                }
            }
        }

        // set outgroup freq
        for (i=0; i<_structure->num_indiv_outgroup(); i++) {
            const StructureIndiv& indiv = _structure->get_indiv_outgroup(i);

            // process all alleles of the genotype
            for (j=0; j<indiv.num_samples(); j++) { // use num_samples() rather than _pl to support haploid outgroup
                idx = indiv.get_sample(j);
                if (site.get_sample(idx) >= 0) _frq_otg.incr_allele(find_allele(site.get_sample(idx)), 1);
            }

            // process genotype
            if (!(_structure->outgroup_haploid() && _pl != 1)) {
                gen_idx = _find_genotype(indiv, site);
                if (gen_idx != MISSING) _frq_otg.incr_genotype(gen_idx, 1);
            }
        }

        // process heterozygote genotypes
        if (_pl > 1) {
            for (i=0; i<_ngen; i++) {
                for (j=1; j<_pl; j++) {
                    if (_genotypes[i][j] != _genotypes[i][0]) break;
                }
                // if heterozygote
                if (j < _pl) {
                    _gen_het[i] = true;
                    for (j=0; j<_nall; j++) _matched[j] = false;
                    for (j=0; j<_pl; j++) {
                        unsigned int all_index = get_allele_index(_genotypes[i][j]);
                        if (all_index != MISSING) _matched[all_index] = true;
                    }
                    for (j=0; j<_nall; j++) {
                        if (_matched[j]) {
                            _frq_ing.tell_het(i, j);
                            _frq_otg.tell_het(i, j);
                            for (k=0; k<_nclu; k++) _frq_clu[k]->tell_het(i, j);
                            for (k=0; k<_npop; k++) _frq_pop[k]->tell_het(i, j);
                        }
                    }
                }
            }
        }
    }

    void FreqHolder::process_vcf(const VcfParser& vcf) {
        unsigned int AN = vcf.AN();
        if (AN == UNKNOWN) throw EggArgumentValueError("cannot import VCF data: AN is missing");
        unsigned int acc = 0;
        setup_raw(1, 1, 1);
        setup_pop(0, 0, 0, AN);
        set_ngeno(vcf.num_AC()+1);
        _set_nall(vcf.num_AC()+1);
        for (unsigned int i=0; i<_nall; i++) {
            set_genotype_item(i, 0, i);
            _alleles[i] = i;
        }

        unsigned int AC;
        for (unsigned int i=1; i<_nall; i++) {
            AC = vcf.AC(i-1);
            if (AC == UNKNOWN) AC = 0;
            _frq_ing.incr_allele(i, AC);
            _frq_clu[0]->incr_allele(i, AC);
            _frq_pop[0]->incr_allele(i, AC);
            _frq_ing.incr_genotype(i, AC);
            _frq_clu[0]->incr_genotype(i, AC);
            _frq_pop[0]->incr_genotype(i, AC);
            acc += AC;
        }
        if (acc > AN) throw EggRuntimeError("invalid VCF data: sum of AC fields is > AN");
        acc = AN - acc;
        _frq_ing.incr_allele(0, acc);
        _frq_clu[0]->incr_allele(0, acc);
        _frq_pop[0]->incr_allele(0, acc);
        _frq_ing.incr_genotype(0, acc);
        _frq_clu[0]->incr_genotype(0, acc);
        _frq_pop[0]->incr_genotype(0, acc);
    }

    const FreqSet& FreqHolder::frq_ingroup() const {
        return _frq_ing;
    }

    const FreqSet& FreqHolder::frq_outgroup() const {
        return _frq_otg;
    }

    const FreqSet& FreqHolder::frq_cluster(unsigned int i) const {
        return * _frq_clu[i];
    }

    const FreqSet& FreqHolder::frq_population(unsigned int i) const {
        return * _frq_pop[i];
    }

    unsigned int FreqHolder::ploidy() const {
        return _pl;
    }

    unsigned int FreqHolder::num_alleles() const {
        return _nall;
    }

    unsigned int FreqHolder::num_genotypes() const {
        return _ngen;
    }

    const int * FreqHolder::genotype(unsigned int i) const {
        return _genotypes[i];
    }

    bool FreqHolder::genotype_het(unsigned int i) const {
        return _gen_het[i];
    }

    int FreqHolder::genotype_item(unsigned int i, unsigned int j) const {
        return _genotypes[i][j];
    }

    void FreqHolder::set_genotype_item(unsigned int i, unsigned int j, int a) {
        _genotypes[i][j] = a;
    }

    unsigned int FreqHolder::num_clusters() const {
        return _nclu;
    }

    unsigned int FreqHolder::num_populations() const {
        return _npop;
    }

    int FreqHolder::allele(unsigned int i) const {
        return _alleles[i];
    }

    unsigned int FreqHolder::get_allele_index(int all) const {
        if (all < 0) return MISSING;
        for (unsigned int i=0; i<_nall; i++) {
            if (_alleles[i] == all) return i;
        }
        return MISSING;
    }

    unsigned int FreqHolder::cluster_index(unsigned int i) const {
        return _clu_idx[i];
    }
}
