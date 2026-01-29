# SPDX-License-Identifier: MIT

from abc import abstractmethod
from enum import Enum
from typing import Protocol

try:
    from typing import Self
except ImportError:  # python<3.11
    from typing_extensions import Self


class InvalidVersion(ValueError):
    """
    Raised when an operation results in an invalid version
    """

    def __init__(self, version: str, *args, **kwargs):
        super().__init__(version, *args, **kwargs)

    @property
    def version(self) -> str:
        return self.args[0]


class VersionBump(Enum):
    """
    Kind of version bump
    """

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class Version(Protocol):
    """
    Generic version interface
    """

    @abstractmethod
    def __str__(self) -> str:
        ...

    @abstractmethod
    def __lt__(self) -> str:
        ...

    @abstractmethod
    def is_prerelease(self) -> bool:
        """
        Return `True` when the version is a pre-release, `False` otherwise
        """
        ...

    @classmethod
    @abstractmethod
    def parse(cls, version: str) -> Self:
        """
        Parse a version from a string
        """
        ...

    @abstractmethod
    def bump(self, bump: VersionBump) -> Self:
        """
        Return the version bumped by `bump`
        """
        ...
