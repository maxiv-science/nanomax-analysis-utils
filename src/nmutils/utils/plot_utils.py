""" This file contains isolated helper functions and constants related to plotting. """

from matplotlib.colors import LinearSegmentedColormap
from colorsys import hsv_to_rgb, hls_to_rgb
import numpy as np

def complex2image(z, vmin=None, vmax=None, argmin=-np.pi, argmax=np.pi, offset=0.0, cmap='hsv'):
    """
    Combined theft from ptypy and stack overflow. The cmap kwarg can be 'hsv' or 'hls',
    where the latter goes from white (at vmin, lightness=1.0) to full color
    (at vmax, lightness=0.5). The offset argument rotates the hue over the [0,1]
    interval.
    """

    arg = np.angle(z)
    s = np.ones(z.shape)
    h = (arg.clip(argmin, argmax) - argmin) / (argmax - argmin) # [0, 1]
    h += offset
    
    r = np.abs(z)
    if vmin is None:
        vmin = r.min()
    if vmax is None:
        vmax = r.max()

    if cmap == 'hsv':
        v = (r.clip(vmin, vmax) - vmin) / (vmax - vmin)
        c = np.vectorize(hsv_to_rgb)(h,s,v) # tuple
    elif cmap == 'hls':
        l = (r.clip(vmin, vmax) - vmin) / (vmax - vmin) # [0, 1]
        l = 1 - l * .5 # [1, .5]
        c = np.vectorize(hls_to_rgb)(h,l,s) # tuple
    else:
        raise AttributeError('Invalid cmap, has to be hsv or hls.')
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

