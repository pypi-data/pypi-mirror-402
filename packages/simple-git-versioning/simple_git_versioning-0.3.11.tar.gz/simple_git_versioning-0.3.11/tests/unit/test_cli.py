# SPDX-License-Identifier: MIT

# from pathlib import Path
# from typing import Iterator
# from unittest.mock import patch
#
# import pytest
# from sh import Command, python
#
# from versioning import version
#
#
# @pytest.fixture
# def cli() -> Iterator[Command]:
#     with patch.dict("os.environ", {"PYTHONPATH": str(Path(__file__).parent.parent)}):
#         yield python.bake("-m", "versioning")
#
#
# def test_cli(cli):
#     assert cli().strip() == str(version())
#
#
# def test_cli_help(cli):
#     assert cli("--help").startswith("usage:")
#
#
# def test_cli_project_path(cli):
#     assert cli(Path(__file__).parent).strip() == str(version())
