""" Implements the Scan class, a container for N-dimensional sample scans holding arbitrary data at each position. This data can typically be, for each scan position, one or more 2D detector images, 1D fluorescence spectra, transmissions, etc. """

    #######################################################################################
    # next up: write a GUI which uses this class to map out ROI intensities, for example. #
    #######################################################################################

import numpy as np
import h5py

__docformat__ = 'restructuredtext' # This is what we're using! Learn about it.

class Scan():
    
    def __init__(self):
        """ Positions and data are added later. """
        self.nDataSets = 0
        self.nPositions = None
        
    def _readPositions(self, fileName):
        """ Placeholder method to be subclassed. Private method which interfaces with the actual hdf5 file and returns an array of coordinates Nx(image size). """
        pass
        
    def _readData(self, fileName, name):
        """ Placeholder method to be subclassed. Private method which interfaces with the actual hdf5 file and returns an Nx(image size) array. The name kwarg should say what type of data we're reading (for example 'pilatus', 'transmission', ...), so data from different sources can be handled by this method. """
        pass
        
    def addData(self, fileName, name=None):
        """ This method adds positions the first time data is loaded. Then, subsequent data additions should check for consistency and complain if datasets are not compatible. """
        
        if not name:
            name = 'data%u' % self.nDataSets
        
        # Check if any data exists.
        if not hasattr(self, 'data'):
            # initialize data dict and read positions
            self.data = {}
            self.positions = self._readPositions(fileName)
        else:
            # verify that the data isn't already loaded
            if name in self.data.keys():
                raise ValueError("Dataset '%s' already exists!"%name)
            # verify that positions are are consistent
            if not (self.positions.shape == self._readPositions(fileName)):
                raise ValueError("Positions of new dataset are inconsistent with previously loaded positions!")
        
        # The actual reading is done by _readData() which knows about the details of the hdf5 file
        data = self._readData(fileName, name)
        self.data[name] = data
        self.nDataSets += 1
        
    def removeData(self, name):
        if name in self.data.keys():
            self.data.pop(name, None)
        else:
            raise ValueError("Dataset '%s' doesn't exist!"%name)
        self.nDataSets -= 1
        
    def listData(self):
        return self.data.keys()
        
    def meanData(self, name=None):
        """ Returns the scan-average of the specified data set. """
        if not name: 
            if self.nDataSets == 1:
                name = self.listData()[0]
            else:
                raise ValueError("There is more than one dataset to choose from. Please specify!")
        return np.mean(self.data[name], axis=0)

class nanomaxScan(Scan):
    def _readPositions(self, fileName):
        """ Override the method which reads scan positions. This is based on a very early hdf5 format. """
        with h5py.File(fileName,'r') as hf:
            data = hf.get('entry/detector/data')
            data = np.array(data)
            self.nPositions = data.shape[0]
        positions = []
        for i in range(int(np.sqrt(self.nPositions))):
            for j in range(int(np.sqrt(self.nPositions))):
                positions.append([i, j])
        return np.array(positions)
        
    def _readData(self, fileName, name):
        """ Override the method which reads actual data. This is based on a very early hdf5 format. """
        # Add pilatus data from MxN scan, ad hoc for now
        with h5py.File(fileName,'r') as hf:
            data = hf.get('entry/detector/data')
            data = np.array(data)
        return data
            
class i13Scan(Scan):
    def _readPositions(self, fileName):
        """ Override position reading. Based on Aaron Parson's I13 data. """
        with h5py.File(fileName,'r') as hf:
            x = np.array(hf.get('entry1/instrument/lab_sxy/lab_sx'))
            y = np.array(hf.get('entry1/instrument/lab_sxy/lab_sy'))
        positions = np.vstack((x, y)).T
        return positions
        
    def _readData(self, fileName, name):
        """ Override data reading. Based on Aaron Parson's I13 data. """
        with h5py.File(fileName,'r') as hf:
            data = hf.get('entry1/merlin_sw_hdf/data')
            data = np.array(data)
        return data

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    #s = nanomaxScan()
    #s.addData('/home/alex/data/zoneplatescan-s3-m4.hdf5')
    s = i13Scan()
    s.addData('/home/alex/data/aaronsSiemensStar/68862.nxs')
    opts = {'interpolation':'none', 'cmap':'gray'}
    plt.figure()
    plt.plot(s.positions[:,0], s.positions[:,1], 'o-')
    plt.figure()    
    plt.imshow(np.log10(s.data['data0'][10]), **opts)
    plt.figure()
    plt.imshow(np.log10(s.meanData('data0')), **opts)