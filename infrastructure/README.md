# AWS infrastructure and backend deployment

This directory contains the AWS infrastructure for `przeczytai.me`. The dev
backend is deployed automatically by GitHub Actions when a tag matching `v*`
is pushed. Jobs run on Blacksmith runners and authenticate to AWS with GitHub
OIDC, so no permanent AWS access keys are stored in GitHub.

## What is in the repository

- `environments/bootstrap/` manages the Terraform state bucket, GitHub OIDC
  provider, and the tag-restricted GitHub Actions deploy role.
- `environments/dev/` manages the API Lambda, processor Lambda and ECR
  repository, API Gateway, DynamoDB table, file bucket, logs, and budget.
- `modules/github_actions_deploy/` contains the deploy role's trust and scoped
  AWS permissions.
- `.github/workflows/backend-ci.yml` runs backend lint and unit tests on
  Blacksmith for relevant pull requests and pushes to `main`.
- `.github/workflows/backend-deploy.yml` tests, builds, applies Terraform, and
  smoke-tests the backend for every `v*` tag.

Non-secret dev values are committed in
`environments/dev/deployment.auto.tfvars`. The OpenAI key itself remains in
AWS Secrets Manager; only its ARN is committed.

## One-time setup

Complete these steps once, in order.

### 1. Verify Blacksmith for the repository

The `blacksmith-sh` GitHub App is already active for all repositories in the
`Przeczytai-me` organization. Follow the
[Blacksmith quickstart](https://docs.blacksmith.sh/introduction/quickstart),
sign in at [app.blacksmith.sh](https://app.blacksmith.sh/) with GitHub, and
confirm that `Przeczytai-me/przeczytai.me` is visible. Complete the Blacksmith
billing/trial setup if prompted.

The workflows already use these runner labels:

- `blacksmith-2vcpu-ubuntu-2404` for lint and tests;
- `blacksmith-4vcpu-ubuntu-2404` for Docker builds and deployment.

No Blacksmith token or GitHub secret is required. Blacksmith provisions an
ephemeral runner when GitHub queues a job with one of those labels. If a job
stays queued with “Waiting for a runner”, verify that the Blacksmith GitHub App
has access to this repository.

### 2. Create the AWS OIDC provider and deploy role

Use the AWS identity that currently manages the state bucket
(`arn:aws:iam::638175212741:user/przeczyt-ai-janek`) and run:

```bash
terraform -chdir=infrastructure/environments/bootstrap init -reconfigure
terraform -chdir=infrastructure/environments/bootstrap plan
terraform -chdir=infrastructure/environments/bootstrap apply
```

Review the plan before approving it. The first apply will:

- import the existing state bucket into durable S3-backed bootstrap state;
- register `token.actions.githubusercontent.com` as an AWS OIDC provider;
- create `przeczytai-me-github-deploy-dev`;
- allow that role to access the dev Terraform state;
- restrict role assumption to `v*` tags from
  `Przeczytai-me/przeczytai.me`.

The GitHub OIDC provider is an account-wide resource. This AWS account does not
currently have one. If one is added by another stack before these commands are
run, use:

```bash
terraform -chdir=infrastructure/environments/bootstrap apply \
  -var='create_github_oidc_provider=false'
```

Keep that variable set on later bootstrap applies as well.

Check the resulting role if needed:

```bash
terraform -chdir=infrastructure/environments/bootstrap output github_actions_deploy_role_arn
```

There are no AWS credentials, GitHub repository secrets, or GitHub repository
variables to configure for deployment. The non-secret account, region, role
ARN, ECR URL, and dev application settings are version-controlled.
GitHub's [AWS OIDC guide](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws)
explains the short-lived credential exchange used by the workflow.

### 3. Protect deployment tags

Anyone who can create a matching tag can start a deployment. In GitHub, open
**Settings → Rules → Rulesets**, create an active **tag ruleset** targeting
`v*`, and enable **Restrict creations**, **Restrict updates**, and **Restrict
deletions**. Give bypass permission only to the repository administrators or
release team who should be able to deploy. See GitHub's
[ruleset guide](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository).

### 4. Run CI once

Open or update a pull request that changes `backend/`, `infrastructure/`, or a
backend workflow. Confirm that the **Backend CI / Lint and unit tests** check is
green. This verifies the Blacksmith integration before the first deployment.

## Deploying a backend release

Create an annotated version tag pointing to the commit or branch to deploy,
then push only that tag. The target does not need to be `main`.

Deploy the currently checked-out branch:

```bash
git tag -a v0.1.0 -m "Deploy backend v0.1.0"
git push origin v0.1.0
```

Deploy another branch or a specific commit without switching branches:

```bash
git tag -a v0.1.0 feature/my-backend-change -m "Deploy backend v0.1.0"
git push origin v0.1.0

# Or use a commit SHA:
git tag -a v0.1.1 <commit-sha> -m "Deploy backend v0.1.1"
git push origin v0.1.1
```

The tag triggers this sequence:

1. lint and unit tests on a 2-vCPU Blacksmith runner;
2. short-lived AWS credentials obtained through GitHub OIDC;
3. Terraform initialization and validation;
4. processor image build with Blacksmith's Docker layer cache and push to ECR;
5. automatic Terraform apply, including the API Lambda zip;
6. retries against the public `/api/v1/health` endpoint;
7. a deployment summary in the GitHub Actions run.

Tags pushed with Git trigger the workflow from the tagged commit. Releases
published in the GitHub browser trigger the workflow from the default branch.
In both cases the workflow checks out and deploys the commit referenced by the
`v*` tag, so browser releases can deploy a commit from any branch even when
that commit does not contain the workflow file. Creating an ordinary branch,
pushing a branch, saving a draft release, or opening a pull request never
deploys. Deployments are serialized, so two deployments cannot apply the same
Terraform state concurrently.

### Watch a deployment

Open the repository's GitHub **Actions** tab and select **Deploy backend to
dev**. A successful run shows the tag, commit, processor image, and API URL in
its summary.

### Roll back

Tag the previous known-good commit with a new version and push that tag. Tags
should not be moved or reused.

```bash
git tag -a v0.1.1 <known-good-commit> -m "Rollback backend to known-good commit"
git push origin v0.1.1
```

The workflow rebuilds that commit and reapplies it. Terraform does not
automatically roll back an apply when the post-deploy health check fails.

## Manual dev operations

The committed `deployment.auto.tfvars` is loaded automatically:

```bash
terraform -chdir=infrastructure/environments/dev init
terraform -chdir=infrastructure/environments/dev plan
terraform -chdir=infrastructure/environments/dev apply
```

The processor Lambda is an ECR image. For a fully manual first deployment:

```bash
terraform -chdir=infrastructure/environments/dev apply \
  -target=aws_ecr_repository.processor
backend/scripts/build-push-processor-image.sh
terraform -chdir=infrastructure/environments/dev apply
```

The manual image script writes an ignored `processor.auto.tfvars.json`. The CI
workflow does not write repository files; it passes the immutable commit-based
image tag through `TF_VAR_processor_image_tag`.

## Authentication and integration tests

API Gateway protects application endpoints with a Clerk JWT authorizer. Docs
and health checks remain public at `/docs`, `/redoc`, `/openapi.json`, and
`/api/v1/health`. The frontend must request a token from the matching Clerk JWT
template and send `Authorization: Bearer <token>`.

For live API Gateway tests, copy the ignored test environment and use a
dedicated user in the development Clerk instance:

```bash
cp tests/api_gateway/.env.example tests/api_gateway/.env
backend/.venv/bin/python -m pytest tests/api_gateway -q -rs
```

Set `CLERK_SECRET_KEY` and `CLERK_TEST_USER_ID` in that `.env` file. The tests
create a temporary session and revoke it after the run. Do not use a production
Clerk key or a real user's ID.

OpenAI TTS is enabled by `openai_api_key_secret_arn`. The referenced Secrets
Manager value may be the raw key or JSON containing `OPENAI_API_KEY`,
`openai_api_key`, or `api_key`.

## Validation

Run all local checks with:

```bash
terraform fmt -check -recursive infrastructure
terraform -chdir=infrastructure/environments/bootstrap init -reconfigure
terraform -chdir=infrastructure/environments/bootstrap validate
terraform -chdir=infrastructure/environments/dev init
terraform -chdir=infrastructure/environments/dev validate
backend/.venv/bin/ruff check backend
backend/.venv/bin/python -m pytest backend/tests -q
```

`terraform validate` does not change AWS resources. `terraform init` may create
an S3 lock object briefly while accessing remote state.
