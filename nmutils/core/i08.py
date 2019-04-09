from Scan import Scan
from ..utils import fastBinPixels
from .. import NoDataException
import numpy as np
import h5py
import copy as cp
import os.path

class i08_scan(Scan):

    default_opts = {
        # the dataType option is mandatory for use with scanViewer
        'fileName': {
            'value': None,
            'type': str,
            'doc': "name of the main data file",
            },
        'dataType': {
            'value': 'xrd',
            'type': str,
            'doc': "type of data, 'xrd' or 'xrf'",
            },
        'normalizeI0': {
            'value': True,
            'type': bool,
            'doc': "divide by the incoming x-ray intensity?",
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
        self.fileName = opts['fileName']['value']
        self.dataType = opts['dataType']['value']
        self.normalize = opts['normalizeI0']['value']

    def _readPositions(self):
        """
        Override position reading. A bit complicated since xrd (stxm)
        and xrf data are written with different position formats.
        """
        if not os.path.exists(self.fileName): raise NoDataException
        with h5py.File(self.fileName, 'r') as hf:
            x_ = np.array(hf.get('entry/I0_data/SampleX'))
            y_ = np.array(hf.get('entry/I0_data/SampleY'))
        if x_ is None or None in x_ or x_ == np.array(None):
            # ok we are reading one of these xrf files
            fn = self.fileName[:-4] + '_b.nxs'
            if not os.path.exists(fn): raise NoDataException
            with h5py.File(fn, 'r') as hf:
                x_ = np.array(hf.get('entry/xmapMca/SampleX'))
                y_ = np.array(hf.get('entry/xmapMca/SampleY'))
            print "took positions from", fn
        else:
            print "took positions from", self.fileName

        xx, yy = np.meshgrid(x_, y_)
        x = xx.flatten()
        y = yy.flatten()
        return np.vstack((x, y)).T

    def _readData(self):
        """
        Override data reading.
        """

        if self.dataType == 'xrf':
            print "loading fluorescence data..."
            fn = self.fileName[:-4] + '_b.nxs'
            if not os.path.exists(fn): raise NoDataException
            with h5py.File(fn, 'r') as fp:
                data = np.array(fp.get('entry/xmapMca/data'))
                data = data.reshape(-1, data.shape[-1])
                I0 = np.array(fp.get('entry/xmapMca/I0'))
                I0 = I0.reshape(-1)
                I0 = np.tile(I0, data.shape[1]).reshape(-1, I0.shape[0]).T
            if self.normalize:
                data = data / I0
        elif self.dataType == 'xrd':
            print "loading STXM data..."
            with h5py.File(self.fileName, 'r') as fp:
                data = np.array(fp.get('entry/I0_data/I0'))
                if len(data.shape) == 5:
                    data = data[0]
                    print '*** NOTE: there seems to be many diode channels. Choosing the first.'
                data = data.reshape(data.shape[0] * data.shape[1], 1, 1)
        else:
            raise RuntimeError('unknown datatype specified (should be ''xrf'' or ''xrd''')
        return data

