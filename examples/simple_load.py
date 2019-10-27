"""
This is an example script showing how to load and operate on data.
"""

import nmutils

# create an object of the appropriate Scan subclass,
scan = nmutils.core.contrast_flyscan()

# to see the options available to this specific subclass,
# we can print the default_opts dictionary,
print(nmutils.core.contrast_flyscan.default_opts)

# then, knowing what the options are, it's easy to load data,
scan.addData(name='my_waxs_data', dataSource='pilatus1m', scanNr=3,
             path='/data/staff/nanomax/commissioning_2019-2/20191008/raw/Si_14keV')

# we now have a dictionary where each dataset, for example the data
# from each detector, is an entry.
print(scan.data.keys())
print(scan.data['my_waxs_data'].shape) # the first index is the position, the following indices are the data dimensions (pixels for example).

# now we're free to operate on the data as we wish,
import numpy as np
my_average_image = np.mean(scan.data['my_waxs_data'], axis=0) # average over the images
my_average_sequence = np.mean(scan.data['my_waxs_data'], axis=(1,2)) # average over the pixels

