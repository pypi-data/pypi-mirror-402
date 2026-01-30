/*
    Copyright 2018-2025 Stéphane De Mita

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
#include "Structure.hpp"
#include "Genotypes.hpp"

namespace egglib {

    Genotypes::Genotypes() {
        _n_genot = 0;
        _pl = 0;
        _genot_c = 0;
        _pl_c = NULL;
        _array_c = 0;
        _heter = NULL;
        _genot = NULL;
        _array = NULL;
        _flags = NULL;
    }

    Genotypes::~Genotypes() {
        if (_array) free(_array);
        if (_flags) free(_flags);
        if (_heter) free(_heter);
        if (_pl_c) free(_pl_c);
        if (_genot) {
            for (unsigned int i=0; i<_genot_c; i++) {
                if (_genot[i]) free(_genot[i]);
            }
            free(_genot);
        }
    }

    void Genotypes::process(const SiteHolder& site, StructureHolder& stru, bool phased) {
        _site.reset();
        _n_genot = 0;
        if (phased) {
            _site.add(stru.get_ni() + stru.get_no());
            _pl = 1;
        }
        else {
            _site.add(stru.num_indiv_ingroup() + stru.num_indiv_outgroup());
            _pl = stru.get_ploidy();
        }

        if (_pl > _array_c) {
            _array = (int *) realloc(_array, _pl * sizeof(int));
            if (!_array) throw EGGMEM;
            _flags = (bool *) realloc(_flags, _pl * sizeof(bool));
            if (!_flags) throw EGGMEM;
        }
        unsigned int idx = 0;
        for (unsigned int c=0; c < stru.num_clust(); c++) {
            for (unsigned int p=0; p < stru.get_cluster(c).num_pop(); p++) {
                for (unsigned int i=0; i < stru.get_cluster(c).get_population(p).num_indiv(); i++) {
                    const StructureIndiv& idv = stru.get_cluster(c).get_population(p).get_indiv(i);
                    if (phased) {
                        for (unsigned int j=0; j<idv.num_samples(); j++) {
                            _array[0] = site.get_sample(idv.get_sample(j));
                            _site.set_sample(idx++, _find_genotype());
                        }
                    }
                    else {
                        for (unsigned int j=0; j < _pl; j++) {
                            _array[j] = site.get_sample(idv.get_sample(j));
                        }
                        _site.set_sample(idx++, _find_genotype()); // _array could be erased
                    }
                }
            }
        }

        if (phased) {
            for (unsigned int i=0; i < stru.num_indiv_outgroup(); i++) {
                const StructureIndiv& idv = stru.get_indiv_outgroup(i);
                for (unsigned int j=0; j < idv.num_samples(); j++) {
                    _array[0] = site.get_sample(idv.get_sample(j));
                    _site.set_sample(idx++, _find_genotype());
                }
            }
        }
        else if (!(stru.outgroup_haploid() && _pl != 1)) {
            for (unsigned int i=0; i < stru.num_indiv_outgroup(); i++) {
                const StructureIndiv& idv = stru.get_indiv_outgroup(i);
                for (unsigned int j=0; j < _pl; j++) {
                    _array[j] = site.get_sample(idv.get_sample(j));
                }
                _site.set_sample(idx++, _find_genotype()); // _array could be erased
            }
        }
        else {
            _site.set_sample(idx++, -1);
        }
    }

    int Genotypes::_find_genotype() {
        // treat immediately missing data
        for (unsigned int i=0; i<_pl; i++) if (_array[i] < 0) return -1;

        // process all existing genotypes
        unsigned int geno;
        for (geno=0; geno < _n_genot; geno++) {

            // initialize the flag array
            for (unsigned int i=0; i<_pl; i++) _flags[i] = false;

            // compare all alleles
            unsigned int i;
            for (i=0; i<_pl; i++) {
                unsigned int j;
                for (j=0; j<_pl; j++) {
                    if (_flags[j] == false && _array[i] == _genot[geno][j]) {
                        _flags[j] = true; // allele j of _genot[geno] is consumed
                        break; // allele i of _array has been matched by j of _genot[geno]
                    }
                }
                if (j==_pl) break; // allele i of _array has not been matched by any non-consumed j of _genot[geno]
            }
            if (i==_pl) break; // at least one of the i alleles of _array has not been matched
        }
        if (geno == _n_genot) { // none of the the genotypes matches array
            _n_genot++;

            // allocate new genotype
            if (_n_genot > _genot_c) {
                _heter = (bool *) realloc(_heter, _n_genot * sizeof(bool));
                if (!_heter) throw EGGMEM;
                _genot = (int **) realloc(_genot, _n_genot * sizeof(int *));
                if (!_genot) throw EGGMEM;
                _pl_c = (unsigned int *) realloc(_pl_c, _n_genot * sizeof(unsigned int));
                if (!_pl_c) throw EGGMEM;
                _genot_c = _n_genot;
                _genot[geno] = _array; // this is to skip copy of alleles
                _pl_c[geno] = _array_c;
                _array = (int *) malloc(_pl * sizeof(int)); // still need to allocate a new _array
                if (!_array) throw EGGMEM;
                _array_c = _pl;
            }

            // if no allocation needed, copy data
            else {
                if (_pl > _pl_c[geno]) {
                    _genot[geno] = (int *) realloc(_genot[geno], _pl * sizeof(int));
                    if (!_genot[geno]) throw EGGMEM;
                    _pl_c[geno] = _pl;
                }
                for (unsigned int i=0; i<_pl; i++) {
                    _genot[geno][i] = _array[i]; // copy of alleles
                }
            }

            // check if genotype is heterozygote
            _heter[geno] = false;
            for (unsigned int i=1; i<_pl; i++) {
                if (_genot[geno][i] != _genot[geno][0]) {
                    _heter[geno] = true;
                    break;
                }
            }
        }

        // return genotype index
        return static_cast<int>(geno); // if would be possible to check for overflow here but I am lazy
    }

    unsigned int Genotypes::ploidy() const {
        return _pl;
    }

    const SiteHolder& Genotypes::site() const {
        return _site;
    }

    bool Genotypes::heter(unsigned int i) const {
        return _heter[i];
    }

    const int * const Genotypes::genot(unsigned int i) const {
        return _genot[i];
    }

    unsigned int Genotypes::num_genotypes() const {
        return _n_genot;
    }
}
