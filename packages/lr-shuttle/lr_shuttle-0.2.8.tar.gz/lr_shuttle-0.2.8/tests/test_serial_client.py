import json
import queue
from pathlib import Path

import pytest

import shuttle.serial_client as serial_client


def test_sequence_tracker_handles_empty_file(tmp_path):
    meta = tmp_path / "seq.meta"
    meta.write_text("", encoding="utf-8")
    tracker = serial_client.SequenceTracker(meta)
    assert tracker._last_seq is None


def test_sequence_tracker_dir_creation_error(monkeypatch, tmp_path):
    meta = tmp_path / "seq.meta"

    def fail_mkdir(self, *args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr(Path, "mkdir", fail_mkdir)
    with pytest.raises(ValueError):
        serial_client.SequenceTracker(meta)


def test_sequence_tracker_read_error(monkeypatch, tmp_path):
    meta = tmp_path / "seq.meta"
    meta.write_text("42", encoding="utf-8")

    def fail_read(self, *args, **kwargs):
        raise OSError("boom")

    monkeypatch.setattr(Path, "read_text", fail_read)
    with pytest.raises(ValueError):
        serial_client.SequenceTracker(meta)


def test_ndjson_serial_client_opens_closed_port(monkeypatch):
    class DummySerial:
        def __init__(self):
            self.is_open = False
            self.open_calls = 0
            self.reset_calls = 0

        def open(self):
            self.open_calls += 1
            self.is_open = True

        def reset_input_buffer(self):
            self.reset_calls += 1

        def close(self):
            self.is_open = False

    stub = DummySerial()
    captured = {}

    def fake_serial_for_url(*args, **kwargs):
        captured["kwargs"] = kwargs
        return stub

    monkeypatch.setattr(serial_client.serial, "serial_for_url", fake_serial_for_url)

    client = serial_client.NDJSONSerialClient("/dev/null", baudrate=57600, timeout=0.5)

    assert captured["kwargs"]["do_not_open"] is True
    assert stub.open_calls == 1
    assert stub.reset_calls == 1
    assert stub.is_open is True

    client.close()
    assert stub.is_open is False


def test_ndjson_serial_client_handles_serial_without_open(monkeypatch):
    class NoOpenSerial:
        def __init__(self):
            self.is_open = True
            self.reset_calls = 0

        def reset_input_buffer(self):
            self.reset_calls += 1

        def close(self):
            self.is_open = False

    stub = NoOpenSerial()
    monkeypatch.setattr(
        serial_client.serial, "serial_for_url", lambda *args, **kwargs: stub
    )

    client = serial_client.NDJSONSerialClient("/dev/null", baudrate=115200, timeout=0.1)

    assert stub.reset_calls == 1
    client.close()
    assert stub.is_open is False


def test_ndjson_serial_client_close_closes_underlying():
    class DummySerial:
        def __init__(self):
            self.is_open = True
            self.closed = False

        def close(self):
            self.closed = True
            self.is_open = False

    client = serial_client.NDJSONSerialClient.__new__(serial_client.NDJSONSerialClient)
    client._serial = DummySerial()

    client.close()

    assert client._serial.closed is True
    assert client._serial.is_open is False


def test_ndjson_serial_client_payload_builders():
    calls = []

    def _command(op, payload):
        calls.append((op, payload))
        return {"op": op, "payload": payload}

    client = serial_client.NDJSONSerialClient.__new__(serial_client.NDJSONSerialClient)
    client._command = _command
    client._seq_tracker = None

    client.spi_cfg({"hz": 123})
    client.uart_cfg({"baudrate": 9600})
    client.spi_enable()
    client.spi_disable()
    client.uart_sub({"enable": True, "gap_ms": 5})
    client.uart_sub()
    client.power_state()
    client.power_enable()
    client.power_disable()

    assert calls == [
        ("spi.cfg", {"spi": {"hz": 123}}),
        ("uart.cfg", {"uart": {"baudrate": 9600}}),
        ("spi.enable", {}),
        ("spi.disable", {}),
        ("uart.sub", {"uart": {"sub": {"enable": True, "gap_ms": 5}}}),
        ("uart.sub", {}),
        ("power.state", {}),
        ("power.enable", {}),
        ("power.disable", {}),
    ]


def test_record_sequence_no_tracker(monkeypatch):
    client = serial_client.NDJSONSerialClient.__new__(serial_client.NDJSONSerialClient)
    client._seq_tracker = None
    client._record_sequence({"type": "resp", "id": 1, "seq": 10})


def test_client_uses_injected_logger_and_tracker(monkeypatch):
    writes = []

    class DummySerial:
        def __init__(self, *args, **kwargs):
            self.is_open = True
            self.writes = writes

        def reset_input_buffer(self):
            pass

        def write(self, data):
            self.writes.append(data)
            return len(data)

        def close(self):
            self.is_open = False

    logger_calls = []

    class DummyLogger:
        def log(self, direction, payload):
            logger_calls.append((direction, payload))

    class DummyTracker:
        def __init__(self):
            self.observed = []

        def observe(self, seq, source):
            self.observed.append((seq, source))

    monkeypatch.setattr(serial_client.serial, "Serial", DummySerial)
    logger = DummyLogger()
    tracker = DummyTracker()
    client = serial_client.NDJSONSerialClient(
        "/dev/null", baudrate=1, timeout=1.0, logger=logger, seq_tracker=tracker
    )

    client._log_serial("TX", b"payload")
    client._record_sequence({"type": "resp", "id": 1, "seq": 5})

    assert logger_calls == [("TX", b"payload")]
    assert tracker.observed == [(5, "response id=1")]


def test_client_no_tracker_skips_observation(monkeypatch):
    class DummySerial:
        def __init__(self, *args, **kwargs):
            self.is_open = True

        def reset_input_buffer(self):
            pass

        def write(self, data):
            return len(data)

        def close(self):
            self.is_open = False

    monkeypatch.setattr(serial_client.serial, "Serial", DummySerial)
    client = serial_client.NDJSONSerialClient("/dev/null", baudrate=1, timeout=1.0)
    client._record_sequence({"type": "resp", "id": 9, "seq": 2})


def test_event_callback_receives_events(monkeypatch):
    class DummySerial:
        def __init__(self, *args, **kwargs):
            self.is_open = True

        def reset_input_buffer(self):
            pass

        def close(self):
            self.is_open = False

    monkeypatch.setattr(
        serial_client.serial, "serial_for_url", lambda *args, **kwargs: DummySerial()
    )
    client = serial_client.NDJSONSerialClient("/dev/null", baudrate=1, timeout=0.1)
    received = []

    def _callback(event):
        received.append(event)

    client.set_event_callback(_callback)
    client._dispatch({"type": "ev", "ev": "sys.error", "code": "EFAIL", "seq": 5})

    assert received and received[0]["code"] == "EFAIL"
    client.close()


def test_send_command_future_and_event_listener(monkeypatch):
    class DummySerial:
        def __init__(self, *args, **kwargs):
            self.lines = queue.Queue()
            self.is_open = True

        def reset_input_buffer(self):
            pass

        def write(self, data):
            return len(data)

        def readline(self):
            try:
                return self.lines.get(timeout=0.1)
            except queue.Empty:
                return b""

        def close(self):
            self.is_open = False

    serial_obj = DummySerial()
    monkeypatch.setattr(serial_client.serial, "Serial", lambda *a, **kw: serial_obj)
    client = serial_client.NDJSONSerialClient("/dev/null", baudrate=1, timeout=0.2)
    client._next_cmd_id = lambda: 1  # type: ignore[assignment]

    irq_listener = client.register_event_listener("irq")
    future = client.send_command("ping", {})

    serial_obj.lines.put(b'{"type":"ev","ev":"irq","edge":"rising"}\n')
    serial_obj.lines.put(b'{"type":"resp","id":1,"ok":true}\n')

    assert future.result(timeout=1)["ok"] is True
    assert irq_listener.next(timeout=1)["edge"] == "rising"
    client.close()


def test_multiple_listeners_receive_same_event(monkeypatch):
    class DummySerial:
        def __init__(self, *args, **kwargs):
            self.lines = queue.Queue()
            self.is_open = True

        def reset_input_buffer(self):
            pass

        def write(self, data):
            return len(data)

        def readline(self):
            try:
                return self.lines.get(timeout=0.1)
            except queue.Empty:
                return b""

        def close(self):
            self.is_open = False

    serial_obj = DummySerial()
    monkeypatch.setattr(serial_client.serial, "Serial", lambda *a, **kw: serial_obj)
    client = serial_client.NDJSONSerialClient("/dev/null", baudrate=1, timeout=0.2)
    listener_a = client.register_event_listener("dmx")
    listener_b = client.register_event_listener("dmx")

    serial_obj.lines.put(b'{"type":"ev","ev":"dmx","payload":1}\n')

    assert listener_a.next(timeout=1)["payload"] == 1
    assert listener_b.next(timeout=1)["payload"] == 1
    client.close()


def test_command_future_timeout():
    future = serial_client.CommandFuture(cmd_id=1, timeout=0.01)
    with pytest.raises(serial_client.ShuttleSerialError):
        future.result(timeout=1)


def test_command_future_without_timer():
    future = serial_client.CommandFuture(cmd_id=2, timeout=0)
    future.mark_result({"ok": True})
    assert future.result(timeout=1)["ok"] is True
    # Ensure duplicate completions are ignored
    future.mark_exception(RuntimeError("late"))
    assert future.result(timeout=1)["ok"] is True


def test_event_subscription_queueing():
    sub = serial_client.EventSubscription("irq")
    sub.emit({"edge": "rising"})
    sub.emit({"edge": "falling"})
    assert sub.next(timeout=1)["edge"] == "rising"
    assert sub.next(timeout=1)["edge"] == "falling"
    with pytest.raises(serial_client.ShuttleSerialError):
        sub.fail(serial_client.ShuttleSerialError("boom"))
        sub.next(timeout=0.1)
    # When already closed, additional emits are ignored and completed future is returned
    with pytest.raises(serial_client.ShuttleSerialError):
        sub.emit({"edge": "extra"})
        sub.next(timeout=0.1)


def test_event_subscription_next_uses_internal_queue():
    sub = serial_client.EventSubscription("irq")
    sub._queue.append({"edge": "queued"})  # type: ignore[attr-defined]
    assert sub.next(timeout=0)["edge"] == "queued"


def test_event_subscription_future_returns_from_queue():
    sub = serial_client.EventSubscription("irq")
    sub._queue.append({"edge": "queued"})  # type: ignore[attr-defined]
    future = sub.future()
    assert future.result(timeout=0)["edge"] == "queued"


def test_event_subscription_fail_sets_pending_future():
    sub = serial_client.EventSubscription("irq")
    sub.fail(serial_client.ShuttleSerialError("boom"))
    with pytest.raises(serial_client.ShuttleSerialError):
        sub.next(timeout=0)


def test_response_backlog_delivered(monkeypatch):
    class DummySerial:
        def __init__(self, *args, **kwargs):
            self.lines = queue.Queue()
            self.is_open = True

        def reset_input_buffer(self):
            pass

        def write(self, data):
            return len(data)

        def readline(self):
            try:
                return self.lines.get(timeout=0.1)
            except queue.Empty:
                return b""

        def close(self):
            self.is_open = False

    serial_obj = DummySerial()
    monkeypatch.setattr(serial_client.serial, "Serial", lambda *a, **kw: serial_obj)
    client = serial_client.NDJSONSerialClient("/dev/null", baudrate=1, timeout=0.2)
    # Simulate response arriving before the command is issued
    serial_obj.lines.put(b'{"type":"resp","id":1,"ok":true}\n')
    client._dispatch(json.loads(serial_obj.lines.get().decode()))
    future = client.send_command("ping", {})
    assert future.result(timeout=1)["ok"] is True
    client.close()
