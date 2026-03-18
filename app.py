import os, requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TOKEN       = os.environ["WHATSAPP_TOKEN"]
PHONE_ID    = os.environ["PHONE_NUMBER_ID"]
SUBSCRIBERS = os.environ.get("SUBSCRIBERS", "").split(",")

API_URL = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

STATE_EMOJI = {"alerting": "🔴", "ok": "✅", "no_data": "⚠️", "pending": "🟡"}

def format_alert(payload):
    if "alerts" in payload:
        status = payload.get("status", "unknown")
        emoji  = STATE_EMOJI.get(status, "❓")
        lines  = [f"{emoji} *Grafana — {status.upper()}*"]
        for a in payload["alerts"]:
            name = a.get("labels", {}).get("alertname", "Alert")
            desc = a.get("annotations", {}).get("description") or \
                   a.get("annotations", {}).get("summary", "")
            lines.append(f"\n• *{name}*")
            if desc:
                lines.append(f"  {desc}")
        url = payload.get("externalURL", "")
        if url:
            lines.append(f"\n🔗 {url}")
        return "\n".join(lines)
    state = payload.get("state", "unknown")
    emoji = STATE_EMOJI.get(state, "❓")
    return f"{emoji} *{payload.get('title', '')}*\n{payload.get('message', '')}"

def send_wa(to, msg):
    requests.post(API_URL, headers=HEADERS, json={
        "messaging_product": "whatsapp",
        "to": to.strip(),
        "type": "text",
        "text": {"body": msg}
    }, timeout=10)

@app.route("/alert", methods=["POST"])
def alert():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "bad json"}), 400
    msg = format_alert(payload)
    for n in SUBSCRIBERS:
        if n.strip():
            send_wa(n, msg)
    return jsonify({"sent": len(SUBSCRIBERS)}), 200

@app.route("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)