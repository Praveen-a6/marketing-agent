"""
db_client.py - Centralized PostgreSQL access with menu state helpers.
"""
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "configs", ".env"))

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager

logger = logging.getLogger("db_client")
logging.basicConfig(level=logging.INFO)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "marketing_agent")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT", "5432")

if not DB_USER:
    raise RuntimeError("DB_USER environment variable is required. Check your .env file.")

_pool = pool.ThreadedConnectionPool(
    minconn=1, maxconn=10,
    host=DB_HOST, dbname=DB_NAME,
    user=DB_USER, password=DB_PASSWORD, port=DB_PORT,
)

@contextmanager
def get_conn():
    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)

@contextmanager
def get_cursor():
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cur
        finally:
            cur.close()

# ==================== IDEMPOTENCY ====================
def is_event_processed(event_id: str) -> bool:
    with get_cursor() as cur:
        cur.execute("SELECT 1 FROM webhook_events WHERE event_id = %s", (event_id,))
        return cur.fetchone() is not None

def mark_event_processed(event_id: str, platform: str, payload: dict) -> bool:
    with get_cursor() as cur:
        try:
            cur.execute(
                "INSERT INTO webhook_events (event_id, platform, payload) VALUES (%s, %s, %s) ON CONFLICT (event_id) DO NOTHING RETURNING id",
                (event_id, platform, Json(payload))
            )
            return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"mark_event_processed failed: {e}")
            return False

# ==================== LEAD MANAGEMENT ====================
def get_or_create_lead_by_igsid(igsid: str, source_platform: str = "instagram",
                                  social_username: str = None, source_post: str = None):
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO leads (igsid, source_platform, social_username, source_post, lead_status)
            VALUES (%s, %s, %s, %s, 'new')
            ON CONFLICT (igsid) WHERE igsid IS NOT NULL
            DO UPDATE SET
                social_username = COALESCE(EXCLUDED.social_username, leads.social_username),
                updated_at = CURRENT_TIMESTAMP
            RETURNING *
            """,
            (igsid, source_platform, social_username, source_post)
        )
        return cur.fetchone()

def get_lead_by_igsid(igsid: str):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM leads WHERE igsid = %s", (igsid,))
        return cur.fetchone()

def get_lead(lead_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM leads WHERE id = %s", (lead_id,))
        return cur.fetchone()

def update_lead_fields(lead_id: int, **fields):
    allowed = {
        "full_name", "phone", "email", "college_name", "degree",
        "year_of_study", "interested_course", "career_goal",
        "lead_status", "qualification_status", "qualification_reason",
        "assigned_to", "notes", "qualification_step",
        "conversation_summary", "last_comment_id", "last_message_id",
        "last_interaction_at", "menu_state"
    }
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return None
    # Convert menu_state to JSON string if present
    if "menu_state" in fields and isinstance(fields["menu_state"], dict):
        fields["menu_state"] = Json(fields["menu_state"])
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [lead_id]
    with get_cursor() as cur:
        cur.execute(
            f"UPDATE leads SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING *",
            values
        )
        return cur.fetchone()

def update_lead_score(lead_id: int, score_delta: int, reason: str = None):
    with get_cursor() as cur:
        cur.execute(
            """
            UPDATE leads
            SET lead_score = LEAST(100, GREATEST(0, COALESCE(lead_score, 0) + %s)),
                qualification_reason = COALESCE(%s, qualification_reason),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING *
            """,
            (score_delta, reason, lead_id)
        )
        return cur.fetchone()

# ==================== PROJECTS ====================
def insert_project(lead_id: int, project_data: dict):
    allowed = ["project_type", "description", "budget_estimate", "timeline", "requirements"]
    data = {k: v for k, v in project_data.items() if k in allowed}
    if not data:
        return None
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    values = list(data.values())
    with get_cursor() as cur:
        cur.execute(
            f"INSERT INTO projects (lead_id, {cols}) VALUES (%s, {placeholders}) RETURNING *",
            [lead_id] + values
        )
        return cur.fetchone()

# ==================== MENU STATE HELPERS ====================
def get_menu_state(lead: dict) -> dict:
    """Retrieve menu state as dict, initialise if empty."""
    state = lead.get("menu_state")
    if isinstance(state, dict):
        return state
    if isinstance(state, str):
        try:
            return json.loads(state)
        except:
            pass
    return {"current_menu": "main", "history": [], "data": {}}

def save_menu_state(lead_id: int, state: dict):
    """Persist menu state."""
    update_lead_fields(lead_id, menu_state=state)

def close_pool():
    _pool.closeall()
