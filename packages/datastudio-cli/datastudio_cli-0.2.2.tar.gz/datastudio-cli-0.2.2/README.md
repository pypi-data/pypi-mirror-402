# DataStudio datakit CLI

A command line client for running DataStudio datakits.

Usage documentation can be found [here](https://docs.datastudioapp.com).


## Development

To install and test locally, navigate to the datakit directory you want to
test.
```
cd /path/to/datakit
```

Create a virtualenv and install the CLI via pip in local mode:
```
python -m venv .venv
source .venv/bin/activate
pip install -e [/path/to/cli]
```

You can now run the CLI script with:
```
ds
```
