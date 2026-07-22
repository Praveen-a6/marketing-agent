import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '../configs/instagram.env')
load_dotenv(dotenv_path=env_path)

class MarketingDB:
    def __init__(self):
        self.conn_str = os.getenv("DATABASE_URL")
        if not self.conn_str:
            raise ValueError("DATABASE_URL not found in environment")

    def _get_connection(self):
        return psycopg2.connect(self.conn_str, cursor_factory=RealDictCursor)

    def execute_query(self, query, params=None, fetch=False):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    if fetch:
                        return cur.fetchall()
                    conn.commit()
                    return {"status": "success", "message": "Transaction committed."}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def insert_lead(self, full_name, platform, username, email=None, phone=None, text=None):
        query = """
        INSERT INTO leads (full_name, source_platform, social_username, email, phone, notes, lead_status)
        VALUES (%s, %s, %s, %s, %s, %s, 'new')
        RETURNING id, full_name, source_platform, social_username;
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (full_name, platform, username, email, phone, text))
                    result = cur.fetchone()
                    conn.commit()
                    return result
        except Exception as e:
            print(f"DB insert error: {e}")
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
            print(f"Update score error: {e}")
            return None

    def get_pending_leads(self):
        query = "SELECT * FROM leads WHERE lead_status = 'new' ORDER BY created_at ASC;"
        return self.execute_query(query, fetch=True)
