# SPDX-License-Identifier: MIT

from itertools import combinations
from typing import Literal

import pytest
from hypothesis import given
from hypothesis.strategies import composite, integers

from versioning.pep440 import Version as PEP440Version
from versioning.semver2 import Version as SemVer2Version
from versioning.version import InvalidVersion, Version, VersionBump

from . import DummyVersion


def across_implementations() -> pytest.MarkDecorator:
    return pytest.mark.parametrize(
        "implementation",
        [
            pytest.param(DummyVersion, id="dummy"),
            pytest.param(PEP440Version, id="pep440"),
            pytest.param(SemVer2Version, id="semver2"),
        ],
    )


def test_invalid_version():
    assert InvalidVersion("not-a-valid-version").version == "not-a-valid-version"


@pytest.mark.parametrize(
    ("version", "bump", "expected"),
    [
        pytest.param(version, bump, expected, id=f"{version} | {bump} -> {expected}")
        for version, bump, expected in (
            ("0.0.0", "patch", "0.0.1"),
            ("0.0.0", "minor", "0.1.0"),
            ("0.0.1", "minor", "0.1.0"),
            ("0.0.0", "major", "1.0.0"),
            ("0.1.1", "major", "1.0.0"),
        )
    ],
)
@across_implementations()
def test_version_bump(
    implementation: type[Version],
    version: str,
    bump: Literal["patch"] | Literal["minor"] | Literal["major"],
    expected: str,
):
    assert implementation.parse(version).bump(VersionBump(bump)) == implementation.parse(expected)


@composite
def version_strings(
    draw,
) -> str:
    return f"{draw(integers(min_value=0))}.{draw(integers(min_value=0))}.{draw(integers(min_value=0))}"


@given(version_string=version_strings())
@across_implementations()
def test_version_parse_as_themselves(implementation: type[Version], version_string: str):
    version = implementation.parse(version_string)
    assert implementation.parse(str(version)) == version


def sorted_version_strings() -> tuple[str, ...]:
    return (
        "0.0.0",
        "0.0.2",
        "0.0.10",
        "0.2.0",
        "0.10.0",
        "2.0.0",
        "10.0.0",
    )


@across_implementations()
def test_version_unsupported_comparison(implementation: type[Version]):
    with pytest.raises(TypeError):
        implementation() < None


@pytest.mark.parametrize(
    ("version_string",),
    [pytest.param(version_string, id=version_string) for version_string in sorted_version_strings()],
)
@across_implementations()
def test_version_self_comparison(implementation: type[Version], version_string: str):
    version = implementation.parse(version_string)
    assert version == version
    assert version <= version
    assert version >= version


@pytest.mark.parametrize(
    ("less_string", "more_string"),
    [
        pytest.param(less_string, more_string, id=f"{less_string} < {more_string}")
        for less_string, more_string in combinations(sorted_version_strings(), 2)
    ],
)
@across_implementations()
def test_version_comparison(implementation: type[Version], less_string: str, more_string: str):
    less, more = implementation.parse(less_string), implementation.parse(more_string)
    assert less != more
    assert less < more
    assert more > less
