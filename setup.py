from setuptools import setup, find_packages

setup(
    name = "NanoMAX Analysis Utilities",
    version = "0.4.1",
    packages = find_packages(),
    install_requires = ['numpy', 'h5py', 'silx>=0.11'],
    scripts = ['apps/scanViewer', 'apps/ptychoViewer', 'apps/limaLiveViewer', 'apps/fluxMonitor.py', 'apps/streamLiveViewer/streamLiveViewer.py'],
    )
