from enum import StrEnum

from pydantic import BaseModel, Field


DEFAULT_USER_SETTINGS = {
    "tts_vendor": "edge-tts",
    "tts_voice": "Zofia",
    "pronunciation_style": None,
    "playback_speed": 1.0,
    "sentence_highlighting": True,
    "export_format": "mp3",
    "abbreviation_readings": [],
}


class ReadingStatus(StrEnum):
    UPLOADED = "uploaded"
    NORMALIZING = "normalizing"
    GENERATING_AUDIO = "generating_audio"
    MERGING_AUDIO = "merging_audio"
    COMPLETED = "completed"
    FAILED = "failed"
    FAILED_TO_START = "failed_to_start"


class ApiError(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ApiError


class AbbreviationReading(BaseModel):
    abbreviation: str
    read_as: str


class ReadingCreateRequest(BaseModel):
    original_text: str
    vendor: str | None = Field(default=None, max_length=120)
    voice: str | None = Field(default=None, max_length=120)
    abbreviation_readings: list[AbbreviationReading] | None = None


class Reading(BaseModel):
    id: str
    original_text_key: str
    corrected_text_key: str | None = None
    recording_key: str | None = None
    vendor: str | None = None
    voice: str | None = None
    status: str
    metadata: dict[str, object] = Field(default_factory=dict)
    char_count: int
    created_at: str
    updated_at: str


class ReadingListResponse(BaseModel):
    items: list[Reading]
    next_cursor: str | None = None


class TtsVoiceOption(BaseModel):
    id: str
    label: str
    provider_voice: str
    language: str | None
    preview_url: str | None


class TtsVendorOptions(BaseModel):
    id: str
    label: str
    model: str | None
    default_voice: str
    voices: list[TtsVoiceOption]


class TtsOptionsResponse(BaseModel):
    default_vendor: str
    vendors: list[TtsVendorOptions]


class UserSettings(BaseModel):
    tts_vendor: str
    tts_voice: str
    pronunciation_style: str | None
    playback_speed: float
    sentence_highlighting: bool
    export_format: str
    abbreviation_readings: list[AbbreviationReading]


class UserSettingsUpdate(BaseModel):
    tts_vendor: str | None = None
    tts_voice: str | None = None
    pronunciation_style: str | None = None
    playback_speed: float | None = Field(default=None, strict=True)
    sentence_highlighting: bool | None = Field(default=None, strict=True)
    export_format: str | None = None
    abbreviation_readings: list[AbbreviationReading] | None = None


class UserSettingsResponse(BaseModel):
    settings: UserSettings
    defaults: UserSettings


class TimingSegment(BaseModel):
    id: str
    text: str
    start: float
    end: float
    paragraph: int


class TimingMapResponse(BaseModel):
    reading_id: str
    duration: float
    segments: list[TimingSegment]


class Job(BaseModel):
    id: str
    reading_id: str
    attempt: int
    status: str
    state: str
    step_message: str
    progress: int | None = None
    error: str | None = None
    failed_step: str | None = None
    created_at: str
    updated_at: str


class JobListResponse(BaseModel):
    items: list[Job]
    next_cursor: str | None = None
