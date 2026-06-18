"""Pure tests: stage sequences/mapping, stepper model, activity formatting,
MediaInfo builders, and the recording observer. No Qt required.
"""

from __future__ import annotations

from pathlib import Path

from shobdohotao.domain import (
    ActivityCode,
    AudioMetadata,
    AudioStreamInfo,
    JobState,
    MediaInfo,
    MediaType,
    ProcessingStage,
    VideoMetadata,
    stage_for_jobstate,
    stage_sequence_for,
)
from shobdohotao.i18n import Language, Translator
from shobdohotao.services.events import RecordingObserver
from shobdohotao.ui.activity_format import format_activity
from shobdohotao.ui.stepper_model import StepperModel, StepStatus


def test_stage_sequences_have_six_steps() -> None:
    assert len(stage_sequence_for(MediaType.AUDIO)) == 6
    assert len(stage_sequence_for(MediaType.VIDEO)) == 6
    assert ProcessingStage.DENOISING in stage_sequence_for(MediaType.AUDIO)
    assert ProcessingStage.MUXING_VIDEO in stage_sequence_for(MediaType.VIDEO)


def test_jobstate_to_stage_mapping() -> None:
    assert stage_for_jobstate(JobState.VALIDATING) is ProcessingStage.PREPARING
    assert stage_for_jobstate(JobState.INSPECTING) is ProcessingStage.INSPECTING
    assert stage_for_jobstate(JobState.EXTRACTING) is ProcessingStage.EXTRACTING_AUDIO
    assert stage_for_jobstate(JobState.ENHANCING) is ProcessingStage.DENOISING
    assert stage_for_jobstate(JobState.MUXING) is ProcessingStage.MUXING_VIDEO
    assert stage_for_jobstate(JobState.DONE) is ProcessingStage.COMPLETED


# --- stepper model --------------------------------------------------------

def _audio_model() -> StepperModel:
    return StepperModel(stage_sequence_for(MediaType.AUDIO))


def test_stepper_set_active_marks_before_completed() -> None:
    m = _audio_model()
    m.set_active(ProcessingStage.DENOISING)
    assert m.status_of(ProcessingStage.PREPARING) is StepStatus.COMPLETED
    assert m.status_of(ProcessingStage.CONVERTING) is StepStatus.COMPLETED
    assert m.status_of(ProcessingStage.LOADING_MODEL) is StepStatus.COMPLETED
    assert m.status_of(ProcessingStage.DENOISING) is StepStatus.ACTIVE
    assert m.status_of(ProcessingStage.ENCODING) is StepStatus.PENDING
    assert m.active_index() == 3


def test_stepper_complete_all() -> None:
    m = _audio_model()
    m.complete_all()
    assert all(st is StepStatus.COMPLETED for _, st in m.statuses())


def test_stepper_failed_marks_active_step() -> None:
    m = _audio_model()
    m.set_active(ProcessingStage.DENOISING)
    m.set_failed()
    assert m.status_of(ProcessingStage.DENOISING) is StepStatus.FAILED
    # Steps before remain completed.
    assert m.status_of(ProcessingStage.CONVERTING) is StepStatus.COMPLETED


def test_stepper_cancelled_marks_active_step() -> None:
    m = _audio_model()
    m.set_active(ProcessingStage.CONVERTING)
    m.set_cancelled()
    assert m.status_of(ProcessingStage.CONVERTING) is StepStatus.CANCELLED


def test_stepper_ignores_stage_not_in_sequence() -> None:
    m = StepperModel(stage_sequence_for(MediaType.VIDEO))
    m.set_active(ProcessingStage.CONVERTING)  # audio-only stage; no-op
    assert m.active_index() is None


# --- activity formatting --------------------------------------------------

def test_format_activity_fills_params_en() -> None:
    t = Translator(Language.EN)
    msg = format_activity(t, ActivityCode.AUDIO_STREAM,
                          {"codec": "aac", "sample_rate": 48000, "channels": 2})
    assert msg == "Audio stream: aac, 48000 Hz, 2 ch"


def test_format_activity_progress_and_bn() -> None:
    t = Translator(Language.BN)
    msg = format_activity(t, ActivityCode.FFMPEG_PROGRESS, {"current": 5, "total": 30})
    assert "5" in msg and "30" in msg


def test_format_activity_missing_param_is_safe() -> None:
    t = Translator(Language.EN)
    msg = format_activity(t, ActivityCode.AUDIO_STREAM, {"codec": "aac"})
    assert "aac" in msg  # missing placeholders do not raise


def test_no_path_param_leaks_in_known_activities() -> None:
    # The activity templates we emit never reference a filesystem path field.
    t = Translator(Language.EN)
    for code in ActivityCode:
        template = t.tr(f"activity.{code.value}")
        assert "{path}" not in template and "Temp" not in template


# --- MediaInfo builders ---------------------------------------------------

def test_media_info_from_audio() -> None:
    meta = AudioMetadata(Path("a.mp3"), 12.0, 44100, 2, 2048, "mp3")
    info = MediaInfo.from_audio(meta)
    assert info.media_type is MediaType.AUDIO
    assert info.duration_seconds == 12.0
    assert info.sample_rate == 44100 and info.channels == 2


def test_media_info_from_video() -> None:
    meta = VideoMetadata(
        Path("v.mp4"), "mp4", "h264", 61.5, 4096, 1920, 1080, 30.0,
        audio_streams=(AudioStreamInfo(1, "aac", 2, 48000),),
    )
    info = MediaInfo.from_video(meta)
    assert info.media_type is MediaType.VIDEO
    assert info.width == 1920 and info.height == 1080
    assert info.audio_codec == "aac" and info.sample_rate == 48000


# --- recording observer ---------------------------------------------------

def test_recording_observer_captures_events() -> None:
    obs = RecordingObserver()
    obs.on_stage(ProcessingStage.DENOISING)
    obs.on_progress(5, 30)
    obs.on_activity(ActivityCode.MODEL_READY)
    assert obs.stages == [ProcessingStage.DENOISING]
    assert obs.progress == [(5, 30)]
    assert obs.activities[0][0] is ActivityCode.MODEL_READY
