from fastapi import FastAPI
from common.kafka import get_producer
from common.models import Packet
import time, threading

app = FastAPI()
producer = get_producer()

TOPIC_OUT = "raw_packets"

def loop():
    while True:
        packet = Packet.new()
        producer.send(TOPIC_OUT, packet.dict())
        print("[SIMULATOR] Packet sent:", packet.id)
        time.sleep(5)

@app.on_event("startup")
def start():
    threading.Thread(target=loop, daemon=True).start()

@app.get("/health")
def health():
    return {"status": "ok"}
