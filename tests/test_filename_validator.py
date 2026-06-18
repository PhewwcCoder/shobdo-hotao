"""Windows-safe filename validation + collision-safe naming."""

from __future__ import annotations

from pathlib import Path

import pytest

from shobdohotao.storage.filename_validator import (
    FilenameIssue,
    check_filename,
    collision_safe_name,
    is_valid_filename,
)


@pytest.mark.parametrize("name", [
    "lecture_cleaned",
    "interview_cleaned.wav",
    "ক্লাস_রেকর্ডিং",          # Bengali
    "réunion",                  # accented
    "my recording 2026",
    "v1.2 final notes",
])
def test_valid_names(name: str) -> None:
    assert is_valid_filename(name), name


def test_empty_and_space_only() -> None:
    assert check_filename("") is FilenameIssue.EMPTY
    assert check_filename("   ") is FilenameIssue.EMPTY
    assert check_filename(None) is FilenameIssue.EMPTY  # type: ignore[arg-type]


@pytest.mark.parametrize("name", [
    "a<b", "a>b", "a:b", 'a"b', "a/b", "a\\b", "a|b", "a?b", "a*b",
])
def test_invalid_chars(name: str) -> None:
    assert check_filename(name) is FilenameIssue.INVALID_CHARS


@pytest.mark.parametrize("name", [
    "CON", "con", "PRN", "aux", "NUL", "COM1", "lpt1", "COM9",
    "CON.mp3", "nul.wav",
])
def test_reserved_names(name: str) -> None:
    assert check_filename(name) is FilenameIssue.RESERVED


def test_trailing_space_or_dot() -> None:
    assert check_filename("name ") is FilenameIssue.TRAILING
    assert check_filename("name.") is FilenameIssue.TRAILING


def test_too_long() -> None:
    assert check_filename("x" * 250) is FilenameIssue.TOO_LONG


# --- collision-safe naming ------------------------------------------------

def test_collision_safe_first_is_plain() -> None:
    out = collision_safe_name(Path("/lib"), "song", "mp3", exists=lambda p: False)
    assert out == Path("/lib/song.mp3")


def test_collision_safe_appends_2_then_3() -> None:
    taken = {Path("/lib/song.mp3")}
    out = collision_safe_name(Path("/lib"), "song", "mp3", exists=lambda p: p in taken)
    assert out == Path("/lib/song_2.mp3")

    taken = {Path("/lib/song.mp3"), Path("/lib/song_2.mp3")}
    out = collision_safe_name(Path("/lib"), "song", "mp3", exists=lambda p: p in taken)
    assert out == Path("/lib/song_3.mp3")


def test_collision_safe_handles_dotted_extension_arg() -> None:
    out = collision_safe_name(Path("/lib"), "clip", ".mp4", exists=lambda p: False)
    assert out == Path("/lib/clip.mp4")
