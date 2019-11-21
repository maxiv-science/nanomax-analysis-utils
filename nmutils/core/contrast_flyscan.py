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
        'type': ['pilatus', 'merlin', 'pilatus1m', 'xspress3', 'counter1', 'counter2', 'counter3', 'adlink', 'waxs'],
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
    'xrdCropping': {
        'value': [],
        'type': list,
        'doc': 'detector area to load, [i0, i1, j0, j1]',
        },
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
    'waxsPath': {
        'value': '../../process/radial_integration/<sampledir>',
        'type': str,
        'doc': 'path to waxs data, absolute or relative to h5 folder, <sampledir> is replaced',
        },
    }

    # an optional class attribute which lets scanViewer know what
    # dataSource options have what dimensionalities.
    sourceDims = {'pilatus':2, 'xspress3':1, 'adlink':0, 'merlin':2,
                  'pilatus1m':2, 'counter1':0, 'counter2':0, 'counter3':0,
                  'waxs':1}
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
        self.xrdCropping = list(map(int, opts['xrdCropping']['value']))
        self.nMaxLines = opts['nMaxLines']['value']
        self.globalPositions = opts['globalPositions']['value']
        self.normalize_by_I0 = opts['normalize_by_I0']['value']
        self.waxsPath = opts['waxsPath']['value']

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
            crop = (self.dataSource != 'xspress3') and self.xrdCropping

            with h5py.File(self.fileName, 'r') as fp:

                # pre-allocate an array, to avoid wasting memory
                try:
                    n_lines = len(fp['entry/measurement/%s'%self.dataSource].keys())
                    n_lines = min(self.nMaxLines, n_lines) if self.nMaxLines else n_lines
                except KeyError:
                    raise NoDataException
                line1 = self._safe_get_dataset(fp, 'entry/measurement/%s/000000'%self.dataSource)
                line_length = line1.shape[0]
                if crop:
                    i0, i1, j0, j1 = self.xrdCropping
                    data_shape = line1[0, i0:i1, j0:j1].shape
                else:
                    data_shape = line1.shape[1:]
                dtype = line1.dtype
                shape = (n_lines*line_length, *data_shape)
                print('allocating a %s %s array'%(shape, dtype))
                data = np.empty(shape, dtype=dtype)

                # load
                for i in range(n_lines):
                    v = fp['entry/measurement/%s/%06u' % (self.dataSource, i)]
                    if crop:
                        data[i*line_length : (i+1)*line_length] = v[:, i0:i1, j0:j1]
                    else:
                        data[i*line_length : (i+1)*line_length] = v
                    print('loaded %u/%u lines' % (i, n_lines) + '\r', end='')

        elif self.dataSource in ('counter1', 'counter2', 'counter3', 'adlink'):
            if 'counter' in self.dataSource:
                self.dataSource = 'ni/' + self.dataSource
            with h5py.File(self.fileName, 'r') as fp:
                data = self._safe_get_array(fp, 'entry/measurement/%s'%self.dataSource).flatten()

        elif self.dataSource == 'waxs':
            if self.waxsPath[0] == '/':
                path = self.waxsPath
            else:
                sampledir = os.path.basename(os.path.dirname(os.path.abspath(self.fileName)))
                self.waxsPath = self.waxsPath.replace('<sampledir>', sampledir)
                path = os.path.abspath(os.path.join(os.path.dirname(self.fileName), self.waxsPath))
            fn = os.path.basename(self.fileName)
            waxsfn = fn.replace('.h5', '_waxs.h5')
            waxs_file = os.path.join(path, waxsfn)
            print('loading waxs data from %s' % waxs_file)
            with h5py.File(waxs_file, 'r') as fp:
                q = self._safe_get_array(fp, 'q')
                I = self._safe_get_array(fp, 'I')
            data = I
            self.dataAxes[name] = [q,]
            self.dataDimLabels[name] = ['q (1/nm)']

        else:
            raise RuntimeError('Something is seriously wrong, we should never end up here since _updateOpts checks the options.')

        # normalize
        if self.normalize_by_I0:
            data = (data.T / I0_data[:, ]).T # broadcasting

        # select/average the xrf channels
        if self.dataSource == 'xspress3':
            data = np.mean(data[:, self.xrfChannel, :4096], axis=1)
        return data
