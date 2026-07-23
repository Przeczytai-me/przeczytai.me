# Creating a reading

A "reading" turns submitted Polish text into a normalized transcript and one MP3
recording. This runbook walks the flow end to end against a deployed API. For the
full request/response schema see the interactive docs at `/docs`, `/redoc`, or
`/openapi.json` (all public).

## Base URL and auth

The API base URL is the `api_base_url` Terraform output:

```bash
API=$(terraform -chdir=infrastructure/environments/dev output -raw api_base_url)
```

All `/api/v1/readings*` endpoints require a **Clerk JWT** sent as
`Authorization: Bearer <token>`. Only `/api/v1/health`, `/docs`, `/redoc`, and
`/openapi.json` are public.

- **In the app:** the frontend requests a JWT from its Clerk template and sends
  it automatically (see `docs/frontend-clerk-api-integration.md`).
- **For manual/testing use:** mint a short-lived token from the development Clerk
  instance the way `tests/api_gateway/` does — the `wait_for_completed` helper and
  the session fixture in `tests/api_gateway/helpers.py` are a working reference.

```bash
TOKEN=... # Clerk JWT for the signed-in user
```

## 1. Submit text

```bash
curl -sS -X POST "$API/api/v1/readings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"original_text": "Ala ma kota. Kot ma Alę."}'
```

`vendor` and `voice` are optional; omitted, they default to the `edge-tts`
vendor with the Polish voice `Zofia`. The response is `202 Accepted` with the new
reading, including its `id` and `status: "uploaded"`. Processing starts
asynchronously in the processor Lambda.

Text is validated up front: empty/whitespace-only input is rejected with `422`,
and input longer than `MAX_TEXT_CHARS` with `413`.

## 2. Poll status

```bash
curl -sS "$API/api/v1/readings/{id}" -H "Authorization: Bearer $TOKEN"
```

The `status` field advances through the pipeline:

`uploaded → normalizing → generating_audio → merging_audio → completed`

A failure ends at `failed`, with `metadata.failed_stage` and `metadata.error`
explaining where and why (`failed_to_start` means the processor could not be
invoked at all). See `docs/reading-statuses.md` for the full table. Poll until the
status is terminal (`completed`, `failed`, or `failed_to_start`).

For a completed reading, `metadata.normalization` identifies the normalization
rule-set version used to produce the corrected text. The current value,
`regex-v1`, means the first version of the deterministic regex-based rules in
`backend/app/normalization.py`.

## 3. Download the outputs

Once `completed`:

```bash
# Recording (302 redirect to a short-lived presigned S3 URL)
curl -sSL "$API/api/v1/readings/{id}/recording" -H "Authorization: Bearer $TOKEN" -o reading.mp3

# Normalized transcript
curl -sS "$API/api/v1/readings/{id}/corrected-text.md" -H "Authorization: Bearer $TOKEN"
```

## Other operations

- `GET /api/v1/readings` — list the signed-in user's readings (paginated via
  `limit` and `cursor`).
- `DELETE /api/v1/readings/{id}` — delete a reading.
- `POST /api/v1/readings/{id}/retry` — start another processing attempt for an
  existing reading. The endpoint returns the new processing job with status
  `202 Accepted`.
