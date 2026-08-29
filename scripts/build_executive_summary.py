"""Builds docs/Ordino-Executive-Summary.pdf -- a plain-English summary
for judges, non-technical reviewers and recruiters. Run with:
    python scripts/build_executive_summary.py
"""
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Frame,
    PageTemplate, BaseDocTemplate, NextPageTemplate, PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfgen import canvas as pdfcanvas

NAVY = colors.HexColor("#0B1229")
NAVY2 = colors.HexColor("#141B36")
ICE = colors.HexColor("#CADCFC")
WHITE = colors.white
ACCENT = colors.HexColor("#4C8DFF")
ACCENT2 = colors.HexColor("#35D0A6")
INK = colors.HexColor("#1B2444")
MUTED = colors.HexColor("#5B6785")

OUT_PATH = "docs/Ordino-Executive-Summary.pdf"

styles = getSampleStyleSheet()

title_style = ParagraphStyle("TitleBig", parent=styles["Title"], fontName="Helvetica-Bold",
                              fontSize=30, leading=34, textColor=NAVY, spaceAfter=4, alignment=TA_LEFT)
subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontName="Helvetica",
                                  fontSize=13, leading=17, textColor=MUTED, spaceAfter=2)
kicker_style = ParagraphStyle("Kicker", parent=styles["Normal"], fontName="Helvetica-Bold",
                                fontSize=10, leading=12, textColor=ACCENT, spaceAfter=6)
h1_style = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
                            fontSize=17, leading=21, textColor=NAVY, spaceBefore=18, spaceAfter=8)
body_style = ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica",
                              fontSize=10.5, leading=15.5, textColor=colors.HexColor("#222833"), spaceAfter=6)
bullet_style = ParagraphStyle("Bullet", parent=body_style, leftIndent=14, bulletIndent=0, spaceAfter=5)
callout_style = ParagraphStyle("Callout", parent=body_style, fontName="Helvetica-Oblique",
                                 fontSize=11.5, leading=17, textColor=WHITE, alignment=TA_LEFT)
footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontName="Helvetica",
                                fontSize=8, textColor=MUTED, alignment=TA_CENTER)


def header_footer(canvas: pdfcanvas.Canvas, doc):
    canvas.saveState()
    page_w, page_h = LETTER
    # top band
    canvas.setFillColor(NAVY)
    canvas.rect(0, page_h - 0.85 * inch, page_w, 0.85 * inch, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(0.75 * inch, page_h - 0.55 * inch, "Ordino")
    canvas.setFont("Helvetica", 9.5)
    canvas.setFillColor(ICE)
    canvas.drawString(0.75 * inch, page_h - 0.72 * inch, "AI Business Intelligence Assistant")
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(ACCENT2)
    canvas.drawRightString(page_w - 0.75 * inch, page_h - 0.63 * inch, "AI BUILDFEST 2026")
    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(ICE)
    canvas.drawRightString(page_w - 0.75 * inch, page_h - 0.76 * inch, "Executive Summary")

    # footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawCentredString(page_w / 2, 0.45 * inch,
                              f"Ordino AI Business Intelligence Assistant  ·  Page {doc.page}")
    canvas.restoreState()


def cover_page(canvas: pdfcanvas.Canvas, doc):
    page_w, page_h = LETTER
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    canvas.setFillColor(NAVY2)
    canvas.circle(page_w - 0.5 * inch, page_h - 0.5 * inch, 2.6 * inch, fill=1, stroke=0)

    canvas.setFillColor(ACCENT2)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(0.9 * inch, page_h - 2.1 * inch, "AI BUILDFEST 2026  ·  TRACK 1: AI FOR BUSINESS & PRODUCTIVITY")
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 34)
    canvas.drawString(0.85 * inch, page_h - 2.75 * inch, "Ordino")
    canvas.setFillColor(ICE)
    canvas.setFont("Helvetica", 18)
    canvas.drawString(0.9 * inch, page_h - 3.2 * inch, "AI Business Intelligence Assistant")
    canvas.setFont("Helvetica-Oblique", 12.5)
    canvas.setFillColor(colors.HexColor("#9FB3E8"))
    canvas.drawString(0.9 * inch, page_h - 3.65 * inch, "Turning disconnected retail data into decisions worth acting on.")

    canvas.setFillColor(colors.HexColor("#1B2444"))
    canvas.roundRect(0.85 * inch, page_h - 4.7 * inch, page_w - 1.7 * inch, 0.6 * inch, 6, fill=1, stroke=0)
    canvas.setFillColor(ACCENT2)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawCentredString(page_w / 2, page_h - 4.45 * inch, "Executive Summary")

    canvas.setFillColor(colors.HexColor("#7C89B5"))
    canvas.setFont("Helvetica", 9.5)
    canvas.drawString(0.9 * inch, 0.9 * inch, "Built by Tomola Oke  ·  Solo builder  ·  100% free & open-source stack")
    canvas.restoreState()


def section(story, kicker_text, title_text):
    story.append(Paragraph(kicker_text.upper(), kicker_style))
    story.append(Paragraph(title_text, h1_style))


def bullets(story, items):
    for it in items:
        story.append(Paragraph(f"&bull;&nbsp;&nbsp;{it}", bullet_style))
    story.append(Spacer(1, 4))


def build():
    doc = BaseDocTemplate(OUT_PATH, pagesize=LETTER,
                           leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                           topMargin=1.15 * inch, bottomMargin=0.75 * inch)
    frame_cover = Frame(0, 0, LETTER[0], LETTER[1], id="cover")
    frame_body = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[frame_cover], onPage=cover_page),
        PageTemplate(id="Body", frames=[frame_body], onPage=header_footer),
    ])

    story = []
    story.append(NextPageTemplate("Body"))
    story.append(PageBreak())

    # --- Section 1: Problem ---
    section(story, "01 · The Problem We Are Solving", "Revenue can grow while profit quietly doesn't.")
    story.append(Paragraph(
        "NexaSphere Retail Ltd. is a growing omnichannel electronics and appliance retailer. "
        "Like most growing retailers, its sales, returns, delivery, inventory, marketing and "
        "employee data live in separate systems. Management can see that revenue is going up "
        "&mdash; but can't quickly tell whether profit, delivery quality, returns or customer "
        "satisfaction are quietly getting worse underneath that headline number.",
        body_style))
    story.append(Paragraph(
        "Today, finding out takes a manager 30&ndash;60+ minutes of manually cross-referencing "
        "spreadsheets &mdash; and that has to happen again for every new question.",
        body_style))

    # --- Section 2: Use Case ---
    section(story, "02 · The Use Case", "One screen, the questions a manager actually asks.")
    story.append(Paragraph(
        "A retail operations or commercial manager opens the Ordino AI Business Intelligence "
        "Assistant and immediately sees a ranked list of things that need attention today, for example:",
        body_style))
    bullets(story, [
        "“Revenue grew 63.2%, but profit only grew 53.8%.”",
        "“One delivery partner is delayed 34% of the time, versus about 8% for the others.”",
        "“The Audio product category has an unusually high return rate.”",
    ])
    story.append(Paragraph(
        "The manager can also type a plain-English question &mdash; such as “which marketing "
        "campaign gives the best return?” &mdash; and get an answer computed from the real data, "
        "explained in plain language.",
        body_style))

    # --- Section 3: Advantages ---
    section(story, "03 · The Advantages", "What this actually changes.")
    bullets(story, [
        "Turns 30&ndash;60 minutes of manual spreadsheet work into a few seconds.",
        "Every number shown is backed by a real calculation the manager can inspect &mdash; never invented by the AI.",
        "Works with zero budget: built entirely on free, open-source tools (Python, pandas, Streamlit, "
        "and an optional free local AI model called Ollama).",
        "Honest by design: if it can't answer a question confidently, it says so instead of guessing.",
        "22 automated tests prove the numbers match an independently calculated answer key.",
    ])

    # --- Section 4: Recommendations ---
    section(story, "04 · Recommendations", "What Ordino management should act on.")
    bullets(story, [
        "Investigate the pricing and discounting behind recent revenue growth before assuming the growth is healthy.",
        "Review the Audio product category's quality and listing accuracy, given its elevated return rate.",
        "Review the underperforming delivery partner's service levels, or reallocate delivery volume to stronger partners.",
        "Address the inventory mismatch where some products run out while others pile up unsold.",
        "Continue investing in the top-performing marketing campaign, with normal diligence on diminishing returns.",
    ])

    # --- Section 5: Value proposition (callout box) ---
    story.append(Spacer(1, 6))
    vp_table = Table(
        [[Paragraph(
            "Ordino turns disconnected retail data into decisions worth acting on. Unlike a typical "
            "AI chatbot bolted onto a spreadsheet, every number it shows comes from a tested, deterministic "
            "calculation &mdash; the AI's only job is to explain that number in plain English, never to "
            "invent it. This means a manager gets the speed of AI with the trustworthiness of a real "
            "calculation, at zero cost.", callout_style)]],
        colWidths=[doc.width],
    )
    vp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [8, 8, 8, 8]),
    ]))
    story.append(Paragraph("05 · VALUE PROPOSITION", kicker_style))
    story.append(vp_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#DCE3F5"), thickness=0.75))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Built solo for AI BuildFest 2026, Case Study 4 (AI Business Intelligence Assistant), "
        "using a 100% free and open-source technology stack.", footer_style))

    doc.build(story)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    build()
