from .__init__ import load_product, _StateRegistry, _MqttBus
from typing import Dict, Optional, Any, List, Iterable
import time, json

class SensorBase:
    NAME = "SENSOR"
    PLACE: List[str] = []

    LEAF = "STATE"

    def __init__(self, place: str):
        place_norm = place.strip().upper()
        if self.PLACE and place_norm not in self.PLACE:
            raise ValueError(f"{self.NAME}: invalid place '{place}'. allowed={self.PLACE}")

        self.place = place_norm

        prod = load_product()
        self.BROKER_DOMAIN = prod["BROKER_DOMAIN"]
        self.DEVICE_NAME = prod["DEVICE_NAME"]
        self.INSITUTION_NAME = prod["INSITUTION_NAME"]
        self.DEV_NUM = prod["DEV_NUM"]

        self.TOPIC_HEADER = f"{self.DEVICE_NAME}/{self.INSITUTION_NAME}{self.DEV_NUM}"

        self._value_key = _StateRegistry.key(self.TOPIC_HEADER, self.place, self.NAME)

        self._bus = _MqttBus.get(self.BROKER_DOMAIN)

        self._topic_value = f"{self.TOPIC_HEADER}/{self.place}/{self.NAME}/{self.LEAF}"
        self._bus.subscribe_with_handler(self._topic_value, self._on_value_message)

    def _on_value_message(self, topic: str, payload: bytes) -> None:
        raw = payload.decode("utf-8", errors="replace").strip()
        try:
            data = json.loads(raw)
        except Exception:
            data = {"raw": raw}

        _StateRegistry.set(self._value_key, data=data, raw=raw)

    def read(self) -> Optional[Dict[str, Any]]:
        return _StateRegistry.get(self._value_key)

    @property
    def raw(self) -> Optional[str]:
        return _StateRegistry.get_raw(self._value_key)

    @property
    def updated_at(self) -> Optional[float]:
        return _StateRegistry.get_updated_at(self._value_key)

    def is_stale(self, max_age_sec: float) -> bool:
        ua = self.updated_at
        if ua is None:
            return True
        return (time.time() - ua) > max_age_sec

class Tphg(SensorBase):
    NAME = "TPHG"
    PLACE = ["ENTRANCE", "ROOM", "KITCHEN"]

class TphgGroup:
    def __init__(self, places: Optional[Iterable[str]] = None):
        if places is None:
            places = Tphg.PLACE
        self._sensors: Dict[str, Tphg] = {p.upper(): Tphg(p) for p in places}

    def read(self) -> Dict[str, Optional[Dict[str, Any]]]:
        return {p: s.read() for p, s in self._sensors.items()}

    def get(self, place: str) -> Tphg:
        return self._sensors[place.upper()]

class Light(SensorBase):
    NAME = "LIGHT"
    PLACE = ["ENTRANCE", "ROOM", "KITCHEN"]

class LightGroup:
    def __init__(self, places: Optional[Iterable[str]] = None):
        if places is None:
            places = Light.PLACE
        self._sensors: Dict[str, Light] = {p.upper(): Light(p) for p in places}

    def read(self) -> Dict[str, Optional[Dict[str, Any]]]:
        return {p: s.read() for p, s in self._sensors.items()}

    def get(self, place: str) -> Light:
        return self._sensors[place.upper()]

class Switch(SensorBase):
    NAME = "Switch"
    PLACE = ["ENTRANCE", "ROOM", "KITCHEN"]

class SwitchGroup:
    def __init__(self, places: Optional[Iterable[str]] = None):
        if places is None:
            places = Switch.PLACE
        self._sensors: Dict[str, Switch] = {p.upper(): Switch(p) for p in places}

    def read(self) -> Dict[str, Optional[Dict[str, Any]]]:
        return {p: s.read() for p, s in self._sensors.items()}

    def get(self, place: str) -> Switch:
        return self._sensors[place.upper()]

class Impact(SensorBase):
    NAME = "IMPACT"
    PLACE = ["ENTRANCE", "ROOM", "KITCHEN"]
    
class ImpactGroup:
    def __init__(self, places: Optional[Iterable[str]] = None):
        if places is None:
            places = Impact.PLACE
        self._sensors: Dict[str, Impact] = {p.upper(): Impact(p) for p in places}

    def read(self) -> Dict[str, Optional[Dict[str, Any]]]:
        return {p: s.read() for p, s in self._sensors.items()}

    def get(self, place: str) -> Impact:
        return self._sensors[place.upper()]

class Pir(SensorBase):
    NAME = "PIR"
    PLACE = ["ENTRANCE"]
    
    def __init__(self):
        super().__init__(self.PLACE[0])

class Dust(SensorBase):
    NAME = "DUST"
    PLACE = ["ROOM"]
    
    def __init__(self):
        super().__init__(self.PLACE[0])

class GasDetector(SensorBase):
    NAME = "GASDETECTOR"
    PLACE = ["KITCHEN"]
    
    def __init__(self):
        super().__init__(self.PLACE[0])