name: lead_stats
description: Calculates total leads generated today and this week from PostgreSQL.
user-invocable: true

# Usage
- Command: `/stats`

# Steps
1. Query PostgreSQL for today's total: 
   `SELECT COUNT(*) as today_total FROM leads WHERE DATE(created_at) = CURRENT_DATE;`
2. Query PostgreSQL for today's hot leads: 
   `SELECT COUNT(*) as hot_leads FROM leads WHERE lead_score >= 60 AND DATE(created_at) = CURRENT_DATE;`
3. Query PostgreSQL for the 7-day total: 
   `SELECT COUNT(*) as weekly_total FROM leads WHERE created_at >= NOW() - INTERVAL '7 days';`
4. Format the retrieved numbers into a clean, high-level Markdown summary report.
5. Present the report to the user in Telegram.
