# hdf5plugin is needed to read compressed Eiger files, and has to be
# imported before h5py.
try:
    import hdf5plugin 
    HAS_HDF5PLUGIN = True
except ImportError:
    print "hdf5plugin not found - won't be able to read compressed Eiger files"
    HAS_HDF5PLUGIN = False
    
from Scan import *
from nanomax_june2016 import *
from ptypy import *
from nanomax_week48 import *
from nanomax_april2017 import *
from nanomax_nov2017 import *
