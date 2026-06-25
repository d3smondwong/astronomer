# Monitoring — backend error alerts

A Cloud Logging **log-based alert** that emails you whenever the FastAPI backend logs an
error (`severity>=ERROR`) on Cloud Run.

## Why it exists

The backend logs errors to Cloud Logging, but logs sitting in a console do nothing on their own — someone has to be watching. This directory automates creating the alert that watches for you: when the FastAPI backend writes a severity>=ERROR log on Cloud Run, Google emails you. So you find out about failures proactively instead of waiting for a user to complain.

It lives in the repo (rather than being clicked together by hand in the Cloud Console) so the alert config is reviewable, repeatable, and recoverable — anyone can re-create the exact same alert in a new project or after it's deleted, and changes are tracked in git.

## What's in it

| File | What it is | You... |
|------|------------|--------|
| `backend_error_alert.sh` | The runnable setup script. Calls `gcloud` to create (idempotently) an email notification channel + the alert policy. | run this once after deploy |
| `alert_policy.example.json` | A reference copy of the alert rule the script generates (the filter + email routing). | read it to understand/audit the rule |
| `README.md` | Prereqs, how to run, parameters, how to verify after deploy, and tuning options. | read first |

## How it relates to the rest
- `apps/utils/logging.py` (B1) is the source — it makes the backend emit structured error logs with severity and chart_key/uid fields.
- `scripts/monitoring/` (B2) is the consumer — it stands up the alert that fires on those error logs and routes the notification to you.

One is application behavior (how logs are written); the other is infrastructure setup (what happens when an error log appears). Keeping the latter in its own scripts/monitoring/ folder signals "this is ops/infra you run against GCP," cleanly separated from the app.

It's currently dormant — nothing runs automatically, and it does nothing until you deploy the backend to Cloud Run and run the script with your project id and alert email.

## How it works

The backend's structured JSON logging ([apps/utils/logging.py](../../apps/utils/logging.py))
emits, in production, one Cloud Logging entry per Python log with a parsed `severity` and
queryable `jsonPayload` fields (`request_id`, `chart_key`, `uid`, `profile_id`). The alert
condition matches:

```
resource.type="cloud_run_revision"
resource.labels.service_name="<SERVICE_NAME>"
severity>=ERROR
```

When a matching entry appears, the policy notifies the email channel — rate-limited to one
notification per 5 minutes so a burst of errors doesn't spam you.

> **Why structured JSON matters here.** Plain-text logs give Cloud Logging only a
> `textPayload` string — no reliable `severity`, no field queries. The JSON handler is what
> makes both `severity>=ERROR` alerting and `jsonPayload.chart_key="…"` support lookups work.

## Prerequisites

1. The FastAPI backend is **deployed to Cloud Run** (this is what produces the logs). Until
   then, the script will create the policy but it has nothing to match.
2. `gcloud` CLI installed and authenticated: `gcloud auth login`.
3. The project has the **Monitoring** and **Logging** APIs enabled.
4. On Cloud Run, set `LOG_FORMAT=json` (or rely on the auto-detect via the `K_SERVICE` env
   var that Cloud Run sets). Locally, logs stay human-readable text.

## Run it

```bash
PROJECT_ID=your-gcp-project \
ALERT_EMAIL=you@example.com \
SERVICE_NAME=astronomer-api \
bash scripts/monitoring/backend_error_alert.sh
```

| Variable       | Required | Default          | Notes |
|----------------|----------|------------------|-------|
| `PROJECT_ID`   | yes      | —                | Your GCP project id. |
| `ALERT_EMAIL`  | yes      | —                | Where alerts are sent. |
| `SERVICE_NAME` | no       | `astronomer-api` | The Cloud Run service name of the FastAPI backend. |
| `MON_TRACK`    | no       | GA               | Set to `beta` or `alpha` if your gcloud lacks the GA `gcloud monitoring` group. |

The script is **idempotent**: it reuses an existing email channel and skips creation if a
policy named *"Backend errors (Cloud Run FastAPI)"* already exists. To recreate, delete the
policy first (the command is printed when it's found).

## Verify after deploy

Because the backend isn't on Cloud Run yet, the alert can't be exercised locally. Once
deployed:

1. Trigger a backend error (e.g. an insights request that makes the LLM call fail) and
   confirm an `ERROR` entry in Logs Explorer with the expected `jsonPayload` fields.
2. Check **Monitoring → Alerting** for the policy and that the email channel is *verified*
   (Google sends a confirmation email on channel creation).
3. Confirm an alert email arrives within a few minutes of the error.

## Tuning

- **Alert on a rate/spike instead of every error.** Swap the `conditionMatchedLog` for a
  log-based **metric + threshold** condition (e.g. *> 5 errors in 5 min*): create a counter
  metric with `gcloud logging metrics create` over the same filter, then a
  `conditionThreshold` policy on `logging.googleapis.com/user/<metric>`. Better at higher
  traffic; the current per-occurrence alert is the right default while volume is low.
- **Narrow to specific events.** Append e.g. `jsonPayload.message=~"insights_.*(failed|error)"`
  to the filter to alert only on the LLM-insight failures rather than all errors.
- **Add a second channel** (Slack/PagerDuty): create it with `gcloud monitoring channels
  create --type=...` and add its `name` to `notificationChannels` in the policy.

## Files

- [`backend_error_alert.sh`](./backend_error_alert.sh) — the setup script (run this).
- [`alert_policy.example.json`](./alert_policy.example.json) — reference copy of the policy
  the script generates, for manual application or review.
