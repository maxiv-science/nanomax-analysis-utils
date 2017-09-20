"""
This window is launched from scanViewer and does FMRE on a loaded scan.
"""

# silx version already checked in main
from silx.gui import qt
from silx.gui.icons import getQIcon
import nmutils.utils.fmre as fmre
import design
import sys
import numpy as np

# using the single inheritance method here, as described in main.py

class FmreWindow(qt.QMainWindow):

    def __init__(self, scan=None, roi=None):

        # Qt base class constructor
        super(FmreWindow, self).__init__()

        # instantiate the form class and set it up in the current QMainWindow
        self.ui = design.Ui_MainWindow()
        self.ui.setupUi(self)

        # connect run button
        self.ui.runButton.clicked.connect(self.run)

        # connect browse button
        def wrap():
            self.ui.filenameBox.setText(qt.QFileDialog.getOpenFileName())
        self.ui.browseButton.clicked.connect(wrap)

        # populate the options grid
        self.populateOptions(roi)

        # scan and probe file
        self.scan = scan

    def run(self):
        opts = self.gatherOptions()
        ptyr_file = self.ui.filenameBox.text()
        image, res, info = fmre.enhance(self.scan, ptyr_file, **opts)
        self.ui.plotWidget.addImage(image, legend='data', resetzoom=False)
                #scale=[abs(x[0,0]-x[0,1]), abs(y[0,0]-y[1,0])],
                #origin=[x.min(), y.min()], resetzoom=False)

    def gatherOptions(self):
        # should return a dict of kwargs based on the options fields
        opts = {}
        for name, w in self.formWidgets.iteritems():
            if isinstance(w, qt.QCheckBox):
                val = bool(w.isChecked())
            elif isinstance(w, qt.QLineEdit):
                val = str(w.text())
            elif isinstance(w, qt.QComboBox):
                val = str(w.currentText())
            else:
                val = w.value()
            opts[name] = val
        return opts

    def populateOptions(self, roi_override):
        grid = self.ui.optionsGrid
        opts = fmre.DEFAULTS.copy()
        self.formWidgets = {}
        i = 0
        for name, opt in opts.iteritems():
            grid.addWidget(qt.QLabel(name), i, 0)
            grid.addWidget(qt.QLabel(opt['doc']), i, 2)
            if 'alternatives' in opt.keys():
                # make a drop down menu
                w = qt.QComboBox()
                for alt in opt['alternatives']:
                    w.addItem(alt)
                w.setCurrentIndex(opt['alternatives'].index(opt['value']))
            elif opt['type'] == int:
                w = qt.QSpinBox()
                max_ = opt['max'] if 'max' in opt.keys() else 9999
                min_ = opt['min'] if 'min' in opt.keys() else 0
                w.setRange(min_, max_)
                w.setValue(opt['value'])
            elif opt['type'] == float:
                w = qt.QDoubleSpinBox()
                max_ = opt['max'] if 'max' in opt.keys() else 9999
                min_ = opt['min'] if 'min' in opt.keys() else 0
                step_ = opt['step'] if 'step' in opt.keys() else .1
                dec_ = -np.log10(step_) * 2
                w.setRange(min_, max_)
                w.setSingleStep(step_)
                w.setValue(opt['value'])
                w.setDecimals(dec_)
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
        if roi_override:
            try:
                self.formWidgets['roi'].setText('%d %d'%tuple(roi_override))
            except:
                pass

if __name__ == '__main__':

    # testing data
    import nmutils
    myscan = nmutils.core.nanomaxScan_stepscan_april2017()
    # Add data to the scan
    myscan.addData(
        dataType='xrf', 
        filename='/home/alex/tmp/JWX33.h5',
        scannr=72,
    )
    ptyrfile = '/home/alex/tmp/scan72_DMML_ML.ptyr'

    # you always need a qt app
    app = qt.QApplication(sys.argv)
    # instantiate and show the main object
    viewer = FmreWindow(myscan, ptyrfile)
    viewer.show()
    # run the app
    app.exec_()

