#!/usr/bin/env bash
# Deletes everything that costs money. Run it after every test session.
#   bash week3/aws/teardown.sh             delete ASG, ALB, instances and the database
#   bash week3/aws/teardown.sh --keep-db   keep the database (about $0.5/day)
#   bash week3/aws/teardown.sh --all       also delete security groups, role and ECR repo
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

KEEP_DB=0; ALL=0
for arg in "$@"; do
  case "$arg" in
    --keep-db) KEEP_DB=1 ;;
    --all) ALL=1 ;;
  esac
done

log "Load generator"
LG_IDS="$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=${PREFIX}-loadgen" \
            "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[].Instances[].InstanceId' --output text)"
if [ -n "$LG_IDS" ]; then
  # shellcheck disable=SC2086
  aws ec2 terminate-instances --instance-ids $LG_IDS --query 'TerminatingInstances[].InstanceId' --output text
else
  echo "none"
fi
rm -f "${TMP_DIR}/loadgen-id.txt"

log "Auto Scaling group (terminates the instances)"
if aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$ASG_NAME" \
     --query 'AutoScalingGroups[0].AutoScalingGroupName' --output text 2>/dev/null | grep -qv '^None$'; then
  aws autoscaling delete-auto-scaling-group --auto-scaling-group-name "$ASG_NAME" --force-delete
  echo "waiting for instances to terminate..."
  for _ in $(seq 1 40); do
    left="$(aws ec2 describe-instances \
      --filters "Name=tag:Project,Values=${PROJECT_TAG}" \
                "Name=instance-state-name,Values=pending,running,shutting-down,stopping" \
      --query 'length(Reservations[].Instances[])' --output text)"
    [ "$left" = "0" ] && break
    sleep 10
  done
fi

log "Load balancer and target group"
ALB_ARN="$(aws elbv2 describe-load-balancers --names "$ALB_NAME" \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || true)"
if [ -n "$ALB_ARN" ] && [ "$ALB_ARN" != "None" ]; then
  aws elbv2 delete-load-balancer --load-balancer-arn "$ALB_ARN"
  aws elbv2 wait load-balancers-deleted --load-balancer-arns "$ALB_ARN" || true
fi
TG_ARN="$(aws elbv2 describe-target-groups --names "$TG_NAME" \
  --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || true)"
if [ -n "$TG_ARN" ] && [ "$TG_ARN" != "None" ]; then
  aws elbv2 delete-target-group --target-group-arn "$TG_ARN" || true
fi

log "Launch template"
aws ec2 delete-launch-template --launch-template-name "$LT_NAME" >/dev/null 2>&1 || echo "none"

if [ "$KEEP_DB" = "0" ]; then
  log "RDS database (data is deleted, no final snapshot)"
  if aws rds describe-db-instances --db-instance-identifier "$DB_ID" >/dev/null 2>&1; then
    aws rds delete-db-instance --db-instance-identifier "$DB_ID" \
      --skip-final-snapshot --delete-automated-backups >/dev/null
    aws rds wait db-instance-deleted --db-instance-identifier "$DB_ID"
  fi
  aws rds delete-db-subnet-group --db-subnet-group-name "$DB_SUBNET_GROUP" >/dev/null 2>&1 || true
fi

if [ "$ALL" = "1" ]; then
  log "Security groups, instance role and ECR repository"
  aws s3 rb "s3://${PREFIX}-results-${ACCOUNT_ID}" --force >/dev/null 2>&1 || true
  aws iam delete-role-policy --role-name "$ROLE_NAME" --policy-name "${PREFIX}-results-bucket" 2>/dev/null || true
  for name in "$APP_SG_NAME" "$DB_SG_NAME" "$ALB_SG_NAME" "${PREFIX}-loadgen-sg"; do
    id="$(sg_id "$name")"
    [ -n "$id" ] && { aws ec2 delete-security-group --group-id "$id" 2>/dev/null || echo "could not delete ${name} yet (retry in a minute)"; }
  done
  aws iam remove-role-from-instance-profile --instance-profile-name "$PROFILE_NAME" --role-name "$ROLE_NAME" 2>/dev/null || true
  aws iam delete-instance-profile --instance-profile-name "$PROFILE_NAME" 2>/dev/null || true
  aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly 2>/dev/null || true
  aws iam detach-role-policy --role-name "$ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore 2>/dev/null || true
  aws iam delete-role --role-name "$ROLE_NAME" 2>/dev/null || true
  aws ecr delete-repository --repository-name "$ECR_REPO" --force >/dev/null 2>&1 || true
  rm -f "${TMP_DIR}/url.txt"
fi

log "Teardown finished. Run status.sh to confirm nothing is left."
