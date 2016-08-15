from scipy.interpolate import griddata
import nmutils
import numpy as np
import matplotlib.pyplot as plt
import sys
#import matplotlib as mpl
#mpl.rcParams['backend'] = 'Qt4Agg'

def fn(x):
    return np.log10(x)

class Plotter():
    """ Class which creates a figure, visualizes a scan as a map and a diffraction pattern, and provides methods for updating the two plots. """
    def __init__(self, scan):
        self.fig, self.ax = plt.subplots(ncols=2)
        self.scan = scan
        self.reset()
        plt.setp(self.ax[0].xaxis.get_majorticklabels(), rotation=70)
        plt.setp(self.ax[1].xaxis.get_majorticklabels(), rotation=70)
        
    def reset(self):
        # diffraction pattern
        imshape = scan.meanData().shape
        self.ax[0].imshow(fn(scan.meanData()), interpolation='none')
        self.ax[0].set_xlim(0, imshape[1])
        self.ax[0].set_ylim(0, imshape[0])
        # map
        x, y, z = interpolate([0, imshape[0], 0, imshape[1]], scan, 5)
        self.ax[1].imshow(fn(z), extent=[x.min(), x.max(), y.min(), y.max()], interpolation='none')
        self.ax[1].set_xlim([x.min(), x.max()])
        self.ax[1].set_ylim([y.min(), y.max()])
        
    def updateImage(self, rect):
        xmin, xmax = min(rect[0], rect[2]), max(rect[0], rect[2])
        ymin, ymax = min(rect[1], rect[3]), max(rect[1], rect[3])
        rect = np.array([[xmin, ymin], [xmax, ymax]])
        subScan = self.scan.subset(rect, closest=True)
        xlim, ylim = self.ax[0].get_xlim(), self.ax[0].get_ylim()
        self.ax[0].clear()
        self.ax[0].imshow(fn(subScan.meanData()))
        plt.draw()
        self.ax[0].set_xlim(xlim)
        self.ax[0].set_ylim(ylim)
        
    def updateMap(self, rect):
        xmin, xmax = min(rect[0], rect[2]), max(rect[0], rect[2])
        ymin, ymax = min(rect[1], rect[3]), max(rect[1], rect[3])
        rect = np.array([ymin, ymax, xmin, xmax], dtype=int) # here we convert from the event's xy coordinates to the detector image's row-column order.
        x, y, z = interpolate(rect, scan, 5)
        xlim, ylim = self.ax[1].get_xlim(), self.ax[1].get_ylim()
        self.ax[1].clear()
        self.ax[1].imshow(fn(z), extent=[x.min(), x.max(), y.min(), y.max()], interpolation='none')
        plt.draw()
        self.ax[1].set_xlim(xlim)
        self.ax[1].set_ylim(ylim)

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
    """ Helper function which provides a regular and interpolated xy map of a scan, integrated over a roi. """
    if roi[0] == roi[1]: roi[1] += 1
    if roi[2] == roi[3]: roi[3] += 1
    integral = np.mean(scan.data['data0'][:, roi[0]:roi[1], roi[2]:roi[3]], axis=(1,2))

    oversampling = 3.0
    xMin, xMax = np.min(scan.positions[:,0]), np.max(scan.positions[:,0])
    yMin, yMax = np.min(scan.positions[:,1]), np.max(scan.positions[:,1])
    stepsize = np.sqrt((xMax-xMin) * (yMax-yMin) / float(scan.nPositions)) / oversampling
    
    x, y = np.mgrid[xMin:xMax:stepsize, yMin:yMax:stepsize]
    z = griddata(scan.positions, integral, (x, y), method='nearest')
    return x, y, z.T # z is indexed (x, y) but we want it indexed (y, x) like an image

# parse arguments
if len(sys.argv) < 3:
    print "\nUsage: roiMapping.py <Scan subclass> <data file> \n"
    print "Found these subclasses:"
    for subclass in nmutils.core.Scan.__subclasses__():
        print "       %s"%(subclass.__name__)
    print "\n"
    exit()
subclass = sys.argv[1]
fileName = sys.argv[2]

# create a Scan object and load data
scan = None
exec "scan = nmutils.core.%s()"%subclass
scan.addData(fileName)

# start the gui
plotter = Plotter(scan)
a = GuiListener(plotter)
plt.show()
