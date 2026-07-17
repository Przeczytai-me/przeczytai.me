# Reading statuses

Persisted in DynamoDB and returned verbatim by `GET /api/v1/readings` and
`GET /api/v1/readings/{id}`. Older readings may still carry the legacy
`processing` status; treat it like `normalizing`.

| Status | Meaning | Suggested UI label (PL) | Terminal |
|---|---|---|---|
| `uploaded` | Text stored, processing not started yet | Przesłano | no |
| `normalizing` | Cleaning/normalizing the text | Przetwarzanie tekstu | no |
| `generating_audio` | Synthesizing audio chunks | Generowanie audio | no |
| `merging_audio` | Merging chunks and uploading the recording | Scalanie nagrania | no |
| `completed` | Recording and corrected text ready | Gotowe | yes |
| `failed` | A stage failed; `metadata.failed_stage` and `metadata.error` say where/why | Błąd przetwarzania | yes |
| `failed_to_start` | Processor invocation could not be started | Błąd uruchomienia | yes |
