"""
llm_factory.py
--------------

Provider-agnostic LLM factory.
Automatically selects an available LLM based on environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def get_llm():
    """
    Return an LLM instance based on available API keys.

    Priority:
    1. OpenAI
    2. Google Gemini
    3. Anthropic
    """
    # --- OpenAI ---
    if os.getenv("OPENAI_API_KEY"):
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as e:
            raise ImportError(
                "OPENAI_API_KEY found but langchain-openai not installed.\n"
                "Install with: pip install langchain-openai"
            ) from e

        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.9,
        )

    # --- Google Gemini ---
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as e:
            raise ImportError(
                "Gemini API key found but langchain-google-genai not installed.\n"
                "Install with: pip install langchain-google-genai"
            ) from e

        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0.9,
        )

    # --- Anthropic ---
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as e:
            raise ImportError(
                "ANTHROPIC_API_KEY found but langchain-anthropic not installed.\n"
                "Install with: pip install langchain-anthropic"
            ) from e

        return ChatAnthropic(
            model="claude-3-haiku-20240307",
            temperature=0.9,
        )

    # --- Nothing found ---
    raise RuntimeError(
        "No supported LLM API key found.\n\n"
        "Set one of:\n"
        "- OPENAI_API_KEY\n"
        "- GOOGLE_API_KEY or GEMINI_API_KEY\n"
        "- ANTHROPIC_API_KEY\n\n"
        "Or use file input mode instead."
    )
