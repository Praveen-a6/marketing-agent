import os
import sys
import traceback
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
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def append_lead(lead_id, sheet_name="Leads"):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        query = """
            SELECT id, full_name, social_username, phone, email,
                   interested_course, college_name, lead_score,
                   qualification_status, notes, created_at
            FROM leads WHERE id = %s
        """
        cur.execute(query, (lead_id,))
        lead = cur.fetchone()
        conn.close()
        
        if not lead:
            print(f"❌ Lead {lead_id} not found in database.")
            return

        row = [
            lead.get("id", ""),
            lead.get("full_name", ""),
            lead.get("social_username", ""),
            lead.get("phone", ""),
            lead.get("email", ""),
            lead.get("interested_course", ""),
            lead.get("college_name", ""),
            lead.get("lead_score", ""),
            lead.get("qualification_status", ""),
            lead.get("notes", ""),
            str(lead.get("created_at", ""))
        ]
        headers = ["ID", "Name", "Username", "Phone", "Email", "Course", "College", "Score", "Status", "Notes", "Created"]

        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID)
        
        try:
            worksheet = sheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            print(f"⚠️ Tab '{sheet_name}' not found. Falling back to the first tab (index 0).")
            worksheet = sheet.get_worksheet(0)
        
        if not worksheet.get_all_values():
            worksheet.append_row(headers)
            
        worksheet.append_row([str(v) if v is not None else "" for v in row])
        print(f"✅ Lead {lead_id} appended to Google Sheets ({worksheet.title})")

    except Exception as e:
        print(f"❌ Append failed for Lead {lead_id}: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 2:
        append_lead(int(sys.argv[1]), sys.argv[2])
    elif len(sys.argv) > 1:
        append_lead(int(sys.argv[1]), "Leads")
    else:
        print("Usage: python sheets_append.py <lead_id> [sheet_name]")
