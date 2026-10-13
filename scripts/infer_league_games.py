"""Infer who played whom (and the scores) from two standings snapshots.

Usage:  python3 scripts/infer_league_games.py PREV.json NEW.json DATE [--known KNOWN.json]
  PREV/NEW: JSON lists of {team, W, L, T, PF, PA} (the standings.teams arrays).
  DATE:     game-night date to stamp on inferred games (YYYY-MM-DD).
  KNOWN:    optional list of games already known (e.g. ours from the recap),
            same shape as standings.games: {a, a_score, b, b_score}.
Prints JSON {"games": [...], "unresolved": {team: remaining delta}}.
Exit code 0 when every team's weekly change is explained, 1 when ambiguous.

Method: per-team weekly delta (games, W/L/T, PF, PA). Subtract known games,
then repeatedly take a team with exactly one game left and look for opponents
that could have been its other side (exact mirror if that opponent also has one
game left; otherwise enough PF/PA/W/L/T room). A unique candidate becomes a
game; ties are left unresolved for a human to call.
"""
import json, sys

KEYS = ("W", "L", "T", "PF", "PA")

def deltas(prev, new):
    p = {t["team"]: t for t in prev}
    out = {}
    for t in new:
        o = p.get(t["team"], {k: 0 for k in KEYS})
        d = {k: t[k] - o.get(k, 0) for k in KEYS}
        d["G"] = d["W"] + d["L"] + d["T"]
        if any(d[k] < 0 for k in KEYS):
            raise SystemExit(f"{t['team']}: standings went backwards {d}")
        if d["G"]:
            out[t["team"]] = d
    return out

def subtract(d, team, us, them):
    r = d[team]
    r["G"] -= 1; r["PF"] -= us; r["PA"] -= them
    r["W" if us > them else "L" if us < them else "T"] -= 1

def fits(r, us, them):
    """Can remaining delta r absorb one game scored us-them?"""
    k = "W" if us > them else "L" if us < them else "T"
    if r["G"] < 1 or r[k] < 1 or r["PF"] < us or r["PA"] < them:
        return False
    if r["G"] == 1:
        return r["PF"] == us and r["PA"] == them
    return True

def infer(prev, new, date, known=()):
    d = deltas(prev, new)
    games = []
    for g in known:
        for me, ms, os in ((g["a"], g["a_score"], g["b_score"]), (g["b"], g["b_score"], g["a_score"])):
            if me in d: subtract(d, me, ms, os)
    progress = True
    while progress:
        progress = False
        for team, r in sorted(d.items()):
            if r["G"] != 1:
                continue
            us, them = r["PF"], r["PA"]
            cands = [o for o, ro in d.items() if o != team and fits(ro, them, us)]
            if len(cands) == 1:
                opp = cands[0]
                a, b = (team, opp) if us >= them else (opp, team)
                sa, sb = (us, them) if a == team else (them, us)
                games.append({"date": date, "a": a, "a_score": sa, "b": b, "b_score": sb,
                              "source": "inferred from standings"})
                subtract(d, team, us, them); subtract(d, opp, them, us)
                progress = True
                break
    unresolved = {t: r for t, r in d.items() if any(r[k] for k in ("G", "PF", "PA"))}
    return games, unresolved

if __name__ == "__main__":
    args = sys.argv[1:]
    known = []
    if "--known" in args:
        i = args.index("--known"); known = json.load(open(args[i + 1])); del args[i:i + 2]
    prev, new, date = json.load(open(args[0])), json.load(open(args[1])), args[2]
    games, unresolved = infer(prev, new, date, known)
    print(json.dumps({"games": games, "unresolved": unresolved}, indent=2))
    sys.exit(1 if unresolved else 0)
