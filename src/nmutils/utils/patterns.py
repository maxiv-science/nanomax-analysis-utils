"""
Test patterns and other geometrical utilities.
"""

import numpy as np

def siemens_star(psize, extent):
    """
    Generate a model of the XRESO-50HC Siemens star.
    """
    psize = psize * 1e6
    shape = int(extent * 1e6 / psize)
    ii, jj = np.indices((shape, shape))
    yy = -(ii - shape//2) * psize
    xx = (jj - shape//2) * psize
    r = np.sqrt(xx**2 + yy**2)

    # start with ones
    a = np.ones((shape, shape), dtype=bool)

    # zero the rings
    for start, width in ([1.5, 0.1], [2.1, 0.2], [5.25, 0.5], [10.5, 1], [20.9, 2]):
        a[np.where((r > start) & (r < start + width))] = 0
    a[np.where(r < .57)] = 0
    a[np.where(r > 46)] = 0

    # zero the 36 segments, toggle every 5 degrees
    N = 36 # full period
    dangle = 360 / N / 2 # angle over which the fields are toggled
    angles = np.arctan(yy / (xx + 1e-20)) / np.pi * 180
    cut = (((angles+dangle/2) // dangle) % 2).astype(bool)
    a[np.where(cut)] = 0

    return a.astype(float)
