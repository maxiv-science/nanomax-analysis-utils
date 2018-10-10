from Scan import Scan
from ..utils import fastBinPixels
import numpy as np
import h5py
import copy as cp
import os.path

class i08_scan(Scan):

    default_opts = {
        # the dataType option is mandatory for use with scanViewer
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
        self.dataType = opts['dataType']['value']
        self.normalize = opts['normalizeI0']['value']

        # check file name, we want the one called *_b.nxs
        splt = self.fileName.split('.')
        if not splt[-2][-2:] == '_b':
            splt[-2] += '_b'
        self.fileName = '.'.join(splt)
        print 'going to load %s' % self.fileName

    def _readPositions(self):
        """
        Override position reading.
        """

        with h5py.File(self.fileName, 'r') as hf:
            x_ = np.array(hf.get('entry/xmapMca/SampleX'))
            y_ = np.array(hf.get('entry/xmapMca/SampleY'))
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
            with h5py.File(self.fileName, 'r') as fp:
                data = np.array(fp.get('entry/xmapMca/data'))
                data = data.reshape(-1, data.shape[-1])
                I0 = np.array(fp.get('entry/xmapMca/I0'))
                I0 = I0.reshape(-1)
                I0 = np.tile(I0, data.shape[1]).reshape(-1, I0.shape[0]).T
        else:
            raise RuntimeError('unknown datatype specified (should be ''xrf''')
        if self.normalize:
            data = data / I0
        return data

