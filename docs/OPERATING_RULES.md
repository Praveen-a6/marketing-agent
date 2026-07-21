# Operating Rules & Guardrails (OpenClaw Specific)

These are absolute rules enforced at the agent/system level.

---

## 1. Source of Truth
- Repository and PostgreSQL are the **source of truth**.
- OpenClaw is an **ephemeral execution layer**.

---

## 2. Allowed Actions (No Approval)
- Read files in `/home/praveen/marketing-agent`.
- Read `knowledge/*.md`.
- Generate drafts.
- Search CRM (SELECT queries).

---

## 3. Actions Requiring Explicit Approval
- Sending any message (WhatsApp, Instagram DM, Telegram).
- Publishing content.
- INSERT/UPDATE/DELETE on PostgreSQL.
- Writing to critical files (`openclaw.json`, `schema.sql`, `.env`).
- Running shell commands outside `~/marketing-agent`.
- Installing packages.

---

## 4. Strictly Forbidden
- Auto-sending WhatsApp messages (even drafts).
- Auto-overwriting important files without confirmation.
- Running shell commands outside `~/marketing-agent`.
- Bypassing CAPTCHA, MFA, or bot detection.
- Scraping private/authenticated data.
- Using personal social accounts.

---

## 5. Approval Protocol
1. Agent generates draft.
2. Sends to Telegram with Action ID.
3. Human replies `APPROVE <id>` or `REJECT <id>`.
4. Executes only after approval.
5. Logs to `logs/actions.md`.

---

## 6. Role-Based Access
| Role | Permissions |
|------|-------------|
| Admin | Full access |
| Placement Officer | View leads, update status |
| Marketing Executive | View leads, content drafts |
