"""  
Implements the Scan class, a container for N-dimensional sample scans
holding arbitrary data at each position. This data can typically be, for
each scan position, one or more 2D detector images, 1D fluorescence
spectra, transmissions, etc.
"""

import numpy as np
import h5py
import copy as cp
import os.path

import scipy.ndimage.measurements
from scipy.interpolate import griddata

__docformat__ = 'restructuredtext'  # This is what we're using! Learn about it.


class Scan(object):

    def __init__(self, options=None):
        """ 
        Only initializes counters and options. Positions and data are
        added later.
        """
        self.nDataSets = 0
        self.nPositions = None
        self.nDimensions = None  # scan dimensions
        self.options = None

    def _readPositions(self, fileName, opts=None):
        """ 
        Placeholder method to be subclassed. Private method which
        interfaces with the actual hdf5 file and returns an array of
        coordinates N-by-(number of scan dimensions).

        The positions are defined as [x, y], where columns x and y are
        motor positions. It is then up to the viewer to display the
        image in a good way. For example, if the motor positions denote
        sample position and under the nanomax coordinate system, the xy
        origin should be top left. Then, the bottom right corner
        corresponds to maximum motor positions, which means minimum in
        the sample frame under the nanomax coordinate system. Phew.
        """
        pass

    def _readData(self, fileName, opts=None):
        """ 
        Placeholder method to be subclassed. Private method which
        interfaces with the actual hdf5 file and returns an N-by-(image
        size) array. The name kwarg should hint at what type of data
        we're reading (for example 'pilatus', 'transmission', ...), so
        data from different sources can be handled by this method.
        """
        pass

    def addData(self, fileName, name=None, opts=None):
        """ 
        This method adds positions the first time data is loaded. Then,
        subsequent data additions should check for consistency and
        complain if datasets are not compatible.
        """

        if not name:
            name = 'data%u' % self.nDataSets

        # Check if any data exists.
        if not hasattr(self, 'data'):
            # initialize data dict and read positions
            self.data = {}
            self.positions = self._readPositions(fileName, opts)
            self.nPositions = self.positions.shape[0]
            self.nDimensions = self.positions.shape[1]
        else:
            # verify that the data isn't already loaded
            if name in self.data.keys():
                raise ValueError("Dataset '%s' already exists!" % name)
            # verify that positions are are consistent
            if not np.all(self.positions == self._readPositions(fileName, opts)):
                raise ValueError(
                    "Positions of new dataset are inconsistent with previously loaded positions!")

        # The actual reading is done by _readData() which knows about the
        # details of the hdf5 file
        data = self._readData(fileName, opts)
        self.data[name] = data
        self.nDataSets += 1

    def removeData(self, name):
        if name in self.data.keys():
            self.data.pop(name, None)
        else:
            raise ValueError("Dataset '%s' doesn't exist!" % name)
        self.nDataSets -= 1

    def listData(self):
        return self.data.keys()

    def meanData(self, name=None):
        """ Returns the scan-average of the specified data set. """
        if not name:
            if self.nDataSets == 1:
                name = self.listData()[0]
            else:
                raise ValueError(
                    "There is more than one dataset to choose from. Please specify!")
        return np.mean(self.data[name], axis=0)

    def copy(self, data=True):
        """ 
        Returns a copy of the Scan instance. The kwarg data can be set
        to False to ignore data and positions, which is useful for
        creating Scan instances with only a subset of the data. This
        method also copies all attributes and does not need to be
        updated.
        """

        # copy all
        if data:
            return cp.deepcopy(self)

        # otherwise, construct a new objects and copy all the attributes
        # create a new object of the right subclass:
        new = None  # just tricking the editor
        exec("new = %s()" % type(self).__name__)

        # copy all the non-data attributes
        for key in self.__dict__.keys():
            if key not in ['data', 'positions', 'nPositions']:
                exec("new.%s = cp.deepcopy(self.%s)" % (key, key))
        new.data = {}
        new.nPositions = 0
        new.positions = None
        new.nDatasets = 0
        for dataset in self.data.keys():
            new.data[dataset] = None
            new.nDatasets += 1

        return new

    def subset(self, posRange, closest=False):
        """ 
        Returns a Scan instance containing only the scan positions which
        are within a specified range, array([[xmin, ymin, ...], [xmax,
        ymax, ...]]). If the kwarg closest is True, and the specified
        range contains no positions, then the returned instance contains
        only the single closest position.
        """
        new = self.copy(data=False)

        # lists of data and positions to fill in
        new.positions = []
        for dataset in self.data.keys():
            new.data[dataset] = []

        # go through all positions and only include the ones which are
        # within range
        for i in range(self.nPositions):
            ok = True
            for dim in range(self.nDimensions):
                pos = self.positions[i, dim]
                if pos < posRange[0, dim] or pos > posRange[1, dim]:
                    ok = False
                    break
            if ok:
                for dataset in self.data.keys():
                    new.data[dataset].append(self.data[dataset][i])
                new.positions.append(self.positions[i])

        # get the closest positions if requested
        if (len(new.positions) == 0) and closest:
            rangeCenter = np.mean(posRange, axis=0)
            # using sum instead of linalg.norm here, for old numpy at beamline:
            index = np.argmin(
                np.sum((self.positions - rangeCenter)**2, axis=1))
            for dataset in self.data.keys():
                new.data[dataset].append(self.data[dataset][index])
            new.positions.append(self.positions[index])

        # convert lists to arrays
        for dataset in self.data.keys():
            new.data[dataset] = np.array(new.data[dataset])
        new.positions = np.array(new.positions)
        new.nPositions = new.positions.shape[0]

        return new

    def interpolatedMap(self, values, oversampling, origin='lr'):
        """ 
        Provides a regular and interpolated xy map of the scan, with the
        values provided. For example, a ROI integral can be provided which
        results in an interpolated map of that ROI.

        values: a length-N array, with one value per position
        oversampling: the oversampling ratio relative to the average position spacing
        origin: 'lr', 'll', 'ur', 'ul'
        """
        xMin, xMax = np.min(self.positions[:,0]), np.max(self.positions[:,0])
        yMin, yMax = np.min(self.positions[:,1]), np.max(self.positions[:,1])

        # here we need special cases for 1d scans (where x or y doesn't vary)
        if np.abs(yMax - yMin) < 1e-12:
            stepsize = (xMax - xMin) / float(self.nPositions) / oversampling
            margin = oversampling * stepsize / 2
            y, x = np.mgrid[yMin-(stepsize*oversampling*5)/2:yMin+(stepsize*oversampling*5)/2:stepsize, xMax+margin:xMin-margin:-stepsize]
        elif np.abs(xMax - xMin) < 1e-12:
            stepsize = (yMax - yMin) / float(self.nPositions) / oversampling
            margin = oversampling * stepsize / 2
            y, x = np.mgrid[yMax+margin:yMin-margin:-stepsize, xMin-(stepsize*oversampling*5)/2:xMin+(stepsize*oversampling*5)/2:stepsize]
        else:
            stepsize = np.sqrt((xMax-xMin) * (yMax-yMin) / float(self.nPositions)) / oversampling
            margin = oversampling * stepsize / 2
            y, x = np.mgrid[yMax+margin:yMin-margin:-stepsize, xMax+margin:xMin-margin:-stepsize]
        z = griddata(self.positions, values, (x, y), method='nearest')
        
        # we've been assuming lower-right origin. adjust:
        if origin == 'll':
            x = np.fliplr(x)
            y = np.fliplr(y)
            z = np.fliplr(z)
        elif origin == 'ur':
            x = np.flipud(x)
            y = np.flipud(y)
            z = np.flipud(z)
        elif origin == 'ul':
            x = np.flipud(x)
            y = np.flipud(y)
            z = np.flipud(z)
            x = np.fliplr(x)
            y = np.fliplr(y)
            z = np.fliplr(z)

        return x, y, z


####
# Here follow special subclasses which describe how to load from
# specific data sources.

class nanomaxScan_june2016(Scan):

    def _readPositions(self, fileName, opts=None):
        """ 
        Override the method which reads scan positions. This is based on
        a very early hdf5 format.
        """
        with h5py.File(fileName, 'r') as hf:
            data = hf.get('entry/detector/data')
            data = np.array(data)
            self.nPositions = data.shape[0]
        positions = []
        if self.options:
            Nx, Ny = self.options['scanshape']
            stepsize = self.options['stepsize']
        else:
            # assume square scan, 160 nm steps
            Nx, Ny = [int(np.sqrt(self.nPositions)), ] * 2
            stepsize = 160e-9
        for i in range(Ny):
            for j in range(Nx):
                # by the convention noted in the base class:
                positions.append([-j, i])
        return np.array(positions) * stepsize

    def _readData(self, fileName, opts=None):
        """ 
        Override the method which reads actual data. This is based on a
        very early hdf5 format.
        """
        # Add pilatus data from MxN scan, ad hoc for now
        with h5py.File(fileName, 'r') as hf:
            data = hf.get('entry/detector/data')
            data = np.array(data)
        return data


class i13Scan(Scan):

    def _readPositions(self, fileName, opts=None):
        """ 
        Override position reading. Based on Aaron Parson's I13 data. 
        """
        with h5py.File(fileName, 'r') as hf:
            # assuming the xy positions are motor positions, we want the
            # negative of those for the sample frame.
            x = np.array(hf.get('entry1/instrument/lab_sxy/lab_sx'))
            y = np.array(hf.get('entry1/instrument/lab_sxy/lab_sy'))
        positions = np.vstack((x, y)).T
        return positions

    def _readData(self, fileName, opts=None):
        """ 
        Override data reading. Based on Aaron Parson's I13 data. 
        """
        with h5py.File(fileName, 'r') as hf:
            data = hf.get('entry1/merlin_sw_hdf/data')
            data = np.array(data)
        return data


class alsScan(Scan):

    def _readPositions(self, fileName, opts=None):
        """ 
        Override position reading. Based on Joerg's ALS data. 
        """
        with h5py.File(fileName, 'r') as hf:
            translation = np.array(hf.get('entry_1/data_1/translation'))
        print translation
        positions = translation[:, :2]
        return positions

    def _readData(self, fileName, opts=None):
        """ 
        Override data reading. Based on Joerg's ALS data. 
        """
        with h5py.File(fileName, 'r') as hf:
            data = hf.get('entry_1/data_1/data')
            data = np.array(data)
        return data


class nanomaxScan_flyscan_week48(Scan):
    # Class representing late November 2016, when fly-scanning was set
    # up in a very temporary way. Uses the addData opts list for the
    # scan number and optionally for the amount of data around the
    # diffraction center of mass to load:
    #
    # opts = [datatype scannr (ROI size)], where datatype is 'xrf' or 'xrd'

    def _readPositions(self, fileName, opts=None):
        """ 
        Override position reading.
        """
        if not (len(opts) >= 2):
            raise RuntimeError('The addData opts list is insufficient for this Scan subclass.')

        skipX = 1
        entry = 'entry%d' % int(opts[1])

        x, y = None, None
        with h5py.File(fileName, 'r') as hf:
            # get fast x positions
            xdataset = hf.get(entry + '/measurement/AdLinkAI')
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

        return np.vstack((x, y)).T

    def _readData(self, fileName, opts=None):
        """ 
        Override data reading.
        """

        datatype = opts[0]

        if len(opts) == 3:
            delta = int(opts[2]) / 2
        else:
            delta = None

        scannr = int(opts[1])
        
        if datatype == 'xrd':
            print 'loading diffraction data'
            path = os.path.split(os.path.abspath(fileName))[0]
            # check which detector was used
            if os.path.isfile(os.path.join(path, 'pilatus_scan_%d_%04d.hdf5'%(scannr,0))):
                filepattern = 'pilatus_scan_%d_%04d.hdf5'
                print "This is a Pilatus 100k scan"
            elif os.path.isfile(os.path.join(path, 'pilatus1m_scan_%d_%04d.hdf5'%(scannr,0))):
                filepattern = 'pilatus1m_scan_%d_%04d.hdf5'
                print "This is a Pilatus 1M scan"
            else:
                print "No 1M or 100k data found."

            done = False
            line = 0
            data = []
            while not done:
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
                        #data.append(np.array(dataset))
                    line += 1
                except IOError:
                    done = True
            print "loaded %d lines of Pilatus data"%len(data)
            data = np.concatenate(data, axis=0)

        elif datatype == 'xrf':
            raise NotImplementedError('xrf for fly scan not implemented')

        else:
            raise RuntimeError('unknown datatype specified (should be ''xrd'' or ''xrf''')
        return data


class nanomaxScan_stepscan_week48(Scan):
    # Class representing late November 2016, when step-scanning was set
    # up in a very temporary way. Uses the addData opts list for the
    # scan number:
    #
    # opts = [datatype, scannr], where datatype is 'xrf' or 'xrd'

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

        return np.vstack((x, y)).T

    def _readData(self, fileName, opts=None):
        """ 
        Override data reading.
        """

        datatype = opts[0]
        scannr = int(opts[1])

        if datatype == 'xrd':
            path = os.path.split(os.path.abspath(fileName))[0]
            # check which detector was used
            if os.path.isfile(os.path.join(path, 'pilatus_scan_%d_%04d.hdf5'%(scannr,0))):
                filepattern = 'pilatus_scan_%d_%04d.hdf5'
                print "This is a Pilatus 100k scan"
            elif os.path.isfile(os.path.join(path, 'pilatus1m_scan_%d_%04d.hdf5'%(scannr,0))):
                filepattern = 'pilatus1m_scan_%d_%04d.hdf5'
                print "This is a Pilatus 1M scan"
            else:
                print "No 1M or 100k data found."

            data = []
            for im in range(self.positions.shape[0]):
                with h5py.File(os.path.join(path, filepattern%(scannr, im)), 'r') as hf:
                    print 'loading data: ' + filepattern%(scannr, im)
                    dataset = hf.get('entry_0000/measurement/Pilatus/data')
                    data.append(np.array(dataset)[0])
            print "loaded %d Pilatus images"%len(data)
            data = np.array(data)

        elif datatype == 'xrf':
            with h5py.File(fileName, 'r') as hf:
                data = np.array(hf.get('entry%d/measurement/xrf_px5'%scannr))

        else:
            raise RuntimeError('unknown datatype specified (should be ''xrd'' or ''xrf''')
            dataset = hf.get('entry_0000/measurement/Pilatus/data')

        return data

# if __name__ == '__main__':
#    import matplotlib.pyplot as plt
#    #s = nanomaxScan()
#    #s.addData('/home/alex/data/zoneplatescan-s3-m4.hdf5')
#    s = i13Scan()
#    s.addData('/home/alex/data/aaronsSiemensStar/68862.nxs')
#    plt.plot(s.positions[:,0], s.positions[:,1], '.-')
#    plt.figure(); plt.imshow(np.log10(s.data['data0'][10]))
#    roi = np.array([[1438, -697], [1443, -695]])
#    s = s.roi(roi)
#    plt.figure(); plt.plot(s.positions[:,0], s.positions[:,1], '.-')
#    plt.figure(); plt.imshow(np.log10(s.data['data0'][10]))
#    #plt.imshow(np.log10(s.meanData('data0')), **opts)
