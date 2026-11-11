"""Ramp profile (runs R0 to R2): warm-up, steady ramp, cool-down.

  0-120 s     10 users                         warm-up
  120-720 s   10 -> PEAK users, linear         ramp (find the latency knee)
  720-1020 s  10 users                         cool-down (watch scale-in)

PEAK comes from LOCUST_PEAK_USERS (default 200).
"""
import os

from locust import LoadTestShape

PEAK = int(os.getenv("LOCUST_PEAK_USERS", "200"))
BASE = 10
WARMUP_S = 120
RAMP_S = 600
COOLDOWN_S = 300


class RampShape(LoadTestShape):
    def tick(self):
        t = self.get_run_time()
        if t < WARMUP_S:
            return BASE, BASE
        if t < WARMUP_S + RAMP_S:
            progress = (t - WARMUP_S) / RAMP_S
            users = int(BASE + (PEAK - BASE) * progress)
            return users, max(1, (PEAK - BASE) / RAMP_S * 5)
        if t < WARMUP_S + RAMP_S + COOLDOWN_S:
            return BASE, max(1, PEAK / 10)
        return None
