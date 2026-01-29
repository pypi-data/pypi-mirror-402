# evm-log-father

Fast EVM log decoding library with Python bindings.

## Performance

![Benchmark Results](assets/benchmark.png)

**400-500k logs/second** with parallel decoding on large parquet files.

## Features

- Decode Ethereum event logs using alloy's dynamic ABI
- Read logs from parquet files (multiple schema formats supported)
- Parallel decoding with rayon
- Python bindings via PyO3
- CLI for quick testing

## Installation

### Python (from PyPI)

```bash
pip install evm-log-father
```

### Python (from source)

```bash
pip install maturin
maturin develop --features python
```

### Rust

```toml
[dependencies]
evm-log-father = "0.1"
```

## Usage

### Python

```python
from evm_log_father import EventSchema, decode_parquet

# Create schema from event signature
schema = EventSchema("Transfer(address indexed from, address indexed to, uint256 value)")

# Decode logs from parquet file
logs = decode_parquet("transfers.parquet", schema, parallel=True)

for log in logs:
    print(f"Block {log['block_number']}: {log['params']['from']} -> {log['params']['to']}")
```

### Rust

```rust
use evm_log_father::{EventSchema, decode_parquet_parallel};

let schema = EventSchema::new("Transfer(address indexed from, address indexed to, uint256 value)")?;
let logs = decode_parquet_parallel("transfers.parquet", &schema)?;

for log in logs {
    println!("Block {}: {:?}", log.block_number, log.params);
}
```

### CLI

```bash
# Decode logs and output JSON
evm-log-father decode \
  --parquet transfers.parquet \
  --event "Transfer(address indexed from, address indexed to, uint256 value)" \
  --output decoded.json \
  --parallel \
  --timing

# Show event info
evm-log-father info --event "Transfer(address indexed from, address indexed to, uint256 value)"
```

## Parquet Schema Support

Flexible schema support for various parquet formats:

### Column Names
Both snake_case and camelCase supported:
- `block_number` / `blockNumber`
- `transaction_hash` / `transactionHash` / `tx_hash`
- `log_index` / `logIndex`
- `contract` / `address`

### Topics Format
- Individual columns: `topic0`, `topic1`, `topic2`, `topic3`
- List column: `topics` (Spark format)

### Data Types
- `block_number`: u64 or i64
- `log_index`: u32, u64, or i64
- `data`: binary or hex string

## Benchmarking

```bash
python examples/benchmark.py transfers.parquet
```

## License

MIT
