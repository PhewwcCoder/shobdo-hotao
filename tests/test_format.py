"""Pure formatter tests."""

from __future__ import annotations

from shobdohotao.ui.format import human_duration, human_size


def test_human_size() -> None:
    assert human_size(0) == "0 B"
    assert human_size(512) == "512 B"
    assert human_size(1536) == "1.5 KB"
    assert human_size(5 * 1024 * 1024) == "5.0 MB"
    assert human_size(3 * 1024**3) == "3.0 GB"


def test_human_duration() -> None:
    assert human_duration(0) == "0:00"
    assert human_duration(5) == "0:05"
    assert human_duration(127) == "2:07"
    assert human_duration(3785) == "1:03:05"
