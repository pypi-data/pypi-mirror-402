// Copyright (c) 2026 Bilinear Labs
// SPDX-License-Identifier: MIT

//! Core types for EVM log decoding.

use serde::{Deserialize, Serialize};

/// A decoded EVM log with all parameters extracted.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecodedLog {
    /// Block number where the log was emitted
    pub block_number: u64,
    /// Transaction hash
    pub tx_hash: String,
    /// Log index within the transaction
    pub log_index: u32,
    /// Contract address that emitted the event
    pub contract: String,
    /// Decoded parameters as (name, value) pairs
    pub params: Vec<(String, String)>,
}

impl DecodedLog {
    /// Creates a new DecodedLog.
    pub fn new(
        block_number: u64,
        tx_hash: String,
        log_index: u32,
        contract: String,
        params: Vec<(String, String)>,
    ) -> Self {
        Self {
            block_number,
            tx_hash,
            log_index,
            contract,
            params,
        }
    }

    /// Returns the parameters as a map for easier access.
    pub fn params_map(&self) -> std::collections::HashMap<&str, &str> {
        self.params
            .iter()
            .map(|(k, v)| (k.as_str(), v.as_str()))
            .collect()
    }
}

/// Raw log data from a parquet file or other source.
#[derive(Debug, Clone)]
pub struct RawLog {
    /// Block number
    pub block_number: u64,
    /// Transaction hash (hex string with 0x prefix)
    pub tx_hash: String,
    /// Log index
    pub log_index: u32,
    /// Contract address (hex string with 0x prefix)
    pub contract: String,
    /// Topics as hex strings with 0x prefix (topic[0] is event selector)
    pub topics: Vec<String>,
    /// Data as raw bytes
    pub data: Vec<u8>,
}

/// Errors that can occur during decoding.
#[derive(Debug, thiserror::Error)]
pub enum DecodeError {
    #[error("Invalid event signature: {0}")]
    InvalidSignature(String),
    #[error("Failed to decode log: {0}")]
    DecodeFailed(String),
    #[error("Topic count mismatch: expected {expected}, got {actual}")]
    TopicMismatch { expected: usize, actual: usize },
    #[error("Invalid hex string: {0}")]
    InvalidHex(String),
    #[error("Parquet error: {0}")]
    ParquetError(String),
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
}

impl From<hex::FromHexError> for DecodeError {
    fn from(e: hex::FromHexError) -> Self {
        DecodeError::InvalidHex(e.to_string())
    }
}
