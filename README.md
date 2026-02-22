## Installation:

Install *nanomax-analysis-utils* and the contained python library module *nmutils* using the modern package manager *uv*.

If you don't have *uv* installed, install it using [the instructions](https://docs.astral.sh/uv/getting-started/installation/) for your system. On linux this is simply

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, navigate to the root folder and run one of the endpoint apps. For example,

```
cd nanomax-analysis-utils
uv run python apps/scanViewer
```

To use the python library module *nmutils* in your own analysis scripts, install it into your favourite environment like you would any other module, for example

```
cd nanomax-analysis-utils/nmutils
pip install .
```

