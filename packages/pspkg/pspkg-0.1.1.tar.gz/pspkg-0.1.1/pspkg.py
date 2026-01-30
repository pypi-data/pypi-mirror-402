"""
A simple and deliberately naive client for consuming the PyScript packages
static API.

This is a straw man pending feedback.

Copyright © `2025` `Anaconda Inc. https://www.anaconda.com/`

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the “Software”), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

"""

import argparse
import os
import requests
import json
from typing import Dict, List

__version__ = "0.1.1"

__all__ = [
    "refresh",
    "reset",
    "match_packages",
]


# The default location on the local filesystem for the dump of supported
# packages (from an ENVAR or just fall back to a default location).
_CACHE_FILEPATH = os.environ.get("PYSCRIPT_PACKAGES_CACHE") or os.path.join(
    os.path.dirname(__file__), "pspkg_cache.json"
)


def _refresh_supported_packages() -> Dict:
    """
    Fetch the list of supported packages from the PyScript packages static
    API.
    """
    response = requests.get(
        "https://packages.pyscript.net/api/all.json"
    )
    response.raise_for_status()
    return response.json()


def _get_pypi_package_info(package_name: str) -> Dict:
    """
    Fetch package information from the PyPI JSON API.
    """
    response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
    response.raise_for_status()
    return response.json()


def _load_supported_packages() -> Dict:
    """
    Load the supported packages from the local cache file. If the file does
    not exist, fetch the data from the API and create the cache file.
    """
    if not os.path.exists(_CACHE_FILEPATH):  #
        refresh()
    with open(_CACHE_FILEPATH, "r") as f:
        return json.load(f)


def refresh():
    """
    Refresh the local cache file of supported packages from the PyScript
    packages static API.
    """
    supported_packages = _refresh_supported_packages()
    with open(_CACHE_FILEPATH, "w") as f:
        json.dump(supported_packages, f, indent=2)


def reset():
    """
    Delete the local cache file of supported packages.
    """
    if os.path.exists(_CACHE_FILEPATH):
        os.remove(_CACHE_FILEPATH)


def match_packages(required_packages: List) -> Dict[str, Dict]:
    """
    Given a set of required package names, return a dictionary indicating
    whether each package is confirmed as supported, or has a potential pure
    Python wheel available or is definitely not supported.
    """
    supported_packages_data = _load_supported_packages()
    result = {}
    for package in required_packages:
        if package in supported_packages_data:
            # Known to be supported, so return all the version/Pyodide/etc
            # metadata from the API.
            result[package] = {
                "supported": True,
                "info": supported_packages_data[package],
            }
        else:
            # No known support. So check PyPI for basic info. If the package
            # doesn't exist on PyPI, we just return None for info. Otherwise
            # we return the basic PyPI info while also indicating if the
            # package has a "none-any" wheel available.
            try:
                pypi_info = _get_pypi_package_info(package)
                wheels = [
                    file_info
                    for file_info in pypi_info["releases"].get(
                        pypi_info["info"]["version"], []
                    )
                    if file_info["filename"].endswith("none-any.whl")
                ]
                result[package] = {
                    "supported": False,
                    "is_pure_python": len(wheels) > 0,
                    "info": pypi_info,
                }
                continue
            except requests.HTTPError as e:
                # 404? Package not found on PyPI, otherwise report.
                if e.response.status_code != 404:
                    raise
            result[package] = {
                "supported": False,
                "is_pure_python": False,
                "info": None,
            }
    return result


def main():
    """
    A simple command line interface for the pspkg module.
    """
    parser = argparse.ArgumentParser(
        description="A simple client for the PyScript packages static API."
    )
    parser.add_argument(
        "packages",
        metavar="PACKAGES",
        type=str,
        nargs="*",
        help="Package names to check for support. Emits JSON output.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh the local dump of supported packages from the API.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the local dump of supported packages.",
    )

    args = parser.parse_args()

    if args.reset:
        reset()
        print("Local dump of supported packages has been deleted.")
    elif args.refresh:
        refresh()
        print("Local dump of supported packages has been refreshed.")
    elif args.packages:
        matches = match_packages(args.packages)
        print(json.dumps(matches, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
