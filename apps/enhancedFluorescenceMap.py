"""
A usage example for probe deconvolution of fluorescence maps. The settings
were adapted for scan 17 of /data/staff/nanomax/com20170517_eh3/testing/testing.h5.
"""

import nmutils
import nmutils.utils.fmre
import matplotlib.pyplot as plt
import numpy as np
import sys

# parse command-line arguments
try:
    hdf5file = sys.argv[1]
    scannr = int(sys.argv[2].strip())
    ptyrfile = sys.argv[3]
except:
    print "Usage: enhancedFluorescenceMap.py [h5 file] [scan number] [ptyr file]"
    exit(1)

# Create an instance of a Scan subclass
myscan = nmutils.core.nanomaxScan_stepscan_april2017()

# Add data to the scan
myscan.addData(
    dataType='xrf', 
    filename=hdf5file,
    scannr=scannr,
)

# Enhance by the Landweber method
EFM_Landweber,residuals_Landweber,info_Landweber = nmutils.utils.fmre.enhance(
    myscan, 
    ptyrfile,
    lam=.5,
    roi='1 1300',
    method='Landweber',
    non_neg=True,
    iterations=50,
    interp_method='nearest',
    show=False,
    )

fig, ax = plt.subplots(ncols=3)
asize = 64
ax[0].imshow(EFM_Landweber[asize:-asize,asize:-asize])
ax[1].imshow(np.fliplr(np.angle(info_Landweber['Pty_obj'][asize:-asize,asize:-asize])), cmap='jet_r')
ax[2].imshow(info_Landweber['interpolated_map'])

plt.show()