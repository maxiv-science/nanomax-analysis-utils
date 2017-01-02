from Scan import Scan
import numpy as np
import h5py

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