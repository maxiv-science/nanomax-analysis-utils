from setuptools import setup, find_packages

setup(
    name = "NanoMAX Analysis Utilities",
    version = "0.1a0",
    packages = find_packages(),
    install_requires = ['numpy', 'h5py'],
    scripts = ['apps/scanViewer.py', 'apps/ptychoViewer.py'],
    )
