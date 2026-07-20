data "aws_caller_identity" "current" {}

locals {
  state_bucket_name       = "${var.project_slug}-tfstate-${var.aws_account_id}-${var.aws_region}"
  github_deploy_role_name = "${var.project_slug}-github-deploy-dev"
  github_deploy_role_arn  = "arn:aws:iam::${var.aws_account_id}:role/${local.github_deploy_role_name}"

  common_tags = {
    Project     = var.project_name
    Environment = "bootstrap"
    ManagedBy   = "terraform"
  }
}

module "backend_state" {
  source = "../../modules/backend_state"

  bucket_name = local.state_bucket_name
  terraform_principal_arns = distinct(concat(
    length(var.terraform_principal_arns) > 0 ? var.terraform_principal_arns : [data.aws_caller_identity.current.arn],
    [local.github_deploy_role_arn],
  ))
  tags = local.common_tags
}

module "github_actions_deploy" {
  source = "../../modules/github_actions_deploy"

  aws_account_id       = var.aws_account_id
  aws_region           = var.aws_region
  project_slug         = var.project_slug
  environment          = "dev"
  github_repository    = var.github_repository
  role_name            = local.github_deploy_role_name
  state_bucket_arn     = module.backend_state.bucket_arn
  create_oidc_provider = var.create_github_oidc_provider
  tags                 = local.common_tags
}
