from fastapi import FastAPI
from common.kafka import get_consumer, get_producer
import threading, time

from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter

app = FastAPI(title="modifier-service")

Instrumentator().instrument(app).expose(app)

consumer = get_consumer("to_modify", "modifier-group")
producer = get_producer()

PACKETS_MODIFIED = Counter(
    "inspection_packets_modified_total",
    "Total packets modified"
)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains"
}

def modify_headers(headers: dict):
    headers["Content-Type"] = "application/json"
    headers.setdefault("Authorization", "Bearer sanitized")
    headers.setdefault("User-Agent", "InspectionZone/Modifier")
    for k, v in SECURITY_HEADERS.items():
        headers[k] = v
    headers["X-Inspection-Status"] = "MODIFIED"
    headers["X-Inspection-Time"] = str(time.time())
    headers["X-Inspection-Node"] = "modifier-ms"
    return headers

def consume():
    for msg in consumer:
        packet = msg.value
        packet["headers"] = modify_headers(packet.get("headers", {}))
        packet["status"] = "MODIFIED"
        packet["verdict"] = True
        packet["reason"] = "Headers normalized"

        PACKETS_MODIFIED.inc()
        producer.send("modified_packets", packet)

@app.on_event("startup")
def start():
    threading.Thread(target=consume, daemon=True).start()

@app.get("/health")
def health():
    return {"status": "ok"}
