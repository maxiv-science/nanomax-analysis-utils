from cffi import FFI

ffibuilder = FFI()

ffibuilder.cdef('void read_cbf(char* cbf, int32_t* output, double* exposure_time);')

ffibuilder.set_source('_cbf',
"""
   #include <stdint.h>
   void read_cbf(char* cbf, int32_t* output, double* exposure_time);
""",
    sources=['cbf.c'])

if __name__ == '__main__':
    ffibuilder.compile(verbose=True)
 
