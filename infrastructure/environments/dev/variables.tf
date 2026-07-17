variable "aws_account_id" {
  type    = string
  default = "638175212741"
}

variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

variable "project_name" {
  type    = string
  default = "przeczytai.me"
}

variable "project_slug" {
  type    = string
  default = "przeczytai-me"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "allowed_origins" {
  type    = list(string)
  default = ["http://localhost:3000"]
}

variable "max_text_chars" {
  type    = number
  default = 100000
}

variable "api_lambda_timeout_seconds" {
  type    = number
  default = 20
}

variable "api_lambda_memory_size" {
  type    = number
  default = 256
}

variable "processor_lambda_timeout_seconds" {
  type    = number
  default = 30
}

variable "processor_lambda_memory_size" {
  type    = number
  default = 256
}

variable "processor_image_tag" {
  type    = string
  default = "latest"
}

variable "openai_api_key_secret_arn" {
  type        = string
  default     = ""
  description = "Secrets Manager secret ARN containing the OpenAI API key for processor TTS."
}

variable "clerk_jwt_issuer" {
  type        = string
  description = "Clerk issuer URL for API Gateway JWT authorizer validation."
}

variable "clerk_jwt_audience" {
  type        = string
  description = "Audience claim expected in Clerk JWTs accepted by the API."
}

variable "budget_limit_usd" {
  type    = number
  default = 8
}

variable "budget_subscriber_email_addresses" {
  type    = set(string)
  default = ["leski.jn@gmail.com"]
}

variable "activate_project_cost_allocation_tag" {
  type    = bool
  default = true
}
