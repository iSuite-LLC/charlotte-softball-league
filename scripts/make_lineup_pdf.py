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
# Origin (0,0) = bottom-left of plot. Home plate at (5, 1.2). 45-deg foul lines
# extend to foul poles at (1.5, 4.7) and (8.5, 4.7). Fence is a semicircle
# centered at (5, 4.7) radius 3.5, bulging up to (5, 8.2).
POSITIONS = {
    "P":   (5.0, 3.2),
    "C":   (5.0, 0.7),
    "1B":  (7.0, 3.7),
    "2B":  (6.0, 4.9),
    "SS":  (4.0, 4.9),
    "3B":  (3.0, 3.7),
    "LF":  (2.0, 5.7),
    "LCF": (3.7, 6.7),
    "RCF": (6.3, 6.7),
    "RF":  (8.0, 5.7),
}


def fmt_time(t):
    """Format a 'HH:MM' 24-hour string as 12-hour with AM/PM. Empty passes through."""
    if not t:
        return ""
    try:
        h, m = map(int, t.split(":"))
    except (ValueError, AttributeError):
        return t
    period = "PM" if h >= 12 else "AM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {period}"


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
        sub += f"  ·  {fmt_time(sched['time'])}"
    fig.text(0.5, 0.93, sub, ha="center", fontsize=11)

    # --- Batting order (top half) ---
    ax_bat = fig.add_axes([0.08, 0.49, 0.84, 0.40])
    ax_bat.axis("off")
    ax_bat.text(0.0, 1.0, "BATTING ORDER", fontsize=13, fontweight="bold",
                transform=ax_bat.transAxes)

    # Build table data: header row + one row per batter.
    header = ["#", "Player", "AB", "H", "HR", "RBI", "R", "BB", "K"]
    rows = []
    for entry in lineup.get("batting_order", []):
        nick = entry["nickname"]
        jersey = entry.get("jersey", jersey_by_nick.get(nick, "?"))
        real = name_by_nick.get(nick, "")
        tag = "  [EH]" if entry.get("eh_only") else ""
        player_cell = f"{nick}  #{jersey}  ({real}){tag}"
        rows.append([str(entry["order"]), player_cell, "", "", "", "", "", "", ""])

    # Column widths as a fraction of the axes width.
    # 0.4 + 3.0 + 7*0.5 = 6.9 inches over 7.14 inches of body width
    # → normalize each by 6.9 so they sum to ~1.0.
    col_widths = [w / 6.9 for w in (0.4, 3.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5)]

    table = ax_bat.table(
        cellText=[header] + rows,
        colWidths=col_widths,
        cellLoc="center",
        loc="upper left",
        bbox=[0.0, 0.0, 1.0, 0.93],  # leave top 7% of axes for "BATTING ORDER" heading
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    # Style header row: bold text on all 9 columns.
    n_cols = len(header)
    for col in range(n_cols):
        cell = table[(0, col)]
        cell.set_text_props(weight="bold")

    # Style Player column (column index 1): monospace + left-aligned.
    # Cells are keyed (row_index, col_index); row 0 is header, rows 1..N are batters.
    n_rows = len(rows)
    for row in range(0, n_rows + 1):  # include header row so "Player" header is also monospace
        cell = table[(row, 1)]
        cell.set_text_props(family="monospace", size=8)
        # Left-align by setting the cell's text horizontal alignment.
        cell.get_text().set_horizontalalignment("left")
        # Add small left padding so text doesn't kiss the left border.
        # matplotlib has no native cell padding; achieve it with a leading space.
        existing = cell.get_text().get_text()
        cell.get_text().set_text(" " + existing)

    # --- Diamond (bottom half) ---
    ax_dia = fig.add_axes([0.08, 0.06, 0.84, 0.40])
    ax_dia.set_xlim(0, 10)
    ax_dia.set_ylim(0, 10)
    ax_dia.set_aspect("equal")
    ax_dia.axis("off")
    ax_dia.text(0.0, 1.02, "DEFENSE  (4-OF alignment)",
                fontsize=13, fontweight="bold", transform=ax_dia.transAxes)

    # Fence: semicircle behind outfielders, from foul pole to foul pole
    import math
    arc_pts = [(5 + 3.5 * math.cos(math.pi * (1 - t)),
                4.7 + 3.5 * math.sin(math.pi * (1 - t)))
               for t in [i / 50 for i in range(51)]]
    ax_dia.plot([p[0] for p in arc_pts], [p[1] for p in arc_pts],
                color="black", linewidth=1.0)
    # Foul lines: home plate to foul poles
    ax_dia.plot([5, 1.5], [1.2, 4.7], color="black", linewidth=0.8)
    ax_dia.plot([5, 8.5], [1.2, 4.7], color="black", linewidth=0.8)

    # Infield diamond
    diamond = Polygon([(5, 1.2), (7, 3.2), (5, 5.2), (3, 3.2)],
                      closed=True, fill=False, edgecolor="black", linewidth=1.2)
    ax_dia.add_patch(diamond)
    # Pitcher's mound
    ax_dia.add_patch(Circle((5, 3.2), 0.2, fill=False, edgecolor="black"))

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
