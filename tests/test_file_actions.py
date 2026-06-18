"""file_actions: per-OS open/reveal command construction + guards."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest

from shobdohotao.domain import ErrorCode, ProcessingError
from shobdohotao.platform import file_actions

# Use explicit path flavors so these tests assert OS-correct strings regardless
# of the host running the suite.


def test_reveal_windows_selects_file() -> None:
    cmd = file_actions.build_reveal_command(PureWindowsPath(r"C:\lib\song.mp3"), "win32")
    assert cmd[0] == "explorer"
    assert cmd[1] == r"/select,C:\lib\song.mp3"


def test_reveal_macos() -> None:
    cmd = file_actions.build_reveal_command(PurePosixPath("/lib/song.mp3"), "darwin")
    assert cmd == ["open", "-R", "/lib/song.mp3"]


def test_reveal_linux_opens_parent() -> None:
    cmd = file_actions.build_reveal_command(PurePosixPath("/lib/song.mp3"), "linux")
    assert cmd == ["xdg-open", "/lib"]


def test_open_directory_per_os() -> None:
    assert file_actions.build_open_directory_command(
        PureWindowsPath(r"C:\lib"), "win32") == ["explorer", r"C:\lib"]
    assert file_actions.build_open_directory_command(
        PurePosixPath("/lib"), "darwin") == ["open", "/lib"]
    assert file_actions.build_open_directory_command(
        PurePosixPath("/lib"), "linux") == ["xdg-open", "/lib"]


def test_open_file_command_non_windows() -> None:
    assert file_actions.build_open_file_command(
        PurePosixPath("/lib/song.mp3"), "darwin") == ["open", "/lib/song.mp3"]
    assert file_actions.build_open_file_command(
        PurePosixPath("/lib/song.mp3"), "linux") == ["xdg-open", "/lib/song.mp3"]


def test_open_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ProcessingError) as exc:
        file_actions.open_file(tmp_path / "does_not_exist.mp3")
    assert exc.value.code is ErrorCode.FILE_MISSING


def test_reveal_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ProcessingError) as exc:
        file_actions.reveal_in_file_manager(tmp_path / "nope.mp3")
    assert exc.value.code is ErrorCode.FILE_MISSING
