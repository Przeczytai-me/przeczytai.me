# Backend cost model

The cost model is observability for money, not billing. It estimates the cost of
completed processing runs so operators can see cost drivers and apply a coarse
per-run guardrail. The figures are not customer charges and are not reconciled
with vendor invoices.

Monetary cost data is stored in DynamoDB and deliberately excluded from the
user-facing reading response model. It is available through the admin-only
`GET /api/v1/costs` and `POST /api/v1/costs/estimate` endpoints. The internal
dashboard is at `/app/costs`; it is absent from application navigation, and it
renders authentication or authorization failures as not found.

No cost-related data appears in a reading response. The top-level
`cost_usd_micros`, `cost_components`, `cost_usage` and `price_book_version`
attributes are never serialized, and the reading serializer recursively strips
any key containing `cost` or `price_book` from the generic `metadata` dict
before returning it - including nested objects and lists. That filter exists
because the processor once did copy `cost_usage` into `metadata`, which the
serializer returned verbatim; enforcing it at the boundary means a careless
write cannot reopen the leak.

## Calculation

Every component is calculated in USD and independently converted to integer
microdollars with `_usd_micros(value) = round(value * 1_000_000)`. The total is
the sum of the five rounded components. `compute_ms` is the sum of all values in
`compute_ms_by_stage`.

| Component | Formula before conversion to microdollars |
|---|---|
| TTS | `chars_synthesized / 1_000_000 * prices.get("tts.<vendor>", prices["tts.default"])` |
| LLM | `llm_input_tokens / 1_000_000 * prices["llm.input"] + llm_output_tokens / 1_000_000 * prices["llm.output"]` |
| Compute | `lambda_memory_mb / 1024 * compute_ms / 1000 * prices["lambda.gb_second"] + prices["lambda.request"]` |
| Storage | `stored_bytes / 1_000_000_000 * prices["s3.gb_month"] + 4 / 1000 * prices["s3.per_1k_put"]` |
| Platform | `prices["platform.per_run"]` |

The storage formula models one month of stored bytes and a flat four PUTs -
original text, corrected text, timing map and merged recording. Chunk mp3s are
written to `/tmp` and never uploaded, so PUTs do not scale with chunk count. The
platform component is a flat allowance for DynamoDB and API Gateway activity.

### Worked example

This is the hand-calculated fixture from `backend/tests/test_costs.py`. It is a
formula example, not an input that the current API limits would accept.

Usage: 2,000,000 synthesized characters, 996 chunks, 120,000 ms of audio,
1,000,000,000 stored bytes, 1,024 MB Lambda memory, and 60,000 ms of compute
(`10,000 + 20,000 + 30,000`). LLM usage is 1,000,000 input tokens and 2,000,000
output tokens; the vendor is OpenAI.

| Component | Hand calculation | Result |
|---|---|---:|
| TTS | `2,000,000 / 1,000,000 * $15` | $30.000000 |
| LLM | `1,000,000 / 1,000,000 * $3 + 2,000,000 / 1,000,000 * $15` | $33.000000 |
| Compute | `1,024 / 1,024 * 60,000 / 1,000 * $0.0000166667 + $0.0000002` | $0.001000202, rounded to $0.001000 |
| Storage | `1,000,000,000 / 1,000,000,000 * $0.023 + 4 / 1,000 * $0.005` | $0.023020 |
| Platform | `$0.00001` | $0.000010 |
| Total | Sum of the rounded components | **$63.024030** (`63,024,030` microdollars) |

## Pre-run estimate and post-run cost

The API builds a pre-run `RunUsage` from the submitted text. The processor
builds a post-run `RunUsage` after the recording has been generated and
uploaded. Both paths then use the same five formulas.

| `RunUsage` field | Pre-run estimate | Post-run cost |
|---|---|---|
| `chars_synthesized` | `len()` of the text after abbreviation substitutions and normalization - the same deterministic transforms the processor applies, so expansion cannot smuggle a large run past the cap | `len(corrected)` after normalization and abbreviation substitutions |
| `chunks` | Actual result of `split_text()` on that transformed text | Actual result of splitting the corrected text |
| `audio_ms` | `round(len(text) / 900 * 60_000)` | Duration from the generated timing map |
| `stored_bytes` | Twice the original UTF-8 byte length, plus estimated audio bytes at 48,000 bit/s | Sum of UTF-8 bytes for original text, corrected text, and timing-map JSON, plus merged recording bytes |
| `compute_ms_by_stage` | `{"estimated": lambda_timeout_ms}` | Rounded wall-clock milliseconds for `normalize`, `synthesize` and `merge`, plus an `overhead` stage covering the rest of the invocation (S3 transfers, status writes, splitting) so billed time is not recorded as free |
| `lambda_memory_mb` | `LAMBDA_MEMORY_MB` | `AWS_LAMBDA_FUNCTION_MEMORY_SIZE`, falling back to `LAMBDA_MEMORY_MB` |
| `vendor` | Resolved request vendor | Resolved processor vendor |
| `llm_input_tokens` | `0` | `0`; token usage is not captured yet |
| `llm_output_tokens` | `0` | `0`; token usage is not captured yet |

The pre-run compute duration is pinned to the full Lambda timeout. Runtime is
the only estimate input for which choosing the configured maximum guarantees
the figure cannot be too low. This is intentionally conservative, and compute
is a rounding error against the per-run cap either way.

The two material guesses are audio duration, based on 900 characters per
minute, and stored recording size, based on 48 kbit/s. For a paid vendor the
great majority of the cost is TTS, which is linear in character count. Character
count is known exactly before the run, so changing the assumed speech rate has
little effect on the estimate.

Post-run costing is resilient by design. A cost-calculation failure does not
fail an otherwise completed reading. If saving a completed reading with cost
attributes fails, the processor retries completion without those attributes.
A rollup failure is logged but also does not fail the reading.

## Price book

Price book version: `2026-08-05`.

**Every entry in this table is unverified. Verify vendor prices before using
these estimates for a decision.**

| Key | Value | Unit | Derivation |
|---|---:|---|---|
| `tts.edge-tts` | 0.0 | USD per 1 million characters | Edge TTS exposes no usage price. It is an unofficial free endpoint with no contract or SLA; if that changes, every historical zero-TTS figure becomes wrong. |
| `tts.openai` | 15.0 | USD per 1 million characters | Weakest entry in the book. It was estimated from $0.015 per audio minute and 900 characters per minute. That derivation implies about $16.67 per million characters, not the stored $15.00. |
| `tts.default` | 15.0 | USD per 1 million characters | Fallback for an unknown vendor, copied from the OpenAI estimate. |
| `llm.input` | 3.0 | USD per 1 million input tokens | Representative OpenAI input-token price. |
| `llm.output` | 15.0 | USD per 1 million output tokens | Representative OpenAI output-token price. |
| `lambda.gb_second` | 0.0000166667 | USD per GB-second | AWS Lambda public x86 duration rate. |
| `lambda.request` | 0.0000002 | USD per request | AWS Lambda public request rate. |
| `s3.gb_month` | 0.023 | USD per GB-month | AWS S3 Standard public storage rate. |
| `s3.per_1k_put` | 0.005 | USD per 1,000 PUTs | AWS S3 Standard public PUT rate. |
| `platform.per_run` | 0.00001 | USD per run | Internal flat allowance for platform activity. |

## Updating a price

For an API-side hotfix, set `COST_PRICE_OVERRIDES` to a JSON object containing
recognized price-book keys, for example:

```json
{"tts.openai": 16.7, "s3.gb_month": 0.024}
```

Unknown keys are ignored. Invalid JSON or a non-object value causes the entire
override to be ignored and defaults to be used. Individual values that are not
finite numbers, or are negative, are skipped and fall back to that key's
default while valid siblings in the same object still apply - a `NaN` would
otherwise raise inside the estimator and turn every reading creation into a 500.

The override applies everywhere a cost is computed: the estimate endpoint, the
pre-run creation guardrail and the processor's stored post-run cost. A hotfix
therefore changes both what is blocked and what is recorded.

For a permanent change, edit `DEFAULT_PRICES` in `backend/app/pricing.py` and
bump `PRICE_BOOK_VERSION` in the same change. Per-reading and per-run records
retain the version that produced them, so changing the book never silently
rewrites history. Monthly and per-user rollups are additive counters and do not
carry a version; one rollup can therefore combine runs from different versions.

## Known omissions and biases

- Post-run compute timing starts inside the processor. Lambda cold start and
  initialization are excluded, so recorded compute cost runs low.
- Storage is charged once as one GB-month at run time. Retained data continues
  to accrue storage cost each month, but the model does not add that recurring
  cost.
- DynamoDB and API Gateway are represented by the flat
  `platform.per_run` constant rather than counted per operation.
- Each successful retry is another paid run and increments both aggregate
  rollups again. A failed attempt never reaches cost capture, so any vendor or
  infrastructure spend before that failure is absent from the model.
- LLM token counts remain zero even when AI normalization is enabled. Enabling
  a billable implementation without usage capture would make the LLM component
  run low.

## DynamoDB layout

All dollar amounts are stored as integer USD microdollars.

The reading item remains under `pk=USER#<user_id>`,
`sk=READING#<reading_id>` and receives these attributes on successful cost
persistence:

| Attribute | Contents |
|---|---|
| `cost_usd_micros` | Total of the five components |
| `cost_components` | `tts_usd_micros`, `llm_usd_micros`, `compute_usd_micros`, `storage_usd_micros`, and `platform_usd_micros` |
| `cost_usage` | Full serialized `RunUsage` |
| `price_book_version` | Version used for the calculation |

`add_cost_rollup()` makes three writes in the shared `SYSTEM` partition:

| Sort-key family | Write | Purpose |
|---|---|---|
| `COST#<YYYY-MM>` | Atomic add | System monthly totals for cost components, characters, audio duration, and run count |
| `COSTUSER#<YYYY-MM>#<user_id>` | Atomic add | The same counters for one user and month |
| `COSTRUN#<YYYY-MM>#<run_key>` | Conditional put, written first | Reading, user, vendor, voice, component, usage, price-version and timestamp detail for the dashboard |

The run record is written **first**, under a deterministic `run_key` (the job
id, or the reading id when there is none) and guarded by
`attribute_not_exists(sk)`. If the record already exists the call returns
before touching either counter, so a duplicate Lambda delivery of the same run
cannot double-count the month.

**Known limitation:** the three writes are idempotent but not transactional as
a group. If a counter update fails after the run record is claimed, a later
replay returns early and the monthly totals stay short by that run. The failure
is logged. Making this exact would require `TransactWriteItems` with manual
attribute-value serialization; that was judged not worth the complexity for an
internal estimate dashboard, and is the first thing to change if the aggregates
ever need to be authoritative.

The per-run item is necessary because `ReadingRepository.list()` queries only
`pk=USER#<user_id>`. It can return one user's readings, but cannot support an
all-users dashboard without a DynamoDB Scan. The separate `COSTRUN#` family is
queryable by sort-key prefix and preserves every successful retry as a distinct
run.

Putting all rollups under `pk=SYSTEM` creates a known hot-partition trade-off.
It is acceptable at the current write volume. If volume grows, add a GSI for
the dashboard access patterns or shard the partition key by month.

## Guardrails for frontend clients

The cost API requires a valid user and membership in the comma-separated
`ADMIN_USER_IDS` setting. Missing API Gateway JWT claims return HTTP `401` with
code `unauthorized`. A non-admin, including every user when `ADMIN_USER_IDS` is
empty, receives HTTP `403` with code `forbidden`.

| Limit | Create-reading behavior | Estimate behavior |
|---|---|---|
| `MAX_TEXT_CHARS` (default `100000`) | Blocks `POST /api/v1/readings` with HTTP `413`, code `payload_too_large` | HTTP `200`; each vendor is marked `allowed: false` with rejection code `payload_too_large` |
| Provider input cap (OpenAI: `4096` characters) | Blocks with HTTP `413`, code `payload_too_large` | HTTP `200`; that vendor is marked `allowed: false` with rejection code `payload_too_large` |
| `MAX_RUN_COST_USD` (default `$0.25`) | Blocks before any S3, DynamoDB, or Lambda write with HTTP `413`, code `cost_limit_exceeded` | HTTP `200`; that vendor is marked `allowed: false` with rejection code `cost_limit_exceeded` |
| `MONTHLY_BUDGET_USD` (default unset) | Does not block | Dashboard warning and utilization only; thresholds are 50%, 80%, and 95% |

The estimate endpoint reports only the first applicable rejection in this
order: global character limit, provider character limit, then per-run cost.
The create guardrail rejects only when estimated cost is strictly greater than
the cap. `POST /api/v1/readings/{id}/retry` runs the same guardrail before
claiming the retry, creating a job or invoking the processor. It reads the
stored original text to do so; if that read fails the retry returns HTTP `500`
`storage_error` rather than proceeding, so a transient storage failure cannot
bypass the cap.

A retry is charged the same four PUTs and the same original-text bytes as a
first run, even though the original object already exists and is not
re-uploaded. This slightly overstates retry cost and is a known simplification.

With the current defaults, the highest-cost accepted OpenAI input is 4,096
characters and estimates to about $0.064. The `$0.25` cap is therefore a
backstop against future changes, not a limit expected to fire today. Relevant
changes include raising `MAX_TEXT_CHARS`, lifting OpenAI's 4,096-character cap,
adding a more expensive vendor, or enabling billable LLM normalization.

## Processor capacity

The processor Lambda timeout was raised from 30 seconds to 10 minutes (`600`
seconds), matched by the `LAMBDA_TIMEOUT_MS` default of `600000` used for
pre-run estimates. Longer documents can now finish instead of being cut off by
the earlier timeout.

The next likely constraint is peak memory. The processor Lambda remains at
256 MB, and after merging the chunk files it reads the entire recording into
memory with `recording_path.read_bytes()` before uploading it.
