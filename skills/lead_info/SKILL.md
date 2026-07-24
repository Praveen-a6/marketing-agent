name: lead_info
description: Fetches the complete detailed dossier for a specific lead ID from PostgreSQL.
user-invocable: true

# Usage
- Command: `/lead <id>` (Example: `/lead 4`)

# Steps
1. Parse the integer `<id>` from the user command.
2. Run query: `SELECT * FROM leads WHERE id = <id>;`
3. If no lead found, return: "❌ Lead #<id> not found in database."
4. If found, display in Markdown:

---
👤 **LEAD DOSSIER #<id>**
- **Full Name / Handle:** @{social_username}
- **Source Platform:** {source_platform}
- **Lead Score:** {lead_score}/100
- **Status:** {lead_status} | Tier: {qualification_status}

📞 **Contact Information**
- **Phone:** {phone or "Not provided"}
- **Email:** {email or "Not provided"}

🎓 **Academic & Career Details**
- **College:** {college_name or "Not provided"}
- **Degree:** {degree or "Not provided"} ({year_of_study or "N/A"})
- **Interested Course:** {interested_course}
- **Career Goal:** {career_goal or "N/A"}

📝 **Audit Notes & AI Reasoning**
- {qualification_reason}
- {notes}
---
