
import os
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from psycopg_pool import PoolTimeout
from pydantic import BaseModel, Field, StringConstraints

from app.database import close_pool, get_connection, initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield
    close_pool()


app = FastAPI(
    title="IRCTC Cloud Scaling PoC",
    description="A simulated railway booking API for load testing.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(PoolTimeout)
async def database_busy(request: Request, exc: PoolTimeout):
    # No database connection became free in time: tell the caller (and the load
    # balancer) the service is overloaded instead of returning a generic 500.
    return JSONResponse(
        {"detail": "Database busy, please retry shortly"},
        status_code=503,
        headers={"Retry-After": "1"},
    )


# Optional load shedding (experiment R5). When ADMISSION_LIMIT is above 0, a
# worker that already has that many requests in flight answers new ones at once
# with 429 instead of queueing them. /health is never shed, so the load balancer
# health check keeps working. Off by default.
ADMISSION_LIMIT = int(os.getenv("ADMISSION_LIMIT", "0"))
_in_flight = 0


@app.middleware("http")
async def admission_control(request: Request, call_next):
    global _in_flight
    if ADMISSION_LIMIT <= 0 or request.url.path == "/health":
        return await call_next(request)
    if _in_flight >= ADMISSION_LIMIT:
        return JSONResponse(
            {"detail": "Server busy, please retry shortly"},
            status_code=429,
            headers={"Retry-After": "1"},
        )
    _in_flight += 1
    try:
        return await call_next(request)
    finally:
        _in_flight -= 1


class BookingRequest(BaseModel):
    train_id: int = Field(default=12951, gt=0)
    # A name made only of spaces is rejected (422) instead of being stored empty.
    passenger_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
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
