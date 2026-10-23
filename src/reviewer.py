import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
from fastapi import HTTPException
from src.schemas import Issue

load_dotenv()

# Initialize the GenAI client.
# It automatically looks for the GEMINI_API_KEY environment variable.
client = genai.Client()


async def perform_ai_review(code: str, language: str) -> list[Issue]:
    """
    Sends code to Gemini for static analysis and returns a structured list of Issues.
    """
    if not code.strip():
        return []

    # TEMPORARY MOCK: Bypass the API outage to verify the FastAPI pipeline
    # return [
    #     Issue(
    #         issue_type="Mock SQL Injection",
    #         severity="High",
    #         description="The API is down, but this mock proves the API routing and Pydantic schemas work.",
    #         suggestion="Use parameterized queries instead of string concatenation.",
    #     )
    # ]

    # TEMPORARY: Return a fake issue that does NOT say "Mock"
    # so the database thinks it's a real API response and saves it.
    # return [
    #     Issue(
    #         issue_type="Hardcoded SQL Injection",
    #         severity="High",
    #         description="Testing database persistence.",
    #         suggestion="Use parameterized queries.",
    #     )
    # ]

    # System instruction ensuring the LLM acts as an analyzer, not an executor
    prompt = f"""
    You are an expert senior software engineer and security auditor. 
    Review the following {language} code.
    Identify concrete bugs, security vulnerabilities, performance bottlenecks, and anti-patterns.
    Do not execute the code. Perform static analysis only.
    If the code is perfectly clean and secure, return an empty list.
    
    Code to review:
    ```{language}
    {code}
    ```
    """

    try:
        # Make the asynchronous call to Gemini
        response = await client.aio.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[Issue],
                # temperature=0.2,  # Low temperature for more analytical, deterministic responses
            ),
        )

        # response.parsed contains the data mapped directly to your Pydantic schema
        if response.parsed is not None:
            return response.parsed

        return []

    except APIError as e:
        # Gracefully handle Gemini-specific errors (rate limits, bad auth, timeouts)
        raise HTTPException(
            status_code=502, detail=f"Downstream LLM API Error: {str(e)}"
        )
    except Exception as e:
        # Catch unexpected validation or parsing failures
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while parsing the review.",
        )
