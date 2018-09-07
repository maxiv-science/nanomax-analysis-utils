from Scan import Scan
from ..utils import fastBinPixels
import numpy as np
import h5py
import copy as cp
import os.path

class nanomaxScan_flyscan_nov2017(Scan):
    """
    Class representing November 2017, with buffered positions just implemented.
    Here the positions can have different dimensions in x or y depending on
    whether or not they are buffered (samx_buff vs sams_y, samx_buff vs. samy_buff,
    sams_x vs samy_buff, etc...).
    """

    default_opts = {
        # the dataType option is mandatory for use with scanViewer
        'dataType': {
            'value': 'xrd',
            'type': str,
            'doc': "type of data, 'xrd' or 'xrf'",
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
#        'fastAxis': {
#            'value': 'xMotor',
#            'type': ['xMotor', 'yMotor'],
#            'doc': 'the fly scanned motor, must be the same as xMotor or yMotor',
#            },
        'xrfChannel': {
            'value': 3,
            'type': int,
            'doc': 'xspress3 channel from which to read XRF',
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
        'detectorPreference': {
            'value': 'none',
            'type': str,
            'doc': 'preferred XRD detector: pil100k, pil1m, merlin, ...',
            },
        'globalPositions': {
                'value': False,
                'type': bool,
                'doc': 'attempt to assign global scanning positions',
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
        # self.fastAxis = opts['fastAxis']['value']
        self.xrfChannel = int(opts['xrfChannel']['value'])
        self.xrfCropping = map(int, opts['xrfCropping']['value'])
        self.xrdCropping = map(int, opts['xrdCropping']['value'])
        self.xrdBinning = int(opts['xrdBinning']['value'])
        self.xrdNormalize = map(int, opts['xrdNormalize']['value'])
        self.nMaxLines = int(opts['nMaxLines']['value'])
        self.detPreference = opts['detectorPreference']['value']
        self.globalPositions = opts['globalPositions']['value']

    def _read_buffered(self, fp, entry):
        """
        Returns a flat array of buffered positions
        """
        data = np.asarray(fp.get(entry))
        nLines = data.shape[0]
        # find line length by looking for padding zeros
        for i in range(data.shape[1]):
            if data[0, i] == 0:
                Nx = i
                break
        data = data[:, :Nx].flatten()
        return data, nLines, Nx

    def _read_non_buffered(self, fp, entry, lineLength, nLines):
        """
        Returns a flat array of non-buffered positions, repeated to match
        buffered data.
        """
        data = np.asarray(fp.get(entry))
        if not (len(data) == nLines): raise Exception('Something''s wrong with the positions')
        data = np.repeat(data, lineLength)
        return data

    def _readPositions(self):
        """ 
        Override position reading.
        """
        
        entry = 'entry%d' % self.scanNr
        fileName = self.fileName

        # open hdf5 file
        fp = h5py.File(fileName, 'r')

        # infer which is the slow axis
        slowMotorHint = fp.get(entry + '/title').value.split(' ')[1]
        if slowMotorHint in self.xMotor:
            fastMotor = self.yMotor
            slowMotor = self.xMotor
            print "Loader inferred that %s is the fast axis" % self.yMotor
        elif slowMotorHint in self.yMotor:
            fastMotor = self.xMotor
            slowMotor = self.yMotor
            print "Loader inferred that %s is the fast axis" % self.xMotor
        else:
            raise Exception("Couldn't determine which is the fast axis!")

        # read the fast axis
        fast, nLines, lineLen = self._read_buffered(fp, entry+'/measurement/%s'%fastMotor)

        # save number of lines for the _readData method
        self.nlines = nLines

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
            print "x and y shapes:", x.shape, y.shape

        # assign fast and slow positions
        if fastMotor == self.xMotor:
            x = fast
            y = slow
        else:
            y = fast
            x = slow

        # optionally add coarse stage position
        if self.globalPositions:
            sams_x = fp.get(entry+'/measurement/sams_x').value * 1e3
            sams_y = fp.get(entry+'/measurement/sams_y').value * 1e3
            sams_z = fp.get(entry+'/measurement/sams_z').value * 1e3
            offsets = {'samx': sams_x, 'samy': sams_y, 'samz': sams_z}
            x += offsets[self.xMotor[:4]]
            y += offsets[self.yMotor[:4]]
            print '*** added rough position offsets!'

        print "loaded positions from %d lines, %d positions on each"%(self.nlines, lineLen)

        # close hdf5 file
        fp.close()

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
            if len(avail_dets) == 0:
                print "No XRD data available"
                return

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
            else:
                print "Something went really wrong in detector choice"
                return
                
            data = []
            print "attempting to read %d lines of diffraction data (based on the positions array or max number of lines set)"%self.nlines
            for line in range(self.nlines):
                try:
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
                    if self.xrfCropping:
                        ch0, ch1 = self.xrfCropping
                        data.append(np.array(dataset)[:, self.xrfChannel, ch0:ch1])
                    else:
                        data.append(np.array(dataset)[:, self.xrfChannel, :])
                    line += 1
            print "loaded %d lines of xspress3 data"%len(data)
            data = np.vstack(data)
        else:
            raise RuntimeError('unknown datatype specified (should be ''xrd'' or ''xrf''')
        return data

