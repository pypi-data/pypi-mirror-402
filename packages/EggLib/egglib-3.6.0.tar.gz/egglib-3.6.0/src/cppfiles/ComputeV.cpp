/*
    Copyright 2016-2021 Stéphane De Mita

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
#include "egglib.hpp"
#include "ComputeV.hpp"
#include "FreqHolder.hpp"
#include "SiteHolder.hpp"

namespace egglib {

    ComputeV::ComputeV() {
        reset();
    }

    void ComputeV::reset() {
        _num_sites = 0;
        _num_sites_m = 0;
        _num_sites_rst = 0;
        _acc_V = 0.0;
        _acc_Ar = 0.0;
        _acc_M = 0.0;
        _cur_V = UNDEF;
        _cur_Ar = UNDEF;
        _cur_M = UNDEF;
        _cur_Rst = UNDEF;
        _Sw = 0.0;
        _Sbar = 0.0;
        _maf = 0.0;
    }

    ComputeV::~ComputeV() {
    }

    void ComputeV::set_maf(double maf) {
        _maf = maf;
    }

    bool ComputeV::compute(const FreqHolder& frq, AbstractTemplateAlphabet<int>& alph) {
        const FreqSet& set = frq.frq_ingroup();
        if (set.nseff() < 2) return UNDEF;
        double sum = 0.0;
        double sum2 = 0.0;
        unsigned int num_all = 0;
        int min_allele = MISSINGDATA;
        int max_allele = -MISSINGDATA;
        unsigned int nseff = 0;
        for (unsigned int i=0; i<frq.num_alleles(); i++) {
            int a = alph.get_value(frq.allele(i));
            if (static_cast<double>(set.frq_all(i)) / set.nseff() < _maf) continue;
            sum += 1.0 * set.frq_all(i) * a;
            sum2 += 1.0 * set.frq_all(i) * a * a;
            num_all++;
            if (a < min_allele) min_allele = a;
            if (a > max_allele) max_allele = a;
            nseff += set.frq_all(i);
        }
        if (num_all == 0 || nseff < 2) {
            _cur_V = UNDEF;
            _cur_Ar = UNDEF;
            _cur_M = UNDEF;
            _cur_Rst = UNDEF;
            return false;
        }

        sum /= nseff;
        _cur_V = sum2 / nseff - sum * sum;
        _cur_V *= nseff / (nseff-1.0); 
        if (_cur_V < 0) throw EggRuntimeError("negative variance!");

        _num_sites++;
        _acc_V += _cur_V;
        _cur_Ar = max_allele - min_allele;
        _acc_Ar += _cur_Ar;
        if (_cur_Ar == 0 && num_all > 1) throw EggRuntimeError("several alleles but they are identical");
        if (_cur_Ar > 0) {
            _num_sites_m++;
            _cur_M = num_all / (_cur_Ar + 1);
            _acc_M += _cur_M;
        }
        else {
            _cur_M = UNDEF;
        }

        // compute Rst
        if (_cur_V == 0.0 || frq.num_populations() < 2) {
            _cur_Rst = UNDEF;
        }
        else {
            unsigned int a, p;
            unsigned int np = 0;
            double acc = 0.0;
            double sum_V = 0.0; // to compute V without populations with < 2 samples
            double sum2_V = 0.0;
            unsigned int ns = 0;
            for (unsigned int pop=0; pop<frq.num_populations(); pop++) {
                num_all = 0;
                sum = 0.0;
                sum2 = 0.0;
                nseff = 0;
                for (unsigned int i=0; i<frq.num_alleles(); i++) {
                    a = frq.allele(i);
                    p = frq.frq_population(pop).frq_all(i);
                    if (static_cast<double>(p) / set.nseff() < _maf) continue;
                    sum += p * a;
                    sum2 += p * a * a;
                    num_all++;
                    nseff += p;
                }
                if (num_all > 0 && nseff > 1) {
                    np++;
                    acc += (sum2/nseff - (sum * sum / (nseff * nseff))) * nseff / (nseff - 1.0);
                    sum_V += sum;
                    sum2_V += sum2;
                    ns += nseff;
                }
            }
            if (np > 1) {
                sum_V /= ns;
                double V2 = sum2_V/ns - sum_V * sum_V;
                V2 *= ns / (ns-1.0);
                _num_sites_rst++;
                _Sbar += V2;
                _Sw += acc / np;
                _cur_Rst = (V2 - acc / np) / (V2);
            }
        }
        return true;
    }

    unsigned int ComputeV::num_sites() const {
        return _num_sites;
    }

    unsigned int ComputeV::num_sites_m() const {
        return _num_sites_m;
    }

    unsigned int ComputeV::num_sites_rst() const {
        return _num_sites_rst;
    }

    double ComputeV::average_V() const {
        if (_num_sites == 0) return UNDEF;
        return _acc_V / _num_sites;
    }

    double ComputeV::average_Ar() const {
        if (_num_sites == 0) return UNDEF;
        return _acc_Ar / _num_sites;
    }

    double ComputeV::average_M() const {
        if (_num_sites_m == 0) return UNDEF;
        return _acc_M / _num_sites_m;
    }

    double ComputeV::average_Rst() const {
        if (_num_sites_rst == 0) return UNDEF;
        return (_Sbar-_Sw)/_Sbar;
    }

    double ComputeV::curr_V() const {
        return _cur_V;
    }

    double ComputeV::curr_Ar() const {
        return _cur_Ar;
    }

    double ComputeV::curr_M() const {
        return _cur_M;
    }

    double ComputeV::curr_Rst() const {
        return _cur_Rst;
    }
}
