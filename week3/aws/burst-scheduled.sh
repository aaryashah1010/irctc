#!/usr/bin/env bash
# R4 with a real AWS scheduled action: capacity is raised on a schedule a few
# minutes before the burst, the way a known 10:00 Tatkal opening would be handled.
# Compare with R3 (reactive) from burst-experiment.sh.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

export LOCUST_PEAK_USERS="${LOCUST_PEAK_USERS:-1200}"
export LOCUST_WAIT_MIN="${LOCUST_WAIT_MIN:-0.1}"
export LOCUST_WAIT_MAX="${LOCUST_WAIT_MAX:-0.3}"
export LOCUST_READ_WEIGHT="${LOCUST_READ_WEIGHT:-1}"
export LOCUST_BOOK_WEIGHT="${LOCUST_BOOK_WEIGHT:-1}"
export LOCUST_BOOK_TRAIN_COUNT="${LOCUST_BOOK_TRAIN_COUNT:-200}"

ACTION="${PREFIX}-prewarm"
LEAD_MINUTES="${LEAD_MINUTES:-3}"

log "Start from 1 instance"
aws autoscaling update-auto-scaling-group --auto-scaling-group-name "$ASG_NAME" \
  --min-size 1 --max-size "$ASG_MAX" --desired-capacity 1
bash "${AWS_DIR}/wait-healthy.sh" 1
sleep 20
bash "${AWS_DIR}/reset-data.sh"

START="$(date -u -d "+${LEAD_MINUTES} minutes" +%Y-%m-%dT%H:%M:00Z)"
log "Scheduled action ${ACTION}: raise to 4 instances at ${START}"
aws autoscaling put-scheduled-update-group-action --auto-scaling-group-name "$ASG_NAME" \
  --scheduled-action-name "$ACTION" --start-time "$START" \
  --min-size 4 --max-size "$ASG_MAX" --desired-capacity 4
echo "$START" > "${TMP_DIR}/prewarm-start.txt"

bash "${AWS_DIR}/wait-healthy.sh" 4
sleep 20
log "Capacity is ready; starting the burst"
bash "${AWS_DIR}/run-test.sh" burst-scheduled shape burst
bash "${AWS_DIR}/verify-db.sh" burst-scheduled
echo "{\"scheduled_action_start\":\"${START}\"}" \
  > "${AWS_DIR}/../load_tests/results/aws/burst-scheduled/schedule.json"

aws autoscaling delete-scheduled-action --auto-scaling-group-name "$ASG_NAME" \
  --scheduled-action-name "$ACTION" || true
bash "${AWS_DIR}/set-capacity.sh" auto
