from .ScanViewer import ScanViewer
import sys
from silx.gui import qt

def main():
    # you always need a qt app
    app = qt.QApplication(sys.argv)
    app.setStyle('Fusion')
    # for convenience, you can pass the filename as an argument
    fn = None
    if len(sys.argv) >= 2:
        fn = sys.argv[1]
    # instantiate and show the main object
    viewer = ScanViewer(fn)
    viewer.show()
    # run the app
    app.exec_()
