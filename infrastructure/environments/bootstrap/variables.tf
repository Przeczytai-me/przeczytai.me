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

variable "terraform_principal_arns" {
  type    = list(string)
  default = []
}

variable "github_repository" {
  type        = string
  default     = "Przeczytai-me/przeczytai.me"
  description = "Repository allowed to assume the deploy role from v* tag workflows."
}

variable "create_github_oidc_provider" {
  type        = bool
  default     = true
  description = "Set false when this AWS account already has the GitHub Actions OIDC provider."
}
