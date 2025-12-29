from fastapi import FastAPI
from common.kafka import get_consumer, get_producer
import threading
import uuid
import time

app = FastAPI()

consumer = get_consumer("to_modify", "modifier-group")
producer = get_producer()

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains"
}

def modify_headers(headers: dict):
    # Normalisation minimale
    headers["Content-Type"] = "application/json"
    headers.setdefault("Authorization", "Bearer sanitized")
    headers.setdefault("User-Agent", "InspectionZone/Modifier")

    # Sécurité
    for k, v in SECURITY_HEADERS.items():
        headers[k] = v

    # Traçabilité
    headers["X-Inspection-Status"] = "MODIFIED"
    headers["X-Inspection-Time"] = str(time.time())
    headers["X-Inspection-Node"] = "modifier-ms"

    return headers


def modify(packet: dict):
    # ⚠️ BODY STRICTEMENT INCHANGÉ
    packet["headers"] = modify_headers(packet.get("headers", {}))

    packet["status"] = "MODIFIED"
    packet["verdict"] = True
    packet["reason"] = "Headers normalized and secured"


def consume():
    for msg in consumer:
        packet = msg.value
        modify(packet)

        producer.send("modified_packets", packet)
        print(f"[MODIFIER] {packet['id']} headers fixed")


@app.on_event("startup")
def start():
    threading.Thread(target=consume, daemon=True).start()


@app.get("/health")
def health():
    return {"status": "ok"}
