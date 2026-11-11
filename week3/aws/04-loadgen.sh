#!/usr/bin/env bash
# Step 4: a load-generator EC2 instance in the same region, so the load does not
# depend on a laptop or home internet. Also creates a private S3 bucket used to
# move the load-test files in and the result files out.
# Cost: about $0.17 per hour for c6i.xlarge while it runs.
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

LOADGEN_TYPE="${LOADGEN_TYPE:-c6i.xlarge}"
LOADGEN_SG_NAME="${PREFIX}-loadgen-sg"
BUCKET="${PREFIX}-results-${ACCOUNT_ID}"
TAGS="Key=Project,Value=${PROJECT_TAG}"

log "S3 bucket ${BUCKET} (private)"
if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  aws s3api create-bucket --bucket "$BUCKET" \
    --create-bucket-configuration "LocationConstraint=${REGION}" >/dev/null
  aws s3api put-public-access-block --bucket "$BUCKET" \
    --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
fi

log "Allow the instance role to use only this bucket"
cat > "${TMP_DIR}/s3policy.json" <<EOF
{"Version":"2012-10-17","Statement":[{"Effect":"Allow",
 "Action":["s3:GetObject","s3:PutObject","s3:ListBucket"],
 "Resource":["arn:aws:s3:::${BUCKET}","arn:aws:s3:::${BUCKET}/*"]}]}
EOF
aws iam put-role-policy --role-name "$ROLE_NAME" --policy-name "${PREFIX}-results-bucket" \
  --policy-document "file://${TMP_WIN}/s3policy.json"

log "Security group (no inbound rules)"
SG="$(sg_id "$LOADGEN_SG_NAME")"
if [ -z "$SG" ]; then
  SG="$(aws ec2 create-security-group --group-name "$LOADGEN_SG_NAME" \
    --description "IRCTC load generator" --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Project,Value=${PROJECT_TAG}}]" \
    --query GroupId --output text)"
fi
echo "$SG"

EXISTING="$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=${PREFIX}-loadgen" \
            "Name=instance-state-name,Values=pending,running" \
  --query 'Reservations[0].Instances[0].InstanceId' --output text | sed 's/^None$//')"
if [ -n "$EXISTING" ]; then
  echo "load generator already running: ${EXISTING}"
  INSTANCE_ID="$EXISTING"
else
  log "Launching ${LOADGEN_TYPE}"
  AMI_ID="$(aws ssm get-parameter \
    --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
    --query Parameter.Value --output text)"
  FIRST_SUBNET="$(echo "$SUBNET_IDS" | awk '{print $1}')"
  cat > "${TMP_DIR}/loadgen-user-data.sh" <<'EOF'
#!/bin/bash
dnf install -y python3.12 python3.12-pip
python3.12 -m pip install locust
mkdir -p /opt/loadtest /opt/results
touch /opt/ready
EOF
  INSTANCE_ID="$(aws ec2 run-instances --image-id "$AMI_ID" --instance-type "$LOADGEN_TYPE" \
    --subnet-id "$FIRST_SUBNET" --security-group-ids "$SG" \
    --associate-public-ip-address \
    --iam-instance-profile "Name=${PROFILE_NAME}" \
    --metadata-options HttpTokens=required,HttpPutResponseHopLimit=2 \
    --user-data "file://${TMP_WIN}/loadgen-user-data.sh" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${PREFIX}-loadgen},{Key=Project,Value=${PROJECT_TAG}}]" \
    --query 'Instances[0].InstanceId' --output text)"
  echo "$INSTANCE_ID"
fi
echo "$INSTANCE_ID" > "${TMP_DIR}/loadgen-id.txt"

log "Waiting for Session Manager to see the instance"
for _ in $(seq 1 40); do
  state="$(aws ssm describe-instance-information \
    --filters "Key=InstanceIds,Values=${INSTANCE_ID}" \
    --query 'InstanceInformationList[0].PingStatus' --output text 2>/dev/null | sed 's/^None$//')"
  [ "$state" = "Online" ] && break
  sleep 10
done
echo "ssm: ${state:-offline}"

log "Waiting for Locust to finish installing"
CMD_ID="$(aws ssm send-command --instance-ids "$INSTANCE_ID" --document-name AWS-RunShellScript \
  --parameters 'commands=["for i in $(seq 1 60); do [ -f /opt/ready ] && break; sleep 5; done; python3.12 -m locust --version"]' \
  --query Command.CommandId --output text)"
for _ in $(seq 1 60); do
  st="$(aws ssm list-command-invocations --command-id "$CMD_ID" --query 'CommandInvocations[0].Status' --output text)"
  case "$st" in Success|Failed|Cancelled|TimedOut) break ;; esac
  sleep 5
done
aws ssm get-command-invocation --command-id "$CMD_ID" --instance-id "$INSTANCE_ID" \
  --query '[Status,StandardOutputContent]' --output text
echo
echo "Load generator ready. Next: bash week3/aws/run-test.sh <name> ..."
