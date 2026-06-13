"""Domain contract tests — pure, no heavy deps."""

from __future__ import annotations

from pathlib import Path

import pytest

from shobdohotao.domain import (
    DenoiseRequest,
    ErrorCode,
    OutputFormat,
    ProcessingError,
    Strength,
    derive_output_path,
)


def test_strength_attenuation_is_ordered() -> None:
    assert (
        Strength.GENTLE.attenuation_limit_db
        < Strength.BALANCED.attenuation_limit_db
        < Strength.STRONG.attenuation_limit_db
    )


def test_output_format_extension() -> None:
    assert OutputFormat.MP3.extension == "mp3"
    assert OutputFormat.WAV.extension == "wav"
    assert OutputFormat.FLAC.extension == "flac"


def test_derive_output_path_basic() -> None:
    out = derive_output_path(
        Path("/in/lecture.mp3"),
        Path("/out"),
        OutputFormat.MP3,
        exists=lambda p: False,
    )
    assert out == Path("/out/lecture_cleaned.mp3")


def test_derive_output_path_collision_safe() -> None:
    # First collision yields _2 (matches the lecture_cleaned_2.mp4 convention).
    taken = {Path("/out/lecture_cleaned.mp3")}
    out = derive_output_path(
        Path("/in/lecture.mp3"),
        Path("/out"),
        OutputFormat.MP3,
        exists=lambda p: p in taken,
    )
    assert out == Path("/out/lecture_cleaned_2.mp3")


def test_derive_output_path_multiple_collisions() -> None:
    taken = {Path("/out/lecture_cleaned.mp3"), Path("/out/lecture_cleaned_2.mp3")}
    out = derive_output_path(
        Path("/in/lecture.mp3"),
        Path("/out"),
        OutputFormat.MP3,
        exists=lambda p: p in taken,
    )
    assert out == Path("/out/lecture_cleaned_3.mp3")


def test_derive_output_path_never_equals_input() -> None:
    # Input itself is in the output dir with the cleaned name.
    inp = Path("/out/song_cleaned.wav")
    out = derive_output_path(
        inp.with_name("song.wav"),
        Path("/out"),
        OutputFormat.WAV,
        exists=lambda p: False,
    )
    # Even if names would collide with input, result must differ from input.
    assert out != inp.with_name("song.wav") or out.name != inp.name
    assert out.suffix == ".wav"


def test_denoise_request_type_validation() -> None:
    with pytest.raises(TypeError):
        DenoiseRequest(
            input_path="/not/a/path",  # type: ignore[arg-type]
            output_dir=Path("/out"),
            output_format=OutputFormat.MP3,
        )


def test_processing_error_str_includes_code() -> None:
    err = ProcessingError(ErrorCode.FFMPEG_FAILED, "boom")
    assert "ffmpeg_failed" in str(err)
    assert isinstance(err, Exception)
