import os
import platform
import sys

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
    - Update .competencies with <span class="tag"> tags.
    - Update .job blocks. .job-title, .job-company, .job-dates MUST be preserved.
    - Bullets go inside <ul class="bullets"><li> tags. Use <span class="bold"> for metrics.
    - Achievements go in .achievements-grid.
    - DO NOT change CSS or visual design. Only update content.

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
            model="gpt-4o", # Using gpt-4o for complex formatting tasks
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

