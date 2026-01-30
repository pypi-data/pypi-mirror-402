#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Helpers for the prodtest SPI command protocol."""

from __future__ import annotations

from typing import Iterable, Sequence

from . import timo

RESET_OPCODE = ord("?")
PLUS_OPCODE = ord("+")
ANTENNA_OPCODE = ord("a")
CONTINUOUS_TX_OPCODE = ord("o")
HW_DEVICE_ID_OPCODE = ord("I")
SERIAL_NUMBER_READ_OPCODE = ord("x")
SERIAL_NUMBER_WRITE_OPCODE = ord("X")
CONFIG_READ_OPCODE = ord("r")
CONFIG_WRITE_OPCODE = ord("R")
ERASE_NVMC_OPCODE = ord("e")
IO_SELF_TEST_OPCODE = ord("T")
IO_SELF_TEST_MASK_LEN = 8
IO_SELF_TEST_DUMMY_BYTE = 0xFF
IO_SELF_TEST_IRQ_TIMEOUT_US = 500_000
RESET_IRQ_TIMEOUT_US = 200_000
CONTINUOUS_TX_IRQ_TIMEOUT_US = 100_000
HW_DEVICE_ID_RESULT_LEN = 8
HW_DEVICE_ID_DUMMY_BYTE = 0xFF
HW_DEVICE_ID_IRQ_TIMEOUT_US = 100_000
SERIAL_NUMBER_LEN = 8
SERIAL_NUMBER_DUMMY_BYTE = 0xFF
SERIAL_NUMBER_IRQ_TIMEOUT_US = 100_000
CONFIG_RESULT_LEN = 6
CONFIG_WRITE_LEN = 5
CONFIG_DUMMY_BYTE = 0xFF
CONFIG_IRQ_TIMEOUT_US = 100_000
ERASE_NVMC_LEN = 8
ERASE_NVMC_IRQ_TIMEOUT_US = 500_000


def _ensure_byte(value: int) -> int:
    if not 0 <= value <= 0xFF:
        raise ValueError("Prodtest arguments must be in range 0..255")
    return value


def _build_command_bytes(opcode: int, arguments: Iterable[int] | bytes = ()) -> bytes:
    """Build raw bytes from an opcode and a sequence of byte arguments."""

    if isinstance(arguments, bytes):
        payload = arguments
    else:
        payload = bytes(_ensure_byte(arg) for arg in arguments)
    return bytes([opcode]) + payload


def command(
    opcode: int,
    arguments: Iterable[int] | bytes = (),
    *,
    params: dict | None = None,
) -> dict:
    """Build an NDJSON-ready spi.xfer payload for a prodtest command."""

    return timo.command_payload(_build_command_bytes(opcode, arguments), params=params)


def reset() -> dict:
    """Return the prodtest reset command (single '?' byte)."""

    return timo.command_payload(
        bytes([RESET_OPCODE]),
        params={
            "wait_irq": {
                "edge": "leading",
                "timeout_us": RESET_IRQ_TIMEOUT_US,
            }
        },
    )


def reset_transfer() -> dict:
    """Reset command packaged as an NDJSON-ready payload."""

    return reset()


def select_antenna(selection: int) -> dict:
    """Return the prodtest antenna command for the given antenna index."""

    return command(ANTENNA_OPCODE, [selection])


def continuous_transmitter(channel: int, power_level: int) -> dict:
    """Return the prodtest continuous transmitter command (opcode 'o')."""

    return command(
        CONTINUOUS_TX_OPCODE,
        [channel, power_level],
        params={
            "wait_irq": {
                "edge": "trailing",
                "timeout_us": CONTINUOUS_TX_IRQ_TIMEOUT_US,
            }
        },
    )


def hw_device_id_sequence() -> Sequence[dict]:
    """Return the SPI frames required to read the HW Device ID (opcode 'I')."""

    command = timo.command_payload(
        bytes([HW_DEVICE_ID_OPCODE]),
        params={
            "wait_irq": {
                "edge": "trailing",
                "timeout_us": HW_DEVICE_ID_IRQ_TIMEOUT_US,
            }
        },
    )
    readback = timo.command_payload(
        bytes([HW_DEVICE_ID_DUMMY_BYTE] * HW_DEVICE_ID_RESULT_LEN)
    )
    return (command, readback)


def serial_number_read_sequence() -> Sequence[dict]:
    """Return the SPI frames required to read the prodtest serial number (opcode 'x')."""

    command = timo.command_payload(
        bytes([SERIAL_NUMBER_READ_OPCODE]),
        params={
            "wait_irq": {
                "edge": "trailing",
                "timeout_us": SERIAL_NUMBER_IRQ_TIMEOUT_US,
            }
        },
    )
    readback = timo.command_payload(
        bytes([SERIAL_NUMBER_DUMMY_BYTE] * SERIAL_NUMBER_LEN)
    )
    return (command, readback)


def serial_number_write(serial_bytes: bytes) -> dict:
    """Build the prodtest serial-number write command (opcode 'X')."""

    if len(serial_bytes) != SERIAL_NUMBER_LEN:
        raise ValueError("Serial number must be exactly 8 bytes")
    return command(
        SERIAL_NUMBER_WRITE_OPCODE,
        serial_bytes,
        params={
            "wait_irq": {
                "edge": "trailing",
                "timeout_us": SERIAL_NUMBER_IRQ_TIMEOUT_US,
            }
        },
    )


def config_read_sequence() -> Sequence[dict]:
    """Return the SPI frames required to read the prodtest config (opcode 'r')."""

    command = timo.command_payload(
        bytes([CONFIG_READ_OPCODE]),
        params={
            "wait_irq": {
                "edge": "trailing",
                "timeout_us": CONFIG_IRQ_TIMEOUT_US,
            }
        },
    )
    readback = timo.command_payload(bytes([CONFIG_DUMMY_BYTE] * CONFIG_RESULT_LEN))
    return (command, readback)


def config_write(config_bytes: bytes) -> dict:
    """Build the prodtest config write command (opcode 'R')."""

    if len(config_bytes) != CONFIG_WRITE_LEN:
        raise ValueError("Config payload must be exactly 5 bytes")
    return command(
        CONFIG_WRITE_OPCODE,
        config_bytes,
        params={
            "wait_irq": {
                "edge": "trailing",
                "timeout_us": CONFIG_IRQ_TIMEOUT_US,
            }
        },
    )


def erase_nvmc(hw_id: bytes) -> dict:
    """Build the prodtest erase command (opcode 'e')."""

    if len(hw_id) != ERASE_NVMC_LEN:
        raise ValueError("Erase requires an 8-byte HW Device ID argument")
    return command(
        ERASE_NVMC_OPCODE,
        hw_id,
        params={
            "wait_irq": {
                "edge": "trailing",
                "timeout_us": ERASE_NVMC_IRQ_TIMEOUT_US,
            }
        },
    )


def ping_sequence() -> Sequence[dict]:
    """Return the two SPI frames for the prodtest ping action ('+' then dummy)."""
    # First transfer: send '+' (PLUS_OPCODE), expect response (should be ignored)
    # Second transfer: send dummy (0xFF), expect '-' (0x2D) back
    return [
        timo.command_payload(bytes([PLUS_OPCODE])),
        timo.command_payload(bytes([0xFF])),
    ]


def io_self_test(mask: bytes) -> Sequence[dict]:
    """Return the two SPI frames required to run the GPIO self-test."""

    if len(mask) != IO_SELF_TEST_MASK_LEN:
        raise ValueError("IO self-test mask must be exactly 8 bytes")
    command = _build_command_bytes(IO_SELF_TEST_OPCODE, mask)
    readback = bytes([IO_SELF_TEST_DUMMY_BYTE] * IO_SELF_TEST_MASK_LEN)
    return (
        timo.command_payload(
            command,
            params={
                "wait_irq": {
                    "edge": "trailing",
                    "timeout_us": IO_SELF_TEST_IRQ_TIMEOUT_US,
                }
            },
        ),
        timo.command_payload(readback),
    )


def mask_from_hex(value: str) -> bytes:
    """Parse a hex-encoded mask and ensure it is 8 bytes long."""

    trimmed = value.strip().lower()
    if len(trimmed) != IO_SELF_TEST_MASK_LEN * 2:
        raise ValueError("Mask must be 16 hex characters (8 bytes)")
    try:
        decoded = bytes.fromhex(trimmed)
    except ValueError as exc:
        raise ValueError("Mask must be a valid hex string") from exc
    return decoded


def mask_to_hex(mask: bytes) -> str:
    """Render the mask as an uppercase hex string."""

    return mask.hex().upper()


def pins_from_mask(mask: bytes) -> list[int]:
    """Return the 1-indexed pin numbers enabled in the bitmask."""

    pins: list[int] = []
    for byte_offset, byte_value in enumerate(reversed(mask)):
        for bit in range(8):
            if byte_value & (1 << bit):
                pins.append(byte_offset * 8 + bit + 1)
    return pins


def failed_pins(request_mask: bytes, result_mask: bytes) -> list[int]:
    """Return sorted pin numbers that were requested but did not pass."""

    requested = set(pins_from_mask(request_mask))
    passed = set(pins_from_mask(result_mask))
    failures = sorted(requested - passed)
    return failures
