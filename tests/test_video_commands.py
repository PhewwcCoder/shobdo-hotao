"""Unit tests for video FFmpeg command construction, naming, and parsing.

No FFmpeg/ffprobe is executed here — only the pure builders/parsers.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shobdohotao.domain import (
    ProcessingError,
    VideoDenoiseRequest,
    derive_cleaned_path,
)
from shobdohotao.media import probe, video_extractor, video_muxer

# --- extraction -----------------------------------------------------------

def test_extract_cmd_first_stream_is_arg_array_48k() -> None:
    cmd = video_extractor.build_extract_audio_cmd(
        "ffmpeg", Path("in.mp4"), Path("a.wav")
    )
    assert isinstance(cmd, list) and all(isinstance(p, str) for p in cmd)
    assert "pcm_s16le" in cmd and "48000" in cmd
    assert "-vn" in cmd
    # First audio stream when no index given.
    assert "0:a:0" in cmd


def test_extract_cmd_specific_stream_index() -> None:
    cmd = video_extractor.build_extract_audio_cmd(
        "ffmpeg", Path("in.mkv"), Path("a.wav"), stream_index=3
    )
    assert "0:3" in cmd


# --- muxing ---------------------------------------------------------------

def test_mux_cmd_copies_video_and_uses_aac_for_mp4() -> None:
    cmd = video_muxer.build_mux_cmd(
        "ffmpeg", Path("in.mp4"), Path("c.wav"), Path("out.mp4"),
        container="mp4", keep_subtitles=False,
    )
    assert "-c:v" in cmd and cmd[cmd.index("-c:v") + 1] == "copy"
    assert "-c:a" in cmd and cmd[cmd.index("-c:a") + 1] == "aac"
    assert "0:v:0" in cmd and "1:a:0" in cmd
    assert "-map_metadata" in cmd
    assert "+faststart" in cmd


def test_mux_cmd_webm_uses_opus_and_no_subtitle_copy() -> None:
    cmd = video_muxer.build_mux_cmd(
        "ffmpeg", Path("in.webm"), Path("c.wav"), Path("out.webm"),
        container="webm", keep_subtitles=True,
    )
    assert cmd[cmd.index("-c:a") + 1] == "libopus"
    # webm is not subtitle-friendly -> no -c:s copy / no subtitle map.
    assert "-c:s" not in cmd
    assert "0:s?" not in cmd


def test_mux_cmd_mkv_maps_subtitles_when_requested() -> None:
    cmd = video_muxer.build_mux_cmd(
        "ffmpeg", Path("in.mkv"), Path("c.wav"), Path("out.mkv"),
        container="mkv", keep_subtitles=True,
    )
    assert "0:s?" in cmd
    assert "-c:s" in cmd and cmd[cmd.index("-c:s") + 1] == "copy"


def test_audio_codec_for_defaults_to_aac() -> None:
    assert video_muxer.audio_codec_for("avi") == "aac"
    assert video_muxer.audio_codec_for("webm") == "libopus"
    assert video_muxer.audio_codec_for("unknown") == "aac"


# --- naming ---------------------------------------------------------------

def test_video_cleaned_name_collision_uses_underscore_2() -> None:
    taken = {Path("/out/lecture_cleaned.mp4")}
    out = derive_cleaned_path(
        Path("/in/lecture.mp4"), Path("/out"), "mp4", exists=lambda p: p in taken
    )
    assert out.name == "lecture_cleaned_2.mp4"


def test_request_container_defaults_to_input_suffix() -> None:
    req = VideoDenoiseRequest(Path("/in/clip.MOV"), Path("/out"))
    assert req.container() == "mov"
    req2 = VideoDenoiseRequest(Path("/in/clip.mkv"), Path("/out"),
                               output_container=".mp4")
    assert req2.container() == "mp4"


# --- probe parsing --------------------------------------------------------

def test_probe_cmd_requests_all_streams_json() -> None:
    cmd = probe.build_probe_cmd("ffprobe", Path("in.mp4"))
    assert "-show_streams" in cmd and "json" in cmd and "-show_format" in cmd


def test_parse_probe_json_extracts_video_audio_subs() -> None:
    raw = """
    {
      "format": {"format_name": "mov,mp4,m4a", "duration": "61.5"},
      "streams": [
        {"index":0,"codec_type":"video","codec_name":"h264",
         "width":1920,"height":1080,"r_frame_rate":"30000/1001"},
        {"index":1,"codec_type":"audio","codec_name":"aac","channels":2,
         "sample_rate":"48000","tags":{"language":"eng","title":"Main"}},
        {"index":2,"codec_type":"audio","codec_name":"ac3","channels":6,
         "sample_rate":"48000","tags":{"language":"ben"}},
        {"index":3,"codec_type":"subtitle","codec_name":"mov_text",
         "tags":{"language":"eng"}}
      ]
    }
    """
    meta = probe.parse_probe_json(raw, Path("x.mp4"), 4096)
    assert meta.container == "mov"
    assert meta.video_codec == "h264"
    assert meta.width == 1920 and meta.height == 1080
    assert round(meta.frame_rate, 2) == pytest.approx(29.97, abs=0.01)
    assert len(meta.audio_streams) == 2
    assert meta.audio_streams[0].language == "eng"
    assert meta.audio_streams[1].index == 2 and meta.audio_streams[1].channels == 6
    assert len(meta.subtitle_streams) == 1
    assert meta.has_audio is True
    assert meta.duration_seconds == pytest.approx(61.5)


def test_parse_probe_json_no_audio() -> None:
    raw = (
        '{"format":{"format_name":"matroska,webm","duration":"5"},'
        '"streams":[{"index":0,"codec_type":"video","codec_name":"vp9"}]}'
    )
    meta = probe.parse_probe_json(raw, Path("x.webm"), 10)
    assert meta.has_audio is False


def test_parse_frame_rate_edge_cases() -> None:
    assert probe._parse_frame_rate("0/0") == 0.0
    assert probe._parse_frame_rate("25/1") == 25.0
    assert probe._parse_frame_rate("") == 0.0


def test_probe_video_missing_file_raises() -> None:
    with pytest.raises(ProcessingError):
        probe.probe_video(Path("/definitely/missing/file.mp4"),
                          ffprobe_exe="ffprobe")


# --- ffmpeg -i fallback parser -------------------------------------------

_FFMPEG_I_SAMPLE = """\
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'x.mp4':
  Metadata:
    encoder         : Lavf61.7.100
  Duration: 00:01:03.50, start: 0.000000, bitrate: 125 kb/s
  Stream #0:0[0x1](und): Video: h264 (High) (avc1 / 0x31637661), yuv420p, \
320x240 [SAR 1:1 DAR 4:3], 43 kb/s, 24 fps, 24 tbr, 12288 tbn (default)
  Stream #0:1[0x2](eng): Audio: aac (LC) (mp4a / 0x6134706D), 48000 Hz, \
stereo, fltp, 69 kb/s (default)
  Stream #0:2(ben): Audio: ac3, 48000 Hz, 5.1, 384 kb/s
  Stream #0:3(eng): Subtitle: mov_text
At least one output file must be specified
"""


def test_parse_ffmpeg_info_full() -> None:
    meta = probe.parse_ffmpeg_info(_FFMPEG_I_SAMPLE, Path("x.mp4"), 5000)
    assert meta.container == "mov"
    assert meta.video_codec == "h264"
    assert meta.width == 320 and meta.height == 240
    assert meta.frame_rate == 24.0
    assert meta.duration_seconds == pytest.approx(63.5)
    assert len(meta.audio_streams) == 2
    assert meta.audio_streams[0].index == 1
    assert meta.audio_streams[0].channels == 2
    assert meta.audio_streams[0].language == "eng"
    assert meta.audio_streams[1].channels == 6  # 5.1
    assert meta.audio_streams[1].language == "ben"
    assert len(meta.subtitle_streams) == 1
    assert meta.has_audio is True


def test_parse_ffmpeg_info_unreadable_raises() -> None:
    with pytest.raises(ProcessingError):
        probe.parse_ffmpeg_info("garbage with no input header", Path("x.mp4"), 1)
