from functools import lru_cache
from google import genai
from app.config import(
    GENAI_API_KEY, GEMINI_MODEL, LLM_PROVIDER
)

@lru_cache(maxsize=1)
def gemini_client():
    if LLM_PROVIDER == "gemini":
        return genai.Client(api_key=GENAI_API_KEY)
    else:
        raise ValueError("Invalid LLM_PROVIDER. Must be 'gemini'.")

def generate_prompt_response(prompt: str, model: str = GEMINI_MODEL):
    client = gemini_client()
    response = client.generate_text(
        model=model,
        prompt=prompt
    )
    return response.text
