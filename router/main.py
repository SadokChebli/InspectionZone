from fastapi import FastAPI
from common.kafka import get_consumer
import threading

app = FastAPI()

topics = ["verified_ok", "classified_ok", "modified_packets"]

def consume(topic):
    consumer = get_consumer(topic, f"router-{topic}")
    for msg in consumer:
        packet = msg.value
        print(f"[ROUTER] Packet {packet['id']} routed to {packet['destination_ip']}")

@app.on_event("startup")
def start():
    for t in topics:
        threading.Thread(target=consume, args=(t,), daemon=True).start()

@app.get("/health")
def health():
    return {"status": "ok"}
