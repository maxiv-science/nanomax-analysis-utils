## Installation:

One can get installed *nanomax-analysis-utils* in various ways including *maxiv* conda channel. The software there however may not be up-to-date or available for any Python version or cpu-architecture. Using a combination of *conda* and *git* seems as the most universal solution.

### conda and git

Let's use *conda* to create a virtual environment and let's install *nanomax-analysis-utils* from source repo on GitHub.

Use preinstalled `Anaconda3`, `Miniconda3` or `Mamba` at MAX IV cluster or LUNARC and install or use any snake-like tool providing `conda` elsewhere. 
```
module add Anaconda3    # when at MAX IV cluster or LUNARC
```

Create the environment, called `nmutils-24a` here, and install dependecies. You may want to omit Intel MKL `libblas=*=*mkl` on non-x86 (e.g. arm) cpus.

```
conda create -n nmutils-24a -c conda-forge python=3.11 numpy scipy matplotlib h5py hdf5plugin silx qtconsole cython git libblas=*=*mkl
```

Activate environment. You may need to use `source activate ...` at MAX IV and LUNARC. `conda activate` may have the same effect elesewhere.

```
source activate nmutils-24a    # note: Use `source activate` at MAX IV
```

Get source, checkout the release branch and install from the source with pip.

```
git clone https://github.com/maxiv-science/nanomax-analysis-utils.git
cd nanomax-analysis-utils
git checkout v0.4.4
pip install .
```

Test importing the module and starting the *scanViewer* gui.

```
python -c "import nmutils"
scanViewer
```

Note: It is know that on Windows this method does not produce a correct *scanViewer* executabale. This needs to be investigated more.

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
