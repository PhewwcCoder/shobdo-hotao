"""Service layer: FFmpeg, probing, ML backend, pipeline, logging.

The UI must depend only on ``pipeline`` (and read-only ``media_probe``); it
never touches ``ffmpeg_service`` or ``denoise_backend`` directly.
"""
