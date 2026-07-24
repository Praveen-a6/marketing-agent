import os
import json
import logging
import requests
import psycopg2
import re
import subprocess
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

# Load environment configuration
env_path = os.path.join(os.path.dirname(__file__), '../configs/instagram.env')
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv("INSTAGRAM_VERIFY_TOKEN", "career_solution_webhook")
DATABASE_URL = os.getenv("DATABASE_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ADMIN_IDS = [i.strip() for i in os.getenv("TELEGRAM_ADMIN_IDS", "").split(",") if i.strip()]
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

OUR_IG_USERNAME = "careersolutions_7"

app = FastAPI()

class MarketingDB:
    def __init__(self):
        self.conn_str = DATABASE_URL

    def _get_connection(self):
        return psycopg2.connect(self.conn_str, cursor_factory=RealDictCursor)

    def get_or_create_lead(self, username, platform="instagram"):
        """Safely retrieves an existing lead or creates a fresh record."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM leads WHERE social_username = %s AND source_platform = %s ORDER BY created_at DESC LIMIT 1;", (username, platform))
                    lead = cur.fetchone()
                    if lead: return lead
                    
                    cur.execute("""
                        INSERT INTO leads (full_name, social_username, source_platform, lead_status, lead_score)
                        VALUES (%s, %s, %s, 'new', 0) RETURNING *;
                    """, (username, username, platform))
                    conn.commit()
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"DB get/create error: {e}")
            return None

    def update_lead_state(self, lead_id, **kwargs):
        """Dynamically updates lead attributes and returns the fresh record."""
        if not kwargs: return None
        set_clauses = []
        values = []
        for k, v in kwargs.items():
            if k == 'lead_score':
                set_clauses.append("lead_score = LEAST(100, GREATEST(COALESCE(lead_score, 0), %s))")
            else:
                set_clauses.append(f"{k} = %s")
            values.append(v)
        
        values.append(lead_id)
        query = f"UPDATE leads SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *;"
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, tuple(values))
                    res = cur.fetchone()
                    conn.commit()
                    return res
        except Exception as e:
            logger.error(f"DB update error: {e}")
            return None

db = MarketingDB()

# --- NLU Engine & Safety Net ---
def evaluate_comment_intent(text):
    """Hybrid evaluator: Uses keyword safety nets combined with DeepSeek."""
    text_lower = text.lower()
    hot_keywords = ["interest", "intern", "course", "join", "ai", "data", "full stack", "cyber", "fee", "price", "how", "details"]
    
    # Force high intent instantly if buying keywords match
    if any(k in text_lower for k in hot_keywords):
        return True

    if not DEEPSEEK_API_KEY: return False
    
    try:
        res = requests.post("https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": f"Is this user asking about a course, internship, or training program? Answer YES or NO: '{text}'"}], "max_tokens": 10}, timeout=5)
        if "YES" in res.json()["choices"][0]["message"]["content"].upper():
            return True
    except Exception as e:
        logger.error(f"NLU Intent check failed: {e}")
    
    return False

# --- Meta API Integration ---
def send_meta_dm(igsid, text_message, comment_id=None):
    """Sends a private DM, utilizing the comment_id loophole when available."""
    headers = {"Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}", "Content-Type": "application/json"}
    url = "https://graph.instagram.com/v25.0/me/messages"
    
    if comment_id:
        payload = {"recipient": {"comment_id": comment_id}, "message": {"text": text_message}}
    else:
        payload = {"recipient": {"id": igsid}, "message": {"text": text_message}}
        
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        if res.status_code != 200:
            logger.error(f"Meta API Error: {res.text}")
    except Exception as e:
        logger.error(f"Network timeout on Meta DM: {e}")

def send_meta_public_reply(comment_id, text_message):
    """Posts a public reply directly to a user's comment."""
    try:
        url = f"https://graph.instagram.com/v25.0/{comment_id}/replies"
        requests.post(url, headers={"Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}", "Content-Type": "application/json"}, 
                      json={"message": text_message}, timeout=8)
    except Exception as e:
        logger.error(f"Public reply error: {e}")

def send_telegram_alert(lead):
    """Sends executive hot lead alert to Telegram."""
    track = lead.get('qualification_status') or 'Student'
    msg = f"""🔥 <b>HOT LEAD ({str(track).upper()})</b>
👤 <b>Handle:</b> @{lead['social_username']}
🎯 <b>Interest:</b> {lead.get('interested_course') or lead.get('career_goal') or 'Pending'}
📞 <b>Phone:</b> {lead.get('phone') or 'Pending'}
🎓 <b>College/Company:</b> {lead.get('college_name') or 'Pending'}

<i>Data synced to Google Sheets. Use /lead {lead['id']} for details.</i>"""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for admin_id in TELEGRAM_ADMIN_IDS:
        try:
            requests.post(url, json={"chat_id": admin_id, "text": msg, "parse_mode": "HTML"}, timeout=5)
        except Exception:
            pass

def trigger_google_sheets_sync():
    """Triggers background process to mirror PostgreSQL to Google Sheets."""
    try:
        subprocess.Popen(["python3", "/home/praveen/marketing-agent/skills/sheets_sync.py"])
    except Exception as e:
        logger.error(f"Sheets sync trigger failed: {e}")

# --- Deterministic State Machine ---
def process_dm_state_machine(igsid, username, message_text, lead, comment_id=None):
    """Fast, reliable state machine that updates fields sequentially without timeouts."""
    updates = {}
    score = lead.get("lead_score") or 0
    text_lower = message_text.lower().strip()
    
    if lead.get("phone"):
        return # Already fully qualified

    # STEP 1: Capture Course Selection
    if not lead.get("interested_course"):
        course_map = {"1": "AI/ML", "2": "Data Science", "3": "Full Stack", "4": "Internships", "5": "Corporate Training", "ai": "AI/ML", "data": "Data Science", "intern": "Internships"}
        detected = None
        for key, val in course_map.items():
            if key in text_lower:
                detected = val
                break
        
        if detected:
            updates["interested_course"] = detected
            score += 15
        elif len(message_text) > 2:
            updates["interested_course"] = message_text[:250]
            score += 10

    # STEP 2: Capture College Name
    elif not lead.get("college_name"):
        if len(message_text) > 2:
            updates["college_name"] = message_text[:250]
            score += 15

    # STEP 3: Capture Phone Number
    elif not lead.get("phone"):
        digits = re.sub(r'\D', '', message_text)
        if len(digits) >= 8:
            updates["phone"] = message_text[:50]
            score += 30
        else:
            send_meta_dm(igsid, "I didn't quite catch a valid phone number. Could you please share your WhatsApp number again?", comment_id)
            return

    # Commit Updates to Database
    if updates:
        updates["lead_score"] = score
        updated_lead = db.update_lead_state(lead['id'], **updates)
        if updated_lead:
            lead = updated_lead

    # Dynamic Response Routing
    if lead.get("phone"):
        send_meta_dm(igsid, "Thank you so much! 🎉 I've securely noted your details. Our placement team will reach out to you shortly.")
        trigger_google_sheets_sync()
        if score >= 60: send_telegram_alert(lead)
        return

    if not lead.get("interested_course"):
        menu = f"Hi {username}! 👋 Welcome to Career Solutions.\n\nTo get you the right details instantly, please reply with a number:\n1️⃣ AI/ML\n2️⃣ Data Science\n3️⃣ Full Stack / Cybersec\n4️⃣ Internships\n5️⃣ Corporate Training"
        send_meta_dm(igsid, menu, comment_id)
    elif not lead.get("college_name"):
        send_meta_dm(igsid, f"Awesome choice! 🚀\n\nTo check prerequisites, what college and degree are you currently pursuing?", comment_id)
    elif not lead.get("phone"):
        send_meta_dm(igsid, "Perfect! 🎓\n\nLastly, what is your WhatsApp number so our placement officer can share the exact syllabus and fee details?", comment_id)


# --- FastAPI Endpoints ---
@app.get("/webhook")
async def verify(request: Request):
    if request.query_params.get("hub.mode") == "subscribe" and request.query_params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(request.query_params.get("hub.challenge"))
    raise HTTPException(403, "Verification failed")

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    if data.get("object") != "instagram": return {"status": "ignored"}

    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            field = change.get("field")
            val = change.get("value", {})

            # Handle Incoming Comments
            if field == "comments":
                username = val.get("from", {}).get("username", "unknown")
                igsid = val.get("from", {}).get("id", "")
                text = val.get("text", "")
                comment_id = val.get("id", "")

                if username == OUR_IG_USERNAME: continue
                
                lead = db.get_or_create_lead(username)
                
                if igsid and comment_id:
                    is_lead = evaluate_comment_intent(text)
                    
                    if not is_lead:
                        send_meta_public_reply(comment_id, "Thank you for the support! 🙏")
                    else:
                        send_meta_public_reply(comment_id, "Thanks for reaching out! Please check your DMs for details.")
                        process_dm_state_machine(igsid, username, text, lead, comment_id=comment_id)

            # Handle Incoming DMs
            elif field == "messages":
                igsid = val.get("sender", {}).get("id")
                message_text = val.get("message", {}).get("text", "")
                
                username = None
                try:
                    res = requests.get(f"https://graph.instagram.com/v25.0/{igsid}?fields=username&access_token={INSTAGRAM_ACCESS_TOKEN}", timeout=3)
                    if res.status_code == 200:
                        username = res.json().get("username")
                except Exception:
                    pass

                if not username:
                    username = f"user_{igsid}"
                    
                if username == OUR_IG_USERNAME or not message_text: continue
                
                lead = db.get_or_create_lead(username)
                process_dm_state_machine(igsid, username, message_text, lead)

    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
