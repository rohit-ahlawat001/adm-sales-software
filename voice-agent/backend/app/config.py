import os
from dotenv import load_dotenv

load_dotenv()

#LLM Provider Configuration
LLM_ProVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

#LLM Validation Error Handling
def validate_llm():
    if LLM_ProVIDER not in ["gemini", "openai"]:
        raise ValueError("Invalid LLM_PROVIDER. Must be 'gemini' or 'openai'.")
    if LLM_ProVIDER == "gemini" and not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is required for Gemini provider.")