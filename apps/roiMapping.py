from scipy.interpolate import griddata
import nmutils
import numpy as np
import matplotlib.pyplot as plt
#plt.ion()
import sys

class Plotter():
    """ Class which creates a figure, visualizes a scan as a map and a diffraction pattern, and provides methods for updating the two plots. """
    def __init__(self, scan):
        self.fig, self.ax = plt.subplots(ncols=2)
        self.scan = scan
        self.reset()

    def reset(self):
        # diffraction pattern
        imshape = self.scan.meanData().shape
        self.ax[0].imshow(np.log10(self.scan.meanData()), interpolation='none')
        self.ax[0].set_xlim(0, imshape[1])
        self.ax[0].set_ylim(imshape[0], 0)
        # map
        x, y, z = interpolate([0, imshape[0], 0, imshape[1]], self.scan, 5)
        self.ax[1].clear()
        self.ax[1].imshow(z, 
            extent = [x.max(), x.min(), y.min(), y.max()],
            interpolation='none')
        self.ax[1].plot(scan.positions[:,0], scan.positions[:,1], 'k.', ms=2)
        self.ax[1].set_xlim((x.max(), x.min()))
        self.ax[1].set_ylim((y.min(), y.max()))
        self.format_axes()
        plt.draw()

    def format_axes(self):
        aspect = np.abs(np.diff(self.ax[0].get_ylim())) / np.abs(np.diff(self.ax[0].get_xlim()))
        self.ax[0].set_title('Diffraction', y=1.2 + (1-aspect)/2)
        self.ax[1].set_title('Scan map', y=1.1)
        plt.setp(self.ax[1], xlabel='laboratory x (um)', ylabel='laboratory y (um)')
        self.ax[1].yaxis.tick_right()
        self.ax[1].yaxis.set_label_position('right')
        self.ax[0].xaxis.tick_top()
        self.ax[0].xaxis.set_label_position('top') 
        plt.setp(self.ax[0].xaxis.get_majorticklabels(), rotation=70)
        plt.setp(self.ax[1].xaxis.get_majorticklabels(), rotation=70)
        
    def updateImage(self, rect):
        xmin, xmax = min(rect[0], rect[2]), max(rect[0], rect[2])
        ymin, ymax = min(rect[1], rect[3]), max(rect[1], rect[3])
        rect = np.array([[xmin, ymin], [xmax, ymax]])
        subScan = self.scan.subset(rect, closest=True)
        xlim, ylim = self.ax[0].get_xlim(), self.ax[0].get_ylim()
        self.ax[0].clear()
        self.ax[0].imshow(np.log10(subScan.meanData()), interpolation='none')
        self.ax[0].set_xlim(xlim)
        self.ax[0].set_ylim(ylim)
        self.format_axes()
        plt.draw()
        
    def updateMap(self, rect):
        xmin, xmax = min(rect[0], rect[2]), max(rect[0], rect[2])
        ymin, ymax = min(rect[1], rect[3]), max(rect[1], rect[3])
        #import ipdb; ipdb.set_trace()
        # convert the event's xy coordinates into image row-column:
        rect = np.array([ymin, ymax, xmin, xmax], dtype=int) 
        x, y, z = interpolate(rect, scan, 5)
        xlim, ylim = self.ax[1].get_xlim(), self.ax[1].get_ylim()
        self.ax[1].clear()
        self.ax[1].imshow(z, 
            extent = [x.max(), x.min(), y.min(), y.max()],
            interpolation='none')
        self.ax[1].plot(scan.positions[:,0], scan.positions[:,1], 'k.', ms=2)
        self.ax[1].set_xlim(xlim)
        self.ax[1].set_ylim(ylim)
        self.format_axes()
        plt.draw()

class GuiListener(object):
    """ Class which keeps track of matplotlib events and requests a Plotter instance to update according to user input. It ignores normal zoom/pan interactions. """
    def __init__(self, plotter):
        self.plotter = plotter
        self.fig = plotter.fig
        self.x0 = None
        self.y0 = None
        self.x1 = None
        self.y1 = None
        self.buttonDown = False
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        
    def on_motion(self, event):
        if self.fig.canvas.manager.toolbar._active:
            return
        if self.buttonDown:
            pass

    def on_press(self, event):
        if self.fig.canvas.manager.toolbar._active:
            return
        self.buttonDown = True
        self.x0 = event.xdata
        self.y0 = event.ydata

    def on_release(self, event):
        if self.fig.canvas.manager.toolbar._active:
            return
        self.buttonDown = False
        self.x1 = event.xdata
        self.y1 = event.ydata
        rect = (self.x0, self.y0, self.x1, self.y1)
        if event.button == 3:
            self.plotter.reset()
            return
        if event.inaxes == self.plotter.ax[0]:
            self.plotter.updateMap(rect)
        elif event.inaxes == self.plotter.ax[1]:
            self.plotter.updateImage(rect)

def interpolate(roi, scan, oversampling):
    """ 
    Helper function which provides a regular and interpolated xy map of
    a scan, integrated over a roi. The map is in the coordinates defined
    in the Scan class, that is, right-handed lab coordinates in the 
    sample frame, with x horizontal and y vertical, and the origin in 
    the bottom right of the sample map array.
    """
    if roi[0] == roi[1]: roi[1] += 1
    if roi[2] == roi[3]: roi[3] += 1
    integral = np.mean(scan.data['data0'][:, roi[0]:roi[1], roi[2]:roi[3]], axis=(1,2))

    xMin, xMax = np.min(scan.positions[:,0]), np.max(scan.positions[:,0])
    yMin, yMax = np.min(scan.positions[:,1]), np.max(scan.positions[:,1])

    # here we need special cases for 1d scans (where x or y doesn't vary)
    if np.abs(yMax - yMin) < 1e-12:
        stepsize = (xMax - xMin) / float(scan.nPositions) / oversampling
        margin = oversampling * stepsize / 2
        y, x = np.mgrid[yMin-(stepsize*oversampling*5)/2:yMin+(stepsize*oversampling*5)/2:stepsize, xMax+margin:xMin-margin:-stepsize]
    elif np.abs(xMax - xMin) < 1e-12:
        stepsize = (yMax - yMin) / float(scan.nPositions) / oversampling
        margin = oversampling * stepsize / 2
        y, x = np.mgrid[yMax+margin:yMin-margin:-stepsize, xMin-(stepsize*oversampling*5)/2:xMin+(stepsize*oversampling*5)/2:stepsize]
    else:
        stepsize = np.sqrt((xMax-xMin) * (yMax-yMin) / float(scan.nPositions)) / oversampling
        margin = oversampling * stepsize / 2
        y, x = np.mgrid[yMax+margin:yMin-margin:-stepsize, xMax+margin:xMin-margin:-stepsize]
    z = griddata(scan.positions, integral, (x, y), method='nearest')
    return x, y, z

# parse arguments
if len(sys.argv) < 3:
    print "\nUsage: roiMapping.py <Scan subclass> <data file> <subclass options> \n"
    print "Found these subclasses:"
    for subclass in nmutils.core.Scan.__subclasses__():
        print "       %s"%(subclass.__name__)
    print "\n"
    try:
        __IPYTHON__
        raise Exception("too few input arguments")
    except NameError:
        sys.exit(0)
subclass = sys.argv[1]
fileName = sys.argv[2]
opts = sys.argv[3:]

# create a Scan object and load data
scan = None
exec "scan = nmutils.core.%s()"%subclass
scan.addData(fileName, opts=opts)

# start the gui
plotter = Plotter(scan)
a = GuiListener(plotter)
plt.show()
