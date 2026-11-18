"""Generate the four-page Rajasthan Royals SupeRR Selector scouting dossier."""
from pathlib import Path
import json
import html
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle, Image

ROOT = Path(__file__).resolve().parent
PINK = colors.HexColor("#EA1A85")
BLUE = colors.HexColor("#071D49")
INK = colors.HexColor("#17233C")
MUTED = colors.HexColor("#58677F")
PALE = colors.HexColor("#F8F2F6")
LINE = colors.HexColor("#D9DFEA")
PAGE_W, PAGE_H = A4

NOTES = {
    "Shiv Mathur": "The Unstop audit gives Shiv a 117.0 pressure strike rate across 53 balls, a strong signal that he does not wait for ideal conditions. His right-handed profile is built for a fearless chase finish, with enough evidence to merit a live scouting look.",
    "Ben Mayes": "Ben’s 444 tournament runs at a 112.4 strike rate make him the most complete overseas batting bet in this group. He offers top-order volume without sacrificing the tempo RR need when a chase starts to tighten.",
    "Vaibhav Sooryavanshi": "Vaibhav’s 169.5 strike rate is the benchmark in this dossier: elite acceleration, not just promise. RR already know the upside; this page frames him as the retained reference point against which new batting targets should be measured.",
    "Faisal Shinozada": "Faisal paired 435 runs with a 107.1 strike rate, giving him the workload to back up his attacking intent. He is a credible overseas option for a side that wants middle-order boundary access without a one-dimensional slogger.",
    "Thomas Rew": "Thomas brings 330 runs at a 105.1 strike rate and the added value of a right-handed wicketkeeper-batter profile. That combination gives RR selection flexibility when the auction plan needs both runs and squad balance.",
    "Viran Chamuditha": "Viran’s left-handed angle and 122.1 strike rate give the batting group a useful change-up. His 310 runs suggest a repeatable contribution rather than a single-match spike, making him a developmental top-six watch.",
    "Jason Rowles": "Jason produced 280 runs at a 112.0 strike rate from a left-handed base. The profile points to a direct, high-tempo option who could be developed into a pressure finisher or aggressive No. 3.",
    "Zawad Abrar": "Zawad’s Unstop sample is deliberately modest but useful: 94.1 pressure strike rate over 68 balls. The right-hander looks more like a value development pick than a finished product, which is exactly where targeted academy work can add value.",
    "Nitesh Samuel": "Nitesh’s left-handed profile and 275 tournament runs give RR a different route through the middle order. The 67.4 strike rate keeps the risk visible, but the age and volume make him a watchlist player rather than a discard.",
    "Abhigyan Kundu": "Abhigyan is the cleanest Indian squad-balance play in the batting group: a left-handed wicketkeeper-batter with 239 tournament runs. His 87.6 strike rate is developmental, but the role scarcity and domestic eligibility make him worth a measured bid.",
    "Nooristani Omarzai": "Nooristani’s 14 wickets at a 4.23 economy mark him as the leading bowling control profile here. The right-arm fast-medium style gives RR a practical powerplay and middle-overs option with pressure evidence behind it.",
    "Manny Lumsden": "Manny combined 16 wickets with a 4.90 economy across 52.3 overs. His right-arm pace profile offers a high-upside overseas seam bet: enough wicket threat to attack, with a workload that suggests durability.",
    "Iqbal Hossain Emon": "Iqbal returned 11 wickets at 4.03 economy, an excellent control-to-impact blend. The right-arm fast-medium route fits the kind of repeatable middle-overs spell RR can build around in a young bowling unit.",
    "Al Fahad": "Al Fahad’s 12 wickets at 4.66 economy show a useful balance between attacking intent and run-rate discipline. He is a credible Bangladesh-based seam prospect for matchups where RR need a bowler who can stay in the contest.",
    "Will Byrom": "Will owns the tournament’s sharpest economy in this shortlist at 3.64, alongside 10 wickets. That is a strong new-ball and squeeze-overs signal, giving RR a particularly attractive overseas control option.",
    "Henil Patel": "Henil’s 11 wickets at 4.45 economy make him one of the most relevant domestic Indian pace targets in the pool. He can add local depth without using an overseas slot, while the workload suggests he is ready for a structured next step.",
    "Charles Lachmund": "Charles took 12 wickets from 38 overs, showing a reliable strike threat even at a 5.16 economy. His right-arm fast-medium profile is best viewed as an attacking overseas option whose value rises in wicket-seeking matchups.",
    "RS Ambrish": "RS Ambrish gives RR another Indian pace pathway: 11 wickets from 46 overs at 4.93 economy. That combination of volume and control makes him a sensible domestic target for depth, cover, and long-term development.",
    "Ralphie Albert": "Ralphie’s left-arm orthodox profile returned 10 wickets at 4.88 economy over 57 overs. He offers a different angle for matchup planning and enough tournament workload to justify continued tracking.",
    "Vitel Lawes": "Vitel’s 10 wickets at 4.93 economy show a steady left-arm orthodox option with room to grow. He is a later-round overseas development target whose value lies in variety and a dependable work rate.",
}


def para(c, text, x, y_top, width, style, height=None):
    p = Paragraph(text, style)
    w, h = p.wrap(width, height or PAGE_H)
    p.drawOn(c, x, y_top - h)
    return h


def footer(c, page):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.5)
    c.line(42, 30, PAGE_W - 42, 30)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.5)
    c.drawString(42, 18, "SupeRR Selector Season 2 | Jagadeeshwar Reddy Kota | github.com/kota-jagadeesh")
    c.drawRightString(PAGE_W - 42, 18, f"Page {page} of 4")


def banner(c):
    c.setFillColor(BLUE)
    c.rect(0, PAGE_H - 132, PAGE_W, 132, fill=1, stroke=0)
    c.setFillColor(PINK)
    c.rect(42, PAGE_H - 112, 7, 77, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(64, PAGE_H - 66, "SupeRR Selector Season 2:")
    c.setFont("Helvetica-Bold", 17)
    c.drawString(64, PAGE_H - 89, "IPL 2027 U-19 Pressure Scouting Dossier")
    c.setFont("Helvetica", 9.5)
    c.setFillColor(colors.HexColor("#DCE4F4"))
    c.drawString(64, PAGE_H - 111, "Data-Driven Identification of High-Leverage Uncapped & Youth Talent")
    c.setFillColor(PINK)
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(PAGE_W - 48, PAGE_H - 76, "RR")


def author_card(c):
    x, y, w, h = 42, PAGE_H - 236, PAGE_W - 84, 90
    c.setFillColor(colors.white)
    c.setStrokeColor(LINE)
    c.roundRect(x, y, w, h, 9, fill=1, stroke=1)
    label = ParagraphStyle("CardLabel", fontName="Helvetica-Bold", fontSize=7.2, leading=8.5, textColor=PINK)
    value = ParagraphStyle("CardValue", fontName="Helvetica-Bold", fontSize=9.2, leading=11, textColor=BLUE)
    link = ParagraphStyle("CardLink", fontName="Helvetica", fontSize=7.1, leading=8.5, textColor=PINK)
    data = [
        [Paragraph("SUBMITTED BY<br/><font color='#071D49'><b>Jagadeeshwar Reddy Kota · Kota-Jagadeesh</b></font>", label),
         Paragraph("EMAIL<br/><font color='#071D49'><b>kota.jagadesh123@gmail.com</b></font>", label), ""],
        [Paragraph("GITHUB<br/><link href='https://github.com'>https://github.com</link>", label),
         Paragraph("REPOSITORY<br/><link href='https://github.com/RR-IPL-auction-radar'>https://github.com/RR-IPL-auction-radar</link>", label),
         Paragraph("LIVE DASHBOARD<br/><link href='https://kota-jagadeesh.github.io/RR-IPL-auction-radar/dashboard/'>kota-jagadeesh.github.io/RR-IPL-auction-radar/dashboard/</link>", label)],
    ]
    table = Table(data, colWidths=[2.45 * inch, 2.0 * inch, 2.55 * inch], rowHeights=[39, 39])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, 0), 0.35, LINE),
    ]))
    table.wrapOn(c, w - 12, h - 8)
    table.drawOn(c, x + 6, y + 4)


def kpis(c, payload):
    values = [
        ("867", "MATCHES AUDITED"),
        ("200,999", "DELIVERIES ANALYZED"),
        ("20", "VERIFIED U-19/U-20 PROSPECTS"),
        ("100%", "DOB & ELIGIBILITY VERIFIED"),
    ]
    x, y, gap = 42, PAGE_H - 304, 8
    w = (PAGE_W - 84 - gap * 3) / 4
    for i, (value, label) in enumerate(values):
        bx = x + i * (w + gap)
        c.setFillColor(BLUE if i % 2 == 0 else PINK)
        c.roundRect(bx, y, w, 53, 7, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(bx + w / 2, y + 30, value)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawCentredString(bx + w / 2, y + 15, label)


def tag(row):
    if row["player_name"] == "Vaibhav Sooryavanshi":
        return "RR Retained Benchmark"
    return str(row.get("auction_tag", "")).replace("Current RR Squad Benchmark (Retained)", "Current RR benchmark")


def role_table(rows):
    data = [["#", "Player", "Style", "DOB / age", "Country", "Auction context", "Score", "Key output"]]
    cell = ParagraphStyle("Cell", fontName="Helvetica", fontSize=7.1, leading=8.3, textColor=INK)
    for _, r in rows.sort_values("rank").iterrows():
        age = "" if pd.isna(r.get("age_as_of_nov_2026")) else str(int(r["age_as_of_nov_2026"]))
        if r["role"] == "Batter":
            output = f"SR {float(r['pressure_strike_rate']):.1f} | {int(r['pressure_runs'])} runs"
        else:
            output = f"Econ {float(r['pressure_economy']):.2f} | {int(r['pressure_wickets'])} wkts"
        data.append([int(r["rank"]), Paragraph(str(r["player_name"]), cell), Paragraph(str(r.get("style", "")), cell), Paragraph(f"{r.get('dob', '')}<br/>{age} yrs", cell), Paragraph(str(r.get("country", "")), cell), Paragraph(tag(r), cell), Paragraph(f"{float(r['pressure_score']):.1f}", cell), Paragraph(output, cell)])
    t = Table(data, colWidths=[0.25 * inch, 1.35 * inch, 0.53 * inch, 0.78 * inch, 0.74 * inch, 1.65 * inch, 0.42 * inch, 1.28 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, 0), 7.2),
        ("FONTSIZE", (0, 1), (-1, -1), 7.2), ("FONTSIZE", (5, 1), (5, -1), 6.7),
        ("LEADING", (0, 0), (-1, -1), 8.4),
        ("GRID", (0, 0), (-1, -1), 0.25, LINE), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("TEXTCOLOR", (6, 1), (6, -1), PINK),
        ("FONTNAME", (6, 1), (6, -1), "Helvetica-Bold"),
    ]))
    return t


def role_page(c, players, role, page, title):
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(42, PAGE_H - 58, title)
    c.setFillColor(PINK)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(42, PAGE_H - 73, "PRESSURE INDEX SHORTLIST  ·  VERIFIED YOUTH POOL")
    table = role_table(players[players.role == role])
    tw, th = table.wrap(PAGE_W - 84, 300)
    table.drawOn(c, 42, PAGE_H - 92 - th)
    y = PAGE_H - 105 - th
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(42, y, "Scouting read")
    y -= 13
    body = ParagraphStyle("Note", fontName="Helvetica", fontSize=7.8, leading=9.4, textColor=INK, spaceAfter=0)
    for _, row in players[players.role == role].sort_values("rank").iterrows():
        text = f"<b>{int(row['rank'])}. {html.escape(row['player_name'])}</b>  {html.escape(NOTES[row['player_name']])}"
        h = para(c, text, 42, y, PAGE_W - 84, body)
        y -= h + 5
    footer(c, page)


def main():
    payload = json.loads((ROOT / "dashboard_data.json").read_text())
    players = pd.DataFrame(payload["players"])
    c = canvas.Canvas(str(ROOT / "RR_SupeRR_Selector_Submission.pdf"), pagesize=A4)
    body = ParagraphStyle("Body", fontName="Helvetica", fontSize=9.1, leading=12.3, textColor=INK)
    small = ParagraphStyle("Small", fontName="Helvetica", fontSize=7.6, leading=9.5, textColor=MUTED)

    banner(c)
    author_card(c)
    kpis(c, payload)
    y = PAGE_H - 330
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(42, y, "Executive summary")
    y -= 17
    y -= para(c, "The auction is won by players whose best skills survive the hard overs: the chase that needs 12 an over, the spell that must stop a set batter, and the moment when one mistake changes the game. This dossier gives Rajasthan Royals a focused, evidence-led view of young players who have already shown pressure resilience in verified development and youth competition records.", 42, y, PAGE_W - 84, body) + 8
    y -= para(c, "We audited 867 matches (200,999 deliveries) from the Unstop dataset, enriched missing birthdates via verified public registries, enforced strict IPL auction eligibility, excluded ineligible nationalities, and integrated verified 2026 ICC Men's U-19 World Cup performance records into one unified 0–100 Pressure Index.", 42, y, PAGE_W - 84, body) + 10
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(42, y, "Data architecture & pressure lens")
    y -= 17
    y -= para(c, "The shortlist combines two complementary evidence streams: ball-by-ball pressure outputs from the Unstop pack, and tournament-level impact from the verified 2026 ICC Men's U-19 World Cup archive. Batting scores reward pressure strike rate, lift over baseline, boundary rate and non-dot rate; bowling scores reward economy, dot-ball control, wickets and pressure overs. Each component is normalized before the final score is combined, so the ranking rewards repeatable match impact rather than reputation alone.", 42, y, PAGE_W - 84, body)
    y -= 10
    para(c, "The result is a practical scouting board: two Indian uncapped batting/bowling pathways, proven overseas youth performers, and a clear retained RR benchmark in Vaibhav Sooryavanshi. The source and auction context remain visible for every player so the shortlist can move directly into live scouting conversations.", 42, y, PAGE_W - 84, body)
    footer(c, 1)
    c.showPage()

    role_page(c, players, "Batter", 2, "Top 10 U-19 batters under pressure")
    c.showPage()
    role_page(c, players, "Bowler", 3, "Top 10 U-19 bowlers under pressure")
    c.showPage()

    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(42, PAGE_H - 58, "Auction strategy & visual evidence")
    c.setFillColor(PINK)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(42, PAGE_H - 73, "IPL 2027 ACTION PLAN FOR RAJASTHAN ROYALS")
    chart = Image(str(ROOT / "assets" / "pressure_comparison.png"), width=7.05 * inch, height=2.85 * inch)
    chart.drawOn(c, 42, PAGE_H - 365)
    y = PAGE_H - 390
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(42, y, "Three moves for the auction room")
    y -= 18
    bullets = [
        ("Priority Indian uncapped picks", "Henil Patel, RS Ambrish and Abhigyan Kundu add domestic depth without consuming overseas slots. Henil and Ambrish bring pace-bowling volume; Abhigyan adds a left-handed wicketkeeper-batter route to squad balance."),
        ("High-upside overseas pairing", "Pair a proven tournament striker such as Ben Mayes or Faisal Shinozada with a control bowler such as Nooristani Omarzai or Will Byrom. That pairing protects both batting intent and bowling economy while keeping the investment role-specific."),
        ("Interactive verification", "Use the live dashboard to move beyond rank: compare any two players head-to-head, filter by country or source, and test the minimum Pressure Score needed for the shortlist. Visit the interactive radar at the link below."),
    ]
    bullet_style = ParagraphStyle("Bullet", fontName="Helvetica", fontSize=8.7, leading=11.2, textColor=INK)
    for heading, text in bullets:
        h = para(c, f"<b>{heading}.</b> {text}", 54, y, PAGE_W - 96, bullet_style)
        c.setFillColor(PINK)
        c.circle(44, y - 5, 2.2, fill=1, stroke=0)
        y -= h + 10
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(42, y - 2, "LIVE DASHBOARD")
    dashboard_url = "https://kota-jagadeesh.github.io/RR-IPL-auction-radar/dashboard/"
    c.setFillColor(PINK)
    c.setFont("Helvetica", 8)
    c.drawString(42, y - 15, dashboard_url.replace("https://", ""))
    c.linkURL(dashboard_url, (42, y - 18, PAGE_W - 42, y - 5))
    footer(c, 4)
    c.save()
    print("Wrote RR_SupeRR_Selector_Submission.pdf (4 pages)")


if __name__ == "__main__":
    main()
