from functools import lru_cache

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    max_text_chars: int = 100_000
    max_chunk_chars: int = 3000
    readings_table_name: str = Field(
        default="local-readings",
        validation_alias=AliasChoices(
            "READINGS_TABLE_NAME",
            "TEXTS_TABLE_NAME",
        ),
    )
    processor_function_name: str | None = Field(
        default=None,
        validation_alias="PROCESSOR_FUNCTION_NAME",
    )
    files_bucket_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("FILES_BUCKET_NAME", "TEXTS_BUCKET_NAME"),
    )
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_api_key_secret_arn: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY_SECRET_ARN", "OPENAI_API_KEY_SECRET_ID"),
    )
    openai_tts_enabled: bool | None = Field(default=None, validation_alias="OPENAI_TTS_ENABLED")

    @model_validator(mode="after")
    def _derive_openai_tts_enabled(self) -> "Settings":
        # OPENAI_TTS_ENABLED is an explicit operator override; when unset, availability
        # follows from having credentials. After construction this is always a bool.
        if self.openai_tts_enabled is None:
            self.openai_tts_enabled = bool(
                (self.openai_api_key or "").strip()
                or (self.openai_api_key_secret_arn or "").strip()
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
