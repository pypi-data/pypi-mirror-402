# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
from abc import abstractmethod
from collections import deque
from collections.abc import Iterable, Iterator
from contextlib import suppress
from functools import cached_property
from pathlib import Path
from typing import Protocol, TypeVar
from unittest.mock import patch

try:
    from typing import Self
except ImportError:  # python<3.11
    from typing_extensions import Self

from icontract import require
from sh import Command, ErrorReturnCode_128, ErrorReturnCode_129
from sh.contrib import git

from .version import InvalidVersion, Version, VersionBump


class NotAGitWorkTree(RuntimeError):
    """
    Raised when an operation requires a git worktree but there is none
    """

    def __init__(self, path: Path, *args, **kwargs):
        super().__init__(path, *args, **kwargs)

    @property
    def path(self) -> str:
        return self.args[0]


class NoVersion(RuntimeError):
    """
    Raised when no version can be found for a project at a given reference
    """

    def __init__(self, project: Project, reference: str, *args, **kwargs):
        super().__init__(project, reference, *args, **kwargs)

    @property
    def project(self) -> Project:
        return self.args[0]

    @property
    def reference(self) -> str:
        return self.args[1]


class AmbiguousReference(RuntimeError):
    """
    Raised when an operation fails due to an ambiguity in the history
    """

    def __init__(self, reference: str, candidates: Iterable[str], *args, **kwargs):
        super().__init__(reference, frozenset(candidates), *args, **kwargs)
        assert len(self.candidates) > 1

    @cached_property
    def reference(self) -> frozenset[str]:
        return self.args[0]

    @cached_property
    def candidates(self) -> frozenset[str]:
        return frozenset(self.args[1])


class AmbiguousRoot(AmbiguousReference):
    """
    Raised when a single root commit cannot be computed due to an ambiguity in the history
    """


class AmbiguousVersion(AmbiguousReference):
    """
    Raised when a version cannot be computed due to an ambiguity in the history
    """


class InvalidReference(ValueError):
    """
    Raised when an operation incurs a lookup on an invalid reference
    """

    def __init__(self, reference: str, *args, **kwargs):
        super().__init__(reference, *args, **kwargs)

    @property
    def reference(self) -> str:
        return self.args[0]


def _is_inside_git_work_tree() -> bool:
    """
    Return `True` if the current directory is inside a git work tree, `False` otherwise
    """
    try:
        return git("rev-parse", "--is-inside-work-tree").rstrip() == "true"
    except ErrorReturnCode_128:
        return False


class InvalidVersionBumpTrailer(ValueError):
    """
    Raised when an invalid version bump is specified as a git trailer
    """

    def __init__(self, bump: str, *args, **kwargs):
        super().__init__(bump, *args, **kwargs)

    @property
    def bump(self) -> str:
        return self.args[0]


V = TypeVar("V", bound=Version)


class Project(Protocol[V]):
    path: Path
    scheme: type[V]
    _pushed: list[str]

    def __init__(self, *args, path: Path, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path.resolve()
        self._pushed = []

    def __enter__(self) -> Self:
        self._pushed.append(os.getcwd())
        os.chdir(self.path)
        if not _is_inside_git_work_tree():
            os.chdir(self._pushed.pop())
            raise NotAGitWorkTree(path=self.path)
        return self

    def __exit__(self, *args, **kwargs) -> bool | None:
        os.chdir(self._pushed.pop())

    @property
    @require(lambda self: Path.cwd().resolve() == self.path.resolve())
    def _git(self) -> Command:
        return git

    def canonical(self, reference: str) -> str:
        try:
            return self._git("rev-list", "--max-count=1", reference, "--").rstrip()
        except ErrorReturnCode_128 as exc:
            raise InvalidReference(reference) from exc

    def _tags(self, reference: str) -> Iterator[str]:
        try:
            yield from self._git.tag("--points-at", reference, "--").rstrip().split("\n")
        except ErrorReturnCode_129 as exc:
            if b"malformed object name" in exc.stderr:
                raise InvalidReference(reference) from exc

    def versions(self, reference: str) -> Iterator[V]:
        for tag in self._tags(reference):
            with suppress(InvalidVersion):
                yield self.scheme.parse(tag)

    def version(self, reference: str = "HEAD") -> V:
        try:
            return max(self.versions(reference))
        except InvalidReference:
            raise
        except ValueError as exc:
            if os.environ.get("SIMPLE_GIT_VERSIONING_RELEASE", "").lower() not in ("", "0", "false"):
                with patch.dict(os.environ, {"SIMPLE_GIT_VERSIONING_RELEASE": ""}):
                    return self.release()
            raise NoVersion(self, reference) from exc

    def roots(self, reference: str) -> Iterator[str]:
        try:
            yield from self._git("rev-list", "--max-parents=0", reference, "--").rstrip().split("\n")
        except ErrorReturnCode_128 as exc:
            if b"bad revision" in exc.stderr:
                raise InvalidReference(reference) from exc

    def root(self, reference: str) -> str:
        try:
            roots = frozenset(self.roots(reference))
        except InvalidReference:
            raise
        assert roots, "every commit has at least one root"

        if len(roots) > 1:
            raise AmbiguousRoot(reference, roots)
        return next(iter(roots))

    def parents(self, reference: str) -> list[str]:
        try:
            return self._git("rev-list", "--max-count=1", "--parents", reference, "--").rstrip().split(" ")[1:]
        except ErrorReturnCode_128 as exc:
            if b"bad revision" in exc.stderr:
                raise InvalidReference(reference) from exc

    def last(self, reference: str = "HEAD") -> V:
        refs = deque((reference,))
        candidates = set()
        while refs:
            ref = refs.popleft()

            try:
                candidates.add(self.version(ref))
            except NoVersion:
                refs.extend(self.parents(ref))

        if not candidates:
            raise NoVersion(self, reference)
        if len(candidates) > 1:
            raise AmbiguousVersion(reference, map(str, candidates))

        return next(iter(candidates))

    def trailers(self, commit: str, *args: str) -> Iterator[tuple[str, str]]:
        trailers = self._git(
            "interpret-trailers",
            "--no-divider",
            "--unfold",
            "--only-trailers",
            *args,
            _in=self._git.show("--format=format:%B", "--no-patch", commit, _piped=True),
        ).rstrip()
        if not trailers:
            return

        for trailer in trailers.split("\n"):
            key, value = trailer.split(":", maxsplit=1)
            yield key.strip(), value.strip()

    def revisions(self, start: str, end: str = "HEAD") -> Iterator[str]:
        yield from (line for line in self._git("rev-list", "--reverse", f"{start}..{end}").rstrip().split("\n") if line)

    @abstractmethod
    def release(self, reference: str = "HEAD") -> V:
        try:
            version = self.last(reference)
        except NoVersion:
            version = self.scheme()
            root = self.root(reference)
        else:
            root = str(version)

        for commit in self.revisions(root, reference):
            for token, value in self.trailers(
                commit, "--if-missing", "add", "--if-exists", "doNothing", "--trailer", "Version-Bump: patch"
            ):
                if token.casefold() != "version-bump":
                    continue

                try:
                    bump = VersionBump(value)
                except ValueError:
                    raise InvalidVersionBumpTrailer(value)

                version = version.bump(bump)

        return version
