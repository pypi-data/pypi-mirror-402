/*
    Copyright 2024-2025 Stéphane De Mita, Mathieu Siol

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
#include "structmember.h"

#include <string.h>
#include "htslib/hts_log.h"
#include "htslib/hts.h"
#include "htslib/vcf.h"
#include "htslib/hfile.h"
#include "htslib/bgzf.h"
#include "htslib/synced_bcf_reader.h"

#define END_VALUE -2

/** GLOBAL FUNCTIONS
*********************************/

const char doc_index_vcf[] = "index_vcf(fname)\n"
    "Index a BCF file.\n\nThe file is required to be in format BCF. "
    "If *outname* is not specified, use the standard naming scheme for "
    "CSI index files.\n\n"
    ".. versionchanged:: 3.6\n"
    "    The argument *outname* is not supported anymore.";

static PyObject * vcf_index_vcf(PyObject * self, PyObject * args, PyObject * kwargs) {
    PyObject * bytes1;
    PyObject * bytes2 = NULL;
    static char * kwlist[] = {"fname", "outname", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O&|O&", kwlist, PyUnicode_FSConverter, &bytes1, PyUnicode_FSConverter, &bytes2)) {
        return NULL;
    }

    const char * s1 = PyBytes_AsString(bytes1);
    if (s1 == NULL) {
        Py_DECREF(bytes1);
        Py_XDECREF(bytes2);
        return NULL;
    }

    if (bytes2) {
        PyErr_SetString(PyExc_ValueError, "argument *outname* is not supported anymore");
        Py_DECREF(bytes1);
        Py_DECREF(bytes2);
        return NULL;
    }

    int min_shift = 14; // 14 is the recommended value for min_shift
    int ret = bcf_index_build(s1, min_shift);

    Py_DECREF(bytes1);

    if (ret == 0) Py_RETURN_NONE;
    if (ret == -1) {
        PyErr_SetString(PyExc_ValueError, "cannot create index: indexing failed");
        return NULL;
    }
    if (ret == -2) {
        PyErr_SetString(PyExc_OSError, "cannot create index: cannot open file");
        return NULL;
    }
    if (ret == -3) {
        PyErr_SetString(PyExc_ValueError, "cannot create index: format not indexable");
        return NULL;
    }
    if (ret == -4) {
        PyErr_SetString(PyExc_OSError, "cannot create index: failed to create and/or save the index");
        return NULL;
    }
    PyErr_SetString(PyExc_ValueError, "cannot create index: undefined error");
    return NULL;
}

const char doc_hts_set_log[] = "hts_set_log_level(level)\n"
    "Activate VCF parsing logs.\n\n"
    "Control the verbosity of messages pushed by the htslib while "
    "indexing, reading or dumping VCF data.\n"
    "When the module is loaded, log is disabled. Allowing log allows "
    "to have more detailed information relative to parsing errors, and "
    "additional warning regarding the structure of input file.\n\n"
    "Possible values are:\n\n"
    " +---------------+-----------------------------------------------------+\n"
    " | ``\"off\"``     | no log                                              |\n"
    " +---------------+-----------------------------------------------------+\n"
    " | ``\"error\"``   | errors only                                         |\n"
    " +---------------+-----------------------------------------------------+\n"
    " | ``\"warning\"`` | errors and warnings                                 |\n"
    " +---------------+-----------------------------------------------------+\n"
    " | ``\"info\"``    | errors, warnings, and normal but significant events |\n"
    " +---------------+-----------------------------------------------------+\n"
    " | ``\"debug\"``   | all except the most detailed debug events           |\n"
    " +---------------+-----------------------------------------------------+\n"
    " | ``\"trace\"``   | all logging enabled                                 |\n"
    " +---------------+-----------------------------------------------------+\n\n"
    ".. versionadded 3.6\n";

static PyObject * hts_set_log(PyObject * self, PyObject * args, PyObject * kwargs) {
    const char * level;
    static char * kwlist[] = {"level", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s", kwlist, &level)) {
        return NULL;
    }

    if (!strcmp(level, "off")) {hts_set_log_level(HTS_LOG_OFF); Py_RETURN_NONE;}
    if (!strcmp(level, "error")) {hts_set_log_level(HTS_LOG_ERROR); Py_RETURN_NONE;}
    if (!strcmp(level, "warning")) {hts_set_log_level(HTS_LOG_WARNING); Py_RETURN_NONE;}
    if (!strcmp(level, "info")) {hts_set_log_level(HTS_LOG_INFO); Py_RETURN_NONE;}
    if (!strcmp(level, "debug")) {hts_set_log_level(HTS_LOG_DEBUG); Py_RETURN_NONE;}
    if (!strcmp(level, "trace")) {hts_set_log_level(HTS_LOG_TRACE); Py_RETURN_NONE;}

    PyErr_SetString(PyExc_ValueError, "invalid level string");
    return NULL;
}

/** DEFINITION OF PARSER TYPE
*********************************/

static const int NUM_TYPES = 5;
static const int TYPES[] = {VCF_SNP, VCF_MNP, VCF_INDEL, VCF_OTHER, VCF_BND};
static const char * TYPENAMES[] = {"SNP", "MNP", "INDEL", "OTHER", "BND", "OVERLAP"};

static const int NUM_ERRORS = 7;
static const int ERRORS[] = {BCF_ERR_CTG_UNDEF, BCF_ERR_TAG_UNDEF,
    BCF_ERR_NCOLS, BCF_ERR_LIMITS, BCF_ERR_CHAR, BCF_ERR_CTG_INVALID,
    BCF_ERR_TAG_INVALID};
static const char * ERRORNAMES[] = {"ERR_CTG_UNDEF", "ERR_TAG_UNDEF",
    "ERR_NCOLS", "ERR_LIMITS", "ERR_CHAR", "ERR_CTG_INVALID",
    "ERR_TAG_INVALID"};

typedef struct {
    PyObject_HEAD
    htsFile * wpfile; // dumpfile (write)

    int num_samples;
    int status; // 1 if a line has been read
    int types; // variant type flag (is status)
    PyObject ** type_strings; // strings representing names of variant types
    PyObject ** error_strings; // strings representing names of non fatal-errors
    char has_index; // 1 if index is not NULL

    bcf_srs_t * readers; // readers set with only one reader
    bcf_sr_t * reader; // first and only readers
    hts_idx_t * index; // shortcut to index
    bcf_hdr_t * header; // shortcut to header
    bcf1_t * record; // shortcut to record
    const char * fname; // shortcut to fname
    htsFile * file; // shortcut to file
    const char * first_contig; // name of the first contig if available (otherwise NULL)

    // internal usage memory (to write info/format parsing results)
    int32_t * p_int;
    int n_int;
    float * p_float;
    int n_float;
    char * p_str;
    int n_str;
    int pass_id;

    int32_t * gt_p; // for GT field
    int gt_n;
    int gt_num; // value of given by last call to get_genotypes (reset to 0 at each read/goto)
    PyObject * GAP_OBJECT;
    //char *fname;

} VCF_object;

/** CREATION/DELETION METHODS
*******************************/

// DEL METHOD
static void VCF_dealloc(VCF_object * self) {
    if (self->readers) bcf_sr_destroy(self->readers);
    if (self->wpfile) hts_close(self->wpfile);
    if (self->type_strings) {
        for (int i=0; i<NUM_TYPES; i++) Py_XDECREF(self->type_strings[i]);
        free(self->type_strings);
    }
    if (self->error_strings) {
        for (int i=0; i<NUM_ERRORS; i++) Py_XDECREF(self->error_strings[i]);
        free(self->error_strings);
    }
    if (self->p_int) free(self->p_int);
    if (self->gt_p) free(self->gt_p);
    if (self->p_float) free(self->p_float);
    if (self->p_str) free(self->p_str);
    Py_DECREF(self->GAP_OBJECT);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

// NEW METHOD
static PyObject * VCF_new(PyTypeObject * type, PyObject * args, PyObject * kwds) {
    VCF_object * self;
    self = (VCF_object *) type->tp_alloc(type, 0);
    if (!self) return NULL;
    self->type_strings = (PyObject **) malloc(NUM_TYPES * sizeof(PyObject *));
    if (!self->type_strings) return PyErr_NoMemory();
    for (int i=0; i<NUM_TYPES; i++) {
        self->type_strings[i] = NULL;
    }
    for (int i=0; i<NUM_TYPES; i++) {
        self->type_strings[i] = PyUnicode_FromString(TYPENAMES[i]);
        if (self->type_strings[i] == NULL) return NULL;
    }
    self->error_strings = (PyObject **) malloc(NUM_ERRORS * sizeof(PyObject *));
    if (!self->error_strings) return PyErr_NoMemory();
    for (int i=0; i<NUM_ERRORS; i++) {
        self->error_strings[i] = NULL;
    }
    for (int i=0; i<NUM_ERRORS; i++) {
        self->error_strings[i] = PyUnicode_FromString(ERRORNAMES[i]);
        if (self->error_strings[i] == NULL) return NULL;
    }
    self->GAP_OBJECT = PyUnicode_FromString("-");
    if (!self->GAP_OBJECT) return NULL;
    self->wpfile = NULL;
    self->num_samples = 0;
    self->status = 0;
    self->p_int = NULL;
    self->n_int = 0;
    self->p_float = NULL;
    self->n_float = 0;
    self->p_str = NULL;
    self->n_str = 0;
    self->gt_p = NULL;
    self->gt_n = 0;
    self->gt_num = 0;
    self->has_index = 0;
    self->fname = NULL;
    self->header = NULL;
    self->record = NULL;
    self->file = NULL;
    self->first_contig = NULL;

    return (PyObject *) self;
}

const char doc_VCF[] = "VCF(fname, subset=None, dumpfile=None, require_index=False)\n"
              "VCF/BCF parser using htslib.\n\n"
              ":param fname: input VCF/BCF file name. "
                "Gzip-compressed files are supported.\n"
              ":param subset: sequence of sample names to import. "
                "The order of samples in this sequence is not considered. "
                "Duplicated names in this sequence are ignored. "
                "Other samples are ignored. This is useful to speed up parsing.\n"
              ":param dumpfile: name of an output VCF/BCF file where "
                "lines can be written as needed using :meth:`.dump_record`. "
                "The input VCF header is used as is. The dump file can be "
                "closed at any time using :meth:`.dump_close` and is "
                "closed by by default when the current instance is destroyed.\n"
              ":param require_index: require that the default index is present. "
                "By default, it is loaded if present, otherwhise the file "
                "is processed without index.\n\n"
              "Index is only loaded at object creation time.\n\n"
              ".. versionchanged:: 3.6\n"
              "    The argument *index* is not supported anymore.\n";

// INIT METHOD: open file, read header
static int VCF_init(VCF_object * self, PyObject * args, PyObject * kwargs) {

    /* Process arguments 
     ********************/

    // argument variables
    PyObject * bytes_fname;
    PyObject * bytes_index = NULL;
    PyObject * bytes_dumpfile = NULL;
    const char * fname;
    PyObject * subset = NULL;
    const char * dumpfile = NULL;
    signed require_index = 0;

    // parse arguments
    static char *kwlist[] = {"fname", "subset", "dumpfile", "require_index", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O&|OO&p", kwlist, PyUnicode_FSConverter, &bytes_fname, &subset, PyUnicode_FSConverter, &bytes_dumpfile, &require_index)) {
        return -1;
    }

    // macro to clean bytes objects corresponding to file names
    #define CLEAN \
        Py_DECREF(bytes_fname); \
        Py_XDECREF(bytes_dumpfile);

    // convert VCF file name to string
    fname = PyBytes_AsString(bytes_fname);
    if (fname == NULL) {
        CLEAN
        return -1;
    }

    // convert dumpfile name to string
    if (bytes_dumpfile) {
        dumpfile = PyBytes_AsString(bytes_dumpfile);
        if (dumpfile == NULL) {
            CLEAN
            return -1;
        }
    }

    /* load reader (open VCF file)
     ******************************/

    self->readers = bcf_sr_init();
    if (!self->readers) {
        PyErr_NoMemory();
        CLEAN;
        return -1;
    }
    bcf_sr_set_opt(self->readers, BCF_SR_REQUIRE_IDX);
    if (!bcf_sr_add_reader(self->readers, fname)) {
        if ((self->readers->errnum == idx_load_failed || self->readers->errnum == not_bgzf) && require_index == 0) {

            // try again
            bcf_sr_destroy(self->readers);
            self->readers = bcf_sr_init();
            if (!self->readers) {
                PyErr_NoMemory();
                CLEAN;
                return -1;
            }
            if (!bcf_sr_add_reader(self->readers, fname)) {
                PyErr_Format(PyExc_ValueError, "an error occurred when opening VCF file %s: %s", fname, bcf_sr_strerror(self->readers->errnum));
                CLEAN;
                return -1;
            }
        }
        else {
            PyErr_Format(PyExc_ValueError, "an error occurred when opening VCF file %s (index required): %s", fname, bcf_sr_strerror(self->readers->errnum));
            CLEAN;
            return -1;
        }
    }

    // set shortcut pointers
    self->reader = self->readers->readers+0;
    self->header = self->reader->header;
    self->fname = self->reader->fname;
    self->file = self->reader->file;

    // determine if an index has been loaded
    self->has_index = self->reader->bcf_idx || self->reader->tbx_idx; 

    // if so, record the name of the first chromosome to allow restart
    if (self->has_index && self->readers->regions && self->readers->regions->nseqs > 0) {
        self->first_contig = self->readers->regions->seq_names[0];
    }

    // get ID of PASS INFO (used to skip PASS as a lone filter value)
    self->pass_id = bcf_hdr_id2int(self->header, BCF_DT_ID, "PASS");

    /* specify subset of samples
     ****************************/

    if (subset && subset != Py_None) {
        PyObject * item;
        subset = PySequence_Fast(subset, "subset: expect a sequence of strings");
        if (!subset) {
            CLEAN;
            return -1;
        }
        unsigned int n = PySequence_Fast_GET_SIZE(subset);
        if (n == 0) {
            if (bcf_hdr_set_samples(self->header, NULL, 0)) {
                Py_DECREF(subset);
                PyErr_SetString(PyExc_ValueError, "problem setting null list of samples");
                CLEAN;
                return -1;
            }
        }
        else {
            char * list = NULL, * list2;
            unsigned int c = 0, d;
            for (unsigned int i=0; i<n; i++) {
                item = PySequence_Fast_GET_ITEM(subset, i);
                if (!PyUnicode_Check(item)) {
                    if (list) free(list);
                    Py_DECREF(subset);
                    PyErr_SetString(PyExc_TypeError, "subset: expect a sequence of strings");
                    CLEAN;
                    return -1;
                }
                PyObject * string = PyUnicode_AsEncodedString(item, "utf-8", "strict");
                if (!string) {
                    if (list) free(list);
                    Py_DECREF(subset);
                    PyErr_SetString(PyExc_ValueError, "encoding error using utf-8");
                    CLEAN;
                    return -1;
                }
                d = c + PyBytes_GET_SIZE(string) + 1;
                list2 = realloc(list, d * sizeof(char));
                if (!list2) {
                    if (list) free(list);
                    Py_DECREF(subset);
                    Py_DECREF(string);
                }
                list = list2;

                strcpy(list+c, PyBytes_AS_STRING(string));
                list[d-1] = ',';
                c = d;
                Py_DECREF(string);
            }
            list[c-1] = '\0';

            int r = bcf_hdr_set_samples(self->reader->header, list, 0);
            if (r != 0) {
                if (list) free(list);
                if (r < -1) PyErr_SetString(PyExc_ValueError, "cannot set subset of samples");
                else PyErr_Format(PyExc_ValueError, "unknown sample at position %d", r);
                CLEAN;
                Py_DECREF(subset);
                return -1;
            }
            if (list) free(list);
        }

        Py_DECREF(subset);
    }
    else {
        if (!bcf_sr_set_samples(self->readers, "-", 0)) {
            PyErr_SetString(PyExc_ValueError, "cannot set subset of samples");
            CLEAN;
            return -1;
        }
    }

    self->num_samples = bcf_hdr_nsamples(self->reader->header);

    /* open dumpfile and write header
     *********************************/

    if (dumpfile) {
        #ifdef _WIN32
        char sep = 92; // "\\"
        #else
        char sep = 47; // "/"
        #endif

        const char * mode;
        const char * p = strrchr(dumpfile, sep);
        if (!p) p = dumpfile;
        else p++;
        
        if (!strcmp(dumpfile, fname)) {
            PyErr_Format(PyExc_ValueError, "dump file cannot have the same name as: %s", fname);
            CLEAN;
            return -1;
        }
        size_t l = strlen(p);
        if (l < 5) {
            PyErr_SetString(PyExc_ValueError, "invalid dump file name");
            CLEAN;
            return -1;
        }
        if (!strcmp(p + (l-4),".bcf")) mode = "wb";
        else {
            if (!strcmp(p + (l-4),".vcf")) mode = "wu";
            else {
                if (l < 8) {
                    PyErr_SetString(PyExc_ValueError, "invalid dump file name");
                    CLEAN;
                    return -1;
                }
                if (!strcmp(p + (l-7),".vcf.gz")) mode = "wz";
                else {
                    PyErr_SetString(PyExc_ValueError, "invalid dump file name");
                    CLEAN;
                    return -1;
                }
            }
        }
        
        self->wpfile = hts_open(dumpfile, mode);
        if (!self->wpfile) {
            PyErr_Format(PyExc_ValueError, "cannot open file: %s", p);
            CLEAN;
            return -1;
        }

        int res = bcf_hdr_write(self->wpfile, self->header);
        if (res != 0) {
            hts_close(self->wpfile);
            PyErr_SetString(PyExc_ValueError, "could not write header");
            CLEAN;
            return -1;
        }
    }

    /* terminate
     ************/

    CLEAN
    #undef CLEAN

    return 0;
}

/** READ A LINE
 ************************************/

void read_success(VCF_object * self) {
    self->record = self->reader->buffer[0];
    self->types = bcf_get_variant_types(self->record);
    self->status = 1;
    self->gt_num = 0;
} // this method set so variant upon reading a variant (for read() and goto())

const char doc_read[] = "Read one variant of the VCF file.\n\n"
                        "Return ``True`` if read is successful, "
                        "``False`` if end of file. "
                        ":exc:`ValueError` in case of critical error.\n\n"
                        ".. note:: Due to internal caching, parsing\n"
                        "   errors might appear at an earlier line\n"
                        "   than the actual error. To obtain details\n"
                        "   about the error, activate htslib logging\n"
                        "   with :func:`hts_set_log_level`.\n";

static PyObject * VCF_read(VCF_object * self, PyObject * args) { // when VCF will be pure C: PyObject * Py_UNUSED(ignored) (also for other methods)
    self->status = 0; // in case an error/EOF occurs
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future

    // try to read next line
    int res = bcf_sr_next_line(self->readers);

    // in case an error was detected on this read
    if (self->readers->errnum) {
        PyErr_Format(PyExc_ValueError,
            "an error occurred when reading VCF file %s: %s",
            self->reader->fname, bcf_sr_strerror(self->readers->errnum));
        self->readers->errnum = 0;
        return NULL;
    }

    if (res == 1) {
        read_success(self);
        Py_RETURN_TRUE;
    }
    else {
        Py_RETURN_FALSE;
    }
}

/** WRITE A LINE
 ************************************/
 
const char doc_dump_record[] = "Write one variant of the VCF file. "
                         "Return ``None`` if write is successful, "
                         ":exc:`ValueError` in case of critical error.";

static PyObject * VCF_dump_record(VCF_object * self, PyObject * args) {
    if (!self->status) {
        PyErr_SetString(PyExc_ValueError, "no record available");
        return NULL;
    }
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (!self->wpfile) {
        PyErr_SetString(PyExc_ValueError, "no dump file open");
        return NULL;
    }
    int res = bcf_write(self->wpfile, self->header,
                                      self->record);
    if (res != 0) {
        PyErr_SetString(PyExc_ValueError, "critical error while writing a variant");
        return NULL;
    }
    Py_RETURN_NONE;
}

/** CLOSE THE DUMPFILE
 ************************************/
 
const char doc_close[] = "Close the dumpfile VCF. "
                         "Return ``None`` if operation is successful, "
                         ":exc:`ValueError` in case of critical error.";
 
static PyObject * VCF_dump_close(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (!self->wpfile) {
        PyErr_Format(PyExc_ValueError, "no dump file open");
        return NULL;
    }
    int res = hts_close(self->wpfile);
    if (res != 0) {
        PyErr_SetString(PyExc_ValueError, "critical error while closing dump file");
        return NULL;
    }
    self->wpfile = NULL;
    Py_RETURN_NONE;
}
 
/** GET LIST OF CONTIGS
 ************************************/

const char doc_get_chromosomes[] = "Generate a :class:`dict` of chromosomes or contigs. "
                             "Get the list of chromosomes (contigs) defined in the header "
                             "and return a :class:`dict` with the chromosome "
                             "names as keys and chromosome lengths as values. "
                             "In case no chromosomes are defined, return ``None``. "
                             "The chromosome lengths may be 0 (e.g. if the "
                             "chromosome names are obtained through an index file).\n\n"
                             ".. versionadded:: 3.6\n";

static PyObject * VCF_get_chromosomes(VCF_object * self, PyObject * arguments) {
    if (!PyArg_ParseTuple(arguments, "")) return NULL; // remove in future

    if (!self->header || self->header->n[BCF_DT_CTG] == 0) Py_RETURN_NONE;

    PyObject * dict = PyDict_New();
    if (dict == NULL) return NULL;

    PyObject * key, *value;

    for (int i=0; i<self->header->n[BCF_DT_CTG]; i++) {

        // get key
        key = PyUnicode_FromString(bcf_hdr_id2name(self->header, i));
        if (!key) return NULL;

        // get value
        #if (PY_VERSION_HEX >= 0x30e0000)
        value = PyLong_FromUInt64(self->header->id[BCF_DT_CTG][i].val->info[0]);
        #else
        value = PyLong_FromLong(self->header->id[BCF_DT_CTG][i].val->info[0]);
        #endif
        if (!value) { Py_DECREF(key); return NULL; }

        // load key,value pair
        if (PyDict_SetItem(dict, key, value) != 0) {
            Py_DECREF(dict);
            Py_DECREF(key);
            Py_DECREF(value);
            return NULL;
        }
        Py_DECREF(key);
        Py_DECREF(value);
    }

    return dict;
}
 
/** NAVIGATION
    (indexed bcf files)
 ************************************/

const char doc_goto[] = "goto(target[, position, [limit]])\n"
        "Move to a given location in the file. "
        "Data at the new location are available immediately with no "
        "need to call :meth:`read` (this method should be understood "
        "as a call to :meth:`read` at an arbitrary location). "
        "If *position* is not specified, move to the  first "
        "available position of contig *target*. "
        "If *target* does not exist in file, or in case of unexpected "
        "parsing error, a :class:`ValueError` is thrown. "
        "By default, *limit* is equal to *position* + 1 (meaning that "
        "only the exact position can be retrieved). "
        "If this condition is not met (in particular if *position* is "
        "past the end of the contig *target*), return ``False``).\n\n"
        ":return: ``True`` if a variant is available in the requested "
        "range, ``False`` otherwise. In case the method returns "
        "``False``, the user is not expected to call :meth:`read` "
        "directly (the behaviour is currently undefined).\n\n"
        ".. note::\n"
        "    Only available for indexed BCF.\n\n"
        ".. versionchanged:: 3.4\n"
        "    The method returns ``False`` and doesn't raise an "
        " exception if the target position is out of range.";
static PyObject * VCF_goto(VCF_object * self, PyObject * args, PyObject * kwargs) {
    if (!self->has_index) {
        PyErr_SetString(PyExc_ValueError, "an index is required");
        return NULL;
    }

    self->status = 0; // in case an error/EOF occurs
    const char * target;
    int pos = -1;
    long int limit = -1;

    static char *kwlist[] = {"target", "pos", "limit", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|il", kwlist, &target, &pos, &limit)) {
        return NULL;
    }

    if (pos == -1) {
        pos = 0;
        if (limit == -1) limit = HTS_POS_MAX;
    }
    else {
        if (limit == -1) limit = pos + 1;
        else if (limit == END_VALUE) limit = HTS_POS_MAX;
    }

    if (limit < 1) {
        PyErr_Format(PyExc_ValueError, "`limit` must be strictly positive");
        return NULL;
    }
    if (limit <= pos) {
        PyErr_Format(PyExc_ValueError, "`limit` must be larger than `pos`");
        return NULL;
    }

    if (bcf_sr_seek(self->readers, target, pos) != 0) {
        if (self->readers->errnum) {
            PyErr_Format(PyExc_ValueError, "an error occurred when seeking position in VCF file: %s", bcf_sr_strerror(self->readers->errnum));
            return NULL;
        }
        if (pos == 0 || bcf_sr_seek(self->readers, target, 0) != 0) {
            PyErr_Format(PyExc_ValueError, "cannot find contig %s in %s", target, self->fname);
            return NULL;
        }
        Py_RETURN_FALSE;
    }

    // actually read the line
    if (bcf_sr_next_line(self->readers) != 1) {
        if (self->readers->errnum) {
            PyErr_Format(PyExc_ValueError, "an error occurred when reading VCF file %s: %s", self->reader->fname, bcf_sr_strerror(self->readers->errnum));
            return NULL;
        }
        Py_RETURN_FALSE;
    }

    if (self->reader->buffer[0]->pos >= limit) Py_RETURN_FALSE; // record is updated by read_success which I don't want to call too early
    if (strcmp(bcf_hdr_id2name(self->header, self->reader->buffer[0]->rid), target)) Py_RETURN_FALSE;
    read_success(self);
    Py_RETURN_TRUE;
}

const char doc_restart[] = "restart()\n"
        "Return to the beginning of the file. The parser is restored "
        "the initial step (before reading the first variant). No index "
        "is needed.\n\n"
        ".. versionadded:: 3.6\n";
static PyObject *VCF_restart(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future

    self->status = 0;
    self->gt_num = 0;

    if (!self->first_contig) {
        PyErr_SetString(PyExc_ValueError, "cannot restart file: unknown first contig");
        return NULL;
    }

    if (bcf_sr_seek(self->readers, self->first_contig, 0) != 0) {
        PyErr_SetString(PyExc_ValueError, "cannot restart file");
        return NULL;
    }
    if (self->readers->errnum) {
        PyErr_Format(PyExc_ValueError, "an error occurred when restarting VCF file: %s", bcf_sr_strerror(self->readers->errnum));
        return NULL;
    }
    Py_RETURN_NONE;
}

/** ACCESS METHODS
    (require that header was read
     -- always the case if object created)
 *******************************************/

const char doc_get_sample[] = "get_sample(index)\n"
                              "Get the name of the sample at index *index*.";
static PyObject * VCF_get_sample(VCF_object * self, PyObject * args) {
    int idx = 0;
    if (!PyArg_ParseTuple(args, "i", &idx)) return NULL;
    if (idx < 0) idx += self->num_samples;
    if (idx < 0 || idx >= self->num_samples) {
        PyErr_SetString(PyExc_IndexError, "sample index out of range");
        return NULL;
    }
    return PyUnicode_FromString(self->header->samples[idx]);
}

const char doc_get_samples[] = ":class:`list` of all samples.";
static PyObject * VCF_get_samples(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    PyObject * item, * list = PyList_New(self->num_samples);
    if (!list) return NULL;
    for (int i=0; i<self->num_samples; i++) {
        item = PyUnicode_FromString(self->header->samples[i]);
        if (item) PyList_SET_ITEM(list, i, item);
        else {
            Py_DECREF(list);
            return NULL;
        }
    }
    return list;
}

/** ACCESS METHODS
    (require that a line was read)
 ************************************/

// extract polymorphic type names from the flag
const char doc_get_types[] = "Get the type(s) of the last variant. "
                             "Return a :class:`list`. "
                             "Return ``None`` by default (no available data).";
static PyObject * VCF_get_types(VCF_object * self, PyObject * args) {
    if (self->status == 0) Py_RETURN_NONE;
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    PyObject * list = PyList_New(0);
    for (int i=0; i<NUM_TYPES; i++) {
        if (self->types & TYPES[i]) {
            Py_INCREF(self->type_strings[i]);
            if (PyList_Append(list, self->type_strings[i]) != 0) return NULL;
        }
    }
    return list;
}

// extract error names from the flag
const char doc_get_errors[] = "Errors while reading last variant. "
                              "Get the non-fatal errors generated while "
                              "importing last variant, as a list, "
                              "or ``None`` if nothing has been read.";
static PyObject * VCF_get_errors(VCF_object * self, PyObject * args) {
    if (self->status == 0) Py_RETURN_NONE;
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    PyObject * list = PyList_New(0);
    for (int i=0; i<NUM_ERRORS; i++) {
        if (self->record->errcode & ERRORS[i]) {
            Py_INCREF(self->error_strings[i]);
            if (PyList_Append(list, self->error_strings[i]) != 0) return NULL;
        }
    }
    return list;
}

// return a boolean to say if the polymorphism is SNP (and SNP only)
const char doc_is_snp[] = "Check if last variant is a SNP. "
                          "``True`` if the last variant is of type SNP, and SNP only.\n\n"
                          ".. versionchanged:: 3.4\n"
                          "    SNPs overlapping a deletion are now considered to be SNPs";
static PyObject * VCF_is_snp(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (self->status == 0) Py_RETURN_FALSE;
    return PyBool_FromLong((self->types & VCF_SNP) && ((self->types & (~(VCF_SNP | VCF_OVERLAP))) == 0));
}

// return a boolean to say if the polymorphism is SNP of invariant
const char doc_is_single[] = "Check if last variant is invariant or SNP. "
                          "``True`` if the last variant has no other flag than SNP and deletion overlap.\n\n"
                          ".. versionadded:: 3.4\n\n"
                          ".. versionchanged:: 3.6\n"
                          "    ``False`` is returned if an allele length is different than 1.";
static PyObject * VCF_is_single(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (self->status == 0) Py_RETURN_FALSE;
    bcf_unpack(self->record, BCF_UN_STR); // unpack to get alleles
    for (unsigned i=0; i<self->record->n_allele; i++) {
        if (strlen(self->record->d.allele[i]) != 1) Py_RETURN_FALSE;
    }
    return PyBool_FromLong((self->types & ~(VCF_SNP | VCF_OVERLAP)) == 0);
}

// identify variant type
const char doc_get_allele_type[] = "Summary of type of last variant. "
                "Return 0 if all alleles have length 1 and are valid DNA codes "
                "(SNPs or non-variant bases), "
                "1 if there is at least one allele with length >1 but all alleles contain valid DNA codes "
                "(indels), "
                "2 there is at least one non-DNA codes in alleles, "
                "or ``None`` if no data are available.\n\n"
                ".. versionadded:: 3.4.";
static PyObject * VCF_get_allele_type(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (self->status == 0) Py_RETURN_NONE;
    unsigned int j;
    long flag = 0;
    for (unsigned int i=0; i<self->record->n_allele; i++) {
        for (j=0; self->record->d.allele[i][j] != '\0'; j++) {
            switch(self->record->d.allele[i][j]) {
                case 'A': case 'a':
                case 'C': case 'c':
                case 'G': case 'g':
                case 'T': case 't':
                case 'N': case 'n':
                case '*': break;
                default: return PyLong_FromLong(2);
            }
        }
        if (j>1) flag |= 1;
    }
    return PyLong_FromLong(flag);
}

// get chromosome name
const char doc_get_chrom[] = "Chromosome or contig name. "
                             "Return ``None`` by default (no available data).";
static PyObject * VCF_get_chrom(VCF_object * self, PyObject * args) {
    static char * kwlist[] = {};
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (self->status == 0) Py_RETURN_NONE;
    return PyUnicode_FromString(bcf_hdr_id2name(self->header, self->record->rid));
}

// get position
const char doc_get_pos[] = "Chromosome position. "
                             "Return ``None`` by default (no available data).";
static PyObject * VCF_get_pos(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (self->status == 0) Py_RETURN_NONE;
    return PyLong_FromLong(self->record->pos);
}

// get quality
const char doc_get_quality[] = "Quality value. "
                             "Return ``None`` by default (no available data or missing value).";
static PyObject * VCF_get_qual(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (self->status == 0 || bcf_float_is_missing(self->record->qual)) Py_RETURN_NONE;
    bcf_unpack(self->record, BCF_UN_FLT); // necessary?
    return PyFloat_FromDouble(self->record->qual);
}

// get reference allele
const char doc_get_reference[] = "Reference allele. "
                                 "Return ``None`` by default (no available data).";
static PyObject * VCF_get_ref(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (self->status == 0) Py_RETURN_NONE;
    if (self->record->n_allele == 0) Py_RETURN_NONE;
    bcf_unpack(self->record, BCF_UN_STR);
    return PyUnicode_FromString(self->record->d.allele[0]);
}

// get list of alternate allele(s)
const char doc_get_alternate[] = ":class:`list` of alternate alleles. "
                               "If present, the * allele (position overlapping previous deletion) "
                               "is omitted. Return ``None`` by default (no available data).\n\n"
                                 " .. versionchanged:: 3.5.1\n"
                                 "     Omit the * allele.\n";
static PyObject * VCF_get_alt(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (self->status == 0) Py_RETURN_NONE;
    bcf_unpack(self->record, BCF_UN_STR);
    PyObject * list = PyList_New(0);
    if (list) {
        for (unsigned int i=1; i<self->record->n_allele; i++) {
            if ((self->types & VCF_OVERLAP) && !strcmp(self->record->d.allele[i], "*")) {
                continue; // don't load *
            }
            PyObject * item = PyUnicode_FromString(self->record->d.allele[i]);
            if (item) PyList_Append(list, item);
            else {
                Py_DECREF(list);
                return NULL;
            }
        }
    }
    return list;
}

// get list of allele(s)
const char doc_get_alleles[] = ":class:`list` of alleles. "
                               "If present, the * allele (position overlapping previous deletion) "
                               "is omitted. Return ``None`` by default (no available data).\n\n"
                                 " .. versionchanged:: 3.5.1\n"
                                 "     Omit the * allele.\n";
static PyObject * VCF_get_alleles(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (self->status == 0) Py_RETURN_NONE;
    bcf_unpack(self->record, BCF_UN_STR);
    PyObject * list = PyList_New(0);
    if (list) {
        for (unsigned int i=0; i<self->record->n_allele; i++) {
            if ((self->types & VCF_OVERLAP) && !strcmp(self->record->d.allele[i], "*")) {
                // don't load * as an allele
            }
            else {
                PyObject * item = PyUnicode_FromString(self->record->d.allele[i]);
                if (item) PyList_Append(list, item);
                else {
                    Py_DECREF(list);
                    return NULL;
                }
            }
        }
    }
    return list;
}

// get list of ID's
const char doc_get_id[] = "Get list of identifiers for the current variant. "
                          "Empty list if none provided. "
                          "``None`` if nothing has been read. "
                          "The uniqueness of ID's is not tested.";

static PyObject * VCF_get_id(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (self->status == 0) Py_RETURN_NONE;
    bcf_unpack(self->record, BCF_UN_FLT);
    PyObject * list = PyList_New(0);
    if (strcmp(self->record->d.id, ".")) { // only proceed if not missing
        size_t ln = strlen(self->record->d.id);
        for(char * p = strtok(self->record->d.id, ";"); p != NULL; p = strtok(NULL, ";")) {
            if (PyList_Append(list, PyUnicode_FromString(p)) != 0)  {
                *(p+strlen(p)) = ';'; self->record->d.id[ln] = '\0'; // repairing string before leaving
                return NULL;
            }
            *(p+strlen(p)) = ';'; // repair the string
        }
        self->record->d.id[ln] = '\0'; // remove the last separator
    }
    return list;
}

// get list of filter values
const char doc_get_filter[] = ":class:`list` of filters. "
                              "Return ``None`` by default (no available data).";
static PyObject * VCF_get_filter(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (self->status == 0) Py_RETURN_NONE;
    bcf_unpack(self->record, BCF_UN_FLT);
    PyObject * list = PyList_New(0);
    if (self->record->d.n_flt != 1 || self->record->d.flt[0] != self->pass_id) { // only proceed if filter is not PASS (if so, return empty list)
        for (int i=0; i<self->record->d.n_flt; i++) {
            if (PyList_Append(list, PyUnicode_FromString(bcf_hdr_int2id(self->header, BCF_DT_ID, self->record->d.flt[i]))) != 0) return NULL;
        }
    }
    return list;
}

// get a given info value (as a string, int, float or list of int or float)
const char doc_get_info[] = "get_info(tag)\n"
                            "Get a given INFO field. "
                            "Return ``None`` by default (no available data for key not available).";
static PyObject * VCF_get_info(VCF_object * self, PyObject * args) {
    if (self->status == 0) Py_RETURN_NONE;

    // get tag from argument
    char * tag;
    if (!PyArg_ParseTuple(args, "s", &tag)) return NULL;
    bcf_unpack(self->record, BCF_UN_INFO);

    int num, info_id;
    PyObject * item, *list;

    // get info specification (the info must be defined in the header)
    info_id = bcf_hdr_id2int(self->header, BCF_DT_ID, tag);
    if (info_id < 0) {
        PyErr_Format(PyExc_ValueError, "invalid info key: %s", tag);
        return NULL;
    }

    // avoid duplication of operations
    #define int_is_missing(x) (x==bcf_int32_missing)
    #define PROCESS(getter, p, n, Py, missing) { \
        num = getter(self->header, self->record, tag, &p, &n); \
        if (num == -3) Py_RETURN_NONE; \
        if (num < 0) { \
            PyErr_SetString(PyExc_ValueError, "cannot import INFO data"); \
            return NULL; \
        } \
        if (num == 1 && bcf_hdr_id2number(self->header, BCF_HL_INFO, info_id) == 1) { \
            if (missing(p[0])) Py_RETURN_NONE; \
            else return Py(p[0]); \
        } \
        else { \
            list = PyList_New(num); \
            if (!list) return NULL; \
            for (int idx=0; idx<num; idx++) { \
                if (missing(p[idx])) { \
                    Py_INCREF(Py_None); \
                    item = Py_None; \
                } \
                else { \
                    item = Py(p[idx]); \
                    if (!item) return NULL; \
                } \
                PyList_SET_ITEM(list, idx, item); \
            } \
            return list; \
        } \
    }

    // process field by type
    switch (bcf_hdr_id2type(self->header, BCF_HL_INFO, info_id)) {
        case BCF_HT_FLAG:
            num = bcf_get_info_flag(self->header, self->record, tag, NULL, NULL);
            if (num == -3) Py_RETURN_NONE;
            if (num < 0) {
                PyErr_SetString(PyExc_ValueError, "cannot import INFO data");
                return NULL;
            }
            item = PyBool_FromLong(num);
            if (!item) return NULL;
            return item;
        case BCF_HT_INT:
            PROCESS(bcf_get_info_int32, self->p_int, self->n_int, PyLong_FromLong, int_is_missing);
        case BCF_HT_REAL:
            PROCESS(bcf_get_info_float, self->p_float, self->n_float, PyFloat_FromDouble, bcf_float_is_missing);
        case BCF_HT_STR:
            num = bcf_get_info_string(self->header, self->record, tag, &self->p_str, &self->n_str);
            if (num == -3) Py_RETURN_NONE;
            if (num < 0) {
                PyErr_SetString(PyExc_ValueError, "cannot import INFO data");
                return NULL;
            }
            item = PyUnicode_FromString(self->p_str);
            if (!item) return NULL;
            return item;
        default:
            PyErr_SetString(PyExc_RuntimeError, "cannot process info type");
            return NULL;
    }
    #undef int_is_missing
    #undef PROCESS
    Py_RETURN_NONE; // should be unused
}

// get a given format value
const char doc_get_format[] = "get_format(tag, index)\n"
                              "Get a given FORMAT field. " 
                              "Return ``None`` by default (no available data for key not available).";
static PyObject * VCF_get_format(VCF_object * self, PyObject * args) {
    // get arguments
    const char * tag;
    int idx;
    if (!PyArg_ParseTuple(args, "si", &tag, &idx)) {
        return NULL;
    }
    if (self->status == 0) Py_RETURN_NONE;
    bcf_unpack(self->record, BCF_UN_FMT);

    int i, format_id, res, num, L;
    PyObject * list, *item;

    if (idx < 0) idx += self->num_samples;
    if (idx < 0 || idx >= self->num_samples) {
        PyErr_SetString(PyExc_IndexError, "sample index out of range");
        return NULL;
    }

    // get format specification (the format must be defined in the header)
    format_id = bcf_hdr_id2int(self->header, BCF_DT_ID, tag);
    if (format_id < 0) {
        PyErr_Format(PyExc_ValueError, "invalid format key: %s", tag);
        return NULL;
    }

    // avoid duplication of operations
    #define int_is_missing(x) (x==bcf_int32_missing)
    #define int_is_vector_end(x) (x==bcf_int32_vector_end)
    #define PROCESS(getter, p, n, Py, missing, vector_end) { \
        res = getter(self->header, self->record, tag, &p, &n); \
        if (res == -3) Py_RETURN_NONE; \
        if (res < 1) { \
            PyErr_SetString(PyExc_ValueError, "cannot import FORMAT data"); \
            return NULL; \
        } \
        if (res < self->num_samples) { \
            PyErr_SetString(PyExc_ValueError, "cannot import FORMAT data (invalid number of items)"); \
            return NULL; \
        } \
        num = res/self->num_samples; \
        if (num == 1 && bcf_hdr_id2number(self->header, BCF_HL_FMT, format_id) == 1) { \
            if (missing(p[idx])) Py_RETURN_NONE; \
            else return Py(p[idx]); \
        } \
        else { \
            list = PyList_New(0); \
            if (!list) return NULL; \
            for (i=0; i<num; i++) { \
                if (vector_end(p[idx*num+i])) break;\
                if (missing(p[idx*num+i])) { \
                    Py_INCREF(Py_None); \
                    item = Py_None; \
                } \
                else { \
                    item = Py(p[idx*num+i]); \
                    if (!item) { \
                        Py_DECREF(list); \
                        return NULL; \
                    } \
                } \
                if (PyList_Append(list, item) != 0) { \
                    Py_DECREF(list); \
                    return NULL; \
                } \
            } \
            return list; \
        } \
    }

    // process field by type
    switch (bcf_hdr_id2type(self->header, BCF_HL_FMT, format_id)) {
        case BCF_HT_INT:
            PROCESS(bcf_get_format_int32, self->p_int, self->n_int, PyLong_FromLong, int_is_missing, int_is_vector_end);
        case BCF_HT_REAL:
            PROCESS(bcf_get_format_float, self->p_float, self->n_float, PyFloat_FromDouble, bcf_float_is_missing, bcf_float_is_vector_end);
        case BCF_HT_STR:
            res = bcf_get_format_char(self->header, self->record, tag, &self->p_str, &self->n_str);
            if (res == -3) Py_RETURN_NONE;
            if (res < self->num_samples) {
                PyErr_SetString(PyExc_ValueError, "cannot import FORMAT data");
                return NULL;
            }
            num = res / self->num_samples;
            L = strlen(self->p_str+idx*num);
            if (num < L) L = num;
            item = PyUnicode_FromStringAndSize(self->p_str+idx*num, L);
            if (!item) return NULL;
            return item;
        default:
            PyErr_SetString(PyExc_RuntimeError, "cannot process format type");
            return NULL;
    }
    #undef int_is_missing
    #undef int_is_vector_end
    #undef PROCESS
    Py_RETURN_NONE; // should be unused
}

// get all info values
const char doc_get_infos[] = ":class:`dict` of INFO fields. "
                             "Return ``None`` by default (no available data).";
static PyObject * VCF_get_infos(VCF_object * self, PyObject * arguments) {
    if (!PyArg_ParseTuple(arguments, "")) return NULL; // remove in future
    if (self->status == 0) Py_RETURN_NONE;
    bcf_unpack(self->record, BCF_UN_INFO);

    PyObject * dict = PyDict_New();
    if (dict == NULL) return NULL;

    PyObject * key, *value, *args;
    const char * tag;

    for (unsigned int idx=0; idx<self->record->n_info; idx++) {

        // get key
        tag = self->header->id[BCF_DT_ID][self->record->d.info[idx].key].key;

        key = PyUnicode_FromString(tag);
        if (!key) return NULL;

        // get value
        args = Py_BuildValue("(s)", tag);
        if (!args) return NULL;
        value = VCF_get_info(self, args);
        Py_DECREF(args);
        if (value == NULL) return NULL;
        if (PyDict_SetItem(dict, key, value) != 0) {
            Py_DECREF(dict);
            Py_DECREF(key);
            Py_DECREF(value);
            return NULL;
        }
        Py_DECREF(key);
        Py_DECREF(value);
    }

    return dict;
}

// get all format values for all samples
const char doc_get_formats[] = "FORMAT fields for all samples. "
                               "Return a :class:`list` of :class:`dict` instances. "
                               "Return ``None`` by default (no available data).";
static PyObject * VCF_get_formats(VCF_object * self, PyObject * arguments) {
    if (!PyArg_ParseTuple(arguments, "")) return NULL; // remove in future
    if (self->status == 0) Py_RETURN_NONE;
    bcf_unpack(self->record, BCF_UN_FMT);

    PyObject * list = PyList_New(self->num_samples);
    if (!list) return NULL;

    PyObject * dict;
    PyObject * key, *value, *args;
    const char * tag;

    for (int sam=0; sam<self->num_samples; sam++) {

        dict = PyDict_New();
        if (dict == NULL) {
            Py_DECREF(list);
            return NULL;
        }
        for (unsigned int fmt=0; fmt<self->record->n_fmt; fmt++) {

            // get key
            tag = self->header->id[BCF_DT_ID][self->record->d.fmt[fmt].id].key;
            if (!strcmp(tag, "GT")) continue;

            key = PyUnicode_FromString(tag);
            if (!key) {
                Py_DECREF(list);
                Py_DECREF(dict);
                return NULL;
            }

            // get value
            args = Py_BuildValue("(si)", tag, sam);
            if (!args) return NULL;
            value = VCF_get_format(self, args);
            Py_DECREF(args);
            if (value == NULL) {
                Py_DECREF(list);
                Py_DECREF(dict);
                Py_DECREF(key);
                return NULL;
            }
            if (PyDict_SetItem(dict, key, value) != 0) {
                Py_DECREF(list);
                Py_DECREF(dict);
                Py_DECREF(key);
                Py_DECREF(value);
                return NULL;
            }
            Py_DECREF(key);
            Py_DECREF(value);
        }
        PyList_SET_ITEM(list, sam, dict);
    }

    return list;
}

// get all GT values for the last site
static int VCF_get_GT(VCF_object * self) {
    if (self->status == 0) return 0;
    bcf_unpack(self->record, BCF_UN_FMT);
    int ngt = bcf_get_genotypes(self->header, self->record, &self->gt_p, &self->gt_n);
    if (ngt <= 0) return 0;
    self->gt_num = ngt/self->num_samples;
    return 1;
}

const char doc_get_genotypes[] = "Get genotypes. "
                                 "Return a :class:`list` giving, for each sample, "
                                 "the :class:`list` of alleles composing its genotype. "
                                 "To generate a :class:`.Site` object, use :meth:`.as_site`. "
                                 "Return ``None`` by default (no data available).\n\n"
                                 " .. versionchanged 3.4::\n"
                                 "    In case of overlapping deletion, the ``*`` allele "
                                 " will be replaced by the gap character (``-``).";
static PyObject * VCF_get_genotypes(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (self->gt_num == 0 && VCF_get_GT(self) == 0) Py_RETURN_NONE;

    int i, j;
    int32_t * p;
    PyObject * list, * item, * value;
    list = PyList_New(self->num_samples);
    if (!list) return NULL;

    for (i=0; i<self->num_samples; i++) {
        item = PyList_New(0);
        if (!item) {
            Py_DECREF(list);
            return NULL;
        }
        p = self->gt_p + i * self->gt_num;
        for (j=0; j<self->gt_num; j++) {
            if (p[j] == bcf_int32_vector_end) break; // sample has smaller ploidy
            if (bcf_gt_is_missing(p[j])) { // missing allele
                Py_INCREF(Py_None);
                if (PyList_Append(item, Py_None) != 0) {
                    Py_DECREF(list);
                    Py_DECREF(item);
                    return NULL;
                }
                continue;
            }
            if (bcf_gt_allele(p[j]) >= self->record->n_allele) {
                Py_DECREF(list);
                Py_DECREF(item);
                PyErr_SetString(PyExc_ValueError, "invalid allele in GT field");
                return NULL;
            }
            value = PyUnicode_FromString(self->record->d.allele[bcf_gt_allele(p[j])]);
            if (!value) {
                Py_DECREF(list);
                Py_DECREF(item);
                return NULL;
            }
            if ((self->types & VCF_OVERLAP) && self->record->d.allele[bcf_gt_allele(p[j])][0] == '*') {
                if (PyList_Append(item, self->GAP_OBJECT) != 0) {
                    Py_DECREF(list);
                    Py_DECREF(item);
                    Py_DECREF(value);
                    return NULL;
                }
            }
            else if (PyList_Append(item, value) != 0) {
                Py_DECREF(list);
                Py_DECREF(item);
                Py_DECREF(value);
                return NULL;
            }
        }
        PyList_SET_ITEM(list, i, item);
    }
    return list;
}

const char doc_get_phased[] = "Get booleans indicating if genotypes are phased. "
                              "The return value is the :class:`tuple`: "
                              "``(all_phased, phased_table)``, with a boolean "
                              "for all samples and all alleles beyond the "
                              "first. Return ``None`` is no appropriate data are available.";
static PyObject * VCF_get_phased(VCF_object * self, PyObject * args) {
    if (!PyArg_ParseTuple(args, "")) return NULL; // remove in future
    if (self->gt_num == 0 && VCF_get_GT(self) == 0) Py_RETURN_NONE;

    int i, j, all_b = 1;
    int32_t * p;
    PyObject * ret_tuple, * list, * item, * boolean, * all_phased;
    list = PyList_New(self->num_samples);
    if (!list) return NULL;

    for (i=0; i<self->num_samples; i++) {
        item = PyList_New(0);
        if (!item) {
            Py_DECREF(list);
            return NULL;
        }
        p = self->gt_p + i * self->gt_num;
        for (j=1; j<self->gt_num; j++) {
            if (p[j] == bcf_int32_vector_end) break; // sample has smaller ploidy
            all_b &= bcf_gt_is_phased(p[j]);
            boolean = PyBool_FromLong(bcf_gt_is_phased(p[j]));
            if (!boolean) {
                Py_DECREF(list);
                Py_DECREF(item);
                return NULL;
            }

            if (PyList_Append(item, boolean) != 0) {
                Py_DECREF(list);
                Py_DECREF(item);
                Py_DECREF(boolean);
                return NULL;
            }
        }
        PyList_SET_ITEM(list, i, item);
    }

    all_phased = PyBool_FromLong(all_b);
    if (!all_phased) {
        Py_DECREF(list);
        return NULL;
    }

    ret_tuple = PyTuple_New(2);
    if (!ret_tuple){
        Py_DECREF(list);
        Py_DECREF(all_phased);
        return NULL;
    }
    PyTuple_SET_ITEM(ret_tuple, 0, all_phased);
    PyTuple_SET_ITEM(ret_tuple, 1, list);

    return ret_tuple;
}

/** DEFINITION OF PYTHON TYPE
 ************************************/

// methods
static PyMethodDef VCF_methods[] = {
    {"read",            (PyCFunction) VCF_read,            METH_VARARGS, doc_read},
    {"get_chromosomes", (PyCFunction) VCF_get_chromosomes, METH_VARARGS, doc_get_chromosomes},
    {"dump_record",     (PyCFunction) VCF_dump_record,     METH_VARARGS, doc_dump_record}, // when VCF will be pure C: METH_NOARGS
    {"dump_close",      (PyCFunction) VCF_dump_close,      METH_VARARGS, doc_close},
    {"get_id",          (PyCFunction) VCF_get_id,          METH_VARARGS, doc_get_id},
    {"get_sample",      (PyCFunction) VCF_get_sample,      METH_VARARGS, doc_get_sample},
    {"get_samples",     (PyCFunction) VCF_get_samples,     METH_VARARGS, doc_get_samples},
    {"get_errors",      (PyCFunction) VCF_get_errors,      METH_VARARGS, doc_get_errors},
    {"get_types",       (PyCFunction) VCF_get_types,       METH_VARARGS, doc_get_types},
    {"is_snp",          (PyCFunction) VCF_is_snp,          METH_VARARGS, doc_is_snp},
    {"is_single",       (PyCFunction) VCF_is_single,       METH_VARARGS, doc_is_single},
    {"get_allele_type", (PyCFunction) VCF_get_allele_type, METH_VARARGS, doc_get_allele_type},
    {"get_quality",     (PyCFunction) VCF_get_qual,        METH_VARARGS, doc_get_quality},
    {"get_chrom",       (PyCFunction) VCF_get_chrom,       METH_VARARGS, doc_get_chrom},
    {"get_pos",         (PyCFunction) VCF_get_pos,         METH_VARARGS, doc_get_pos},
    {"get_reference",   (PyCFunction) VCF_get_ref,         METH_VARARGS, doc_get_reference},
    {"get_alternate",   (PyCFunction) VCF_get_alt,         METH_VARARGS, doc_get_alternate},
    {"get_alleles",     (PyCFunction) VCF_get_alleles,     METH_VARARGS, doc_get_alleles},
    {"get_filter",      (PyCFunction) VCF_get_filter,      METH_VARARGS, doc_get_filter},
    {"get_infos",       (PyCFunction) VCF_get_infos,       METH_VARARGS, doc_get_infos},
    {"get_formats",     (PyCFunction) VCF_get_formats,     METH_VARARGS, doc_get_formats},
    {"get_info",        (PyCFunction) VCF_get_info,        METH_VARARGS, doc_get_info},
    {"get_format",      (PyCFunction) VCF_get_format,      METH_VARARGS, doc_get_format},
    {"get_genotypes",   (PyCFunction) VCF_get_genotypes,   METH_VARARGS, doc_get_genotypes},
    {"get_phased",      (PyCFunction) VCF_get_phased,      METH_VARARGS, doc_get_phased},
    {"goto",            (PyCFunction) VCF_goto,            METH_VARARGS | METH_KEYWORDS, doc_goto},
    {"restart",         (PyCFunction) VCF_restart,         METH_VARARGS, doc_restart},
    {NULL, NULL, 0, NULL}
};

// simple members
static PyMemberDef VCF_members[] = {
    {"num_samples", T_INT, offsetof(VCF_object, num_samples), READONLY, "Number of samples."},
    {"has_index", T_BOOL, offsetof(VCF_object, has_index), READONLY, "Boolean indicating whether an index is available."},
    {NULL}
};

// type
static PyTypeObject VCF = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "_vcfparser.VCF",
    .tp_doc = doc_VCF,
    .tp_basicsize = sizeof(VCF_object),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = VCF_new,
    .tp_init = (initproc) VCF_init,
    .tp_dealloc = (destructor) VCF_dealloc,
    .tp_methods = VCF_methods,
    .tp_members = VCF_members
};

/** MODULE CONFIGURATION
 ************************************/

static PyMethodDef vcf_methods[] = {
    {"index_vcf", (PyCFunction)(void(*)(void))vcf_index_vcf, METH_VARARGS | METH_KEYWORDS, doc_index_vcf},
    {"hts_set_log_level", (PyCFunction)(void(*)(void))hts_set_log, METH_VARARGS | METH_KEYWORDS, doc_hts_set_log},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef vcfmodule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "_vcfparser",
    .m_doc = "VCF/BCF parser using HTSlib",
    .m_size = -1,
    vcf_methods
};

// module initialisation function
PyMODINIT_FUNC PyInit__vcfparser(void) { // N.B. double underscore because the module name is _vcf
    PyObject * m;
    if (PyType_Ready(&VCF) < 0) return NULL;

    PyObject * d = VCF.tp_dict;
    PyObject * END = PyLong_FromLong(END_VALUE);
    if (END == NULL || PyDict_SetItemString(d, "END", END) < 0) return NULL;
    Py_DECREF(END);

    m = PyModule_Create(&vcfmodule);
    if (!m) return NULL;

    // add the VCF type to the module
    Py_INCREF(&VCF);
    if (PyModule_AddObject(m, "VCF", (PyObject *) &VCF) < 0) {
        Py_DECREF(&VCF);
        Py_DECREF(m);
        return NULL;
    }

    // add END as class attribute
        // https://llllllllll.github.io/c-extension-tutorial/member-vs-getset.html
        // https://stackoverflow.com/questions/46133021/how-to-define-static-class-attributes-in-python-from-c

    hts_set_log_level(HTS_LOG_OFF); // by default, prevent htslib log messages in case of errors/warnings
    return m;
}
