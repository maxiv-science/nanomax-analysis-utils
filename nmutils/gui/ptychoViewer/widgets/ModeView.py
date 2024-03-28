import numpy as np
import silx
from silx.gui import qt
from silx.gui import colors
from silx.gui.plot import Plot1D
from silx.gui.plot.StackView import StackView
from ptypy.utils import ortho
from scipy.optimize import leastsq

def model(zeta, beta):
    n = np.arange(len(beta))
    return beta[0] * ((1 - zeta) / (1 + zeta))**n

def residuals(zeta, beta):
    return beta - model(zeta, beta)

class ModeView(qt.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hist = Plot1D(self)
        self.stack = StackView(self)
        #self.stack.setColormap({'name':'viridis', 'autoscale':True})  # this does not work with silx 2.0.0 anymore
        self.stack.setColormap(colormap=colors.Colormap(name='viridis'))
        self.setLayout(qt.QHBoxLayout())
        splitter = qt.QSplitter()
        splitter.addWidget(self.hist)
        splitter.addWidget(self.stack)
        self.layout().addWidget(splitter)

    def set_data(self, probes, psize):
        ampl, nplist = ortho(probes)
        edges = list(range(len(ampl)))
        self.hist.addHistogram(ampl, edges, legend='data', fill=True, color='b')
        self.hist.setGraphXLabel('Mode #')
        self.hist.setGraphYLabel('Relative power $\\beta$')
        self.stack.setStack(np.abs(np.array(nplist))**2)
        zeta = leastsq(func=residuals, x0=.5, args=(ampl,))[0][0]
        self.hist.addCurve(edges, model(zeta, ampl), color='r', linewidth=2)
        self.hist.setGraphYLimits(0, 1)
        self.hist.setGraphTitle('$\\zeta$=%.2f (fit)'%zeta)
