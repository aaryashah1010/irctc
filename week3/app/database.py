
import os

import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://irctc_user:local_dev_password@localhost:5432/irctc",
)


def get_connection():
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
        connect_timeout=5,
    )


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

        # Seed the demo train only if it doesn't already exist.
        # Restarting the API will not reset its remaining inventory.
        conn.execute("""
            INSERT INTO train_inventory
                (train_id, total_seats, available_seats)
            VALUES (12951, 100, 100)
            ON CONFLICT (train_id) DO NOTHING
        """)
