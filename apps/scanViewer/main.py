import PyQt4
from silx.gui import qt
from silx.gui.plot.PlotActions import PlotAction
from silx.gui.icons import getQIcon
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

        ###### INITIALIZE THE GLOBAL WIDGETS
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
            else:
                self.ui.scanOptionsBox.setText('')
        self.ui.scanClassBox.currentIndexChanged.connect(wrap)

        # connect load button
        self.ui.loadButton.clicked.connect(self.load)

        ###### INITIALIZE THE XRD TAB
        # add a positionsAction button to the toolbar - didn't work with
        # PlotAction as the silx tutorial says so using normal PyQT.
        self.ui.xrdMapPlot.positionsAction = qt.QAction('positions', self.ui.xrdMapPlot, checkable=True)
        self.ui.xrdMapPlot.toolBar().addAction(self.ui.xrdMapPlot.positionsAction)
        self.ui.xrdMapPlot.positionsAction.triggered.connect(self.toggleXrdPositions)

        # customize the mask tools for use as ROI selectors
        # unfortunately, tooltip and icon reset each other, so only changing the icon.
        self.ui.xrdMapPlot.maskToolsDockWidget.setWindowTitle('scan map ROI')
        self.ui.xrdMapPlot.maskAction.setToolTip('Select a scan map region of interest')
        self.ui.xrdMapPlot.maskAction.setIcon(getQIcon('image-select-box'))
        self.ui.xrdImagePlot.maskToolsDockWidget.setWindowTitle('diffraction ROI')
        self.ui.xrdImagePlot.maskAction.setToolTip('Select a diffraction region of interest')
        self.ui.xrdImagePlot.maskAction.setIcon(getQIcon('image-select-box'))

        # add an interpolation toolbar
        self.ui.xrdMapPlot.interpolToolbar = self.ui.xrdMapPlot.addToolBar('Interpolation')
        self.ui.xrdMapPlot.interpolBox = PyQt4.QtGui.QSpinBox(
            toolTip='Map oversampling relative to average step size')
        self.ui.xrdMapPlot.interpolBox.setRange(1, 50)
        self.ui.xrdMapPlot.interpolBox.setValue(5)
        self.ui.xrdMapPlot.interpolMenu = PyQt4.QtGui.QComboBox(
            toolTip='Type of interpolation between scan positions')
        self.ui.xrdMapPlot.interpolMenu.insertItems(1, ['nearest', 'linear', 'cubic'])
        self.ui.xrdMapPlot.interpolToolbar.addWidget(self.ui.xrdMapPlot.interpolMenu)
        self.ui.xrdMapPlot.interpolToolbar.addWidget(PyQt4.QtGui.QLabel(' N:'))
        self.ui.xrdMapPlot.interpolToolbar.addWidget(self.ui.xrdMapPlot.interpolBox)
        self.ui.xrdMapPlot.interpolBox.valueChanged.connect(self.updateXrdMap)
        self.ui.xrdMapPlot.interpolMenu.currentIndexChanged.connect(self.updateXrdMap)

        # connect the mask widget to update functions
        self.ui.xrdImagePlot.maskToolsDockWidget.widget()._mask.sigChanged.connect(self.updateXrdMap)
        self.ui.xrdMapPlot.maskToolsDockWidget.widget()._mask.sigChanged.connect(self.updateXrdImage)

    def load(self):
        subclass = str(self.ui.scanClassBox.currentText())
        filename = str(self.ui.filenameBox.text())
        self.scan = getattr(nmutils.core, subclass)()
        opts = str(self.ui.scanOptionsBox.text()).split()
        # add xrd data:
        self.scan.addData(filename, opts=['xrd',]+opts, name='xrd')
        try:
            print "loaded xrd data: %d positions, %d x %d pixels"%(self.scan.data['xrd'].shape)
        except:
            print "no xrd data found"
        # add xrf data:
        try:
            self.scan.addData(filename, opts=['xrf',]+opts, name='xrf')
        except: pass
        try:
            print "loaded xrf data: %d positions, %d channels"%(self.scan.data['xrf'].shape)
        except:
            print "no xrf data found"

        self.ui.comWidget.setScan(self.scan)

        self.reset()
        
    def toggleXrdPositions(self):
        xlims = self.ui.xrdMapPlot.getGraphXLimits()
        ylims = self.ui.xrdMapPlot.getGraphYLimits()
        if self.ui.xrdMapPlot.positionsAction.isChecked():
            self.ui.xrdMapPlot.addCurve(self.scan.positions[:,0], self.scan.positions[:,1], 
                label='scan positions', symbol='+', color='red', linestyle=' ')
        else:
            self.ui.xrdMapPlot.addCurve([], [], label='scan positions')
        self.ui.xrdMapPlot.setGraphXLimits(*xlims)
        self.ui.xrdMapPlot.setGraphYLimits(*ylims)

    def resetXrdImage(self):
        self.ui.xrdImagePlot.addImage(self.scan.meanData(name='xrd'), 
            colormap=self.diffCmap, legend='data')
        self.ui.xrdImagePlot.setKeepDataAspectRatio(True)
        self.ui.xrdImagePlot.setYAxisInverted(True)

    def resetXrdMap(self):
        average = np.mean(self.scan.data['xrd'], axis=(1,2))
        method = self.ui.xrdMapPlot.interpolMenu.currentText()
        sampling = self.ui.xrdMapPlot.interpolBox.value()
        x, y, z = self.scan.interpolatedMap(average, sampling, 
            origin='ul', method=method)
        self.ui.xrdMapPlot.addImage(z, colormap=self.mapCmap,
            scale=[abs(x[0,0]-x[0,1]), abs(y[0,0]-y[1,0])], 
            origin=[x.min(), y.min()],
            legend='data')
        self.ui.xrdMapPlot.setKeepDataAspectRatio(True)
        self.ui.xrdMapPlot.setYAxisInverted(True)

    def reset(self):
        self.resetXrdImage()
        self.resetXrdMap()

    def updateXrdMap(self):
        # workaround to avoid the infinite loop which occurs when both
        # mask widgets are open at the same time
        self.ui.xrdMapPlot.maskToolsDockWidget.setVisible(False)
        # store the limits to maintain zoom
        xlims = self.ui.xrdMapPlot.getGraphXLimits()
        ylims = self.ui.xrdMapPlot.getGraphYLimits()
        # get and check the mask array
        mask = self.ui.xrdImagePlot.maskToolsDockWidget.widget().getSelectionMask()
        # if the mask is cleared, reset without wasting time
        if mask.sum() == 0:
            print 'building map by averaging all pixels'
            average = np.mean(self.scan.data['xrd'], axis=(1,2))
        else:
            ii, jj = np.where(mask)
            print 'building map by averaging %d pixels'%len(ii)
            average = np.mean(self.scan.data['xrd'][:, ii, jj], axis=1)
        method = self.ui.xrdMapPlot.interpolMenu.currentText()
        sampling = self.ui.xrdMapPlot.interpolBox.value()
        x, y, z = self.scan.interpolatedMap(average, sampling, origin='ul', method=method)
        self.ui.xrdMapPlot.addImage(z, legend='data', 
            scale=[abs(x[0,0]-x[0,1]), abs(y[0,0]-y[1,0])],
            origin=[x.min(), y.min()])
        self.ui.xrdMapPlot.setGraphXLimits(*xlims)
        self.ui.xrdMapPlot.setGraphYLimits(*ylims)

    def updateXrdImage(self):
        # workaround to avoid the infinite loop which occurs when both
        # mask widgets are open at the same time
        self.ui.xrdImagePlot.maskToolsDockWidget.setVisible(False)
        # get and check the mask array
        mask = self.ui.xrdMapPlot.maskToolsDockWidget.widget().getSelectionMask()
        if mask.sum() == 0:
            # the mask is empty, don't waste time with positions
            print 'building diffraction pattern from all positions'
            data = np.mean(self.scan.data['xrd'], axis=0)
        else:
            # recreate the interpolated grid from above, to find masked
            # positions on the oversampled grid
            dummy = np.zeros(self.scan.nPositions)
            x, y, z = self.scan.interpolatedMap(dummy, self.ui.xrdMapPlot.interpolBox.value(), origin='ul')
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
        self.ui.xrdImagePlot.addImage(data, legend='data')

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