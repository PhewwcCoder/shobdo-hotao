# Product Spec — শব্দ-হটাও (ShobdoHotao)

## What it is
An offline desktop app that removes background noise from recordings — both
**audio files and the audio track of videos** — using DeepFilterNet3, with a
bilingual (Bangla/English) Frutiger-Aero interface. Nothing is uploaded; there
are no accounts, API keys, quotas, or telemetry.

## Users
University students and budget creators recording lectures, viva practice,
interviews, podcasts, and video voiceovers in noisy rooms.

## Core capabilities

### Audio (MVP)
Import a noisy audio file → choose a strength (Gentle / Balanced / Strong →
মৃদু / সুষম / কড়া) → clean → export to WAV / MP3 / FLAC with a collision-safe
`_cleaned` name.

### Video noise removal
Import **MP4, MOV, MKV, AVI, or WebM** → the app:

1. Inspects the container with ffprobe (container, video codec, audio codec(s),
   duration, audio-stream count, subtitle streams).
2. If there is more than one audio track, lets the user pick which to clean.
3. Extracts the chosen audio stream to a temporary 48 kHz WAV.
4. Cleans it through the shared DeepFilterNet pipeline.
5. Remuxes the cleaned audio with the **original video copied losslessly**
   (`-c:v copy`), so resolution, frame rate, and aspect ratio are preserved.
6. Encodes the cleaned audio as AAC (MP4/MOV/MKV/AVI) or Opus (WebM).
7. Preserves global metadata and subtitle streams where the container allows.
8. Writes a collision-safe output, e.g. `lecture_cleaned.mp4`,
   `lecture_cleaned_2.mp4`. The original is never overwritten.

Progress is reported in plain stages: **Inspecting video → Extracting audio →
Removing noise → Creating cleaned video → Finished**. A Cancel button safely
terminates the running FFmpeg subprocess and cleans up. All FFmpeg and model
work runs on background workers; the window stays responsive.

## Validation & errors (plain, translated)
The app refuses or explains rather than crashing when: the video has no audio,
the container/codec is unsupported, the video exceeds the supported maximum
length, free disk space is insufficient, FFmpeg fails, or the model fails to
start. Temporary WAV/working files are deleted on success, cancellation, and
error.

## Non-goals (pre-v1.0)
Real-time mic filtering, accounts, cloud/web hosting, mobile apps, music source
separation, transcription, generative enhancement.

## Honesty
The app never claims all noise is removed or that output is studio quality.
