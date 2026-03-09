#!/usr/bin/env python3
"""
Resume Tailor — Johnny Trueman
Usage: python3 resume_tailor.py
Paste a job posting when prompted. Outputs tailored resume PDF + cover letter PDF.
"""

import os
import anthropic
import re
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Base Resume Data ───────────────────────────────────────────────────────────
BASE_RESUME = """
NAME: Johnny Trueman
EMAIL: JohnnyTrueman@gmail.com
PHONE: (207) 841-8794
LOCATION: Augusta, ME (Remote preferred)

SUMMARY:
Software engineer with 12+ years of experience building full-stack web applications. Expert in Django, React, and Python with proven ability to architect complex data processing systems and lead technical teams delivering mission-critical solutions.

EXPERIENCE:

RailPod | Lead Software Engineer | September 2024 – December 2025
- Architected full-stack railway inspection platform using Django REST Framework backend with React/TypeScript frontend, processing terabytes of track geometry data from laser scanners and multi-camera systems
- Built interactive data visualization system using Highcharts and D3.js, converting legacy SVG charts to JavaScript components via Python Transcrypt for real-time track profile analysis
- Developed advanced rail profile segmentation algorithms using NumPy/SciPy for automated region identification and implemented FRA compliance curve analysis with sub-meter odometer accuracy
- Optimized PostgreSQL queries and Django ORM performance, reducing query times by 60% while leading team through architecture decisions and code reviews

VividCloud | Software Engineer | June 2020 – July 2024
- Developed full-stack solutions using .NET, Java, Python, F#, and C++ for clients in insurance and warehouse automation industries
- Designed scalable microservices architectures and RESTful APIs optimized for high-volume transaction processing
- Built data pipelines and automation systems serving high-volume enterprise clients

Abbott Manufacturing | Software Engineer | September 2018 – June 2019
- Pioneered Manufacturing Software Engineer role, architecting software systems for production line automation
- Led team of interns with bi-weekly mentoring, establishing coding standards that improved team productivity

Building 36 | Device Engineer | February 2017 – July 2018
- Designed test procedures for IoT thermostats and Z-Wave devices using Embedded C, ensuring product reliability
- Developed factory test automation with custom GUI using I2C protocols and Raspberry Pi, reducing validation time by 40%

EDUCATION:
Bachelor of Science in Computer Engineering, University of Maine, 2016

CERTIFICATIONS:
- AWS Solutions Architect Associate (May 2024)
- Google Cloud Engineer Associate (November 2021)

SKILLS:
Languages: Python, JavaScript/TypeScript, Java, C++, F#, SQL, Embedded C
Frameworks: Django, Django REST Framework, React, Node.js
Data: NumPy, SciPy, Pandas, Highcharts, D3.js
Cloud: AWS, GCP, Docker, CI/CD
Databases: PostgreSQL, MySQL, MongoDB
AI/ML: Building autonomous AI agents, LLM integration, Python-based ML pipelines

SIDE PROJECTS:
- CrapperMapper: Full-stack mobile app (React Native/Expo + Django backend on AWS EC2) with PostGIS, AWS Cognito auth, S3, published to App Store and Google Play
- OptionsTrader: Autonomous Python trading bot using LLM-based signal judgment, live trading via Tradier API, deployed as systemd service on AWS EC2
"""

# ── Claude API Call ────────────────────────────────────────────────────────────
def tailor_resume(job_posting: str) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set.")
        print("   Export it first: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are a professional resume writer. Given a base resume and a job posting, produce a tailored resume and cover letter.

BASE RESUME:
{BASE_RESUME}

JOB POSTING:
{job_posting}

Instructions:
1. Rewrite the Professional Summary (3-4 sentences) to directly match the job's needs
2. Reorder and reword bullet points to emphasize the most relevant experience — do NOT invent new facts
3. Highlight the most relevant skills for this role
4. Write a compelling 3-paragraph cover letter (no more, no less)
5. Keep the cover letter professional but not generic — reference specific things in the job posting

Return your response in this EXACT format (use these exact section headers):

===SUMMARY===
[tailored summary here]

===EXPERIENCE===
[Company Name] | [Title] | [Dates]
- bullet
- bullet

[repeat for each role]

===SKILLS===
[relevant skills grouped logically, comma separated per line with category label]

===COVER_LETTER===
[3 paragraphs, no salutation/closing needed - just the body paragraphs]

===COMPANY===
[company name from job posting]

===ROLE===
[job title from job posting]
"""

    print("🤖 Calling Claude to tailor resume...")
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    response = message.content[0].text
    return parse_response(response)


def parse_response(text: str) -> dict:
    sections = {}
    pattern = r'===(\w+)===(.*?)(?====\w+===|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    for key, value in matches:
        sections[key.strip()] = value.strip()
    return sections


# ── PDF Generation ─────────────────────────────────────────────────────────────
def build_resume_pdf(sections: dict, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.65*inch,
        leftMargin=0.65*inch,
        topMargin=0.6*inch,
        bottomMargin=0.6*inch
    )

    # ── Styles ──
    accent = colors.HexColor("#1a3a5c")
    light_rule = colors.HexColor("#cccccc")

    name_style = ParagraphStyle("Name", fontSize=22, fontName="Helvetica-Bold",
                                 textColor=accent, spaceAfter=6, alignment=TA_LEFT)
    contact_style = ParagraphStyle("Contact", fontSize=9.5, fontName="Helvetica",
                                    textColor=colors.HexColor("#555555"), spaceAfter=8)
    section_header = ParagraphStyle("SectionHeader", fontSize=10, fontName="Helvetica-Bold",
                                     textColor=accent, spaceBefore=10, spaceAfter=3,
                                     textTransform="uppercase", letterSpacing=1)
    job_title_style = ParagraphStyle("JobTitle", fontSize=10, fontName="Helvetica-Bold",
                                      textColor=colors.black, spaceBefore=6, spaceAfter=1)
    job_meta_style = ParagraphStyle("JobMeta", fontSize=9, fontName="Helvetica-Oblique",
                                     textColor=colors.HexColor("#555555"), spaceAfter=2)
    bullet_style = ParagraphStyle("Bullet", fontSize=9, fontName="Helvetica",
                                   leftIndent=12, firstLineIndent=-8, spaceAfter=2,
                                   leading=13)
    body_style = ParagraphStyle("Body", fontSize=9, fontName="Helvetica",
                                 spaceAfter=4, leading=13)
    skills_label = ParagraphStyle("SkillsLabel", fontSize=9, fontName="Helvetica-Bold",
                                   spaceAfter=2)

    story = []

    # ── Header ──
    story.append(Paragraph("Johnny Trueman", name_style))
    story.append(Paragraph(
        "JohnnyTrueman@gmail.com &nbsp;&nbsp;|&nbsp;&nbsp; (207) 841-8794 &nbsp;&nbsp;|&nbsp;&nbsp; Augusta, ME &nbsp;&nbsp;|&nbsp;&nbsp; Remote",
        contact_style
    ))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=2, color=accent, spaceAfter=10))

    # ── Summary ──
    if "SUMMARY" in sections:
        story.append(Paragraph("Professional Summary", section_header))
        story.append(HRFlowable(width="100%", thickness=0.5, color=light_rule, spaceAfter=4))
        story.append(Paragraph(sections["SUMMARY"], body_style))

    # ── Experience ──
    if "EXPERIENCE" in sections:
        story.append(Paragraph("Professional Experience", section_header))
        story.append(HRFlowable(width="100%", thickness=0.5, color=light_rule, spaceAfter=4))

        exp_text = sections["EXPERIENCE"]
        entries = re.split(r'\n(?=[A-Z][^\n]+\|)', exp_text)

        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            lines = entry.split('\n')
            header_line = lines[0].strip()

            # Parse "Company | Title | Dates"
            parts = [p.strip() for p in header_line.split('|')]
            if len(parts) >= 3:
                company, title, dates = parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                company, title, dates = parts[0], parts[1], ""
            else:
                company, title, dates = header_line, "", ""

            # Company + dates on same line
            data = [[Paragraph(f"<b>{company}</b> — {title}", job_title_style),
                     Paragraph(dates, ParagraphStyle("Dates", fontSize=9,
                                fontName="Helvetica-Oblique",
                                textColor=colors.HexColor("#555555"),
                                alignment=TA_RIGHT))]]
            t = Table(data, colWidths=[4.5*inch, 2.5*inch])
            t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                                   ('LEFTPADDING', (0,0), (-1,-1), 0),
                                   ('RIGHTPADDING', (0,0), (-1,-1), 0),
                                   ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
            story.append(t)

            for line in lines[1:]:
                line = line.strip()
                if line.startswith('- '):
                    story.append(Paragraph(f"• {line[2:]}", bullet_style))
                elif line:
                    story.append(Paragraph(line, bullet_style))

    # ── Skills ──
    if "SKILLS" in sections:
        story.append(Paragraph("Technical Skills", section_header))
        story.append(HRFlowable(width="100%", thickness=0.5, color=light_rule, spaceAfter=4))
        for line in sections["SKILLS"].split('\n'):
            line = line.strip().lstrip('-').strip()
            if ':' in line:
                label, rest = line.split(':', 1)
                story.append(Paragraph(f"<b>{label.strip()}:</b> {rest.strip()}", body_style))
            elif line:
                story.append(Paragraph(line, body_style))

    # ── Education ──
    story.append(Paragraph("Education & Certifications", section_header))
    story.append(HRFlowable(width="100%", thickness=0.5, color=light_rule, spaceAfter=4))
    story.append(Paragraph("B.S. Computer Engineering, University of Maine, 2016", body_style))
    story.append(Paragraph("AWS Solutions Architect Associate (May 2024) &nbsp;|&nbsp; Google Cloud Engineer Associate (November 2021)", body_style))

    doc.build(story)
    print(f"✅ Resume saved: {output_path}")


def build_cover_letter_pdf(sections: dict, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=1*inch,
        leftMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )

    accent = colors.HexColor("#1a3a5c")
    name_style = ParagraphStyle("Name", fontSize=20, fontName="Helvetica-Bold",
                                 textColor=accent, spaceAfter=6)
    contact_style = ParagraphStyle("Contact", fontSize=9.5, fontName="Helvetica",
                                    textColor=colors.HexColor("#555555"), spaceAfter=8)
    date_style = ParagraphStyle("Date", fontSize=10, fontName="Helvetica",
                                 spaceAfter=16, spaceBefore=20)
    body_style = ParagraphStyle("Body", fontSize=10.5, fontName="Helvetica",
                                 leading=16, spaceAfter=12)
    closing_style = ParagraphStyle("Closing", fontSize=10.5, fontName="Helvetica",
                                    spaceBefore=20, spaceAfter=4)

    story = []

    story.append(Paragraph("Johnny Trueman", name_style))
    story.append(Paragraph(
        "JohnnyTrueman@gmail.com &nbsp;&nbsp;|&nbsp;&nbsp; (207) 841-8794 &nbsp;&nbsp;|&nbsp;&nbsp; Augusta, ME",
        contact_style
    ))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=2, color=accent, spaceAfter=12))

    today = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(today, date_style))

    company = sections.get("COMPANY", "the Company")
    role = sections.get("ROLE", "this position")
    story.append(Paragraph(f"Re: Application for {role} at {company}", 
                           ParagraphStyle("Re", fontSize=10.5, fontName="Helvetica-Bold", spaceAfter=16)))

    story.append(Paragraph(f"Dear Hiring Team at {company},", body_style))

    if "COVER_LETTER" in sections:
        paragraphs = [p.strip() for p in sections["COVER_LETTER"].split('\n\n') if p.strip()]
        for para in paragraphs:
            story.append(Paragraph(para.replace('\n', ' '), body_style))

    story.append(Paragraph("Sincerely,", closing_style))
    story.append(Spacer(1, 0.4*inch))
    story.append(Paragraph("Johnny Trueman", body_style))

    doc.build(story)
    print(f"✅ Cover letter saved: {output_path}")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  RESUME TAILOR — Johnny Trueman")
    print("=" * 60)
    print()
    print("Paste the job posting below.")
    print("When done, enter a line with just '---' and press Enter.")
    print()

    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "---":
                break
            lines.append(line)
        except EOFError:
            break

    job_posting = '\n'.join(lines).strip()
    if not job_posting:
        print("No job posting provided. Exiting.")
        sys.exit(1)

    print()
    sections = tailor_resume(job_posting)

    if not sections:
        print("❌ Failed to parse Claude's response. Raw output saved to debug.txt")
        sys.exit(1)

    company = sections.get("COMPANY", "Company").replace(" ", "_").replace("/", "-")
    role = sections.get("ROLE", "Role").replace(" ", "_").replace("/", "-")
    timestamp = datetime.now().strftime("%Y%m%d")
    base_name = f"{timestamp}_{company}_{role}"

    resume_path = f"{base_name}_Resume.pdf"
    cover_path = f"{base_name}_CoverLetter.pdf"

    build_resume_pdf(sections, resume_path)
    build_cover_letter_pdf(sections, cover_path)

    print()
    print(f"📄 Resume:      {resume_path}")
    print(f"📝 Cover Letter: {cover_path}")
    print()
    print("Done!")


if __name__ == "__main__":
    main()
