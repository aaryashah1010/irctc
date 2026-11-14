#!/usr/bin/env bash
# R5: the same burst as R3 (reactive, starts at 1 instance) but with load shedding
# in the API: a worker that already has ADMISSION_LIMIT requests in flight answers
# new ones at once with 429. Does shaping demand protect the latency of served requests?
# common.sh resets ADMISSION_LIMIT to 0, so the limit is chosen before sourcing it
SHED_LIMIT="${SHED_LIMIT:-32}"
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

export ADMISSION_LIMIT="$SHED_LIMIT"
export LOCUST_PEAK_USERS="${LOCUST_PEAK_USERS:-1200}"
export LOCUST_WAIT_MIN="${LOCUST_WAIT_MIN:-0.1}"
export LOCUST_WAIT_MAX="${LOCUST_WAIT_MAX:-0.3}"
export LOCUST_READ_WEIGHT="${LOCUST_READ_WEIGHT:-1}"
export LOCUST_BOOK_WEIGHT="${LOCUST_BOOK_WEIGHT:-1}"
export LOCUST_BOOK_TRAIN_COUNT="${LOCUST_BOOK_TRAIN_COUNT:-200}"

log "New launch template version with ADMISSION_LIMIT=${ADMISSION_LIMIT}"
bash "${AWS_DIR}/03-app.sh" 2>&1 | grep -vi password | tail -3

log "Replace the running instances so they pick up the setting"
aws autoscaling update-auto-scaling-group --auto-scaling-group-name "$ASG_NAME" \
  --min-size 0 --max-size "$ASG_MAX" --desired-capacity 0
for _ in $(seq 1 40); do
  left="$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=${PREFIX}-api" \
              "Name=instance-state-name,Values=pending,running,shutting-down,stopping" \
    --query 'length(Reservations[].Instances[])' --output text)"
  [ "$left" = "0" ] && break
  sleep 10
done
aws autoscaling update-auto-scaling-group --auto-scaling-group-name "$ASG_NAME" \
  --min-size 1 --max-size "$ASG_MAX" --desired-capacity 1
bash "${AWS_DIR}/wait-healthy.sh" 1
sleep 20
bash "${AWS_DIR}/reset-data.sh"
bash "${AWS_DIR}/run-test.sh" burst-shed shape burst
bash "${AWS_DIR}/verify-db.sh" burst-shed
echo "{\"admission_limit_per_worker\":${ADMISSION_LIMIT}}" \
  > "${AWS_DIR}/../load_tests/results/aws/burst-shed/shed.json"
bash "${AWS_DIR}/set-capacity.sh" auto
