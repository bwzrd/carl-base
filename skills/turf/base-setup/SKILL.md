---
name: base-setup
description: One-command setup of a new course's Airtable base - creates all 13 Carl tables (Job Board, Employees, Equipment, logs...) with selects, links, formulas, and starter rows.
version: 1.0.0
author: Brendan Wise
metadata:
  hermes:
    tags: [Turf, Airtable, Onboarding]
    related_skills: [job-board, field-logs, crew]
---

# Base Setup

When the operator asks to "set up my base", "build my Airtable", or their
`AIRTABLE_BASE_ID` points at an empty/new base, provision the standard Carl
schema with the bundled script — do NOT hand-create tables one by one.

## Steps

1. Confirm `AIRTABLE_API_KEY` and `AIRTABLE_BASE_ID` are set. The base should
   be a fresh one the operator created ("Start from scratch" in Airtable).
2. Preview first:
   ```
   python "${HERMES_SKILL_DIR}/scripts/provision_base.py" --base $AIRTABLE_BASE_ID --dry-run
   ```
3. Run it for real (drops the `--dry-run`). It is idempotent — safe to re-run
   if it fails partway.
4. Verify by listing the base's tables; you should see 13 (Courses, Job List,
   Employees, Equipment, Job Board, Service Records, Fuel Records, Daily Logs,
   Protocols / SOPs, Pesticide Applications, Fertility, Irrigation Records,
   Scouting) plus starter Job List task types.
5. Tell the operator to rename the "Main Course" row in Courses and add their
   crew to Employees (or offer to add them now, one short question at a time).

## Failure notes

- **403 / INVALID_PERMISSIONS**: their token is missing `schema.bases:write`
  (most PATs only have data scopes). Tell them to edit the token at
  airtable.com/create/tokens, add `schema.bases:read` + `schema.bases:write`,
  and grant it access to the base.
- The script skips tables/fields that already exist by name, so a base that
  already has a "Job Board" won't be touched — flag mismatches instead of
  forcing.
