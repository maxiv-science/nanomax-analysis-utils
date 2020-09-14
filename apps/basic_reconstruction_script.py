"""
Offline data preparation and reconstruction for standard NanoMAX ptycho.

This script is adapted for and requires ptypy 0.3. It is tested with
MPI on the compute cluster.
"""

import sys
import numpy as np
import ptypy
from ptypy.core import Ptycho
from ptypy import utils as u
from distutils.version import LooseVersion

## simplest possible input #############################################
detector = 'eiger' # or 'merlin' or 'pilatus'
folder = '/data/staff/nanomax/commissioning_2020-1/20200130/raw/sample'
scannr = int(sys.argv[1])
distance = 4.05
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
p.scans.scan00.data.name = 'NanomaxContrast'
p.scans.scan00.data.path = folder
p.scans.scan00.data.detector = detector
p.scans.scan00.data.maskfile = {'merlin': '/data/visitors/nanomax/common/masks/merlin/latest.h5',
								'pilatus': None,
                                'eiger': None,}[detector]
p.scans.scan00.data.scanNumber = scannr
p.scans.scan00.data.xMotor = 'sx'
p.scans.scan00.data.yMotor = 'sy'
p.scans.scan00.data.shape = 256
p.scans.scan00.data.save = None
p.scans.scan00.data.center = None # auto, you can also set (i, j) center here.
p.scans.scan00.data.orientation = {'merlin': (False, False, True), 'pilatus': None, 'eiger': None}[detector]
p.scans.scan00.data.distance = distance
p.scans.scan00.data.psize = {'pilatus': 172e-6, 'merlin': 55e-6, 'eiger': 75e-6}[detector]
p.scans.scan00.data.I0 = None # can be like 'alba2/1'
p.scans.scan00.data.min_frames = 10
p.scans.scan00.data.load_parallel = 'all'

# Scan parameters: illumination
p.scans.scan00.illumination = u.Param()
p.scans.scan00.illumination.model = None
p.scans.scan00.illumination.aperture = u.Param()
p.scans.scan00.illumination.aperture.form = 'circ'
p.scans.scan00.illumination.aperture.size = 500e-9

# Reconstruction parameters
p.engines = u.Param()
p.engines.engine00 = u.Param()
p.engines.engine00.name = 'DM'
p.engines.engine00.numiter = 100
p.engines.engine00.numiter_contiguous = 10

p.engines.engine01 = u.Param()
p.engines.engine01.name = 'ML'
p.engines.engine01.numiter = 100
p.engines.engine01.numiter_contiguous = 10

if LooseVersion(ptypy.version) < LooseVersion('0.3.0'):
    raise Exception('Use ptypy 0.3.0 or better!')

P = Ptycho(p,level=5)

