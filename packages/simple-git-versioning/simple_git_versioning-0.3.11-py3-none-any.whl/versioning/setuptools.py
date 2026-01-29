import logging
from collections.abc import Mapping
from dataclasses import replace
from io import TextIOWrapper
from pathlib import Path

try:
    import tomllib
except ImportError:
    import toml

from sh.contrib import git

from setuptools import Distribution
from versioning import pep440, semver2
from versioning.project import InvalidReference, NotAGitWorkTree, NoVersion

LOGGER = logging.getLogger(__name__)


def finalize_distribution_options(distribution: Distribution) -> None:  # pragma: no cover
    if distribution.metadata.version is not None:
        LOGGER.debug(f"version is set already to: {distribution.metadata.version}")
        return

    try:
        with open("pyproject.toml", mode="rb") as stream:
            try:
                pyproject = tomllib.load(stream)
            except NameError:
                pyproject = toml.load(TextIOWrapper(stream))  # toml.load expects a TextIO
    except FileNotFoundError:
        LOGGER.debug("pyproject.toml not found: bailing out")
        return

    if (
        "project" not in pyproject
        or "dynamic" not in pyproject["project"]
        or "version" not in pyproject["project"]["dynamic"]
    ):
        LOGGER.debug("'version' is not set to be dynamic in pyproject.toml")
        return

    try:
        config = pyproject["tool"]["simple-git-versioning"]["setuptools"]
    except KeyError:
        LOGGER.debug("simple-git-versioning is not enabled")
        return

    if isinstance(config, str):
        scheme = config
    elif isinstance(config, Mapping):
        scheme = config.get("scheme", "pep440")
    else:
        raise TypeError(f"unexpected type for `tool.simple-git-versioning.setuptools`: '{type(config)}'")

    scheme = scheme.casefold()
    if scheme == "pep440":
        Project = pep440.Project
    elif scheme == "semver2":
        Project = semver2.Project
    else:
        raise ValueError(
            f"unexpected value for `tool.simple-git-versioning.setuptools.scheme`: '{scheme}', expected 'pep440' or 'semver2'"
        )

    if distribution.metadata.name is None:
        distribution.metadata.name = pyproject["project"]["name"]

    try:
        with Project(path=Path(".")) as proj:
            try:
                distribution.metadata.version = str(proj.version())
            except NoVersion:
                revision = git("rev-parse", "--short", "HEAD").strip()
                if isinstance(proj, pep440.Project):
                    options = dict(dev=0, local=(revision,))
                elif isinstance(proj, semver2.Project):
                    options = dict(build=revision)
                distribution.metadata.version = str(proj.release(**options))
            except InvalidReference:
                version = proj.scheme()
                if isinstance(proj, pep440.Project):
                    version = replace(version, dev=0, local=("norevision",))
                elif isinstance(proj, semver2.Project):
                    version = replace(version, build="norevision")
                distribution.metadata.version = str(version)
    except NotAGitWorkTree:
        with open("PKG-INFO") as stream:
            for line in stream:
                key, value = line.split(": ", maxsplit=1)
                if key == "Version":
                    distribution.metadata.version = value
                    break
