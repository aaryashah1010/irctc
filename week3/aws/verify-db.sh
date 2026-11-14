#!/usr/bin/env bash
# Runs the database consistency check (verify_db.py) inside the API container
# and saves the result next to a run's other files.
#   bash week3/aws/verify-db.sh <run-name>
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

NAME="${1:?run name}"
BUCKET="${PREFIX}-results-${ACCOUNT_ID}"
INSTANCE_ID="$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$ASG_NAME" \
  --query "AutoScalingGroups[0].Instances[?LifecycleState=='InService']|[0].InstanceId" --output text)"
[ -n "$INSTANCE_ID" ] && [ "$INSTANCE_ID" != "None" ] || { echo "no running instance"; exit 1; }

aws s3 cp "$(cygpath -m "${AWS_DIR}/verify_db.py")" "s3://${BUCKET}/verify_db.py" >/dev/null
CMD_ID="$(aws ssm send-command --instance-ids "$INSTANCE_ID" --document-name AWS-RunShellScript \
  --parameters "commands=[\"aws s3 cp s3://${BUCKET}/verify_db.py /tmp/verify_db.py --region ${REGION} >/dev/null\",\"docker exec -i api python < /tmp/verify_db.py\"]" \
  --query Command.CommandId --output text)"
for _ in $(seq 1 60); do
  st="$(aws ssm list-command-invocations --command-id "$CMD_ID" --query 'CommandInvocations[0].Status' --output text)"
  case "$st" in Success|Failed|Cancelled|TimedOut) break ;; esac
  sleep 3
done
OUT="$(aws ssm get-command-invocation --command-id "$CMD_ID" --instance-id "$INSTANCE_ID" \
  --query 'StandardOutputContent' --output text | grep '^{' | tail -1)"
echo "verify-db (${NAME}): ${st} ${OUT}"
mkdir -p "${AWS_DIR}/../load_tests/results/aws/${NAME}"
echo "$OUT" > "${AWS_DIR}/../load_tests/results/aws/${NAME}/verify-db.json"
