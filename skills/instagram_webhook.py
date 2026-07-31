#!/usr/bin/env python3
"""
Instagram Webhook Handler – Production Grade
Includes Full Menu Routing (Students, HR, Projects) and Smart Regex Extraction.
"""
import os
import sys
import re
import json
import hmac
import hashlib
import logging
import requests
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Header, BackgroundTasks

load_dotenv_path = os.path.join(os.path.dirname(__file__), "..", "configs", "instagram.env")
from dotenv import load_dotenv
load_dotenv(load_dotenv_path, override=True)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "database"))

from db_client import (
    mark_event_processed, get_or_create_lead_by_igsid,
    update_lead_fields, update_lead_score,
    get_menu_state, save_menu_state, is_event_processed,
    get_cursor, get_conn, get_lead
)
from resume_extractor import process_resume
from sheets_append import append_lead

app = FastAPI()
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("instagram_webhook")

# ==================== CONFIG ====================
VERIFY_TOKEN = os.getenv("INSTAGRAM_VERIFY_TOKEN", "career_solution_webhook")
INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET", "")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_IDS = [i.strip() for i in os.getenv("TELEGRAM_ADMIN_IDS", "").split(",") if i.strip()]
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OUR_IG_USERNAME = "careersolutions_7".lower()

NAV_FOOTER = "\n\n💡 Reply with option number, or type 'home' / 'back'."
GREETINGS = {"hi", "hello", "hey", "menu", "start", "help", "option", "home"}

# ==================== HELPERS ====================
def verify_meta_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    if not INSTAGRAM_APP_SECRET or not signature_header: return True
    expected = hmac.new(INSTAGRAM_APP_SECRET.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)

def send_telegram_alert(lead: dict, reason: str, extra: str = ""):
    msg = f"⚠️ <b>{reason}</b>\n👤 @{lead.get('social_username', 'Unknown')}\n{extra}"
    for admin_id in TELEGRAM_ADMIN_IDS:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": admin_id, "text": msg, "parse_mode": "HTML"},
                timeout=5
            )
        except: pass

def send_instagram_public_reply(comment_id: str, message: str):
    url = f"https://graph.facebook.com/v25.0/{comment_id}/replies"
    headers = {"Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}", "Content-Type": "application/json"}
    try:
        res = requests.post(url, headers=headers, json={"message": message}, timeout=15)
        logger.info(f"📢 Public Reply Status: {res.status_code}")
    except Exception as e:
        logger.error(f"❌ Failed to send public reply: {e}")

def send_instagram_dm(recipient_id: str, message: str, is_comment_reply: bool = False, lead: dict = None) -> bool:
    url = "https://graph.facebook.com/v25.0/me/messages"
    recipient_payload = {"comment_id": recipient_id} if is_comment_reply else {"id": recipient_id}
    payload = {"recipient": recipient_payload, "message": {"text": message}}
    try:
        res = requests.post(url, headers={"Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"}, json=payload, timeout=15)
        return res.status_code in (200, 201)
    except Exception as e:
        logger.error(f"❌ DM send exception: {e}")
        return False

def call_deepseek(prompt: str) -> str:
    if not DEEPSEEK_API_KEY: return "casual"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "system", "content": "You are a precise classifier and router for an education agency."}, {"role": "user", "content": prompt}], "temperature": 0.1}
    try:
        res = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=8)
        return res.json()["choices"][0]["message"]["content"].strip().lower()
    except Exception: return "casual"

# ==================== WEBHOOK PROCESSORS ====================
def process_form_resume(phone: str, drive_link: str):
    """Handles the incoming Google Forms webhook data and downloads the PDF."""
    logger.info(f"Processing form webhook for phone: {phone}")
    with get_cursor() as cur:
        cur.execute("SELECT id FROM leads WHERE phone LIKE %s ORDER BY created_at DESC LIMIT 1", (f"%{phone[-10:]}%",))
        res = cur.fetchone()
    
    if not res:
        logger.error(f"❌ No lead found for phone {phone}")
        return
        
    lead_id = res['id']
    update_lead_fields(lead_id, qualification_status="resume_received", notes=f"Drive ID: {drive_link}")
    
    try:
        # Check if drive_link is a raw ID or a full URL
        file_id = drive_link.strip()
        if "http" in file_id or "drive.google.com" in file_id:
            match = re.search(r'/d/([a-zA-Z0-9_-]+)', file_id)
            if not match:
                match = re.search(r'id=([a-zA-Z0-9_-]+)', file_id)
            if match:
                file_id = match.group(1)
            else:
                logger.error(f"❌ Could not extract File ID from Drive link: {drive_link}")
                return
                
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        
        # Ensure the directory exists
        save_path = f"/home/praveen/marketing-agent/downloads/resumes/{lead_id}_resume.pdf"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Download the file
        response = requests.get(download_url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"✅ Successfully downloaded resume for Lead #{lead_id}")
            
            # Process the downloaded file
            process_resume(lead_id, save_path)
        else:
            logger.error(f"❌ Failed to download PDF from Drive. Status code: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Failed to process resume for lead {lead_id}: {e}")

def build_main_menu() -> str:
    return ("👋 Welcome to Career Solutions!\n\nPlease select an option:\n1️⃣ I am a Student / Job Seeker / Learner\n2️⃣ I am looking for Projects / Services\n3️⃣ I am an HR / Manager looking to hire\n4️⃣ Know about us\n5️⃣ I want to talk to an Admin / Manager\n\nReply with the number (1-5).")

def handle_dm_message(igsid: str, username: str, message_text: str, lead: dict):
    try:
        state = get_menu_state(lead)
        current_menu = state.get("current_menu", "main")
        history = state.get("history", [])
        data = state.get("data", {})
        msg = message_text.strip().lower()

        if msg in GREETINGS:
            state.update({"current_menu": "main", "history": [], "data": {}})
            save_menu_state(lead["id"], state)
            send_instagram_dm(igsid, build_main_menu(), lead=lead)
            update_lead_fields(lead["id"], qualification_status="dm_sent")
            return

        if current_menu == "main":
            if msg in ("1", "1️⃣"):
                state["current_menu"] = "student"
                state["history"].append("main")
                send_instagram_dm(igsid, "🎓 Great! Are you looking for:\n1️⃣ A Course\n2️⃣ An Internship\n3️⃣ A Job Placement" + NAV_FOOTER, lead=lead)
                save_menu_state(lead["id"], state)
                
            elif msg in ("2", "2️⃣", "3", "3️⃣", "5", "5️⃣"):
                state["current_menu"] = "collect_other_info"
                state["history"].append("main")
                
                if "2" in msg:
                    update_lead_fields(lead["id"], qualification_status="project_inquiry")
                    prompt = "💻 Please type your WhatsApp number and a brief description of your project."
                elif "3" in msg:
                    update_lead_fields(lead["id"], qualification_status="hr_inquiry")
                    prompt = "🤝 Please type your WhatsApp number, Company Name, and Designation."
                else:
                    update_lead_fields(lead["id"], qualification_status="admin_inquiry")
                    prompt = "📞 Please type your WhatsApp number and your reason for contacting."
                    
                send_instagram_dm(igsid, prompt + NAV_FOOTER, lead=lead)
                save_menu_state(lead["id"], state)
            else: 
                send_instagram_dm(igsid, "Please select a valid option or type 'home'.\n\n" + build_main_menu(), lead=lead)

        elif current_menu == "student" and msg in ("1", "2", "3"):
            choice_map = {"1": "Course", "2": "Internship", "3": "Job Placement"}
            data["domain"] = choice_map[msg]
            state["current_menu"] = "collect_phone"
            state["data"] = data
            state["history"].append("student")
            save_menu_state(lead["id"], state)
            
            send_instagram_dm(igsid, "To securely link your profile, please type your WhatsApp Phone Number (e.g., 9876543210):" + NAV_FOOTER, lead=lead)
            
        elif current_menu == "collect_phone":
            interested = data.get("domain", "Unknown")
            phones = re.findall(r'\d{10}', msg)
            phone_val = phones[0] if phones else None
            
            if not phone_val:
                send_instagram_dm(igsid, "Please enter a valid 10-digit WhatsApp number.", lead=lead)
                return
            
            update_lead_fields(lead["id"], phone=phone_val, interested_course=interested, qualification_status="number_received")
            update_lead_score(lead["id"], 20, f"Interested in {interested}")
            
            final_message = f"✅ Perfect! Now, please click the LINK IN OUR BIO to upload your resume. We will automatically link it to this number!"
            dm_success = send_instagram_dm(igsid, final_message, lead=lead)
            
            if dm_success:
                state["current_menu"] = "done"
                save_menu_state(lead["id"], state)
                append_lead(lead["id"], "Leads")

        elif current_menu == "collect_other_info":
            phones = re.findall(r'\d{10}', msg)
            phone_val = phones[0] if phones else None
            
            lead = update_lead_fields(lead["id"], phone=phone_val, notes=f"User Details: {msg}")
            send_instagram_dm(igsid, "✅ Thank you! Your details have been recorded. Our team will reach out to you shortly.", lead=lead)
            
            state["current_menu"] = "done"
            save_menu_state(lead["id"], state)
            append_lead(lead["id"], "Leads")
            send_telegram_alert(lead, "🔔 New Non-Student Inquiry", f"Type: {lead.get('qualification_status')}\nDetails: {msg}")

        elif current_menu == "done":
            send_instagram_dm(igsid, "Your request is recorded. Type 'home' to start over.", lead=lead)

    except Exception as e:
        logger.error(f"🚨 FATAL ERROR in handle_dm_message: {str(e)}", exc_info=True)

def process_instagram_webhook(data: dict):
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") == "comments":
                    val = change.get("value", {})
                    username = val.get("from", {}).get("username", "unknown")
                    igsid = val.get("from", {}).get("id")
                    text = val.get("text", "")
                    comment_id = val.get("id")

                    if username.lower() == OUR_IG_USERNAME: continue
                    if not igsid: igsid = f"temp_cmnt_{comment_id}"
                    if is_event_processed(comment_id): continue
                    mark_event_processed(comment_id, "instagram", val)

                    intent = call_deepseek(f"Classify this Instagram comment as 'casual' or 'intent'. 'Intent' means asking about courses, fees, AI, etc. Return ONLY the word 'casual' or 'intent'. Comment: '{text}'")
                    
                    if "intent" in intent:
                        send_instagram_public_reply(comment_id, "Thanks for reaching out! Please check your DMs.")
                        lead = get_or_create_lead_by_igsid(igsid, social_username=username, source_post=comment_id)
                        update_lead_fields(lead["id"], last_comment_id=comment_id, qualification_status="new_lead")
                        update_lead_score(lead["id"], 30, "High-intent comment")
                        save_menu_state(lead["id"], {"current_menu": "main", "history": [], "data": {}})
                        send_instagram_dm(comment_id, f"Hi @{username}!\n\n{build_main_menu()}", is_comment_reply=True)

            for msg_event in entry.get("messaging", []):
                if msg_event.get("message", {}).get("is_echo"): continue
                
                message_id = msg_event.get("message", {}).get("mid")
                if not message_id or is_event_processed(message_id): continue
                mark_event_processed(message_id, "instagram", msg_event)

                igsid = msg_event.get("sender", {}).get("id")
                message_text = msg_event.get("message", {}).get("text", "")
                if not message_text: continue

                lead = get_or_create_lead_by_igsid(igsid)
                if not lead.get("menu_state"):
                    initial_state = {"current_menu": "main", "history": [], "data": {}}
                    save_menu_state(lead["id"], initial_state)
                    lead["menu_state"] = initial_state 
                    update_lead_fields(lead["id"], qualification_status="new_lead")

                handle_dm_message(igsid, lead.get("social_username", "User"), message_text, lead)
    except Exception as e:
        logger.error(f"🚨 Top-level webhook processing crash: {e}", exc_info=True)

# ==================== ENDPOINTS ====================
@app.get("/webhook")
async def verify(request: Request):
    if request.query_params.get("hub.mode") == "subscribe": return int(request.query_params.get("hub.challenge"))
    raise HTTPException(403, "Verification failed")

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks, x_hub_signature_256: str = Header(None)):
    try: payload_bytes = await request.body()
    except Exception: return {"status": "error"}

    if not verify_meta_signature(payload_bytes, x_hub_signature_256): raise HTTPException(status_code=403, detail="Invalid signature")
    try: data = json.loads(payload_bytes.decode('utf-8'))
    except Exception: return {"status": "error"}
        
    background_tasks.add_task(process_instagram_webhook, data)
    return {"status": "ok"}

@app.post("/form-webhook")
async def form_webhook(request: Request, background_tasks: BackgroundTasks):
    try: data = await request.json()
    except Exception: return {"status": "error"}
    phone = data.get("phone")
    drive_link = data.get("resume_link")
    if not phone or not drive_link: return {"status": "error"}
    
    background_tasks.add_task(process_form_resume, phone, drive_link)
    return {"status": "received"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
