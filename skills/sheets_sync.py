import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment
env_path = os.path.join(os.path.dirname(__file__), '../configs/instagram.env')
load_dotenv(dotenv_path=env_path)

# Configuration
CREDS_PATH = os.path.join(os.path.dirname(__file__), '../configs/google_credentials.json')
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
DATABASE_URL = os.getenv("DATABASE_URL")
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def sync_database_to_sheets():
    if not os.path.exists(CREDS_PATH):
        print("❌ Error: google_credentials.json not found in configs directory.")
        return

    print("🔄 Connecting to Google Sheets...")
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1

    print("🔄 Fetching data from PostgreSQL...")
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Select the most important fields for the team to review
        query = """
            SELECT 
                id, TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') as date, 
                full_name, social_username, phone, email, 
                college_name, degree, interested_course, 
                lead_score, qualification_status, qualification_reason 
            FROM leads 
            ORDER BY created_at DESC;
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        if not rows:
            print("ℹ️ No leads found in database.")
            return

        # Prepare data matrix
        headers = list(rows[0].keys())
        data_matrix = [headers]
        
        for row in rows:
            data_matrix.append([str(row[key]) if row[key] is not None else "" for key in headers])

        # Push to Google Sheets (clears old data and writes new matrix)
        print("🔄 Pushing updates to spreadsheet...")
        sheet.clear()
        sheet.update(values=data_matrix, range_name='A1')
        print(f"✅ Successfully synced {len(rows)} leads to Google Sheets.")
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    sync_database_to_sheets()
