#!/usr/bin/env python3
import os
import sys
import requests
from dotenv import load_dotenv

# Load environments and database module
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "configs", "instagram.env"), override=True)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "database"))

from db_client import get_lead, update_lead_fields

INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

def reply_to_comment(comment_id, message):
    url = f"https://graph.instagram.com/v25.0/{comment_id}/replies"
    payload = {"message": message, "access_token": INSTAGRAM_ACCESS_TOKEN}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def reply_to_dm(igsid, message):
    url = "https://graph.instagram.com/v25.0/me/messages"
    payload = {
        "recipient": {"id": igsid},
        "message": {"text": message},
        "access_token": INSTAGRAM_ACCESS_TOKEN
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def main():
    if len(sys.argv) < 3:
        print("Usage: python instagram_reply.py <lead_id> <message>")
        sys.exit(1)

    lead_id = int(sys.argv[1])
    message = " ".join(sys.argv[2:])

    lead = get_lead(lead_id)
    if not lead:
        print(f"❌ Lead {lead_id} not found in database.")
        sys.exit(1)

    # Determine if it's a DM or comment reply based on the new schema
    result = {}
    
    # Always prefer DM if we have their IGSID
    if lead.get('igsid'):
        result = reply_to_dm(lead['igsid'], message)
        print(f"Reply via DM: {result}")
    
    # Fallback to public comment reply if no DM thread exists yet
    elif lead.get('last_comment_id') or lead.get('comment_id'):
        target_comment = lead.get('last_comment_id') or lead.get('comment_id')
        result = reply_to_comment(target_comment, message)
        print(f"Reply to comment: {result}")
    
    else:
        print("❌ No igsid or comment_id found for this lead; cannot reply.")
        sys.exit(1)

    # Update database if the API call was successful
    if result.get('id') or result.get('message_id') or result.get('success'):
        update_lead_fields(lead_id, lead_status='replied')
        print("✅ Reply sent and status updated successfully.")
    else:
        print(f"❌ Reply failed: {result}")

if __name__ == "__main__":
    main()
