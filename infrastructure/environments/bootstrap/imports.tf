# The state bucket predates remote state for this bootstrap stack. These import
# blocks make the migration repeatable and are no-ops after the resources are in
# state.
import {
  to = module.backend_state.aws_s3_bucket.state
  id = "przeczytai-me-tfstate-638175212741-eu-west-1"
}

import {
  to = module.backend_state.aws_s3_bucket_public_access_block.state
  id = "przeczytai-me-tfstate-638175212741-eu-west-1"
}

import {
  to = module.backend_state.aws_s3_bucket_versioning.state
  id = "przeczytai-me-tfstate-638175212741-eu-west-1"
}

import {
  to = module.backend_state.aws_s3_bucket_server_side_encryption_configuration.state
  id = "przeczytai-me-tfstate-638175212741-eu-west-1"
}

import {
  to = module.backend_state.aws_s3_bucket_policy.state
  id = "przeczytai-me-tfstate-638175212741-eu-west-1"
}
