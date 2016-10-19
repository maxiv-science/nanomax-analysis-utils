from scipy.interpolate import griddata
import nmutils
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib as mpl
import h5py
import sys


class Plotter():
    """ 
    Class which creates a figure, visualizes an average detector image
    and adds masked areas as instructed by the GUI.
    """

    def __init__(self, image, outputFile, initialMask):
        self.fig, self.ax = plt.subplots(ncols=1)
        self.image = image
        self.outputFile = outputFile
        self.mask = initialMask
        self.vertices = []
        self.update()

    def update(self):
        # show a masked version of the image
        self.ax.clear()
        self.ax.imshow(np.log10(self.image), interpolation='none', cmap='jet')
        self.ax.imshow((1 - self.mask)*.6, cmap=nmutils.utils.alpha2black, vmin=0, vmax=1, interpolation='none')
        plt.draw()

    def add_point(self, point):
        self.vertices.append(point)
        # plot the current line if appropriate
        if len(self.vertices) > 1:
            xl, yl = plotter.ax.get_xlim(), plotter.ax.get_ylim()
            plotter.ax.plot([self.vertices[-2][0], self.vertices[-1][0]],
                            [self.vertices[-2][1], self.vertices[-1][1]], 'r-')
            plotter.ax.set_xlim(xl)
            plotter.ax.set_ylim(yl)
            plt.draw()

    def finish_block(self, logic):
        # add closing vertex, position is ignored
        self.add_point(self.vertices[0])
        # create a closed Path instance
        N = len(self.vertices)
        codes = [Path.MOVETO] + (N - 2) * [Path.LINETO] + [Path.CLOSEPOLY]
        path = Path(self.vertices, codes)

        # fill the mask array
        # grid of x, y coordinates
        yy, xx = np.indices(self.image.shape)
        # list of pixel points taken in row order
        points = zip(np.reshape(xx, np.prod(xx.shape)),
                     np.reshape(yy, np.prod(yy.shape)))
        # array of bools saying whether each pixel is contained in the
        # path, reshaped row-first into a np.shape(image) array
        inside = path.contains_points(points).reshape(self.image.shape)
        if logic == 'negative':
            self.mask *= (1 - inside)
        elif logic == 'positive':
            self.mask = 1 * inside

        self.update()

        # reset the list of points
        self.vertices = []

        # save to file
        with h5py.File(self.outputFile, 'w') as hf:
            dset = hf.create_dataset("mask", self.mask.shape, dtype='i')
            dset[:] = self.mask


class GuiListener(object):
    """ Class which keeps track of matplotlib events and requests a Plotter instance to update according to user input. It ignores normal zoom/pan interactions. """

    def __init__(self, plotter):
        self.plotter = plotter
        self.fig = plotter.fig
        self.buttonDown = False
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)

    def on_motion(self, event):
        # not used for this simple case
        if self.fig.canvas.manager.toolbar._active:
            return
        if self.buttonDown:
            pass

    def on_press(self, event):
        # store the clicked positions
        if self.fig.canvas.manager.toolbar._active:
            return
        self.buttonDown = True
        if event.button == 1:
            self.plotter.add_point([event.xdata, event.ydata])
        elif event.button == 2:
            self.plotter.finish_block('positive')
        elif event.button == 3:
            self.plotter.finish_block('negative')

    def on_release(self, event):
        # not used for this simple case
        if self.fig.canvas.manager.toolbar._active:
            return
        self.buttonDown = False


# mandatory arguments
if len(sys.argv) < 3:
    print "\nUsage: maskMaker.py <data file> <hdf5 path> \n     [<output file> <initial mask file> <initial mask hdf5 path>] \n"
    try:
        __IPYTHON__
        raise Exception("too few input arguments")
    except NameError:
        sys.exit(0)
fileName, hdfPath = sys.argv[1:3]

# optional arguments
outputFile, initialFile, initialHdfPath = 'out.hdf5', None, 'mask'
if len(sys.argv) >= 4:
    outputFile = sys.argv[3]
if len(sys.argv) >= 5:
    initialFile = sys.argv[4]
if len(sys.argv) >= 6:
    initialHdfPath = sys.argv[5]

# load data and average first dim until it's two dimensional
with h5py.File(fileName, 'r') as hf:
    data = hf.get(hdfPath)
    data = np.array(data)
    while len(data.shape) > 2:
        data = np.mean(data, axis=0)

# optionally load initial mask
if initialFile:
    with h5py.File(initialFile, 'r') as hf:
        initialMask = hf.get(initialHdfPath)
        initialMask = np.array(initialMask)
else:
    initialMask = np.ones(data.shape)

# start the gui
plotter = Plotter(data, outputFile, initialMask)
a = GuiListener(plotter)
plt.show()
