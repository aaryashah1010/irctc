#!/usr/bin/env bash
# Failure test: three instances under steady load; one is terminated abruptly
# (not drained) about two minutes in. Shows how many requests fail and how long the
# load balancer and Auto Scaling group take to recover.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

export LOCUST_WAIT_MIN="${LOCUST_WAIT_MIN:-0.1}"
export LOCUST_WAIT_MAX="${LOCUST_WAIT_MAX:-0.3}"
export LOCUST_READ_WEIGHT="${LOCUST_READ_WEIGHT:-1}"
export LOCUST_BOOK_WEIGHT="${LOCUST_BOOK_WEIGHT:-1}"
export LOCUST_BOOK_TRAIN_COUNT="${LOCUST_BOOK_TRAIN_COUNT:-200}"
NAME="failure-kill-1instance"

log "Three instances"
aws autoscaling update-auto-scaling-group --auto-scaling-group-name "$ASG_NAME" \
  --min-size 3 --max-size "$ASG_MAX" --desired-capacity 3
bash "${AWS_DIR}/wait-healthy.sh" 3
sleep 20
bash "${AWS_DIR}/reset-data.sh"

# 800 users is below the capacity of three instances, so errors come from the failure.
bash "${AWS_DIR}/run-test.sh" "$NAME" steady 800 100 6m &
RUN_PID=$!

sleep 150
VICTIM="$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$ASG_NAME" \
  --query "AutoScalingGroups[0].Instances[?LifecycleState=='InService']|[0].InstanceId" --output text)"
KILL_UTC="$(date -u +%FT%TZ)"
log "Terminating ${VICTIM} at ${KILL_UTC} (no draining)"
aws ec2 terminate-instances --instance-ids "$VICTIM" --query 'TerminatingInstances[0].CurrentState.Name' --output text

wait "$RUN_PID"
OUT="${AWS_DIR}/../load_tests/results/aws/${NAME}"
echo "{\"instance\":\"${VICTIM}\",\"kill_utc\":\"${KILL_UTC}\"}" > "${OUT}/kill.json"
bash "${AWS_DIR}/verify-db.sh" "$NAME"
bash "${AWS_DIR}/wait-healthy.sh" 3
bash "${AWS_DIR}/set-capacity.sh" auto
