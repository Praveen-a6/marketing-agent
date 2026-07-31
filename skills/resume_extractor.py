import os
import sys
import json
import subprocess
import pdfplumber
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", "configs", "instagram.env")
load_dotenv(env_path)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ADMIN_IDS = [i.strip() for i in os.getenv("TELEGRAM_ADMIN_IDS", "").split(",") if i.strip()]
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "database"))
from db_client import update_lead_fields, update_lead_score, get_lead

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
    except Exception as e: print(f"Error reading PDF: {e}")
    return text

def parse_resume_with_ai(resume_text: str) -> dict:
    prompt = f"""
    You are a data extraction agent. Extract the following from the provided resume text.
    Return ONLY a valid JSON object. No markdown formatting.
    
    Expected JSON schema:
    {{
        "email": "string or null",
        "passout_year": "string or null",
        "years_experience": "integer or 0",
        "ai_summary": "A concise 2-sentence summary of the candidate's core profile, skills, and experience level."
    }}
    
    Resume Text:
    {resume_text[:4000]}
    """
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}
    try:
        res = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=15)
        text = res.json()["choices"][0]["message"]["content"].strip()
        if text.startswith("```json"): text = text[7:-3].strip()
        return json.loads(text)
    except Exception as e: return {}

def send_unified_hot_lead_alert(lead: dict, pdf_path: str, extracted_data: dict):
    caption = (
        f"🔥 <b>HOT LEAD RESUME RECEIVED</b> (Lead #{lead.get('id')})\n\n"
        f"👤 <b>Handle:</b> @{lead.get('social_username', 'N/A')}\n"
        f"📞 <b>Phone:</b> {lead.get('phone', 'N/A')}\n"
        f"📧 <b>Email:</b> {extracted_data.get('email', 'N/A')}\n"
        f"🎯 <b>Interested Course:</b> {lead.get('interested_course', 'N/A')}\n"
        f"⭐ <b>Lead Score:</b> {lead.get('lead_score', 0)}/100\n\n"
        f"📝 <b>AI Summary:</b> {extracted_data.get('ai_summary', 'N/A')}"
    )

    for admin_id in TELEGRAM_ADMIN_IDS:
        try:
            if os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as doc:
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
                        data={"chat_id": admin_id, "caption": caption, "parse_mode": "HTML"},
                        files={"document": doc},
                        timeout=15
                    )
        except Exception as e: print(f"Telegram push failed: {e}")

def send_success_dm(igsid: str):
    url = "https://graph.facebook.com/v25.0/me/messages"
    payload = {
        "recipient": {"id": igsid}, 
        "message": {"text": "✅ We received your resume! Our team will review your profile and connect with you shortly. Thank you for your interest in Career Solutions!"}
    }
    try:
        requests.post(url, headers={"Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"}, json=payload, timeout=15)
    except Exception as e:
        print(f"Failed to send success DM: {e}")

def process_resume(lead_id: int, pdf_path: str):
    print(f"Processing resume for Lead ID: {lead_id}")
    raw_text = extract_text_from_pdf(pdf_path)
    extracted_data = parse_resume_with_ai(raw_text) if raw_text else {}
    
    # 1. Fetch existing lead to avoid overwriting primary DM data
    lead_info = get_lead(lead_id)
    if not lead_info: return
    
    # 2. Compile secondary AI summary and append to existing notes
    existing_notes = lead_info.get("notes") or ""
    new_notes = f"{existing_notes}\n[AI Extraction]: Passout: {extracted_data.get('passout_year')}, Exp: {extracted_data.get('years_experience')} yrs\n[AI Summary]: {extracted_data.get('ai_summary')}".strip()
    
    # 3. Update fields (preserving DM inputs)
    update_lead_fields(
        lead_id,
        email=extracted_data.get("email") or lead_info.get("email"),
        notes=new_notes,
        qualification_status="resume_received"
    )
    
    # 4. Add Resume Submission Score Bump (+30)
    update_lead_score(lead_id, 30, "Resume Parsed and Summarized")
    
    # 5. Re-fetch for accurate Telegram alerting and DMs
    updated_lead = get_lead(lead_id)
    score = updated_lead.get("lead_score", 0)
    
    # Send Instagram Confirmation DM
    if updated_lead.get("igsid"):
        send_success_dm(updated_lead["igsid"])
    
    # Send Telegram Alert if hot lead
    if score >= 50 or updated_lead.get("qualification_status") == "resume_received":
        send_unified_hot_lead_alert(updated_lead, pdf_path, extracted_data)
        # Set strict hot lead status
        update_lead_fields(lead_id, qualification_status="hot_lead_pinged")
        
    # 6. Instantly Sync Database to Google Sheets
    try:
        subprocess.Popen(["python3", "/home/praveen/marketing-agent/skills/sheets_sync.py"])
    except Exception as e:
        print(f"Failed to trigger sheets sync: {e}")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        process_resume(int(sys.argv[1]), sys.argv[2])
