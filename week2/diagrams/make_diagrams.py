"""Generate the Week 2 report diagrams (PNG) with matplotlib.

Run:  python week2/diagrams/make_diagrams.py
Outputs go next to this script.
"""
import os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = os.path.dirname(os.path.abspath(__file__))

NAVY, BLUE, LIGHT, GREY, AMBER, GREEN = "#1F3864", "#2F5597", "#D9E2F3", "#F2F2F2", "#FFF2CC", "#E2F0D9"


def box(ax, x, y, w, h, text, fc=LIGHT, ec=BLUE, fs=9, bold=False, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=fc, ec=ec, lw=1.4, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color="#111111", wrap=True)


def arrow(ax, x1, y1, x2, y2, style="-|>", ls="-", color=NAVY):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14,
                                 lw=1.4, color=color, ls=ls))


def canvas(w, h, title, subtitle):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    ax.text(0.15, h - 0.3, title, fontsize=13, fontweight="bold", color=NAVY, va="top")
    ax.text(0.15, h - 0.75, subtitle, fontsize=8.5, color="#444444", va="top", style="italic")
    return fig, ax


def case_diagram():
    fig, ax = canvas(11, 7.2, "Figure 1. Reservation architecture around IRCTC and CRIS",
                     "Conceptual view built from PIB, CRIS and IRCTC Annual Report FY2024-25. Arrows show access, not protocols.")
    # users
    box(ax, 0.3, 4.9, 2.3, 1.1, "Online passengers\nIRCTC website, Rail Connect,\nRailOne app\n(86.38% of reserved tickets)", GREY, "#7F7F7F", 8.5)
    box(ax, 0.3, 3.2, 2.3, 1.1, "Reservation counters,\nauthorised agents", GREY, "#7F7F7F", 8.5)
    # edge
    box(ax, 3.2, 3.9, 2.6, 2.3,
        "Edge protection\nCDN: ~67% of hits, ~91% of\ntraffic volume offloaded\nBot mitigation: ~30% of traffic\nblocked (Akamai per Ministry)\nWAF, firewalls, IPS, ADC", AMBER, "#BF9000", 8.2)
    # NGeT
    box(ax, 6.4, 3.9, 2.0, 2.3,
        "IRCTC NGeT\n(e-ticketing)\nData centre at CRIS,\nChanakyapuri, New Delhi\nRecord: 30,155 tickets/min\n(12 Mar 2025, 10:01)", LIGHT, BLUE, 8.2)
    # PRS legacy
    box(ax, 6.4, 0.8, 4.3, 2.4,
        "PRS / CONCERT (CRIS)\n3-tier client-server, distributed database\n4 data centres: New Delhi, Mumbai,\nKolkata, Chennai (databases split by zone)\nGeneration deployed 2010: Itanium, OpenVMS\n~32,000 bookings/min, 4 lakh enquiries/min", LIGHT, BLUE, 8.2)
    # new PRS
    box(ax, 8.9, 3.9, 1.95, 2.3,
        "New PRS (CRIS)\n'cloud-enabled'\nTarget: 1.5 lakh\nbookings/min\nInternals not\npublished", GREEN, "#548235", 8.2, ls="--")
    # demand shaping
    box(ax, 0.3, 0.8, 5.5, 1.7,
        "Demand shaping (policy layer)\nAadhaar auth for Tatkal (1 Jul 2025), OTP (15 Jul 2025)\nAgents blocked first 30 min of each window\n3.6 crore IDs deactivated in FY25; 3.02 crore since Jan 2025",
        AMBER, "#BF9000", 8.2)
    arrow(ax, 2.6, 5.45, 3.2, 5.2)
    arrow(ax, 5.8, 5.05, 6.4, 5.05)
    arrow(ax, 8.4, 5.05, 8.9, 5.05, ls="--")
    arrow(ax, 7.4, 3.9, 7.4, 3.2)
    arrow(ax, 2.6, 3.75, 6.4, 2.6)
    arrow(ax, 3.0, 2.5, 3.9, 3.9, ls="--", color="#BF9000")
    ax.text(0.15, 0.25, "Dashed = announced or policy element. Sources: PIB 29 Jun 2025, 11 Dec 2025, 6 Aug 2026; CRIS PRS page; IRCTC Annual Report FY2024-25.",
            fontsize=7.5, color="#444444")
    fig.savefig(os.path.join(OUT, "fig1-case-architecture.png"), dpi=170, bbox_inches="tight")
    plt.close(fig)


def exercise_diagram():
    fig, ax = canvas(11, 6.3, "Figure 2. Group 40 exercise architecture (our design, not IRCTC's)",
                     "Autoscaled booking API behind a load balancer, load-tested to plot response time against instance count.")
    box(ax, 0.3, 2.3, 1.9, 1.5, "Load generator\nLocust or k6\n(ramp up, hold,\nramp down)", GREY, "#7F7F7F", 8.8)
    box(ax, 2.8, 2.3, 1.9, 1.5, "Load balancer\n(health checks,\nround robin)", LIGHT, BLUE, 8.8)
    ax.add_patch(FancyBboxPatch((5.3, 1.2), 3.0, 3.7, boxstyle="round,pad=0.02,rounding_size=0.12", fc="white", ec=BLUE, lw=1.4, ls="--"))
    ax.text(6.8, 4.65, "Auto Scaling group (min 1, max N)", ha="center", fontsize=8.8, fontweight="bold", color=NAVY)
    for i, y in enumerate([3.45, 2.4, 1.35]):
        box(ax, 5.6, y, 2.4, 0.85, f"API instance {i + 1}\navailability, health, book", LIGHT, BLUE, 8.2)
    box(ax, 8.9, 2.3, 1.9, 1.5, "Shared seat\ninventory\n(atomic update,\nno per-instance counters)", GREEN, "#548235", 8.2)
    box(ax, 2.8, 0.3, 5.5, 0.6, "Metrics: CPU or requests per instance, instance count, latency (avg, p95), errors, cost", AMBER, "#BF9000", 8.2)
    arrow(ax, 2.2, 3.05, 2.8, 3.05)
    arrow(ax, 4.7, 3.05, 5.6, 3.9)
    arrow(ax, 4.7, 3.05, 5.6, 2.85)
    arrow(ax, 4.7, 3.05, 5.6, 1.8)
    arrow(ax, 8.0, 2.85, 8.9, 3.05)
    arrow(ax, 6.8, 1.2, 6.8, 0.9, ls="--", color="#BF9000")
    arrow(ax, 5.0, 0.9, 5.3, 1.7, ls="--", color="#BF9000")
    ax.text(3.2, 1.3, "scaling policy adds\nor removes instances", fontsize=7.8, color="#BF9000")
    fig.savefig(os.path.join(OUT, "fig2-exercise-architecture.png"), dpi=170, bbox_inches="tight")
    plt.close(fig)


def capacity_chart():
    labels = ["Previous\ne-ticketing", "NGeT\n(early)", "NGeT FY25\nrecord (observed)", "PRS today\n(PIB, stated)", "New PRS\n(target)"]
    vals = [2000, 7200, 30155, 32000, 150000]
    colors = ["#A6A6A6", "#8EA9DB", BLUE, BLUE, "#70AD47"]
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    bars = ax.bar(labels, vals, color=colors, edgecolor="#333333", linewidth=0.8)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 2500, f"{v:,}", ha="center", fontsize=9, fontweight="bold")
    ax.set_ylabel("Bookings per minute")
    ax.set_ylim(0, 170000)
    ax.set_title("Figure 3. Reported booking capacity levels (not measured by us)", fontsize=11, color=NAVY, loc="left", fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", labelsize=8.5)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f"{int(x):,}"))
    fig.text(0.01, -0.02, "Sources: IRCTC Annual Report FY2024-25 (2,000; 7,200; 30,155 record 12 Mar 2025); PIB 29 Jun 2025 (32,000; 1.5 lakh target). "
             "Early levels have no stated year.", fontsize=7, color="#444444")
    fig.savefig(os.path.join(OUT, "fig3-capacity-levels.png"), dpi=170, bbox_inches="tight")
    plt.close(fig)


def docker_diagram():
    fig, ax = canvas(11, 3.2, "", "")
    box(ax, 0.2, 1.1, 1.9, 1.3, "Repository\nDockerfile +\nAPI code", GREY, "#7F7F7F", 8.5)
    box(ax, 2.5, 1.1, 1.9, 1.3, "docker build\n(laptop, then\nsame image on AWS)", LIGHT, BLUE, 8.5)
    box(ax, 4.8, 1.1, 1.7, 1.3, "Image registry\n(Amazon ECR)", LIGHT, BLUE, 8.5)
    ax.add_patch(FancyBboxPatch((6.95, 0.35), 2.35, 2.45, boxstyle="round,pad=0.02,rounding_size=0.12", fc="white", ec=BLUE, lw=1.4, ls="--"))
    ax.text(8.12, 2.6, "Auto Scaling group", ha="center", fontsize=8.2, fontweight="bold", color=NAVY)
    box(ax, 7.1, 1.55, 2.05, 0.8, "EC2 instance\ndocker run: API container", LIGHT, BLUE, 7.6)
    box(ax, 7.1, 0.5, 2.05, 0.8, "EC2 instance\ndocker run: API container", LIGHT, BLUE, 7.6)
    box(ax, 9.65, 1.1, 1.2, 1.3, "Shared\nseat DB\n(not in the\ncontainer)", GREEN, "#548235", 8.0)
    arrow(ax, 2.1, 1.75, 2.5, 1.75)
    arrow(ax, 4.4, 1.75, 4.8, 1.75)
    ax.text(5.65, 0.45, "launch template:\ninstall Docker, pull,\nrun on start-up", ha="center", fontsize=7.5, color="#BF9000")
    arrow(ax, 6.5, 1.75, 7.1, 1.95, color="#BF9000", ls="--")
    arrow(ax, 6.5, 1.5, 7.1, 0.95, color="#BF9000", ls="--")
    arrow(ax, 9.15, 1.95, 9.65, 1.85)
    arrow(ax, 9.15, 0.95, 9.65, 1.45)
    ax.text(0.2, 0.2, "Local check before AWS: docker compose (API + database + Locust).", fontsize=7.5, color="#444444")
    fig.savefig(os.path.join(OUT, "fig4-docker-architecture.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    docker_diagram()
    case_diagram()
    exercise_diagram()
    capacity_chart()
    print("done")
