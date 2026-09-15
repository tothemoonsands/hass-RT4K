"""Serial connection helpers for the RetroTINK integration."""
from __future__ import annotations

import serial

SERIAL_BAUD_RATE = 115200
SERIAL_TIMEOUT = 1


def open_serial_connection(serial_port: str) -> serial.SerialBase:
    """Open a local serial device or a PySerial URL."""
    return serial.serial_for_url(
        serial_port,
        baudrate=SERIAL_BAUD_RATE,
        bytesize=serial.EIGHTBITS,
        stopbits=serial.STOPBITS_ONE,
        parity=serial.PARITY_NONE,
        timeout=SERIAL_TIMEOUT,
    )
