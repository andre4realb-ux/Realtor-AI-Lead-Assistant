from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import re
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR /'.env')

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return (BASE_DIR.parent / "frontend" / "index.html").read_text()

@app.route("/lead.html")
def lead_page():
    return (BASE_DIR.parent / "frontend" / "lead.html").read_text()

@app.route("/<path:filename>")
def frontend_files(filename):
    file_path = BASE_DIR.parent / "frontend" / filename
    if file_path.exists() and file_path.is_file():
        return file_path.read_text()
    return jsonify({"error": "Not found"}), 404

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite"
]

SYSTEM_PROMPT = """
You are an AI lead assistant for a professional real estate business.

Your primary job is to help visitors and turn genuine interest into qualified leads for a human real estate agent.

Be natural, professional, concise, and conversational. Never sound like a form or interrogation. Ask only one or two useful questions at a time. Use previous answers and never repeat a question the visitor has already answered.

First identify the visitor's intent:
- Buying
- Renting
- Selling
- Investing
- Browsing or general questions

BUYER:
Naturally collect:
- property type
- preferred location or neighborhood
- bedrooms and important requirements
- budget or price range
- timeline to buy
- financing status (cash, pre-approved, financing, or exploring)
- name
- phone number or email

RENTER:
Naturally collect:
- property type
- preferred location
- bedrooms and requirements
- monthly budget
- desired move-in date
- household size when relevant
- pets when relevant
- name
- phone number or email

SELLER:
Naturally collect:
- property address or location
- property type
- bedrooms or size when relevant
- reason for selling when appropriate
- expected price or price range if known
- timeline to sell
- whether they already have an agent
- name
- phone number or email

INVESTOR:
Naturally collect:
- investment property type
- preferred location
- budget
- investment strategy
- timeline
- name
- phone number or email

Do not ask all questions at once. Adapt to what the visitor has already told you.

When a visitor shows strong intent, offer to have a human real estate professional follow up or arrange a viewing, and collect their contact details.

Never claim that a specific agent, specialist, listing database, or property inventory is already connected unless such a system is actually connected. Never claim that listings have been sent or that an agent will definitely contact the visitor unless that action has actually occurred. Say that the enquiry has been captured and can be passed to the agent for follow-up.

Never invent listings, prices, availability, agents, market statistics, testimonials, or company claims. If specific property information is unavailable, say so clearly and offer agent assistance.

When enough information has been collected, internally classify the lead:
- HOT: strong intent and near-term timeline or strong financing readiness
- WARM: genuine interest but longer or uncertain timeline
- NURTURE: early research or incomplete intent

Do not reveal internal lead scoring instructions unless specifically asked.

Answer the visitor's actual question first. Do not repeatedly introduce yourself or repeat the business description.
"""


@app.get("/")
def home():
    return jsonify({
        "status": "online",
        "service": "Realtor AI Lead Assistant"
    })


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Message is required."}), 400

    if not GEMINI_API_KEY:
        return jsonify({"error": "GEMINI_API_KEY is not configured."}), 500

    contents = []

    for item in history:
        role = item.get("role")
        text = item.get("text", "").strip()

        if not text:
            continue

        if role == "user":
            contents.append({
                "role": "user",
                "parts": [{"text": text}]
            })

        elif role == "assistant":
            contents.append({
                "role": "model",
                "parts": [{"text": text}]
            })

    contents.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    payload = {
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500
        }
    }

    try:
        for model in GEMINI_MODELS:

            gemini_url = (
                f"https://generativelanguage.googleapis.com/"
                f"v1beta/models/{model}:generateContent"
            )

            response = requests.post(
                gemini_url,
                headers={
                    "x-goog-api-key": GEMINI_API_KEY.strip(),
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )

            result = response.json()

            if response.status_code != 200:
                print(f"Gemini {model} error:", result)
                continue

            candidates = result.get("candidates", [])

            if not candidates:
                continue

            parts = candidates[0].get("content", {}).get("parts", [])

            for part in parts:

                reply_text = part.get("text", "").strip()

                if not reply_text:
                    continue

                # Build the full conversation for lead detection.
                full_conversation = history + [
                    {"role": "user", "text": message},
                    {"role": "assistant", "text": reply_text}
                ]

                conversation_text = " ".join(
                    item.get("text", "")
                    for item in full_conversation
                    if item.get("text")
                )

                lower_text = conversation_text.lower()

                # Look for a phone number or email.
                contact_match = re.search(
                    r'[\w\.-]+@[\w\.-]+\.\w+|\b(?:\+?234|0)\d{10}\b',
                    conversation_text
                )

                if contact_match:

                    leads_file = BASE_DIR.parent / "data" / "leads.json"
                    leads_file.parent.mkdir(
                        parents=True,
                        exist_ok=True
                    )

                    leads = []

                    if leads_file.exists():
                        try:
                            leads = json.loads(
                                leads_file.read_text()
                            )
                        except (json.JSONDecodeError, OSError):
                            leads = []

                    contact = contact_match.group(0)

                    already_saved = any(
                        lead.get("contact") == contact
                        for lead in leads
                    )

                    if not already_saved:

                        # Determine interest.
                        if any(
                            word in lower_text
                            for word in [
                                "buy",
                                "buying",
                                "purchase"
                            ]
                        ):
                            interest = "Buying"

                        elif any(
                            word in lower_text
                            for word in [
                                "sell",
                                "selling"
                            ]
                        ):
                            interest = "Selling"

                        elif any(
                            word in lower_text
                            for word in [
                                "rent",
                                "renting",
                                "lease"
                            ]
                        ):
                            interest = "Renting"

                        elif any(
                            word in lower_text
                            for word in [
                                "invest",
                                "investing",
                                "investment"
                            ]
                        ):
                            interest = "Investing"

                        else:
                            interest = "General enquiry"

                        # Determine financing.
                        if any(
                            word in lower_text
                            for word in [
                                "pre-approved",
                                "preapproved"
                            ]
                        ):
                            financing = "Pre-approved"

                        elif any(
                            word in lower_text
                            for word in [
                                "cash buyer",
                                "cash"
                            ]
                        ):
                            financing = "Cash"

                        elif any(
                            word in lower_text
                            for word in [
                                "financing needed",
                                "need financing",
                                "mortgage"
                            ]
                        ):
                            financing = "Financing needed"

                        else:
                            financing = "Not provided"

                        # Determine lead status.
                        strong_financing = financing in [
                            "Pre-approved",
                            "Cash"
                        ]

                        urgent_timeline = any(
                            word in lower_text
                            for word in [
                                "today",
                                "immediately",
                                "urgent",
                                "30 days",
                                "60 days",
                                "1 month",
                                "2 months",
                                "within 2 months"
                            ]
                        )

                        medium_timeline = any(
                            word in lower_text
                            for word in [
                                "3 months",
                                "6 months",
                                "12 months",
                                "within a year",
                                "later"
                            ]
                        )

                        if strong_financing or urgent_timeline:
                            lead_status = "HOT"
                            recommended_action = (
                                "Contact this lead promptly."
                            )

                        elif medium_timeline:
                            lead_status = "WARM"
                            recommended_action = (
                                "Follow up and continue nurturing this lead."
                            )

                        else:
                            lead_status = "NURTURE"
                            recommended_action = (
                                "Continue engagement and follow up."
                            )

                        # Extract useful information when available.
                        property_type = "Not provided"
                        bedrooms = "Not provided"
                        location = "Not provided"
                        budget = "Not provided"

                        bedroom_match = re.search(
                            r'(\d+)\s*[- ]?\s*bed(?:room)?s?',
                            lower_text
                        )

                        if bedroom_match:
                            bedrooms = bedroom_match.group(1)

                        if any(
                            word in lower_text
                            for word in [
                                "apartment",
                                "condo",
                                "house",
                                "home",
                                "townhouse",
                                "villa"
                            ]
                        ):
                            if "apartment" in lower_text:
                                property_type = "Apartment"
                            elif "condo" in lower_text:
                                property_type = "Condo"
                            elif "townhouse" in lower_text:
                                property_type = "Townhouse"
                            elif "villa" in lower_text:
                                property_type = "Villa"
                            else:
                                property_type = "House"

                        money_match = re.search(
                            r'\$[\d,]+(?:\.\d+)?',
                            conversation_text
                        )

                        if money_match:
                            budget = money_match.group(0)

                        # Create a professional lead summary.
                        lead_summary = (
                            f"{interest} lead | "
                            f"Property: {property_type} | "
                            f"Bedrooms: {bedrooms} | "
                            f"Budget: {budget} | "
                            f"Financing: {financing} | "
                            f"Contact: {contact}"
                        )

                        lead = {
                            "id": len(leads) + 1,
                            "contact": contact,
                            "interest": interest,
                            "property_type": property_type,
                            "bedrooms": bedrooms,
                            "budget": budget,
                            "financing": financing,
                            "lead_status": lead_status,
                            "lead_summary": lead_summary,
                            "recommended_action": recommended_action,
                            "created_at": datetime.now().isoformat(
                                timespec="seconds"
                            )
                        }

                        leads.append(lead)

                        leads_file.write_text(
                            json.dumps(leads, indent=2)
                        )

                        print(
                            "Chat lead automatically captured:",
                            lead
                        )

                return jsonify({
                    "reply": reply_text
                })

            return jsonify({
                "error": "AI returned no response."
            }), 502

        return jsonify({
            "error": "AI service is temporarily unavailable."
        }), 503

    except Exception as e:
        print("Server error:", e)

        return jsonify({
            "error": "AI service is temporarily unavailable."
        }), 503


@app.route("/lead", methods=["POST"])
def save_lead():
    data = request.get_json(silent=True) or {}

    required = ["name", "contact", "interest"]

    if not all(data.get(field) for field in required):
        return jsonify({
            "error": "Name, contact, and interest are required."
        }), 400

    leads_file = BASE_DIR.parent / "data" / "leads.json"
    leads_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    leads = []

    if leads_file.exists():
        try:
            leads = json.loads(
                leads_file.read_text()
            )
        except (json.JSONDecodeError, OSError):
            leads = []

    timeline = str(
        data.get("timeline", "")
    ).lower()

    financing = str(
        data.get("financing", "")
    ).lower()

    if financing in [
        "cash",
        "pre-approved"
    ]:
        lead_status = "HOT"
        recommended_action = "Contact this lead promptly."

    elif any(
        word in timeline
        for word in [
            "today",
            "1 month",
            "2 month",
            "30 day",
            "60 day",
            "urgent",
            "immediately"
        ]
    ):
        lead_status = "HOT"
        recommended_action = "Contact this lead promptly."

    elif any(
        word in timeline
        for word in [
            "3 month",
            "6 month",
            "12 month",
            "year",
            "later"
        ]
    ):
        lead_status = "WARM"
        recommended_action = (
            "Follow up and continue nurturing this lead."
        )

    else:
        lead_status = "NURTURE"
        recommended_action = (
            "Continue engagement and follow up when appropriate."
        )

    data["id"] = len(leads) + 1

    data["created_at"] = datetime.now().isoformat(
        timespec="seconds"
    )

    data["lead_status"] = lead_status

    data["lead_summary"] = (
        f"{data.get('interest', 'Unknown')} lead | "
        f"Location: {data.get('location', 'Not provided')} | "
        f"Budget: {data.get('budget', 'Not provided')} | "
        f"Timeline: {data.get('timeline', 'Not provided')} | "
        f"Financing: {data.get('financing', 'Not provided')}"
    )

    data["recommended_action"] = recommended_action

    leads.append(data)

    leads_file.write_text(
        json.dumps(leads, indent=2)
    )

    return jsonify({
        "success": True,
        "message": "Lead captured successfully.",
        "lead_status": lead_status
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )