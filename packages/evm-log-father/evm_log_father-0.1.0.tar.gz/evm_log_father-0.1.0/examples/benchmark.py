#!/usr/bin/env python3
# Copyright (c) 2026 Bilinear Labs
# SPDX-License-Identifier: MIT

"""
Benchmark comparing evm-log-father vs web3.py for EVM log decoding.

Usage:
    python benchmark.py <parquet_file> [event_signature]

Example:
    python benchmark.py transfers.parquet "Transfer(address indexed from, address indexed to, uint256 value)"
"""

import sys
import time
from pathlib import Path

# Check for required dependencies
try:
    from evm_log_father import EventSchema, decode_parquet
except ImportError:
    print("Error: evm-log-father not installed. Run: maturin develop")
    sys.exit(1)

try:
    import pyarrow.parquet as pq
except ImportError:
    print("Warning: pyarrow not installed. Skipping raw data loading for web3 comparison.")
    pq = None

try:
    from web3 import Web3
    from eth_abi import decode as abi_decode
except ImportError:
    print("Warning: web3.py not installed. Skipping web3 comparison.")
    Web3 = None


def benchmark_evm_log_father(parquet_path: str, event_sig: str, parallel: bool = False):
    """Benchmark evm-log-father decoding."""
    schema = EventSchema(event_sig)

    start = time.perf_counter()
    logs = decode_parquet(parquet_path, schema, parallel=parallel)
    elapsed = time.perf_counter() - start

    return logs, elapsed


def benchmark_web3(parquet_path: str, event_sig: str):
    """Benchmark web3.py decoding (for comparison)."""
    if Web3 is None or pq is None:
        return None, None

    # Parse event signature to get types
    # Example: "Transfer(address indexed from, address indexed to, uint256 value)"
    name_start = event_sig.find("(")
    name_end = event_sig.find(")")
    if name_start == -1 or name_end == -1:
        return None, None

    params_str = event_sig[name_start + 1:name_end]
    params = [p.strip() for p in params_str.split(",") if p.strip()]

    indexed_types = []
    data_types = []

    for param in params:
        parts = param.split()
        if len(parts) >= 2:
            param_type = parts[0]
            is_indexed = "indexed" in parts

            if is_indexed:
                indexed_types.append(param_type)
            else:
                data_types.append(param_type)

    # Read parquet file
    table = pq.read_table(parquet_path)
    df = table.to_pandas()

    start = time.perf_counter()
    decoded_count = 0

    for _, row in df.iterrows():
        try:
            # Decode indexed topics (skip topic0 which is event selector)
            topics = []
            for i, topic_col in enumerate(["topic1", "topic2", "topic3"]):
                if topic_col in row and row[topic_col]:
                    topic_hex = row[topic_col]
                    if topic_hex.startswith("0x"):
                        topic_hex = topic_hex[2:]
                    topics.append(bytes.fromhex(topic_hex))

            # Decode data
            if "data" in row and row["data"]:
                data = row["data"]
                if isinstance(data, str):
                    if data.startswith("0x"):
                        data = data[2:]
                    data = bytes.fromhex(data)

                if data_types and len(data) > 0:
                    abi_decode(data_types, data)

            decoded_count += 1
        except Exception:
            pass

    elapsed = time.perf_counter() - start
    return decoded_count, elapsed


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    parquet_path = sys.argv[1]
    event_sig = sys.argv[2] if len(sys.argv) > 2 else "Transfer(address indexed from, address indexed to, uint256 value)"

    if not Path(parquet_path).exists():
        print(f"Error: File not found: {parquet_path}")
        sys.exit(1)

    print(f"Parquet file: {parquet_path}")
    print(f"Event signature: {event_sig}")
    print("-" * 60)

    # evm-log-father (sequential)
    print("\n[evm-log-father] Sequential decoding...")
    logs_seq, time_seq = benchmark_evm_log_father(parquet_path, event_sig, parallel=False)
    print(f"  Decoded: {len(logs_seq)} logs")
    print(f"  Time: {time_seq:.3f}s")
    if logs_seq:
        print(f"  Throughput: {len(logs_seq) / time_seq:.0f} logs/s")

    # evm-log-father (parallel)
    print("\n[evm-log-father] Parallel decoding...")
    logs_par, time_par = benchmark_evm_log_father(parquet_path, event_sig, parallel=True)
    print(f"  Decoded: {len(logs_par)} logs")
    print(f"  Time: {time_par:.3f}s")
    if logs_par:
        print(f"  Throughput: {len(logs_par) / time_par:.0f} logs/s")

    if time_seq > 0:
        print(f"  Parallel speedup: {time_seq / time_par:.1f}x")

    # web3.py comparison
    if Web3 is not None and pq is not None:
        print("\n[web3.py] Sequential decoding...")
        count_web3, time_web3 = benchmark_web3(parquet_path, event_sig)
        if count_web3 is not None:
            print(f"  Decoded: {count_web3} logs")
            print(f"  Time: {time_web3:.3f}s")
            if count_web3:
                print(f"  Throughput: {count_web3 / time_web3:.0f} logs/s")

            if time_web3 > 0 and time_par > 0:
                print(f"\n[Comparison]")
                print(f"  evm-log-father vs web3.py: {time_web3 / time_par:.1f}x faster")

    # Show sample decoded log
    if logs_seq:
        print("\n[Sample decoded log]")
        sample = logs_seq[0]
        print(f"  Block: {sample['block_number']}")
        print(f"  TX: {sample['tx_hash']}")
        print(f"  Contract: {sample['contract']}")
        print(f"  Params:")
        for name, value in sample['params'].items():
            print(f"    {name}: {value}")


if __name__ == "__main__":
    main()
