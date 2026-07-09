#!/usr/bin/env python3
from __future__ import annotations

import textwrap
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "glam-homes-engineering-report.pdf"
PAGESIZE = landscape(LETTER)
W, H = PAGESIZE

INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#4B5563")
LIGHT = colors.HexColor("#F8FAFC")
MID = colors.HexColor("#E5E7EB")
GOLD = colors.HexColor("#B9975B")
GOLD_LIGHT = colors.HexColor("#F7F1E6")
NAVY = colors.HexColor("#0F172A")
BLUE = colors.HexColor("#1D4ED8")
GREEN = colors.HexColor("#047857")
RED = colors.HexColor("#B91C1C")
PURPLE = colors.HexColor("#6D28D9")

MARGIN_X = 0.55 * inch
TOP = H - 0.45 * inch
BOTTOM = 0.45 * inch


def clean(text: object) -> str:
    return str(text).replace("\u2013", "-").replace("\u2014", "-").replace("\u00a0", " ")


def draw_wrapped(c, text, x, y, max_w, font="Helvetica", size=9.2, leading=12, color=INK, max_lines=None):
    c.setFont(font, size)
    c.setFillColor(color)
    words = clean(text).split()
    lines = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if stringWidth(candidate, font, size) <= max_w:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(".") + "..."
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def footer(c, page_num):
    c.setStrokeColor(MID)
    c.setLineWidth(0.5)
    c.line(MARGIN_X, 0.34 * inch, W - MARGIN_X, 0.34 * inch)
    c.setFont("Helvetica", 7.2)
    c.setFillColor(MUTED)
    c.drawString(MARGIN_X, 0.2 * inch, "GLAM HOMES | Orbit / Ai People reference implementation")
    c.drawRightString(W - MARGIN_X, 0.2 * inch, f"Page {page_num}")


def header(c, title, page_num, section="GLAM HOMES CALL CENTER SYSTEM"):
    c.setFont("Helvetica-Bold", 7.2)
    c.setFillColor(GOLD)
    c.drawString(MARGIN_X, TOP, section)
    c.setFont("Helvetica-Bold", 17)
    c.setFillColor(INK)
    c.drawString(MARGIN_X, TOP - 0.28 * inch, clean(title))
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.1)
    c.line(MARGIN_X, TOP - 0.38 * inch, W - MARGIN_X, TOP - 0.38 * inch)
    footer(c, page_num)
    return TOP - 0.62 * inch


def new_page(c, page_num, title, section="GLAM HOMES CALL CENTER SYSTEM"):
    c.showPage()
    return header(c, title, page_num, section)


def kpi(c, x, y, w, h, label, value, note, color=BLUE):
    c.setFillColor(LIGHT)
    c.setStrokeColor(MID)
    c.roundRect(x, y - h, w, h, 6, fill=1, stroke=1)
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(MUTED)
    c.drawCentredString(x + w / 2, y - 0.22 * inch, clean(label))
    c.setFont("Helvetica-Bold", 21)
    c.setFillColor(color)
    c.drawCentredString(x + w / 2, y - 0.52 * inch, clean(value))
    c.setFont("Helvetica", 7.5)
    c.setFillColor(MUTED)
    c.drawCentredString(x + w / 2, y - 0.75 * inch, clean(note))


def bullets(c, items, x, y, max_w, size=9.2, leading=13.2, color=INK, bullet_color=GOLD):
    for item in items:
        c.setFillColor(bullet_color)
        c.circle(x, y + 3, 2.2, fill=1, stroke=0)
        y = draw_wrapped(c, item, x + 0.18 * inch, y, max_w - 0.18 * inch, size=size, leading=leading, color=color)
        y -= 0.08 * inch
    return y


def callout(c, x, y, w, h, title, text, accent=GOLD):
    c.setFillColor(GOLD_LIGHT)
    c.setStrokeColor(accent)
    c.roundRect(x, y - h, w, h, 6, fill=1, stroke=1)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(INK)
    c.drawString(x + 0.12 * inch, y - 0.20 * inch, clean(title))
    draw_wrapped(c, text, x + 0.12 * inch, y - 0.38 * inch, w - 0.24 * inch, size=8.2, leading=11, color=INK)


def table(c, x, y, widths, rows, header_fill=NAVY, font_size=7.1, row_h=0.36 * inch):
    total_w = sum(widths)
    for r, row in enumerate(rows):
        h = row_h
        fill = header_fill if r == 0 else (colors.white if r % 2 else LIGHT)
        c.setFillColor(fill)
        c.setStrokeColor(MID)
        c.rect(x, y - h, total_w, h, fill=1, stroke=1)
        cx = x
        for i, cell in enumerate(row):
            c.setStrokeColor(MID)
            c.line(cx, y, cx, y - h)
            c.setFont("Helvetica-Bold" if r == 0 else "Helvetica", font_size)
            c.setFillColor(colors.white if r == 0 else INK)
            draw_wrapped(c, cell, cx + 0.06 * inch, y - 0.14 * inch, widths[i] - 0.12 * inch, size=font_size, leading=font_size + 2, color=colors.white if r == 0 else INK, max_lines=2)
            cx += widths[i]
        c.line(x + total_w, y, x + total_w, y - h)
        y -= h
    return y


def image_fit(c, path, x, y, w, h, caption=None):
    p = ROOT / path
    if not p.exists():
        callout(c, x, y, w, h, "Missing image", path, RED)
        return
    img = ImageReader(str(p))
    iw, ih = img.getSize()
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    c.setFillColor(colors.white)
    c.setStrokeColor(MID)
    c.roundRect(x, y - h, w, h, 6, fill=1, stroke=1)
    c.drawImage(img, x + (w - dw) / 2, y - h + (h - dh) / 2, dw, dh, preserveAspectRatio=True, mask="auto")
    if caption:
        c.setFont("Helvetica", 7)
        c.setFillColor(MUTED)
        c.drawString(x, y - h - 0.13 * inch, clean(caption))


def two_col_text(c, y, left_title, left_items, right_title, right_items):
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(INK)
    c.drawString(MARGIN_X, y, left_title)
    c.drawString(W / 2 + 0.15 * inch, y, right_title)
    bullets(c, left_items, MARGIN_X, y - 0.25 * inch, W / 2 - MARGIN_X - 0.25 * inch, size=8.3, leading=11.5)
    bullets(c, right_items, W / 2 + 0.15 * inch, y - 0.25 * inch, W / 2 - MARGIN_X - 0.25 * inch, size=8.3, leading=11.5)


def flow_diagram(c, x, y, labels, colors_list=None):
    colors_list = colors_list or [NAVY, BLUE, PURPLE, GREEN, GOLD]
    box_w = 1.28 * inch
    box_h = 0.48 * inch
    gap = 0.16 * inch
    for i, label in enumerate(labels):
        bx = x + i * (box_w + gap)
        c.setFillColor(colors_list[i % len(colors_list)])
        c.setStrokeColor(colors_list[i % len(colors_list)])
        c.roundRect(bx, y - box_h, box_w, box_h, 8, fill=1, stroke=1)
        c.setFont("Helvetica-Bold", 7.2)
        c.setFillColor(colors.white)
        draw_wrapped(c, label, bx + 0.08 * inch, y - 0.18 * inch, box_w - 0.16 * inch, font="Helvetica-Bold", size=7.2, leading=8.4, color=colors.white, max_lines=2)
        if i < len(labels) - 1:
            c.setStrokeColor(MUTED)
            c.line(bx + box_w + 0.02 * inch, y - box_h / 2, bx + box_w + gap - 0.03 * inch, y - box_h / 2)
            c.line(bx + box_w + gap - 0.08 * inch, y - box_h / 2 + 3, bx + box_w + gap - 0.03 * inch, y - box_h / 2)
            c.line(bx + box_w + gap - 0.08 * inch, y - box_h / 2 - 3, bx + box_w + gap - 0.03 * inch, y - box_h / 2)


def mini_panel_mock(c, x, y, w, h):
    c.setFillColor(colors.white)
    c.setStrokeColor(MID)
    c.roundRect(x, y - h, w, h, 7, fill=1, stroke=1)
    c.setFillColor(NAVY)
    c.roundRect(x + 0.12 * inch, y - 0.44 * inch, w - 0.24 * inch, 0.28 * inch, 5, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 7.6)
    c.setFillColor(colors.white)
    c.drawString(x + 0.26 * inch, y - 0.34 * inch, "Performance Snapshot")
    c.setFont("Helvetica", 6.6)
    c.drawRightString(x + w - 0.26 * inch, y - 0.34 * inch, "Last 7 days | Protected dashboard")

    labels = [("Total calls", "128"), ("Prospects", "41"), ("Coverage", "92%"), ("Handoffs", "9")]
    card_w = (w - 0.52 * inch) / 4
    card_y = y - 0.68 * inch
    for i, (label, value) in enumerate(labels):
        cx = x + 0.14 * inch + i * (card_w + 0.08 * inch)
        c.setFillColor(LIGHT)
        c.setStrokeColor(MID)
        c.roundRect(cx, card_y - 0.55 * inch, card_w, 0.55 * inch, 5, fill=1, stroke=1)
        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColor(MUTED)
        c.drawCentredString(cx + card_w / 2, card_y - 0.16 * inch, label)
        c.setFont("Helvetica-Bold", 15)
        c.setFillColor(GREEN if label == "Coverage" else BLUE)
        c.drawCentredString(cx + card_w / 2, card_y - 0.40 * inch, value)

    left_x = x + 0.14 * inch
    chart_y = y - 1.52 * inch
    chart_w = (w - 0.42 * inch) / 2
    chart_h = 1.18 * inch
    for title, offset in [("Topics by call volume", 0), ("Pipeline mix", chart_w + 0.14 * inch)]:
        cx = left_x + offset
        c.setFillColor(colors.white)
        c.setStrokeColor(MID)
        c.roundRect(cx, chart_y - chart_h, chart_w, chart_h, 5, fill=1, stroke=1)
        c.setFont("Helvetica-Bold", 7)
        c.setFillColor(INK)
        c.drawString(cx + 0.1 * inch, chart_y - 0.17 * inch, title)
    bars = [0.78, 0.55, 0.38, 0.24]
    names = ["Booking", "Support", "Check-in", "Policy"]
    for i, bar in enumerate(bars):
        bx = left_x + 0.22 * inch
        by = chart_y - 0.42 * inch - i * 0.17 * inch
        c.setFont("Helvetica", 5.8)
        c.setFillColor(MUTED)
        c.drawString(bx, by + 0.02 * inch, names[i])
        c.setFillColor([GOLD, GREEN, PURPLE, RED][i])
        c.rect(bx + 0.52 * inch, by, chart_w * 0.72 * bar, 0.07 * inch, fill=1, stroke=0)

    donut_x = left_x + chart_w + 0.14 * inch + chart_w / 2
    donut_y = chart_y - 0.67 * inch
    c.setStrokeColor(GOLD)
    c.setLineWidth(15)
    c.circle(donut_x, donut_y, 0.28 * inch, fill=0, stroke=1)
    c.setStrokeColor(GREEN)
    c.arc(donut_x - 0.28 * inch, donut_y - 0.28 * inch, donut_x + 0.28 * inch, donut_y + 0.28 * inch, 25, 145)
    c.setStrokeColor(RED)
    c.arc(donut_x - 0.28 * inch, donut_y - 0.28 * inch, donut_x + 0.28 * inch, donut_y + 0.28 * inch, 145, 205)
    c.setStrokeColor(MID)
    c.setLineWidth(1)
    c.setFont("Helvetica", 6)
    c.setFillColor(MUTED)
    c.drawCentredString(donut_x, donut_y - 0.55 * inch, "Prospects | Support | Handoffs | Other")

    c.setFillColor(GOLD_LIGHT)
    c.setStrokeColor(MID)
    c.roundRect(x + 0.14 * inch, y - h + 0.14 * inch, w - 0.28 * inch, 0.52 * inch, 5, fill=1, stroke=1)
    c.setFont("Helvetica-Bold", 6.8)
    c.setFillColor(INK)
    c.drawString(x + 0.25 * inch, y - h + 0.48 * inch, "Conversation Inbox")
    c.setFont("Helvetica", 6.2)
    c.setFillColor(MUTED)
    c.drawString(x + 0.25 * inch, y - h + 0.30 * inch, "Recent | Relevant | Most interaction | Least interaction | Phone | Keyword")


def metric_cards(c, x, y, cards):
    col_w = (W - 2 * MARGIN_X - 0.32 * inch) / 2
    row_h = 0.88 * inch
    for i, card in enumerate(cards):
        cx = x + (i % 2) * (col_w + 0.32 * inch)
        cy = y - (i // 2) * (row_h + 0.16 * inch)
        c.setFillColor(colors.white)
        c.setStrokeColor(MID)
        c.roundRect(cx, cy - row_h, col_w, row_h, 6, fill=1, stroke=1)
        c.setFont("Helvetica-Bold", 8.4)
        c.setFillColor(INK)
        c.drawString(cx + 0.12 * inch, cy - 0.18 * inch, clean(card[0]))
        draw_wrapped(c, card[1], cx + 0.12 * inch, cy - 0.38 * inch, col_w - 0.24 * inch, size=7.4, leading=9.5, color=MUTED, max_lines=4)


def build():
    c = canvas.Canvas(str(OUT), pagesize=PAGESIZE)
    c.setTitle("GLAM HOMES AI Call Center Engineering Report")
    c.setAuthor("Ai People / Orbit")
    c.setSubject("Live-site engineering report, module audit, analytics guide, and Orbit reference architecture")
    c.setCreator("Ai People / Orbit")
    page = 1

    live = "orbit-aipeople/reports/live-screenshots/"

    def add_text_page(title, rows=None, bullets_left=None, callout_text=None, section="GLAM HOMES ENGINEERING REPORT"):
        nonlocal page
        page += 1
        y = new_page(c, page, title, section)
        if rows:
            table(c, MARGIN_X, y, rows[0], rows[1], font_size=7.2, row_h=0.41 * inch)
        if bullets_left:
            bullets(c, bullets_left, MARGIN_X, y, W - 2 * MARGIN_X, size=8.8, leading=12.5)
        if callout_text:
            callout(c, MARGIN_X, 1.22 * inch, W - 2 * MARGIN_X, 0.72 * inch, callout_text[0], callout_text[1])

    def add_image_page(title, image, caption, notes=None, section="LIVE PRODUCT EVIDENCE"):
        nonlocal page
        page += 1
        y = new_page(c, page, title, section)
        if notes:
            image_fit(c, image, MARGIN_X, y, 5.05 * inch, 4.35 * inch, caption)
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(INK)
            c.drawString(5.95 * inch, y, "What this proves")
            bullets(c, notes, 5.95 * inch, y - 0.28 * inch, 2.05 * inch, size=7.8, leading=10.2)
        else:
            image_fit(c, image, MARGIN_X, y, W - 2 * MARGIN_X, 4.55 * inch, caption)

    # 1 Cover
    c.setFillColor(colors.white)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(GOLD)
    c.drawCentredString(W / 2, H - 0.82 * inch, "ORBIT / AI PEOPLE REFERENCE SYSTEM")
    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(INK)
    c.drawCentredString(W / 2, H - 1.35 * inch, "GLAM HOMES AI CALL CENTER")
    c.setFont("Helvetica-Bold", 19)
    c.drawCentredString(W / 2, H - 1.72 * inch, "Engineering Report, Live Front-End Audit, Analytics Guide")
    c.setFont("Helvetica", 10.5)
    c.setFillColor(MUTED)
    c.drawCentredString(W / 2, H - 2.06 * inch, "Based on glamhomes.aipeople.app live screenshots, deployed HTML, local runtime code, and data validation")
    image_fit(c, live + "08-live-voice-console-viewport-current.png", 0.8 * inch, H - 5.15 * inch, 4.45 * inch, 2.6 * inch, "Live product screenshot: voice console and operations monitor")
    callout(c, 5.45 * inch, H - 3.02 * inch, 2.55 * inch, 0.9 * inch, "Executive thesis", "GLAM HOMES is not a chatbot. It is a controlled call-center operating system: live voice, PMS truth, SMS actions, human handoff and analytics.")
    kpi(c, 5.45 * inch, H - 4.08 * inch, 1.1 * inch, 0.8 * inch, "PUBLIC HOMES", "54", "active", BLUE)
    kpi(c, 6.72 * inch, H - 4.08 * inch, 1.1 * inch, 0.8 * inch, "KB CASES", "24,072", "indexed", GREEN)
    kpi(c, 5.45 * inch, H - 5.05 * inch, 1.1 * inch, 0.8 * inch, "LIVE URL", "200", "healthy", GREEN)
    kpi(c, 6.72 * inch, H - 5.05 * inch, 1.1 * inch, 0.8 * inch, "GUESTY", "RO", "read-only", RED)
    footer(c, page)

    add_text_page("Table of contents",
        rows=([1.75 * inch, 1.05 * inch, 4.7 * inch], [
            ["Section", "Pages", "What it covers"],
            ["Executive diagnosis", "3-9", "Problem, solution, value equation, operating model."],
            ["Live front-end audit", "10-31", "Screenshots and module-by-module explanation of glamhomes.aipeople.app."],
            ["Analytics operating guide", "32-45", "Every KPI, priority card, chart, table, filter and decision trigger."],
            ["Architecture and runtime", "46-55", "OpenAI Realtime, Twilio, Guesty, SQLite, transcripts, knowledge base."],
            ["Governance and rollout", "56-64", "Security, deployment gap, operating cadence, risks, roadmap."],
            ["Appendix", "65-70", "Evidence inventory, validation, file map and acceptance criteria."]
        ]),
        callout_text=("Reading guide", "This is written as a board-ready engineering deck: business problem first, evidence next, then operational mechanics and implementation detail."))

    add_text_page("Executive answer - what GLAM HOMES solves",
        rows=([1.85 * inch, 5.65 * inch], [
            ["Question", "Answer"],
            ["What is the product?", "A live AI call-center console for luxury vacation rentals, combining voice, Guesty data, Twilio calls/SMS, protected analytics and human escalation."],
            ["What pain does it remove?", "It reduces missed calls, repetitive guest support, manual property-link routing, unsafe static answers and unmanaged escalation."],
            ["Why is it not a generic bot?", "The agent is tool-grounded. It retrieves live reservation/listing data and sends SMS through controlled Twilio functions."],
            ["Why does management care?", "The dashboard turns conversations into measurable operational signals: volume, prospects, handoffs, repeat contacts, issues, SMS and transcript quality."],
            ["Why does Orbit care?", "It is a reusable pattern for vertical AI tools with live APIs, protected data, and measurable operations."]
        ]),
        callout_text=("Bottom line", "The project is strongest when described as an operating system for hospitality calls, not as a front-end demo."))

    add_text_page("Problem definition - the broken workflow before AI",
        rows=([2.2 * inch, 2.65 * inch, 2.65 * inch], [
            ["Operational pain", "Why it hurts", "What the system now does"],
            ["Booking calls arrive fragmented", "Prospects ask about homes, dates, prices and fit across voice and SMS.", "The concierge qualifies intent and can send public property links."],
            ["Stay details are sensitive", "Door codes, Wi-Fi, address and check-in cannot be guessed.", "Guesty tools require reservation validation before sensitive details."],
            ["Human exceptions are common", "Refunds, parties, VIP requests, complaints and maintenance need judgment.", "Handoff SMS and live transfer move risky cases to people."],
            ["Managers lack visibility", "Call logs alone do not explain what callers asked or why escalation happened.", "Protected analytics and threaded transcripts create an audit trail."],
            ["Knowledge is trapped in history", "Thousands of Guesty conversations contain repeated patterns.", "24,072 cases are distilled into use cases and best practices."]
        ]))

    add_text_page("Solution model - one operating layer",
        bullets_left=[
            "Voice captures intent in real time and lets guests interact naturally.",
            "OpenAI Realtime chooses tools instead of relying on static memory.",
            "Guesty remains the source of truth for reservations, listings, availability and stay details.",
            "SQLite gives fast access to public property links for sales routing.",
            "Twilio synchronizes phone calls, SMS follow-up, advisor alerts and transfer.",
            "Analytics converts transcript events into management signals.",
            "Historical conversations become policy and coaching material, not raw prompt bloat."
        ],
        callout_text=("Design principle", "Autonomy is useful only when it is bounded: read live facts, take low-risk actions, escalate judgment calls."))

    add_text_page("Strategic value equation",
        rows=([1.45 * inch, 2.9 * inch, 3.15 * inch], [
            ["Value lever", "Mechanism", "Expected business effect"],
            ["Revenue capture", "Prospect detection, property search, property-link SMS.", "Fewer lost booking opportunities."],
            ["Service quality", "Reservation confirmation and stay-detail retrieval.", "Fewer incorrect or incomplete answers."],
            ["Risk control", "Read-only Guesty, validation gates, policy escalation.", "Lower probability of costly mistakes."],
            ["Operating leverage", "Routine voice/SMS workflows handled by agent.", "Humans focus on exceptions and high-value guests."],
            ["Learning loop", "Analytics + 24,072 case knowledge base.", "Repeated issues become process improvements."]
        ]))

    add_text_page("What makes this engineering-grade",
        rows=([1.75 * inch, 3.0 * inch, 2.75 * inch], [
            ["Dimension", "Evidence observed", "Why it matters"],
            ["Live deployment", "glamhomes.aipeople.app loads, Twilio public health returns HTTP 200.", "Not only local code."],
            ["Operational UI", "Voice, Analytics, Calls and Security modules are present.", "Supports human operation."],
            ["Protected data", "Analytics, calls and security are locked behind dashboard access.", "Phone and transcript data are treated as sensitive."],
            ["Live tool layer", "Guesty and Twilio functions are registered as runtime tools.", "Agent can act on systems of truth."],
            ["Knowledge base", "24,072 JSONL cases, 0 invalid rows.", "Historical learning is structured."],
            ["Export hygiene", "Private data is kept under ignored local paths.", "Reusable without leaking secrets."]
        ]))

    add_text_page("Audited facts used in this report",
        rows=([2.05 * inch, 3.05 * inch, 2.4 * inch], [
            ["Evidence source", "What was inspected", "Result"],
            ["Live browser", "https://glamhomes.aipeople.app", "Loaded with live status, modules and protected dashboards."],
            ["Live screenshots", "Desktop and mobile module captures.", "Saved under orbit-aipeople/reports/live-screenshots."],
            ["Live HTML", "Downloaded deployed index.html.", "157,478 bytes; includes Analytics and Calls as separate tabs."],
            ["Local code", "apps/voice-agent/server.py and public/index.html.", "Runtime tools, endpoints and local UI reviewed."],
            ["Data checks", "SQLite, JSON exports, case_index.jsonl.", "Integrity and counts validated."]
        ]),
        callout_text=("Important finding", "The live front end is ahead of the local checked file in some analytics UI details; the report calls this out rather than hiding it."))

    add_image_page("Live site - voice console", live + "08-live-voice-console-viewport-current.png", "Live viewport capture from glamhomes.aipeople.app",
        ["Shows public production surface.", "Voice and SMS services are active.", "Twilio monitor reports backend, media bridge, proxy, webhook and provider status.", "Guesty note confirms read-only credentials detected."])

    add_text_page("Voice console - module anatomy", section="LIVE FRONT-END AUDIT",
        rows=([1.85 * inch, 3.2 * inch, 2.45 * inch], [
            ["Area", "What it does", "Engineering meaning"],
            ["Agent stage", "Shows concierge avatar, state, microphone visualization and live marker.", "Human-readable call state for operators."],
            ["Voice actions", "Start voice, Test voice, End session.", "Controls WebRTC/Realtime browser session."],
            ["Voice engine", "Standard OpenAI/Twilio voices plus Vapi option.", "Provider abstraction for call voice."],
            ["Voice lock", "Dashboard unlock required to change call voice.", "Admin control separated from guest-facing testing."],
            ["Microphone panel", "Device selection, test button, audio level.", "Reduces setup failure before live calls."],
            ["Side notes", "Local mode, scope, Guesty, brand.", "Explains runtime boundaries to operators."]
        ]))

    add_text_page("Realtime console and manual composer", section="LIVE FRONT-END AUDIT",
        rows=([1.65 * inch, 3.25 * inch, 2.6 * inch], [
            ["Element", "Observed behavior", "Why it exists"],
            ["Session title", "GLAM HOMES Session with GH timestamp label.", "Creates session identity for live testing."],
            ["Chat feed", "System messages and future transcript turns.", "Operator can see what the agent says and does."],
            ["Composer", "Manual instruction textarea and Send button.", "Allows typed testing without a phone call."],
            ["Status copy", "Explains local WebRTC and OPENAI_API_KEY dependency.", "Makes configuration failures visible."],
            ["Twilio preparation message", "Shows line and webhook readiness context.", "Connects browser test to telephony deployment."]
        ]))

    add_text_page("Twilio operations monitor - what each line means", section="LIVE FRONT-END AUDIT",
        rows=([1.85 * inch, 2.8 * inch, 2.85 * inch], [
            ["Monitor item", "Meaning", "Operational action"],
            ["Voice service", "Whether the voice path is available.", "If down, do not route live calls."],
            ["SMS service", "Whether SMS delivery is available.", "If down, avoid promising text follow-up."],
            ["Backend API", "Local app process readiness.", "Restart server if failed."],
            ["Media bridge", "Twilio audio stream bridge.", "Check port/process for voice failures."],
            ["Public proxy", "Public tunnel/proxy health.", "Verify Cloudflare/public route."],
            ["Public Twilio health", "HTTP health endpoint from deployed URL.", "Confirms Twilio can reach the app."],
            ["Voice/SMS webhook", "Twilio number callback configuration.", "Fix number config if mismatch."],
            ["Voice provider network", "API provider latency.", "Watch for call quality risk."]
        ]))

    add_image_page("Live site - analytics lock", live + "09-live-analytics-viewport.png", "Analytics module from deployed site",
        ["Analytics is intentionally protected.", "The deployed module includes KPIs, priority cards, charts and operational tables behind the lock.", "This protects phone, transcript and customer issue history."])

    add_text_page("Analytics module - live front-end anatomy", section="LIVE FRONT-END AUDIT",
        rows=([1.55 * inch, 3.2 * inch, 2.75 * inch], [
            ["Part", "Live deployed front end", "Purpose"],
            ["Lock screen", "Analytics Locked + dashboard password.", "Protects private operational metrics."],
            ["Range filters", "Today, 7 days, 30 days, All, Custom.", "Controls all KPI/chart scopes."],
            ["KPI grid", "12 management KPIs in deployed HTML.", "Management scorecard."],
            ["Secondary metrics", "10 supporting metrics.", "Operational diagnostics."],
            ["Priority grid", "Priority queue, Repeat issue, VIP pipeline, Quality signal.", "Tells managers what to review first."],
            ["Charts", "Topics, Pipeline mix, Calls by day/hour.", "Volume, mix and timing patterns."],
            ["Tables", "Subtopics/repeats and escalations by reason.", "Root-cause and handoff analysis."],
            ["Frequent concepts", "Top issue chips.", "Fast pattern discovery."]
        ]))

    add_text_page("Live Analytics KPIs - full scorecard", section="ANALYTICS GUIDE",
        rows=([1.6 * inch, 2.95 * inch, 2.95 * inch], [
            ["KPI", "Definition", "Use"],
            ["Total calls", "Calls in selected scope.", "Workload denominator."],
            ["Prospects", "Calls with booking intent.", "Revenue opportunity."],
            ["Transcript coverage", "Calls with transcript evidence.", "Observability health."],
            ["Human handoffs", "Escalation events.", "Human workload and risk."],
            ["First call resolution", "Eligible calls resolved on first contact.", "Service effectiveness."],
            ["Avg resolution", "Start-to-end or transfer duration.", "Speed and friction."],
            ["Repeat contact", "Repeat callers and same-subtopic repeats.", "Unresolved issue detection."],
            ["Issues detected", "Total issue signals and multi-issue calls.", "Complexity load."],
            ["Influencers", "VIP/influencer callers flagged.", "High-touch sales/service routing."],
            ["Needs attention", "Calls marked for review, with praise count.", "Quality queue."],
            ["Missed/abandoned", "Telephony status and short unresolved calls.", "Lost-contact risk."],
            ["SMS sent", "Guest/advisor SMS actions.", "Channel follow-through."]
        ],),)

    add_text_page("Priority cards - management triage", section="ANALYTICS GUIDE",
        rows=([1.65 * inch, 3.0 * inch, 2.85 * inch], [
            ["Card", "What it measures", "Decision trigger"],
            ["Priority queue", "Attention calls needing review.", "Open red conversations first."],
            ["Repeat issue", "Same-subtopic callbacks.", "Fix underlying workflow/property issue."],
            ["VIP pipeline", "Influencer/VIP signals and unique callers.", "Route to premium human process."],
            ["Quality signal", "Praise calls and positive guest sentiment.", "Identify scripts and behaviors to preserve."]
        ]),
        callout_text=("How to use", "This row is the daily manager shortcut: what needs review, what keeps repeating, who needs VIP handling, and where the agent performed well."))

    add_text_page("Charts - how to read them", section="ANALYTICS GUIDE",
        rows=([1.75 * inch, 3.05 * inch, 2.7 * inch], [
            ["Chart", "Meaning", "Management action"],
            ["Topics by call volume", "Counts topic hits by transcript category.", "Prioritize scripts and property data for the tallest bars."],
            ["Pipeline mix", "Prospects, support, handoffs and other share.", "Understand whether the line is sales-heavy or support-heavy."],
            ["Calls by day and hour", "Bubble heatmap of call timing.", "Staff coverage and campaign timing decisions."],
            ["Subtopics and repeats", "Operational root causes and repeat counts.", "Find unresolved loops."],
            ["Escalations by reason", "Handoff reasons by category.", "Improve policy, staffing, data or maintenance playbooks."],
            ["Frequent concepts", "Top chips from subtopics and topics.", "Fast discovery of recurring issues."]
        ]))

    add_text_page("Analytics filters and interpretation rules", section="ANALYTICS GUIDE",
        rows=([1.45 * inch, 2.9 * inch, 3.15 * inch], [
            ["Filter", "What it does", "Correct use"],
            ["Today", "Same-day view.", "Operational standup and live triage."],
            ["7 days", "Default recent operating window.", "Weekly review and staffing."],
            ["30 days", "Monthly trend read.", "Management reporting."],
            ["All", "Historical baseline.", "Benchmarking and audits."],
            ["Custom", "Exact incident/campaign/shift window.", "Postmortems and launch analysis."],
            ["Phone", "Caller-specific search in Calls module.", "Follow-up and dispute review."],
            ["Keyword", "Issue/property/name search.", "Root-cause investigation."]
        ]),
        callout_text=("Rule", "No KPI should be quoted without its date range. Scope is part of the number."))

    add_image_page("Live site - Calls module", live + "10-live-calls-viewport.png", "Calls / Conversation Inbox module from deployed site",
        ["Calls are separated from Analytics in production.", "The inbox supports time filters, phone/keyword search and sort modes.", "Transcript detail tabs include Chat, SMS, Technical and Audio."])

    add_text_page("Calls module - conversation memory", section="LIVE FRONT-END AUDIT",
        rows=([1.6 * inch, 3.15 * inch, 2.75 * inch], [
            ["Part", "What it does", "Why it matters"],
            ["Calls lock", "Protects call memory and customer issue history.", "PII and transcript security."],
            ["Time range", "Today, 7 days, 30 days, All, Custom.", "Find calls in the right operational window."],
            ["Thread sorting", "Recent, Relevant, Most interaction, Least interaction.", "Triage by recency, risk or complexity."],
            ["Search", "Phone number and keyword search.", "Find a guest, property, issue or phrase."],
            ["Call list", "Caller-level thread rows.", "Keeps continuity across multiple calls."],
            ["Transcript panel", "Conversation detail viewer.", "Quality, audit and follow-up."],
            ["Detail tabs", "Chat, SMS, Technical, Audio.", "Separates human-readable transcript from system evidence."]
        ]))

    add_text_page("Transcript detail tabs - what a supervisor checks", section="ANALYTICS GUIDE",
        rows=([1.55 * inch, 3.2 * inch, 2.75 * inch], [
            ["Tab", "Likely content", "Supervisor question"],
            ["Chat", "Guest and concierge transcript turns.", "Was the answer accurate, concise and brand-safe?"],
            ["SMS", "Text actions to guest/advisor.", "Did the agent send the promised durable follow-up?"],
            ["Technical", "Tool/system events and metadata.", "Did the agent ground the response in Guesty/Twilio/SQLite?"],
            ["Audio", "Audio-related call artifacts when available.", "Was there a voice quality or transcription issue?"]
        ]),
        callout_text=("Audit standard", "A good call validates facts, sends useful SMS, avoids unsupported promises and escalates judgment calls."))

    add_image_page("Live site - Security module", live + "11-live-security-viewport.png", "Security settings module from deployed site",
        ["Security is protected by dashboard access.", "Controls reservation validation mode and human escalation numbers.", "Separates guest-facing service from admin-only risk settings."])

    add_text_page("Security module - controls and risk posture", section="LIVE FRONT-END AUDIT",
        rows=([1.65 * inch, 3.05 * inch, 2.8 * inch], [
            ["Control", "Observed live function", "Risk controlled"],
            ["Reservation validation", "Code only, relaxed, strict.", "How much proof is needed before stay details."],
            ["Emergency advisor SMS", "Human issues notify a configured advisor line.", "Operational exceptions do not stay with the bot."],
            ["VIP Reservations", "Separate high-touch reservations line.", "Premium/VIP pipeline gets human attention."],
            ["Current call rules", "Use caller ID, confirm code/name, offer SMS, transfer on human request.", "Operator-readable policy."]
        ]))

    add_image_page("Live site - mobile voice console", live + "06-live-mobile-voice-console-fullpage.png", "Mobile live capture",
        ["The app is responsive.", "Voice controls, monitor and status copy remain accessible.", "Mobile view matters for operators testing from a phone-sized browser."])

    add_image_page("Live site - mobile analytics lock", live + "07-live-mobile-analytics-fullpage.png", "Mobile Analytics module",
        ["Protected analytics remains clear on mobile.", "The lock copy explains why access is restricted.", "The module is copyable as a vertical dashboard pattern."])

    add_text_page("Front-end module map", section="ENGINEERING ARCHITECTURE",
        rows=([1.65 * inch, 3.25 * inch, 2.6 * inch], [
            ["Module", "Primary user", "Core responsibility"],
            ["Voice Console", "Operator / tester", "Start/test voice, select voice, monitor Twilio and compose test instructions."],
            ["Analytics", "Manager", "Scorecard, priorities, charts, repeated issues and escalation reasons."],
            ["Calls", "Supervisor", "Caller memory, transcript review, SMS/tool/audio audit."],
            ["Security", "Admin", "Validation mode and human escalation contact controls."],
            ["Booking surfaces", "Guest/prospect", "Property inventory and public link routing."]
        ]))

    add_text_page("Backend endpoint map", section="ENGINEERING ARCHITECTURE",
        rows=([1.95 * inch, 3.2 * inch, 2.35 * inch], [
            ["Endpoint family", "Purpose", "Visible front-end use"],
            ["/session / realtime", "OpenAI Realtime session and tool registration.", "Voice testing and call flow."],
            ["/api/status", "Configuration status and knowledge-base flags.", "Server/Guesty/Twilio/Vapi readiness."],
            ["/api/twilio/monitor", "Deep Twilio monitor for local dashboard.", "Operations monitor."],
            ["/api/twilio/public-health", "Public health endpoint.", "Tunnel/Twilio reachability."],
            ["/api/calls/threads", "Threaded call inbox + metrics.", "Analytics and Calls modules."],
            ["/api/calls/thread", "One caller history.", "Transcript panel."],
            ["/api/*contact", "Advisor and VIP phone settings.", "Security module."]
        ]))

    add_text_page("Tool architecture - agent action surface", section="ENGINEERING ARCHITECTURE",
        rows=([1.85 * inch, 3.2 * inch, 2.45 * inch], [
            ["Tool family", "Functions", "Control posture"],
            ["Guesty status/search", "guesty_status, guesty_search_reservation.", "Read-only discovery."],
            ["Guesty confirmation", "guesty_confirm_reservation, guesty_confirmed_stay_details.", "Validation-gated sensitive data."],
            ["Guesty inventory", "listings, available listings, listing calendar.", "Read-only property facts."],
            ["Public links", "glam_search_public_property_links.", "Public SQLite only."],
            ["Twilio SMS", "property link, stay details, human handoff.", "Consent/context aware."],
            ["Twilio transfer", "twilio_transfer_call_to_human.", "Escalation path."]
        ]),
        callout_text=("Core safety choice", "Guesty writes, payments, refunds and policy exceptions are intentionally outside the autonomous tool surface."))

    add_text_page("Guesty as a live API tool", section="ENGINEERING ARCHITECTURE",
        rows=([1.7 * inch, 3.15 * inch, 2.65 * inch], [
            ["Use case", "Guesty role", "Agent behavior"],
            ["Find reservation", "Search by code, phone, email or name.", "Handles noisy phone-call confirmation codes."],
            ["Confirm stay", "Returns verified reservation/listing details.", "Requires validation before sensitive details."],
            ["Check availability", "Search listings by dates and guests.", "Supports prospect calls."],
            ["Calendar/pricing", "Listing calendar and nightly pricing.", "Grounds booking discussion."],
            ["Missing fields", "Diagnostics for access/Wi-Fi/custom fields.", "Escalates when Guesty data is incomplete."]
        ]))

    add_text_page("Twilio call and SMS synchronization", section="ENGINEERING ARCHITECTURE",
        rows=([1.7 * inch, 3.1 * inch, 2.7 * inch], [
            ["Flow", "Mechanism", "Why it matters"],
            ["Inbound call", "Twilio line routes to realtime bridge.", "Turns phone call into AI conversation."],
            ["Media stream", "Bridge carries audio to realtime agent.", "Voice experience instead of text-only bot."],
            ["Property-link SMS", "Agent texts public property link after consent.", "Moves sales follow-up into durable channel."],
            ["Stay-details SMS", "Agent texts verified arrival/access details.", "Reduces repeat calls and confusion."],
            ["Human handoff SMS", "Advisor receives reason and summary.", "Escalation is actionable."],
            ["Live transfer", "Active call can be transferred.", "Guest can reach a human immediately."]
        ]))

    add_text_page("Data architecture", section="ENGINEERING ARCHITECTURE",
        rows=([2.05 * inch, 3.05 * inch, 2.4 * inch], [
            ["Data asset", "Role", "Status"],
            ["data/glam_homes_property_links.sqlite", "Public property link lookup.", "Integrity ok; 54 active records."],
            ["data/guesty-property-links.json", "Portable public property export.", "JSON valid."],
            ["data/private/guesty-conversations", "Raw/private Guesty export and builders.", "Private internal only."],
            ["GLAM HOMES KNOWLEDGE BASE", "Use cases, playbooks, best practices.", "24,072 structured cases."],
            ["transcripts", "Local call transcripts.", "Private; not GitHub-safe."],
            ["live-screenshots", "Evidence used for this report.", "Stored in Orbit report folder."]
        ]))

    add_text_page("Knowledge base model", section="ENGINEERING ARCHITECTURE",
        rows=([1.85 * inch, 3.1 * inch, 2.55 * inch], [
            ["Layer", "Purpose", "Output"],
            ["Raw export", "Preserve original Guesty conversations.", "Local private archive."],
            ["Filtering", "Remove empty/noisy/low-value threads.", "Cleaner corpus."],
            ["Case index", "Structured JSONL cases.", "24,072 rows, 0 invalid JSON."],
            ["Use cases", "Cluster repeated guest patterns.", "Training and review material."],
            ["Property playbooks", "Property-specific recurring guidance.", "Better per-home handling."],
            ["Runtime best practices", "Compact instructions for active agent.", "Loaded with knowledge_base_loaded=True."]
        ]))

    add_text_page("Analytics computation model", section="ENGINEERING ARCHITECTURE",
        rows=([1.7 * inch, 3.15 * inch, 2.65 * inch], [
            ["Metric group", "Source", "Computation idea"],
            ["Volume", "Call summaries and Twilio metadata.", "Count calls in selected time range."],
            ["Topics", "Transcript text keyword categories.", "Booking, support, handoff, events risk, payment."],
            ["Tool actions", "Transcript event role/kind.", "Count system-grounded actions."],
            ["Handoffs", "human_handoff event kinds.", "Escalation count and rate."],
            ["Repeat contact", "Caller/thread grouping.", "Repeat callers and same-subtopic repeats."],
            ["SMS", "Twilio transcript/tool events.", "Guest/advisor follow-through count."],
            ["Attention/praise", "Conversation analysis fields in deployed UI.", "Quality review queue."]
        ]))

    add_text_page("Security and privacy model", section="GOVERNANCE",
        rows=([1.8 * inch, 3.1 * inch, 2.6 * inch], [
            ["Risk", "Control", "Evidence"],
            ["PII exposure", "Dashboard locks for analytics/calls/security.", "Live lock screens."],
            ["Sensitive stay details", "Reservation validation before details.", "Guesty tool schemas and security module."],
            ["Unauthorized changes", "Guesty read-only; no payment/refund writes.", "Tool manifest and runtime tools."],
            ["Private corpora", "data/private ignored/export-marked.", "Export manifest."],
            ["Credential leakage", ".env/API Keys kept private.", ".gitignore and docs."],
            ["Bad automation", "Human handoff and transfer tools.", "Twilio handoff functions."]
        ]))

    add_text_page("Deployment finding - live and local UI differ", section="GOVERNANCE",
        rows=([2.05 * inch, 2.95 * inch, 2.5 * inch], [
            ["Observation", "Live deployed site", "Local repo file"],
            ["Tab model", "Voice Console, Analytics, Calls, Security.", "Voice Console, Calls & Analytics, Security."],
            ["Analytics depth", "12 KPIs, priority grid, heatmap, subtopic/escalation tables.", "Simpler KPI/chart set in current local file."],
            ["Security controls", "VIP Reservations line present live.", "Local file may not reflect that exact deployed split."],
            ["Implication", "Production has evolved beyond local checked HTML.", "Export should include live evidence and reconcile source before future deploys."]
        ]),
        callout_text=("Recommendation", "Before the next production release, pull/export the deployed front-end version or reconcile local source so GitHub is the single source of truth."))

    add_text_page("How a human should use the panel daily", section="OPERATING MODEL",
        rows=([1.25 * inch, 3.3 * inch, 2.95 * inch], [
            ["Cadence", "Review", "Decision"],
            ["Start day", "Missed/abandoned, needs attention, priority queue.", "Who needs callback or human follow-up?"],
            ["Midday", "Prospects, VIP pipeline, SMS sent.", "Which booking opportunities need action?"],
            ["End day", "Top topics, subtopics, handoffs, repeat issues.", "What data/process changed tomorrow?"],
            ["Weekly", "7-day call timing, FCR, repeat contact, escalation reasons.", "Staffing and playbook improvements."],
            ["Monthly", "30-day trends and knowledge-base update candidates.", "Automation roadmap and client reporting."]
        ]))

    add_text_page("Operational playbooks by scenario", section="OPERATING MODEL",
        rows=([1.75 * inch, 2.9 * inch, 2.85 * inch], [
            ["Scenario", "Agent/system path", "Human rule"],
            ["Prospect asks for villa", "Search availability or public links; SMS property link.", "Human only for discount or special deal."],
            ["Guest needs access", "Confirm reservation; retrieve stay details; SMS details.", "Human if missing data or lockout."],
            ["Policy exception", "Explain policy; collect summary; handoff.", "Human approves refunds, pets, events, late checkout."],
            ["Maintenance issue", "Capture issue, urgency, reservation; advisor SMS.", "Human coordinates service."],
            ["VIP/influencer", "Flag pipeline and route to VIP number.", "High-touch handling."]
        ]))

    add_text_page("Risk matrix", section="GOVERNANCE",
        rows=([1.9 * inch, 2.9 * inch, 2.7 * inch], [
            ["Risk", "Current mitigation", "Next hardening step"],
            ["Dashboard password reuse", "Protected lock already exists.", "Move to signed internal auth."],
            ["Local/deploy drift", "Report documents discrepancy.", "Make deployment artifact versioned."],
            ["Transcript privacy", "Local/private boundaries documented.", "Role-based access and retention policy."],
            ["Analytics false positives", "Metrics are decision support.", "Human labels and QA scorecards."],
            ["Tool overreach", "Guesty read-only and SMS/handoff scoped.", "Approval workflow before any write tool."],
            ["Unstaffed handoff", "SMS/transfer tools exist.", "Define SLA and schedule."]
        ]))

    add_text_page("Roadmap - next engineering improvements", section="GOVERNANCE",
        rows=([1.9 * inch, 3.05 * inch, 2.55 * inch], [
            ["Initiative", "Why", "Priority"],
            ["Reconcile deployed UI into repo", "Removes source-of-truth ambiguity.", "High"],
            ["Signed admin auth", "Hardens protected dashboard.", "High"],
            ["Property-level analytics", "Find homes causing repeat issues.", "High"],
            ["Resolution labels", "Make FCR and quality more reliable.", "Medium"],
            ["Conversion funnel", "Connect calls to bookings.", "Medium"],
            ["Alerting", "Notify spikes in lockouts, handoffs or VIP calls.", "Medium"],
            ["Retrieval-based KB", "Use cases without prompt bloat.", "Medium"]
        ]))

    add_text_page("Orbit / Ai People reusable pattern", section="ORBIT REFERENCE MODEL",
        rows=([1.65 * inch, 3.15 * inch, 2.7 * inch], [
            ["Pattern", "GLAM HOMES proof", "Reusable vertical example"],
            ["Live API tool", "Guesty PMS.", "CRM, EHR, dispatch, ERP."],
            ["Voice interface", "Realtime phone concierge.", "Call centers and service desks."],
            ["Durable action channel", "Twilio SMS.", "Email, SMS, WhatsApp, ticketing."],
            ["Protected dashboard", "Analytics, calls, security.", "Supervisor consoles."],
            ["Human escalation", "Advisor SMS and transfer.", "Operations handoff."],
            ["Conversation intelligence", "24,072 case KB.", "Vertical playbooks."]
        ]))

    add_text_page("Executive recommendations", section="ORBIT REFERENCE MODEL",
        bullets_left=[
            "Position GLAM HOMES as the flagship hospitality call-center reference, not merely a concierge UI.",
            "Show the live screenshots first when presenting the project; they prove the product is operational.",
            "Lead with the problem solved: missed calls, unsafe static answers, manual SMS follow-up, and lack of management visibility.",
            "Treat Guesty as the first Ai People vertical tool: a read-only PMS connector with strict safety gates.",
            "Use the Analytics and Calls modules as the demo of managerial value: what happened, why it happened, what to do next.",
            "Before public export, reconcile the deployed front-end source back into the repo to avoid version drift."
        ],
        callout_text=("Board-level message", "The defensible asset is the operating pattern: live API truth + voice + action channel + protected supervision."))

    add_image_page("Supporting screenshot - Guesty tool test", "reports/glam-concierge-guesty-tool-test.png", "Existing QA evidence: Guesty tool test",
        ["Shows tool-level verification.", "Useful as appendix evidence.", "Complements live front-end screenshots."])

    add_image_page("Supporting screenshot - booking inventory", "reports/glamhomes-booking-site-properties.png", "Public booking property inventory",
        ["Shows public property surface.", "Connects SQLite links to user-facing booking inventory.", "Supports property-link SMS use case."])

    add_image_page("Supporting screenshot - rendered booking page", "reports/glamhomes-booking-site-rendered.png", "Rendered public booking property page",
        ["Shows destination experience after SMS link.", "Important for prospect conversion workflow.", "Confirms links are not abstract data only."])

    add_text_page("Appendix - screenshot inventory", section="APPENDIX",
        rows=([2.25 * inch, 3.15 * inch, 2.1 * inch], [
            ["Artifact", "Description", "Source"],
            ["01-live-voice-console-fullpage.png", "Desktop live voice console.", "Browser capture"],
            ["02-live-analytics-locked-fullpage.png", "Desktop live Analytics lock.", "Browser capture"],
            ["03-live-calls-locked-fullpage.png", "Desktop live Calls lock/inbox.", "Browser capture"],
            ["04-live-security-locked-fullpage.png", "Desktop live Security lock/settings.", "Browser capture"],
            ["06-live-mobile-voice-console-fullpage.png", "Mobile voice console.", "Browser capture"],
            ["07-live-mobile-analytics-fullpage.png", "Mobile Analytics lock.", "Browser capture"],
            ["08/09/10/11-live-*-viewport.png", "Clear desktop viewport captures for PDF readability.", "Browser capture"],
            ["live-index.html", "Downloaded deployed front-end HTML.", "curl"]
        ],),)

    add_text_page("Appendix - validation snapshot", section="APPENDIX",
        rows=([2.1 * inch, 3.15 * inch, 2.25 * inch], [
            ["Check", "Result", "Status"],
            ["Live site", "Loaded GLAM HOMES Concierge; screenshots captured.", "OK"],
            ["PDF generation", "ReportLab build with live images.", "OK"],
            ["SQLite", "PRAGMA integrity_check returned ok; 54/54 active properties.", "OK"],
            ["Knowledge base", "case_index.jsonl: 24,072 rows, 0 invalid JSON.", "OK"],
            ["Runtime import", "knowledge_base_loaded=True; Guesty/Twilio/Vapi configured after load_dotenv().", "OK"],
            ["JSON", "Property links and Guesty tool manifest parse as valid JSON.", "OK"],
            ["Runtime behavior", "No runtime code changed by this report generation.", "OK"]
        ]))

    add_text_page("Appendix - export package", section="APPENDIX",
        rows=([2.25 * inch, 3.15 * inch, 2.1 * inch], [
            ["Path", "Purpose", "Privacy"],
            ["orbit-aipeople/README.md", "Entry point for Orbit/Ai People.", "Safe"],
            ["SKILL_CATALOG.md", "Reusable skills list.", "Safe"],
            ["CONTROL_PANEL_ANALYTICS_GUIDE.md", "Human guide for dashboard use.", "Safe"],
            ["tools/guesty/tool-manifest.json", "Guesty tool contract.", "Safe"],
            ["reports/live-screenshots", "Live visual evidence and deployed HTML.", "Review before public sharing"],
            ["data/private/guesty-conversations", "Raw/private corpus and KB.", "Private"],
            ["transcripts/logs/.env/API Keys", "Operational secrets/data.", "Private"]
        ]))

    add_text_page("Final acceptance statement", section="APPENDIX",
        bullets_left=[
            "The report now uses real live screenshots from glamhomes.aipeople.app.",
            "Each front-end module is explained: Voice Console, Analytics, Calls and Security.",
            "Every visible analytics category is defined: KPIs, priority cards, charts, operational tables, concepts, filters and inbox controls.",
            "The report introduces the real business problem and why the system solves it.",
            "Engineering architecture is tied to code, APIs, data assets and runtime controls.",
            "A concrete deployment finding is documented: production UI is ahead of local front-end source in analytics separation/depth.",
            "No production runtime behavior was changed while producing this report."
        ],
        callout_text=("Conclusion", "GLAM HOMES is ready to be presented as a serious Orbit/Ai People reference implementation once the deployed UI is reconciled back into source control."))

    c.save()
    print(OUT)


if __name__ == "__main__":
    build()
