from silx.gui.plot import PlotWindow
from silx.gui.plot.Profile import ProfileToolBar
import PyQt4
from silx.gui.icons import getQIcon
import numpy as np

class MapWidget(PlotWindow):
    """
    A re-implementation of Plot2D, with customized tools.
    """

    def __init__(self, parent=None):
        # List of information to display at the bottom of the plot
        posInfo = [
            ('X', lambda x, y: x),
            ('Y', lambda x, y: y),
            ('Data', self._getActiveImageValue)]

        super(MapWidget, self).__init__(parent=parent, backend=None,
                                     resetzoom=True, autoScale=False,
                                     logScale=False, grid=False,
                                     curveStyle=False, colormap=True,
                                     aspectRatio=True, yInverted=True,
                                     copy=True, save=True, print_=False,
                                     control=False, position=posInfo,
                                     roi=False, mask=True)
        if parent is None:
            self.setWindowTitle('comMapWidget')

        self.setGraphTitle('Scan map')
        self.setGraphXLabel('Columns')
        self.setGraphYLabel('Rows')
        self.setKeepDataAspectRatio(True)
        self.setYAxisInverted(True)

        # add an interpolation toolbar
        self.interpolToolbar = self.addToolBar('Interpolation')
        self.interpolBox = PyQt4.QtGui.QSpinBox(
            toolTip='Map oversampling relative to average step size')
        self.interpolBox.setRange(1, 50)
        self.interpolBox.setValue(5)
        self.interpolMenu = PyQt4.QtGui.QComboBox(
            toolTip='Type of interpolation between scan positions')
        self.interpolMenu.insertItems(1, ['nearest', 'linear', 'cubic'])
        self.interpolToolbar.addWidget(self.interpolMenu)
        self.interpolToolbar.addWidget(PyQt4.QtGui.QLabel(' N:'))
        self.interpolToolbar.addWidget(self.interpolBox)

        # customize the mask tools for use as ROI selectors
        # unfortunately, tooltip and icon reset each other, so only changing the icon.
        self.maskToolsDockWidget.setWindowTitle('scan map ROI')
        self.maskAction.setToolTip('Select a scan map region of interest')
        self.maskAction.setIcon(getQIcon('image-select-box'))

        # add a button to toggle positions
        self.positionsAction = PyQt4.QtGui.QAction('positions', self, checkable=True)
        self.toolBar().addAction(self.positionsAction)

        # add a profile tool
        self.profile = ProfileToolBar(plot=self)
        self.addToolBar(self.profile)

    def _getActiveImageValue(self, x, y):
        """Get value of active image at position (x, y)

        :param float x: X position in plot coordinates
        :param float y: Y position in plot coordinates
        :return: The value at that point or '-'
        """
        image = self.getActiveImage()
        if image is not None:
            data, params = image[0], image[4]
            ox, oy = params['origin']
            sx, sy = params['scale']
            if (y - oy) >= 0 and (x - ox) >= 0:
                # Test positive before cast otherwisr issue with int(-0.5) = 0
                row = int((y - oy) / sy)
                col = int((x - ox) / sx)
                if (row < data.shape[0] and col < data.shape[1]):
                    return data[row, col]
        return '-'

class ImageWidget(PlotWindow):
    """
    A re-implementation of Plot2D, with customized tools.
    """

    def __init__(self, parent=None):
        # List of information to display at the bottom of the plot
        posInfo = [
            ('X', lambda x, y: x),
            ('Y', lambda x, y: y),
            ('Data', self._getActiveImageValue)]

        super(ImageWidget, self).__init__(parent=parent, backend=None,
                                     resetzoom=True, autoScale=False,
                                     logScale=False, grid=False,
                                     curveStyle=False, colormap=True,
                                     aspectRatio=True, yInverted=True,
                                     copy=True, save=True, print_=False,
                                     control=False, position=posInfo,
                                     roi=False, mask=True)
        if parent is None:
            self.setWindowTitle('comImageWidget')

        self.setGraphXLabel('Columns')
        self.setGraphYLabel('Rows')
        self.setGraphTitle('Diffraction')
        self.setKeepDataAspectRatio(True)
        self.setYAxisInverted(True)

        self.maskToolsDockWidget.setWindowTitle('diffraction ROI')
        self.maskAction.setToolTip('Select a diffraction region of interest')
        self.maskAction.setIcon(getQIcon('image-select-box'))

    def _getActiveImageValue(self, x, y):
        """Get value of active image at position (x, y)

        :param float x: X position in plot coordinates
        :param float y: Y position in plot coordinates
        :return: The value at that point or '-'
        """
        image = self.getActiveImage()
        if image is not None:
            data, params = image[0], image[4]
            ox, oy = params['origin']
            sx, sy = params['scale']
            if (y - oy) >= 0 and (x - ox) >= 0:
                # Test positive before cast otherwisr issue with int(-0.5) = 0
                row = int((y - oy) / sy)
                col = int((x - ox) / sx)
                if (row < data.shape[0] and col < data.shape[1]):
                    return data[row, col]
        return '-'


class XrdWidget(PyQt4.QtGui.QWidget):
    def __init__(self, parent=None):

        super(XrdWidget, self).__init__()
        self.map = MapWidget()
        self.image = ImageWidget()
        parent.layout().addWidget(self.image)
        parent.layout().addWidget(self.map)

        self.diffCmap = {'name':'temperature', 'autoscale':True, 'normalization':'log'}
        self.mapCmap = {'name':'gray', 'autoscale':True, 'normalization':'linear'}

        # connect the interpolation thingies
        self.map.interpolBox.valueChanged.connect(self.updateMap)
        self.map.interpolMenu.currentIndexChanged.connect(self.updateMap)

        # connect the positions button
        self.map.positionsAction.triggered.connect(self.togglePositions)

        # connect the mask widget to the update
        self.image.maskToolsDockWidget.widget()._mask.sigChanged.connect(self.updateMap)
        self.map.maskToolsDockWidget.widget()._mask.sigChanged.connect(self.updateImage)

    def setScan(self, scan):
        self.scan = scan
        self.resetMap()
        self.resetImage()

    def resetMap(self):
        self.updateMap()
        self.map.resetZoom()

    def resetImage(self):
        self.updateImage()
        self.image.resetZoom()

    def updateMap(self):
        # workaround to avoid the infinite loop which occurs when both
        # mask widgets are open at the same time
        self.map.maskToolsDockWidget.setVisible(False)
        # store the limits to maintain zoom
        xlims = self.map.getGraphXLimits()
        ylims = self.map.getGraphYLimits()
        # get and check the mask array
        mask = self.image.maskToolsDockWidget.widget().getSelectionMask()
        # if the mask is cleared, reset without wasting time
        if mask.sum() == 0:
            print 'building XRD map by averaging all pixels'
            average = np.mean(self.scan.data['xrd'], axis=(1,2))
        else:
            ii, jj = np.where(mask)
            print 'building XRD map by averaging %d pixels'%len(ii)
            average = np.mean(self.scan.data['xrd'][:, ii, jj], axis=1)
        method = self.map.interpolMenu.currentText()
        sampling = self.map.interpolBox.value()
        x, y, z = self.scan.interpolatedMap(average, sampling, origin='ul', method=method)
        self.map.addImage(z, legend='data', 
            scale=[abs(x[0,0]-x[0,1]), abs(y[0,0]-y[1,0])],
            origin=[x.min(), y.min()])
        self.map.setGraphXLimits(*xlims)
        self.map.setGraphYLimits(*ylims)

    def updateImage(self):
        # workaround to avoid the infinite loop which occurs when both
        # mask widgets are open at the same time
        self.image.maskToolsDockWidget.setVisible(False)
        # get and check the mask array
        mask = self.map.maskToolsDockWidget.widget().getSelectionMask()
        if mask.sum() == 0:
            # the mask is empty, don't waste time with positions
            print 'building diffraction pattern from all positions'
            data = np.mean(self.scan.data['xrd'], axis=0)
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
            print 'building diffraction pattern from %d positions'%len(maskedPositions)
            # get the average and replace the image with legend 'data'
            data = np.mean(self.scan.data['xrd'][maskedPositions], axis=0)
        self.image.addImage(data, legend='data', colormap=self.diffCmap)

    def togglePositions(self):
        xlims = self.map.getGraphXLimits()
        ylims = self.map.getGraphYLimits()
        if self.map.positionsAction.isChecked():
            self.map.addCurve(self.scan.positions[:,0], self.scan.positions[:,1], 
                label='scan positions', symbol='+', color='red', linestyle=' ')
        else:
            self.map.addCurve([], [], label='scan positions')
        self.map.setGraphXLimits(*xlims)
        self.map.setGraphYLimits(*ylims)
