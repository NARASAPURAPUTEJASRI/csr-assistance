# AI-Powered Customer Service Assistant
An intelligent, scope-aware customer service assistant built for e-commerce platforms. Combines a FastAPI backend, SQLite database, and Gemini LLM to handle order queries, customer lookups, ticket/complaint management, and more — all through a clean chat UI.

# Table of Contents

Problem Statement

Features

Tech Stack

Project Structure

Architecture & Workflow

LLM vs Backend Responsibilities

Test Prompts


# Problem Statement
Customer support teams face repetitive, high-volume queries that slow resolution times and strain human agents. This project automates first-line support for e-commerce platforms by building an AI assistant that:

Stays on-topic — Rejects unrelated general knowledge questions

Returns clean data — Filters customer records to only relevant fields

Prevents duplicates — Blocks or confirms duplicate tickets/complaints

Collects smartly — Only prompts for truly missing data during ticket/complaint creation

Prioritises automatically — Classifies complaint urgency as HIGH, MEDIUM, or LOW

Reports clearly — Renders high-priority complaints in formatted table output


# Features

**General Interactions**

Greetings, goodbyes, acknowledgements
Escalation to a human agent

**Order Management**

Order status, details, and delay enquiries
Order cancellation
New order creation

**Customer Queries**

Customer information lookup (filtered by requested fields)
Customer order history

**Ticket & Complaint Handling**

Create support tickets with duplicate detection
Create complaints with automatic priority classification
Look up complaints by order ID, customer ID, or customer name
High-priority complaints report (table format)

**Safety & Intelligence**

Out-of-scope query detection and graceful rejection
Smart field collection — only asks for what's genuinely missing
Duplicate prevention with confirmation flow


🛠️ **Tech Stack**

FastAPI - REST API framework 

SQLite  - Local file-based database (csr_database.db)

Gemini  - LLMAI engine for intent detection and NLP

Pydantic- Request/response validation and modelling

Uvicorn - ASGI server

Tailwind CSS   - Utility-first CSS 

HTML / CSS / JS - Frontend chat interface

🔄 **Architecture & Workflow**

![image alt](https://github.com/NARASAPURAPUTEJASRI/csr-assistance/blob/506a51e9dbb84fed7385ee5ab928237ec65c7b5b/flow_img.png)


# LLM vs Backend Responsibilities
**Gemini LLM handles**:

Intent classification from natural language

Out-of-scope (OUT_OF_SCOPE) detection

Entity extraction — order_id, customer_id, customer_name

Customer response field filtering

Complaint priority classification (HIGH / MEDIUM / LOW)

Fallback conversational replies for ambiguous inputs

**FastAPI + SQLite handles**:

Data storage and retrieval

Business logic and intent routing

Order lookup, creation, and cancellation

Customer data lookup and field filtering

Ticket and complaint creation with duplicate detection

Table-formatted report generation for high-priority complaints

# Start the server
python -m uvicorn app:app --reload

Open index.html in your browser or navigate to http://localhost:8000.

# Test Prompts
Use these prompts to validate all assistant capabilities:

**Out-of-Scope Detection**

What is AI?

What is oxygen?

**Greetings & Polite Interactions**

hi

hello

thanks

bye

**Order Queries**

status of order 101

details of order 101

order 101 delay

cancel order 102

create order for customer id 1 product iPhone 16 quantity 1

**Customer Information**

Tejasri phone number

Tejasri email

Tejasri details

customer id 1 details

Customer Order History

show orders for Tejasri

orders for customer id 1

**Ticket Creation**

create ticket for order 104 issue damaged screen

create ticket customer id 1 order id 101 issue wrong shipment

create ticket                          ← triggers smart field collection

**Complaint Creation**

create complaint for order 104 product damaged

create complaint for customer id 1 order id 101 issue late delivery

create complaint                       ← triggers smart field collection

create complaint for customer id 19    ← prompts for missing order_id and issue

**Complaint Lookup**

complaint details for order 113

complaint details for customer id 1

complaint details for Tejasri

**Duplicate Prevention**

create ticket for order 104 issue damaged screen    ← first time: created

create ticket for order 104 issue damaged screen    ← second time: duplicate warning


Outputs Images:
![image alt](https://github.com/NARASAPURAPUTEJASRI/csr-assistance/blob/ea814269230d219bbb93d3bb707fffbad627030a/img1.png)

![image alt](https://github.com/NARASAPURAPUTEJASRI/csr-assistance/blob/0d89b03f8c5a7860e543c110dd6615f17b8fa054/img2.png)

![image alt](https://github.com/NARASAPURAPUTEJASRI/csr-assistance/blob/4306315ea645e3d9464218e92fc68ac880e3bbc8/img3.png)

![image alt](https://github.com/NARASAPURAPUTEJASRI/csr-assistance/blob/7c26c595bdcf0059e6665f5df8581d3cc0d02ea2/img4.png)
