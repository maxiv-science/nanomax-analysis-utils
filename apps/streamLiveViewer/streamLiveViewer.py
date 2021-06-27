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
import requests
import time
from skimage.io import imread
import io

class LiveViewer2dBase(ImageView):
    """
    Displays 2d detector images live from the Pilatus zmq streamer.

    alarm is the maximum photon flux per pixel allowed.
    """

    def __init__(self, hostname, port=9998, interval=.1, alarm=None):
        # run the base class constructor
        super().__init__()

        # initialize the connection
        self.hostname = hostname
        self.port = port
        self.initialize()

        # set some properties
        self.setWindowTitle(hostname)
        self.setKeepDataAspectRatio(True)
        self.setColormap(normalization='log')
        self.setYAxisInverted(True)
        self.hasImage = False
        self.alarm = alarm
        self.waiting_for_frame = False
        self.latest_request = time.time()

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

    def initialize(self):
        raise NotImplementedError

    def _get_image(self):
        """
        gets the last image
        """
        raise NotImplementedError

    def _update(self):
        image, exptime = self._get_image()
        if image is None:
            return
        self.setImage(image, copy=False, reset=(not self.hasImage))
        self.hasImage = True
        total = np.sum(image)
        hottest = np.max(image)
        if (self.alarm is not None) and (hottest/exptime > self.alarm):
            self.setBackgroundColor(qt.QColor(255, 0, 0))
        else:
            self.setBackgroundColor(qt.QColor(255, 255, 255))
        self.setGraphTitle('Total: %.1e (%.1e / s) \n Hottest: %.1e (%.1e / s)' % (total, total/exptime, hottest, hottest/exptime))
        self._positionWidget.updateInfo()

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


class LiveViewer1dBase(PlotWindow):
    """
    Displays stacks of 1d spectra live from zmq streamers.

    alarm is the maximum photon flux per curve allowed.
    """

    def __init__(self, hostname, port=9998, interval=.1, alarm=None):
        # run the base class constructor
        super().__init__()

        # initialize the connection
        self.hostname = hostname
        self.port = port
        self.initialize()

        # set some properties
        self.setWindowTitle(hostname)
        self.hasData = False
        self.alarm = alarm
#        self.waiting_for_frame = False
#        self.latest_request = time.time()

        # a periodic timer triggers the update
        self.timer = qt.QTimer(self)
        self.timer.setInterval(interval * 1000.0)
        self.timer.timeout.connect(self._update)
        self.timer.start()

        # a periodic timer triggers the update
        self.timer = qt.QTimer(self)
        self.timer.setInterval(interval * 1000.0)
        self.timer.timeout.connect(self._update)
        self.timer.start()

    def initialize(self):
        raise NotImplementedError

    def _get_data(self):
        """
        gets the last image
        """
        raise NotImplementedError

    def _update(self):
        data, exptime = self._get_data()
        E = np.arange(data.shape[1]) * 10 # ad hoc
        for i in range(data.shape[0]):
            self.addCurve(E, data[i, :], legend=str(i), resetzoom=(not self.hasData))
            self.hasData = True
        sums = np.sum(data, axis=1)
        self.setGraphTitle('max(Channels 0,1,2): %.1e (%.1e / s)\nChannel 3: %.1e (%.1e / s)' % (np.max(sums[0:3]), np.max(sums[0:3])/exptime, sums[3], sums[3]/exptime))
        if (self.alarm is not None) and (sums.max()/exptime > self.alarm):
            self.setBackgroundColor(qt.QColor(255, 0, 0))
        else:
            self.setBackgroundColor(qt.QColor(255, 255, 255))


class PilatusLiveViewer(LiveViewer2dBase):
    def initialize(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        res = self.socket.connect('tcp://%s:%u' % (self.hostname, self.port))

    def _get_image(self):
        """
        gets the last image
        """
        self.socket.send(b'give me a frame\0')
        parts = self.socket.recv_multipart(copy=False)
        header = json.loads(parts[0].bytes)
        shape = header['shape']
        length = shape[0] * shape[1]
        import _cbf
        output_buffer = _cbf.ffi.new('int32_t[]', length)
        exptime = _cbf.ffi.new('double*')
        _cbf.lib.read_cbf(_cbf.ffi.from_buffer(parts[1]), output_buffer, exptime)
        image = np.frombuffer(_cbf.ffi.buffer(output_buffer, length*4), dtype=np.int32).reshape(shape)
        return image, exptime[0]


class EigerLiveViewer(LiveViewer2dBase):
    def initialize(self):
        self.session = requests.Session()
        self.session.trust_env = False

    def _get_image(self):
        try:
            response = self.session.get('http://%s/monitor/api/1.8.0/images/monitor' % self.hostname, timeout=1)
        except requests.exceptions.Timeout:
            print('request timed out, returning dummy data')
            return np.zeros((100,100)), 1.0
        image = imread(io.BytesIO(response.content))
        exptime = self.session.get('http://%s/detector/api/1.8.0/config/count_time' % self.hostname).json()['value']
        return image, exptime


class AndorLiveViewer(PilatusLiveViewer):
    def _get_image(self):
        """
        gets the last image
        """
        self.socket.send(b'give me a frame (please)\0')
        parts = self.socket.recv_multipart()
        header = json.loads(parts[0])
        image = np.frombuffer(parts[1], dtype=header['type']).reshape(header['shape'])
        exptime = 1.
        return image, exptime


class Xspress3LiveViewer(LiveViewer1dBase):
    def initialize(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        res = self.socket.connect('tcp://%s:%u' % (self.hostname, self.port))

    def _get_data(self):
        """
        gets the last image
        """
        self.socket.send_string('give us a frame please!')
        print('asked for a frame...')
        parts = self.socket.recv_multipart() # blocks
        print('...got this:')
        meta = json.loads(parts[0])
        frameno = meta['frame']
        m, n = meta['shape'][:2]
        print(meta, '\n')
        frame = np.frombuffer(parts[1], dtype=meta['type']).reshape((m, n))
        exptime = meta['exptime']
        return frame, exptime

if __name__ == '__main__':
    # you always need a qt app     
    app = qt.QApplication(sys.argv)
    app.setStyle('Fusion')

    # parse arguments
    dettype = sys.argv[1].lower()
    hostname = sys.argv[2]

    # instantiate the viewer and run
    if dettype == 'eiger':
        print('Making an EigerLiveViewer instance')
        viewer = EigerLiveViewer(hostname, interval=.1)
    elif dettype == 'pilatus':
        print('Making a PilatusLiveViewer instance')
        viewer = PilatusLiveViewer(hostname, interval=.1, alarm=1e6)
    elif dettype in ('andor', 'krytur', 'zyla'):
        viewer = AndorLiveViewer(hostname, interval=.1)
    elif 'xspress' in dettype.lower():
        viewer = Xspress3LiveViewer(hostname, interval=.1, alarm=2e6)
    viewer.show()
    app.exec_()
