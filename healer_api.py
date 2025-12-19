from flask import Flask, request, jsonify
from lxml import html
import openai
import os
import traceback
import warnings
from dotenv import load_dotenv

# -------------------- ENV SETUP --------------------
load_dotenv(override=True)
warnings.filterwarnings("ignore")

# -------------------- FLASK APP --------------------
app = Flask(__name__)

# -------------------- OPENAI CONFIG --------------------
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise RuntimeError("OPENAI_API_KEY not loaded")

# -------------------- PROMPT BUILDER --------------------
def build_prompt(intent: str, dom: str) -> str:
    return f"""
You are an expert Selenium self-healing locator engine.

GOAL:
Please find proper locator and needs to be healed for the failed element, and the healed locator
MUST work when executed in Selenium automation.

STRICT RULES (MANDATORY):
1. Return ONLY valid JSON. No explanation text.
2. The healed locator MUST uniquely identify EXACTLY ONE element in the DOM.
3. The healed locator MUST be executable directly in Selenium without modification.
4. If a safe, unique, and executable locator cannot be guaranteed,
   return an empty "locators" list.
5. Prefer attributes in this order:
   id > name > aria-label > placeholder > role > stable class
6. Do NOT invent attributes or values not present in the DOM.

Target intent:
"{intent}"

DOM CONTEXT (reduced, interactive-only):
{dom}

Return format:
{{
  "locators": [
    {{ "type": "xpath", "value": "..." }},
    {{ "type": "css", "value": "..." }}
  ]
}}
"""

# -------------------- DOM REDUCTION --------------------
def extract_relevant_dom(dom: str, intent: str, max_chars=6000) -> str:
    tree = html.fromstring(dom)
    intent_words = intent.lower().split()

    snippets = []

    for el in tree.xpath(INTERACTIVE_XPATH):
        # skip hidden
        style = el.attrib.get("style", "").lower()
        if "display:none" in style or "visibility:hidden" in style:
            continue

        # skip disabled
        if el.attrib.get("disabled"):
            continue

        attrs = " ".join(el.attrib.values()).lower()
        text = (el.text_content() or "").lower()

        combined = f"{attrs} {text}"

        if any(w in combined for w in intent_words):
            snippets.append(
                html.tostring(el, encoding="unicode", with_tail=False)
            )

        if sum(len(s) for s in snippets) >= max_chars:
            break

    # -------------------
    # SAFE FALLBACK
    # -------------------
    if not snippets:
        for el in tree.xpath(INTERACTIVE_XPATH)[:10]:
            snippets.append(
                html.tostring(el, encoding="unicode", with_tail=False)
            )

    return "\n".join(snippets)[:max_chars]
# -------------------- INTERACTIVE ELEMENT DETECTION --------------------
INTERACTIVE_XPATH = (
    "//*"
    "["
    "self::input or self::textarea or self::select or self::button or self::a"
    " or @role='button' or @role='textbox'"
    " or @tabindex"
    " or contains(@class,'btn')"
    "]"
)


# -------------------- FILTERS --------------------
def is_interactive(xpath: str, dom: str) -> bool:
    try:
        tree = html.fromstring(dom)
        nodes = tree.xpath(xpath)
        return len(nodes) == 1 and nodes[0].tag.lower() in ["a", "button", "input"]
    except:
        return False

# -------------------- LLM CALL --------------------
def call_llm(prompt: str) -> dict:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0,
        messages=[
            {"role": "system", "content": "You generate Selenium locators."},
            {"role": "user", "content": prompt}
        ]
    )
    return eval(response.choices[0].message.content)

# -------------------- CORE HEALER --------------------
def heal_locator(dom: str, intent: str):
    reduced_dom = extract_relevant_dom(dom, intent)
    prompt = build_prompt(intent, reduced_dom)
    llm_response = call_llm(prompt)

    valid = []
    for loc in llm_response.get("locators", []):
        value = loc.get("value")
        if value and is_interactive(value, dom):
            valid.append(loc)

    return valid

# -------------------- API --------------------
@app.route("/heal-locator", methods=["POST"])
def heal_locator_api():
    try:
        payload = request.get_json(force=True)

        intent = payload.get("description") or payload.get("intent")
        dom = payload.get("dom")

        if not intent or not dom:
            return jsonify({"locators": []}), 200

        locators = heal_locator(dom, intent)

        # 🔥 FINAL FIX: never return 500 for healing failure
        return jsonify({"locators": locators}), 200

    except Exception as e:
        traceback.print_exc()
        # Even unexpected errors should not crash Java
        return jsonify({"locators": []}), 200


# -------------------- START SERVER --------------------
if __name__ == "__main__":
    print("🚀 Healer API running on port 9000")
    app.run(host="0.0.0.0", port=9000, debug=True)
