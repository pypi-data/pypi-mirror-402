#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from shuttle import prodtest


def test_mask_from_hex_parses_and_formats():
    mask = prodtest.mask_from_hex("0000000000000004")
    assert mask == bytes.fromhex("0000000000000004")
    assert prodtest.mask_to_hex(mask) == "0000000000000004"


def test_mask_from_hex_validations():
    with pytest.raises(ValueError):
        prodtest.mask_from_hex("0000")
    with pytest.raises(ValueError):
        prodtest.mask_from_hex("zzzzzzzzzzzzzzzz")


def test_io_self_test_requires_eight_bytes():
    with pytest.raises(ValueError):
        prodtest.io_self_test(b"\x00")


def test_io_self_test_frames():
    mask = prodtest.mask_from_hex("000000000000000f")
    frames = prodtest.io_self_test(mask)
    assert len(frames) == 2
    assert frames[0]["tx"] == (b"T" + mask).hex()
    assert frames[0]["wait_irq"] == {
        "edge": "trailing",
        "timeout_us": prodtest.IO_SELF_TEST_IRQ_TIMEOUT_US,
    }
    assert (
        frames[1]["tx"]
        == bytes(
            [prodtest.IO_SELF_TEST_DUMMY_BYTE] * prodtest.IO_SELF_TEST_MASK_LEN
        ).hex()
    )


def test_reset_waits_for_irq():
    frame = prodtest.reset_transfer()
    assert frame["tx"] == bytes([prodtest.RESET_OPCODE]).hex()
    assert frame["wait_irq"] == {
        "edge": "leading",
        "timeout_us": prodtest.RESET_IRQ_TIMEOUT_US,
    }


def test_pins_from_mask_and_failures():
    requested = prodtest.mask_from_hex("000000000000000F")
    result = prodtest.mask_from_hex("0000000000000005")
    assert prodtest.pins_from_mask(result) == [1, 3]
    assert prodtest.failed_pins(requested, result) == [2, 4]


def test_command_builder_and_limits():
    cmd = prodtest.command(ord("a"), [0x00, 0xFF])
    assert cmd["tx"] == "6100ff"
    assert cmd["n"] == 3
    with pytest.raises(ValueError):
        prodtest.command(ord("a"), [256])


def test_continuous_transmitter_command():
    frame = prodtest.continuous_transmitter(0x2A, 7)
    assert frame["tx"] == "6f2a07"
    assert frame["n"] == 3
    assert frame["wait_irq"] == {
        "edge": "trailing",
        "timeout_us": prodtest.CONTINUOUS_TX_IRQ_TIMEOUT_US,
    }


def test_hw_device_id_sequence():
    frames = prodtest.hw_device_id_sequence()
    assert len(frames) == 2
    assert frames[0]["tx"] == "49"
    assert frames[0]["wait_irq"] == {
        "edge": "trailing",
        "timeout_us": prodtest.HW_DEVICE_ID_IRQ_TIMEOUT_US,
    }
    expected = bytes(
        [prodtest.HW_DEVICE_ID_DUMMY_BYTE] * prodtest.HW_DEVICE_ID_RESULT_LEN
    )
    assert frames[1]["tx"] == expected.hex()


def test_serial_number_read_sequence():
    frames = prodtest.serial_number_read_sequence()
    assert len(frames) == 2
    assert frames[0]["tx"] == "78"
    assert frames[0]["wait_irq"] == {
        "edge": "trailing",
        "timeout_us": prodtest.SERIAL_NUMBER_IRQ_TIMEOUT_US,
    }
    expected = bytes([prodtest.SERIAL_NUMBER_DUMMY_BYTE] * prodtest.SERIAL_NUMBER_LEN)
    assert frames[1]["tx"] == expected.hex()


def test_serial_number_write_validates_length():
    serial = bytes(range(8))
    cmd = prodtest.serial_number_write(serial)
    assert cmd["tx"] == (b"X" + serial).hex()
    assert cmd["wait_irq"] == {
        "edge": "trailing",
        "timeout_us": prodtest.SERIAL_NUMBER_IRQ_TIMEOUT_US,
    }
    with pytest.raises(ValueError):
        prodtest.serial_number_write(b"\x00")


def test_config_read_sequence_and_write():
    frames = prodtest.config_read_sequence()
    assert len(frames) == 2
    assert frames[0]["tx"] == "72"
    assert frames[0]["wait_irq"] == {
        "edge": "trailing",
        "timeout_us": prodtest.CONFIG_IRQ_TIMEOUT_US,
    }
    expected = bytes([prodtest.CONFIG_DUMMY_BYTE] * prodtest.CONFIG_RESULT_LEN)
    assert frames[1]["tx"] == expected.hex()

    payload = bytes(range(5))
    cmd = prodtest.config_write(payload)
    assert cmd["tx"] == (b"R" + payload).hex()
    assert cmd["wait_irq"] == {
        "edge": "trailing",
        "timeout_us": prodtest.CONFIG_IRQ_TIMEOUT_US,
    }
    with pytest.raises(ValueError):
        prodtest.config_write(b"\x00")


def test_erase_nvmc_validates_length():
    hw_id = bytes(range(8))
    cmd = prodtest.erase_nvmc(hw_id)
    assert cmd["tx"] == (b"e" + hw_id).hex()
    assert cmd["wait_irq"] == {
        "edge": "trailing",
        "timeout_us": prodtest.ERASE_NVMC_IRQ_TIMEOUT_US,
    }
    with pytest.raises(ValueError):
        prodtest.erase_nvmc(b"\x00")
