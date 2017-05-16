from Scan import Scan
import numpy as np
import h5py
import copy as cp
import os.path

class nanomaxScan_flyscan_april2017(Scan):
    # Class representing April 2017, with fly-scanning still set up
    # in a temporary way. Uses the addData opts list for the
    # scan number and optionally for the amount of data around the
    # diffraction center of mass to load:
    #
    # opts = [datatype scannr (XRF channel) (ROI size)], where datatype is 'xrf' or 'xrd'

    def _readPositions(self, fileName, opts=None):
        """ 
        Override position reading.
        """
        if not (len(opts) >= 2):
            raise RuntimeError('The addData opts list is insufficient for this Scan subclass.')

        skipX = 0
        entry = 'entry%d' % int(opts[1])

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
            ydataset = hf.get(entry + '/measurement/samy')
            yall = np.array(ydataset)
            if not (len(yall) == Ny): raise Exception('Something''s wrong with the positions')
            y = np.repeat(yall, Nx)

            # save number of lines for the _readData method
            self.nlines = Ny

            print "loaded positions from %d lines, %d positions on each"%(self.nlines, Nx)

        return np.vstack((x, y)).T

    def _readData(self, fileName, opts=None):
        """ 
        Override data reading.
        """

        datatype = opts[0]

        if len(opts) >= 3:
            xrfChannel = int(opts[2])
        else: 
            xrfChannel = 2

        if len(opts) == 4:
            delta = int(opts[3]) / 2
        else:
            delta = None

        scannr = int(opts[1])
        
        if datatype == 'xrd':
            print "loading diffraction data..."
            print "selecting fluorescence channel %d"%xrfChannel
            path = os.path.split(os.path.abspath(fileName))[0]
            # check which detector was used
            if os.path.isfile(os.path.join(path, 'scan_%04d_pil100k_%04d.hdf5'%(scannr,0))):
                filepattern = 'scan_%04d_pil100k_%04d.hdf5'
                print "This is a Pilatus 100k scan"
            elif os.path.isfile(os.path.join(path, 'scan_%04d_pil1m_%04d.hdf5'%(scannr,0))):
                filepattern = 'scan_%04d_pil1m_%04d.hdf5'
                print "This is a Pilatus 1M scan"
            else:
                print "No 1M or 100k data found."

            data = []
            print "attempting to read %d lines of diffraction data (based on the positions array)"%self.nlines
            for line in range(self.nlines):
                try:
                    with h5py.File(os.path.join(path, filepattern%(scannr, line)), 'r') as hf:
                        print 'loading data: ' + filepattern%(scannr, line)
                        dataset = hf.get('entry_0000/measurement/Pilatus/data')
                        # for the first file, determine center of mass
                        if len(data) == 0:
                            import scipy.ndimage.measurements
                            im = np.array(dataset[0])
                            ic, jc = map(int, scipy.ndimage.measurements.center_of_mass(im))
                            print "Estimated center of mass to (%d, %d)"%(ic, jc)
                        if delta:
                            data.append(np.array(dataset[:, ic-delta:ic+delta, jc-delta:jc+delta]))
                        else:
                            data.append(np.array(dataset))
                        del dataset
                except IOError:
                    # fewer hdf5 files than positions -- this is ok
                    print "couldn't find expected file %s, returning"%(filepattern%(scannr, line))
                    break

            print "loaded %d lines of Pilatus data"%len(data)
            data = np.concatenate(data, axis=0)

        elif datatype == 'xrf':
            print "loading flurescence data..."
            path = os.path.split(os.path.abspath(fileName))[0]
            filepattern = 'scan_%04d_xspress3_0000.hdf5'
            print 'loading data: ' + filepattern%(scannr)
            data = []
            with h5py.File(os.path.join(path, filepattern%(scannr)), 'r') as hf:
                line = 0
                while True:
                    dataset = hf.get('entry_%04d/measurement/xspress3/data'%line)
                    if not dataset:
                        break
                    data.append(np.array(dataset)[:, xrfChannel, :])
                    line += 1
            print "loaded %d lines of xspress3 data"%len(data)
            data = np.vstack(data)
        else:
            raise RuntimeError('unknown datatype specified (should be ''xrd'' or ''xrf''')
        return data


class nanomaxScan_stepscan_april2017(Scan):
    # Class representing April 2017, with the beamline still temporarily
    # set up for commissioning and user runs. Uses the addData opts list
    # for the scan number:
    #
    # opts = [datatype, scannr, (XRF channel)], where datatype is 'xrf' or 'xrd'

    def _readPositions(self, fileName, opts=None):
        """ 
        Override position reading.
        """
        if not (len(opts) >= 2):
            raise RuntimeError('The addData opts list is insufficient for this Scan subclass.')

        entry = 'entry%d' % int(opts[1])

        with h5py.File(fileName, 'r') as hf:
            x = np.array(hf.get(entry + '/measurement/samx'))
            y = np.array(hf.get(entry + '/measurement/samy'))

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

    def _readData(self, fileName, opts=None):
        """ 
        Override data reading. Here the filename is only used to find the
        path of the Lima hdf5 files.
        """

        datatype = opts[0]
        scannr = int(opts[1])

        if len(opts) >= 3:
            xrfChannel = int(opts[2])
        else: 
            xrfChannel = 2

        if datatype == 'xrd':
            print "loading diffraction data..."
            path = os.path.split(os.path.abspath(fileName))[0]
            # check which detector was used
            if os.path.isfile(os.path.join(path, 'scan_%04d_pil100k_%04d.hdf5'%(scannr,0))):
                filepattern = 'scan_%04d_pil100k_%04d.hdf5'
                print "This is a Pilatus 100k scan"
            elif os.path.isfile(os.path.join(path, 'scan_%04d_pil1m_%04d.hdf5'%(scannr,0))):
                filepattern = 'scan_%04d_pil1m_%04d.hdf5'
                print "This is a Pilatus 1M scan"
            else:
                print "No 1M or 100k data found."

            data = []
            for im in range(self.positions.shape[0]):
                try:
                    with h5py.File(os.path.join(path, filepattern%(scannr, im)), 'r') as hf:
                        print 'loading data: ' + filepattern%(scannr, im)
                        dataset = hf.get('entry_0000/measurement/Pilatus/data')
                        data.append(np.array(dataset)[0])
                except IOError:
                    # missing files -- this is ok
                    print "couldn't find expected file %s, returning"%(filepattern%(scannr, im))
                    break
            print "loaded %d Pilatus images"%len(data)
            data = np.array(data)

        elif datatype == 'xrf':
            print "loading flurescence data..."
            print "selecting fluorescence channel %d"%xrfChannel
            path = os.path.split(os.path.abspath(fileName))[0]
            filepattern = 'scan_%04d_xspress3_0000.hdf5'
            print 'loading data: ' + filepattern%(scannr)
            data = []
            with h5py.File(os.path.join(path, filepattern%(scannr)), 'r') as hf:
                for im in range(self.positions.shape[0]):
                    dataset = hf.get('entry_%04d/measurement/xspress3/data'%im)
                    if not dataset:
                        break
                    data.append(np.array(dataset)[0, xrfChannel])
            data = np.array(data)

        else:
            raise RuntimeError('unknown datatype specified (should be ''xrd'' or ''xrf''')
            dataset = hf.get('entry_0000/measurement/Pilatus/data')

        return data

class nanomaxScan_rough_stepscan_april2017(nanomaxScan_stepscan_april2017):
    # Override to read the rough stages instead

    def _readPositions(self, fileName, opts=None):
        """ 
        Override position reading.
        """
        if not (len(opts) >= 2):
            raise RuntimeError('The addData opts list is insufficient for this Scan subclass.')

        entry = 'entry%d' % int(opts[1])

        with h5py.File(fileName, 'r') as hf:
            x = np.array(hf.get(entry + '/measurement/sams_x'))
            y = np.array(hf.get(entry + '/measurement/sams_y'))

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

