from enum import StrEnum

from pydantic import BaseModel, Field


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


class ReadingCreateRequest(BaseModel):
    original_text: str
    vendor: str | None = Field(default=None, max_length=120)
    voice: str | None = Field(default=None, max_length=120)


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
