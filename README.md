# Realtor AI Lead Assistant

An AI-powered real estate lead qualification application built with Python, Flask and Google Gemini. It helps website visitors enquire about buying, selling or renting property, gathers requirements and supports agent follow-up.

## Features

- AI-powered real estate conversations using Google Gemini.
- Buyer, seller and renter enquiry handling.
- Collection of property preferences, location, budget and timeline.
- Conversation history passed to the AI assistant.
- Contact and lead information capture.
- Dedicated Connect With an Agent form.
- HOT, WARM and NURTURE lead classification.
- Structured JSON-based lead storage.
- Model fallback and request timeout handling.
- Responsive HTML interface.

## Technology

- Python
- Flask
- Google Gemini API
- Requests
- Flask-CORS
- python-dotenv
- HTML, CSS and JavaScript
- JSON

## Project Structure

```text
Realtor-AI-Lead-Assistant/
├── backend/
│   ├── app.py
│   └── .env.example
├── frontend/
│   ├── index.html
│   └── lead.html
├── data/
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup

1. Clone the repository:

   `git clone https://github.com/andre4realb-ux/Realtor-AI-Lead-Assistant.git`

2. Enter the project directory:

   `cd Realtor-AI-Lead-Assistant`

3. Create and activate a virtual environment:

   `python -m venv .venv`

   macOS/Linux:

   `source .venv/bin/activate`

4. Install dependencies:

   `pip install -r requirements.txt`

5. Create `backend/.env` and add your Google Gemini API key:

   `GEMINI_API_KEY=your_actual_api_key`

6. Start the application:

   `python backend/app.py`

7. Open `http://127.0.0.1:5000` in your browser.

## Application Routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Chat interface |
| GET | `/lead.html` | Agent contact form |
| POST | `/chat` | AI conversation |
| POST | `/lead` | Lead submission |

## Lead Classification

- **HOT:** Enquiries with urgent timelines or qualifying financing status.
- **WARM:** Enquiries with a longer but defined buying or selling timeline.
- **NURTURE:** Enquiries requiring continued engagement.

## Security and Data

- Store API credentials in `backend/.env`.
- Never commit API keys or private customer contact records.
- Local lead records are stored in `data/leads.json`, which is excluded from Git.

## Project Status

A working local prototype. It demonstrates AI-assisted property enquiry handling and lead capture. It is not a production CRM or a live property-listing service. Production deployment, persistent database integration, agent notification and further validation are future improvements.

## Author

**Andrew Bassey Enyekung**

GitHub: https://github.com/andre4realb-ux
