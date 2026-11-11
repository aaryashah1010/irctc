"""Locust workload for the IRCTC booking API.

Default mix: 90% availability checks and 10% bookings. This is a modelling
assumption for our experiment, not an IRCTC statistic.

Bookings go to the large-inventory load-test train (12952) so that a run does
not sell out. A 409 (sold out) is a valid business answer, not an error.

Environment variables:
  LOCUST_WAIT_MIN / LOCUST_WAIT_MAX  seconds between a user's requests (1 / 2)
  LOCUST_BOOK_TRAIN_ID               train used for bookings (12952)
  LOCUST_READ_TRAIN_ID               train used for availability (12951)

Load profiles live in separate files; combine them with -f, for example:
  locust -f load_tests/locustfile.py,load_tests/shapes/ramp.py --host http://...
"""
import os
import random

from locust import HttpUser, between, task

WAIT_MIN = float(os.getenv("LOCUST_WAIT_MIN", "1"))
WAIT_MAX = float(os.getenv("LOCUST_WAIT_MAX", "2"))
BOOK_TRAIN_ID = int(os.getenv("LOCUST_BOOK_TRAIN_ID", "12952"))
READ_TRAIN_ID = int(os.getenv("LOCUST_READ_TRAIN_ID", "12951"))


class IRCTCUser(HttpUser):
    # Simulate users waiting between requests
    wait_time = between(WAIT_MIN, WAIT_MAX)

    @task(9)
    def check_availability(self):
        self.client.get(
            "/availability",
            params={"train_id": READ_TRAIN_ID},
            name="/availability",
        )

    @task(1)
    def book_seat(self):
        payload = {
            "train_id": BOOK_TRAIN_ID,
            "passenger_name": f"Load User {random.randint(1, 1_000_000)}",
            "seats": 1,
        }
        with self.client.post(
            "/book", json=payload, name="/book", catch_response=True
        ) as response:
            if response.status_code in (201, 409):
                response.success()
            else:
                response.failure(f"unexpected status {response.status_code}")
