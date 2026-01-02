from fastapi import FastAPI
from common.kafka import get_consumer, get_producer
import threading, re

from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter

app = FastAPI(title="classifier-service")
app = FastAPI(title="classifier-service")

# ✅ PROMETHEUS AVANT STARTUP
Instrumentator().instrument(app).expose(app)

consumer = get_consumer("to_classify", "classifier-group")
producer = get_producer()

PACKETS_CLASSIFIED = Counter(
    "inspection_packets_classified_total",
    "Total packets classified"
)

FORBIDDEN_KEYS = {"password", "token", "secret"}
SQL_XSS_PATTERNS = re.compile(r"(select|drop|insert|delete|<script>)", re.IGNORECASE)

def inspect_body(body: dict):
    for k, v in body.items():
        if k.lower() in FORBIDDEN_KEYS:
            return False, f"Forbidden field: {k}"
        if v is None:
            return False, f"Null value for key: {k}"
        if isinstance(v, str) and SQL_XSS_PATTERNS.search(v):
            return False, f"Injection detected in {k}"
    return True, "Payload clean"

def consume():
    for msg in consumer:
        packet = msg.value
        verdict, reason = inspect_body(packet["body"])

        PACKETS_CLASSIFIED.inc()

        packet["verdict"] = verdict
        packet["reason"] = reason
        packet["status"] = "CLASSIFIED"

        producer.send("classified_ok" if verdict else "to_modify", packet)

@app.on_event("startup")
def start():
    threading.Thread(target=consume, daemon=True).start()

@app.get("/health")
def health():
    return {"status": "ok"}
