import io

import pytest
from shuttle import timo


def test_format_bytes_empty():
    assert timo.format_bytes(b"") == "—"


def test_format_bytes_single():
    assert timo.format_bytes(b"\x01") == "01"


def test_format_bytes_multi():
    assert timo.format_bytes(b"\x01\x02\x0a\xff") == "01 02 0a ff"


def test_requires_restart():
    assert timo.requires_restart(0x80) is True
    assert timo.requires_restart(0x00) is False
    assert timo.requires_restart(0x7F) is False
    assert timo.requires_restart(0xFF) is True


def test_read_asc_and_rdm_sequences():
    asc_seq = timo.read_asc_sequence(2)
    rdm_seq = timo.read_rdm_sequence(3)
    assert asc_seq[0]["tx"] == bytes([timo.READ_ASC_CMD]).hex()
    assert asc_seq[1]["tx"] == bytes([timo.READ_REG_DUMMY, 0x00, 0x00]).hex()
    assert rdm_seq[0]["tx"] == bytes([timo.READ_RDM_CMD]).hex()
    assert "wait_irq" in asc_seq[0]
    assert "wait_irq" in rdm_seq[0]
    with pytest.raises(ValueError):
        timo.read_asc_sequence(0)
    with pytest.raises(ValueError):
        timo.read_rdm_sequence(0)


def test_write_dmx_and_rdm_commands():
    dmx_cmd = timo.write_dmx_command(b"\x01\x02")
    rdm_cmd = timo.write_rdm_command(b"\x03\x04")
    assert dmx_cmd["tx"].startswith(bytes([timo.WRITE_DMX_CMD]).hex())
    assert rdm_cmd["tx"].startswith(bytes([timo.WRITE_RDM_CMD]).hex())
    assert dmx_cmd["n"] == 3
    assert rdm_cmd["n"] == 3


def test_slice_bits():
    data = bytes.fromhex("0a0b0c0d")
    # Bits indexed from MSB (0) to LSB (31)
    assert timo.slice_bits(data, 0, 3) == 0x0  # top nibble of 0x0A
    assert timo.slice_bits(data, 4, 7) == 0xA
    assert timo.slice_bits(data, 8, 15) == 0x0B
    assert timo.slice_bits(data, 28, 31) == 0xD  # low nibble
    assert timo.slice_bits(data, 0, 31) == int.from_bytes(data, "big")


def test_register_map_contains_expected_entries():
    assert "CONFIG" in timo.REGISTER_MAP
    assert timo.REGISTER_MAP["CONFIG"]["address"] == 0x00
    assert "UART_EN" in timo.REGISTER_MAP["CONFIG"]["fields"]
    assert "PRODUCT_ID" in timo.REGISTER_MAP
    assert timo.REGISTER_MAP["PRODUCT_ID"]["address"] == 0x3F


def test_parse_read_reg_response_errors():
    # Not enough frames
    with pytest.raises(ValueError):
        timo.parse_read_reg_response(0, 1, ["00"])
    # Command frame wrong length
    with pytest.raises(ValueError):
        timo.parse_read_reg_response(0, 1, ["", "00ff"])
    with pytest.raises(ValueError):
        timo.parse_read_reg_response(0, 1, ["abcd", "00ff"])
    # Payload frame too short
    with pytest.raises(ValueError):
        timo.parse_read_reg_response(0, 2, ["00", "00"])
    # Valid parse
    result = timo.parse_read_reg_response(1, 2, ["40", "00cafe"])
    assert result.address == 1
    assert result.length == 2
    assert result.data == b"\xca\xfe"
    assert result.irq_flags_command == 0x40
    assert result.irq_flags_payload == 0x00


def test_read_cci_header_and_iter_chunks():
    payload_1 = bytes(range(timo.FW_BLOCK_CMD_1_SIZE))
    payload_2 = bytes(range(timo.FW_BLOCK_CMD_2_SIZE))
    buffer = io.BytesIO(b"\xaa\xbb\xcc\xdd" + payload_1 + payload_2)
    header = timo.read_cci_header(buffer)
    assert header == b"\xaa\xbb\xcc\xdd"
    chunks = list(timo.iter_cci_chunks(buffer))
    assert len(chunks) == 1
    index, first, second = chunks[0]
    assert index == 1
    assert first == payload_1
    assert second == payload_2


def test_iter_cci_chunks_detects_truncation():
    payload = b"A" * timo.FW_BLOCK_CMD_1_SIZE + b"B" * (timo.FW_BLOCK_CMD_2_SIZE - 1)
    buffer = io.BytesIO(b"\x00\x00\x00\x00" + payload)
    timo.read_cci_header(buffer)
    with pytest.raises(ValueError):
        next(timo.iter_cci_chunks(buffer))


def test_iter_cci_chunks_detects_first_payload_truncation():
    payload = b"A" * (timo.FW_BLOCK_CMD_1_SIZE - 1)
    buffer = io.BytesIO(b"\x00\x00\x00\x00" + payload)
    timo.read_cci_header(buffer)
    with pytest.raises(ValueError):
        next(timo.iter_cci_chunks(buffer))


def test_read_cci_header_requires_full_header():
    buffer = io.BytesIO(b"\x01\x02\x03")
    with pytest.raises(ValueError):
        timo.read_cci_header(buffer)


def test_parse_read_dmx_response_errors():
    with pytest.raises(ValueError):
        timo.parse_read_dmx_response(1, ["00"])
    with pytest.raises(ValueError):
        timo.parse_read_dmx_response(1, ["", "00"])
    with pytest.raises(ValueError):
        timo.parse_read_dmx_response(2, ["00", "00"])
