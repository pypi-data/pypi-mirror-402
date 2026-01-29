// Copyright (c) 2026 Bilinear Labs
// SPDX-License-Identifier: MIT

//! # evm-log-father
//!
//! Fast EVM log decoding library with Python bindings.
//!
//! This library provides efficient decoding of Ethereum event logs using
//! alloy's dynamic ABI decoding. It supports reading raw logs from parquet
//! files and decoding them in parallel using rayon.
//!
//! ## Example
//!
//! ```ignore
//! use evm_log_father::{EventSchema, decode_parquet};
//!
//! let schema = EventSchema::new("Transfer(address indexed from, address indexed to, uint256 value)")?;
//! let logs = decode_parquet("logs.parquet", &schema)?;
//! ```

pub mod decoder;
pub mod types;

pub use decoder::{EventSchema, decode_log};
pub use types::{DecodeError, DecodedLog, RawLog};

use arrow::array::{
    Array, AsArray, BinaryArray, Int64Array, ListArray, StringArray, UInt32Array, UInt64Array,
};
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;
use rayon::prelude::*;
use std::fs::File;
use std::path::Path;

/// Reads raw logs from a parquet file.
///
/// Expected parquet schema:
/// - `block_number`: u64
/// - `tx_hash`: string
/// - `log_index`: u32
/// - `contract` or `address`: string
/// - `topic0`, `topic1`, `topic2`, `topic3`: string (optional)
/// - `data`: binary
///
/// Alternative schema (topics as array):
/// - `topics`: list<string>
pub fn read_parquet(path: impl AsRef<Path>) -> Result<Vec<RawLog>, DecodeError> {
    let file = File::open(path.as_ref())?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file)
        .map_err(|e| DecodeError::ParquetError(e.to_string()))?;

    let reader = builder
        .build()
        .map_err(|e| DecodeError::ParquetError(e.to_string()))?;

    let mut logs = Vec::new();

    for batch_result in reader {
        let batch = batch_result.map_err(|e| DecodeError::ParquetError(e.to_string()))?;

        // block_number can be snake_case or camelCase, and can be i64 or u64
        let block_number_col = batch
            .column_by_name("block_number")
            .or_else(|| batch.column_by_name("blockNumber"))
            .ok_or_else(|| DecodeError::ParquetError("Missing block_number column".to_string()))?;
        let block_numbers_u64 = block_number_col.as_any().downcast_ref::<UInt64Array>();
        let block_numbers_i64 = block_number_col.as_any().downcast_ref::<Int64Array>();

        // tx_hash can be "tx_hash", "transaction_hash", or "transactionHash"
        let tx_hashes = batch
            .column_by_name("tx_hash")
            .or_else(|| batch.column_by_name("transaction_hash"))
            .or_else(|| batch.column_by_name("transactionHash"))
            .ok_or_else(|| {
                DecodeError::ParquetError("Missing tx_hash/transaction_hash column".to_string())
            })?
            .as_any()
            .downcast_ref::<StringArray>()
            .ok_or_else(|| DecodeError::ParquetError("tx_hash is not string".to_string()))?;

        // log_index can be u32 or u64, snake_case or camelCase
        let log_index_col = batch
            .column_by_name("log_index")
            .or_else(|| batch.column_by_name("logIndex"))
            .ok_or_else(|| DecodeError::ParquetError("Missing log_index column".to_string()))?;
        let log_indices_u32 = log_index_col.as_any().downcast_ref::<UInt32Array>();
        let log_indices_u64 = log_index_col.as_any().downcast_ref::<UInt64Array>();
        let log_indices_i64 = log_index_col.as_any().downcast_ref::<Int64Array>();

        // Contract address can be "contract" or "address"
        let contracts = batch
            .column_by_name("contract")
            .or_else(|| batch.column_by_name("address"))
            .ok_or_else(|| {
                DecodeError::ParquetError("Missing contract/address column".to_string())
            })?
            .as_any()
            .downcast_ref::<StringArray>()
            .ok_or_else(|| DecodeError::ParquetError("contract is not string".to_string()))?;

        // Try to get topics as LIST column first, then individual columns
        let topics_list = batch
            .column_by_name("topics")
            .and_then(|c| c.as_any().downcast_ref::<ListArray>());

        // Try to get individual topic columns (fallback)
        let topic0 = batch
            .column_by_name("topic0")
            .and_then(|c| c.as_any().downcast_ref::<StringArray>());
        let topic1 = batch
            .column_by_name("topic1")
            .and_then(|c| c.as_any().downcast_ref::<StringArray>());
        let topic2 = batch
            .column_by_name("topic2")
            .and_then(|c| c.as_any().downcast_ref::<StringArray>());
        let topic3 = batch
            .column_by_name("topic3")
            .and_then(|c| c.as_any().downcast_ref::<StringArray>());

        // data can be binary or string (hex)
        let data_col = batch
            .column_by_name("data")
            .ok_or_else(|| DecodeError::ParquetError("Missing data column".to_string()))?;
        let data_binary = data_col.as_any().downcast_ref::<BinaryArray>();
        let data_string = data_col.as_any().downcast_ref::<StringArray>();

        for i in 0..batch.num_rows() {
            let mut topics = Vec::new();

            // Try LIST format first
            if let Some(list) = topics_list {
                if !list.is_null(i) {
                    let arr = list.value(i);
                    let str_arr: &StringArray = arr.as_string();
                    for j in 0..str_arr.len() {
                        if !str_arr.is_null(j) {
                            topics.push(str_arr.value(j).to_string());
                        }
                    }
                }
            } else {
                // Fallback to individual columns
                if let Some(t0) = topic0
                    && !t0.is_null(i)
                {
                    topics.push(t0.value(i).to_string());
                }
                if let Some(t1) = topic1
                    && !t1.is_null(i)
                {
                    topics.push(t1.value(i).to_string());
                }
                if let Some(t2) = topic2
                    && !t2.is_null(i)
                {
                    topics.push(t2.value(i).to_string());
                }
                if let Some(t3) = topic3
                    && !t3.is_null(i)
                {
                    topics.push(t3.value(i).to_string());
                }
            }

            // Get block_number from u64 or i64
            let block_number = if let Some(arr) = block_numbers_u64 {
                arr.value(i)
            } else if let Some(arr) = block_numbers_i64 {
                arr.value(i) as u64
            } else {
                return Err(DecodeError::ParquetError(
                    "block_number is neither u64 nor i64".to_string(),
                ));
            };

            // Get log_index from u32, u64, or i64
            let log_index = if let Some(arr) = log_indices_u32 {
                arr.value(i)
            } else if let Some(arr) = log_indices_u64 {
                arr.value(i) as u32
            } else if let Some(arr) = log_indices_i64 {
                arr.value(i) as u32
            } else {
                return Err(DecodeError::ParquetError(
                    "log_index is not u32/u64/i64".to_string(),
                ));
            };

            // Get data from binary or hex string
            let data = if let Some(arr) = data_binary {
                arr.value(i).to_vec()
            } else if let Some(arr) = data_string {
                let hex_str = arr.value(i);
                let hex_str = hex_str.strip_prefix("0x").unwrap_or(hex_str);
                hex::decode(hex_str).unwrap_or_default()
            } else {
                return Err(DecodeError::ParquetError(
                    "data is neither binary nor string".to_string(),
                ));
            };

            logs.push(RawLog {
                block_number,
                tx_hash: tx_hashes.value(i).to_string(),
                log_index,
                contract: contracts.value(i).to_string(),
                topics,
                data,
            });
        }
    }

    Ok(logs)
}

/// Decodes all logs in a parquet file using the provided schema.
///
/// Returns a vector of successfully decoded logs. Failed decodings are skipped.
pub fn decode_parquet(
    path: impl AsRef<Path>,
    schema: &EventSchema,
) -> Result<Vec<DecodedLog>, DecodeError> {
    let raw_logs = read_parquet(path)?;
    let mut decoded = Vec::with_capacity(raw_logs.len());

    for raw in &raw_logs {
        if let Ok(log) = decode_log(schema, raw) {
            decoded.push(log);
        }
    }

    Ok(decoded)
}

/// Decodes all logs in a parquet file in parallel using rayon.
///
/// Returns a vector of successfully decoded logs. Failed decodings are skipped.
pub fn decode_parquet_parallel(
    path: impl AsRef<Path>,
    schema: &EventSchema,
) -> Result<Vec<DecodedLog>, DecodeError> {
    let raw_logs = read_parquet(path)?;

    let decoded: Vec<DecodedLog> = raw_logs
        .par_iter()
        .filter_map(|raw| decode_log(schema, raw).ok())
        .collect();

    Ok(decoded)
}

/// Decodes a batch of raw logs using the provided schema.
///
/// Returns a vector of successfully decoded logs. Failed decodings are skipped.
pub fn decode_logs(schema: &EventSchema, raw_logs: &[RawLog]) -> Vec<DecodedLog> {
    raw_logs
        .iter()
        .filter_map(|raw| decode_log(schema, raw).ok())
        .collect()
}

/// Decodes a batch of raw logs in parallel using rayon.
///
/// Returns a vector of successfully decoded logs. Failed decodings are skipped.
pub fn decode_logs_parallel(schema: &EventSchema, raw_logs: &[RawLog]) -> Vec<DecodedLog> {
    raw_logs
        .par_iter()
        .filter_map(|raw| decode_log(schema, raw).ok())
        .collect()
}

// Python bindings
#[cfg(feature = "python")]
mod python {
    use super::*;
    use pyo3::prelude::*;
    use pyo3::types::{PyBytes, PyDict, PyList};

    #[pyclass(name = "EventSchema")]
    struct PyEventSchema {
        inner: EventSchema,
    }

    #[pymethods]
    impl PyEventSchema {
        #[new]
        fn new(signature: &str) -> PyResult<Self> {
            let inner = EventSchema::new(signature)
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
            Ok(Self { inner })
        }

        #[getter]
        fn name(&self) -> &str {
            self.inner.name()
        }

        #[getter]
        fn signature(&self) -> &str {
            self.inner.signature()
        }

        #[getter]
        fn selector(&self) -> String {
            format!("0x{}", hex::encode(self.inner.selector().as_slice()))
        }

        #[getter]
        fn param_names(&self) -> Vec<String> {
            self.inner
                .param_names()
                .into_iter()
                .map(String::from)
                .collect()
        }
    }

    /// Decode a single log from topics and data.
    #[pyfunction]
    #[allow(clippy::too_many_arguments)]
    fn decode_log_py(
        py: Python<'_>,
        schema: &PyEventSchema,
        topics: Vec<String>,
        data: &Bound<'_, PyBytes>,
        block_number: Option<u64>,
        tx_hash: Option<String>,
        log_index: Option<u32>,
        contract: Option<String>,
    ) -> PyResult<Py<PyDict>> {
        let raw = RawLog {
            block_number: block_number.unwrap_or(0),
            tx_hash: tx_hash.unwrap_or_default(),
            log_index: log_index.unwrap_or(0),
            contract: contract.unwrap_or_default(),
            topics,
            data: data.as_bytes().to_vec(),
        };

        let decoded = decode_log(&schema.inner, &raw)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        decoded_to_dict(py, &decoded)
    }

    /// Decode logs from a parquet file.
    #[pyfunction]
    #[pyo3(signature = (path, schema, parallel=false, limit=None))]
    fn decode_parquet_py(
        py: Python<'_>,
        path: &str,
        schema: &PyEventSchema,
        parallel: bool,
        limit: Option<usize>,
    ) -> PyResult<Py<PyList>> {
        let decoded = if parallel {
            decode_parquet_parallel(path, &schema.inner)
        } else {
            decode_parquet(path, &schema.inner)
        }
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

        let result = PyList::empty(py);
        let iter = if let Some(n) = limit {
            decoded.iter().take(n).collect::<Vec<_>>()
        } else {
            decoded.iter().collect::<Vec<_>>()
        };

        for log in iter {
            let dict = decoded_to_dict(py, log)?;
            result.append(dict)?;
        }

        Ok(result.into())
    }

    fn decoded_to_dict(py: Python<'_>, log: &DecodedLog) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("block_number", log.block_number)?;
        dict.set_item("tx_hash", &log.tx_hash)?;
        dict.set_item("log_index", log.log_index)?;
        dict.set_item("contract", &log.contract)?;

        let params = PyDict::new(py);
        for (name, value) in &log.params {
            params.set_item(name, value)?;
        }
        dict.set_item("params", params)?;

        Ok(dict.into())
    }

    #[pymodule]
    fn evm_log_father(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_class::<PyEventSchema>()?;
        m.add_function(wrap_pyfunction!(decode_log_py, m)?)?;
        m.add_function(wrap_pyfunction!(decode_parquet_py, m)?)?;
        Ok(())
    }
}
