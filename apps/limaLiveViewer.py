"""
A live viewer app which grabs data from Lima and plots them in a silx 
widget, either as 2d images or as spectra.
"""

# to do:
#   limits of histograms are not right, set image limits perhaps
#   don't reset zoom when updating
#   some way to avoid reading the same image more than once?

import PyTango
import sys
import numpy as np
from silx.gui.plot import ImageView, PlotWindow
from silx.gui import qt


class LimaLiveViewer2D(ImageView):
    """
    Displays 2d detector images live from Lima.

    alarm is the maximum photon flux per pixel allowed.
    """

    def __init__(self, limaPath, interval=.1, alarm=None):
        # run the base class constructor
        super(LimaLiveViewer2D, self).__init__()

        # initialize the lima proxy
        self.lima = PyTango.DeviceProxy(limaPath)

        # learn about the shape and bit depth of the image
        ignore, bytes, self.w, self.h = self.lima.image_sizes
        self.dtype = {1: np.int8, 2: np.int16, 4:np.int32}[bytes]

        # set some properties
        self.setWindowTitle(limaPath)
        self.setKeepDataAspectRatio(True)
        self.setColormap(normalization='log')
        self.setYAxisInverted(True)
        self.hasImage = False
        self.alarm = alarm

        # a periodic timer triggers the update
        self.timer = qt.QTimer(self)
        self.timer.setInterval(interval * 1000.0)
        self.timer.timeout.connect(self._update)
        self.timer.start()

    def _update(self):
        """
        gets and plots the last image
        """
        last = self.lima.last_image_ready
        if last > -1:
            try:
                image = np.frombuffer(self.lima.getImage(last), dtype=self.dtype)
                image = image.reshape((self.h, self.w))
                self.setImage(image, copy=False, reset=(not self.hasImage))
                self.hasImage = True
                exptime = self.lima.acq_expo_time
                total = np.sum(image)
                hottest = np.max(image)
                if (self.alarm is not None) and (hottest/exptime > self.alarm):
                    self.setStyleSheet('QMainWindow{background-color: red}')
                else:
                    self.setStyleSheet('QMainWindow{background-color: white}')
                self.setGraphTitle('Total: %.1e (%.1e / s) \n Hottest: %.1e (%.1e / s)' % (total, total/exptime, hottest, hottest/exptime))
            except:
                pass # sometimes you miss frames, no big deal


class LimaLiveViewer1D(PlotWindow):
    """
    Displays a stack of 1D spectra live from Lima.
    """

    def __init__(self, limaPath, interval=.1, alarm=None):
        # run the base class constructor
        super(LimaLiveViewer1D, self).__init__()

        # initialize the lima proxy
        self.lima = PyTango.DeviceProxy(limaPath)

        # learn about the shape and bit depth of the image
        ignore, bytes, self.n, self.N = self.lima.image_sizes
        self.dtype = {1: np.int8, 2: np.int16, 4:np.int32}[bytes]

        # determine the x axis, in future perhaps a calibrated scale
        self.E = np.arange(self.n)

        # set some properties
        self.setWindowTitle(limaPath)
        self.hasData = False

        # a periodic timer triggers the update
        self.timer = qt.QTimer(self)
        self.timer.setInterval(interval * 1000.0)
        self.timer.timeout.connect(self._update)
        self.timer.start()

    def _update(self):
        """
        gets and plots the last spectra
        """
        last = self.lima.last_image_ready
        if last > -1:
            try:
                data = np.frombuffer(self.lima.getImage(last), dtype=self.dtype)
                data = data.reshape((self.N, self.n))
                for i in range(self.N):
                    self.addCurve(self.E, data[i, :], legend=str(i), resetzoom=(not self.hasData))
                    self.hasData = True
            except:
                pass # sometimes you miss frames, no big deal


if __name__ == '__main__':
    # you always need a qt app     
    app = qt.QApplication(sys.argv)

    # a dict of known detectors for convenience
    known = {
        'pil100k': 'lima/limaccd/b-nanomax-mobile-ipc-01',
        'pil1m': 'lima/limaccd/b-nanomax-pilatus1m-ipc-01',
        'merlin': 'lima/limaccd/b303a-a100384-dia-detpicu-02',
        'eiger': 'lima/limaccds/eiger',
        'xspress3': 'lima/limaccd/b303a-a100380-dia-detxfcu-01',
    }

    # alarm levels in photons per pixel per second
    alarm_levels = {
        'lima/limaccd/b-nanomax-mobile-ipc-01': 5e6,
        'lima/limaccd/lima/limaccd/b-nanomax-pilatus1m-ipc-01': 5e6,
        'lima/limaccd/test_merlin': 1e5,
        }
    
    # parse arguments
    try:
        limaPath = known[sys.argv[1]] if sys.argv[1] in known.keys() else sys.argv[1] # parse shortcuts
        alarm = alarm_levels[limaPath] if limaPath in alarm_levels.keys() else None
        Viewer = LimaLiveViewer2D   # default
        interval = 0.1              # default
        if len(sys.argv) >= 3 and sys.argv[2].lower() == '1d':
            Viewer = LimaLiveViewer1D
        if len(sys.argv) >= 4:
            interval = float(sys.argv[3])
    except:
        print "\nUsage: python limaLiveViewer.py <lima device> [<det type> <polling interval>]\n"
        print "   <lima device>       full lima path or one of these shortcuts:"
        for key, val in known.iteritems():
            print " "*26 + "%-10s (%s)"%(key, val)
        print "   <detector type>     1d or 2d, defaults to 2d"
        print "   <polling interval>  interval with which to check for new images, defaults to 0.1\n\n"
        exit(0)

    # instantiate the viewer and run
    viewer = Viewer(limaPath, interval=interval, alarm=alarm)
    viewer.show()
    app.exec_()

