import os
import asyncio
from google import genai
from dotenv import load_dotenv

async def test_model(model_name):
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    try:
        print(f"Testing model: {model_name}...")
        response = client.models.generate_content(
            model=model_name,
            contents="hi"
        )
        print(f"SUCCESS: {model_name} responded: {response.text}")
        return True
    except Exception as e:
        print(f"FAILED: {model_name} error: {e}")
        return False

async def main():
    models_to_test = [
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash-001"
    ]
    for model in models_to_test:
        if await test_model(model):
            print(f"\nRecommended model: {model}")
            break

if __name__ == "__main__":
    asyncio.run(main())
