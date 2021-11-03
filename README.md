## Installation:

### From conda

For the easiest installation, including dependencies, use conda. Install Anaconda3, miniconda3, or so (Google knows how). If you're working at the MAX IV compute cluster, Anaconda is already installed and the installation is loaded with:

```
module load Anaconda3
```

First, set up the conda-forge and maxiv software channels.

```
conda config --add channels conda-forge
conda config --add channels maxiv
```

Next, create and activate your conda environment, name it what you like (my_env here).

```
conda create -n my_env
conda activate my_env
```

Now, installing the nmutils package will install all the dependencies.

```
conda install -c maxiv nanomax-analysis-utils
```

When that's done, you can use the library or run the `scanViewer` application directly. For Eiger images, it's good to have `bitshuffle` or `hdf5plugin` installed.

NOTE: Windows users have noticed that silx does not play well with glymur 0.9.5 (one of its dependencies). To get around this, they have downgraded glymur after the above installation steps, as follows.

```
conda install glymur=0.9.4
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
