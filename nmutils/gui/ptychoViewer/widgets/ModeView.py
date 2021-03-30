import numpy as np
import silx
from silx.gui import qt
from silx.gui.plot import Plot1D
from silx.gui.plot.StackView import StackView
from ptypy.utils import ortho

class ModeView(qt.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hist = Plot1D(self)
        self.stack = StackView(self)
        self.stack.setColormap({'name':'viridis', 'autoscale':True})
        self.setLayout(qt.QHBoxLayout())
        splitter = qt.QSplitter()
        splitter.addWidget(self.hist)
        splitter.addWidget(self.stack)
        self.layout().addWidget(splitter)

    def set_data(self, probes, psize):
        ampl, nplist = ortho(probes)
        edges = list(range(len(ampl)))
        self.hist.addHistogram(ampl, edges, legend='data', fill=True, color='k')
        self.hist.setGraphYLimits(0, 1)
        self.hist.setGraphXLabel('Mode #')
        self.hist.setGraphYLabel('Relative power')
        self.stack.setStack(np.abs(np.array(nplist))**2)
