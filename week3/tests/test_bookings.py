from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from app.database import get_connection

BASE_URL = "http://127.0.0.1:8000"
TEST_TRAIN_ID = 99001


@pytest.fixture(scope="module")
def test_train():
    # Create isolated inventory for this test.
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM bookings WHERE train_id = %s",
            (TEST_TRAIN_ID,),
        )
        conn.execute(
            """
            INSERT INTO train_inventory
                (train_id, total_seats, available_seats)
            VALUES (%s, 10, 10)
            ON CONFLICT (train_id) DO UPDATE
            SET total_seats = 10, available_seats = 10
            """,
            (TEST_TRAIN_ID,),
        )

    yield TEST_TRAIN_ID

    # Remove test data after the test.
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM bookings WHERE train_id = %s",
            (TEST_TRAIN_ID,),
        )
        conn.execute(
            "DELETE FROM train_inventory WHERE train_id = %s",
            (TEST_TRAIN_ID,),
        )


def test_health_endpoint():
    response = httpx.get(f"{BASE_URL}/health", timeout=10)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_concurrent_bookings_do_not_oversell(test_train):
    def book_seat(number):
        return httpx.post(
            f"{BASE_URL}/book",
            json={
                "train_id": test_train,
                "passenger_name": f"Passenger {number}",
                "seats": 1,
            },
            timeout=30,
        )

    # Twenty users compete for ten seats simultaneously.
    with ThreadPoolExecutor(max_workers=20) as executor:
        responses = list(executor.map(book_seat, range(20)))

    successful = sum(r.status_code == 201 for r in responses)
    rejected = sum(r.status_code == 409 for r in responses)

    assert successful == 10
    assert rejected == 10

    availability = httpx.get(
        f"{BASE_URL}/availability",
        params={"train_id": test_train},
        timeout=10,
    )

    assert availability.status_code == 200
    assert availability.json()["available_seats"] == 0

    with get_connection() as conn:
        result = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM bookings
            WHERE train_id = %s
            """,
            (test_train,),
        ).fetchone()

    assert result["count"] == 10
