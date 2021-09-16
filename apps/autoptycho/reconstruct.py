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
detector   = 'eiger' # or 'merlin' or 'pilatus'
folder     = '../../raw/sample'
distance_m = 3.512	# distance between the sample and the detector in meters
defocus_um = 600	# distance between the focus and the sample plane in micro meters -> used for inital probe
scannr     = int(sys.argv[1])
########################################################################


# General parameters
p = u.Param()
p.verbose_level = 3
p.run = 'scan%d' % scannr
p.io = u.Param()
p.io.rfile = 'recons/%(run)s_%(engine)s.ptyr'
p.io.autoplot = u.Param()
p.io.autoplot.active = False

# Scan parameters
p.scans = u.Param()
p.scans.scan00 = u.Param()
p.scans.scan00.name = 'Full'
p.scans.scan00.coherence = u.Param()
p.scans.scan00.coherence.num_probe_modes = 1		# Number of probe modes

p.scans.scan00.data = u.Param()
p.scans.scan00.data.I0 = 'alba2/1'
p.scans.scan00.data.dfile = '%s.ptyd'%(p.run)
p.scans.scan00.data.save = 'append' 
p.scans.scan00.data.name = 'NanomaxContrast'
p.scans.scan00.data.path = folder
p.scans.scan00.data.detector = detector
p.scans.scan00.data.maskfile = {'merlin': '/data/visitors/nanomax/common/masks/merlin/latest.h5',
								'pilatus': None,
                                'eiger': None,}[detector]
#p.scans.scan00.data.maskfile = 'tmpmask.h5'
p.scans.scan00.data.scanNumber = scannr
p.scans.scan00.data.xMotor = 'sx'
p.scans.scan00.data.yMotor = 'sy'
p.scans.scan00.data.zDetectorAngle = 0#+0.78 # [deg]  # +0.78 measured Sep 2020
p.scans.scan00.data.shape = 256
p.scans.scan00.data.center = None # auto, you can also set (i, j) center here.
p.scans.scan00.data.orientation = {'merlin': (False, False, True), 'pilatus': None, 'eiger': None}[detector]
p.scans.scan00.data.distance = distance_m
p.scans.scan00.data.psize = {'pilatus': 172e-6, 'merlin': 55e-6, 'eiger': 75e-6}[detector]
p.scans.scan00.data.min_frames = 10
p.scans.scan00.data.xMotorAngle = 0
p.scans.scan00.data.load_parallel = 'all'

# Scan parameters: illumination
p.scans.scan00.illumination = u.Param()
p.scans.scan00.illumination.model = None
p.scans.scan00.illumination.aperture = u.Param()
p.scans.scan00.illumination.aperture.form = 'rect'
p.scans.scan00.illumination.aperture.size = 100e-9			           # at the focus
p.scans.scan00.illumination.propagation = u.Param()
p.scans.scan00.illumination.propagation.parallel = -1.*defocus_um*1e-6 # somehow this has to be negative to the basez axis 
p.scans.scan00.illumination.diversity = u.Param()
p.scans.scan00.illumination.diversity.noise = (.5, 1.0)
p.scans.scan00.illumination.diversity.power = .1
															           # -> being downstream of the focus means negative distance

# Reconstruction parameters
p.engines = u.Param()
p.engines.engine00 = u.Param()
p.engines.engine00.name = 'DM'
p.engines.engine00.numiter = 200
p.engines.engine00.numiter_contiguous = 10
p.engines.engine00.probe_support = 10

p.engines.engine01 = u.Param()
p.engines.engine01.name = 'ML'
p.engines.engine01.numiter = 200
p.engines.engine01.numiter_contiguous = 10
p.engines.engine01.probe_support = 10


if LooseVersion(ptypy.version) < LooseVersion('0.3.0'):
    raise Exception('Use ptypy 0.3.0 or better!')

P = Ptycho(p,level=5)

