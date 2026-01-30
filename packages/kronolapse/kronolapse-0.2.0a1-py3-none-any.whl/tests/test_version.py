# -*- mode: python -*-
# -*- coding: utf-8 -*-
#
# test_version.py
#
# To ensure that the version reported by the package's __version__
# attribute within the imported module matches the version reported by
# importlib.metadata.version("dist-name") for the installed
# distribution.

from kronolapse.__main__ import __version__
from importlib.metadata import version


def test_version():
    pkg_version_attribute = __version__
    dist_version = version("kronolapse")
    assert pkg_version_attribute == dist_version, \
        f"Version mismatch: __version__ is {pkg_version_attribute}, " \
        f"but importlib.metadata reports {dist_version}"
