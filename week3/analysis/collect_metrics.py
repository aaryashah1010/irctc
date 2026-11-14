"""Download per-minute CloudWatch metrics for every AWS load-test run.

Reads load_tests/results/aws/<run>/meta.json (start and end time of the run) and
writes metrics.json next to it: instances in service, app CPU, database CPU and
the load balancer's own response-time and request-count figures.

Needs the AWS CLI configured for the account. Run it before tearing down.
"""
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "load_tests" / "results" / "aws"
ASG = "irctc-asg"
DB = "irctc-db"
REGION = "ap-south-1"


def current_alb_dimension():
    """The load balancer id changes with every deployment, so look it up."""
    out = subprocess.run(
        ["aws", "elbv2", "describe-load-balancers", "--region", REGION,
         "--names", "irctc-alb", "--query", "LoadBalancers[0].LoadBalancerArn",
         "--output", "text"], capture_output=True, text=True)
    arn = out.stdout.strip()
    return arn.split("loadbalancer/")[-1] if "loadbalancer/" in arn else None


def parse(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def metric(namespace, name, dim_name, dim_value, stat, start, end):
    extended = stat.startswith("p")  # percentile such as p95
    out = subprocess.run(
        ["aws", "cloudwatch", "get-metric-statistics", "--region", REGION,
         "--namespace", namespace, "--metric-name", name,
         "--dimensions", f"Name={dim_name},Value={dim_value}",
         "--start-time", start.strftime("%Y-%m-%dT%H:%M:%SZ"),
         "--end-time", end.strftime("%Y-%m-%dT%H:%M:%SZ"),
         "--period", "60",
         "--extended-statistics" if extended else "--statistics", stat,
         "--output", "json"],
        capture_output=True, text=True, check=True).stdout
    points = json.loads(out)["Datapoints"]
    value = (lambda p: p["ExtendedStatistics"][stat]) if extended else (lambda p: p[stat])
    return sorted(({"t": p["Timestamp"], "v": value(p)} for p in points),
                  key=lambda p: p["t"])


def target_group_dimension():
    out = subprocess.run(
        ["aws", "elbv2", "describe-target-groups", "--region", REGION,
         "--names", "irctc-tg", "--query", "TargetGroups[0].TargetGroupArn",
         "--output", "text"], capture_output=True, text=True)
    arn = out.stdout.strip()
    return arn.split(":")[-1] if "targetgroup/" in arn else None


def healthy_hosts(alb, tg, start, end):
    """Instances the load balancer sees as healthy. Used when the Auto Scaling
    group did not publish GroupInServiceInstances (group metrics are off by default)."""
    out = subprocess.run(
        ["aws", "cloudwatch", "get-metric-statistics", "--region", REGION,
         "--namespace", "AWS/ApplicationELB", "--metric-name", "HealthyHostCount",
         "--dimensions", f"Name=LoadBalancer,Value={alb}", f"Name=TargetGroup,Value={tg}",
         "--start-time", start.strftime("%Y-%m-%dT%H:%M:%SZ"),
         "--end-time", end.strftime("%Y-%m-%dT%H:%M:%SZ"),
         "--period", "60", "--statistics", "Maximum", "--output", "json"],
        capture_output=True, text=True, check=True).stdout
    return sorted(({"t": p["Timestamp"], "v": p["Maximum"]}
                   for p in json.loads(out)["Datapoints"]), key=lambda p: p["t"])


def main(only=(), force=False):
    alb = current_alb_dimension()
    tg = target_group_dimension()
    print("load balancer:", alb)
    for meta_file in sorted(RESULTS.glob("*/meta.json")):
        meta = json.loads(meta_file.read_text())
        if only and not any(o in meta["name"] for o in only):
            continue
        if (meta_file.parent / "metrics.json").exists() and not force:
            continue  # keep metrics saved from an earlier deployment
        # pad the window a little so edge minutes are included
        start = parse(meta["start"]) - timedelta(minutes=1)
        end = parse(meta["end"]) + timedelta(minutes=2)
        data = {
            "instances": metric("AWS/AutoScaling", "GroupInServiceInstances",
                                "AutoScalingGroupName", ASG, "Maximum", start, end),
            "app_cpu_avg": metric("AWS/EC2", "CPUUtilization",
                                  "AutoScalingGroupName", ASG, "Average", start, end),
            "db_cpu": metric("AWS/RDS", "CPUUtilization",
                             "DBInstanceIdentifier", DB, "Average", start, end),
            "db_connections": metric("AWS/RDS", "DatabaseConnections",
                                     "DBInstanceIdentifier", DB, "Maximum", start, end),
        }
        for key, name, stat in [
            ("alb_target_response_s", "TargetResponseTime", "Average"),
            ("alb_p95_s", "TargetResponseTime", "p95"),
            ("alb_requests", "RequestCount", "Sum"),
            ("alb_target_5xx", "HTTPCode_Target_5XX_Count", "Sum"),
            ("alb_elb_5xx", "HTTPCode_ELB_5XX_Count", "Sum"),
        ]:
            data[key] = (metric("AWS/ApplicationELB", name, "LoadBalancer", alb,
                                stat, start, end) if alb else [])
        if not data["instances"] and alb and tg:
            data["instances"] = healthy_hosts(alb, tg, start, end)
            data["instances_source"] = "ALB HealthyHostCount"
        (meta_file.parent / "metrics.json").write_text(json.dumps(data, indent=1))
        print(f"{meta['name']}: " + ", ".join(f"{k}={len(v)}" for k, v in data.items() if isinstance(v, list)))


if __name__ == "__main__":
    import sys
    args = [a for a in sys.argv[1:] if a != "--force"]
    # optional name filters, for example: burst; --force rewrites existing files
    main(args, force="--force" in sys.argv)
