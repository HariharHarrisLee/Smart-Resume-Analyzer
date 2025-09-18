# ai_feedback.py
import os
import openai
import json
import re
from dotenv import load_dotenv

load_dotenv()  # loads .env if present

# -----------------------------
# CONFIGURATION
# -----------------------------
USE_MOCK_AI = True  # Set True for demo/mock mode, False to use real OpenAI
MAX_RESUME_CHARS = 8000
MAX_JOB_CHARS = 3000

# -----------------------------
# SYSTEM PROMPT
# -----------------------------
SYSTEM_PROMPT = (
    "You are an expert resume coach and hiring manager. "
    "Given a candidate resume and a job description, produce a concise, actionable report "
    "that includes: a short overall assessment (1-2 sentences), top 5 improvements ordered by impact, "
    "3 short rewritten bullets for the candidate that incorporate missing keywords, and a short ATS advice section. "
    "Return the response as JSON with keys: 'summary', 'top_improvements', 'rewrites', 'ats_advice'."
)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def _openai_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise EnvironmentError(
            "OPENAI_API_KEY not set. Set it in environment or create a .env file."
        )
    openai.api_key = key
    return openai

def _attempt_parse_json(raw_text: str):
    try:
        return json.loads(raw_text)
    except Exception:
        m = re.search(r"(\{.*\})", raw_text, re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
    return None

# -----------------------------
# GENERATE RESUME FEEDBACK
# -----------------------------
def generate_resume_feedback(resume_text: str, job_text: str, match_data: dict = None, model_choice: str = None) -> dict:
    if USE_MOCK_AI:
        # Return mock/demo suggestions for portfolio
        return {
            "summary": "Resume is solid but could better emphasize game design impact and achievements.",
            "top_improvements": [
                "Include measurable results from game design projects.",
                "Highlight teamwork and cross-functional collaboration.",
                "Add keywords from the job description like 'game mechanics', 'monetization', 'player types'.",
                "Showcase experience with tools like Unreal or Unity.",
                "Make bullets more concise and achievement-focused."
            ],
            "rewrites": [
                "Designed immersive game levels that increased player engagement by 20%.",
                "Led cross-functional team to implement game mechanics and narrative integration.",
                "Developed and optimized gameplay systems to enhance player experience."
            ],
            "ats_advice": "Ensure all relevant keywords from the job description appear naturally in the resume to pass ATS checks."
        }

    client = _openai_client()
    system = {"role": "system", "content": SYSTEM_PROMPT}
    user = {
        "role": "user",
        "content": f"Job description:\n\n{job_text[:MAX_JOB_CHARS]}\n\nResume:\n\n{resume_text[:MAX_RESUME_CHARS]}"
    }
    messages = [system, user]
    if match_data:
        messages.append({"role": "user", "content": f"Match data: {json.dumps(match_data)}"})

    preferred = []
    if model_choice:
        preferred.append(model_choice)
    env_model = os.getenv("OPENAI_MODEL")
    if env_model:
        preferred.append(env_model)
    preferred.extend(["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"])

    last_exc = None
    raw = None
    for mdl in preferred:
        try:
            resp = client.chat.completions.create(
                model=mdl,
                messages=messages,
                max_tokens=700,
                temperature=0.15
            )
            raw = resp.choices[0].message.content.strip()
            break
        except Exception as e:
            last_exc = e
            continue

    if raw is None:
        raise RuntimeError(f"OpenAI calls failed. Last error: {last_exc}")

    parsed = _attempt_parse_json(raw)
    return parsed if parsed else {"raw": raw}

# -----------------------------
# REWRITE A SECTION
# -----------------------------
def rewrite_section(text_segment: str, missing_keywords: list, role_hint: str = "", model_choice: str = None) -> str:
    if USE_MOCK_AI:
        # Return mock rewritten section
        keywords = ", ".join(missing_keywords[:5]) if missing_keywords else ""
        return f"[MOCK REWRITE] {text_segment[:120]}... (keywords: {keywords})"

    client = _openai_client()
    keywords = ", ".join(missing_keywords[:12]) if missing_keywords else ""
    prompt = (
        f"You are a resume writer. Rewrite the following text to be concise, achievement-focused, and "
        f"include these keywords naturally: {keywords}. Role hint: {role_hint}\n\nInput:\n{text_segment}"
    )

    preferred = []
    if model_choice:
        preferred.append(model_choice)
    env_model = os.getenv("OPENAI_MODEL")
    if env_model:
        preferred.append(env_model)
    preferred.extend(["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"])

    last_exc = None
    for mdl in preferred:
        try:
            resp = client.chat.completions.create(
                model=mdl,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250,
                temperature=0.2
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            last_exc = e
            continue

    raise RuntimeError(f"OpenAI rewrite failed. Last error: {last_exc}")
