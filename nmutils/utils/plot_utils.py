""" This file contains isolated helper functions and constants related to plotting. """

from matplotlib.colors import LinearSegmentedColormap

def complex2image(z):
    """ Wraps a ptypy util """
    import ptypy
    rgb = ptypy.utils.complex2rgb(z)
    return rgb / rgb.max()

    
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
