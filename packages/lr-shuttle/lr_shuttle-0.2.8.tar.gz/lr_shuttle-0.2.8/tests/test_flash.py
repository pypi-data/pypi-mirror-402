#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from shuttle import flash
from shuttle.firmware import DEFAULT_BOARD


def test_list_available_boards_includes_default():
    assert DEFAULT_BOARD in flash.list_available_boards()


def test_load_firmware_manifest_returns_segments():
    manifest, package = flash.load_firmware_manifest("esp32c5")
    assert manifest["segments"]
    assert package.endswith("esp32c5")


def test_flash_firmware_invokes_esptool(monkeypatch):
    calls = []

    def fake_run(args):
        calls.append(args)

    monkeypatch.setattr(flash, "_run_esptool", fake_run)

    manifest = flash.flash_firmware(
        port="/dev/ttyUSB0",
        baudrate=921600,
        board="esp32c5",
        erase_first=True,
    )

    assert manifest["label"]
    assert len(calls) == 2  # erase + write
    erase_args, write_args = calls
    assert erase_args[:4] == ["--chip", manifest["chip"], "--port", "/dev/ttyUSB0"]
    assert "write-flash" in write_args
    assert any("devboard.ino.bin" in arg for arg in write_args)


def test_flash_firmware_unknown_board():
    with pytest.raises(flash.FirmwareFlashError):
        flash.flash_firmware(port="/dev/null", baudrate=921600, board="does-not-exist")


def test_flash_firmware_handles_no_compress(monkeypatch):
    calls = []

    def fake_run(args):
        calls.append(args)

    manifest, package = flash.load_firmware_manifest("esp32c5")
    custom_manifest = dict(manifest)
    custom_manifest["compress"] = False

    monkeypatch.setattr(flash, "_run_esptool", fake_run)
    monkeypatch.setattr(
        flash,
        "load_firmware_manifest",
        lambda _board: (custom_manifest, package),
    )

    flash.flash_firmware(port="/dev/ttyUSB0", baudrate=921600)

    assert len(calls) == 1
    assert "--no-compress" in calls[0]


def test_run_esptool_success_with_exit_zero(monkeypatch):
    recorded = []

    def fake_main(args):
        recorded.append(list(args))
        raise SystemExit(0)

    monkeypatch.setattr(flash.esptool, "main", fake_main)

    flash._run_esptool(["ping"])

    assert recorded[0] == ["ping"]


def test_run_esptool_failure(monkeypatch):
    def fake_main(_args):
        raise SystemExit(2)

    monkeypatch.setattr(flash.esptool, "main", fake_main)

    with pytest.raises(flash.FirmwareFlashError):
        flash._run_esptool(["bad"])
