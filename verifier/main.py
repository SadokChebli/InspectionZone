from fastapi import FastAPI
from common.kafka import get_consumer, get_producer
import threading
import re

app = FastAPI()

consumer = get_consumer("raw_packets", "verifier-group")
producer = get_producer()

# =========================
# VERIFICATION LOGIC
# =========================
def verify_headers(headers: dict):
    # Host
    if headers.get("Host") not in ["api.example.com", "service.local", "internal.net"]:
        return False, "Invalid Host"

    # Authorization
    auth = headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or len(auth) < 20:
        return False, "Invalid Authorization token"

    # Content-Type
    if headers.get("Content-Type") != "application/json":
        return False, "Invalid Content-Type"

    # User-Agent
    ua = headers.get("User-Agent", "")
    if len(ua) < 5:
        return False, "Invalid User-Agent"

    # Accept
    if not any(x in headers.get("Accept", "") for x in ["application/json", "*/*"]):
        return False, "Unacceptable Accept header"

    # Cookie
    cookie = headers.get("Cookie", "")
    if "session_id=" not in cookie:
        return False, "Missing session cookie"

    # Cache-Control
    if headers.get("Cache-Control") not in ["no-cache", "max-age=3600", "no-store"]:
        return False, "Invalid Cache-Control"

    # Origin
    origin = headers.get("Origin", "")
    if not origin.startswith("https://"):
        return False, "Invalid Origin"

    # Accept-Encoding
    enc = headers.get("Accept-Encoding", "")
    if not any(x in enc for x in ["gzip", "br"]):
        return False, "Unsupported encoding"

    # Referer
    ref = headers.get("Referer", "")
    if not re.match(r"^https?://", ref):
        return False, "Invalid Referer"

    return True, "Headers OK"


# =========================
# CONSUMER LOOP
# =========================
def consume():
    for msg in consumer:
        packet = msg.value

        verdict, reason = verify_headers(packet["headers"])

        packet["verdict"] = verdict
        packet["reason"] = reason
        packet["status"] = "VERIFIED"

        if verdict:
            producer.send("verified_ok", packet)
        else:
            producer.send("to_classify", packet)

        print(f"[VERIFIER] {packet['id']} → {verdict} ({reason})")


@app.on_event("startup")
def start():
    threading.Thread(target=consume, daemon=True).start()


@app.get("/health")
def health():
    return {"status": "ok"}
