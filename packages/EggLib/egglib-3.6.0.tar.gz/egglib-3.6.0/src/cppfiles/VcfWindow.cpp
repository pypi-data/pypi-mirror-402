/*
    Copyright 2016-2021 Stéphane De Mita, Mathieu Siol, Thomas Coudoux

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
#include <new>
#include "VcfWindow.hpp"

namespace egglib {

    WSite::WSite(WPool * p) {
        _pool = p;
        _which_alphabet = NULL;
        _salph.set_name("VCF_alphabet_indels");
        _salph.set_type("string");
        _csalph.set_name("VCF_alphabet_custom");
        _csalph.set_type("custom");
        reset(1);
    }

    void WSite::reset(unsigned int pl) {
        _pos = UNKNOWN;
        _site.reset();
        _which_alphabet = NULL;
    }

    void WSite::init() {
        _prev = NULL;
        _next = NULL;
    }

    WSite::~WSite() {
    }

    SiteHolder& WSite::site() {
        return _site;
    }

    void WSite::set_pos(unsigned long p) {
        _pos = p;
    }

    unsigned long WSite::get_pos() const {
        return _pos;
    }

    void WSite::set_alphabet(VcfParser * parser) {
        switch (parser->type_alleles()) {
            case 0:
                _which_alphabet = NULL;
                return;
                break;
            case 1:
                _salph.reset();
                _which_alphabet = & _salph;
                break;
            case 2:
            case 3:
                _csalph.reset();
                _which_alphabet = & _csalph;
                break;
            default:
                throw EggRuntimeError("unexpected value for `type_alleles` (internal error)");
        }
        parser->set_alleles(static_cast<StringAlphabet&>(*_which_alphabet));
    }

    StringAlphabet * WSite::alphabet() {
        return _which_alphabet;
    }

    WSite * WSite::next() {
        return _next;
    }

    WSite * WSite::prev() {
        return _prev;
    }

    WSite * WSite::push_back(WSite * ws) {
        _next = ws;
        ws->_prev = this;
        ws->_next = NULL;
        return ws;
    }

    WSite * WSite::pop_front() {
        if (_next != NULL) _next->_prev = NULL;
        _pool->put(this);
        return _next;
    }

    WSite * WSite::pop_back() {
        if (_prev != NULL) _prev->_next = NULL;
        _pool->put(this);
        return _prev;
    }

    WPool::WPool() {
        _cache = NULL;
        _pool = NULL;
        _c_cache = 0;
        _c_pool = 0;
        _n_pool = 0;
    }

    WPool::~WPool() {
        for (unsigned int i=0; i<_c_cache; i++) {
            if (_cache[i]) delete _cache[i];
        }
        if (_cache) free(_cache);
        if (_pool) free(_pool);
    }

    WSite * WPool::get() {
        if (_n_pool == 0) {
            _c_cache++;
            _cache = (WSite **) realloc(_cache, _c_cache * sizeof(WSite *));
            if (!_cache) throw EGGMEM;
            _cache[_c_cache-1] = new(std::nothrow) WSite(this);
            if (!_cache[_c_cache-1]) throw EGGMEM;
            return _cache[_c_cache-1];
        }
        else {
            return _pool[--_n_pool];
        }
    }

    void WPool::put(WSite * p) {
        _n_pool++;
        if (_n_pool > _c_pool) {
            _pool = (WSite **) realloc(_pool, _n_pool * sizeof(WSite *));
            if (!_pool) throw EGGMEM;
            _c_pool = _n_pool;
        }
        _pool[_n_pool-1] = p;
    }

    VcfWindowBase::VcfWindowBase() {
        _first_site = NULL;
        _last_site = NULL;
        _num = 0;
        _mask = 3;
        _max_missing = 0;
        _vcf = NULL;
        _chrom = (char *) malloc(1 * sizeof(char));
        if (!_chrom) throw EGGMEM;
        _chrom[0] = '\0';
        _c_chrom = 1;
        _win_start = BEFORE;
        _win_stop = BEFORE;
        _status = 0;
    }

    VcfWindowBase::~VcfWindowBase() {
        if (_chrom) free(_chrom);
    }

    void VcfWindowBase::setup_base(VcfParser& parser, unsigned int max_missing, unsigned int mask) {
        while (_first_site != NULL) _first_site = _first_site->pop_front();
        _last_site = NULL;
        _num = 0;
        _vcf = &parser;
        _max_missing = max_missing;
        _win_start = BEFORE;
        _win_stop = BEFORE;
        _mask = mask;
        _status = 0;
    }

    const char * VcfWindowBase::chromosome() const {
        return _chrom;
    }

    unsigned long VcfWindowBase::win_start() const { return _win_start; }

    unsigned long VcfWindowBase::win_stop() const { return _win_stop; }

    unsigned int VcfWindowBase::num_sites() const { return _num; }

    const WSite * VcfWindowBase::first_site() const { return _first_site; }

    const WSite * VcfWindowBase::last_site() const { return _last_site; }

    unsigned int VcfWindowBase::num_samples() const { return _vcf->num_samples(); }

    const WSite * VcfWindowBase::get_site(unsigned int idx) const {
        WSite * site = _first_site;
        for (unsigned int i=0; i<idx; i++) site = site->next();
        return site;
    }

    int VcfWindowBase::_read(unsigned long limit) {
        while (true) {
            // no data at all
            if (!_vcf->good()) return _status = 3;

            // read one
            _vcf->read();
            if (!_vcf->has_GT()) throw EggArgumentValueError("cannot extract sites from VCF: no GT available");

            // is next chromosome
            if (strcmp(_vcf->chromosome(), _chrom)) {
                _vcf->unread();
                return _status = 2;
            }

            // skip sites not matching mask
            if ((_vcf->type_alleles() & _mask) != 0) continue;

            // reached limit
            if (_vcf->position() >= limit) {
                _vcf->unread();
                return _status = 1;
            }

            return _status = 0;
        }
    }

    void VcfWindowBase::_slide_window() {
        // pop sites from start of window
        while (_first_site != NULL && _first_site->get_pos() < _win_start) {
            _first_site = _first_site->pop_front();
            _num--;
        }
        if (_first_site == NULL) _last_site = NULL;

        // add sites at the end of window
        while (_read(_win_stop) == 0) {
            _add();
        }
    }

    void VcfWindowBase::_add() {
        if (!_last_site) {
            _last_site = _pool.get();
            _first_site = _last_site;
            _first_site->init();
        }
        else {
            _last_site = _last_site->push_back(_pool.get());
        }
        _last_site->reset(_vcf->ploidy());
        _last_site->set_pos(_vcf->position());
        _last_site->set_alphabet(_vcf);
        if (_last_site->site().process_vcf(*_vcf, 0, _vcf->num_samples()) < ((int)_vcf->num_samples() - _max_missing)) {
            _last_site = _last_site->pop_back();
            if (!_last_site) _first_site = NULL;
        }
        else {
            _num++;
        }
    }

    VcfWindowSliderBase::VcfWindowSliderBase() {
        _start_pos = BEFORE;
        _stop_pos = BEFORE;
    }

    VcfWindowSliderBase::~VcfWindowSliderBase() {
    }

    bool VcfWindowSliderBase::good() const {
        return _vcf->good() && _status == 0;
    }

    void VcfWindowSliderBase::setup(VcfParser& parser, unsigned int wsize, unsigned int wstep,
                unsigned long start_pos, unsigned long stop_pos,
                unsigned int max_missing, unsigned int mask) {

        // load data to base class
        setup_base(parser, max_missing, mask);

        // get own parameters
        _start_pos = start_pos;
        _stop_pos = stop_pos;
        _wsize = wsize;
        _wstep = wstep;
        if (wstep == 0) throw EggArgumentValueError("step cannot be null");

        // get chromosome name
        if (_vcf->good()) {
            _vcf->read();
            const char * chr = _vcf->chromosome();
            if ((strlen(chr)+1) > _c_chrom) {
                _chrom = (char *) realloc(_chrom, (strlen(chr)+1) * sizeof(char));
                if (!_chrom) throw EGGMEM;
                _c_chrom = strlen(chr) + 1;
            }
            strcpy(_chrom, chr);
            _vcf->unread();
        }
        else {
            _chrom[0] = '\0';
        }

        // advance until start position is met
        while (_read(_start_pos) == 0);
        if (_status == 1) _status = 0;
    }

    VcfWindowSlider::VcfWindowSlider() {
        _next_start = BEFORE;
    }

    VcfWindowSlider::~VcfWindowSlider() {
    }

    void VcfWindowSlider::setup(VcfParser& parser, unsigned int wsize, unsigned int wstep,
                unsigned long start_pos, unsigned long stop_pos,
                unsigned int max_missing, unsigned int mask) {
        VcfWindowSliderBase::setup(parser, wsize, wstep, start_pos, stop_pos, max_missing, mask);
        _next_start = start_pos;
    }

    void VcfWindowSlider::next_window() {
        // define bounds and position of next window
        _win_start = _next_start;
        _win_stop = _win_start + _wsize;
        if (_win_stop >= _stop_pos) {
            _win_stop = _stop_pos;
        }
        _next_start += _wstep;
        if (_next_start > _stop_pos) _next_start = _stop_pos;

        // update window
        _slide_window();

        // go to start of next window if step>size
        if (_status < 2) { // if status is 2/3, we changed chromosome or reached end (good->false)
            while (_read(_next_start) == 0);
            if (_next_start != _stop_pos && _status == 1) { // if reached _win_stop, status is left to 1 (good->false)
                _status = 0; // if not reached _win_stop and status != 2, _status set to 0 (good->true)
            }
        }
    }

    VcfWindowSliderPerSite::VcfWindowSliderPerSite() {
    }

    VcfWindowSliderPerSite::~VcfWindowSliderPerSite() {
    }

    void VcfWindowSliderPerSite::next_window() {

        // pop sites from start of window
        for (unsigned long i=0; i<_wstep; i++) {
            if (_first_site == NULL) break; // for first window or if step>size
            _first_site = _first_site->pop_front();
            _num--;
        }
        if (_first_site == NULL) _last_site = NULL;

        // add sites at the end of window
        while (_num < _wsize && _read(_stop_pos) == 0) _add(); // 2020.08.17: added == 0 (flag should be 0 to add site)

        // set start/stop positions of current window
        if (_num > 0) {
            _win_start = _first_site->get_pos();
            _win_stop = _last_site->get_pos() + 1;
        }
        else {
            throw EggRuntimeError("empty window (this should not occur)");
        }

        if (_status == 0) {

            // check that there is at least one site left
            _read(_stop_pos);
            _vcf->unread();

            // go to start of next window if step>size
            for (unsigned long i=_wsize; i<_wstep; i++) {
                if (_read(_stop_pos)) break;
            }
        }
    }

    VcfWindowBED::VcfWindowBED() {
        _bed = NULL;
        _bed_idx = 0;
    }

    VcfWindowBED::~VcfWindowBED() {
    }

    void VcfWindowBED::setup(VcfParser& parser, BedParser& bed,
                            unsigned int max_missing, unsigned int mask) {
        setup_base(parser, max_missing, mask);
        _bed = &bed;
        _bed_idx = 0;

        /* if there is no index, check that
                - all windows are with the same (current) chromosome
                - all windows are with increasing start position */
        if (!_vcf->get_index().has_data() && _bed->n_bed_data() > 0) {
            _vcf->read(true);
            const char * chr = _bed->get_chrom(0);
            if (strcmp(_vcf->chromosome(), chr)) {
                throw EggArgumentValueError("cannot jump to a different chromosome without a VCF index");
            }
            _vcf->unread();
            unsigned int c = 0;
            for (unsigned int i=0; i<_bed->n_bed_data(); i++) {
                if (strcmp(_bed->get_chrom(i), chr)) {
                    throw EggArgumentValueError("cannot jump to a different chromosome without a VCF index");
                }
                if (_bed->get_start(i) < c) {
                    throw EggArgumentValueError("BED windows must be sorted if there is no VCF index");
                }
                c = _bed->get_start(i);
            }
            if ((strlen(chr)+1) > _c_chrom) {
                _chrom = (char *) realloc(_chrom, (strlen(chr)+1) * sizeof(char));
                if (!_chrom) throw EGGMEM;
                _c_chrom = strlen(chr) + 1;
            }
            strcpy(_chrom, chr);
        }
    }

    bool VcfWindowBED::good() const {
        #ifdef DEBUG
        if (_bed == NULL) throw EggRuntimeError("setup has not been called");
        #endif        
        return _bed_idx < _bed->n_bed_data();
    }

    void VcfWindowBED::next_window() {
        if (_vcf->get_index().has_data()) {

            const char * chr = _bed->get_chrom(_bed_idx);
            _vcf->get_index().go_to(chr, _bed->get_start(_bed_idx));

            // update chromosome
            if (strcmp(chr, _chrom)) {
                if ((strlen(chr)+1) > _c_chrom) {
                    _chrom = (char *) realloc(_chrom, (strlen(chr)+1) * sizeof(char));
                    if (!_chrom) throw EGGMEM;
                    _c_chrom = strlen(chr) + 1;
                }
                strcpy(_chrom, chr);
            }

            // reset completely the window
            while (_first_site != NULL) _first_site = _first_site->pop_front();
            _last_site = NULL;
            _num = 0;
            _status = 0;
        }
        _win_start = _bed->get_start(_bed_idx);
        _win_stop = _bed->get_end(_bed_idx);
        if (_vcf->good() && _status != 2)  _slide_window(); // don't read anything if eof reached or if changed chromosome
        _bed_idx++;
    }
}
