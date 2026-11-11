"""Locust workload for the IRCTC booking API.

Default mix: 90% availability checks and 10% bookings. This is a modelling
assumption for our experiment, not an IRCTC statistic.

Bookings go to the large-inventory load-test train (12952) so that a run does
not sell out. A 409 (sold out) is a valid business answer, not an error.

Environment variables:
  LOCUST_WAIT_MIN / LOCUST_WAIT_MAX  seconds between a user's requests (1 / 2)
  LOCUST_BOOK_TRAIN_ID               train used for bookings (12952)
  LOCUST_READ_TRAIN_ID               train used for availability (12951)
  LOCUST_READ_WEIGHT / LOCUST_BOOK_WEIGHT   task mix (9 / 1)
  LOCUST_BOOK_TRAIN_COUNT            spread bookings over N trains (1 = one hot train)

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
# With LOCUST_BOOK_TRAIN_COUNT > 1, bookings are spread over that many trains
# (ids 20001 and up, created by aws/reset.py). With 1 (default) every booking
# hits train BOOK_TRAIN_ID, which models one hot Tatkal train.
BOOK_TRAIN_COUNT = int(os.getenv("LOCUST_BOOK_TRAIN_COUNT", "1"))
SPREAD_BASE_ID = 20001
# Task weights: 9 reads to 1 booking by default. The Tatkal runs use a
# booking-heavy mix, for example LOCUST_READ_WEIGHT=1 LOCUST_BOOK_WEIGHT=1.
READ_WEIGHT = int(os.getenv("LOCUST_READ_WEIGHT", "9"))
BOOK_WEIGHT = int(os.getenv("LOCUST_BOOK_WEIGHT", "1"))


class IRCTCUser(HttpUser):
    # Simulate users waiting between requests
    wait_time = between(WAIT_MIN, WAIT_MAX)

    @task(READ_WEIGHT)
    def check_availability(self):
        self.client.get(
            "/availability",
            params={"train_id": READ_TRAIN_ID},
            name="/availability",
        )

    @task(BOOK_WEIGHT)
    def book_seat(self):
        train_id = (
            BOOK_TRAIN_ID
            if BOOK_TRAIN_COUNT <= 1
            else SPREAD_BASE_ID + random.randrange(BOOK_TRAIN_COUNT)
        )
        payload = {
            "train_id": train_id,
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
