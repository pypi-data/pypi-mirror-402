# SPDX-License-Identifier: MIT

"""
Opinionated version numbering library
"""


from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as importlib_metadata_version
from pathlib import Path

from .pep440 import Project as _Project
from .project import NoVersion

try:
    __version__ = importlib_metadata_version("simple-git-versioning")
except PackageNotFoundError:
    # package is not installed
    with _Project(path=Path(__file__).parent) as project:
        try:
            __version__ = str(project.version())
        except NoVersion:
            __version__ = str(project.release(dev=0))
