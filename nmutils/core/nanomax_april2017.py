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
        'detectorPreference': {
            'value': 'pil100k',
            'type': ['pil100k', 'pil1m', 'merlin', 'eiger1m-edf'],
            'doc': 'preferred XRD detector',
            },
        'nominalYPositions': {
            'value': False,
            'type': bool,
            'doc': 'use nominal rather than sampled y positions',
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
        self.steppedMotor = opts['steppedMotor']['value']
        self.xrfChannel = int(opts['xrfChannel']['value'])
        self.xrdCropping = map(int, opts['xrdCropping']['value'])
        self.xrdBinning = int(opts['xrdBinning']['value'])
        self.xrdNormalize = map(int, opts['xrdNormalize']['value'])
        self.nMaxLines = int(opts['nMaxLines']['value'])
        self.detPreference = opts['detectorPreference']['value']
        self.nominalYPositions = bool(opts['nominalYPositions']['value'])
        self.scanNr = int(opts['scanNr']['value'])
        self.fileName = opts['fileName']['value']

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
            if self.nominalYPositions:
                title = str(hf.get(entry + '/title').value).split(' ')
                yall = np.linspace(
                    float(title[2]),
                    float(title[3]),
                    int(title[4])+1,
                    endpoint=True)
            else:
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
            path = os.path.split(os.path.abspath(self.fileName))[0]

            # check which detector data are available:
            avail_dets = []
            if os.path.isfile(os.path.join(path, 'scan_%04d_merlin_%04d.hdf5'%(self.scanNr,0))):
                avail_dets.append('merlin')
                print "Merlin data available"                
            if os.path.isfile(os.path.join(path, 'scan_%04d_pil100k_%04d.hdf5'%(self.scanNr,0))):
                avail_dets.append('pil100k')
                print "100k data available"
            if os.path.isfile(os.path.join(path, 'scan_%04d_pil1m_%04d.hdf5'%(self.scanNr,0))):
                avail_dets.append('pil1m')
                print "1M data available"
            if os.path.isfile(os.path.join(path, 'scan_%04d_eiger1m_%04d.edf'%(self.scanNr,0))):
                avail_dets.append('eiger1m-edf')
                print "Eiger1M (edf) data available"
            if len(avail_dets) == 0:
                print "No XRD data available"
                return

            # default file format
            fileFormat = 'hdf'
            
            # check which detector was used
            if self.detPreference in avail_dets:
                chosen_det = self.detPreference
            else: 
                chosen_det = avail_dets[0]
            if chosen_det == 'merlin':
                filepattern = 'scan_%04d_merlin_%04d.hdf5'
                hdfDataPath = 'entry_0000/measurement/Merlin/data'
                print "Using Merlin XRD data"
            elif chosen_det == 'pil100k':
                filepattern = 'scan_%04d_pil100k_%04d.hdf5'
                hdfDataPath = 'entry_0000/measurement/Pilatus/data'
                print "Using Pilatus 100k data"
            elif chosen_det == 'pil1m':
                filepattern = 'scan_%04d_pil1m_%04d.hdf5'
                hdfDataPath = 'entry_0000/measurement/Pilatus/data'
                print "Using Pilatus 1M data"
            elif chosen_det == 'eiger1m-edf':
                filepattern = 'scan_%04d_eiger1m_%04d.edf'
                hdfDataPath = ''
                fileFormat = 'edf'
                print "Using Eiger 1M (edf) data"
            else:
                print "Something went really wrong in detector choice"
                return

            data = []
            print "attempting to read %d lines of diffraction data (based on the positions array or max number of lines set)"%self.nlines
            for line in range(self.nlines):
                try:
                    if fileFormat == 'hdf':
                        data.append(self._readLineXrdDataHdf5(line,path,filepattern,hdfDataPath))
                    elif fileFormat == 'edf':
                        data.append(self._readLineXrdDataEdf(line,path,filepattern))
                    else:
                        raise Exception("Unknown file-format: %s" % (fileformat,))
                except IOError:
                    # fewer hdf5 files than positions -- this is ok
                    print "couldn't find expected file %s, returning"%(filepattern%(self.scanNr, line))
                    break

            print "loaded %d lines of diffraction data"%len(data)
            data = np.concatenate(data, axis=0)

        elif self.dataType == 'xrf':
            print "loading flurescence data..."
            print "selecting fluorescence channel %d"%self.xrfChannel
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
            print "loaded %d lines of flurescence data"%len(data)
            data = np.vstack(data)
        else:
            raise RuntimeError('unknown datatype specified (should be ''xrd'' or ''xrf''')
        return data

    def _readLineXrdDataHdf5(self,line,path,filepattern,hdfDataPath):
        data_ = []
        with h5py.File(os.path.join(path, filepattern%(self.scanNr, line)), 'r') as hf:
            print 'loading data: ' + filepattern%(self.scanNr, line)
            dataset = hf.get(hdfDataPath)
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
            if self.xrdNormalize:
                i0, i1, j0, j1 = self.xrdNormalize
                data_ = np.array(data_, dtype=float)
                for i in range(data_.shape[0]):
                    norm = float(np.sum(np.array(dataset[i, i0 : i1, j0 : j1])))
                    data_[i] /= norm
            if 'Merlin' in hdfDataPath:
                for i in range(data_.shape[0]):
                    data_[i] = np.flipud(data_[i]) # Merlin images indexed from the bottom left...
            del dataset
        return data_

    def _readLineXrdDataEdf(self,line,path,filepattern):
        import fabio
        data_ = []
        print 'loading data: ' + filepattern%(self.scanNr, line)
        imgf = fabio.open(os.path.join(path, filepattern%(self.scanNr, line)))
        dtp = np.int32 # imgf.data.dtype
        if self.xrdCropping:
            i0, i1, j0, j1 = self.xrdCropping
            data_ = np.ndarray((imgf.nframes,i1-i0,j1-j0),dtp)
            for iframe in range(imgf.nframes):
                data_[iframe] = imgf.data[i0 : i1, j0 : j1]
                imgf.next()
        else:
            data_ = np.ndarray((imgf.nframes,)+imgf.data.shape,dtp)
            for iframe in range(imgf.nframes):
                data_[iframe] = imgf.data
                imgf.next()
        if self.xrdBinning > 1:
            shape = fastBinPixels(data_[0], self.xrdBinning).shape
            new_data_ = np.zeros((data_.shape[0],) + shape)
            for ii in range(data_.shape[0]):
                new_data_[ii] = fastBinPixels(data_[ii], self.xrdBinning)
            data_ = new_data_
        if self.xrdNormalize:
            i0, i1, j0, j1 = self.xrdNormalize
            data_ = np.array(data_, dtype=float)
            imgf.getframe(0)
            for i in range(data_.shape[0]):
                norm = float(np.sum(np.array(imgf.data[i, i0 : i1, j0 : j1])))
                data_[i] /= norm
                imgf.next()
        return data_
        
class nanomaxScan_stepscan_april2017(Scan):
    # Class representing April 2017, with the beamline still temporarily
    # set up for commissioning and user runs.

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
        'xrdNormalize': {
            'value': False,
            'type': bool,
            'doc': 'normalize XRD images by total intensity',
            },
        'detectorPreference': {
            'value': 'pil100k',
            'type': ['pil100k', 'pil1m', 'merlin', 'eiger1m-edf'],
            'doc': 'preferred XRD detector',
            },
        'nominalPositions': {
            'value': False,
            'type': bool,
            'doc': 'use nominal instead of recorded positions',
            },
        'maxPositions': {
            'value': 0,
            'type': int,
            'doc': 'max number of measurements to load, introduced to duck some corrupt data'
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
        self.xrfChannel = int(opts['xrfChannel']['value'])
        self.xrdCropping = int(opts['xrdCropping']['value'])
        self.xrdBinning = int(opts['xrdBinning']['value'])
        self.xrdNormalize = bool(opts['xrdNormalize']['value'])
        self.detPreference = opts['detectorPreference']['value']
        self.nominalPositions = bool(opts['nominalPositions']['value'])
        self.scanNr = int(opts['scanNr']['value'])
        self.fileName = opts['fileName']['value']
        self.maxPositions = opts['maxPositions']['value']

    def _readPositions(self):
        """ 
        Override position reading.
        """

        with h5py.File(self.fileName, 'r') as hf:
            if self.nominalPositions:
                title = str(hf.get('entry%d' % self.scanNr + '/title').value).split(' ')
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
                if self.maxPositions:
                    x = x[:self.maxPositions]
                    y = y[:self.maxPositions]
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
            elif self.maxPositions:
                x = hf['entry%d' % self.scanNr + '/measurement/%s' % self.xMotor][:self.maxPositions]
                y = hf['entry%d' % self.scanNr + '/measurement/%s' % self.yMotor][:self.maxPositions]
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

        return np.vstack((x, y)).T

    def _readData(self):
        """ 
        Override data reading. Here the filename is only used to find the
        path of the Lima hdf5 files.
        """

        if self.dataType == 'xrd':
            print "loading diffraction data..."
            path = os.path.split(os.path.abspath(self.fileName))[0]

            # check which detector data are available:
            avail_dets = []
            if os.path.isfile(os.path.join(path, 'scan_%04d_merlin_%04d.hdf5'%(self.scanNr,0))):
                avail_dets.append('merlin')
                print "Merlin data available"                
            if os.path.isfile(os.path.join(path, 'scan_%04d_pil100k_%04d.hdf5'%(self.scanNr,0))):
                avail_dets.append('pil100k')
                print "100k data available"
            if os.path.isfile(os.path.join(path, 'scan_%04d_pil1m_%04d.hdf5'%(self.scanNr,0))):
                avail_dets.append('pil1m')
                print "1M data available"
            if os.path.isfile(os.path.join(path, 'scan_%04d_eiger1m_%04d.edf'%(self.scanNr,0))):
                avail_dets.append('eiger1m-edf')
                print "Eiger1M (edf) data available"
            if len(avail_dets) == 0:
                print "No XRD data available"
                return

            # default file format
            fileFormat = 'hdf'

            # check which detector was used
            if self.detPreference in avail_dets:
                chosen_det = self.detPreference
            else: 
                chosen_det = avail_dets[0]
            if chosen_det == 'merlin':
                filepattern = 'scan_%04d_merlin_%04d.hdf5'
                hdfDataPath = 'entry_0000/measurement/Merlin/data'
                print "Using Merlin XRD data"
            elif chosen_det == 'pil100k':
                filepattern = 'scan_%04d_pil100k_%04d.hdf5'
                hdfDataPath = 'entry_0000/measurement/Pilatus/data'
                print "Using Pilatus 100k data"
            elif chosen_det == 'pil1m':
                filepattern = 'scan_%04d_pil1m_%04d.hdf5'
                hdfDataPath = 'entry_0000/measurement/Pilatus/data'
                print "Using Pilatus 1M data"
            elif chosen_det == 'eiger1m-edf':
                filepattern = 'scan_%04d_eiger1m_%04d.edf'
                hdfDataPath = ''
                fileFormat = 'edf'
                print "Using Eiger 1M (edf) data"
            else:
                print "Something went really wrong in detector choice"
                return

            data = []
            ic = None; jc = None # center of mass
            missing = 0
            for im in range(self.positions.shape[0]):
                try:
                    if fileFormat == 'hdf':
                        data_, ic, jc = self._readLineXrdDataHdf5(im,path,filepattern,hdfDataPath,ic,jc)
                        data.append(data_)
                    elif fileFormat == 'edf':
                        data_, ic, jc = self._readLineXrdDataEdf(im,path,filepattern,ic,jc) 
                        data.append(data_)
                    else:
                        raise Exception("Unknown file-format: %s" % (fileformat,))
                except IOError:
                    # missing files -- this is ok
                    print "couldn't find expected file %s, filling with zeros"%(filepattern%(self.scanNr, im))
                    data.append(np.zeros(data[-1].shape, dtype=data[-1].dtype))
                    missing += 1
            print "loaded %d images"%len(data)
            if missing:
                print "there were %d missing images" % missing
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

    def _readLineXrdDataHdf5(self,im,path,filepattern,hdfDataPath,ic=None,jc=None):
        data_ = []
        with h5py.File(os.path.join(path, filepattern%(self.scanNr, im)), 'r') as hf:
            print 'loading data: ' + filepattern%(self.scanNr, im)
            dataset = hf.get(hdfDataPath)
            # for the first file, determine center of mass
            if ic is None or jc is None == 0:
                import scipy.ndimage.measurements
                img = np.array(dataset[0])
                ic, jc = map(int, scipy.ndimage.measurements.center_of_mass(img))
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
        return data_, ic, jc

    def _readLineXrdDataEdf(self,im,path,filepattern,ic=None,jc=None):
        import fabio
        data_ = []
        print 'loading data: ' + filepattern%(self.scanNr, im)
        imgf = fabio.open(os.path.join(path, filepattern%(self.scanNr, im)))
        # for the first file, determine center of mass
        if ic is None or jc is None == 0:
            import scipy.ndimage.measurements
            ##img = np.ndarray(sz,dtype)
            img = np.array(imgf.data)
            ic, jc = map(int, scipy.ndimage.measurements.center_of_mass(img))
            print "Estimated center of mass to (%d, %d)"%(ic, jc)
        if self.xrdCropping:
            delta = self.xrdCropping / 2
            data_ = np.array(imgf.data[ic-delta:ic+delta, jc-delta:jc+delta])
        else:
            data_ = np.array(imgf.data)
        if self.xrdBinning > 1:
            data_ = fastBinPixels(data_, self.xrdBinning)
        if self.xrdNormalize:
            data_ = np.array(data_, dtype=float) / np.sum(self.xrdNormalize)
        return data_, ic, jc
