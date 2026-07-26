import os
import platform
from html.parser import HTMLParser

# CRITICAL: Fix for Mac WeasyPrint library path (Pango, etc.)
if platform.system() == "Darwin":
    homebrew_lib = "/opt/homebrew/lib"
    if os.path.exists(homebrew_lib):
        # Setting both for maximum compatibility across different MacOS/Python versions
        os.environ["DYLD_LIBRARY_PATH"] = homebrew_lib + ":" + os.environ.get("DYLD_LIBRARY_PATH", "")
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = homebrew_lib + ":" + os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        os.environ["PATH"] = homebrew_lib + ":" + os.environ.get("PATH", "")

import fitz
from dotenv import load_dotenv
from openai import OpenAI
from apify_client import ApifyClient

# Load environment variables (this automatically populates os.environ)
load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize Apify client
apify_client = ApifyClient(APIFY_API_TOKEN)

def extract_text_from_pdf(uploaded_file):
    """
    Extracts text from a PDF file.

    Args:
        uploaded_file (str or bytes): The path to the PDF file or a file-like object (like a Streamlit file upload).

    Returns:
        str: The extracted text.
    """
    text = ""
    try:
        # If it's a Streamlit UploadedFile, we read its stream.
        # Otherwise, if it's a file path string, we open it directly.
        if hasattr(uploaded_file, "read"):
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        else:
            doc = fitz.open(uploaded_file)

        with doc:
            for page in doc:
                text += page.get_text()

    except Exception as e:
        print(f"Error extracting text: {e}")

    return text

def tailor_resume(resume_text, job_description, html_template, approved_keywords=None, star_stories=None):
    """
    Tailors the resume text to the job description using OpenAI.
    """
    system_prompt = f"""
    # Resume Tailoring Agent — System Prompt

    ROLE
    You are an expert Resume Tailoring Agent. You take a candidate's resume and a Job
    Description, tailor the resume content to the JD, and output a tailored resume using
    resume_template.html as the base.

    STRICT RULES — MUST FOLLOW AT ALL TIMES
    1. Do not invent roles, projects, metrics, skills, or responsibilities not present in
       the original resume.
    2. Job titles must remain exactly as they appear in the original resume. Never upgrade
       or alter them.
    3. Do not add technologies, certifications, domain exposure, or tools not already
       evidenced in the resume.
    4. All numbers, percentages, and business outcomes must be preserved exactly as stated.
       Never round up or embellish.
    5. A JD keyword may only be added if the underlying skill or experience already exists
       in the resume. Relabelling is allowed; inventing is not.

    WHAT YOU ARE ALLOWED TO CHANGE
    - Update {{{{TARGET_TITLE}}}} to mirror the JD's role title, if it's an honest match to the
      candidate's actual scope.
    - Rewrite {{{{PROFESSIONAL_SUMMARY}}}} using the JD's top keywords, grounded entirely in
      existing experience.
    - Rephrase bullets using JD vocabulary without changing the underlying fact.
    - Reorder bullets within a role to lead with the most JD-relevant ones first.
    - Reorder, relabel, and surface skills in {{{{CORE_COMPETENCIES_HTML}}}} if they are already
      evidenced in the experience section.
    - Select which existing bullets to include if a role has more than fits cleanly.

    OUTPUT QUALITY STANDARDS
    - Top 5–8 skills and keywords from the JD must appear naturally, only where truthfully
      applicable.
    - {{{{PROFESSIONAL_SUMMARY}}}} must address the JD's top 2-3 requirements within its first
      2-3 sentences.
    - Every bullet follows the pattern: <li><b>Label:</b> detail sentence with a measurable
      outcome where one genuinely exists.</li>
    - Resume must not exceed 2 pages for candidates with under 10 years of experience.

    HTML TEMPLATE EDITING RULES — resume_template.html
    - Fill {{{{FULL_NAME}}}}, {{{{TARGET_TITLE}}}}, {{{{PHONE}}}}, {{{{EMAIL}}}}, {{{{LINKEDIN_URL}}}},
      {{{{LINKEDIN_DISPLAY}}}}, {{{{LOCATION}}}} from the source resume exactly as given.
    - Build {{{{EXPERIENCE_HTML}}}} following the .role-header / .company-desc / .team-line /
      ul.bullets structure documented in the template's own header comment. Role title,
      company, and dates MUST be preserved exactly as in the source resume.
    - Build {{{{EDUCATION_HTML}}}} using .edu-line divs, unchanged from source.
    - Build {{{{CORE_COMPETENCIES_HTML}}}} using .skills-category / .skills-line divs — never a
      <table>. Category order and skill order may be reprioritized for JD relevance.
    - DO NOT modify the <style> block. Content only.

    PORTFOLIO / CONTACT LINKS RULES
    - {{{{PORTFOLIO_ROW}}}}: if the source resume contains a personal website/portfolio URL,
      output plain text: "{{{{URL}}}} &nbsp;|&nbsp; " (no icon, no badge, no emoji).
    - If no portfolio URL exists in the source resume, set {{{{PORTFOLIO_ROW}}}} to an empty
      string. Never invent a URL.

    JD-AWARE BOLDING IN PROFESSIONAL SUMMARY
    - After writing {{{{PROFESSIONAL_SUMMARY}}}}, identify 4–6 short phrases (2–5 words each)
      that most directly mirror the JD's specific language or required skills.
    - Wrap ONLY those phrases in <b> tags. Do not bold entire sentences. Do not add new
      content — only highlight phrases that already exist in the summary you wrote.

    Return the COMPLETE tailored HTML, using resume_template.html as the unmodified base
    structure.
    """

    if approved_keywords:
        system_prompt += f"""
    APPROVED ATS KEYWORDS (relevance-filtered injection):
    {", ".join(approved_keywords)}

    For EACH keyword above, apply this check before using it:
    - Does the candidate's resume contain evidence of the underlying skill or experience?
    - If YES → weave the keyword in naturally (rephrase an existing bullet, add to skills section).
    - If NO → skip this keyword entirely. Do NOT invent experience, projects, or skills to justify it.
    Only a subset of the approved keywords will be relevant to any given resume. That is expected and correct.
    """

    if star_stories:
        from src.star_bank import build_resume_star_block
        system_prompt += build_resume_star_block(star_stories)

    user_prompt = f"""
    ORIGINAL RESUME TEXT:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    HTML TEMPLATE:
    {html_template}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1 if star_stories else 0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error tailoring resume: {e}")
        return ""

def generate_resume_pdf(html_content, output_filename):
    """
    Generates a PDF from HTML content using WeasyPrint.
    Always writes into the project-root output/ folder.
    """
    try:
        from weasyprint import HTML
        # Route to output/ folder unless a full absolute path is already given
        if not os.path.isabs(output_filename):
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
            os.makedirs(output_dir, exist_ok=True)
            output_filename = os.path.join(output_dir, os.path.basename(output_filename))

        # Remove markdown code blocks if the LLM returned them
        if "```html" in html_content:
            html_content = html_content.split("```html")[1].split("```")[0].strip()
        elif "```" in html_content:
            html_content = html_content.split("```")[1].split("```")[0].strip()

        HTML(string=html_content).write_pdf(output_filename)
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False

def generate_cover_letter(resume_text, job_description, html_template, company="", job_title="", star_stories=None):
    """
    Generates a filled cover letter HTML from the template using GPT-4o.
    company and job_title are passed explicitly so GPT cannot get them wrong.
    """
    from datetime import date
    today = date.today().strftime("%d %B %Y")

    system_prompt = f"""
You are an expert Cover Letter Writer. Given a candidate's resume and a job description, you fill a cover letter HTML template with personalized, compelling content.

STRICT RULES:
1. Never invent facts, companies, metrics, or skills not in the resume.
2. All numbers and achievements must come directly from the resume.
3. Contact details (LinkedIn, GitHub, website) only included if present in the resume.
4. Notice period: only state if explicitly present in the resume or provided by the candidate. If not available, omit the sentence entirely rather than defaulting to a guessed timeframe.
5. Keep paragraphs concise — 3–4 sentences each.

FIXED VALUES — use these EXACTLY, do not extract or infer from JD:
- {{DATE}} = {today}
- {{COMPANY_NAME}} = {company if company else "the company"}
- {{JOB_TITLE}} = {job_title if job_title else "the role"}

PLACEHOLDERS TO FILL:
Replace every {{{{PLACEHOLDER}}}} in the template with appropriate content.
- {{{{CANDIDATE_NAME}}}}: Full name from resume
- {{{{CANDIDATE_TITLE}}}}: Current or target role title aligned to JD
- {{{{CANDIDATE_PHONE}}}}: Phone from resume
- {{{{CANDIDATE_EMAIL}}}}: Email from resume
- {{{{LINKEDIN_URL}}}} / {{{{LINKEDIN_DISPLAY}}}}: LinkedIn URL if in resume, else remove the row
- {{{{WEBSITE_ROW}}}}: If website/portfolio URL in resume:
  <tr><td class="ci-label">Portfolio</td><td><a href="URL">display</a></td></tr>
  else empty string.
- {{{{GITHUB_ROW}}}}: If GitHub URL in resume:
  <tr><td class="ci-label">GitHub</td><td><a href="URL">display</a></td></tr>
  else empty string.
- {{{{CANDIDATE_LOCATION}}}}: Location from resume
- {{{{COMPANY_LOCATION}}}}: Company location from JD if available, else leave blank
- {{{{OPENING_PARAGRAPH}}}}: Strong opening — express interest in the role, mention years of experience, 2 key domains, and core value proposition. Use <strong> for at most 1-2 genuinely key phrases, not every notable phrase.
- {{{{WHY_ROLE_PARAGRAPH}}}}: Why this specific role excites the candidate — reference something specific from the JD. Use <strong> for at most 1-2 genuinely key phrases.
- {{{{HIGHLIGHT_1_LABEL}}}} to {{{{HIGHLIGHT_4_LABEL}}}}: Short label (3–5 words) for each achievement
- {{{{HIGHLIGHT_1_DETAIL}}}} to {{{{HIGHLIGHT_4_DETAIL}}}}: One-line detail with a real metric from the resume
- {{{{CULTURE_PARAGRAPH}}}}: Why the candidate fits this company's culture — grounded in resume evidence. Use <strong> for the company name only.
- {{{{CLOSING_PARAGRAPH}}}}: Closing — mention 2 specific skills and availability if the notice period is known (per Rule 4). Use <strong> for at most 1-2 genuinely key phrases.
- {{{{FOOTER_LINKS}}}}: If website in resume: <a href="URL">display</a> · then GitHub if present. Else empty string.

Restraint on <strong> matters more than coverage — a paragraph with one well-chosen bolded phrase reads as confident; a paragraph with four reads as noise.

Return ONLY the complete filled HTML. No markdown, no explanation.
"""

    if star_stories:
        from src.star_bank import build_cover_letter_star_block
        system_prompt += build_cover_letter_star_block(star_stories)

    user_prompt = f"""
RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

HTML TEMPLATE:
{html_template}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.3 if star_stories else 0.4,
        )
        filled_html = response.choices[0].message.content
        if "```html" in filled_html:
            filled_html = filled_html.split("```html")[1].split("```")[0].strip()
        elif "```" in filled_html:
            filled_html = filled_html.split("```")[1].split("```")[0].strip()
        return filled_html
    except Exception as e:
        print(f"Error generating cover letter: {e}")
        return ""


class _CoverLetterBodyExtractor(HTMLParser):
    """Pulls only the message body (salutation, paragraphs, highlights, sign-off) out of
    the filled cover letter HTML — the letterhead contact table, date/recipient block,
    subject line, and footer are PDF-only presentational elements that don't belong in a
    pasted message and were the source of the large gaps of near-empty lines."""

    _INCLUDE_CLASSES = {"salutation", "body-section", "highlight-box", "closing-block"}
    _BLOCK_TAGS = {"div", "p", "li", "ul"}

    def __init__(self):
        super().__init__()
        self.chunks = []
        self._include_depth = 0  # >0 while inside an included region
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        self._depth += 1
        classes = set((dict(attrs).get("class") or "").split())
        if self._include_depth == 0 and classes & self._INCLUDE_CLASSES:
            self._include_depth = self._depth
        if self._include_depth:
            if tag == "li":
                self.chunks.append("\n- ")
            elif tag in self._BLOCK_TAGS:
                self.chunks.append("\n")

    def handle_endtag(self, tag):
        if self._include_depth and self._depth == self._include_depth:
            self._include_depth = 0
        self._depth -= 1

    def handle_data(self, data):
        if self._include_depth:
            self.chunks.append(data)


def _extract_cover_letter_text(filled_html):
    """Extract plain, paste-ready text from filled cover letter HTML for copying into
    emails, LinkedIn messages, etc. No markdown or HTML markup — a destination that
    doesn't render markdown would otherwise show literal ** and swallow $ figures."""
    import re
    # Drop <strong> markup entirely — plain text has no bold, so don't fake it with markdown
    filled_html = re.sub(r'</?strong>', '', filled_html)
    parser = _CoverLetterBodyExtractor()
    parser.feed(filled_html)
    text = "".join(parser.chunks)
    lines = [ln.strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln]
    return "\n\n".join(lines)


def extract_post_job_signal(post_text):
    """Strip noise from a LinkedIn post and return only relevant job/skill signals."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": (
                    "You are a keyword extractor. Given a LinkedIn post, extract ONLY: "
                    "role titles, required skills, technologies, domain expertise, and experience requirements. "
                    "Ignore: calls to action, follower counts, emojis, 'we are hiring', 'DM me', "
                    "company culture fluff, motivational text, and candidate shoutouts. "
                    "Output a concise job signal summary in plain text, 100-150 words max."
                )},
                {"role": "user", "content": post_text}
            ],
            temperature=0.2,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error extracting post signal: {e}")
        return post_text


def generate_linkedin_dm(resume_text, post_text, author_name=""):
    """Generate a short LinkedIn DM (3-5 sentences) based on a post and the candidate's resume."""
    system_prompt = (
        "You are a LinkedIn outreach specialist. Write a SHORT, genuine LinkedIn DM based on "
        "a post and the candidate's resume.\n\n"
        "RULES:\n"
        "1. 4-5 sentences maximum. This is a casual DM, not a formal letter.\n"
        "2. Reference something specific from the post to show you actually read it.\n"
        "3. One strong sentence about the candidate's most relevant experience from the resume.\n"
        "4. End with a soft CTA — ask to connect or explore further.\n"
        "5. Tone: warm, professional, NOT salesy or desperate.\n"
        "6. Never invent skills or achievements not in the resume.\n"
        "7. Output ONLY the DM body — no greeting ('Hi X,'), no sign-off, no subject line. "
        "The user will add the personalised greeting themselves."
    )
    user_prompt = (
        f"POST BY {author_name or 'Author'}:\n{post_text}\n\n"
        f"MY RESUME:\n{resume_text}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating LinkedIn DM: {e}")
        return ""


def generate_poster_dm(resume_text, job_title, company, poster_name,
                        candidate_name, candidate_website="", candidate_github=""):
    """Generate a ready-to-send LinkedIn DM to a job poster."""
    salutation = f"Hi {poster_name.split()[0]}," if poster_name.strip() else "Hi,"

    sig_lines = [candidate_name]
    if candidate_website:
        sig_lines.append(candidate_website)
    if candidate_github:
        sig_lines.append(candidate_github)
    signature = "\n".join(sig_lines)

    system_prompt = (
        "You are a LinkedIn outreach specialist. Write ONLY 2-3 sentences explaining "
        "why the candidate is a strong fit for the role, based on their resume.\n\n"
        "RULES:\n"
        "- Be specific — reference actual skills or achievements from the resume.\n"
        "- Never invent anything not in the resume.\n"
        "- Tone: warm, confident, NOT salesy.\n"
        "- Output ONLY the 2-3 fit sentences. No greeting, no opening line, no sign-off."
    )
    user_prompt = (
        f"ROLE: {job_title} at {company}\n\n"
        f"RESUME:\n{resume_text[:3000]}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=150,
            temperature=0.4,
        )
        fit_lines = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating poster DM: {e}")
        fit_lines = "My background closely aligns with this role."

    return (
        f"{salutation}\n\n"
        f"I recently came across the {job_title} opening at {company} and wanted to reach out.\n\n"
        f"{fit_lines}\n\n"
        f"Looking forward to hearing from you.\n\n"
        f"{signature}"
    )


def extract_ats_keywords(jd_texts: list, progress_callback=None) -> dict:
    """
    Extract ATS-boosting keywords from a list of JD texts using 5 parallel workers.
    progress_callback(completed_batches, total_batches) is called after each batch finishes.
    Returns {category: {keyword: frequency}} aggregated across all batches.
    """
    import json as _json
    import math
    import time
    import random
    from concurrent.futures import ThreadPoolExecutor, as_completed

    BATCH_SIZE = 15
    TRUNC      = 1000
    MAX_WORKERS = 5
    MAX_RETRIES = 5

    system_prompt = (
        "You are an ATS keyword extraction specialist. Given a batch of job descriptions, "
        "extract the most impactful ATS-boosting terms across 4 categories.\n\n"
        "Return ONLY a valid JSON object with these exact keys:\n"
        "- power_verbs: action verbs that appear in JDs (Led, Scaled, Optimized, Drove, Launched...)\n"
        "- technical_skills: tools, platforms, methodologies (SQL, JIRA, OKRs, A/B Testing, Agile...)\n"
        "- domain_keywords: industry/domain terms (go-to-market, product-market fit, NPS, CAC, LTV...)\n"
        "- ats_phrases: multi-word phrases recruiters search for (cross-functional collaboration, "
        "stakeholder management, data-driven decision making...)\n\n"
        "Rules:\n"
        "- Only include terms that genuinely appear across multiple JDs in this batch\n"
        "- 15-25 items per category maximum\n"
        "- No duplicates, no generic filler words\n"
        "- Return ONLY the JSON, no explanation"
    )

    category_map = {
        "power_verbs":     "power_verb",
        "technical_skills":"technical_skill",
        "domain_keywords": "domain_keyword",
        "ats_phrases":     "ats_phrase",
    }
    aggregated = {cat: {} for cat in category_map.values()}

    # Build non-empty batches upfront
    total_batches = math.ceil(len(jd_texts) / BATCH_SIZE)
    batches = []
    for i in range(total_batches):
        chunk = jd_texts[i * BATCH_SIZE:(i + 1) * BATCH_SIZE]
        combined = "\n\n---\n\n".join(t[:TRUNC] for t in chunk if t and t.strip())
        if combined.strip():
            batches.append((i, combined))

    def _call_api(idx_combined):
        idx, combined = idx_combined
        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model="gpt-4.1",
                    temperature=0.1,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": f"JOB DESCRIPTIONS:\n{combined}"},
                    ],
                )
                return idx, _json.loads(response.choices[0].message.content)
            except Exception as e:
                err = str(e)
                if "429" in err or "rate_limit" in err.lower():
                    wait = (2 ** attempt) + random.uniform(0.5, 1.5)
                    time.sleep(wait)
                else:
                    print(f"ATS extraction error (batch {idx}, attempt {attempt+1}): {e}")
                    return idx, {}
        return idx, {}

    completed = 0
    total = len(batches)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_call_api, b): b[0] for b in batches}
        for future in as_completed(futures):
            _, raw = future.result()
            completed += 1
            if progress_callback:
                progress_callback(completed, total)
            for json_key, db_category in category_map.items():
                for kw in raw.get(json_key, []):
                    kw = kw.strip()
                    if kw:
                        aggregated[db_category][kw] = aggregated[db_category].get(kw, 0) + 1

    return aggregated


def ask_openai(prompt, max_tokens=1000):
    """
    Sends a prompt to the OpenAI API and returns the response.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.5,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error communicating with OpenAI: {e}")
        return ""


def generate_search_titles(resume_summary: str) -> dict:
    """
    Returns {"current_title": str, "search_titles": [str, ...]} ordered as:
      [0] exact current designation
      [1-2] aliases / common variants (including Product Owner / Senior Product Owner where applicable)
      [3-4] one level above
      [5-6] two levels above
    """
    import json
    prompt = f"""You are a job search expert. Analyse the resume summary below and return a JSON object with exactly two keys:

"current_title": the exact current or most recent job title from the resume (string)
"search_titles": an ordered list of 6-8 job titles to search, structured as:
  - Index 0: exact current designation
  - Index 1-2: common aliases and variants (e.g. for a Product Manager role, include "Product Owner" and "Senior Product Owner" as aliases)
  - Index 3-4: titles one level above current (e.g. Senior / Lead equivalents)
  - Index 5-6: titles two levels above current (e.g. Director / Group-level equivalents)
  If the resume shows strong AI/ML exposure, include an "AI Product Manager" or equivalent AI variant.
  Keep each title concise (2-5 words). No explanations in the list — only job title strings.

Resume summary:
{resume_summary}

Return ONLY valid JSON, no explanation, no markdown."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful assistant that returns only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"generate_search_titles error: {e}")
        return {"current_title": "Product Manager", "search_titles": ["Product Manager", "Senior Product Manager"]}

