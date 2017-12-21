import numpy as np
import matplotlib.pyplot as plt
import h5py
import ptypy
from ptypy import utils as u
import nmutils
import sys

"""
This script visualizes the probe coverage of a reconstruction.
"""

raise Exception('This script is currently broken. Try fixing it!')

### Parse input
if len(sys.argv) < 3:
    print "\nUsage: reconstructionAnalysis.py <ptyd input file> <ptyr recons/dump file> \n"
    exit()
ptydFile = sys.argv[1]
ptyrFile = sys.argv[2]

### load reconstructed probe
with h5py.File(ptyrFile, 'r') as hf:
    probe = np.array(hf.get('content/probe/S00G00/data'))[0]
probe_int = np.abs(probe)**2
probe_int /= probe_int.max()
print "Loaded probe %d x %d"%(probe.shape)

### create a Ptycho instance and sort 
p = u.Param()
p.scans = u.Param()
p.scans.NM = u.Param()
p.scans.NM.data= u.Param()
p.scans.NM.data.source = 'file'
p.scans.NM.data.dfile = ptydFile
P = ptypy.core.Ptycho(p)

S = P.obj.storages.values()[0] 
S.fill(0.0)
for v in S.views:
    S[v] += probe_int

plt.imshow(S.data[0].real)
plt.colorbar()
plt.show()

