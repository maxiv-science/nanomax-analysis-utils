from silx.gui.plot import PlotWindow
from silx.gui.plot.Profile import ProfileToolBar
from silx.gui.icons import getQIcon
from silx.gui import qt
import scipy.ndimage.measurements
import numpy as np

from .XrdWidget import MapWidget

class ScalarWidget(qt.QWidget):
    # This widget defines a MapWidget and and normal text label and describes
    # how they are related by data operations.
    def __init__(self, parent=None):

        super(ScalarWidget, self).__init__()
        self.map = MapWidget(self)
        self.value = qt.QLabel(self)
        self.value.setText('scalar value')
        self.setLayout(qt.QHBoxLayout())
        splitter = qt.QSplitter()
        splitter.addWidget(self.value)
        splitter.addWidget(self.map)
        splitter.setSizes((300,300))
        self.layout().addWidget(splitter)

        # connect the interpolation thingies
        self.map.interpolBox.valueChanged.connect(self.updateMap)

        # connect the clicker box
        self.map.indexBox.valueChanged.connect(self.selectByIndex)

        # connect the positions button
        self.map.positionsAction.triggered.connect(self.togglePositions)

        # connect the mask widget to the update
        self.map.getMaskToolsDockWidget().widget()._mask.sigChanged.connect(self.updateImage)

        # keep track of map selections by ROI or by index
        self.selectionMode = 'roi' # 'roi' or 'ind'

    def setScan(self, scan):
        self.scan = scan
        if not scan:
            self.map.removeImage('data')
            self.value.setText('scalar data')
            return
        # avoid old position grids:
        if self.map.positionsAction.isChecked():
            self.togglePositions()
        self.map.indexBox.setMaximum(scan.nPositions - 1)
        self.resetMap()

    def resetMap(self):
        self.updateMap()
        self.map.resetZoom()

    def updateMap(self):
        if self.scan is None:
            return
        try:
            self.window().statusOutput('Building scalar map...')
            # workaround to avoid the infinite loop which occurs when both
            # mask widgets are open at the same time
            self.map.getMaskToolsDockWidget().setVisible(False)
            # store the limits to maintain zoom
            xlims = self.map.getGraphXLimits()
            ylims = self.map.getGraphYLimits()
            # if the mask is cleared, reset without wasting time
            sampling = self.map.interpolBox.value()
            x, y, z = self.scan.interpolatedMap(self.scan.data['0d'], sampling, origin='ul', method='nearest')
            self.map.addImage(z, legend='data', 
                scale=[abs(x[0,0]-x[0,1]), abs(y[0,0]-y[1,0])],
                origin=[x.min(), y.min()], resetzoom=False)
            self.map.setGraphXLimits(*xlims)
            self.map.setGraphYLimits(*ylims)
            aspect = (x.max() - x.min()) / (y.max() - y.min())
            if aspect > 50 or aspect < 1./50:
                self.map.setKeepDataAspectRatio(False)
            else:
                self.map.setKeepDataAspectRatio(True)
            self.window().statusOutput('')
        except:
            self.window().statusOutput('Failed to build scalar map. See terminal output.')
            raise

    def updateImage(self):
        if self.scan is None:
            return
        try:
            # get and check the mask array
            if self.selectionMode == 'ind':
                index = self.map.indexBox.value()
                data = self.scan.data['0d'][index]
            elif self.selectionMode == 'roi':
                self.indexMarkerOn(False)
                mask = self.map.getMaskToolsDockWidget().widget().getSelectionMask()
                if (mask is None) or (not np.sum(mask)):
                    # the mask is empty, don't waste time with positions
                    print 'calculating scalar from all positions'
                    data = np.mean(self.scan.data['0d'], axis=0)
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
                    # get the average and replace the image with legend 'data'
                    print 'calculating average scalar from %d positions'%len(maskedPositions)
                    data = np.mean(self.scan.data['0d'][maskedPositions], axis=0)
            self.value.setText('scalar value: \n%s' % data)
            self.window().statusOutput('')
        except:
            self.window().statusOutput('Failed to build diffraction pattern. See terminal output.')
            raise

    def togglePositions(self):
        if self.map.positionsAction.isChecked():
            self.map.addCurve(self.scan.positions[:,0], self.scan.positions[:,1], 
                legend='scan positions', symbol='+', color='red', linestyle=' ',
                resetzoom=False, replace=False)
        else:
            self.map.addCurve([], [], legend='scan positions', resetzoom=False, replace=False)

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
        # clearing the mask also invokes self.updateImage():
        self.map.getMaskToolsDockWidget().widget().resetSelectionMask()
        self.selectionMode = 'roi'
