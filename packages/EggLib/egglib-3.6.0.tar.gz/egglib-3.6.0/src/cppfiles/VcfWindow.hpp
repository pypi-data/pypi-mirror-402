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

#ifndef EGGLIB_WINDOW_HPP
#define EGGLIB_WINDOW_HPP

#include "egglib.hpp"
#include "SiteHolder.hpp"
#include "VCF.hpp"
#include "BED.hpp"

namespace egglib {

    class WPool;

    ///< Class for sites within a double-linked list
    class WSite {
        private:
            WSite * _next;
            WSite * _prev;
            unsigned long _pos;
            SiteHolder _site;
            StringAlphabet _salph;
            CustomStringAlphabet _csalph;
            StringAlphabet * _which_alphabet; // address of the right alphabet (salph, csalph, or NULL if DNA)
            WPool * _pool;

            WSite() {}
            WSite(const WSite& src) {}
            WSite& operator=(const WSite* src) { return *this; }

        public:
            WSite(WPool *); ///< Constructor
            ~WSite(); ///< Destructor
            SiteHolder& site(); ///< Get the included site object
            void set_pos(unsigned long); ///< Set site position
            unsigned long get_pos() const; ///< Get site position
            void set_alphabet(VcfParser *); ///< use vcf parser to define alphabet
            StringAlphabet * alphabet(); ///< Get the corresponding alphabet (DNA alphabet or internal one)
            WSite * next(); ///< Get next site
            WSite * prev(); ///< Get previous site
            WSite * push_back(WSite *); ///< Add site to the end, return new end
            WSite * pop_front(); ///< Disconnect first, return it to pool, return its follower
            WSite * pop_back(); ///< Disconnect last, return it to pool, return its predecessor
            void reset(unsigned int pl); ///< Reset values
            void init(); ///< Set pointers to NULL
    };

    ///< WSite pool
    class WPool {
        private:
            WSite ** _cache;
            WSite ** _pool;
            unsigned int _c_cache;
            unsigned int _c_pool;
            unsigned int _n_pool;
            WPool(const WPool& src) {}
            WPool& operator=(const WPool& src) { return *this; }

        public:
            WPool();
            ~WPool();
            WSite * get();
            void put(WSite *);
    };

    /// Pure virtual base class for sliding windows
    class VcfWindowBase {
        private:
            VcfWindowBase(const VcfWindowBase& src) {}
            VcfWindowBase& operator=(const VcfWindowBase& src) { return *this; }

        protected:
            WPool _pool;
            WSite * _first_site;            // first site of current window
            WSite * _last_site;             // last site of current window
            unsigned int _num;              // number of sites
            unsigned int _mask;             // mask for selecting allele types
            unsigned int _max_missing; // SiteHolder argument
            VcfParser * _vcf;
            char * _chrom;              // current chromosome
            unsigned int _c_chrom;
            unsigned long _win_start;  // start of current window
            unsigned long _win_stop;    // stop of current window
            int _status;                // 0: default or have successfully read a site
                                        // 1: reached set limit
                                        // 2: changed chromosome
                                        // 3: end of file reached
            void _add();
            void _slide_window();   // move window based in _win_start and _win_stop
            int _read(unsigned long); // read one site and set status
                                       // return: staus after operation

        public:
            VcfWindowBase(); ///< Constructor
            virtual ~VcfWindowBase(); ///< Destructor
            void setup_base(VcfParser&, unsigned int max_missing, unsigned int mask); ///< Setup a new sliding window
            const char * chromosome() const; ///< Get chromosome
            virtual void next_window() = 0; ///< Load the next window
            unsigned int num_samples() const; ///< Number of samples
            unsigned int num_sites() const; ///< Number of actual sites (from vcf)
            unsigned long win_start() const; ///< Window start bound
            unsigned long win_stop() const; ///< Window stop bound
            const WSite * first_site() const; ///< Get first site (NULL if no site at all)
            const WSite * last_site() const; ///< Get last site (NULL if no site at all)
            virtual bool good() const = 0; ///< False if sliding has completed
            const WSite * get_site(unsigned int) const; ///< Get a random site (slower -- there must be enough sites)
    };

    /// base class for VCF windows when window bounds are computed automatically
    class VcfWindowSliderBase : public VcfWindowBase {
        private:
            VcfWindowSliderBase(const VcfWindowSliderBase&) {}
            VcfWindowSliderBase& operator=(const VcfWindowSliderBase&) {return * this;}

        protected:
            unsigned int _wsize;       // window size
            unsigned int _wstep;       // window step
            unsigned long _start_pos;  // where to start the sliding window
            unsigned long _stop_pos;   // where to stop the sliding window (not included)

        public:
            VcfWindowSliderBase();
            virtual ~VcfWindowSliderBase();
            virtual void setup(VcfParser& parser, unsigned int wsize, unsigned int wstep,
                unsigned long start_pos, unsigned long stop_pos,
                unsigned int max_missing, unsigned int mask);
            virtual bool good() const;
    };

    /// VCF sliding window with bounds as genomic bp
    class VcfWindowSlider : public VcfWindowSliderBase {
        private:
            VcfWindowSlider(const VcfWindowSlider&) {}
            VcfWindowSlider& operator=(const VcfWindowSlider&) {return * this;}
            unsigned long _next_start;
        public:
            VcfWindowSlider();
            virtual ~VcfWindowSlider();
            virtual void setup(VcfParser& parser, unsigned int wsize, unsigned int wstep,
                unsigned long start_pos, unsigned long stop_pos,
                unsigned int max_missing, unsigned int mask);
            virtual void next_window();
    };

    /// VCF sliding window with bounds as site numbers
    class VcfWindowSliderPerSite : public VcfWindowSliderBase {
        private:
            VcfWindowSliderPerSite(const VcfWindowSliderPerSite&) {}
            VcfWindowSliderPerSite& operator=(const VcfWindowSliderPerSite&) {return * this;}
        public:
            VcfWindowSliderPerSite();
            virtual ~VcfWindowSliderPerSite();
            virtual void next_window();
    };

    /// VCF windows based on bounds from a BED file
    class VcfWindowBED : public VcfWindowBase {
        private:
            VcfWindowBED(const VcfWindowBED&) {}
            VcfWindowBED& operator=(const VcfWindowBED&) {return * this;}
            BedParser * _bed;
            unsigned int _bed_idx;
        public:
            VcfWindowBED();
            virtual ~VcfWindowBED();
            void setup(VcfParser& parser, BedParser&, unsigned int max_missing, unsigned int mask);
            virtual void next_window();
            virtual bool good() const;
    };
}

#endif
