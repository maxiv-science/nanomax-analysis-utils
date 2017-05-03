# hdf5plugin is needed to read compressed Eiger files, and has to be
# imported before h5py.
try:
    import hdf5plugin 
except ImportError:
    print "hdf5plugin not found - won't be able to read compressed Eiger files"

# temporarily suppress deprecation warnings from silx
import logging
deprecation_logger = logging.getLogger("DEPRECATION")
deprecation_logger.setLevel(logging.ERROR)

import PyQt4
from silx.gui import qt
from silx.gui.icons import getQIcon
import sys
import gc
import design
import numpy as np
from scipy.interpolate import griddata
import nmutils

# using the single inheritance method here, as described here,
# http://pyqt.sourceforge.net/Docs/PyQt4/designer.html
#
# this means:
# 1) create a new class for the containing widget, which will 
#    have all the code and connections
# 2) create an UI object from qt-designer and own it as self.ui
# 3) run its setupUi method and pass the containing widget (self)
#
class ScanViewer(PyQt4.QtGui.QMainWindow):

    def __init__(self, filename=None):

        # Qt base class constructor
        super(ScanViewer, self).__init__()

        # instantiate the form class and set it up in the current QMainWindow
        self.ui = design.Ui_MainWindow()
        self.ui.setupUi(self)

        # possibly set initial values
        if filename:
            self.ui.filenameBox.setText(filename)

        # set up default plot settings
        self.diffCmap = {'name':'temperature', 'autoscale':True, 'normalization':'log'}
        self.mapCmap = {'name':'gray', 'autoscale':True, 'normalization':'linear'}

        # populate the scan class list
        self.ui.scanClassBox.addItem('select scan type')
        for subclass in nmutils.core.Scan.__subclasses__():
            self.ui.scanClassBox.addItem(subclass.__name__)

        # connect browse button
        def wrap():
            self.ui.filenameBox.setText(PyQt4.QtGui.QFileDialog.getOpenFileName())
        self.ui.browseButton.clicked.connect(wrap)

        # hint at the subclass options when a subclass is selected
        def wrap():
            subclass = str(self.ui.scanClassBox.currentText())
            if subclass == 'nanomaxScan_flyscan_week48':
                self.ui.scanOptionsBox.setText('<scannr> (<ROI size>)')
            elif subclass == 'nanomaxScan_stepscan_week48':
                self.ui.scanOptionsBox.setText('<scannr>')
            elif subclass == 'id13Scan':
                self.ui.scanOptionsBox.setText('<ROI size>')
            elif subclass == 'nanomaxScan_stepscan_april2017':
                self.ui.scanOptionsBox.setText('<scannr>')
            elif subclass == 'nanomaxScan_flyscan_april2017':
                self.ui.scanOptionsBox.setText('<scannr> (<ROI size>)')
            else:
                self.ui.scanOptionsBox.setText('')
        self.ui.scanClassBox.currentIndexChanged.connect(wrap)

        # connect load button
        self.ui.loadButton.clicked.connect(self.load)

	# dummy scan
	self.scan = None

    def load(self):
        print "Loading data..."
        subclass = str(self.ui.scanClassBox.currentText())
        filename = str(self.ui.filenameBox.text())
    	if self.scan:
            print "Deleting previous scan from memory"
            # These references have to go
            self.ui.comWidget.setScan(None)
            self.ui.xrdWidget.setScan(None)
            self.ui.xrfWidget.setScan(None)
            del(self.scan)
            # enforcing garbage collection for good measure
            gc.collect()
        self.scan = getattr(nmutils.core, subclass)()
        opts = str(self.ui.scanOptionsBox.text()).split()

        # add xrd data:
        self.scan.addData(filename, opts=['xrd',]+opts, name='xrd')
        try:
            print "loaded xrd data: %d positions, %d x %d pixels"%(self.scan.data['xrd'].shape)
            has_xrd = True
        except:
            print "no xrd data found"
            has_xrd = False

        # add xrf data:
        try:
            self.scan.addData(filename, opts=['xrf',]+opts, name='xrf')
        except: pass
        try:
            print "loaded xrf data: %d positions, %d channels"%(self.scan.data['xrf'].shape)
            has_xrf = True
        except:
            print "no xrf data found"
            has_xrf = False

        if has_xrd:
            self.ui.comWidget.setScan(self.scan)
            self.ui.xrdWidget.setScan(self.scan)
        if has_xrf:
            self.ui.xrfWidget.setScan(self.scan)

if __name__ == '__main__':
    # you always need a qt app
    app = PyQt4.QtGui.QApplication(sys.argv)
    # for convenience, you can pass the filename as an argument
    fn = None
    if len(sys.argv) >= 2:
        fn = sys.argv[1]
    # instantiate and show the main object
    viewer = ScanViewer(fn)
    viewer.show()
    # run the app
    app.exec_()

