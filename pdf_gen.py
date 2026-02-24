"""
FirstVoice - Legal Dossier Generator (pdf_gen.py)
--------------------------------------------------
Generates a professional court-ready PDF identity dossier
from the user's interview data.

Free: Uses ReportLab (no API needed, runs locally)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os


# ─────────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────────

DARK_BLUE   = colors.HexColor("#1a2744")
GOLD        = colors.HexColor("#c9a96e")
LIGHT_GRAY  = colors.HexColor("#f5f5f5")
MID_GRAY    = colors.HexColor("#888888")
GREEN       = colors.HexColor("#2d7a4f")
ORANGE      = colors.HexColor("#c47c2b")
RED         = colors.HexColor("#a83232")
WHITE       = colors.white
BLACK       = colors.black


# ─────────────────────────────────────────────
# SCORE COLOR
# ─────────────────────────────────────────────

def score_color(score):
    if score >= 75:
        return GREEN
    elif score >= 50:
        return ORANGE
    else:
        return RED

def score_label(score):
    if score >= 75:
        return "STRONG"
    elif score >= 50:
        return "MODERATE"
    else:
        return "PRELIMINARY"


# ─────────────────────────────────────────────
# MAIN PDF GENERATOR
# ─────────────────────────────────────────────

def generate_dossier_pdf(user_data, output_path=None):
    """
    Generate a legal identity dossier PDF.

    Args:
        user_data   : dict from conversation.conduct_interview()
        output_path : where to save the PDF (default: firstvoice_dossier.pdf)

    Returns:
        Path to the generated PDF file
    """

    if output_path is None:
        name_slug = user_data.get("name", "unknown").replace(" ", "_").lower()
        output_path = f"firstvoice_{name_slug}_dossier.pdf"

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    story = []
    styles = _build_styles()

    # ── HEADER ──
    story += _build_header(styles)
    story.append(Spacer(1, 0.5*cm))

    # ── DOSSIER ID & DATE ──
    story += _build_meta(user_data, styles)
    story.append(Spacer(1, 0.4*cm))

    # ── CONFIDENCE SCORE BANNER ──
    story += _build_score_banner(user_data, styles)
    story.append(Spacer(1, 0.5*cm))

    # ── SUBJECT PROFILE ──
    story += _build_subject_profile(user_data, styles)
    story.append(Spacer(1, 0.4*cm))

    # ── EVIDENCE BREAKDOWN ──
    story += _build_evidence_breakdown(user_data, styles)
    story.append(Spacer(1, 0.4*cm))

    # ── INTERVIEW TESTIMONY ──
    story += _build_testimony(user_data, styles)
    story.append(Spacer(1, 0.4*cm))

    # ── LEGAL SUMMARY ──
    story += _build_legal_summary(user_data, styles)
    story.append(Spacer(1, 0.4*cm))

    # ── NEXT STEPS ──
    story += _build_next_steps(user_data, styles)
    story.append(Spacer(1, 0.6*cm))

    # ── FOOTER ──
    story += _build_footer(styles)

    doc.build(story)
    print(f"✅ PDF generated: {output_path}")
    return output_path


# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["title"] = ParagraphStyle(
        "title", fontSize=22, textColor=DARK_BLUE,
        alignment=TA_CENTER, fontName="Helvetica-Bold",
        spaceAfter=4
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle", fontSize=11, textColor=GOLD,
        alignment=TA_CENTER, fontName="Helvetica",
        spaceAfter=2, letterSpacing=2
    )
    styles["section_header"] = ParagraphStyle(
        "section_header", fontSize=10, textColor=WHITE,
        fontName="Helvetica-Bold", spaceAfter=6,
        spaceBefore=4, letterSpacing=1
    )
    styles["body"] = ParagraphStyle(
        "body", fontSize=10, textColor=BLACK,
        fontName="Helvetica", leading=16,
        spaceAfter=4, alignment=TA_JUSTIFY
    )
    styles["label"] = ParagraphStyle(
        "label", fontSize=8, textColor=MID_GRAY,
        fontName="Helvetica-Bold", letterSpacing=1,
        spaceAfter=2
    )
    styles["value"] = ParagraphStyle(
        "value", fontSize=11, textColor=DARK_BLUE,
        fontName="Helvetica-Bold", spaceAfter=6
    )
    styles["small"] = ParagraphStyle(
        "small", fontSize=8, textColor=MID_GRAY,
        fontName="Helvetica", alignment=TA_CENTER
    )
    styles["fact"] = ParagraphStyle(
        "fact", fontSize=9, textColor=BLACK,
        fontName="Helvetica", leading=14,
        leftIndent=10, spaceAfter=2
    )

    return styles


# ─────────────────────────────────────────────
# SECTIONS
# ─────────────────────────────────────────────

def _build_header(styles):
    elements = []
    elements.append(Paragraph("FIRSTVOICE", styles["subtitle"]))
    elements.append(Paragraph("Legal Identity Dossier", styles["title"]))
    elements.append(HRFlowable(
        width="100%", thickness=2,
        color=GOLD, spaceAfter=6
    ))
    elements.append(Paragraph(
        "This document has been generated by FirstVoice AI — "
        "a system designed to help undocumented individuals establish legal identity "
        "through structured oral testimony and community evidence.",
        styles["small"]
    ))
    return elements


def _build_meta(user_data, styles):
    now = datetime.now()
    dossier_id = f"FV-{now.strftime('%Y%m%d')}-{abs(hash(user_data.get('name', 'X'))) % 9999:04d}"

    data = [
        ["DOSSIER ID", dossier_id, "DATE GENERATED", now.strftime("%d %B %Y")],
        ["LANGUAGE", user_data.get("language", "Unknown"), "STATUS", "PENDING VERIFICATION"],
    ]

    table = Table(data, colWidths=[3.5*cm, 6*cm, 4*cm, 4*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT_GRAY),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), DARK_BLUE),
        ("TEXTCOLOR", (2, 0), (2, -1), DARK_BLUE),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_GRAY]),
    ]))
    return [table]


def _build_score_banner(user_data, styles):
    score = user_data.get("overall_confidence", 0)
    col = score_color(score)
    label = score_label(score)

    data = [[
        Paragraph(f"IDENTITY CONFIDENCE SCORE", ParagraphStyle(
            "s", fontSize=9, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_CENTER
        )),
        Paragraph(f"{score}%", ParagraphStyle(
            "s2", fontSize=28, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_CENTER
        )),
        Paragraph(f"{label} EVIDENCE", ParagraphStyle(
            "s3", fontSize=11, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_CENTER
        )),
    ]]

    table = Table(data, colWidths=[6*cm, 3.5*cm, 7.5*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), col),
        ("PADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [6]),
    ]))
    return [table]


def _build_subject_profile(user_data, styles):
    elements = []

    # Section header
    header_data = [[Paragraph("SUBJECT PROFILE", styles["section_header"])]]
    header_table = Table(header_data, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.2*cm))

    fields = [
        ("IDENTIFIED NAME", user_data.get("name", "Unknown")),
        ("LOCATION / REGION", user_data.get("location", "Unknown")),
        ("COMMUNITY TIES", user_data.get("community", "Unknown")),
        ("FAMILY RECORD", user_data.get("family", "Unknown")),
        ("INTERVIEW LANGUAGE", user_data.get("language", "Unknown")),
    ]

    data = []
    for label, value in fields:
        data.append([
            Paragraph(label, styles["label"]),
            Paragraph(str(value), styles["value"])
        ])

    table = Table(data, colWidths=[4.5*cm, 12.5*cm])
    table.setStyle(TableStyle([
        ("PADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(table)
    return elements


def _build_evidence_breakdown(user_data, styles):
    elements = []

    header_data = [[Paragraph("EVIDENCE BREAKDOWN", styles["section_header"])]]
    header_table = Table(header_data, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.2*cm))

    evidence_scores = user_data.get("evidence_scores", {})

    evidence_labels = {
        "name_identity":       "Name & Identity",
        "location_history":    "Location History",
        "community_ties":      "Community Ties",
        "cultural_proof":      "Cultural Proof",
        "family_record":       "Family Record",
        "institutional_contact": "Institutional Contact",
        "physical_evidence":   "Physical Evidence",
        "additional_evidence": "Additional Evidence",
    }

    data = [["EVIDENCE TYPE", "SCORE", "RATING"]]
    for key, label in evidence_labels.items():
        score = evidence_scores.get(key, 0)
        rating = score_label(score)
        data.append([label, f"{score}%", rating])

    table = Table(data, colWidths=[8*cm, 3*cm, 6*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
    ]))

    # Color the rating column
    row_idx = 1
    for key in evidence_labels:
        score = evidence_scores.get(key, 0)
        col = score_color(score)
        table.setStyle(TableStyle([
            ("TEXTCOLOR", (2, row_idx), (2, row_idx), col),
            ("FONTNAME", (2, row_idx), (2, row_idx), "Helvetica-Bold"),
        ]))
        row_idx += 1

    elements.append(table)
    return elements


def _build_testimony(user_data, styles):
    elements = []

    header_data = [[Paragraph("ORAL TESTIMONY RECORD", styles["section_header"])]]
    header_table = Table(header_data, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.2*cm))

    answers = user_data.get("answers", {})
    extracted = user_data.get("extracted", {})

    question_map = {
        1: "Name & Identity",
        2: "Location & Origins",
        3: "Community Witnesses",
        4: "Cultural Markers",
        5: "Family Record",
        6: "Institutional Contact",
        7: "Physical Evidence",
        8: "Additional Statement",
    }

    if not answers:
        elements.append(Paragraph("No testimony recorded.", styles["body"]))
        return elements

    for q_id, answer in answers.items():
        if not answer:
            continue
        label = question_map.get(int(q_id), f"Question {q_id}")
        elements.append(Paragraph(f"▸ {label.upper()}", ParagraphStyle(
            "ql", fontSize=9, textColor=DARK_BLUE,
            fontName="Helvetica-Bold", spaceAfter=3, spaceBefore=6
        )))
        elements.append(Paragraph(f'"{answer}"', ParagraphStyle(
            "ans", fontSize=9, textColor=colors.HexColor("#333333"),
            fontName="Helvetica-Oblique", leading=14,
            leftIndent=10, spaceAfter=2
        )))

    return elements


def _build_legal_summary(user_data, styles):
    elements = []

    header_data = [[Paragraph("LEGAL ASSESSMENT", styles["section_header"])]]
    header_table = Table(header_data, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.2*cm))

    summary = user_data.get("legal_summary", (
        "Oral testimony and community evidence has been gathered through structured "
        "interview. The evidence collected forms a preliminary basis for identity "
        "verification proceedings with the appropriate authorities."
    ))

    elements.append(Paragraph(summary, styles["body"]))
    return elements


def _build_next_steps(user_data, styles):
    elements = []

    header_data = [[Paragraph("RECOMMENDED NEXT STEPS", styles["section_header"])]]
    header_table = Table(header_data, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.2*cm))

    next_steps = user_data.get("next_steps", [
        "Submit dossier to nearest District Legal Services Authority (DLSA)",
        "Apply for Aadhaar enrollment at a special camp with this dossier",
        "Contact local NGO partner to arrange elder testimony recording",
    ])

    for i, step in enumerate(next_steps, 1):
        elements.append(Paragraph(f"{i}.  {step}", styles["fact"]))

    return elements


def _build_footer(styles):
    elements = []
    elements.append(HRFlowable(
        width="100%", thickness=1,
        color=GOLD, spaceAfter=6
    ))
    elements.append(Paragraph(
        "This document was generated by FirstVoice AI — "
        "a tool for legal identity establishment for undocumented individuals. "
        "This dossier is intended to support, not replace, formal legal proceedings. "
        f"Generated on {datetime.now().strftime('%d %B %Y at %H:%M')}.",
        styles["small"]
    ))
    return elements


# ─────────────────────────────────────────────
# TEST — python pdf_gen.py
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  FirstVoice — PDF Generator Test")
    print("=" * 50)

    # Sample user data
    sample_data = {
        "name": "Chinna Ramu",
        "location": "Pallipalayam village, Tamil Nadu",
        "community": "Known by Elder Murugesan and Palanisamy since childhood",
        "family": "Mother: Lakshmi, Father: Selvam (farmers)",
        "language": "Tamil",
        "overall_confidence": 80,
        "evidence_scores": {
            "name_identity": 85,
            "location_history": 80,
            "community_ties": 75,
            "cultural_proof": 70,
            "family_record": 85,
            "institutional_contact": 65,
            "physical_evidence": 70,
            "additional_evidence": 60,
        },
        "answers": {
            1: "My name is Ramu. People call me Chinna Ramu in our village.",
            2: "I grew up near the Kaveri river in Pallipalayam village, Tamil Nadu.",
            3: "Elder Murugesan and Palanisamy have known me since I was a child.",
            4: "We celebrated Pongal every year. My family grew rice fields.",
            5: "My mother is Lakshmi, father is Selvam. They were farmers.",
            6: "I went to the village school until class 3. Teacher was Mr. Rajan.",
            7: "I have a scar on my left hand from a farming accident at age 10.",
            8: "My family has lived in this village for three generations.",
        },
        "legal_summary": (
            "Pursuant to applicable identity verification standards, this dossier "
            "presents corroborated oral testimony establishing the identity of the "
            "subject known as Chinna Ramu with an overall confidence rating of 80%. "
            "Evidence gathered includes consistent location history, named community "
            "witnesses, family records, and cultural markers specific to the Tamil Nadu "
            "region, collectively forming a strong basis for formal identity proceedings."
        ),
        "next_steps": [
            "Submit dossier to nearest District Legal Services Authority (DLSA)",
            "Apply for Aadhaar enrollment at a special camp with this dossier",
            "Contact local NGO partner to arrange elder testimony recording",
            "File application for birth certificate with Municipal Corporation",
        ],
    }

    path = generate_dossier_pdf(sample_data, "test_dossier.pdf")
    print(f"\n📄 Open this file to see your dossier:")
    print(f"   {os.path.abspath(path)}")
    print("\n✅ PDF generator working!\n")