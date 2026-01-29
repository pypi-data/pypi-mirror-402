# SPDX-License-Identifier: MIT

import os
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture(autouse=True)
def testdir() -> Iterator[Path]:
    with TemporaryDirectory() as testdir:
        os.chdir(testdir)
        yield Path(testdir)
