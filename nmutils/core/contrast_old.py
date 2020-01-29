from . import Scan
from ..utils import fastBinPixels
from .. import NoDataException
import numpy as np
import h5py
import copy as cp
import os.path


class contrast_stepscan_old(Scan):
    """
    Stepscan format for the Contrast acquisition software.
    """

    alba_names = ['alba%u/%u'%(i,j) for i in (0,2) for j in (1,2,3,4)]
    default_opts = {
        'scanNr': {
            'value': 0,
            'type': int,
            'doc': "scan number",
            },
        'path': {
            'value': None,
            'type': str,
            'doc': "folder containing the main data file",
            },
        'dataSource': {
            'value': 'merlin',
            'type': ['merlin', 'xspress3', 'pilatus', 'pilatus1m', 'ni/counter1', 'ni/counter2', 'ni/counter3', 'waxs']+alba_names,
            'doc': "type of data",
            },
        'xMotor': {
            'value': 'sx',
            'type': str,
            'doc': 'scanned motor to plot on the x axis',
            },
        'yMotor': {
            'value': 'sy',
            'type': str,
            'doc': 'scanned motor to plot on the y axis',
            },
        'xrfChannel': {
            'value': 3,
            'type': int,
            'doc': 'xspress3 channel from which to read XRF',
            },
        'xrdCropping': {
            'value': [],
            'type': list,
            'doc': 'detector area to load, [i0, i1, j0, j1]',
            },
        'xrdBinning': {
            'value': 1,
            'type': int,
            'doc': 'bin xrd pixels n-by-n (after cropping)',
            },
        'normalize_by_I0': {
            'value': False,
            'type': bool,
            'doc': 'whether to normalize against I0 (ni/counter1)',
            },
        'nominalPositions': {
            'value': False,
            'type': bool,
            'doc': 'use nominal instead of recorded positions',
            },
        'waxsPath': {
            'value': '../../process/radial_integration/<sampledir>',
            'type': str,
            'doc': 'path to waxs data, absolute or relative to h5 folder, <sampledir> is replaced',
        },
        'burstSum': {
            'value': False,
            'type': bool,
            'doc': 'whether or not to sum burst acquisitions (otherwise you get the first frame)',
        },
        'nMaxPositions': {
            'value': 0,
            'type': int,
            'doc': 'maximum number of positions to read (0 means all)',
        },
    }

    # an optional class attribute which lets scanViewer know what
    # dataSource options have what dimensionalities.
    sourceDims = {'pilatus':2, 'xspress3':1, 'merlin':2, 'pilatus1m':2, 'ni/counter1':0, 'ni/counter2':0, 'ni/counter3':0, 'waxs':1}
    albaDims = {name:0 for name in alba_names}
    sourceDims.update(albaDims)
    assert sorted(sourceDims.keys()) == sorted(default_opts['dataSource']['type'])

    def _prepareData(self, **kwargs):
        """ 
        This method gets the kwargs passed to the addData() method, and
        stores them for use during this data loading.
        """
        # copy defaults, then update with kwarg options
        opts = cp.deepcopy(self.default_opts)
        opts = self._updateOpts(opts, **kwargs)
        
        # parse options
        path = opts['path']['value']
        if path.endswith('h5'):
            path = os.path.dirname(path)
        scanNr = int(opts['scanNr']['value'])
        self.dataSource = opts['dataSource']['value']
        self.fileName = os.path.join(path, '%06u.h5'%scanNr)
        self.xMotor = opts['xMotor']['value']
        self.yMotor = opts['yMotor']['value']
        self.xrfChannel = int(opts['xrfChannel']['value'])
        self.xrdCropping = opts['xrdCropping']['value']
        self.xrdBinning = int(opts['xrdBinning']['value'])
        self.normalize_by_I0 = (opts['normalize_by_I0']['value'])
        self.nominalPositions = bool(opts['nominalPositions']['value'])
        self.waxsPath = opts['waxsPath']['value']
        self.burstSum = opts['burstSum']['value']
        self.nMaxPositions = opts['nMaxPositions']['value']

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

        if not os.path.exists(self.fileName): raise NoDataException
        with h5py.File(self.fileName, 'r') as hf:
            x = np.array(hf.get('entry/measurement/%s' % self.xMotor))
            y = np.array(hf.get('entry/measurement/%s' % self.yMotor))
        if self.nMaxPositions:
            x = x[:self.nMaxPositions]
            y = y[:self.nMaxPositions]
        # allow 1d scans
        try:
            len(y)
        except TypeError:
            y = np.zeros(x.shape)
        try:
            len(x)
        except TypeError:
            x = np.zeros(y.shape)

        # save motor labels
        self.positionDimLabels = [self.xMotor, self.yMotor]

        return np.vstack((x, y)).T

    def _readData(self, name):
        """ 
        Override data reading. Here the filename is only used to find the
        path of the Lima hdf5 files.
        """

        if self.normalize_by_I0:
            if not os.path.exists(self.fileName): raise NoDataException
            with h5py.File(self.fileName, 'r') as hf:
                I0_data = self._safe_get_array(hf, 'entry/measurement/ni/counter1')
                I0_data = I0_data.astype(float) * 1e-5
                print(I0_data)

        if self.dataSource in ('merlin', 'pilatus', 'pilatus1m'):
            print("loading diffraction data...")
            path = os.path.split(os.path.abspath(self.fileName))[0]

            data = []
            ic = None; jc = None # center of mass
            missing = 0
            hdf_pattern = 'entry/measurement/%s/%%06u' % self.dataSource

            with h5py.File(self.fileName, 'r') as hf:
                print('loading diffraction data: ' + self.fileName)
                for im in range(self.positions.shape[0]):
                    if self.nMaxPositions and im == self.nMaxPositions:
                        break
                    dataset = self._safe_get_dataset(hf, hdf_pattern%im)
                    if dataset.shape[0] == self.positions.shape[0]:
                        # this is hybrid triggering data!
                        subframe = im
                    else:
                        subframe = 0
                    # for the first frame, determine center of mass
                    if ic is None or jc is None == 0:
                        import scipy.ndimage.measurements
                        img = np.array(dataset[0])
                        try:
                            ic, jc = list(map(int, scipy.ndimage.measurements.center_of_mass(img)))
                        except ValueError:
                            ic = img.shape[0] // 2
                            jc = img.shape[1] // 2
                        print("Estimated center of mass to (%d, %d)"%(ic, jc))
                    if self.xrdCropping:
                        i0, i1, j0, j1 = self.xrdCropping
                        if self.burstSum:
                            data_ = np.sum(np.array(dataset[:, i0:i1, j0:j1]), axis=0)
                        else:
                            data_ = np.array(dataset[subframe, i0:i1, j0:j1])
                    else:
                        if self.burstSum:
                            data_ = np.sum(np.array(dataset), axis=0)
                        else:
                            data_ = np.array(dataset[subframe])
                    if self.xrdBinning > 1:
                        data_ = fastBinPixels(data_, self.xrdBinning)
                    data.append(data_)

            print("loaded %d images"%len(data))
            if missing:
                print("there were %d missing images" % missing)
            data = np.array(data)
            if self.normalize_by_I0:
                data = data / I0_data[:, None, None]

        elif self.dataSource == 'xspress3':
            print("loading fluorescence data...")
            print("selecting xspress3 channel %d"%self.xrfChannel)
            data = []
            with h5py.File(self.fileName, 'r') as hf:
                for im in range(self.positions.shape[0]):
                    dataset = self._safe_get_dataset(hf, 'entry/measurement/xspress3/%06d' % im)
                    if not dataset:
                        break
                    data.append(np.array(dataset)[0, self.xrfChannel, :4096])
            data = np.array(data)
            if self.normalize_by_I0:
                data = data / I0_data[:, None]
            self.dataDimLabels[name] = ['Approx. energy (keV)']
            self.dataAxes[name] = [np.arange(data.shape[-1]) * .01]

        elif 'ni/' in self.dataSource or 'alba' in self.dataSource:
            entry = 'entry/measurement/%s' % self.dataSource
            with h5py.File(self.fileName, 'r') as hf:
                data = self._safe_get_array(hf, entry)
                data = data.astype(float)
                data = data.flatten()

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
        
        return data

from . import Scan
from ..utils import fastBinPixels
from .. import NoDataException
import numpy as np
import h5py
import copy as cp
import os.path


class contrast_flyscan_old(Scan):
    """
    Flyscan format for the Contrast acquisition software
    """

    # the dataSource option is mandatory for use with scanViewer.
    alba_names = ['alba%u/%u'%(i,j) for i in (0,2) for j in (1,2,3,4)]
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
        'type': ['pilatus', 'merlin', 'pilatus1m', 'xspress3', 'ni/counter1', 'ni/counter2', 'ni/counter3', 'adlink', 'waxs']+alba_names,
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
                  'pilatus1m':2, 'ni/counter1':0, 'ni/counter2':0, 'ni/counter3':0,
                  'waxs':1}
    albaDims = {name:0 for name in alba_names}
    sourceDims.update(albaDims)
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
            if self.dataSource == 'xspress3':
                self.dataDimLabels[name] = ['Approx. energy (keV)']
                self.dataAxes[name] = [np.arange(4096) * .01]

        elif (self.dataSource[:4] == 'alba') or self.dataSource == 'adlink' or self.dataSource[:3] == 'ni/':
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
