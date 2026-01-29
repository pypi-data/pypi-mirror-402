# SPDX-License-Identifier: MIT

from __future__ import annotations

import string
from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import InitVar, dataclass, field, replace
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterator, Literal, Protocol, TypeVar

from hypothesis.strategies import composite, none, one_of, sampled_from, text
from sh import pushd
from sh.contrib import git

from versioning.project import Project
from versioning.version import InvalidVersion, Version, VersionBump


class GitOperation(Protocol):
    @abstractmethod
    def __call__(self, *args, **kwargs) -> None: ...

    @abstractmethod
    def abbreviated(self) -> str: ...


def _format_commit_message(message: str) -> str:
    return "\n".join(map(str.strip, message.strip().split("\n")))


_DEFAULT_COMMIT_TITLE = "lorem ipsum dolor sit amet"
_DEFAULT_COMMIT_MESSAGE = _format_commit_message(
    """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
    tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
    veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
    commodo consequat. Duis aute irure dolor in reprehenderit in voluptate
    velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint
    occaecat cupidatat non proident, sunt in culpa qui officia deserunt
    mollit anim id est laborum.
    """
)


@dataclass(frozen=True, kw_only=True)
class GitCommit(GitOperation):
    title: str = field(default=_DEFAULT_COMMIT_TITLE)
    message: str = field(default=_DEFAULT_COMMIT_MESSAGE)
    trailers: dict[str, str] = field(default_factory=dict)
    bump: InitVar[None | Literal["patch"] | Literal["minor"] | Literal["major"]] = None

    def __post_init__(self, bump: None | Literal["patch"] | Literal["minor"] | Literal["major"]):
        object.__setattr__(self, "message", _format_commit_message(self.message))
        if bump is not None:
            self.trailers["Version-Bump"] = bump

    def __str__(self) -> str:
        def parts() -> Iterator[str]:
            yield self.title
            if self.message:
                yield self.message
            if self.trailers:
                yield "\n".join(
                    (": ".join((key, value.strip().replace("\n", "\n\t"))) for key, value in self.trailers.items())
                )

        return "\n\n".join(parts())

    def __call__(self, *args, **kwargs) -> None:
        git.commit("--allow-empty", "--message", str(self))

    def abbreviated(self) -> str:
        return f"C[{self.trailers.get('bump', 'patch')}]"


INIT = GitCommit(title="initial empty commit", message="")
PATCH = GitCommit(bump="patch")
FEATURE = GitCommit(bump="minor")
BREAKING_CHANGE = GitCommit(bump="major")


@composite
def git_commits(draw) -> GitCommit:
    message = draw(
        text(alphabet=string.ascii_letters + " ", min_size=1).filter(lambda x: len(set(x)) != 1 or x[0] != " ")
    )
    return GitCommit(
        message=message,
        bump=draw(one_of(sampled_from(("patch", "minor", "major")), none())),
    )


@dataclass(frozen=True, kw_only=True)
class GitTag(GitOperation):
    value: str
    message: str = ""

    def __call__(self, *args, **kwargs) -> None:
        git.tag("--annotate", "--message", self.message, self.value)

    def abbreviated(self) -> str:
        return f"T[{self.value}]"


@composite
def git_tags(draw) -> GitTag:
    return GitTag(
        value=draw(text(min_size=1)),
        message=draw(text(min_size=1)),
    )


class GitVersion(GitTag):
    def __init__(self, version: Version, *args, **kwargs):
        super().__init__(value=str(version), message=f"Version {version}", *args, **kwargs)
        self.version = version


@composite
def git_versions(draw, versions) -> GitVersion:
    return GitVersion(version=draw(versions))


@dataclass(frozen=True, kw_only=True)
class GitBranch(GitOperation):
    name: str

    def __call__(self, *args, **kwargs) -> None:
        git.branch(self.name)

    def abbreviated(self) -> str:
        return f"B[{self.name}]"


@dataclass(frozen=True, kw_only=True)
class GitSwitch(GitOperation):
    branch: str

    def __call__(self, *args, **kwargs) -> None:
        git.switch(self.branch)

    def abbreviated(self) -> str:
        return f"S[{self.branch}]"


@dataclass(frozen=True, kw_only=True)
class GitMerge(GitOperation):
    parents: tuple[str, ...]

    def __call__(self, *args, **kwargs) -> None:
        git.merge("--allow-unrelated-histories", *self.parents)

    def abbreviated(self) -> str:
        return f"M[{', '.join(self.parents)}]"


@dataclass(frozen=True, kw_only=True)
class GitCommand(GitOperation):
    command: str
    arguments: tuple[str, ...] = ()

    def __call__(self, *args, **kwargs) -> None:
        git(self.command, *self.arguments)

    def abbreviated(self) -> str:
        return f"{self.command.upper()}[{' '.join(self.arguments)}]"


@dataclass
class Release(GitOperation):
    options: dict[str, Any] = field(default_factory=dict)

    def __call__(self, *args, project: Project, **kwargs) -> None:
        version = project.release("HEAD", **self.options)
        GitVersion(version=version)()

    def abbreviated(self) -> str:
        return f"R[{''.join(f'{key}={value}' for key, value in self.options.items())}]"


@dataclass(order=True, frozen=True, kw_only=True)
class DummyVersion(Version):
    major: int = 0
    minor: int = 0
    patch: int = 0

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_prerelease(self) -> bool:
        return False

    def matches(self, other: DummyVersion) -> bool:
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    @classmethod
    def parse(cls, version: str) -> DummyVersion:
        try:
            major, minor, patch = map(int, version.split("."))
        except ValueError:
            raise InvalidVersion(version)

        return cls(major=major, minor=minor, patch=patch)

    def bump(self, bump: VersionBump) -> DummyVersion:
        if bump is VersionBump.MAJOR:
            return replace(self, major=self.major + 1, minor=0, patch=0)
        if bump is VersionBump.MINOR:
            return replace(self, minor=self.minor + 1, patch=0)
        if bump is VersionBump.PATCH:
            return replace(self, patch=self.patch + 1)


class DummyProject(Project[DummyVersion]):
    scheme = DummyVersion

    def release(self, reference: str = "HEAD") -> DummyVersion:
        return super().release(reference)


def gitdir(directory: Path) -> Path:
    with pushd(directory):
        git.init()
        git.config("user.name", "Jane Doe")
        git.config("user.email", "jane.doe@example.com")
        git.branch("--move", "--force", "main")

    return directory


P_co = TypeVar("P_co", bound=Project, covariant=True)


class ProjectFactory(Protocol[P_co]):
    def __call__(self, *, path: Path) -> P_co: ...


@contextmanager
def project(project_factory: ProjectFactory[P_co], *operations: GitOperation) -> Iterator[P_co]:
    with TemporaryDirectory() as tmpdir:
        gitdir(Path(tmpdir))
        with project_factory(path=Path(tmpdir)) as proj:
            for operation in operations:
                operation(project=proj)
            yield proj
