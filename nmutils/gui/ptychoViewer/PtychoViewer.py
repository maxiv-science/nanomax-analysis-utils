"""
This application loads ptypy reconstruction files and displays them nicely.
"""

# make sure silx is not too old (API features have appeared)
from distutils.version import LooseVersion
try:
    import silx
    assert LooseVersion(silx.version) >= LooseVersion('0.8.0')
except:
    raise Exception('This application requires silx >= 0.8.0')

from .widgets.Probe import ProbeManager
from silx.gui import qt
from silx.gui.icons import getQIcon
from . import design
import sys
import numpy as np
import h5py
print('silx %s using %s on Python %d.%d' % (silx.version, qt.BINDING, *sys.version_info[:2]))

# using the single inheritance method here, as described here,
# http://pyqt.sourceforge.net/Docs/PyQt4/designer.html
#
# this means:
# 1) create a new class for the containing widget, which will 
#    have all the code and connections
# 2) create an UI object from qt-designer and own it as self.ui
# 3) run its setupUi method and pass the containing widget (self)
#
class PtychoViewer(qt.QMainWindow):

    def __init__(self, filename=None):

        # Qt base class constructor
        super(PtychoViewer, self).__init__()

        # instantiate the form class and set it up in the current QMainWindow
        self.ui = design.Ui_MainWindow()
        self.ui.setupUi(self)

        # keep a ProbeManager instance
        self.probeManager = ProbeManager(self.ui)

        # possibly set initial values
        if filename:
            self.ui.filenameBox.setText(filename)
            self.load()

        # connect browse button
        def wrap():
            result = qt.QFileDialog.getOpenFileName()
            # PyQt5 gives a tuple here...
            if type(result) == tuple:
                result = result[0]
            self.ui.filenameBox.setText(result)
        self.ui.browseButton.clicked.connect(wrap)

        # connect load button
        self.ui.loadButton.clicked.connect(self.load)

        # dummy scan
        self.scan = None

    def statusOutput(self, msg):
        self.ui.statusbar.showMessage(msg)
        self.ui.statusbar.showMessage(msg)

    def load(self):
        try:
            self.statusOutput("Loading data...")
            inputFile = self.ui.filenameBox.text()

            # load reconstruction data
            with h5py.File(inputFile, 'r') as hf:
                scanid = str(list(hf['content/probe'].keys())[0])
                print('loading entry %s' % scanid)
                probe = np.array(hf.get('content/probe/%s/data' % scanid))
                obj = np.array(hf.get('content/obj/%s/data' % scanid))
                psize = np.array(hf.get('content/probe/%s/_psize' % scanid))
                energy = np.array(hf.get('content/probe/%s/_energy' % scanid))
                origin = np.array(hf.get('content/probe/%s/_origin' % scanid))

                probe = probe[0]
                obj = obj[0]
                psize = psize[0]

            print("Loaded probe %d x %d and object %d x %d, pixel size %.1f nm, energy %.2f keV"%(probe.shape + obj.shape + (psize*1e9, energy)))
            
            # give loaded data to the widgets
            self.ui.objectWidget.set_data(obj, origin, psize)
            self.probeManager.set_data(probe, psize, energy)

            self.statusOutput("")
        except Exception as e:
            self.statusOutput("Loading failed. See terminal output for details.")
            print('The error was: ', e)

if __name__ == '__main__':
    # you always need a qt app
    app = qt.QApplication(sys.argv)

    # Parse input
    import argparse
    parser = argparse.ArgumentParser(
        description='This application visualizes the output of a ptypy run, by loading a ptyr file.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('file', type=str, nargs='?',
                        help='a ptypy reconstruction file', default=None)
    args = parser.parse_args()

    # instantiate and show the main object
    viewer = PtychoViewer(args.file)
    viewer.show()
    # run the app
    app.exec_()
