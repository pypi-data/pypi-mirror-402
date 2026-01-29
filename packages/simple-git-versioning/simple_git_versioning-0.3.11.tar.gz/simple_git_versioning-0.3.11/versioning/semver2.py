# SPDX-License-Identifier: MIT

from __future__ import annotations

import logging
import re
from argparse import ArgumentParser
from collections.abc import Iterator
from contextlib import suppress
from dataclasses import dataclass, field, replace
from functools import partial, total_ordering, wraps
from os import EX_DATAERR, EX_NOINPUT, EX_SOFTWARE, EX_USAGE
from pathlib import Path
from platform import python_version_tuple
from sys import stdout, version_info
from typing import Any, ClassVar, Protocol

try:
    from typing import Self
except ImportError:  # python<3.11
    from typing_extensions import Self

from .project import (
    InvalidReference,
    InvalidVersionBumpTrailer,
    NotAGitWorkTree,
    NoVersion,
)
from .project import Project as _Project
from .version import InvalidVersion as _InvalidVersion
from .version import Version as _Version
from .version import VersionBump

LOGGER = logging.getLogger(__name__)

if tuple(map(int, python_version_tuple())) >= (3, 11):
    dataclass = partial(dataclass, kw_only=True)


class InvalidVersion(_InvalidVersion):
    """
    Raised when an operation results in an invalid PEP440 version
    """


class _Version(_Version, Protocol):
    """
    SemVer2 version protocol
    """

    major: int
    minor: int
    patch: int
    pre: tuple[str | int, ...] = ()
    build: str = ""

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}{'-' + '.'.join(map(str, self.pre)) if self.pre else ''}{f'+{self.build}' if self.build else ''}"

    def is_prerelease(self) -> bool:
        return bool(self.pre)


def _identifierize(identifiers: str) -> Iterator[str | int]:
    if not identifiers:
        return iter(())

    for identifier in identifiers.split("."):
        try:
            yield int(identifier)
        except ValueError:
            yield identifier


@total_ordering
@dataclass(frozen=True)
class Version(_Version):
    """
    SemVer2 version
    """

    major: int = 0
    minor: int = 0
    patch: int = 0
    pre: tuple[str | int, ...] = ()
    build: str = field(default="", compare=False)

    _VERSION_PATTERN: ClassVar[str] = r"""
        v?
        (?P<major>0|[1-9]\d*)
        \.
        (?P<minor>0|[1-9]\d*)
        \.
        (?P<patch>0|[1-9]\d*)
        (?:
            -(?P<prerelease>
                (?:
                    0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*
                )
                (?:
                    \.(?:
                        0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*
                      )
                )*
             )
        )?
        (?:
            \+(?P<buildmetadata>
                [0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*
              )
        )?
    """

    _VERSION_REGEX: ClassVar[re.Pattern] = re.compile(f"^{_VERSION_PATTERN}$", re.VERBOSE | re.IGNORECASE)

    @classmethod
    def parse(cls, version: str) -> Self:
        if (match := cls._VERSION_REGEX.match(version)) is None:
            raise InvalidVersion(version)

        return cls(
            major=int(match.group("major") or "0"),
            minor=int(match.group("minor") or "0"),
            patch=int(match.group("patch") or "0"),
            pre=tuple(_identifierize(match.group("prerelease") or "")),
            build=match.group("buildmetadata") or "",
        )

    def bump(self, bump: VersionBump) -> Self:
        if bump is VersionBump.MAJOR:
            return replace(self, major=self.major + 1, minor=0, patch=0, pre=(), build="")
        if bump is VersionBump.MINOR:
            return replace(self, minor=self.minor + 1, patch=0, pre=(), build="")
        if VersionBump.PATCH:
            return replace(self, patch=self.patch + 1, pre=(), build="")

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented

        if self.major < other.major:
            return True
        if self.major > other.major:
            return False
        if self.minor < other.minor:
            return True
        if self.minor > other.minor:
            return False
        if self.patch < other.patch:
            return True
        if self.patch > other.patch:
            return False

        if self.pre and not other.pre:
            return True
        if not self.pre:
            return False

        for left, right in zip(self.pre, other.pre):
            if left == right:
                continue

            with suppress(TypeError):
                return left < right
            return isinstance(left, int)
        return len(self.pre) < len(other.pre)


class Project(_Project[Version]):
    scheme = Version

    if version_info < (3, 11):

        def __init__(self, *args, path: Path, **kwargs):
            super().__init__(*args, **kwargs)
            self.path = path
            self._pushed = []

    def release(
        self,
        reference: str = "HEAD",
        *,
        pre: tuple[str | int, ...] = (),
        release: bool = False,
        build: str = "",
    ) -> Version:
        if pre and release:
            raise ValueError("At most one one of 'pre' or 'release' may be set")

        try:
            version = self.last(reference)
        except NoVersion:
            version = self.scheme()
            root = self.root(reference)
        else:
            root = str(version)

        if version.pre:
            if not isinstance(version.pre[-1], int):
                version = replace(version, pre=version.pre + (0,))
            assert isinstance(version.pre[-1], int)  # typeguard for type checkers

            version = replace(
                version, pre=version.pre[:-1] + (version.pre[-1] + sum(1 for _ in self.revisions(root, reference)),)
            )
        else:
            version = super().release(reference=reference)

        if pre:
            if not version.pre or version.pre[:-1] != pre:
                version = replace(version, pre=pre + (0,))
        elif release:
            version = replace(version, pre=())

        version = replace(version, build=build)
        return version


@wraps(print)
def _error(*args, **kwargs):
    return print(*args, **kwargs, file=stdout)


def _pre_release(pre: str) -> tuple[str | int, ...]:
    if not pre:
        return ()
    return Version.parse(f"0.0.0-{pre}").pre


def _build_metadata(build: str) -> str:
    if not build:
        return ""
    return Version.parse(f"0.0.0+{build}").build


def main() -> None:  # pragma: no cover
    parser = ArgumentParser(description="Compute the version of a project based on git's tags and trailers")

    # -q, --quiet / -v, --verbose
    parser.add_argument(
        "-q", "--quiet", action="count", default=0, help="decrease verbosity (can be specified multiple times)"
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="increase verbosity (can be specified multiple times)"
    )

    # Release kind
    release_kind_group = parser.add_mutually_exclusive_group()

    ## --pre
    release_kind_group.add_argument(
        "--pre",
        metavar="PREFIX",
        type=_pre_release,
        help="make the version a pre release, using the provided pre-release PREFIX",
    )

    ## --release
    release_kind_group.add_argument(
        "--release",
        action="store_true",
        help="make the version a regular release",
    )

    # --build
    parser.add_argument("--build", type=_build_metadata, help="build metadata to append to the version")

    # path
    parser.add_argument(
        "path",
        metavar="PROJECT",
        nargs="?",
        type=Path,
        default=".",
        help="path to the project whose version to compute (defaults to the current directory)",
    )

    # reference
    parser.add_argument(
        "reference",
        metavar="REF",
        default="HEAD",
        nargs="?",
        help="git ref in the project whose version to compute (defaults to %(default)s)",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING + (args.quiet - args.verbose) * 10)
    LOGGER.debug(args)

    try:
        with Project(path=args.path) as project:
            version = project.release(
                reference=args.reference,
                pre=args.pre,
                release=args.release,
                build=args.build,
            )
    except FileNotFoundError as exc:
        _error(exc)
        exit(EX_NOINPUT)
    except NotAGitWorkTree as exc:
        _error(f"Not a git work tree: {exc.path}")
        exit(EX_USAGE)
    except NoVersion as exc:
        _error(exc)
        exit(EX_DATAERR)
    except InvalidReference as exc:
        if exc.reference == "HEAD":
            _error("Repository does not contain any commit")
        else:
            _error(f"Invalid reference: {exc.reference}")
        exit(EX_DATAERR)
    except InvalidVersionBumpTrailer as exc:
        _error(f"Unexpected value for Version-Bump trailer: '{exc.bump}', expected one of 'patch', 'minor', or 'major'")
        exit(EX_DATAERR)
    except:  # noqa: E722
        LOGGER.exception(
            "unexpected error, please report it there: https://gitlab.com/ypsah/simple-git-versioning/-/issues"
        )
        exit(EX_SOFTWARE)

    print(version)

    exit(0)


if __name__ == "__main__":
    main()
