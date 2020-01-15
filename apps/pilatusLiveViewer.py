"""
A live viewer app which grabs data from the pilatus zmq interface
and plots them in a silx widget.
"""

import sys
import numpy as np
from silx.gui.plot import ImageView, PlotWindow, tools
from silx.gui import qt
import zmq
from zmq.utils import jsonapi as json


class PilatusLiveViewer(ImageView):
    """
    Displays 2d detector images live from the Pilatus zmq streamer.

    alarm is the maximum photon flux per pixel allowed.
    """

    def __init__(self, hostname, port=9998, interval=.1, alarm=None):
        # run the base class constructor
        super(PilatusLiveViewer, self).__init__()

        # initialize the zmq
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect('tcp://%s:%u' % (hostname, port))

        # set some properties
        self.setWindowTitle(hostname)
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

        # Display mouseover position info
        posInfo = [
            ('X', lambda x, y: int(x)),
            ('Y', lambda x, y: int(y)),
            ('Data', self._getActiveImageValue)]
        self._positionWidget = tools.PositionInfo(plot=self, converters=posInfo)
        self.statusBar().addWidget(self._positionWidget)

    def _update(self):
        """
        gets and plots the last image
        """
        try:
            self.socket.send_string('give me!')
            parts = self.socket.recv_multipart()
            header = json.loads(parts[0])
            image = np.frombuffer(parts[1], dtype=header['type']).reshape(header['shape'])
            self.setImage(image, copy=False, reset=(not self.hasImage))
            self.hasImage = True
            total = np.sum(image)
            hottest = np.max(image)
            exptime = np.nan
            if (self.alarm is not None) and (hottest/exptime > self.alarm):
                self.setBackgroundColor(qt.QColor(255, 0, 0))
            else:
                self.setBackgroundColor(qt.QColor(255, 255, 255))
            self.setGraphTitle('Total: %.1e (%.1e / s) \n Hottest: %.1e (%.1e / s)' % (total, total/exptime, hottest, hottest/exptime))
            self._positionWidget.updateInfo()
        except Exception as e:
            print(e)

    def _getActiveImageValue(self, x, y):
        """
        Get value of active image at position (x, y)
        """
        image = self.getActiveImage()
        if image is not None:
            data, params = image[0], image[4]
            ox, oy = params['origin']
            sx, sy = params['scale']
            if (y - oy) >= 0 and (x - ox) >= 0:
                # Test positive before cast otherwisr issue with int(-0.5) = 0
                row = int((y - oy) / sy)
                col = int((x - ox) / sx)
                if (row < data.shape[0] and col < data.shape[1]):
                    return data[row, col]
        return '-'

if __name__ == '__main__':
    # you always need a qt app     
    app = qt.QApplication(sys.argv)
    app.setStyle('Fusion')

    # parse arguments
    hostname = sys.argv[1]

    # instantiate the viewer and run
    viewer = PilatusLiveViewer(hostname, interval=1., alarm=1e6)
    viewer.show()
    app.exec_()

