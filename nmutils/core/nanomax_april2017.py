from Scan import Scan
from ..utils import fastBinPixels
import numpy as np
import h5py
import copy as cp
import os.path

class nanomaxScan_flyscan_april2017(Scan):
    # Class representing April 2017, with fly-scanning still set up
    # in a temporary way. 

    default_opts = {
        # the dataType option is mandatory for use with scanViewer
        'dataType': {
            'value': 'xrd',
            'type': str,
            'doc': "type of data, 'xrd' or 'xrf'",
            },
        'steppedMotor': {
            'value': 'samy',
            'type': str,
            'doc': 'the second motor, stepped for each flyscan line',
            },
        'xrfChannel': {
            'value': 2,
            'type': int,
            'doc': 'xspress3 channel from which to read XRF',
            },
        'xrdCropping': {
            'value': 'none',
            'type': str,
            'doc': 'detector area to load, "i0 i1 j0 j1" - none means load all',
            },
        'xrdBinning': {
            'value': 1,
            'type': int,
            'doc': 'bin xrd pixels n-by-n (after cropping)',
            },
        'xrdNormalize': {
            'value': 'none',
            'type': str,
            'doc': 'normalize XRD images by average over the ROI "i0 i1 j0 j1"',
            },
        'nMaxLines': {
            'value': 0,
            'type': int,
            'doc': 'load at most N lines - 0 means load all',
            },
    }

    def _prepareData(self, **kwargs):
        """ 
        This method gets the kwargs passed to the addData() method, and
        stores them for use during this data loading.
        """
        # copy defaults, then update with kwarg options
        opts = self.default_opts.copy()
        opts = self._updateOpts(opts, **kwargs)
        
        # parse options
        self.dataType = opts['dataType']['value']
        self.steppedMotor = opts['steppedMotor']['value']
        self.xrfChannel = int(opts['xrfChannel']['value'])
        if len(opts['xrdCropping']['value'].split()) == 4:
            self.xrdCropping = map(int, opts['xrdCropping']['value'].split())
        else:
            self.xrdCropping = False
        self.xrdBinning = int(opts['xrdBinning']['value'])
        if len(opts['xrdNormalize']['value'].split()) == 4:
            self.xrdNormalize = map(int, opts['xrdNormalize']['value'].split())
        else:
            self.xrdNormalize = False
        self.nMaxLines = int(opts['nMaxLines']['value'])

    def _readPositions(self):
        """ 
        Override position reading.
        """
        
        skipX = 0
        entry = 'entry%d' % self.scanNr
        fileName = self.fileName

        x, y = None, None
        with h5py.File(fileName, 'r') as hf:
            # get fast x positions
            xdataset = hf.get(entry + '/measurement/AdLinkAI_buff')
            xall = np.array(xdataset)
            # manually find shape by looking for zeros
            Ny = xall.shape[0]
            if skipX > 0:
                print "Skipping %d position(s) at the end of each line"%skipX
            for i in range(xall.shape[1]):
                if xall[0,i+skipX] == 0:
                    Nx = i
                    break
            x = xall[:, :Nx].flatten()

            # get slow y positions
            ydataset = hf.get(entry + '/measurement/%s' % self.steppedMotor)
            yall = np.array(ydataset)
            if not (len(yall) == Ny): raise Exception('Something''s wrong with the positions')
            y = np.repeat(yall, Nx)

            # save number of lines for the _readData method
            self.nlines = Ny

            if self.nMaxLines:
                self.nlines = self.nMaxLines
                x = x[:Nx * self.nMaxLines]
                y = y[:Nx * self.nMaxLines]
                print "x and y shapes:", x.shape, y.shape

            print "loaded positions from %d lines, %d positions on each"%(self.nlines, Nx)

        return np.vstack((x, y)).T

    def _readData(self):
        """ 
        Override data reading.
        """

        if self.dataType == 'xrd':
            print "loading diffraction data..."
            print "selecting fluorescence channel %d"%self.xrfChannel
            path = os.path.split(os.path.abspath(self.fileName))[0]
            # check which detector was used
            if os.path.isfile(os.path.join(path, 'scan_%04d_pil100k_%04d.hdf5'%(self.scanNr, 0))):
                filepattern = 'scan_%04d_pil100k_%04d.hdf5'
                print "This is a Pilatus 100k scan"
            elif os.path.isfile(os.path.join(path, 'scan_%04d_pil1m_%04d.hdf5'%(self.scanNr, 0))):
                filepattern = 'scan_%04d_pil1m_%04d.hdf5'
                print "This is a Pilatus 1M scan"
            else:
                print "No 1M or 100k data found."
                return

            data = []
            print "attempting to read %d lines of diffraction data (based on the positions array or max number of lines set)"%self.nlines
            for line in range(self.nlines):
                try:
                    with h5py.File(os.path.join(path, filepattern%(self.scanNr, line)), 'r') as hf:
                        print 'loading data: ' + filepattern%(self.scanNr, line)
                        dataset = hf.get('entry_0000/measurement/Pilatus/data')
                        if isinstance(self.xrdCropping, list):
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
                        if isinstance(self.xrdNormalize, list):
                            i0, i1, j0, j1 = self.xrdNormalize
                            data_ = np.array(data_, dtype=float)
                            for i in range(data_.shape[0]):
                                norm = float(np.sum(np.array(dataset[i, i0 : i1, j0 : j1])))
                                data_[i] /= norm
                        data.append(data_)
                        del dataset
                except IOError:
                    # fewer hdf5 files than positions -- this is ok
                    print "couldn't find expected file %s, returning"%(filepattern%(self.scanNr, line))
                    break

            print "loaded %d lines of Pilatus data"%len(data)
            data = np.concatenate(data, axis=0)

        elif self.dataType == 'xrf':
            print "loading flurescence data..."
            path = os.path.split(os.path.abspath(self.fileName))[0]
            filepattern = 'scan_%04d_xspress3_0000.hdf5'
            print 'loading data: ' + filepattern%(self.scanNr)
            data = []
            with h5py.File(os.path.join(path, filepattern%(self.scanNr)), 'r') as hf:
                line = 0
                while True:
                    if line >= self.nlines:
                        break
                    dataset = hf.get('entry_%04d/measurement/xspress3/data'%line)
                    if not dataset:
                        break
                    data.append(np.array(dataset)[:, self.xrfChannel, :])
                    line += 1
            print "loaded %d lines of xspress3 data"%len(data)
            data = np.vstack(data)
        else:
            raise RuntimeError('unknown datatype specified (should be ''xrd'' or ''xrf''')
        return data


class nanomaxScan_stepscan_april2017(Scan):
    # Class representing April 2017, with the beamline still temporarily
    # set up for commissioning and user runs.

    default_opts = {
        # the dataType option is mandatory for use with scanViewer
        'dataType': {
            'value': 'xrd',
            'type': str,
            'doc': "type of data, 'xrd' or 'xrf'",
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
            'value': 2,
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
        'xrdNormalize': {
            'value': False,
            'type': bool,
            'doc': 'normalize XRD images by total intensity',
            },
    }

    def _prepareData(self, **kwargs):
        """ 
        This method gets the kwargs passed to the addData() method, and
        stores them for use during this data loading.
        """
        # copy defaults, then update with kwarg options
        opts = self.default_opts.copy()
        opts = self._updateOpts(opts, **kwargs)
        
        # parse options
        self.dataType = opts['dataType']['value']
        self.xMotor = opts['xMotor']['value']
        self.yMotor = opts['yMotor']['value']
        self.xrfChannel = int(opts['xrfChannel']['value'])
        self.xrdCropping = int(opts['xrdCropping']['value'])
        self.xrdBinning = int(opts['xrdBinning']['value'])
        self.xrdNormalize = bool(opts['xrdNormalize']['value'])

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
            print "loading diffraction data..."
            path = os.path.split(os.path.abspath(self.fileName))[0]
            # check which detector was used
            if os.path.isfile(os.path.join(path, 'scan_%04d_merlin_%04d.hdf5'%(self.scanNr,0))):
                filepattern = 'scan_%04d_merlin_%04d.hdf5'
                hdfDataPath = 'entry_0000/measurement/Merlin/data'
                print "This is a Merlin scan"                
            elif os.path.isfile(os.path.join(path, 'scan_%04d_pil100k_%04d.hdf5'%(self.scanNr,0))):
                filepattern = 'scan_%04d_pil100k_%04d.hdf5'
                hdfDataPath = 'entry_0000/measurement/Pilatus/data'
                print "This is a Pilatus 100k scan"
            elif os.path.isfile(os.path.join(path, 'scan_%04d_pil1m_%04d.hdf5'%(self.scanNr,0))):
                filepattern = 'scan_%04d_pil1m_%04d.hdf5'
                hdfDataPath = 'entry_0000/measurement/Pilatus/data'
                print "This is a Pilatus 1M scan"
            else:
                print "No 1M or 100k data found."
                return

            data = []
            for im in range(self.positions.shape[0]):
                try:
                    with h5py.File(os.path.join(path, filepattern%(self.scanNr, im)), 'r') as hf:
                        print 'loading data: ' + filepattern%(self.scanNr, im)
                        dataset = hf.get(hdfDataPath)
                        # for the first file, determine center of mass
                        if len(data) == 0:
                            import scipy.ndimage.measurements
                            im = np.array(dataset[0])
                            ic, jc = map(int, scipy.ndimage.measurements.center_of_mass(im))
                            print "Estimated center of mass to (%d, %d)"%(ic, jc)
                        if self.xrdCropping:
                            delta = self.xrdCropping / 2
                            data_ = np.array(dataset[0, ic-delta:ic+delta, jc-delta:jc+delta])
                        else:
                            data_ = np.array(dataset[0])
                        if self.xrdBinning > 1:
                            data_ = fastBinPixels(data_, self.xrdBinning)
                        if self.xrdNormalize:
                            data_ = np.array(data_, dtype=float) / np.sum(self.xrdNormalize)
                        if 'Merlin' in hdfDataPath: 
                            data_ = np.flipud(data_) # Merlin images indexed from the bottom left...
                        data.append(data_)
                except IOError:
                    # missing files -- this is ok
                    print "couldn't find expected file %s, returning"%(filepattern%(self.scanNr, im))
                    break
            print "loaded %d images"%len(data)
            data = np.array(data)

        elif self.dataType == 'xrf':
            print "loading flurescence data..."
            print "selecting fluorescence channel %d"%self.xrfChannel
            path = os.path.split(os.path.abspath(self.fileName))[0]
            filepattern = 'scan_%04d_xspress3_0000.hdf5'
            print 'loading data: ' + filepattern%(self.scanNr)
            data = []
            with h5py.File(os.path.join(path, filepattern%(self.scanNr)), 'r') as hf:
                for im in range(self.positions.shape[0]):
                    dataset = hf.get('entry_%04d/measurement/xspress3/data'%im)
                    if not dataset:
                        break
                    data.append(np.array(dataset)[0, self.xrfChannel])
            data = np.array(data)

        else:
            raise RuntimeError('unknown datatype specified (should be ''xrd'' or ''xrf''')

        return data
