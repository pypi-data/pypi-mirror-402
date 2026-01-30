/*
    Copyright 2012-2024 Stéphane De Mita, Mathieu Siol

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
#include <cstdlib>
#include <cstring>
#include "DataHolder.hpp"
#include "Structure.hpp"
#include "SiteHolder.hpp"
#include "VCF.hpp"
#include "Alphabet.hpp"

namespace egglib {

    SiteHolder::SiteHolder() {
        _ns_c = 0;
        _data = NULL;
        _chrom_sz =  0;
        _chrom = (char *) malloc(sizeof(char));
        if (!_chrom) throw EGGMEM;
        _chrom_sz = 0;
        reset();
    }

    SiteHolder::~SiteHolder() {
        if (_data) ::free(_data);
    }

    void SiteHolder::reset() {
        _ns = 0;
        _missing = 0;
        _position = UNDEF;
        _chrom[0] = '\0';
    }

    void SiteHolder::set_position(double p) {
        _position = p;
    }

    double SiteHolder::get_position() const {
        return _position;
    }

    void SiteHolder::set_chrom(const char * s) {
        if (strlen(s) > _chrom_sz) {
            char * tp = (char *) realloc(_chrom, strlen(s)+1);
            if (!tp) throw EGGMEM;
            _chrom = tp;
            _chrom_sz = sizeof(s);
        }
        strcpy(_chrom, s);
    }

    const char * SiteHolder::get_chrom() const {
        return _chrom;
    }

    void SiteHolder::add(unsigned int num) {
        _ns += num;
        if (_ns > _ns_c) {
            _data = (int *) realloc(_data, _ns * sizeof(int));
            if (!_data) throw EGGMEM;
            _ns_c = _ns;
        }
    }

    unsigned int SiteHolder::get_ns() const {
        return _ns;
    }

    int SiteHolder::get_sample(unsigned int sam) const {
        #ifdef DEBUG
        if (sam >= _ns) throw EggArgumentValueError("invalid sample index");
        #endif
        return _data[sam];
    }

    void SiteHolder::set_sample(unsigned int sam, int all) {
        if (all < 0) _missing++;
        _data[sam] = all;
    }

    void SiteHolder::del_sample(unsigned int sam) {
        if (_data[sam] < 0) {
            #ifdef DEBUG
            if (_missing == 0) throw EggRuntimeError("missing is 0 but a missing allele was found");
            #endif
            _missing--;
        }
        _ns--;
        for (unsigned int i=sam; i<_ns; i++) _data[i] = _data[i+1];
    }

    void SiteHolder::append(int all) {
        if (all < 0) _missing++;
        
    }

    unsigned int SiteHolder::get_missing() const {
        return _missing;
    }

    unsigned int SiteHolder::process_align(const DataHolder& aln,
                    unsigned int site_idx, StructureHolder * struc) {

        if (aln.get_is_matrix() == false) throw EggArgumentValueError("argument must be an alignment");

        unsigned int cur = _ns;
        unsigned int good = 0;
        _position = (double) site_idx;

        if (struc != NULL) {
            add(struc->get_ni() + struc->get_no());
            unsigned int sam_idx = struc->init_i();
            while (sam_idx != UNKNOWN) {
                set_sample(cur++, aln.get_sample(sam_idx, site_idx));
                sam_idx = struc->iter_i();
                if (_data[cur-1] >= 0) good++;
            }
            sam_idx = struc->init_o();
            while (sam_idx != UNKNOWN) {
                set_sample(cur++, aln.get_sample(sam_idx, site_idx));
                sam_idx = struc->iter_o();
            }
        }

        else {
            add(aln.get_nsam());
            for (unsigned int i = 0; i < aln.get_nsam(); i++) {
                set_sample(cur++, aln.get_sample(i, site_idx));
                if (_data[cur-1] >= 0) good++;
            }
        }

        return good;
    }

    unsigned int SiteHolder::process_vcf(VcfParser& vcf,
                     unsigned int start, unsigned int stop) {

        unsigned int cur = _ns;
        int allele;
        int missing = vcf.type_alleles() == 0 ? -3 : -1; // -3 for DNA alphabet (?)
        unsigned int ploidy = vcf.ploidy();
        add((stop-start)*ploidy);
        _position = (double) vcf.position();

        for (unsigned int i=start; i<stop; i++) {
            for (unsigned int j=0; j<ploidy; j++) {
                if (vcf.GT(i, j) == UNKNOWN) {
                    allele = missing;
                }
                else {
                    allele = static_cast<int>(vcf.GT(i, j));
                    if (vcf.type_alleles() == 0) allele = get_static_DNAAlphabet().get_code(allele==0?vcf.reference()[0]:vcf.alternate(allele-1)[0]);
                }
                set_sample(cur++, allele);
            }
        }

        return _ns - _missing;
    }
}
