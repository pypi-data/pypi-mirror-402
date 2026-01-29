import os, time, uuid, threading
from typing import Dict, Optional, Any, Callable, List
import paho.mqtt.client as mqtt

def load_product() -> Dict[str, str]:
    paths: List[str] = []
    here = os.path.dirname(os.path.abspath(__file__))
    paths.append(os.path.join(here, "product"))
    paths.append(os.path.join(os.getcwd(), "product"))

    if os.name != "nt":
        paths.append("/etc/product")

    cfg: Dict[str, str] = {}
    for path in paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        cfg[k.strip()] = v.strip()
            break

    required = ["BROKER_DOMAIN", "DEVICE_NAME", "INSITUTION_NAME", "DEV_NUM"]
    for k in required:
        if k not in cfg:
            raise RuntimeError(f"product file missing key: {k}")

    return cfg

class _StateRegistry:
    _lock = threading.Lock()
    _state: Dict[str, Dict[str, Any]] = {}
    _raw: Dict[str, str] = {}
    _updated: Dict[str, float] = {}

    @classmethod
    def key(cls, topic_header: str, place: str, device: str) -> str:
        return f"{topic_header}/{place}/{device}"

    @classmethod
    def set(cls, key: str, data: Dict[str, Any], raw: str) -> None:
        with cls._lock:
            cls._state[key] = data
            cls._raw[key] = raw
            cls._updated[key] = time.time()

    @classmethod
    def get(cls, key: str) -> Optional[Dict[str, Any]]:
        with cls._lock:
            return cls._state.get(key)

    @classmethod
    def get_raw(cls, key: str) -> Optional[str]:
        with cls._lock:
            return cls._raw.get(key)

    @classmethod
    def get_updated_at(cls, key: str) -> Optional[float]:
        with cls._lock:
            return cls._updated.get(key)

class _MqttBus:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, broker: str):
        self.broker = broker
        self.client = mqtt.Client(client_id=f"aiot-{uuid.uuid4().hex[:8]}")
        self.client.on_message = self._on_message
        self.client.on_connect = self._on_connect

        self._subs = set()
        self._handlers: Dict[str, List[Callable[[str, bytes], None]]] = {}
        self._handlers_lock = threading.Lock()

        self.client.connect(self.broker)
        self.client.loop_start()

    @classmethod
    def get(cls, broker: str) -> "_MqttBus":
        with cls._lock:
            if cls._instance is None:
                cls._instance = _MqttBus(broker)
            return cls._instance

    def _on_connect(self, client, userdata, flags, rc):
        for t in list(self._subs):
            try:
                client.subscribe(t)
            except Exception:
                pass

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload
        with self._handlers_lock:
            cbs = self._handlers.get(topic, [])
        for cb in cbs:
            try:
                cb(topic, payload)
            except Exception:
                pass

    def subscribe_with_handler(self, topic: str, cb: Callable[[str, bytes], None]) -> None:
        with self._handlers_lock:
            self._handlers.setdefault(topic, []).append(cb)

        if topic not in self._subs:
            self._subs.add(topic)
            try:
                self.client.subscribe(topic)
            except Exception:
                pass