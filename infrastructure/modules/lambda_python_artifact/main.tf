locals {
  app_files          = sort(fileset("${var.backend_path}/app", "**"))
  build_platform     = "linux/amd64"
  lambda_build_image = "public.ecr.aws/lambda/python:3.13"
}

resource "null_resource" "package" {
  triggers = {
    app_hash       = sha256(join("", [for file in local.app_files : filesha256("${var.backend_path}/app/${file}")]))
    pyproject_hash = filesha256("${var.backend_path}/pyproject.toml")
    builder        = "${local.lambda_build_image}-${local.build_platform}-v1"
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command     = <<-EOT
      rm -rf '${var.build_dir}'
      mkdir -p '${var.build_dir}'

      docker run --rm \
        --platform '${local.build_platform}' \
        --entrypoint /bin/bash \
        -v '${var.backend_path}:/src:ro' \
        -v '${var.build_dir}:/asset' \
        '${local.lambda_build_image}' \
        -lc 'cp -R /src /tmp/backend && python -m pip install --no-cache-dir /tmp/backend -t /asset'
    EOT
  }
}

data "archive_file" "package" {
  type        = "zip"
  source_dir  = var.build_dir
  output_path = var.output_path

  depends_on = [null_resource.package]
}
