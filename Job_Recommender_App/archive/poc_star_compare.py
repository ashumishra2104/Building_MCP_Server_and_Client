"""
POC: Compare Traditional vs STAR-Enhanced Resume
─────────────────────────────────────────────────
1. Paste your JD into poc_jd.txt
2. Run: python poc_star_compare.py
3. Two PDFs are generated:
   - POC_A_Traditional.pdf   ← existing method
   - POC_B_STAR_Enhanced.pdf ← STAR stories woven in
"""

import os, json, re
from datetime import datetime
import openpyxl
from dotenv import load_dotenv

load_dotenv(override=True)

from openai import OpenAI
from supabase import create_client
from src.helper import generate_resume_pdf

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

APP_DIR    = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(APP_DIR, "output", "testing")
os.makedirs(OUTPUT_DIR, exist_ok=True)
EXCEL_PATH = os.path.join(APP_DIR, "Ashu_STAR_Bank_v2.xlsx")
JD_FILE    = os.path.join(APP_DIR, "poc_jd.txt")
TEMPLATE   = os.path.join(APP_DIR, "resume_template.html")
USER_EMAIL = "demo@nomail.com"

# ── Helpers ────────────────────────────────────────────────────────

def load_jd():
    if not os.path.exists(JD_FILE):
        raise FileNotFoundError(f"Create {JD_FILE} and paste the job description into it.")
    with open(JD_FILE) as f:
        jd = f.read().strip()
    if not jd:
        raise ValueError("poc_jd.txt is empty — paste the JD into it.")
    return jd


def extract_company_name(jd):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content":
            f"Extract only the hiring company name from this job description. "
            f"Return just the company name, nothing else. Max 3 words.\n\nJD:\n{jd[:1500]}"}],
        temperature=0,
        max_tokens=20,
    )
    name = resp.choices[0].message.content.strip().replace("/", "-").replace(" ", "_")
    return name or "Unknown"


def load_resume():
    row = supabase.table("user_profiles").select("resume_text, candidate_name") \
        .eq("user_email", USER_EMAIL).single().execute()
    if not row.data or not row.data.get("resume_text"):
        raise ValueError("No resume found in Supabase for this user. Save one via My Profile first.")
    print(f"✓ Resume loaded for: {row.data.get('candidate_name', USER_EMAIL)}")
    return row.data["resume_text"], row.data.get("candidate_name", "Candidate")


def load_html_template():
    with open(TEMPLATE) as f:
        return f.read()


def parse_star_bank():
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb["STAR Achievement Bank"]
    stories = []
    for row in ws.iter_rows(min_row=4, values_only=True):
        company      = row[1]
        project_name = row[2]
        # skip Amazon LP column (index 3)
        situation    = row[4]
        task         = row[5]
        action       = row[6]
        result       = row[7]
        if not company:
            continue
        stories.append({
            "company":      str(company).strip(),
            "project_name": str(project_name).strip() if project_name else "",
            "situation":    str(situation).strip()    if situation    else "",
            "task":         str(task).strip()         if task         else "",
            "action":       str(action).strip()       if action       else "",
            "result":       str(result).strip()       if result       else "",
        })
    print(f"✓ Parsed {len(stories)} stories from STAR bank")
    return stories


def select_stories(jd, stories, top_n=3):
    summaries = "\n".join(
        f"[{i}] {s['company']} | {s['project_name']}\n"
        f"    Result: {s['result'][:220]}"
        for i, s in enumerate(stories)
    )
    prompt = f"""You are evaluating which achievement stories from a candidate's experience bank
are most relevant to a given Job Description.

Return a JSON object with key "indices" containing an array of the top {top_n} most relevant
story indices (0-based integers), ordered by relevance. If fewer than {top_n} stories are
clearly relevant, return only those. If none are relevant, return an empty array.

JOB DESCRIPTION (first 2500 chars):
{jd[:2500]}

CANDIDATE STORIES:
{summaries}

Return ONLY valid JSON, e.g. {{"indices": [2, 7, 0]}}"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    data = json.loads(resp.choices[0].message.content)
    indices = [i for i in data.get("indices", []) if 0 <= i < len(stories)][:top_n]
    selected = [stories[i] for i in indices]
    print(f"✓ Selected {len(selected)} STAR stories: "
          + ", ".join(f"[{i}] {stories[i]['company']} | {stories[i]['project_name']}" for i in indices))
    return selected


def build_star_block(selected_stories):
    if not selected_stories:
        return ""
    block = "\n\n    STAR ACHIEVEMENT BANK — WEAVING INSTRUCTIONS\n"
    block += f"    The following {len(selected_stories)} verified achievement stories must inform your rewrite.\n\n"
    for i, s in enumerate(selected_stories, 1):
        block += f"""
    [STORY {i} — {s['company']} | {s['project_name']}]
    Situation : {s['situation']}
    Task      : {s['task']}
    Action    : {s['action']}
    Result    : {s['result']}
    [END STORY {i}]
"""
    block += """
    MANDATORY WEAVING RULES:
    1. Find bullets in the Experience section whose role/company/context overlaps with a story above.
    2. Where overlap exists, incorporate the story's confirmed metrics/outcomes into that bullet as
       supporting evidence. Blend naturally — do not append as a new sentence.
    3. Use ONLY numbers and facts that appear verbatim in the story. Never paraphrase metrics.
       "55 crore" stays "55 crore". "99.5%" stays "99.5%". "500 → 700 STRs/day" stays as-is.
    4. Company binding: Story 1 belongs to its named company. Only use its metrics in bullets
       for that company's role in the Experience section. Never cross-contaminate.
    5. Do NOT create a new section or sub-heading for these stories. Weave into existing bullets only.
    6. If no existing bullet is a natural home for a story's metrics — skip that story. Do not force.
    7. All anti-fabrication rules above still apply on top of these instructions.
    """
    return block


def tailor_resume_traditional(resume_text, jd, html_template):
    """Resume A — existing method, no STAR stories."""
    system_prompt = _base_system_prompt()
    return _call_gpt(system_prompt, resume_text, jd, html_template, temperature=0.3)


def tailor_resume_star(resume_text, jd, html_template, selected_stories):
    """Resume B — STAR-enhanced method."""
    system_prompt = _base_system_prompt() + build_star_block(selected_stories)
    return _call_gpt(system_prompt, resume_text, jd, html_template, temperature=0.1)


def _base_system_prompt():
    return """
    # Resume Tailoring Agent — System Prompt

    ROLE
    You are an expert Resume Tailoring Agent. You take a candidate's resume and a Job Description,
    tailor the resume content to the JD, and output a beautifully formatted PDF using the HTML template.

    STRICT RULES — MUST FOLLOW AT ALL TIMES
    1. Do not invent roles, projects, metrics, skills, or responsibilities not in the original resume.
    2. Job titles must remain exactly as they appear in the original resume. Never upgrade or alter them.
    3. Do not add technologies, certifications, domain exposure, or tools not already evidenced.
    4. All numbers, percentages, and business outcomes must be preserved exactly. Never round up or embellish.
    5. A JD keyword may only be added if the underlying skill or experience already exists in the resume.

    WHAT YOU ARE ALLOWED TO CHANGE
    - Update the resume tagline to mirror the JD's role title.
    - Rewrite the Professional Summary using the JD's top keywords, grounded in existing experience.
    - Rephrase bullets using JD vocabulary without changing the underlying fact.
    - Reorder bullets within a role to lead with the most JD-relevant ones first.
    - Reorder, relabel, and surface skills in Core Competencies if already evidenced.
    - Elevate sections that directly address the JD's key requirements.

    OUTPUT QUALITY STANDARDS
    - Top 5–8 skills and keywords from JD must appear naturally.
    - Professional Summary must address top 2-3 requirements in first 3 lines.
    - Every bullet must lead with an action verb and include a measurable outcome.
    - Resume must not exceed 3 pages. Third-person implicit tone.

    HTML TEMPLATE EDITING RULES
    - Use the HTML template provided as the BASE.
    - Fill in .name, .tagline. Update .summary p content.
    - Update .competency-table rows (3 rows × 4 cols max).
    - Update .job blocks. .job-title, .job-company, .job-dates MUST be preserved.
    - Bullets inside <ul class="bullets"><li>. Use <span class="bold"> for metrics.
    - Achievements in .achievements-table (2 cols, <span class="label"> for titles).
    - DO NOT change CSS or visual design.

    PORTFOLIO / CONTACT LINKS
    - Scan resume for GitHub URL → replace <!-- PORTFOLIO_GITHUB_ROW --> or remove placeholder.
    - Scan resume for portfolio website → replace <!-- PORTFOLIO_WEBSITE_ROW --> or remove.
    - Never invent URLs.

    JD-AWARE BOLDING IN SUMMARY
    - After writing summary, identify 4–6 short phrases (2–5 words) that mirror JD language.
    - Wrap ONLY those in <strong> tags. Do not bold entire sentences.

    Return the COMPLETE tailored HTML.
    """


def _call_gpt(system_prompt, resume_text, jd, html_template, temperature):
    user_prompt = f"""
ORIGINAL RESUME TEXT:
{resume_text}

JOB DESCRIPTION:
{jd}

HTML TEMPLATE:
{html_template}
"""
    resp = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content


def validate_metrics(selected_stories, html_output):
    """Check that each key metric from selected stories appears verbatim in the HTML."""
    metric_pattern = re.compile(
        r'(\d[\d,\.]*\s*(?:crore|lakh|%|x|X)?'
        r'|\d+\s*→\s*\d+'
        r'|\d+\s*(?:warehouses?|clients?|days?|weeks?|months?)'
        r'|\d+\.\d+%?)',
        re.IGNORECASE
    )
    missing = []
    for s in selected_stories:
        metrics_in_story = set(metric_pattern.findall(s["result"]))
        for m in metrics_in_story:
            if m not in html_output:
                missing.append((s["project_name"], m))
    return missing


# ── Main ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== POC: Traditional vs STAR-Enhanced Resume ===\n")

    jd            = load_jd()
    resume_text, name = load_resume()
    html_template = load_html_template()
    stories       = parse_star_bank()

    company  = extract_company_name(jd)
    run_ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_tag  = f"{company}_{run_ts}"
    print(f"✓ Company detected: {company.replace('_', ' ')}")

    selected      = select_stories(jd, stories)

    # ── Resume A: Traditional ──────────────────────────────────────
    print("\n[1/2] Generating Resume A — Traditional method...")
    html_a = tailor_resume_traditional(resume_text, jd, html_template)
    out_a  = os.path.join(OUTPUT_DIR, f"POC_A_Traditional_{run_tag}.pdf")
    if generate_resume_pdf(html_a, out_a):
        print(f"    ✓ Saved: {out_a}")
    else:
        print("    ✗ PDF generation failed for Resume A")

    # ── Resume B: STAR-Enhanced ────────────────────────────────────
    print("\n[2/2] Generating Resume B — STAR-Enhanced method...")
    if selected:
        html_b = tailor_resume_star(resume_text, jd, html_template, selected)
        out_b  = os.path.join(OUTPUT_DIR, f"POC_B_STAR_Enhanced_{run_tag}.pdf")
        if generate_resume_pdf(html_b, out_b):
            print(f"    ✓ Saved: {out_b}")
        else:
            print("    ✗ PDF generation failed for Resume B")

        # ── Post-validation ────────────────────────────────────────
        missing = validate_metrics(selected, html_b)
        if missing:
            print(f"\n⚠️  Metric check — {len(missing)} metric(s) not found verbatim in Resume B:")
            for proj, m in missing:
                print(f"    [{proj}] missing: '{m}'")
        else:
            print("\n✅  Metric check passed — all story metrics present verbatim in Resume B")
    else:
        print("    ⚠️  No matching STAR stories found for this JD.")
        print("    Resume B not generated — traditional method is the correct fallback.")

    print("\n=== Done. Compare the two PDFs side by side. ===\n")
