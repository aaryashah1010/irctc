#!/usr/bin/env bash
# Waits until exactly N targets are healthy behind the load balancer.
#   bash week3/aws/wait-healthy.sh 3
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

WANT="${1:?number of healthy targets}"
TG_ARN="$(aws elbv2 describe-target-groups --names "$TG_NAME" \
  --query 'TargetGroups[0].TargetGroupArn' --output text)"
for i in $(seq 1 90); do
  healthy="$(aws elbv2 describe-target-health --target-group-arn "$TG_ARN" \
    --query "length(TargetHealthDescriptions[?TargetHealth.State=='healthy'])" --output text)"
  total="$(aws elbv2 describe-target-health --target-group-arn "$TG_ARN" \
    --query "length(TargetHealthDescriptions)" --output text)"
  [ "$healthy" = "$WANT" ] && [ "$total" = "$WANT" ] && { echo "${healthy} healthy after ~$((i*10))s"; exit 0; }
  sleep 10
done
echo "timed out: ${healthy}/${total} healthy, wanted ${WANT}"; exit 1
