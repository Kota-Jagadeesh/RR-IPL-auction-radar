"""Enrich development-player candidates with conservative public-record metadata.

The raw pack has no DOB or cap field. This script uses the development
competitions as the candidate universe, ball-volume thresholds for activity,
Wikidata's public API for identity/DOB/country, and the supplied competition
format as the cap-status signal (T20I appearance means capped in this pack).
"""
from datetime import date
from pathlib import Path
import json
import time
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / ".player_metadata_cache.json"
TODAY = date(2026, 11, 17)
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
HEADERS = {"User-Agent": "RR-SupeRR-Selector/1.0 (research script)"}


def age_on(dob):
    years = TODAY.year - dob.year
    if (TODAY.month, TODAY.day) < (dob.month, dob.day):
        years -= 1
    return years


def search_wikidata(name, session):
    params = {
        "action": "wbsearchentities", "search": f"{name} cricketer",
        "language": "en", "format": "json", "limit": 5
    }
    data = session.get(WIKIDATA_API, params=params, headers=HEADERS, timeout=20).json()
    candidates = data.get("search", [])
    if not candidates:
        params["search"] = name
        candidates = session.get(WIKIDATA_API, params=params, headers=HEADERS, timeout=20).json().get("search", [])
    for item in candidates:
        desc = (item.get("description") or "").lower()
        if "cricketer" in desc or "cricket" in desc:
            return item["id"]
    return candidates[0]["id"] if candidates else None


def get_entity(entity_id, session):
    data = session.get(
        WIKIDATA_API,
        params={"action": "wbgetentities", "ids": entity_id, "props": "claims|labels", "languages": "en", "format": "json"},
        headers=HEADERS,
        timeout=20,
    ).json()
    return data.get("entities", {}).get(entity_id, {})


def claim_value(entity, prop):
    claims = entity.get("claims", {}).get(prop, [])
    if not claims:
        return None
    value = claims[0].get("mainsnak", {}).get("datavalue", {}).get("value")
    return value


def country_label(entity, session):
    country = claim_value(entity, "P27")
    if not isinstance(country, dict):
        return ""
    entity_id = country.get("id")
    if not entity_id:
        return ""
    related = get_entity(entity_id, session)
    return related.get("labels", {}).get("en", {}).get("value", "")


def load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    return {}


def country_from_team(team_name):
    team = str(team_name).strip()
    for suffix in (" A", " XI"):
        if team.endswith(suffix):
            team = team[:-len(suffix)]
    return team if team and team not in {"India", "Hong Kong"} else team


def main():
    mapping = pd.read_csv(ROOT / "competition_team_player_mapping.csv")
    ball = pd.read_csv(ROOT / "ball_by_ball.csv", usecols=["striker_id", "bowler_id"])
    bat_counts = ball.groupby("striker_id").size()
    bowl_counts = ball.groupby("bowler_id").size()
    development = mapping[mapping.comp_name.isin({
        "Mens T20 Emerging Teams Asia Cup 2024", "Asia Cup Rising Stars 2025"
    })].copy()
    development = development[~development.team_name.str.contains("Pakistan", case=False, na=False)]
    candidates = development[
        development.player_id.map(bat_counts).fillna(0).ge(30)
        | development.player_id.map(bowl_counts).fillna(0).ge(24)
    ].drop_duplicates("player_id")
    competitions = pd.read_csv(ROOT / "competitions.csv")[["comp_id", "match_format"]]
    mapping_with_format = mapping.merge(competitions, on="comp_id", how="left")
    match_formats = mapping_with_format.groupby("player_id")["match_format"].agg(set)
    cache = load_cache()
    session = requests.Session()
    names = sorted(candidates.player_name.dropna().unique())
    values = " ".join(f'"{name.replace(chr(34), chr(92) + chr(34))}"@en' for name in names)
    sparql = f"""SELECT ?person ?personLabel ?dob ?countryLabel WHERE {{
      VALUES ?personLabel {{ {values} }}
      ?person rdfs:label ?personLabel; wdt:P569 ?dob.
      OPTIONAL {{ ?person wdt:P27 ?country. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}"""
    try:
        response = session.get(
            WIKIDATA_SPARQL, params={"query": sparql, "format": "json"},
            headers=HEADERS, timeout=60
        ).json()
        sparql_records = {}
        for binding in response.get("results", {}).get("bindings", []):
            name = binding["personLabel"]["value"]
            sparql_records[name] = {
                "dob": binding.get("dob", {}).get("value", "")[:10],
                "country": binding.get("countryLabel", {}).get("value", ""),
                "source_verified": bool(binding.get("dob")),
                "wikidata_id": binding.get("person", {}).get("value", "").rsplit("/", 1)[-1],
            }
    except (requests.RequestException, ValueError):
        sparql_records = {}
    rows = []
    for i, row in enumerate(candidates.itertuples(index=False), 1):
        pid = str(row.player_id)
        record = cache.get(pid, {})
        if not record and row.player_name in sparql_records:
            record = sparql_records[row.player_name]
            cache[pid] = record
        if not record:
            try:
                entity_id = search_wikidata(row.player_name, session)
                entity = get_entity(entity_id, session) if entity_id else {}
                dob_raw = claim_value(entity, "P569")
                dob = (dob_raw.get("time", "")[1:11] if isinstance(dob_raw, dict) else "")
                record = {
                    "wikidata_id": entity_id or "",
                    "dob": dob,
                    "country": country_label(entity, session) if entity else "",
                    "source_verified": bool(entity_id and dob),
                }
                cache[pid] = record
                time.sleep(0.08)
            except (requests.RequestException, ValueError, KeyError) as exc:
                record = {"dob": "", "country": "", "source_verified": False, "error": str(exc)}
        dob = pd.to_datetime(record.get("dob"), errors="coerce")
        capped = "T20I" in match_formats.get(row.player_id, set())
        rows.append({
            "player_id": row.player_id, "player_name": row.player_name,
            "dob": dob.strftime("%Y-%m-%d") if not pd.isna(dob) else "",
            "age_as_of_nov_2026": age_on(dob.date()) if not pd.isna(dob) else "",
            "country": record.get("country", "") or country_from_team(row.team_name),
            "country_source": "Wikidata" if record.get("country") else "Competition team mapping",
            "senior_cap_status": "Capped" if capped else "Uncapped",
            "is_ipl_eligible": not "Pakistan" in str(row.team_name),
            "bat_balls": int(bat_counts.get(row.player_id, 0)),
            "bowl_balls": int(bowl_counts.get(row.player_id, 0)),
            "development_comp": row.comp_name, "development_team": row.team_name,
            "source_verified": bool(record.get("source_verified", False)),
            "source": f"Wikidata {record.get('wikidata_id', '')}".strip(),
        })
        if i % 25 == 0:
            print(f"Processed {i}/{len(candidates)} candidates")
    CACHE.write_text(json.dumps(cache, indent=2))
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "player_metadata_enriched.csv", index=False)
    print(f"Candidates: {len(out)}; verified DOBs: {out.source_verified.sum()}")
    print("Born in 2006 or later:")
    print(out[pd.to_datetime(out.dob, errors="coerce").ge("2006-01-01")][
        ["player_id", "player_name", "dob", "age_as_of_nov_2026", "country", "senior_cap_status"]
    ].to_string(index=False))


if __name__ == "__main__":
    main()
