#cython: boundscheck=False, wraparound=False, initializedcheck=False, overflowcheck=False, cdivision=True, language_level=3
##cython: boundscheck=True, wraparound=True, initializedcheck=True, overflowcheck=True, cdivision=False, language_level=3
#!python

__license__ = "MIT"
__authors__ = ["Marvin Jens"]
__email__ = "marvin.jens@charite.de"

from types cimport *
from types import *

import numpy as np
cimport numpy as np
cimport cython
cimport openmp

from libc.math cimport exp, log
from libc.stdlib cimport abort, malloc, free

cpdef inline CIGAR_to_blocks(str cigar, int pos):
    cdef list blocks = []
    cdef UINT32_t L = len(py_str)
    cdef UINT8_t x = 0
    cdef UINT8_t nt = 0
    cdef bytes py_byte_str = py_str.encode('ascii')
    cdef unsigned char *seq = py_byte_str
    
    cdef UINT64_t idx = 0
    for x in range(L):
        idx = (idx << 2) | letter_to_bits[seq[x]]

    return idx
