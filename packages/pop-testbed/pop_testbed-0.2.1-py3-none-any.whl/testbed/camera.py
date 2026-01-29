import socket
import struct
import logging
import time
import threading
import cv2
import numpy as np
from typing import Literal
from .__init__ import load_product

LOCATION_TYPE = Literal["entrance", "room"]

logger = logging.getLogger(__name__)

MAX = 1400
TO = 2.0
HDR_FMT = ">IHHQI"
HDR_SIZE = struct.calcsize(HDR_FMT)

class Camera:
    def __init__(self, location:LOCATION_TYPE, server_ip=None, client_port=None, start_timeout=5.0, no_data_timeout=5.0):
        if location == "entrance":
            port = 5000
        elif location == "room":
            port = 5001
        else:
            port = 0
            raise TypeError("Please input correct location type.")
        
        prod = load_product()
        self.server_ip = prod["CAMERA_DOMAIN"] if server_ip is None else server_ip
        self.server_port = port
        self.client_port = client_port

        self.start_timeout = start_timeout
        self.no_data_timeout = no_data_timeout

        self._sock = None
        self._thread = None
        self._running = threading.Event()

        self._last_frame = None
        self._last_frame_id = None
        self._lock = threading.Lock()

        self._first_frame_event = threading.Event()

    def start(self):
        if self._running.is_set():
            return
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
        if self.client_port is None:
            self._sock.bind(("", 0))
            self.client_port = self._sock.getsockname()[1]
        else:
            self._sock.bind(("", self.client_port))
        self._sock.settimeout(1.0)
        self._running.set()
        self._first_frame_event.clear()
        try:
            self._sock.sendto(b"HELLO", (self.server_ip, self.server_port))
        except Exception as e:
            logger.error("failed to send HELLO: %s", e)
        self._thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._thread.start()
        logger.info("Camera started on port %d", self.client_port)
        if not self._first_frame_event.wait(timeout=self.start_timeout):
            logger.error("no frame received within %.1f seconds after start", self.start_timeout)
            self.stop()
            raise RuntimeError("no frame received from server")

    def stop(self):
        if not self._running.is_set():
            return
        self._running.clear()
        if self._sock is not None:
            try:
                self._sock.sendto(b"BYE", (self.server_ip, self.server_port))
            except Exception:
                pass
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("Camera stopped")

    def _recv_loop(self):
        fbuf = {}
        frame_count = 0
        last_data_time = time.time()
        while self._running.is_set():
            now = time.time()
            if now - last_data_time > self.no_data_timeout:
                logger.error("no camera data for %.1f seconds, stopping client", self.no_data_timeout)
                self._running.clear()
                break
            try:
                try:
                    d, _ = self._sock.recvfrom(MAX)
                except socket.timeout:
                    now = time.time()
                    drop = [k for k, v in fbuf.items() if now - v["t"] > TO]
                    for k in drop:
                        del fbuf[k]
                    continue
            except OSError:
                break
            last_data_time = time.time()
            if len(d) < HDR_SIZE:
                continue
            try:
                fid, idx, tot, ts_us, size = struct.unpack(HDR_FMT, d[:HDR_SIZE])
            except struct.error:
                continue
            pay = d[HDR_SIZE:]
            f = fbuf.get(fid)
            if f is None:
                f = {"t": time.time(), "tot": tot, "p": {}, "ts": ts_us, "sz": size}
                fbuf[fid] = f
            f["p"][idx] = pay
            if len(f["p"]) == f["tot"]:
                try:
                    j = b"".join(f["p"][i] for i in range(f["tot"]))
                except KeyError:
                    del fbuf[fid]
                    continue
                if len(j) != f["sz"]:
                    logger.warning("size mismatch frame=%d expected=%d got=%d", fid, f["sz"], len(j))
                a = np.frombuffer(j, np.uint8)
                img = cv2.imdecode(a, cv2.IMREAD_COLOR)
                if img is not None:
                    with self._lock:
                        self._last_frame = img
                        self._last_frame_id = fid
                    if not self._first_frame_event.is_set():
                        self._first_frame_event.set()
                    frame_count += 1
                    if frame_count % 100 == 0:
                        logger.info("received frame=%d", fid)
                del fbuf[fid]

    def read(self, copy=True):
        with self._lock:
            if self._last_frame is None:
                return None
            if copy:
                return self._last_frame.copy()
            return self._last_frame


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    client = Camera()
    try:
        client.start()
    except RuntimeError as e:
        logger.error("failed to start client: %s", e)
    else:
        try:
            while True:
                frame = client.read()
                time.sleep(0.01)
        except KeyboardInterrupt:
            pass
        finally:
            client.stop()
