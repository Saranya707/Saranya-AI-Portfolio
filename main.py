
import os
import sqlite3
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# ==========================================
# 1. PROJECT CONFIGURATION
# ==========================================

BASE = Path(__file__).resolve().parent

load_dotenv(BASE / ".env")

DB_PATH = BASE / "portfolio_messages.db"

MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL", "").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

app = FastAPI(
    title="Saranya AI Portfolio API",
    description="AI Portfolio with REST APIs, Ollama and Make.com",
    version="1.0.0"
)

# ==========================================
# 2. SQLITE DATABASE
# ==========================================

def initialize_database():
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.commit()

    finally:
        connection.close()


initialize_database()

# ==========================================
# 3. DATA MODELS
# ==========================================

class Contact(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    message: str = Field(min_length=1, max_length=5000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


# ==========================================
# 4. PORTFOLIO INFORMATION
# ==========================================

PORTFOLIO_CONTEXT = """
You are an AI assistant for Saranya's portfolio.

Education:
M.Tech in Artificial Intelligence and Data Science.

Skills:
Python, SQL, Machine Learning, Data Science,
HTML, CSS, JavaScript, FastAPI, Streamlit,
GitHub, Data Analytics and Generative AI.

Projects:

1. E-Commerce Sales Analytics and Forecasting
   Sales analysis and machine learning forecasting.

2. ResearchIQ
   AI Research Assistant using RAG.

3. StyleSync AI
   Digital wardrobe and AI styling platform.

4. Banking and Loan Analytics
   SQL-based banking analytics and dashboards.

Career interests:
AI Engineer, ML Engineer, Data Scientist
and Data Analyst.

Answer questions about the portfolio.
Be professional, friendly and concise.
Do not invent achievements or qualifications.
"""


# ==========================================
# 5. HEALTH CHECK REST API
# ==========================================

@app.get("/api/health")
async def health_check():
    return {
        "status": "success",
        "message": "AI Portfolio Backend is running"
    }


# ==========================================
# 6. PROJECTS REST API
# ==========================================

@app.get("/api/projects")
async def projects():
    return {
        "success": True,
        "projects": [
            {
                "name": "E-Commerce Sales Analytics",
                "category": "Data Science"
            },
            {
                "name": "ResearchIQ",
                "category": "Artificial Intelligence"
            },
            {
                "name": "StyleSync AI",
                "category": "Artificial Intelligence"
            },
            {
                "name": "Banking & Loan Analytics",
                "category": "Data Analytics"
            }
        ]
    }


# ==========================================
# 7. MAKE.COM WEBHOOK INTEGRATION
# ==========================================

async def notify_make(
    name: str,
    email: str,
    message: str
) -> bool:

    url = os.getenv("MAKE_WEBHOOK_URL", "").strip()

    if not url:
        print("Webhook skipped: URL not configured")
        return False

    if not url.startswith("https://"):
        print("Webhook skipped: Invalid URL")
        return False

    payload = {
        "event": "portfolio.contact",
        "name": name,
        "email": email,
        "message": message,
        "source": "AI Portfolio Contact Form"
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:

            response = await client.post(
                url,
                json=payload
            )

            response.raise_for_status()

            print("Webhook sent successfully")
            print("Webhook HTTP status:", response.status_code)

            return True

    except httpx.HTTPStatusError as exc:

        print(
            "Webhook HTTP status:",
            exc.response.status_code
        )

        print(
            "Webhook response:",
            exc.response.text[:500]
        )

        return False

    except httpx.RequestError as exc:

        print(
            "Webhook connection error:",
            type(exc).__name__
        )

        return False


# ==========================================
# 8. CONTACT FORM REST API
# ==========================================

@app.post("/api/contact", status_code=201)
async def contact(payload: Contact):

    name = payload.name.strip()
    email = payload.email.strip()
    message = payload.message.strip()

    if not name or not email or not message:
        raise HTTPException(
            status_code=400,
            detail="All fields are required"
        )

    if "@" not in email:
        raise HTTPException(
            status_code=400,
            detail="Invalid email address"
        )

    try:
        connection = sqlite3.connect(DB_PATH)

        try:
            cursor = connection.execute(
                """
                INSERT INTO messages
                (name, email, message)
                VALUES (?, ?, ?)
                """,
                (name, email, message)
            )

            message_id = cursor.lastrowid
            connection.commit()

        finally:
            connection.close()

    except sqlite3.Error as exc:

        print("Database error:", type(exc).__name__)

        raise HTTPException(
            status_code=500,
            detail="Unable to save message"
        ) from exc

    webhook_sent = await notify_make(
        name,
        email,
        message
    )

    return {
        "success": True,
        "message": "Message received successfully",
        "message_id": message_id,
        "webhook_sent": webhook_sent
    }


# ==========================================
# 9. OLLAMA AI CHATBOT
# ==========================================

async def generate_ai_response(question: str):

    prompt = f"""
{PORTFOLIO_CONTEXT}

Visitor question:
{question}

AI assistant answer:
"""

    request_data = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:

            response = await client.post(
                OLLAMA_URL,
                json=request_data
            )

            response.raise_for_status()

            result = response.json()

            return result.get(
                "response",
                "I could not generate an answer."
            )

    except httpx.HTTPError as exc:

        print(
            "Ollama connection error:",
            type(exc).__name__
        )

        raise HTTPException(
            status_code=503,
            detail="Ollama is unavailable. Check the AI model."
        ) from exc

    except ValueError as exc:

        raise HTTPException(
            status_code=502,
            detail="Invalid response from Ollama"
        ) from exc


# ==========================================
# 10. AI CHAT REST API
# ==========================================

@app.post("/api/chat")
@app.post("/api/ai-chat")
async def chat(payload: ChatRequest):

    question = payload.message.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a question"
        )

    answer = await generate_ai_response(question)

    return {
        "success": True,
        "reply": answer,
        "response": answer
    }


# ==========================================
# 11. FRONTEND FILE SERVING
# ==========================================

@app.get("/")
async def index():

    file_path = BASE / "index.html"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="index.html not found"
        )

    return FileResponse(file_path)


@app.get("/style.css")
async def stylesheet():

    file_path = BASE / "style.css"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="style.css not found"
        )

    return FileResponse(
        file_path,
        media_type="text/css"
    )


@app.get("/script.js")
async def javascript():

    file_path = BASE / "script.js"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="script.js not found"
        )

    return FileResponse(
        file_path,
        media_type="application/javascript"
    )


# ==========================================
# END OF MAIN.PY
# ==========================================


@app.get("/portrait.png")
async def portrait_image():
    file_path = BASE / "portrait.png"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Portrait not found")
    return FileResponse(file_path, media_type="image/png")
