# Terraform

This directory contains the AWS infrastructure for `przeczytai.me`.

## Layout

- `modules/` contains reusable resource modules.
- `environments/bootstrap/` creates the Terraform state S3 bucket. State locking uses the S3 backend lockfile.
- `environments/dev/` creates the dev application stack.

## Bootstrap State

Run bootstrap first with local state:

```bash
terraform -chdir=infrastructure/environments/bootstrap init
terraform -chdir=infrastructure/environments/bootstrap apply
```

Bootstrap creates:

- S3 bucket: `przeczytai-me-tfstate-638175212741-eu-west-1`

By default, the state bucket policy restricts state access to the AWS caller that applies bootstrap. To use a dedicated Terraform role instead, pass `terraform_principal_arns`.

## Dev

Create a local tfvars file from the example:

```bash
cp infrastructure/environments/dev/terraform.tfvars.example infrastructure/environments/dev/terraform.tfvars
terraform -chdir=infrastructure/environments/dev init
terraform -chdir=infrastructure/environments/dev apply
```

The API Gateway protects application endpoints with a Clerk JWT authorizer.
Docs and health checks remain public at `/docs`, `/redoc`, `/openapi.json`,
and `/api/v1/health`. Set the Clerk JWT authorizer values in
`infrastructure/environments/dev/terraform.tfvars`:

```hcl
clerk_jwt_issuer   = "https://fitting-bonefish-84.clerk.accounts.dev"
clerk_jwt_audience = "przeczytai-api-dev"
```

The frontend must request a Clerk JWT from the matching template and send it as
`Authorization: Bearer <token>`.

For repeatable API Gateway tests, create a dedicated user in the development
Clerk instance and copy the example test environment:

```bash
cp tests/api_gateway/.env.example tests/api_gateway/.env
```

Set the development instance's `CLERK_SECRET_KEY` and the dedicated user's
`CLERK_TEST_USER_ID` in `tests/api_gateway/.env`. This file is ignored by Git.
Then run:

```bash
backend/.venv/bin/python -m pytest tests/api_gateway -q -rs
```

`conftest.py` loads `tests/api_gateway/.env` automatically. The test fixture
uses the Clerk Backend API to create a temporary session, generate a short-lived
token from `CLERK_JWT_TEMPLATE`, and revoke the session after the test run.
`CLERK_JWT` remains available as a manual override. Do not use a production
Clerk secret key or a real user's ID for these tests.

The legacy `X-Api-Key` header is intentionally not accepted. If
`X-Api-Key: tatuazyk` can still read `/api/v1/readings`, the deployed API is
still running the old API key authorizer/configuration and the dev Terraform
stack needs to be applied.

OpenAI TTS is enabled only when `openai_api_key_secret_arn` is set. Create the
Secrets Manager secret outside Terraform so the API key does not get written to
Terraform state. The secret value may be the raw API key or JSON containing
`OPENAI_API_KEY`, `openai_api_key`, or `api_key`.

The dev backend stores state at `environments/dev/terraform.tfstate`.

The processor Lambda is deployed from an ECR image. On the first deploy, create
the repository before pushing the image:

```bash
terraform -chdir=infrastructure/environments/dev apply -target=aws_ecr_repository.processor
backend/scripts/build-push-processor-image.sh
terraform -chdir=infrastructure/environments/dev apply
```

## Validation

```bash
terraform -chdir=infrastructure/environments/bootstrap init -backend=false
terraform -chdir=infrastructure/environments/bootstrap validate
terraform -chdir=infrastructure/environments/dev init -backend=false
terraform -chdir=infrastructure/environments/dev validate
```
