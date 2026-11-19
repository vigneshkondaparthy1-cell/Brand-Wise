from datetime import datetime, timezone
from fastapi import APIRouter
from ..schemas import SlackNotificationRequest

router = APIRouter(prefix="/api", tags=["Integrations"])

@router.post("/notify/slack", response_model=dict)
def trigger_slack_notification(payload: SlackNotificationRequest):
    status_text = payload.status
    color = "#0879d1" if status_text == "Approved" else "#e97821" if status_text == "Changes requested" else "#138a69"

    slack_block = {
        "channel": payload.channel,
        "username": "BrandWise Bot",
        "icon_emoji": ":shield:",
        "attachments": [
            {
                "color": color,
                "title": f"[{status_text.upper()}] {payload.title} ({payload.docId})",
                "title_link": f"http://127.0.0.1:8765/#diff?id={payload.docId}",
                "text": f"*{payload.actor}*: {payload.message}",
                "fields": [
                    {"title": "Review State", "value": status_text, "short": True},
                    {"title": "Platform", "value": "BrandWise Governance", "short": True}
                ],
                "footer": "BrandWise Pre-Publication Governance · Notification Engine",
                "ts": int(datetime.now(timezone.utc).timestamp())
            }
        ]
    }
    return {"sent": True, "slackPayload": slack_block}

@router.get("/integrations/status", response_model=dict)
def get_integrations_status():
    return {
        "slack": {"status": "connected", "channel": "#brand-governance-alerts"},
        "googleDocs": {"status": "connected", "addonVersion": "1.2.0"},
        "figma": {"status": "planned", "phase": "Stretch"},
        "canva": {"status": "planned", "phase": "Stretch"}
    }
