#!/usr/bin/env python3
"""
Scheduled Follow-ups - Runs via cron to recover abandoned leads.
Sends exactly ONE reminder after 4 hours of inactivity.
"""
import os
import sys
import logging
import requests
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load config
load_dotenv_path = os.path.join(os.path.dirname(__file__), "..", "configs", "instagram.env")
load_dotenv(load_dotenv_path, override=True)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("scheduled_followups")

INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
GOOGLE_FORM_LINK = os.getenv("GOOGLE_FORM_LINK", "https://forms.gle/93faSYNWzYbQ4t4r8")

def send_instagram_dm(recipient_id: str, message: str) -> bool:
    url = "https://graph.facebook.com/v25.0/me/messages"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": message}}
    try:
        res = requests.post(url, headers={"Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"}, json=payload, timeout=8)
        return res.status_code in (200, 201)
    except Exception as e:
        logger.error(f"DM send exception: {e}")
        return False

def run_followups():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # ==========================================
        # 1. RESUME ABANDONMENT (Stuck at Form Link)
        # ==========================================
        # Find leads waiting for resume, idle for > 4 hours, but less than 24 hours (don't message ancient leads)
        cur.execute("""
            SELECT id, igsid, social_username 
            FROM leads 
            WHERE qualification_status = 'waiting_for_resume' 
              AND updated_at <= NOW() - INTERVAL '4 hours'
              AND updated_at >= NOW() - INTERVAL '24 hours'
              AND igsid IS NOT NULL;
        """)
        resume_dropoffs = cur.fetchall()
        
        for lead in resume_dropoffs:
            msg = (f"Hi @{lead['social_username']}! 👋\n\n"
                   f"Just a quick reminder to complete your profile by uploading your resume using the link in our bio\n\n"
                   f"This allows us to fast-track your application. Let us know if you need any help!")
            
            if send_instagram_dm(lead['igsid'], msg):
                cur.execute("UPDATE leads SET qualification_status = 'resume_reminder_sent', updated_at = NOW() WHERE id = %s", (lead['id'],))
                logger.info(f"✅ Sent Resume Reminder to Lead #{lead['id']}")

        # ==========================================
        # 2. MENU ABANDONMENT (Stuck navigating)
        # ==========================================
        # Find leads who interacted > 4 hours ago, are NOT in a completed state, and haven't been reminded yet
        cur.execute("""
            SELECT id, igsid, social_username, menu_state 
            FROM leads 
            WHERE (qualification_status IS NULL OR qualification_status = 'new')
              AND updated_at <= NOW() - INTERVAL '4 hours'
              AND updated_at >= NOW() - INTERVAL '24 hours'
              AND igsid IS NOT NULL;
        """)
        menu_dropoffs = cur.fetchall()
        
        for lead in menu_dropoffs:
            state = lead.get('menu_state', {})
            current_menu = state.get('current_menu', 'main')
            
            # If they are stuck somewhere other than 'done'
            if current_menu not in ('done', 'collect_phone'):
                msg = (f"Hi @{lead['social_username']}! We noticed you started exploring our options but didn't finish.\n\n"
                       f"If you're still interested, simply reply with 'home' to see the main menu again, or let us know if you have any questions! 🚀")
                
                if send_instagram_dm(lead['igsid'], msg):
                    cur.execute("UPDATE leads SET qualification_status = 'menu_reminder_sent', updated_at = NOW() WHERE id = %s", (lead['id'],))
                    logger.info(f"✅ Sent Menu Reminder to Lead #{lead['id']}")

        conn.commit()
        conn.close()
        logger.info("🎉 Follow-up sweep completed successfully.")

    except Exception as e:
        logger.error(f"❌ Database/Execution Error: {e}")

if __name__ == "__main__":
    run_followups()
