"""
Example script to show how a ScanViewer object can be created and
acted upon directly, here to load a series of scans together.
"""

import nmutils
from nmutils.gui.scanViewer import ScanViewer
from silx.gui import qt
import sys

# define a set of scan numbers
scan_numbers = range(2, 32+1) # to 32
#scan_numbers = (2, 6, 10, 14, 18) # to 32
#scan_numbers = (14,)

# loop through these and load the data, merging them together after each
for i, n in enumerate(scan_numbers):
	new = nmutils.core.flyscan_nov2018()
	new.addData(dataSource='xspress3', normalize_by_I0=True, globalPositions=True,
		#fileName='/data/staff/nanomax/commissioning_2019-1/20190415_Vajda/raw/sphere-1/sphere-1.h5',
		fileName='/home/alex/tmp/sphere-1/sphere-1.h5',
		scanNr=n, name='1d', xrfCropping=[0,1800])
	if i == 0:
		scan = new
		continue
	scan.merge(new)	

# create the ScanViewer instance, do some qt magic that you always need,
# and pass the loaded data to the viewer.
app = qt.QApplication(sys.argv)
viewer = ScanViewer()
viewer.scan = scan
viewer.show()
app.exec_()
