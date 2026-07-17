#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../.." && pwd)
AWS_REGION=${AWS_REGION:-eu-west-1}
TF_DIR="$REPO_ROOT/infrastructure/environments/dev"

cd "$REPO_ROOT"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPOSITORY_URL=$(terraform -chdir="$TF_DIR" output -raw processor_ecr_repository_url)
REGISTRY="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

IMAGE_HASH=$(
  {
    sha256sum backend/Dockerfile.processor backend/pyproject.toml
    find backend/app -type f -name "*.py" -print0 | sort -z | xargs -0 sha256sum
  } | sha256sum | cut -c1-12
)
IMAGE_TAG="processor-${IMAGE_HASH}"
IMAGE_URI="${REPOSITORY_URL}:${IMAGE_TAG}"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$REGISTRY"

docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -f backend/Dockerfile.processor \
  -t "$IMAGE_URI" \
  --push \
  backend

cat > "$TF_DIR/processor.auto.tfvars.json" <<EOF
{
  "processor_image_tag": "$IMAGE_TAG"
}
EOF

echo "$IMAGE_URI"
