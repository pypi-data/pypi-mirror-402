/*
    Copyright 2023 Stéphane De Mita

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

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "random.h"

static PyObject * random_set_seed(PyObject * self, PyObject * args) {
    unsigned int long s = 0;
    if (!PyArg_ParseTuple(args, "l", &s)) {
        return NULL;
    }
    egglib_random_set_seed(s);
    Py_RETURN_NONE;
}

static PyObject * random_get_seed(PyObject * self, PyObject * args) {
    return PyLong_FromUnsignedLong(egglib_random_get_seed());
}

static PyObject * random_integer_32bit(PyObject * self, PyObject * args) {
    return PyLong_FromUnsignedLong(egglib_random_integer_32bit());
}

static PyObject * random_bernoulli(PyObject * self, PyObject * args) {
    double p = 0;
    if (!PyArg_ParseTuple(args, "d", &p)) {
        return NULL;
    }
    if (p < 0.0 || p > 1.0) {
        PyErr_SetString(PyExc_ValueError, "parameter out of range");
        return NULL;
    }
    return PyBool_FromLong(egglib_random_uniform() < p);
}

static PyObject * random_brand(PyObject * self, PyObject * args) {
    return PyBool_FromLong(egglib_random_brand());
}

static PyObject * random_uniform(PyObject * self, PyObject * args) {
    return PyFloat_FromDouble(egglib_random_uniform());
}

static PyObject * random_uniformcl(PyObject * self, PyObject * args) {
    return PyFloat_FromDouble(egglib_random_uniformcl());
}

static PyObject * random_uniformop(PyObject * self, PyObject * args) {
    return PyFloat_FromDouble(egglib_random_uniformop());
}

static PyObject * random_uniform53(PyObject * self, PyObject * args) {
    return PyFloat_FromDouble(egglib_random_uniform53());
}

static PyObject * random_erand(PyObject * self, PyObject * args) {
    double e = 0.0;
    if (!PyArg_ParseTuple(args, "d", &e)) {
        return NULL;
    }
    if (e <= 0.0) {
        PyErr_SetString(PyExc_ValueError, "expectation must be strictly positive");
        return NULL;
    }
    return PyFloat_FromDouble(egglib_random_erand(e));
}

static PyObject * random_irand(PyObject * self, PyObject * args) {
    int n = 0;
    if (!PyArg_ParseTuple(args, "i", &n)) {
        return NULL;
    }
    if (n <= 0) {
        PyErr_SetString(PyExc_ValueError, "number of cards must be strictly positive");
        return NULL;
    }
    return PyLong_FromLong(egglib_random_irand(n));
}

static PyObject * random_prand(PyObject * self, PyObject * args) {
    double m = 0.0;
    if (!PyArg_ParseTuple(args, "d", &m)) {
        return NULL;
    }
    if (m <= 0) {
        PyErr_SetString(PyExc_ValueError, "mean must be strictly positive");
        return NULL;
    }
    return PyLong_FromLong(egglib_random_prand(m));
}

static PyObject * random_grand(PyObject * self, PyObject * args) {
    double p = 0.0;
    if (!PyArg_ParseTuple(args, "d", &p)) {
        return NULL;
    }
    if (p <= 0 || p > 1) {
        PyErr_SetString(PyExc_ValueError, "parameter must be in (0, 1] range");
        return NULL;
    }
    return PyLong_FromLong(egglib_random_grand(p));
}

static PyObject * random_nrand(PyObject * self, PyObject * args) {
    return PyFloat_FromDouble(egglib_random_nrand());
}

static PyObject * random_nrandb(PyObject * self, PyObject * args) {
    double m = 0.0;
    double sd = 0.0;
    double min = 0.0;
    double max = 0.0;
    if (!PyArg_ParseTuple(args, "dddd", &m, &sd, &min, &max)) {
        return NULL;
    }
    if (sd < 0) {
        PyErr_SetString(PyExc_ValueError, "standard deviation must be >= 0");
        return NULL;
    }
    if (max <= min) {
        PyErr_SetString(PyExc_ValueError, "maximum must be larger than minimum");
        return NULL;
    }
    return PyFloat_FromDouble(egglib_random_nrandb(m, sd, min, max));
}

static PyObject * random_binomrand(PyObject * self, PyObject * args) {
    int n = 0;
    double p = 0.0;
    if (!PyArg_ParseTuple(args, "id", &n, &p)) {
        return NULL;
    }
    if (n <= 0) {
        PyErr_SetString(PyExc_ValueError, "n must be larger than 0");
        return NULL;
    }
    if (p < 0 || p > 1) {
        PyErr_SetString(PyExc_ValueError, "p must be in range [0, 1]");
        return NULL;
    }
    return PyLong_FromLong(egglib_random_binomrand(n, p));
}

// MODULE CONFIGURATION

static PyMethodDef random_methods[] = {
    {"set_seed",       random_set_seed,      METH_VARARGS, "Set the seed."},
    {"get_seed",       random_get_seed,      METH_NOARGS, "Get the seed used to configure the pseudorandom number generator."},
    {"integer_32bit",  random_integer_32bit, METH_NOARGS, "Generate a 32-bit random integer (in the range :math:`[0, 2^{32-1}]`)."},
    {"bernoulli",      random_bernoulli,     METH_VARARGS, "Draw a boolean with given probability."},
    {"boolean",        random_brand,         METH_VARARGS, "Draw a boolean with equal probabilities (:math:`p = 0.5`)."},
    {"uniform",        random_uniform,       METH_NOARGS, "Draw a value in the half-open interval :math:`[0,1)` with default 32-bit precision."},
    {"uniform_closed", random_uniformcl,     METH_NOARGS, "Draw a value in the closed interval :math:`[0,1]`."},
    {"uniform_open",   random_uniformop,     METH_NOARGS, "Draw a value in the open interval :math:`(0,1)`."},
    {"uniform_53bit",  random_uniform53,     METH_NOARGS, "Draw a value in the half-open interval :math:`[0,1)` with increased 53-bit precision."},
    {"exponential",    random_erand,         METH_VARARGS, "Draw a value from an exponential distribution."},
    {"integer",        random_irand,         METH_VARARGS, "Draw an integer from a uniform distribution."},
    {"poisson",        random_prand,         METH_VARARGS, "Draw a value from a Poisson distribution."},
    {"geometric",      random_grand,         METH_VARARGS, "Draw a value from a geometric distribution."},
    {"normal",         random_nrand,         METH_NOARGS, "Draw a value from the normal distribution.."},
    {"normal_bounded", random_nrandb,        METH_VARARGS, "Draw a value from a bounded normal distribution."},
    {"binomial",       random_binomrand,     METH_VARARGS, "Draw a value from a binomial distribution."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef randommodule = {
    PyModuleDef_HEAD_INIT,
    "random",                             /* name of module */
    "Random number generator",            /* module documentation, may be NULL */
    -1,                                   /* size of per-interpreter state of the module */
    random_methods
};

PyMODINIT_FUNC PyInit_random(void) {
    if (egglib_random_init() < 0) {
        PyErr_NoMemory();
        return NULL;
    }
    return PyModule_Create(&randommodule);
}
