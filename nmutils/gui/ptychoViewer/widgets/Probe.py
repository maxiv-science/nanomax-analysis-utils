import numpy as np
from silx.gui.plot import PlotWidget, PlotWindow
from silx.gui.plot.ComplexImageView import ComplexImageView
from silx.gui import qt
import nmutils
import scipy.interpolate


class ProbeManager(object):
    """
    Class which coordinates the various probe plots and widgets, propagates and so on.
    """
    def __init__(self, ui):
        self.ui = ui
        self.ui.focusButton.clicked.connect(self.autofocus)
        self.ui.propagateButton.clicked.connect(self.propagate)
        self.ui.focusSlider.valueChanged.connect(self.updatePlane)
        label = 'micrometers'
        self.ui.probePlot.getPlot().setGraphYLabel(label)
        self.ui.probePlot.getPlot().setGraphXLabel(label)
        self.ui.probePlot2.getPlot().setGraphYLabel(label)
        self.ui.probePlot2.getPlot().setGraphXLabel(label)
        self.ui.probePlot.setGraphTitle('Plane of interest')
        self.ui.probePlot2.setGraphTitle('Sample plane')
        self.ui.probeHist.setGraphTitle('Probe histogram')
        self.ui.probeHist.setGraphXLabel('micrometers')
        self.ui.probeHist.setGraphYLabel(' ')
        self.ui.probeHist.chooserMenu.currentIndexChanged.connect(self.updatePlane)
        self.ui.verticalFocusView.setGraphTitle('Vertical focus (M1)')
        self.ui.horizontalFocusView.setGraphTitle('Horizontal focus (M2)')

    def set_data(self, probe, psize, energy):
        self.psize = psize
        self.probe2d = probe
        self.energy = energy
        self.ui.probePlot.setScale(psize * 1e6)
        self.ui.probePlot2.setScale(psize * 1e6)
        self.ui.probePlot2.set_data(self.probe2d)
        self.ui.verticalFocusView.addXMarker(0., legend='sample', text='sample', color='g')
        self.ui.horizontalFocusView.addXMarker(0., legend='sample', text='', color='g')
        lims = [-1e6*probe.shape[0] * psize / 2, 1e6*probe.shape[0] * psize / 2] # um
        self.xtrans = np.linspace(lims[0], lims[1], probe.shape[0])
        self.propagate()

    def calculateFWHM(self):
        z = self.ui.focusSlider.value()
        zslice = np.argmin(np.abs(self.zdist*1e6 - z))
        data = self.probe3d[zslice]
        yh = np.sum(np.abs(data)**2, axis=0)
        yv = np.sum(np.abs(data)**2, axis=1)
        edges = scipy.interpolate.UnivariateSpline(self.xtrans, yh-yh.max()/2).roots()
        fwhmh = abs(edges[0] - edges[-1])
        edges = scipy.interpolate.UnivariateSpline(self.xtrans, yv-yv.max()/2).roots()
        fwhmv = abs(edges[0] - edges[-1])
        x0, x1 = self.ui.probeHist.getXAxis().getLimits()
        y0, y1 = self.ui.probeHist.getYAxis().getLimits()
        self.ui.probeHist.addMarker(x0, y0 + .9 * (y1 - y0), legend='fwhm_h',
            text='FWHM\n  %.0f x %.0f nm\n  (v x h)' % (fwhmv*1000, fwhmh*1000),
            color='k', selectable=True, draggable=True, symbol=',')

    def updatePlane(self):
        self.ui.probeHist.addMarker(0, 0, legend='fwhm_h', text=' ', color='w')
        z = self.ui.focusSlider.value()
        try:
            # plane of interest image
            zslice = np.argmin(np.abs(self.zdist*1e6 - z))
            data = self.probe3d[zslice]
            zz = self.zdist[zslice]*1e6
            self.ui.probePlot.set_data(data)
            self.ui.verticalFocusView.addXMarker(zz, legend='zslice',
                        text='\n\n %d um'%int(np.round(zz)), color='m')
            self.ui.horizontalFocusView.addXMarker(zz, legend='zslice',
                        text='', color='m')

            # histograms
            if self.ui.probeHist.chooserMenu.currentIndex() == 0:
                # histogram at plane of interest
                intensity = np.abs(data)**2
                yh = np.sum(intensity, axis=0)
                yv = np.sum(intensity, axis=1)
            else:
                # histogram at reconstruction plane
                intensity = np.abs(self.probe2d)**2
                yh = np.sum(intensity, axis=0)
                yv = np.sum(intensity, axis=1)
            self.ui.probeHist.addCurve(self.xtrans, yh, legend='horizontal')
            self.ui.probeHist.addCurve(self.xtrans, yv, legend='vertical')

        except AttributeError:
            pass # no data yet

    def propagate(self):
        # get the parameters
        nn = self.ui.numberBox.value()
        fw = self.ui.forwardBox.value()
        bw = self.ui.backwardBox.value()
        # update the range
        self.ui.focusSlider.setMaximum(fw)
        self.ui.focusSlider.setMinimum(-bw)

        # define distances and propagate
        self.zdist = np.linspace(-bw, fw, nn) * 1e-6
        dist = self.zdist
        dx = dist[1] - dist[0]
        print("propagating to %d positions separated by %.1f um..."\
            % (len(dist), dx*1e6))
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
        origin = [-bw, -self.psize*self.probe2d.shape[0]/2.0*1e6]
        self.ui.verticalFocusView.addImage(power_vertical, replace=True,
            xlabel='beamline z axis (micrometers)', ylabel='micrometers', scale=scale, origin=origin)
        self.ui.horizontalFocusView.addImage(power_horizontal, replace=True,
            xlabel='beamline z axis (micrometers)', ylabel='micrometers', scale=scale, origin=origin)

        # indicate vertical and horizontal foci
        y = self.ui.verticalFocusView.getYAxis().getLimits()
        self.ui.verticalFocusView.addXMarker(focus_vertical_x*1e6, legend='local', text='\n %d um'%int(np.round(focus_vertical_x*1e6)), color='c')
        self.ui.horizontalFocusView.addXMarker(focus_horizontal_x*1e6, legend='local', text='\n %d um'%int(np.round(focus_horizontal_x*1e6)), color='c')

        # autofocus
        focus_ind = np.argmax(np.sum(power3d**2, axis=(1,2)))
        self.realFocus = dist[focus_ind] * 1e6
        self.autofocus()

    def autofocus(self):
        try:
            self.ui.focusSlider.setValue(int(np.round(self.realFocus)))
            self.updatePlane()
            self.calculateFWHM()
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
        self.setComplexMode(self.Mode.LOG10_AMPLITUDE_PHASE)
        self.setKeepDataAspectRatio(True)
        self.getPlot().getColorBarWidget().setVisible(False)

        # add a phase shift number
        self.phaseShiftBox = qt.QDoubleSpinBox(toolTip='Phase shift everything')
        self.phaseShiftBox.setRange(-3.14, 3.14)
        self.phaseShiftBox.setSingleStep(.1)
        self.phaseShiftBox.setValue(0.)
        self.phaseShiftBox.setPrefix('phase shift: ')
        self.phaseShiftBox.valueChanged.connect(self._update)
        self.getPlot().toolBar().addWidget(self.phaseShiftBox)

    def set_data(self, data):
        self.data = data
        self._update()

    def _update(self):
        shift = self.phaseShiftBox.value()
        shifted = np.exp(1j * shift) * self.data
        self.setData(shifted, copy=False)

class Histogram(PlotWindow):
    def __init__(self, parent=None):
        super(Histogram, self).__init__(parent=parent,
                                        resetzoom=True, autoScale=True,
                                        logScale=True, grid=True,
                                        curveStyle=True, colormap=False,
                                        aspectRatio=False, yInverted=False,
                                        copy=True, save=True, print_=True,
                                        control=True, position=True,
                                        roi=False, mask=False, fit=False)
        # add a POI/reconstruction chooser
        self.chooserToolbar = self.addToolBar('Interpolation')
        self.chooserMenu = qt.QComboBox(
            toolTip='Choose whether to display probe at the plane of interest of in the sample plane')
        self.chooserMenu.insertItems(1, ['Plane of interest', 'Sample plane'])
        self.chooserToolbar.addWidget(self.chooserMenu)
