"""Generate the four-page Round 1 Rajasthan Royals scouting dossier."""
from pathlib import Path
import html
import pandas as pd
from reportlab.lib import colors
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
    c.drawString(64, PAGE_H - 89, "IPL 2027 Young Uncapped Stars Dossier")
    c.setFillColor(colors.HexColor("#DCE4F4"))
    c.setFont("Helvetica", 9.5)
    c.drawString(64, PAGE_H - 111, "Pressure Performance, Youth Age and Official-Roster Data")

def author_card(c):
    x, y, w, h = 42, PAGE_H - 236, PAGE_W - 84, 90
    c.setFillColor(colors.white)
    c.setStrokeColor(LINE)
    c.roundRect(x, y, w, h, 9, fill=1, stroke=1)
    label = ParagraphStyle("CardLabel", fontName="Helvetica-Bold", fontSize=7.2, leading=8.5, textColor=PINK)
    data = [
        [Paragraph("SUBMITTED BY<br/><font color='#071D49'><b>Jagadeeshwar Reddy Kota · Kota-Jagadeesh</b></font>", label),
         Paragraph("EMAIL<br/><font color='#071D49'><b>kota.jagadesh123@gmail.com</b></font>", label), ""],
        [Paragraph("GITHUB<br/><link href='https://github.com/kota-jagadeesh'>https://github.com/kota-jagadeesh</link>", label),
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

def kpis(c):
    values = [("867", "MATCHES AUDITED"), ("200,999", "DELIVERIES ANALYZED"),
              ("20", "OFFICIAL UNCAPPED PROFILES"), ("100%", "DOB & BOUNDARY CHECKED")]
    x, y, gap = 42, PAGE_H - 304, 8
    w = (PAGE_W - 84 - gap * 3) / 4
    for i, (value, label) in enumerate(values):
        bx = x + i * (w + gap)
        c.setFillColor(BLUE if i % 2 == 0 else PINK)
        c.roundRect(bx, y, w, 53, 7, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(bx + w / 2, y + 30, value)
        c.setFont("Helvetica-Bold", 6.2)
        c.drawCentredString(bx + w / 2, y + 15, label)

def role_table(df):
    cell = ParagraphStyle("Cell", fontName="Helvetica", fontSize=7.0, leading=8.2, textColor=INK)
    data = [["#", "Player", "ID", "Nation", "DOB / age", "Ball-by-ball evidence"]]
    for _, r in df.iterrows():
        data.append([
            int(r["Rank"]),
            Paragraph(html.escape(str(r["Player Name"])), cell),
            str(r["Player ID"]),
            str(r["Nationality"]),
            Paragraph(f"{html.escape(str(r['DOB']))}<br/>Age {int(r['Age'])}", cell),
            Paragraph(html.escape(str(r["Ball-by-Ball Stats"])), cell),
        ])
    t = Table(data, colWidths=[0.28*inch, 1.28*inch, 0.62*inch, 0.72*inch, 0.82*inch, 3.28*inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BLUE), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,-1), 7),
        ("GRID", (0,0), (-1,-1), 0.25, LINE),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, PALE]),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("TOPPADDING",(0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
    ]))
    return t

def para(c, text, x, y, width, style):
    p = Paragraph(text, style)
    w, h = p.wrap(width, PAGE_H)
    p.drawOn(c, x, y-h)
    return h

def role_page(c, df, page, title):
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(42, PAGE_H-58, title)
    c.setFillColor(PINK)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(42, PAGE_H-73, "OFFICIAL DATASET  ·  UNCAPPED  ·  AGE 25 OR YOUNGER")
    table = role_table(df)
    tw, th = table.wrap(PAGE_W-84, 320)
    table.drawOn(c, 42, PAGE_H-88-th)
    y = PAGE_H-102-th
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(42, y, "Scouting read")
    y -= 12
    note = ParagraphStyle("Note", fontName="Helvetica", fontSize=7.2, leading=8.5, textColor=INK)
    for _, r in df.iterrows():
        text = f"<b>{int(r['Rank'])}. {html.escape(str(r['Player Name']))}</b> — {html.escape(str(r['Scouting Rationales']))}"
        y -= para(c, text, 42, y, PAGE_W-84, note) + 3
    footer(c, page)

def main():
    bat = pd.read_csv(ROOT/"round1_top10_uncapped_batters.csv")
    bowl = pd.read_csv(ROOT/"round1_top10_uncapped_bowlers.csv")
    external = pd.read_csv(ROOT/"round1_top5_external_senior_gems.csv")
    c = canvas.Canvas(str(ROOT/"RR_SupeRR_Selector_Submission.pdf"), pagesize=A4)
    body = ParagraphStyle("Body", fontName="Helvetica", fontSize=8.8, leading=12, textColor=INK)

    banner(c); author_card(c); kpis(c)
    y = PAGE_H-330
    c.setFillColor(BLUE); c.setFont("Helvetica-Bold",13); c.drawString(42,y,"Executive summary"); y-=16
    y -= para(c, "The strongest scouting target is a young uncapped player whose pressure output survives real T20 match situations. This Round 1 dossier resets the shortlist around the official 1,217-player roster, verified age and uncapped status, and the strongest batting, bowling or all-round evidence from the supplied ball-by-ball dataset.",42,y,PAGE_W-84,body)+8
    y -= para(c, "We audited 867 matches and 200,999 deliveries, then applied an under-25 DOB filter and strict uncapped verification. The batting list prioritises powerplay acceleration and middle/death-over pressure; the bowling list prioritises economy, wicket-taking and pressure-over control. Players with only a small sample are labelled plainly rather than overstated.",42,y,PAGE_W-84,body)+10
    c.setFillColor(BLUE); c.setFont("Helvetica-Bold",13); c.drawString(42,y,"Official boundary and external appendix"); y-=16
    para(c, "Names are included here because they appear in the official competition-player mapping and supporting CSV files. Retention status and IPL experience do not remove a player from this Round 1 report. The five-player external appendix contains only senior Indian domestic standouts absent from all six CSV files.",42,y,PAGE_W-84,body)
    footer(c,1); c.showPage()

    role_page(c, bat, 2, "Top 10 youngest uncapped batters / all-rounders")
    c.showPage()
    role_page(c, bowl, 3, "Top 10 youngest uncapped bowlers")
    c.showPage()

    c.setFillColor(BLUE); c.setFont("Helvetica-Bold",17); c.drawString(42,PAGE_H-58,"External senior domestic pressure gems")
    c.setFillColor(PINK); c.setFont("Helvetica-Bold",8); c.drawString(42,PAGE_H-73,"APPENDIX  ·  100% ABSENT FROM ALL SIX CSVs")
    ext_style=ParagraphStyle("Ext",fontName="Helvetica",fontSize=7.8,leading=9.4,textColor=INK)
    y=PAGE_H-105
    for _,r in external.iterrows():
        text=f"<b>{int(r['Rank'])}. {html.escape(str(r['Player Name']))}</b> ({html.escape(str(r['DOB']))}, age {int(r['Age'])}) — {html.escape(str(r['Scouting Rationales']))}"
        y -= para(c,text,42,y,PAGE_W-84,ext_style)+8
    c.setFillColor(BLUE); c.setFont("Helvetica-Bold",11); c.drawString(42,y-5,"RR action: integrate these names as bonus scouting depth")
    y-=20
    para(c,"Use Andre Siddarth, Sunny Sandhu, Ayush Doseja, Raj Limbani and Eden Apple Tom to expand state/T20 league coverage. None of these names should appear as official portal dropdown selections.",42,y,PAGE_W-84,body)
    footer(c,4)
    c.save()
    print("Wrote RR_SupeRR_Selector_Submission.pdf")

if __name__=="__main__":
    main()
