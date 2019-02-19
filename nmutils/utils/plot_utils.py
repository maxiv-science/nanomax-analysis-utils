""" This file contains isolated helper functions and constants related to plotting. """

from matplotlib.colors import LinearSegmentedColormap
from colorsys import hsv_to_rgb
import numpy as np

def complex2image(z, vmin=None, vmax=None, argmin=-np.pi, argmax=np.pi):
    """
    Combined theft from ptypy and stack overflow
    """

    arg = np.angle(z)
    h = (arg.clip(argmin, argmax) - argmin) / (argmax - argmin) # [0, 1]

    s = np.ones(z.shape)

    v = abs(z)
    if vmin is None:
        vmin = v.min()
    if vmax is None:
        vmax = v.max()
    if vmin==vmax:
        v = np.ones_like(v) * v.mean()
        v = v.clip(0.0, 1.0)
    else:
        assert vmin < vmax
        v = (v.clip(vmin, vmax)-vmin)/(vmax-vmin)

    c = np.vectorize(hsv_to_rgb) (h,s,v) # tuple
    c = np.array(c)      # (3, m, n)
    c = c.swapaxes(0, 2) # (n, m, 3)
    c = c.swapaxes(0, 1) # (m, n, 3)
    return c
    
# constants
alpha2red = LinearSegmentedColormap('alpha2red', 
                                    {
          'red':   ((0.0, 0.0, 0.0),
                   (1.0, 1.0, 1.0)) ,
         'green': ((0.0, 0.0, 0.0),
                   (1.0, 0.0, 0.0)),
         'blue': ((0.0, 0.0, 0.0),
                   (1.0, 0.0, 0.0)),
         'alpha': ((0.0, 0.0, 0.0),
                   (1.0, 1.0, 1.0)) 
                   })
                   
alpha2redTransparent = LinearSegmentedColormap('alpha2red', 
                                    {
          'red':   ((0.0, 0.0, 0.0),
                   (1.0, 1.0, 1.0)) ,
         'green': ((0.0, 0.0, 0.0),
                   (1.0, 0.0, 0.0)),
         'blue': ((0.0, 0.0, 0.0),
                   (1.0, 0.0, 0.0)),
         'alpha': ((0.0, 0.0, 0.0),
                   (1.0, 0.5, 0.5)) 
                   })

alpha2black = LinearSegmentedColormap('alpha2black', 
                                    {
          'red':   ((0.0, 0.0, 0.0),
                   (1.0, 0.0, 1.0)) ,
         'green': ((0.0, 0.0, 0.0),
                   (1.0, 0.0, 0.0)),
         'blue': ((0.0, 0.0, 0.0),
                   (1.0, 0.0, 0.0)),
         'alpha': ((0.0, 0.0, 0.0),
                   (1.0, 1.0, 1.0))
                   })
