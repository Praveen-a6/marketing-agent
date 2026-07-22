import os
import json
import logging
from fastapi import FastAPI, Request, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import requests

load_dotenv(os.path.join(os.path.dirname(__file__), '../configs/instagram.env'))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv("INSTAGRAM_VERIFY_TOKEN", "career_solution_webhook")
DATABASE_URL = os.getenv("DATABASE_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ADMIN_IDS = os.getenv("TELEGRAM_ADMIN_IDS", "").split(",")

app = FastAPI()

class MarketingDB:
    def __init__(self):
        self.conn_str = DATABASE_URL

    def _get_connection(self):
        return psycopg2.connect(self.conn_str, cursor_factory=RealDictCursor)

    def insert_lead(self, full_name, platform, username, text, comment_id=None, media_id=None, sender_id=None, conversation_id=None):
        query = """
        INSERT INTO leads (full_name, source_platform, social_username, notes, lead_status,
                           comment_id, media_id, sender_id, conversation_id)
        VALUES (%s, %s, %s, %s, 'new', %s, %s, %s, %s)
        RETURNING id, full_name, source_platform, social_username;
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (full_name, platform, username, text, comment_id, media_id, sender_id, conversation_id))
                    result = cur.fetchone()
                    conn.commit()
                    return result
        except Exception as e:
            logger.error(f"DB insert error: {e}")
            return None

    def update_lead_score(self, lead_id, score, reason=""):
        query = """
        UPDATE leads SET lead_score = %s, qualification_reason = %s, qualification_status = 'scored'
        WHERE id = %s
        RETURNING id;
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (score, reason, lead_id))
                    conn.commit()
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Update score error: {e}")
            return None

    def get_lead_by_id(self, lead_id):
        query = "SELECT * FROM leads WHERE id = %s;"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (lead_id,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Get lead error: {e}")
            return None

db = MarketingDB()

def calculate_score(text):
    score = 0
    reasons = []
    keywords = {
        "internship": 25,   # increased
        "placement": 30,    # increased
        "join": 15,         # new
        "how to": 10,       # new
        "ai": 15,
        "data science": 15,
        "full stack": 10,
        "cybersecurity": 10,
        "data analytics": 10,
        "interested": 10,
        "course": 10,
        "training": 10
    }
    text_lower = (text or "").lower()
    for word, pts in keywords.items():
        if word in text_lower:
            score += pts
            reasons.append(f"{word}(+{pts})")
    if len(text) > 5:
        score += 5
        reasons.append("text_length(+5)")
    score = min(score, 100)
    return score, ", ".join(reasons)

def send_telegram_alert(lead):
    msg = f"""🔔 *New Instagram Lead*

👤 Name: {lead['full_name']}
🆔 Username: {lead['social_username']}
📱 Platform: {lead['source_platform']}
📊 Lead ID: {lead['id']}
📝 Message: {lead.get('notes', '')[:100]}

Use `/view {lead['id']}` for details.
Use `/reply {lead['id']} <message>` to reply.
"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for admin_id in TELEGRAM_ADMIN_IDS:
        if admin_id.strip():
            try:
                requests.post(url, json={
                    "chat_id": admin_id.strip(),
                    "text": msg,
                    "parse_mode": "Markdown"
                }, timeout=5)
            except Exception as e:
                logger.error(f"Telegram send failed: {e}")

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    logger.info(f"Received webhook: {json.dumps(data, indent=2)}")
    if data.get("object") != "instagram":
        return {"status": "ignored"}

    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            field = change.get("field")
            value = change.get("value", {})
            if field == "comments":
                from_user = value.get("from", {})
                username = from_user.get("username", "unknown")
                text = value.get("text", "")
                comment_id = value.get("id")
                media_id = value.get("media", {}).get("id")
                lead = db.insert_lead(
                    full_name=username,
                    platform="instagram",
                    username=username,
                    text=text,
                    comment_id=comment_id,
                    media_id=media_id,
                    sender_id=from_user.get("id")
                )
                if lead:
                    score, reason = calculate_score(text)
                    db.update_lead_score(lead['id'], score, reason)
                    if score >= 50:
                        send_telegram_alert(lead)
                    logger.info(f"Lead {lead['id']} scored {score} ({reason})")

            elif field == "messages":
                # Handle DMs
                sender = value.get("sender", {})
                sender_id = sender.get("id")
                recipient = value.get("recipient", {})
                recipient_id = recipient.get("id")
                message = value.get("message", {})
                text = message.get("text", "")
                mid = message.get("mid")
                # Create lead with sender_id and conversation_id (mid)
                lead = db.insert_lead(
                    full_name=f"user_{sender_id}",  # we don't have username for DM
                    platform="instagram_dm",
                    username=f"user_{sender_id}",
                    text=text,
                    sender_id=sender_id,
                    conversation_id=mid
                )
                if lead:
                    score, reason = calculate_score(text)
                    db.update_lead_score(lead['id'], score, reason)
                    if score >= 50:
                        send_telegram_alert(lead)
                    logger.info(f"Lead {lead['id']} (DM) scored {score} ({reason})")

    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
