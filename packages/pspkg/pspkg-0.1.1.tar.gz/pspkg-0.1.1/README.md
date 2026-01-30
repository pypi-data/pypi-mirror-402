# PyScript Packages (pspkg) 📦

[PyScript](https://pyscript.net/) is a platform for Python in the browser.

This is a deliberately simple module and command line tool for discovering the
compatibility of packages in PyPI with [PyScript](https://pyscript.net/).
It's a shim around the static API provided by the
[PyScript Packages](https://packages.pyscript.net/) website.

Why?

Running Python in the context of a browser means certain assumptions made by
packages running in traditional Python environments do not apply. This tool
provides details about packages compatible with PyScript so developers can
make informed decisions about which packages to use.

## Usage 💻

```
pip install pspkg
```

This will install the module and give you a command line tool called `pspkg`.

```
$ pspkg --help
usage: pspkg.py [-h] [--refresh] [--reset] [PACKAGES ...]

A simple client for the PyScript packages static API.

positional arguments:
  PACKAGES              Package names to check for support. Emits JSON output.

options:
  -h, --help            show this help message and exit
  --refresh             Refresh the local dump of supported packages from the API.
  --reset               Delete the local dump of supported packages.
```

For example:

```
$ pspkg numpy dogpt pyqt5 qwertyuiop123
```

Will emit JSON data about the support status of the four packages `numpy`,
`dogpt`, `pyqt5` and `qwertyuiop123`.

Use the module within Python code like this, to gather the same package
information:

```
import pspkg

# A blocking call to get package support info. The cache will be automatically
# filled.
pkg_info = pspkg.match_packages(["numpy", "dogpt", "pyqt5", "qwertyuiop123", ])

# Reset the cache.
pspkg.reset()

# Refresh the cache from the Python projects API.
pspkg.refresh()
```

A local cache is stored in the location specified by the environment variable
`PYSCRIPT_PACKAGES_CACHE` or, if not specified, a file called
`pspkg_cache.json` adjacent to the location of the module on the local
filesystem.

## Output 📊

The output data contains an entry for each package specified. Each entry is
referenced by a key that is the package name.

```
{
    "numpy": {
        "supported": True,
        "info": {
            ...
        }
    },
    "dogpt": {
        "supported": False,
        "is_pure_python": True,
        "info": {
            ...
        }
    },
    "pyqt5": {
        "supported": False,
        "is_pure_python": False,
        "info": {
            ...
        }
    },
    "qwertyuiop123": {
        "supported": False,
        "is_pure_python": False,
        "info": None,
    }
}
```

The associated values for each package depend on the status of the package.
Given the example package list, the following states exist:

* `numpy` - known to be supported by PyScript. The `info` dict will contain
  information conforming to the metadata specified by the
  [PyScript packages API](https://packages.pyscript.net/help/#api).
* `dogpt` - unknown PyScript support. But
  [metadata from PyPI](https://docs.pypi.org/api/json/) indicates this is a
  pure Python package, so *could work* (pending user validation). The `info`
  dict will contain information describing the package from PyPI.
* `pyqt5` - unknown PyScript support. PyPI metadata suggests this is NOT a
  pure Python package and so will definitely NOT work with PyScript. The
  `info` dict will contain information describingthe package from PyPI.
* `qwertyuiop123` - unknown PyScript support. An unknown package on PyPI. Have
  you typed in the package name properly?

## Contributing 💐

Create a virtual environment, clone the GitHub repository, and then install the
local dependencies like this:

```
pip install -e .[dev]
```

We have a simple Makefile to automate common local development tasks. Please
read it to learn more. 

Many thanks for wanting to improve the project.

Contributions are welcome without prejudice from *anyone* irrespective of
their background. If you're thinking, "but they don't mean me", *then we
especially mean YOU*. Good quality code and engagement with respect, humour
and intelligence wins every time.

We expect contributors to follow the spirit of our statement on the
care of community (CARE_OF_COMMUNITY.md) file found within this repository.

Feedback may be given for contributions and, where necessary, changes will
be politely requested and discussed with the originating author. Respectful
yet robust argument is most welcome.

**Contributions are subject to the following caveats**: the contribution
was created by the contributor who, by submitting the contribution, is
confirming that they have the authority to submit the contribution and
place it under the license as defined in the license (LICENSE.md) file found
within this repository. If this is a significant contribution
the contributor should add themselves to the AUTHORS.md file found in the
root of this repository. Contributors agree, for the sake of convenience,
that copyright passes exclusively to Anaconda Inc. on behalf of the
project.

## Acknowledgements ❤️

Huge thanks to [Anaconda](https://anaconda.com/), who support the development
of PyScript.