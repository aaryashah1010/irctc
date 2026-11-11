#!/usr/bin/env bash
# Step 1: ECR repository, security groups, instance role and the RDS database.
# Billing starts when the RDS instance is created (about $0.02 per hour).
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

TAGS="Key=Project,Value=${PROJECT_TAG}"

log "ECR repository ${ECR_REPO}"
if ! aws ecr describe-repositories --repository-names "$ECR_REPO" >/dev/null 2>&1; then
  aws ecr create-repository --repository-name "$ECR_REPO" \
    --tags "$TAGS" --query 'repository.repositoryUri' --output text
else
  echo "already exists"
fi

log "Security groups in ${VPC_ID}"
make_sg() {
  local name="$1" desc="$2" id
  id="$(sg_id "$name")"
  if [ -z "$id" ]; then
    id="$(aws ec2 create-security-group --group-name "$name" --description "$desc" \
      --vpc-id "$VPC_ID" \
      --tag-specifications "ResourceType=security-group,Tags=[{Key=Project,Value=${PROJECT_TAG}},{Key=Name,Value=${name}}]" \
      --query GroupId --output text)"
  fi
  echo "$id"
}
ALB_SG="$(make_sg "$ALB_SG_NAME" "IRCTC load balancer")"
APP_SG="$(make_sg "$APP_SG_NAME" "IRCTC API instances")"
DB_SG="$(make_sg "$DB_SG_NAME" "IRCTC database")"
echo "alb=${ALB_SG} app=${APP_SG} db=${DB_SG}"

# internet -> ALB:80, ALB -> app:8000, app -> database:5432 (duplicates are fine)
aws ec2 authorize-security-group-ingress --group-id "$ALB_SG" \
  --protocol tcp --port 80 --cidr 0.0.0.0/0 >/dev/null 2>&1 || true
aws ec2 authorize-security-group-ingress --group-id "$APP_SG" \
  --protocol tcp --port 8000 --source-group "$ALB_SG" >/dev/null 2>&1 || true
aws ec2 authorize-security-group-ingress --group-id "$DB_SG" \
  --protocol tcp --port 5432 --source-group "$APP_SG" >/dev/null 2>&1 || true

log "Instance role ${ROLE_NAME} (pull from ECR, Session Manager access)"
if ! aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  cat > "${TMP_DIR}/trust.json" <<'EOF'
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}
EOF
  aws iam create-role --role-name "$ROLE_NAME" \
    --assume-role-policy-document "file://${TMP_WIN}/trust.json" \
    --tags "$TAGS" --query 'Role.RoleName' --output text
  aws iam attach-role-policy --role-name "$ROLE_NAME" \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
  aws iam attach-role-policy --role-name "$ROLE_NAME" \
    --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
fi
if ! aws iam get-instance-profile --instance-profile-name "$PROFILE_NAME" >/dev/null 2>&1; then
  aws iam create-instance-profile --instance-profile-name "$PROFILE_NAME" >/dev/null
  aws iam add-role-to-instance-profile --instance-profile-name "$PROFILE_NAME" \
    --role-name "$ROLE_NAME"
fi

log "Database password"
if [ ! -f "$SECRET_FILE" ]; then
  # hex only, so it is safe inside a URL
  printf 'DB_PASSWORD=%s\n' "$(openssl rand -hex 16)" > "$SECRET_FILE"
  echo "created ${SECRET_FILE} (git-ignored, do not share it)"
else
  echo "reusing ${SECRET_FILE}"
fi
# shellcheck disable=SC1090
source "$SECRET_FILE"

log "RDS PostgreSQL ${DB_ID} (${DB_CLASS})"
if ! aws rds describe-db-subnet-groups --db-subnet-group-name "$DB_SUBNET_GROUP" >/dev/null 2>&1; then
  # shellcheck disable=SC2086
  aws rds create-db-subnet-group --db-subnet-group-name "$DB_SUBNET_GROUP" \
    --db-subnet-group-description "IRCTC default VPC subnets" \
    --subnet-ids $SUBNET_IDS --tags "$TAGS" >/dev/null
fi

if ! aws rds describe-db-instances --db-instance-identifier "$DB_ID" >/dev/null 2>&1; then
  aws rds create-db-instance \
    --db-instance-identifier "$DB_ID" \
    --db-instance-class "$DB_CLASS" \
    --engine postgres --engine-version 17.11 \
    --allocated-storage 20 --storage-type gp3 \
    --db-name "$DB_NAME" \
    --master-username "$DB_USER" --master-user-password "$DB_PASSWORD" \
    --db-subnet-group-name "$DB_SUBNET_GROUP" \
    --vpc-security-group-ids "$DB_SG" \
    --no-publicly-accessible --no-multi-az \
    --backup-retention-period 0 \
    --no-auto-minor-version-upgrade \
    --tags "$TAGS" \
    --query 'DBInstance.DBInstanceStatus' --output text
else
  echo "already exists"
fi

log "Step 1 done. The database takes about 5-10 minutes to become available."
echo "Next: bash week3/aws/02-image.sh"
