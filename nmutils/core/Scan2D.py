""" Implements the Scan2D class, a container for 2D sample scans holding arbitrary data at each position. This data can typically be, for each scan position, one or more 2D detector images, 1D fluorescence spectra, transmissions, etc. """

    #######################################################################################
    # next up: write a GUI which uses this class to map out ROI intensities, for example. #
    #######################################################################################

import numpy as np
import h5py

__docformat__ = 'restructuredtext' # This is what we're using! Learn about it.

class Scan2D():
    
    def __init__(self, scanDimensions):
        """ Object-level properties, like scan positions and dimensions. """
        
        self.scanDimensions = tuple(scanDimensions)
        self.positions = [np.array(range(scanDimensions[0])), np.array(range(scanDimensions[1]))]
        self.nDataSets = 0
        
    def _readData(self, fileName, name):
        """ Private method which interfaces with the actual hdf5 file and returns an MxNx(image size) array. The name kwarg should say what type of data we're reading (for example 'pilatus', 'transmission', ...), so data from different sources can be handled by this method. Subclass this! """
        
        if name == 'pilatus':
            # Add pilatus data from MxN scan, ad hoc for now
            with h5py.File(fileName,'r') as hf:
                data = hf.get('entry/detector/data')
                imshape = data.shape[-2:]
                print data.shape
                data = np.array(data).reshape(self.scanDimensions + imshape)
            return data
        
    def addData(self, fileName, name=None):
        """ This method adds positions the first time data is loaded. Then, subsequent data additions should check for consistency and complain if datasets are not compatible. """
        
        if not name:
            name = 'data%u' % self.nDataSets
        
        # Check if any data exists.
        if not hasattr(self, 'data'):
            self.data = {}
        else:
            if name in self.data.keys():
                raise ValueError("Dataset '%s' already exists!"%name)
        
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
        return np.mean(self.data[name], axis=(0,1))

#if __name__ == '__main__':
#    import matplotlib.pyplot as plt
#    s = Scan2D([51, 51])
#    s.addData('/home/alex/Data/zoneplatescan-s3-m4.hdf5', 'pilatus')
#    opts = {'interpolation':'none', 'cmap':'gray'}
#    plt.imshow(np.log10(s.data['pilatus'][10,10]), **opts)
#    plt.imshow(np.log10(s.meanData('pilatus')), **opts)