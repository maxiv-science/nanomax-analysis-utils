"""
Offline data preparation and reconstruction for standard NanoMAX ptycho.

This script is adapted for and requires ptypy 0.3. It is tested with
MPI on the compute cluster.
"""

import numpy as np
import ptypy
from ptypy.core import Ptycho
from ptypy import utils as u
from distutils.version import LooseVersion

## simplest possible input #############################################
detector = 'pilatus' # or 'merlin'
folder = '/data/staff/nanomax/commissioning_2017-2/20171222/raw/siemens-star/'
scannr = 4
distance = 4.11
########################################################################


# General parameters
p = u.Param()
p.verbose_level = 3
p.run = 'scan%d' % scannr

# Scan parameters
p.scans = u.Param()
p.scans.scan00 = u.Param()
p.scans.scan00.name = 'Full'
p.scans.scan00.data = u.Param()
p.scans.scan00.data.name = 'NanomaxStepscanMay2017'
p.scans.scan00.data.dataPath = folder
p.scans.scan00.data.pilatusPath = p.scans.scan00.data.dataPath
p.scans.scan00.data.pilatusPattern = 'scan_%%04u_%s_%%04u.hdf5' % {'pilatus': 'pil100k', 'merlin': 'merlin'}[detector]
p.scans.scan00.data.datafile = folder.strip('/').split('/')[-1] + '.h5'
p.scans.scan00.data.hdfPath = 'entry_0000/measurement/%s/data' % {'pilatus': 'Pilatus', 'merlin': 'Merlin'}[detector]
p.scans.scan00.data.maskfile = {'merlin': '/data/visitors/nanomax/common/masks/mask_merlin_combined.h5',
                            'pilatus': None}[detector]
p.scans.scan00.data.scannr = scannr
p.scans.scan00.data.shape = 256
p.scans.scan00.data.save = None
p.scans.scan00.data.center = None # auto, you can also set (i, j) center here.
p.scans.scan00.data.orientation = {'merlin': (False, True, False), 'pilatus': None}[detector]
p.scans.scan00.data.distance = distance
p.scans.scan00.data.psize = {'pilatus': 172e-6, 'merlin': 55e-6}[detector]
p.scans.scan00.data.energy = 9.4
p.scans.scan00.data.min_frames = 10
p.scans.scan00.data.load_parallel = 'all'

# Scan parameters: illumination
p.scans.scan00.illumination = u.Param()
p.scans.scan00.illumination.model = None
p.scans.scan00.illumination.aperture = u.Param()
p.scans.scan00.illumination.aperture.form = 'circ'
p.scans.scan00.illumination.aperture.size = 300e-9 

# Reconstruction parameters
p.engines = u.Param()
p.engines.engine00 = u.Param()
p.engines.engine00.name = 'DM'
p.engines.engine00.numiter = 100
p.engines.engine00.numiter_contiguous = 10

p.engines.engine01 = u.Param()
p.engines.engine01.name = 'ML'
p.engines.engine01.numiter = 20

if LooseVersion(ptypy.version) < LooseVersion('0.3.0'):
    raise Exception('Use ptypy 0.3.0 or better!')

P = Ptycho(p,level=5)

