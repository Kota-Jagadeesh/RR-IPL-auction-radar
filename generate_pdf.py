"""Create the submission-ready scouting report from analysis outputs."""
from pathlib import Path
import json
import textwrap
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
)

ROOT = Path(__file__).resolve().parent
PINK, BLUE = colors.HexColor("#EA1A85"), colors.HexColor("#071D49")


def note(row):
    if row["role"] == "Batter":
        if row.get("data_source") == "Unstop Data Pack":
            return f"{row['player_name']} combines a {row['pressure_strike_rate']:.1f} pressure strike rate with {row['pressure_balls']:.0f} pressure balls. The profile points to a batter who keeps scoring options open when the innings is closing."
        return f"{row['player_name']} finished the World Cup supplement with a {row['pressure_strike_rate']:.1f} strike rate and {row['pressure_runs']:.0f} pressure-weighted runs. That combination of output and age makes him a clear RR development watch."
    if row.get("data_source") == "Unstop Data Pack":
        return f"{row['player_name']} operates at {row['pressure_economy']:.2f} pressure economy with {row['pressure_wickets']:.0f} pressure wickets. That blend of control and wicket threat is the type of repeatable skill RR can trust in a tight spell."
    return f"{row['player_name']} took {row['pressure_wickets']:.0f} wickets in the World Cup supplement at {row['pressure_economy']:.2f} runs per over. The wicket volume gives RR a credible starting point for a powerplay or middle-overs role."


def table_for(rows):
    data = [["Rank", "Player", "DOB / age", "Country", "Source", "Score", "Key pressure output"]]
    for _, r in rows.iterrows():
        if r["role"] == "Batter":
            if r.get("data_source") == "Unstop Data Pack":
                key = f"SR {r['pressure_strike_rate']:.1f} | balls {r['pressure_balls']:.0f}"
            else:
                key = f"SR {r['pressure_strike_rate']:.1f} | runs {r['pressure_runs']:.0f}"
        else:
            key = f"Econ {r['pressure_economy']:.2f} | wkts {r['pressure_wickets']:.0f}"
        age = "" if pd.isna(r.get("age_as_of_nov_2026")) else f"{int(r['age_as_of_nov_2026'])}"
        source = "Unstop" if r.get("data_source") == "Unstop Data Pack" else "U19 supplement"
        data.append([int(r["rank"]), r["player_name"], f"{r.get('dob', '')}\n({age})", r.get("country", "") or "Unresolved", source, f"{r['pressure_score']:.1f}", key])
    t = Table(data, colWidths=[0.35*inch, 1.25*inch, 0.95*inch, 0.9*inch, 0.85*inch, 0.55*inch, 1.55*inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d6dbe5")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f2f6")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def main():
    payload = json.loads((ROOT / "dashboard_data.json").read_text())
    players = pd.DataFrame(payload["players"])
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleRR", parent=styles["Title"], textColor=BLUE, fontSize=24, leading=28, spaceAfter=12))
    styles.add(ParagraphStyle(name="HeadingRR", parent=styles["Heading2"], textColor=PINK, fontSize=15, leading=18, spaceBefore=12, spaceAfter=8))
    styles.add(ParagraphStyle(name="BodyRR", parent=styles["BodyText"], fontSize=9.5, leading=14, alignment=TA_LEFT, spaceAfter=8))
    styles.add(ParagraphStyle(name="SmallRR", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#44516a"), spaceAfter=5))
    doc = SimpleDocTemplate(str(ROOT / "RR_SupeRR_Selector_Submission.pdf"), pagesize=A4, rightMargin=42, leftMargin=42, topMargin=38, bottomMargin=38)
    story = [
        Paragraph("SupeRR Selector Season 2", styles["TitleRR"]),
        Paragraph("A pressure-first shortlist for Rajasthan Royals", styles["Heading2"]),
        Paragraph("Executive summary", styles["HeadingRR"]),
        Paragraph("The auction is not won by finding talent only when the game is comfortable. It is won by finding young players whose best skills survive a chase, the last five overs, and a match that is still in the balance. This shortlist uses the supplied ball-by-ball record to identify development-level players who have not appeared in the supplied IPL or T20I mapping, then ranks their repeatable output in pressure contexts.", styles["BodyRR"]),
        Paragraph("The goal is not to label a prospect after one highlight. Minimum pressure samples, baseline comparisons, and separate batting and bowling scores keep the list practical for scouting conversations.", styles["BodyRR"]),
        Paragraph("Methodology in plain English", styles["HeadingRR"]),
        Paragraph("The files do not include date of birth or a formal capped/uncapped field. Candidate players were therefore enriched from public records, then checked against the supplied competition mapping. The final pool requires a verified DOB, an uncapped status in the supplied formats, enough ball-by-ball sample, and no Pakistan/Pakistan A team mapping.", styles["BodyRR"]),
        Paragraph("Data Engineering & Multi-Source Enrichment", styles["HeadingRR"]),
        Paragraph("The raw Unstop pack supplied ball-by-ball pressure evidence for Shiv Mathur and Zawad Abrar but no DOB field. We enriched those profiles through public records, then added the 2026 ICC Men's U19 World Cup leaderboards from a public structured tournament table after ESPNcricinfo's records endpoint returned HTTP 403. Pakistan U19 players were removed, DOBs were checked through public player profiles/Wikidata, and the two cohorts were normalized into one 0–100 pressure-and-impact score. The source column in every row keeps the audit trail visible.", styles["BodyRR"]),
        Paragraph("A delivery counts as pressure-context if it is in the second innings of a match (a chase), in overs 16–20, or in a match where the final target gap is 10 runs or fewer. For batters, the score blends pressure strike rate, lift over their overall strike rate, boundary rate, and non-dot rate. For bowlers, it blends low pressure economy, pressure dot-ball rate, wickets, and pressure overs. Each component is percentile-ranked within the eligible pool, then combined with the published weights in dashboard_data.json.", styles["BodyRR"]),
        Paragraph(f"Coverage: {payload['metadata']['source_rows']['matches']} matches and {payload['metadata']['source_rows']['deliveries']:,} deliveries in the Unstop audit; {payload['metadata']['source_rows']['unstop_verified_players']} Unstop profiles and {payload['metadata']['source_rows']['supplemental_players']} tournament profiles passed the final filters.", styles["SmallRR"]),
    ]
    for role, heading in [("Batter", "Top 10 U-19 batters under pressure"), ("Bowler", "Top 10 U-19 bowlers under pressure")]:
        story += [PageBreak(), Paragraph(heading, styles["HeadingRR"]), table_for(players[players.role == role].sort_values("rank")), Spacer(1, 10)]
        for _, row in players[players.role == role].sort_values("rank").iterrows():
            story.append(Paragraph(f"<b>{int(row['rank'])}. {row['player_name']}</b> — {note(row)}", styles["BodyRR"]))
    story += [
        PageBreak(), Paragraph("Auction strategy and visual evidence", styles["HeadingRR"]),
        Paragraph("Keep the shortlist role-specific at the table. The highest-ranked batters are candidates for a late-innings accelerator or chase stabiliser; the bowlers are candidates for powerplay wicket-taking or death-over control depending on their style. Rather than spend the entire budget on one name, RR can pair one high-score specialist with one lower-cost development bet whose sample is still growing. The dashboard makes that trade-off visible instead of hiding it behind a single rank.", styles["BodyRR"]),
        Image(str(ROOT / "assets" / "pressure_comparison.png"), width=7.0*inch, height=3.0*inch),
        Spacer(1, 8),
        Paragraph("Limitations and next step: the source does not expose DOB, caps, required run rate, wickets-in-hand, or delivery-level match state. Before a final auction decision, reconcile this proxy against official player-registration and age records, then rerun the model with required-run-rate and phase context if those fields become available.", styles["SmallRR"]),
    ]
    doc.build(story)
    print("Wrote RR_SupeRR_Selector_Submission.pdf")


if __name__ == "__main__":
    main()
