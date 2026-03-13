# SheGen

**Women Harassment Detection & Privacy-Preserving Moderation**

A production-ready prototype that detects abusive content across English, Hindi, Malayalam, and Tamil, with PII masking and a moderator triage workflow.

## Features

- **Multilingual Harassment Detection** – English, Hindi, Malayalam, Tamil
- **Privacy-Preserving** – PII detection and masking before LLM processing
- **Groq-Powered** – Fast LLM inference for classification and explanations
- **Moderation Triage** – Approve, Warn, Escalate, Delete workflow
- **Clean Architecture** – Modular, scalable, type-hinted code

## Tech Stack

- **Backend:** Python, FastAPI, Groq API, LangChain, SQLite
- **Dashboard:** Built-in HTML (served at /dashboard)
- **ML:** langdetect, Groq LLM

## Quick Start

### 1. Clone & Setup

```bash
cd TCSGenAIProfanityFilter
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` and add your Groq API key:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a key at [console.groq.com](https://console.groq.com).

### 3. Install Dependencies

```bash
# Use a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run

```bash
source venv/bin/activate  # if using venv
python run.py
```

- **Dashboard:** http://localhost:8000/dashboard  
- **Test API:** http://localhost:8000/docs  

**Demo script (optional):**
```bash
python demo/run_demo.py
```  

## Project Structure

```
TCSGenAIProfanityFilter/
├── backend/
│   ├── api/           # FastAPI routes, static dashboard
│   ├── services/      # Business logic
│   ├── models/        # Pydantic schemas
│   ├── privacy/       # PII detection & masking
│   ├── detection/     # Language, classifier
│   └── database/      # SQLAlchemy models & DB
├── demo/
│   └── run_demo.py
├── requirements.txt
└── .env.example
```

## API Endpoints

### POST /api/analyze

Analyze text for harassment.

**Request:**
```json
{
  "text": "User message to analyze"
}
```

**Response:**
```json
{
  "language": "en",
  "classification": "abusive",
  "confidence": 0.92,
  "pii_detected": true,
  "masked_text": "Contact [EMAIL_REDACTED] for help",
  "explanation": "Contains direct insults and threats.",
  "severity": "high",
  "message_id": 1
}
```

### GET /api/moderation_queue

Get moderation queue. Query params: `status` (pending|approved|warned|escalated|deleted), `limit`, `offset`.

### POST /api/moderation_action

Apply moderator action.

**Request:**
```json
{
  "moderation_id": 1,
  "action": "escalate",
  "notes": "Requires human review"
}
```

Actions: `approve`, `warn_user`, `escalate`, `delete`.

## Example Requests (curl)

```bash
# Analyze a message
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "You are an idiot. I will find you."}'

# Get moderation queue
curl "http://localhost:8000/api/moderation_queue?status=pending"

# Take action
curl -X POST http://localhost:8000/api/moderation_action \
  -H "Content-Type: application/json" \
  -d '{"moderation_id": 1, "action": "escalate"}'
```

## Privacy & Security

- **PII Masking:** Emails, phone numbers (Indian & generic) are detected and replaced with `[EMAIL_REDACTED]`, `[PHONE_REDACTED]` before sending to the LLM.
- **Anonymized Storage:** Only hashed content and masked text are stored. No raw PII in logs or database.
- **Secrets:** All credentials via environment variables (`.env`).

## Extensibility

- **Multimedia:** Detection pipeline can be extended with image/audio modules.
- **Database:** Switch to PostgreSQL by changing `DATABASE_URL` in `.env`.

## Sharing / Installing on Another System

**Exclude when zipping:** `venv/`, `*.db`, `.env`, `__pycache__/`

```bash
# Create a shareable zip (from project root)
zip -r shegen.zip . -x "venv/*" -x "*.db" -x ".env" -x "*__pycache__*"
```

**On new system:** Unzip, `cp .env.example .env`, add Groq key, `pip install -r requirements.txt`, `python run.py`.

## License

MIT
