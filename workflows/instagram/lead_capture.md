cat > ~/marketing-agent/workflows/instagram/lead_capture.md <<'EOF'
# Instagram Lead Capture Workflow

## Trigger
- Instagram comment
- Instagram mention
- Instagram DM (if permissions available)

---

## 1. Comment Classification

### A. General Engagement
- **Keywords:** "Nice", "Great", "Awesome", "Good work", "Interesting"
- **Action:** Public reply only. Do NOT create a lead. Do NOT send DM.

### B. Interest
- **Keywords:** "Interested", "Course details", "Tell me more", "Info", "Price", "Details"
- **Action:**
  - Public reply: *"Thanks for your interest. Please check your DMs."*
  - Send qualification DM (or save draft for human approval).
  - Create a lead record with `lead_status = 'new'`.

### C. Lead Intent
- **Keywords:** "Need AI training", "Want internship", "Job ready", "Placement support", "Looking for"
- **Action:**
  - Public reply: *"Thanks for reaching out. We'll connect with you shortly."*
  - Create a lead record with `lead_status = 'new'`.
  - Assign `lead_score` via scoring rules.
  - Trigger Lead Enrichment.
  - Send Telegram alert (if score ≥ 50).

---

## 2. Qualification Questions (DM Sequence)
Send these questions one by one:
1. What is your full name?
2. What is your phone number?
3. Which college are you studying in?
4. What degree are you pursuing?
5. Which year of study?
6. Which course are you interested in? (AI/ML, Data Science, Full Stack, Cybersecurity, Data Analytics)
7. What is your career goal?

---

## 3. Lead Creation Rules
Create CRM lead when:
- Contact details are received.
- Student expresses training/internship/placement interest.
- Any qualification question is answered.

---

## 4. Human Takeover (Telegram Digest)
If the bot detects:
- More than 2 complex questions unanswered.
- Questions about fees or certifications.
- Conversation exceeds 2 exchanges without resolution.

**Then:** Send a single Telegram digest to Admin + Marketing Team with:
- Lead Name
- Platform (Instagram)
- Summary of conversation
- Reason for takeover
- Action: "Please take over manually via CRM."

---

## 5. Escalation
High-intent leads (score ≥ 50) must be assigned to staff for follow-up immediately.
EOF
