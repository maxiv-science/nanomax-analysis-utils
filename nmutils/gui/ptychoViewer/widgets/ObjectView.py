import sys
import argparse
import h5py
import numpy as np
import silx
from silx.gui.plot.ComplexImageView import ComplexImageView
from silx.gui import qt
from distutils.version import LooseVersion
from ptypy.utils import rmphaseramp

class ObjectView(ComplexImageView):
    """
    Adapted ComplexImageView with some ptycho-specific options.
    """
    def __init__(self, parent=None):
        super(ObjectView, self).__init__(parent=parent)

        if parent is None:
            self.setWindowTitle('comMapWidget')

        self.setKeepDataAspectRatio(True)
        self.setComplexMode(self.Mode.PHASE)
        self.getPlot().setGraphYLabel('micrometers')
        self.getPlot().setGraphXLabel('micrometers')

        # add a button to toggle positions
        self.positionsAction = qt.QAction('positions', self, checkable=True)
        self.getPlot().toolBar().addAction(self.positionsAction)

        # add a button to toggle phase ramp removal
        self.rampAction = qt.QAction('ramp', self, checkable=True)
        self.getPlot().toolBar().addAction(self.rampAction)
        self.rampAction.triggered.connect(self._toggleRamp)

        # add a phase shift number
        self.phaseShiftBox = qt.QDoubleSpinBox(
            toolTip='Phase shift everything')
        self.phaseShiftBox.setRange(-3.14, 3.14)
        self.phaseShiftBox.setSingleStep(.1)
        self.phaseShiftBox.setValue(0.)
        self.phaseShiftBox.setPrefix('phase shift: ')
        self.phaseShiftBox.valueChanged.connect(self._update)
        self.getPlot().toolBar().addWidget(self.phaseShiftBox)

    def set_data(self, data, origin, psize):
        self.original_data = data
        self.data = self.original_data
        if self.rampAction.isChecked():
            self.data = self._deramped_data
        self.setScale(psize * 1e6)
        self.setOrigin(tuple(origin * 1e6))
        self._update()

    @property
    def _deramped_data(self):
        weights = np.zeros_like(self.original_data)
        M, N = weights.shape
        weights[M//3:M//3*2, N//3:N//3*2] = 1
        return rmphaseramp(self.original_data, weights)

    def _toggleRamp(self):
        if self.rampAction.isChecked():
            self.data = self._deramped_data
        else:
            self.data = self.original_data
        self._update()

    def _update(self):
        shift = self.phaseShiftBox.value()
        shifted = np.exp(1j * shift) * self.data
        self.setData(shifted)

if __name__ == '__main__':
    if LooseVersion(silx.version) <= LooseVersion('0.9.0'):
        print("NOTE: Changing phase colormaps requires silx 0.10.0")

    # you always need a qt app     
    app = qt.QApplication(sys.argv)    

    ### Parse input
    parser = argparse.ArgumentParser(
        description='This application visualizes the output of a ptypy run, by loading a ptyr file.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('ptyr_file', type=str,
                        help='a ptypy reconstruction file')
    args = parser.parse_args()

    ### load reconstruction data
    with h5py.File(args.ptyr_file, 'r') as hf:
        scanid = str(list(hf['content/probe'].keys())[0])
        print('loading entry %s' % scanid)
        probe = np.array(hf.get('content/probe/%s/data' % scanid))
        obj = np.array(hf.get('content/obj/%s/data' % scanid))
        psize = np.array(hf.get('content/probe/%s/_psize' % scanid))
        energy = np.array(hf.get('content/probe/%s/_energy' % scanid))
        origin = np.array(hf.get('content/probe/%s/_origin' % scanid))

    try:
        probe = probe[0]
        obj = obj[0]
        psize = psize[0]
    except IndexError:
        raise IOError('That doesn''t look like a valid reconstruction file!')
    print("Loaded probe %d x %d and object %d x %d, pixel size %.1f nm, energy %.2f keV"%(probe.shape + obj.shape + (psize*1e9, energy)))

    # instantiate and run the viewer
    viewer = ObjectView()
    viewer.set_data(obj, origin, psize)
    viewer.show()
    app.exec_()
