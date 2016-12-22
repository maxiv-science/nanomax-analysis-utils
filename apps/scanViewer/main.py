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

        # add an interpolation toolbar
        self.ui.mapPlot.interpolToolbar = self.ui.mapPlot.addToolBar('Interpolation')
        self.ui.mapPlot.interpolBox = PyQt4.QtGui.QSpinBox(
            toolTip='Map oversampling relative to average step size')
        self.ui.mapPlot.interpolBox.setRange(1, 50)
        self.ui.mapPlot.interpolBox.setValue(5)
        self.ui.mapPlot.interpolMenu = PyQt4.QtGui.QComboBox(
            toolTip='Type of interpolation between scan positions')
        self.ui.mapPlot.interpolMenu.insertItems(1, ['nearest', 'linear', 'cubic'])
        self.ui.mapPlot.interpolToolbar.addWidget(self.ui.mapPlot.interpolBox)
        self.ui.mapPlot.interpolToolbar.addWidget(self.ui.mapPlot.interpolMenu)
        self.ui.mapPlot.interpolBox.valueChanged.connect(self.updateMap)
        self.ui.mapPlot.interpolMenu.currentIndexChanged.connect(self.updateMap)

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

        # connect the mask widget to update functions
        self.ui.diffPlot.maskToolsDockWidget.widget()._mask.sigChanged.connect(self.updateMap)
        self.ui.mapPlot.maskToolsDockWidget.widget()._mask.sigChanged.connect(self.updateImage)

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
            # add xrd data:
            try:
                self.scan.addData(filename, opts=['xrd',]+opts, name='xrd')
                print "loaded xrd data"
            except:
                print "no xrd data for this scan"
            # add xrf data:
            try:
                self.scan.addData(filename, opts=['xrf',]+opts, name='xrf')
                print "loaded xrf data"
            except:
                print "no xrf data for this scan"
            self.reset()
        self.ui.loadButton.clicked.connect(wrap)

    def togglePositions(self):
        xlims = self.ui.mapPlot.getGraphXLimits()
        ylims = self.ui.mapPlot.getGraphYLimits()
        if self.positionsAction.isChecked():
            self.ui.mapPlot.addCurve(self.scan.positions[:,0], self.scan.positions[:,1], 
                label='scan positions', symbol='+', color='red', linestyle=' ')
        else:
            self.ui.mapPlot.addCurve([], [], label='scan positions')
        self.ui.mapPlot.setGraphXLimits(*xlims)
        self.ui.mapPlot.setGraphYLimits(*ylims)

    def resetImage(self):
        self.ui.diffPlot.addImage(self.scan.meanData(name='xrd'), 
            colormap=self.diffCmap, legend='data')
        self.ui.diffPlot.setKeepDataAspectRatio(True)
        self.ui.diffPlot.setYAxisInverted(True)

    def resetMap(self):
        average = np.mean(self.scan.data['xrd'], axis=(1,2))
        method = self.ui.mapPlot.interpolMenu.currentText()
        sampling = self.ui.mapPlot.interpolBox.value()
        x, y, z = self.scan.interpolatedMap(average, sampling, 
            origin='ul', method=method)
        self.ui.mapPlot.addImage(z, colormap=self.mapCmap,
            scale=[abs(x[0,0]-x[0,1]), abs(y[0,0]-y[1,0])], 
            origin=[x.min(), y.min()],
            legend='data')
        self.ui.mapPlot.setKeepDataAspectRatio(True)
        self.ui.mapPlot.setYAxisInverted(True)

    def reset(self):
        self.resetImage()
        self.resetMap()

    def updateMap(self):
        # workaround to avoid the infinite loop which occurs when both
        # mask widgets are open at the same time
        self.ui.mapPlot.maskToolsDockWidget.setVisible(False)
        # store the limits to maintain zoom
        xlims = self.ui.mapPlot.getGraphXLimits()
        ylims = self.ui.mapPlot.getGraphYLimits()
        # get and check the mask array
        mask = self.ui.diffPlot.maskToolsDockWidget.widget().getSelectionMask()
        # if the mask is cleared, reset without wasting time
        if mask.sum() == 0:
            print 'building map by averaging all pixels'
            average = np.mean(self.scan.data['xrd'], axis=(1,2))
        else:
            ii, jj = np.where(mask)
            print 'building map by averaging %d pixels'%len(ii)
            average = np.mean(self.scan.data['xrd'][:, ii, jj], axis=1)
        method = self.ui.mapPlot.interpolMenu.currentText()
        sampling = self.ui.mapPlot.interpolBox.value()
        x, y, z = self.scan.interpolatedMap(average, sampling, origin='ul', method=method)
        self.ui.mapPlot.addImage(z, legend='data', 
            scale=[abs(x[0,0]-x[0,1]), abs(y[0,0]-y[1,0])],
            origin=[x.min(), y.min()])
        self.ui.mapPlot.setGraphXLimits(*xlims)
        self.ui.mapPlot.setGraphYLimits(*ylims)

    def updateImage(self):
        # workaround to avoid the infinite loop which occurs when both
        # mask widgets are open at the same time
        self.ui.diffPlot.maskToolsDockWidget.setVisible(False)
        # get and check the mask array
        mask = self.ui.mapPlot.maskToolsDockWidget.widget().getSelectionMask()
        if mask.sum() == 0:
            # the mask is empty, don't waste time with positions
            print 'building diffraction pattern from all positions'
            data = np.mean(self.scan.data['xrd'], axis=0)
        else:
            # recreate the interpolated grid from above, to find masked
            # positions on the oversampled grid
            dummy = np.zeros(self.scan.nPositions)
            x, y, z = self.scan.interpolatedMap(dummy, self.ui.mapPlot.interpolBox.value(), origin='ul')
            maskedPoints = np.vstack((x[np.where(mask)], y[np.where(mask)])).T
            pointSpacing2 = (x[0,1] - x[0,0])**2 + (y[0,0] - y[1,0])**2
            # go through actual positions and find the masked ones
            maskedPositions = []
            for i in range(self.scan.nPositions):
                # the minimum distance of the current position to a selected grid point:
                dist2 = np.sum((maskedPoints - self.scan.positions[i])**2, axis=1).min()
                if dist2 < pointSpacing2:
                    maskedPositions.append(i)
            print 'building diffraction pattern from %d positions'%len(maskedPositions)
            # get the average and replace the image with legend 'data',
            # retaining settings from reset()
            data = np.mean(self.scan.data['xrd'][maskedPositions], axis=0)
        self.ui.diffPlot.addImage(data, legend='data')

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