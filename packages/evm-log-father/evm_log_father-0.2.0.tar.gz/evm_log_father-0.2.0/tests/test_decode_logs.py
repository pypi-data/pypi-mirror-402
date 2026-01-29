# Copyright (c) 2026 adidonato
# SPDX-License-Identifier: MIT

"""Tests for the batch decode_logs API."""

import pytest
from evm_log_father import EventSchema, decode_logs


# Transfer event selector: keccak256("Transfer(address,address,uint256)")
TRANSFER_SELECTOR = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def make_transfer_log(
    from_addr: str,
    to_addr: str,
    value: int,
    block_number: int = 12345678,
    tx_hash: str = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    log_index: int = 0,
    contract: str = "0xdac17f958d2ee523a2206206994597c13d831ec7",
) -> dict:
    """Helper to create a raw Transfer log dict."""
    # Pad addresses to 32 bytes (64 hex chars)
    from_padded = "0x" + from_addr.lower().replace("0x", "").zfill(64)
    to_padded = "0x" + to_addr.lower().replace("0x", "").zfill(64)
    # Encode value as 32-byte hex
    value_hex = "0x" + value.to_bytes(32, "big").hex()

    return {
        "topics": [TRANSFER_SELECTOR, from_padded, to_padded],
        "data": value_hex,
        "block_number": block_number,
        "tx_hash": tx_hash,
        "log_index": log_index,
        "contract": contract,
    }


class TestDecodeLogs:
    """Tests for decode_logs batch API."""

    def test_decode_single_log(self):
        """Test decoding a single log in a batch."""
        schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")
        raw_logs = [
            make_transfer_log(
                from_addr="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                to_addr="0xb0c7891c6218b36c1d19d4a2e9eb0ce3606eb990",
                value=100_000_000,
            )
        ]

        decoded = decode_logs(schema, raw_logs)

        assert len(decoded) == 1
        log = decoded[0]
        assert log["block_number"] == 12345678
        assert log["log_index"] == 0
        assert log["params"]["from"] == "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        assert log["params"]["to"] == "0xb0c7891c6218b36c1d19d4a2e9eb0ce3606eb990"
        assert log["params"]["value"] == "100000000"

    def test_decode_multiple_logs(self):
        """Test decoding multiple logs in a batch."""
        schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")
        raw_logs = [
            make_transfer_log(
                from_addr="0xaaaa00000000000000000000000000000000aaaa",
                to_addr="0xbbbb00000000000000000000000000000000bbbb",
                value=1000,
                block_number=100,
                log_index=0,
            ),
            make_transfer_log(
                from_addr="0xcccc00000000000000000000000000000000cccc",
                to_addr="0xdddd00000000000000000000000000000000dddd",
                value=2000,
                block_number=101,
                log_index=1,
            ),
            make_transfer_log(
                from_addr="0xeeee00000000000000000000000000000000eeee",
                to_addr="0xffff00000000000000000000000000000000ffff",
                value=3000,
                block_number=102,
                log_index=2,
            ),
        ]

        decoded = decode_logs(schema, raw_logs)

        assert len(decoded) == 3
        assert decoded[0]["block_number"] == 100
        assert decoded[0]["params"]["value"] == "1000"
        assert decoded[1]["block_number"] == 101
        assert decoded[1]["params"]["value"] == "2000"
        assert decoded[2]["block_number"] == 102
        assert decoded[2]["params"]["value"] == "3000"

    def test_decode_with_parallel_false(self):
        """Test decoding with parallel=False."""
        schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")
        raw_logs = [
            make_transfer_log(
                from_addr="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                to_addr="0xb0c7891c6218b36c1d19d4a2e9eb0ce3606eb990",
                value=100,
            )
        ]

        decoded = decode_logs(schema, raw_logs, parallel=False)

        assert len(decoded) == 1
        assert decoded[0]["params"]["value"] == "100"

    def test_decode_with_bytes_data(self):
        """Test decoding with data as bytes instead of hex string."""
        schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")
        raw_logs = [
            {
                "topics": [
                    TRANSFER_SELECTOR,
                    "0x000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                    "0x000000000000000000000000b0c7891c6218b36c1d19d4a2e9eb0ce3606eb990",
                ],
                "data": bytes.fromhex("0000000000000000000000000000000000000000000000000000000005f5e100"),
                "block_number": 12345678,
                "tx_hash": "0xabcdef",
                "log_index": 0,
                "contract": "0xdac17f958d2ee523a2206206994597c13d831ec7",
            }
        ]

        decoded = decode_logs(schema, raw_logs)

        assert len(decoded) == 1
        assert decoded[0]["params"]["value"] == "100000000"

    def test_decode_empty_list(self):
        """Test decoding an empty list returns empty list."""
        schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")

        decoded = decode_logs(schema, [])

        assert decoded == []

    def test_decode_skips_invalid_logs(self):
        """Test that invalid logs are skipped (not causing errors)."""
        schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")
        raw_logs = [
            # Valid log
            make_transfer_log(
                from_addr="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                to_addr="0xb0c7891c6218b36c1d19d4a2e9eb0ce3606eb990",
                value=100,
            ),
            # Invalid log (wrong selector)
            {
                "topics": [
                    "0x1111111111111111111111111111111111111111111111111111111111111111",
                    "0x000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                ],
                "data": "0x",
                "block_number": 999,
                "tx_hash": "0x",
                "log_index": 0,
                "contract": "0x",
            },
            # Another valid log
            make_transfer_log(
                from_addr="0xc0c7891c6218b36c1d19d4a2e9eb0ce3606eb111",
                to_addr="0xd0c7891c6218b36c1d19d4a2e9eb0ce3606eb222",
                value=200,
            ),
        ]

        decoded = decode_logs(schema, raw_logs)

        # Only valid logs should be decoded (invalid ones are skipped)
        assert len(decoded) == 2
        assert decoded[0]["params"]["value"] == "100"
        assert decoded[1]["params"]["value"] == "200"

    def test_decode_with_optional_fields_missing(self):
        """Test decoding with optional fields missing uses defaults."""
        schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")
        raw_logs = [
            {
                "topics": [
                    TRANSFER_SELECTOR,
                    "0x000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                    "0x000000000000000000000000b0c7891c6218b36c1d19d4a2e9eb0ce3606eb990",
                ],
                "data": "0x0000000000000000000000000000000000000000000000000000000005f5e100",
            }
        ]

        decoded = decode_logs(schema, raw_logs)

        assert len(decoded) == 1
        assert decoded[0]["block_number"] == 0
        assert decoded[0]["tx_hash"] == ""
        assert decoded[0]["log_index"] == 0
        assert decoded[0]["contract"] == ""

    def test_decode_large_batch(self):
        """Test decoding a large batch of logs."""
        schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")
        raw_logs = [
            make_transfer_log(
                from_addr=f"0x{'a' * 38}{i:02x}",
                to_addr=f"0x{'b' * 38}{i:02x}",
                value=i * 1000,
                block_number=i,
                log_index=i,
            )
            for i in range(1000)
        ]

        decoded = decode_logs(schema, raw_logs)

        assert len(decoded) == 1000
        assert decoded[0]["block_number"] == 0
        assert decoded[999]["block_number"] == 999
        assert decoded[999]["params"]["value"] == "999000"


class TestDecodeLogsErrors:
    """Tests for error handling in decode_logs."""

    def test_missing_topics_key(self):
        """Test that missing 'topics' key raises KeyError."""
        schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")
        raw_logs = [{"data": "0x1234"}]

        with pytest.raises(KeyError, match="topics"):
            decode_logs(schema, raw_logs)

    def test_missing_data_key(self):
        """Test that missing 'data' key raises KeyError."""
        schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")
        raw_logs = [{"topics": [TRANSFER_SELECTOR]}]

        with pytest.raises(KeyError, match="data"):
            decode_logs(schema, raw_logs)

    def test_invalid_hex_data(self):
        """Test that invalid hex in data raises ValueError."""
        schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")
        raw_logs = [
            {
                "topics": [TRANSFER_SELECTOR],
                "data": "not_valid_hex",
            }
        ]

        with pytest.raises(ValueError, match="Invalid hex"):
            decode_logs(schema, raw_logs)

    def test_topics_not_list(self):
        """Test that topics not being a list raises TypeError."""
        schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")
        raw_logs = [{"topics": "not_a_list", "data": "0x"}]

        with pytest.raises(TypeError, match="list"):
            decode_logs(schema, raw_logs)

    def test_raw_logs_not_list_of_dicts(self):
        """Test that raw_logs containing non-dicts raises TypeError."""
        schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")
        raw_logs = ["not_a_dict"]

        with pytest.raises(TypeError, match="dicts"):
            decode_logs(schema, raw_logs)
