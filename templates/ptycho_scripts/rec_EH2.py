"""
Offline data preparation and reconstruction for standard NanoMAX ptycho.

This script is adapted for and requires ptypy 0.7. It is tested with
MPI on the compute cluster.
"""

import os
import sys
import time
import numpy as np
import ptypy
from ptypy.core import Ptycho
from ptypy import utils as u
from distutils.version import LooseVersion
from mpi4py import MPI

if LooseVersion(ptypy.version) >= LooseVersion('0.5.0'):
    ptypy.load_ptyscan_module("nanomax")
    ptypy.load_gpu_engines(arch="cuda")

################################################################################
# hard coded user input 
################################################################################

detector         = 'eiger1m'
beamtime_basedir = '/data/staff/nanomax/commissioning_2025-2/20250819_startup/'
sample           = '0005_ptycho'

scannr           = 24
distance_m       = 3.650    # distance between the sample and the detector in meters
defocus_um       = 2000     # distance between the focus and the sample plane in micro meters -> used for inital probe
cropping         = 512
binning          = 1
probe_modes      = 1

if len(sys.argv)>=2:
    # scan number is given as first argument of this script
    scannr = int(sys.argv[1]) 

if len(sys.argv)>=3:
    # scan number is given as first argument of this script
    cropping = int(sys.argv[2]) 

################################################################################
# some preparations before the actual reaconstruction 
################################################################################

# define the output directories
out_dir         = f'{beamtime_basedir}/process/{sample}/scan_{scannr:0>6}/ptycho_ptypy_crop-{cropping}_bin-{binning}_Pmodes-{probe_modes}_dist-{distance_m:.3f}/'
out_dir_data    = f'{out_dir}data/'
out_dir_dumps   = f'{out_dir}dumps/'
out_dir_scripts = f'{out_dir}scripts/'
out_dir_rec     = f'{out_dir}rec/'

# and what the files are supposed to be called
path_data       = f'{out_dir_data}data_scan_{scannr:0>6}.ptyd'                                # the file with the prepared data
path_dumps      = f'{out_dir_dumps}dump_scan_{scannr:0>6}_%(engine)s_%(iterations)04d.ptyr'   # intermediate results
path_rec        = f'{out_dir_rec}rec_scan_{scannr:0>6}_%(engine)s_%(iterations)04d.ptyr'      # final reconstructions (of each engine)

# stuff to only do once
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
if rank==0:

    # create output directories if it does not already exists
    os.makedirs(out_dir,         exist_ok=True)
    os.makedirs(out_dir_data,    exist_ok=True)
    os.makedirs(out_dir_dumps,   exist_ok=True)
    os.makedirs(out_dir_scripts, exist_ok=True)
    os.makedirs(out_dir_rec,     exist_ok=True)

    # copy this file into this directory with a tag made from the time and date this script was run
    os.system(f'cp {str(__file__)} {out_dir_scripts}{time.strftime("%Y-%m-%d_%H%M")}_{os.path.basename(__file__)}')

################################################################################
# creating the parameter tree
################################################################################

# General parameters
p = u.Param()
p.verbose_level = 3
p.run = 'scan%d' % scannr
p.frames_per_block = 10000                  # reduce this number if you run out of memory on the GPU.

# where to put the reconstructions
p.io = u.Param()
p.io.home = out_dir_rec                     # where to save the final reconstructions
p.io.rfile = path_rec                       # how to name those files for the final reconstructions
p.io.autosave = u.Param()
p.io.autosave.rfile = path_dumps            # where to save the intermediate reconstructions and how to name them
p.io.autoplot = u.Param(active=False) 
p.io.interaction = u.Param(active=False) 

# Scan parameters
p.scans = u.Param()
p.scans.scan00 = u.Param()
p.scans.scan00.name = 'BlockFull'
p.scans.scan00.coherence = u.Param()
p.scans.scan00.coherence.num_probe_modes = probe_modes   # number of probe modes
p.scans.scan00.coherence.num_object_modes = 1            # number of object modes


p.scans.scan00.data = u.Param()
p.scans.scan00.data.name = 'NanomaxContrast'
p.scans.scan00.data.path = beamtime_basedir+'/raw/'+sample+'/'
p.scans.scan00.data.detector = detector
p.scans.scan00.data.maskfile = {'merlin': '/data/visitors/nanomax/common/masks/merlin/latest.h5',
                                'pilatus': None,
                                'eiger': '/data/visitors/nanomax/common/masks/eiger/eiger_4M_blinking_pixels.h5', # legacy
                                'eiger1m': None,
								'eiger4m': None}[detector]
p.scans.scan00.data.scanNumber = scannr
p.scans.scan00.data.xMotor = 'pseudo/x'
p.scans.scan00.data.yMotor = 'pseudo/y'
p.scans.scan00.data.zDetectorAngle = 0.0    # rotation of the detector around the beam axis in [deg]
p.scans.scan00.data.xyAxisSkewOffset = 0.0
p.scans.scan00.data.shape = cropping        # size of the window of the diffraction patterns to be used in pixel
p.scans.scan00.data.save = 'append'
p.scans.scan00.data.dfile = path_data       # once all data is collected, save it as .ptyd file
p.scans.scan00.data.center = (737,405)      # center of the diffraction pattern (y,x) in pixel or None -> auto
p.scans.scan00.data.cropOnLoad = True       # only load used part of detector frames -> save memory
                                            # requires center to be set explicitly
p.scans.scan00.data.xMotorFlipped = True
p.scans.scan00.data.yMotorFlipped = False
p.scans.scan00.data.orientation = {'merlin': (False, False, True),              # (do_transpose, do_flipud, do_fliplr)
                                   'pilatus': (False, True, False), 
                                   'eiger': (False, True, False),               # legacy
                                   'eiger1m': (False, True, False),
                                   'eiger4m': (False, True, False)}[detector]   # when mounted 180 degrees rotated
                                   #'eiger4m': (False, True, False)}[detector]  # old version when mounted the right way around
p.scans.scan00.data.distance = distance_m   # distance between sample and detector in [m] 
p.scans.scan00.data.psize = {'pilatus': 172e-6, 
                             'merlin': 55e-6, 
                             'eiger': 75e-6,   # legacy
                             'eiger1m': 75e-6,
                             'eiger4m': 75e-6}[detector]
p.scans.scan00.data.rebin = binning 
#p.scans.scan00.data.energy = energy_keV    # incident photon energy in [keV], now read from file
p.scans.scan00.data.I0 = None               # can be like 'alba2/1'
p.scans.scan00.data.min_frames = 10
p.scans.scan00.data.load_parallel = 'all'

################################################################################
# init probe from KB parameters
################################################################################
p.scans.scan00.illumination = u.Param()
p.scans.scan00.illumination.model = None
p.scans.scan00.illumination.aperture = u.Param()
p.scans.scan00.illumination.aperture.form = 'rect'
p.scans.scan00.illumination.aperture.size = 379e-6        # EH2-M1 aperture diameter 
p.scans.scan00.illumination.propagation = u.Param()
p.scans.scan00.illumination.propagation.focussed = 0.310  # EH2-M1 focal length
p.scans.scan00.illumination.propagation.parallel = 1.*defocus_um*1e-6 # propagate the inital guess -> gives phase curvature
p.scans.scan00.illumination.propagation.antialiasing = 1

### details on how to init multiple probe modes differently
p.scans.scan00.illumination.diversity = u.Param()
p.scans.scan00.illumination.diversity.power = 0.1         # Power of modes relative to main mode (zero-layer)
p.scans.scan00.illumination.diversity.noise = (0.5, 1.0)  # (rms, mfs, rms_mod, mfs_mod)

################################################################################
# init probe from previous reconstruction
################################################################################
#p.scans.scan00.illumination = u.Param()
#p.scans.scan00.illumination.model = 'recon'
#p.scans.scan00.illumination.recon = u.Param()
#p.scans.scan00.illumination.recon.rfile = '....ptyr'      # absolute path to a .ptyr file containing the probe to be used as initial guess
#p.scans.scan00.illumination.aperture = u.Param()
#p.scans.scan00.illumination.aperture.form = 'rect'        # this aperture is not optional
#p.scans.scan00.illumination.aperture.size = 10e-6         # either make it very large, or cut down the loaded probe
#p.scans.scan00.illumination.diversity = None

################################################################################
# init object from STXM / DPC information
################################################################################
#p.scans.scan00.sample = u.Param()
#p.scans.scan00.sample.model = 'stxm'
#p.scans.scan00.sample.process = None
#p.scans.scan00.sample.diversity = None

p.engines = u.Param()
############################################################################
# 1st use the difference map algorithm
############################################################################

p.engines.engine00 = u.Param()
p.engines.engine00.name = 'DM_cupy'
p.engines.engine00.numiter = 1000                     # number of iterations
p.engines.engine00.numiter_contiguous = 100           # Number of iterations without interruption
p.engines.engine00.probe_support = 3                  # non-zero probe area as fraction of the probe frame
#p.engines.engine00.probe_update_start = 50            # number of iterations before probe update starts

p.engines.engine00.obj_smooth_std = 10.               # gaussian smoothing (pixel) of the current object prior to update
p.engines.engine00.clip_object = (0,1)                # clip object amplitude into this interval

############################################################################
# 2nd use the maximum likelyhood algorithm
############################################################################

# general
p.engines.engine01 = u.Param()
p.engines.engine01.name = 'ML_cupy'
p.engines.engine01.numiter = 1000                     # number of iterations
p.engines.engine01.numiter_contiguous = 100           # Number of iterations without interruption
p.engines.engine01.probe_support = 3                  # non-zero probe area as fraction of the probe frame
#p.engines.engine01.probe_update_start = 50           # number of iterations before probe update starts

############################################################################
# start the reconstruction
############################################################################

if LooseVersion(ptypy.version) < LooseVersion('0.7.0'):
    raise Exception('Use ptypy 0.7.0 or better!')

P = Ptycho(p,level=5)

