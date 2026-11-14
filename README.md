# AI Portfolio — Full Stack (Phase 3)

## Run on Mac in VS Code
1. Open the extracted `ai_portfolio` folder in VS Code.
2. Open **Terminal → New Terminal**.
3. Create a virtual environment: `python3 -m venv .venv`
4. Activate it: `source .venv/bin/activate`
5. Install packages: `python -m pip install -r requirements.txt`
6. Start the server: `python -m uvicorn main:app --reload`
7. Visit **http://127.0.0.1:8000** (do not double-click index.html).

## API endpoints
- `GET /api/health` — check the backend
- `GET /api/projects` — example JSON project data
- `POST /api/contact` — save contact message in `portfolio_messages.db`
- `POST /api/chat` — preset replies by default, optional real LLM
- `/docs` — interactive REST API documentation

## Optional integrations
Copy `.env.example` to `.env`. To use real AI, set `OPENAI_API_KEY` (API billing may apply). To notify an external service of contacts, set `WEBHOOK_URL` to a trusted HTTPS webhook URL. **Never put API keys in JavaScript, HTML, or GitHub.** The contact form stores personal information locally: do not deploy publicly without adding anti-spam protections, privacy notice, authentication for any admin access, and an appropriate data retention policy. SQLite data stays on the host machine and may not persist on some cloud platforms.

## Notes
The project gallery is currently rendered in HTML; `/api/projects` demonstrates a separate REST endpoint. The site does not require a paid API for demo chat. A real model is optional.
