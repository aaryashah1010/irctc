
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.database import get_connection, initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="IRCTC Cloud Scaling PoC",
    description="A simulated railway booking API for load testing.",
    version="1.0.0",
    lifespan=lifespan,
)


class BookingRequest(BaseModel):
    train_id: int = Field(default=12951, gt=0)
    passenger_name: str = Field(min_length=1, max_length=100)
    seats: int = Field(default=1, ge=1, le=6)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/availability")
def availability(
    train_id: Annotated[int, Query(gt=0)] = 12951,
):
    with get_connection() as conn:
        train = conn.execute(
            """
            SELECT train_id, total_seats, available_seats
            FROM train_inventory
            WHERE train_id = %s
            """,
            (train_id,),
        ).fetchone()

    if train is None:
        raise HTTPException(status_code=404, detail="Train not found")

    return train


@app.post("/book", status_code=201)
def book(request: BookingRequest):
    with get_connection() as conn:
        # This conditional UPDATE is atomic in PostgreSQL.
        # Concurrent requests cannot reserve the same remaining seats.
        updated = conn.execute(
            """
            UPDATE train_inventory
            SET available_seats = available_seats - %s
            WHERE train_id = %s
              AND available_seats >= %s
            RETURNING train_id, available_seats
            """,
            (request.seats, request.train_id, request.seats),
        ).fetchone()

        if updated is None:
            train = conn.execute(
                "SELECT train_id FROM train_inventory WHERE train_id = %s",
                (request.train_id,),
            ).fetchone()

            if train is None:
                raise HTTPException(
                    status_code=404,
                    detail="Train not found",
                )

            raise HTTPException(
                status_code=409,
                detail="Not enough seats available",
            )

        booking = conn.execute(
            """
            INSERT INTO bookings (train_id, passenger_name, seats)
            VALUES (%s, %s, %s)
            RETURNING booking_id, train_id, passenger_name, seats, created_at
            """,
            (request.train_id, request.passenger_name.strip(), request.seats),
        ).fetchone()

    return {
        "message": "Booking successful",
        "booking": booking,
        "remaining_seats": updated["available_seats"],
    }
