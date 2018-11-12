from Scan import Scan
import numpy as np
import h5py
import copy as cp

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

        if self.dataType == 'xrd':
            with h5py.File(self.fileName, 'r') as hf:
                data = np.array(hf.get('entry%d' % self.scanNr + '/measurement/%s' % self.scalarData))
        else:
            raise RuntimeError('unknown datatype specified (should be ''xrd''')
        # pretend this is 2d detector data
        data = data.reshape(-1, 1, 1)
        return data

