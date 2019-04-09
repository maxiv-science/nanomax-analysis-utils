from Scan import Scan
from ..utils import fastBinPixels
from .. import NoDataException
import numpy as np
import h5py
import copy as cp
import os.path

class i13_stepscan(Scan):

    default_opts = {
        'path': {
            'value': None,
            'type': str,
            'doc': "path to the data folder",
            },
        'scanNr': {
            'value': 0,
            'type': int,
            'doc': "scan number",
            },
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
            'value': [],
            'type': list,
            'doc': 'detector area to load, [i0, i1, j0, j1]',
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
        self.xrdCropping = map(int, opts['xrdCropping']['value'])
        self.detector = opts['detector']['value']
        path = opts['path']['value']
        scannr = opts['path']['value']

        self.fileName = os.path.join(path, scannr) + '.nxs'
        print "going to use nexus file:", self.fileName

    def _readPositions(self):
        """ 
        Override position reading.
        """

        if not os.path.exists(self.fileName): raise NoDataException
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
            if not os.path.exists(self.fileName): raise NoDataException
            with h5py.File(self.fileName, 'r') as fp:
                d = fp.get('entry1/instrument/%s/data' % self.detector)
                if self.xrdCropping:
                    roi = self.xrdCropping
                    data = np.array(d[:, roi[0]:roi[1], roi[2]:roi[3]])
                else:
                    data = np.array(d)
        else:
            raise RuntimeError('unknown datatype specified (should be ''xrd'' or ''xrf''')

        return data

