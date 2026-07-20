variable "aws_account_id" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "project_slug" {
  type = string
}

variable "environment" {
  type = string
}

variable "github_repository" {
  type        = string
  description = "GitHub repository in owner/name form. Use the immutable owner@id/name@id form if enabled for this repository."

  validation {
    condition     = can(regex("^[^/]+/[^/]+$", var.github_repository))
    error_message = "github_repository must be in owner/name form."
  }
}

variable "deployment_tag_pattern" {
  type    = string
  default = "v*"
}

variable "role_name" {
  type = string
}

variable "state_bucket_arn" {
  type = string
}

variable "create_oidc_provider" {
  type        = bool
  default     = true
  description = "Set false when token.actions.githubusercontent.com is already registered in this AWS account."
}

variable "tags" {
  type    = map(string)
  default = {}
}
