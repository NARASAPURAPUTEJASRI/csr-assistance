import json
import re
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)

_SIMPLE_RULES = [
    (["hello", "hi", "hey", "good morning", "good afternoon"], "GREETING"),
    (["bye", "goodbye", "see you", "take care"], "GOODBYE"),
    (["thanks", "thank you", "thx"], "THANK_YOU"),
    (["talk to agent", "human agent", "speak to agent", "escalate"], "ESCALATE_TO_AGENT"),
]

def _rule_based_check(query: str):
    q = query.lower().strip()
    for keywords, intent in _SIMPLE_RULES:
        if any(kw in q for kw in keywords):
            return intent
    return None

_GEMINI_PROMPT = """
You are an expert intent classifier for e-commerce customer service.

Return ONLY a valid JSON object. No other text.

Keys:
- intent: one of ORDER_STATUS, ORDER_DETAILS, ORDER_CANCEL, ORDER_DELAY, ORDER_CREATE, CUSTOMER_INFO, CUSTOMER_ORDERS, CUSTOMER_VERIFY, TICKET_CREATE, TICKET_CHECK, TICKET_CLOSE, TICKET_LIST, COMPLAINT_CREATE, COMPLAINT_CHECK, COMPLAINT_CLOSE, HIGH_PRIORITY_COMPLAINTS, FAQ, OUT_OF_SCOPE, UNKNOWN
- order_id: integer or null
- customer_id: integer or null
- customer_name: string or null
- confidence: float 0.0 to 1.0

Examples:
User: status of order 101
{"intent": "ORDER_STATUS", "order_id": 101, "customer_id": null, "customer_name": null, "confidence": 0.95}

User: customer id 1 details
{"intent": "CUSTOMER_INFO", "order_id": null, "customer_id": 1, "customer_name": null, "confidence": 0.93}

User: Show orders for Tejasri
{"intent": "CUSTOMER_ORDERS", "order_id": null, "customer_id": null, "customer_name": "Tejasri", "confidence": 0.92}

User: Create a ticket for order 104
{"intent": "TICKET_CREATE", "order_id": 104, "customer_id": null, "customer_name": null, "confidence": 0.90}

User: Create order for customer id 1 product iPhone 16 quantity 1
{"intent": "ORDER_CREATE", "order_id": null, "customer_id": 1, "customer_name": null, "confidence": 0.92}

User: complaint details for order 113
{"intent": "COMPLAINT_CHECK", "order_id": 113, "customer_id": null, "customer_name": null, "confidence": 0.94}

User: what is ai
{"intent": "OUT_OF_SCOPE", "order_id": null, "customer_id": null, "customer_name": null, "confidence": 0.85}

User: show high priority complaints
{"intent": "HIGH_PRIORITY_COMPLAINTS", "order_id": null, "customer_id": null, "customer_name": null, "confidence": 0.90}

Now classify this query:
User: {query}
"""

def _safe_int(value):
    try:
        return int(value) if value is not None else None
    except:
        return None

def _extract_json(text: str):
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except:
        pass
    return None

def detect_intent(query: str) -> dict:
    simple = _rule_based_check(query)
    if simple:
        return {"intent": simple, "order_id": None, "customer_id": None, "customer_name": None, "confidence": 1.0}

    try:
        prompt = _GEMINI_PROMPT.replace("{query}", query)
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        raw_text = response.text.strip()
        parsed = _extract_json(raw_text)

        if parsed and isinstance(parsed, dict) and "intent" in parsed:
            return {
                "intent": parsed.get("intent", "UNKNOWN"),
                "order_id": _safe_int(parsed.get("order_id")),
                "customer_id": _safe_int(parsed.get("customer_id")),
                "customer_name": parsed.get("customer_name"),
                "confidence": float(parsed.get("confidence", 0.75)),
            }
    except Exception as e:
        print(f"[Gemini Error] {type(e).__name__}: {e}")

    return {"intent": "UNKNOWN", "order_id": None, "customer_id": None, "customer_name": None, "confidence": 0.0}

def get_llm_answer(query: str) -> str:
    try:
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"You are a helpful customer service assistant.\n\nUser: {query}"
        )
        return response.text.strip()
    except Exception as e:
        print(f"[get_llm_answer Error] {type(e).__name__}: {e}")
        return "Sorry, I'm having trouble connecting right now. Please try again."

def filter_customer_response(query: str, customer_data: dict) -> str:
    try:
        prompt = f"""
        User query: "{query}"
        Full customer data: {json.dumps(customer_data)}
        Based on the query, return ONLY the relevant fields in a clean, readable format. If asking for specific info (e.g., phone), return only that. If 'details', return all. No extra text.
        """
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Filter Error] {type(e).__name__}: {e}")
        return "Sorry, I'm having trouble processing the request."

def classify_priority(issue: str) -> str:
    try:
        prompt = f"""
        Classify the priority of this customer issue: "{issue}"
        Rules:
        - HIGH: Damaged product, wrong item, urgent issues.
        - MEDIUM: Late delivery, minor delays.
        - LOW: General inquiries, thanks.
        Return only: HIGH, MEDIUM, or LOW.
        """
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        priority = response.text.strip().upper()
        return priority if priority in ["HIGH", "MEDIUM", "LOW"] else "LOW"
    except Exception as e:
        print(f"[Priority Error] {type(e).__name__}: {e}")
        return "LOW"