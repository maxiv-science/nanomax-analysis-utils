from silx.gui.plot import PlotWindow
from silx.gui.plot.Profile import ProfileToolBar
import PyQt4
import scipy.ndimage.measurements
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
                                     roi=False, mask=False)
        if parent is None:
            self.setWindowTitle('comMapWidget')

        self.setGraphTitle('COM deviation from the mean')
        self.setGraphXLabel('Columns')
        self.setGraphYLabel('Rows')
        self.setKeepDataAspectRatio(True)
        self.setYAxisInverted(True)

        # add an interpolation toolbar
        self.interpolToolbar = self.addToolBar('Interpolation & COM')
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

        # add a menu for COM type
        self.interpolToolbar.addSeparator()
        self.comDirectionBox = PyQt4.QtGui.QComboBox(
            toolTip='Type of COM deviation calculated')
        self.comDirectionBox.insertItems(1, ['horizontal', 'vertical', 'magnitude'])
        self.interpolToolbar.addWidget(PyQt4.QtGui.QLabel(' COM:'))
        self.interpolToolbar.addWidget(self.comDirectionBox)

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
                                     copy=False, save=False, print_=False,
                                     control=False, position=posInfo,
                                     roi=False, mask=True)
        if parent is None:
            self.setWindowTitle('comImageWidget')

        self.setGraphXLabel('Columns')
        self.setGraphYLabel('Rows')
        self.setGraphTitle('Mask excluded areas for COM analysis')
        self.setKeepDataAspectRatio(True)
        self.setYAxisInverted(True)

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

class ComWidget(PyQt4.QtGui.QWidget):
    def __init__(self, parent=None):

        super(ComWidget, self).__init__()
        self.map = MapWidget()
        self.image = ImageWidget()
        parent.layout().addWidget(self.image)
        parent.layout().addWidget(self.map)

        self.diffCmap = {'name':'temperature', 'autoscale':True, 'normalization':'log'}

        # connect the interpolation thingies
        self.map.interpolBox.valueChanged.connect(self.updateMap)
        self.map.interpolMenu.currentIndexChanged.connect(self.updateMap)

        # connect the COM chooser
        self.map.comDirectionBox.currentIndexChanged.connect(self.updateMap)

        # connect the positions button
        self.map.positionsAction.triggered.connect(self.togglePositions)

        # connect the mask widget to the update
        self.image.maskToolsDockWidget.widget()._mask.sigChanged.connect(self.updateMap)

    def setScan(self, scan):
        self.scan = scan
        self.resetMap()
        self.resetImage()

    def resetMap(self):
        self.updateMap()
        self.map.resetZoom()

    def resetImage(self):
        self.image.addImage(self.scan.meanData(name='xrd'), 
            colormap=self.diffCmap, legend='data')
        self.image.setKeepDataAspectRatio(True)
        self.image.setYAxisInverted(True)
        self.image.resetZoom()

    def updateMap(self):
        print 'building COM map'
        # store the limits to maintain zoom
        xlims = self.map.getGraphXLimits()
        ylims = self.map.getGraphYLimits()
        # calculate COM
        com = []
        mask = self.image.maskToolsDockWidget.widget().getSelectionMask()
        if np.prod(mask.shape) == 0:
            mask = np.zeros(self.scan.data['xrd'][0].shape, dtype=int)
        for im in self.scan.data['xrd']:
            com_ = scipy.ndimage.measurements.center_of_mass(im * (1 - mask))
            if np.any(np.isnan(com_)):
                com_ = (0, 0)
            com.append(com_)
        com = np.array(com)
        # choose which COM to show
        direction = self.map.comDirectionBox.currentIndex()
        if direction == 0:
            com = com[:, 1] - np.mean(com[:, 1])
        elif direction == 1:
            com = com[:, 0] - np.mean(com[:, 0])
        elif direction == 2:
            com = np.sum((com - np.mean(com, axis=0))**2, axis=1)
        else:
            return
        # interpolate and show
        method = self.map.interpolMenu.currentText()
        sampling = self.map.interpolBox.value()
        x, y, z = self.scan.interpolatedMap(com, sampling, origin='ul', method=method)
        self.map.addImage(z, legend='data', 
            scale=[abs(x[0,0]-x[0,1]), abs(y[0,0]-y[1,0])],
            origin=[x.min(), y.min()])
        self.map.setGraphXLimits(*xlims)
        self.map.setGraphYLimits(*ylims)


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
