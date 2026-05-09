import os
import platform

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

def tailor_resume(resume_text, job_description, html_template):
    """
    Tailors the resume text to the job description using OpenAI.
    """
    system_prompt = f"""
    # Resume Tailoring Agent — System Prompt

    ROLE
    You are an expert Resume Tailoring Agent. You take a candidate's resume and a Job Description, tailor the resume content to the JD, and output a beautifully formatted PDF using the HTML template provided.

    STRICT RULES — MUST FOLLOW AT ALL TIMES
    1. Do not invent roles, projects, metrics, skills, or responsibilities not present in the original resume.
    2. Job titles must remain exactly as they appear in the original resume. Never upgrade or alter them.
    3. Do not add technologies, certifications, domain exposure, or tools not already evidenced in the resume.
    4. All numbers, percentages, and business outcomes must be preserved exactly as stated. Never round up or embellish.
    5. A JD keyword may only be added if the underlying skill or experience already exists in the resume. Relabelling is allowed; inventing is not.

    WHAT YOU ARE ALLOWED TO CHANGE
    - Update the resume tagline to mirror the JD's role title.
    - Rewrite the Professional Summary using the JD's top keywords, grounded entirely in existing experience.
    - Rephrase bullets using JD vocabulary without changing the underlying fact.
    - Reorder bullets within a role to lead with the most JD-relevant ones first.
    - Reorder, relabel, and surface skills in Core Competencies if they are already evidenced in the experience section.
    - Elevate sections that directly address the JD's key requirements.

    OUTPUT QUALITY STANDARDS
    - Top 5–8 skills and keywords from JD must appear naturally.
    - Professional Summary must address top 2-3 requirements in first 3 lines.
    - Every bullet must lead with an action verb and include a measurable outcome.
    - Resume must not exceed 3 pages.
    - Third-person implicit tone.

    HTML TEMPLATE EDITING RULES
    - Use the HTML template provided as the BASE.
    - Fill in .name, .tagline.
    - Update .summary p content.
    - Update .competency-table rows with up to 12 cells (3 rows × 4 cols). Keep the table structure.
    - Update .job blocks. .job-title, .job-company, .job-dates MUST be preserved.
    - Bullets go inside <ul class="bullets"><li> tags. Use <span class="bold"> for metrics.
    - Achievements go in .achievements-table (2 columns, each cell has <span class="label"> for the title).
    - DO NOT change CSS or visual design. Only update content.

    PORTFOLIO / CONTACT LINKS RULES
    The template contains placeholder comments in the contact-table row:
      <!-- PORTFOLIO_GITHUB_ROW -->
      <!-- PORTFOLIO_WEBSITE_ROW -->
    - Scan the original resume text for a GitHub URL (github.com/...) and a personal website/portfolio URL.
    - If a GitHub URL is found in the resume, replace <!-- PORTFOLIO_GITHUB_ROW --> with:
      <td><a class="contact-badge badge-github" href="GITHUB_URL">&lt;/&gt; GitHub</a></td>
    - If a website/portfolio URL is found in the resume (not linkedin, not github), replace <!-- PORTFOLIO_WEBSITE_ROW --> with:
      <td><a class="contact-badge badge-website" href="WEBSITE_URL">🌐 Portfolio</a></td>
    - If a link is NOT present in the resume, remove its placeholder comment entirely. Never invent URLs.

    JD-AWARE BOLDING IN PROFESSIONAL SUMMARY
    - After writing the Professional Summary, identify 4–6 short phrases (2–5 words each) within it that most directly mirror the JD's specific language, required skills, or key responsibilities.
    - Wrap ONLY those phrases in <strong> tags: <strong>phrase here</strong>
    - Do NOT bold entire sentences. Do NOT add new content. Only highlight phrases that already exist in the summary.
    - The <strong> styling (navy, bold) is already defined in the CSS — do not add inline styles.

    Return the COMPLETE tailored HTML.
    """

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
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error tailoring resume: {e}")
        return ""

def generate_resume_pdf(html_content, output_filename):
    """
    Generates a PDF from HTML content using WeasyPrint.
    """
    try:
        from weasyprint import HTML
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

def generate_cover_letter(resume_text, job_description, html_template, company="", job_title=""):
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
4. Notice period: extract from resume if mentioned, otherwise use "immediate to 4 weeks".
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
- {{{{WEBSITE_ROW}}}}: If website/portfolio URL in resume: <tr><td class="ci">🌐</td><td><a href="URL">display</a></td></tr>, else empty string
- {{{{GITHUB_ROW}}}}: If GitHub URL in resume: <tr><td class="ci"><span class="contact-badge gh">&lt;/&gt;</span></td><td><a href="URL">display</a></td></tr>, else empty string
- {{{{CANDIDATE_LOCATION}}}}: Location from resume
- {{{{COMPANY_LOCATION}}}}: Company location from JD if available, else leave blank
- {{{{OPENING_PARAGRAPH}}}}: Strong opening — express interest in the role, mention years of experience, 2 key domains, and core value proposition. Use <strong> tags for key phrases.
- {{{{WHY_ROLE_PARAGRAPH}}}}: Why this specific role excites the candidate — reference something specific from the JD. Use <strong> tags.
- {{{{HIGHLIGHT_1_LABEL}}}} to {{{{HIGHLIGHT_4_LABEL}}}}: Short label (3–5 words) for each achievement
- {{{{HIGHLIGHT_1_DETAIL}}}} to {{{{HIGHLIGHT_4_DETAIL}}}}: One-line detail with a real metric from the resume
- {{{{CULTURE_PARAGRAPH}}}}: Why the candidate fits this company's culture — grounded in resume evidence. Use <strong> for company name and work style.
- {{{{CLOSING_PARAGRAPH}}}}: Closing — mention 2 specific skills, availability, notice period. Use <strong> tags.
- {{{{FOOTER_LINKS}}}}: If website in resume: <a href="URL">display</a> · then GitHub if present. Else empty string.

Return ONLY the complete filled HTML. No markdown, no explanation.
"""

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
            temperature=0.4,
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


def _extract_cover_letter_text(filled_html):
    """Extract readable text blocks from filled cover letter HTML for UI preview."""
    import re
    # Remove style/head
    filled_html = re.sub(r'<head.*?</head>', '', filled_html, flags=re.DOTALL)
    filled_html = re.sub(r'<style.*?</style>', '', filled_html, flags=re.DOTALL)
    # Convert <strong> to markdown bold
    filled_html = re.sub(r'<strong>(.*?)</strong>', r'**\1**', filled_html)
    # Strip all other tags
    text = re.sub(r'<[^>]+>', ' ', filled_html)
    # Collapse whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


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

