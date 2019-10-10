from . import Scan
from ..utils import fastBinPixels
from .. import NoDataException
import numpy as np
import h5py
import copy as cp
import os.path


class contrast_flyscan(Scan):
    """
    Flyscan format for the Contrast acquisition software
    """

    # the dataSource option is mandatory for use with scanViewer.
    default_opts = {
    'scanNr': {
        'value': 0,
        'type': int,
        'doc': "scan number",
        },
    'path': {
        'value': None,
        'type': str,
        'doc': "path to the folder containing the main data file",
        },
    'dataSource': {
        'value': 'pilatus',
        'type': ['pilatus', 'merlin', 'pilatus1m', 'xspress3', 'counter1', 'counter2', 'counter3', 'adlink', 'pil1m-waxs'],
        'doc': "type of data",
        },
    'slowMotor': {
        'value': None,
        'type': str,
        'doc': 'slow motor, leave empty to detect the slow motor among the npoint axes',
        },
    'xrfChannel': {
        'value': [3,],
        'type': list,
        'doc': 'xspress3 channels from which to read XRF, averaged',
        },
    # 'xrfCropping': {
    #     'value': [],
    #     'type': list,
    #     'doc': 'energy channel range to load, [ch0, ch1]',
    #     },
    # 'xrdCropping': {
    #     'value': [],
    #     'type': list,
    #     'doc': 'detector area to load, [i0, i1, j0, j1]',
    #     },
    # 'xrdBinning': {
    #     'value': 1,
    #     'type': int,
    #     'doc': 'bin xrd pixels n-by-n (after cropping)',
    #     },
    'nMaxLines': {
        'value': 0,
        'type': int,
        'doc': 'load at most N lines - 0 means load all',
        },
    'globalPositions': {
        'value': False,
        'type': bool,
        'doc': 'attempt to assign global scanning positions',
        },
    'normalize_by_I0': {
        'value': False,
        'type': bool,
        'doc': 'whether or not to normalize (all) data against I0',
        },
    # 'waxsPath': {
    #     'value': '../../process/radial_integration/<sampledir>',
    #     'type': str,
    #     'doc': 'path to waxs data, absolute or relative to h5 folder, <sampledir> is replaced',
    #     },
    }

    # an optional class attribute which lets scanViewer know what
    # dataSource options have what dimensionalities.
    sourceDims = {'pilatus':2, 'xspress3':1, 'adlink':0, 'merlin':2,
                  'pilatus1m':2, 'counter1':0, 'counter2':0, 'counter3':0,
                  'pil1m-waxs':1}
    assert sorted(sourceDims.keys()) == sorted(default_opts['dataSource']['type'])

    def _prepareData(self, **kwargs):
        """ 
        Parse the derived options
        """
        # copy defaults, then update with kwarg options

        opts = cp.deepcopy(self.default_opts)
        opts = self._updateOpts(opts, **kwargs)
        
        # parse options
        path = opts['path']['value']
        if path.endswith('h5'):
            path = os.path.dirname(path)
        scanNr = int(opts['scanNr']['value'])
        self.fileName = os.path.join(path, '%06u.h5'%scanNr)
        self.dataSource = opts['dataSource']['value']
        self.slowMotor = opts['slowMotor']['value']
        self.xrfChannel = list(map(int, opts['xrfChannel']['value']))
        # self.xrfCropping = list(map(int, opts['xrfCropping']['value']))
        # self.xrdCropping = list(map(int, opts['xrdCropping']['value']))
        # self.xrdBinning = opts['xrdBinning']['value']
        # self.xrdNormalize = list(map(int, opts['xrdNormalize']['value']))
        self.nMaxLines = opts['nMaxLines']['value']
        self.globalPositions = opts['globalPositions']['value']
        self.normalize_by_I0 = opts['normalize_by_I0']['value']
        # self.xrfChannel = list(map(int, opts['xrfChannel']['value']))
        # self.waxsPath = opts['waxsPath']['value']

        # Sanity check
        try:
            with h5py.File(self.fileName, 'r') as fp:
                pass
        except OSError:
            raise NoDataException('Could not find or open the file %s' % self.fileName)

    def _readPositions(self):
        """ 
        Override position reading.
        """

        with h5py.File(self.fileName, 'r') as fp:
            # first, work out which is the flyscan axis and load that
            jranges = [self._safe_get_dataset(fp, 'entry/measurement/npoint_buff/%s'%ax)[0, :].ptp() for ax in 'xyz']
            fast = 'xyz'[np.argmax(jranges)]
            print('determined that %s is the fast axis' % fast)
            fast_pos = self._safe_get_array(fp, 'entry/measurement/npoint_buff/%s'%fast).flatten()
            line_length = self._safe_get_dataset(fp, 'entry/measurement/npoint_buff/x').shape[1]

            # then, is the slow axis one of the npoint buffers or a normal motor?
            if not self.slowMotor:
                iranges = [self._safe_get_dataset(fp, 'entry/measurement/npoint_buff/%s'%ax)[:, 0].ptp() for ax in 'xyz']
                slow = 'xyz'[np.argmax(iranges)]
                print('determined that %s is the slow axis' % slow)
                slow_pos = self._safe_get_array(fp, 'entry/measurement/npoint_buff/%s' % slow).flatten()
            else:
                slow = self.slowMotor
                slow_pos = self._safe_get_array(fp, 'entry/measurement/%s'%self.slowMotor)
                slow_pos = np.repeat(slow_pos, line_length)

        # Assign the slow/fast axes to x and y
        if fast == 'y':
            y = fast_pos
            x = slow_pos
            ymotor = fast
            xmotor = slow
        else:
            x = fast_pos
            y = slow_pos
            xmotor = fast
            ymotor = slow

        # Honour the limiting option
        if self.nMaxLines:
            x = x[:self.nMaxLines*line_length]
            y = y[:self.nMaxLines*line_length]

        # allow 1d scans
        try:
            len(y)
        except TypeError:
            y = np.zeros(x.shape)
        try:
            len(x)
        except TypeError:
            x = np.zeros(y.shape)

        # account for base motors
        if self.globalPositions:
            with h5py.File(self.fileName, 'r') as fp:
                x += self._safe_get_array(fp, 'entry/snapshot/basex')
                y += self._safe_get_array(fp, 'entry/snapshot/basey')

        # save motor labels
        self.positionDimLabels = [xmotor, ymotor]

        return np.vstack((x, y)).T

    def _readData(self, name):
        """ 
        Override data reading. Here the filename is only used to find the
        path of the Lima hdf5 files.
        """

        if self.normalize_by_I0:
            with h5py.File(self.fileName, 'r') as fp:
                I0_data = fp['entry/measurement/ni/counter1'][()].flatten()

        if self.dataSource in ('merlin', 'pilatus', 'pilatus1m', 'xspress3'):
            print("Loading %s data..." % self.dataSource)

            with h5py.File(self.fileName, 'r') as fp:

                # pre-allocate an array, to avoid wasting memory
                try:
                    n_lines = len(fp['entry/measurement/%s'%self.dataSource].keys())
                except KeyError:
                    raise NoDataException
                line1 = self._safe_get_dataset(fp, 'entry/measurement/%s/000000'%self.dataSource)
                line_length = line1.shape[0]
                data_shape = line1.shape[1:]
                dtype = line1.dtype
                lines = min(self.nMaxLines, n_lines) if self.nMaxLines else n_lines
                shape = (n_lines*line_length, *data_shape)
                print('allocating a %s %s array'%(shape, dtype))
                data = np.empty(shape, dtype=dtype)

                # load
                for i in range(lines):
                    v = fp['entry/measurement/%s/%06u' % (self.dataSource, i)]
                    data[i*line_length : (i+1)*line_length] = v
                    print('loaded %u/%u lines' % (i, lines) + '\r', end='')

        elif self.dataSource in ('counter1', 'counter2', 'counter3', 'adlink'):
            if 'counter' in self.dataSource:
                self.dataSource = 'ni/' + self.dataSource
            with h5py.File(self.fileName, 'r') as fp:
                data = self._safe_get_array(fp, 'entry/measurement/%s'%self.dataSource).flatten()

        elif self.dataSource == 'pil1m-waxs':
            raise NotImplementedError('waxs has to be reimplemented! sorry.')

        else:
            raise RuntimeError('Something is seriously wrong, we should never end up here since _updateOpts checks the options.')

        # normalize
        if self.normalize_by_I0:
            data = (data.T / I0_data[:, ]).T # broadcasting

        # select/average the xrf channels
        if self.dataSource == 'xspress3':
            data = np.mean(data[:, self.xrfChannel, :4096], axis=1)
        return data
