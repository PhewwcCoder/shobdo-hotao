"""AppPaths resolution + directory creation (temp dirs only)."""

from __future__ import annotations

from pathlib import Path

from shobdohotao.domain import MediaType
from shobdohotao.storage.app_paths import AppPaths, resolve_documents_dir


def test_layout_relative_to_root(tmp_path: Path) -> None:
    p = AppPaths(tmp_path / "ShobdoHotao")
    root = tmp_path / "ShobdoHotao"
    assert p.app_root() == root
    assert p.cleaned_files_dir() == root / "Cleaned Files"
    assert p.audio_library() == root / "Cleaned Files" / "Audio"
    assert p.video_library() == root / "Cleaned Files" / "Video"
    assert p.database_path() == root / "Database" / "library.db"
    assert p.logs_dir() == root / "Logs"
    assert p.temp_dir() == root / "Temp"


def test_create_required_dirs_is_idempotent(tmp_path: Path) -> None:
    p = AppPaths(tmp_path / "app")
    p.create_required_dirs()
    p.create_required_dirs()  # second call must not fail
    for d in p.all_dirs():
        assert d.is_dir()


def test_library_for_media_type(tmp_path: Path) -> None:
    p = AppPaths(tmp_path / "app")
    assert p.library_for(MediaType.AUDIO) == p.audio_library()
    assert p.library_for(MediaType.VIDEO) == p.video_library()


def test_unicode_and_bengali_root(tmp_path: Path) -> None:
    root = tmp_path / "ব্যবহারকারী" / "ShobdoHotao"
    p = AppPaths(root)
    p.create_required_dirs()
    assert p.audio_library().is_dir()
    assert "ব্যবহারকারী" in str(p.app_root())


def test_resolve_documents_dir_returns_path() -> None:
    # Without Qt it falls back to USERPROFILE/Documents or ~/Documents.
    d = resolve_documents_dir()
    assert isinstance(d, Path)
    assert d.name == "Documents"


def test_default_root_is_under_documents() -> None:
    p = AppPaths()
    assert p.app_root().name == "ShobdoHotao"
    assert p.app_root().parent.name == "Documents"
