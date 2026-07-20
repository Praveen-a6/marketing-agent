# Marketing-Agent Database

## Purpose

PostgreSQL is the permanent memory layer for Marketing-Agent.

The database stores:

* Student leads
* Companies
* HR contacts
* Campaigns
* Tasks
* Agent memory

OpenClaw is not the source of truth.

The database is the source of truth.

---

## Planned Tables

students

companies

hr_contacts

campaigns

tasks

agent_memory

---

## Rules

* No table deletion without approval
* No schema changes without approval
* No database reset without approval

---

## Future Deployment

Database engine:

PostgreSQL

Deployment:

Docker

Backup strategy:

Daily backups
