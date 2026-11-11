import os
import threading

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://irctc_user:local_dev_password@localhost:5432/irctc",
)

# Each API instance keeps a small pool instead of opening a new connection per
# request. With N autoscaled instances the database sees at most
# N * DB_POOL_MAX_SIZE connections, so size this against the database limit.
POOL_MIN_SIZE = int(os.getenv("DB_POOL_MIN_SIZE", "1"))
POOL_MAX_SIZE = int(os.getenv("DB_POOL_MAX_SIZE", "10"))
POOL_TIMEOUT = float(os.getenv("DB_POOL_TIMEOUT", "10"))

# Large-inventory train used by load tests so that booking traffic does not
# sell out during a run.
LOAD_TEST_TRAIN_ID = 12952
LOAD_TEST_TRAIN_SEATS = 1_000_000

_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()


def _get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                pool = ConnectionPool(
                    DATABASE_URL,
                    min_size=POOL_MIN_SIZE,
                    max_size=POOL_MAX_SIZE,
                    timeout=POOL_TIMEOUT,
                    kwargs={"row_factory": dict_row, "connect_timeout": 5},
                    open=False,
                )
                pool.open()
                _pool = pool
    return _pool


def get_connection():
    """Return a context manager that yields a pooled connection.

    Use it as `with get_connection() as conn:`. The transaction commits when
    the block exits normally, rolls back on an exception, and the connection
    goes back to the pool.
    """
    return _get_pool().connection()


def close_pool():
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.close()
            _pool = None


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS train_inventory (
                train_id INTEGER PRIMARY KEY,
                total_seats INTEGER NOT NULL CHECK (total_seats >= 0),
                available_seats INTEGER NOT NULL
                    CHECK (available_seats >= 0
                           AND available_seats <= total_seats)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                train_id INTEGER NOT NULL
                    REFERENCES train_inventory(train_id),
                passenger_name VARCHAR(100) NOT NULL,
                seats INTEGER NOT NULL CHECK (seats > 0),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # Seed the demo trains only if they don't already exist.
        # Restarting the API will not reset their remaining inventory.
        conn.execute("""
            INSERT INTO train_inventory
                (train_id, total_seats, available_seats)
            VALUES (12951, 100, 100)
            ON CONFLICT (train_id) DO NOTHING
        """)

        conn.execute(
            """
            INSERT INTO train_inventory
                (train_id, total_seats, available_seats)
            VALUES (%s, %s, %s)
            ON CONFLICT (train_id) DO NOTHING
            """,
            (LOAD_TEST_TRAIN_ID, LOAD_TEST_TRAIN_SEATS, LOAD_TEST_TRAIN_SEATS),
        )
