# Carl — pocket turf professional

Operations agent for golf course maintenance crews, packaged as a
[Hermes Agent](https://hermes-agent.nousresearch.com) profile distribution.
Carl assigns crew jobs, logs fuel/equipment/service work, builds schedules, and
answers turf questions — over Telegram, with everything stored in your Airtable
base.

## Install (2 minutes)

**1. Install Hermes** (skip if you have it):

```bash
# Linux / macOS / WSL2
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```
```powershell
# Windows
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

**2. Install Carl:**

```bash
hermes profile install github.com/OWNER/carl-base --name carl --alias -y
```

**3. Log in — no API keys needed:**

```bash
carl setup --portal
```

One browser login (Nous Portal) covers the model and built-in tools. On a
Claude Max plan with extra usage credits instead? Run `carl model` and pick
**Anthropic OAuth**.

**4. Connect your course:**

```bash
cp ~/.hermes/profiles/carl/.env.EXAMPLE ~/.hermes/profiles/carl/.env
# then edit .env:
#   TELEGRAM_BOT_TOKEN  — from @BotFather
#   AIRTABLE_API_KEY    — PAT with data.records read/write + schema read
#   AIRTABLE_BASE_ID    — your copy of the Carl template base (app…)
#   COURSE_NAME / WEATHER_LOCATION — optional
```

**5. Start Carl:**

```bash
carl gateway start     # Telegram comes online
carl chat              # or talk to him right here
```

## Enable the scheduled jobs (recommended)

Shipped cron jobs are **not** auto-scheduled — review `cron/*.json`, then:

```bash
carl cron create "0 6 * * *"  "$(python -c "import json;print(json.load(open('cron/morning-job-board.json'))['prompt'])")" --skill job-board --name morning-job-board
carl cron create "0 17 * * *" "$(python -c "import json;print(json.load(open('cron/eod-check.json'))['prompt'])")" --skill job-board --name eod-check
```

(Or just tell Carl: "every morning at 6 post the job board summary".)

## What's inside

```
distribution.yaml   manifest + required env vars
SOUL.md             Carl's personality and operating rules
config.yaml         Airtable MCP server (mcp_servers)
skills/turf/        job-board · field-logs · crew
cron/               morning board push · end-of-day check (enable manually)
```

## Updating

```bash
hermes profile update carl
```

Your `.env`, memories, and chat history are never touched; Carl's skills,
persona, and cron templates update.

## Notes

- Crew interaction happens on **Telegram** (per-user chat IDs). The Hermes web
  dashboard is single-operator only — don't share it with the crew.
- Airtable 403s mean your token is missing scopes or base access, not that
  Carl is broken.
