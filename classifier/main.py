from fastapi import FastAPI
from common.kafka import get_consumer, get_producer
import threading
import re

app = FastAPI()

consumer = get_consumer("to_classify", "classifier-group")
producer = get_producer()

# =========================
# DPI INSPECTION LOGIC
# =========================
FORBIDDEN_KEYS = {"password", "token", "secret"}
SQL_XSS_PATTERNS = re.compile(r"(select|drop|insert|delete|<script>)", re.IGNORECASE)

def inspect_body(body: dict):

    for key, value in body.items():
        # 2️⃣ Clés interdites
        if key.lower() in FORBIDDEN_KEYS:
            return False, f"Forbidden field: {key}"

        # 3️⃣ Valeur nulle
        if value is None:
            return False, f"Null value for key: {key}"

        # 4️⃣ Strings suspectes
        if isinstance(value, str):
            if len(value) > 100:
                return False, f"String too long: {key}"
            if SQL_XSS_PATTERNS.search(value):
                return False, f"Injection detected in {key}"

        # 5️⃣ Valeurs numériques
        if isinstance(value, (int, float)):
            if value < 0 or value > 10_000:
                return False, f"Numeric value out of range: {key}"

        # 6️⃣ Règles métiers
        if key == "age" and not (0 <= value <= 120):
            return False, "Invalid age value"

        if key in {"price", "amount"} and value < 0:
            return False, f"Negative value for {key}"

    return True, "Payload clean"


# =========================
# CONSUMER LOOP
# =========================
def consume():
    for msg in consumer:
        packet = msg.value
        body = packet["body"]

        verdict, reason = inspect_body(body)

        packet["verdict"] = verdict
        packet["reason"] = reason
        packet["status"] = "CLASSIFIED"

        if verdict:
            producer.send("classified_ok", packet)
        else:
            producer.send("to_modify", packet)

        print(f"[CLASSIFIER] {packet['id']} → {verdict} ({reason})")


@app.on_event("startup")
def start():
    threading.Thread(target=consume, daemon=True).start()


@app.get("/health")
def health():
    return {"status": "ok"}
