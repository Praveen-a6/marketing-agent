# Instagram Lead Capture Workflow

## Trigger
- Instagram comment
- Instagram mention
- Instagram DM

## 1. Comment Classification
### A. General Engagement
**Action:** Public reply only. Do NOT create a lead. Do NOT send DM.

### B. Interest
**Action:**
- Public reply: "Thanks for your interest. Please check your DMs."
- Send qualification DM.
- Create lead record (`lead_status = 'new'`).

### C. Lead Intent
**Action:**
- Public reply.
- Create lead record.
- Trigger Lead Enrichment.
- Send Telegram alert (if score >= 50).

## 2. Qualification Questions (DM Sequence)
1. Full name
2. Phone number
3. College name
4. Degree
5. Year of study
6. Interested course
7. Career goal

## 3. Human Takeover (Telegram Digest)
Trigger if:
- > 2 complex unanswered questions.
- Queries on fees/certifications.
- > 2 exchanges without resolution.
