/*
    Copyright 2017-2021 Thomas Coudoux, Stéphane De Mita, Mathieu Siol

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
#include <fstream>
#include "egglib.hpp"
#include "VCF.hpp"
#include "VcfIndex.hpp"

namespace egglib {

    void make_vcf_index(egglib::VcfParser& VCF, const char * output) {

        // open output file
        std::ofstream stream(output, std::ios::out | std::ios::binary);
        if (!stream.is_open()) throw EggOpenFileError(output);

        // current chromosome
        char * cur_ctg = (char *) malloc(1 * sizeof(char));
        if (!cur_ctg) throw EGGMEM;
        unsigned int r_ctg = 0;
        cur_ctg[0] = '\0';
        std::streampos file_end = VCF.file_end();
        stream.write((char *)&file_end, sizeof(std::streampos));

        unsigned int nc = 0;
        unsigned int nv = 0;
        while (VCF.good()) {
            if (!stream.good()) throw EggRuntimeError("an error occurred while writing index");
            std::streampos idx = VCF.get_filepos();
            VCF.read(true);
            const char * ctg = VCF.chromosome();
            unsigned long pos = VCF.position();

            size_t ln = strlen(ctg);
            if (strcmp(ctg, cur_ctg)) {
                if (ln > r_ctg) {
                    cur_ctg = (char *) realloc(cur_ctg, (ln+1) * sizeof(char));
                    if (!cur_ctg) throw EGGMEM;
                    strcpy(cur_ctg, ctg);
                    stream.put(1);
                    stream.write((char *) &ln, sizeof(size_t));
                    stream.write(ctg, ln * sizeof(char));
                    nc++;
                }
            }

            stream.put(2);
            stream.write((char *) &pos, sizeof(unsigned long));
            stream.write((char *) &idx, sizeof(std::streampos));
            nv++;

            if (!stream.good()) throw EggArgumentValueError("cannot write to index file (stream error)");
        }

        stream.put(0);
        stream.write((char *) &nc, sizeof(unsigned int));
        stream.write((char *) &nv, sizeof(unsigned int));
        stream.close();
        if (!stream.good()) throw EggArgumentValueError("cannot write to index file (stream error)");
        if (VCF.get_filepos() != VCF.file_end()) throw EggArgumentValueError("error creating index file (garbage at the end of VCF file?)");

        if (cur_ctg) free(cur_ctg);
    }

    VcfIndex::VcfIndex() {
        _vcf = NULL;
        _has_data = false;
        _num_contigs = 0;
        _res_contigs = 0;
        _num_variants = 0;
        _res_variants = 0;
        _res_contig_name = NULL;
        _contig_name = NULL;
        _contig_first_variant = NULL;
        _contig_last_variant = NULL;
        _variant_contig = NULL;
        _variant_position = NULL;
        _variant_filepos = NULL;
    }

    VcfIndex::~VcfIndex() {
        if (_res_contig_name) free(_res_contig_name);
        for (unsigned int i=0; i<_res_contigs; i++) {
            if (_contig_name[i]) free(_contig_name[i]);
        }
        if (_contig_name) free(_contig_name);
        if (_contig_first_variant) free(_contig_first_variant);
        if (_contig_last_variant) free(_contig_last_variant);
        if (_variant_contig) free(_variant_contig);
        if (_variant_position) free(_variant_position);
        if (_variant_filepos) free(_variant_filepos);
    }

    void VcfIndex::load_data(VcfParser& ref, const char * fname) {
        std::ifstream stream(fname, std::ios::in | std::ios::binary);
        if (!stream.is_open()) throw EggOpenFileError(fname);

        // check that file end matches with expectation
        std::streampos file_end;
        stream.read((char *) &file_end, sizeof(std::streampos));
        if (file_end != ref.file_end()) throw EggArgumentValueError("invalid VCF index file (file_end mismatch)");

        // go to the end of index file to read number of contigs/variants
        stream.seekg(- 2 * sizeof(unsigned int), std::  ios_base::end);
        unsigned int nc, nv;
        stream.read((char *) &nc, sizeof(unsigned int));
        stream.read((char *) &nv, sizeof(unsigned int));
        if (!stream.good()) throw EggArgumentValueError("invalid VCF index file (stream error)");
        stream.seekg(sizeof(std::streampos), std::ios_base::beg);

        // allocate
        _num_contigs = nc;
        if (nc > _res_contigs) {
            _res_contig_name = (unsigned int *) realloc(_res_contig_name, nc * sizeof(unsigned int));
            if (!_res_contig_name) throw EGGMEM;
            _contig_name = (char **) realloc(_contig_name, nc * sizeof(char *));
            if (!_contig_name) throw EGGMEM;
            for (unsigned int i=_res_contigs; i<nc; i++) {
                _res_contig_name[i] = 0;
                _contig_name[i] = NULL;
            }
            _res_contigs = nc;
        }
        _num_variants = nv;
        if (nv > _res_variants) {
            _contig_first_variant = (unsigned int *) realloc(_contig_first_variant, nv * sizeof(unsigned int));
            if (!_contig_first_variant) throw EGGMEM;
            _contig_last_variant = (unsigned int *) realloc(_contig_last_variant, nv * sizeof(unsigned int));
            if (!_contig_last_variant) throw EGGMEM;
            _variant_contig = (unsigned int *) realloc(_variant_contig, nv * sizeof(unsigned int));
            if (!_variant_contig) throw EGGMEM;
            _variant_position = (unsigned long *) realloc(_variant_position, nv * sizeof(unsigned long));
            if (!_variant_position) throw EGGMEM;
            _variant_filepos = (std::streampos *) realloc(_variant_filepos, nv * sizeof(std::streampos));
            if (!_variant_filepos) throw EGGMEM;
            _res_variants = nv;
        }

        // process contigs and variants
        unsigned int cur_ctg = 0;
        unsigned int cur_var = 0;
        size_t ln;
        int status = stream.get();
        while (cur_ctg < nc) {
            if (status != 1) throw EggArgumentValueError("invalid VCF index file (expect a `1` before contig)");
            // read contig name
            stream.read((char *) &ln, sizeof(size_t));
            if (ln + 1 > _res_contig_name[cur_ctg]) {
                _contig_name[cur_ctg] = (char *) realloc(_contig_name[cur_ctg], (ln + 1) * sizeof(char));
                if (!_contig_name[cur_ctg]) throw EGGMEM;
                _res_contig_name[cur_ctg] = ln + 1;
            }
            stream.read(_contig_name[cur_ctg], sizeof(char) * ln);
            _contig_name[cur_ctg][ln] = '\0';
            _contig_first_variant[cur_ctg] = cur_var;
            _contig_last_variant[cur_ctg] = UNKNOWN;
            if (!stream.good()) throw EggArgumentValueError("invalid VCF index file (stream error)");

            // read variants
            status = stream.get();
            if (status != 2) throw EggArgumentValueError("invalid VCF index file (contigs must have at least one variant)");
            while (cur_var < nv && status == 2) {
                stream.read((char *) &_variant_position[cur_var], sizeof(unsigned long));
                stream.read((char *) &_variant_filepos[cur_var], sizeof(std::streampos));
                if (_variant_filepos[cur_var] >= ref.file_end()) throw EggArgumentValueError("invalid VCF index file: filepos out of file range");
                 _variant_contig[cur_var] = cur_ctg;
                cur_var++;
                 _contig_last_variant[cur_ctg] = cur_var - 1;
                status = stream.get();
                if (!stream.good()) throw EggArgumentValueError("invalid VCF index file (stream error)");
            }

            if (_contig_last_variant[cur_ctg] == UNKNOWN) throw EggArgumentValueError("invalid VCF index file (empty contig)");
            cur_ctg++; // at the end (used inside the variant loop)
        }

        // some checking
        if (status != 0) throw EggArgumentValueError("invalid VCF index file (inconsistency)");
        unsigned int x;
        stream.read((char *) &x, sizeof(unsigned int));
        if (x != nc) throw EggArgumentValueError("invalid VCF index file (inconsistency)");
        stream.read((char *) &x, sizeof(unsigned int));
        if (x != nv) throw EggArgumentValueError("invalid VCF index file (inconsistency)");
        if (!stream.good()) throw EggArgumentValueError("invalid VCF index file (stream error)");
        stream.peek();
        if (!stream.eof()) throw EggArgumentValueError("invalid VCF index file (garbage at the end of file)");

        _has_data = true;
        _vcf = &ref;
    }

    bool VcfIndex::has_data() const {
        return _has_data;
    }

    unsigned long VcfIndex::num() const {
        return _num_variants;
    }

    void VcfIndex::go_to(const char * contig, unsigned long position) {
        if (!_has_data) throw EggArgumentValueError("no index loaded");

        // identify contig
        unsigned int ctg;
        for (ctg=0; ctg<_num_contigs; ctg++) {
            if (!strcmp(_contig_name[ctg], contig)) break;
        }
        if (ctg == _num_contigs) throw EggArgumentValueError("cannot find specified contig");

        // identify variant
        unsigned int var;
        if (position == FIRST) var = _contig_first_variant[ctg];
        else if (position == LAST) var = _contig_last_variant[ctg];
        else {
            for (var=_contig_first_variant[ctg]; var<=_contig_last_variant[ctg]; var++) {
                if (_variant_position[var] == position) break;
            }
            if (var == _contig_last_variant[ctg] + 1) throw EggArgumentValueError("cannot find specified variant");
        }

        #ifdef DEBUG
        if (_variant_contig[var] != ctg) throw EggRuntimeError("mismatch between contig and variant");
        #endif

        // move to requested position
        _vcf->set_filepos(_variant_filepos[var], var);
    }
}
