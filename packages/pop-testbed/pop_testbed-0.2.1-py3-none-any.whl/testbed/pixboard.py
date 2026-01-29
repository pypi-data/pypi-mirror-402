from .__init__ import load_product, _StateRegistry, _MqttBus
from typing import Dict, Optional, Any, List, Iterable, Literal
import json, time

class Pixboard:
    direction_type = Literal["left","right","up","down","off"]

    def __init__(self):
        self.place = "PIXBOARD" 

        prod = load_product()
        self.BROKER_DOMAIN = prod["BROKER_DOMAIN"]
        self.DEVICE_NAME = prod["DEVICE_NAME"]
        self.INSITUTION_NAME = prod["INSITUTION_NAME"]
        self.DEV_NUM = prod["DEV_NUM"]

        self.TOPIC_HEADER = f"{self.DEVICE_NAME}/{self.INSITUTION_NAME}{self.DEV_NUM}/{self.place}"
        self._state_key = _StateRegistry.key(self.TOPIC_HEADER, self.place, "pixboard")
        self._bus = _MqttBus.get(self.BROKER_DOMAIN)
        self._topic_state = f"{self.TOPIC_HEADER}/STATE"
        self._bus.subscribe_with_handler(self._topic_state, self._on_state_message)

    def _on_state_message(self, topic: str, payload: bytes) -> None:
        raw = payload.decode("utf-8", errors="replace").strip()
        try:
            data = json.loads(raw)
        except Exception:
            data = {"raw": raw}

        _StateRegistry.set(self._state_key, data=data, raw=raw)

    @property
    def state(self) -> Optional[Dict[str, Any]]:
        return _StateRegistry.get(self._state_key)

    @property
    def state_raw(self) -> Optional[str]:
        return _StateRegistry.get_raw(self._state_key)

    @property
    def updated_at(self) -> Optional[float]:
        return _StateRegistry.get_updated_at(self._state_key)

    def text(self, text: str, ts: Optional[float] = None) -> None:
        if ts is None:
            ts = time.time()
        payload = f'{{"ts":{ts:.6f},"text":"{text}"}}'
        topic = f"{self.TOPIC_HEADER}/TEXT/SET"
        result = self._bus.client.publish(topic, payload, qos=1)
        result.wait_for_publish()
    
    def shift(self, shift_dir: direction_type, shift_speed: int, ts: Optional[float] = None) -> None:
        if ts is None:
            ts = time.time()
        payload = f'{{"ts":{ts:.6f},"shift_dir":"{shift_dir}","shift_speed":{shift_speed}}}'
        topic = f"{self.TOPIC_HEADER}/SHIFT/SET"
        result = self._bus.client.publish(topic, payload, qos=1) 
        result.wait_for_publish()
    
    def textColor(self, color: list, ts: Optional[float] = None) -> None:
        if ts is None:
            ts = time.time()
        payload = f'{{"ts":{ts:.6f},"color":{color}}}'
        topic = f"{self.TOPIC_HEADER}/TEXT_COLOR/SET"
        result = self._bus.client.publish(topic, payload, qos=1)
        result.wait_for_publish()

    def bgColor(self, color: list, ts: Optional[float] = None) -> None:
        if ts is None:
            ts = time.time()
        payload = f'{{"ts":{ts:.6f},"color":{color}}}'
        topic = f"{self.TOPIC_HEADER}/BG_COLOR/SET"
        result = self._bus.client.publish(topic, payload, qos=1)
        result.wait_for_publish()