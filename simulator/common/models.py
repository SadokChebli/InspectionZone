from pydantic import BaseModel
from typing import Dict, Optional, Any
import time
import uuid
import random
import ipaddress

class Packet(BaseModel):
    id: str
    source_ip: str
    destination_ip: str
    headers: Dict[str, str]
    body: Dict[str, Any]
    timestamp: float
    verdict: Optional[bool] = None
    reason: Optional[str] = None
    status: str

    # =========================
    # BODY GENERATION
    # =========================
    @staticmethod
    def generate_body() -> Dict[str, Any]:
        possible_keys = {
            "temperature": (-10, 50),
            "pressure": (900, 1100),
            "humidity": (0, 100),
            "speed": (0, 180),
            "voltage": (110, 240),
            "current": (0, 20),
            "altitude": (0, 9000),
            "signal_strength": (-120, -30),
            "cpu_usage": (0, 100),
            "memory_usage": (0, 100),
            "disk_usage": (0, 100),
            "latency": (1, 500),
            "packet_loss": (0, 10),
            "throughput": (1, 1000),
            "session_time": (1, 3600),
            "error_rate": (0, 5),
            "battery_level": (0, 100),
            "fan_speed": (500, 3000),
            "noise_level": (20, 120),
            "power_consumption": (10, 500)
        }

        selected_keys = random.sample(list(possible_keys.keys()), random.randint(5, 10))
        body = {}

        for key in selected_keys:
            min_v, max_v = possible_keys[key]
            body[key] = round(random.uniform(min_v, max_v), 2)

        return body

    # =========================
    # HEADERS GENERATION
    # =========================
    @staticmethod
    def generate_headers() -> Dict[str, str]:
        headers_pool = {
            "Host": lambda: random.choice(["api.example.com", "service.local", "internal.net"]),
            "Authorization": lambda: f"Bearer {uuid.uuid4()}",
            "Content-Type": lambda: "application/json",
            "User-Agent": lambda: random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "curl/8.0",
                "PostmanRuntime/7.35"
            ]),
            "Accept": lambda: random.choice([
                "application/json",
                "text/html",
                "*/*"
            ]),
            "Cookie": lambda: f"session_id={uuid.uuid4()}",
            "Cache-Control": lambda: random.choice([
                "no-cache",
                "max-age=3600",
                "no-store"
            ]),
            "Origin": lambda: random.choice([
                "https://client.app",
                "https://dashboard.local"
            ]),
            "Accept-Encoding": lambda: random.choice([
                "gzip",
                "br",
                "gzip, deflate"
            ]),
            "Referer": lambda: random.choice([
                "https://google.com",
                "https://github.com",
                "https://internal.portal"
            ])
        }

        # Host est obligatoire
        headers = {"Host": headers_pool["Host"]()}

        # Ajouter aléatoirement les autres headers
        optional_headers = list(headers_pool.keys())
        optional_headers.remove("Host")

        selected = random.sample(optional_headers, 9)

        for h in selected:
            headers[h] = headers_pool[h]()

        return headers

    # =========================
    # IP GENERATION (same network)
    # =========================
    @staticmethod
    def generate_ips():
        network = ipaddress.IPv4Network("10.0.0.0/24")
        hosts = list(network.hosts())
        src, dst = random.sample(hosts, 2)
        return str(src), str(dst)

    # =========================
    # FACTORY METHOD
    # =========================
    @staticmethod
    def new():
        src_ip, dst_ip = Packet.generate_ips()

        return Packet(
            id=str(uuid.uuid4()),
            source_ip=src_ip,
            destination_ip=dst_ip,
            headers=Packet.generate_headers(),
            body=Packet.generate_body(),
            timestamp=time.time(),
            status="RAW"
        )
