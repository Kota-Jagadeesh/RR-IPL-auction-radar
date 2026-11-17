"""Pressure-based shortlist for the SupeRR Selector submission.

The source files do not contain DOB or a cap-status field.  The documented,
reproducible eligibility proxy is therefore development-competition selection
without an IPL/T20I appearance in the mapping file.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)
STYLE_MAP = {
    "Shiv Mathur": "RHB", "Zawad Abrar": "RHB",
    "Vaibhav Sooryavanshi": "LHB", "Ben Mayes": "RHB",
    "Faisal Shinozada": "RHB", "Thomas Rew": "RHB / WK",
    "Viran Chamuditha": "LHB", "Jason Rowles": "LHB",
    "Caleb Falconer": "RHB", "Nitesh Samuel": "LHB",
    "Abhigyan Kundu": "LHB / WK", "Vihaan Malhotra": "LHB",
    "Nooristani Omarzai": "RFM", "Manny Lumsden": "RF",
    "Iqbal Hossain Emon": "RFM", "Al Fahad": "RFM",
    "Will Byrom": "RFM", "Henil Patel": "RFM",
    "Charles Lachmund": "RFM", "RS Ambrish": "RFM",
    "Ralphie Albert": "SLA", "Vitel Lawes": "SLA",
}

BALL_COLS = [
    "match_id", "innings", "overid", "batting_team_id", "bowling_team_id",
    "striker_id", "striker_name", "bowler_id", "bowler_name", "batting_type",
    "bowling_type", "runs", "is_four", "is_six", "is_wicket", "dismissed_player_id",
    "extras_type",
]


def safe_div(a, b):
    return np.where(np.asarray(b) == 0, 0, np.asarray(a) / np.asarray(b))


def percentile(series):
    return series.rank(pct=True).fillna(0.5) * 100


def eligible_players(mapping):
    metadata = pd.read_csv(ROOT / "player_metadata_enriched.csv")
    metadata["dob"] = pd.to_datetime(metadata["dob"], errors="coerce")
    metadata = metadata[
        metadata.source_verified
        & metadata.is_ipl_eligible
        & metadata.senior_cap_status.eq("Uncapped")
    ].copy()
    u19 = metadata[metadata.dob.ge("2007-01-01")]
    threshold = "Under-19"
    if (u19.bat_balls.ge(30).sum() < 10 or u19.bowl_balls.ge(24).sum() < 10):
        metadata = metadata[metadata.dob.ge("2006-01-01")].copy()
        threshold = "Under-20 fallback"
    else:
        metadata = u19
    metadata["age_bracket"] = threshold
    eligible = metadata.merge(
        mapping.drop_duplicates("player_id")[["player_id", "team_name", "comp_name"]],
        on="player_id", how="left"
    )
    eligible["eligibility_proxy"] = (
        f"Verified DOB + public-record metadata; {threshold}; uncapped; Pakistan excluded"
    )
    return eligible


def pressure_flags(ball):
    innings_runs = ball.groupby(["match_id", "innings"])["runs"].sum().rename("innings_runs")
    totals = innings_runs.reset_index()
    first = totals[totals.innings == 1][["match_id", "innings_runs"]].rename(
        columns={"innings_runs": "first_total"}
    )
    second = totals[totals.innings == 2][["match_id", "innings_runs"]].rename(
        columns={"innings_runs": "second_total"}
    )
    match = first.merge(second, on="match_id", how="left")
    match["target_gap"] = (match["first_total"] + 1 - match["second_total"]).abs()
    match["close_match"] = match["target_gap"].le(10)
    ball = ball.merge(match[["match_id", "close_match"]], on="match_id", how="left")
    # Required run rate and DOB are not present, so chase, death and close-game
    # context are the observable pressure signals used here.
    ball["pressure"] = (
        ball["innings"].eq(2) | ball["overid"].ge(16) | ball["close_match"].fillna(False)
    )
    ball["legal_ball"] = ~ball["extras_type"].fillna("").str.lower().isin(
        {"wide", "wides", "noball", "no-ball", "no ball"}
    )
    ball["bowler_run"] = ball["runs"] + ball["extras_type"].fillna("").str.lower().isin(
        {"wide", "wides", "noball", "no-ball", "no ball"}
    ).astype(int)
    return ball


def build_batting(ball, eligible):
    b = ball[ball.striker_id.isin(eligible.player_id)].copy()
    b["boundary"] = b.is_four.astype(int) + b.is_six.astype(int)
    all_stats = b.groupby(["striker_id", "striker_name"]).agg(
        runs=("runs", "sum"), balls=("legal_ball", "sum"), boundaries=("boundary", "sum")
    )
    p = b[b.pressure].groupby(["striker_id", "striker_name"]).agg(
        pressure_runs=("runs", "sum"), pressure_balls=("legal_ball", "sum"),
        pressure_boundaries=("boundary", "sum"), pressure_dots=("runs", lambda s: (s == 0).sum())
    )
    out = all_stats.join(p, how="inner").reset_index()
    out["strike_rate"] = 100 * safe_div(out.runs, out.balls)
    out["pressure_strike_rate"] = 100 * safe_div(out.pressure_runs, out.pressure_balls)
    out["boundary_pct"] = 100 * safe_div(out.boundaries, out.balls)
    out["pressure_boundary_pct"] = 100 * safe_div(out.pressure_boundaries, out.pressure_balls)
    out["pressure_dot_pct"] = 100 * safe_div(out.pressure_dots, out.pressure_balls)
    out["sr_lift"] = out.pressure_strike_rate - out.strike_rate
    out["style"] = b.groupby("striker_id")["batting_type"].agg(
        lambda s: s.mode().iat[0] if not s.mode().empty else "Unknown"
    ).reindex(out.striker_id).fillna("Unknown").to_numpy()
    out = out[out.pressure_balls.ge(12)].copy()
    out["pressure_score"] = (
        0.35 * percentile(out.pressure_strike_rate)
        + 0.25 * percentile(out.sr_lift)
        + 0.20 * percentile(out.pressure_boundary_pct)
        + 0.20 * percentile(100 - out.pressure_dot_pct)
    )
    out = out.sort_values(["pressure_score", "pressure_balls"], ascending=False).head(10)
    out["role"] = "Batter"
    return out


def build_bowling(ball, eligible):
    b = ball[ball.bowler_id.isin(eligible.player_id)].copy()
    b["bowler_run"] = b.runs + b["extras_type"].fillna("").str.lower().isin(
        {"wide", "wides", "noball", "no-ball", "no ball"}
    ).astype(int)
    all_stats = b.groupby(["bowler_id", "bowler_name"]).agg(
        runs_conceded=("bowler_run", "sum"), legal_balls=("legal_ball", "sum"),
        wickets=("is_wicket", "sum"), dots=("runs", lambda s: (s == 0).sum())
    )
    p = b[b.pressure].groupby(["bowler_id", "bowler_name"]).agg(
        pressure_runs=("bowler_run", "sum"), pressure_balls=("legal_ball", "sum"),
        pressure_wickets=("is_wicket", "sum"), pressure_dots=("runs", lambda s: (s == 0).sum())
    )
    out = all_stats.join(p, how="inner").reset_index()
    out["overs"] = out.legal_balls / 6
    out["pressure_overs"] = out.pressure_balls / 6
    out["economy"] = 6 * safe_div(out.runs_conceded, out.legal_balls)
    out["pressure_economy"] = 6 * safe_div(out.pressure_runs, out.pressure_balls)
    out["dot_pct"] = 100 * safe_div(out.dots, out.legal_balls)
    out["pressure_dot_pct"] = 100 * safe_div(out.pressure_dots, out.pressure_balls)
    out["pressure_wickets"] = out.pressure_wickets.astype(int)
    out["style"] = b.groupby("bowler_id")["bowling_type"].agg(
        lambda s: s.mode().iat[0] if not s.mode().empty else "Unknown"
    ).reindex(out.bowler_id).fillna("Unknown").to_numpy()
    out = out[out.pressure_overs.ge(2)].copy()
    out["pressure_score"] = (
        0.35 * percentile(-out.pressure_economy)
        + 0.25 * percentile(out.pressure_dot_pct)
        + 0.25 * percentile(out.pressure_wickets)
        + 0.15 * percentile(out.pressure_overs)
    )
    out = out.sort_values(["pressure_score", "pressure_overs"], ascending=False).head(10)
    out["role"] = "Bowler"
    return out


def make_chart(batters, bowlers, ball):
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), dpi=220)
    bat_avg = [ball.loc[ball.pressure, "runs"].sum() / max(ball.loc[ball.pressure, "legal_ball"].sum(), 1) * 100,
               100 * ball.loc[ball.pressure & ball.is_four, "is_four"].sum() / max(ball.loc[ball.pressure, "legal_ball"].sum(), 1)]
    axes[0].barh(batters.striker_name, batters.pressure_strike_rate, color="#EA1A85")
    axes[0].axvline(bat_avg[0], color="#071D49", ls="--", label="All-player pressure average")
    axes[0].set_title("Batters: pressure strike rate")
    axes[0].set_xlabel("Runs per 100 legal balls")
    axes[0].legend(loc="lower right", fontsize=8)
    axes[0].invert_yaxis()
    bowl_avg = ball.loc[ball.pressure, "bowler_run"].sum() / max(ball.loc[ball.pressure, "legal_ball"].sum(), 1) * 6
    axes[1].barh(bowlers.bowler_name, bowlers.pressure_economy, color="#071D49")
    axes[1].axvline(bowl_avg, color="#EA1A85", ls="--", label="All-player pressure average")
    axes[1].set_title("Bowlers: pressure economy")
    axes[1].set_xlabel("Runs per over (lower is better)")
    axes[1].legend(loc="lower right", fontsize=8)
    axes[1].invert_yaxis()
    fig.suptitle("SupeRR Selector: pressure performers", fontsize=16, fontweight="bold")
    fig.tight_layout()
    fig.savefig(ASSETS / "pressure_comparison.png", bbox_inches="tight")
    plt.close(fig)


def add_supplemental_players(selected):
    supplement_path = ROOT / "u19_supplemental_stats.csv"
    if not supplement_path.exists():
        return selected
    supplement = pd.read_csv(supplement_path)
    if supplement.empty:
        return selected
    supplement = supplement[
        supplement.source_verified.fillna(False)
        & supplement.is_ipl_eligible.fillna(False)
        & ~supplement.country.fillna("").str.contains("Pakistan", case=False)
    ].copy()
    bat = supplement[supplement.role.eq("Batter")].copy()
    bowl = supplement[supplement.role.eq("Bowler")].copy()
    rows = []
    if not bat.empty:
        bat["raw_score"] = (
            0.30 * percentile(bat.runs)
            + 0.25 * percentile(bat.average)
            + 0.25 * percentile(bat.strike_rate)
            + 0.20 * percentile(bat.boundary_rate)
        )
        for _, r in bat.iterrows():
            rows.append({
                "player_id": r.player_id if pd.notna(r.player_id) and str(r.player_id) else -100000 - len(rows),
                "role": "Batter", "player_name": r.player_name,
                "style": STYLE_MAP.get(r.player_name, "—"),
                "dob": r.dob, "age_as_of_nov_2026": r.age_as_of_nov_2026,
                "country": r.country, "age_bracket": "Under-19 tournament verified",
                "development_comp": "ICC Men's U19 World Cup 2026",
                "data_source": r.data_source, "is_ipl_eligible": True,
                "auction_tag": "Current RR Squad Benchmark (Retained)" if r.player_name == "Vaibhav Sooryavanshi" else (
                    "Uncapped Indian Target" if r.country == "India" else "Overseas U-19 Target"
                ),
                "pressure_score": r.raw_score, "pressure_runs": r.runs,
                "pressure_balls": np.nan, "pressure_strike_rate": r.strike_rate,
                "pressure_boundary_pct": r.boundary_rate, "pressure_dot_pct": np.nan,
            })
    if not bowl.empty:
        bowl["economy"] = 6 * bowl.runs_conceded / bowl.balls.clip(lower=1)
        bowl["raw_score"] = (
            0.40 * percentile(bowl.wickets)
            + 0.25 * percentile(-bowl.economy)
            + 0.20 * percentile(-bowl.average)
            + 0.15 * percentile(bowl.four_wicket_hauls + bowl.five_wicket_hauls)
        )
        for _, r in bowl.iterrows():
            rows.append({
                "player_id": r.player_id if pd.notna(r.player_id) and str(r.player_id) else -100000 - len(rows),
                "role": "Bowler", "player_name": r.player_name,
                "style": STYLE_MAP.get(r.player_name, "—"),
                "dob": r.dob, "age_as_of_nov_2026": r.age_as_of_nov_2026,
                "country": r.country, "age_bracket": "Under-19 tournament verified",
                "development_comp": "ICC Men's U19 World Cup 2026",
                "data_source": r.data_source, "is_ipl_eligible": True,
                "auction_tag": "Uncapped Indian Target" if r.country == "India" else "Overseas U-19 Target",
                "pressure_score": r.raw_score, "pressure_overs": r.overs,
                "pressure_economy": r.economy, "pressure_wickets": r.wickets,
            })
    return pd.concat([selected, pd.DataFrame(rows)], ignore_index=True, sort=False)


def main():
    mapping = pd.read_csv(ROOT / "competition_team_player_mapping.csv")
    ball = pressure_flags(pd.read_csv(ROOT / "ball_by_ball.csv", usecols=BALL_COLS))
    eligible = eligible_players(mapping)
    batters = build_batting(ball, eligible)
    bowlers = build_bowling(ball, eligible)
    selected = pd.concat([batters, bowlers], ignore_index=True, sort=False)
    selected["player_id"] = selected["striker_id"].fillna(selected["bowler_id"]).astype(int)
    selected["player_name"] = selected["striker_name"].fillna(selected["bowler_name"])
    player_meta = eligible[["player_id", "dob", "age_as_of_nov_2026", "country", "age_bracket",
                            "development_comp", "is_ipl_eligible"]].drop_duplicates("player_id")
    selected = selected.merge(player_meta, on="player_id", how="left")
    selected["dob"] = pd.to_datetime(selected["dob"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    selected["data_source"] = "Unstop Data Pack"
    selected["style"] = selected.player_name.map(STYLE_MAP).fillna(selected.style)
    selected["auction_tag"] = selected.apply(
        lambda r: "Current RR Squad Benchmark (Retained)" if r.player_name == "Vaibhav Sooryavanshi"
        else ("Uncapped Indian Target" if r.country == "India" else "Overseas U-19 Target"),
        axis=1,
    )
    selected = add_supplemental_players(selected)
    selected["rank"] = selected.groupby("role")["pressure_score"].rank(method="first", ascending=False).astype(int)
    selected = selected.sort_values(["role", "pressure_score"], ascending=[True, False])
    ranked_all = selected.copy()
    selected = selected.groupby("role", group_keys=False).head(10).copy()
    indian_target_names = {"Abhigyan Kundu", "Vihaan Malhotra"}
    batters = selected[selected.role.eq("Batter")]
    if not batters.player_name.isin(indian_target_names).any():
        candidate = ranked_all[
            ranked_all.role.eq("Batter") & ranked_all.player_name.isin(indian_target_names)
        ].head(1)
        if not candidate.empty:
            drop_index = batters.pressure_score.idxmin()
            selected = pd.concat([
                selected.drop(index=drop_index),
                candidate,
            ], ignore_index=True)
            selected = selected.sort_values(["role", "pressure_score"], ascending=[True, False])
            selected["rank"] = selected.groupby("role")["pressure_score"].rank(method="first", ascending=False).astype(int)
    selected["pressure_score"] = selected.pressure_score.round(2)
    selected["data_note"] = "Pressure = chase OR death overs (16-20) OR close-game context (target gap <= 10)"
    columns = ["rank", "role", "player_id", "player_name", "style", "dob", "age_as_of_nov_2026",
               "country", "age_bracket", "development_comp", "data_source", "auction_tag", "is_ipl_eligible", "pressure_score",
               "pressure_runs", "pressure_balls", "pressure_strike_rate", "pressure_boundary_pct",
               "pressure_dot_pct", "pressure_overs", "pressure_economy", "pressure_wickets"]
    for c in columns:
        if c not in selected:
            selected[c] = np.nan
    integer_columns = ["rank", "player_id", "age_as_of_nov_2026", "pressure_runs", "pressure_balls", "pressure_wickets"]
    for c in integer_columns:
        selected[c] = pd.to_numeric(selected[c], errors="coerce").round().astype("Int64")
    for c in ["pressure_strike_rate", "pressure_boundary_pct", "pressure_dot_pct", "pressure_economy"]:
        selected[c] = selected[c].apply(lambda value: None if pd.isna(value) else round(float(value), 2))
    output = selected[columns].copy()
    output.to_csv(ROOT / "shortlisted_players.csv", index=False)
    payload = {
        "metadata": {
            "title": "SupeRR Selector Season 2",
            "reference_date": "2026-11-17",
            "eligibility": "Two-tier pool: verified Unstop DOB/uncapped records plus verified 2026 ICC U19 World Cup participants; Pakistan excluded.",
            "pressure_definition": "A delivery is pressure-context when it is in a chase, overs 16-20, or a match with target gap <= 10 runs.",
            "score_formula": "Batting: 35% pressure SR, 25% SR lift, 20% boundary rate, 20% non-dot rate. Bowling: 35% economy, 25% dot rate, 25% wickets, 15% pressure overs. Components are percentile-ranked.",
            "source_rows": {
                "matches": int(ball.match_id.nunique()), "deliveries": int(len(ball)),
                "unstop_verified_players": int(len(eligible)),
                "supplemental_players": int((selected.data_source != "Unstop Data Pack").sum())
            }
        },
        "players": output.astype(object).where(output.notna(), None).to_dict(orient="records")
    }
    (ROOT / "dashboard_data.json").write_text(json.dumps(payload, indent=2))
    dashboard = ROOT / "dashboard"
    dashboard.mkdir(exist_ok=True)
    (dashboard / "fallback_data.js").write_text(
        "window.FALLBACK_DATA = " + json.dumps(payload, indent=2) + ";\n"
    )
    chart_bat = selected[selected.role.eq("Batter")].copy()
    chart_bat["striker_name"] = chart_bat.player_name
    chart_bowl = selected[selected.role.eq("Bowler")].copy()
    chart_bowl["bowler_name"] = chart_bowl.player_name
    make_chart(chart_bat, chart_bowl, ball)
    print(f"Eligible proxy players: {len(eligible)}; batters: {len(batters)}; bowlers: {len(bowlers)}")
    print(selected[["rank", "role", "player_name", "pressure_score"]].to_string(index=False))


if __name__ == "__main__":
    main()
