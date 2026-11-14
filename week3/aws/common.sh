#!/usr/bin/env bash
# Shared settings for the AWS scripts. Source this file, do not run it.
set -euo pipefail

# Git Bash on Windows rewrites paths that start with a slash; turn that off.
export MSYS_NO_PATHCONV=1
export AWS_PAGER=""

REGION="ap-south-1"
export AWS_DEFAULT_REGION="$REGION"

PREFIX="irctc"
PROJECT_TAG="irctc-it457"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
ECR_REPO="${PREFIX}-api"
ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
ECR_URI="${ECR_REGISTRY}/${ECR_REPO}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

INSTANCE_TYPE="${INSTANCE_TYPE:-t3.small}"
DB_CLASS="${DB_CLASS:-db.t3.medium}"
DB_NAME="irctc"
DB_USER="irctc_user"
DB_ID="${PREFIX}-db"
DB_SUBNET_GROUP="${PREFIX}-db-subnets"

ALB_SG_NAME="${PREFIX}-alb-sg"
APP_SG_NAME="${PREFIX}-app-sg"
DB_SG_NAME="${PREFIX}-db-sg"
ROLE_NAME="${PREFIX}-ec2-role"
PROFILE_NAME="${PREFIX}-ec2-profile"
LT_NAME="${PREFIX}-lt"
TG_NAME="${PREFIX}-tg"
ALB_NAME="${PREFIX}-alb"
ASG_NAME="${PREFIX}-asg"

ASG_MIN="${ASG_MIN:-1}"
ASG_MAX="${ASG_MAX:-6}"
CPU_TARGET="${CPU_TARGET:-50}"
# Each uvicorn worker has its own pool, so connections per instance =
# UVICORN_WORKERS x DB_POOL_MAX_SIZE. Keep instances x that below the RDS limit.
UVICORN_WORKERS="${UVICORN_WORKERS:-2}"
DB_POOL_MAX_SIZE="${DB_POOL_MAX_SIZE:-8}"
ADMISSION_LIMIT="${ADMISSION_LIMIT:-0}"   # 0 = load shedding off (see experiment R5)

AWS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_DIR="${AWS_DIR}/.tmp"
SECRET_FILE="${AWS_DIR}/.env.aws"   # git-ignored; holds the database password
mkdir -p "$TMP_DIR"
# aws.exe is a Windows program and needs Windows-style paths for file:// arguments.
TMP_WIN="$(cygpath -m "$TMP_DIR" 2>/dev/null || echo "$TMP_DIR")"

VPC_ID="$(aws ec2 describe-vpcs --filters Name=is-default,Values=true \
  --query 'Vpcs[0].VpcId' --output text)"
SUBNET_IDS="$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=${VPC_ID}" Name=default-for-az,Values=true \
  --query 'Subnets[].SubnetId' --output text)"

sg_id() {
  # Prints the id of a security group by name, or nothing if it is missing.
  aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$1" "Name=vpc-id,Values=${VPC_ID}" \
    --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null | sed 's/^None$//'
}

log() { printf '\n==> %s\n' "$*"; }
