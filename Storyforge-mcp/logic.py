import os
import time
import requests
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient

load_dotenv(override=True)

# Initialize clients once
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

model_info = "gpt-4o-mini"
model_script = "gpt-4o-mini"

CSS_THEME = """
    <style>
        .stApp {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            color: #f5f5f5;
        }
        h1, h2, h3 {
            text-align: center;
            color: #F9FAFB !important;
        }
        .stTextInput>div>div>input {
            border: 1px solid #6EE7B7 !important;
            border-radius: 10px;
            padding: 12px;
            background-color: #111827;
            color: white !important;
        }
        div.stButton > button {
            background: linear-gradient(90deg, #06b6d4, #3b82f6);
            color: white;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            border: none;
            transition: 0.3s ease-in-out;
        }
        div.stButton > button:hover {
            transform: scale(1.05);
            background: linear-gradient(90deg, #2563eb, #06b6d4);
        }
        .card {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            margin-top: 20px;
        }
        .stRadio > div {
            justify-content: center;
        }
        footer, .stCaption {
            text-align: center;
            color: #9CA3AF;
        }
    </style>
"""

def get_realtime_info(query):
    """Core logic to fetch and summarize real-time web info."""
    try:
        search_result = tavily_client.search(query=query, search_depth="advanced")
        source_info = "\n".join([f"- {r['title']}: {r['content']}" for r in search_result['results'][:5]])
        
        prompt = f"Summarize the following real-time information for the topic '{query}':\n\n{source_info}"
        response = client.chat.completions.create(
            model=model_info,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip() if response else source_info
    except Exception:
        return ""

def create_did_video(script):
    """Create an AI talking-head video from a script using D-ID."""
    api_key = os.getenv("DID_API_KEY")
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "source_url": "https://d-id-public-bucket.s3.us-east-1.amazonaws.com/alice.jpg",
        "script": {
            "type": "text",
            "input": script,
            "provider": {
                "type": "microsoft",
                "voice_id": "en-US-JennyNeural"
            }
        },
        "config": {"fluent": True}
    }
    try:
        response = requests.post("https://api.d-id.com/talks", json=payload, headers=headers)
        if response.status_code not in (200, 201):
            return None, f"D-ID error: {response.text}"
        talk_id = response.json().get("id")
        for _ in range(30):
            time.sleep(3)
            poll = requests.get(f"https://api.d-id.com/talks/{talk_id}", headers=headers)
            data = poll.json()
            if data.get("status") == "done":
                return data.get("result_url"), None
            elif data.get("status") == "error":
                return None, "D-ID video generation failed"
        return None, "Timed out waiting for video"
    except Exception as e:
        return None, str(e)


def generate_video_script(topic, refined_info):
    """Core logic to generate a script from refined info."""
    prompt = f"Write an engaging video script for '{topic}' based on this info:\n{refined_info}\nKeep it 100-120 words."
    try:
        response = client.chat.completions.create(
            model=model_script,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip() if response else ""
    except Exception:
        return ""
