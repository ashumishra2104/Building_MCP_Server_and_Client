import fitz
import os
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

def ask_openai(prompt, max_tokens=1000):
    """
    Sends a prompt to the OpenAI API and returns the response.

    Args:
        prompt (str): The prompt to send to the OpenAI API.
        max_tokens (int): The maximum number of tokens to generate.
    Returns:
        str: The response from the OpenAI API.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.5,
            messages=[
                {   "role": "system", 
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error communicating with OpenAI: {e}")
        return ""

