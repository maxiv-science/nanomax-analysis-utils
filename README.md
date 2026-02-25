## Installation and usage

### Use the GUI:s with `uv` (recommended)

These applications are most easily run by using the modern package manager `uv`, which sets up temporary virtual environments in the background.

If you don't have `uv` installed, install it using [the instructions](https://docs.astral.sh/uv/getting-started/installation/) for your system. On linux this is simply

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, navigate to the root folder and run one of the endpoints scanViewer or ptychoViewer. For example,

```
cd nanomax-analysis-utils
uv run python scanViewer
```

To install these endpoints so that you can run e.g. `scanViewer` from anywhere, install the package.

```
cd nanomax-analysis-utils
uv tool install .
```

### Install into an existing Python environment

To use the python library module `nmutils` in your own analysis scripts, it's convenient to install it into your favourite environment like you would any other module. For example,

```
cd nanomax-analysis-utils/nmutils
pip install .
```

which will also install the scanViewer and ptychoViewer endpoints into the env.
