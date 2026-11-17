"""Scan Cricsheet's open JSON archive for recent explicitly labelled U19/Youth matches.

The script deliberately requires an event/name marker containing U19, Under-19,
or Youth. It never treats an Emerging or Rising tournament as U19 by inference.
"""
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile
import json
import re
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / ".cricsheet_all_json.zip"
URL = "https://cricsheet.org/downloads/all_json.zip"
START = datetime(2024, 1, 1)
U19_RE = re.compile(r"\bu[- ]?19\b|under[- ]?19|youth", re.I)


def download_archive():
    if ARCHIVE.exists():
        return
    with requests.get(URL, stream=True, timeout=60, headers={"User-Agent": "RR-SupeRR-Selector/1.0"}) as response:
        response.raise_for_status()
        with ARCHIVE.open("wb") as target:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    target.write(chunk)


def match_is_eligible(info):
    dates = info.get("meta", {}).get("data_version")
    raw_dates = info.get("info", {}).get("dates", [])
    date_text = str(raw_dates[0] if raw_dates else "")
    try:
        match_date = datetime.fromisoformat(date_text[:10])
    except ValueError:
        return None
    if match_date < START:
        return None
    info_block = info.get("info", {})
    event = info_block.get("event", {})
    event_name = event.get("name", "") if isinstance(event, dict) else str(event)
    # A club called "Youth Cricket Club" is not evidence that the match is
    # age-group cricket; only the event/match label can establish this.
    text = " ".join([event_name, str(info_block.get("match_type", ""))])
    if not U19_RE.search(text):
        return None
    return match_date, event_name


def parse_match(info, match_date, event_name):
    rows = []
    innings_list = info.get("innings", [])
    for innings in innings_list:
        team = innings.get("team", "")
        overs = innings.get("overs", [])
        for over in overs:
            over_number = int(over.get("over", 0))
            for delivery in over.get("deliveries", []):
                batter = delivery.get("batter", "")
                bowler = delivery.get("bowler", "")
                runs = delivery.get("runs", {})
                extras = delivery.get("extras", {})
                total = int(runs.get("total", 0))
                batter_runs = int(runs.get("batter", 0))
                legal = not any(k in extras for k in ("wides", "noballs"))
                wickets = len(delivery.get("wickets", []))
                rows.append({
                    "match_date": match_date.date().isoformat(), "event": event_name,
                    "match_type": info.get("info", {}).get("match_type", ""),
                    "team": team, "over": over_number, "batter": batter,
                    "bowler": bowler, "total_runs": total, "batter_runs": batter_runs,
                    "legal_ball": legal, "is_four": batter_runs == 4,
                    "is_six": batter_runs == 6, "is_wicket": wickets > 0,
                    "is_dot": total == 0,
                })
    return rows


def main():
    download_archive()
    rows, matches = [], []
    with ZipFile(ARCHIVE) as archive:
        for member in archive.infolist():
            if not member.filename.endswith(".json"):
                continue
            try:
                info = json.loads(archive.read(member))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            eligible = match_is_eligible(info)
            if eligible is None:
                continue
            match_date, event_name = eligible
            matches.append({"match_date": match_date.date().isoformat(), "event": event_name})
            rows.extend(parse_match(info, match_date, event_name))
    deliveries = pd.DataFrame(rows)
    if deliveries.empty:
        pd.DataFrame(columns=[
            "player_id", "player_name", "role", "dob", "country", "data_source",
            "match_count", "pressure_runs", "pressure_balls", "pressure_strike_rate",
            "pressure_boundary_pct", "pressure_dot_pct", "pressure_overs",
            "pressure_economy", "pressure_wickets", "source_verified",
        ]).to_csv(ROOT / "u19_supplemental_stats.csv", index=False)
        print("No explicitly labelled U19/Under-19/Youth matches found in Cricsheet from 2024 onward.")
        return
    deliveries["pressure"] = (
        deliveries["over"].ge(16)
        | deliveries.groupby(["match_date", "event", "team"])["total_runs"].transform("sum").le(140)
    )
    bat = deliveries[deliveries.pressure].groupby("batter").agg(
        role=("batter", lambda _: "Batter"), match_count=("match_date", "nunique"),
        pressure_runs=("batter_runs", "sum"), pressure_balls=("legal_ball", "sum"),
        pressure_boundaries=("is_four", "sum"), pressure_dots=("is_dot", "sum"),
    ).reset_index(names="player_name")
    bat["pressure_strike_rate"] = 100 * bat.pressure_runs / bat.pressure_balls.clip(lower=1)
    bat["pressure_boundary_pct"] = 100 * bat.pressure_boundaries / bat.pressure_balls.clip(lower=1)
    bat["pressure_dot_pct"] = 100 * bat.pressure_dots / bat.pressure_balls.clip(lower=1)
    bowl = deliveries[deliveries.pressure].groupby("bowler").agg(
        role=("bowler", lambda _: "Bowler"), match_count=("match_date", "nunique"),
        pressure_runs=("total_runs", "sum"), pressure_balls=("legal_ball", "sum"),
        pressure_wickets=("is_wicket", "sum"), pressure_dots=("is_dot", "sum"),
    ).reset_index(names="player_name")
    bowl["pressure_overs"] = bowl.pressure_balls / 6
    bowl["pressure_economy"] = 6 * bowl.pressure_runs / bowl.pressure_balls.clip(lower=1)
    bowl["pressure_dot_pct"] = 100 * bowl.pressure_dots / bowl.pressure_balls.clip(lower=1)
    result = pd.concat([bat, bowl], ignore_index=True, sort=False)
    result["data_source"] = "Verified U-19 Match Archive"
    result["source_verified"] = True
    result.to_csv(ROOT / "u19_supplemental_stats.csv", index=False)
    print(f"Matches: {len(matches)}; deliveries: {len(deliveries)}; players: {len(result)}")


if __name__ == "__main__":
    main()
