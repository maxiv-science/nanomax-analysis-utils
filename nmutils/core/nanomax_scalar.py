from Scan import Scan
from .. import NoDataException
import numpy as np
import h5py
import copy as cp
from .nanomax_nov2018 import flyscan_nov2018
import os.path

class nanomax_scalar(Scan):
    # Simple loading of x y z data from sardana's h5 file.
    default_opts = {
        'scanNr': {
            'value': 0,
            'type': int,
            'doc': "scan number",
            },
        'fileName': {
            'value': None,
            'type': str,
            'doc': "path to the main data file",
            },
        # the dataType option is mandatory for use with scanViewer
        'dataType': {
            'value': 'xrd',
            'type': str,
            'doc': "type of data, 'xrd' or 'xrf'",
            },
        'xMotor': {
            'value': 'slit01_posx',
            'type': str,
            'doc': 'scanned motor to plot on the x axis',
            },
        'yMotor': {
            'value': 'slit01_posy',
            'type': str,
            'doc': 'scanned motor to plot on the y axis',
            },
        'scalarData': {
            'value': 'counter3',
            'type': str,
            'doc': 'scalar data to inspect',
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
        self.scalarData = opts['scalarData']['value']
        self.scanNr = int(opts['scanNr']['value'])
        self.fileName = opts['fileName']['value']

    def _readPositions(self):
        """ 
        Override position reading.
        """

        if not os.path.exists(self.fileName): raise NoDataException
        with h5py.File(self.fileName, 'r') as hf:
            x = np.array(hf.get('entry%d' % self.scanNr + '/measurement/%s' % self.xMotor))
            y = np.array(hf.get('entry%d' % self.scanNr + '/measurement/%s' % self.yMotor))

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
        Override data reading. Here the filename is only used to find the
        path of the Lima hdf5 files.
        """

        if not os.path.exists(self.fileName): raise NoDataException
        if self.dataType == 'xrd':
            with h5py.File(self.fileName, 'r') as hf:
                data = np.array(hf.get('entry%d' % self.scanNr + '/measurement/%s' % self.scalarData))
        else:
            raise NoDataException('unknown datatype specified (should be ''xrd''')
        # pretend this is 2d detector data
        data = data.reshape(-1, 1, 1)
        return data

class scalar_flyscan_mar2019(flyscan_nov2018, Scan):

    default_opts = cp.deepcopy(flyscan_nov2018.default_opts)
    remove_keys = ['xrfChannel', 'detectorPreference', 'xrdBinning', 'xrdCropping',
                   'xrdNormalize', 'xrfCropping',]
    for key in remove_keys:
        default_opts.pop(key)
    default_opts['scalarData'] = {
            'value': 'AdLinkAI_buff',
            'type': ['Ni6602_buff', 'AdLinkAI_buff'],
            'doc': "channel to load",
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
        self.fileName = opts['fileName']['value']
        self.scanNr = opts['scanNr']['value']
        self.dataType = opts['dataType']['value']
        self.xMotor = opts['xMotor']['value']
        self.yMotor = opts['yMotor']['value']
        self.nMaxLines = opts['nMaxLines']['value']
        self.globalPositions = opts['globalPositions']['value']
        self.scalarData = opts['scalarData']['value']
        self.normalize_by_I0 = opts['normalize_by_I0']['value']

    def _readData(self):
        """ 
        Override data reading.
        """
        if self.normalize_by_I0:
            entry = 'entry%d' % self.scanNr
            if not os.path.exists(self.fileName): raise NoDataException
            with h5py.File(self.fileName, 'r') as hf:
                I0_data = np.array(hf[entry+'/measurement/Ni6602_buff'])
                I0_data = I0_data.astype(float) * 1e-5
                I0_data = I0_data[:, :self.images_per_line]

        if self.dataType == 'xrd':
            print "loading scalar data..."

            data = []
            print "attempting to read %d lines of diffraction data (based on the positions array or max number of lines set)"%self.nlines
            
            entry = 'entry%d' % self.scanNr
            fileName = self.fileName
            if not os.path.exists(fileName): raise NoDataException
            with h5py.File(fileName, 'r') as hf:
                data = hf[entry + '/measurement/' + self.scalarData]
                data = data[:self.nlines, :self.images_per_line]

            if self.normalize_by_I0:
                data = data / I0_data

        else:
            raise NoDataException('unknown datatype specified (should be ''xrd'')')
        return data.reshape(-1, 1, 1)
