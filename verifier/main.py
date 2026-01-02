from fastapi import FastAPI
from common.kafka import get_consumer, get_producer
import threading
import re

from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter

app = FastAPI(title="verifier-service")

Instrumentator().instrument(app).expose(app)

consumer = get_consumer("raw_packets", "verifier-group")
producer = get_producer()

PACKETS_VERIFIED = Counter(
    "inspection_packets_verified_total",
    "Total packets verified"
)

PACKETS_REJECTED = Counter(
    "inspection_packets_rejected_total",
    "Total packets rejected by verifier"
)

def verify_headers(headers: dict):
    if headers.get("Host") not in ["api.example.com", "service.local", "internal.net"]:
        return False, "Invalid Host"
    auth = headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or len(auth) < 20:
        return False, "Invalid Authorization token"
    if headers.get("Content-Type") != "application/json":
        return False, "Invalid Content-Type"
    if len(headers.get("User-Agent", "")) < 5:
        return False, "Invalid User-Agent"
    if not any(x in headers.get("Accept", "") for x in ["application/json", "*/*"]):
        return False, "Unacceptable Accept header"
    if "session_id=" not in headers.get("Cookie", ""):
        return False, "Missing session cookie"
    if headers.get("Cache-Control") not in ["no-cache", "max-age=3600", "no-store"]:
        return False, "Invalid Cache-Control"
    if not headers.get("Origin", "").startswith("https://"):
        return False, "Invalid Origin"
    if not any(x in headers.get("Accept-Encoding", "") for x in ["gzip", "br"]):
        return False, "Unsupported encoding"
    if not re.match(r"^https?://", headers.get("Referer", "")):
        return False, "Invalid Referer"

    return True, "Headers OK"

def consume():
    for msg in consumer:
        packet = msg.value
        verdict, reason = verify_headers(packet["headers"])

        PACKETS_VERIFIED.inc()

        packet["verdict"] = verdict
        packet["reason"] = reason
        packet["status"] = "VERIFIED"

        if verdict:
            producer.send("verified_ok", packet)
        else:
            PACKETS_REJECTED.inc()
            producer.send("to_classify", packet)

        print(f"[VERIFIER] {packet['id']} → {verdict}")

@app.on_event("startup")
def start():
    threading.Thread(target=consume, daemon=True).start()

@app.get("/health")
def health():
    return {"status": "ok"}
