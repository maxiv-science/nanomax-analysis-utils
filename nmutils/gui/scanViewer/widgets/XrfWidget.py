from silx.gui.plot import PlotWindow, Plot1D
from silx.gui.plot.Profile import ProfileToolBar
from silx.gui.icons import getQIcon
from silx.gui import qt
import numpy as np
import time
import h5py
import os, tempfile

from .XrdWidget import MapWidget

class SpectrumWidget(PlotWindow):
    """
    Reimplementation of Plot1D, with custom tools.
    """

    def __init__(self, parent=None):
        super(SpectrumWidget, self).__init__(parent=parent, backend=None,
                                     resetzoom=True, autoScale=True,
                                     logScale=True, grid=True,
                                     curveStyle=True, colormap=False,
                                     aspectRatio=False, yInverted=False,
                                     copy=True, save=True, print_=False,
                                     control=False, position=True,
                                     roi=True, mask=False, fit=False)
        if parent is None:
            self.setWindowTitle('Plot1D')
        self.setGraphXLabel('Detector channel')
        self.setGraphYLabel('Signal')
        self.setGraphTitle('Fluorescence emission')
        self.setYAxisLogarithmic(True)

class XrfWidget(qt.QWidget):
    def __init__(self, parent=None):
        
        super(XrfWidget, self).__init__()
        self.map = MapWidget(self)
        self.spectrum = SpectrumWidget(self)
        self.setLayout(qt.QHBoxLayout())
        splitter = qt.QSplitter()
        splitter.addWidget(self.spectrum)
        splitter.addWidget(self.map)
        self.layout().addWidget(splitter)

        # connect the interpolation thingies
        self.map.interpolBox.valueChanged.connect(self.updateMap)

        # connect the positions button
        self.map.positionsAction.triggered.connect(self.togglePositions)

        # connect the clicker box
        self.map.indexBox.valueChanged.connect(self.selectByIndex)

        # connect the mask widget to the update
        self.map.getMaskToolsDockWidget().widget()._mask.sigChanged.connect(self.updateSpectrum)
        self.spectrum.getCurvesRoiWidget().sigROISignal.connect(self.updateMap)

        # keep track of map selections by ROI or by index
        self.selectionMode = 'roi' # 'roi' or 'ind'

        # workaround to avoid multiple updates
        self.last_map_update = 0.0

        # a list of pymca windows to keep then in scope
        self.pymcaWindows = []

    def setScan(self, scan):
        self.scan = scan
        if not scan:
            self.map.removeImage('data')
            self.spectrum.addCurve([], [], legend='data')
            return
        # avoid old position grids:
        if self.map.positionsAction.isChecked():
            self.togglePositions()
        self.map.indexBox.setMaximum(scan.nPositions - 1)
        self.resetMap()
        self.resetSpectrum()

    def resetMap(self):
        self.updateMap()
        self.map.resetZoom()

    def resetSpectrum(self):
        self.updateSpectrum()
        self.spectrum.resetZoom()

    def updateMap(self):
        if self.scan is None:
            return
        elif time.time() - self.last_map_update < .05:
            return

        try:
            self.window().statusOutput('Building 1D data map...')
            # workaround to avoid the infinite loop which occurs when both
            # mask widgets are open at the same time
            self.map.getMaskToolsDockWidget().setVisible(False)
            # store the limits to maintain zoom
            xlims = self.map.getGraphXLimits()
            ylims = self.map.getGraphYLimits()
            # get ROI information
            roi = self.spectrum.getCurvesRoiWidget().currentRoi
            if roi is None:
                print "building 1D data map from the whole spectrum"
                average = np.mean(self.scan.data['1d'], axis=1)
            else:
                lower = int(np.floor(roi.getFrom()))
                upper = int(np.ceil(roi.getTo()))
                print "building 1D data map from channels %d to %d"%(lower, upper)
                average = np.mean(self.scan.data['1d'][:, lower:upper], axis=1)

            # interpolate and plot map
            sampling = self.map.interpolBox.value()
            x, y, z = self.scan.interpolatedMap(average, sampling, origin='ul', method='nearest')
            self.map.addImage(z, legend='data', 
                scale=[abs(x[0,0]-x[0,1]), abs(y[0,0]-y[1,0])],
                origin=[x.min(), y.min()], resetzoom=False)
            self.map.setGraphXLimits(*xlims)
            self.map.setGraphYLimits(*ylims)
            self.window().statusOutput('')
            self.last_map_update = time.time()
        except:
            self.window().statusOutput('Failed to build 1D data map. See terminal output.')
            raise

    def updateSpectrum(self):
        if self.scan is None:
            return
        try:
            self.window().statusOutput('Building 1D curve...')
            if self.selectionMode == 'ind':
                index = self.map.indexBox.value()
                data = self.scan.data['1d'][index]
            elif self.selectionMode == 'roi':
                self.indexMarkerOn(False)
                mask = self.map.getMaskToolsDockWidget().widget().getSelectionMask()
                if (mask is None) or (not np.sum(mask)):
                    # the mask is empty, don't waste time with positions
                    print 'building 1D curve from all positions'
                    data = np.mean(self.scan.data['1d'], axis=0)
                else:
                    # recreate the interpolated grid from above, to find masked
                    # positions on the oversampled grid
                    dummy = np.zeros(self.scan.nPositions)
                    x, y, z = self.scan.interpolatedMap(dummy, self.map.interpolBox.value(), origin='ul')
                    maskedPoints = np.vstack((x[np.where(mask)], y[np.where(mask)])).T
                    pointSpacing2 = (x[0,1] - x[0,0])**2 + (y[0,0] - y[1,0])**2
                    # go through actual positions and find the masked ones
                    maskedPositions = []
                    for i in range(self.scan.nPositions):
                        # the minimum distance of the current position to a selected grid point:
                        dist2 = np.sum((maskedPoints - self.scan.positions[i])**2, axis=1).min()
                        if dist2 < pointSpacing2:
                            maskedPositions.append(i)
                    print 'building 1D curve from %d positions'%len(maskedPositions)
                    # get the average and replace the image with legend 'data'
                    data = np.mean(self.scan.data['1d'][maskedPositions], axis=0)
            self.spectrum.addCurve(range(len(data)), data, legend='data',
                resetzoom = False)
            self.window().statusOutput('')
        except:
            self.window().statusOutput('Failed to build 1D curve. See terminal output.')
            raise

    def togglePositions(self):
        xlims = self.map.getGraphXLimits()
        ylims = self.map.getGraphYLimits()
        if self.map.positionsAction.isChecked():
            self.map.addCurve(self.scan.positions[:,0], self.scan.positions[:,1], 
                legend='scan positions', symbol='+', color='red', linestyle=' ')
        else:
            self.map.addCurve([], [], legend='scan positions')
        self.map.setGraphXLimits(*xlims)
        self.map.setGraphYLimits(*ylims)

    def indexMarkerOn(self, on):
        index = self.map.indexBox.value()
        if on:
            self.map.addCurve([self.scan.positions[index, 0]], 
                [self.scan.positions[index, 1]], symbol='o', color='red', 
                linestyle=' ', legend='index marker', resetzoom=False,
                replace=False)
        else:
            self.map.addCurve([], [], legend='index marker', 
                resetzoom=False, replace=False)

    def selectByIndex(self):
        self.selectionMode = 'ind'
        self.indexMarkerOn(True)
        # clearing the mask also invokes self.updateSpectrum():
        self.map.getMaskToolsDockWidget().widget().resetSelectionMask()
        self.selectionMode = 'roi'

    def launchPyMCA(self):
        """
        Exports the current scan, loads it, and launches a PyMCA QStackWidget.
        The data is written to disk so that the Scan.export method can be used
        as it is. This allows discarding the held data before launching PyMCA,
        avoiding double memory usage.
        """
        filename = os.path.join(tempfile.gettempdir(), 'tmp.hdf5')
        method, shape, oversampling, equal, discard, ok = PymcaLaunchDialog().getValues()
        if ok:
            self.window().statusOutput("Exporting data and launching PyMCA...")
            # reshape/resample and export data to temporary hdf5
            if os.path.exists(filename):
                os.remove(filename)
            try:
                self.scan.export(filename, method=method, shape=shape,
                    oversampling=oversampling, equal=equal)
            except Exception as e:
                print e
                self.window().statusOutput("Failed to export data, see terminal for info.")
                return
            if discard:
                # discard all data on the parent widget
                self.window().scan = None
            # launch a PyMCA widget with that data
            from PyMca5.PyMca.QStackWidget import QStackWidget
            w = QStackWidget()
            with h5py.File(filename) as fp:
                data = fp['entry0/data/1d'][:]
            if data.ndim == 2:
                data = data.reshape((1,) + data.shape)
            w.setStack(data)
            w.show()
            self.pymcaWindows.append(w)
            self.window().statusOutput("")

class PymcaLaunchDialog(qt.QDialog):
    """
    Dialog box for getting options before launching PyMCA.
    """
    def setupUi(self):
        # form layout for grid scan inputs
        layout = qt.QFormLayout()
        self.noChangeBox = qt.QRadioButton()
        layout.addRow(qt.QLabel("Export flat list of points:"), self.noChangeBox)
        self.reshapeBox = qt.QRadioButton()
        self.reshapeBox.setChecked(True)
        layout.addRow(qt.QLabel("Try reshaping the data:"), self.reshapeBox)
        self.shapeBox = qt.QLineEdit('auto')
        layout.addRow(qt.QLabel("    shape:"), self.shapeBox)
        self.resampleBox = qt.QRadioButton()
        layout.addRow(qt.QLabel("Resample the data on a grid:"), self.resampleBox)
        self.oversamplingBox = qt.QSpinBox()
        self.oversamplingBox.setValue(1)
        layout.addRow(qt.QLabel("    oversampling relative to typical step size:"), self.oversamplingBox)
        self.equalBox = qt.QCheckBox()
        self.equalBox.setChecked(True)
        layout.addRow(qt.QLabel("    equal horizontal and vertical steps"), self.equalBox)
        self.formGroupBox = qt.QGroupBox("PyMCA needs data layed out on a regular grid.")
        self.formGroupBox.setLayout(layout)

        # another form layout for an option to discard the data
        layout = qt.QFormLayout()
        self.discardBox = qt.QCheckBox()
        layout.addRow(qt.QLabel("Discard data in scanviewer before launching"), self.discardBox)
        self.discardGroupBox = qt.QGroupBox("Opening the data in PyMCA might double memory use.")
        self.discardGroupBox.setLayout(layout)

        # ok/cancel buttons
        buttonBox = qt.QDialogButtonBox(qt.QDialogButtonBox.Ok | qt.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        # put everything together
        mainLayout = qt.QVBoxLayout()
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(self.discardGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Launch PyMCA...")

    def getValues(self):
        self.setupUi()
        self.exec_()
        ok = (self.result() == self.Accepted)
        if self.reshapeBox.isChecked():
            method = 'reshape'
        elif self.resampleBox.isChecked():
            method = 'resample'
        else:
            method = 'none'
        shape = self.shapeBox.text()
        print shape
        shape = shape.replace(',', ' ').replace('x', ' ').split()
        shape = [int(s) for s in shape] if len(shape) == 2 else None
        oversampling = self.oversamplingBox.value()
        equal = self.equalBox.isChecked()
        discard = self.discardBox.isChecked()
        print 'getValues  done'
        return method, shape, oversampling, equal, discard, ok
