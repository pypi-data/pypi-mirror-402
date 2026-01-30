#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Helpers for flashing embedded firmware bundles to the devboard."""

from __future__ import annotations

import json
from contextlib import ExitStack
from importlib import resources
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import esptool

from .firmware import DEFAULT_BOARD


class FirmwareFlashError(RuntimeError):
    """Raised when preparing or flashing bundled firmware fails."""


def list_available_boards() -> List[str]:
    """Return the set of firmware bundles shipped with the package."""

    firmware_pkg = resources.files("shuttle.firmware")
    return sorted(child.name for child in firmware_pkg.iterdir() if child.is_dir())


def load_firmware_manifest(board: str) -> Tuple[Dict[str, object], str]:
    """Load the manifest for the requested firmware bundle."""

    package = f"shuttle.firmware.{board}"
    try:
        manifest_path = resources.files(package) / "manifest.json"
    except ModuleNotFoundError as exc:
        raise FirmwareFlashError(f"Unknown firmware target '{board}'") from exc

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FirmwareFlashError(f"Firmware manifest missing for '{board}'") from exc
    except json.JSONDecodeError as exc:
        raise FirmwareFlashError(f"Invalid manifest for '{board}': {exc}") from exc

    if not manifest.get("segments"):
        raise FirmwareFlashError(f"Firmware manifest for '{board}' defines no segments")
    manifest.setdefault("label", board)
    manifest.setdefault("chip", board)
    manifest.setdefault("compress", True)
    return manifest, package


def _run_esptool(args: Sequence[str]) -> None:
    try:
        esptool.main(list(args))
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
        if code:
            raise FirmwareFlashError(f"esptool exited with status {code}") from exc
    except Exception as exc:  # pragma: no cover - esptool internal errors
        raise FirmwareFlashError(str(exc)) from exc


def flash_firmware(
    *,
    port: str,
    baudrate: int,
    board: str = DEFAULT_BOARD,
    erase_first: bool = False,
) -> Dict[str, object]:
    """Flash the bundled firmware to the specified serial port."""

    manifest, package = load_firmware_manifest(board)
    base_args: List[str] = [
        "--chip",
        str(manifest.get("chip", board)),
        "--port",
        port,
        "--baud",
        str(baudrate),
        "--before",
        str(manifest.get("before", "default-reset")),
        "--after",
        str(manifest.get("after", "hard-reset")),
    ]

    with ExitStack() as stack:
        resolved_segments: List[Tuple[str, Path]] = []
        for segment in manifest["segments"]:
            offset = segment.get("offset")
            file_name = segment.get("file")
            if not offset or not file_name:
                raise FirmwareFlashError(
                    "Manifest segment entries require 'offset' and 'file'"
                )
            traversable = resources.files(package) / file_name
            try:
                file_path = stack.enter_context(resources.as_file(traversable))
            except FileNotFoundError as exc:
                raise FirmwareFlashError(
                    f"Missing firmware artifact: {file_name}"
                ) from exc
            resolved_segments.append((str(offset), Path(file_path)))

        if erase_first:
            _run_esptool(base_args + ["erase-flash"])

        write_args: List[str] = base_args + ["write-flash"]
        option_keys = [
            ("flash-mode", manifest.get("flash-mode") or manifest.get("flash_mode")),
            ("flash-freq", manifest.get("flash-freq") or manifest.get("flash_freq")),
            ("flash-size", manifest.get("flash-size") or manifest.get("flash_size")),
        ]
        for option, value in option_keys:
            if value:
                write_args += [f"--{option}", str(value)]

        if manifest.get("compress", True):
            write_args.append("--compress")
        else:
            write_args.append("--no-compress")

        for offset, artifact_path in resolved_segments:
            write_args += [offset, str(artifact_path)]

        _run_esptool(write_args)

    return manifest


__all__ = [
    "FirmwareFlashError",
    "flash_firmware",
    "list_available_boards",
    "load_firmware_manifest",
]
