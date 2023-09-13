from . import Scan
from ..utils import fastBinPixels
from .. import NoDataException
import numpy as np
import h5py
import copy as cp
import os.path

class contrast_scan(Scan):
    """
    General format for Contrast at NanoMAX.
    """

    alba_names = ['alba%u/%u'%(i,j) for i in (2,0) for j in (1,2,3,4)]
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
            'type': ['eiger1m', 'eiger500k', 'eiger4m', 'eiger(old)', 'merlin', 'pilatus', 'pilatus1m', 'andor','cake', 'xspress3', 'x3mini', 'waxs'] + alba_names + ['ni/counter1', 'ni/counter2', 'ni/counter3', 'adlink', 'pseudo/xbic'],
            'doc': "type of data",
            },
        'xspress3Channels': {
            'value': [3,],
            'type': list,
            'doc': 'xspress3 channels from which to read XRF',
            },
        'x3miniChannels': {
            'value': [0,],
            'type': list,
            'doc': 'x3mini channels from which to read XRF',
            },
        'xrfCropping': {
            'value': [],
            'type': list,
            'doc': 'XRF detector range to load, [i0, i1]',
            },
        'xrdCropping': {
            'value': [],
            'type': list,
            'doc': 'detector area to load, [i0, i1, j0, j1]',
            },
        'xrdBinning': {
            'value': 1,
            'type': int,
            'doc': 'bin pixels n by n (disables cropping)',
            },
        'I0': {
            'value': '',
            'type': str,
            'doc': 'channel over which to normalize signals, eg "alba2/1"',
            },
        'waxsPath': {
            'value': '../../process/azint/<sampledir>',
            'type': str,
            'doc': 'path to waxs data, absolute or relative to h5 folder, <sampledir> is replaced',
        },
        'xMotor': {
            'value': 'pseudo/x',
            'type': str,
            'doc': 'scanned motor to plot on the x axis',
            },
        'yMotor': {
            'value': 'pseudo/y',
            'type': str,
            'doc': 'scanned motor to plot on the y axis',
            },
        'nMaxPositions': {
            'value': 0,
            'type': int,
            'doc': 'maximum number of positions to read (0 means all)',
        },
        'globalPositions': {
            'value': False,
            'type': bool,
            'doc': 'adds base motor values to piezo positions',
        },
        'cake_downsample': {
            'value': 1,
            'type': int,
            'doc': 'how to downsample cake data to save memory (1 for no binning)',
        },
    }

    # an optional class attribute which lets scanViewer know what
    # dataSource options have what dimensionalities. Good for the GUI.
    sourceDims = {'eiger(old)':2, 'eiger500k':2, 'eiger1m':2, 'eiger4m':2, 'pilatus':2, 'xspress3':1, 'x3mini':1, 'merlin':2, 'pilatus1m':2, 'ni/counter1':0, 'ni/counter2':0, 'ni/counter3':0, 'waxs':1, 'adlink':0, 'pseudo/xbic':0, 'andor':2, 'cake':2}
    albaDims = {name:0 for name in alba_names}
    sourceDims.update(albaDims)
    assert sorted(sourceDims.keys()) == sorted(default_opts['dataSource']['type'])

    def _prepareData(self, **kwargs):
        """ 
        This method gets the kwargs passed to the addData() method, and
        stores them for use during this data loading.
        """
        # the base class method parses everything
        super()._prepareData(**kwargs)

        # just join the path and filename
        if self.path.endswith('h5'):
            self.path = os.path.dirname(self.path)
        self.fileName = os.path.join(self.path, '%06u.h5'%self.scanNr)

    def find_snapshot_path(self):
        """
        added to be backwards compatible, as snapshots inside the scan file 
        could be in
            entry/snapshot               # old
            entry/snapshots/pre_scan     # new possibility 1
            entry/snapshots/pre_scan     # new possibility 2
        """
        path_options = ['entry/snapshot/',
                        'entry/snapshots/pre_scan/',
                        'entry/snapshots/prost_scan/']
        with h5py.File(self.fileName, 'r') as F:
            existing_paths = [x for x in path_options if x in F.keys()]
        if existing_paths==[]:
            print('[!] no snapshot found in scan file')
            self.snapshot_path = ''
        else:
            self.snapshot_path = existing_paths[0]

    def _readPositions(self):
        """ 
        Override position reading. Should return N by 2 array [x, y].
        """

        if not os.path.exists(self.fileName):
            print('File not found! \n    ', self.fileName)
            raise NoDataException(self.fileName)
        with h5py.File(self.fileName, 'r') as fp:
            # replace sx, sy, sz by buffered positions
            if 'entry/measurement/npoint_buff' in fp:
                mapping = {'s%s'%dim: 'npoint_buff/%s'%dim for dim in 'xyz'}
                if self.xMotor in mapping.keys():
                    self.xMotor = mapping[self.xMotor]
                if self.yMotor in mapping.keys():
                    self.yMotor = mapping[self.yMotor]

            if self.globalPositions:
                xyz = ['npoint_buff/%s'%dim for dim in 'xyz'] + ['pseudo/%s'%dim for dim in 'xyz'] + ['s%s'%dim for dim in 'xyz']
                xbase, ybase = 0, 0
                self.find_snapshot_path()
                if self.xMotor in xyz:
                    xbase = fp[f'{self.snapshot_path}/base{self.xMotor[-1]}'][:]
                if self.yMotor in xyz:
                    ybase = fp[f'{self.snapshot_path}/base{self.yMotor[-1]}'][:]

            # read the positions
            self.find_snapshot_path()
            xkey = 'entry/measurement/%s' % self.xMotor
            xsnapkey = f'{self.snapshot_path}/{self.xMotor}' 
            if xkey in fp:
                x = fp[xkey][:]
            elif xsnapkey in fp:
                print('%s not found in measurement, using snapshot value' % self.xMotor)
                x = fp[xsnapkey][:]
            else:
                msg = 'Cannot find any positions for motor %s' % self.xMotor
                print(msg)
                raise NoDataException(msg)
                
            ykey = 'entry/measurement/%s' % self.yMotor
            ysnapkey = f'{self.snapshot_path}/{self.yMotor}' 
            if ykey in fp:
                y = fp[ykey][:]
            elif ysnapkey in fp:
                print('%s not found in measurement, using snapshot value' % self.yMotor)
                y = fp[ysnapkey][:]
            else:
                msg = 'Cannot find any positions for motor %s' % self.yMotor
                print(msg)
                raise NoDataException(msg)

        # sometimes flyscans are done with non-buffered slow motors,
        # or a 1d scan is done with a snapshot motor on the second axis.
        if len(x) < len(y):
            x = np.repeat(x, len(y) // len(x))
        if len(x) > len(y):
            y = np.repeat(y, len(x) // len(y))

        # limit the number of positions
        self.nAvailablePositions = len(x)
        if self.nMaxPositions:
            x = x[:self.nMaxPositions]
            y = y[:self.nMaxPositions]

        # optionally add add base motor positions
        if self.globalPositions:
            x[:] = x + xbase
            y[:] = y + ybase

        # save motor labels
        self.positionDimLabels = [self.xMotor, self.yMotor]

        print('loaded %u positions'%x.shape)
        return np.vstack((x, y)).T

    def _readData(self, name):
        """ 
        Override data reading. In principle these are the same for
        all data sources (except WAXS), it's just that there are
        some detector-specific cropping and channel options to respect.
        """

        if self.I0:
            with h5py.File(self.fileName, 'r') as fp:
                try:
                    I0_data = fp['entry/measurement/%s' % self.I0][:].flatten()
                except KeyError:
                    print('I0 data %s not found'%self.I0)
                    raise NoDataException()

        if self.dataSource in ('merlin', 'pilatus', 'pilatus1m', 'eiger(old)', 'eiger500k', 'eiger1m', 'eiger4m', 'andor'):
            print('loading %s data...' % self.dataSource)
            if self.dataSource == 'eiger(old)':
                self.dataSource = 'eiger' # legacy thing
            with h5py.File(self.fileName, 'r') as fp:
                try:
                    group = fp['entry/measurement/%s' % self.dataSource]
                except KeyError:
                    raise NoDataException()
                if 'frames' in group:
                    dset = group['frames']
                elif 'data' in group:
                    dset = group['data']
                else:
                    print('couldnt find %s'%self.dataSource)
                    raise NoDataException()

                # find out what to load
                if self.xrdCropping:
                    i0, i1, j0, j1 = self.xrdCropping
                else:
                    i0, i1 = 0, dset.shape[-2]
                    j0, j1 = 0, dset.shape[-1]                    

                # maybe there were detector bursts - then no need to allocate the whole thing
                im_per_pos = None
                if dset.shape[0] > self.nAvailablePositions:
                    nmax = self.nAvailablePositions
                    if self.nMaxPositions:
                        nmax = self.nMaxPositions
                    im_per_pos = dset.shape[0] // self.nAvailablePositions
                    print('more images than positions, assuming bursts of %u were made and summing these'%im_per_pos)
                    data = np.empty(dtype=dset.dtype, shape=(nmax, *dset.shape[1:]))
                    for i in range(nmax):
                        data[i] = np.sum(dset[i*im_per_pos:(i+1)*im_per_pos], axis=0)
                elif self.nMaxPositions:
                    data = dset[:self.nMaxPositions, i0:i1, j0:j1]
                elif self.xrdBinning == 1:
                    data = dset[:, i0:i1, j0:j1]
                else:
                    shape = fastBinPixels(dset[0], self.xrdBinning).shape
                    new_data_ = np.zeros((dset.shape[0],) + shape)
                    for ii in range(dset.shape[0]):
                        print('binning frame %u'%ii)
                        new_data_[ii] = fastBinPixels(dset[ii], self.xrdBinning)
                    data = new_data_

            if self.I0:
                data = data / I0_data[:, None, None]

        elif self.dataSource in ('xspress3', 'x3mini'):

            with h5py.File(self.fileName, 'r') as fp:
                try:
                    dset = fp['entry/measurement/%s/data' % self.dataSource]
                except KeyError:
                    try:
                        # maybe an old file from before the nxus format
                        dset = fp['entry/measurement/%s/frames' % self.dataSource]
                    except KeyError:
                        print('couldnt find %s'%self.dataSource)
                        raise NoDataException
                if self.xrfCropping:
                    i0, i1 = self.xrfCropping
                else:
                    i0, i1 = 0, dset.shape[-1]-10 # last bins annoying
                if self.dataSource == 'xspress3':
                    chans = self.xspress3Channels
                else:
                    chans = self.x3miniChannels
                data = np.sum(dset[:, chans, i0:i1], axis=1)

            if self.I0:
                print('****, %s, %s, %s'%(data.shape, I0_data.shape, I0_data[:, None].shape))
                data = data / I0_data[:, None]

            self.dataDimLabels[name] = ['Approx. energy (keV)']
            self.dataAxes[name] = [np.arange(data.shape[-1]) * .01]

        elif self.sourceDims[self.dataSource] == 0:
            with h5py.File(self.fileName, 'r') as fp:
                try:
                    data = fp['entry/measurement/%s' % self.dataSource][:]
                    print('#'*20)
                    print(f'did load {self.dataSource} ({np.shape(data)})')
                    data = data.flatten()
                except KeyError:
                    print('couldnt find %s'%self.dataSource)
                    raise NoDataException

            if self.I0:
                data = data / I0_data

        elif self.dataSource in ('waxs', 'cake'):
            if self.waxsPath[0] == '/':
                path = self.waxsPath
            else:
                sampledir = os.path.basename(os.path.dirname(os.path.abspath(self.fileName)))
                self.waxsPath = self.waxsPath.replace('<sampledir>', sampledir)
                path = os.path.abspath(os.path.join(os.path.dirname(self.fileName), self.waxsPath))
            hint = '%06u'%self.scanNr
            files = os.listdir(path)
            matches = [f for f in files if hint in f]
            try:
                waxsfn = matches[0]
            except:
                print('no waxs file matching %s found at %s'%(hint, path))
            waxs_file = os.path.join(path, waxsfn)
            print('loading %s data from %s' % (self.dataSource, waxs_file))
            if not os.path.exists(waxs_file):
                raise NoDataException('%s doesnt exist!'%waxs_file)
            nmax = self.nAvailablePositions
            if self.nMaxPositions:
                nmax = self.nMaxPositions
            with h5py.File(waxs_file, 'r') as fp:
                q = fp['q'][:]
                if self.dataSource == 'cake':
                    if 'phi' in fp:
                        phi = fp['phi'][:nmax]
                    elif 'azi' in fp:
                        phi = fp['azi'][:nmax]
                    else:
                        raise NoDataException(f'azimuthal bins do not exist in {waxs_file}')
                dset = fp['I']
                if self.cake_downsample == 1:
                    data = dset[:nmax]
                else:
                    shape = fastBinPixels(dset[0], self.cake_downsample).shape
                    new_data_ = np.zeros((nmax,) + shape)
                    for ii in range(nmax):
                        new_data_[ii] = fastBinPixels(dset[ii], self.cake_downsample)
                        print('downsampling cake frame %u'%ii)
                    data = new_data_

            if self.I0:
                print('****, %s, %s, %s'%(data.shape, I0_data.shape, I0_data[:, None].shape))
                data = data / I0_data[:, None]
            if self.dataSource == 'waxs':
                self.dataAxes[name] = [q,]
                self.dataDimLabels[name] = ['q (1/nm)']
            elif self.dataSource == 'cake':
                self.dataAxes[name] = [phi, q]
                self.dataDimLabels[name] = ['phi (rad.)', 'q (1/nm)']

        else:
            raise RuntimeError('Something is seriously wrong, we should never end up here since _updateOpts checks the options.')
        
        return data
