"""
A live viewer app which grabs 2D images from Lima and plots these in a silx widget.
"""

# to do:
#   aspect ratio and log scale from start
#   another class for spectra with a switch in main
#   lima path as window title
#   some way to avoid reading the same image more than once?

import PyTango
import time
import sys
import numpy as np
from silx.gui.plot import ImageView
from silx.gui import qt


class LimaLiveViewer(ImageView):

    def __init__(self, limaPath, interval=.1):
        # initialize the lima proxy
        self.lima = PyTango.DeviceProxy(limaPath)

        # learn about the shape and bit depth of the image
        ignore, bytes, self.w, self.h = self.lima.image_sizes
        self.dtype = {1: np.int8, 2: np.int16, 4:np.int32}[bytes]

        # run the base class constructor
        super(LimaLiveViewer, self).__init__()

        # a periodic timer triggers the update
        self.timer = qt.QTimer(self)
        self.timer.setInterval(float(interval) * 1000.0)
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
                self.setImage(image, reset=False)
            except:
                pass # sometimes you miss frames, no big deal


if __name__ == '__main__':     # you always need a qt app     
    app = qt.QApplication(sys.argv)
    if len(sys.argv) == 1:
        print "\nUsage: python limaLiveViewer.py <lima device> [<polling interval>=0.1]\n\n"
        exit(0)
    viewer = LimaLiveViewer(*sys.argv[1:])
    viewer.show()
    app.exec_()

