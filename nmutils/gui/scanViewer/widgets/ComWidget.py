from silx.gui.plot import PlotWindow
from silx.gui.plot.Profile import ProfileToolBar
from silx.gui import qt
import scipy.ndimage.measurements
import numpy as np

from .XrdWidget import MapWidget
from .Base import CustomPlotWindow

class ImageWidget(CustomPlotWindow):
    """
    A re-implementation of Plot2D, with customized tools.
    """

    def __init__(self, parent=None):

        super(ImageWidget, self).__init__(parent=parent, backend=None,
                                     resetzoom=True, autoScale=False,
                                     logScale=False, grid=False,
                                     curveStyle=False, colormap=True,
                                     aspectRatio=True, yInverted=True,
                                     copy=False, save=False, print_=False,
                                     control=False, roi=False, mask=True)
        if parent is None:
            self.setWindowTitle('comImageWidget')

        self.setGraphXLabel('Columns')
        self.setGraphYLabel('Rows')
        self.setGraphTitle('Mask excluded areas for COM analysis')
        self.setKeepDataAspectRatio(True)
        self.setYAxisInverted(True)

        # set the default colormap
        self.setDefaultColormap({'name':'temperature', 'autoscale':True, 'normalization':'log'})


class ComWidget(qt.QWidget):
    def __init__(self, parent=None):

        super(ComWidget, self).__init__(parent=parent)
        self.setLayout(qt.QVBoxLayout())

        # the direction menu
        hbox = qt.QHBoxLayout()
        self.directionCombo = qt.QComboBox()
        self.directionCombo.insertItems(1, ['', 'horizontal', 'vertical', 'magnitude'])
        self.directionCombo.currentIndexChanged.connect(self.updateMap)
        hbox.addWidget(qt.QLabel('COM direction:'))
        hbox.addWidget(self.directionCombo)
        hbox.addStretch(1)
        self.layout().addLayout(hbox)

        # the image and map parts
        splitter = qt.QSplitter()
        self.map = MapWidget(self, mask=False)
        self.image = ImageWidget(self)
        splitter.addWidget(self.image)
        splitter.addWidget(self.map)
        self.layout().addWidget(splitter)

        # connect the interpolation thingies
        self.map.interpolBox.valueChanged.connect(self.updateMap)

        # connect the positions button
        self.map.positionsAction.triggered.connect(self.togglePositions)

        # connect the mask widget to the update
        self.image.getMaskToolsDockWidget().widget()._mask.sigChanged.connect(self.updateMap)

    def setScan(self, scan):
        self.scan = scan
        if not scan:
            self.map.removeImage('data')
            self.image.removeImage('data')
            return
        if scan.data['2d'].shape[1:] == (1, 1):
            return
        # avoid old position grids:
        if self.map.positionsAction.isChecked():
            self.togglePositions()
        self.resetMap()
        self.resetImage()

    def resetMap(self):
        self.updateMap()
        self.map.resetZoom()

    def resetImage(self):
        self.image.addImage(self.scan.meanData(name='2d'), legend='data')
        self.image.setKeepDataAspectRatio(True)
        self.image.setYAxisInverted(True)
        self.image.resetZoom()

    def updateMap(self):
        if self.scan is None:
            return
        try:
            direction = self.directionCombo.currentIndex()
            if not direction:
                return
            print 'building COM map'
            self.window().statusOutput('Building COM map...')
            # store the limits to maintain zoom
            xlims = self.map.getGraphXLimits()
            ylims = self.map.getGraphYLimits()
            # calculate COM
            com = []
            mask = self.image.getMaskToolsDockWidget().widget().getSelectionMask()
            if (mask is None) or (not np.sum(mask)):
                mask = np.zeros(self.scan.data['2d'][0].shape, dtype=int)
            for im in self.scan.data['2d']:
                com_ = scipy.ndimage.measurements.center_of_mass(im * (1 - mask))
                if np.any(np.isnan(com_)):
                    com_ = (0, 0)
                com.append(com_)
            com = np.array(com)
            # choose which COM to show
            if direction == 1:
                com = com[:, 1] - np.mean(com[:, 1])
            elif direction == 2:
                com = com[:, 0] - np.mean(com[:, 0])
            elif direction == 3:
                com = np.sum((com - np.mean(com, axis=0))**2, axis=1)
            else:
                return
            # interpolate and show
            sampling = self.map.interpolBox.value()
            x, y, z = self.scan.interpolatedMap(com, sampling, origin='ul', method='nearest')
            try:
                self.map.addImage(z, legend='data', 
                    scale=[abs(x[0,0]-x[0,1]), abs(y[0,0]-y[1,0])],
                    origin=[x.min(), y.min()])
                self.map.setGraphXLimits(*xlims)
                self.map.setGraphYLimits(*ylims)
            except:
                print "Invalid center of mass"
            self.map.setGraphXLabel(self.scan.positionDimLabels[0])
            self.map.setGraphYLabel(self.scan.positionDimLabels[1])
            self.window().statusOutput('')
        except:
            self.window().statusOutput('Failed to build COM map. See terminal output.')
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

#class ComWidget(qt.QWidget):
#    def setScan(self, scan):
#        pass
