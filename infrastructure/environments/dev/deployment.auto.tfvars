# Non-secret dev deployment configuration used by local Terraform and CI.
allowed_origins    = ["http://localhost:3000"]
budget_limit_usd   = 8
clerk_jwt_issuer   = "https://fitting-bonefish-84.clerk.accounts.dev"
clerk_jwt_audience = "przeczytai-api-dev"

# Only the secret ARN is stored here. The OpenAI API key value remains in AWS
# Secrets Manager and is never placed in source control or Terraform state.
openai_api_key_secret_arn = "arn:aws:secretsmanager:eu-west-1:638175212741:secret:przeczytai-me/dev/openai-api-key-RQx4HB"
