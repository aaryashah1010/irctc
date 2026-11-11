#!/usr/bin/env bash
# Shows what is running: instances, target health, database and the URL.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

log "Auto Scaling group"
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$ASG_NAME" \
  --query 'AutoScalingGroups[0].{min:MinSize,max:MaxSize,desired:DesiredCapacity,instances:Instances[].[InstanceId,AvailabilityZone,LifecycleState,HealthStatus]}' \
  --output json 2>/dev/null || echo "no ASG"

log "Target health"
TG_ARN="$(aws elbv2 describe-target-groups --names "$TG_NAME" \
  --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || true)"
if [ -n "$TG_ARN" ] && [ "$TG_ARN" != "None" ]; then
  aws elbv2 describe-target-health --target-group-arn "$TG_ARN" \
    --query 'TargetHealthDescriptions[].[Target.Id,TargetHealth.State,TargetHealth.Reason]' --output table
fi

log "Database"
aws rds describe-db-instances --db-instance-identifier "$DB_ID" \
  --query 'DBInstances[0].[DBInstanceIdentifier,DBInstanceClass,DBInstanceStatus]' --output text 2>/dev/null || echo "no database"

[ -f "${TMP_DIR}/url.txt" ] && { log "URL"; cat "${TMP_DIR}/url.txt"; }
