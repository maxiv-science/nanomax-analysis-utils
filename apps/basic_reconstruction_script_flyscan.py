"""
Offline data preparation and reconstruction for NanoMAX flyscan ptycho.

You typically need a number of incoherent modes for flyscan data.
See the ptypy documentation.

The parameter structure for this data format is quite messy and should
be cleaned up. The NanomaxFlyscanNov2018 should be reimplemented with
less complicated inheritance (as a direct subclass of PtyScan) but
this will have to wait...

This script is adapted for and requires ptypy 0.3. It is tested with
MPI on the compute cluster.
"""

import numpy as np
import ptypy
from ptypy.core import Ptycho
from ptypy import utils as u
from distutils.version import LooseVersion

## simplest possible input #############################################
detector = 'pilatus'
folder = '/data/visitors/nanomax/20180514/2018121908/raw/backup/'
scannr = 3
distance = 4.05
########################################################################

# General parameters
p = u.Param()
p.verbose_level = 3
p.run = 'scan%d' % scannr
p.io = u.Param()

# Scan parameters
p.scans = u.Param()
p.scans.scan00 = u.Param()
p.scans.scan00.name = 'Full'
p.scans.scan00.coherence = u.Param()
p.scans.scan00.coherence.num_probe_modes = 5

p.scans.scan00.data = u.Param()
p.scans.scan00.data.name = 'NanomaxFlyscanNov2018'
p.scans.scan00.data.dfile = p.run + '.ptyd'
p.scans.scan00.data.xMotorFlipped = False
p.scans.scan00.data.yMotorFlipped = False
p.scans.scan00.data.xMotor = 'samx_buff'
p.scans.scan00.data.yMotor = 'samy_buff'
p.scans.scan00.data.nMaxLines = 20
#p.scans.scan00.data.firstLine=5
p.scans.scan00.data.dataPath = folder
p.scans.scan00.data.pilatusPath = p.scans.scan00.data.dataPath
p.scans.scan00.data.pilatusPattern = 'scan_%%04u_%s_%%04u.hdf5' % {'pilatus': 'pil100k', 'merlin': 'merlin'}[detector]
p.scans.scan00.data.datafile = folder.strip('/').split('/')[-1] + '.h5'
p.scans.scan00.data.hdfPath = 'entry_%%04u/measurement/%s/data' % {'pilatus': 'Pilatus', 'merlin': 'Merlin'}[detector]
p.scans.scan00.data.maskfile = {'merlin': '/data/visitors/nanomax/common/masks/mask_merlin_combined.h5',
                            'pilatus': None}[detector]
p.scans.scan00.data.scannr = scannr
p.scans.scan00.data.shape = 128
p.scans.scan00.data.save = 'append'
p.scans.scan00.data.center = None
##############
# the merlin is usually flipped vertically. but now it's also rotated
# 180 degrees, so that (vertical flip plus rotation) adds up to just
# a horizontal flip
p.scans.scan00.data.orientation = {'merlin':(False, False, True), 'pilatus':None}[detector]
##############
p.scans.scan00.data.distance = distance
p.scans.scan00.data.psize = {'pilatus': 172e-6, 'merlin': 55e-6}[detector]
p.scans.scan00.data.energy = 10.4
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
p.engines.engine00.numiter = 100#500
p.engines.engine00.numiter_contiguous = 5
p.engines.engine00.probe_center_tol = 3
#p.engines.engine00.probe_support = .5
#p.engines.engine00.probe_update_start = 50

p.engines.engine01 = u.Param()
p.engines.engine01.name = 'ML'
p.engines.engine01.numiter = 20

if LooseVersion(ptypy.version) < LooseVersion('0.3.0'):
    raise Exception('Use ptypy 0.3.0 or better!')

P = Ptycho(p,level=5)

