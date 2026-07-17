data "aws_caller_identity" "current" {}

locals {
  name_prefix        = "${var.project_slug}-${var.environment}"
  repo_root          = abspath("${path.root}/../../..")
  backend_path       = "${local.repo_root}/backend"
  openai_tts_enabled = var.openai_api_key_secret_arn != ""

  processor_environment_variables = merge(
    {
      ENVIRONMENT         = var.environment
      FILES_BUCKET_NAME   = module.storage.files_bucket_name
      READINGS_TABLE_NAME = module.storage.metadata_table_name
    },
    local.openai_tts_enabled ? { OPENAI_API_KEY_SECRET_ARN = var.openai_api_key_secret_arn } : {}
  )

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

module "lambda_artifact" {
  source = "../../modules/lambda_python_artifact"

  backend_path = local.backend_path
  build_dir    = "${path.root}/.terraform-build/lambda"
  output_path  = "${path.root}/.terraform-build/lambda.zip"
}

module "storage" {
  source = "../../modules/storage"

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

resource "aws_ecr_repository" "processor" {
  name         = "${local.name_prefix}-processor"
  force_delete = true
  tags         = merge(local.common_tags, { Name = "${local.name_prefix}-processor" })
}

module "api_lambda" {
  source = "../../modules/lambda_function"

  function_name    = "${local.name_prefix}-api"
  description      = "FastAPI HTTP API for przeczytai.me dev."
  handler          = "app.main.handler"
  filename         = module.lambda_artifact.filename
  source_code_hash = module.lambda_artifact.output_base64sha256
  timeout          = var.api_lambda_timeout_seconds
  memory_size      = var.api_lambda_memory_size
  tags             = local.common_tags

  environment_variables = {
    ENVIRONMENT             = var.environment
    FILES_BUCKET_NAME       = module.storage.files_bucket_name
    MAX_TEXT_CHARS          = tostring(var.max_text_chars)
    OPENAI_TTS_ENABLED      = tostring(local.openai_tts_enabled)
    PROCESSOR_FUNCTION_NAME = module.processor_lambda.function_name
    READINGS_TABLE_NAME     = module.storage.metadata_table_name
  }

  policy_statements = [
    {
      sid = "MetadataTableAccess"
      actions = [
        "dynamodb:DeleteItem",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem",
      ]
      resources = [module.storage.metadata_table_arn]
    },
    {
      sid       = "InvokeProcessor"
      actions   = ["lambda:InvokeFunction"]
      resources = [module.processor_lambda.function_arn]
    },
    {
      sid = "FileObjectAccess"
      actions = [
        "s3:DeleteObject",
        "s3:GetObject",
        "s3:PutObject",
      ]
      resources = ["${module.storage.files_bucket_arn}/*"]
    },
  ]
}

module "processor_lambda" {
  source = "../../modules/lambda_function"

  function_name = "${local.name_prefix}-processor"
  description   = "Reading audio processor for przeczytai.me dev."
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.processor.repository_url}:${var.processor_image_tag}"
  timeout       = var.processor_lambda_timeout_seconds
  memory_size   = var.processor_lambda_memory_size
  tags          = local.common_tags

  environment_variables = local.processor_environment_variables

  policy_statements = concat([
    {
      sid = "MetadataTableAccess"
      actions = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem",
      ]
      resources = [module.storage.metadata_table_arn]
    },
    {
      sid = "FileObjectAccess"
      actions = [
        "s3:DeleteObject",
        "s3:GetObject",
        "s3:PutObject",
      ]
      resources = ["${module.storage.files_bucket_arn}/*"]
    },
    ], local.openai_tts_enabled ? [
    {
      sid       = "ReadOpenaiApiKeySecret"
      actions   = ["secretsmanager:GetSecretValue"]
      resources = [var.openai_api_key_secret_arn]
    },
  ] : [])
}

resource "aws_lambda_function_event_invoke_config" "processor" {
  function_name                = module.processor_lambda.function_name
  maximum_event_age_in_seconds = 3600
  maximum_retry_attempts       = 0
}

module "http_api" {
  source = "../../modules/http_api"

  api_name             = "${local.name_prefix}-api"
  lambda_function_name = module.api_lambda.function_name
  lambda_invoke_arn    = module.api_lambda.invoke_arn
  allowed_origins      = var.allowed_origins
  clerk_jwt_issuer     = var.clerk_jwt_issuer
  clerk_jwt_audience   = var.clerk_jwt_audience
  tags                 = local.common_tags
}

module "budget" {
  source = "../../modules/budget"

  account_id                   = data.aws_caller_identity.current.account_id
  name                         = "${local.name_prefix}-budget"
  limit_amount_usd             = var.budget_limit_usd
  subscriber_email_addresses   = var.budget_subscriber_email_addresses
  notification_thresholds      = [50, 80, 95]
  project_tag_key              = "Project"
  project_tag_value            = var.project_name
  filter_by_project_tag        = true
  activate_cost_allocation_tag = var.activate_project_cost_allocation_tag
  tags                         = local.common_tags
}
