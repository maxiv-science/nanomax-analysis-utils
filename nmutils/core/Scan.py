"""  
Implements the Scan class, a container for N-dimensional sample scans
holding arbitrary data at each position. This data can typically be, for
each scan position, one or more 2D detector images, 1D fluorescence
spectra, transmissions, etc.
"""

import numpy as np
import h5py
import copy as cp

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
        the beam positions on the sample, in right-handed lab
        coordinates but relative to the sample frame (which means that
        moving a motor positive moves the position on the sample
        negative). The coordinate system is the same as NEXUS:
        http://download.nexusformat.org/doc/html/design.html#nexus-coordinate-systems
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
            if not (self.positions.shape == self._readPositions(fileName)):
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
            index = np.argmin(np.linalg.norm(
                self.positions - rangeCenter, axis=1))
            for dataset in self.data.keys():
                new.data[dataset].append(self.data[dataset][index])
            new.positions.append(self.positions[index])

        # convert lists to arrays
        for dataset in self.data.keys():
            new.data[dataset] = np.array(new.data[dataset])
        new.positions = np.array(new.positions)
        new.nPositions = new.positions.shape[0]

        return new


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
            Nx, Ny = [int(np.sqrt(self.nPositions)),] * 2
            stepsize = 160e-9
        for i in range(Ny):
            for j in range(Nx):
                # by the convention noted in the base class:
                positions.append([j, -i])
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
            x = -np.array(hf.get('entry1/instrument/lab_sxy/lab_sx'))
            y = -np.array(hf.get('entry1/instrument/lab_sxy/lab_sy'))
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

class nanomaxScan_nov2016(Scan):
    # This class optionally uses the opts entry to addData(), where the
    # first element specifies the first-level hdf5 group.

    def _readPositions(self, fileName, opts=None):
        """ 
        Override position reading. Based on a preliminary hdf5 format,
        where either x or y position can be undefined.
        """
        x, y = None, None
        with h5py.File(fileName, 'r') as hf:
            # check if the entry has been specified, otherwise use the first one
            if opts:
                entry = opts[0]
            else:
                entry = hf.keys()[0]
            xdataset = hf.get(entry + '/measurement/pi727_x')
            ydataset = hf.get(entry + '/measurement/pi727_y')
            if (xdataset is None) and (ydataset is None):
                raise RuntimeError('No x or y data found!')
            if xdataset is not None:
                x = -np.array(xdataset)
            if ydataset is not None:
                y = -np.array(ydataset)
        if (y is None):
            y = np.zeros(x.shape)
        if (x is None):
            x = np.zeros(y.shape)
        return np.vstack((x, y)).T

    def _readData(self, fileName, opts=None):
        """ 
        Override data reading. Based on a preliminary hdf5 format.
        """
        with h5py.File(fileName, 'r') as hf:
            # check if the entry has been specified, otherwise use the first one
            if opts:
                entry = opts[0]
            else:
                entry = hf.keys()[0]
            data = hf.get(entry + '/measurement/pilatus1m')
            data = np.array(data)
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
