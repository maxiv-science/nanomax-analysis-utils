import numpy as np
from Scan import Scan
from scipy.misc import face
import copy

class dummyScan(Scan):
    """
    Scan class which gives dummy data for testing and demonstration.
    """

    default_opts = {
        # the dataSource option is mandatory for use with scanViewer
        'dataSource': {
            'value': 'xrd',
            'type': ['fake-xrd', 'fake-xrf', 'fake-scalar'],
            'doc': "type of data",
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
        'framesize': {
            'value': 50,
            'type': int,
            'doc': 'Frame covered in every position',
            },
        'fourier': {
            'value': False,
            'type': bool,
            'doc': "Whether or not to Fourier transform exposure",
            },
        }

    # an optional class attribute which lets scanViewer know what
    # dataSource options have what dimensionalities.
    sourceDims = {'fake-xrd': 2,
                  'fake-xrf': 1,
                  'fake-scalar': 0}


    def _prepareData(self, **kwargs):
        """ 
        This method gets the kwargs passed to the addData() method, and
        stores them for use during this data loading.
        """
        # copy defaults, then update with kwarg options
        opts = copy.deepcopy(self.default_opts)
        opts = self._updateOpts(opts, **kwargs)
        
        self.dataSource = opts['dataSource']['value']
        self.xrange = map(int, opts['xrange']['value'])
        self.yrange = map(int, opts['yrange']['value'])
        self.stepsize = int(opts['stepsize']['value'])
        self.framesize = int(opts['framesize']['value'])
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
        frame = self.framesize
        x = np.arange(x0+frame/2, x1-frame/2, step)
        y = np.arange(y0+frame/2, y1-frame/2, step)
        lenx = len(x)
        x = np.repeat(x, len(y))
        y = np.tile(y, lenx)
        self.positionDimLabels = ['fake x motor (um)', 'fake y motor (um)']
        return np.vstack((x, y)).T

    def _readData(self, name):
        """ 
        Override data reading.
        """
        frame = self.framesize
        data = []
        if self.dataSource == 'fake-xrd':
            for pos in self.positions:
                dataframe = self.image[pos[1]-frame/2:pos[1]+frame/2,
                                   pos[0]-frame/2:pos[0]+frame/2,]
                if self.doFourier:
                    dataframe = np.abs(np.fft.fftshift(np.fft.fft2(dataframe)))**2
                data.append(dataframe)
                self.dataTitles[name] = 'Very fake XRD data'
        elif self.dataSource == 'fake-xrf':
            for pos in self.positions:
                dataframe = self.image[pos[1]-frame/2:pos[1]+frame/2,
                                   pos[0]-frame/2:pos[0]+frame/2,]
                if self.doFourier:
                    dataframe = np.abs(np.fft.fftshift(np.fft.fft2(dataframe)))**2
                data.append(np.mean(dataframe, axis=0))
                self.dataTitles[name] = 'Very fake XRF data'
                self.dataAxes[name] = [np.arange(data[-1].shape[-1]) * .01,]
                self.dataDimLabels[name] = ['Fake energy (some unit)']
        elif self.dataSource == 'fake-scalar':
            self.dataSource = 'fake-xrd'
            data = self._readData(name)
            data = np.var(data, axis=(1,2))
        return np.array(data)
