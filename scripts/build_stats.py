"""Derive stats_summary from game_logs and write back to data.json.

Run from repo root: `python scripts/build_stats.py`
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_JSON = REPO_ROOT / "data.json"


def compute_player_summary(lines):
    """Aggregate a list of per-game player_line dicts into one season summary."""
    totals = {
        "G": len(lines),
        "PA": sum(l["PA"] for l in lines),
        "AB": sum(l["AB"] for l in lines),
        "1B": sum(l["1B"] for l in lines),
        "2B": sum(l["2B"] for l in lines),
        "3B": sum(l["3B"] for l in lines),
        "HR": sum(l["HR"] for l in lines),
        "BB": sum(l["BB"] for l in lines),
        "K":  sum(l["K"] for l in lines),
        "RBI": sum(l["RBI"] for l in lines),
        "R":  sum(l["R"] for l in lines),
    }
    H = totals["1B"] + totals["2B"] + totals["3B"] + totals["HR"]
    TB = totals["1B"] + 2 * totals["2B"] + 3 * totals["3B"] + 4 * totals["HR"]
    AB = totals["AB"]
    PA_ob_denom = AB + totals["BB"]  # simplified OBP (no HBP/SF tracked)
    obp_raw = (H + totals["BB"]) / PA_ob_denom if PA_ob_denom > 0 else 0.0
    slg_raw = TB / AB if AB > 0 else 0.0
    AVG = round(H / AB, 3) if AB > 0 else 0.0
    OBP = round(obp_raw, 3)
    SLG = round(slg_raw, 3)
    OPS = round(obp_raw + slg_raw, 3)
    totals.update({"H": H, "AVG": AVG, "OBP": OBP, "SLG": SLG, "OPS": OPS})
    return totals


def main():
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    by_player = {}
    for gl in data.get("game_logs", []):
        for player, line in gl.get("player_lines", {}).items():
            by_player.setdefault(player, []).append(line)
    summary = {p: compute_player_summary(lines) for p, lines in by_player.items()}
    data["stats_summary"] = summary
    DATA_JSON.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote stats_summary for {len(summary)} players")


if __name__ == "__main__":
    main()
