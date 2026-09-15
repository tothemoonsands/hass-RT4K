"""Tests for RetroTINK serial connection helpers."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "retrotink"
    / "connection.py"
)
SPEC = importlib.util.spec_from_file_location("retrotink_connection", MODULE_PATH)
connection = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(connection)


class OpenSerialConnectionTest(unittest.TestCase):
    """Test local and RFC2217 connection setup."""

    def test_opens_local_serial_path(self) -> None:
        """Local serial device paths remain supported."""
        with patch.object(connection.serial, "serial_for_url") as serial_for_url:
            connection.open_serial_connection("/dev/ttyUSB0")

        serial_for_url.assert_called_once_with(
            "/dev/ttyUSB0",
            baudrate=115200,
            bytesize=connection.serial.EIGHTBITS,
            stopbits=connection.serial.STOPBITS_ONE,
            parity=connection.serial.PARITY_NONE,
            timeout=1,
        )

    def test_opens_rfc2217_url(self) -> None:
        """RFC2217 URLs are passed to PySerial's URL-aware factory."""
        with patch.object(connection.serial, "serial_for_url") as serial_for_url:
            connection.open_serial_connection("rfc2217://192.168.1.95:4000")

        serial_for_url.assert_called_once_with(
            "rfc2217://192.168.1.95:4000",
            baudrate=115200,
            bytesize=connection.serial.EIGHTBITS,
            stopbits=connection.serial.STOPBITS_ONE,
            parity=connection.serial.PARITY_NONE,
            timeout=1,
        )


if __name__ == "__main__":
    unittest.main()
