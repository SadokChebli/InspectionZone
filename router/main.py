from fastapi import FastAPI
from common.kafka import get_consumer
import threading

from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter

app = FastAPI(title="router-service")

Instrumentator().instrument(app).expose(app)

topics = ["verified_ok", "classified_ok", "modified_packets"]

PACKETS_ROUTED = Counter(
    "inspection_packets_routed_total",
    "Total packets routed"
)

def consume(topic):
    consumer = get_consumer(topic, f"router-{topic}")
    for msg in consumer:
        PACKETS_ROUTED.inc()
        packet = msg.value
        print(f"[ROUTER] Packet {packet['id']} routed")

@app.on_event("startup")
def start():
    for t in topics:
        threading.Thread(target=consume, args=(t,), daemon=True).start()

@app.get("/health")
def health():
    return {"status": "ok"}
