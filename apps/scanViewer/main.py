import PyQt4
from silx.gui import qt
from silx.gui.plot.PlotActions import PlotAction
import sys
import design
import nmutils
import numpy as np
from scipy.interpolate import griddata


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

        # add a positionsAction button to the toolbar - didn't work with
        # PlotAction as the silx tutorial says so using normal PyQT.
        self.positionsAction = qt.QAction('positions', self.ui.mapPlot, checkable=True)
        self.ui.mapPlot.toolBar().addAction(self.positionsAction)
        self.positionsAction.triggered.connect(self.togglePositions)

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
            else:
                self.ui.scanOptionsBox.setText('')
        self.ui.scanClassBox.currentIndexChanged.connect(wrap)

        # connect load button
        def wrap():
            subclass = str(self.ui.scanClassBox.currentText())
            filename = str(self.ui.filenameBox.text())
            self.scan = getattr(nmutils.core, subclass)()
            opts = str(self.ui.scanOptionsBox.text()).split()
            self.scan.addData(filename, opts=opts)
            self.reset()

        self.ui.loadButton.clicked.connect(wrap)

    def togglePositions(self):
        if self.positionsAction.isChecked():
            self.ui.mapPlot.addCurve(self.scan.positions[:,0], self.scan.positions[:,1], 
                label='scan positions', symbol=',', linestyle=' ',
                selectable=True)
        else:
            self.ui.mapPlot.addCurve([], [], label='scan positions')

    def reset(self):
        # diffraction pattern
        self.ui.diffPlot.addImage(self.scan.meanData(), colormap=self.diffCmap, 
            replace=True, selectable=True)
        self.ui.diffPlot.setKeepDataAspectRatio(True)
        self.ui.diffPlot.setYAxisInverted(True)
        # map
        imshape = self.scan.meanData().shape
        x, y, z = interpolate([0, imshape[0], 0, imshape[1]], self.scan, 5)
        self.ui.mapPlot.addImage(z, colormap=self.mapCmap, replace=True,
            scale=[x[0,1]-x[0,0], y[1,0]-y[0,0]], origin=[x.max(), y.max()])
        self.ui.mapPlot.setKeepDataAspectRatio(True)

def interpolate(roi, scan, oversampling):
    """ 
    Helper function which provides a regular and interpolated xy map of
    a scan, integrated over a roi. The map is in the coordinates defined
    in the Scan class, that is, right-handed lab coordinates in the 
    sample frame, with x horizontal and y vertical, and the origin in 
    the bottom right of the sample map array.
    """
    if roi[0] == roi[1]: roi[1] += 1
    if roi[2] == roi[3]: roi[3] += 1
    integral = np.mean(scan.data['data0'][:, roi[0]:roi[1], roi[2]:roi[3]], axis=(1,2))

    xMin, xMax = np.min(scan.positions[:,0]), np.max(scan.positions[:,0])
    yMin, yMax = np.min(scan.positions[:,1]), np.max(scan.positions[:,1])

    # here we need special cases for 1d scans (where x or y doesn't vary)
    if np.abs(yMax - yMin) < 1e-12:
        stepsize = (xMax - xMin) / float(scan.nPositions) / oversampling
        margin = oversampling * stepsize / 2
        y, x = np.mgrid[yMin-(stepsize*oversampling*5)/2:yMin+(stepsize*oversampling*5)/2:stepsize, xMax+margin:xMin-margin:-stepsize]
    elif np.abs(xMax - xMin) < 1e-12:
        stepsize = (yMax - yMin) / float(scan.nPositions) / oversampling
        margin = oversampling * stepsize / 2
        y, x = np.mgrid[yMax+margin:yMin-margin:-stepsize, xMin-(stepsize*oversampling*5)/2:xMin+(stepsize*oversampling*5)/2:stepsize]
    else:
        stepsize = np.sqrt((xMax-xMin) * (yMax-yMin) / float(scan.nPositions)) / oversampling
        margin = oversampling * stepsize / 2
        y, x = np.mgrid[yMax+margin:yMin-margin:-stepsize, xMax+margin:xMin-margin:-stepsize]
    print stepsize
    z = griddata(scan.positions, integral, (x, y), method='nearest')
    return x, y, z


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