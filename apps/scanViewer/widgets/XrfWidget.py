from silx.gui.plot import PlotWindow, Plot1D
try:
    from silx.gui.plot.Profile import ProfileToolBar
except ImportError:
    from silx.gui.plot.PlotTools import ProfileToolBar
import PyQt4
from silx.gui.icons import getQIcon
import numpy as np

from XrdWidget import MapWidget

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

class XrfWidget(PyQt4.QtGui.QWidget):
    def __init__(self, parent=None):
        
        super(XrfWidget, self).__init__()
        self.map = MapWidget()
        self.spectrum = SpectrumWidget()
        parent.layout().addWidget(self.spectrum)
        parent.layout().addWidget(self.map)

        self.diffCmap = {'name':'temperature', 'autoscale':True, 'normalization':'log'}
        self.mapCmap = {'name':'gray', 'autoscale':True, 'normalization':'linear'}

        # connect the interpolation thingies
        self.map.interpolBox.valueChanged.connect(self.updateMap)
        self.map.interpolMenu.currentIndexChanged.connect(self.updateMap)

        # connect the positions button
        self.map.positionsAction.triggered.connect(self.togglePositions)

        # connect the clicker box
        self.map.indexBox.valueChanged.connect(self.selectByIndex)

        # connect the mask widget to the update
        self.map.maskToolsDockWidget.widget()._mask.sigChanged.connect(self.updateSpectrum)
        self.spectrum.curvesROIDockWidget.sigROISignal.connect(self.updateMap)

        # keep track of map selections by ROI or by index
        self.selectionMode = 'roi' # 'roi' or 'ind'

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
        try:
            self.window().statusOutput('Building XRF map...')
            # workaround to avoid the infinite loop which occurs when both
            # mask widgets are open at the same time
            self.map.maskToolsDockWidget.setVisible(False)
            # store the limits to maintain zoom
            xlims = self.map.getGraphXLimits()
            ylims = self.map.getGraphYLimits()
            # get ROI information
            try:
                roiName = self.spectrum.curvesROIDockWidget.currentROI
                # this doesn't update properly:
                # roiDict = self.spectrum.curvesROIDockWidget.roidict
                # ... but this does:
                roiList, roiDict = self.spectrum.curvesROIDockWidget.widget().getROIListAndDict()
                lower = int(np.floor(roiDict[roiName]['from']))
                upper = int(np.ceil(roiDict[roiName]['to']))
                print "building fluorescence map from channels %d to %d"%(lower, upper)
                average = np.mean(self.scan.data['xrf'][:, lower:upper], axis=1)
            except:
                print "building fluorescence map from the whole spectrum"
                average = np.mean(self.scan.data['xrf'], axis=1)
            # interpolate and plot map
            method = self.map.interpolMenu.currentText()
            sampling = self.map.interpolBox.value()
            x, y, z = self.scan.interpolatedMap(average, sampling, origin='ul', method=method)
            self.map.addImage(z, legend='data', 
                scale=[abs(x[0,0]-x[0,1]), abs(y[0,0]-y[1,0])],
                origin=[x.min(), y.min()], resetzoom=False)
            self.map.setGraphXLimits(*xlims)
            self.map.setGraphYLimits(*ylims)
            self.window().statusOutput('')
        except:
            self.window().statusOutput('Failed to build XRF map. See terminal output.')
            raise

    def updateSpectrum(self):
        try:
            self.window().statusOutput('Building XRF spectrum...')
            if self.selectionMode == 'ind':
                index = self.map.indexBox.value()
                data = self.scan.data['xrf'][index]
            elif self.selectionMode == 'roi':
                self.indexMarkerOn(False)
                mask = self.map.maskToolsDockWidget.widget().getSelectionMask()
                if mask.sum() == 0:
                    # the mask is empty, don't waste time with positions
                    print 'building fluorescence spectrum from all positions'
                    data = np.mean(self.scan.data['xrf'], axis=0)
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
                    print 'building fluorescence spectrum from %d positions'%len(maskedPositions)
                    # get the average and replace the image with legend 'data'
                    data = np.mean(self.scan.data['xrf'][maskedPositions], axis=0)
            self.spectrum.addCurve(range(len(data)), data, legend='data',
                resetzoom = False)
            self.window().statusOutput('')
        except:
            self.window().statusOutput('Failed to build XRF spectrum. See terminal output.')
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
        self.map.maskToolsDockWidget.widget().resetSelectionMask()
        self.selectionMode = 'roi'