import numpy as np
from Scan import Scan
from scipy.misc import face

class dummyScan(Scan):
    """
    Scan class which gives dummy data for testing and demonstration.
    """

    default_opts = {
        # the dataType option is mandatory for use with scanViewer
        'dataType': {
            'value': 'xrd',
            'type': str,
            'doc': "type of data, 'xrd' or 'xrf'",
            },
        'xrange': {
            'value': [0, 1024],
            'type': list,
            'doc': "x range of the dummy scan",
            },
        'yrange': {
            'value': [0, 768],
            'type': list,
            'doc': "y range of the dummy scan",
            },
        'stepsize': {
            'value': 50,
            'type': int,
            'doc': 'Step size of the dummy scan',
            },
        'fourier': {
            'value': False,
            'type': bool,
            'doc': "Whether or not to Fourier transform exposure",
            }
        }

    def addData(self, name=None, filename=None, scannr=None, **kwargs):
        """
        Override that doesn't require filename and scannr.
        """
        super(dummyScan, self).addData(name=name, filename='dummy',
                                       scannr=-1, **kwargs)

    def _prepareData(self, **kwargs):
        """ 
        This method gets the kwargs passed to the addData() method, and
        stores them for use during this data loading.
        """
        # copy defaults, then update with kwarg options
        opts = self.default_opts.copy()
        opts = self._updateOpts(opts, **kwargs)
        
        self.dataType = opts['dataType']['value']
        self.xrange = map(int, opts['xrange']['value'])
        self.yrange = map(int, opts['yrange']['value'])
        self.stepsize = int(opts['stepsize']['value'])
        self.doFourier = opts['fourier']['value']

        self.image = face(gray=True)

    def _readPositions(self):
        """ 
        Override position reading.
        """
        shape = self.image.shape
        x0, x1 = self.xrange
        y0, y1 = self.yrange
        step = self.stepsize
        x = np.arange(x0+step/2, x1-step/2, step)
        y = np.arange(y0+step/2, y1-step/2, step)
        lenx = len(x)
        x = np.repeat(x, len(y))
        y = np.tile(y, lenx)
        return np.vstack((x, y)).T

    def _readData(self):
        """ 
        Override data reading.
        """
        step = self.stepsize
        data = []
        if self.dataType == 'xrd':
            for pos in self.positions:
                frame = self.image[pos[1]-step/2:pos[1]+step/2,
                                   pos[0]-step/2:pos[0]+step/2,]
                if self.doFourier:
                    frame = np.abs(np.fft.fftshift(np.fft.fft2(frame)))**2
                data.append(frame)
        return np.array(data)
