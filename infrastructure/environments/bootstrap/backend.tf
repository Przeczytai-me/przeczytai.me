terraform {
  backend "s3" {
    bucket       = "przeczytai-me-tfstate-638175212741-eu-west-1"
    key          = "environments/bootstrap/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true
    use_lockfile = true
  }
}
