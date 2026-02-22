"""
Example class for early softimax data.
"""


from . import Scan
from .. import NoDataException
import numpy as np
import h5py
import copy as cp
import os.path

class softimax_nxus_scan(Scan):
    """
    Early template for softimax
    """

    alba_names = ['aem_o04_01_ch1', 'aem_o04_01_ch2']
    default_opts = {
        'scanNr': {
            'value': 0,
            'type': int,
            'doc': "scan number",
            },
        'path': {
            'value': None,
            'type': str,
            'doc': "nxus file",
            },
        'dataSource': {
            'value': alba_names[0],
            'type': [] + alba_names,
            'doc': "type of data",
            },
        'xMotor': {
            'value': 'mm_h_offset',
            'type': str,
            'doc': 'scanned motor to plot on the x axis',
            },
        'yMotor': {
            'value': 'mm_v_offset',
            'type': str,
            'doc': 'scanned motor to plot on the y axis',
            },
    }

    # an optional class attribute which lets scanViewer know what
    # dataSource options have what dimensionalities. Good for the GUI.
    sourceDims = {}
    albaDims = {name:0 for name in alba_names}
    sourceDims.update(albaDims)
    assert sorted(sourceDims.keys()) == sorted(default_opts['dataSource']['type'])

    def _prepareData(self, **kwargs):
        """ 
        This method gets the kwargs passed to the addData() method, and
        stores them for use during this data loading.
        """
        # the base class method parses everything
        super()._prepareData(**kwargs)

    def _readPositions(self):
        """ 
        Override position reading. Should return N by 2 array [x, y].
        """

        if not os.path.exists(self.path):
            print('File not found! \n    ', self.path)
            raise NoDataException(self.path)
        with h5py.File(self.path, 'r') as fp:
            # read the positions
            entry_name = 'entry%u' % self.scanNr
            try:
                entry = fp[entry_name]
                x = entry['measurement/%s' % self.xMotor][:]
            except KeyError:
                print('entry %s not found'%self.xMotor)
                raise NoDataException
            try:
                y = entry['measurement/%s' % self.yMotor][:]
            except KeyError:
                print('entry %s not found'%self.yMotor)
                raise NoDataException

        # save motor labels, this is optional
        self.positionDimLabels = [self.xMotor, self.yMotor]

        print('loaded %u positions'%x.shape)
        return np.vstack((x, y)).T

    def _readData(self, name):
        """ 
        Override data reading. Do any detector-specific cropping or
        data treatment here, with if clauses as needed.
        """

        with h5py.File(self.path, 'r') as fp:
            try:
                data = fp['entry%u/measurement/%s' % (self.scanNr, self.dataSource)][:]
            except KeyError:
                print('couldnt find %s'%self.dataSource)
                raise NoDataException

        # for 1d or 2d detectors, you can also set axis labels and units
        # here, see existing classes like contrast_scan.
        
        return data
