#!/usr/bin/env bash
# Runs one Locust test from the load-generator instance and downloads the results.
#
#   bash week3/aws/run-test.sh <name> steady <users> <spawn_rate> <duration>
#   bash week3/aws/run-test.sh <name> shape  <ramp|burst>
#
# Locust settings are passed through from LOCUST_* environment variables, for example
#   LOCUST_WAIT_MIN=0.1 LOCUST_WAIT_MAX=0.3 bash week3/aws/run-test.sh n3 steady 800 50 3m
#   LOCUST_PEAK_USERS=1500 LOCUST_READ_WEIGHT=1 LOCUST_BOOK_WEIGHT=1 \
#       bash week3/aws/run-test.sh tatkal-auto shape burst
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

NAME="${1:?name required}"; MODE="${2:?steady or shape}"
BUCKET="${PREFIX}-results-${ACCOUNT_ID}"
PROCESSES="${LOCUST_PROCESSES:-4}"
INSTANCE_ID="$(cat "${TMP_DIR}/loadgen-id.txt")"
HOST_URL="$(cat "${TMP_DIR}/url.txt")"
LOCAL_OUT="${AWS_DIR}/../load_tests/results/aws/${NAME}"

case "$MODE" in
  steady)
    USERS="${3:?users}"; RATE="${4:?spawn rate}"; DURATION="${5:?duration}"
    FILES="locustfile.py"
    ARGS="-u ${USERS} -r ${RATE} -t ${DURATION}" ;;
  shape)
    SHAPE="${3:?ramp or burst}"
    FILES="locustfile.py,shapes/${SHAPE}.py"
    ARGS="" ;;
  *) echo "mode must be steady or shape"; exit 1 ;;
esac

log "Uploading load-test files"
SRC="$(cygpath -m "${AWS_DIR}/../load_tests" 2>/dev/null || echo "${AWS_DIR}/../load_tests")"
aws s3 sync "$SRC" "s3://${BUCKET}/loadtests" --delete \
  --exclude "results/*" --exclude "__pycache__/*" --exclude "*.pyc" >/dev/null

{
  echo '#!/bin/bash'
  echo 'set -x'
  env | grep '^LOCUST_' | sed 's/^/export /'
  cat <<EOF
rm -rf /opt/loadtest /opt/results/${NAME}
mkdir -p /opt/loadtest /opt/results/${NAME}
aws s3 sync s3://${BUCKET}/loadtests /opt/loadtest --delete --region ${REGION}
cd /opt/loadtest
python3.12 -m locust -f ${FILES} --headless --processes ${PROCESSES} ${ARGS} \\
  --host ${HOST_URL} --csv /opt/results/${NAME}/stats \\
  --html /opt/results/${NAME}/report.html > /opt/results/${NAME}/locust.log 2>&1
echo "exit code: \$?" >> /opt/results/${NAME}/locust.log
aws s3 sync /opt/results/${NAME} s3://${BUCKET}/results/${NAME} --region ${REGION}
EOF
} > "${TMP_DIR}/run.sh"
aws s3 cp "$(cygpath -m "${TMP_DIR}/run.sh")" "s3://${BUCKET}/run.sh" >/dev/null

START_UTC="$(date -u +%FT%TZ)"
log "Running ${NAME} (${MODE}) from ${INSTANCE_ID}, ${PROCESSES} processes, start ${START_UTC}"
CMD_ID="$(aws ssm send-command --instance-ids "$INSTANCE_ID" --document-name AWS-RunShellScript \
  --timeout-seconds 3600 \
  --parameters "commands=[\"aws s3 cp s3://${BUCKET}/run.sh /opt/run.sh --region ${REGION} && bash /opt/run.sh\"]" \
  --query Command.CommandId --output text)"

while :; do
  st="$(aws ssm list-command-invocations --command-id "$CMD_ID" --query 'CommandInvocations[0].Status' --output text)"
  case "$st" in Success|Failed|Cancelled|TimedOut) break ;; esac
  sleep 15
done
END_UTC="$(date -u +%FT%TZ)"
echo "ssm status: ${st}, end ${END_UTC}"

mkdir -p "$LOCAL_OUT"
aws s3 sync "s3://${BUCKET}/results/${NAME}" "$(cygpath -m "$LOCAL_OUT")" >/dev/null
INSTANCES="$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names "$ASG_NAME" \
  --query 'AutoScalingGroups[0].DesiredCapacity' --output text)"
printf '{"name":"%s","mode":"%s","start":"%s","end":"%s","desired_capacity_at_end":%s}\n' \
  "$NAME" "$MODE" "$START_UTC" "$END_UTC" "$INSTANCES" > "${LOCAL_OUT}/meta.json"

python - "$(cygpath -m "${LOCAL_OUT}")/stats_stats.csv" <<'PY'
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
for r in rows:
    print("%-14s req=%-8s fail=%-6s rps=%-8.1f p50=%-6s p95=%-6s p99=%-6s" % (
        r["Name"], r["Request Count"], r["Failure Count"], float(r["Requests/s"]),
        r["50%"], r["95%"], r["99%"]))
PY
echo "results saved in ${LOCAL_OUT}"
