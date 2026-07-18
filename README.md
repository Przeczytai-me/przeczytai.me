# przeczytai.me

Text-to-speech web app for the Polish language. Paste or type any Polish text and have it read aloud.

## Project structure

```
/
├── frontend/       # Customer-facing Next.js app
├── backend/        # Python API implementation and tests
├── infrastructure/ # Deployment and cloud infrastructure code
├── docs/           # Architecture notes and integration contracts
└── tests/          # Repository-level integration tests
```

## Running locally

**Prerequisites:** Node.js 18+, pnpm

```bash
# 1. Clone the repo
git clone https://github.com/szmydlo98/przeczytai.me.git
cd przeczytai.me/frontend

# 2. Install dependencies
pnpm install

# 3. Start the dev server
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

### Frontend API mocks

Set `NEXT_PUBLIC_API_MOCKING=true` in `frontend/.env.local` to enable the
development-only Mock Service Worker layer. Existing health and readings API
routes continue to use the real backend. Missing jobs, retry, original-text,
timing-map, settings, and TTS-options routes are mocked in the browser.

The mocked `POST /api/v1/readings` contract accepts optional document-level
abbreviation readings and forwards the currently supported fields to the real
endpoint:

```json
{
  "original_text": "Np. Ala ma kota.",
  "voice": "Zofia",
  "abbreviation_readings": [
    { "abbreviation": "Np.", "read_as": "Na przykład" }
  ]
}
```
