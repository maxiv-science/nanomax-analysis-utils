from Scan import Scan
import numpy as np
import h5py
import copy as cp
import os.path

class id13Scan(Scan):
    # Playing with scanning data from ID13

    def _readPositions(self, fileName, opts=None):
        """ 
        Override position reading.

        opts = [datatype, ROI size]

        """

        with h5py.File(fileName, 'r') as hf:
            datasets = hf.get('entry/data').items()
            Npos = 0
            for d in datasets:
                Npos += int(d[1].shape[0])

        x, y = [], []
        for i in range(int(np.sqrt(Npos))):
            for j in range(int(np.sqrt(Npos))):
                x.append(i)
                y.append(j)

        return np.vstack((x, y)).T

    def _readData(self, fileName, opts=None):
        """ 
        Override data reading. 

        opts = [datatype, ROI size]
        
        """

        delta = int(opts[1]) / 2
        center = np.array((1178, 1164))
        center = np.array((2060, 1360))

        data = []
        with h5py.File(fileName, 'r') as hf:
            datasets = hf.get('entry/data').items()
            for d in datasets:
                data.append(d[1][:, center[0]-delta:center[0]+delta, center[1]-delta:center[1]+delta])
        data = np.concatenate(data, axis=0)
        return data
