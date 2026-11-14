"""C1: correctness suite for the deployed booking API.

Run from the load generator against the load balancer URL:
    python3.12 correctness_aws.py http://<alb-dns> /opt/results/c1/c1.json

It expects the small trains created by aws/reset.py:
    99001 (10 seats), 99002 (10 seats), 99003 (1 seat)

Concurrent requests go through the load balancer, so they are spread across all
running instances and workers. Exit code 0 only if every check passes.
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

BASE = sys.argv[1].rstrip("/")
OUT = sys.argv[2] if len(sys.argv) > 2 else None
results = []
# Size of the biggest burst. 200 on AWS; use a smaller value (for example
# C1_BIG=40) on a slow local machine. Other bursts are derived from it.
BIG = int(os.getenv("C1_BIG", "200"))


def check(name, ok, detail=""):
    results.append({"check": name, "passed": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))


def book(train_id, seats=1, name="Test Passenger"):
    return requests.post(
        f"{BASE}/book",
        json={"train_id": train_id, "passenger_name": name, "seats": seats},
        timeout=30,
    )


def availability(train_id):
    r = requests.get(f"{BASE}/availability", params={"train_id": train_id}, timeout=30)
    return r.status_code, (r.json() if r.status_code == 200 else None)


def burst(count, train_id, seats=1):
    with ThreadPoolExecutor(max_workers=count) as pool:
        responses = list(pool.map(lambda i: book(train_id, seats, f"P{i}"), range(count)))
    codes = [r.status_code for r in responses]
    return {c: codes.count(c) for c in sorted(set(codes))}


# S1: 200 simultaneous single-seat bookings for 10 seats
codes = burst(BIG, 99001)
check(f"S1 {BIG} concurrent bookings, 10 seats: exactly 10 succeed",
      codes.get(201, 0) == 10, str(codes))
check(f"S1 the other {BIG - 10} are rejected with 409",
      codes.get(409, 0) == BIG - 10, str(codes))
check("S1 no other status codes", set(codes) <= {201, 409}, str(codes))
status, body = availability(99001)
check("S1 availability is exactly 0 (never negative)",
      status == 200 and body["available_seats"] == 0, str(body))

# S2: sold-out stays sold out
more = max(10, BIG // 5)
codes = burst(more, 99001)
check(f"S2 {more} more bookings after sell-out: all 409", codes == {409: more},
      str(codes))
status, body = availability(99001)
check("S2 availability still 0", body and body["available_seats"] == 0, str(body))

# S3: multi-seat requests: 50 x 3 seats for 10 seats -> 3 succeed, 1 seat left
codes = burst(max(8, BIG // 4), 99002, seats=3)
check("S3 concurrent 3-seat bookings, 10 seats: exactly 3 succeed",
      codes.get(201, 0) == 3, str(codes))
status, body = availability(99002)
check("S3 exactly 1 seat left", body and body["available_seats"] == 1, str(body))
r = book(99002, seats=2)
check("S3 asking for 2 seats when 1 is left is rejected (409)",
      r.status_code == 409, str(r.status_code))
status, body = availability(99002)
check("S3 the rejected request did not change availability",
      body and body["available_seats"] == 1, str(body))
r = book(99002, seats=1)
check("S3 the last seat can still be booked (201)", r.status_code == 201,
      str(r.status_code))
r = book(99002, seats=1)
check("S3 and then nothing is left (409)", r.status_code == 409, str(r.status_code))

# S4: one seat, 100 simultaneous requests
codes = burst(max(4, BIG // 2), 99003)
check("S4 concurrent bookings for 1 seat: exactly 1 succeeds",
      codes.get(201, 0) == 1, str(codes))
r = book(99003, seats=6)
check("S4 asking for more seats than exist is rejected (409)",
      r.status_code == 409, str(r.status_code))

# S5: invalid input and unknown trains
bad_requests = {
    "seats = 0": {"train_id": 99001, "passenger_name": "A", "seats": 0},
    "seats = 7": {"train_id": 99001, "passenger_name": "A", "seats": 7},
    "seats = -1": {"train_id": 99001, "passenger_name": "A", "seats": -1},
    "seats is text": {"train_id": 99001, "passenger_name": "A", "seats": "abc"},
    "empty name": {"train_id": 99001, "passenger_name": "", "seats": 1},
    "name of spaces only": {"train_id": 99001, "passenger_name": "   ", "seats": 1},
    "name over 100 characters": {"train_id": 99001, "passenger_name": "x" * 101, "seats": 1},
    "train_id = 0": {"train_id": 0, "passenger_name": "A", "seats": 1},
    "train_id = -5": {"train_id": -5, "passenger_name": "A", "seats": 1},
    "name missing": {"train_id": 99001, "seats": 1},
}
for label, payload in bad_requests.items():
    r = requests.post(f"{BASE}/book", json=payload, timeout=30)
    check(f"S5 invalid input ({label}) is rejected with 422", r.status_code == 422,
          str(r.status_code))
r = requests.post(f"{BASE}/book", data="not json",
                  headers={"Content-Type": "application/json"}, timeout=30)
check("S5 malformed JSON body is rejected with 422", r.status_code == 422,
      str(r.status_code))
r = book(987654)
check("S5 booking an unknown train returns 404", r.status_code == 404, str(r.status_code))
status, _ = availability(987654)
check("S5 availability of an unknown train returns 404", status == 404, str(status))
r = requests.get(f"{BASE}/availability", params={"train_id": "abc"}, timeout=30)
check("S5 availability with a non-numeric train id returns 422",
      r.status_code == 422, str(r.status_code))
r = requests.get(f"{BASE}/health", timeout=30)
check("S5 health endpoint answers ok", r.status_code == 200 and r.json().get("status") == "ok")

passed = sum(r["passed"] for r in results)
summary = {"passed": passed, "total": len(results), "all_passed": passed == len(results),
           "results": results}
print(f"\n{passed} of {len(results)} checks passed")
if OUT:
    with open(OUT, "w") as f:
        json.dump(summary, f, indent=1)
sys.exit(0 if summary["all_passed"] else 1)
