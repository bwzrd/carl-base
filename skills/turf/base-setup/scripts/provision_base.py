#!/usr/bin/env python3
"""Provision the Carl turf-operations schema into an (ideally empty) Airtable base.

Creates 13 tables with selects, links, formulas, and starter rows. Idempotent:
tables and fields that already exist (by name) are skipped, so it is safe to
re-run after a partial failure.

Usage:
    AIRTABLE_API_KEY=pat... python provision_base.py --base appXXXXXXXXXXXXXX
    python provision_base.py --base appXXXXXXXXXXXXXX --dry-run

The token needs scopes: schema.bases:read, schema.bases:write,
data.records:read, data.records:write — and access to the target base.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.airtable.com/v0"

CHECK = {"icon": "check", "color": "greenBright"}


def sel(choices):
    return {"choices": [{"name": c} for c in choices]}


def num(precision):
    return {"precision": precision}


DATE = {"dateFormat": {"name": "iso"}}
DATETIME = {"dateFormat": {"name": "iso"}, "timeFormat": {"name": "24hour"}, "timeZone": "client"}
CURRENCY = {"precision": 2, "symbol": "$"}
DURATION = {"durationFormat": "h:mm"}

# ── Tables (first field = primary). Link and formula fields are added later. ──
TABLES = [
    {"name": "Courses", "fields": [
        {"name": "Name", "type": "singleLineText"},
    ]},
    {"name": "Job List", "description": "Catalog of task types the Job Board links to.", "fields": [
        {"name": "Tasks", "type": "singleLineText"},
    ]},
    {"name": "Employees", "description": "Crew roster of record.", "fields": [
        {"name": "Full Name", "type": "singleLineText"},
        {"name": "Position", "type": "singleLineText"},
        {"name": "Hire Date", "type": "date", "options": DATE},
        {"name": "Contact #", "type": "phoneNumber"},
        {"name": "Email Address", "type": "singleLineText"},
        {"name": "Skills", "type": "multipleSelects", "options": sel([
            "Turf Management", "Irrigation", "Equipment Maintenance", "Project Management",
            "Customer Service", "IPM", "Landscaping", "Arborist", "Gardening", "Grass Cutting"])},
        {"name": "Emergency Contact", "type": "singleLineText"},
        {"name": "Emergency #", "type": "phoneNumber"},
        {"name": "Shirt Size", "type": "singleLineText"},
        {"name": "Status", "type": "singleSelect", "options": sel([
            "Active", "On Leave", "Retired", "Terminated"])},
        {"name": "Employment Type", "type": "singleSelect", "options": sel([
            "Part-Time Seasonal", "Full-Time Seasonal", "Full-Time Permanent", "Contract", "Volunteer"])},
        {"name": "Last Day", "type": "date", "options": DATE},
        {"name": "Hourly Rate", "type": "currency", "options": CURRENCY},
    ]},
    {"name": "Equipment", "fields": [
        {"name": "Equipment Name", "type": "singleLineText"},
        {"name": "Brand", "type": "singleLineText"},
        {"name": "Equipment Type", "type": "singleSelect", "options": sel([
            "Mower", "Tractor", "Sprayer", "Aerator", "Bunker Pro", "Golf Cart",
            "Utility Vehicle", "Reel Grinder", "Roller", "Tool", "Other"])},
        {"name": "Hours", "type": "number", "options": num(1)},
        {"name": "Purchase Date", "type": "date", "options": DATE},
        {"name": "Year", "type": "number", "options": num(0)},
        {"name": "Cost", "type": "currency", "options": CURRENCY},
        {"name": "Condition", "type": "singleSelect", "options": sel(["New", "Good", "Fair", "Poor"])},
        {"name": "Last Maintenance Date", "type": "date", "options": DATE},
        {"name": "Next Maintenance Date", "type": "date", "options": DATE},
        {"name": "Photo", "type": "multipleAttachments"},
        {"name": "Known Issues", "type": "multilineText"},
    ]},
    {"name": "Job Board", "description": "One row per assigned job. Status is a formula - never write it.", "fields": [
        {"name": "Task Description", "type": "singleLineText"},
        {"name": "Job Number", "type": "singleSelect", "options": sel([
            "Task #1", "Task #2", "Task #3", "Task #4", "Task #5"])},
        {"name": "Assigned Date", "type": "date", "options": DATE},
        {"name": "Route", "type": "singleSelect", "options": sel(["Route 1", "Route 2"])},
        {"name": "Mowing Direction", "type": "multipleSelects", "options": sel([
            "North -> South (12:00-6:00)", "East -> West (9:00-3:00)",
            "Left -> Right (8:00-2:00)", "Right -> Left (4:00-10:00)"])},
        {"name": "Cleanup Cut", "type": "checkbox", "options": CHECK},
        {"name": "Task Notes", "type": "singleLineText"},
        {"name": "Start Task", "type": "checkbox", "options": CHECK},
        {"name": "Complete Task", "type": "checkbox", "options": CHECK},
        {"name": "Task Started", "type": "dateTime", "options": DATETIME},
        {"name": "Task Completed", "type": "dateTime", "options": DATETIME},
        {"name": "Crew Feedback", "type": "singleSelect", "options": sel([
            "Good", "Confusing", "Wrong", "Needs More Detail"])},
    ]},
    {"name": "Service Records", "fields": [
        {"name": "Issues", "type": "singleLineText"},
        {"name": "Date", "type": "date", "options": DATE},
        {"name": "Status", "type": "singleSelect", "options": sel([
            "Todo", "In progress", "Done", "Broken Down", "Fixed", "Awaiting Parts"])},
        {"name": "Parts Needed", "type": "singleLineText"},
        {"name": "Parts Cost Estimate", "type": "currency", "options": CURRENCY},
        {"name": "Money Spent", "type": "currency", "options": CURRENCY},
        {"name": "Parts PO", "type": "multipleAttachments"},
        {"name": "Receipt", "type": "multipleAttachments"},
        {"name": "Time Spent", "type": "duration", "options": DURATION},
        {"name": "Tires", "type": "checkbox", "options": CHECK},
        {"name": "Brakes", "type": "checkbox", "options": CHECK},
        {"name": "Fluids", "type": "checkbox", "options": CHECK},
        {"name": "Reels", "type": "checkbox", "options": CHECK},
        {"name": "Bearings", "type": "checkbox", "options": CHECK},
        {"name": "Hoses", "type": "checkbox", "options": CHECK},
        {"name": "Rollers", "type": "checkbox", "options": CHECK},
        {"name": "Lights", "type": "checkbox", "options": CHECK},
        {"name": "Important Notes", "type": "singleLineText"},
    ]},
    {"name": "Fuel Records", "fields": [
        {"name": "Date of Record", "type": "date", "options": DATE},
        {"name": "Fuel Type", "type": "singleSelect", "options": sel([
            "Gasoline", "Diesel", "Electric", "Mix"])},
        {"name": "Pump Reading", "type": "number", "options": num(1)},
        {"name": "Quantity Used", "type": "number", "options": num(1)},
        {"name": "Equipment Notes", "type": "multilineText"},
        {"name": "Initials", "type": "singleLineText"},
    ]},
    {"name": "Daily Logs", "fields": [
        {"name": "Date", "type": "date", "options": DATE},
        {"name": "Weather", "type": "multipleSelects", "options": sel([
            "Sunny", "Cloudy", "Rainy", "Windy", "Stormy", "Foggy", "Snow", "Hail"])},
        {"name": "Rainfall", "type": "number", "options": num(1)},
        {"name": "Temperature High", "type": "number", "options": num(0)},
        {"name": "Tasks Completed", "type": "singleLineText"},
        {"name": "Notes", "type": "multilineText"},
        {"name": "Issues Detected", "type": "multipleSelects", "options": sel([
            "Dry", "Wet", "Disease", "Pest", "Equipment", "Staff", "Weather", "Safety", "Irrigation"])},
        {"name": "Next Day Suggestions", "type": "multilineText"},
    ]},
    {"name": "Protocols / SOPs", "description": "SOPs per task type; Estimated Time drives scheduling.", "fields": [
        {"name": "Protocol Name", "type": "singleLineText"},
        {"name": "Protocol Type", "type": "singleSelect", "options": sel([
            "Daily Task", "Weekly Task", "Emergency", "Spray", "Fertility",
            "Irrigation", "Equipment", "Safety", "Training"])},
        {"name": "Applies To Area", "type": "multipleSelects", "options": sel([
            "Greens", "Tees", "Fairways", "Rough", "Bunkers", "Irrigation", "Shop", "Clubhouse Grounds"])},
        {"name": "Step By Step Instructions", "type": "multilineText"},
        {"name": "Crew Version", "type": "multilineText"},
        {"name": "Required Tools", "type": "multipleSelects", "options": sel([
            "Mower", "Cup cutter", "Rake", "Hose", "Moisture meter", "Blower",
            "Sprayer", "Utility cart", "Hand tools"])},
        {"name": "Required Staff Skill", "type": "singleSelect", "options": sel([
            "Beginner", "Trained", "Experienced", "Licensed", "Supervisor Only"])},
        {"name": "Estimated Time", "type": "duration", "options": DURATION},
        {"name": "Quality Standard", "type": "multilineText"},
        {"name": "Common Mistakes", "type": "multilineText"},
        {"name": "Safety Notes", "type": "multilineText"},
        {"name": "When To Use", "type": "multilineText"},
        {"name": "When Not To Use", "type": "multilineText"},
        {"name": "Status", "type": "singleSelect", "options": sel([
            "Draft", "Active", "Needs Review", "Archived"])},
        {"name": "Last Reviewed", "type": "date", "options": DATE},
    ]},
    {"name": "Pesticide Applications", "description": "Legally significant records - be precise.", "fields": [
        {"name": "Product", "type": "singleLineText"},
        {"name": "Company", "type": "singleLineText"},
        {"name": "Targeted Pest", "type": "singleLineText"},
        {"name": "Location", "type": "singleLineText"},
        {"name": "Spray Area (Msq)", "type": "number", "options": num(0)},
        {"name": "Label Rate (L/ha)", "type": "number", "options": num(2)},
        {"name": "Sprayer Rate (L/ha)", "type": "number", "options": num(2)},
        {"name": "Tank Volume (L)", "type": "number", "options": num(0)},
        {"name": "Notes", "type": "multilineText"},
        {"name": "Name of Applicator", "type": "singleLineText"},
        {"name": "Certification #", "type": "singleLineText"},
        {"name": "Wind Speed", "type": "number", "options": num(0)},
        {"name": "Wind Direction", "type": "singleSelect", "options": sel([
            "Todo", "In progress", "Done"])},
        {"name": "Humidity", "type": "singleSelect", "options": sel(["Low", "Medium", "High"])},
        {"name": "Temperature", "type": "number", "options": num(0)},
        {"name": "Conditions", "type": "multipleSelects", "options": sel([
            "Cool", "Hot", "Warm", "Mild", "Dry", "Wet", "Rainy", "Humid", "Windy", "Stormy"])},
        {"name": "Status", "type": "singleSelect", "options": sel(["To do", "In Progress", "Done"])},
        {"name": "Legal/Safety Critical?", "type": "checkbox", "options": CHECK},
    ]},
    {"name": "Fertility", "fields": [
        {"name": "FertilizerType", "type": "singleLineText"},
        {"name": "Brand", "type": "singleLineText"},
        {"name": "ApplicationDate", "type": "date", "options": DATE},
        {"name": "Quantity Used", "type": "number", "options": num(1)},
        {"name": "Application Rate", "type": "number", "options": num(2)},
        {"name": "Application Method", "type": "multipleSelects", "options": sel(["Soluble", "Granular"])},
        {"name": "Application Equipment", "type": "multipleSelects", "options": sel([
            "Sprayer", "Backpack Sprayer", "Tow Behind Hopper", "Walk Behind Hopper"])},
        {"name": "N-P-K", "type": "singleLineText"},
        {"name": "Location", "type": "multipleSelects", "options": sel([
            "Greens", "Tees", "Fairway", "Rough", "Range", "Putting Green"])},
        {"name": "Turf Health Assessment", "type": "singleLineText"},
        {"name": "Cost", "type": "currency", "options": CURRENCY},
        {"name": "PhotoDocumentation", "type": "multipleAttachments"},
        {"name": "Expected Result", "type": "multilineText"},
        {"name": "Follow Up Date", "type": "date", "options": DATE},
    ]},
    {"name": "Irrigation Records", "fields": [
        {"name": "Irrigation Date", "type": "date", "options": DATE},
        {"name": "Water Usage", "type": "number", "options": num(0)},
        {"name": "Pump Reading", "type": "number", "options": num(1)},
        {"name": "Rainfall", "type": "number", "options": num(1)},
        {"name": "Watering Reason", "type": "singleSelect", "options": sel([
            "Heat", "Wilt", "Dry Spot", "Programmed Cycle", "Hand Water", "New Seed/Sod", "Syringe"])},
        {"name": "Notes", "type": "multilineText"},
    ]},
    {"name": "Scouting", "fields": [
        {"name": "Scout Name", "type": "singleLineText"},
        {"name": "Date", "type": "date", "options": DATE},
        {"name": "Precipitation", "type": "number", "options": num(1)},
        {"name": "Temperature Low", "type": "number", "options": num(0)},
        {"name": "Temperature High", "type": "number", "options": num(0)},
        {"name": "Humidity", "type": "singleSelect", "options": sel(["Low", "Medium", "High"])},
        {"name": "Pests Seen", "type": "checkbox", "options": CHECK},
        {"name": "Actions Taken", "type": "singleSelect", "options": sel(["Spray Applied", "None"])},
        {"name": "Suspected Issue", "type": "multipleSelects", "options": sel([
            "Disease", "Pest", "Drought Stress", "Wet Area", "Nutrient Issue", "Weed", "Mechanical Damage"])},
        {"name": "Notes", "type": "multilineText"},
        {"name": "Recommended Action", "type": "multilineText"},
    ]},
]

# ── Link fields: (table, field name, linked table). Reverse links auto-create. ──
LINKS = [
    ("Job Board", "Course", "Courses"),
    ("Job Board", "Job Title", "Job List"),
    ("Job Board", "Assigned Staff", "Employees"),
    ("Job Board", "Equipment", "Equipment"),
    ("Job Board", "Related Protocol", "Protocols / SOPs"),
    ("Job List", "Course", "Courses"),
    ("Equipment", "Last Operator", "Employees"),
    ("Service Records", "Equipment Name", "Equipment"),
    ("Fuel Records", "Recorded By", "Employees"),
    ("Fuel Records", "Equipment Used", "Equipment"),
    ("Daily Logs", "Course", "Courses"),
    ("Daily Logs", "Equipment Used", "Equipment"),
    ("Protocols / SOPs", "Related Job List", "Job List"),
    ("Protocols / SOPs", "Related Equipment", "Equipment"),
    ("Protocols / SOPs", "Course", "Courses"),
    ("Protocols / SOPs", "Approved By", "Employees"),
]

# ── Formula fields (ordered: later formulas may reference earlier ones). ──
FORMULAS = [
    ("Job Board", "Status",
     'IF({Complete Task}, "Completed", IF({Start Task}, "In Progress", "Assigned"))'),
    ("Job Board", "Task Duration",
     'IF(AND({Task Started}, {Task Completed}), '
     'DATETIME_FORMAT(DATEADD(DATETIME_PARSE("1970-01-01"), '
     "MAX(DATETIME_DIFF({Task Completed}, {Task Started}, 'seconds'), 0), 'seconds'), \"HH:mm\"))"),
    ("Pesticide Applications", "Spray Area (acres)",
     'ROUND({Spray Area (Msq)} / 4046.856, 2) & " acres"'),
    ("Pesticide Applications", "ha per Full Tank",
     "ROUND({Tank Volume (L)} / {Sprayer Rate (L/ha)}, 2)"),
    ("Pesticide Applications", "Tanks",
     "{Spray Area (Msq)} / 10000 / {ha per Full Tank}"),
    ("Pesticide Applications", "Total Product Required (L)",
     "ROUND(({Spray Area (Msq)} / 10000) * {Label Rate (L/ha)}, 2)"),
    ("Pesticide Applications", "Product per Tank",
     "ROUND({ha per Full Tank} * {Label Rate (L/ha)}, 2)"),
]

# ── Starter rows (only written when the table is empty). ──
SEEDS = {
    "Courses": [{"Name": "Main Course"}],
    "Job List": [{"Tasks": t} for t in [
        "Mow Greens", "Mow Tees", "Mow Fairways", "Mow Rough", "Mow Collars & Approaches",
        "Rake Bunkers", "Change Cups", "Move Tee Markers", "Water Greens", "Roll Greens",
        "Topdress Greens", "Verticut Greens", "Blow Debris", "String Trim", "Fill Divots"]],
}


class Client:
    def __init__(self, key, dry_run=False):
        self.key = key
        self.dry_run = dry_run

    def call(self, method, path, body=None):
        if self.dry_run and method != "GET":
            print(f"  [dry-run] {method} {path} {json.dumps(body)[:120]}...")
            return {}
        req = urllib.request.Request(
            f"{API}{path}",
            data=json.dumps(body).encode() if body is not None else None,
            method=method,
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
        )
        time.sleep(0.25)  # stay under Airtable's 5 req/s limit
        try:
            with urllib.request.urlopen(req) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            raise SystemExit(f"ERROR {e.code} on {method} {path}\n{detail}\n"
                             "Check the token has schema.bases:write + data.records:write "
                             "scopes and access to this base.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default=os.environ.get("AIRTABLE_BASE_ID"),
                    help="Target base ID (appXXXXXXXXXXXXXX)")
    ap.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    ap.add_argument("--no-seed", action="store_true", help="Skip starter rows")
    args = ap.parse_args()

    key = os.environ.get("AIRTABLE_API_KEY", "")
    if not key:
        sys.exit("Set AIRTABLE_API_KEY in the environment.")
    if not args.base or not args.base.startswith("app"):
        sys.exit("Pass --base appXXXXXXXXXXXXXX (or set AIRTABLE_BASE_ID).")

    c = Client(key, args.dry_run)
    base = args.base

    existing = c.call("GET", f"/meta/bases/{base}/tables")
    tables = {t["name"]: t for t in existing.get("tables", [])}
    print(f"Base {base}: {len(tables)} existing table(s).")

    # 1. Tables
    for spec in TABLES:
        if spec["name"] in tables:
            print(f"= table exists: {spec['name']}")
            continue
        print(f"+ create table: {spec['name']}")
        created = c.call("POST", f"/meta/bases/{base}/tables", spec)
        if created:
            tables[spec["name"]] = created

    def field_names(tname):
        return {f["name"] for f in tables.get(tname, {}).get("fields", [])}

    def add_field(tname, field):
        tid = tables[tname]["id"]
        print(f"+ field {tname}.{field['name']}")
        created = c.call("POST", f"/meta/bases/{base}/tables/{tid}/fields", field)
        if created:
            tables[tname]["fields"].append(created)

    # 2. Links (reverse fields appear automatically on the linked table)
    for tname, fname, target in LINKS:
        if fname in field_names(tname):
            print(f"= link exists: {tname}.{fname}")
            continue
        add_field(tname, {"name": fname, "type": "multipleRecordLinks",
                          "options": {"linkedTableId": tables[target]["id"]}})

    # Refresh so reverse-link fields don't collide with later creates
    if not args.dry_run:
        refreshed = c.call("GET", f"/meta/bases/{base}/tables")
        tables = {t["name"]: t for t in refreshed.get("tables", [])}

    # 3. Formulas
    for tname, fname, formula in FORMULAS:
        if fname in field_names(tname):
            print(f"= formula exists: {tname}.{fname}")
            continue
        add_field(tname, {"name": fname, "type": "formula", "options": {"formula": formula}})

    # 4. Starter rows
    if not args.no_seed:
        for tname, rows in SEEDS.items():
            tid = tables[tname]["id"]
            has = c.call("GET", f"/{base}/{tid}?maxRecords=1") if not args.dry_run else {}
            if has.get("records"):
                print(f"= seed skipped ({tname} has data)")
                continue
            print(f"+ seed {len(rows)} row(s) into {tname}")
            c.call("POST", f"/{base}/{tid}", {"records": [{"fields": r} for r in rows],
                                              "typecast": True})

    print("\nDone. Carl's base is ready — point AIRTABLE_BASE_ID at it.")


if __name__ == "__main__":
    main()
