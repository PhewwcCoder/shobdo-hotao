"""StorageService: save staged outputs into the library + discard."""

from __future__ import annotations

from pathlib import Path

import pytest

from shobdohotao.domain import ErrorCode, MediaType, ProcessingError
from shobdohotao.storage.app_paths import AppPaths
from shobdohotao.storage.storage_service import StorageService


def _staged(tmp_path: Path, name: str = "noisy_cleaned.mp3") -> Path:
    staging = tmp_path / "app" / "Temp" / "job1"
    staging.mkdir(parents=True, exist_ok=True)
    f = staging / name
    f.write_bytes(b"AUDIODATA")
    return f


def _service(tmp_path: Path) -> StorageService:
    return StorageService(AppPaths(tmp_path / "app"))


def test_save_audio_moves_into_audio_library(tmp_path: Path) -> None:
    svc = _service(tmp_path)
    staged = _staged(tmp_path)
    out = svc.save_cleaned(staged, "lecture_cleaned", MediaType.AUDIO)
    assert out == svc.paths.audio_library() / "lecture_cleaned.mp3"
    assert out.exists()
    assert not staged.exists()  # moved, not copied


def test_save_video_uses_video_library_and_keeps_extension(tmp_path: Path) -> None:
    svc = _service(tmp_path)
    staged = _staged(tmp_path, "clip_cleaned.mp4")
    out = svc.save_cleaned(staged, "my video", MediaType.VIDEO)
    assert out.parent == svc.paths.video_library()
    assert out.name == "my video.mp4"


def test_save_is_collision_safe(tmp_path: Path) -> None:
    svc = _service(tmp_path)
    svc.paths.audio_library().mkdir(parents=True, exist_ok=True)
    (svc.paths.audio_library() / "lecture.mp3").write_bytes(b"existing")
    out = svc.save_cleaned(_staged(tmp_path), "lecture", MediaType.AUDIO)
    assert out.name == "lecture_2.mp3"
    # The pre-existing file is untouched.
    assert (svc.paths.audio_library() / "lecture.mp3").read_bytes() == b"existing"


def test_save_strips_user_typed_extension(tmp_path: Path) -> None:
    svc = _service(tmp_path)
    out = svc.save_cleaned(_staged(tmp_path), "lecture.mp3", MediaType.AUDIO)
    assert out.name == "lecture.mp3"  # not lecture.mp3.mp3


def test_save_rejects_invalid_name(tmp_path: Path) -> None:
    svc = _service(tmp_path)
    with pytest.raises(ProcessingError) as exc:
        svc.save_cleaned(_staged(tmp_path), "bad/name", MediaType.AUDIO)
    assert exc.value.code is ErrorCode.INVALID_FILENAME


def test_save_missing_staged_raises(tmp_path: Path) -> None:
    svc = _service(tmp_path)
    with pytest.raises(ProcessingError) as exc:
        svc.save_cleaned(tmp_path / "ghost.mp3", "x", MediaType.AUDIO)
    assert exc.value.code is ErrorCode.SAVE_FAILED


def test_save_bengali_filename(tmp_path: Path) -> None:
    svc = _service(tmp_path)
    out = svc.save_cleaned(_staged(tmp_path), "ক্লাস_রেকর্ডিং", MediaType.AUDIO)
    assert out.name == "ক্লাস_রেকর্ডিং.mp3"
    assert out.exists()


def test_discard_removes_staged_file_and_dir(tmp_path: Path) -> None:
    svc = _service(tmp_path)
    staged = _staged(tmp_path)
    svc.discard(staged)
    assert not staged.exists()
    assert not staged.parent.exists()  # staging dir under Temp removed


def test_discard_is_safe_when_missing(tmp_path: Path) -> None:
    svc = _service(tmp_path)
    svc.discard(tmp_path / "nope.mp3")  # must not raise


def test_suggested_stem(tmp_path: Path) -> None:
    svc = _service(tmp_path)
    assert svc.suggested_stem("lecture.mp3") == "lecture_cleaned"
    assert svc.suggested_stem("interview.mov") == "interview_cleaned"
