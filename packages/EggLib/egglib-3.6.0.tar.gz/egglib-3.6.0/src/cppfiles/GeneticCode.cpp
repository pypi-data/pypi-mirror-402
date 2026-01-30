/*
    Copyright 2013-2021 Stéphane De Mita, Mathieu Siol

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
#include "GeneticCode.hpp"
#include "SiteHolder.hpp"

namespace egglib {

    const char * GeneticCode::name() const {
        return _names[_index];
    }

    GeneticCode::GeneticCode(unsigned int index) {
        set_code(index);
    }

    unsigned int GeneticCode::get_code() const {
        return _code;
    }

    void GeneticCode::set_code(unsigned int index) {
        _index = index;
        _code = _codes[index];
        _shift = index * 4913;
    }

    int GeneticCode::translate(int codon) {
        if (codon >= 0) return _aa[_shift + codon];
        else return _aa[_shift + 63 - codon];
    }

    bool GeneticCode::start(int codon) const {
        if (codon >= 0) return _start[_shift + codon] == 'M';
        else return _start[_shift + 63 - codon] == 'M';
    }

    bool GeneticCode::stop(int codon) const {
        if (codon >= 0) return _start[_shift + codon] == '*';
        else return _start[_shift + 63 - codon] == '*';
    }

    bool GeneticCode::is_stop_unsmart(int codon) const {
        if (codon >= 0) return _start[_shift + codon] == '*';
        else return false;
    }

    double GeneticCode::NSsites(int codon, bool ignorestop) const {
        return ignorestop ? _NS2[_shift + codon] : _NS1[_shift + codon];
    }

    double GeneticCode::Ssites(int codon, bool ignorestop) const {
        return ignorestop ? _S2[_shift + codon] : _S1[_shift + codon];
    }

    double GeneticCode::NSsites(const SiteHolder& site, unsigned int& num_samples, bool ignorestop) const {
        num_samples = 0;
        unsigned int ns = site.get_ns();
        double NS = 0.0;
        for (unsigned int i=0; i<ns; i++) {
            int a = site.get_sample(i);
            if (a<0 || a>63) continue;
            if (ignorestop && _aa[_shift + a] == 20) continue;
            num_samples++;
            NS += ignorestop? _NS2[_shift + a] : _NS1[_shift + a];
        }
        return NS;
    }

    double GeneticCode::Ssites(const SiteHolder& codons, unsigned int& num_samples, bool ignorestop) const {
        num_samples = 0;
        unsigned int ns = codons.get_ns();
        double S = 0.0;
        for (unsigned int i=0; i<ns; i++) {
            int a = codons.get_sample(i);
            if (a < 0 || a > 63) continue;
            if (ignorestop && _aa[_shift + a] == 20) continue;
            num_samples++;
            S += ignorestop? _S2[_shift + a] : _S1[_shift + a];
        }
        return S;
    }

#include "GeneticCode.epp"

}
