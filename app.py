from datetime import date, timedelta
import re

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import CONFIDENCE_THRESHOLD
from ai_engine import detect_intent, get_llm_answer, filter_customer_response, classify_priority
from db import (
    init_db,
    get_order_by_id,
    get_orders_by_customer_id,
    get_orders_by_customer_name,
    cancel_order,
    get_customer_by_id,
    get_customer_by_name,
    create_ticket,
    create_complaint,
    create_order,
    check_duplicate_complaint,
    check_duplicate_ticket,
    get_high_priority_complaints,
    get_complaints_by_order_id,
    get_complaints_by_customer_id,
    get_complaints_by_customer_name,
)

app = FastAPI(title="AI Customer Assistant", version="3.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

init_db()

class Query(BaseModel):
    query: str

class Reply(BaseModel):
    response: str
    intent: str = ""
    confidence: float = 0.0

def reply(message: str, intent: str, confidence: float):
    return Reply(response=message, intent=intent, confidence=round(confidence, 2))

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/chat")
async def chat(body: Query):
    query = body.query.strip()
    if not query:
        return reply("Please type your question.", "EMPTY", 0.0)

    result = detect_intent(query)
    intent = result["intent"]
    order_id = result["order_id"]
    cust_id = result["customer_id"]
    cust_name = result["customer_name"]
    confidence = result["confidence"]

    if confidence < CONFIDENCE_THRESHOLD and intent not in ("GREETING", "GOODBYE", "THANK_YOU", "ESCALATE_TO_AGENT"):
        return reply(get_llm_answer(query), intent, confidence)

    if intent == "GREETING":
        return reply("Hello! How can I help you today?", intent, confidence)
    if intent == "GOODBYE":
        return reply("Goodbye! Have a great day.", intent, confidence)
    if intent == "THANK_YOU":
        return reply("You're welcome!", intent, confidence)
    if intent == "ESCALATE_TO_AGENT":
        return reply("Connecting you to a human agent...", intent, confidence)
    if intent == "OUT_OF_SCOPE":
        return reply("I’m a Customer Service Assistant and can only help with orders, customers, and complaints. Please ask a relevant query.", intent, confidence)

    if intent in ("ORDER_STATUS", "ORDER_DETAILS", "ORDER_DELAY"):
        order = _find_order(order_id, cust_name)
        if not order:
            return reply(_order_not_found_msg(order_id, cust_name), intent, confidence)

        if intent == "ORDER_STATUS":
            return reply(f"Order {order['id']} status is {order['status']}. Expected delivery: {order['delivery_date']}.", intent, confidence)
        if intent == "ORDER_DETAILS":
            return reply(
                f"Order Details\n"
                f"ID        : {order['id']}\n"
                f"Customer  : {order['customer_name']}\n"
                f"Product   : {order['product']}\n"
                f"Quantity  : {order['quantity']}\n"
                f"Amount    : Rs {order['amount']}\n"
                f"Status    : {order['status']}\n"
                f"Delivery  : {order['delivery_date']}",
                intent, confidence
            )
        if intent == "ORDER_DELAY":
            return reply(f"Order {order['id']} is currently {order['status']}. Expected on {order['delivery_date']}.", intent, confidence)

    if intent == "ORDER_CANCEL":
        if not order_id:
            return reply("Please provide order_id to cancel the order.", intent, confidence)
        success = cancel_order(order_id)
        msg = f"Order {order_id} has been cancelled successfully." if success else f"Order {order_id} not found."
        return reply(msg, intent, confidence)

    if intent == "CUSTOMER_INFO":
        customer = None
        if cust_id:
            customer = get_customer_by_id(cust_id)
        elif cust_name:
            results = get_customer_by_name(cust_name)
            customer = results[0] if results else None
        if customer:
            filtered = filter_customer_response(query, customer)
            return reply(filtered, intent, confidence)
        return reply("Customer not found.", intent, confidence)

    if intent == "CUSTOMER_ORDERS":
        orders = []
        if cust_id:
            orders = get_orders_by_customer_id(cust_id)
        elif cust_name:
            orders = get_orders_by_customer_name(cust_name)
        if orders:
            lines = [f"• Order {o['id']}: {o['product']} — {o['status']}" for o in orders]
            return reply(f"Orders for {cust_name or f'ID {cust_id}'}:\n" + "\n".join(lines), intent, confidence)
        return reply("No orders found for this customer.", intent, confidence)

    if intent == "TICKET_CREATE":
        issue = _extract_issue(query)
        if order_id:
            order = get_order_by_id(order_id)
            if order and not cust_id:
                cust_id = order["customer_id"]
        missing = []
        if not cust_id:
            missing.append("customer_id")
        if not order_id:
            missing.append("order_id")
        if not issue:
            missing.append("issue")
        if missing:
            return reply(_required_creation_prompt("ticket"), intent, confidence)

        if check_duplicate_ticket(order_id):
            return reply(f"A ticket already exists for order {order_id}. Do you want to create another one? (yes/no)", intent, confidence)
        ticket_id = create_ticket(order_id, cust_id, issue)
        return reply(f"Ticket #{ticket_id} created successfully for order {order_id}.", intent, confidence)

    if intent == "COMPLAINT_CREATE":
        issue = _extract_issue(query)
        if order_id:
            order = get_order_by_id(order_id)
            if order and not cust_id:
                cust_id = order["customer_id"]
        missing = []
        if not cust_id:
            missing.append("customer_id")
        if not order_id:
            missing.append("order_id")
        if not issue:
            missing.append("issue")
        if missing:
            return reply(_required_creation_prompt("complaint"), intent, confidence)

        if check_duplicate_complaint(order_id):
            return reply(f"A complaint already exists for order {order_id}. Do you want to create another one? (yes/no)", intent, confidence)
        priority = classify_priority(issue)
        comp_id = create_complaint(order_id, cust_id, issue, priority)
        return reply(f"Complaint #{comp_id} created for order {order_id} with priority {priority}.", intent, confidence)

    if intent == "ORDER_CREATE":
        product_name = _extract_product(query)
        quantity = _extract_quantity(query)
        user_customer_name = _extract_customer_name(query)
        if cust_id and not user_customer_name:
            customer = get_customer_by_id(cust_id)
            if customer:
                user_customer_name = customer["name"]
        if cust_name and not user_customer_name:
            user_customer_name = cust_name
        missing = []
        if not cust_id:
            missing.append("customer_id")
        if not user_customer_name:
            missing.append("customer_name")
        if not product_name:
            missing.append("product_name")
        if not quantity:
            missing.append("quantity")
        if missing:
            return reply(_required_order_prompt(), intent, confidence)

        amount = _get_product_price(product_name) * quantity
        delivery_date = (date.today() + timedelta(days=5)).isoformat()
        created_order_id = create_order(cust_id, user_customer_name, product_name, quantity, amount, "Processing", delivery_date)
        return reply(
            f"Order {created_order_id} created successfully.\n"
            f"Customer : {user_customer_name}\n"
            f"Product  : {product_name}\n"
            f"Quantity : {quantity}\n"
            f"Amount   : Rs {amount}\n"
            f"Status   : Processing\n"
            f"Delivery : {delivery_date}",
            intent, confidence
        )

    if intent == "COMPLAINT_CHECK":
        complaints = []
        if order_id:
            complaints = get_complaints_by_order_id(order_id)
        elif cust_id:
            complaints = get_complaints_by_customer_id(cust_id)
        elif cust_name:
            complaints = get_complaints_by_customer_name(cust_name)
        if not complaints:
            return reply("No complaints found for this query. Please provide an order_id, customer_id, or customer_name.", intent, confidence)

        lines = [
            f"Complaint #{c['id']} | Order {c['order_id']} | Customer {c['customer_name']} | Issue: {c['reason']} | Priority: {c['priority']} | Status: {c['status']}"
            for c in complaints
        ]
        return reply("Complaint Details\n" + "\n".join(lines), intent, confidence)

    if intent == "HIGH_PRIORITY_COMPLAINTS":
        complaints = get_high_priority_complaints()
        if complaints:
            rows = [
                f"{c['id']} | {c['order_id']} | {c['customer_name']} | {c['reason']} | {c['priority']}"
                for c in complaints
            ]
            return reply("High Priority Complaints\n\nComplaint ID | Order ID | Customer | Issue | Priority\n" + "-"*70 + "\n" + "\n".join(rows), intent, confidence)
        return reply("No high priority complaints found.", intent, confidence)

    return reply(get_llm_answer(query), intent, confidence)

def _find_order(order_id, cust_name):
    if order_id:
        return get_order_by_id(order_id)
    if cust_name:
        results = get_orders_by_customer_name(cust_name)
        return results[0] if results else None
    return None

def _order_not_found_msg(order_id, cust_name):
    if order_id:
        return f"No order found with ID {order_id}."
    if cust_name:
        return f"No orders found for '{cust_name}'."
    return "Please provide an order number."

def _required_creation_prompt(kind: str):
    return (
        f"To create a {kind}, please provide:\n"
        "customer_id: <value>\n"
        "order_id: <value>\n"
        "issue: <description>"
    )

def _required_order_prompt():
    return (
        "To create an order, please provide:\n"
        "customer_id: <value>\n"
        "customer_name: <value>\n"
        "product_name: <value>\n"
        "quantity: <value>"
    )

def _extract_quantity(query: str):
    match = re.search(r'quantity\s*[:=]?\s*(\d+)', query, re.I)
    if match:
        return int(match.group(1))
    match = re.search(r'(\d+)\s+(?:units|pcs|pieces|qty)\b', query, re.I)
    return int(match.group(1)) if match else None

def _extract_product(query: str):
    match = re.search(r'product(?: name)?\s*[:=]?\s*([A-Za-z0-9 ]+?)(?:\s+quantity\b|\s+customer\b|$)', query, re.I)
    return match.group(1).strip() if match else ""

def _extract_customer_name(query: str):
    match = re.search(r'customer(?: name)?\s*[:=]?\s*([A-Za-z ]+?)(?:\s+product|\s+quantity|\s+order\b|$)', query, re.I)
    return match.group(1).strip() if match else ""

def _extract_issue(query: str):
    cleaned = re.sub(r'^(please\s*)?(create|open)\s+(?:ticket|complaint)\s*', '', query, flags=re.I).strip()
    cleaned = re.sub(r'\bfor\s+order\s*\d+\b', '', cleaned, flags=re.I).strip()
    cleaned = re.sub(r'\bcustomer\s*id\s*\d+\b', '', cleaned, flags=re.I).strip()
    cleaned = re.sub(r'product(?: name)?\s*[:=]?\s*[A-Za-z0-9 ]+', '', cleaned, flags=re.I).strip()
    cleaned = re.sub(r'quantity\s*[:=]?\s*\d+', '', cleaned, flags=re.I).strip()
    return cleaned.strip(" :-") if len(cleaned.strip(" :-")) > 2 else ""

_PRICE_LOOKUP = {
    "macbook air m3": 124900,
    "wireless earbuds": 8990,
    "iphone 16": 79900,
    "samsung galaxy watch": 28990,
    "sony wh-1000xm5": 29990,
}

def _get_product_price(product_name: str):
    name = product_name.lower().strip()
    for key, price in _PRICE_LOOKUP.items():
        if key in name:
            return price
    return 2999