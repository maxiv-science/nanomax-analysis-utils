"""
This application loads data through subclasses of nmutils.core.Scan. 
These subclasses should have the option "dataSource" for data loading,
and they can have a dict "sourceDims" that assigns a dimensionality
to each data source. In addition, they can have whatever options they
want.
"""

try:
    from silx.gui.console import IPythonDockWidget
    HAS_QTCONSOLE = True
except ImportError:
    HAS_QTCONSOLE = False

# nmutils loads Eiger plugins, which have to be imported before h5py
import nmutils

# silx automatically chooses PyQt version. You can force it here
# by first importing it explicitly.
# #from PyQt5 import QtCore

# make sure silx is not too old (API features have appeared)
from distutils.version import LooseVersion
try:
    import silx
    assert LooseVersion(silx.version) >= LooseVersion('0.11')
except (ImportError, AssertionError):
    raise Exception('This application requires silx >= 0.11')

from silx.gui import qt
if not HAS_QTCONSOLE:
    print('Interactive console not available, make sure to have qtconsole installed and working. The following line should succeed on your system, \n    python -c "from silx.gui.console import IPythonDockWidget"')
from silx.gui.icons import getQIcon
from . import design
import sys
import gc
import numpy as np
from scipy.interpolate import griddata
print('silx %s using %s on Python %d.%d' % (silx.version, qt.BINDING, *sys.version_info[:2]))

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
            result = qt.QFileDialog.getOpenFileName()
            # PyQt5 gives a tuple here...
            if type(result) == tuple:
                result = result[0]
            self.ui.filenameBox.setText(result)
        self.ui.browseButton.clicked.connect(wrap)

        # populate the options tab
        self.ui.scanClassBox.currentIndexChanged.connect(self.populateOptions)

        # connect load button
        self.ui.loadButton.clicked.connect(self.load)

        # connect the PyMCA button to the slot on that widget
        self.ui.pymcaButton.clicked.connect(self.ui.xrfWidget.launchPyMCA)

        # dummy scan
        self._scan = None

        # select the last class and emit a signal
        self.ui.scanClassBox.setCurrentIndex(len(self.ui.scanClassBox)-1)

        # the ipython button
        self.ui.ipythonButton.setCheckable(True)
        self.ui.ipythonButton.setChecked(False)
        self.ui.ipythonButton.clicked.connect(self._toggle_ipython)
        if HAS_QTCONSOLE:
            self.console = IPythonDockWidget(parent=self,
                available_vars={'self': self, 'ui': self.ui, 'update':self._update},
                custom_banner=('Nanomax Scan Viewer console.\n'
                               + '"self" refers to the ScanViewer instance.\n'
                               + '"self.scan" refers to the current Scan object.\n'
                               + '"update()" refreshes all plots and images after modifying data.'
                               + '\n\n')
                )
            self.console.hide()
            self.addDockWidget(qt.Qt.BottomDockWidgetArea, self.console)
        else:
            self.ui.ipythonButton.setEnabled(False)

    def _toggle_ipython(self):
        if self.ui.ipythonButton.isChecked():
            self.console.show()
        else:
            self.console.hide()

    def _current_subclass_opts(self):
        subclass_ = str(self.ui.scanClassBox.currentText())
        try:
            subclass = getattr(nmutils.core, subclass_)
            opts = subclass.default_opts.copy()
        except AttributeError:
            opts = {}
        return opts

    def gatherOptions(self):
        # collect options from the options tab:
        opts = {}
        for name, w in self.formWidgets.items():
            if isinstance(w, qt.QCheckBox):
                val = bool(w.isChecked())
            elif isinstance(w, qt.QComboBox):
                val = str(w.currentText())
            elif isinstance(w, qt.QLineEdit) and not w.evaluate_me:
                val = str(w.text())
            elif isinstance(w, qt.QLineEdit) and w.evaluate_me:
                val = eval(str(w.text()))
            else:
                val = w.value()
            opts[name] = val

        # collect special options from the top of the GUI:
        subclass_opts = self._current_subclass_opts()
        if 'path' in subclass_opts.keys():
            opts['path'] = str(self.ui.filenameBox.text())
        if 'fileName' in subclass_opts.keys():
            opts['fileName'] = str(self.ui.filenameBox.text())
        if 'scanNr' in subclass_opts.keys():
            opts['scanNr'] = self.ui.scanNumberBox.value()

        return opts

    def populateOptions(self):
        grid = self.ui.optionsGrid
        # remove all old options
        for i in reversed(range(grid.count())): 
            grid.itemAt(i).widget().setParent(None)

        # add new ones
        opts = self._current_subclass_opts()
        self.formWidgets = {}
        i = 0
        for name, opt in opts.items():
            # special: the options scanNr and fileName (or path) have their input
            # widgets at the top of the GUI for convenience, while dataSource is
            # handled per tab.
            if name in ('dataSource', 'scanNr', 'path', 'fileName'):
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
            elif opt['type'] in (list, tuple):
                w = qt.QLineEdit()
                w.setText(str(opt['value']))
                w.evaluate_me = True
            elif type(opt['type']) in (list, tuple):
                w = qt.QComboBox()
                defaultindex = 0
                for j, item in enumerate(opt['type']):
                    w.addItem(item)
                    if item == opt['value']:
                        defaultindex = j
                w.setCurrentIndex(defaultindex)
            else:
                w = qt.QLineEdit()
                w.setText(opt['value'])
                w.evaluate_me = False
            grid.addWidget(w, i, 1)
            # save a dict of the options widgets, to parse when loading
            self.formWidgets[name] = w
            i += 1

        # add a vertical spacer on the last line to make the table more compact
        grid.setRowStretch(i, 1)

        # special treatment
        oldtext = str(self.ui.filenameBox.text())
        if 'path' in opts.keys() and oldtext.startswith('<'):
            self.ui.filenameBox.setText('<data path>')
        elif 'fileName' in opts.keys() and oldtext.startswith('<'):
            self.ui.filenameBox.setText('<input file>')
        self.ui.filenameBox.setDisabled(not ('path' in opts.keys() or 'fileName' in opts.keys()))
        self.ui.browseButton.setDisabled(not ('path' in opts.keys() or 'fileName' in opts.keys()))
        self.ui.scanNumberBox.setDisabled('scanNr' not in opts.keys())

        # per-tab dataSource option
        boxes = {self.ui.dataSource2dBox:2, self.ui.dataSource1dBox:1, self.ui.dataSource0dBox:0}
        subclass_ = str(self.ui.scanClassBox.currentText())
        try:
            subclass = getattr(nmutils.core, subclass_)
        except AttributeError:
            subclass = None

        for box, dim in boxes.items():
            box.clear()
            if subclass is not None:
                for name in opts['dataSource']['type']:
                    if hasattr(subclass, 'sourceDims') and not subclass.sourceDims[name] == dim:
                        continue
                    box.addItem(name)
                box.addItem('')

    def statusOutput(self, msg):
        self.ui.statusbar.showMessage(msg)
        self.ui.statusbar.showMessage(msg)

    def _update(self):
        """
        Dummy property for use with the ipython console, makes the plots
        update by activating the self.scan setter method.
        """
        self.scan = self.scan

    @property
    def scan(self):
        return self._scan

    @scan.setter
    def scan(self, scn):
        self._scan = scn
        if scn is None:
            # clear all the widgets' references
            self.ui.xrdWidget.setScan(None)
            self.ui.comWidget.setScan(None)
            self.ui.xrfWidget.setScan(None)
            self.ui.pymcaButton.setEnabled(False)
            self.ui.scalarWidget.setScan(None)
            # do this just to be sure
            del(self._scan)
            self._scan = None
            # enforce garbage collection for good measure
            gc.collect()
        else:
            if '2d' in scn.data.keys():
                self.ui.xrdWidget.setScan(scn)
                self.ui.comWidget.setScan(scn)
            if '1d' in scn.data.keys():
                self.ui.xrfWidget.setScan(scn)
                self.ui.pymcaButton.setEnabled(True)
            if '0d' in scn.data.keys():
                self.ui.scalarWidget.setScan(scn)

    def load(self):
        try:
            self.statusOutput("Loading data...")

            if self.scan and not self.ui.appendBox.isChecked():
                print("Deleting previous scan from memory")
                self.scan = None

            # construct a scan
            try:
                subclass = str(self.ui.scanClassBox.currentText())
                scan_ = getattr(nmutils.core, subclass)()
            except AttributeError:
                self.statusOutput("Invalid subclass!")
                return

            # get options
            opts = self.gatherOptions()

            # add 2D data:
            try:
                source = self.ui.dataSource2dBox.currentText()
                if not source:
                    raise nmutils.NoDataException
                scan_.addData(dataSource=source, name='2d', **opts)
                dim = len(scan_.data['2d'].shape[1:])
                if not dim == 2:
                    scan_.removeData(name='2d')
                    print("loaded 2D was %uD, discarding" % dim)
                    raise nmutils.NoDataException
                print("loaded 2D data: %d positions, %d x %d pixels"%(scan_.data['2d'].shape))
            except MemoryError:
                print("Out of memory! Consider cropping or binning your images")
            except nmutils.NoDataException:
                print("no 2D data found")
            except KeyboardInterrupt:
                print("cancelled")
                self.statusOutput("")
                return

            # add 1D data:
            try:
                source = self.ui.dataSource1dBox.currentText()
                if not source:
                    raise nmutils.NoDataException
                scan_.addData(dataSource=source, name='1d', **opts)
                dim = len(scan_.data['1d'].shape[1:])
                if not dim == 1:
                    scan_.removeData(name='1d')
                    print("loaded 1D was %uD, discarding" % dim)
                    raise nmutils.NoDataException
                print("loaded 1D data: %d positions, %d channels"%(scan_.data['1d'].shape))
            except nmutils.NoDataException:
                print("no 1D data found")
            except KeyboardInterrupt:
                print("cancelled")
                self.statusOutput("")
                return

            # add 0D data:
            try:
                source = self.ui.dataSource0dBox.currentText()
                if not source:
                    raise nmutils.NoDataException
                scan_.addData(dataSource=source, name='0d', **opts)
                dim = len(scan_.data['0d'].shape[1:])
                if not dim == 0:
                    scan_.removeData(name='0d')
                    print("loaded 0D was %uD, discarding" % dim)
                    raise nmutils.NoDataException
                print("loaded 0D data: %d positions"%(scan_.data['0d'].shape))
            except nmutils.NoDataException:
                print("no 0D data found")
            except KeyboardInterrupt:
                print("cancelled")
                self.statusOutput("")
                return

            # maybe there was no data at all
            if scan_.positions is None:
                self.statusOutput("No data found")
                return

            # append or store loaded scan as it is
            if self.scan is None:
                merged = scan_
            else:
                merged = self.scan
                merged.merge(scan_)

            # update the widgets
            if merged.nPositions > 1:
                self.scan = merged
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

