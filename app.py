import os, requests, logging
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

TOKEN       = "EAAWM8gB6LR8BQbc1q5mlw63yd2u2cn0hs6jnzf2gljhr486u3dkgm2yIuBcNDeiDRae3ZCTlQeZAy4uf80Y1lNwqJQJZCXZBRg50hLCacsmfVe76N6mjfOIxBzvhBA7pHeX7cm7DPXHp25BcTCU24MvXwETiZBA2SU0bc1q5mlw63yd2u2cn0hs6jnzf2gljhr486u3dkgm2y"
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
    resp = requests.post(API_URL, headers=HEADERS, json={
        "messaging_product": "whatsapp",
        "to": to.strip(),
        "type": "text",
        "text": {"body": msg}
    }, timeout=10)
    logger.info(f"META RESPONSE for {to}: {resp.status_code} — {resp.text}")

@app.route("/alert", methods=["POST"])
def alert():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "bad json"}), 400
    msg = format_alert(payload)
    logger.info(f"Sending to {len(SUBSCRIBERS)} subscribers")
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