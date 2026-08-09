# Backend configuration

The backend reads settings from environment variables (see
`backend/app/config.py`). Locally they can go in `backend/.env`; in AWS they are
set as Lambda environment variables by Terraform
(`infrastructure/environments/dev/`). Each setting is read by the API Lambda, the
processor Lambda, or both.

## Settings

| Env var | Default | Used by | Meaning |
|---|---|---|---|
| `MAX_TEXT_CHARS` | `100000` | API | Max characters accepted by `POST /api/v1/readings`; larger input is rejected with `413`. |
| `MAX_CHUNK_CHARS` | `3000` | Processor | Target max characters per synthesis chunk. Text is split into paragraphs, with a sentence-level fallback for paragraphs over this size (`app/splitting.py`). Smaller values mean more, shorter audio segments. |
| `AI_NORMALIZATION_ENABLED` | `false` | Processor | Enables fail-open Polish proofreading with Grok before regex normalization and custom abbreviation readings. The existing name is retained for deployment compatibility. |
| `AI_PROOFREADING_TIMEOUT_SECONDS` | `20` | Processor | Per-request xAI timeout. The client does not retry; timeout or any validation/provider failure falls back to the original source before deterministic processing. |
| `XAI_API_KEY` | — | Processor | xAI API key for local use. In AWS use `XAI_API_KEY_SECRET_ARN` instead so the key never lands in Terraform state. |
| `XAI_API_KEY_SECRET_ARN` | — | Processor | Secrets Manager ARN holding the xAI key (raw string or JSON with `XAI_API_KEY`/`xai_api_key`/`api_key`). |
| `OPENAI_TTS_ENABLED` | derived | API, Processor | Whether the OpenAI TTS vendor is offered. When unset it is `true` if an OpenAI key is configured, else `false`. |
| `OPENAI_API_KEY` | — | Processor | OpenAI API key for local use. In AWS use `OPENAI_API_KEY_SECRET_ARN` instead so the key never lands in Terraform state. |
| `OPENAI_API_KEY_SECRET_ARN` | — | Processor | Secrets Manager ARN holding the OpenAI key (raw string or JSON with `OPENAI_API_KEY`/`openai_api_key`/`api_key`). |
| `READINGS_TABLE_NAME` | `local-readings` | API, Processor | DynamoDB readings table. Set by Terraform. |
| `FILES_BUCKET_NAME` | — | API, Processor | S3 bucket for original text, corrected text, and recordings. Set by Terraform. |
| `PROCESSOR_FUNCTION_NAME` | — | API | Name of the processor Lambda the API async-invokes to start processing. Set by Terraform. |

## Changing a value in AWS

`MAX_CHUNK_CHARS`, `AI_NORMALIZATION_ENABLED`, the proofreading timeout, and the
xAI secret ARN are exposed as Terraform variables (`max_chunk_chars`,
`ai_normalization_enabled`, `ai_proofreading_timeout_seconds`,
`xai_api_key_secret_arn`). Set them in
`infrastructure/environments/dev/terraform.tfvars` (examples are in
`terraform.tfvars.example`) and apply:

```bash
terraform -chdir=infrastructure/environments/dev apply
```

They are read by the processor Lambda, so no image rebuild is needed to change
them — only a Terraform apply that updates the function's environment. Keep the
feature flag disabled until the xAI secret has been configured.
