from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

PINK = RGBColor(234, 26, 133)
BLUE = RGBColor(7, 29, 73)
INK = RGBColor(23, 35, 60)
MUTED = RGBColor(91, 105, 132)
LINE = RGBColor(220, 225, 234)
WHITE = RGBColor(255, 255, 255)
PALE_PINK = RGBColor(253, 246, 251)
PALE_BLUE = RGBColor(245, 248, 253)

batters = pd.read_csv(ROOT / "round1_top10_uncapped_batters.csv")
bowlers = pd.read_csv(ROOT / "round1_top10_uncapped_bowlers.csv")
external = pd.read_csv(ROOT / "round1_top5_external_senior_gems.csv")

# Correct known public T20 sample wording: 51 runs came from a 27-ball sample.
for df in (batters,):
    mask = df["Player Name"].eq("Musheer Khan")
    df.loc[mask, "Ball-by-Ball Stats"] = df.loc[mask, "Ball-by-Ball Stats"].str.replace(
        "51-ball T20 sample", "27-ball T20 sample", regex=False
    )
for df in (bowlers,):
    mask = df["Player Name"].eq("Musheer Khan")
    df.loc[mask, "Ball-by-Ball Stats"] = "27-ball T20 batting sample: 51 runs, 188.88 SR"
batters.to_csv(ROOT / "round1_top10_uncapped_batters.csv", index=False)
bowlers.to_csv(ROOT / "round1_top10_uncapped_bowlers.csv", index=False)

def add_text(slide, text, x, y, w, h, size=16, color=INK, bold=False,
             align=PP_ALIGN.LEFT, font="Aptos", margin=0.04):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.margin_left = Inches(margin)
    tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin)
    tf.margin_bottom = Inches(margin)
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    r = p.runs[0]
    r.font.name = font
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    return box

def add_rect(slide, x, y, w, h, fill=WHITE, line=LINE, radius=True):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line
    shape.line.width = Pt(0.8)
    return shape

def footer(slide, num):
    slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.18), Inches(13.333), Inches(0.012)).fill.solid()
    slide.shapes[-1].fill.fore_color.rgb = PINK
    slide.shapes[-1].line.fill.background()
    add_text(slide, "SupeRR Selector Season 2 | Jagadeeshwar Reddy Kota | github.com/kota-jagadeesh",
             0.48, 7.19, 10.7, 0.22, size=7.5, color=MUTED)
    add_text(slide, f"{num} / 6", 11.9, 7.19, 0.95, 0.22, size=7.5, color=MUTED, align=PP_ALIGN.RIGHT)

def title_slide_band(slide, title, subtitle):
    band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(1.28))
    band.fill.solid()
    band.fill.fore_color.rgb = BLUE
    band.line.fill.background()
    add_text(slide, title, 0.62, 0.30, 11.55, 0.48, size=26, color=WHITE, bold=True)
    add_text(slide, subtitle, 0.62, 0.82, 11.55, 0.26, size=10.5, color=RGBColor(220,228,244))
    add_text(slide, "RR", 12.05, 0.38, 0.62, 0.44, size=20, color=PINK, bold=True, align=PP_ALIGN.CENTER)

def add_table(slide, df, y, height, columns, widths):
    rows = len(df) + 1
    table_shape = slide.shapes.add_table(rows, len(columns), Inches(0.48), Inches(y),
                                         Inches(sum(widths)), Inches(height))
    table = table_shape.table
    for i, w in enumerate(widths):
        table.columns[i].width = Inches(w)
    for i, col in enumerate(columns):
        cell = table.cell(0, i)
        cell.text = col
        cell.fill.solid()
        cell.fill.fore_color.rgb = BLUE
        cell.margin_left = Inches(0.06)
        cell.margin_right = Inches(0.06)
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.LEFT
            for r in p.runs:
                r.font.name = "Aptos"
                r.font.size = Pt(7.5)
                r.font.bold = True
                r.font.color.rgb = WHITE
    for ri, (_, r) in enumerate(df.iterrows(), start=1):
        vals = [str(r[c]) if c not in ("DOB",) else f"{r[c]} / {int(r['Age'])}" for c in columns]
        for ci, val in enumerate(vals):
            cell = table.cell(ri, ci)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if ri % 2 else PALE_PINK
            cell.margin_left = Inches(0.05)
            cell.margin_right = Inches(0.05)
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.LEFT
                for run in p.runs:
                    run.font.name = "Aptos"
                    run.font.size = Pt(6.9)
                    run.font.color.rgb = INK
    return table_shape

def add_link(box, url):
    run = box.text_frame.paragraphs[0].runs[0]
    run.hyperlink.address = url

def make_charts():
    ball = pd.read_csv(ROOT / "ball_by_ball.csv")
    ball["runs"] = pd.to_numeric(ball["runs"], errors="coerce").fillna(0)
    ball["overid"] = pd.to_numeric(ball["overid"], errors="coerce")
    ball["innings"] = pd.to_numeric(ball["innings"], errors="coerce")
    ball["is_wicket"] = ball["is_wicket"].astype(str).str.lower().eq("true")
    pressure = ball[(ball["innings"] == 2) | (ball["overid"] >= 16)]

    bat_map = {"Priyansh Arya":25, "Sameer Rizvi":22, "Vipraj Nigam":24, "Abishek Porel":24,
               "Musheer Khan":21, "Shaik Rasheed":22}
    bat_rows = []
    for name, age in bat_map.items():
        d = pressure[pressure["striker_name"] == name]
        balls = len(d)
        if balls:
            psr = d["runs"].sum() / balls * 100
        else:
            psr = np.nan
        bat_rows.append((name, age, psr))

    bowl_map = {"Suyash Sharma":23, "Sakib Hussain":23, "Madhav Tiwari":23}
    bowl_rows = []
    for name, age in bowl_map.items():
        d = pressure[pressure["bowler_name"] == name]
        balls = len(d)
        wkts = d["is_wicket"].sum()
        econ = d["runs"].sum() / balls * 6 if balls else np.nan
        bowl_rows.append((name, econ, wkts))

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8.4, 5.2), dpi=300)
    xs = [r[1] for r in bat_rows]
    ys = [r[2] for r in bat_rows]
    ax.scatter(xs, ys, s=150, c="#EA1A85", edgecolors="#071D49", linewidths=1.2, zorder=3)
    for name, age, psr in bat_rows:
        ax.annotate(name, (age, psr), xytext=(5, 5), textcoords="offset points", fontsize=9,
                    color="#071D49", fontweight="bold")
    ax.axvspan(18, 25, color="#EA1A85", alpha=0.05)
    ax.set_title("Batting Quadrant: Age vs Pressure Strike Rate", fontsize=15, color="#071D49", fontweight="bold")
    ax.set_xlabel("Verified age")
    ax.set_ylabel("Pressure strike rate")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    batting_chart = ASSETS / "round1_batting_quadrant.png"
    fig.savefig(batting_chart, dpi=300, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.4, 5.2), dpi=300)
    econ = [r[1] for r in bowl_rows]
    wkts = [r[2] for r in bowl_rows]
    ax.scatter(econ, wkts, s=180, c="#071D49", edgecolors="#EA1A85", linewidths=1.2, zorder=3)
    for name, economy, wickets in bowl_rows:
        ax.annotate(name, (economy, wickets), xytext=(5, 5), textcoords="offset points", fontsize=9,
                    color="#071D49", fontweight="bold")
    ax.invert_xaxis()
    ax.set_title("Bowling Quadrant: Pressure Economy vs Wicket Impact", fontsize=15, color="#071D49", fontweight="bold")
    ax.set_xlabel("Pressure economy (lower is better)")
    ax.set_ylabel("Pressure wickets")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    bowling_chart = ASSETS / "round1_bowling_quadrant.png"
    fig.savefig(bowling_chart, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return batting_chart, bowling_chart

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]

# Slide 1
slide = prs.slides.add_slide(blank)
slide.background.fill.solid()
slide.background.fill.fore_color.rgb = WHITE
title_slide_band(slide, "SupeRR Selector Season 2",
                  "IPL 2027 Young Uncapped Stars Dossier  |  Executive Scouting Presentation")
add_text(slide, "Jagadeeshwar Reddy Kota", 0.62, 1.45, 4.2, 0.34, size=13, color=BLUE, bold=True)
add_text(slide, "Kota-Jagadeesh  ·  kota.jagadesh123@gmail.com", 0.62, 1.75, 6.2, 0.28, size=9, color=MUTED)
github_box = add_text(slide, "github.com/kota-jagadeesh", 7.82, 1.45, 2.35, 0.28, size=8.2, color=PINK, bold=True)
github_box.text_frame.paragraphs[0].runs[0].hyperlink.address = "https://github.com/kota-jagadeesh"
dashboard_box = add_text(slide, "kota-jagadeesh.github.io/…/dashboard/", 10.18, 1.45, 2.55, 0.28, size=7.2, color=PINK, bold=True)
dashboard_box.text_frame.paragraphs[0].runs[0].hyperlink.address = "https://kota-jagadeesh.github.io/RR-IPL-auction-radar/dashboard/"
add_text(slide, "KPI SUMMARY", 0.62, 2.18, 2.0, 0.22, size=8.5, color=PINK, bold=True)
kpis = [("867", "Matches"), ("200,999", "Deliveries"), ("20", "Official Profiles"), ("100%", "Verified")]
for i, (value, label) in enumerate(kpis):
    x = 0.62 + i * 3.02
    add_rect(slide, x, 2.48, 2.72, 1.06, BLUE if i in (0,2) else PINK)
    add_text(slide, value, x+0.12, 2.63, 2.48, 0.38, size=19, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, label, x+0.12, 3.06, 2.48, 0.22, size=8.5, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
add_text(slide, "METHODOLOGY FUNNEL", 0.62, 3.92, 2.5, 0.22, size=8.5, color=PINK, bold=True)
funnel = [("1", "1,217", "Roster players"),
          ("2", "Under-25", "Uncapped filter"),
          ("3", "Pressure", "Ball-by-ball ranking")]
for i, (n, big, small) in enumerate(funnel):
    x = 0.62 + i * 4.02
    add_rect(slide, x, 4.25, 3.55, 1.0, PALE_BLUE if i != 1 else PALE_PINK)
    add_text(slide, n, x+0.18, 4.43, 0.38, 0.38, size=12, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    circ = slide.shapes[-1]
    add_text(slide, big, x+0.72, 4.38, 2.55, 0.34, size=15, color=BLUE, bold=True)
    add_text(slide, small, x+0.72, 4.78, 2.55, 0.22, size=8.5, color=MUTED)
    if i < 2:
        add_text(slide, "→", x+3.58, 4.48, 0.42, 0.34, size=18, color=PINK, bold=True, align=PP_ALIGN.CENTER)
add_text(slide, "Primary objective", 0.62, 5.68, 1.5, 0.24, size=8.5, color=PINK, bold=True)
add_text(slide, "Find young uncapped talent whose skills hold under chase, death-over and clutch-match pressure.",
         0.62, 5.98, 11.9, 0.55, size=17, color=BLUE, bold=True)
footer(slide, 1)

# Slide 2
slide = prs.slides.add_slide(blank)
slide.background.fill.solid(); slide.background.fill.fore_color.rgb = WHITE
add_text(slide, "Top 10 Youngest Uncapped Batters / All-Rounders", 0.48, 0.32, 12.2, 0.48, size=21, color=BLUE, bold=True)
add_text(slide, "Inside official dataset  ·  Under-25  ·  No retained-player filter", 0.48, 0.78, 11.8, 0.24, size=8.5, color=PINK, bold=True)
add_table(slide, batters,
          1.10, 3.18,
          ["Rank","Player Name","Player ID","Nationality","DOB","Ball-by-Ball Stats"],
          [0.55,2.05,0.82,1.05,1.35,6.03])
takeaways = [
    ("Musheer Khan — Dual-Threat All-Rounder", "27-ball T20 sample: 51 runs, 188.88 SR."),
    ("Shaik Rasheed", "Pressure SR rises to 128.1; calm top-order stabiliser."),
    ("Sameer Rizvi", "245 pressure balls and 153.47 pressure SR."),
    ("Vipraj Nigam — Dual-Threat All-Rounder", "185.33 pressure SR and 13 bowling wickets."),
    ("Abishek Porel", "33 matches and 548 balls; 167.57 death-over SR."),
    ("Priyansh Arya", "Elite 182.71 SR across 538 balls."),
    ("Vicky Ostwal — Dual-Threat All-Rounder", "Middle-over spin and 15-T20 all-round evidence."),
    ("Shiv Mathur", "Youngest prospect: Hong Kong RHB wicketkeeper."),
    ("Zawad Abrar", "Four-match pressure sample; development target."),
    ("Jishan Alam — Dual-Threat All-Rounder", "Offbreaks plus 89-ball batting sample."),
]
for i,(head,detail) in enumerate(takeaways):
    col=i%2; row=i//2
    x=0.48+col*6.19; y=4.52+row*0.47
    add_rect(slide,x,y,5.95,0.38,PALE_PINK if col==0 else PALE_BLUE)
    add_text(slide,f"{head} — {detail}",x+0.12,y+0.02,5.70,0.31,size=7.2,color=INK,bold=False)
footer(slide,2)

# Slide 3
slide = prs.slides.add_slide(blank)
slide.background.fill.solid(); slide.background.fill.fore_color.rgb=WHITE
add_text(slide,"Top 10 Youngest Uncapped Bowlers",0.48,0.32,12.2,0.48,size=21,color=BLUE,bold=True)
add_text(slide,"Inside official dataset  ·  Powerplay / middle / death-over evidence",0.48,0.78,11.8,0.24,size=8.5,color=PINK,bold=True)
add_table(slide,bowlers,1.10,3.18,
          ["Rank","Player Name","Player ID","Nationality","DOB","Ball-by-Ball Stats"],
          [0.55,2.05,0.82,1.05,1.35,6.03])
takeaways=[
("Suyash Sharma","Leg-spinner — 34 wickets, 8.20 economy, 524 pressure balls."),
("Vipraj Nigam — Dual-Threat All-Rounder","Leg-break phase control plus finishing upside."),
("Vicky Ostwal — Dual-Threat All-Rounder","Left-arm spin with 14 wickets across 15 T20s."),
("Naman Tiwari — Pace prospect","Left-arm fast-medium — 145kph ceiling; no supplied ball sample."),
("Musheer Khan — Dual-Threat All-Rounder","Left-arm spin is developmental; batting remains the stronger skill."),
("Garuka Sanketh","Right-arm medium — 7.45 economy and 2 pressure wickets."),
("Jishan Alam — Dual-Threat All-Rounder","Right-arm offbreak with 89-ball batting and 18-ball bowling sample."),
("Sakib Hussain","Pressure economy 6.73 with 14 pressure wickets."),
("Madhav Tiwari","Right-arm medium-fast — 75 balls and 4 wickets at 7.36 economy."),
("Vignesh Puthur","Left-arm wrist spin — 73 balls and 6 wickets.")
]
for i,(head,detail) in enumerate(takeaways):
    col=i%2; row=i//2
    x=0.48+col*6.19; y=4.52+row*0.47
    add_rect(slide,x,y,5.95,0.38,PALE_PINK if col==0 else PALE_BLUE)
    add_text(slide,f"{head} — {detail}",x+0.12,y+0.02,5.70,0.31,size=7.1,color=INK)
footer(slide,3)

# Slide 4
slide = prs.slides.add_slide(blank)
slide.background.fill.solid(); slide.background.fill.fore_color.rgb=WHITE
add_text(slide,"Visual Analytics & Phase Impact",0.48,0.32,12.2,0.48,size=21,color=BLUE,bold=True)
add_text(slide,"Pressure context = chase innings or overs 16-20",0.48,0.78,11.8,0.24,size=8.5,color=PINK,bold=True)
bat_chart,bowl_chart=make_charts()
slide.shapes.add_picture(str(bat_chart),Inches(0.55),Inches(1.12),width=Inches(6.05),height=Inches(4.85))
slide.shapes.add_picture(str(bowl_chart),Inches(6.75),Inches(1.12),width=Inches(6.05),height=Inches(4.85))
add_text(slide,"Batting read",0.62,6.12,2.0,0.22,size=9,color=PINK,bold=True)
add_text(slide,"Arya and Rizvi combine elite youth pressure SR with meaningful volume.",0.62,6.38,5.85,0.45,size=9.2,color=INK)
add_text(slide,"Bowling read",6.82,6.12,2.0,0.22,size=9,color=PINK,bold=True)
add_text(slide,"Suyash leads wicket volume; Sakib offers the strongest control/wicket blend.",6.82,6.38,5.85,0.45,size=9.2,color=INK)
footer(slide,4)

# Slide 5
slide = prs.slides.add_slide(blank)
slide.background.fill.solid(); slide.background.fill.fore_color.rgb=WHITE
add_text(slide,"Final Recommended Top 10 Unstop Submission Squad",0.48,0.32,12.2,0.48,size=20,color=BLUE,bold=True)
add_text(slide,"Balanced tactical starting ten  ·  4 Batters/WKs  ·  3 All-Rounders  ·  3 Bowlers",0.48,0.78,12.0,0.24,size=8.5,color=PINK,bold=True)
squad=[
("Priyansh Arya","Batter","Powerplay opener"),
("Abishek Porel","WK-batter","Left-hand middle"),
("Sameer Rizvi","Batter","Middle-order finisher"),
("Shaik Rasheed","Batter","Top/middle stabiliser"),
("Musheer Khan","All-rounder","Middle spin/bat"),
("Vipraj Nigam","All-rounder","Leg spin/finish"),
("Vicky Ostwal","All-rounder","Left-arm spin/bat"),
("Suyash Sharma","Bowler","Leg-spin middle"),
("Sakib Hussain","Bowler","Pace middle/death"),
("Madhav Tiwari","Bowler","Medium-fast depth"),
]
for i,(name,role,fit) in enumerate(squad):
    col=i%5; row=i//5
    x=0.48+col*2.50; y=1.35+row*2.38
    add_rect(slide,x,y,2.28,2.08,PALE_PINK if role=="Bowler" else PALE_BLUE)
    add_text(slide,str(i+1).zfill(2),x+0.12,y+0.12,0.48,0.30,size=10,color=PINK,bold=True)
    add_text(slide,name,x+0.12,y+0.50,2.02,0.48,size=12,color=BLUE,bold=True)
    add_text(slide,role,x+0.12,y+1.08,2.02,0.28,size=8.5,color=PINK,bold=True)
    add_text(slide,fit,x+0.12,y+1.48,2.02,0.36,size=7.8,color=MUTED)
add_rect(slide,0.48,6.16,12.35,0.62,BLUE)
add_text(slide,"Unstop submission rule",0.68,6.29,2.0,0.20,size=8.5,color=PINK,bold=True)
add_text(slide,"Rank these 10 in batters/bowlers dropdowns only if the player remains available on the official Unstop portal.",
         2.28,6.26,10.12,0.28,size=9.2,color=WHITE,bold=True)
footer(slide,5)

# Slide 6
slide = prs.slides.add_slide(blank)
slide.background.fill.solid(); slide.background.fill.fore_color.rgb=WHITE
add_text(slide,"Appendix — External Senior Domestic Pressure Gems",0.48,0.32,12.2,0.48,size=20,color=BLUE,bold=True)
add_text(slide,"Outside the official six-CSV roster  ·  Senior domestic T20 standouts",0.48,0.78,12.0,0.24,size=8.5,color=PINK,bold=True)
for i,(_,r) in enumerate(external.iterrows()):
    col=i%3; row=i//3
    x=0.48+col*4.18
    y=1.35+row*2.38
    w=3.88
    add_rect(slide,x,y,w,1.82,PALE_PINK if i%2==0 else PALE_BLUE)
    add_text(slide,str(r["Player Name"]),x+0.16,y+0.16,w-0.32,0.36,size=12,color=BLUE,bold=True)
    add_text(slide,f"{r['DOB']}  ·  Age {int(r['Age'])}",x+0.16,y+0.56,w-0.32,0.28,size=8.5,color=MUTED)
    add_text(slide,str(r["Key Stats"]),x+0.16,y+0.92,w-0.32,0.36,size=8.2,color=PINK,bold=True)
    add_text(slide,str(r["Scouting Rationales"]),x+0.16,y+1.34,w-0.32,0.38,size=7.5,color=INK)
add_rect(slide,0.48,5.85,12.35,0.82,BLUE)
add_text(slide,"PORTAL EXCLUSION CALLOUT",0.68,5.99,2.25,0.24,size=8.5,color=PINK,bold=True)
add_text(slide,"These 5 names were programmatically absent from all 6 CSVs. They add state-league scouting depth but should not be entered into portal dropdown selections.",
         2.80,5.94,9.65,0.42,size=9.2,color=WHITE,bold=True)
footer(slide,6)

out_pptx = ROOT / "RR_SupeRR_Round1_Executive_Presentation.pptx"
prs.save(out_pptx)
print("Wrote", out_pptx)
