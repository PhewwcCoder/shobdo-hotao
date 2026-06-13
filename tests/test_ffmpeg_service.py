"""FFmpeg command-construction tests (no FFmpeg execution)."""

from __future__ import annotations

from pathlib import Path

import pytest

from shobdohotao.domain import OutputFormat
from shobdohotao.services import ffmpeg_service, media_probe


def test_convert_cmd_uses_arg_array_and_pcm_48k() -> None:
    cmd = ffmpeg_service.build_convert_to_wav_cmd(
        "ffmpeg", Path("in.mp3"), Path("out.wav")
    )
    assert isinstance(cmd, list)
    assert "pcm_s16le" in cmd
    assert "48000" in cmd
    assert "-y" in cmd
    # No shell metacharacters / never a single string.
    assert all(isinstance(part, str) for part in cmd)


def test_export_cmd_mp3_uses_lame_and_bitrate() -> None:
    cmd = ffmpeg_service.build_export_cmd(
        "ffmpeg", Path("e.wav"), Path("o.mp3"), OutputFormat.MP3
    )
    assert "libmp3lame" in cmd
    assert "-b:a" in cmd


def test_export_cmd_wav_and_flac() -> None:
    wav = ffmpeg_service.build_export_cmd(
        "ffmpeg", Path("e.wav"), Path("o.wav"), OutputFormat.WAV
    )
    assert "pcm_s16le" in wav
    flac = ffmpeg_service.build_export_cmd(
        "ffmpeg", Path("e.wav"), Path("o.flac"), OutputFormat.FLAC
    )
    assert "flac" in flac


def test_probe_cmd_selects_audio_json() -> None:
    cmd = media_probe.build_probe_cmd("ffprobe", Path("in.m4a"))
    assert "-print_format" in cmd and "json" in cmd
    assert "-select_streams" in cmd and "a" in cmd


def test_parse_probe_json_extracts_fields() -> None:
    raw = (
        '{"streams":[{"sample_rate":"44100","channels":2,'
        '"codec_name":"aac","duration":"12.5"}],'
        '"format":{"duration":"12.5"}}'
    )
    meta = media_probe._parse_probe_json(raw, Path("x.m4a"), 2048)
    assert meta.sample_rate == 44100
    assert meta.channels == 2
    assert meta.codec == "aac"
    assert meta.size_bytes == 2048
    assert meta.duration_seconds == pytest.approx(12.5)


def test_parse_probe_json_no_audio_stream_raises() -> None:
    from shobdohotao.domain import ProcessingError

    with pytest.raises(ProcessingError):
        media_probe._parse_probe_json('{"streams":[]}', Path("x.mp4"), 1)
