# SPDX-License-Identifier: MIT

from collections.abc import Iterable, Iterator
from itertools import combinations
from typing import Any

import pytest

from versioning.semver2 import Project, Version

from .. import testdir  # noqa: F401  (autouse fixture)
from . import INIT, PATCH, GitOperation, GitTag, Release, project


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        pytest.param("0.0.0", False, id="regular"),
        pytest.param("0.0.0-pre", True, id="-pre"),
        pytest.param("0.0.0-0", True, id="-0"),
        pytest.param("0.0.0-pre.0", True, id="-pre.0"),
    ],
)
def test_version_is_pre_release(version: str, expected: bool):
    assert Version.parse(version).is_prerelease() == expected


def sorted_version_strings() -> tuple[str, ...]:
    return (
        "0.0.0-0.0",
        "0.0.0-2.0",
        "0.0.0-10.0",
        "0.0.0-pre",
        "0.0.0-pre0",
        "0.0.0-pre10",
        "0.0.0-pre2",
        "0.0.0-pre2.0",
        "0.0.0-pre2.2",
        "0.0.0-pre2.10",
        "0.0.0",
        "0.0.2",
        "0.0.10",
        "0.2.0",
        "0.10.0",
        "2.0.0",
        "10.0.0",
    )


def sorted_versions() -> Iterator[Version]:
    yield from map(Version.parse, sorted_version_strings())


@pytest.mark.parametrize(("version",), [pytest.param(version, id=str(version)) for version in sorted_versions()])
def test_version_self_comparison(version: Version):
    assert version == version
    assert version <= version
    assert version >= version


@pytest.mark.parametrize(
    ("less", "more"),
    [pytest.param(less, more, id=f"{less} < {more}") for less, more in combinations(sorted_versions(), 2)],
)
def test_version_comparison(less: Version, more: Version):
    assert less != more
    assert less < more
    assert more > less


def test_project_incompatible_release_options():
    with project(Project, INIT) as proj:
        with pytest.raises(ValueError):
            proj.release(pre=("pre", 0), release=True)


@pytest.mark.parametrize(
    ("setup", "options", "expected"),
    [
        pytest.param(
            (INIT,),
            dict(pre=("rc",)),
            "0.0.0-rc.0",
            id="none + patch / rc -> 0.0.0-rc.0",
        ),
        pytest.param(
            (INIT, GitTag(value="0.0.0-rc"), PATCH),
            dict(),
            "0.0.0-rc.1",
            id="0.0.0-rc + patch -> 0.0.0-rc.1",
        ),
        pytest.param(
            (INIT, Release(options=dict(pre=("rc",)))),
            dict(pre=("rc",)),
            "0.0.0-rc.0",
            id="0.0.0-rc.0 / rc -> 0.0.0-rc.0",
        ),
        pytest.param(
            (INIT, Release(options=dict(pre=("rc",))), PATCH),
            dict(),
            "0.0.0-rc.1",
            id="0.0.0-rc.0 + patch -> 0.0.0-rc.1",
        ),
        pytest.param(
            (INIT, Release(options=dict(pre=("rc",)))),
            dict(release=True),
            "0.0.0",
            id="0.0.0-rc.0 / release -> 0.0.0",
        ),
    ],
)
def test_project_release(setup: Iterable[GitOperation], options: dict[str, Any], expected: str):
    with project(Project, *setup) as proj:
        assert proj.release(**options) == proj.scheme.parse(expected)
