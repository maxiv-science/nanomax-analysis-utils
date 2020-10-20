## Installation:

### From conda

For the easiest installation, including dependencies, use conda. Install Anaconda3, miniconda3, or so (Google knows how). Then,

```
conda config --add channels maxiv
conda install -c maxiv nanomax-analysis-utils
```

### From git

For the latest verision, clone this git repository.

```
git clone https://github.com/maxiv-science/nanomax-analysis-utils.git
```

From the main folder, to install for the current user.

```
cd nanomax-analysis-utils
python3 setup.py install --user
```

Note that use of scanViewer and other GUIs require the silx
package, as well as h5py and other common python packages.
These can be installed for the current userthrough pip.

```
pip3 install h5py --user
pip3 install silx --user
```

etc.
