"""Media operations layer: ffprobe inspection, audio extraction, muxing.

This subpackage holds the video-specific FFmpeg building blocks, kept out of
both the UI and the orchestration service. Command builders are pure; the
:class:`~shobdohotao.media.ffmpeg_runner.FfmpegRunner` adds cancellable
execution for long encodes.
"""
