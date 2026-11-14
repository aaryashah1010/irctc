"""Figures and summary numbers for the second AWS session:
C1 correctness, ramp runs R0-R2, scheduled pre-scaling R4, the failure test and
load shedding R5. Run after collect_metrics.py:  python analysis/make_charts_extra.py
"""
import csv
import json
from pathlib import Path

from make_charts import (BLUE, GREEN, GREY, ORANGE, OUT, RED, RES, aggregated,
                         history, metrics, peak, plt, when)


def exists(run):
    return (RES / run / "stats_stats.csv").exists() and (RES / run / "metrics.json").exists()


def rows_by_name(run):
    with open(RES / run / "stats_stats.csv", newline="") as f:
        return {r["Name"]: r for r in csv.DictReader(f)}


def timeline(runs, title, fname, kill=None):
    runs = [r for r in runs if exists(r[0])]
    fig, axes = plt.subplots(3, len(runs), figsize=(4.7 * len(runs) + 1, 8.4),
                             sharey="row", squeeze=False)
    for col, (run, label) in enumerate(runs):
        t0, hist = history(run)
        m = metrics(run)
        mins = [(float(r["Timestamp"]) - t0) / 60 for r in hist]

        ax = axes[0][col]
        ax.plot(mins, [float(r["User Count"]) for r in hist], color=GREY)
        ax.set(title=label, ylabel="Users")
        ax2 = ax.twinx()
        ax2.step([(when(p["t"]) - t0) / 60 for p in m["instances"]],
                 [p["v"] for p in m["instances"]], where="post", color=BLUE, lw=2.2)
        ax2.set_ylim(0, 7)
        ax2.set_ylabel("Instances in service", color=BLUE)
        ax2.grid(False)
        ax2.spines["right"].set_visible(True)

        ax = axes[1][col]
        ax.plot([(when(p["t"]) - t0) / 60 for p in m["alb_target_response_s"]],
                [p["v"] * 1000 for p in m["alb_target_response_s"]], "o-", color=GREEN,
                label="average")
        if m.get("alb_p95_s"):
            ax.plot([(when(p["t"]) - t0) / 60 for p in m["alb_p95_s"]],
                    [p["v"] * 1000 for p in m["alb_p95_s"]], "s-", color=ORANGE,
                    label="p95")
        ax.set(ylabel="Server response (ms)")
        ax.legend(frameon=False, loc="upper right")

        ax = axes[2][col]
        ax.plot(mins, [float(r["Requests/s"]) for r in hist], color=BLUE, label="requests/s")
        ax.plot(mins, [float(r["Failures/s"]) for r in hist], color=RED, label="failures/s")
        ax.set(ylabel="Per second", xlabel="Minutes since the test started")
        ax.legend(frameon=False, loc="upper right")

        if kill and run in kill:
            k = (when(kill[run]) - t0) / 60
            for row in range(3):
                axes[row][col].axvline(k, color=RED, ls="--", lw=1.2)
            axes[0][col].text(k, 0, " instance killed", color=RED, va="bottom", fontsize=9)
    fig.suptitle(title, y=0.995)
    fig.tight_layout()
    fig.savefig(OUT / fname, bbox_inches="tight")
    plt.close(fig)


def served(run):
    """Latency of requests the API actually served (shed 429 rows excluded)."""
    r = rows_by_name(run)
    out = {}
    for name in ("/availability", "/book"):
        if name in r:
            out[name] = {"requests": int(r[name]["Request Count"]),
                         "p50": float(r[name]["50%"]), "p95": float(r[name]["95%"]),
                         "p99": float(r[name]["99%"])}
    shed = sum(int(v["Request Count"]) for k, v in r.items() if "shed 429" in k)
    served_n = sum(v["requests"] for v in out.values())
    out["shed_requests"] = shed
    out["served_requests"] = served_n
    out["shed_share"] = shed / (shed + served_n) if shed + served_n else 0
    return out


def fig_shed(reactive, shed):
    a, b = served(reactive), served(shed)
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.8))
    labels = ["R3 reactive,\nno shedding", "R5 reactive,\nwith shedding"]
    for i, name in enumerate(("/availability", "/book")):
        ax[i].bar(labels, [a[name]["p50"], b[name]["p50"]], color=GREEN, label="median",
                  width=0.35, align="edge")
        ax[i].bar(labels, [a[name]["p95"], b[name]["p95"]], color=ORANGE, label="p95",
                  width=-0.35, align="edge")
        ax[i].set(title=f"{name}: latency of served requests", ylabel="Milliseconds")
        ax[i].legend(frameon=False)
    ax[2].bar(labels, [a["shed_share"] * 100, b["shed_share"] * 100], color=RED)
    ax[2].set(title="Requests turned away (429)", ylabel="% of all requests")
    fig.tight_layout()
    fig.savefig(OUT / "fig_e_shed.png", bbox_inches="tight")
    plt.close(fig)


def failure_summary(run):
    t0, hist = history(run)
    kill = json.loads((RES / run / "kill.json").read_text())
    k = (when(kill["kill_utc"]) - t0) / 60
    bad = [(float(r["Timestamp"]) - t0) / 60 for r in hist if float(r["Failures/s"]) > 0]
    agg = aggregated(run)
    m = metrics(run)
    return {
        **agg,
        "kill_minute": round(k, 2),
        "first_failure_minute": round(min(bad), 2) if bad else None,
        "last_failure_minute": round(max(bad), 2) if bad else None,
        "failure_window_s": round((max(bad) - min(bad)) * 60) if bad else 0,
        "min_instances": min(p["v"] for p in m["instances"]),
        "elb_5xx": sum(p["v"] for p in m.get("alb_elb_5xx", [])),
        "target_5xx": sum(p["v"] for p in m.get("alb_target_5xx", [])),
    }


def main():
    summary = {}

    c1 = {}
    for run in ("c1-correctness", "c1-correctness-3instances"):
        f = RES / run / "c1.json"
        if f.exists():
            d = json.loads(f.read_text())
            c1[run] = {"passed": d["passed"], "total": d["total"]}
    summary["c1"] = c1

    ramp_runs = [("ramp-r0-fixed1", "R0: 1 fixed instance"),
                 ("ramp-r1-fixed3", "R1: 3 fixed instances"),
                 ("ramp-r2-autoscale", "R2: autoscaling 1 to 6")]
    timeline(ramp_runs, "Ramp: 10 to 1,500 users over 10 minutes", "fig_d_ramp.png")
    summary["ramp"] = {}
    for run, _ in ramp_runs:
        if exists(run):
            m = metrics(run)
            summary["ramp"][run] = {**aggregated(run), "peak_instances": peak(m["instances"]),
                                    "db_cpu_peak": peak(m["db_cpu"]),
                                    "app_cpu_peak": peak(m["app_cpu_avg"])}

    burst_runs = [("burst-reactive", "R3: reactive (1 instance)"),
                  ("burst-prescaled", "R4 (manual): 4 instances at start"),
                  ("burst-scheduled", "R4: scheduled action to 4"),
                  ("burst-shed", "R5: reactive + load shedding")]
    timeline(burst_runs, "Tatkal burst compared: reactive, pre-scaled, scheduled, shedding",
             "fig_g_burst_all.png")
    if exists("burst-scheduled"):
        sched = json.loads((RES / "burst-scheduled" / "schedule.json").read_text())
        t0, _ = history("burst-scheduled")
        m = metrics("burst-scheduled")
        summary["scheduled"] = {**aggregated("burst-scheduled"), "schedule": sched,
                                "peak_instances": peak(m["instances"]),
                                "db_cpu_peak": peak(m["db_cpu"])}
    if exists("burst-shed") and exists("burst-reactive"):
        fig_shed("burst-reactive", "burst-shed")
        summary["shed"] = {"reactive": served("burst-reactive"), "shedding": served("burst-shed")}

    fail = "failure-kill-1instance"
    if exists(fail):
        kill = json.loads((RES / fail / "kill.json").read_text())
        timeline([(fail, "Failure test: 3 instances, one killed")],
                 "Failure test: one of three instances terminated under load",
                 "fig_f_failure.png", kill={fail: kill["kill_utc"]})
        summary["failure"] = failure_summary(fail)

    summary["consistency"] = {}
    for f in sorted(RES.glob("*/verify-db.json")):
        try:
            summary["consistency"][f.parent.name] = json.loads(f.read_text())
        except json.JSONDecodeError:
            pass

    (OUT / "summary_extra.json").write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps(summary, indent=1, default=str))


if __name__ == "__main__":
    main()
