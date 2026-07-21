# Lead Qualification Engine

This is the core logic for processing all incoming leads.

---

## 1. Lead Sources
- `instagram` (comments, mentions, DMs)
- `whatsapp` (inbound messages)
- `telegram` (inbound messages)
- `web` (website forms)
- `referral` (existing students)

---

## 2. Incoming Message Classification

### A. General Engagement
- **Keywords:** "Nice", "Great", "Awesome", "Good work", "Interesting"
- **Action:** Public reply only. Do NOT create a lead. Do NOT send DM.

### B. Interest
- **Keywords:** "Interested", "Course details", "Tell me more", "Info"
- **Action:**
  - Public reply: *"Thanks for your interest. Please check your DMs."*
  - Send qualification DM (or save draft).
  - Create a lead record with `lead_status = 'new'`.

### C. Lead Intent
- **Keywords:** "Need AI training", "Want internship", "Job ready", "Placement support"
- **Action:**
  - Public reply: *"Thanks for reaching out. We'll connect with you shortly."*
  - Create a lead record with `lead_status = 'new'`.
  - Assign `lead_score`.
  - Trigger Lead Enrichment.
  - Send Telegram alert.

---

## 3. Lead Enrichment (New Phase)
After a lead is created, automatically run:
1. Search for the lead's college/company (if provided).
2. Check if they are a final-year student.
3. Look for any relevant social activity (if username is provided).
4. Update the CRM record with enriched data.
5. Recalculate lead score based on enrichment.

---

## 4. Lead Scoring (Assumed Best Fit)

| Factor | Points |
|--------|--------|
| Final Year Student | +20 |
| Pre-final Year Student | +10 |
| Graduate | +15 |
| Working Professional | +15 |
| AI/ML Interest | +15 |
| Data Science Interest | +15 |
| Data Analytics Interest | +10 |
| Full Stack Interest | +10 |
| Cybersecurity Interest | +10 |
| Course Enquiry | +10 |
| Internship Request | +20 |
| Placement Request | +25 |
| Phone Provided | +20 |
| Email Provided | +10 |

**Negative:**
- Spam: -100
- Incomplete: -10

---

## 5. Priority & Action

| Score | Priority | Action |
|-------|----------|--------|
| 0–20 | Low | Nurture |
| 21–50 | Medium | Follow up in 48 hrs |
| 51–100 | High | Immediate Telegram alert |

---

## 6. Human Takeover (Telegram Digest)
**If the bot detects:**
- Multiple DMs requiring human attention (≥2 complex questions).
- Questions about fees, certifications, or off-script courses.
- Conversation exceeds 2 exchanges without resolution.

**Then:**
The agent sends a **single Telegram digest** to Admin + Marketing Team listing:
- Lead Name
- Platform (Instagram/WhatsApp)
- Summary of conversation
- Reason for takeover
- Action: "Please take over manually via CRM."

---

## 7. Approval Rules
- Require explicit approval before sending any DM or WhatsApp reply.
- Draft → Approval → Send → Log.
