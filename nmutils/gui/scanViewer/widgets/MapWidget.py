from silx.gui.icons import getQIcon
from silx.gui import qt
from silx.gui.plot.Profile import ProfileToolBar

from .Base import CustomPlotWindow

class MapWidget(CustomPlotWindow):
    """
    A re-implementation of Plot2D, with customized tools and signals.
    """

    clickSelectionChanged = qt.pyqtSignal(float, float)
    indexSelectionChanged = qt.pyqtSignal(int)
    selectionCleared = qt.pyqtSignal()

    def __init__(self, parent=None, mask=True):

        super(MapWidget, self).__init__(parent=parent, backend=None,
                                     resetzoom=True, autoScale=False,
                                     logScale=False, grid=False,
                                     curveStyle=False, colormap=True,
                                     aspectRatio=True, yInverted=True,
                                     copy=True, save=True, print_=False,
                                     control=False, roi=False, mask=mask)
        if parent is None:
            self.setWindowTitle('comMapWidget')

        self.setGraphTitle('Scan map')
        self.setKeepDataAspectRatio(True)
        self.setYAxisInverted(True)

        # customize the mask tools for use as ROI selectors
        # unfortunately, tooltip and icon reset each other, so only changing the icon.
        self.getMaskToolsDockWidget().setWindowTitle('scan map ROI')
        roiAction = self.getMaskAction()
        roiAction.setToolTip('Select a scan map region of interest')
        roiAction.setIcon(getQIcon('image-select-box'))

        # Remove the mask action from where it was
        self.toolBar().removeAction(roiAction)

        # Rebuild the zoom/pan toolbar and add selection tools
        tb = self.getInteractiveModeToolBar()
        for w in tb.actions():
            tb.removeAction(w)
        zoomAction = qt.QAction(getQIcon('zoom'),
                                          'Zoom', parent=self,
                                          checkable=True)
        panAction = qt.QAction(getQIcon('pan'),
                                          'Pan', parent=self,
                                          checkable=True)
        selectAction = qt.QAction(getQIcon('image-select-add'),
                                          'Select single scan point', parent=self,
                                          checkable=True)
        clearAction = qt.QAction(getQIcon('image-select-erase'),
                                          'Clear selections', parent=self,
                                          checkable=False)
        tb.addAction(zoomAction)
        tb.addAction(panAction)
        tb.addAction(selectAction)
        tb.addAction(roiAction)
        tb.addAction(clearAction)
        group = qt.QActionGroup(self)
        group.addAction(zoomAction)
        group.addAction(panAction)
        group.addAction(selectAction)
        group.addAction(roiAction)
        zoomAction.setChecked(True)
        def setZoomMode(active):
            if active:
                self.setInteractiveMode('zoom')
        def setPanMode(active):
            if active:
                self.setInteractiveMode('pan')
        def setSelectMode(active):
            if active:
                self.setInteractiveMode('select')
        zoomAction.toggled.connect(setZoomMode)
        panAction.toggled.connect(setPanMode)
        selectAction.toggled.connect(setSelectMode)
        self.selectAction = selectAction
        self.sigPlotSignal.connect(self.filterMouseEvents)
        clearAction.triggered.connect(self.selectionCleared)

        # Add the index clicker
        self.indexBox = qt.QSpinBox(
            toolTip='Select a specific position by index')
        self.indexBox.setMinimum(0)
        tb.addWidget(self.indexBox)
        self.indexBox.valueChanged.connect(self.indexSelectionChanged)

        # add a button to toggle positions
        self.positionsAction = qt.QAction('positions', self, checkable=True)
        self.toolBar().addAction(self.positionsAction)

        # add the interpolation button
        self.interpolBox = qt.QSpinBox(
            toolTip='Map oversampling relative to average step size')
        self.interpolBox.setRange(1, 50)
        self.interpolBox.setValue(5)
        self.toolBar().addWidget(qt.QLabel(' N:'))
        self.toolBar().addWidget(self.interpolBox)

        # add a profile tool
        self.profile = ProfileToolBar(plot=self)
        self.addToolBar(self.profile)

        # set default colormap
        self.setDefaultColormap({'name':'gray', 'autoscale':True, 'normalization':'linear'})

    def filterMouseEvents(self, event):
        if event['event'] == 'mouseClicked' and self.selectAction.isChecked():
            self.clickSelectionChanged.emit(event['x'], event['y'])
