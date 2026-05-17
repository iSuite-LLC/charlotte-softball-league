"""Generate a print-ready PDF lineup card from data.json.

Usage: python scripts/make_lineup_pdf.py YYYY-MM-DD

Writes lineups/YYYY-MM-DD-lineup.pdf (US Letter, portrait, B&W).
"""
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # no display needed
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from matplotlib.backends.backend_pdf import PdfPages

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_JSON = REPO_ROOT / "data.json"
LINEUPS_DIR = REPO_ROOT / "lineups"

# Position coordinates on the diamond, in arbitrary units (0..10 both axes).
# Origin (0,0) = bottom-left of plot; home plate is bottom-center.
POSITIONS = {
    "P":   (5.0, 4.5),
    "C":   (5.0, 2.0),
    "1B":  (7.0, 4.0),
    "2B":  (6.0, 5.5),
    "SS":  (4.0, 5.5),
    "3B":  (3.0, 4.0),
    "LF":  (1.5, 8.0),
    "LCF": (3.5, 8.5),
    "RCF": (6.5, 8.5),
    "RF":  (8.5, 8.0),
}


def find_lineup(data, date):
    for ln in data.get("lineups", []):
        if ln.get("date") == date:
            return ln
    raise SystemExit(f"No lineup found in data.json for date {date}")


def find_schedule_entry(data, date):
    for s in data.get("schedule", []):
        if s.get("date") == date:
            return s
    return {}


def make_pdf(date):
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    lineup = find_lineup(data, date)
    sched = find_schedule_entry(data, date)

    # Build a nickname -> full-name lookup for the batting order
    name_by_nick = {p["nickname"]: p["name"] for p in data["roster"]}
    jersey_by_nick = {p["nickname"]: p["jersey"] for p in data["roster"]}

    fig = plt.figure(figsize=(8.5, 11))  # US Letter
    fig.patch.set_facecolor("white")

    # --- Header ---
    fig.text(0.5, 0.96, f"IMI SOFTBALL — Game {lineup.get('game', '?')}",
             ha="center", fontsize=18, fontweight="bold")
    sub = f"{date}"
    if sched.get("opponent") and sched["opponent"] != "TBD":
        sub += f"  ·  vs. {sched['opponent']}"
    if sched.get("location"):
        sub += f"  ·  {sched['location']}"
    if sched.get("time"):
        sub += f"  ·  {sched['time']}"
    fig.text(0.5, 0.93, sub, ha="center", fontsize=11)

    # --- Batting order (top half) ---
    ax_bat = fig.add_axes([0.08, 0.55, 0.84, 0.34])
    ax_bat.axis("off")
    ax_bat.text(0.0, 1.0, "BATTING ORDER", fontsize=13, fontweight="bold",
                transform=ax_bat.transAxes)
    y = 0.92
    for entry in lineup.get("batting_order", []):
        nick = entry["nickname"]
        jersey = entry.get("jersey", jersey_by_nick.get(nick, "?"))
        real = name_by_nick.get(nick, "")
        tag = "  [EH]" if entry.get("eh_only") else ""
        line = f"{entry['order']:>2}.  #{jersey:<3}  {nick:<14}  ({real}){tag}"
        ax_bat.text(0.0, y, line, fontsize=11, family="monospace",
                    transform=ax_bat.transAxes)
        y -= 0.07

    # --- Diamond (bottom half) ---
    ax_dia = fig.add_axes([0.08, 0.06, 0.84, 0.46])
    ax_dia.set_xlim(0, 10)
    ax_dia.set_ylim(0, 10)
    ax_dia.set_aspect("equal")
    ax_dia.axis("off")
    ax_dia.text(0.0, 1.02, "DEFENSE  (4-OF alignment)",
                fontsize=13, fontweight="bold", transform=ax_dia.transAxes)

    # Field outline (foul lines + arc)
    ax_dia.plot([5, 0.5], [2, 9.5], color="black", linewidth=0.8)
    ax_dia.plot([5, 9.5], [2, 9.5], color="black", linewidth=0.8)
    # Simple curved fence
    import math
    arc_pts = [(5 + 4.7 * math.cos(math.pi * (1 - t)),
                2 + 4.7 * math.sin(math.pi * (1 - t)))
               for t in [i / 50 for i in range(51)]]
    ax_dia.plot([p[0] for p in arc_pts], [p[1] for p in arc_pts],
                color="black", linewidth=0.8)

    # Infield diamond
    diamond = Polygon([(5, 2), (7, 4), (5, 6), (3, 4)],
                      closed=True, fill=False, edgecolor="black", linewidth=1.2)
    ax_dia.add_patch(diamond)
    # Pitcher's mound
    ax_dia.add_patch(Circle((5, 4.5), 0.25, fill=False, edgecolor="black"))

    # Place player labels at each position
    for pos, (x, y) in POSITIONS.items():
        player = lineup.get("defense", {}).get(pos, "?")
        ax_dia.text(x, y, player, ha="center", va="center", fontsize=10,
                    fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                              edgecolor="black", linewidth=0.5))
        ax_dia.text(x, y - 0.45, pos, ha="center", va="center", fontsize=8,
                    color="black")

    LINEUPS_DIR.mkdir(exist_ok=True)
    output = LINEUPS_DIR / f"{date}-lineup.pdf"
    with PdfPages(output) as pdf:
        pdf.savefig(fig)
    plt.close(fig)
    print(f"Wrote {output}")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/make_lineup_pdf.py YYYY-MM-DD")
    make_pdf(sys.argv[1])


if __name__ == "__main__":
    main()
