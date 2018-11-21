# hdf5plugin is needed to read compressed Eiger files, and has to be
# imported before h5py.
try:
    import hdf5plugin 
    HAS_HDF5PLUGIN = True
except ImportError:
    print "hdf5plugin not found - may not be able to read compressed Eiger files"
    HAS_HDF5PLUGIN = False
    
from Scan import *
from dummy import *
from i13 import *
from i08 import *
from nanomax_week48 import *
from nanomax_april2017 import *
from nanomax_nov2017 import *
from nanomax_scalar import nanomax_scalar
from nanomax_nov2018 import *

