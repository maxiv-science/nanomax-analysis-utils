import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import h5py
import sys

"""
This script visualizes a ptypy input ptyd file.
"""

raise Exception('This script is probably broken. Try fixing it!')

### Parse input
if len(sys.argv) < 2 or len(sys.argv) > 2:
    print "\nUsage: plotPtypyInput.py <ptyd file>\n"
    exit()
inputFile = sys.argv[1]

### load input data
with h5py.File(inputFile, 'r') as hf:
    diff = np.array(hf.get('chunks/0/data'))
    weights = np.array(hf.get('chunks/0/weights'))
    shape = diff.shape
    diff = np.mean(diff, axis=0)
    print "Loaded and averaged %d diffraction patterns, %dx%d"%shape
    if weights.shape == shape:
        print "Found individual masks for each diff pattern, averaging these"
        weights = np.mean(weights, axis=0)
    else:
        weights = np.array(hf.get('meta/weight2d'))
        print "Loaded common mask %dx%d"%weights.shape
    iweights = 1 - weights

### plot
#plt.ion()
fig, ax = plt.subplots(ncols=3)
ax[0].imshow(np.log10(diff), interpolation='none')
plt.setp(ax[0], 'title', 'diff')

ax[1].imshow(weights, interpolation='none', cmap='gray')
plt.setp(ax[1], 'title', 'mask')

ax[2].imshow(np.log10(diff), interpolation='none', vmax = np.log10(diff * weights).max())
plt.setp(ax[2], 'title', 'masked')
masked_array = np.ma.array(iweights, mask=(iweights == 0))
ax[2].imshow(masked_array, interpolation='none', cmap='gray')

plt.show()