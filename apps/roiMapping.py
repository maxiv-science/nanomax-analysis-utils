from scipy.interpolate import griddata
import scipy.ndimage.measurements
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
        self.com_map()

    def com_map(self):
        com = []
        for im in self.scan.data['data0']:
            com.append(scipy.ndimage.measurements.center_of_mass(im))
        com = np.array(com)
        x, y, z = scan.interpolatedMap(np.sum((com-np.mean(com, axis=0))**2, axis=1), 5, origin='ul')
        plt.figure()
        plt.imshow(z, extent = [x.max(), x.min(), y.min(), y.max()],
            interpolation='none', cmap='gray')
        plt.xlim((x.max(), x.min()))
        plt.ylim((y.min(), y.max()))
        plt.title('Diffraction center of mass deviation')
        ax = plt.gca()
        plt.setp(ax, xlabel='laboratory x (um)', ylabel='laboratory y (um)')
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position('right')
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=70)

    def reset(self):
        # diffraction pattern
        imshape = self.scan.meanData().shape
        self.ax[0].imshow(np.log10(self.scan.meanData()), interpolation='none')
        self.ax[0].set_xlim(0, imshape[1])
        self.ax[0].set_ylim(imshape[0], 0)
        # map
        integral = np.mean(self.scan.data['data0'], axis=(1,2))
        x, y, z = self.scan.interpolatedMap(integral, 5, origin='ul')
        # show it
        self.ax[1].clear()
        self.ax[1].imshow(z, 
            extent = [x.min(), x.max(), y.max(), y.min()],
            interpolation='none', cmap='gray')
        self.ax[1].plot(scan.positions[:,0], scan.positions[:,1], 'k.', ms=2)
        self.ax[1].set_xlim((x.min(), x.max()))
        self.ax[1].set_ylim((y.max(), y.min()))
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
        roi = np.array([ymin, ymax, xmin, xmax], dtype=int) 
        if roi[0] == roi[1]: roi[1] += 1
        if roi[2] == roi[3]: roi[3] += 1
        # calculate the integrated roi and get an interpolated map
        integral = np.mean(scan.data['data0'][:, roi[0]:roi[1], roi[2]:roi[3]], axis=(1,2))
        x, y, z = self.scan.interpolatedMap(integral, 5, origin='ul')
        # show it
        xlim, ylim = self.ax[1].get_xlim(), self.ax[1].get_ylim()
        self.ax[1].clear()
        self.ax[1].imshow(z, 
            extent = [x.min(), x.max(), y.max(), y.min()],
            interpolation='none', cmap='gray')
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
opts = ['xrd',] + sys.argv[3:]

# create a Scan object and load data
scan = None
exec "scan = nmutils.core.%s()"%subclass
scan.addData(fileName, opts=opts)

# start the gui
plotter = Plotter(scan)
a = GuiListener(plotter)
plt.show()
