#!/usr/bin/env bash
# Tatkal-style burst, run twice from the same starting point:
#   R3 burst-reactive    start with 1 instance, CPU-based autoscaling reacts to the burst
#   R4 burst-prescaled   start with 4 instances (capacity added before the window opens)
# Load: 10 users for 60 s, jump to PEAK users in about 10 s, hold 300 s, drop for 300 s.
# Bookings are spread over 200 trains (see Experiment A in the README).
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

export LOCUST_PEAK_USERS="${LOCUST_PEAK_USERS:-1200}"
export LOCUST_WAIT_MIN="${LOCUST_WAIT_MIN:-0.1}"
export LOCUST_WAIT_MAX="${LOCUST_WAIT_MAX:-0.3}"
export LOCUST_READ_WEIGHT="${LOCUST_READ_WEIGHT:-1}"
export LOCUST_BOOK_WEIGHT="${LOCUST_BOOK_WEIGHT:-1}"
export LOCUST_BOOK_TRAIN_COUNT="${LOCUST_BOOK_TRAIN_COUNT:-200}"

log "R3 burst-reactive: min 1, max ${ASG_MAX}, start with 1 instance"
aws autoscaling update-auto-scaling-group --auto-scaling-group-name "$ASG_NAME" \
  --min-size 1 --max-size "$ASG_MAX" --desired-capacity 1
bash "${AWS_DIR}/wait-healthy.sh" 1
sleep 20
bash "${AWS_DIR}/reset-data.sh"
bash "${AWS_DIR}/run-test.sh" burst-reactive shape burst

log "R4 burst-prescaled: min 4, max ${ASG_MAX}, start with 4 instances"
aws autoscaling update-auto-scaling-group --auto-scaling-group-name "$ASG_NAME" \
  --min-size 4 --max-size "$ASG_MAX" --desired-capacity 4
bash "${AWS_DIR}/wait-healthy.sh" 4
sleep 20
bash "${AWS_DIR}/reset-data.sh"
bash "${AWS_DIR}/run-test.sh" burst-prescaled shape burst

log "Restoring autoscaling range ${ASG_MIN}-${ASG_MAX}"
bash "${AWS_DIR}/set-capacity.sh" auto
