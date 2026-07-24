name: lead_digest
description: Fetches a batched summary of leads captured in the last 3 hours from PostgreSQL.
user-invocable: true

# Usage
- Command: `/digest`

# Steps
1. Query PostgreSQL:
   `SELECT id, full_name, social_username, interested_course, lead_score, phone, qualification_reason FROM leads WHERE created_at >= NOW() - INTERVAL '3 hours' ORDER BY lead_score DESC;`
2. If 0 rows are returned, output:
   "📊 **3-Hour Lead Digest Report**\n\nℹ️ *No new leads captured in the last 3 hours.*"
3. If rows exist, output a formatted table showing Lead ID, Username, Course, Score, and Phone number.
