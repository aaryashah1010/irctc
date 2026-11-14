#!/usr/bin/env bash
# Planned runs R0, R1 and R2: the same ramp (10 to PEAK users over 10 minutes,
# preceded by a 2 minute warm-up and followed by a 5 minute cool-down).
#   R0  one fixed instance                (where does a single instance saturate?)
#   R1  three fixed instances             (how does fixed capacity move the knee?)
#   R2  autoscaling, 1 to 6 instances     (does latency recover as instances join?)
# The consistency check runs after each run, before the data is reset.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

export LOCUST_PEAK_USERS="${LOCUST_PEAK_USERS:-1500}"
export LOCUST_WAIT_MIN="${LOCUST_WAIT_MIN:-0.1}"
export LOCUST_WAIT_MAX="${LOCUST_WAIT_MAX:-0.3}"
export LOCUST_READ_WEIGHT="${LOCUST_READ_WEIGHT:-1}"
export LOCUST_BOOK_WEIGHT="${LOCUST_BOOK_WEIGHT:-1}"
export LOCUST_BOOK_TRAIN_COUNT="${LOCUST_BOOK_TRAIN_COUNT:-200}"

run_ramp() {
  local name="$1" min="$2" max="$3" desired="$4"
  log "${name}: instances min ${min}, max ${max}, start ${desired}"
  aws autoscaling update-auto-scaling-group --auto-scaling-group-name "$ASG_NAME" \
    --min-size "$min" --max-size "$max" --desired-capacity "$desired"
  bash "${AWS_DIR}/wait-healthy.sh" "$desired"
  sleep 20
  bash "${AWS_DIR}/reset-data.sh"
  bash "${AWS_DIR}/run-test.sh" "$name" shape ramp
  bash "${AWS_DIR}/verify-db.sh" "$name"
}

run_ramp ramp-r0-fixed1 1 1 1
run_ramp ramp-r1-fixed3 3 3 3
run_ramp ramp-r2-autoscale "$ASG_MIN" "$ASG_MAX" 1

log "Ramp runs finished"
