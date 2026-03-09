#!/usr/bin/env python3

import os
import re
import sys
import argparse
import anthropic
from datetime import datetime
from pathlib import Path
from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT


def extract_resume_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()


def tailor_resume(base_resume: str, job_posting: str) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("Export it first: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are a professional resume writer. Given a base resume and a job posting, produce a tailored resume and cover letter.

BASE RESUME:
{base_resume}

JOB POSTING:
{job_posting}

Instructions:
1. Rewrite the Professional Summary (3-4 sentences) to directly match the job's needs
2. Reorder and reword bullet points to emphasize the most relevant experience -- do NOT invent new facts
3. Highlight the most relevant skills for this role
4. Write a compelling 3-paragraph cover letter (no more, no less)
5. Keep the cover letter professional but not generic -- reference specific things in the job posting

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

    print("Calling Claude to tailor resume...")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    return parse_response(message.content[0].text)


def parse_response(text: str) -> dict:
    sections = {}
    pattern = r'===(\w+)===(.*?)(?====\w+===|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    for key, value in matches:
        sections[key.strip()] = value.strip()
    return sections


def build_resume_pdf(sections: dict, name: str, contact: str, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.55*inch,
        leftMargin=0.55*inch,
        topMargin=0.45*inch,
        bottomMargin=0.45*inch
    )

    accent = colors.HexColor("#1a3a5c")
    light_rule = colors.HexColor("#cccccc")

    name_style = ParagraphStyle("Name", fontSize=20, fontName="Helvetica-Bold",
                                textColor=accent, spaceAfter=0, leading=24, alignment=TA_LEFT)
    contact_style = ParagraphStyle("Contact", fontSize=9, fontName="Helvetica",
                                   textColor=colors.HexColor("#555555"), spaceAfter=0)
    section_header = ParagraphStyle("SectionHeader", fontSize=9, fontName="Helvetica-Bold",
                                    textColor=accent, spaceBefore=6, spaceAfter=2,
                                    textTransform="uppercase", letterSpacing=1)
    job_title_style = ParagraphStyle("JobTitle", fontSize=9.5, fontName="Helvetica-Bold",
                                     textColor=colors.black, spaceBefore=4, spaceAfter=1)
    bullet_style = ParagraphStyle("Bullet", fontSize=8.5, fontName="Helvetica",
                                  leftIndent=10, firstLineIndent=-7, spaceAfter=1, leading=12)
    body_style = ParagraphStyle("Body", fontSize=8.5, fontName="Helvetica",
                                spaceAfter=2, leading=12)

    story = []

    story.append(Paragraph(name, name_style))
    story.append(Spacer(1, 5))
    story.append(Paragraph(contact, contact_style))
    story.append(Spacer(1, 5))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent, spaceAfter=6))

    if "SUMMARY" in sections:
        story.append(Paragraph("Professional Summary", section_header))
        story.append(HRFlowable(width="100%", thickness=0.5, color=light_rule, spaceAfter=2))
        story.append(Paragraph(sections["SUMMARY"], body_style))

    if "EXPERIENCE" in sections:
        story.append(Paragraph("Professional Experience", section_header))
        story.append(HRFlowable(width="100%", thickness=0.5, color=light_rule, spaceAfter=2))

        for entry in re.split(r'\n(?=[A-Z][^\n]+\|)', sections["EXPERIENCE"]):
            entry = entry.strip()
            if not entry:
                continue
            lines = entry.split('\n')
            parts = [p.strip() for p in lines[0].split('|')]
            company = parts[0] if len(parts) > 0 else ""
            title   = parts[1] if len(parts) > 1 else ""
            dates   = parts[2] if len(parts) > 2 else ""

            row = [[
                Paragraph(f"<b>{company}</b> -- {title}", job_title_style),
                Paragraph(dates, ParagraphStyle("Dates", fontSize=9,
                          fontName="Helvetica-Oblique",
                          textColor=colors.HexColor("#555555"),
                          alignment=TA_RIGHT))
            ]]
            t = Table(row, colWidths=[4.8*inch, 2.6*inch])
            t.setStyle(TableStyle([
                ('VALIGN',        (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING',   (0,0), (-1,-1), 0),
                ('RIGHTPADDING',  (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ]))
            story.append(t)

            for line in lines[1:]:
                line = line.strip()
                if line.startswith('- '):
                    story.append(Paragraph(f"* {line[2:]}", bullet_style))
                elif line:
                    story.append(Paragraph(line, bullet_style))

    if "SKILLS" in sections:
        story.append(Paragraph("Technical Skills", section_header))
        story.append(HRFlowable(width="100%", thickness=0.5, color=light_rule, spaceAfter=2))
        for line in sections["SKILLS"].split('\n'):
            line = line.strip().lstrip('-').strip()
            if not line:
                continue
            if ':' in line:
                label, rest = line.split(':', 1)
                story.append(Paragraph(f"<b>{label.strip()}:</b> {rest.strip()}", body_style))
            else:
                story.append(Paragraph(line, body_style))

    story.append(Paragraph("Education & Certifications", section_header))
    story.append(HRFlowable(width="100%", thickness=0.5, color=light_rule, spaceAfter=2))
    story.append(Paragraph("B.S. Computer Engineering, University of Maine, 2016", body_style))
    story.append(Paragraph(
        "AWS Solutions Architect Associate (May 2024) &nbsp;|&nbsp; Google Cloud Engineer Associate (November 2021)",
        body_style
    ))

    doc.build(story)
    print(f"Resume saved: {output_path}")


def build_cover_letter_pdf(sections: dict, name: str, contact: str, output_path: str):
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
                                textColor=accent, spaceAfter=0, leading=26)
    contact_style = ParagraphStyle("Contact", fontSize=9.5, fontName="Helvetica",
                                   textColor=colors.HexColor("#555555"), spaceAfter=0)
    date_style = ParagraphStyle("Date", fontSize=10, fontName="Helvetica",
                                spaceAfter=16, spaceBefore=20)
    body_style = ParagraphStyle("Body", fontSize=10.5, fontName="Helvetica",
                                leading=16, spaceAfter=12)
    closing_style = ParagraphStyle("Closing", fontSize=10.5, fontName="Helvetica",
                                   spaceBefore=20, spaceAfter=4)

    story = []

    story.append(Paragraph(name, name_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(contact, contact_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=accent, spaceAfter=14))

    story.append(Paragraph(datetime.now().strftime("%B %d, %Y"), date_style))

    company = sections.get("COMPANY", "the Company")
    role    = sections.get("ROLE", "this position")
    story.append(Paragraph(
        f"Re: Application for {role} at {company}",
        ParagraphStyle("Re", fontSize=10.5, fontName="Helvetica-Bold", spaceAfter=16)
    ))
    story.append(Paragraph(f"Dear Hiring Team at {company},", body_style))

    if "COVER_LETTER" in sections:
        for para in [p.strip() for p in sections["COVER_LETTER"].split('\n\n') if p.strip()]:
            story.append(Paragraph(para.replace('\n', ' '), body_style))

    story.append(Paragraph("Sincerely,", closing_style))
    story.append(Spacer(1, 0.4*inch))
    story.append(Paragraph(name, body_style))

    doc.build(story)
    print(f"Cover letter saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Resume Tailor")
    parser.add_argument("resume", help="Path to base resume PDF")
    parser.add_argument("job_posting", nargs="?", help="Path to job posting .txt file (optional -- paste interactively if omitted)")
    args = parser.parse_args()

    if not Path(args.resume).exists():
        print(f"ERROR: Resume file not found: {args.resume}")
        sys.exit(1)

    print("=" * 60)
    print("  RESUME TAILOR")
    print("=" * 60)
    print()

    print(f"Reading resume: {args.resume}")
    base_resume = extract_resume_text(args.resume)

    # Pull name and contact line from top of extracted PDF text
    pdf_lines = [l.strip() for l in base_resume.splitlines() if l.strip()]
    name = pdf_lines[0] if pdf_lines else "Applicant"
    contact = ""
    for line in pdf_lines[1:4]:
        if "@" in line or re.search(r'\d{3}.*\d{4}', line):
            contact = line
            break

    if args.job_posting:
        if not Path(args.job_posting).exists():
            print(f"ERROR: Job posting file not found: {args.job_posting}")
            sys.exit(1)
        with open(args.job_posting, "r") as f:
            job_posting = f.read().strip()
        print(f"Reading job posting: {args.job_posting}")
    else:
        print("Paste the job posting below.")
        print("When done, enter a line with just '---' and press Enter.")
        print()
        pasted_lines = []
        while True:
            try:
                line = input()
                if line.strip() == "---":
                    break
                pasted_lines.append(line)
            except EOFError:
                break
        job_posting = '\n'.join(pasted_lines).strip()

    if not job_posting:
        print("No job posting provided. Exiting.")
        sys.exit(1)

    print()
    sections = tailor_resume(base_resume, job_posting)

    if not sections:
        print("ERROR: Failed to parse Claude's response.")
        sys.exit(1)

    output_dir = Path(args.resume).parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    company   = sections.get("COMPANY", "Company").replace(" ", "_").replace("/", "-")
    role      = sections.get("ROLE", "Role").replace(" ", "_").replace("/", "-")
    timestamp = datetime.now().strftime("%Y%m%d")
    base_name = f"{timestamp}_{company}_{role}"

    resume_path = output_dir / f"{base_name}_Resume.pdf"
    cover_path  = output_dir / f"{base_name}_CoverLetter.pdf"

    build_resume_pdf(sections, name, contact, str(resume_path))
    build_cover_letter_pdf(sections, name, contact, str(cover_path))

    print()
    print(f"Resume:       outputs/{base_name}_Resume.pdf")
    print(f"Cover Letter: outputs/{base_name}_CoverLetter.pdf")


if __name__ == "__main__":
    main()
