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
ALB = "app/irctc-alb/a40a091b880df907"
REGION = "ap-south-1"


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


def main(only=()):
    for meta_file in sorted(RESULTS.glob("*/meta.json")):
        meta = json.loads(meta_file.read_text())
        if only and not any(o in meta["name"] for o in only):
            continue
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
            "alb_target_response_s": metric("AWS/ApplicationELB", "TargetResponseTime",
                                            "LoadBalancer", ALB, "Average", start, end),
            "alb_p95_s": metric("AWS/ApplicationELB", "TargetResponseTime",
                                "LoadBalancer", ALB, "p95", start, end),
            "alb_requests": metric("AWS/ApplicationELB", "RequestCount",
                                   "LoadBalancer", ALB, "Sum", start, end),
        }
        (meta_file.parent / "metrics.json").write_text(json.dumps(data, indent=1))
        print(f"{meta['name']}: " + ", ".join(f"{k}={len(v)}" for k, v in data.items()))


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])  # optional name filters, for example: burst
