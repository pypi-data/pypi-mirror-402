Opinionated version numbering CLIs, and library

--------------------------------------------------------------------------------

This project aims at easing the burden of computing and managing a project's
version numbers by leveraging `git` tags and commit trailers.

`simple-git-versioning` provides two CLIs: `semver2` and `pep440`, one for each
supported versioning sheme of the same name: [`SemVer2`](https://semver.org) and 
[`PEP440`](https://peps.python.org/pep-0440/).

Integration with [`setuptools`](#setuptools) is supported.

Snippets to expose your project's version number programatically are provided in
the [`Libraries`](#libraries) section.

# Installation

With `pip`:

```python
pip install simple-git-versioning
```

# Usage

By default, `pep440` and `semver2` will compute a version number of the form
`X.Y.Z`. Every project starts at `0.0.0` on their initial commit, and each
commit after that increments the number `Z` by one, unless they include a
`Version-Bump` trailer (case-insensitive) with a value of:
- `major`: `X` is incremented;
- `minor`: `Y` is incremented;
- `patch`: `Z` is incremented (same as the default).

Each tool then provides the ability to _switch_ to a pre-release mode; or
post-release, and/or dev release, etc. in the case of `pep440`.

## CLIs

All CLIs provide comprehensive help messages, available via the `--help` option.

## Libraries

Libraries that wish to expose their version number programatically may do so by
including the following snippet:

### `PEP440`

```python
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from versioning.pep440 import NoVersion, Project

try:
    __version__ = version("<your python package's name>")
except PackageNotFoundError:
    # package is not installed
    with Project(path=Path(__file__).parent) as project:
        try:
            __version__ = str(project.version())
        except NoVersion:
            __version__ = str(project.release(dev=0))
```

### `SemVer2`

```python
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from versioning.semver2 import NoVersion, Project

try:
    __version__ = version("<your python package's name>")
except PackageNotFoundError:
    # package is not installed
    with Project(path=Path(__file__).parent) as project:
        try:
            __version__ = str(project.version())
        except NoVersion:
            __version__ = str(project.release(pre=("dev", 0))
```

## `setuptools`

If you use `setuptools` as a build backend for your project, you can configure
`simple-git-versioning` to derive a version automatically as follows:

In your `pyproject.toml`:
  - declare `version` as a dynamic metadata field;
  - add `simple-git-versioning` to your project's `build-system.requires`;
  - enable the `setuptools` integration in your `pyproject.toml`, and pick the
    versioning scheme you wish to apply.

```toml
[project]
name = ...
dynamic = ["version"]

[build-system]
requires = ["setuptools>=63", "simple-git-versioning[setuptools]"]
build-backend = "setuptools.build_meta"

[tool.simple-git-versioning.setuptools]
# scheme = "pep440" (default) or "semver2"
```

## `hatchling`

If you use `hatchling` as a build backend for your project, you can configure
`simple-git-versioning` to derive a version automatically as follows:

In your `pyproject.toml`:
  - declare `version` as a dynamic metadata field;
  - add `simple-git-versioning` to your project's `build-system.requires`;
  - enable the `hatchling` integration in your `pyproject.toml`, and pick the
    versioning scheme you wish to apply.

```toml
[project]
name = ...
dynamic = ["version"]

[build-system]
requires = ["hatchling", "simple-git-versioning[hatchling]"]
build-backend = "hatchling.build"

[tool.hatch.version]
source = "simple-git-versioning"
# scheme = "pep440" (default) or "semver2"
```

## CI/CD

Maintainers may prefer to keep their CI/CD configuration agnostic to
`simple-git-versioning`. In this case, they should instruct
`simple-git-versioning` to switch to release mode by setting the
`SIMPLE_GIT_VERSIONING_RELEASE` environment variable (to any value other than
the empty string, `0`, or `false`) and use their build frontend to extract the
current (release) version:

```bash
SIMPLE_GIT_VERSIONING_RELEASE=1 pdm show --version
```

> Without `SIMPLE_GIT_VERSIONING_RELEASE`, the version you would extract would
> have a `dev` suffix and a local segment identifying the current commit (e.g.
> `0.3.6.dev0+04aa73b`).

> `uv version` currently does not support computing dynamic versions, but it
> eventually should: https://github.com/astral-sh/uv/issues/14137.
