#!/usr/bin/env python3
"""
sheets_pull_status.py – Syncs manual status updates from Google Sheets back into PostgreSQL.
Validates against a strict predefined list of operational statuses.
"""
import os
import sys
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '../configs/instagram.env')
load_dotenv(dotenv_path=env_path)

CREDS_PATH = os.path.join(os.path.dirname(__file__), '../configs/google_credentials.json')
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
DATABASE_URL = os.getenv("DATABASE_URL")
SCOPE = ["[https://spreadsheets.google.com/feeds](https://spreadsheets.google.com/feeds)", "[https://www.googleapis.com/auth/drive](https://www.googleapis.com/auth/drive)"]

# Strict Enum Definition
VALID_STATUSES = {
    "new_lead", 
    "dm_sent", 
    "number_received", 
    "resume_received", 
    "hot_lead_pinged", 
    "project_inquiry", 
    "hr_inquiry", 
    "admin_inquiry",
    "replied",
    "nurture",
    "closed"
}

def pull_status_updates():
    if not os.path.exists(CREDS_PATH):
        print("❌ Error: google_credentials.json not found.")
        return

    print("🔄 Checking Google Sheets for status updates...")
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
    
    records = sheet.get_all_records()
    if not records:
        print("ℹ️ No records found in spreadsheet.")
        return

    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        updated_count = 0

        for row in records:
            lead_id = row.get("ID") or row.get("Lead ID")
            sheet_status = str(row.get("Status") or row.get("qualification_status")).strip().lower()

            if not lead_id or not sheet_status:
                continue

            # Validate against exact dropdown options
            if sheet_status not in VALID_STATUSES:
                print(f"⚠️ Invalid status '{sheet_status}' for Lead #{lead_id}. Skipping.")
                continue

            # Compare with current DB status
            cur.execute("SELECT qualification_status FROM leads WHERE id = %s", (int(lead_id),))
            db_lead = cur.fetchone()

            if db_lead and db_lead["qualification_status"] != sheet_status:
                cur.execute(
                    "UPDATE leads SET qualification_status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (sheet_status, int(lead_id))
                )
                updated_count += 1
                print(f"✅ Lead #{lead_id} status updated to '{sheet_status}' in DB.")

        conn.commit()
        conn.close()
        print(f"🎉 Sync complete. {updated_count} lead status(es) updated in PostgreSQL.")

    except Exception as e:
        print(f"❌ Status pull failed: {e}")

if __name__ == "__main__":
    pull_status_updates()
