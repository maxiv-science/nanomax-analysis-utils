import numpy as np
from silx.gui.plot import PlotWidget
from silx.gui.plot.ComplexImageView import ComplexImageView
from silx.gui import qt
import nmutils

BW = 1000
FW = 1000
NN = 200

class ProbeManager(object):
    """
    Class which coordinates the various probe plots and widgets, propagates and so on.
    """
    def __init__(self, ui):
        self.ui = ui
        self.ui.focusButton.clicked.connect(self.autofocus)
        self.ui.focusSlider.valueChanged.connect(self.updatePlane)
        label = 'micrometers'
        self.ui.probePlot.getPlot().setGraphYLabel(label)
        self.ui.probePlot.getPlot().setGraphXLabel(label)
        self.ui.probePlot2.getPlot().setGraphYLabel(label)
        self.ui.probePlot2.getPlot().setGraphXLabel(label)

    def set_data(self, probe, psize, energy):
        self.probe2d = probe
        self.psize = psize
        self.energy = energy
        self.ui.probePlot.setScale(psize * 1e6)
        self.ui.probePlot2.setScale(psize * 1e6)
        self.ui.probePlot2.setData(self.probe2d, copy=False)
        self.propagate()

    def updatePlane(self):
        z = self.ui.focusSlider.value()
        try:
            zslice = np.argmin(np.abs(self.zdist*1e6 - z))
            zz = self.zdist[zslice]*1e6
            self.ui.probePlot.setData(self.probe3d[zslice], copy=False)
            self.ui.verticalFocusView.addXMarker(zz, legend='zslice', text='\n%d um'%int(np.round(zz)), color='m')
            self.ui.horizontalFocusView.addXMarker(zz, legend='zslice', text='', color='m')
        except AttributeError:
            pass # no data yet

    def propagate(self):
        # update the range
        self.ui.focusSlider.setMaximum(FW)
        self.ui.focusSlider.setMinimum(-BW)

        # define distances and propagate
        self.zdist = np.linspace(-BW, FW, NN) * 1e-6
        dist = self.zdist
        dx = dist[1] - dist[0]
        print "propagating to %d positions separated by %.1f um..."\
            % (len(dist), dx*1e6)
        self.probe3d = nmutils.utils.propagateNearfield(self.probe2d, self.psize, -dist, self.energy)

        # get intensities and focii
        power3d = np.abs(self.probe3d)**2
        power_vertical = np.sum(power3d, axis=2).T
        power_horizontal = np.sum(power3d, axis=1).T
        focus_vertical_ind = np.argmax(np.sum(power_vertical**2, axis=0))
        focus_vertical_x = dist[focus_vertical_ind]
        focus_horizontal_ind = np.argmax(np.sum(power_horizontal**2, axis=0))
        focus_horizontal_x = dist[focus_horizontal_ind]

        # show top and side views
        scale = [(self.zdist[1]-self.zdist[0])*1e6, self.psize*1e6]
        origin = [-BW, -self.psize*self.probe2d.shape[0]/2.0*1e6]
        self.ui.verticalFocusView.addImage(power_vertical, replace=True,
            xlabel='micrometers', ylabel='micrometers', scale=scale, origin=origin)
        self.ui.horizontalFocusView.addImage(power_horizontal, replace=True,
            xlabel='micrometers', ylabel='micrometers', scale=scale, origin=origin)

        # indicate vertical and horizontal foci
        y = self.ui.verticalFocusView.getYAxis().getLimits()
        self.ui.verticalFocusView.addXMarker(focus_vertical_x*1e6, legend='local', text='%d um'%int(np.round(focus_vertical_x*1e6)), color='c')
        self.ui.horizontalFocusView.addXMarker(focus_horizontal_x*1e6, legend='local', text='%d um'%int(np.round(focus_horizontal_x*1e6)), color='c')

        # autofocus
        focus_ind = np.argmax(np.sum(power3d**2, axis=(1,2)))
        self.realFocus = dist[focus_ind] * 1e6
        self.autofocus()

    def autofocus(self):
        try:
            self.ui.focusSlider.setValue(int(np.round(self.realFocus)))
            self.updatePlane()
        except AttributeError:
            pass # no data yet

class PropagationView(PlotWidget):
    """
    Bare bones plot widget for side views of the propagated probe
    """
    def __init__(self, parent=None):
        super(PropagationView, self).__init__(parent=parent)

class ProbeView(ComplexImageView):
    """
    Complex probe in 2d
    """
    def __init__(self, parent=None):
        super(ProbeView, self).__init__(parent=parent)
        self.setVisualizationMode(self.Mode.LOG10_AMPLITUDE_PHASE)
        self.setKeepDataAspectRatio(True)
        self.getPlot().getColorBarWidget().setVisible(False)
