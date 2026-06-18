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
    "error.invalid_filename": "That output name is not valid.",
    "error.output_folder_failed": "The output folder could not be created.",
    "error.save_failed": "The cleaned file could not be saved.",
    "error.file_locked": "The file is in use by another program.",
    "error.cannot_open": "Windows could not open that file.",
    "error.file_missing": "The cleaned file was moved or deleted.",
    # Home screen
    "home.no_file": "No file selected",
    "home.selected": "Selected:",
    "action.clean_video_audio": "Clean Video Audio",
    "action.cleaned_files": "Cleaned Files",
    # Save-cleaned-file dialog
    "save.title": "Save Cleaned File",
    "save.filename": "File name",
    "save.type": "File type",
    "save.destination": "Will be saved to",
    "save.button": "Save",
    "save.discard.title": "Discard cleaned file?",
    "save.discard.body": "You have not saved this cleaned file yet. "
    "Discard it and start over?",
    "save.discard.keep": "Keep editing",
    "save.discard.discard": "Discard",
    # Live filename validation
    "validate.empty": "Please enter a file name.",
    "validate.invalid_chars": "A name cannot contain  < > : \" / \\ | ? *",
    "validate.reserved": "That name is reserved by Windows. Choose another.",
    "validate.too_long": "That name is too long.",
    "validate.trailing": "A name cannot end with a space or a dot.",
    # Completion panel
    "completion.ready": "Your cleaned file is ready",
    "completion.filename": "Name",
    "completion.folder": "Folder",
    "completion.type": "Type",
    "completion.size": "Size",
    "completion.duration": "Duration",
    "action.play_cleaned_file": "Play Cleaned File",
    "action.open_cleaned_video": "Open Cleaned Video",
    "action.show_in_folder": "Show in Folder",
    "action.clean_another": "Clean Another File",
    "action.go_to_cleaned_files": "Go to Cleaned Files",
    # Navigation / shell
    "nav.home": "Home",
    "nav.cleaned_files": "Cleaned Files",
    # Home hero
    "home.hero_statement": "A Bangladesh-made Windows app that removes background "
    "noise from your audio and video — fully offline.",
    # Home drop zone
    "home.drop": "Drop audio or video here",
    "home.or_choose": "or choose a file",
    "home.supported": "Supported: MP3, WAV, M4A, FLAC · MP4, MOV, MKV, AVI, WebM",
    "home.reading_file": "Reading file…",
    "home.replace_file": "Replace File",
    "media.format": "Format",
    "media.size": "Size",
    "media.duration": "Duration",
    "media.sample_rate": "Sample rate",
    "media.resolution": "Resolution",
    "media.audio": "Audio",
    "media.video": "Video",
    # Processing view
    "processing.title": "PROCESSING",
    "processing.subtitle": "Local AI · No upload · CPU · DeepFilterNet3",
    "processing.privacy": "Processed locally — nothing is uploaded",
    "processing.elapsed": "Elapsed",
    "processing.stage_of": "Stage {current} of {total}",
    "processing.visualization": "Processing visualization",
    "processing.engine_log": "Engine log",
    "processing.pipeline": "Pipeline",
    "processing.cancel": "Cancel Processing",
    "processing.hide_details": "Hide technical details",
    "console.copy": "Copy activity",
    "console.pause_scroll": "Pause auto-scroll",
    "console.resume_scroll": "Resume auto-scroll",
    # Error recovery
    "action.try_again": "Try Again",
    "action.choose_another": "Choose Another File",
    "action.view_log_folder": "View Log Folder",
    # Pipeline stage names (stage.<ProcessingStage value>)
    "stage.preparing": "Preparing file",
    "stage.inspecting": "Inspecting video",
    "stage.extracting_audio": "Extracting audio",
    "stage.converting": "Converting audio",
    "stage.loading_model": "Loading AI model",
    "stage.denoising": "Removing noise",
    "stage.encoding": "Encoding output",
    "stage.muxing_video": "Rebuilding video",
    "stage.finalizing": "Saving result",
    "stage.completed": "Completed",
    "stage.failed": "Failed",
    "stage.cancelled": "Cancelled",
    # Activity log templates (activity.<ActivityCode value>)
    "activity.input_identified": "Input identified: {kind}",
    "activity.audio_stream": "Audio stream: {codec}, {sample_rate} Hz, {channels} ch",
    "activity.extracting": "Extracting audio track",
    "activity.converting": "Preparing audio at 48 kHz",
    "activity.model_ready": "DeepFilterNet3 model ready",
    "activity.denoise_started": "Noise removal started",
    "activity.analyzing": "Analyzing frequency spectrum (STFT · 48 kHz)",
    "activity.profiling_noise": "Profiling background noise floor",
    "activity.separating": "Separating speech from noise",
    "activity.applying_mask": "Applying deep-filter mask across frequency bands",
    "activity.reconstructing": "Reconstructing clean waveform (overlap-add)",
    "activity.verifying": "Verifying output integrity",
    "activity.ffmpeg_progress": "Processed {current}s of {total}s",
    "activity.rebuilding_video": "Rebuilding video with cleaned audio",
    "activity.encoding": "Encoding cleaned audio",
    "activity.saving": "Saving result to library",
    "activity.done": "Done",
}
