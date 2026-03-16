# scripts/snapshot_odds.py
import os
import sys
import csv
import json
from datetime import datetime
from pathlib import Path

import requests

API_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"


def main(out_dir: str):
    api_key = os.getenv("ODDS_API_KEY")
    if not api_key:
        print("Missing ODDS_API_KEY env var", file=sys.stderr)
        sys.exit(1)

    params = {
        "apiKey": api_key,
        "regions": "au",
                "markets": "h2h,spreads",
        "oddsFormat": "decimal",
    }

    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    csv_path = out_path / f"odds_snapshot_{ts}.csv"

    rows = []
    for event in data:
        event_id = event.get("id")
        sport_key = event.get("sport_key")
        home_team = event.get("home_team")
        away_team = event.get("away_team")
        commence_time = event.get("commence_time")
        for bk in event.get("bookmakers", []):
            bk_key = bk.get("key")
            bk_title = bk.get("title")
            last_update = bk.get("last_update")
            for market in bk.get("markets", []):
                market_key = market.get("key")
                for outcome in market.get("outcomes", []):
                    rows.append(
                        {
                            "event_id": event_id,
                            "sport_key": sport_key,
                            "home_team": home_team,
                            "away_team": away_team,
                            "commence_time": commence_time,
                            "bookmaker": bk_key,
                            "bookmaker_title": bk_title,
                            "last_update": last_update,
                            "market": market_key,
                            "outcome_name": outcome.get("name"),
                            "price": outcome.get("price"),
                            "point": outcome.get("point"),
                            "snapshot_utc": ts,
                        }
                    )

    fieldnames = list(rows[0].keys()) if rows else ["snapshot_utc", "raw_json"]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)
        else:
            writer.writerow({"snapshot_utc": ts, "raw_json": json.dumps(data)})

    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--out":
        main(sys.argv[2])
    else:
        print("Usage: python snapshot_odds.py --out <output_dir>", file=sys.stderr)
        sys.exit(1)
