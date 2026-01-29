# SPDX-License-Identifier: MIT

from __future__ import annotations

import logging
import re
from argparse import ArgumentParser
from contextlib import suppress
from dataclasses import dataclass, replace
from enum import Enum
from functools import partial, total_ordering, wraps
from os import EX_DATAERR, EX_NOINPUT, EX_SOFTWARE, EX_USAGE
from pathlib import Path
from sys import stdout, version_info
from typing import Any, ClassVar, Iterator, Protocol

try:
    from typing import Self
except ImportError:  # python<3.11
    from typing_extensions import Self

from .project import (
    AmbiguousRoot,
    AmbiguousVersion,
    InvalidReference,
    InvalidVersionBumpTrailer,
    NotAGitWorkTree,
)
from .project import NoVersion as NoVersion
from .project import Project as _Project
from .version import InvalidVersion as _InvalidVersion
from .version import Version as _Version
from .version import VersionBump

LOGGER = logging.getLogger(__name__)

if version_info >= (3, 11):
    dataclass = partial(dataclass, kw_only=True)


class IllegalRelease(ValueError):
    """
    Raised when an operation results in making an illegal release
    """


class InvalidVersion(_InvalidVersion):
    """
    Raised when an operation results in an invalid PEP440 version
    """


@total_ordering
class PreReleaseLabel(Enum):
    """
    Enumeration of valid PEP440 pre-release labels
    """

    A = "a"
    ALPHA = A
    B = "b"
    BETA = B
    RC = "rc"
    C = RC
    PRE = RC
    PREVIEW = RC

    def __str__(self) -> str:
        if self is PreReleaseLabel.A or self is PreReleaseLabel.ALPHA:
            return "alpha"
        if self is PreReleaseLabel.B or self is PreReleaseLabel.BETA:
            return "beta"
        if (
            self is PreReleaseLabel.C
            or self is PreReleaseLabel.RC
            or self is PreReleaseLabel.PRE
            or self is PreReleaseLabel.PREVIEW
        ):
            return "release candidate"
        raise RuntimeError(f"Unexpected pre-release label: {self}")

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, PreReleaseLabel):
            return NotImplemented
        return self.value.__lt__(other.value)


@dataclass(order=True, frozen=True)
class PreRelease:
    """
    PEP440 pre-release: label + revision
    """

    label: PreReleaseLabel
    revision: int


class _Version(_Version, Protocol):
    """
    PEP440 version protocol
    """

    epoch: int = 0
    release: tuple[int, ...]
    dev: int | None = None
    pre: PreRelease | None = None
    post: int | None = None
    local: tuple[int | str, ...] = ()

    def __str__(self) -> str:
        return f"{f'{self.epoch}!' if self.epoch else ''}{'.'.join(map(str, self.release))}{f'{self.pre.label.value}{self.pre.revision}' if self.pre else ''}{f'.post{self.post}' if self.post is not None else ''}{f'.dev{self.dev}' if self.dev is not None else ''}{'+' + '.'.join(map(str, self.local)) if self.local else ''}"

    def is_prerelease(self) -> bool:
        return self.pre is not None or self.dev is not None

    @property
    def major(self) -> int:
        return self.release[0]

    @property
    def minor(self) -> int:
        try:
            return self.release[1]
        except IndexError:
            return 0

    @property
    def patch(self) -> int:
        try:
            return self.release[2]
        except IndexError:
            return 0


def _segment(identifier: str) -> Iterator[int | str]:
    if not identifier:
        return iter(())

    for segment in identifier.replace("-", ".").replace("_", ".").split("."):
        try:
            yield int(segment)
        except ValueError:
            yield segment


@total_ordering
@dataclass(frozen=True)
class Version(_Version):
    """
    PEP440 version
    """

    epoch: int = 0
    release: tuple[int, ...] = (0, 0, 0)
    pre: PreRelease | None = None
    post: int | None = None
    dev: int | None = None
    local: tuple[str | int, ...] = ()

    _VERSION_PATTERN: ClassVar[
        str
    ] = r"""
        v?
        (?:(?P<epoch>[0-9]+)!)?                           # epoch
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<post>                                         # post release
            (?:-(?P<post_n1>[0-9]+))
            |
            (?:
                [-_\.]?
                (?P<post_l>post|rev|r)
                [-_\.]?
                (?P<post_n2>[0-9]+)?
            )
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
        (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?  # local version
    """

    _VERSION_REGEX: ClassVar[re.Pattern] = re.compile(f"^{_VERSION_PATTERN}$", re.VERBOSE | re.IGNORECASE)

    def __post_init__(self) -> None:
        assert self.release

    @classmethod
    def parse(cls, version: str) -> Self:
        if (match := cls._VERSION_REGEX.match(version)) is None:
            raise InvalidVersion(version)

        epoch = int(match.group("epoch") or "0")
        release = tuple(map(int, match.group("release").split(".")))

        if match.group("pre"):
            label = PreReleaseLabel[match.group("pre_l").upper()]
            revision = int(match.group("pre_n"))
            pre = PreRelease(label=label, revision=revision)
        else:
            pre = None

        if match.group("post"):
            post = int(match.group("post_n1") or "0") if match.group("post_n1") else int(match.group("post_n2"))
        else:
            post = None

        dev = int(match.group("dev_n") or "0") if match.group("dev") else None
        local = tuple(_segment(match.group("local") or ""))

        return cls(epoch=epoch, release=release, pre=pre, post=post, dev=dev, local=local)

    def bump(self, bump: VersionBump) -> Self:
        if bump is VersionBump.MAJOR:
            return replace(self, release=(self.major + 1, 0, 0), pre=None, post=None, dev=None, local=())
        if bump is VersionBump.MINOR:
            return replace(self, release=(self.major, self.minor + 1, 0), pre=None, post=None, dev=None, local=())
        if bump is VersionBump.PATCH:
            return replace(
                self, release=(self.major, self.minor, self.patch + 1), pre=None, post=None, dev=None, local=()
            )

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Version):
            return NotImplemented

        if self.epoch < other.epoch:
            return True
        if self.epoch > other.epoch:
            return False
        if self.release < other.release:
            return True
        if self.release > other.release:
            return False

        if self.pre and other.pre:
            if self.pre < other.pre:
                return True
            if self.pre > other.pre:
                return False
        elif self.pre:
            return True
        elif other.pre:
            return False

        if self.post is not None and other.post is not None:
            if self.post < other.post:
                return True
            if self.post > other.post:
                return False
        elif self.post is not None:
            return False
        elif other.post is not None:
            return True

        if self.dev is not None and other.dev is not None:
            if self.dev < other.dev:
                return True
            if self.dev > other.dev:
                return False
        elif self.dev is not None:
            return True
        elif other.dev is not None:
            return False

        for left, right in zip(self.local, other.local):
            if left == right:
                continue

            with suppress(TypeError):
                return left < right
            return isinstance(left, str)
        return len(self.local) < len(other.local)


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
        alpha: bool = False,
        beta: bool = False,
        rc: bool = False,
        release: bool = False,
        post: bool = False,
        dev: int | None = None,
        local: tuple[int | str, ...] = (),
    ) -> Version:
        if sum((alpha, beta, rc, release, post)) > 1:
            raise ValueError("At most one of 'alpha', 'beta', 'rc', 'release', or 'post' may be set to True")

        reference = self.canonical(reference)

        try:
            version = self.last(reference)
        except NoVersion:
            if post:
                raise IllegalRelease("Cannot make a post release without first making a release")
            version = self.scheme()
            root = self.root(reference)
        else:
            if version.dev is not None:
                raise IllegalRelease(
                    f"Dev releases are not meant to be published: {self.canonical(str(version))} was released as"
                    f" {version}"
                )
            root = str(version)

        if post:
            if version.pre:
                raise IllegalRelease("Cannot make a post release without first making a release")
            if version.post is None:
                version = replace(version, post=0)

        if version.post is not None:
            version = replace(version, post=version.post + sum(1 for _ in self.revisions(root, reference)))
        elif version.pre:
            version = replace(
                version,
                pre=replace(
                    version.pre, revision=version.pre.revision + sum(1 for _ in self.revisions(root, reference))
                ),
            )
        else:
            version = super().release(reference=reference)

        if alpha or beta or rc:
            label = PreReleaseLabel.ALPHA if alpha else PreReleaseLabel.BETA if beta else PreReleaseLabel.RC
            if not version.pre or version.pre.label != label:
                version = replace(version, pre=PreRelease(label=label, revision=0))
        elif release:
            version = replace(version, pre=None)

        version = replace(version, dev=dev)
        version = replace(version, local=local)

        try:
            canonical = self.canonical(str(version))
        except InvalidReference:
            pass
        else:
            if canonical != reference:
                raise IllegalRelease(
                    f"Computed release is: {version} but there is already a release for {version} at {canonical}"
                )

        return version


@wraps(print)
def _error(*args, **kwargs):
    return print(*args, **kwargs, file=stdout)


def _local(local: str) -> tuple[int | str, ...]:
    if not local:
        return ()
    return Version.parse(f"0.0.0+{local}").local


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

    ## -a, --alpha
    release_kind_group.add_argument(
        "-a",
        "--alpha",
        action="store_true",
        help="make the version an alpha release",
    )

    ## -b, --beta
    release_kind_group.add_argument(
        "-b",
        "--beta",
        action="store_true",
        help="make the version a beta release",
    )

    ## -c, --rc, --pre, --preview
    release_kind_group.add_argument(
        "-c",
        "--rc",
        "--pre",
        "--preview",
        action="store_true",
        help="make the version a release candidate",
    )

    ## --release
    release_kind_group.add_argument(
        "--release",
        action="store_true",
        help="make the version a regular release",
    )

    ## --post
    release_kind_group.add_argument(
        "--post",
        action="store_true",
        help="make the version a post release",
    )

    # --dev
    parser.add_argument(
        "--dev",
        nargs="?",
        const=0,
        type=int,
        default=None,
        help="make the version a dev release",
    )

    # --local
    parser.add_argument("--local", type=_local, default=(), help="a local identifier to append to the version")

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
                alpha=args.alpha,
                beta=args.beta,
                rc=args.rc,
                release=args.release,
                post=args.post,
                dev=args.dev,
                local=args.local,
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
    except AmbiguousRoot as exc:
        _error(f"ambiguous root for {exc.reference}, candidates: {exc.candidates}")
        exit(EX_DATAERR)
    except AmbiguousVersion as exc:
        _error(f"unable to decide which version to release from: {exc.candidates}")
        exit(EX_DATAERR)
    except IllegalRelease as exc:
        _error(exc)
        exit(EX_DATAERR)
    except:  # noqa: E722
        LOGGER.exception(
            "Unexpected error. Please report it here: https://gitlab.com/ypsah/simple-git-versioning/-/issues"
        )
        exit(EX_SOFTWARE)

    print(version)

    exit(0)


if __name__ == "__main__":
    main()
