import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime

import serial
import serial.tools.list_ports

logger = logging.getLogger(__name__)

PARITY_MAP = {
    "none": serial.PARITY_NONE,
    "even": serial.PARITY_EVEN,
    "odd": serial.PARITY_ODD,
    "mark": serial.PARITY_MARK,
    "space": serial.PARITY_SPACE,
}

STOPBITS_MAP = {
    1: serial.STOPBITS_ONE,
    1.5: serial.STOPBITS_ONE_POINT_FIVE,
    2: serial.STOPBITS_TWO,
}

BYTESIZE_MAP = {
    5: serial.FIVEBITS,
    6: serial.SIXBITS,
    7: serial.SEVENBITS,
    8: serial.EIGHTBITS,
}


@dataclass
class ManagedPort:
    port_id: str
    device_path: str
    serial_instance: serial.Serial
    opened_at: datetime = field(default_factory=datetime.now)
    config: dict = field(default_factory=dict)


class PortManager:
    def __init__(self):
        self._ports: dict[str, ManagedPort] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def list_available_ports() -> list[dict]:
        return [
            {
                "device": port.device,
                "description": port.description,
                "hwid": port.hwid,
                "manufacturer": port.manufacturer,
                "product": port.product,
                "serial_number": port.serial_number,
                "vid": port.vid,
                "pid": port.pid,
            }
            for port in serial.tools.list_ports.comports()
        ]

    async def open_port(
        self,
        device_path: str,
        baud_rate: int = 9600,
        data_bits: int = 8,
        parity: str = "none",
        stop_bits: float = 1,
        timeout: float = 1.0,
        rtscts: bool = False,
        xonxoff: bool = False,
    ) -> str:
        async with self._lock:
            for pid, managed in self._ports.items():
                if managed.device_path == device_path:
                    raise ValueError(f"Port {device_path} already open as {pid}")

            port_id = str(uuid.uuid4())[:8]

            try:
                ser = serial.Serial(
                    port=device_path,
                    baudrate=baud_rate,
                    bytesize=BYTESIZE_MAP.get(data_bits, serial.EIGHTBITS),
                    parity=PARITY_MAP.get(parity.lower(), serial.PARITY_NONE),
                    stopbits=STOPBITS_MAP.get(stop_bits, serial.STOPBITS_ONE),
                    timeout=timeout,
                    rtscts=rtscts,
                    xonxoff=xonxoff,
                )

                self._ports[port_id] = ManagedPort(
                    port_id=port_id,
                    device_path=device_path,
                    serial_instance=ser,
                    config={
                        "baud_rate": baud_rate,
                        "data_bits": data_bits,
                        "parity": parity,
                        "stop_bits": stop_bits,
                        "timeout": timeout,
                        "rtscts": rtscts,
                        "xonxoff": xonxoff,
                    },
                )

                logger.info(f"Opened port {device_path} as {port_id}")
                return port_id

            except Exception as e:
                logger.error(f"Failed to open {device_path}: {e}")
                raise

    async def read_bytes(
        self, port_id: str, num_bytes: int, timeout: float
    ) -> tuple[bytes, bool]:
        managed = self._get_port(port_id)
        original_timeout = managed.serial_instance.timeout
        managed.serial_instance.timeout = timeout

        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, managed.serial_instance.read, num_bytes
            )
            return data, len(data) < num_bytes
        finally:
            managed.serial_instance.timeout = original_timeout

    async def read_until(
        self, port_id: str, terminator: bytes, timeout: float, max_bytes: int
    ) -> tuple[bytes, bool]:
        managed = self._get_port(port_id)
        original_timeout = managed.serial_instance.timeout
        managed.serial_instance.timeout = timeout

        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, managed.serial_instance.read_until, terminator, max_bytes
            )
            return data, not data.endswith(terminator)
        finally:
            managed.serial_instance.timeout = original_timeout

    async def read_for_duration(
        self, port_id: str, duration: float, max_bytes: int
    ) -> bytes:
        managed = self._get_port(port_id)
        original_timeout = managed.serial_instance.timeout
        managed.serial_instance.timeout = 0.1

        collected_data = bytearray()
        loop = asyncio.get_event_loop()
        start_time = loop.time()

        try:
            while (loop.time() - start_time) < duration:
                if len(collected_data) >= max_bytes:
                    break

                chunk = await loop.run_in_executor(
                    None,
                    managed.serial_instance.read,
                    min(1024, max_bytes - len(collected_data)),
                )
                if chunk:
                    collected_data.extend(chunk)

                await asyncio.sleep(0.01)

            return bytes(collected_data)
        finally:
            managed.serial_instance.timeout = original_timeout

    async def write_data(self, port_id: str, data: bytes) -> int:
        managed = self._get_port(port_id)
        loop = asyncio.get_event_loop()
        bytes_written = await loop.run_in_executor(
            None, managed.serial_instance.write, data
        )
        await loop.run_in_executor(None, managed.serial_instance.flush)
        return bytes_written

    async def send_break(self, port_id: str, duration: float):
        managed = self._get_port(port_id)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, managed.serial_instance.send_break, duration
        )

    async def close_port(self, port_id: str):
        async with self._lock:
            if port_id not in self._ports:
                raise ValueError(f"Port {port_id} not found")

            managed = self._ports.pop(port_id)
            if managed.serial_instance.is_open:
                managed.serial_instance.close()

            logger.info(f"Closed port {port_id}")

    async def close_all(self):
        async with self._lock:
            for port_id in list(self._ports.keys()):
                try:
                    managed = self._ports.pop(port_id)
                    if managed.serial_instance.is_open:
                        managed.serial_instance.close()
                    logger.info(f"Closed port {port_id}")
                except Exception as e:
                    logger.error(f"Error closing {port_id}: {e}")

    def _get_port(self, port_id: str) -> ManagedPort:
        if port_id not in self._ports:
            raise ValueError(f"Port {port_id} not found")
        return self._ports[port_id]

    def get_port_status(self, port_id: str) -> dict | None:
        if port_id not in self._ports:
            return None

        managed = self._ports[port_id]
        ser = managed.serial_instance

        status = {
            "port_id": port_id,
            "device": managed.device_path,
            "is_open": ser.is_open,
            "opened_at": managed.opened_at.isoformat(),
            "config": managed.config,
        }

        if ser.is_open:
            for attr in ("in_waiting", "out_waiting", "cts", "dsr", "ri", "cd"):
                try:
                    status[attr] = getattr(ser, attr)
                except OSError:
                    status[attr] = None

        return status

    def list_managed_ports(self) -> list[dict]:
        return [
            {
                "port_id": p.port_id,
                "device": p.device_path,
                "opened_at": p.opened_at.isoformat(),
                "config": p.config,
                "is_open": p.serial_instance.is_open,
            }
            for p in self._ports.values()
        ]
