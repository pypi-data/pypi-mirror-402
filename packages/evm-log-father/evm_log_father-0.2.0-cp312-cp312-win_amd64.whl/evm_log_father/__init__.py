# Copyright (c) 2026 adidonato
# SPDX-License-Identifier: MIT

"""
evm-log-father: Fast EVM log decoding library.

This module provides efficient decoding of Ethereum event logs using
Rust's alloy library for ABI decoding.

Example:
    >>> from evm_log_father import EventSchema, decode_parquet_py
    >>> schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")
    >>> logs = decode_parquet_py("logs.parquet", schema)
    >>> for log in logs:
    ...     print(log["params"]["from"], "->", log["params"]["to"])
"""

from .evm_log_father import (
    EventSchema,
    decode_log_py,
    decode_logs_py,
    decode_parquet_py,
)

# Re-export with nicer names
decode_log = decode_log_py
decode_logs = decode_logs_py
decode_parquet = decode_parquet_py

__all__ = [
    "EventSchema",
    "decode_log",
    "decode_logs",
    "decode_parquet",
    "decode_log_py",
    "decode_logs_py",
    "decode_parquet_py",
]
