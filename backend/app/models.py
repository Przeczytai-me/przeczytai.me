from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


DEFAULT_USER_SETTINGS = {
    "reading_model": "edge-tts",
    "fallback_model": None,
    "voice": "Zofia",
    "pronunciation_style": "natural",
    "playback_speed": 1.0,
    "sentence_highlighting": True,
    "custom_abbreviation_readings": [],
    "exports": {
        "filename_pattern": "{reading_id}",
        "mp3_quality": "standard",
        "text_format": "md",
    },
    "updated_at": "1970-01-01T00:00:00Z",
}

PRONUNCIATION_STYLES = [
    {"id": "natural", "label": "Naturalny"},
    {"id": "clear", "label": "Wyraźny"},
]


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
    provider_id: str
    label: str
    language: str
    preview_url: str | None


class TtsVendorOption(BaseModel):
    id: str
    label: str


class TtsModelOption(BaseModel):
    id: str
    vendor_id: str
    label: str


class PronunciationStyleOption(BaseModel):
    id: str
    label: str


class TtsDefaults(BaseModel):
    model: str
    voice: str
    pronunciation_style: str


class TtsOptionsResponse(BaseModel):
    vendors: list[TtsVendorOption]
    models: list[TtsModelOption]
    voices: list[TtsVoiceOption]
    pronunciation_styles: list[PronunciationStyleOption]
    defaults: TtsDefaults


class UserSettingsExports(BaseModel):
    filename_pattern: str
    mp3_quality: str
    text_format: str


class UserSettings(BaseModel):
    reading_model: str
    fallback_model: str | None
    voice: str
    pronunciation_style: str
    playback_speed: float
    sentence_highlighting: bool
    custom_abbreviation_readings: list[AbbreviationReading]
    exports: UserSettingsExports
    updated_at: str


class UserSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    reading_model: str
    fallback_model: str | None = None
    voice: str
    pronunciation_style: str
    playback_speed: float = Field(strict=True)
    sentence_highlighting: bool = Field(strict=True)
    custom_abbreviation_readings: list[AbbreviationReading]
    exports: UserSettingsExports


class TimingSegment(BaseModel):
    id: str
    text: str
    paragraph_index: int
    start_ms: int
    end_ms: int


class TimingMapResponse(BaseModel):
    reading_id: str
    duration_ms: int
    segments: list[TimingSegment]


class JobError(BaseModel):
    code: str
    message: str
    step: str


class Job(BaseModel):
    id: str
    reading_id: str
    attempt: int
    status: str
    progress: int | None = None
    current_step: str
    error: JobError | None = None
    created_at: str
    updated_at: str


class JobListResponse(BaseModel):
    items: list[Job]
    next_cursor: str | None = None
