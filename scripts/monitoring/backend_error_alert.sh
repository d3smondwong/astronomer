#!/usr/bin/env bash
#
# Create (idempotently) a Cloud Logging log-based alert that fires when the FastAPI
# backend writes an error (severity>=ERROR) on Cloud Run, and routes it to an email
# notification channel.
#
# Relies on the backend's structured JSON logging (apps/utils/logging.py): on Cloud Run
# each Python error log becomes a Cloud Logging entry with severity=ERROR and queryable
# jsonPayload.chart_key / request_id / uid / profile_id fields.
#
# Usage:
#   PROJECT_ID=my-gcp-project ALERT_EMAIL=alerts@example.com \
#     [SERVICE_NAME=astronomer-api] [MON_TRACK=beta] \
#     bash scripts/monitoring/backend_error_alert.sh
#
# Re-running is safe: it reuses an existing channel/policy with the same display name.
set -euo pipefail

# ── Config (override via env) ────────────────────────────────────────────────
PROJECT_ID="${PROJECT_ID:-}"
SERVICE_NAME="${SERVICE_NAME:-astronomer-api}"   # Cloud Run service name for the FastAPI backend
ALERT_EMAIL="${ALERT_EMAIL:-}"
# Release track for the monitoring command group. Empty = GA (gcloud monitoring ...).
# If your gcloud version lacks the GA group, set MON_TRACK=beta (or alpha).
MON_TRACK="${MON_TRACK:-}"

POLICY_NAME="Backend errors (Cloud Run FastAPI)"
CHANNEL_NAME="Astronomer Alerts (email)"

# ── Preconditions ────────────────────────────────────────────────────────────
command -v gcloud >/dev/null 2>&1 || { echo "ERROR: gcloud CLI not found. Install the Google Cloud SDK." >&2; exit 1; }
[ -n "$PROJECT_ID" ]  || { echo "ERROR: set PROJECT_ID (your GCP project id)." >&2; exit 1; }
[ -n "$ALERT_EMAIL" ] || { echo "ERROR: set ALERT_EMAIL (where alerts are sent)." >&2; exit 1; }

# gcloud monitoring [TRACK] ...
mon() { gcloud ${MON_TRACK:+$MON_TRACK} monitoring "$@"; }

echo "Project:  $PROJECT_ID"
echo "Service:  $SERVICE_NAME"
echo "Email:    $ALERT_EMAIL"
echo "Mon track: ${MON_TRACK:-GA}"
echo

# ── 1. Notification channel (create-or-reuse by display name) ────────────────
echo "Looking up notification channel '$CHANNEL_NAME'..."
CHANNEL="$(mon channels list \
  --project="$PROJECT_ID" \
  --filter="displayName=\"$CHANNEL_NAME\" AND type=email" \
  --format="value(name)" 2>/dev/null | head -n1 || true)"

if [ -z "$CHANNEL" ]; then
  echo "  none found — creating it."
  CHANNEL="$(mon channels create \
    --project="$PROJECT_ID" \
    --display-name="$CHANNEL_NAME" \
    --type=email \
    --channel-labels=email_address="$ALERT_EMAIL" \
    --format="value(name)")"
else
  echo "  reusing: $CHANNEL"
fi
[ -n "$CHANNEL" ] || { echo "ERROR: could not resolve a notification channel." >&2; exit 1; }

# ── 2. Alert policy (skip if one with this display name already exists) ──────
echo "Checking for existing alert policy '$POLICY_NAME'..."
EXISTING="$(mon policies list \
  --project="$PROJECT_ID" \
  --filter="displayName=\"$POLICY_NAME\"" \
  --format="value(name)" 2>/dev/null | head -n1 || true)"

if [ -n "$EXISTING" ]; then
  echo "  already exists: $EXISTING"
  echo "  (delete it first to recreate: gcloud ${MON_TRACK:+$MON_TRACK} monitoring policies delete \"$EXISTING\" --project=$PROJECT_ID)"
  echo "Done (no changes)."
  exit 0
fi

POLICY_FILE="$(mktemp)"
trap 'rm -f "$POLICY_FILE"' EXIT
cat > "$POLICY_FILE" <<JSON
{
  "displayName": "$POLICY_NAME",
  "documentation": {
    "content": "A FastAPI backend log entry with severity ERROR or higher was written on Cloud Run (service: $SERVICE_NAME). Open Logs Explorer and filter by jsonPayload.chart_key / jsonPayload.request_id / jsonPayload.uid / jsonPayload.profile_id to trace the failing request.",
    "mimeType": "text/markdown"
  },
  "combiner": "OR",
  "conditions": [
    {
      "displayName": "Backend log severity>=ERROR",
      "conditionMatchedLog": {
        "filter": "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"$SERVICE_NAME\" severity>=ERROR"
      }
    }
  ],
  "alertStrategy": {
    "notificationRateLimit": { "period": "300s" }
  },
  "notificationChannels": ["$CHANNEL"]
}
JSON

echo "Creating alert policy..."
mon policies create --project="$PROJECT_ID" --policy-from-file="$POLICY_FILE"
echo "Done. Alerts for backend errors will be emailed to $ALERT_EMAIL (max 1 per 5 min)."
