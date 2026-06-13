"""English string catalog. Keys are stable identifiers used across the app.

Every user-facing string lives here and in ``bn.py`` with identical keys.
No English prose is hardcoded inside widget or logic code.
"""

STRINGS: dict[str, str] = {
    # App identity
    "app.title": "ShobdoHotao",
    "app.title.native": "শব্দ-হটাও",
    "app.tagline": "Remove background noise from your recordings — fully offline.",
    "app.value": "Select a noisy recording, choose a strength, click Clean Audio, "
    "compare, and export. No account. No upload. No limit.",
    # Primary actions
    "action.open": "Open file",
    "action.clean": "Clean Audio",
    "action.cancel": "Cancel",
    "action.export": "Export",
    "action.play_original": "Play original",
    "action.play_cleaned": "Play cleaned",
    "action.settings": "Settings",
    # Strength presets
    "strength.gentle": "Gentle",
    "strength.balanced": "Balanced",
    "strength.strong": "Strong",
    "strength.label": "Strength",
    # Settings
    "settings.output_folder": "Output folder",
    "settings.output_format": "Output format",
    "settings.language": "Language",
    "settings.reduce_motion": "Reduce motion",
    "settings.reduce_transparency": "Simple theme (reduce transparency)",
    # Status
    "status.idle": "Ready",
    "status.validating": "Checking file…",
    "status.converting": "Preparing audio…",
    "status.enhancing": "Removing noise…",
    "status.exporting": "Saving cleaned audio…",
    "status.done": "Done",
    "status.cancelled": "Cancelled",
    # Video stages
    "status.inspecting": "Inspecting video…",
    "status.extracting": "Extracting audio…",
    "status.muxing": "Creating cleaned video…",
    # Video stream selection
    "video.choose_audio.title": "Choose an audio track",
    "video.choose_audio.prompt": "This video has multiple audio tracks. "
    "Which one should be cleaned?",
    "video.open": "Open video",
    # Metadata labels
    "meta.duration": "Duration",
    "meta.channels": "Channels",
    "meta.sample_rate": "Sample rate",
    "meta.size": "Size",
    # First run / privacy
    "firstrun.title": "Welcome to ShobdoHotao",
    "firstrun.body": "Your audio never leaves this computer. Processing runs "
    "entirely offline on your PC. No account, no upload, no limit.",
    "privacy.title": "Privacy & About",
    "privacy.body": "ShobdoHotao processes audio fully offline. Nothing is "
    "uploaded, no accounts, no tracking. App source is MIT licensed.",
    "privacy.disclaimer": "Note: not all noise can be removed, and the result "
    "is not studio quality.",
    # Errors (mapped from ErrorCode)
    "error.unknown": "Something went wrong. Please try again.",
    "error.file_not_found": "That file could not be found.",
    "error.unsupported_format": "This file type is not supported.",
    "error.unsupported_container": "This video format is not supported.",
    "error.video_too_long": "This video is too long to process.",
    "error.corrupt_media": "This file appears to be damaged and cannot be read.",
    "error.no_audio_stream": "This file has no audio to clean.",
    "error.ffmpeg_failed": "Could not process the audio. The file may be damaged.",
    "error.backend_init_failed": "The noise remover could not start. "
    "Please restart the app.",
    "error.enhance_failed": "Noise removal failed for this file.",
    "error.output_not_written": "The cleaned file could not be saved.",
    "error.low_disk_space": "Not enough free disk space to save the result.",
    "error.cancelled": "Processing was cancelled.",
}
