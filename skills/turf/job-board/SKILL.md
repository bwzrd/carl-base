---
name: job-board
description: Assign, update, and report on crew jobs in the course's Airtable Job Board — linked-record handling, status rules, and the morning/end-of-day board workflows.
version: 1.0.0
author: Brendan Wise
metadata:
  hermes:
    tags: [Turf, Airtable, Operations]
    related_skills: [field-logs, crew]
---

# Job Board

The Job Board table in the course base (`AIRTABLE_BASE_ID`) is where all crew
work is assigned and tracked. Use the Airtable tools for every operation.

## Standard tables (Carl template base)

| Table | Purpose | Primary field |
|---|---|---|
| Job Board | one row per assigned job | Job Title (linked) |
| Job List | catalog of task types ("Mow Greens", "Rake Bunkers"…) | Tasks |
| Employees | crew roster | Full Name |
| Equipment | machines | (name) |
| Courses | course(s) on the property | (name) |
| Protocols | SOPs per task type, carries "Estimated Time" | (name) |

Table and field IDs differ per base. On first use, discover the schema (list
tables + fields for the base), then remember the IDs in memory so you don't
re-discover every time.

## Writing Job Board records — the rules that matter

1. **Linked-record fields take arrays of record IDs, not strings**: `Job Title`
   (→ Job List), `Assigned Staff` (→ Employees), `Equipment` (→ Equipment),
   `Course` (→ Courses). To set one: search the target table for the record by
   name, then write `["recXXXX"]`. If a task type or employee doesn't exist yet,
   create it in its table first, then link it.
2. **Never write `Status`** — it's a formula field driven by dates/checkboxes.
   Writing it fails.
3. Plain writable fields: `Task Description`, `Task Notes`, `Assigned Date`
   (ISO date), `Mowing Direction`, `Cleanup Cut`.
4. Resolve employee names against the Employees table `Full Name` field —
   fuzzy-match politely ("Did you mean Mike R.?") rather than creating
   near-duplicate roster entries.

## Daily workflows

**Morning board push** (also run by cron): read today's Job Board rows
(`Assigned Date` = today), group by assigned staff, and post a short crew
summary — who's on what, with equipment. Flag unassigned jobs.

**Assigning work**: create the Job Board row with links resolved, confirm back
in one line ("Mike's on greens with the 2500E, down for 7am"). If the crew
member has a Telegram chat set up, they'll see the board summary.

**End of day**: list today's jobs still incomplete (status not done), flag them
to the superintendent, and ask whether to roll them to tomorrow (update
`Assigned Date`) or drop them.

## Reporting

For "what did we do this week" style asks: filter Job Board by date range,
summarize counts by task type and person — short table, no dumping raw records.
