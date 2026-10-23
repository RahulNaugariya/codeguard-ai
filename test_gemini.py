import os
import asyncio
from dotenv import load_dotenv
from google import genai

# Load variables from the .env file
load_dotenv()

# Read the API key without displaying it
api_key = os.getenv("GEMINI_API_KEY")


async def test_connection():
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env")
        return

    client = genai.Client(api_key=api_key)

    try:
        response = await client.aio.models.generate_content(
            model="gemini-3.8-flash",
            contents="Reply with exactly: CodeGuard AI connection successful",
        )
        print("Gemini response:", response.text)
    except Exception as error:
        print("Connection failed:", type(error).__name__, str(error))
    finally:
        await client.aio.aclose()


asyncio.run(test_connection())
