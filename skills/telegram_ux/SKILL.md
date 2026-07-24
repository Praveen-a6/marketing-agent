name: telegram_ux
description: Explains the digital marketing system, commands, and workflows to the human operators.
user-invocable: true

# Usage
- Command: `/manual` or "How does this bot work?"

# Steps
1. When the user invokes this command, output the following formatted text exactly as written below. Do not alter the formatting.

---

🤖 **Marketing-Agent OS: Team Manual** 🤖
Welcome to the Career Solutions Operations Hub. Here is how our automated lead engine works:

**1. 📥 Inbound Flow (Instagram)**
- When a user comments on our IG, the system catches it instantly.
- The AI Engine evaluates the text. If it scores **>= 70**, you will receive an instant 🔥 **HOT LEAD ALERT** right here in Telegram.
- Leads scoring < 70 are quietly saved to our CRM for nurturing.

**2. 🛠️ Your Daily Commands**
Reply directly to me with any of these commands to operate the system:

- `/digest` : Fetches a summary of all warm leads (Score 30-69) from the database that haven't been contacted yet.
- `/reply <Lead_ID> "<Message>"` : Commands me to use the Meta API to reply to the user's comment/DM directly. (e.g., `/reply 14 "Thanks! Just sent you a DM."`)
- `/stats` : Generates a quick daily tally of total leads captured vs. leads contacted.

**3. 🛑 Guardrails & Safety**
- I will **never** send an outbound message, publish a post, or alter a campaign without your explicit command.
- All lead data is permanently secured in our PostgreSQL database.

---
