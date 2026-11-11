#!/usr/bin/env bash
# Step 2: build the API image from week3/Dockerfile and push it to ECR.
# Needs Docker Desktop running.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

log "Logging in to ${ECR_REGISTRY}"
aws ecr get-login-password | docker login --username AWS --password-stdin "$ECR_REGISTRY"

log "Building the image for linux/amd64 (the instances are x86)"
CONTEXT="${AWS_DIR}/.."
CONTEXT="$(cygpath -m "$CONTEXT" 2>/dev/null || echo "$CONTEXT")"
docker build --platform linux/amd64 -t "${ECR_URI}:${IMAGE_TAG}" "$CONTEXT"

log "Pushing ${ECR_URI}:${IMAGE_TAG}"
docker push "${ECR_URI}:${IMAGE_TAG}"

echo
echo "Next: bash week3/aws/03-app.sh"
