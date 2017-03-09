from Scan import Scan
import numpy as np
import h5py

class ptypyScan(Scan):
    """
    This subclass reads from ptyd/ptyr files.
    """

    def _readPositions(self, fileName, opts=None):
        """ 
        Override position reading.
        """

        with h5py.File(fileName, 'r') as hf:
            if fileName[-4:] == 'ptyr':
                pass

            elif fileName[-4:] == 'ptyd':
                positions = []
                for chunk in hf.get('chunks').keys():
                    positions.append(np.array(hf.get('chunks/%s/positions'%chunk)))
                positions = np.vstack(positions)

        positions = -np.fliplr(positions)
        return positions


    def _readData(self, fileName, opts=None):
        """ 
        Override data reading
        """
        with h5py.File(fileName, 'r') as hf:
            if fileName[-4:] == 'ptyr':
                pass

            elif fileName[-4:] == 'ptyd':
                data = []
                weights = []
                for chunk in hf.get('chunks').keys():
                    data.append(np.array(hf.get('chunks/%s/data'%chunk)))
                    weights.append(np.array(hf.get('chunks/%s/weights'%chunk)))
                data = np.vstack(data)
                weights = np.vstack(weights)
                if not (data.shape == weights.shape):
                    weights = np.array(hf.get('meta/weight2d'))
                data *= weights

        return data