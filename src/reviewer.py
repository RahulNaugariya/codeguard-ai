import asyncio
import logging
import os
import random
import time

from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from google.genai import types
from google.genai.errors import APIError

from src.schemas import Issue

load_dotenv()

logger = logging.getLogger("codeguard.reviewer")

# The client automatically reads the GEMINI_API_KEY environment variable.
client = genai.Client(
    http_options=types.HttpOptions(timeout=180_000)
)  # 3 minutes, in milliseconds

# Comma-separated list in .env, e.g. GEMINI_MODELS=model-a,model-b
# Attempts alternate between them, so a 503 on one falls back to the other.
MODELS = [m.strip() for m in os.getenv("GEMINI_MODELS", "gemini-3.8-flash").split(",")]

# Transient errors worth retrying: rate limit, server error, overloaded, timeout.
RETRYABLE_CODES = {429, 500, 503, 504}
MAX_ATTEMPTS = 5


async def _generate(prompt: str, model: str):
    return await client.aio.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=list[Issue],
        ),
    )


async def perform_ai_review(code: str, language: str) -> list[Issue]:
    """
    Sends code to Gemini for static analysis (the code is never executed)
    and returns a structured list of Issues.
    """
    if not code.strip():
        return []

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

    response = None
    model = MODELS[0]
    for attempt in range(1, MAX_ATTEMPTS + 1):
        model = MODELS[(attempt - 1) % len(MODELS)]
        start = time.perf_counter()
        try:
            response = await _generate(prompt, model)
            logger.warning(
                "Attempt %d ok in %.1fs (model=%s)",
                attempt,
                time.perf_counter() - start,
                model,
            )
            break
        except APIError as e:
            logger.warning(
                "Attempt %d/%d failed after %.1fs (model=%s, code=%s): %s",
                attempt,
                MAX_ATTEMPTS,
                time.perf_counter() - start,
                model,
                e.code,
                e,
            )
            retryable = e.code in RETRYABLE_CODES

            # Model not available for this key: skip straight to the next model
            if e.code == 404 and len(MODELS) > 1 and attempt < MAX_ATTEMPTS:
                logger.warning("Model %s unavailable, trying next model", model)
                continue

            if retryable and attempt < MAX_ATTEMPTS:
                # Exponential backoff with jitter: ~2s, 4s, 8s, 16s
                await asyncio.sleep(2**attempt + random.random())
                continue
            if retryable:
                raise HTTPException(
                    status_code=503,
                    detail="Gemini is busy right now. Please try again in a moment.",
                )
            raise HTTPException(
                status_code=502,
                detail="Downstream LLM API error.",
            )
        except Exception:
            # Network errors, timeouts, SDK bugs: log the full traceback.
            logger.exception("Unexpected error while calling Gemini")
            raise HTTPException(
                status_code=500,
                detail="Unexpected error while calling the LLM.",
            )

    logger.warning("Gemini usage (model=%s): %s", model, response.usage_metadata)

    # Parsing step: kept separate so failures here are clearly identified.
    try:
        parsed = response.parsed
    except Exception:
        logger.exception("Failed to parse Gemini response into Issue schema")
        parsed = None

    if parsed is None:
        finish_reason = (
            response.candidates[0].finish_reason if response.candidates else None
        )
        logger.error(
            "Gemini returned unparseable output (finish_reason=%s): %s",
            finish_reason,
            response.text,
        )
        # Do NOT return [] here: a parse failure must not look like "code is clean".
        raise HTTPException(
            status_code=502,
            detail="The LLM returned a malformed response.",
        )

    return parsed
