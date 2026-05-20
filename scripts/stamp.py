"""Set season.lastUpdated in data.json to the current ET timestamp.

Run before every commit/push so the header timestamp on the live site reflects
the deploy. Idempotent — safe to run any time.

Usage: python scripts/stamp.py
"""
import json
from datetime import datetime
from pathlib import Path

DATA_JSON = Path(__file__).resolve().parent.parent / "data.json"


def stamp(data):
    """Mutate `data` in place, setting season.lastUpdated to now (ET)."""
    now = datetime.now()
    data.setdefault("season", {})["lastUpdated"] = (
        now.strftime("%Y-%m-%d ") + now.strftime("%I:%M %p").lstrip("0") + " ET"
    )
    return data["season"]["lastUpdated"]


def main():
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    value = stamp(data)
    DATA_JSON.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Stamped: {value}")


if __name__ == "__main__":
    main()
