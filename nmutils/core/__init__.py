# hdf5plugin is needed to read compressed Eiger files, and has to be
# imported before h5py.
try:
    import hdf5plugin 
    HAS_HDF5PLUGIN = True
except ImportError:
    print("hdf5plugin not found - may not be able to read compressed Eiger files")
    HAS_HDF5PLUGIN = False
    
from .Scan import *
from .dummy import *
from .nanomax_nov2017 import flyscan_nov2017
from .nanomax_nov2018 import *
from .contrast_old import *
