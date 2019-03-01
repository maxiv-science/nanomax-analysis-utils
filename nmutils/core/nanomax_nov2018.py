from Scan import Scan
from ..utils import fastBinPixels
import numpy as np
import h5py
import copy as cp
import os.path
from nanomax_nov2017 import nanomaxScan_flyscan_nov2017

class flyscan_nov2018(nanomaxScan_flyscan_nov2017):
    """
    More mature fly scan format.
    """

    default_opts = cp.deepcopy(nanomaxScan_flyscan_nov2017.default_opts)
    default_opts['normalize_by_I0'] = {
            'value': False,
            'type': bool,
            'doc': 'whether or not to normalize against I0',
            }
    default_opts['xrfChannel'] = {
            'value': [3,],
            'type': list,
            'doc': 'xspress3 channels from which to read XRF, averaged',
            }

    def _prepareData(self, **kwargs):
        """ 
        Parse the derived options
        """
        # copy defaults, then update with kwarg options
        super(flyscan_nov2018, self)._prepareData(**kwargs)
        opts = cp.deepcopy(self.default_opts)
        opts = self._updateOpts(opts, **kwargs)
        self.normalize_by_I0 = opts['normalize_by_I0']['value']
        self.xrfChannel = map(int, opts['xrfChannel']['value'])

    def _readData(self):
        """ 
        Override data reading.
        """

        if self.normalize_by_I0:
            entry = 'entry%d' % self.scanNr
            with h5py.File(self.fileName, 'r') as hf:
                I0_data = np.array(hf[entry+'/measurement/Ni6602_buff'])
                I0_data = I0_data.astype(float) * 1e-5
                I0_data = I0_data[:, :self.images_per_line]

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
            if len(avail_dets) == 0:
                print "No XRD data available"
                return
            
            # check which detector was used
            if self.detPreference in avail_dets:
                chosen_det = self.detPreference
            else: 
                chosen_det = avail_dets[0]
            if chosen_det == 'merlin':
                filename_pattern = 'scan_%04d_merlin_0000.hdf5'
                hdfpath_pattern = 'entry_%04d/measurement/Merlin/data'
                print "Using Merlin XRD data"
            elif chosen_det == 'pil100k':
                filename_pattern = 'scan_%04d_pil100k_0000.hdf5'
                hdfpath_pattern = 'entry_%04d/measurement/Pilatus/data'
                print "Using Pilatus 100k data"
            elif chosen_det == 'pil1m':
                filename_pattern = 'scan_%04d_pil1m_0000.hdf5'
                hdfpath_pattern = 'entry_%04d/measurement/Pilatus/data'
                print "Using Pilatus 1M data"
            else:
                print "Something went really wrong in detector choice"
                return

            data = []
            print "attempting to read %d lines of diffraction data (based on the positions array or max number of lines set)"%self.nlines
                    
            with h5py.File(os.path.join(path, filename_pattern%self.scanNr), 'r') as hf:
                for line in range(self.nlines):
                    try:
                        print 'loading data: ' + filename_pattern%self.scanNr + ', line %d'%line
                        dataset = hf.get(hdfpath_pattern%line)
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
                        if 'Merlin' in hdfpath_pattern:
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

        elif self.dataType == 'xrf':
            print "loading flurescence data..."
            print "selecting fluorescence channels %s"%self.xrfChannel
            path = os.path.split(os.path.abspath(self.fileName))[0]
            filename_pattern = 'scan_%04d_xspress3_0000.hdf5'
            print 'loading data: ' + filename_pattern%(self.scanNr)
            data = []
            with h5py.File(os.path.join(path, filename_pattern%(self.scanNr)), 'r') as hf:
                line = 0
                while True:
                    if line >= self.nlines:
                        break
                    dataset = hf.get('entry_%04d/measurement/xspress3/data'%line)
                    if not dataset:
                        break
                    data_ = np.mean(np.array(dataset)[:, self.xrfChannel, :], axis=1)
                    if self.normalize_by_I0:
                        I0_line = I0_data[line]
                        data_ = data_ / I0_line[:, None]
                    data.append(data_)
                    line += 1
            print "loaded %d lines of flurescence data"%len(data)
            data = np.vstack(data)

        elif self.dataType == 'I0':
            print "loading I0 data..."
            entry = 'entry%d' % self.scanNr
            with h5py.File(self.fileName, 'r') as hf:
                data = np.array(hf[entry+'/measurement/Ni6602_buff'])
                data = data.astype(float)
                data = data[:, :self.images_per_line]
                data = data.flatten()
        else:
            raise RuntimeError('unknown datatype specified (should be ''xrd'', ''xrf'' or ''I0''')
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
        'normalize_by_I0': {
            'value': False,
            'type': bool,
            'doc': 'whether to normalize against I0 (counter1)',
            },
        'detectorPreference': {
            'value': 'pil100k',
            'type': ['pil100k', 'pil1m', 'merlin'],
            'doc': 'preferred XRD detector',
            },
        'nominalPositions': {
            'value': False,
            'type': bool,
            'doc': 'use nominal instead of recorded positions',
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
        self.normalize_by_I0 = (opts['normalize_by_I0']['value'])
        self.detPreference = opts['detectorPreference']['value']
        self.nominalPositions = bool(opts['nominalPositions']['value'])
        self.scanNr = int(opts['scanNr']['value'])
        self.fileName = opts['fileName']['value']

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

        return np.vstack((x, y)).T

    def _readData(self):
        """ 
        Override data reading. Here the filename is only used to find the
        path of the Lima hdf5 files.
        """

        if self.normalize_by_I0:
            entry = 'entry%d' % self.scanNr
            with h5py.File(self.fileName, 'r') as hf:
                I0_data = np.array(hf[entry+'/measurement/counter1'])
                I0_data = I0_data.astype(float) * 1e-5
                print I0_data

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
            if len(avail_dets) == 0:
                print "No XRD data available"
                return

            # check which detector was used
            if self.detPreference in avail_dets:
                chosen_det = self.detPreference
            else: 
                chosen_det = avail_dets[0]
            if chosen_det == 'merlin':
                filename_pattern = 'scan_%04d_merlin_0000.hdf5'
                hdfpath_pattern = 'entry_%04d/measurement/Merlin/data'
                print "Using Merlin XRD data"
            elif chosen_det == 'pil100k':
                filename_pattern = 'scan_%04d_pil100k_0000.hdf5'
                hdfpath_pattern = 'entry_%04d/measurement/Pilatus/data'
                print "Using Pilatus 100k data"
            elif chosen_det == 'pil1m':
                filename_pattern = 'scan_%04d_pil1m_0000.hdf5'
                hdfpath_pattern = 'entry_%04d/measurement/Pilatus/data'
                print "Using Pilatus 1M data"
            else:
                print "Something went really wrong in detector choice"
                return

            data = []
            ic = None; jc = None # center of mass
            missing = 0

            try:
                with h5py.File(os.path.join(path, filename_pattern%self.scanNr), 'r') as hf:
                    print 'loading data: ' + os.path.join(path, filename_pattern%self.scanNr)
                    for im in range(self.positions.shape[0]):
                        dataset = hf.get(hdfpath_pattern%im)
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
                            data_ = np.array(dataset[0, ic-delta:ic+delta, jc-delta:jc+delta])
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

        elif self.dataType == 'xrf':
            print "loading flurescence data..."
            print "selecting fluorescence channel %d"%self.xrfChannel
            path = os.path.split(os.path.abspath(self.fileName))[0]
            filename_pattern = 'scan_%04d_xspress3_0000.hdf5'
            print 'loading data: ' + filename_pattern%(self.scanNr)
            data = []
            with h5py.File(os.path.join(path, filename_pattern%(self.scanNr)), 'r') as hf:
                for im in range(self.positions.shape[0]):
                    dataset = hf.get('entry_%04d/measurement/xspress3/data'%im)
                    if not dataset:
                        break
                    data.append(np.array(dataset)[0, self.xrfChannel])
            data = np.array(data)
            if self.normalize_by_I0:
                data = data / I0_data[:, None]

        elif self.dataType == 'I0':
            entry = 'entry%d' % self.scanNr
            with h5py.File(self.fileName, 'r') as hf:
                I0_data = np.array(hf[entry+'/measurement/counter1'])
                I0_data = I0_data.astype(float)
                data = I0_data.flatten()
        else:
            raise RuntimeError('unknown datatype specified (should be ''xrd'' or ''xrf''')

        return data

