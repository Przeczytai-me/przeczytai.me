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
