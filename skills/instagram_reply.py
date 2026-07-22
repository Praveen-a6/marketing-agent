#!/usr/bin/env python3
import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import requests

env_path = os.path.join(os.path.dirname(__file__), '../configs/instagram.env')
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def get_lead(lead_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM leads WHERE id = %s;", (lead_id,))
            return cur.fetchone()

def update_lead_status(lead_id, status):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE leads SET lead_status = %s WHERE id = %s;", (status, lead_id))
            conn.commit()

def reply_to_comment(comment_id, message):
    url = f"https://graph.instagram.com/v25.0/{comment_id}/replies"
    params = {"message": message, "access_token": INSTAGRAM_ACCESS_TOKEN}
    resp = requests.post(url, data=params)
    return resp.json()

def reply_to_dm(sender_id, message):
    # Instagram DM endpoint (conversation)
    url = f"https://graph.instagram.com/v25.0/me/messages"
    params = {
        "recipient": {"id": sender_id},
        "message": {"text": message},
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    resp = requests.post(url, json=params)
    return resp.json()

def main():
    if len(sys.argv) < 3:
        print("Usage: python instagram_reply.py <lead_id> <message>")
        sys.exit(1)

    lead_id = int(sys.argv[1])
    message = " ".join(sys.argv[2:])

    lead = get_lead(lead_id)
    if not lead:
        print(f"Lead {lead_id} not found.")
        sys.exit(1)

    # Determine if it's a comment or DM
    if lead.get('comment_id'):
        result = reply_to_comment(lead['comment_id'], message)
        print(f"Reply to comment: {result}")
    elif lead.get('sender_id'):
        result = reply_to_dm(lead['sender_id'], message)
        print(f"Reply to DM: {result}")
    else:
        print("No comment_id or sender_id found; cannot reply.")
        sys.exit(1)

    if result.get('id') or result.get('success'):
        update_lead_status(lead_id, 'replied')
        print("Reply sent successfully.")
    else:
        print(f"Reply failed: {result}")

if __name__ == "__main__":
    main()
