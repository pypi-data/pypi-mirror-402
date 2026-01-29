# SPDX-License-Identifier: MIT

import string
from collections.abc import Iterable, Iterator
from dataclasses import replace
from itertools import combinations
from random import sample
from typing import Any

import pytest
from hypothesis import given
from hypothesis.strategies import (
    SearchStrategy,
    booleans,
    composite,
    integers,
    iterables,
    just,
    none,
    one_of,
    sampled_from,
    text,
    tuples,
)

from versioning.pep440 import (
    IllegalRelease,
    InvalidVersion,
    PreRelease,
    PreReleaseLabel,
    Project,
    Version,
)

from .. import testdir  # noqa: F401  (autouse fixture)
from . import (
    BREAKING_CHANGE,
    FEATURE,
    INIT,
    PATCH,
    GitBranch,
    GitOperation,
    GitSwitch,
    GitVersion,
    Release,
    project,
)


@pytest.mark.parametrize(
    ("labels",),
    [
        pytest.param((PreReleaseLabel.A, PreReleaseLabel.ALPHA), id="alpha"),
        pytest.param((PreReleaseLabel.B, PreReleaseLabel.BETA), id="beta"),
        pytest.param((PreReleaseLabel.C, PreReleaseLabel.RC, PreReleaseLabel.PRE, PreReleaseLabel.PREVIEW), id="rc"),
    ],
)
def test_pre_release_label_aliases(labels: Iterable[PreReleaseLabel]):
    assert len(set(labels)) == 1


@pytest.mark.parametrize(
    ("labels", "expected"),
    [
        pytest.param((PreReleaseLabel.A, PreReleaseLabel.ALPHA), "alpha", id="alpha"),
        pytest.param((PreReleaseLabel.B, PreReleaseLabel.BETA), "beta", id="beta"),
        pytest.param(
            (PreReleaseLabel.C, PreReleaseLabel.RC, PreReleaseLabel.PRE, PreReleaseLabel.PREVIEW),
            "release candidate",
            id="rc",
        ),
    ],
)
def test_pre_release_label_str(labels: Iterable[PreReleaseLabel], expected: str):
    assert all(str(label) == expected for label in labels)


def test_pre_release_label_ordering():
    expected = [PreReleaseLabel.A, PreReleaseLabel.B, PreReleaseLabel.C]
    assert sorted(expected) == expected


def test_pre_release_label_invalid_comparison():
    with pytest.raises(TypeError):
        PreReleaseLabel.A < None


def test_version_major():
    assert Version(release=(1, 2, 3)).major == 1


@pytest.mark.parametrize(
    ("release", "expected"),
    [
        pytest.param((1, 2, 3), 2, id="explicit"),
        pytest.param((1,), 0, id="implicit"),
    ],
)
def test_version_minor(release: tuple[int, ...], expected: int):
    assert Version(release=release).minor == expected


@pytest.mark.parametrize(
    ("release", "expected"),
    [
        pytest.param((1, 2, 3), 3, id="explicit"),
        pytest.param((1,), 0, id="implicit"),
    ],
)
def test_version_patch(release: tuple[int, ...], expected: int):
    assert Version(release=release).patch == expected


def test_invalid_version():
    with pytest.raises(InvalidVersion, match="not-a-version"):
        Version.parse("not-a-version")


@composite
def pre_releases(draw) -> PreRelease:
    return PreRelease(
        label=draw(sampled_from(PreReleaseLabel)),
        revision=draw(integers(min_value=0)),
    )


@composite
def _segments(
    draw,
    *,
    alphabet: str = string.ascii_lowercase + string.digits,
) -> str:
    return draw(text(alphabet=alphabet, min_size=1).filter(lambda x: not set(x) <= set(string.digits)))


@composite
def segments(
    draw,
    *,
    integers: SearchStrategy[int] = integers(min_value=0),
    strings: SearchStrategy[str] = _segments(),
) -> int | str:
    return draw(one_of(integers, strings))


@composite
def locals__(
    draw, *, segments: SearchStrategy[Iterable[int | str]] = iterables(segments()), end_with_integer: bool | None = None
) -> tuple[int | str, ...]:
    segments_ = tuple(draw(segments))
    if end_with_integer is True and (not segments_ or not isinstance(segments_[-1], int)):
        segments_ += (draw(integers(min_value=0)),)
    elif end_with_integer is False and segments_ and isinstance(segments_[-1], int):
        segments_ += (draw(_segments()),)
    return segments_


@composite
def versions(
    draw,
    *,
    epoch: SearchStrategy[int] = integers(min_value=0),
    release: SearchStrategy[tuple[int, ...]] = tuples(
        integers(min_value=0), integers(min_value=0), integers(min_value=0)
    ),
    pre: SearchStrategy[PreRelease | None] = pre_releases(),
    post: SearchStrategy[int | None] = one_of(integers(min_value=0), none()),
    dev: SearchStrategy[int | None] = one_of(integers(min_value=0), none()),
    local: SearchStrategy[tuple[str | int, ...] | None] = locals__(),
) -> Version:
    return Version(
        epoch=draw(epoch),
        release=draw(release),
        pre=draw(pre),
        post=draw(post),
        dev=draw(dev),
        local=draw(local),
    )


@given(version=versions())
def test_version_parse_as_themselves(version: Version):
    assert Version.parse(str(version)) == version


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        pytest.param("0.0.0", False, id="regular"),
        pytest.param("0.0.0a0", True, id="alpha"),
        pytest.param("0.0.0b0", True, id="beta"),
        pytest.param("0.0.0rc0", True, id="candidate"),
        pytest.param("0.0.0.dev0", True, id="dev"),
        pytest.param("0.0.0a0.dev0", True, id="dev-alpha"),
        pytest.param("0.0.0b0.dev0", True, id="dev-beta"),
        pytest.param("0.0.0rc0.dev0", True, id="dev-candidate"),
    ],
)
def test_version_is_pre_release(version: str, expected: bool):
    assert Version.parse(version).is_prerelease() == expected


@composite
def options(
    draw,
    *,
    dev: SearchStrategy[bool] = booleans(),
    local: SearchStrategy[tuple[int | str, ...]] = locals__(),
) -> dict[str, Any]:
    alpha, beta, rc, release, post = sample([False, False, False, False, draw(booleans())], k=5)
    return dict(
        alpha=alpha,
        beta=beta,
        rc=rc,
        release=release,
        post=post,
        dev=draw(dev),
        local=draw(local),
    )


def sorted_version_strings() -> tuple[str, ...]:
    return (
        "0.0.0a0.dev0",
        "0.0.0a0.dev2",
        "0.0.0a0.dev10",
        "0.0.0a0",
        "0.0.0a2",
        "0.0.0a10",
        "0.0.0a10-post0.dev0",
        "0.0.0a10-post0",
        "0.0.0a10-post2",
        "0.0.0a10-post10",
        "0.0.0b0",
        "0.0.0rc0",
        "0.0.0.dev0",
        "0.0.0",
        "0.0.0+build",
        "0.0.0+build.a",
        "0.0.0+build.0",
        "0.0.0+build.2",
        "0.0.0+build.10",
        "0.0.0+build0.0",
        "0.0.0+build10.0",
        "0.0.0+build2.0",
        "0.0.0-post0.dev0",
        "0.0.0-post0",
        "0.0.2",
        "0.0.10",
        "0.2.0",
        "0.10.0",
        "2.0.0",
        "10.0.0",
        "2!0.0.0.a0.dev0",
        "10!0.0.0.a0.dev0",
    )


def sorted_versions() -> Iterator[Version]:
    yield from map(Version.parse, sorted_version_strings())


def test_version_unsupported_comparison():
    with pytest.raises(TypeError):
        Version() < None


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


@pytest.mark.parametrize(
    ("options",),
    [
        pytest.param(options, id=" | ".join(options))
        for options in (
            {key: True for key in keys} for keys in combinations(("alpha", "beta", "rc", "release", "post"), 2)
        )
    ],
)
def test_project_incompatible_release_options(options: dict[str, bool]):
    with project(Project, INIT) as proj:
        with pytest.raises(ValueError, match=r".*".join(rf"\b{key}\b" for key in options)):
            proj.release(**options)


@given(version=versions(dev=just(None), local=just(())))
def test_project_rerelease_without_local(version: Version):
    with project(Project, INIT, GitVersion(version=version)) as proj:
        assert proj.release() == replace(version, local=())


def test_project_rerelease_trims_local():
    with project(Project, INIT, GitVersion(version=Version(local=("build", 0)))) as proj:
        assert proj.release() == Version()


def test_project_dev_versions_should_not_be_published():
    with project(Project, INIT, GitVersion(version=Version(dev=0))) as proj:
        with pytest.raises(IllegalRelease):
            proj.release()


@pytest.mark.parametrize(
    ("setup",),
    [
        pytest.param((INIT,), id="no-release"),
        pytest.param((INIT, Release(options=dict(alpha=True))), id="pre-release"),
    ],
)
def test_project_post_release_without_release(setup: Iterable[GitOperation]):
    with project(Project, *setup) as proj:
        with pytest.raises(IllegalRelease):
            proj.release(post=True)


VERSION_1_0_0a0 = (INIT, BREAKING_CHANGE, Release(options=(dict(alpha=True))))
VERSION_1_0_0 = (INIT, BREAKING_CHANGE, Release())


@pytest.mark.parametrize(
    ("setup", "options", "expected"),
    [
        pytest.param(
            VERSION_1_0_0,
            dict(post=True),
            "1.0.0-post0",
            id="1.0.0 / post -> 1.0.0-post0",
        ),
        pytest.param(
            VERSION_1_0_0 + (Release(options=dict(post=True)), PATCH),
            dict(post=True),
            "1.0.0-post1",
            id="1.0.0-post0 + patch / post -> 1.0.0-post1",
        ),
        pytest.param(
            VERSION_1_0_0a0 + (PATCH,),
            dict(alpha=True),
            "1.0.0a1",
            id="1.0.0a0 + patch / alpha -> 1.0.0a1",
        ),
        pytest.param(
            VERSION_1_0_0a0,
            dict(release=True),
            "1.0.0",
            id="1.0.0a0 / release -> 1.0.0",
        ),
    ],
)
def test_project_release(setup: Iterable[GitOperation], options: dict[str, Any], expected: str):
    with project(Project, *setup) as proj:
        assert proj.release(**options) == proj.scheme.parse(expected)


def test_project_duplicate_release():
    with project(
        Project,
        INIT,
        GitBranch(name="feature/one"),
        GitSwitch(branch="feature/one"),
        replace(FEATURE, title="one"),
        Release(),
        GitSwitch(branch="main"),
        replace(FEATURE, title="two"),
    ) as proj:
        with pytest.raises(IllegalRelease, match=proj.canonical("feature/one")):
            proj.release()
