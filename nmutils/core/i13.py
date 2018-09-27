from Scan import Scan
from ..utils import fastBinPixels
import numpy as np
import h5py
import copy as cp
import os.path

class i13_stepscan(Scan):

    default_opts = {
        # the dataType option is mandatory for use with scanViewer
        'dataType': {
            'value': 'xrd',
            'type': str,
            'doc': "type of data, 'xrd' or 'xrf'",
            },
        'xMotor': {
            'value': 't1_pi_lx',
            'type': str,
            'doc': 'scanned motor to plot on the x axis',
            },
        'yMotor': {
            'value': 't1_pi_ly',
            'type': str,
            'doc': 'scanned motor to plot on the y axis',
            },
        'xrdCropping': {
            'value': 0,
            'type': int,
            'doc': 'size of detector area to load, 0 means no cropping',
            },
        'xrdBinning': {
            'value': 1,
            'type': int,
            'doc': 'bin xrd pixels n-by-n (after cropping)',
            },
        'xrdNormalize': {
            'value': False,
            'type': bool,
            'doc': 'normalize XRD images by total intensity',
            },
        'detector': {
            'value': 'excalibur',
            'type': ['excalibur', 'merlin'],
            'doc': 'XRD detector to read',
            },
    }

    def _prepareData(self, **kwargs):
        """ 
        This method gets the kwargs passed to the addData() method, and
        stores them for use during this data loading.
        """
        # copy defaults, then update with kwarg options
        opts = cp.deepcopy(self.default_opts)
        opts = self._updateOpts(opts, **kwargs)
        
        # parse options
        self.dataType = opts['dataType']['value']
        self.xMotor = opts['xMotor']['value']
        self.yMotor = opts['yMotor']['value']
        self.xrdCropping = int(opts['xrdCropping']['value'])
        self.xrdBinning = int(opts['xrdBinning']['value'])
        self.xrdNormalize = bool(opts['xrdNormalize']['value'])
        self.detector = opts['detector']['value']

        self.fileName = os.path.join(self.fileName, str(self.scanNr)) + '.nxs'
        print "going to use nexus file:", self.fileName

    def _readPositions(self):
        """ 
        Override position reading.
        """

        with h5py.File(self.fileName, 'r') as hf:
            x = np.array(hf.get('entry1/instrument/%s/%s' % ((self.xMotor,)*2)))
            y = np.array(hf.get('entry1/instrument/%s/%s' % ((self.yMotor,)*2)))

        # allow 1d scans
        try:
            len(y)
        except TypeError:
            y = np.zeros(x.shape)
        try:
            len(x)
        except TypeError:
            x = np.zeros(y.shape)

        return np.vstack((x, y)).T

    def _readData(self):
        """ 
        Override data reading.
        """

        if self.dataType == 'xrd':
            print "loading diffraction data..."
            
            with h5py.File(self.fileName, 'r') as hf:
                data = np.array(hf.get('entry1/instrument/%s/data' % self.detector))

        else:
            raise RuntimeError('unknown datatype specified (should be ''xrd'' or ''xrf''')

        return data
