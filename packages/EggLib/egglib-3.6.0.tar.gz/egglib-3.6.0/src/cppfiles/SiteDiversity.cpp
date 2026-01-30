/*
    Copyright 2012-2025 Stéphane De Mita, Mathieu Siol

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
#include "SiteDiversity.hpp"
#include "FreqHolder.hpp"
#include <cstdlib>
#include <cstring>

#define SETFLAG(i) _flag |= (1<<(i))
#define CHECKFLAG(i) _flag & (1<<(i))

namespace egglib {

    void SiteDiversity::init() {
        _npop_c = 0;
        _He_pop = NULL;
        _maf_pop = NULL;
        _ni = NULL;
        _pi = NULL;
        _clu_flags = NULL;
        _r_c = 0;
        _pairdiff_inter = NULL;
        _glob_c = 0;
        _glob_alleles = NULL;
        _der = NULL;
        _c_der = 0;
        _maf_filter = 0.0;
        _f3focus = 0;
        _f4flag = 0;
        toggle_off();
        reset();
    }

    void SiteDiversity::f3focus(unsigned int v) {
        switch (v) {
            case 0:
                _f3focus = 0b100100; // 0 1 2
                break;
            case 1:
                _f3focus = 0b100001; // 1 0 2
                break;
            case 2:
                _f3focus = 0b010010; // 2 0 1
                break;
            default:
                _f3focus = 0;
        }
    }

    void SiteDiversity::f4flag(bool b) {
        _f4flag = b;
    }

    void SiteDiversity::alloc() {

        if (_npop > _npop_c) {
            _He_pop = (double *) realloc(_He_pop, _npop * sizeof(double));
            if (!_He_pop) throw EGGMEM;

            _maf_pop = (double *) realloc(_maf_pop, _npop * sizeof(double));
            if (!_maf_pop) throw EGGMEM;

            if (_npop > 1) {
                _pairdiff_inter = (double **) realloc(_pairdiff_inter, (_npop-1) * sizeof(double *));
                if (!_pairdiff_inter) throw EGGMEM;
            }

            for (unsigned int i=_npop_c>0?_npop_c-1:0; i<_npop-1; i++) _pairdiff_inter[i] = NULL;  // the ternary operation is due to the fact that only _npop-1 blocks are allocated

            for (unsigned int i=0; i<_npop-1; i++) {
                _pairdiff_inter[i] = (double *) realloc(_pairdiff_inter[i], (_npop-i-1) * sizeof(double));
                if (!_pairdiff_inter[i]) throw EGGMEM;
            }

            _npop_c = _npop;
        }
    }

    void SiteDiversity::free() {
        if (_He_pop) ::free(_He_pop);
        if (_ni) ::free(_ni);
        if (_pi) ::free(_pi);
        if (_clu_flags) ::free(_clu_flags);
        if (_npop_c > 1) {
            for (unsigned int i=0; i<_npop_c-1; i++) {
                if (_pairdiff_inter[i]) ::free(_pairdiff_inter[i]);
            }
        }
        if (_pairdiff_inter) ::free(_pairdiff_inter);
        if (_glob_alleles) ::free(_glob_alleles);
        if (_der) ::free(_der);
        if (_maf_pop) ::free(_maf_pop);
    }

    SiteDiversity::SiteDiversity() {
        init();
    }

    SiteDiversity::~SiteDiversity() {
        free();
    }

    void SiteDiversity::reset() {
        _npop = 0;
        _npop_eff1 = 0;
        _npop_eff2 = 0;
        _npop_eff3 = 0;
        _nclu_eff = 0;
        _A_glo = 0.0;
        _A_tot = 0.0;
        _A_ing = 0.0;
        _A_out = 0.0;
        _S_tot = 0.0;
        _S_der = 0.0;
        _R = 0;
        _He = 0.0;
        _thetaIAM_acc = 0.0;
        _thetaSMM_acc = 0.0;
        _Ho = 0.0;
        _pairdiff = 0.0;
        _n_der = 0;
        _a = 0.0;
        _b = 0.0;
        _c = 0.0;
        _a0 = 0.0;
        _b1 = 0.0;
        _b2 = 0.0;
        _c0 = 0.0;
        _n = 0.0;
        _d = 0.0;
        _orientable = false;
        _Hst = 0.0;
        _Gst = 0.0;
        _Gste = 0.0;
        _JostD = 0.0;
        _ns = 0.0;
        _nso = 0.0;
        _flag = 0;
        _nsites1 = 0;
        _nsites2 = 0;
        _nsites3 = 0;
        _nsites4 = 0;
        _nsites5 = 0;
        _nsites5A = 0;
        _nsites6 = 0;
        _nsites7 = 0;
        _nsites8 = 0;
        _nsites9 = 0;
        _nsites10 = 0;
        _nsites11 = 0;
        _nsites12 = 0;
        _nsites13 = 0;
        _nsites14 = 0;
        _nsites15 = 0;
        _ns_acc = 0.0;
        _nso_acc = 0.0;
        _Aglob_acc = 0.0;
        _Aing_acc = 0.0;
        _Aout_acc = 0.0;
        _S_acc = 0.0;
        _R_acc = 0.0;
        _pairdiff_acc = 0.0;
        _He_acc = 0.0;
        _Ho_acc = 0.0;
        _Sd_acc = 0.0;
        _a_acc = 0.0;
        _b_acc = 0.0;
        _c_acc = 0.0;
        _a0_acc = 0.0;
        _b1_acc = 0.0;
        _b2_acc = 0.0;
        _c0_acc = 0.0;
        _n_acc = 0.0;
        _d_acc = 0.0;
        _Hst_acc = 0.0;
        _Gst_acc = 0.0;
        _Gste_acc = 0.0;
        _D_acc = 0.0;
        _thetaIAM_acc = 0.0;
        _thetaSMM_acc = 0.0;
        _f2_acc = 0.0;
        _f3_acc = 0.0;
        _f4_acc = 0.0;
        _Dp_den_acc = 0.0;
        _maf = 0.0;
    }

    unsigned int SiteDiversity::k() const         { return _npop; }
    unsigned int SiteDiversity::npop_eff1() const { return _npop_eff1; }
    unsigned int SiteDiversity::npop_eff2() const { return _npop_eff2; }
    unsigned int SiteDiversity::npop_eff3() const { return _npop_eff3; }
    unsigned int SiteDiversity::nclu_eff() const  { return _nclu_eff; }
    double SiteDiversity::ns() const              { return _ns; }
    double SiteDiversity::nso() const              { return _nso; }
    double SiteDiversity::Aglob() const           { return _A_glo; }
    double SiteDiversity::Aout() const            { return _A_out; }
    int SiteDiversity::global_allele(unsigned int i) const { return _glob_alleles[i]; }
    double SiteDiversity::Aing() const            { return _A_ing; }
    double SiteDiversity::S() const               { return _S_tot; }
    double SiteDiversity::Sd() const              { return _S_der; }
    double SiteDiversity::R() const               { return _R; }
    double SiteDiversity::He() const              { return _He; }
    double SiteDiversity::Ho() const              { return _Ho; }
    double SiteDiversity::pairdiff() const        { return _pairdiff; }
    double SiteDiversity::maf() const             { return _maf; }
    double SiteDiversity::maf_pop(unsigned int i) const { return _maf_pop[i]; }
    unsigned int SiteDiversity::num_pop() const   { return _npop; }

    double SiteDiversity::pairdiff_inter(unsigned int pop1, unsigned int pop2) const {
        if (pop1 < pop2) return _pairdiff_inter[pop1][pop2-pop1-1];
        else return _pairdiff_inter[pop2][pop1-pop2-1];
    }

    double SiteDiversity::He_pop(unsigned int pop) const { return _He_pop[pop]; }
    bool SiteDiversity::orientable() const               { return _orientable; }
    unsigned int SiteDiversity::num_derived() const      { return _n_der; }
    double SiteDiversity::derived(unsigned int i) const  { return _der[i]; }
    double SiteDiversity::a() const                      { return _a; }
    double SiteDiversity::b() const                      { return _b; }
    double SiteDiversity::c() const                      { return _c; }
    double SiteDiversity::a0() const                     { return _a0; }
    double SiteDiversity::b1() const                     { return _b1; }
    double SiteDiversity::b2() const                     { return _b2; }
    double SiteDiversity::c0() const                     { return _c0; }
    double SiteDiversity::n() const                      { return _n; }
    double SiteDiversity::d() const                      { return _d; }
    double SiteDiversity::f2() const                     { return _f2; }
    double SiteDiversity::f3() const                     { return _f3; }
    double SiteDiversity::f4() const                     { return _f4; }
    double SiteDiversity::Dp() const                     { return _Dp; }
    double SiteDiversity::Hst() const                    { return _Hst; }
    double SiteDiversity::Gst() const                    { return _Gst; }
    double SiteDiversity::Gste() const                   { return _Gste; }
    double SiteDiversity::D() const                      { return _JostD; }
    double SiteDiversity::thetaIAM() const               { return _thetaIAM; }
    double SiteDiversity::thetaSMM() const               { return _thetaSMM; }
    unsigned int SiteDiversity::nsites1() const          { return _nsites1; }
    unsigned int SiteDiversity::nsites2() const          { return _nsites2; }
    unsigned int SiteDiversity::nsites3() const          { return _nsites3; }
    unsigned int SiteDiversity::nsites4() const          { return _nsites4; }
    unsigned int SiteDiversity::nsites5() const          { return _nsites5; }
    unsigned int SiteDiversity::nsites6() const          { return _nsites6; }
    unsigned int SiteDiversity::nsites7() const          { return _nsites7; }
    unsigned int SiteDiversity::nsites8() const          { return _nsites8; }
    unsigned int SiteDiversity::nsites9() const          { return _nsites9; }
    unsigned int SiteDiversity::nsites10() const         { return _nsites10; }
    unsigned int SiteDiversity::nsites11() const         { return _nsites11; }
    unsigned int SiteDiversity::nsites12() const         { return _nsites12; }

    void SiteDiversity::toggle_off() {
        _flag_fdip = false;
        _flag_fhap = false;
        _flag_fhie = false;
        _flag_h = false;
    }

    void SiteDiversity::toggle_fstats_diplo() {
        _flag_fdip = true;
    }

    void SiteDiversity::toggle_fstats_haplo() {
        _flag_fhap = true;
    }

    void SiteDiversity::toggle_fstats_hier() {
        _flag_fhie = true;
    }

    void SiteDiversity::toggle_hstats() {
        _flag_h = true;
    }

    void SiteDiversity::set_maf(double maf) {
        _maf_filter = maf;
    }

    unsigned long SiteDiversity::flag() const {
        return _flag;
    }

    unsigned long SiteDiversity::process(const FreqHolder& frq) {
        _flag = 0;
        _stats(frq);
        if (CHECKFLAG(1)) {
            if (_flag_fdip) _fstats_diplo(frq);
            if (_flag_fhap) _fstats_haplo(frq);
            if (_flag_fhie) _fstats_hier(frq);
            if (_flag_h) _hstats(frq);
            SETFLAG(9);
        }
        return _flag;
    }

    void SiteDiversity::_stats(const FreqHolder& freqs) {
        _npop = freqs.num_populations();
        alloc();

        unsigned int pi, po;

        // global statistics
        _ns = freqs.frq_ingroup().nseff();
        _nso = freqs.frq_outgroup().nseff();

        SETFLAG(0);
        _nsites1++;
        _ns_acc += _ns;
        _nso_acc += _nso;
        if (_ns < 2) return;

        _A_tot = freqs.num_alleles(); // there can be "ghost" alleles
        _A_glo = 0;
        _A_ing = 0;
        _A_out = 0;
        _S_tot = 0;
        _pairdiff = 0.0;
        _maf = 1.0;

        for (unsigned int all = 0; all<_A_tot; all++) {
            pi = freqs.frq_ingroup().frq_all(all);
            if (pi / _ns < _maf_filter) return;
            if (pi / _ns < _maf) {
                _maf = pi / _ns;
                for (unsigned int i=0; i<_npop; i++) {
                    if (freqs.frq_population(i).nseff() == 0) _maf_pop[i] = UNDEF;
                    else _maf_pop[i] = 1.0 * freqs.frq_population(i).frq_all(all) / freqs.frq_population(i).nseff();
                }
            }
            po = freqs.frq_outgroup().frq_all(all);
            _pairdiff += 1.0 * pi * pi / (_ns * _ns);
            if (pi > 0) {
                _A_ing++;
                if (pi == 1) {
                    _S_tot++;
                }
            }
            if (po > 0) _A_out++;
            if (pi > 0 || po > 0) {
                _A_glo++;
                if (_A_glo > _glob_c) {
                    _glob_alleles = (int *) realloc(_glob_alleles, _A_glo * sizeof(int));
                    if (!_glob_alleles) throw EGGMEM;
                    _glob_c = _A_glo;
                }
                _glob_alleles[static_cast<unsigned int>(_A_glo)-1] = freqs.allele(all);
            }
        }

        SETFLAG(1);
        _nsites2++;

        if (freqs.num_populations() == 2) {
            unsigned int n1, n2;
            double p1, p2;
            _f2 = 0;
            switch ((unsigned int) _A_ing) {
                case 2:
                    n1 = freqs.frq_population(0).nseff();
                    n2 = freqs.frq_population(1).nseff();
                    if (n1 < 2 || n2 < 2) break;
                    p1 = 1.0 * freqs.frq_population(0).frq_all(0) / n1;
                    p2 = 1.0 * freqs.frq_population(1).frq_all(0) / n2;
                    _f2 = (p1-p2) * (p1-p2) - p1*(1-p1)/(n1-1) - p2*(1-p2)/(n2-1);
                    _f2_acc += _f2;

                case 1:
                    _nsites13++;
                    SETFLAG(15);
            }
        }

        if (freqs.num_populations() == 3 && _f3focus != 0) {
            unsigned int n1, n2, n3;
            double p1, p2, p3;
            _f3 = 0;

            switch ((unsigned int) _A_ing) {
                case 2:
                    n1 = freqs.frq_population(_f3focus&3).nseff();
                    n2 = freqs.frq_population((_f3focus&12)>>2).nseff();
                    n3 = freqs.frq_population((_f3focus&48)>>4).nseff();
                    if (n1 < 2 || n2 < 2 || n3 < 2) break;
                    p1 = 1.0 * freqs.frq_population(_f3focus&3).frq_all(0) / n1;
                    p2 = 1.0 * freqs.frq_population((_f3focus&12)>>2).frq_all(0) / n2;
                    p3 = 1.0 * freqs.frq_population((_f3focus&48)>>4).frq_all(0) / n3;
                    _f3 = (p1-p2) * (p1-p3) - p1*(1-p1)/(n1-1);
                    _f3_acc += _f3;

                case 1:
                    _nsites14++;
                    SETFLAG(16);
            }
        }

        if (_f4flag) {
            unsigned int n[4];
            double p[4];
            double Dp_den;
            _f4 = 0;
            _Dp = 0;

            switch ((unsigned int) _A_ing) {
                case 2:
                    n[0] = freqs.frq_population(0).nseff();
                    n[1] = freqs.frq_population(1).nseff();
                    n[2] = freqs.frq_population(2).nseff();
                    n[3] = freqs.frq_population(3).nseff();
                    if (n[0] < 2 || n[1] < 2 || n[2] < 2 || n[3] < 2) break;
                    p[0] = 1.0 * freqs.frq_population(0).frq_all(0) / n[0];
                    p[1] = 1.0 * freqs.frq_population(1).frq_all(0) / n[1];
                    p[2] = 1.0 * freqs.frq_population(2).frq_all(0) / n[2];
                    p[3] = 1.0 * freqs.frq_population(3).frq_all(0) / n[3];
                    _f4 = (p[0] - p[1]) * (p[2] - p[3]);
                    _f4_acc += _f4;
                    Dp_den = (p[0]+p[1]-2*p[0]*p[1])*(p[2]+p[3]-2*p[2]*p[3]);
                    if (Dp_den > 0) {
                        _Dp = _f4 / Dp_den;
                        _Dp_den_acc += Dp_den;
                        SETFLAG(18);
                    }
                case 1:
                    _nsites15++;
                    SETFLAG(17);
            }
        }

        if (_A_ing > 1) SETFLAG(10);
        _pairdiff = 1 - _pairdiff;
        _He = _pairdiff * _ns / (_ns - 1);
        if (_He < 1.0) {
            _nsites3++;
            SETFLAG(2);
            _thetaIAM = _He / (1.0-_He);
            _thetaSMM = 0.5*(1/((1.0-_He)*(1.0-_He))-1.0);
            _thetaIAM_acc += _thetaIAM;
            _thetaSMM_acc += _thetaSMM;
        }
        if (freqs.ploidy() > 1) {
            _nsites4++;
            SETFLAG(3);
            _Ho = static_cast<double>(freqs.frq_ingroup().tot_het()) / freqs.frq_ingroup().nieff();
            _Ho_acc += _Ho;

            // compute between-individual number of differences
            /* REMOVED because not enough tested and probably not so useful
            unsigned int K = freqs.ploidy();
            double pdinter = _pairdiff * (_ns*_ns/2.0);   // to compute Hi (see below)
            for (unsigned int i=0; i<freqs.num_genotypes(); i++) {
                for (unsigned int j=0; j<K; j++) {
                    for (unsigned int k=j+1; k<K; k++) {
                        if (freqs.genotype_item(i,j) != freqs.genotype_item(i,k)) {
                            pdinter -= freqs.frq_ingroup().frq_gen(i);
                        }
                    }
                }
            }
            _Hi = pdinter / (freqs.frq_ingroup().nieff() * (freqs.frq_ingroup().nieff()-1) / 2 * K * K);
            */
        }

        _R = (double) (_A_ing - 1) / (_ns - 1);

        _Aglob_acc += _A_glo;
        _Aing_acc += _A_ing;
        _S_acc += _S_tot;
        _R_acc += _R;
        _pairdiff_acc += _pairdiff;
        _He_acc += _He;

        // per population statistics
        _npop_eff1 = 0;

        for (unsigned int pop1=0; pop1<_npop; pop1++) {

            _He_pop[pop1] = 0.0;
            if (pop1<_npop-1) {
                for (unsigned int pop2=0; pop2<_npop-pop1-1; pop2++) {
                    _pairdiff_inter[pop1][pop2] = 0.0;
                }
            }

            // consider populations with >= 1 samples only
            if (freqs.frq_population(pop1).nseff() > 1) {

                _npop_eff1++;

                for (unsigned int all = 0; all < _A_tot; all++) {
                    double p1 = 1.0 * freqs.frq_population(pop1).frq_all(all) / freqs.frq_population(pop1).nseff();
                    _He_pop[pop1] += p1 * p1;
                    if (p1 > 0 && pop1 < _npop-1) {
                        for (unsigned int pop2=pop1+1; pop2<_npop; pop2++) {
                            if (freqs.frq_population(pop2).nseff() > 1) {
                                _pairdiff_inter[pop1][pop2-pop1-1] += 
                                        p1 * freqs.frq_population(pop2).frq_all(all)
                                            / freqs.frq_population(pop2).nseff();
                            }
                        }
                    }
                }
                _He_pop[pop1] = (1 - _He_pop[pop1]) * freqs.frq_population(pop1).nseff() / (freqs.frq_population(pop1).nseff() - 1);

                for (unsigned int pop2=0; pop2<_npop-pop1-1; pop2++) {
                    if (freqs.frq_population(pop2).nseff() > 1) {
                        _pairdiff_inter[pop1][pop2] = 1.0 - _pairdiff_inter[pop1][pop2]; // unbias here, if necessary
                    }
                }
            }
        }

        // check that exactly one, not outgroup-specific, allele in outgroup
        _orientable = false;
        for (unsigned int all=0; all<_A_tot; all++) {
            if (freqs.frq_outgroup().frq_all(all) > 0) {
                if (_orientable) {
                    _orientable = false;
                    break;
                }
                if (freqs.frq_ingroup().frq_all(all) == 0) {
                    _orientable = false;
                    break;
                }
                _orientable = true;
            }
        }

        // derived allele frequencies
        _S_der = 0;
        _n_der = 0;

        if (freqs.frq_outgroup().nseff() >= 2) {
            _Aout_acc += _A_out;
            SETFLAG(14);
            _nsites5A++;
        }

        if (_orientable) { // one outgroup is required

            // sum derived frequencies
            for (unsigned int all=0; all<_A_tot; all++) {
                if (freqs.frq_ingroup().frq_all(all) > 0 && freqs.frq_outgroup().frq_all(all) == 0) {
                    _n_der++;
                    if (_n_der > _c_der) {
                        _der = (double *) realloc(_der, _n_der * sizeof(double));
                        if (!_der) throw EGGMEM;
                        _c_der = _n_der;
                    }
                    _der[_n_der-1] = freqs.frq_ingroup().frq_all(all);
                    if (freqs.frq_ingroup().frq_all(all) == 1) _S_der++;
                }
            }
            _Sd_acc += _S_der;
            _nsites5++;
            SETFLAG(4);
        }
    }

    void SiteDiversity::_fstats_haplo(const FreqHolder& freqs) {

        _npop_eff3 = 0;
        unsigned int ntot = 0;
        unsigned long n2tot = 0.0;
        unsigned int n;

        for (unsigned int i=0; i<_npop; i++) {
            if (freqs.frq_population(i).nseff() > 1) {
                _npop_eff3++;
                n = freqs.frq_population(i).nseff();
                ntot += n;
                n2tot += n * n;
            }
        }

        if (_npop_eff3 < 2) return; //  || ntot == _npop_eff3 (removed because now enforce >= 2 samples per pop

        _n = 0.0;
        _d = 0.0;

        double nc = static_cast<double>(n2tot)/ntot;
        nc = (ntot - nc) / (_npop_eff3-1);

        double p, pbar;
        double MSP;
        double MSG;

        for(unsigned int all=0; all<_A_tot; all++) {

            pbar = 0.0;
            for (unsigned int pop=0; pop<_npop; pop++) {
                n = freqs.frq_population(pop).nseff();
                if (n > 1) {
                    pbar += static_cast<double>(freqs.frq_population(pop).frq_all(all));
                }
            }
            pbar /= ntot;

            MSP = 0.0;
            MSG = 0.0;
            for (unsigned int pop=0; pop<_npop; pop++) {
                n = freqs.frq_population(pop).nseff();
                if (n > 1) {
                    p = static_cast<double>(freqs.frq_population(pop).frq_all(all)) / n;
                    MSP += n * (p - pbar) * (p - pbar);
                    MSG += n * p * (1.0 - p);
                }
            }
            MSP /= (_npop_eff3 - 1.0);
            MSG /= ntot - _npop_eff3; // this is sum(ni-1) for i up to _npop_eff3

            _n += MSP - MSG;
            _d += MSP + (nc - 1) * MSG;
        }

        _nsites6++;
        SETFLAG(5);

        _n_acc += _n;
        _d_acc += _d;
    }

    void SiteDiversity::_fstats_diplo(const FreqHolder& freq) {
        double nbar = 0.0;
        double nc = 0.0;
        unsigned int ni;
        _npop_eff2 = 0;
        for (unsigned int i=0; i<_npop; i++) {
            ni = freq.frq_population(i).nieff();
            if (ni > 0) {
                _npop_eff2++;
                nbar += ni;
                nc += ni * ni;
            }
        }

        _a = 0.0;
        _b = 0.0;
        _c = 0.0;

        if (_npop_eff2 < 2 || nbar == _npop_eff2) return;

        nbar /= _npop_eff2;
        nc = (_npop_eff2*nbar - nc/(_npop_eff2*nbar)) / (_npop_eff2-1);

        // we assume that nc cannot be 0 (won't happen is sum(ni**2) > sum(ni)**2

        double hbar, pbar, ssquare;

        for(unsigned int all=0; all<_A_tot; all++) {

            hbar = freq.frq_ingroup().frq_het(all) / (nbar * _npop_eff2);
            pbar = 1.0 * freq.frq_ingroup().frq_all(all) / freq.frq_ingroup().nseff();
            ssquare = 0.0;

            for (unsigned int pop=0; pop<_npop; pop++) {

                const FreqSet& frq_pop = freq.frq_population(pop);

                if (frq_pop.nieff() < 2) continue;

                ssquare += frq_pop.nieff() *
                        (1. * frq_pop.frq_all(all) / frq_pop.nseff() - pbar) *
                        (1. * frq_pop.frq_all(all) / frq_pop.nseff() - pbar);
            }
            ssquare /= (_npop_eff2-1) * nbar;
            _a += (ssquare - (pbar*(1.0-pbar)-ssquare*(_npop_eff2-1.0)/_npop_eff2-hbar/4.0)/(nbar-1.0))*nbar/nc;
            _b += (pbar*(1-pbar) - ssquare*(_npop_eff2-1)/_npop_eff2 - hbar*(2*nbar-1)/(4*nbar))*nbar/(nbar-1);
            _c += 0.5 * hbar;
        }

        _nsites7++;
        SETFLAG(6);

        _a_acc += _a;
        _b_acc += _b;
        _c_acc += _c;

    }

    void SiteDiversity::_fstats_hier(const FreqHolder& freqs) {

        //  initialize variance components
        _c0 = 0.0;
        _b1 = 0.0;
        _b2 = 0.0;
        _a0 = 0.0;

       // get global statistics
        _nclu = freqs.num_clusters();
        _nclu_eff = 0;
        _npop_eff2 = 0;

        // allocate memory
        if (_nclu > _r_c) {
            _ni = (unsigned int *) realloc(_ni, _nclu*sizeof(unsigned int));
            if (!_ni) throw EGGMEM;
            _pi = (double *) realloc(_pi, _nclu*sizeof(double));
            if (!_pi) throw EGGMEM;
            _clu_flags = (bool *) realloc(_clu_flags, _nclu*sizeof(bool));
            if (!_clu_flags) throw EGGMEM;
            _r_c = _nclu;
        }
        for (unsigned int i=0; i<_nclu; i++) {
            _ni[i] = 0;
            _clu_flags[i] = 0;
        }

        // compute sample size sums
        unsigned int pop, clu;
        unsigned int nij;

        unsigned int nindiv_tot = 0;
        double n1 = 0.0;
        double n2 = 0.0;
        double n3 = 0.0;

        for (pop=0; pop<_npop; pop++) {
            nij = freqs.frq_population(pop).nieff();
            if (nij > 0) {
                clu = freqs.cluster_index(pop);
                if (!_clu_flags[clu]) {
                    _clu_flags[clu] = true;
                    _nclu_eff++;
                }
                _npop_eff2++;
                nindiv_tot += nij;
                _ni[clu] += nij;
            }
        }

        if (_nclu_eff < 2 || _npop_eff2 == _nclu_eff || nindiv_tot == _npop_eff2) return;

        for (pop=0; pop<_npop; pop++) {
            nij = freqs.frq_population(pop).nieff();
            clu = freqs.cluster_index(pop);
            if (nij > 0) {
                n1 += 1.0 * (nindiv_tot-_ni[clu])*nij*nij / (_ni[clu]*nindiv_tot);
                n3 += 1.0 * nij * nij / _ni[clu];
            }
        }

        for (unsigned int i=0; i<_nclu; i++) n2 += _ni[i] * _ni[i];

        n1 /= (_nclu_eff-1);
        n2 = (nindiv_tot - 1.0*n2/nindiv_tot)/(_nclu_eff-1);
        n3 = (nindiv_tot - n3) / (_npop_eff2 - _nclu_eff);

        // process all alleles

        double MSP, MSD, MSI, MSI2, MSG;
        double pij, p;
        unsigned int hij;

        for (unsigned int all=0; all<_A_tot; all++) {

            p = 1.0 * freqs.frq_ingroup().frq_all(all) / freqs.frq_ingroup().nseff();
            MSP = 0.0;
            MSD = 0.0;
            MSI = 0.0;
            MSI2 = 0.0;
            MSG = 0.0;

            // compute cluster frequencies
            for (unsigned int i=0; i<_nclu; i++) {
                _pi[i] = static_cast<double>(freqs.frq_cluster(i).frq_all(all))
                                                / freqs.frq_cluster(i).nseff();
                MSP += _ni[i] * (_pi[i]-p) * (_pi[i]-p);
            }

            // compute other sum of squares
            for (unsigned int pop=0; pop<_npop; pop++) {
                nij = freqs.frq_population(pop).nieff();
                clu = freqs.cluster_index(pop);
                if (nij > 0) {
                    pij = static_cast<double>(freqs.frq_population(pop).frq_all(all)) / freqs.frq_population(pop).nseff();
                    MSD += nij * (pij-_pi[clu]) * (pij-_pi[clu]);
                    MSI += nij * pij * (1-pij);
                    hij = freqs.frq_population(pop).frq_het(all);
                    MSI2 += hij;
                    MSG += hij;
                }
            }
            MSP = 2 * MSP / (_nclu_eff-1);
            MSD = 2 * MSD / (_npop_eff2 - _nclu_eff);

            MSI = (2 * MSI - 0.5 * MSI2) / (nindiv_tot - _npop_eff2);
            MSG = 0.5 * MSG / nindiv_tot;

            // increment variance components

            _c0 += MSG;
            _b1 += 0.5 * (MSI - MSG);
            _b2 += (MSD - MSI) / (2 * n3);
            _a0 += (n3 * MSP - n1 * MSD - (n3-n1) * MSI) / (2 * n2 * n3);
        }

        _nsites8++;
        SETFLAG(7);

        _a0_acc += _a0;
        _b1_acc += _b1;
        _b2_acc += _b2;
        _c0_acc += _c0;
    }

    void SiteDiversity::_hstats(const FreqHolder& freqs) {

        if (_npop_eff1 < 2) return;
        double Hs1 = 0.0; // for Hst
        double Hs2 = 0.0; // for Gst
        double ntilde = 0.0;
        unsigned int ns, ns_Hs1 = 0, ns_Hs2 = 0;
        unsigned int ns2 = 0; // number of samples without populations with < 2 samples
        for (unsigned int i=0; i<_npop; i++) {
            ns = freqs.frq_population(i).nseff();
            if (ns > 1) {
                Hs1 += _He_pop[i] * (ns-2); // use ns-2 as weight for Hst (to do like DnaSP)
                ntilde += 1.0 / ns;
                Hs2 += _He_pop[i] * ns;
                ns_Hs1 += ns-2;
                ns_Hs2 += ns;
                ns2 += ns;
            }
        }

        if (ns_Hs1 > 0) Hs1 /= ns_Hs1;
        if (ns_Hs2 > 1) Hs2 /= ns_Hs2;
        ntilde = _npop_eff1/ntilde;

        double Hjt = 1.0;
        double sumP;
        double pairdiff2 = 0.0; // like _pairdiff, but without populations with < 2 samples
        double freq;
        for (unsigned int i=0; i<_A_tot; i++) {
            sumP = 0.0;
            freq = 0.0;
            for (unsigned int j=0; j<_npop; j++) {
                ns = freqs.frq_population(j).nseff();
                if (ns > 1) {
                    sumP += static_cast<double>(freqs.frq_population(j).frq_all(i)) / ns;
                    freq += freqs.frq_population(j).frq_all(i);
                }
            }
            sumP /= _npop_eff1;
            freq /= ns2;
            pairdiff2 += freq * freq;
            Hjt -= sumP * sumP;
        }
        pairdiff2 = 1 - pairdiff2;
        double He2 = pairdiff2 * ns2 / (ns2 - 1);
            // like _pairdiff, but without populations with < 2 samples

        double Hjs = 0.0;
        double H, p;
        for (unsigned int i=0; i<_npop; i++) {
            ns = freqs.frq_population(i).nseff();
            if (ns > 1) {
                H = 1.0;
                for (unsigned int j=0; j<_A_tot; j++) {
                    p = static_cast<double>(freqs.frq_population(i).frq_all(j)) / ns;
                    H -= p*p;
                }
                Hjs += H; // this is not He_pop because He_pop is unbiased
            }
        }
        Hjs /= _npop_eff1;

        double Httilde = pairdiff2 + Hs2 / (_npop_eff1*ntilde);
        double Hse = Hjs * ntilde / (ntilde - 1);
        double Hte = Hjt + Hse / (ntilde * _npop_eff1);
        _JostD = (Hte - Hse) * _npop_eff1 / ((1 - Hse) * (_npop_eff1 - 1));

        if (He2 > 0.0 && ns_Hs1 > 0) {
            _Hst = 1.0 - Hs1/He2;
            _Hst_acc += _Hst;
            _nsites10++;
            SETFLAG(11);
        }

        if (Httilde > 0.0 && ns_Hs2 > 0) {
            _Gst = 1.0 - Hs2/Httilde;
            _Gst_acc += _Gst;
            _nsites11++;
            SETFLAG(12);
        }

        if (Hjt > 0.0 && Hjs < 1.0) {
            _Gste = (1.0 - Hjs / Hjt) * (1+Hjs) / (1-Hjs);
            _Gste_acc += _Gste;
            _nsites12++;
            SETFLAG(13);
        }

        _D_acc += _JostD;
        _nsites9++;
        SETFLAG(8);
    }

    unsigned int SiteDiversity::average() {
        _flag = 0;

        if (_nsites1 > 0) {
            SETFLAG(0);
            _ns = _ns_acc / _nsites1;
            _nso = _nso_acc / _nsites1;
        }

        if (_nsites2 > 0) {
            SETFLAG(1);
            if (_Aing_acc > _nsites2) SETFLAG(10);
            _A_glo = _Aglob_acc / _nsites2;
            _A_ing = _Aing_acc / _nsites2;
            _S_tot = _S_acc / _nsites2;
            _R = _R_acc / _nsites2;
            _pairdiff = _pairdiff_acc; // not average, keep sum
            _He = _He_acc / _nsites2;
        }

        if (_nsites3 > 0) {
            SETFLAG(2);
            _thetaIAM = _thetaIAM_acc / _nsites3;
            _thetaSMM = _thetaSMM_acc / _nsites3;
        }

        if (_nsites4 > 0) {
            SETFLAG(3);
            _Ho = _Ho_acc / _nsites4;
        }

        if (_nsites5 > 0) {
            SETFLAG(4);
            _S_der = _Sd_acc / _nsites5;
        }

        if (_nsites5A > 0) {
            SETFLAG(14);
            _A_out = _Aout_acc / _nsites5A;
        }

        if (_nsites6 > 0) {
            SETFLAG(5);
            _n = _n_acc;
            _d = _d_acc; // _nsites6
        }

        if (_nsites7 > 0) {
            SETFLAG(6);
            _a = _a_acc;
            _b = _b_acc;
            _c = _c_acc; // _nsites7
        }

        if (_nsites8 > 0) {
            SETFLAG(7);
            _a0 = _a0_acc;
            _b1 = _b1_acc;
            _b2 = _b2_acc;
            _c0 = _c0_acc; // nsites8
        }

        if (_nsites9 > 0) {
            SETFLAG(8);
            _JostD = _D_acc / _nsites9;
        }

        if (_nsites10 > 0) {
            SETFLAG(11);
            _Hst = _Hst_acc / _nsites10;
        }

        if (_nsites11 > 0) {
            SETFLAG(12);
            _Gst = _Gst_acc / _nsites11;
        }

        if (_nsites12 > 0) {
            SETFLAG(13);
            _Gste = _Gste_acc / _nsites12;
        }

        if (_nsites13 > 0) {
            SETFLAG(15);
            _f2 = _f2_acc / _nsites13;
        }

        if (_nsites14 > 0) {
            SETFLAG(16);
            _f3 = _f3_acc / _nsites14;
        }

        if (_nsites15 > 0) {
            SETFLAG(17);
            _f4 = _f4_acc / _nsites15;
        }

        if (_Dp_den_acc > 0) {
            SETFLAG(18);
            _Dp = _f4_acc / _Dp_den_acc;
        }

        return _flag;
    }

    Triconfigurations::Triconfigurations() {
        min = 0;
        reset();
    }

    void Triconfigurations::reset() {
        n = 0;
        memset(&c, 0, 13*sizeof(unsigned int));
    }

    void Triconfigurations::process(const FreqHolder & frq) {
        if (frq.num_populations() != 3) return;
        if (frq.num_alleles() != 2) return;
        const FreqSet * pops[] = {&frq.frq_population(0),    
                    &frq.frq_population(1), &frq.frq_population(2)};
        int flag = 0b0;
        if (pops[0]->nseff() < min || pops[1]->nseff() < min || pops[2]->nseff() < min) return; 
        n += 1;
        if (pops[0]->num_alleles_eff() > 1) flag |= 0b1;
        if (pops[1]->num_alleles_eff() > 1) flag |= 0b10;
        if (pops[2]->num_alleles_eff() > 1) flag |= 0b100;
        switch (flag) {
            case 0b0:
                if ((pops[1]->frq_all(0) == 0) == (pops[2]->frq_all(0) == 0)) { c[0]++; return; } 
                if ((pops[0]->frq_all(0) == 0) == (pops[2]->frq_all(0) == 0)) { c[1]++; return; } 
                if ((pops[0]->frq_all(0) == 0) == (pops[1]->frq_all(0) == 0)) { c[2]++; return; } 
                break;
            case 0b1:
                if ((pops[1]->frq_all(0) == 0) == (pops[2]->frq_all(0) == 0)) { c[3]++; return; } 
                if ((pops[1]->frq_all(0) == 0) != (pops[2]->frq_all(0) == 0)) { c[4]++; return; } 
                break;
            case 0b10:
                if ((pops[0]->frq_all(0) == 0) == (pops[2]->frq_all(0) == 0)) { c[5]++; return; } 
                if ((pops[0]->frq_all(0) == 0) != (pops[2]->frq_all(0) == 0)) { c[6]++; return; } 
                break;
            case 0b11: c[9]++; return;
            case 0b100:
                if ((pops[0]->frq_all(0) == 0) == (pops[1]->frq_all(0) == 0)) { c[7]++; return; } 
                if ((pops[0]->frq_all(0) == 0) != (pops[1]->frq_all(0) == 0)) { c[8]++; return; } 
                break;
            case 0b101: c[10]++; return;
            case 0b110: c[11]++; return;
            case 0b111: c[12]++; return;
            default:
                throw EggRuntimeError("invalid triconfiguration site met");
        }
        throw EggRuntimeError("invalid triconfiguration site met");
    }

    unsigned int Triconfigurations::num() const {
        return n;
    }

    void Triconfigurations::set_min(unsigned int m) {
        min = m;
    }

    unsigned int Triconfigurations::cnt(unsigned int i) const {
        return c[i];
    }
}
