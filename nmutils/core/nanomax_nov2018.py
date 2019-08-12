from . import Scan
from ..utils import fastBinPixels
from .. import NoDataException
import numpy as np
import h5py
import copy as cp
import os.path

class flyscan_nov2018(Scan):
    """
    Fairly mature fly scan format.
    """

    # the dataSource option is mandatory for use with scanViewer.
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
    'dataSource': {
        'value': 'pil100k',
        'type': ['pil100k', 'merlin', 'pil1m', 'xspress3', 'counter', 'adlink', 'pil1m-waxs'],
        'doc': "type of data",
        },
    'xMotor': {
        'value': 'samx_buff',
        'type': str,
        'doc': 'x axis motor',
        },
    'yMotor': {
        'value': 'samy_buff',
        'type': str,
        'doc': 'y axis motor',
        },
    'xrfChannel': {
        'value': [3,],
        'type': list,
        'doc': 'xspress3 channels from which to read XRF, averaged',
        },
    'xrfCropping': {
        'value': [],
        'type': list,
        'doc': 'energy channel range to load, [ch0, ch1]',
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
    'xrdNormalize': {
        'value': [],
        'type': list,
        'doc': 'normalize XRD images by average over the ROI [i0, i1, j0, j1]',
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
        'doc': 'whether or not to normalize against I0',
        },
    'waxsPath': {
        'value': '../../process/radial_integration/<sampledir>',
        'type': str,
        'doc': 'path to waxs data, absolute or relative to h5 folder, <sampledir> is replaced',
        },
    }

    # an optional class attribute which lets scanViewer know what
    # dataSource options have what dimensionalities.
    sourceDims = {'pil100k':2, 'xspress3':1, 'adlink':0, 'merlin':2, 'pil1m':2, 'counter':0, 'pil1m-waxs':1}
    assert sorted(sourceDims.keys()) == sorted(default_opts['dataSource']['type'])

    def _prepareData(self, **kwargs):
        """ 
        Parse the derived options
        """
        # copy defaults, then update with kwarg options

        opts = cp.deepcopy(self.default_opts)
        opts = self._updateOpts(opts, **kwargs)
        
        # parse options
        self.dataSource = opts['dataSource']['value']
        self.xMotor = opts['xMotor']['value']
        self.yMotor = opts['yMotor']['value']
        self.xrfChannel = opts['xrfChannel']['value']
        self.xrfCropping = map(int, opts['xrfCropping']['value'])
        self.xrdCropping = map(int, opts['xrdCropping']['value'])
        self.xrdBinning = opts['xrdBinning']['value']
        self.xrdNormalize = map(int, opts['xrdNormalize']['value'])
        self.nMaxLines = opts['nMaxLines']['value']
        self.globalPositions = opts['globalPositions']['value']
        self.scanNr = opts['scanNr']['value']
        self.fileName = opts['fileName']['value']
        self.normalize_by_I0 = opts['normalize_by_I0']['value']
        self.xrfChannel = map(int, opts['xrfChannel']['value'])
        self.waxsPath = opts['waxsPath']['value']

    def _read_buffered(self, fp, entry):
        """
        Returns a flat array of buffered positions
        """
        data = np.asarray(fp.get(entry))
        # find line length by looking for padding zeros
        try:
            nLines = data.shape[0]
            for i in range(data.shape[1]):
                if data[0, i] == 0:
                    Nx = i
                    break
            data = data[:, :Nx].flatten()
        except IndexError:
            print '*** Bad positions. Try setting nMaxLines if the scan is still under way.'
            raise NoDataException
        return data, nLines, Nx

    def _read_non_buffered(self, fp, entry, lineLength, nLines):
        """
        Returns a flat array of non-buffered positions, repeated to match
        buffered data.
        """
        data = np.asarray(fp.get(entry))
        if not (len(data) == nLines): 
            print '*** Bad positions. Try setting nMaxLines if the scan is still under way.'
            raise NoDataException
        data = np.repeat(data, lineLength)
        return data

    def _readPositions(self):
        """ 
        Override position reading.
        """
        
        entry = 'entry%d' % self.scanNr
        fileName = self.fileName

        # open hdf5 file
        try:
            fp = h5py.File(fileName, 'r')
        except IOError:
            raise NoDataException

        # infer which is the slow axis
        slowMotorHint = self._safe_get_array(fp, entry + '/title')[()].split(' ')[1]
        if slowMotorHint in ('sx', 'sy', 'sz'):
            slowMotorHint = {'sx':'lc400_buff_2', 'sy':'lc400_buff_3', 'sz':'lc400_buff_1'}[slowMotorHint]
        if slowMotorHint in self.xMotor:
            fastMotor = self.yMotor
            slowMotor = self.xMotor
            print "Loader inferred that %s is the fast axis" % self.yMotor
        elif slowMotorHint in self.yMotor:
            fastMotor = self.xMotor
            slowMotor = self.yMotor
            print "Loader inferred that %s is the fast axis" % self.xMotor
        else:
            raise NoDataException("Couldn't determine which is the fast axis!")

        # read the fast axis
        fast, nLines, lineLen = self._read_buffered(fp, entry+'/measurement/%s'%fastMotor)

        # save number of lines for the _readData method
        self.nlines = nLines
        self.images_per_line = lineLen

        # read the slow axis
        slow_is_buffered = len(fp.get(entry+'/measurement/%s'%slowMotor).shape) > 1
        if slow_is_buffered:
            slow, _, _ = self._read_buffered(fp, entry+'/measurement/%s'%slowMotor)
        else:
            slow = self._read_non_buffered(fp, entry+'/measurement/%s'%slowMotor, lineLen, nLines)

        # limit the number of lines if requested
        if self.nMaxLines:
            self.nlines = self.nMaxLines
            fast = fast[:lineLen * self.nMaxLines]
            slow = slow[:lineLen * self.nMaxLines]

        # assign fast and slow positions
        if fastMotor == self.xMotor:
            x = fast
            y = slow
        else:
            y = fast
            x = slow

        print "x and y shapes:", x.shape, y.shape

        # optionally add coarse stage position
        if self.globalPositions:
            sams_x = fp.get(entry+'/measurement/sams_x')[()] * 1e3
            sams_y = fp.get(entry+'/measurement/sams_y')[()] * 1e3
            sams_z = fp.get(entry+'/measurement/sams_z')[()] * 1e3
            offsets = {'samx': sams_x, 'samy': sams_y, 'samz': sams_z}
            x += offsets[self.xMotor[:4]]
            y += offsets[self.yMotor[:4]]
            print '*** added rough position offsets!'

        print "loaded positions from %d lines, %d positions on each"%(self.nlines, lineLen)

        # close hdf5 file
        fp.close()

        # save motor labels
        if self.globalPositions:
            rough = {'samx_buff':'sams_x', 'samy_buff':'sams_y', 'samz_buff':'sams_z'}
            self.positionDimLabels = ['%s+%s (um)'%(self.xMotor, rough[self.xMotor]),
                                      '%s+%s (um)'%(self.yMotor, rough[self.yMotor])]
        else:
            self.positionDimLabels = ['%s (um)'%self.xMotor, '%s (um)'%self.yMotor]

        return np.vstack((x, y)).T

    def _readData(self, name):
        """ 
        Override data reading.
        """

        if self.normalize_by_I0:
            entry = 'entry%d' % self.scanNr
            if not os.path.exists(self.fileName): raise NoDataException
            with h5py.File(self.fileName, 'r') as fp:
                I0_data = self._safe_get_array(fp, entry+'/measurement/Ni6602_buff')
                I0_data = I0_data.astype(float) * 1e-5
                I0_data = I0_data[:, :self.images_per_line]

        if self.dataSource in ('pil100k', 'merlin', 'pil1m'):
            print "loading diffraction data..."
            path = os.path.split(os.path.abspath(self.fileName))[0]
            
            # set detector paths
            if self.dataSource == 'merlin':
                filename_pattern = 'scan_%04d_merlin_0000.hdf5'
                hdfpath_pattern = 'entry_%04d/measurement/Merlin/data'
            elif self.dataSource == 'pil100k':
                filename_pattern = 'scan_%04d_pil100k_0000.hdf5'
                hdfpath_pattern = 'entry_%04d/measurement/Pilatus/data'
            elif self.dataSource == 'pil1m':
                filename_pattern = 'scan_%04d_pil1m_0000.hdf5'
                hdfpath_pattern = 'entry_%04d/measurement/Pilatus/data'

            data = []
            print "attempting to read %d lines of diffraction data (based on the positions array or max number of lines set)"%self.nlines
                 
            fn = os.path.join(path, filename_pattern%self.scanNr)
            if not os.path.exists(fn): raise NoDataException('No hdf5 file found.')
            with h5py.File(fn, 'r') as hf:
                for line in range(self.nlines):
                    try:
                        print 'loading data: ' + filename_pattern%self.scanNr + ', line %d'%line
                        dataset = self._safe_get_dataset(hf, hdfpath_pattern%line)
                        if self.xrdCropping:
                            i0, i1, j0, j1 = self.xrdCropping
                            data_ = np.array(dataset[:, i0 : i1, j0 : j1])
                        else:
                            data_ = np.array(dataset)
                        if self.xrdBinning > 1:
                            shape = fastBinPixels(data_[0], self.xrdBinning).shape
                            new_data_ = np.zeros((data_.shape[0],) + shape)
                            for ii in range(data_.shape[0]):
                                new_data_[ii] = fastBinPixels(data_[ii], self.xrdBinning)
                            data_ = new_data_
                        if self.dataSource == 'merlin':
                            for i in range(data_.shape[0]):
                                data_[i] = np.flipud(data_[i]) # Merlin images indexed from the bottom left...
                        del dataset
                        if self.normalize_by_I0:
                            I0_line = I0_data[line]
                            data_ = data_ / I0_line[:, None, None]
                        data.append(data_)

                    except IOError:
                        # fewer hdf5 files than positions -- this is ok
                        print "couldn't find expected file %s, returning"%(filename_pattern%(self.scanNr, line))
                        break

            print "loaded %d lines of diffraction data"%len(data)
            data = np.concatenate(data, axis=0)

        elif self.dataSource == 'xspress3':
            print "loading fluorescence data..."
            print "selecting fluorescence channels %s"%self.xrfChannel
            path = os.path.split(os.path.abspath(self.fileName))[0]
            filename_pattern = 'scan_%04d_xspress3_0000.hdf5'
            print 'loading data: ' + filename_pattern%(self.scanNr)
            data = []
            fn = os.path.join(path, filename_pattern%(self.scanNr))
            if not os.path.exists(fn): raise NoDataException
            with h5py.File(fn, 'r') as hf:
                line = 0
                while True:
                    if line >= self.nlines:
                        break
                    dataset = self._safe_get_dataset(hf, 'entry_%04d/measurement/xspress3/data'%line)
                    if not dataset:
                        break
                    data_ = np.mean(np.array(dataset)[:, self.xrfChannel, :], axis=1)
                    if self.xrfCropping:
                        data_ = data_[:, self.xrfCropping[0]:self.xrfCropping[1]]
                    if self.normalize_by_I0:
                        I0_line = I0_data[line]
                        data_ = data_ / I0_line[:, None]
                    data.append(data_)
                    line += 1
            print "loaded %d lines of fluorescence data"%len(data)
            data = np.vstack(data)
            bad = np.where(np.isinf(data) | np.isnan(data))
            good = np.where(np.isfinite(data))
            data[bad] = np.mean(data[good])
            self.dataDimLabels[name] = ['Approx. energy (keV)']
            self.dataAxes[name] = [np.arange(data_.shape[-1]) * .01]

        elif self.dataSource in ('adlink', 'counter'):
            print "loading buffered scalar data..."
            channel = {'adlink': 'AdLinkAI_buff', 'counter': 'Ni6602_buff'}[self.dataSource]
            entry = 'entry%d' % self.scanNr
            if not os.path.exists(self.fileName): raise NoDataException
            with h5py.File(self.fileName, 'r') as hf:
                data = self._safe_get_array(hf, entry+'/measurement/%s'%channel)
                data = data.astype(float)
                data = data[:, :self.images_per_line]
                data = data.flatten()

        elif self.dataSource == 'pil1m-waxs':
            print "loading WAXS data..."
            if self.waxsPath[0] == '/':
                path = self.waxsPath
            else:
                sampledir = os.path.basename(os.path.dirname(os.path.abspath(self.fileName)))
                self.waxsPath = self.waxsPath.replace('<sampledir>', sampledir)
                path = os.path.abspath(os.path.join(os.path.dirname(self.fileName), self.waxsPath))
            fn = os.path.join(path, 'scan_%04d_pil1m_0000_waxs.hdf5' % self.scanNr)
            if not os.path.exists(fn): raise NoDataException
            with h5py.File(fn, 'r') as fp:
                data = fp['I'][:]
                q = fp['q'][:]
            self.dataAxes[name] = [q,]
            self.dataDimLabels[name] = ['q (1/nm)']
            if self.normalize_by_I0:
                data = data / I0_data.flatten()[:, None]
                bad = np.where(np.isinf(data) | np.isnan(data))
                good = np.where(np.isfinite(data))
                data[bad] = np.mean(data[good])
        else:
            raise RuntimeError('Something is seriously wrong, we should never end up here since _updateOpts checks the options.')
        return data

       
class hws_scan_may_2019(Scan):
    """
    Monkey-patched version for the hws scan.
    """

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
        'dataSource': {
            'value': 'merlin',
            'type': ['merlin', 'xspress3', 'pil100k', 'pil1m', 'counter1', 'counter2', 'counter3', 'pil1m-waxs'],
            'doc': "type of data",
            },
        'xMotor': {
            'value': 'samx',
            'type': str,
            'doc': 'scanned motor to plot on the x axis',
            },
        'yMotor': {
            'value': 'samy',
            'type': str,
            'doc': 'scanned motor to plot on the y axis',
            },
        'xrfChannel': {
            'value': 3,
            'type': int,
            'doc': 'xspress3 channel from which to read XRF',
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
        'normalize_by_I0': {
            'value': False,
            'type': bool,
            'doc': 'whether to normalize against I0 (counter1)',
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
    }

    # an optional class attribute which lets scanViewer know what
    # dataSource options have what dimensionalities.
    sourceDims = {'pil100k':2, 'xspress3':1, 'merlin':2, 'pil1m':2, 'counter1':0, 'counter2':0, 'counter3':0, 'pil1m-waxs':1}
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
        self.dataSource = opts['dataSource']['value']
        self.xMotor = opts['xMotor']['value']
        self.yMotor = opts['yMotor']['value']
        self.xrfChannel = int(opts['xrfChannel']['value'])
        self.xrdCropping = int(opts['xrdCropping']['value'])
        self.xrdBinning = int(opts['xrdBinning']['value'])
        self.normalize_by_I0 = (opts['normalize_by_I0']['value'])
        self.nominalPositions = bool(opts['nominalPositions']['value'])
        self.scanNr = int(opts['scanNr']['value'])
        self.fileName = opts['fileName']['value']
        self.waxsPath = opts['waxsPath']['value']

    def _readPositions(self):
        """ 
        Override position reading.
        """
        print 'here in read positions'
        print self.fileName
        if not os.path.exists(self.fileName): raise NoDataException
        with h5py.File(self.fileName, 'r') as hf:
            if self.nominalPositions:
                title = str(hf.get('entry%d' % self.scanNr + '/title')[()]).split(' ')
                xmotorInd = title.index(self.xMotor)
                ymotorInd = title.index(self.yMotor)
                x = np.linspace(float(title[xmotorInd+1]),
                                float(title[xmotorInd+2]),
                                int(title[xmotorInd+3]) + 1,
                                endpoint=True)
                y = np.linspace(float(title[ymotorInd+1]),
                                float(title[ymotorInd+2]),
                                int(title[ymotorInd+3]) + 1,
                                endpoint=True)
                nx = len(x)
                ny = len(y)
                if xmotorInd < ymotorInd:
                    # x is the fast motor
                    y = y.repeat(nx)
                    x = np.tile(x, ny)
                else:
                    # y is the fast motor
                    x = x.repeat(ny)
                    y = np.tile(y, nx)
            else:
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

        # save motor labels
        self.positionDimLabels = [self.xMotor, self.yMotor]
        return np.vstack((x, y)).T

    def _readData(self, name):
        """ 
        Override data reading.
        """
        if self.normalize_by_I0:
            entry = 'entry%d' % self.scanNr
            if not os.path.exists(self.fileName): raise NoDataException
            with h5py.File(self.fileName, 'r') as fp:
                I0_data = self._safe_get_array(fp, entry+'/measurement/Ni6602_buff')
                I0_data = I0_data.astype(float) * 1e-5
                I0_data = I0_data[:, :self.images_per_line]

        if self.dataSource in ('pil100k', 'merlin', 'pil1m'):
            print "loading diffraction data wq345trwq34..."
            path = os.path.split(os.path.abspath(self.fileName))[0]
            
            # set detector paths
            if self.dataSource == 'merlin':
                filename_pattern = 'scan_%04d_merlin_0000.hdf5'
                hdfpath_pattern = 'entry_0000/measurement/Merlin/data'
            elif self.dataSource == 'pil100k':
                filename_pattern = 'scan_%04d_pil100k_0000.hdf5'
                hdfpath_pattern = 'entry_%04d/measurement/Pilatus/data'
            elif self.dataSource == 'pil1m':
                filename_pattern = 'scan_%04d_pil1m_0000.hdf5'
                hdfpath_pattern = 'entry_%04d/measurement/Pilatus/data'

            data = []
            print "attempting to read hws_mesh"
                 
            fn = os.path.join(path, filename_pattern%self.scanNr)
            if not os.path.exists(fn): raise NoDataException('No hdf5 file found.')
            with h5py.File(fn, 'r') as hf:

                
                print 'loading data: all at once, debug here'
                dataset = self._safe_get_dataset(hf, hdfpath_pattern)
                data = np.array(dataset)
                data = np.flip(data,axis=1)

                print "loaded %d lines of diffraction data"%len(data)

#            data = np.concatenate(data, axis=0)

        elif self.dataSource == 'xspress3':
            print "loading fluorescence data..."
            print "selecting fluorescence channels %s"%self.xrfChannel
            path = os.path.split(os.path.abspath(self.fileName))[0]
            filename_pattern = 'scan_%04d_xspress3_0000.hdf5'
            print 'loading data: ' + filename_pattern%(self.scanNr)
            data = []
            fn = os.path.join(path, filename_pattern%(self.scanNr))
            if not os.path.exists(fn): raise NoDataException
            with h5py.File(fn, 'r') as hf:
                line = 0
                while True:
                    if line >= self.nlines:
                        break
                    dataset = self._safe_get_dataset(hf, 'entry_%04d/measurement/xspress3/data'%line)
                    if not dataset:
                        break
                    data_ = np.mean(np.array(dataset)[:, self.xrfChannel, :], axis=1)
                    if self.xrfCropping:
                        data_ = data_[:, self.xrfCropping[0]:self.xrfCropping[1]]
                    if self.normalize_by_I0:
                        I0_line = I0_data[line]
                        data_ = data_ / I0_line[:, None]
                    data.append(data_)
                    line += 1
            print "loaded %d lines of fluorescence data"%len(data)
            data = np.vstack(data)
            bad = np.where(np.isinf(data) | np.isnan(data))
            good = np.where(np.isfinite(data))
            data[bad] = np.mean(data[good])
            self.dataDimLabels[name] = ['Approx. energy (keV)']
            self.dataAxes[name] = [np.arange(data_.shape[-1]) * .01]

        elif self.dataSource in ('adlink', 'counter'):
            print "loading buffered scalar data..."
            channel = {'adlink': 'AdLinkAI_buff', 'counter': 'Ni6602_buff'}[self.dataSource]
            entry = 'entry%d' % self.scanNr
            if not os.path.exists(self.fileName): raise NoDataException
            with h5py.File(self.fileName, 'r') as hf:
                data = self._safe_get_array(hf, entry+'/measurement/%s'%channel)
                data = data.astype(float)
                data = data[:, :self.images_per_line]
                data = data.flatten()

        elif self.dataSource == 'pil1m-waxs':
            print "loading WAXS data..."
            if self.waxsPath[0] == '/':
                path = self.waxsPath
            else:
                sampledir = os.path.basename(os.path.dirname(os.path.abspath(self.fileName)))
                self.waxsPath = self.waxsPath.replace('<sampledir>', sampledir)
                path = os.path.abspath(os.path.join(os.path.dirname(self.fileName), self.waxsPath))
            fn = os.path.join(path, 'scan_%04d_pil1m_0000_waxs.hdf5' % self.scanNr)
            if not os.path.exists(fn): raise NoDataException
            with h5py.File(fn, 'r') as fp:
                data = fp['I'][:]
                q = fp['q'][:]
            self.dataAxes[name] = [q,]
            self.dataDimLabels[name] = ['q (1/nm)']
            if self.normalize_by_I0:
                data = data / I0_data.flatten()[:, None]
                bad = np.where(np.isinf(data) | np.isnan(data))
                good = np.where(np.isfinite(data))
                data[bad] = np.mean(data[good])
        else:
            raise RuntimeError('Something is seriously wrong, we should never end up here since _updateOpts checks the options.')
        return data
       
class stepscan_nov2018(Scan):
    """
    More mature stepscan format.
    """

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
        'dataSource': {
            'value': 'merlin',
            'type': ['merlin', 'xspress3', 'pil100k', 'pil1m', 'counter1', 'counter2', 'counter3', 'pil1m-waxs'],
            'doc': "type of data",
            },
        'xMotor': {
            'value': 'samx',
            'type': str,
            'doc': 'scanned motor to plot on the x axis',
            },
        'yMotor': {
            'value': 'samy',
            'type': str,
            'doc': 'scanned motor to plot on the y axis',
            },
        'xrfChannel': {
            'value': 3,
            'type': int,
            'doc': 'xspress3 channel from which to read XRF',
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
        'normalize_by_I0': {
            'value': False,
            'type': bool,
            'doc': 'whether to normalize against I0 (counter1)',
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
    sourceDims = {'pil100k':2, 'xspress3':1, 'merlin':2, 'pil1m':2, 'counter1':0, 'counter2':0, 'counter3':0, 'pil1m-waxs':1}
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
        self.dataSource = opts['dataSource']['value']
        self.xMotor = opts['xMotor']['value']
        self.yMotor = opts['yMotor']['value']
        self.xrfChannel = int(opts['xrfChannel']['value'])
        self.xrdCropping = int(opts['xrdCropping']['value'])
        self.xrdBinning = int(opts['xrdBinning']['value'])
        self.normalize_by_I0 = (opts['normalize_by_I0']['value'])
        self.nominalPositions = bool(opts['nominalPositions']['value'])
        self.scanNr = int(opts['scanNr']['value'])
        self.fileName = opts['fileName']['value']
        self.waxsPath = opts['waxsPath']['value']
        self.burstSum = opts['burstSum']['value']
        self.nMaxPositions = opts['nMaxPositions']['value']

    def _readPositions(self):
        """ 
        Override position reading.
        """

        if not os.path.exists(self.fileName): raise NoDataException
        with h5py.File(self.fileName, 'r') as hf:
            if self.nominalPositions:
                title = str(hf.get('entry%d' % self.scanNr + '/title')[()]).split(' ')
                xmotorInd = title.index(self.xMotor)
                ymotorInd = title.index(self.yMotor)
                x = np.linspace(float(title[xmotorInd+1]),
                                float(title[xmotorInd+2]),
                                int(title[xmotorInd+3]) + 1,
                                endpoint=True)
                y = np.linspace(float(title[ymotorInd+1]),
                                float(title[ymotorInd+2]),
                                int(title[ymotorInd+3]) + 1,
                                endpoint=True)
                nx = len(x)
                ny = len(y)
                if xmotorInd < ymotorInd:
                    # x is the fast motor
                    y = y.repeat(nx)
                    x = np.tile(x, ny)
                else:
                    # y is the fast motor
                    x = x.repeat(ny)
                    y = np.tile(y, nx)
            else:
                x = np.array(hf.get('entry%d' % self.scanNr + '/measurement/%s' % self.xMotor))
                y = np.array(hf.get('entry%d' % self.scanNr + '/measurement/%s' % self.yMotor))
            if self.nMaxPositions:
                x = x[:self.nMaxPositions]
                y = y[:self.nMaxPositions]
            if 'sams_' in self.xMotor:
                x *= 1000
            if 'sams_' in self.yMotor:
                y *= 1000
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
            entry = 'entry%d' % self.scanNr
            if not os.path.exists(self.fileName): raise NoDataException
            with h5py.File(self.fileName, 'r') as hf:
                I0_data = self._safe_get_array(hf, entry+'/measurement/counter1')
                I0_data = I0_data.astype(float) * 1e-5
                print I0_data

        if self.dataSource in ('merlin', 'pil100k', 'pil1m'):
            print "loading diffraction data..."
            path = os.path.split(os.path.abspath(self.fileName))[0]

            # set detector paths
            if self.dataSource == 'merlin':
                filename_pattern = 'scan_%04d_merlin_0000.hdf5'
                hdfpath_pattern = 'entry_%04d/measurement/Merlin/data'
            elif self.dataSource == 'pil100k':
                filename_pattern = 'scan_%04d_pil100k_0000.hdf5'
                hdfpath_pattern = 'entry_%04d/measurement/Pilatus/data'
            elif self.dataSource == 'pil1m':
                filename_pattern = 'scan_%04d_pil1m_0000.hdf5'
                hdfpath_pattern = 'entry_%04d/measurement/Pilatus/data'

            data = []
            ic = None; jc = None # center of mass
            missing = 0

            fn = os.path.join(path, filename_pattern%self.scanNr)
            if not os.path.exists(fn): raise NoDataException
            try:
                with h5py.File(fn, 'r') as hf:
                    print 'loading data: ' + os.path.join(path, filename_pattern%self.scanNr)
                    for im in range(self.positions.shape[0]):
                        if self.nMaxPositions and im == self.nMaxPositions:
                            break
                        dataset = self._safe_get_dataset(hf, hdfpath_pattern%im)
                        # for the first frame, determine center of mass
                        if ic is None or jc is None == 0:
                            import scipy.ndimage.measurements
                            img = np.array(dataset[0])
                            try:
                                ic, jc = map(int, scipy.ndimage.measurements.center_of_mass(img))
                            except ValueError:
                                ic = img.shape[0] / 2
                                jc = img.shape[1] / 2
                            print "Estimated center of mass to (%d, %d)"%(ic, jc)
                        if self.xrdCropping:
                            delta = self.xrdCropping / 2
                            if self.burstSum:
                                data_ = np.sum(np.array(dataset[:, ic-delta:ic+delta, jc-delta:jc+delta]), axis=0)
                            else:
                                data_ = np.array(dataset[0, ic-delta:ic+delta, jc-delta:jc+delta])
                        else:
                            if self.burstSum:
                                data_ = np.sum(np.array(dataset), axis=0)
                            else:
                                data_ = np.array(dataset[0])
                        if self.xrdBinning > 1:
                            data_ = fastBinPixels(data_, self.xrdBinning)
                        if 'Merlin' in hdfpath_pattern:
                            data_ = np.flipud(data_) # Merlin images indexed from the bottom left...
                        data.append(data_)
            except IOError:
                # missing files -- this is ok
                print "couldn't find expected file %s, filling with zeros"%(filename_pattern%(self.scanNr))
                data.append(np.zeros(data[-1].shape, dtype=data[-1].dtype))
                missing += 1
            print "loaded %d images"%len(data)
            if missing:
                print "there were %d missing images" % missing
            data = np.array(data)
            if self.normalize_by_I0:
                data = data / I0_data[:, None, None]

        elif self.dataSource == 'xspress3':
            print "loading fluorescence data..."
            print "selecting xspress3 channel %d"%self.xrfChannel
            path = os.path.split(os.path.abspath(self.fileName))[0]
            filename_pattern = 'scan_%04d_xspress3_0000.hdf5'
            print 'loading data: ' + filename_pattern%(self.scanNr)
            data = []
            fn = os.path.join(path, filename_pattern%(self.scanNr))
            if not os.path.exists(fn): raise NoDataException
            with h5py.File(fn, 'r') as hf:
                for im in range(self.positions.shape[0]):
                    dataset = self._safe_get_dataset(hf, 'entry_%04d/measurement/xspress3/data'%im)
                    if not dataset:
                        break
                    data.append(np.array(dataset)[0, self.xrfChannel])
            data = np.array(data)
            if self.normalize_by_I0:
                data = data / I0_data[:, None]
            self.dataDimLabels[name] = ['Approx. energy (keV)']
            self.dataAxes[name] = [np.arange(data.shape[-1]) * .01]

        elif self.dataSource == 'pil1m-waxs':
            print "loading WAXS data..."
            if self.waxsPath[0] == '/':
                path = self.waxsPath
            else:
                sampledir = os.path.basename(os.path.dirname(os.path.abspath(self.fileName)))
                self.waxsPath = self.waxsPath.replace('<sampledir>', sampledir)
                path = os.path.abspath(os.path.join(os.path.dirname(self.fileName), self.waxsPath))
            fn = os.path.join(path, 'scan_%04d_pil1m_0000_waxs.hdf5' % self.scanNr)
            if not os.path.exists(fn): raise NoDataException
            with h5py.File(fn, 'r') as fp:
                data = fp['I'][:]
                q = fp['q'][:]
            self.dataAxes[name] = [q,]
            self.dataDimLabels[name] = ['q (1/nm)']
            try:
                if self.normalize_by_I0:
                    data = data / I0_data[:, None]
            except:
                raise NotImplementedError('Something went wrong when normalizing the WAXS data!')

        elif self.dataSource in ('counter1', 'counter2', 'counter3'):
            entry = 'entry%d' % self.scanNr
            if not os.path.exists(self.fileName): raise NoDataException
            with h5py.File(self.fileName, 'r') as hf:
                I0_data = self._safe_get_array(hf, entry+'/measurement/' + self.dataSource)
                I0_data = I0_data.astype(float)
                data = I0_data.flatten()
        else:
            raise RuntimeError('Something is seriously wrong, we should never end up here since _updateOpts checks the options.')
        
        return data



