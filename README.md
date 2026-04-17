AI Customer Assistant

1. Project Overview

This project is an AI-powered customer service assistant for e-commerce. It accepts user queries through a chat UI and responds with information about:

orders
customers
tickets
complaints
It also prevents the assistant from answering unrelated general questions, filters customer data based on user intent, formats responses cleanly, and manages ticket/complaint creation safely.

2. What the Assistant Can Do

Recognize greetings, goodbyes, thanks, and escalation requests
Check order status, details, delay, and cancellation
Lookup customer information and orders
Create support tickets
Create complaints with priority classification
Create new orders from customer inputs
Fetch complaint details via order id, customer id, or customer name
List high priority complaints
Detect out-of-scope queries and reply with a restricted message

3. Project Flow

User sends a query from the web UI.
Frontend POSTs the query to /chat.
app.py receives the request and calls ai_engine.detect_intent(query).
ai_engine.py first applies rule-based checks for greetings, thanks, etc.
If no rule matches, it sends the query to the Gemini LLM with a prompt to classify intent and extract IDs.
The model returns a JSON intent result.
app.py routes the request based on the detected intent:
order queries handled by db.py
customer queries handled by db.py plus LLM filtering
ticket/complaint creation handled with duplicate checks
complaint lookup handled by order/customer queries
Results are formatted and returned to the frontend.

4. File Description

app.py

Main FastAPI application
Receives chat requests, routes intents, formats output
Uses backend database functions and AI helpers

ai_engine.py

Handles intent detection
Uses Gemini LLM for classification, customer filtering, and complaint priority
Contains rule-based shortcuts

db.py

SQLite database layer
Stores and retrieves orders, customers, tickets, and complaints
Handles duplicate checks, order creation, and complaint lookup

index.html

Frontend chat UI
Loads the chat page and displays messages

script.js

Frontend behavior for chat messaging
Sends queries to the backend and shows results

config.py

Stores configuration values such as API key, model, and confidence threshold
Should be changed to load secrets from environment variables

5. Test Prompts

Use these prompts to verify the assistant:

Out-of-scope

What is AI?
What is oxygen?

Greetings / polite

hi
hello
thanks
bye
talk to agent

Order queries

status of order 101
details of order 101
order 101 delay
cancel order 102
create order for customer id 1 product iPhone 16 quantity 1

Customer info

Tejasri phone number
Tejasri email
Tejasri details
customer id 1 details

Customer orders

show orders for Tejasri
orders for customer id 1

Ticket creation

create ticket for order 104 issue damaged screen
create ticket customer id 1 order id 101 issue wrong shipment
create ticket (should ask for all required fields)

Complaint creation

create complaint for order 104 product damaged
create complaint for customer id 1 order id 101 issue late delivery
create complaint (should ask for all required fields)
create complaint for customer id 19 (should ask for order_id and issue too)

Complaint lookup

complaint details for order 113
complaint details for customer id 1
complaint details for Tejasri

Duplicate prevention

create a ticket/complaint twice for the same order and verify the confirmation message


