output "state_bucket_name" {
  value = module.backend_state.bucket_name
}

output "terraform_principal_arns" {
  value = module.backend_state.terraform_principal_arns
}

output "github_actions_deploy_role_arn" {
  value = module.github_actions_deploy.role_arn
}

output "github_actions_oidc_provider_arn" {
  value = module.github_actions_deploy.oidc_provider_arn
}
