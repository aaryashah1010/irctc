#!/usr/bin/env bash
# Step 3: launch template, target group, load balancer and Auto Scaling group.
# Billing starts for the ALB and the EC2 instances (about $0.025/h + $0.02/h each).
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck disable=SC1090
source "$SECRET_FILE"

ALB_SG="$(sg_id "$ALB_SG_NAME")"
APP_SG="$(sg_id "$APP_SG_NAME")"
[ -n "$ALB_SG" ] && [ -n "$APP_SG" ] || { echo "Run 01-infra.sh first"; exit 1; }

log "Waiting for the database to be available (5-10 minutes the first time)"
aws rds wait db-instance-available --db-instance-identifier "$DB_ID"
DB_HOST="$(aws rds describe-db-instances --db-instance-identifier "$DB_ID" \
  --query 'DBInstances[0].Endpoint.Address' --output text)"
echo "database endpoint: ${DB_HOST}"

AMI_ID="$(aws ssm get-parameter \
  --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query Parameter.Value --output text)"

log "Launch template ${LT_NAME} (AMI ${AMI_ID}, ${INSTANCE_TYPE})"
cat > "${TMP_DIR}/user-data.sh" <<EOF
#!/bin/bash
dnf install -y docker
systemctl enable --now docker
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
docker run -d --name api --restart always -p 8000:8000 \\
  -e DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:5432/${DB_NAME} \\
  -e DB_POOL_MAX_SIZE=${DB_POOL_MAX_SIZE} \\
  -e UVICORN_WORKERS=${UVICORN_WORKERS} \\
  ${ECR_URI}:${IMAGE_TAG}
EOF
USER_DATA_B64="$(base64 -w0 "${TMP_DIR}/user-data.sh")"

cat > "${TMP_DIR}/lt.json" <<EOF
{
  "ImageId": "${AMI_ID}",
  "InstanceType": "${INSTANCE_TYPE}",
  "IamInstanceProfile": {"Name": "${PROFILE_NAME}"},
  "NetworkInterfaces": [{"DeviceIndex": 0, "AssociatePublicIpAddress": true, "Groups": ["${APP_SG}"]}],
  "MetadataOptions": {"HttpTokens": "required", "HttpPutResponseHopLimit": 2},
  "Monitoring": {"Enabled": true},
  "UserData": "${USER_DATA_B64}",
  "TagSpecifications": [
    {"ResourceType": "instance", "Tags": [
      {"Key": "Name", "Value": "${PREFIX}-api"},
      {"Key": "Project", "Value": "${PROJECT_TAG}"}]}
  ]
}
EOF

if ! aws ec2 describe-launch-templates --launch-template-names "$LT_NAME" >/dev/null 2>&1; then
  aws ec2 create-launch-template --launch-template-name "$LT_NAME" \
    --launch-template-data "file://${TMP_WIN}/lt.json" \
    --tag-specifications "ResourceType=launch-template,Tags=[{Key=Project,Value=${PROJECT_TAG}}]" \
    --query 'LaunchTemplate.LaunchTemplateId' --output text
else
  # A new version picks up a new image tag, instance type or pool size.
  aws ec2 create-launch-template-version --launch-template-name "$LT_NAME" \
    --launch-template-data "file://${TMP_WIN}/lt.json" \
    --query 'LaunchTemplateVersion.VersionNumber' --output text
  aws ec2 modify-launch-template --launch-template-name "$LT_NAME" --default-version '$Latest' >/dev/null
fi

log "Target group ${TG_NAME} (health check /health)"
TG_ARN="$(aws elbv2 describe-target-groups --names "$TG_NAME" \
  --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || true)"
if [ -z "$TG_ARN" ] || [ "$TG_ARN" = "None" ]; then
  TG_ARN="$(aws elbv2 create-target-group --name "$TG_NAME" \
    --protocol HTTP --port 8000 --vpc-id "$VPC_ID" --target-type instance \
    --health-check-path /health --health-check-interval-seconds 15 \
    --health-check-timeout-seconds 5 --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3 \
    --tags "Key=Project,Value=${PROJECT_TAG}" \
    --query 'TargetGroups[0].TargetGroupArn' --output text)"
  aws elbv2 modify-target-group-attributes --target-group-arn "$TG_ARN" \
    --attributes Key=deregistration_delay.timeout_seconds,Value=30 >/dev/null
fi
echo "$TG_ARN"

log "Application Load Balancer ${ALB_NAME}"
ALB_ARN="$(aws elbv2 describe-load-balancers --names "$ALB_NAME" \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || true)"
if [ -z "$ALB_ARN" ] || [ "$ALB_ARN" = "None" ]; then
  # shellcheck disable=SC2086
  ALB_ARN="$(aws elbv2 create-load-balancer --name "$ALB_NAME" \
    --type application --scheme internet-facing \
    --subnets $SUBNET_IDS --security-groups "$ALB_SG" \
    --tags "Key=Project,Value=${PROJECT_TAG}" \
    --query 'LoadBalancers[0].LoadBalancerArn' --output text)"
  aws elbv2 create-listener --load-balancer-arn "$ALB_ARN" --protocol HTTP --port 80 \
    --default-actions "Type=forward,TargetGroupArn=${TG_ARN}" >/dev/null
fi

log "Auto Scaling group ${ASG_NAME} (min ${ASG_MIN}, max ${ASG_MAX})"
EXISTING_ASG="$(aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names "$ASG_NAME" \
  --query 'AutoScalingGroups[0].AutoScalingGroupName' --output text 2>/dev/null | sed 's/^None$//')"
if [ -z "$EXISTING_ASG" ]; then
  SUBNET_CSV="$(echo "$SUBNET_IDS" | tr -s '[:space:]' ',' | sed 's/,$//')"
  aws autoscaling create-auto-scaling-group --auto-scaling-group-name "$ASG_NAME" \
    --launch-template "LaunchTemplateName=${LT_NAME},Version=\$Default" \
    --min-size "$ASG_MIN" --max-size "$ASG_MAX" --desired-capacity "$ASG_MIN" \
    --vpc-zone-identifier "$SUBNET_CSV" \
    --target-group-arns "$TG_ARN" \
    --health-check-type ELB --health-check-grace-period 180 \
    --default-instance-warmup 120 \
    --tags "Key=Project,Value=${PROJECT_TAG},PropagateAtLaunch=true"
fi

cat > "${TMP_DIR}/scaling.json" <<EOF
{
  "PredefinedMetricSpecification": {"PredefinedMetricType": "ASGAverageCPUUtilization"},
  "TargetValue": ${CPU_TARGET}
}
EOF
aws autoscaling put-scaling-policy --auto-scaling-group-name "$ASG_NAME" \
  --policy-name "${PREFIX}-cpu-target" --policy-type TargetTrackingScaling \
  --target-tracking-configuration "file://${TMP_WIN}/scaling.json" >/dev/null

ALB_DNS="$(aws elbv2 describe-load-balancers --load-balancer-arns "$ALB_ARN" \
  --query 'LoadBalancers[0].DNSName' --output text)"
echo "http://${ALB_DNS}" > "${TMP_DIR}/url.txt"

log "Done. Instances take about 3-5 minutes to install Docker and pass health checks."
echo "URL: http://${ALB_DNS}/health"
echo "Check: bash week3/aws/status.sh"
