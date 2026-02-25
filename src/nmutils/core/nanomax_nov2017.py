from .nanomax_nov2018 import flyscan_nov2018
from .. import NoDataException
import numpy as np
import h5py
import copy as cp
import os.path

class flyscan_nov2017(flyscan_nov2018):
    """
    Legacy format where the 2D detectors wrote one file per line.
    """

    def _readData(self, name):
        """ 
        Override data reading.
        """

        # we only have to override the pixel detector reading
        if not self.dataSource in ('pil100k', 'merlin', 'pil1m'):
            return super(flyscan_nov2017, self)._readData(name)

        if self.normalize_by_I0:
            entry = 'entry%d' % self.scanNr
            if not os.path.exists(self.fileName): raise NoDataException
            with h5py.File(self.fileName, 'r') as fp:
                I0_data = self._safe_get_array(fp, entry+'/measurement/Ni6602_buff')
                I0_data = I0_data.astype(float) * 1e-5
                I0_data = I0_data[:, :self.images_per_line]

        print("loading diffraction data...")
        path = os.path.split(os.path.abspath(self.fileName))[0]
        
        # set detector paths
        if self.dataSource == 'merlin':
            filename_pattern = 'scan_%04d_merlin_%04d.hdf5'
            hdfpath_pattern = 'entry_0000/measurement/Merlin/data'
        elif self.dataSource == 'pil100k':
            filename_pattern = 'scan_%04d_pil100k_%04d.hdf5'
            hdfpath_pattern = 'entry_0000/measurement/Pilatus/data'
        elif self.dataSource == 'pil1m':
            filename_pattern = 'scan_%04d_pil1m_%04d.hdf5'
            hdfpath_pattern = 'entry_0000/measurement/Pilatus/data'

        data = []
        print("attempting to read %d lines of diffraction data (based on the positions array or max number of lines set)"%self.nlines)
        for line in range(self.nlines):
            try:
                with h5py.File(os.path.join(path, filename_pattern%(self.scanNr, line)), 'r') as hf:
                    print('loading data: ' + filename_pattern%(self.scanNr, line))
                    dataset = self._safe_get_dataset(hf, hdfpath_pattern)
                    if self.xrdCropping:
                        i0, i1, j0, j1 = self.xrdCropping
                        data_ = np.array(dataset[:, i0 : i1, j0 : j1])
                    else:
                        data_ = np.array(dataset)
                    if self.xrdBinning > 1:
                        shape = fastBinPixels(data_[0], self.xrdBinning).shape
                        new_data_ = np.zeros((data_.shape[0],) + shape)
                        for ii in range(data_.shape[0]):
                            new_data_[ii] = fastBinPixels(data_[ii], self.xrdBinning)
                        data_ = new_data_
                    if self.xrdNormalize:
                        i0, i1, j0, j1 = self.xrdNormalize
                        data_ = np.array(data_, dtype=float)
                        for i in range(data_.shape[0]):
                            norm = float(np.sum(np.array(dataset[i, i0 : i1, j0 : j1])))
                            data_[i] /= norm
                    if 'Merlin' in hdfpath_pattern:
                        for i in range(data_.shape[0]):
                            data_[i] = np.flipud(data_[i]) # Merlin images indexed from the bottom left...
                    data.append(data_)
                    del dataset
            except IOError:
                # fewer hdf5 files than positions -- this is ok
                print("couldn't find expected file %s, returning"%(filename_pattern%(self.scanNr, line)))
                break

        print("loaded %d lines of Pilatus data"%len(data))
        data = np.concatenate(data, axis=0)

        return data
