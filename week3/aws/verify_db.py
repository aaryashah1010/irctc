"""Check booking consistency in the database. Runs inside the API container.

For every train: seats sold (sum of the bookings table) must equal
total_seats - available_seats, and available_seats must stay between 0 and
total_seats. Prints one JSON line; "violations" must be 0.
"""
import json

from app.database import close_pool, get_connection

with get_connection() as conn:
    rows = conn.execute(
        """
        SELECT t.train_id, t.total_seats, t.available_seats,
               COALESCE(SUM(b.seats), 0)::int AS booked,
               COUNT(b.booking_id)::int AS bookings
        FROM train_inventory t
        LEFT JOIN bookings b ON b.train_id = t.train_id
        GROUP BY t.train_id, t.total_seats, t.available_seats
        ORDER BY t.train_id
        """
    ).fetchall()

bad = [
    r for r in rows
    if r["available_seats"] < 0
    or r["available_seats"] > r["total_seats"]
    or r["total_seats"] - r["available_seats"] != r["booked"]
]
print(json.dumps({
    "trains": len(rows),
    "bookings": sum(r["bookings"] for r in rows),
    "seats_sold": sum(r["booked"] for r in rows),
    "violations": len(bad),
    "examples": bad[:5],
}))
close_pool()
