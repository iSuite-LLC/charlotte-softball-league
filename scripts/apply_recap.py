"""Apply a game_recap form submission to data.json.

Usage (from repo root):  python scripts/apply_recap.py path/to/recap.json [--dry-run]

recap.json is the JSON the game_recap widget sends:
  {"games": [{"game": 1, "date": "2026-10-12", "opponent": "...", "us": 8, "them": 10,
              "outcome": "L", "player_lines": {"Nick": {"PA":3,"AB":3,"1B":1,...,"errors":0}}}],
   "notes": "free text"}

What it does:
  * First recap of a new season: clears the carryover game_logs / stats_summary /
    fun_stats / lineups (they are already preserved in archive[0]).
  * Marks each schedule entry played with result {score "us-them", outcome} and attendance.
  * Upserts the game_logs entry for (game, date) - rerunning a recap overwrites, never duplicates.
  * Recomputes season.record from the schedule, rebuilds stats_summary, stamps lastUpdated.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_stats import compute_player_summary  # noqa: E402
from stamp import stamp  # noqa: E402

DATA_JSON = Path(__file__).resolve().parent.parent / "data.json"
STAT_KEYS = ["PA", "AB", "1B", "2B", "3B", "HR", "BB", "K", "RBI", "R", "errors"]


def apply(data, recap):
    report = []
    if not any(g.get("status") == "played" for g in data["schedule"]):
        prior = (data.get("archive") or [{}])[0]
        if data.get("game_logs") and not prior.get("game_logs"):
            raise SystemExit("Refusing to reset: archive[0] has no game_logs backup.")
        data["game_logs"], data["stats_summary"] = [], {}
        data["fun_stats"], data["lineups"] = {}, []
        report.append("First game of the season: cleared carryover stats (kept in archive).")

    for g in recap["games"]:
        if g.get("outcome") not in ("W", "L", "T"):
            raise SystemExit(f"Game {g['game']}: outcome must be W, L or T")
        sched = next((s for s in data["schedule"]
                      if s.get("game") == g["game"] and s.get("date") == g["date"]), None)
        if sched is None:
            raise SystemExit(f"No schedule entry for game {g['game']} on {g['date']}")
        lines = {}
        for nick, line in g["player_lines"].items():
            clean = {k: int(line.get(k, 0)) for k in STAT_KEYS}
            clean["innings"] = {}
            if line.get("sub"):
                clean["sub"] = True
            lines[nick] = clean
        sched["status"] = "played"
        sched["result"] = {"score": f"{g['us']}-{g['them']}", "outcome": g["outcome"]}
        sched["attendance"] = list(lines)
        logs = data.setdefault("game_logs", [])
        logs[:] = [l for l in logs if not (l["game"] == g["game"] and l["date"] == g["date"])]
        logs.append({"game": g["game"], "date": g["date"], "player_lines": lines})
        logs.sort(key=lambda l: (l["date"], l["game"]))
        report.append(f"Game {g['game']} vs {sched['opponent']}: {g['outcome']} {g['us']}-{g['them']}, "
                      f"{len(lines)} players")

    rec = {"W": 0, "L": 0}
    for s in data["schedule"]:
        o = (s.get("result") or {}).get("outcome")
        if s.get("status") == "played" and o:
            rec[o] = rec.get(o, 0) + 1
    data["season"]["record"] = rec

    by_player = {}
    for gl in data["game_logs"]:
        for p, line in gl["player_lines"].items():
            by_player.setdefault(p, []).append(line)
    data["stats_summary"] = {p: compute_player_summary(ls) for p, ls in by_player.items()}
    stamp(data)
    rec_txt = "-".join(str(rec[k]) for k in ("W", "L", "T") if k in rec)
    report.append(f"Season record now {rec_txt}; stats for {len(by_player)} players.")
    return report


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    recap = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    report = apply(data, recap)
    if "--dry-run" not in sys.argv:
        DATA_JSON.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("\n".join(report))
    if recap.get("notes"):
        print("NOTES:", recap["notes"])


if __name__ == "__main__":
    main()
