#!/usr/bin/env bash
# Response time vs instance count: the same load at a fixed number of instances.
#   bash week3/aws/sweep.sh "1 2 3 4 6" 1500 180s
# Autoscaling is switched off during the sweep (min = max = N) and restored at the end.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

COUNTS="${1:-1 2 3 4 6}"
USERS="${2:-1500}"
DURATION="${3:-180s}"
SPAWN="${SPAWN_RATE:-150}"
TAG="${SWEEP_TAG:-sweep}"

export LOCUST_WAIT_MIN="${LOCUST_WAIT_MIN:-0.1}"
export LOCUST_WAIT_MAX="${LOCUST_WAIT_MAX:-0.3}"
export LOCUST_READ_WEIGHT="${LOCUST_READ_WEIGHT:-1}"
export LOCUST_BOOK_WEIGHT="${LOCUST_BOOK_WEIGHT:-1}"

for n in $COUNTS; do
  log "Sweep: ${n} instance(s), ${USERS} users, ${DURATION}"
  bash "${AWS_DIR}/set-capacity.sh" "$n"
  bash "${AWS_DIR}/wait-healthy.sh" "$n"
  sleep 20
  bash "${AWS_DIR}/reset-data.sh"
  bash "${AWS_DIR}/run-test.sh" "${TAG}-n${n}-${USERS}u" steady "$USERS" "$SPAWN" "$DURATION"
done

log "Restoring autoscaling range ${ASG_MIN}-${ASG_MAX}"
bash "${AWS_DIR}/set-capacity.sh" auto
