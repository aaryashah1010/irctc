"""Tatkal-style burst profile (runs R3 and R4).

  0-60 s      10 users                  quiet before the window opens
  60-70 s     jump to PEAK users        the burst (about 10 s)
  70-370 s    PEAK users                hold
  370-670 s   10 users                  drop, watch scale-in and cost

PEAK comes from LOCUST_PEAK_USERS (default 200). Do not use this against
anything but our own deployment.
"""
import os

from locust import LoadTestShape

PEAK = int(os.getenv("LOCUST_PEAK_USERS", "200"))
BASE = 10
QUIET_S = 60
JUMP_S = 10
HOLD_S = 300
DROP_S = 300


class BurstShape(LoadTestShape):
    def tick(self):
        t = self.get_run_time()
        if t < QUIET_S:
            return BASE, BASE
        if t < QUIET_S + JUMP_S + HOLD_S:
            # spawn fast enough to reach PEAK in about JUMP_S seconds
            return PEAK, max(1, (PEAK - BASE) / JUMP_S)
        if t < QUIET_S + JUMP_S + HOLD_S + DROP_S:
            return BASE, max(1, PEAK / 10)
        return None
