# 🤖 LLM-AI Self Auto-Healing Framework  
### (Locator + Script Auto-Healing for Selenium/PlayWright/Cypress/Webdriver.io and BDD/TestNG)

This repository provides a **safe, enterprise-grade LLM-assisted auto-healing framework** for Selenium automation.  
It supports **two independent healing layers**:

1. **Locator Auto-Healing** – heals broken selectors  
2. **Script / Assertion Auto-Healing** – heals failed assertions 

> ⚠️ LLM is **advisory**  
> ❌ Test scripts are **never auto-modified**  
> ✅ Java framework always makes the **final pass/fail decision**

---

## 🧩 High-Level Architecture

```text
      Test
        |
        |-- Locator fails
        |        |
        |        --> LLM Locator Healer (Python API)
        |        --> New locator returned
        |        --> Retry action
        |
        |-- Assertion fails
                 |
                 --> LLM Script Healer (Python API)
                 --> Heal decision (JSON)
                 --> Client decides PASS / PASS_WITH_HEAL / FAIL
```

---

## 🧠 Design Principles

- LLM does **NOT** execute Selenium/PlayWright/Cypress/Webdriver.io
- LLM does **NOT** hide real bugs
- LLM reasons **only on provided context**

---

## ✨ Features

### ✅ Locator Auto-Healing
- Heals broken locators
- Uses reduced DOM + intent-based reasoning
- Ensures:
  - Unique locator
  - Interactable elements only
- Generic across all pages

### ✅ Script / Assertion Auto-Healing
- Handles failed TestNG Java assertions safely
- Works for **ALL assertion types**
- Semantic reasoning (not hardcoded rules)
- Context-driven (feature flags, flaky env, non-critical UI)

---

## 📁 Project Structure

```text
LLM-AI-Self-Auto-healing
│
├── locator_healer_api.py        # LLM-based locator healing service
├── script_healer_api.py         # LLM-based script/assertion healing service
│
├── java/
│   ├── LLMClient.java           # Java → Python API client
│   ├── HealableAssert.java      # Central assertion wrapper
│   └── LocatorHealerDriver.java
│
└── README.md
```

---

## 📐 Architecture 

<img width="1024" height="1024" alt="Architecture" src="https://github.com/user-attachments/assets/23949b56-b2ae-429d-9b20-4e017d172559" />


---

## 🔹 Locator Auto-Healing

### When triggered
- `NoSuchElementException`
- `TimeoutException`
- `StaleElementReferenceException`
- 'ETC'

### Flow
1. Capture DOM
2. Reduce DOM
3. Send intent + DOM to LLM
4. Receive healed locator
5. Retry action

### Sample LLM Response
```json
{
  "locators": [
    {
      "type": "xpath",
      "value": "//button[normalize-space()='Login']"
    }
  ]
}
```

---

## 🔹 Script / Assertion Auto-Healing

### Supported Assertion Types (Generic)

```text
TEXT_EQUALS
CONTAINS
BOOLEAN_TRUE
BOOLEAN_FALSE
NOT_NULL
NUMERIC_EQUALS
GREATER_THAN
LESS_THAN
```

Healing is triggered **only when an assertion fails**.

---

### Example: TEXT Assertion

#### Java
```java
Assert.assertEquals(
    homePage.getHeadingText(),
    "Login to AI"
);
```

#### Actual
```
Login to AI Agents
```

#### Payload Sent to LLM
```json
{
  "test_intent": "Verify login page heading",
  "assertion_type": "TEXT_EQUALS",
  "expected": "Login to AI",
  "actual": "Login to AI Agents"
}
```

#### LLM Response
```json
{
  "change_type": "SEMANTIC",
  "severity": "LOW",
  "healable": true,
  "healing_strategy": "SEMANTIC_CONTAINS",
  "safe_assertion_hint": "Login to AI Agents",
  "confidence": 0.8
}
```

#### Result
```
PASS_WITH_HEALING
```

---

### Example: BOOLEAN Assertion (`assertTrue`)

```java
Assert.assertTrue(isUserLoggedIn);
```

#### Payload
```json
{
  "test_intent": "Verify user is logged in",
  "assertion_type": "BOOLEAN_TRUE",
  "expected": "true",
  "actual": "false"
}
```

#### Result
```
FAIL (Not healable – correct behavior)
```

---

## 🧠 Context-Driven Healing (Critical)

LLM **never guesses**.  
Healing is allowed **only if context explains the failure**.

### Feature Flag Example
```json
{
  "test_intent": "Verify new login button visibility",
  "assertion_type": "BOOLEAN_TRUE",
  "expected": "true",
  "actual": "false",
  "context": {
    "feature_flag": "LOGIN_V2",
    "flag_state": "OFF",
    "environment": "staging",
    "criticality": "NON_CRITICAL"
  }
}
```

---

## 🚀 Running the Services

### Locator Healer API
```bash
python3 -m uvicorn locator_healer_api:app --port 9000
```

### Script Healer API
```bash
python3 -m uvicorn script_healer_api:app --port 9001
```

---

---

## 🔌 API Contract for Locator Healer API

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

## 🔌 API Contract for Script Healer API


```bash
curl http://localhost:9001/health
```

### Script Healing
```bash
curl -X POST http://localhost:9001/heal/script \
  -H "Content-Type: application/json" \
  -d '{
    "test_intent": "Verify login page heading",
    "assertion_type": "TEXT_EQUALS",
    "expected": "Login to AI",
    "actual": "Login to AI Agents"
   
  }'
```

---

## 🛡️ Safety Rules (Non-Negotiable)

- ❌ Never heal authentication flows
- ❌ Never heal payments / security
- ❌ Never auto-modify test scripts
- ❌ Never assume business correctness
- ✅ Always log healed cases
- ✅ Java decides final outcome

---

## 📊 Recommended Test Results

```text
PASS
PASS_WITH_HEALING
FAIL
```

Example log:
```text
⚠ PASS_WITH_HEALING
Reason: Semantic UI text change
Confidence: 0.8
```

---

## 🏁 Conclusion

This framework delivers:
- Safe auto-healing
- Zero hidden bugs
- Full auditability
- Enterprise-ready design

**LLM augments QA judgment — it does not replace it.**

