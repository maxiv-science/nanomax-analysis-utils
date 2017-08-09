"""
This application loads data through subclasses of nmutils.core.Scan. 
These subclasses should have the option "dataType" for data loading,
and should expect the 'xrd' and 'xrf' values for this keyword. In 
addition, they can have whatever options they want.
"""

# hdf5plugin is needed to read compressed Eiger files, and has to be
# imported before h5py.
try:
    import hdf5plugin 
except ImportError:
    print "hdf5plugin not found - won't be able to read compressed Eiger files"

# make sure silx is not too old (API features have appeared)
from distutils.version import LooseVersion
try:
    import silx
    assert LooseVersion(silx.version) >= LooseVersion('0.4.0')
except:
    raise Exception('This application requires silx >= 0.4.0')

from silx.gui import qt
from silx.gui.icons import getQIcon
import sys
import gc
import design
import numpy as np
from scipy.interpolate import griddata
import nmutils
import time

# using the single inheritance method here, as described here,
# http://pyqt.sourceforge.net/Docs/PyQt4/designer.html
#
# this means:
# 1) create a new class for the containing widget, which will 
#    have all the code and connections
# 2) create an UI object from qt-designer and own it as self.ui
# 3) run its setupUi method and pass the containing widget (self)
#
class ScanViewer(qt.QMainWindow):

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
            for subclass_ in subclass.__subclasses__():
                self.ui.scanClassBox.addItem(subclass_.__name__)

        # connect browse button
        def wrap():
            self.ui.filenameBox.setText(qt.QFileDialog.getOpenFileName())
        self.ui.browseButton.clicked.connect(wrap)

        # populate the options tab
        self.ui.scanClassBox.currentIndexChanged.connect(self.populateOptions)

        # connect load button
        self.ui.loadButton.clicked.connect(self.load)

        # dummy scan
        self.scan = None

    def gatherOptions(self):
        # should return a dict of kwargs based on the options fields
        opts = {}
        for name, w in self.formWidgets.iteritems():
            if isinstance(w, qt.QCheckBox):
                val = bool(w.isChecked())
            elif isinstance(w, qt.QLineEdit):
                val = str(w.text())
            else:
                val = w.value()
            opts[name] = val
        return opts

    def populateOptions(self):
        grid = self.ui.optionsGrid
        # remove all old options
        for i in reversed(range(grid.count())): 
            grid.itemAt(i).widget().setParent(None)
        # add new ones
        subclass_ = str(self.ui.scanClassBox.currentText())
        try:
            subclass = getattr(nmutils.core, subclass_)
        except:
            return
        opts = subclass.default_opts.copy()
        self.formWidgets = {}
        i = 0
        for name, opt in opts.iteritems():
            # special: dataType should not have a field
            if name == 'dataType':
                continue
            grid.addWidget(qt.QLabel(name), i, 0)
            grid.addWidget(qt.QLabel(opt['doc']), i, 2)
            if opt['type'] == int:
                w = qt.QSpinBox()
                w.setMaximum(9999)
                w.setValue(opt['value'])
            elif opt['type'] == float:
                w = qt.QDoubleSpinBox()
                w.setValue(opt['value'])
            elif opt['type'] == bool:
                w = qt.QCheckBox()
                w.setChecked(opt['value'])
            else:
                w = qt.QLineEdit()
                w.setText(opt['value'])
            grid.addWidget(w, i, 1)
            # save a dict of the options widgets, to parse when loading
            self.formWidgets[name] = w
            i += 1

    def statusOutput(self, msg):
        self.ui.statusbar.showMessage(msg)
        self.ui.statusbar.showMessage(msg)

    def load(self):
        try:
            self.statusOutput("Loading data...")
            if self.scan:
                print "Deleting previous scan from memory"
                # These references have to go
                self.ui.comWidget.setScan(None)
                self.ui.xrdWidget.setScan(None)
                self.ui.xrfWidget.setScan(None)
                del(self.scan)
                # enforcing garbage collection for good measure
                gc.collect()

            # construct a scan
            try:
                subclass = str(self.ui.scanClassBox.currentText())
                self.scan = getattr(nmutils.core, subclass)()
            except:
                raise Exception("Invalid subclass")

            # get options
            scannr = self.ui.scanNumberBox.value()
            filename = str(self.ui.filenameBox.text())
            opts = self.gatherOptions()

            # add xrd data:
            try:
                self.scan.addData(scannr=scannr, filename=filename, dataType='xrd', name='xrd', **opts)
                print "loaded xrd data: %d positions, %d x %d pixels"%(self.scan.data['xrd'].shape)
                has_xrd = True
            except MemoryError:
                print "Out of memory! Consider cropping or binning your images"
                has_xrd = False
            except:
                print "no xrd data found"
                has_xrd = False

            # add xrf data:
            try:
                self.scan.addData(scannr=scannr, filename=filename, dataType='xrf', name='xrf', **opts)
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
            self.statusOutput("")
        except:
            self.statusOutput("Loading failed. See terminal output for details.")
            raise

if __name__ == '__main__':
    # you always need a qt app
    app = qt.QApplication(sys.argv)
    # for convenience, you can pass the filename as an argument
    fn = None
    if len(sys.argv) >= 2:
        fn = sys.argv[1]
    # instantiate and show the main object
    viewer = ScanViewer(fn)
    viewer.show()
    # run the app
    app.exec_()

