from Scan import Scan
import numpy as np
import h5py

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