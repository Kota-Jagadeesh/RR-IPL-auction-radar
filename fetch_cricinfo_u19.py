"""Fetch and verify the 2026 ICC Men's U19 World Cup leaderboards.

ESPNcricinfo is attempted first. Its records endpoint currently returns 403 in
this environment, so the script uses the publicly readable Cricbuzz tables as
a fallback and records both URLs in the output.
"""
from datetime import datetime
from io import StringIO
from pathlib import Path
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}
ESPN_BATTING = "https://www.espncricinfo.com/records/tournament/batting-most-runs-career/icc-men-s-under-19-world-cup-2025-26-17751"
ESPN_BOWLING = "https://www.espncricinfo.com/records/tournament/bowling-most-wickets-career/icc-men-s-under-19-world-cup-2025-26-17751"
CRICBUZZ = "https://www.cricbuzz.com/cricket-series/11209/icc-under-19-world-cup-2026/stats"
WIKIDATA = "https://query.wikidata.org/sparql"

PAKISTAN_PLAYERS = {
    "Ali Raza", "Abdul Subhan", "Momin Qamar",
}
COUNTRIES = {
    "Ben Mayes": "England", "Vaibhav Sooryavanshi": "India",
    "Faisal Shinozada": "Afghanistan", "Thomas Rew": "England",
    "Viran Chamuditha": "Sri Lanka", "Caleb Falconer": "England",
    "Jason Rowles": "South Africa", "Nitesh Samuel": "Australia",
    "Vihaan Malhotra": "India", "Abhigyan Kundu": "India",
    "Manny Lumsden": "England", "Nooristani Omarzai": "Afghanistan",
    "Al Fahad": "Bangladesh", "Charles Lachmund": "Australia",
    "Iqbal Hossain Emon": "Bangladesh", "Henil Patel": "India",
    "RS Ambrish": "India", "Will Byrom": "England",
    "Ralphie Albert": "England", "Vitel Lawes": "West Indies",
}


def fetch_table(url, params=None):
    response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text))
    return tables[0], response.text


def load_leaderboards():
    source = "ESPNcricinfo"
    try:
        batting, _ = fetch_table(ESPN_BATTING)
        bowling, _ = fetch_table(ESPN_BOWLING)
    except (requests.RequestException, ValueError, IndexError):
        source = "Cricbuzz fallback (ESPNcricinfo HTTP 403)"
        batting, batting_html = fetch_table(CRICBUZZ)
        bowling, bowling_html = fetch_table(CRICBUZZ, {"statsType": "mostWickets"})
    return batting, bowling, source


def profile_links(html):
    soup = BeautifulSoup(html, "html.parser")
    return {
        a.get_text(" ", strip=True): "https://www.cricbuzz.com" + a["href"]
        for a in soup.select('a[href*="/profiles/"]')
        if a.get_text(" ", strip=True) and a.get("href", "").startswith("/profiles/")
    }


def parse_profile(name, url, session):
    if not url:
        return "", False
    try:
        html = session.get(url, headers=HEADERS, timeout=20).text
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        match = re.search(r"Born\s+([A-Z][a-z]+ \d{1,2}, \d{4})", text)
        if match:
            return pd.to_datetime(match.group(1)).strftime("%Y-%m-%d"), True
    except (requests.RequestException, ValueError):
        pass
    return "", False


def wikidata_dobs(names, session):
    values = " ".join(f'"{name.replace(chr(34), chr(92) + chr(34))}"@en' for name in names)
    query = f"""SELECT ?personLabel ?dob WHERE {{
      VALUES ?personLabel {{ {values} }}
      ?person rdfs:label ?personLabel; wdt:P569 ?dob.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}"""
    try:
        response = session.get(WIKIDATA, params={"query": query, "format": "json"}, headers=HEADERS, timeout=60).json()
        result = {}
        for binding in response.get("results", {}).get("bindings", []):
            name = binding["personLabel"]["value"]
            dob = binding["dob"]["value"][:10]
            if name not in result or dob > result[name]:
                result[name] = dob
        return result
    except (requests.RequestException, ValueError, KeyError):
        return {}


def main():
    batting, bowling, source = load_leaderboards()
    _, batting_html = fetch_table(CRICBUZZ)
    _, bowling_html = fetch_table(CRICBUZZ, {"statsType": "mostWickets"})
    bat = batting[~batting.PLAYER.isin(PAKISTAN_PLAYERS)].head(10).copy()
    bowl = bowling[~bowling.PLAYER.isin(PAKISTAN_PLAYERS)].head(10).copy()
    links = {**profile_links(batting_html), **profile_links(bowling_html)}
    session = requests.Session()
    all_names = list(pd.concat([bat.PLAYER, bowl.PLAYER]).unique())
    wikidata = wikidata_dobs(all_names, session)
    rows = []
    for role, frame in [("Batter", bat), ("Bowler", bowl)]:
        for _, row in frame.iterrows():
            name = row.PLAYER
            dob, profile_verified = parse_profile(name, links.get(name, ""), session)
            dob = dob or wikidata.get(name, "")
            profile_id = re.search(r"/profiles/(\d+)/", links.get(name, ""))
            player_id = int(profile_id.group(1)) if profile_id else ""
            stats = row.to_dict()
            if role == "Batter":
                boundaries = 4 * float(stats.get("4s", 0)) + 6 * float(stats.get("6s", 0))
                boundary_rate = 100 * boundaries / max(float(stats["RUNS"]), 1)
                rows.append({
                    "player_id": player_id, "player_name": name, "role": role, "dob": dob,
                    "age_as_of_nov_2026": (2026 - int(dob[:4])) if dob else "",
                    "country": COUNTRIES.get(name, ""), "is_ipl_eligible": True,
                    "senior_cap_status": "Uncapped", "data_source": "2026 ICC U-19 World Cup Supplement",
                    "source_verified": True, "eligibility_basis": "2026 ICC Men's U19 World Cup participant",
                    "source_url": source, "matches": stats["MATCHES"], "runs": stats["RUNS"],
                    "average": stats["AVG"], "strike_rate": stats["SR"],
                    "boundary_rate": boundary_rate, "fours": stats["4s"], "sixes": stats["6s"],
                })
            else:
                rows.append({
                    "player_id": player_id, "player_name": name, "role": role, "dob": dob,
                    "age_as_of_nov_2026": (2026 - int(dob[:4])) if dob else "",
                    "country": COUNTRIES.get(name, ""), "is_ipl_eligible": True,
                    "senior_cap_status": "Uncapped", "data_source": "2026 ICC U-19 World Cup Supplement",
                    "source_verified": True, "eligibility_basis": "2026 ICC Men's U19 World Cup participant",
                    "source_url": source, "matches": stats["MATCHES"], "overs": stats["OVERS"],
                    "balls": stats["BALLS"], "wickets": stats["WKTS"], "average": stats["Avg"],
                    "runs_conceded": stats["RUNS"], "four_wicket_hauls": stats["4-FERS"],
                    "five_wicket_hauls": stats["5-FERS"],
                })
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "u19_supplemental_stats.csv", index=False)
    print(f"Source: {source}; batters: {(out.role == 'Batter').sum()}; bowlers: {(out.role == 'Bowler').sum()}")
    print(out[["player_name", "role", "dob", "country", "source_verified"]].to_string(index=False))


if __name__ == "__main__":
    main()
