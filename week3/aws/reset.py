"""Reset the load-test data. Runs inside the API container (see reset-data.sh)."""
from app.database import close_pool, get_connection

with get_connection() as conn:
    conn.execute("TRUNCATE bookings RESTART IDENTITY")
    conn.execute(
        "UPDATE train_inventory SET available_seats = total_seats "
        "WHERE train_id IN (12951, 12952)"
    )
    # 200 extra trains for the "spread" workload (ids 20001-20200)
    conn.execute(
        """
        INSERT INTO train_inventory (train_id, total_seats, available_seats)
        SELECT g, 100000, 100000 FROM generate_series(20001, 20200) AS g
        ON CONFLICT (train_id) DO UPDATE
        SET total_seats = 100000, available_seats = 100000
        """
    )
    rows = conn.execute(
        "SELECT train_id, total_seats, available_seats "
        "FROM train_inventory WHERE train_id IN (12951, 12952, 20001, 20200) "
        "ORDER BY train_id"
    ).fetchall()
print(rows)
close_pool()
