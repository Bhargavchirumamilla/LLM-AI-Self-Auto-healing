import openai
import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from typing import Optional, Dict, Any

# =========================================================
# OPENAI CONFIG
# =========================================================

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise RuntimeError("OPENAI_API_KEY not loaded")

app = FastAPI(title="LLM Script Healer API")


# =========================================================
# REQUEST MODEL
# =========================================================
class ScriptHealRequest(BaseModel):
    test_intent: str
    assertion_type: str
    expected: Optional[str]
    actual: Optional[str]
    context: Optional[Dict[str, Any]] = None


# =========================================================
# PROMPT BUILDER
# =========================================================

def build_prompt(req: ScriptHealRequest) -> str:
    return f"""
You are a senior QA automation architect.

Task:
Analyze a FAILED test assertion and decide whether a SAFE TEMPORARY HEAL is possible.

Test Intent:
{req.test_intent}

Assertion Type:
{req.assertion_type}

Expected Value:
{req.expected}

Actual Value:
{req.actual}

Additional Runtime Context (may be empty):
{req.context}

STRICT RULES:
- Do NOT decide if business change is correct
- Do NOT invent assumptions not present in context
- Only heal if TEST INTENT is preserved
- NEVER heal if meaning flips (success ↔ failure)

- NEVER heal auth, payment, security, or data-integrity assertions
- Context is authoritative; if missing, assume UNKNOWN
- Return JSON ONLY (no markdown, no explanation)

HEALING GUIDANCE:
- Feature flags → heal ONLY if context explicitly explains failure
- Flaky environments → heal ONLY if context marks known flakiness
- Non-critical UI → heal ONLY if context marks NON_CRITICAL
- Boolean assertions → healing is RARE and requires strong context

Allowed Healing Strategies:
- RELAXED_EQUALS
- SEMANTIC_CONTAINS
- REGEX_MATCH
- NUMERIC_TOLERANCE
- NO_HEAL

Return JSON in EXACT format:
{{
  "change_type": "SEMANTIC | COSMETIC | ENVIRONMENT | BREAKING",
  "severity": "LOW | MEDIUM | HIGH",
  "healable": true | false,
  "healing_strategy": "RELAXED_EQUALS | SEMANTIC_CONTAINS | REGEX_MATCH | NUMERIC_TOLERANCE | NO_HEAL",
  "safe_assertion_hint": "string or null",
  "confidence": number
}}
""".strip()



# =========================================================
# LLM CALL
# =========================================================

def call_llm(prompt: str) -> dict:
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a strict QA test healer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()

    if not raw:
        raise RuntimeError("LLM returned empty response")

    # ✅ FIX: remove markdown code fences if present
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"LLM did not return valid JSON. Raw response:\n{raw}"
        )


# =========================================================
# SCRIPT HEAL ENDPOINT
# =========================================================

@app.post("/heal/script")
def heal_script(req: ScriptHealRequest):
    try:
        prompt = build_prompt(req)
        return call_llm(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
