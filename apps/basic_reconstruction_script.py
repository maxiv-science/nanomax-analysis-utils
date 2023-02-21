"""
Offline data preparation and reconstruction for standard NanoMAX ptycho.

This script is adapted for and requires at least ptypy 0.3. 
It is tested with MPI on the compute cluster.
"""

import os
import sys
# sys.path.insert(0, '/data/visitors/nanomax/common/sw/ptypy-0.4-cc/build/lib/')  # to run ptypy0.4
import time
import ptypy
from ptypy.core import Ptycho
from ptypy import utils as u
from distutils.version import LooseVersion
from mpi4py import MPI

if LooseVersion(ptypy.version) >= LooseVersion('0.5.0'):
    ptypy.load_ptyscan_module("nanomax")
    hostname = os.uname()[1]
    if hostname.startswith('g'):
        ptypy.load_gpu_engines(arch="cuda")

############################################################################
# hard coded user input 
############################################################################

detector         = 'eiger1m' # or 'merlin' or 'pilatus'
beamtime_basedir = '/data/staff/nanomax/commissioning_2022-1/20220525_hdf_formats/'
sample           = 'sample'
scannr           = 0
distance_m       = 3.62    # distance between the sample and the detector in meters
defocus_um       = 500     # distance between the focus and the sample plane in micro meters -> used for inital probe
#energy_keV      = 6.5     # incident photon energy in keV ... now read from scan file
cropping         = 256
binning          = 1

if len(sys.argv)>=2:
    # scan number is given as first argument of this script
    scannr = int(sys.argv[1]) 

if len(sys.argv)>=3:
    # sample name (and thus data directory) is given as the 2nd argument 
    cropping = str(sys.argv[2]) 

############################################################################
# some preparations before the actual reconstruction 
############################################################################

# define the output directories
out_dir         = beamtime_basedir + '/process/' + sample + '/scan_' + str(scannr).zfill(6) + '/ptycho_ptypy/'
out_dir_data    = out_dir + 'data/'
out_dir_dumps   = out_dir + 'dumps/'
out_dir_scripts = out_dir + 'scripts/'
out_dir_rec     = out_dir + 'rec/'

# and what the files are supposed to be called
path_data       = out_dir_data  + 'data_scan_' + str(scannr).zfill(6) + '.ptyd'                             # the file with the prepared data
path_dumps      = out_dir_dumps + 'dump_scan_' + str(scannr).zfill(6)+'_%(engine)s_%(iterations)04d.ptyr'   # intermediate results
path_rec        = out_dir_rec   + 'rec_scan_' + str(scannr).zfill(6)+'_%(engine)s_%(iterations)04d.ptyr'    # final reconstructions (of each engine)

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
    os.system('cp ./' + str(__file__) + ' ' + out_dir_scripts + time.strftime("%Y-%m-%d_%H%M") + '_' + str(__file__))

############################################################################
# creating the parameter tree
############################################################################

# General parameters
p = u.Param()
p.verbose_level = 3
p.run = 'scan%d' % scannr

# where to put the reconstructions
p.io = u.Param()
p.io.home = out_dir_rec                     # where to save the final reconstructions
p.io.rfile = path_rec                       # how to name those files for the final reconstructions
p.io.autosave = u.Param()
p.io.autosave.rfile = path_dumps            # where to save the intermediate reconstructions and how to name them

# Scan parameters
p.scans = u.Param()
p.scans.scan00 = u.Param()
p.scans.scan00.name = 'Full'
p.scans.scan00.coherence = u.Param()
p.scans.scan00.coherence.num_probe_modes = 1        # number of probe modes
p.scans.scan00.coherence.num_object_modes = 1       # number of object modes

p.scans.scan00.data = u.Param()
p.scans.scan00.data.name = 'NanomaxContrast'
p.scans.scan00.data.path = beamtime_basedir+'/raw/'+sample+'/'
p.scans.scan00.data.detector = detector
p.scans.scan00.data.maskfile = {'merlin': '/data/visitors/nanomax/common/masks/merlin/latest.h5',
                                'pilatus': None,
                                'eiger': '/data/visitors/nanomax/common/masks/eiger/eiger_4M_blinking_pixels.h5', # legacy
                                'eiger1m': None, # none yet
                                'eiger4m': '/data/visitors/nanomax/common/masks/eiger/eiger_4M_blinking_pixels.h5'}[detector]
p.scans.scan00.data.scanNumber = scannr
p.scans.scan00.data.xMotor = 'pseudo/x'
p.scans.scan00.data.yMotor = 'pseudo/y'
p.scans.scan00.data.zDetectorAngle = 1.5    # rotation of the detector around the beam axis in [deg]
p.scans.scan00.data.xyAxisSkewOffset = 3.0
p.scans.scan00.data.shape = cropping        # size of the window of the diffraction patterns to be used in pixel
p.scans.scan00.data.save = 'append'
p.scans.scan00.data.dfile = path_data       # once all data is collected, save it as .ptyd file
p.scans.scan00.data.center = None #(824,367)      # center of the diffraction pattern (y,x) in pixel or None -> auto
p.scans.scan00.data.cropOnLoad = True       # only load used part of detector frames -> save memory
                                            # requires center to be set explicitly
p.scans.scan00.data.xMotorFlipped = True
p.scans.scan00.data.yMotorFlipped = False
p.scans.scan00.data.orientation = {'merlin':  (False, False, False), 
                                   'pilatus': (False, True, False), 
                                   'eiger':   (False, True, False), # legacy
                                   'eiger1m': (False, True, False),
                                   'eiger4m': (False, True, False)}[detector]
p.scans.scan00.data.distance = distance_m   # distance between sample and detector in [m] 
p.scans.scan00.data.psize = {'pilatus': 172e-6, 
                             'merlin':   55e-6, 
                             'eiger':    75e-6,   # legacy
                             'eiger1m':  75e-6,
                             'eiger4m':  75e-6}[detector]
p.scans.scan00.data.rebin = binning 
#p.scans.scan00.data.energy = energy_keV    # incident photon energy in [keV], now read from file
p.scans.scan00.data.I0 = None              # can be like 'alba2/1'
p.scans.scan00.data.min_frames = 10
p.scans.scan00.data.load_parallel = 'all'

# scan parameters: illumination
p.scans.scan00.illumination = u.Param()

p.scans.scan00.illumination.model = None                              # option 1: probe is initialized from a guess
p.scans.scan00.illumination.aperture = u.Param()
p.scans.scan00.illumination.aperture.form = 'rect'                    # initial probe is a rectangle (KB focus)
p.scans.scan00.illumination.aperture.size = 100e-9                     # of this size in [m] the focus
p.scans.scan00.illumination.propagation = u.Param()
p.scans.scan00.illumination.propagation.parallel = 1.*defocus_um*1e-6 # propagate the inital guess -> gives phase curvature

#p.scans.scan00.illumination.model = 'recon'                           # option 2: probe is initialized from a previous reconstruction
#p.scans.scan00.illumination.recon = u.Param()
#p.scans.scan00.illumination.recon.rfile = ...                         # absolute path to a .ptyr file containing the probe to be used as initial guess
#p.scans.scan00.illumination.aperture = u.Param()
#p.scans.scan00.illumination.aperture.form = 'rect'                    # this aperture is not optional
#p.scans.scan00.illumination.aperture.size = 10e-8                     # either make it very large, or cut down the loaded probe


############################################################################
# 1st use the difference map algorithm
############################################################################

# general
p.engines = u.Param()
p.engines.engine00 = u.Param()
p.engines.engine00.name = 'DM'
p.engines.engine00.numiter = 200                     # number of iterations
p.engines.engine00.numiter_contiguous = 100          # save a dump file every x iterations
p.engines.engine00.probe_support = 3                 # non-zero probe area as fraction of the probe frame
#p.engines.engine00.probe_update_start = 50          # number of iterations before probe update starts

############################################################################
# 2nd use the maximum likelyhood algorithm
############################################################################

# general
p.engines.engine01 = u.Param()
p.engines.engine01.name = 'ML'
p.engines.engine01.numiter = 800                    # number of iterations
p.engines.engine01.numiter_contiguous = 100         # save a dump file every x iterations

# position refinement
#p.engines.engine01.position_refinement = u.Param()
#p.engines.engine01.position_refinement.start = 10                      # Number of iterations until position refinement starts
#p.engines.engine01.position_refinement.stop = None                     # Number of iterations after which positon refinement stops, If None, stops after last iteration
#p.engines.engine01.position_refinement.interval = 10                   # Frequency of position refinement
#p.engines.engine01.position_refinement.nshifts = 4*64                  # Number of random shifts calculated in each position refinement step (has to be multiple of 4)
#p.engines.engine01.position_refinement.amplitude =  0.5*7.75e-9        # Distance from original position per random shift [m]
#p.engines.engine01.position_refinement.max_shift = 1000e-9             # Maximum distance from original position [m]
#p.engines.engine01.position_refinement.metric = 'fourier'
#p.engines.engine01.position_refinement.record = True                   # record movement of positions

############################################################################
# start the reconstruction
############################################################################

if LooseVersion(ptypy.version) < LooseVersion('0.3.0'):
    raise Exception('Use ptypy 0.3.0 or better!')

P = Ptycho(p,level=5)
