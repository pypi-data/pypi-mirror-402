# SPDX-License-Identifier: MIT

import os
from collections import deque
from collections.abc import Iterable
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from sh import pushd
from sh.contrib import git

from versioning.pep440 import Project as PEP440Project
from versioning.project import (
    AmbiguousReference,
    AmbiguousRoot,
    AmbiguousVersion,
    InvalidReference,
    InvalidVersionBumpTrailer,
    NotAGitWorkTree,
    NoVersion,
    Project,
)
from versioning.semver2 import Project as SemVer2Project

from .. import testdir  # noqa: F401  (autouse fixture)
from . import (
    BREAKING_CHANGE,
    FEATURE,
    INIT,
    PATCH,
    DummyProject,
    GitBranch,
    GitCommand,
    GitCommit,
    GitMerge,
    GitOperation,
    GitSwitch,
    GitTag,
    Release,
    gitdir,
    project,
)


def across_implementations() -> pytest.MarkDecorator:
    return pytest.mark.parametrize(
        "implementation",
        [
            pytest.param(DummyProject, id="dummy"),
            pytest.param(PEP440Project, id="pep440"),
            pytest.param(SemVer2Project, id="semver2"),
        ],
    )


def test_not_a_git_work_tree():
    not_a_git_work_tree = NotAGitWorkTree(Path("/dev/null"))
    assert isinstance(not_a_git_work_tree, RuntimeError)
    assert not_a_git_work_tree.path == Path("/dev/null")


@across_implementations()
def test_no_version(implementation: type[Project]):
    project = implementation(path=Path("."))
    no_version = NoVersion(project, "HEAD")
    assert isinstance(no_version, RuntimeError)
    assert no_version.project == project
    assert no_version.reference == "HEAD"


@pytest.mark.parametrize(
    ("exception",),
    [
        pytest.param(AmbiguousReference, id="reference"),
        pytest.param(AmbiguousRoot, id="root"),
        pytest.param(AmbiguousVersion, id="version"),
    ],
)
def test_ambiguous_reference(exception: type[AmbiguousReference]):
    ambiguous_version = exception("HEAD", ("01234567", "12345678"))
    assert isinstance(ambiguous_version, AmbiguousReference)
    assert isinstance(ambiguous_version, RuntimeError)
    assert ambiguous_version.reference == "HEAD"
    assert ambiguous_version.candidates == frozenset(("01234567", "12345678"))


def test_invalid_reference():
    invalid_reference = InvalidReference("01234567")
    assert isinstance(invalid_reference, ValueError)
    assert invalid_reference.reference == "01234567"


@across_implementations()
def test_is_inside_git_work_tree(implementation: type[Project]):
    with TemporaryDirectory() as tmpdir:
        gitdir(Path(tmpdir))
        with implementation(path=Path(tmpdir)):
            pass


@across_implementations()
def test_is_not_inside_git_work_tree(implementation: type[Project]):
    with TemporaryDirectory() as tmpdir:
        project = implementation(path=Path(tmpdir))
        with pytest.raises(NotAGitWorkTree):
            with project:
                pass


def test_invalid_version_bump_trailer():
    invalid_version_bump_trailer = InvalidVersionBumpTrailer("invalid-bump")
    assert isinstance(invalid_version_bump_trailer, ValueError)
    assert invalid_version_bump_trailer.bump, "invalid-bump"


@across_implementations()
def test_project_contextmanager(implementation: type[Project]):
    with TemporaryDirectory() as tmpdir:
        with TemporaryDirectory() as otherdir, pushd(otherdir):
            gitdir(Path(tmpdir))
            with implementation(path=Path(tmpdir)):
                assert os.getcwd() == tmpdir


@across_implementations()
def test_project_canonical(implementation: type[Project]):
    with project(implementation, INIT) as proj:
        assert proj.canonical("HEAD") == git("rev-parse", "HEAD").rstrip()


@across_implementations()
def test_project_canonical_invalid_reference(implementation: type[Project]):
    with project(implementation) as proj:
        with pytest.raises(InvalidReference, match="HEAD"):
            proj.canonical("HEAD")


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        pytest.param(tags, versions, id=f"{' | '.join(tags) or 'none'} -> {' | '.join(versions) or 'none'}")
        for tags, versions in (
            ((), ()),
            (("0.0.0",), ("0.0.0",)),
            (("not-a-version",), ()),
            (("0.0.0", "not-a-version"), ("0.0.0",)),
            (("0.0.0", "0.0.1"), ("0.0.0", "0.0.1")),
            (("0.0.0", "0.0.1", "not-a-version"), ("0.0.0", "0.0.1")),
        )
    ],
)
@across_implementations()
def test_project_versions(implementation: type[Project], tags: Iterable[str], expected: Iterable[str]):
    with project(implementation, INIT, *(GitTag(value=tag) for tag in tags)) as proj:
        assert tuple(proj.versions("HEAD")) == tuple((implementation.scheme.parse(version) for version in expected))


@across_implementations()
def test_project_versions_invalid_reference(implementation: type[Project]):
    with project(implementation) as proj:
        with pytest.raises(InvalidReference, match="HEAD"):
            deque(proj.versions("HEAD"), maxlen=0)


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        pytest.param(tags, version, id=f"{' | '.join(tags) or 'none'} -> {version or 'none'}")
        for tags, version in (
            ((), None),
            (("0.0.0",), "0.0.0"),
            (("not-a-version",), None),
            (("0.0.0", "not-a-version"), "0.0.0"),
            (("0.0.0", "0.0.1"), "0.0.1"),
            (("0.0.0", "0.0.1", "not-a-version"), "0.0.1"),
        )
    ],
)
@across_implementations()
def test_project_version(implementation: type[Project], tags: Iterable[str], expected: str | None):
    with patch.dict(os.environ, {}, clear=True):
        with project(implementation, INIT, *(GitTag(value=tag) for tag in tags)) as proj:
            if expected is None:
                with pytest.raises(NoVersion, match="HEAD"):
                    proj.version("HEAD")
            else:
                assert proj.version("HEAD") == implementation.scheme.parse(expected)


@across_implementations()
def test_project_version_in_release_mode(implementation: type[Project]):
    with patch.dict(os.environ, {"SIMPLE_GIT_VERSIONING_RELEASE": "1"}):
        with project(implementation, INIT) as proj:
            assert proj.version("HEAD") == implementation.scheme.parse("0.0.0")


@across_implementations()
def test_project_version_invalid_reference(implementation: type[Project]):
    with project(implementation) as proj:
        with pytest.raises(InvalidReference, match="HEAD"):
            proj.version("HEAD")


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        pytest.param(setup, expected, id=f"{', '.join(op.abbreviated() for op in setup)} -> {', '.join(expected)}")
        for setup, expected in (
            ((INIT,), ("HEAD",)),
            (
                (
                    INIT,
                    GitTag(value="left"),
                    GitCommand(command="checkout", arguments=("--orphan", "other")),
                    PATCH,
                    GitTag(value="right"),
                    GitMerge(
                        parents=("other", "main"),
                    ),
                ),
                ("left", "right"),
            ),
        )
    ],
)
@across_implementations()
def test_project_roots(implementation: type[Project], setup: Iterable[GitOperation], expected: Iterable[str]):
    with project(implementation, *setup) as proj:
        assert sorted(proj.canonical(root) for root in proj.roots("HEAD")) == sorted(
            proj.canonical(_expected) for _expected in expected
        )


@across_implementations()
def test_project_roots_invalid_reference(implementation: type[Project]):
    with project(implementation) as proj:
        with pytest.raises(InvalidReference, match="HEAD"):
            deque(proj.roots("HEAD"), maxlen=0)


@across_implementations()
def test_project_root(implementation: type[Project]):
    with project(implementation, INIT) as proj:
        assert proj.canonical(proj.root("HEAD")) == proj.canonical("HEAD")


@across_implementations()
def test_project_ambiguous_root(implementation: type[Project]):
    with project(
        implementation,
        INIT,
        GitTag(value="left"),
        GitCommand(command="checkout", arguments=("--orphan", "other")),
        PATCH,
        GitTag(value="right"),
        GitMerge(
            parents=(
                "other",
                "main",
            ),
        ),
    ) as proj:
        with pytest.raises(AmbiguousRoot) as excinfo:
            proj.root("HEAD")
        assert excinfo.value.reference == "HEAD"
        assert excinfo.value.candidates == frozenset((proj.canonical("left"), proj.canonical("right")))


@across_implementations()
def test_project_root_invalid_reference(implementation: type[Project]):
    with project(implementation) as proj:
        with pytest.raises(InvalidReference, match="HEAD"):
            proj.root("HEAD")


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        pytest.param(
            setup, expected, id=f"{', '.join(op.abbreviated() for op in setup)} -> {', '.join(expected) or 'empty'}"
        )
        for setup, expected in (
            ((INIT,), ()),
            ((INIT, GitTag(value="parent"), PATCH), ("parent",)),
            (
                (
                    INIT,
                    GitTag(value="left"),
                    GitCommand(command="checkout", arguments=("--orphan", "other")),
                    PATCH,
                    GitTag(value="right"),
                    GitMerge(
                        parents=("other", "main"),
                    ),
                ),
                ("left", "right"),
            ),
        )
    ],
)
@across_implementations()
def test_project_parents(implementation: type[Project], setup: Iterable[GitOperation], expected: Iterable[str]):
    with project(implementation, *setup) as proj:
        assert sorted(proj.canonical(parent) for parent in proj.parents("HEAD")) == sorted(
            proj.canonical(_expected) for _expected in expected
        )


@across_implementations()
def test_project_parents_invalid_reference(implementation: type[Project]):
    with project(implementation) as proj:
        with pytest.raises(InvalidReference, match="HEAD"):
            proj.parents("HEAD")


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        pytest.param(setup, expected, id=f"{', '.join(op.abbreviated() for op in setup)} -> {expected}")
        for setup, expected in (
            ((INIT, GitTag(value="0.0.0")), "0.0.0"),
            ((INIT, GitTag(value="0.0.0"), GitTag(value="0.0.1")), "0.0.1"),
            ((INIT, GitTag(value="0.0.1"), PATCH, GitTag(value="0.0.0")), "0.0.0"),
        )
    ],
)
@across_implementations()
def test_project_last(implementation: type[Project], setup: Iterable[GitOperation], expected: str):
    with project(implementation, *setup) as proj:
        actual = proj.last("HEAD")
        assert proj.canonical(actual) == proj.canonical(expected)


@across_implementations()
def test_project_last_no_version(implementation: type[Project]):
    with project(implementation, INIT) as proj:
        with pytest.raises(NoVersion, match="HEAD"):
            proj.last("HEAD")


@across_implementations()
def test_project_last_ambiguous_version(implementation: type[Project]):
    with project(
        implementation,
        INIT,
        GitTag(value="0.0.0"),
        GitCommand(command="checkout", arguments=("--orphan", "other")),
        PATCH,
        GitTag(value="0.0.1"),
        GitMerge(
            parents=("other", "main"),
        ),
    ) as proj:
        with pytest.raises(AmbiguousVersion) as excinfo:
            proj.last("HEAD")
        assert excinfo.value.reference == "HEAD"
        assert excinfo.value.candidates == frozenset(("0.0.0", "0.0.1"))


@pytest.mark.parametrize(
    ("trailers", "expected"),
    [
        pytest.param({}, {}, id="none"),
        pytest.param({"token": ""}, {"token": ""}, id="empty"),
        pytest.param({"token": "value"}, {"token": "value"}, id="basic"),
        pytest.param({"token": "multi\nline"}, {"token": "multi line"}, id="multi-line"),
    ],
)
@across_implementations()
def test_project_trailers(implementation: type[Project], trailers: dict[str, str], expected: dict[str, str]):
    with project(implementation, GitCommit(message="", trailers=trailers)) as proj:
        assert dict(proj.trailers("HEAD")) == expected


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        pytest.param((INIT,), (), id="none"),
        pytest.param((INIT, PATCH), ("HEAD",), id="one"),
        pytest.param((INIT, PATCH, PATCH), ("HEAD~", "HEAD"), id="linear"),
        pytest.param(
            (
                INIT,
                GitBranch(name="feature/one"),
                GitSwitch(branch="feature/one"),
                FEATURE,
                GitSwitch(branch="main"),
                PATCH,
                GitMerge(parents=("feature/one", "main")),
            ),
            ("feature/one", "main~", "main"),
            id="tree",
        ),
    ],
)
@across_implementations()
def test_project_revisions(implementation: type[Project], setup: Iterable[GitOperation], expected: Iterable[str]):
    with project(implementation, *setup) as proj:
        assert tuple(proj.revisions(proj.root("HEAD"))) == tuple(map(proj.canonical, expected))


@pytest.mark.parametrize(
    ("setup", "expected"),
    [
        pytest.param(setup, expected, id=f"{', '.join(op.abbreviated() for op in setup)} -> {expected}")
        for setup, expected in (
            ((INIT,), "0.0.0"),
            ((INIT, PATCH), "0.0.1"),
            ((INIT, FEATURE), "0.1.0"),
            ((INIT, BREAKING_CHANGE), "1.0.0"),
            ((INIT, GitCommit(trailers={"Reviewed-By": "john.smith@example.com"})), "0.0.1"),
            ((INIT, Release()), "0.0.0"),
            ((INIT, Release(), PATCH), "0.0.1"),
            ((INIT, Release(), FEATURE), "0.1.0"),
            ((INIT, Release(), BREAKING_CHANGE), "1.0.0"),
            ((INIT, Release(), GitCommit(trailers={"Reviewed-By": "john.smith@example.com"})), "0.0.1"),
        )
    ],
)
@across_implementations()
def test_project_release(implementation: type[Project], setup: Iterable[GitOperation], expected: str):
    with project(implementation, *setup) as proj:
        assert str(proj.release("HEAD")) == expected


@across_implementations()
def test_project_release_invalid_bump(implementation: type[Project]):
    with project(implementation, INIT, GitCommit(bump="invalid")) as proj:
        with pytest.raises(InvalidVersionBumpTrailer) as excinfo:
            proj.release("HEAD")
        assert excinfo.value.bump == "invalid"
