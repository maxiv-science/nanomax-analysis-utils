from Scan import Scan
import numpy as np
import h5py

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