from .__init__ import load_product, _StateRegistry, _MqttBus
from typing import Dict, Optional, Any, List, Iterable, Literal
import json, time

class ActuatorBase:
    NAME = "DEVICE"
    PLACE: List[str] = []

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
        self._state_key = _StateRegistry.key(self.TOPIC_HEADER, self.place, self.NAME)
        self._bus = _MqttBus.get(self.BROKER_DOMAIN)
        self._topic_state = f"{self.TOPIC_HEADER}/{self.place}/{self.NAME}/STATE"
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

    def _publish_set_state_fast(self, state_str: str, ts: Optional[float] = None) -> None:
        if ts is None:
            ts = time.time()
        payload = f'{{"ts":{ts:.6f},"state":"{state_str}"}}'
        topic = f"{self.TOPIC_HEADER}/{self.place}/{self.NAME}/SET"
        self._bus.client.publish(topic, payload, qos=1)

class Led(ActuatorBase):
    NAME = "LED"
    PLACE = ["ENTRANCE", "ROOM", "KITCHEN"]

    def setColor(self, color: str) -> None:
        self._publish_set_state_fast(color)

class LedGroup:
    def __init__(self, places: Optional[Iterable[str]] = None):
        if places is None:
            places = Led.PLACE
        self._leds: Dict[str, Led] = {p.upper(): Led(p) for p in places}

    def setColor(self, color: str, place: Optional[str] = None) -> None:
        if place is None:
            for l in self._leds.values():
                l.setColor(color)
        else:
            self._leds[place.upper()].setColor(color)

    @property
    def state(self) -> Dict[str, Optional[Dict[str, Any]]]:
        return {p: l.state for p, l in self._lamps.items()}

    def get(self, place: str) -> Led:
        return self._leds[place.upper()]

class Lamp(ActuatorBase):
    NAME = "LAMP"
    PLACE = ["ENTRANCE", "ROOM", "KITCHEN"]

    def on(self) -> None:
        self._publish_set_state_fast("ON")

    def off(self) -> None:
        self._publish_set_state_fast("OFF")
        
class LampGroup:
    def __init__(self, places: Optional[Iterable[str]] = None):
        if places is None:
            places = Lamp.PLACE
        self._lamps: Dict[str, Lamp] = {p.upper(): Lamp(p) for p in places}

    def on(self, place: Optional[str] = None) -> None:
        if place is None:
            for l in self._lamps.values():
                l.on()
        else:
            self._lamps[place.upper()].on()

    def off(self, place: Optional[str] = None) -> None:
        if place is None:
            for l in self._lamps.values():
                l.off()
        else:
            self._lamps[place.upper()].off()

    @property
    def state(self) -> Dict[str, Optional[Dict[str, Any]]]:
        return {p: l.state for p, l in self._lamps.items()}

    def get(self, place: str) -> Lamp:
        return self._lamps[place.upper()]
    
class Fan(ActuatorBase):
    NAME = "FAN"
    PLACE = ["ROOM", "KITCHEN"]

    def on(self) -> None:
        self._publish_set_state_fast("ON")

    def off(self) -> None:
        self._publish_set_state_fast("OFF")
        
class FanGroup:
    def __init__(self, places: Optional[Iterable[str]] = None):
        if places is None:
            places = Fan.PLACE
        self._fans: Dict[str, Fan] = {p.upper(): Fan(p) for p in places}

    def on(self, place: Optional[str] = None) -> None:
        if place is None:
            for l in self._fans.values():
                l.on()
        else:
            self._fans[place.upper()].on()

    def off(self, place: Optional[str] = None) -> None:
        if place is None:
            for l in self._fans.values():
                l.off()
        else:
            self._fans[place.upper()].off()

    @property
    def state(self) -> Dict[str, Optional[Dict[str, Any]]]:
        return {p: l.state for p, l in self._fans.items()}

    def get(self, place: str) -> Fan:
        return self._fans[place.upper()]

class DoorLock(ActuatorBase):
    NAME = "DOORLOCK"
    PLACE = ["ENTRANCE"]
    
    def __init__(self):
        super().__init__(self.PLACE[0])

    def open(self) -> None:
        self._publish_set_state_fast("OPEN")

    def close(self) -> None:
        self._publish_set_state_fast("CLOSE")

class Curtain(ActuatorBase):
    NAME = "CURTAIN"
    PLACE = ["ROOM"]
    
    def __init__(self):
        super().__init__(self.PLACE[0])

    def open(self) -> None:
        self._publish_set_state_fast("OPEN")

    def close(self) -> None:
        self._publish_set_state_fast("CLOSE")
    
    def stop(self) -> None:
        self._publish_set_state_fast("STOP")

class GasBreaker(ActuatorBase):
    NAME = "GASBREAKER"
    PLACE = ["KITCHEN"]
    
    def __init__(self):
        super().__init__(self.PLACE[0])

    def open(self) -> None:
        self._publish_set_state_fast("OPEN")

    def close(self) -> None:
        self._publish_set_state_fast("CLOSE")