# Adding a new TTS vendor

All vendors live behind one registry in [`backend/app/tts.py`](../backend/app/tts.py).
The API, repository, and processor never branch on the vendor — they read everything
from the `TtsProvider` you register. Adding a vendor is two steps (three if it needs
credentials).

---

## Step 1 — Write a synthesizer

A synthesizer turns text into an audio file. It must match this signature:

```python
async def _synthesize_acme_to_file(
    text: str,
    output_path: str,
    selection: TtsSelection,   # selection.voice is already resolved to the vendor's id
    settings: Settings | None,
) -> None:
    from acme_sdk import AcmeClient  # import inside the function — keeps cold starts cheap

    AcmeClient(api_key=...).speech(
        voice=selection.voice,
        text=text,
        out=output_path,        # write the audio bytes to output_path
    )
```

---

## Step 2 — Register the provider

Add a member to the `TtsVendor` enum and an entry to `TTS_PROVIDERS`. Put the
vendor's constants (voices, default voice, limits) next to the other vendors'
constants at the top of the file.

```python
class TtsVendor(StrEnum):
    ...
    ACME = "acme"

ACME_TTS_VOICE = "nova"
ACME_TTS_VOICES = {"Nova": "nova", "Echo": "echo"}  # friendly name -> vendor voice id

TTS_PROVIDERS = {
    ...,
    TtsVendor.ACME: TtsProvider(
        vendor=TtsVendor.ACME,
        default_voice=ACME_TTS_VOICE,
        voices=ACME_TTS_VOICES,
        synthesizer=_synthesize_acme_to_file,
        # optional, sensible defaults shown:
        model="acme-tts-1",          # recorded in reading metadata (omit if none)
        max_input_chars=4096,        # API rejects longer input (None = no limit)
        output_extension="mp3",      # file extension + S3 key suffix
        content_type="audio/mpeg",   # Content-Type stored on the recording
    ),
}
```

That's it for a vendor with no credentials. Callers select it with
`{"vendor": "acme", "voice": "Nova"}` on `POST /api/v1/readings`.

---

## Step 3 — Only if it needs credentials

Vendors that need an API key (like OpenAI) add a config gate so the API rejects
requests with `503 provider_unavailable` before doing any work.

1. **Add settings** in [`backend/app/config.py`](../backend/app/config.py), e.g.
   `acme_api_key` / `acme_tts_enabled`. Derive the enabled flag once at
   construction time so the rest of the code only reads a bool (see
   `_derive_openai_tts_enabled` for the pattern):

   ```python
   @model_validator(mode="after")
   def _derive_acme_tts_enabled(self) -> "Settings":
       if self.acme_tts_enabled is None:
           self.acme_tts_enabled = bool((self.acme_api_key or "").strip())
       return self
   ```

2. **Give the provider an `is_configured` check** that reads the derived flag:

   ```python
   def _acme_tts_configured(settings: Settings | None) -> bool:
       return bool(settings and settings.acme_tts_enabled)

   TtsVendor.ACME: TtsProvider(
       ...,
       is_configured=_acme_tts_configured,   # default is "always available"
   ),
   ```

   The synthesizer reads the key from `settings` (and, for production, from
   Secrets Manager — see `get_openai_api_key` for the pattern).

3. **Wire the env/secret in Terraform** ([`infrastructure/environments/dev/main.tf`](../infrastructure/environments/dev/main.tf)):
   pass the API key / secret ARN to the **processor** Lambda (plus a
   `secretsmanager:GetSecretValue` policy if it's a secret), and pass the
   `*_TTS_ENABLED` flag to the **api** Lambda so it can gate requests.
