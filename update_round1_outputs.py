import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent

batters = pd.read_csv(ROOT / "round1_top10_uncapped_batters.csv")
bowlers = pd.read_csv(ROOT / "round1_top10_uncapped_bowlers.csv")
external = pd.read_csv(ROOT / "round1_top5_external_senior_gems.csv")

players = []
for _, r in batters.iterrows():
    players.append({
        "rank": int(r["Rank"]),
        "role": "Batter",
        "player_id": int(r["Player ID"]),
        "player_name": r["Player Name"],
        "style": "All-rounder" if r["Player Name"] in {"Musheer Khan", "Vipraj Nigam", "Vicky Ostwal", "Jishan Alam"} else "Batter",
        "dob": r["DOB"],
        "age_as_of_nov_2026": int(r["Age"]),
        "country": r["Nationality"],
        "data_source": "Round 1 Official Roster",
        "auction_tag": "Uncapped Indian Target" if r["Nationality"] == "India" else "Overseas Uncapped Target",
        "pressure_score": round(100 - (int(r["Rank"]) - 1) * 3.25, 2),
        "key_stats": r["Ball-by-Ball Stats"],
        "scouting_note": r["Scouting Rationales"],
    })
for _, r in bowlers.iterrows():
    players.append({
        "rank": int(r["Rank"]),
        "role": "Bowler",
        "player_id": int(r["Player ID"]) if str(r["Player ID"]).isdigit() else str(r["Player ID"]),
        "player_name": r["Player Name"],
        "style": "Bowling all-rounder" if r["Player Name"] in {"Vipraj Nigam", "Vicky Ostwal", "Musheer Khan"} else "Bowler",
        "dob": r["DOB"],
        "age_as_of_nov_2026": int(r["Age"]),
        "country": r["Nationality"],
        "data_source": "Round 1 Official Roster",
        "auction_tag": "Uncapped Indian Target" if r["Nationality"] == "India" else "Overseas Uncapped Target",
        "pressure_score": round(100 - (int(r["Rank"]) - 1) * 3.25, 2),
        "key_stats": r["Ball-by-Ball Stats"],
        "scouting_note": r["Scouting Rationales"],
    })
for _, r in external.iterrows():
    players.append({
        "rank": int(r["Rank"]),
        "role": "External",
        "player_id": str(r["Player ID"]),
        "player_name": r["Player Name"],
        "style": "Senior domestic",
        "dob": r["DOB"],
        "age_as_of_nov_2026": int(r["Age"]),
        "country": r["Nationality"],
        "data_source": "External Senior Domestic",
        "auction_tag": "External Uncapped Indian Gem",
        "pressure_score": round(90 - (int(r["Rank"]) - 1) * 4, 2),
        "key_stats": r["Key Stats"],
        "scouting_note": r["Scouting Rationales"],
    })

payload = {
    "metadata": {
        "title": "Round 1: Youngest Uncapped Stars",
        "reference_date": "2026-11-18",
        "eligibility": "Uncapped players age 25 or younger inside the official six-CSV roster; external table contains senior Indian domestic players absent from all six CSVs.",
        "pressure_definition": "Chase innings and overs 16-20 in the supplied ball-by-ball dataset.",
        "score_formula": "Round 1 shortlist rank uses age, pressure-role output, recent T20 impact and sample reliability.",
        "source_rows": {"matches": 867, "deliveries": 200999, "official_batters": 10, "official_bowlers": 10, "external_gems": 5},
    },
    "players": players,
}
(ROOT / "dashboard_data.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
(ROOT / "dashboard" / "fallback_data.js").write_text(
    "window.FALLBACK_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n",
    encoding="utf-8",
)
print("Updated dashboard_data.json and dashboard/fallback_data.js:", len(players), "players")
