#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import ipaddress
import re
import string
import sys
import time
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import atexit
from concurrent.futures import TimeoutError as FutureTimeout
import typer
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table

from . import flash as flash_module
from . import prodtest, timo
from .constants import (
    DEFAULT_BAUD,
    DEFAULT_TIMEOUT,
    SPI_CHOICE_FIELDS,
    UART_PARITY_ALIASES,
)
from .firmware import DEFAULT_BOARD
from .serial_client import (
    NDJSONSerialClient,
    SerialLogger,
    SequenceTracker,
    ShuttleSerialError,
)

app = typer.Typer(
    add_completion=False, no_args_is_help=True, help="Shuttle command-line utility"
)
timo_app = typer.Typer(help="TiMo SPI helpers")
app.add_typer(timo_app, name="timo", help="Interact with TiMo over SPI")
prodtest_app = typer.Typer(help="Prodtest SPI helpers")
app.add_typer(
    prodtest_app, name="prodtest", help="Interact with prodtest firmware over SPI"
)

console = Console()
UART_RX_POLL_INTERVAL = 0.25
PRODTEST_ANTENNA_CHOICES = {
    "internal": 0,
    "external": 1,
}
PRODTEST_TX_POWER_LEVELS = [
    {
        "value": 0,
        "label": "-30 dBm",
        "macro": "RADIO_TXPOWER_TXPOWER_Neg30dBm",
        "aliases": ["neg30", "neg30dbm", "-30", "-30dbm"],
    },
    {
        "value": 1,
        "label": "-20 dBm",
        "macro": "RADIO_TXPOWER_TXPOWER_Neg20dBm",
        "aliases": ["neg20", "neg20dbm", "-20", "-20dbm"],
    },
    {
        "value": 2,
        "label": "-16 dBm",
        "macro": "RADIO_TXPOWER_TXPOWER_Neg16dBm",
        "aliases": ["neg16", "neg16dbm", "-16", "-16dbm"],
    },
    {
        "value": 3,
        "label": "-12 dBm",
        "macro": "RADIO_TXPOWER_TXPOWER_Neg12dBm",
        "aliases": ["neg12", "neg12dbm", "-12", "-12dbm"],
    },
    {
        "value": 4,
        "label": "-8 dBm",
        "macro": "RADIO_TXPOWER_TXPOWER_Neg8dBm",
        "aliases": ["neg8", "neg8dbm", "-8", "-8dbm"],
    },
    {
        "value": 5,
        "label": "-4 dBm",
        "macro": "RADIO_TXPOWER_TXPOWER_Neg4dBm",
        "aliases": ["neg4", "neg4dbm", "-4", "-4dbm"],
    },
    {
        "value": 6,
        "label": "0 dBm",
        "macro": "RADIO_TXPOWER_TXPOWER_0dBm",
        "aliases": ["0dbm", "0db", "0d", "zero"],
    },
    {
        "value": 7,
        "label": "+4 dBm",
        "macro": "RADIO_TXPOWER_TXPOWER_Pos4dBm",
        "aliases": ["pos4", "pos4dbm", "+4", "+4dbm"],
    },
]
PRODTEST_TX_POWER_META = {entry["value"]: entry for entry in PRODTEST_TX_POWER_LEVELS}
PRODTEST_TX_POWER_ALIASES: Dict[str, int] = {}
for entry in PRODTEST_TX_POWER_LEVELS:
    for alias in entry["aliases"]:
        PRODTEST_TX_POWER_ALIASES[alias.lower()] = entry["value"]
    PRODTEST_TX_POWER_ALIASES[str(entry["value"])] = entry["value"]
PRODTEST_TX_POWER_CANONICAL = [
    entry["aliases"][0] for entry in PRODTEST_TX_POWER_LEVELS
]

_HOST_PORT_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+:\d+$")
_IPV6_HOST_PORT_PATTERN = re.compile(r"^\[[0-9A-Fa-f:]+\]:\d+$")

# Backwards-compatible aliases for tests and external callers
_SerialLogger = SerialLogger
_SequenceTracker = SequenceTracker


def _ctx_resources(ctx: typer.Context) -> Dict[str, Optional[object]]:
    return ctx.obj or {}


@contextmanager
def _sys_error_reporter(client) -> None:
    setter = getattr(client, "set_event_callback", None)
    if setter is None:
        yield
        return
    setter(_handle_sys_error_event)
    try:
        yield
    finally:
        setter(None)


def _handle_sys_error_event(event: Dict[str, Any]) -> None:
    if event.get("ev") != "sys.error":
        return
    code = event.get("code", "?")
    msg = event.get("msg", "")
    seq = event.get("seq")
    parts = [f"Device sys.error ({code})"]
    if seq is not None:
        parts.append(f"seq={seq}")
    if msg:
        parts.append(f"- {msg}")
    console.print(f"[red]{' '.join(parts)}[/]")


@contextmanager
def _open_serial_client(
    resolved_port: str,
    *,
    baudrate: int,
    timeout: float,
    logger: Optional[SerialLogger],
    seq_tracker: Optional[SequenceTracker],
):
    with NDJSONSerialClient(
        resolved_port,
        baudrate=baudrate,
        timeout=timeout,
        logger=logger,
        seq_tracker=seq_tracker,
    ) as client:
        with _sys_error_reporter(client):
            yield client


@contextmanager
def spinner(message: str, enabled: bool = True):
    """Show a Rich spinner while the body executes."""

    if enabled and sys.stdout.isatty():
        with console.status(message, spinner="dots"):
            yield
    else:
        yield


def _normalize_choice(value: Optional[str], *, name: str) -> Optional[str]:
    if value is None:
        return None
    choices = SPI_CHOICE_FIELDS.get(name)
    if choices is None:
        return value
    normalized = value.lower()
    if normalized not in choices:
        allowed = ", ".join(sorted(choices))
        raise typer.BadParameter(f"{name} must be one of: {allowed}")
    return normalized


def _resolve_prodtest_power_choice(value: str) -> Tuple[int, Dict[str, str]]:
    trimmed = value.strip().lower()
    if not trimmed:
        raise typer.BadParameter("Power level cannot be empty")
    resolved = PRODTEST_TX_POWER_ALIASES.get(trimmed)
    if resolved is None:
        try:
            parsed = int(trimmed, 0)
        except ValueError:
            parsed = None
        if parsed is not None and parsed in PRODTEST_TX_POWER_META:
            resolved = parsed
    if resolved is None:
        allowed = ", ".join(PRODTEST_TX_POWER_CANONICAL)
        raise typer.BadParameter(f"Power must be one of: {allowed} or an index 0-7")
    return resolved, PRODTEST_TX_POWER_META[resolved]


def _normalize_uart_parity(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip().lower()
    if not trimmed:
        return None
    mapped = UART_PARITY_ALIASES.get(trimmed)
    if mapped is not None:
        return mapped
    first = trimmed[0]
    if first in ("n", "e", "o"):
        return first
    allowed = ", ".join(sorted({"n", "e", "o", "none", "even", "odd"}))
    raise typer.BadParameter(f"parity must be one of: {allowed}")


def _normalize_hex_payload(value: str) -> str:
    cleaned = "".join(ch for ch in value if not ch.isspace() and ch != "_")
    if cleaned.startswith(("0x", "0X")):
        cleaned = cleaned[2:]
    if not cleaned:
        raise typer.BadParameter("UART payload cannot be empty")
    if len(cleaned) % 2 != 0:
        raise typer.BadParameter(
            "UART payload must contain an even number of hex digits"
        )
    if any(ch not in string.hexdigits for ch in cleaned):
        raise typer.BadParameter("UART payload must be valid hex")
    return cleaned.lower()


def _resolve_uart_payload(
    *,
    data_arg: Optional[str],
    text_payload: Optional[str],
    file_path: Optional[Path],
    encoding: str,
    append_newline: bool,
) -> Tuple[str, int]:
    sources = {
        "hex": data_arg not in (None, "-"),
        "stdin": data_arg == "-",
        "text": text_payload is not None,
        "file": file_path is not None,
    }
    used = [name for name, active in sources.items() if active]
    if not used:
        raise typer.BadParameter(
            "Provide UART data as HEX argument, --text, --file, or '-' for stdin"
        )
    if len(used) > 1:
        raise typer.BadParameter(
            "Specify exactly one UART payload source (HEX, --text, --file, or '-')"
        )

    source = used[0]
    if source == "hex":
        if append_newline:
            raise typer.BadParameter(
                "--newline is only valid with --text, --file, or '-' payloads"
            )
        normalized = _normalize_hex_payload(data_arg or "")
        length = len(normalized) // 2
        if length == 0:
            raise typer.BadParameter("UART payload cannot be empty")
        return normalized, length

    if source == "text":
        assert text_payload is not None
        try:
            payload_bytes = text_payload.encode(encoding)
        except LookupError as exc:
            raise typer.BadParameter(f"Unknown encoding '{encoding}'") from exc
    elif source == "file":
        assert file_path is not None
        try:
            payload_bytes = file_path.read_bytes()
        except OSError as exc:
            raise typer.BadParameter(f"Unable to read {file_path}: {exc}") from exc
    else:  # stdin
        payload_bytes = sys.stdin.buffer.read()

    if append_newline:
        payload_bytes += b"\n"

    if not payload_bytes:
        raise typer.BadParameter("UART payload cannot be empty")

    return payload_bytes.hex(), len(payload_bytes)


def _normalize_port(port: str) -> str:
    trimmed = port.strip()
    if not trimmed:
        raise typer.BadParameter("Serial port is required (use --port or SHUTTLE_PORT)")
    if "://" in trimmed:
        return trimmed
    if trimmed.startswith("/") or trimmed.startswith("\\"):
        return trimmed
    if _HOST_PORT_PATTERN.match(trimmed) or _IPV6_HOST_PORT_PATTERN.match(trimmed):
        return f"socket://{trimmed}"
    return trimmed


def _require_port(port: Optional[str]) -> str:
    if port:
        return _normalize_port(port)
    raise typer.BadParameter("Serial port is required (use --port or SHUTTLE_PORT)")


def _parse_int_option(value: str, *, name: str) -> int:
    try:
        parsed = int(value, 0)
    except ValueError as exc:
        raise typer.BadParameter(
            f"{name} must be an integer literal (e.g. 5 or 0x05)"
        ) from exc
    if parsed < 0:
        raise typer.BadParameter(f"{name} must be non-negative")
    return parsed


def _parse_ipv4(value: Optional[str], *, name: str) -> Optional[str]:
    if value is None:
        return None
    try:
        ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError as exc:
        raise typer.BadParameter(f"{name} must be a valid IPv4 address") from exc
    return value


def _parse_prodtest_mask(value: str) -> bytes:
    try:
        return prodtest.mask_from_hex(value)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


def _parse_fixed_hex(value: str, *, name: str, length: int) -> bytes:
    cleaned = value.strip()
    if cleaned.startswith(("0x", "0X")):
        cleaned = cleaned[2:]
    cleaned = cleaned.replace("_", "").replace(" ", "")
    if len(cleaned) != length * 2:
        raise typer.BadParameter(
            f"{name} must be {length * 2} hex characters ({length} bytes)"
        )
    try:
        return bytes.fromhex(cleaned)
    except ValueError as exc:
        raise typer.BadParameter(f"{name} must be valid hex") from exc


def _format_hex(hex_str: str) -> str:
    if not hex_str:
        return "—"
    grouped = [hex_str[i : i + 2] for i in range(0, len(hex_str), 2)]
    return " ".join(grouped)


def _decode_hex_response(response: Dict[str, Any], *, label: str) -> bytes:
    data = response.get("rx")
    if not isinstance(data, str):
        console.print(f"[red]{label} missing RX payload[/]")
        raise typer.Exit(1)
    try:
        return bytes.fromhex(data)
    except ValueError as exc:
        console.print(f"[red]{label} RX payload is not valid hex[/]")
        raise typer.Exit(1) from exc


def _format_failed_pins_line(failed: Sequence[int]) -> str:
    if not failed:
        return "Test failed on pins: [ ]"
    joined = ", ".join(str(pin) for pin in failed)
    return f"Test failed on pins: [ {joined} ]"


def _build_status_table(title: str, response: Dict[str, Any]) -> Table:
    table = Table(title=title, show_header=False, box=None)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    status = "OK" if response.get("ok") else "ERROR"
    status_color = "green" if response.get("ok") else "red"
    table.add_row("Status", f"[{status_color}]{status}[/]")
    if response.get("err"):
        err = response["err"]
        code = err.get("code", "?")
        msg = err.get("msg", "")
        table.add_row("Error", f"{code}: {msg}")
    return table


def _render_spi_response(
    title: str, response: Dict[str, Any], *, command_label: str
) -> None:
    table = _build_status_table(title, response)
    table.add_row("Command", command_label)
    if response.get("ok") and "rx" in response:
        table.add_row("RX", _format_hex(response.get("rx", "")))
    irq_level = response.get("irq")
    if irq_level is not None:
        table.add_row("IRQ level", str(irq_level))
    console.print(table)


def _render_read_reg_result(
    result: timo.ReadRegisterResult, rx_frames: Sequence[str]
) -> None:
    data_table = Table(title="TiMo read-reg", show_header=False, box=None)
    data_table.add_column("Field", style="cyan", no_wrap=True)
    data_table.add_column("Value", style="white")
    data_table.add_row("Address", f"0x{result.address:02X}")
    data_table.add_row("Length", str(result.length))
    data_table.add_row("Data", timo.format_bytes(result.data))
    data_table.add_row("IRQ (command)", f"0x{result.irq_flags_command:02X}")
    data_table.add_row("IRQ (payload)", f"0x{result.irq_flags_payload:02X}")
    data_table.add_row("Command RX", _format_hex(rx_frames[0]))
    data_table.add_row("Payload RX", _format_hex(rx_frames[1]))
    console.print(data_table)

    warnings: List[str] = []
    for label, value in ("command", result.irq_flags_command), (
        "payload",
        result.irq_flags_payload,
    ):
        if timo.requires_restart(value):
            warnings.append(
                f"IRQ bit7 asserted during {label} phase — resend the entire sequence per TiMo spec."
            )
    if warnings:
        console.print(
            Panel("\n".join(warnings), title="IRQ warning", border_style="yellow")
        )


def _render_write_reg_result(
    result: timo.WriteRegisterResult, rx_frames: Sequence[str]
) -> None:
    data_table = Table(title="TiMo write-reg", show_header=False, box=None)
    data_table.add_row("Address", f"0x{result.address:02X}")
    data_table.add_row("Data written", timo.format_bytes(result.data))
    data_table.add_row("IRQ flags (cmd)", f"0x{result.irq_flags_command:02X}")
    data_table.add_row("IRQ flags (payload)", f"0x{result.irq_flags_payload:02X}")
    console.print(data_table)
    for label, value in zip(
        ["command", "payload"], [result.irq_flags_command, result.irq_flags_payload]
    ):
        if timo.requires_restart(value):
            console.print(
                f"[yellow]IRQ bit7 asserted during {label} phase — resend the entire sequence per TiMo spec.[/]"
            )


def _render_read_dmx_result(result, rx_frames):
    data_table = Table(title="TiMo read-dmx", show_header=False, box=None)
    data_table.add_row("Length", str(result.length))
    data_table.add_row("Data", timo.format_bytes(result.data))
    data_table.add_row("IRQ (command phase)", f"0x{result.irq_flags_command:02X}")
    data_table.add_row("IRQ (payload phase)", f"0x{result.irq_flags_payload:02X}")
    console.print(data_table)
    for label, value in zip(
        ["command", "payload"], [result.irq_flags_command, result.irq_flags_payload]
    ):
        if timo.requires_restart(value):
            console.print(
                f"[yellow]IRQ bit7 asserted during {label} phase — resend the entire sequence per TiMo spec.[/]"
            )


class FirmwareUpdateError(RuntimeError):
    """Raised when TiMo firmware update prerequisites or transfers fail."""


FW_UPDATE_SPI_LIMIT_HZ = 2_000_000
FW_UPDATE_BOOT_DELAY_S = 1.75
FW_UPDATE_IRQ_RETRIES = 5
FW_UPDATE_IRQ_RETRY_DELAY_S = 0.25


def _run_timo_sequence_with_client(
    client,
    sequence: Sequence[Dict[str, Any]],
    *,
    label: str,
) -> List[Dict[str, Any]]:
    responses: List[Dict[str, Any]] = []
    for idx, transfer in enumerate(sequence):
        response = client.spi_xfer(**transfer)
        responses.append(response)
        if not response.get("ok"):
            phase = "command" if idx == 0 else "payload"
            err = response.get("err", {})
            details = f"code={err.get('code')} msg={err.get('msg')}" if err else ""
            raise FirmwareUpdateError(
                f"{label} failed during {phase} phase {details}".strip()
            )
    return responses


def _write_reg_checked(client, address: int, data: bytes) -> timo.WriteRegisterResult:
    label = f"write-reg 0x{address:02X}"
    for attempt in range(1, FW_UPDATE_IRQ_RETRIES + 1):
        responses = _run_timo_sequence_with_client(
            client,
            timo.write_reg_sequence(address, data),
            label=label,
        )
        rx_frames = [resp.get("rx", "") for resp in responses]
        try:
            parsed = timo.parse_write_reg_response(address, data, rx_frames)
        except ValueError as exc:  # pragma: no cover - defensive
            raise FirmwareUpdateError(
                f"Unable to parse {label} response: {exc}"
            ) from exc
        needs_retry = timo.requires_restart(
            parsed.irq_flags_command
        ) or timo.requires_restart(parsed.irq_flags_payload)
        if not needs_retry:
            return parsed
        if attempt < FW_UPDATE_IRQ_RETRIES:
            console.print(
                f"[yellow]{label} attempt {attempt}/{FW_UPDATE_IRQ_RETRIES} reported IRQ bit7; retrying after {FW_UPDATE_IRQ_RETRY_DELAY_S:.3f}s...[/]"
            )
            time.sleep(FW_UPDATE_IRQ_RETRY_DELAY_S)
    raise FirmwareUpdateError(
        f"{label} kept reporting IRQ bit7 after {FW_UPDATE_IRQ_RETRIES} attempts"
    )


def _read_reg_checked(
    client,
    address: int,
    length: int,
    *,
    label: str,
    wait_irq: timo.WaitIrqOption = None,
    retries: int = FW_UPDATE_IRQ_RETRIES,
) -> timo.ReadRegisterResult:
    max_attempts = max(1, retries)
    for attempt in range(1, max_attempts + 1):
        responses = _run_timo_sequence_with_client(
            client,
            timo.read_reg_sequence(address, length, wait_irq=wait_irq),
            label=label,
        )
        rx_frames = [resp.get("rx", "") for resp in responses]
        try:
            parsed = timo.parse_read_reg_response(address, length, rx_frames)
        except ValueError as exc:
            raise FirmwareUpdateError(
                f"Unable to parse {label} response: {exc}"
            ) from exc
        needs_retry = timo.requires_restart(
            parsed.irq_flags_command
        ) or timo.requires_restart(parsed.irq_flags_payload)
        if not needs_retry:
            return parsed
        if attempt < max_attempts and max_attempts > 1:
            console.print(
                f"[yellow]{label} attempt {attempt}/{max_attempts} reported IRQ bit7; retrying after {FW_UPDATE_IRQ_RETRY_DELAY_S:.3f}s...[/]"
            )
            time.sleep(FW_UPDATE_IRQ_RETRY_DELAY_S)
    raise FirmwareUpdateError(
        f"{label} kept reporting IRQ bit7 after {max_attempts} attempts"
    )


def _ensure_spi_ready_for_update(client, *, max_frame_bytes: int) -> Dict[str, Any]:
    info = client.get_info()
    spi_caps = info.get("spi_caps") or {}
    max_transfer = spi_caps.get("max_transfer_bytes")
    if not isinstance(max_transfer, int) or max_transfer < max_frame_bytes:
        raise FirmwareUpdateError(
            "Device SPI transport cannot send the required firmware block size "
            f"(needs {max_frame_bytes} bytes, reports {max_transfer}). Update the devboard firmware."
        )
    cfg_resp = client.spi_cfg()
    spi_cfg = cfg_resp.get("spi") or {}
    hz = spi_cfg.get("hz") or spi_caps.get("default_hz")
    if isinstance(hz, str):
        try:
            hz = int(hz, 0)
        except ValueError:
            hz = None
    if isinstance(hz, int) and hz > FW_UPDATE_SPI_LIMIT_HZ:
        raise FirmwareUpdateError(
            f"Configured SPI clock {hz} Hz exceeds update limit {FW_UPDATE_SPI_LIMIT_HZ} Hz. "
            "Run 'shuttle spi-cfg --hz 2000000' before retrying."
        )
    enable_resp = client.spi_enable()
    if not enable_resp.get("ok"):
        err = enable_resp.get("err", {})
        msg = err.get("msg") if isinstance(err, dict) else "unable to enable SPI"
        raise FirmwareUpdateError(f"spi.enable failed: {msg}")
    return spi_caps


def _send_fw_block(
    client,
    opcode: int,
    payload: bytes,
    *,
    max_transfer_bytes: int,
):
    frame = bytes([opcode]) + payload
    if len(frame) > max_transfer_bytes:
        raise FirmwareUpdateError(
            f"FW block (opcode 0x{opcode:02X}) exceeds spi_caps.max_transfer_bytes"
        )
    response = client.spi_xfer(tx=frame.hex(), n=len(frame))
    if not response.get("ok"):
        err = response.get("err", {})
        msg = err.get("msg") if isinstance(err, dict) else "unknown"
        raise FirmwareUpdateError(f"FW block opcode 0x{opcode:02X} failed: {msg}")


def _read_status_byte(
    client,
    *,
    wait_irq: timo.WaitIrqOption = None,
    retries: int = FW_UPDATE_IRQ_RETRIES,
) -> int:
    reg_meta = timo.REGISTER_MAP["STATUS"]
    result = _read_reg_checked(
        client,
        reg_meta["address"],
        reg_meta.get("length", 1),
        label="STATUS register",
        wait_irq=wait_irq,
        retries=retries,
    )
    return result.data[0] if result.data else 0


def _read_version_bytes(client) -> bytes:
    reg_meta = timo.REGISTER_MAP["VERSION"]
    result = _read_reg_checked(
        client,
        reg_meta["address"],
        reg_meta.get("length", 8),
        label="VERSION register",
    )
    return result.data


def _enter_update_mode(client) -> None:
    config_addr = timo.REGISTER_MAP["CONFIG"]["address"]
    console.print("[cyan]Requesting TiMo UPDATE_MODE[/]")
    _write_reg_checked(client, config_addr, bytes([0x40]))
    console.print(
        f"Waiting {FW_UPDATE_BOOT_DELAY_S:.3f}s before reading STATUS for UPDATE_MODE"
    )
    time.sleep(FW_UPDATE_BOOT_DELAY_S)
    status_byte = _read_status_byte(client, wait_irq=False, retries=3)
    if status_byte & 0x80:
        console.print("[green]TiMo entered UPDATE_MODE[/]")
        return
    raise FirmwareUpdateError("TiMo did not enter update mode (STATUS bit7 missing)")


def _format_fw_progress(block_index: int, total_blocks: int, total_bytes: int) -> str:
    return f"Transferred {block_index}/{total_blocks} blocks ({total_bytes} bytes)"


def _stream_fw_image(
    client,
    *,
    firmware_path: Path,
    max_transfer_bytes: int,
    flush_wait_s: float,
) -> Tuple[int, int, bytes]:
    bytes_per_block = timo.FW_BLOCK_CMD_1_SIZE + timo.FW_BLOCK_CMD_2_SIZE
    try:
        total_size = firmware_path.stat().st_size
        payload_bytes_on_disk = total_size - timo.CCI_HEADER_SIZE
        if payload_bytes_on_disk <= 0:
            raise FirmwareUpdateError("CCI firmware contains no payload blocks")
        if payload_bytes_on_disk % bytes_per_block != 0:
            raise FirmwareUpdateError(
                "CCI firmware size is not aligned to FW block payloads"
            )
        expected_blocks = payload_bytes_on_disk // bytes_per_block
        with firmware_path.open("rb") as raw_file:
            reader = io.BufferedReader(raw_file)
            header = timo.read_cci_header(reader)
            console.print(f"CCI header ({timo.CCI_HEADER_SIZE} bytes): {header.hex()}")
            status_ctx = (
                console.status(
                    _format_fw_progress(0, expected_blocks, 0), spinner="dots"
                )
                if sys.stdout.isatty()
                else nullcontext(None)
            )
            with status_ctx as transfer_status:
                total_blocks = 0
                total_bytes = 0
                for block_index, chunk_1, chunk_2 in timo.iter_cci_chunks(reader):
                    total_blocks += 1
                    _send_fw_block(
                        client,
                        timo.FW_BLOCK_CMD_1,
                        chunk_1,
                        max_transfer_bytes=max_transfer_bytes,
                    )
                    _send_fw_block(
                        client,
                        timo.FW_BLOCK_CMD_2,
                        chunk_2,
                        max_transfer_bytes=max_transfer_bytes,
                    )
                    total_bytes += len(chunk_1) + len(chunk_2)
                    message = _format_fw_progress(
                        block_index, expected_blocks, total_bytes
                    )
                    if transfer_status is not None:
                        transfer_status.update(message)
                    elif block_index == 1 or block_index % 16 == 0:
                        console.print(message)
                    data_blocks_sent = block_index - 1
                    if data_blocks_sent > 0 and data_blocks_sent % 16 == 0:
                        time.sleep(flush_wait_s)
            if total_blocks == 0:
                raise FirmwareUpdateError("CCI firmware contains no payload blocks")
            return total_blocks, total_bytes, header
    except OSError as exc:
        raise FirmwareUpdateError(f"Unable to read firmware: {exc}") from exc
    except ValueError as exc:
        raise FirmwareUpdateError(str(exc)) from exc


def _execute_timo_sequence(
    *,
    port: Optional[str],
    baudrate: int,
    timeout: float,
    sequence: Sequence[Dict[str, Any]],
    spinner_label: str,
    logger: Optional[SerialLogger],
    seq_tracker: Optional[SequenceTracker],
) -> List[Dict[str, Any]]:
    resolved_port = _require_port(port)
    responses: List[Dict[str, Any]] = []
    with spinner(f"{spinner_label} over {resolved_port}"):
        try:
            with _open_serial_client(
                resolved_port,
                baudrate=baudrate,
                timeout=timeout,
                logger=logger,
                seq_tracker=seq_tracker,
            ) as client:
                for transfer in sequence:
                    response = client.spi_xfer(**transfer)
                    responses.append(response)
                    if not response.get("ok"):
                        break
        except ShuttleSerialError as exc:
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(1) from exc
    return responses


def _render_payload_response(
    title: str, response: Dict[str, Any], *, drop_fields: Optional[Set[str]] = None
) -> None:
    table = _build_status_table(title, response)
    console.print(table)
    if not response.get("ok"):
        return
    drop = drop_fields if drop_fields is not None else {"type", "id", "ok"}
    payload = {k: v for k, v in response.items() if k not in drop}
    if not payload:
        console.print("[yellow]Device returned no additional info[/]")
        return
    console.print(
        Panel(
            Pretty(payload, expand_all=True),
            title=f"{title} payload",
            border_style="cyan",
        )
    )


def _render_info_response(response: Dict[str, Any]) -> None:
    _render_payload_response("get.info", response)


def _render_ping_response(response: Dict[str, Any]) -> None:
    _render_payload_response("ping", response)


def _render_uart_event(event: Dict[str, Any]) -> None:
    data_hex = event.get("data")
    if not isinstance(data_hex, str):
        console.print("[yellow]uart.rx event missing data payload[/]")
        return
    try:
        payload = bytes.fromhex(data_hex)
    except ValueError:
        console.print("[red]uart.rx event payload is not valid hex[/]")
        return

    seq = event.get("seq", "?")
    port = event.get("port", 0)
    n_field = event.get("n")
    byte_count = n_field if isinstance(n_field, int) else len(payload)
    preview_limit = 64
    ascii_preview = "".join(
        chr(b) if 32 <= b < 127 else "." for b in payload[:preview_limit]
    )
    if len(payload) > preview_limit:
        ascii_preview += " ..."

    console.print(f"[green]uart.rx[/] seq={seq} port={port} bytes={byte_count}")
    console.print(f"  hex  : {_format_hex(data_hex)}")
    if payload:
        console.print(
            f"  ascii: {ascii_preview if ascii_preview else '(non-printable)'}"
        )


def _consume_uart_events(
    listener,
    *,
    duration: Optional[float],
    forever: bool,
) -> int:
    events_seen = 0
    start = time.monotonic()
    deadline = start + duration if duration is not None else None

    while True:
        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            timeout_value = (
                remaining
                if remaining < UART_RX_POLL_INTERVAL
                else UART_RX_POLL_INTERVAL
            )
        elif forever:
            timeout_value = UART_RX_POLL_INTERVAL
        else:
            timeout_value = None

        try:
            event = listener.next(timeout=timeout_value)
        except FutureTimeout:
            continue

        _render_uart_event(event)
        events_seen += 1
        if duration is None and not forever:
            break

    return events_seen


@app.callback()
def main(
    ctx: typer.Context,
    log: Optional[Path] = typer.Option(
        None,
        "--log",
        help="Append raw serial RX/TX lines with timestamps to the given file",
        show_default=False,
        metavar="FILE",
    ),
    seq_meta: Optional[Path] = typer.Option(
        None,
        "--seq-meta",
        help="Persist last observed device sequence number to ensure gap detection across runs",
        show_default=False,
        metavar="FILE",
    ),
) -> None:
    """Interact with the Shuttle devboard over the JSON serial link."""

    logger = SerialLogger(log) if log else None
    tracker: Optional[SequenceTracker]
    try:
        tracker = (
            SequenceTracker(seq_meta) if seq_meta is not None else SequenceTracker()
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    ctx.obj = {"logger": logger, "seq_tracker": tracker}
    if logger is not None:
        atexit.register(logger.close)


@timo_app.command("nop")
def timo_nop(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Send a TiMo NOP SPI transfer over the Shuttle link."""

    resources = _ctx_resources(ctx)
    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=timo.nop_sequence(),
        spinner_label="Sending TiMo NOP",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )
    if not responses:
        console.print("[red]Device returned no response[/]")
        raise typer.Exit(1)
    _render_spi_response("TiMo NOP", responses[0], command_label="spi.xfer (NOP)")


@timo_app.command("read-reg")
def timo_read_reg(
    ctx: typer.Context,
    address: str = typer.Option(
        ..., "--addr", "--address", help="Register address (decimal or 0x-prefixed)"
    ),
    length: int = typer.Option(
        1,
        "--length",
        min=1,
        max=timo.READ_REG_MAX_LEN,
        help=f"Bytes to read (1..{timo.READ_REG_MAX_LEN})",
    ),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Read a TiMo register via a two-phase SPI sequence."""

    resources = _ctx_resources(ctx)
    addr_value = _parse_int_option(address, name="address")
    try:
        sequence = timo.read_reg_sequence(addr_value, length)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label=f"Reading TiMo register 0x{addr_value:02X}",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )

    if not responses:
        console.print("[red]Device returned no response[/]")
        raise typer.Exit(1)

    failed_idx = next(
        (idx for idx, resp in enumerate(responses) if not resp.get("ok")), None
    )
    if failed_idx is not None:
        phase = "command" if failed_idx == 0 else "payload"
        _render_spi_response(
            f"TiMo read-reg ({phase})",
            responses[failed_idx],
            command_label=f"spi.xfer ({phase} phase)",
        )
        raise typer.Exit(1)

    if len(responses) != len(sequence):
        console.print("[red]Command halted before completing all SPI phases[/]")
        raise typer.Exit(1)

    rx_frames = [resp.get("rx", "") for resp in responses]
    try:
        parsed = timo.parse_read_reg_response(addr_value, length, rx_frames)
    except ValueError as exc:
        console.print(f"[red]Unable to parse read-reg response: {exc}[/]")
        raise typer.Exit(1) from exc

    _render_spi_response(
        "TiMo read-reg",
        responses[-1],
        command_label="spi.xfer (payload phase)",
    )
    _render_read_reg_result(parsed, rx_frames)


@timo_app.command("status")
def timo_status(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Read and render the TiMo STATUS register with bit breakdown."""

    resources = _ctx_resources(ctx)
    reg_meta = timo.REGISTER_MAP["STATUS"]
    length = reg_meta.get("length", 1)
    sequence = timo.read_reg_sequence(reg_meta["address"], length)

    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label="Reading TiMo STATUS",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )
    if not responses or not responses[-1].get("ok"):
        console.print("[red]Failed to read STATUS register[/]")
        raise typer.Exit(1)

    rx = responses[-1].get("rx", "")
    payload = bytes.fromhex(rx) if isinstance(rx, str) else b""
    irq_flags = payload[:1]
    data = payload[1:] if len(payload) > 1 else b""
    status_byte = data[0] if data else 0

    table = Table(title="TiMo STATUS (0x01)", show_header=False, box=None)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Raw", f"0x{status_byte:02X}")
    table.add_row("IRQ flags", timo.format_bytes(irq_flags))

    fields = reg_meta["fields"]

    def bit_set(bit: int) -> bool:
        return bool(status_byte & (1 << bit))

    for name, meta in fields.items():
        lo, hi = meta["bits"]
        if lo != hi:
            val = (status_byte >> lo) & ((1 << (hi - lo + 1)) - 1)
            display = f"{val}"
        else:
            display = "ON" if bit_set(lo) else "off"
        table.add_row(name, display)

    console.print(table)


@timo_app.command("link")
def timo_link(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Force TiMo into link mode by setting RF_LINK bit in STATUS register."""

    resources = _ctx_resources(ctx)
    # Set RF_LINK bit in STATUS.
    sequence = timo.write_reg_sequence(0x01, bytes([0x02]))  # RF_LINK bit set
    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label="Setting TiMo RF_LINK",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )
    if (
        not responses
        or len(responses) < len(sequence)
        or not all(resp.get("ok") for resp in responses)
    ):
        console.print("[red]Failed to set RF_LINK[/]")
        raise typer.Exit(1)

    table = Table(title="TiMo link", show_header=False, box=None)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Register", "STATUS (0x01) RF_LINK=1")
    table.add_row("Result", "[green]OK[/]")
    console.print(table)


@timo_app.command("unlink")
def timo_unlink(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Unlink TiMo by setting the LINKED bit in STATUS to 1 (write-to-unlink)."""

    resources = _ctx_resources(ctx)
    status_sequence = timo.write_reg_sequence(0x01, bytes([0x01]))  # LINKED bit set
    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=status_sequence,
        spinner_label="Clearing TiMo link",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )
    if not responses or not all(resp.get("ok") for resp in responses):
        console.print("[red]Failed to unlink[/]")
        raise typer.Exit(1)

    table = Table(title="TiMo unlink", show_header=False, box=None)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Register", "STATUS (0x01) LINKED=1 (unlink)")
    table.add_row("Result", "[green]OK[/]")
    console.print(table)


@timo_app.command("antenna")
def timo_antenna(
    ctx: typer.Context,
    value: Optional[str] = typer.Argument(
        None,
        metavar="[on-board|ipex]",
        help="Read current antenna when omitted; set antenna when provided",
    ),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Get or set the selected antenna (on-board or IPEX/u.FL)."""

    resources = _ctx_resources(ctx)
    reg_meta = timo.REGISTER_MAP["ANTENNA"]
    spinner_label = "Reading TiMo antenna"
    sequence = timo.read_reg_sequence(reg_meta["address"], reg_meta.get("length", 1))

    set_value: Optional[int] = None
    if value is not None:
        normalized = value.strip().lower()
        if normalized not in ("on-board", "ipex", "ipx", "u.fl", "u-fl", "ufl"):
            raise typer.BadParameter("antenna must be 'on-board' or 'ipex'")
        set_value = 0 if normalized == "on-board" else 1
        spinner_label = f"Setting TiMo antenna to {normalized}"
        sequence = timo.write_reg_sequence(reg_meta["address"], bytes([set_value]))

    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label=spinner_label,
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )
    if not responses or not responses[-1].get("ok"):
        console.print("[red]Antenna operation failed[/]")
        raise typer.Exit(1)

    table = Table(
        title="TiMo antenna",
        show_header=False,
        box=None,
    )
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    if set_value is None:
        rx = responses[-1].get("rx", "")
        payload = bytes.fromhex(rx) if isinstance(rx, str) else b""
        antenna_byte = payload[1] if len(payload) > 1 else 0  # skip IRQ flags
        selection = "on-board" if (antenna_byte & 0x01) == 0 else "ipex"
        table.add_row("Register", "ANTENNA (0x07)")
        table.add_row("Selected", selection)
    else:
        table.add_row("Action", f"Set to {'on-board' if set_value == 0 else 'ipex'}")
        table.add_row("Status", "[green]OK[/]")

    console.print(table)


@timo_app.command("link-quality")
def timo_link_quality(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Read TiMo link quality register and render packet delivery rate."""

    resources = _ctx_resources(ctx)
    reg_meta = timo.REGISTER_MAP["LINK_QUALITY"]
    sequence = timo.read_reg_sequence(reg_meta["address"], reg_meta.get("length", 1))
    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label="Reading TiMo link quality",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )
    if not responses or not responses[-1].get("ok"):
        console.print("[red]Failed to read link quality[/]")
        raise typer.Exit(1)

    rx = responses[-1].get("rx", "")
    payload = bytes.fromhex(rx) if isinstance(rx, str) else b""
    pdr = payload[1] if len(payload) > 1 else 0  # skip IRQ flags
    percent = pdr / 255 * 100

    table = Table(title="TiMo Link Quality", show_header=False, box=None)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Register", "LINK_QUALITY (0x06)")
    table.add_row("Raw", f"0x{pdr:02X}")
    table.add_row("PDR", f"{percent:.1f}%")
    console.print(table)


@timo_app.command("dmx")
def timo_dmx(
    ctx: typer.Context,
    window_size: Optional[str] = typer.Option(
        None,
        "--window-size",
        help="DMX window size (0-65535)",
    ),
    start_address: Optional[str] = typer.Option(
        None,
        "--start-address",
        help="DMX window start address",
    ),
    n_channels: Optional[str] = typer.Option(
        None,
        "--channels",
        help="Number of channels to generate",
    ),
    interslot_time: Optional[str] = typer.Option(
        None,
        "--interslot",
        help="Interslot spacing in microseconds",
    ),
    refresh_period: Optional[str] = typer.Option(
        None,
        "--refresh",
        help="DMX frame length in microseconds",
    ),
    enable: bool = typer.Option(
        False, "--enable", help="Enable internal DMX generation", show_default=False
    ),
    disable: bool = typer.Option(
        False, "--disable", help="Disable internal DMX generation", show_default=False
    ),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Read or update TiMo DMX registers (window, spec, control)."""

    resources = _ctx_resources(ctx)
    desired_enable: Optional[bool] = True if enable else False if disable else None

    def _parse_opt(value: Optional[str], name: str) -> Optional[int]:
        return _parse_int_option(value, name=name) if value is not None else None

    parsed_window = _parse_opt(window_size, "window_size")
    parsed_start = _parse_opt(start_address, "start_address")
    parsed_channels = _parse_opt(n_channels, "channels")
    parsed_interslot = _parse_opt(interslot_time, "interslot_time")
    parsed_refresh = _parse_opt(refresh_period, "refresh_period")

    reg_window = timo.REGISTER_MAP["DMX_WINDOW"]
    reg_spec = timo.REGISTER_MAP["DMX_SPEC"]
    reg_ctrl = timo.REGISTER_MAP["DMX_CONTROL"]

    resolved_port = _require_port(port)

    def _read_register(client, reg_meta):
        seq = timo.read_reg_sequence(reg_meta["address"], reg_meta.get("length", 1))
        responses = [client.spi_xfer(**cmd) for cmd in seq]
        rx = responses[-1].get("rx", "")
        payload = bytes.fromhex(rx) if isinstance(rx, str) else b""
        return payload[1:] if payload else b""

    def _set_bits(base: int, lo: int, hi: int, value: int, total_bits: int) -> int:
        width = hi - lo + 1
        mask = ((1 << width) - 1) << (total_bits - hi - 1)
        return (base & ~mask) | ((value & ((1 << width) - 1)) << (total_bits - hi - 1))

    with _open_serial_client(
        resolved_port,
        baudrate=baudrate,
        timeout=timeout,
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    ) as client:
        # Read current values
        window_bytes = _read_register(client, reg_window)
        spec_bytes = _read_register(client, reg_spec)
        ctrl_bytes = _read_register(client, reg_ctrl)

        window_int = int.from_bytes(
            window_bytes.ljust(reg_window["length"], b"\x00"), "big"
        )
        spec_int = int.from_bytes(spec_bytes.ljust(reg_spec["length"], b"\x00"), "big")
        ctrl_int = int.from_bytes(ctrl_bytes.ljust(reg_ctrl["length"], b"\x00"), "big")

        # Apply updates if provided
        any_change = False
        total_window_bits = reg_window["length"] * 8
        if parsed_window is not None:
            window_int = _set_bits(
                window_int,
                *reg_window["fields"]["WINDOW_SIZE"]["bits"],
                parsed_window,
                total_window_bits,
            )
            any_change = True
        if parsed_start is not None:
            window_int = _set_bits(
                window_int,
                *reg_window["fields"]["START_ADDRESS"]["bits"],
                parsed_start,
                total_window_bits,
            )
            any_change = True

        total_spec_bits = reg_spec["length"] * 8
        if parsed_channels is not None:
            spec_int = _set_bits(
                spec_int,
                *reg_spec["fields"]["N_CHANNELS"]["bits"],
                parsed_channels,
                total_spec_bits,
            )
            any_change = True
        if parsed_interslot is not None:
            spec_int = _set_bits(
                spec_int,
                *reg_spec["fields"]["INTERSLOT_TIME"]["bits"],
                parsed_interslot,
                total_spec_bits,
            )
            any_change = True
        if parsed_refresh is not None:
            spec_int = _set_bits(
                spec_int,
                *reg_spec["fields"]["REFRESH_PERIOD"]["bits"],
                parsed_refresh,
                total_spec_bits,
            )
            any_change = True

        if desired_enable is not None:
            total_ctrl_bits = reg_ctrl["length"] * 8
            ctrl_int = _set_bits(
                ctrl_int,
                *reg_ctrl["fields"]["ENABLE"]["bits"],
                1 if desired_enable else 0,
                total_ctrl_bits,
            )
            any_change = True

        if any_change:
            # Write back registers that changed
            write_sequences = [
                timo.write_reg_sequence(
                    reg_window["address"],
                    window_int.to_bytes(reg_window["length"], "big"),
                ),
                timo.write_reg_sequence(
                    reg_spec["address"], spec_int.to_bytes(reg_spec["length"], "big")
                ),
                timo.write_reg_sequence(
                    reg_ctrl["address"], ctrl_int.to_bytes(reg_ctrl["length"], "big")
                ),
            ]
            for seq in write_sequences:
                for cmd in seq:
                    client.spi_xfer(**cmd)

        # Prepare display values (after potential updates)
        window_size_val = timo.slice_bits(
            window_int.to_bytes(reg_window["length"], "big"),
            *reg_window["fields"]["WINDOW_SIZE"]["bits"],
        )
        start_val = timo.slice_bits(
            window_int.to_bytes(reg_window["length"], "big"),
            *reg_window["fields"]["START_ADDRESS"]["bits"],
        )
        channels_val = timo.slice_bits(
            spec_int.to_bytes(reg_spec["length"], "big"),
            *reg_spec["fields"]["N_CHANNELS"]["bits"],
        )
        interslot_val = timo.slice_bits(
            spec_int.to_bytes(reg_spec["length"], "big"),
            *reg_spec["fields"]["INTERSLOT_TIME"]["bits"],
        )
        refresh_val = timo.slice_bits(
            spec_int.to_bytes(reg_spec["length"], "big"),
            *reg_spec["fields"]["REFRESH_PERIOD"]["bits"],
        )
        enable_val = bool(
            timo.slice_bits(
                ctrl_int.to_bytes(reg_ctrl["length"], "big"),
                *reg_ctrl["fields"]["ENABLE"]["bits"],
            )
        )

    table = Table(title="TiMo DMX", show_header=False, box=None)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Window size", str(window_size_val))
    table.add_row("Start address", str(start_val))
    table.add_row("Channels", str(channels_val))
    table.add_row("Interslot (us)", str(interslot_val))
    table.add_row("Refresh (us)", str(refresh_val))
    table.add_row("Enable", "ON" if enable_val else "off")
    console.print(table)


@timo_app.command("radio-mode")
def timo_radio_mode(
    ctx: typer.Context,
    mode: Optional[str] = typer.Option(
        None, "--mode", help="Set radio mode: rx or tx", case_sensitive=False
    ),
    enable: bool = typer.Option(
        False, "--enable", help="Enable wireless operation", show_default=False
    ),
    disable: bool = typer.Option(
        False, "--disable", help="Disable wireless operation", show_default=False
    ),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Read or set TiMo radio mode and wireless enable (CONFIG register)."""

    if enable and disable:
        raise typer.BadParameter("Cannot specify both --enable and --disable")
    desired_mode: Optional[int] = None
    if mode:
        normalized = mode.strip().lower()
        if normalized not in ("rx", "tx"):
            raise typer.BadParameter("mode must be rx or tx")
        desired_mode = 0 if normalized == "rx" else 1

    resources = _ctx_resources(ctx)
    reg_meta = timo.REGISTER_MAP["CONFIG"]
    seq = timo.read_reg_sequence(reg_meta["address"], reg_meta.get("length", 1))

    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=seq,
        spinner_label="Reading TiMo CONFIG",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )
    if not responses or not responses[-1].get("ok"):
        console.print("[red]Failed to read CONFIG[/]")
        raise typer.Exit(1)

    payload = (
        bytes.fromhex(responses[-1].get("rx", ""))
        if isinstance(responses[-1].get("rx"), str)
        else b""
    )
    config_byte = payload[1] if len(payload) > 1 else 0
    new_byte = config_byte

    if desired_mode is not None:
        new_byte = (new_byte & ~(1 << 1)) | (desired_mode << 1)
    if enable:
        new_byte = new_byte | (1 << 7)
    if disable:
        new_byte = new_byte & ~(1 << 7)

    if new_byte != config_byte:
        write_seq = timo.write_reg_sequence(reg_meta["address"], bytes([new_byte]))
        for cmd in write_seq:
            resp = _execute_timo_sequence(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                sequence=[cmd],
                spinner_label="Writing TiMo CONFIG",
                logger=resources.get("logger"),
                seq_tracker=resources.get("seq_tracker"),
            )
            if not resp or not resp[-1].get("ok"):
                console.print("[red]Failed to update CONFIG[/]")
                raise typer.Exit(1)
        config_byte = new_byte

    table = Table(title="TiMo Radio Mode", show_header=False, box=None)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("CONFIG (0x00)", f"0x{config_byte:02X}")
    mode_str = "tx" if config_byte & (1 << 1) else "rx"
    table.add_row("RADIO_TX_RX_MODE", mode_str)
    table.add_row("SPI_RDM", "enabled" if config_byte & (1 << 3) else "disabled")
    table.add_row("RADIO_ENABLE", "ON" if config_byte & (1 << 7) else "off")
    console.print(table)


@timo_app.command("device-name")
def timo_device_name(
    ctx: typer.Context,
    name: Optional[str] = typer.Argument(
        None,
        help="New device name (omit to read current). Will be truncated to register length.",
    ),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Read or write the TiMo device name register."""

    resources = _ctx_resources(ctx)
    reg_meta = timo.REGISTER_MAP["DEVICE_NAME"]
    resolved_port = _require_port(port)

    def _read_name(client) -> str:
        seq = timo.read_reg_sequence(reg_meta["address"], reg_meta.get("length", 16))
        responses = [client.spi_xfer(**cmd) for cmd in seq]
        rx = responses[-1].get("rx", "")
        payload = bytes.fromhex(rx) if isinstance(rx, str) else b""
        data = payload[1:] if payload else b""
        return data.split(b"\x00", 1)[0].decode("ascii", errors="replace")

    with _open_serial_client(
        resolved_port,
        baudrate=baudrate,
        timeout=timeout,
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    ) as client:
        if name is None:
            current = _read_name(client)
            table = Table(title="TiMo device name", show_header=False, box=None)
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Value", style="white")
            table.add_row("Current", current)
            console.print(table)
            return

        encoded = name.encode("ascii", errors="ignore")[: reg_meta["length"]]
        payload = encoded.ljust(reg_meta["length"], b"\x00")
        write_seq = timo.write_reg_sequence(reg_meta["address"], payload)
        for cmd in write_seq:
            resp = client.spi_xfer(**cmd)
            if not resp.get("ok"):
                console.print("[red]Failed to write device name[/]")
                raise typer.Exit(1)

        updated = _read_name(client)

    table = Table(title="TiMo device name", show_header=False, box=None)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Updated", updated)
    console.print(table)


@timo_app.command("write-reg")
def timo_write_reg(
    ctx: typer.Context,
    address: str = typer.Option(
        ..., "--addr", "--address", help="Register address (decimal or 0x-prefixed)"
    ),
    data: str = typer.Option(..., "--data", help="Hex bytes to write (e.g. cafebabe)"),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Write a TiMo register via a two-phase SPI sequence."""
    resources = _ctx_resources(ctx)
    addr_value = _parse_int_option(address, name="address")
    try:
        data_bytes = bytes.fromhex(data)
    except Exception as exc:
        raise typer.BadParameter(f"Invalid hex for data: {exc}") from exc
    try:
        sequence = timo.write_reg_sequence(addr_value, data_bytes)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label=f"Writing TiMo register 0x{addr_value:02X}",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )

    if not responses:
        console.print("[red]Device returned no response[/]")
        raise typer.Exit(1)

    failed_idx = next(
        (idx for idx, resp in enumerate(responses) if not resp.get("ok")), None
    )
    if failed_idx is not None:
        phase = "command" if failed_idx == 0 else "payload"
        _render_spi_response(
            f"TiMo write-reg ({phase})",
            responses[failed_idx],
            command_label=f"spi.xfer ({phase} phase)",
        )
        raise typer.Exit(1)

    if len(responses) != len(sequence):
        console.print("[red]Command halted before completing all SPI phases[/]")
        raise typer.Exit(1)

    rx_frames = [resp.get("rx", "") for resp in responses]
    try:
        parsed = timo.parse_write_reg_response(addr_value, data_bytes, rx_frames)
    except ValueError as exc:
        console.print(f"[red]Unable to parse write-reg response: {exc}[/]")
        raise typer.Exit(1) from exc

    _render_spi_response(
        "TiMo write-reg",
        responses[-1],
        command_label="spi.xfer (payload phase)",
    )
    _render_write_reg_result(parsed, rx_frames)


@timo_app.command("read-dmx")
def timo_read_dmx(
    ctx: typer.Context,
    length: int = typer.Option(
        32,
        "--length",
        min=1,
        max=timo.DMX_READ_MAX_LEN,
        help=f"Bytes to read (1..{timo.DMX_READ_MAX_LEN})",
    ),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Read the latest received DMX values from TiMo via a two-phase SPI sequence."""
    resources = _ctx_resources(ctx)
    try:
        sequence = timo.read_dmx_sequence(length)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label=f"Reading DMX values (length={length})",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )

    if not responses:
        console.print("[red]Device returned no response[/]")
        raise typer.Exit(1)

    failed_idx = next(
        (idx for idx, resp in enumerate(responses) if not resp.get("ok")), None
    )
    if failed_idx is not None:
        phase = "command" if failed_idx == 0 else "payload"
        _render_spi_response(
            f"TiMo read-dmx ({phase})",
            responses[failed_idx],
            command_label=f"spi.xfer ({phase} phase)",
        )
        raise typer.Exit(1)

    if len(responses) != len(sequence):
        console.print("[red]Command halted before completing all SPI phases[/]")
        raise typer.Exit(1)

    rx_frames = [resp.get("rx", "") for resp in responses]
    try:
        parsed = timo.parse_read_dmx_response(length, rx_frames)
    except ValueError as exc:
        console.print(f"[red]Unable to parse read-dmx response: {exc}[/]")
        raise typer.Exit(1) from exc

    _render_spi_response(
        "TiMo read-dmx",
        responses[-1],
        command_label="spi.xfer (payload phase)",
    )
    _render_read_dmx_result(parsed, rx_frames)


@timo_app.command("update-fw")
def timo_update_fw(
    ctx: typer.Context,
    firmware: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        help="Path to TiMo .cci firmware image",
    ),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
    flush_wait_ms: float = typer.Option(
        100.0,
        "--flush-wait-ms",
        min=0.0,
        help="Delay (ms) after each 16 data blocks (post-header)",
    ),
    final_wait_ms: float = typer.Option(
        1000.0,
        "--final-wait-ms",
        min=0.0,
        help="Delay (ms) after streaming all blocks to let TiMo finalize",
    ),
):
    """Flash TiMo firmware by streaming a .cci file over FW_BLOCK commands."""

    resources = _ctx_resources(ctx)
    resolved_port = _require_port(port)
    flush_wait_s = flush_wait_ms / 1000.0
    final_wait_s = final_wait_ms / 1000.0
    console.print(f"[cyan]Starting TiMo update via {firmware}[/]")

    try:
        with _open_serial_client(
            resolved_port,
            baudrate=baudrate,
            timeout=timeout,
            logger=resources.get("logger"),
            seq_tracker=resources.get("seq_tracker"),
        ) as client:
            spi_caps = _ensure_spi_ready_for_update(
                client, max_frame_bytes=1 + timo.FW_BLOCK_CMD_1_SIZE
            )
            _enter_update_mode(client)
            max_transfer_bytes = int(spi_caps["max_transfer_bytes"])
            blocks_sent, payload_bytes, header = _stream_fw_image(
                client,
                firmware_path=firmware,
                max_transfer_bytes=max_transfer_bytes,
                flush_wait_s=flush_wait_s,
            )
            console.print(
                f"Waiting {final_wait_s:.3f}s for TiMo to finalize the update"
            )
            time.sleep(final_wait_s)
            status_after = _read_status_byte(client)
            if status_after & 0x80:
                raise FirmwareUpdateError(
                    "TiMo still reports UPDATE_MODE after sending all blocks"
                )
            version_bytes = _read_version_bytes(client)
    except FirmwareUpdateError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(1) from exc
    except ShuttleSerialError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(1) from exc

    summary = Table(title="TiMo firmware update", show_header=False, box=None)
    summary.add_column("Field", style="cyan", no_wrap=True)
    summary.add_column("Value", style="white")
    summary.add_row("Blocks transferred", str(blocks_sent))
    summary.add_row("Data blocks", str(blocks_sent - 1))
    summary.add_row("Bytes transferred", str(payload_bytes))
    summary.add_row("CCI header", header.hex())
    console.print(summary)

    if len(version_bytes) < 8:
        console.print(
            "[yellow]VERSION register shorter than expected; unable to decode versions[/]"
        )
    else:
        version_fields = timo.REGISTER_MAP["VERSION"]["fields"]
        fw_field = version_fields["FW_VERSION"]["bits"]
        hw_field = version_fields["HW_VERSION"]["bits"]
        fw_version = timo.slice_bits(version_bytes, *fw_field)
        hw_version = timo.slice_bits(version_bytes, *hw_field)
        version_table = Table(title="TiMo VERSION", show_header=False, box=None)
        version_table.add_column("Field", style="cyan", no_wrap=True)
        version_table.add_column("Value", style="white")
        version_table.add_row("FW_VERSION", f"0x{fw_version:08X}")
        version_table.add_row("HW_VERSION", f"0x{hw_version:08X}")
        console.print(version_table)

    console.print("[green]TiMo firmware update complete[/]")


@prodtest_app.command("reset")
def prodtest_reset(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyACM0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Send the prodtest '?' command to reset the attached module over SPI."""

    resources = _ctx_resources(ctx)
    sequence = [prodtest.reset_transfer()]
    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label="Sending prodtest reset",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )
    if not responses:
        console.print("[red]Device returned no response[/]")
        raise typer.Exit(1)
    _render_spi_response(
        "prodtest reset", responses[0], command_label="spi.xfer (prodtest)"
    )


@prodtest_app.command("ping")
def prodtest_ping(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyACM0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Send the prodtest 'ping' command: send '+' and expect '-' back."""
    resources = _ctx_resources(ctx)
    sequence = prodtest.ping_sequence()
    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label="Sending prodtest ping",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )
    if not responses:
        console.print("[red]Device returned no response[/]")
        raise typer.Exit(1)

    failed_idx = next(
        (idx for idx, resp in enumerate(responses) if not resp.get("ok")), None
    )
    if failed_idx is not None:
        phase = "command" if failed_idx == 0 else "payload"
        _render_spi_response(
            f"prodtest ping ({phase})",
            responses[failed_idx],
            command_label=f"spi.xfer (prodtest {phase})",
        )
        raise typer.Exit(1)

    if len(responses) != len(sequence):
        console.print(
            "[red]Prodtest command halted before completing all SPI phases[/]"
        )
        raise typer.Exit(1)

    command_response, payload_response = responses
    _render_spi_response(
        "prodtest ping (command)",
        command_response,
        command_label="spi.xfer (prodtest command)",
    )
    _render_spi_response(
        "prodtest ping (payload)",
        payload_response,
        command_label="spi.xfer (prodtest payload)",
    )

    rx_bytes = _decode_hex_response(payload_response, label="prodtest ping (payload)")
    if not rx_bytes or rx_bytes[0] != 0x2D:  # ord('-')
        console.print(
            "[red]Ping failed: expected '-' (0x2D), got: "
            f"{_format_hex(payload_response.get('rx', ''))}[/]"
        )
        raise typer.Exit(1)

    console.print("[green]Ping successful: got '-' response[/]")


@prodtest_app.command("antenna")
def prodtest_antenna(
    ctx: typer.Context,
    antenna: str = typer.Argument(
        ...,
        metavar="ANTENNA",
        help="Antenna to select (internal/external)",
    ),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyACM0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Select the active prodtest antenna (opcode 'a')."""

    resources = _ctx_resources(ctx)
    normalized = antenna.strip().lower()
    try:
        antenna_value = PRODTEST_ANTENNA_CHOICES[normalized]
    except KeyError as exc:
        allowed = ", ".join(sorted(PRODTEST_ANTENNA_CHOICES))
        raise typer.BadParameter(f"Antenna must be one of: {allowed}") from exc

    sequence = [prodtest.select_antenna(antenna_value)]
    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label=f"Selecting prodtest antenna ({normalized})",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )

    if not responses:
        console.print("[red]Device returned no response[/]")
        raise typer.Exit(1)

    response = responses[0]
    _render_spi_response(
        "prodtest antenna",
        response,
        command_label="spi.xfer (prodtest)",
    )

    if not response.get("ok"):
        raise typer.Exit(1)

    console.print(f"[green]Antenna set to {normalized}")


@prodtest_app.command("continuous-tx")
def prodtest_continuous_tx(
    ctx: typer.Context,
    channel: int = typer.Argument(
        ...,
        metavar="CHANNEL",
        min=0,
        max=100,
        help="NRF_RADIO->FREQUENCY channel index (0=2400 MHz, 100=2500 MHz)",
    ),
    power: str = typer.Argument(
        ...,
        metavar="POWER",
        help=(
            "Output power alias (neg30, neg20, neg16, neg12, neg8, neg4, 0, pos4) "
            "or numeric index 0-7"
        ),
    ),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyACM0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Run the prodtest continuous transmitter test (opcode 'o')."""

    resources = _ctx_resources(ctx)
    power_value, power_meta = _resolve_prodtest_power_choice(power)
    freq_mhz = 2400 + channel
    sequence = [prodtest.continuous_transmitter(channel, power_value)]
    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label=(
            f"Enabling continuous TX (ch={channel}, power={power_meta['label']})"
        ),
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )

    if not responses:
        console.print("[red]Device returned no response[/]")
        raise typer.Exit(1)

    response = responses[0]
    _render_spi_response(
        "prodtest continuous-tx",
        response,
        command_label="spi.xfer (prodtest)",
    )

    if not response.get("ok"):
        raise typer.Exit(1)

    console.print(
        f"[green]Continuous transmitter enabled[/] channel={channel} ({freq_mhz} MHz) "
        f"power={power_meta['label']} ({power_meta['macro']})"
    )


@prodtest_app.command("hw-device-id")
def prodtest_hw_device_id(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyACM0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Read the prodtest HW Device ID (opcode 'I')."""

    resources = _ctx_resources(ctx)
    sequence = prodtest.hw_device_id_sequence()
    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label="Reading prodtest HW Device ID",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )

    if not responses:
        console.print("[red]Device returned no response[/]")
        raise typer.Exit(1)

    failed_idx = next(
        (idx for idx, resp in enumerate(responses) if not resp.get("ok")), None
    )
    if failed_idx is not None:
        phase = "command" if failed_idx == 0 else "payload"
        _render_spi_response(
            f"prodtest hw-device-id ({phase})",
            responses[failed_idx],
            command_label=f"spi.xfer (prodtest {phase})",
        )
        raise typer.Exit(1)

    if len(responses) != len(sequence):
        console.print(
            "[red]Prodtest command halted before completing all SPI phases[/]"
        )
        raise typer.Exit(1)

    result_response = responses[-1]
    _render_spi_response(
        "prodtest hw-device-id",
        result_response,
        command_label="spi.xfer (prodtest payload)",
    )

    rx_bytes = _decode_hex_response(result_response, label="prodtest hw-device-id")
    if len(rx_bytes) < prodtest.HW_DEVICE_ID_RESULT_LEN:
        console.print("[red]Prodtest HW Device ID response shorter than expected[/]")
        raise typer.Exit(1)

    hw_id = rx_bytes[-prodtest.HW_DEVICE_ID_RESULT_LEN :]
    console.print(f"HW Device ID: {_format_hex(hw_id.hex())}")


@prodtest_app.command("serial-number")
def prodtest_serial_number(
    ctx: typer.Context,
    value: Optional[str] = typer.Option(
        None,
        "--value",
        "-v",
        help="Hex-encoded 8-byte serial number to write (omit to read)",
    ),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyACM0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Read or write the prodtest serial number (opcode 'x'/'X')."""

    resources = _ctx_resources(ctx)
    if value is None:
        sequence = prodtest.serial_number_read_sequence()
        spinner_label = "Reading prodtest serial number"
    else:
        serial_bytes = _parse_fixed_hex(
            value, name="--value", length=prodtest.SERIAL_NUMBER_LEN
        )
        sequence = [prodtest.serial_number_write(serial_bytes)]
        spinner_label = "Writing prodtest serial number"

    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label=spinner_label,
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )

    if not responses:
        console.print("[red]Device returned no response[/]")
        raise typer.Exit(1)

    failed_idx = next(
        (idx for idx, resp in enumerate(responses) if not resp.get("ok")), None
    )
    if failed_idx is not None:
        phase = "command" if failed_idx == 0 else "payload"
        _render_spi_response(
            f"prodtest serial-number ({phase})",
            responses[failed_idx],
            command_label=f"spi.xfer (prodtest {phase})",
        )
        raise typer.Exit(1)

    if len(responses) != len(sequence):
        console.print(
            "[red]Prodtest command halted before completing all SPI phases[/]"
        )
        raise typer.Exit(1)

    if value is None:
        result_response = responses[-1]
        _render_spi_response(
            "prodtest serial-number",
            result_response,
            command_label="spi.xfer (prodtest payload)",
        )
        rx_bytes = _decode_hex_response(result_response, label="prodtest serial-number")
        if len(rx_bytes) < prodtest.SERIAL_NUMBER_LEN:
            console.print(
                "[red]Prodtest serial-number response shorter than expected[/]"
            )
            raise typer.Exit(1)
        serial_bytes = rx_bytes[-prodtest.SERIAL_NUMBER_LEN :]
        console.print(f"Serial number: {_format_hex(serial_bytes.hex())}")
    else:
        _render_spi_response(
            "prodtest serial-number",
            responses[0],
            command_label="spi.xfer (prodtest command)",
        )
        console.print(
            f"[green]Serial number updated[/] value={_format_hex(serial_bytes.hex())}"
        )


@prodtest_app.command("config")
def prodtest_config(
    ctx: typer.Context,
    value: Optional[str] = typer.Option(
        None,
        "--value",
        "-v",
        help="Hex-encoded 5-byte config payload to write (omit to read)",
    ),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyACM0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Read or write the prodtest config (opcode 'r'/'R')."""

    resources = _ctx_resources(ctx)
    if value is None:
        sequence = prodtest.config_read_sequence()
        spinner_label = "Reading prodtest config"
    else:
        config_bytes = _parse_fixed_hex(
            value, name="--value", length=prodtest.CONFIG_WRITE_LEN
        )
        sequence = [prodtest.config_write(config_bytes)]
        spinner_label = "Writing prodtest config"

    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label=spinner_label,
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )

    if not responses:
        console.print("[red]Device returned no response[/]")
        raise typer.Exit(1)

    failed_idx = next(
        (idx for idx, resp in enumerate(responses) if not resp.get("ok")), None
    )
    if failed_idx is not None:
        phase = "command" if failed_idx == 0 else "payload"
        _render_spi_response(
            f"prodtest config ({phase})",
            responses[failed_idx],
            command_label=f"spi.xfer (prodtest {phase})",
        )
        raise typer.Exit(1)

    if len(responses) != len(sequence):
        console.print(
            "[red]Prodtest command halted before completing all SPI phases[/]"
        )
        raise typer.Exit(1)

    if value is None:
        result_response = responses[-1]
        _render_spi_response(
            "prodtest config",
            result_response,
            command_label="spi.xfer (prodtest payload)",
        )
        rx_bytes = _decode_hex_response(result_response, label="prodtest config")
        if len(rx_bytes) < prodtest.CONFIG_RESULT_LEN:
            console.print("[red]Prodtest config response shorter than expected[/]")
            raise typer.Exit(1)
        config_bytes = rx_bytes[-prodtest.CONFIG_RESULT_LEN :]
        console.print(f"Config: {_format_hex(config_bytes.hex())}")
    else:
        _render_spi_response(
            "prodtest config",
            responses[0],
            command_label="spi.xfer (prodtest command)",
        )
        console.print(
            f"[green]Config updated[/] value={_format_hex(config_bytes.hex())}"
        )


@prodtest_app.command("erase-nvmc")
def prodtest_erase_nvmc(
    ctx: typer.Context,
    hw_device_id: str = typer.Argument(
        ...,
        metavar="HW_ID",
        help="Hex-encoded 8-byte HW Device ID (must match device to erase)",
    ),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyACM0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Erase NVMC if the provided HW Device ID matches (opcode 'e')."""

    resources = _ctx_resources(ctx)
    hw_id_bytes = _parse_fixed_hex(
        hw_device_id, name="HW_ID", length=prodtest.ERASE_NVMC_LEN
    )
    sequence = [prodtest.erase_nvmc(hw_id_bytes)]
    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label="Erasing NVMC (if HW ID matches)",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )

    if not responses:
        console.print("[red]Device returned no response[/]")
        raise typer.Exit(1)

    response = responses[0]
    _render_spi_response(
        "prodtest erase-nvmc",
        response,
        command_label="spi.xfer (prodtest)",
    )

    if not response.get("ok"):
        raise typer.Exit(1)

    console.print(
        f"[green]erase-nvmc completed[/] hw-id={_format_hex(hw_id_bytes.hex())}"
    )


@prodtest_app.command("io-self-test")
def prodtest_io_self_test(
    ctx: typer.Context,
    pins_mask: str = typer.Argument(
        ...,
        metavar="PINS",
        help="Eight-byte hex mask describing pins 1-64 (e.g. 0000000000000004)",
    ),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyACM0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Perform the prodtest GPIO self-test (opcode 'T')."""

    resources = _ctx_resources(ctx)
    mask_bytes = _parse_prodtest_mask(pins_mask)
    sequence = prodtest.io_self_test(mask_bytes)
    responses = _execute_timo_sequence(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        sequence=sequence,
        spinner_label="Running prodtest IO self-test",
        logger=resources.get("logger"),
        seq_tracker=resources.get("seq_tracker"),
    )

    if not responses:
        console.print("[red]Device returned no response[/]")
        raise typer.Exit(1)

    if len(responses) != len(sequence):
        console.print(
            "[red]Prodtest command halted before completing all SPI phases[/]"
        )
        raise typer.Exit(1)

    stage_labels = ("command", "result")
    failed_idx = next(
        (idx for idx, resp in enumerate(responses) if not resp.get("ok")), None
    )
    if failed_idx is not None:
        stage = stage_labels[failed_idx]
        _render_spi_response(
            f"prodtest io-self-test ({stage})",
            responses[failed_idx],
            command_label=f"spi.xfer (prodtest {stage})",
        )
        raise typer.Exit(1)

    result_response = responses[-1]
    _render_spi_response(
        "prodtest io-self-test",
        result_response,
        command_label="spi.xfer (prodtest result)",
    )

    rx_bytes = _decode_hex_response(
        result_response, label="prodtest io-self-test result"
    )
    if len(rx_bytes) < prodtest.IO_SELF_TEST_MASK_LEN:
        console.print("[red]Prodtest response shorter than expected[/]")
        raise typer.Exit(1)

    result_mask = rx_bytes[-prodtest.IO_SELF_TEST_MASK_LEN :]
    pins_hex = prodtest.mask_to_hex(mask_bytes)
    result_hex = prodtest.mask_to_hex(result_mask)
    failures = prodtest.failed_pins(mask_bytes, result_mask)

    console.print(f"PINS TO TEST BASE16 ENCODED: {pins_hex}")
    console.print(f"RESULT OF TEST BASE16 ENCODED: {result_hex}")
    console.print(_format_failed_pins_line(failures))


@app.command("spi-cfg")
def spi_cfg_command(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
    hz: Optional[int] = typer.Option(
        None,
        "--hz",
        help="SPI clock frequency in Hz",
        min=1,
    ),
    setup_us: Optional[int] = typer.Option(
        None,
        "--setup-us",
        help="Delay after asserting CS, in microseconds",
        min=0,
    ),
    cs_active: Optional[str] = typer.Option(
        None,
        "--cs-active",
        help="CS polarity (low/high)",
    ),
    bit_order: Optional[str] = typer.Option(
        None,
        "--bit-order",
        help="Bit order (msb/lsb)",
    ),
    byte_order: Optional[str] = typer.Option(
        None,
        "--byte-order",
        help="Byte order (big/little)",
    ),
    clock_polarity: Optional[str] = typer.Option(
        None,
        "--clock-polarity",
        help="Clock polarity (idle_low/idle_high)",
    ),
    clock_phase: Optional[str] = typer.Option(
        None,
        "--clock-phase",
        help="Clock phase (leading/trailing)",
    ),
):
    """Query or update the devboard SPI defaults."""

    resources = _ctx_resources(ctx)
    spi_payload: Dict[str, Any] = {}

    str_fields = {
        "cs_active": cs_active,
        "bit_order": bit_order,
        "byte_order": byte_order,
        "clock_polarity": clock_polarity,
        "clock_phase": clock_phase,
    }
    for name, raw_value in str_fields.items():
        normalized = _normalize_choice(raw_value, name=name)
        if normalized is not None:
            spi_payload[name] = normalized

    for name, numeric_value in (("hz", hz), ("setup_us", setup_us)):
        if numeric_value is not None:
            spi_payload[name] = numeric_value

    resolved_port = _require_port(port)
    action = "Updating" if spi_payload else "Querying"
    with spinner(f"{action} spi.cfg over {resolved_port}"):
        try:
            with _open_serial_client(
                resolved_port,
                baudrate=baudrate,
                timeout=timeout,
                logger=resources.get("logger"),
                seq_tracker=resources.get("seq_tracker"),
            ) as client:
                response = client.spi_cfg(spi=spi_payload if spi_payload else None)
        except ShuttleSerialError as exc:
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(1) from exc

    _render_payload_response("spi.cfg", response)


@app.command("spi-enable")
def spi_enable_command(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Enable SPI on the devboard using the persisted configuration."""

    resources = _ctx_resources(ctx)
    resolved_port = _require_port(port)
    with spinner(f"Enabling SPI over {resolved_port}"):
        try:
            with _open_serial_client(
                resolved_port,
                baudrate=baudrate,
                timeout=timeout,
                logger=resources.get("logger"),
                seq_tracker=resources.get("seq_tracker"),
            ) as client:
                response = client.spi_enable()
        except ShuttleSerialError as exc:
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(1) from exc
    _render_payload_response("spi.enable", response)


@app.command("spi-disable")
def spi_disable_command(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Disable SPI on the devboard and tri-state SPI pins."""

    resources = _ctx_resources(ctx)
    resolved_port = _require_port(port)
    with spinner(f"Disabling SPI over {resolved_port}"):
        try:
            with _open_serial_client(
                resolved_port,
                baudrate=baudrate,
                timeout=timeout,
                logger=resources.get("logger"),
                seq_tracker=resources.get("seq_tracker"),
            ) as client:
                response = client.spi_disable()
        except ShuttleSerialError as exc:
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(1) from exc
    _render_payload_response("spi.disable", response)


@app.command("uart-cfg")
def uart_cfg_command(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
    cfg_baudrate: Optional[int] = typer.Option(
        None,
        "--baudrate",
        help="UART baudrate in Hz",
        min=1200,
        max=4_000_000,
    ),
    stopbits: Optional[int] = typer.Option(
        None,
        "--stopbits",
        help="Stop bits (1 or 2)",
        min=1,
        max=2,
    ),
    parity: Optional[str] = typer.Option(
        None,
        "--parity",
        help="Parity (n/none, e/even, o/odd)",
    ),
):
    """Query or update the devboard UART defaults."""

    resources = _ctx_resources(ctx)
    uart_payload: Dict[str, Any] = {}
    normalized_parity = _normalize_uart_parity(parity)
    if normalized_parity is not None:
        uart_payload["parity"] = normalized_parity

    if stopbits is not None:
        uart_payload["stopbits"] = stopbits

    if cfg_baudrate is not None:
        uart_payload["baudrate"] = cfg_baudrate

    resolved_port = _require_port(port)
    action = "Updating" if uart_payload else "Querying"
    with spinner(f"{action} uart.cfg over {resolved_port}"):
        try:
            with _open_serial_client(
                resolved_port,
                baudrate=baudrate,
                timeout=timeout,
                logger=resources.get("logger"),
                seq_tracker=resources.get("seq_tracker"),
            ) as client:
                response = client.uart_cfg(uart=uart_payload if uart_payload else None)
        except ShuttleSerialError as exc:
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(1) from exc

    _render_payload_response("uart.cfg", response)


@app.command("uart-sub")
def uart_sub_command(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
    enable: Optional[bool] = typer.Option(
        None,
        "--enable/--disable",
        help="Enable or disable uart.rx event emission",
    ),
    gap_ms: Optional[int] = typer.Option(
        None,
        "--gap-ms",
        min=0,
        max=1000,
        help="Milliseconds of idle before emitting buffered bytes",
    ),
    buf: Optional[int] = typer.Option(
        None,
        "--buf",
        min=1,
        max=1024,
        help="Emit an event once this many bytes are buffered",
    ),
):
    """Query or update uart.rx subscription settings."""

    resources = _ctx_resources(ctx)
    sub_payload: Dict[str, Any] = {}
    if enable is not None:
        sub_payload["enable"] = enable
    if gap_ms is not None:
        sub_payload["gap_ms"] = gap_ms
    if buf is not None:
        sub_payload["buf"] = buf

    resolved_port = _require_port(port)
    action = "Updating" if sub_payload else "Querying"
    with spinner(f"{action} uart.sub over {resolved_port}"):
        try:
            with _open_serial_client(
                resolved_port,
                baudrate=baudrate,
                timeout=timeout,
                logger=resources.get("logger"),
                seq_tracker=resources.get("seq_tracker"),
            ) as client:
                response = client.uart_sub(sub_payload if sub_payload else None)
        except ShuttleSerialError as exc:
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(1) from exc

    _render_payload_response("uart.sub", response)


@app.command("wifi-cfg")
def wifi_cfg_command(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port or host:port (e.g., /dev/ttyUSB0 or 192.168.1.10:5000)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
    ssid: Optional[str] = typer.Option(
        None,
        "--ssid",
        help="Set the station SSID",
        show_default=False,
    ),
    psk: Optional[str] = typer.Option(
        None,
        "--psk",
        help="Set the WPA/WPA2/WPA3 passphrase",
        show_default=False,
    ),
    dhcp: Optional[bool] = typer.Option(
        None,
        "--dhcp/--static",
        help="Enable DHCP or force static IPv4 addressing",
    ),
    ip_addr: Optional[str] = typer.Option(
        None,
        "--ip",
        help="Static IPv4 address (requires --static or other static fields)",
        show_default=False,
    ),
    netmask: Optional[str] = typer.Option(
        None,
        "--netmask",
        help="Static subnet mask (e.g., 255.255.255.0)",
        show_default=False,
    ),
    gateway: Optional[str] = typer.Option(
        None,
        "--gateway",
        help="Static default gateway IPv4 address",
        show_default=False,
    ),
    dns: Optional[str] = typer.Option(
        None,
        "--dns",
        help="Primary DNS server IPv4 address",
        show_default=False,
    ),
    dns_alt: Optional[str] = typer.Option(
        None,
        "--dns-alt",
        help="Secondary DNS server IPv4 address",
        show_default=False,
    ),
):
    """Query or update Wi-Fi credentials and network settings."""

    resources = _ctx_resources(ctx)
    wifi_payload: Dict[str, Any] = {}
    if ssid is not None:
        wifi_payload["ssid"] = ssid
    if psk is not None:
        wifi_payload["psk"] = psk
    if dhcp is not None:
        wifi_payload["dhcp"] = dhcp

    network_payload: Dict[str, Any] = {}
    parsed_ip = _parse_ipv4(ip_addr, name="--ip")
    parsed_mask = _parse_ipv4(netmask, name="--netmask")
    parsed_gateway = _parse_ipv4(gateway, name="--gateway")
    parsed_dns_primary = _parse_ipv4(dns, name="--dns")
    parsed_dns_secondary = _parse_ipv4(dns_alt, name="--dns-alt")

    if parsed_ip is not None:
        network_payload["ip"] = parsed_ip
    if parsed_mask is not None:
        network_payload["netmask"] = parsed_mask
    if parsed_gateway is not None:
        network_payload["gateway"] = parsed_gateway

    dns_entries = [
        entry for entry in (parsed_dns_primary, parsed_dns_secondary) if entry
    ]
    if dns_entries:
        network_payload["dns"] = dns_entries

    if network_payload:
        if wifi_payload.get("dhcp") is True:
            raise typer.BadParameter(
                "Static network options cannot be combined with --dhcp"
            )
        wifi_payload.setdefault("dhcp", False)
        wifi_payload["network"] = network_payload

    resolved_port = _require_port(port)
    action = "Updating" if wifi_payload else "Querying"
    with spinner(f"{action} wifi.cfg over {resolved_port}"):
        try:
            with _open_serial_client(
                resolved_port,
                baudrate=baudrate,
                timeout=timeout,
                logger=resources.get("logger"),
                seq_tracker=resources.get("seq_tracker"),
            ) as client:
                response = client.wifi_cfg(wifi_payload if wifi_payload else None)
        except ShuttleSerialError as exc:
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(1) from exc

    _render_payload_response("wifi.cfg", response)


@app.command("uart-tx")
def uart_tx_command(
    ctx: typer.Context,
    data: Optional[str] = typer.Argument(
        None,
        metavar="[HEX|'-']",
        help="Hex payload to send; pass '-' to read raw bytes from stdin",
        show_default=False,
    ),
    text: Optional[str] = typer.Option(
        None,
        "--text",
        help="Literal text payload to encode using --encoding",
        show_default=False,
    ),
    file: Optional[Path] = typer.Option(
        None,
        "--file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Read raw bytes from FILE instead of specifying HEX on the command line",
        show_default=False,
    ),
    newline: bool = typer.Option(
        False,
        "--newline",
        help="Append a newline when using --text/--file/stdin payloads",
        show_default=False,
    ),
    encoding: str = typer.Option(
        "utf-8",
        "--encoding",
        help="Text encoding for --text payloads",
    ),
    uart_port: Optional[int] = typer.Option(
        None,
        "--uart-port",
        min=0,
        help="Target device UART index (defaults to firmware's primary UART)",
    ),
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Send raw UART bytes using the uart.tx protocol command."""

    resources = _ctx_resources(ctx)
    payload_hex, payload_len = _resolve_uart_payload(
        data_arg=data,
        text_payload=text,
        file_path=file,
        encoding=encoding,
        append_newline=newline,
    )
    resolved_port = _require_port(port)
    byte_label = "byte" if payload_len == 1 else "bytes"
    with spinner(f"Sending {payload_len} UART {byte_label} over {resolved_port}"):
        try:
            with _open_serial_client(
                resolved_port,
                baudrate=baudrate,
                timeout=timeout,
                logger=resources.get("logger"),
                seq_tracker=resources.get("seq_tracker"),
            ) as client:
                response = client.uart_tx(payload_hex, port=uart_port)
        except ShuttleSerialError as exc:
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(1) from exc

    _render_payload_response("uart.tx", response)


@app.command("uart-rx")
def uart_rx_command(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
    duration: Optional[float] = typer.Option(
        None,
        "--duration",
        min=0.0,
        help="Listen for uart.rx events for N seconds before exiting",
    ),
    forever: bool = typer.Option(
        False,
        "--forever",
        help="Stream uart.rx events until interrupted",
    ),
    ensure_subscription: bool = typer.Option(
        True,
        "--ensure-subscription/--no-ensure-subscription",
        help="Call uart.sub --enable before listening",
    ),
    gap_ms: Optional[int] = typer.Option(
        None,
        "--gap-ms",
        min=0,
        max=1000,
        help="Override gap_ms while ensuring the subscription",
    ),
    buf: Optional[int] = typer.Option(
        None,
        "--buf",
        min=1,
        max=1024,
        help="Override buf while ensuring the subscription",
    ),
):
    """Stream uart.rx events emitted by the firmware."""

    if forever and duration is not None:
        raise typer.BadParameter("--duration cannot be combined with --forever")

    if (gap_ms is not None or buf is not None) and not ensure_subscription:
        raise typer.BadParameter("--gap-ms/--buf require --ensure-subscription")

    resources = _ctx_resources(ctx)
    resolved_port = _require_port(port)
    console.print(f"Listening for uart.rx events on {resolved_port}...")

    events_seen = 0
    try:
        with _open_serial_client(
            resolved_port,
            baudrate=baudrate,
            timeout=timeout,
            logger=resources.get("logger"),
            seq_tracker=resources.get("seq_tracker"),
        ) as client:
            if ensure_subscription:
                sub_payload: Dict[str, Any] = {"enable": True}
                if gap_ms is not None:
                    sub_payload["gap_ms"] = gap_ms
                if buf is not None:
                    sub_payload["buf"] = buf
                client.uart_sub(sub_payload)
            listener = client.register_event_listener("uart.rx")
            events_seen = _consume_uart_events(
                listener, duration=duration, forever=forever
            )
    except ShuttleSerialError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(1) from exc
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/]")
        raise typer.Exit(1)

    if not events_seen:
        console.print("[yellow]No uart.rx events observed[/]")


@app.command("power")
def power_command(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port (e.g., /dev/ttyUSB0)",
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
    enable: Optional[bool] = typer.Option(
        None,
        "--enable/--disable",
        help="Enable or disable the downstream power rail",
    ),
):
    """Query or toggle the downstream power rail."""

    resources = _ctx_resources(ctx)
    resolved_port = _require_port(port)
    if enable is None:
        action = "Querying"
        label = "power.state"
        method_name = "power_state"
    elif enable:
        action = "Enabling"
        label = "power.enable"
        method_name = "power_enable"
    else:
        action = "Disabling"
        label = "power.disable"
        method_name = "power_disable"

    with spinner(f"{action} power over {resolved_port}"):
        try:
            with _open_serial_client(
                resolved_port,
                baudrate=baudrate,
                timeout=timeout,
                logger=resources.get("logger"),
                seq_tracker=resources.get("seq_tracker"),
            ) as client:
                method = getattr(client, method_name)
                response = method()
        except ShuttleSerialError as exc:
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(1) from exc

    _render_payload_response(label, response)


@app.command("flash")
def flash_command(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None,
        "--port",
        envvar="SHUTTLE_PORT",
        help="Serial port connected to the ESP32-C5 devboard",
    ),
    baudrate: int = typer.Option(
        DEFAULT_BAUD,
        "--baud",
        help="Serial baud used for the ROM bootloader",
    ),
    board: str = typer.Option(
        DEFAULT_BOARD,
        "--board",
        help="Firmware bundle to flash",
    ),
    erase_first: bool = typer.Option(
        False,
        "--erase-first/--no-erase-first",
        help="Erase the entire flash before writing",
    ),
):
    """Flash the bundled firmware image to the devboard."""

    resolved_port = _require_port(port)
    available_boards = flash_module.list_available_boards()
    available = ", ".join(available_boards)
    if board not in available_boards:
        raise typer.BadParameter(
            f"Unknown firmware bundle '{board}'. Available: {available}"
        )

    with spinner(f"Flashing {board} firmware to {resolved_port}"):
        try:
            manifest = flash_module.flash_firmware(
                port=resolved_port,
                baudrate=baudrate,
                board=board,
                erase_first=erase_first,
            )
        except flash_module.FirmwareFlashError as exc:
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(1) from exc

    label = str(manifest.get("label", board))
    console.print(
        f"[green]Successfully flashed {label} ({board}) over {resolved_port}[/]"
    )


@app.command("get-info")
def get_info(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None, "--port", envvar="SHUTTLE_PORT", help="Serial port (e.g., /dev/ttyUSB0)"
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Fetch device capabilities using the get.info command."""

    resources = _ctx_resources(ctx)
    resolved_port = _require_port(port)
    with spinner(f"Querying get.info over {resolved_port}"):
        try:
            with _open_serial_client(
                resolved_port,
                baudrate=baudrate,
                timeout=timeout,
                logger=resources.get("logger"),
                seq_tracker=resources.get("seq_tracker"),
            ) as client:
                response = client.get_info()
        except ShuttleSerialError as exc:
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(1) from exc
    _render_info_response(response)


@app.command("ping")
def ping(
    ctx: typer.Context,
    port: Optional[str] = typer.Option(
        None, "--port", envvar="SHUTTLE_PORT", help="Serial port (e.g., /dev/ttyUSB0)"
    ),
    baudrate: int = typer.Option(DEFAULT_BAUD, "--baud", help="Serial baud rate"),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", help="Read timeout in seconds"
    ),
):
    """Send a ping command to get firmware/protocol metadata."""

    resources = _ctx_resources(ctx)
    resolved_port = _require_port(port)
    with spinner(f"Pinging device over {resolved_port}"):
        try:
            with _open_serial_client(
                resolved_port,
                baudrate=baudrate,
                timeout=timeout,
                logger=resources.get("logger"),
                seq_tracker=resources.get("seq_tracker"),
            ) as client:
                response = client.ping()
        except ShuttleSerialError as exc:
            console.print(f"[red]{exc}[/]")
            raise typer.Exit(1) from exc
    _render_ping_response(response)


if __name__ == "__main__":
    app()
