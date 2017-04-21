from Scan import Scan
import numpy as np
import h5py
import copy as cp
import os.path


class nanomaxScan_stepscan_april2017(Scan):
    # Class representing April 2017, with the beamline still temporarily
    # set up for commissioning and user runs. Uses the addData opts list
    # for the scan number:
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