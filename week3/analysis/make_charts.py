"""Build the report figures from the AWS load-test results.

Inputs : load_tests/results/aws/<run>/stats_stats.csv, stats_stats_history.csv,
         meta.json and metrics.json (from collect_metrics.py)
Outputs: report/figures/*.png and report/figures/summary.json
"""
import csv
import json
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
RES = BASE / "load_tests" / "results" / "aws"
OUT = BASE / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

COUNTS = [1, 2, 3, 4, 6]
BLUE, ORANGE, GREY, RED, GREEN = "#2f6db5", "#e07b21", "#6b7280", "#c0392b", "#2e8b57"

plt.rcParams.update({
    "figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "font.size": 10,
})


def aggregated(run):
    with open(RES / run / "stats_stats.csv", newline="") as f:
        for row in csv.DictReader(f):
            if row["Name"] == "Aggregated":
                return {
                    "requests": int(row["Request Count"]),
                    "failures": int(row["Failure Count"]),
                    "rps": float(row["Requests/s"]),
                    "p50": float(row["50%"]), "p95": float(row["95%"]),
                    "p99": float(row["99%"]),
                }


def metrics(run):
    return json.loads((RES / run / "metrics.json").read_text())


def peak(points):
    return max((p["v"] for p in points), default=float("nan"))


def when(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()


def sweep(prefix):
    rows = {}
    for n in COUNTS:
        run = f"{prefix}-n{n}-1500u"
        a = aggregated(run)
        m = metrics(run)
        a["app_cpu_peak"] = peak(m["app_cpu_avg"])
        a["db_cpu_peak"] = peak(m["db_cpu"])
        rows[n] = a
    return rows


def fig_scaling(spread):
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.9))
    ns = COUNTS
    thr = [spread[n]["rps"] for n in ns]
    ax[0].plot(ns, thr, "o-", color=BLUE, label="measured")
    ax[0].plot(ns, [thr[0] * n for n in ns], "--", color=GREY, label="perfect scaling")
    ax[0].set(title="Throughput", xlabel="Instances", ylabel="Requests per second")
    ax[0].legend(frameon=False)

    ax[1].plot(ns, [spread[n]["p50"] for n in ns], "o-", color=GREEN, label="median")
    ax[1].plot(ns, [spread[n]["p95"] for n in ns], "s-", color=ORANGE, label="p95")
    ax[1].set(title="Response time", xlabel="Instances", ylabel="Milliseconds",
              yscale="log")
    ax[1].legend(frameon=False)

    ax[2].plot(ns, [spread[n]["app_cpu_peak"] for n in ns], "o-", color=BLUE,
               label="API instances (avg)")
    ax[2].plot(ns, [spread[n]["db_cpu_peak"] for n in ns], "s-", color=RED,
               label="Database")
    ax[2].set(title="Peak CPU", xlabel="Instances", ylabel="CPU %", ylim=(0, 105))
    ax[2].legend(frameon=False)
    for a in ax:
        a.set_xticks(ns)
    fig.suptitle("Experiment A: 1,500 users, bookings spread over 200 trains", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / "fig_a_scaling.png", bbox_inches="tight")
    plt.close(fig)


def fig_hot_vs_spread(hot, spread):
    fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.9))
    ns = COUNTS
    ax[0].plot(ns, [spread[n]["rps"] for n in ns], "o-", color=BLUE,
               label="200 trains (spread)")
    ax[0].plot(ns, [hot[n]["rps"] for n in ns], "s-", color=RED,
               label="1 hot train")
    ax[0].set(title="Throughput", xlabel="Instances", ylabel="Requests per second")
    ax[0].legend(frameon=False)
    ax[1].plot(ns, [spread[n]["p50"] for n in ns], "o-", color=BLUE,
               label="200 trains (spread)")
    ax[1].plot(ns, [hot[n]["p50"] for n in ns], "s-", color=RED, label="1 hot train")
    ax[1].set(title="Median response time", xlabel="Instances", ylabel="Milliseconds",
              yscale="log")
    ax[1].legend(frameon=False)
    for a in ax:
        a.set_xticks(ns)
    fig.suptitle("Same load, different data layout: a hot row stops scaling", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / "fig_b_hot_vs_spread.png", bbox_inches="tight")
    plt.close(fig)


def history(run):
    rows = []
    with open(RES / run / "stats_stats_history.csv", newline="") as f:
        for row in csv.DictReader(f):
            if row["Name"] == "Aggregated" and row["User Count"] not in ("", "0"):
                rows.append(row)
    t0 = float(rows[0]["Timestamp"])
    return t0, rows


def fig_burst(runs):
    fig, axes = plt.subplots(3, len(runs), figsize=(12.5, 8.2), sharex="col",
                             sharey="row")
    for col, (run, title) in enumerate(runs):
        t0, hist = history(run)
        m = metrics(run)
        mins = [(float(r["Timestamp"]) - t0) / 60 for r in hist]

        ax = axes[0][col]
        ax.plot(mins, [float(r["User Count"]) for r in hist], color=GREY,
                label="simulated users")
        ax.set(title=title, ylabel="Users")
        ax2 = ax.twinx()
        ax2.step([(when(p["t"]) - t0) / 60 for p in m["instances"]],
                 [p["v"] for p in m["instances"]], where="post", color=BLUE, lw=2.2,
                 label="instances in service")
        ax2.set_ylim(0, 7)
        ax2.set_ylabel("Instances", color=BLUE)
        ax2.grid(False)
        ax2.spines["right"].set_visible(True)

        ax = axes[1][col]
        ax.plot([(when(p["t"]) - t0) / 60 for p in m["alb_target_response_s"]],
                [p["v"] * 1000 for p in m["alb_target_response_s"]], "o-",
                color=GREEN, label="average")
        if m.get("alb_p95_s"):
            ax.plot([(when(p["t"]) - t0) / 60 for p in m["alb_p95_s"]],
                    [p["v"] * 1000 for p in m["alb_p95_s"]], "s-", color=ORANGE,
                    label="p95")
        ax.set(ylabel="Server response (ms)")
        ax.legend(frameon=False, loc="upper right")

        ax = axes[2][col]
        ax.plot(mins, [float(r["Requests/s"]) for r in hist], color=BLUE)
        ax.set(ylabel="Requests per second", xlabel="Minutes since the test started")
    fig.suptitle("Tatkal-style burst: 10 to 1,200 users in about 10 seconds", y=0.995)
    fig.tight_layout()
    fig.savefig(OUT / "fig_c_burst.png", bbox_inches="tight")
    plt.close(fig)


def burst_summary(run):
    t0, hist = history(run)
    m = metrics(run)
    a = aggregated(run)
    users = [(float(r["Timestamp"]) - t0, float(r["User Count"])) for r in hist]
    peak_users = max(u for _, u in users)
    burst_at = next(t for t, u in users if u > 100)
    scale_events = []
    prev = None
    for p in m["instances"]:
        if prev is not None and p["v"] != prev:
            scale_events.append({"minute": round((when(p["t"]) - t0) / 60, 1),
                                 "instances": p["v"]})
        prev = p["v"]
    return {
        **a,
        "burst_starts_min": round(burst_at / 60, 1),
        "peak_instances": peak(m["instances"]),
        "scale_events": scale_events,
        "db_cpu_peak": peak(m["db_cpu"]),
        "app_cpu_peak": peak(m["app_cpu_avg"]),
        "peak_users": peak_users,
    }


def main():
    hot = sweep("sweep")
    spread = sweep("spread")
    fig_scaling(spread)
    fig_hot_vs_spread(hot, spread)
    bursts = {
        "burst-reactive": burst_summary("burst-reactive"),
        "burst-prescaled": burst_summary("burst-prescaled"),
    }
    fig_burst([("burst-reactive", "R3: reactive autoscaling (starts at 1 instance)"),
               ("burst-prescaled", "R4: pre-scaled (starts at 4 instances)")])
    summary = {"hot_train": hot, "spread": spread, "burst": bursts}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps(bursts, indent=1))
    print("figures written to", OUT)


if __name__ == "__main__":
    main()
