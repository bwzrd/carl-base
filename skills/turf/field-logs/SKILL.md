---
name: field-logs
description: Log fuel, equipment condition, service work, and daily notes into the course Airtable base — what goes in which table and the fields each record needs.
version: 1.0.0
author: Brendan Wise
metadata:
  hermes:
    tags: [Turf, Airtable, Logging]
    related_skills: [job-board, crew]
---

# Field Logs

When the crew tells you something happened — fuel pumped, a machine acting up,
service done, spray applied — it goes in a table, immediately. Never just
acknowledge in chat.

## Which table

| They say | Table | Key fields |
|---|---|---|
| "put 40L of diesel in the 5410" | Fuel | fuel type, quantity, pump reading, date, equipment (link), recorded by (link to Employees), initials, notes |
| "the Toro's at 2,340 hours, running rough" | Equipment | hours, condition, notes; last/next maintenance dates |
| "changed the oil / replaced bedknife on…" | Service | equipment (link), date, status, issues, parts needed, money spent, notes |
| "spray round on greens today" | Pesticide | product, rate, area, date, applicator |
| "fertilized fairways" | Fertility | product, rate, area, date |
| "ran heads on 12 for 20 min" | Irrigation | zone/area, duration, date |
| general end-of-day notes | Daily Logs | date, tasks completed, notes |

Exact field IDs vary per base — discover the schema on first use and remember
it. Linked fields (equipment, recorded-by) take arrays of record IDs: resolve
the name in the linked table first.

## Rules

- **Required detail missing → one short question.** Fuel without a quantity,
  service without which machine — ask, don't guess.
- Date defaults to today unless they say otherwise. Use ISO dates.
- Who logged it matters: when you know who's talking (Telegram chat → roster
  name), set the recorded-by/applicator link and initials.
- Equipment names come from the Equipment table — resolve against it; if a
  machine isn't in the table, ask before adding it.
- Pesticide records may be legally required (e.g. Ontario IPM) — be precise
  with product names, rates, and areas; read them back in the confirmation.
- Confirm in one line what was stored: "Logged — 40L diesel, unit 5410, pump
  at 8,912."
