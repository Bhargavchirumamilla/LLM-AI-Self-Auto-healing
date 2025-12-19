# 🧠 Python LLM Locator Healer Service
(Flask + DOM Reduction + LLM)

This service provides runtime Selenium locator healing by analyzing the live DOM and a human-readable intent, then safely generating unique, executable locators.

The service is framework-agnostic and production-safe.

---

## 🎯 Responsibilities

- Reduce large DOM into relevant interactive elements
- Generate locator candidates using LLM intelligence
- Validate locators against the original DOM
- Never crash the calling system
- Return only safe locators or an empty response

---

## 📐 Architecture 
┌──────────────┐   ┌────────────────────┐   ┌──────────────────────┐
│ API Request  │──▶│ DOM Reduction      │──▶│ Prompt Builder       │
│ (Intent+DOM) │   │ Interactive Filter │   │ Strict Rules         │
└──────────────┘   └────────────────────┘   └─────────┬────────────┘
                                                        │
                                                        ▼
┌────────────────────┐   ┌────────────────────────────┐
│ LLM Invocation     │──▶│ Locator Candidate Generator │
│ (GPT / Local LLM)  │   │ XPath / CSS                 │
└────────────────────┘   └─────────┬──────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────┐
│ Locator Validation Layer         │
│ - Uniqueness (exactly 1 match)  │
│ - Interactive element only      │
└───────────────┬─────────────────┘
                │
        ✅ Valid │ ❌ Invalid
                │
                ▼
┌──────────────────────────┐
│ JSON API Response        │
│ { "locators": [...] }   │
└──────────────────────────┘

---

## 🔁 Execution Flow (Sequence)

Client  
↓  
/heal-locator API  
↓  
DOM Reduction  
↓  
Prompt Creation  
↓  
LLM Call  
↓  
Validate Locators  
↓  
Return JSON Response  

---

## 🔌 API Contract

### Endpoint
POST /heal-locator

### Request Payload
{
  "intent": "login button",
  "dom": "<html>...</html>"
}

### Success Response
{
  "locators": [
    { "type": "xpath", "value": "//button[@id='login']" },
    { "type": "css", "value": "button#login" }
  ]
}

### Safe Failure Response
{
  "locators": []
}

HTTP 200 is always returned.

---

## 🔍 DOM Reduction Strategy

Only interactive elements are considered:
- input, textarea, select
- button, a
- role=button, role=textbox
- tabindex
- class containing 'btn'

Hidden or disabled elements are ignored.

---

## 🧠 Prompt Rules

- Return ONLY valid JSON
- Locator must uniquely identify exactly one element
- Locator must be Selenium executable
- Attribute priority:
  id > name > aria-label > placeholder > role > stable class
- Never invent attributes

---

## 🛡️ Safety Guarantees

- No HTTP 500 errors
- No unsafe locators
- No crashes
- Deterministic validation
- LLM output is strictly validated

---

## ⚠️ Limitations

- Elements without semantic meaning cannot be healed
- Multiple matching elements may result in empty response
- This is expected and correct behavior

---

## 🚀 Setup & Run

### Install Dependencies
pip install -r requirements.txt

### Environment Variable
OPENAI_API_KEY=your_key_here

### Start Service
python healer_api.py

Service runs on:
http://localhost:9000

---

## ✅ Status

Production-ready Python LLM locator healing service
