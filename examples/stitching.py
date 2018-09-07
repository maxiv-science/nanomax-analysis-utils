"""
This is an example script illustrating how scans can be merged together.
"""

from nmutils.core import dummyScan
import numpy as np
import matplotlib.pyplot as plt

# the first scan is a rough scan
scan1 = dummyScan()
scan1.addData(stepsize=25, framesize=10)

# the second scan is a finer one
scan2 = dummyScan()
scan2.addData(stepsize=5, framesize=10, xrange=[500,800], yrange=[200,500])

# we can merge scan2 into scan1
scan1.merge(scan2)

# and then plot the average signal
average = np.mean(scan1.data['data0'], axis=(1,2))
x, y, z = scan1.interpolatedMap(average, oversampling=5)
plt.imshow(z, cmap='gray', extent=(x[0,0], x[0,-1], y[-1,0], y[0, 0]))
plt.ylim(y.max(), y.min())
plt.show()
