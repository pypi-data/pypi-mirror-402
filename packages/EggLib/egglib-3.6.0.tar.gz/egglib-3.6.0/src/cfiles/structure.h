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

#ifndef EGGLIB_CLIB_STRUCTURE_H
#define EGGLIB_CLIB_STRUCTURE_H

typedef struct egglib_struct_clu egglib_struct_clu;
typedef struct egglib_struct_pop egglib_struct_pop;
typedef struct egglib_struct_idv egglib_struct_idv;

typedef struct {
    egglib_struct_clu * clust;
    unsigned int ploidy, nclust, cclust;
} egglib_struct;

struct egglib_struct_clu {
    egglib_struct * parent;
    egglib_struct_pop * pop;
    unsigned int npop, cpop;
};

struct egglib_struct_pop {
    egglib_struct_clu * parent;
    egglib_struct_idv * idv;
    unsigned int nidv, cidv;
};

struct egglib_struct_idv {
    egglib_struct_pop * parent;
    unsigned int * samples;
};


egglib_struct * egglib_struct_alloc(); ///< allocate object and initialize (NULL if memory error)
void egglib_struct_free(egglib_struct *); ///< free allocated memory
void egglib_struct_reset(egglib_struct *); ///< reset object

#endif
