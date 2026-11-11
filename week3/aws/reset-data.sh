#!/usr/bin/env bash
# Empties the bookings table and refills the demo trains so each run starts equal.
# Runs the reset script inside the API container on one running instance.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

BUCKET="${PREFIX}-results-${ACCOUNT_ID}"
INSTANCE_ID="$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$ASG_NAME" \
  --query "AutoScalingGroups[0].Instances[?LifecycleState=='InService']|[0].InstanceId" --output text)"
[ -n "$INSTANCE_ID" ] && [ "$INSTANCE_ID" != "None" ] || { echo "no running instance"; exit 1; }

aws s3 cp "$(cygpath -m "${AWS_DIR}/reset.py")" "s3://${BUCKET}/reset.py" >/dev/null
CMD_ID="$(aws ssm send-command --instance-ids "$INSTANCE_ID" --document-name AWS-RunShellScript \
  --parameters "commands=[\"aws s3 cp s3://${BUCKET}/reset.py /tmp/reset.py --region ${REGION} >/dev/null\",\"docker exec -i api python < /tmp/reset.py\"]" \
  --query Command.CommandId --output text)"
for _ in $(seq 1 30); do
  st="$(aws ssm list-command-invocations --command-id "$CMD_ID" --query 'CommandInvocations[0].Status' --output text)"
  case "$st" in Success|Failed|Cancelled|TimedOut) break ;; esac
  sleep 3
done
echo "reset: ${st}"
aws ssm get-command-invocation --command-id "$CMD_ID" --instance-id "$INSTANCE_ID" \
  --query '[StandardOutputContent,StandardErrorContent]' --output text
