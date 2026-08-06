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
| `AI_NORMALIZATION_ENABLED` | `false` | Processor | Routes normalized text through the AI normalization seam after the regex pass. The seam is a stub today (`app/normalization.py`), so enabling it is currently a no-op; the flag exists so the future path can be turned on without a code change. |
| `OPENAI_TTS_ENABLED` | derived | API, Processor | Whether the OpenAI TTS vendor is offered. When unset it is `true` if an OpenAI key is configured, else `false`. |
| `OPENAI_API_KEY` | — | Processor | OpenAI API key for local use. In AWS use `OPENAI_API_KEY_SECRET_ARN` instead so the key never lands in Terraform state. |
| `OPENAI_API_KEY_SECRET_ARN` | — | Processor | Secrets Manager ARN holding the OpenAI key (raw string or JSON with `OPENAI_API_KEY`/`openai_api_key`/`api_key`). |
| `READINGS_TABLE_NAME` | `local-readings` | API, Processor | DynamoDB readings table. Set by Terraform. |
| `FILES_BUCKET_NAME` | — | API, Processor | S3 bucket for original text, corrected text, and recordings. Set by Terraform. |
| `PROCESSOR_FUNCTION_NAME` | — | API | Name of the processor Lambda the API async-invokes to start processing. Set by Terraform. |

## Changing a value in AWS

`MAX_CHUNK_CHARS` and `AI_NORMALIZATION_ENABLED` are exposed as Terraform
variables (`max_chunk_chars`, `ai_normalization_enabled`). Set them in
`infrastructure/environments/dev/terraform.tfvars` (examples are in
`terraform.tfvars.example`) and apply:

```bash
terraform -chdir=infrastructure/environments/dev apply
```

Both are read by the processor Lambda, so no image rebuild is needed to change
them — only a Terraform apply that updates the function's environment.

## Cost model settings

These settings control the internal cost model and dashboard. See
`docs/cost-model.md` for formulas, guardrail behavior, and storage details.

| Env var | Default | Used by | Meaning |
|---|---|---|---|
| `MAX_RUN_COST_USD` | `0.25` | API | Rejects creation when the pre-run estimate is greater than this many USD. |
| `MONTHLY_BUDGET_USD` | unset | API | Optional dashboard comparison value. It only warns; it does not block processing. |
| `ADMIN_USER_IDS` | empty | API | Comma-separated user IDs allowed to call `/api/v1/costs*`. An empty value fails closed. |
| `LAMBDA_MEMORY_MB` | `256` | API, Processor | Memory used by pre-run compute estimates and the processor fallback when `AWS_LAMBDA_FUNCTION_MEMORY_SIZE` is absent. |
| `LAMBDA_TIMEOUT_MS` | `600000` | API | Full processor timeout charged by the conservative pre-run compute estimate. |
| `COST_PRICE_OVERRIDES` | unset | API + processor | JSON object overriding recognized price keys. Applies to estimates, the creation guardrail and processor-recorded post-run costs alike. Non-finite or negative values are ignored per key. |
