#!/usr/bin/env bash
# Pin the number of instances for a fixed-capacity run (response time vs instance count).
#   bash week3/aws/set-capacity.sh 3        -> exactly 3 instances (autoscaling off)
#   bash week3/aws/set-capacity.sh auto     -> back to min 1, max 6 with CPU scaling
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

case "${1:-}" in
  auto)
    aws autoscaling update-auto-scaling-group --auto-scaling-group-name "$ASG_NAME" \
      --min-size "$ASG_MIN" --max-size "$ASG_MAX"
    echo "autoscaling range set to ${ASG_MIN}-${ASG_MAX}"
    ;;
  ''|*[!0-9]*)
    echo "usage: set-capacity.sh <number>|auto"; exit 1 ;;
  *)
    aws autoscaling update-auto-scaling-group --auto-scaling-group-name "$ASG_NAME" \
      --min-size "$1" --max-size "$1" --desired-capacity "$1"
    echo "capacity pinned to $1; wait until status.sh shows all targets healthy"
    ;;
esac
