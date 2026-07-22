name: instagram_reply
description: Reply to Instagram comments or DMs from leads.
user-invocable: true
metadata:
  openclaw:
    requires:
      envs: [INSTAGRAM_ACCESS_TOKEN, DATABASE_URL]

# Usage
- Command: `/reply <lead_id> <message>`
- Example: `/reply 5 "Thanks for your interest! Please check your DMs."`

# Steps
1. Fetch lead by ID from PostgreSQL.
2. If lead has `comment_id`, reply to that comment using Instagram Graph API.
3. If lead has `sender_id`, reply to that DM using Instagram Graph API.
4. Update lead status to `replied`.
5. Return success or error.

# Guardrails
- Always confirm the lead exists and has either comment_id or sender_id.
- Do not reply more than once; check lead_status to prevent duplicates.
- Maximum message length: 1000 characters.
