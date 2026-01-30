/*
    Copyright 2023-2025 Stéphane De Mita

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

#include <time.h>
#include <stdlib.h>
#include <math.h>
#include "random.h"

// Mersenne Twister parameters
static const unsigned int mt_param_n = 624;
static const unsigned int mt_param_m = 397;

// variables
unsigned long * var_state; // stored bits
unsigned int var_pos; // current bit position
int var_b_ncached; // normal value cached boolean
double var_v_ncached; // cached normal value
int var_binom_cache; // binomial data cached boolean
double var_binom_p;
long var_binom_n;
double var_binom_r;
double var_binom_q;
double var_binom_fm;
unsigned long var_binom_m;
double var_binom_p1;
double var_binom_xm;
double var_binom_xl;
double var_binom_xr;
double var_binom_c;
double var_binom_laml;
double var_binom_lamr;
double var_binom_p2;
double var_binom_p3;
double var_binom_p4;
unsigned int long var_seed; // user-specified (or default) seed

// HELPERS

unsigned long twiddle(unsigned long u, unsigned long v) {
    return (((u & 0x80000000UL) | (v & 0x7FFFFFFFUL)) >> 1) ^ ((v & 1UL) ? 0x9908B0DFUL : 0x0UL);
}

void f_gen_state() {
    for (unsigned int i = 0; i < (mt_param_n - mt_param_m); ++i) {
        var_state[i] = var_state[i + mt_param_m] ^ twiddle(var_state[i], var_state[i + 1]);
    }
    for (unsigned int i = mt_param_n - mt_param_m; i < (mt_param_n - 1); ++i) {
        var_state[i] = var_state[i + mt_param_m - mt_param_n] ^ twiddle(var_state[i], var_state[i + 1]);
    }
    var_state[mt_param_n - 1] = var_state[mt_param_m - 1] ^ twiddle(var_state[mt_param_n - 1], var_state[0]);
    var_pos = 0;
}

unsigned long _binomrand_btpe(long n, double p) {
    double r, q, fm, p1, xm, xl, xr, c, laml, lamr, p2, p3, p4;
    double a, u, v, s, F, rho, t, A, nrq, x1, x2, f1, f2, z, z2, w, w2, x;
    long m, y, k, i;

    if (var_binom_cache == 0 || var_binom_n != n || var_binom_p != p) {
        var_binom_n = n;
        var_binom_p = p;
        var_binom_cache = 1;
        var_binom_r = r = p < 0.5 ? p : 1.0 - p;
        var_binom_q = q = 1.0 - r;
        var_binom_fm = fm = n * r + r;
        var_binom_m = m = (long) floor(fm);
        var_binom_p1 = p1 = floor(2.195 * sqrt(n*r*q) - 4.6*q) + 0.5;
        var_binom_xm = xm = m + 0.5;
        var_binom_xl = xl = xm - p1;
        var_binom_xr = xr = xm + p1;
        var_binom_c = c = 0.134 + 20.5/(15.3 + m);
        a = (fm - xl) / (fm - xl*r);
        var_binom_laml = laml = a * (1.0 + a/2.0);
        a = (xr - fm)/(xr * q);
        var_binom_lamr = lamr = a * (1.0 + a/2.0);
        var_binom_p2 = p2 = p1 * (1.0 + 2.0*c);
        var_binom_p3 = p3 = p2 + c/laml;
        var_binom_p4 = p4 = p3 + c/lamr;
    }
    else {
        r = var_binom_r;
        q = var_binom_q;
        fm = var_binom_fm;
        m = var_binom_m;
        p1 = var_binom_p1;
        xm = var_binom_xm;
        xl = var_binom_xl;
        xr = var_binom_xr;
        c = var_binom_c;
        laml = var_binom_laml;
        lamr = var_binom_lamr;
        p2 = var_binom_p2;
        p3 = var_binom_p3;
        p4 = var_binom_p4;
    }

    /* the while loop below replaces goto-based code  ... */
    while (1) {

        // Step10

        nrq = n*r*q;
        u = egglib_random_uniform()*p4;
        v = egglib_random_uniform();
        if (u <= p1) {
            y = (long) floor(xm - p1*v + u);
            break; // ... goto Step60
        }
        // ... goto Step20

        // Step20

        if (u > p2) { // ... goto Step30

            // Step30
            if (u > p3) { // ... goto Step40

                // Step40
                y = (long) floor(xr - log(v)/lamr);
                if (y > n) continue; // ... goto Step40
                v = v*(u-p3)*lamr;
                // .. goto Step50
            }

            // (still Step30)
            else {
                y = (long) floor(xl + log(v)/laml);
                if (y < 0) continue; // ... goto Step10
                v = v*(u-p2)*laml;
                // .. goto Step50
            }
        }

        // (still Step20)
        else {
            x = xl + (u - p1)/c;
            v = v*c + 1.0 - fabs(m - x + 0.5)/p1;
            if (v > 1.0) continue; // .. goto Step10
            y = (long) floor(x);
            // ... goto Step50
        }

        // Step50
        k = fabs(y - m);
        if (!((k > 20) && (k < ((nrq)/2.0 - 1)))) {

            // ... not gotoing Step52
            s = r/q;
            a = s*(n+1);
            F = 1.0;
            if (m < y) {
                for (i=m; i<=y; i++) F *= (a/i - s);
            }
            else if (m > y) {
                for (i=y; i<=m; i++) F /= (a/i - s);
            }
            else {
                if (v > F) continue; // ... goto Step10
                else break; // ... goto Step60
            }
        }

        // Step52

        rho = (k/(nrq))*((k*(k/3.0 + 0.625) + 0.16666666666666666)/nrq + 0.5);
        t = -k*k/(2*nrq);
        A = log(v);
        if (A < (t - rho)) break; // ... goto Step60
        if (A > (t + rho)) continue; // ... goto Step10

        x1 = y+1;
        f1 = m+1;
        z = n+1-m;
        w = n-y+1;
        x2 = x1*x1;
        f2 = f1*f1;
        z2 = z*z;
        w2 = w*w;
        if (A > (xm*log(f1/x1)
                + (n-m+0.5)*log(z/w)
                + (y-m)*log(w*r/(x1*q))
                + (13680.0-(462.0-(132.0-(99.0-140.0/f2)/f2)/f2)/f2)/f1/166320.0
                + (13680.0-(462.0-(132.0-(99.0-140.0/z2)/z2)/z2)/z2)/z/166320.0
                + (13680.0-(462.0-(132.0-(99.0-140.0/x2)/x2)/x2)/x2)/x1/166320.0
                + (13680.0-(462.0-(132.0-(99.0-140.0/w2)/w2)/w2)/w2)/w/166320.0))
        {
            continue; // .. goto Step10
        }
    }

    // Step60
    if (p > 0.5) y = n - y;
    return y;
}

unsigned long _binomrand_inversion(long n, double p) {
    double q, qn, np, px, U;
    long X, bound;

    if (var_binom_cache == 0 || var_binom_n != n || var_binom_p != p) {
        var_binom_n = n;
        var_binom_p = p;
        var_binom_cache = 1;
        var_binom_q = q = 1.0 - p;
        var_binom_r = qn = exp(n * log(q));
        var_binom_c = np = n*p;
        bound = np + 10.0 * sqrt(np*q + 1);
        if (n < bound) bound = n;
        var_binom_m = bound;
    }
    else {
        q = var_binom_q;
        qn = var_binom_r;
        np = var_binom_c;
        bound = var_binom_m;
    }
    X = 0;
    px = qn;
    U = egglib_random_uniform();
    while (U > px) {
        X++;
        if (X > bound) {
            X = 0;
            px = qn;
            U = egglib_random_uniform();
        }
        else {
            U -= px;
            px  = ((n-X+1) * p * px)/(X*q);
        }
    }
    return X;
}

int egglib_random_init() {
    var_state = (unsigned long *) malloc(mt_param_n * sizeof(unsigned long));
    if (!var_state) return -1;
    for (unsigned int i=0; i<mt_param_n; i++) var_state[i] = 0;
    var_pos = 0;
    egglib_random_set_seed(time(NULL));
    var_b_ncached = 0;
    var_v_ncached = 0.0;
    var_binom_cache = 0;
    return 0;
}

// C INTERFACE FUNCTIONS

double egglib_random_uniform() { 
    return (double) (egglib_random_integer_32bit() * (1.0 / 4294967296.0));
}

void egglib_random_set_seed(unsigned long s) {
    var_state[0] = s & 0xFFFFFFFFUL;
    for (unsigned int i = 1; i < mt_param_n; ++i) {
        var_state[i] = 1812433253UL * (var_state[i-1] ^ (var_state[i-1] >> 30)) + i;
        var_state[i] &= 0xFFFFFFFFUL;
    }
    var_pos = mt_param_n;
    var_b_ncached = 0;
    var_v_ncached = 0.0;
    var_binom_cache = 0;
    var_seed = s;
}

unsigned long egglib_random_get_seed() {
    return var_seed;
}

unsigned long egglib_random_integer_32bit() {
    if (var_pos == mt_param_n) f_gen_state();
    unsigned long x = var_state[var_pos++];
    x ^= (x >> 11);
    x ^= (x << 7) & 0x9D2C5680UL;
    x ^= (x << 15) & 0xEFC60000UL;
    return x ^ (x >> 18);
}

int egglib_random_bernoulli(double p) {
    return (egglib_random_uniform() < p);
}

int egglib_random_brand() {
    return egglib_random_integer_32bit() < 2147483648; // true if rand int < 2^32 / 2
}

double egglib_random_uniformcl() { // [0, 1] uniform
    return ((double) egglib_random_integer_32bit()) * (1.0 / 4294967295.0); // rand int / (2^32 - 1)
}

double egglib_random_uniformop() { // (0, 1) uniform
    return (((double) egglib_random_integer_32bit()) + 0.5) * (1.0 / 4294967296.0); // rand int half-shifted right / 2^32
}

double egglib_random_uniform53() { // [0, 1) uniform, 53 bits
    return (((double) (egglib_random_integer_32bit() >> 5)) * 67108864.0 + 
      ((double) (egglib_random_integer_32bit() >> 6))) * (1.0 / 9007199254740992.0);
}

double egglib_random_erand(double expect) {
    double tp;
    do {
        tp = egglib_random_uniform();
    } while (tp == 0.0);
    return ( -(expect)*log(tp) );
}

unsigned int egglib_random_irand(unsigned int ncards) {
    return (unsigned int) (egglib_random_uniform()*ncards);
}

unsigned int egglib_random_prand(double mean) {
    unsigned int i=0;
    double cumul;
    cumul= (-1/mean)*log(egglib_random_uniformop());
    while (cumul<1) {
        cumul += (-1/mean)*log(egglib_random_uniformop());
        i++;
    }
    return i;
}

unsigned int egglib_random_grand(double param) {
    if (param == 1.0) return 1;
    double X = 1.0 - egglib_random_uniform();
    return (unsigned int) ceil(log(X)/log(1.0-param));
}

double egglib_random_nrand() {

    // return cached value, if so
    if (var_b_ncached) {
        var_b_ncached = 0;
        return var_v_ncached;
    }
    
    // polar form of the Box-Muller transformation
    // implementation taken as is from http://www.taygeta.com/random/gaussian.html Nov 10th 2010
    float x1, x2, w, y1, y2;

    do {
        x1 = 2.0 * egglib_random_uniform() - 1.0;
        x2 = 2.0 * egglib_random_uniform() - 1.0;
        w = x1 * x1 + x2 * x2;
     } while (w >= 1.0);

     w = sqrt( (-2.0 * log( w ) ) / w );
     y1 = x1 * w;
     y2 = x2 * w;

    // cache one value and return the other
    var_b_ncached = 1;
    var_v_ncached = y2;
    return y1;
}

double egglib_random_nrandb(double m, double sd, double min, double max) {
    double X;
    do X = egglib_random_nrand() * sd + m;
    while (X < min || X > max);
    return X;
}

unsigned long egglib_random_binomrand(long n, double p) {
    // from numpy 1.8.0 numpy/random/mtrand/distributions.c

    // n must be >= n
    if (p <= 0.5) {
        if (p * n <= 30.0) return _binomrand_inversion(n, p);
        else return _binomrand_btpe(n, p);
    }
    else {
        double q = 1.0 - p;
        if (q * n <= 30.0) return n - _binomrand_inversion(n, q);
        else return n - _binomrand_btpe(n, q);
    }
}
