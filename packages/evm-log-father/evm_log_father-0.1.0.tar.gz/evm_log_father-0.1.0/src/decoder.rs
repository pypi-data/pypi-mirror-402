// Copyright (c) 2026 Bilinear Labs
// SPDX-License-Identifier: MIT

//! Core EVM log decoding logic.
//!
//! This module contains the functions for decoding EVM event logs using alloy's
//! dynamic ABI decoding capabilities.

use alloy::{
    dyn_abi::{DynSolValue, EventExt},
    json_abi::Event,
    primitives::B256,
};

use crate::types::{DecodeError, DecodedLog, RawLog};

/// Event schema wrapper that holds a parsed alloy Event.
#[derive(Debug, Clone)]
pub struct EventSchema {
    event: Event,
    signature: String,
}

impl EventSchema {
    /// Creates a new EventSchema from an event signature string.
    ///
    /// # Example
    /// ```
    /// use evm_log_father::EventSchema;
    /// let schema = EventSchema::new("Transfer(address indexed from, address indexed to, uint256 value)").unwrap();
    /// ```
    pub fn new(signature: &str) -> Result<Self, DecodeError> {
        // Normalize signature: add "event " prefix if not present
        let normalized = if signature.starts_with("event ") {
            signature.to_string()
        } else {
            format!("event {}", signature)
        };

        let event: Event = normalized
            .parse()
            .map_err(|e| DecodeError::InvalidSignature(format!("{:?}", e)))?;

        Ok(Self {
            event,
            signature: signature.to_string(),
        })
    }

    /// Returns the event selector (topic0).
    pub fn selector(&self) -> B256 {
        self.event.selector()
    }

    /// Returns the original signature string.
    pub fn signature(&self) -> &str {
        &self.signature
    }

    /// Returns the event name.
    pub fn name(&self) -> &str {
        &self.event.name
    }

    /// Returns the parameter names in order (indexed first, then non-indexed).
    pub fn param_names(&self) -> Vec<&str> {
        self.event.inputs.iter().map(|p| p.name.as_str()).collect()
    }

    /// Returns the number of indexed parameters (excluding topic0).
    pub fn indexed_count(&self) -> usize {
        self.event.inputs.iter().filter(|p| p.indexed).count()
    }

    /// Returns a reference to the inner alloy Event.
    pub fn inner(&self) -> &Event {
        &self.event
    }
}

/// Decodes a single raw log using the provided event schema.
pub fn decode_log(schema: &EventSchema, raw: &RawLog) -> Result<DecodedLog, DecodeError> {
    // Parse topics from hex strings to B256
    let topics: Vec<B256> = raw
        .topics
        .iter()
        .map(|t| {
            let t = t.strip_prefix("0x").unwrap_or(t);
            let bytes = hex::decode(t)?;
            if bytes.len() != 32 {
                return Err(DecodeError::InvalidHex(format!(
                    "topic has {} bytes, expected 32",
                    bytes.len()
                )));
            }
            let mut arr = [0u8; 32];
            arr.copy_from_slice(&bytes);
            Ok(B256::from(arr))
        })
        .collect::<Result<Vec<_>, DecodeError>>()?;

    // Decode using alloy
    let decoded = schema
        .event
        .decode_log_parts(topics, &raw.data)
        .map_err(|e| DecodeError::DecodeFailed(e.to_string()))?;

    // Build parameter list
    let mut params = Vec::new();
    let param_names = schema.param_names();

    // First, add indexed parameters
    let indexed_params: Vec<_> = schema
        .event
        .inputs
        .iter()
        .enumerate()
        .filter(|(_, p)| p.indexed)
        .collect();

    for (i, (orig_idx, _)) in indexed_params.iter().enumerate() {
        if i < decoded.indexed.len() {
            let name = param_names.get(*orig_idx).copied().unwrap_or("unknown");
            let value = dyn_sol_value_to_string(&decoded.indexed[i]);
            params.push((name.to_string(), value));
        }
    }

    // Then, add non-indexed (body) parameters
    let body_params: Vec<_> = schema
        .event
        .inputs
        .iter()
        .enumerate()
        .filter(|(_, p)| !p.indexed)
        .collect();

    for (i, (orig_idx, _)) in body_params.iter().enumerate() {
        if i < decoded.body.len() {
            let name = param_names.get(*orig_idx).copied().unwrap_or("unknown");
            let value = dyn_sol_value_to_string(&decoded.body[i]);
            params.push((name.to_string(), value));
        }
    }

    Ok(DecodedLog::new(
        raw.block_number,
        raw.tx_hash.clone(),
        raw.log_index,
        raw.contract.clone(),
        params,
    ))
}

/// Removes the zero-padding from a 32-byte padded address.
///
/// EVM logs store addresses in 32-byte (64 hex chars + 0x) format,
/// but we want the standard 20-byte (40 hex chars + 0x) format.
#[inline]
fn remove_address_padding(addr: &str) -> String {
    // Ensure the address starts with "0x" and it's a full address (66 characters).
    if !addr.starts_with("0x") || addr.len() != 66 {
        return addr.to_string();
    }

    // Check if the input address is aligned to 64B using 0s.
    if &addr[..26] == "0x000000000000000000000000" {
        format!("0x{}", &addr[26..])
    } else {
        addr.to_string()
    }
}

/// Converts a `DynSolValue` to a String representation.
///
/// For simple types, returns their natural string representation.
/// For complex types (arrays, tuples), flattens them into a JSON-like string format.
fn dyn_sol_value_to_string(value: &DynSolValue) -> String {
    match value {
        DynSolValue::Address(a) => remove_address_padding(&a.to_string().to_lowercase()),
        DynSolValue::Bool(b) => b.to_string(),
        DynSolValue::Int(i, _) => i.to_string(),
        DynSolValue::Uint(u, _) => u.to_string(),
        DynSolValue::String(s) => s.clone(),
        DynSolValue::FixedBytes(bytes, size) => {
            // Convert fixed bytes to hex string, taking only the relevant bytes
            format!("0x{}", hex::encode(&bytes[..(*size).min(32)]))
        }
        DynSolValue::Bytes(bytes) => {
            // Convert dynamic bytes to hex string
            format!("0x{}", hex::encode(bytes))
        }
        DynSolValue::Function(f) => {
            // Function is 24 bytes: 20 bytes address + 4 bytes selector
            format!("0x{}", hex::encode(f.as_slice()))
        }
        DynSolValue::Array(values) | DynSolValue::FixedArray(values) => {
            // Flatten array into a JSON-like string representation
            let elements: Vec<String> = values.iter().map(dyn_sol_value_to_string).collect();
            format!("[{}]", elements.join(","))
        }
        DynSolValue::Tuple(values) => {
            // Flatten tuple into a JSON-like string representation
            let elements: Vec<String> = values.iter().map(dyn_sol_value_to_string).collect();
            format!("({})", elements.join(","))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_event_schema_parsing() {
        let schema =
            EventSchema::new("Transfer(address indexed from, address indexed to, uint256 value)")
                .unwrap();
        assert_eq!(schema.name(), "Transfer");
        assert_eq!(schema.indexed_count(), 2);
        assert_eq!(schema.param_names(), vec!["from", "to", "value"]);
    }

    #[test]
    fn test_event_schema_without_event_prefix() {
        let schema =
            EventSchema::new("Transfer(address indexed from, address indexed to, uint256 value)")
                .unwrap();
        let schema2 = EventSchema::new(
            "event Transfer(address indexed from, address indexed to, uint256 value)",
        )
        .unwrap();
        assert_eq!(schema.selector(), schema2.selector());
    }

    #[test]
    fn test_remove_address_padding() {
        // Standard padded address
        let padded = "0x000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec7";
        assert_eq!(
            remove_address_padding(padded),
            "0xdac17f958d2ee523a2206206994597c13d831ec7"
        );

        // Already unpadded
        let unpadded = "0xdac17f958d2ee523a2206206994597c13d831ec7";
        assert_eq!(remove_address_padding(unpadded), unpadded);

        // Invalid length
        let short = "0x1234";
        assert_eq!(remove_address_padding(short), short);
    }

    #[test]
    fn test_decode_transfer_log() {
        let schema =
            EventSchema::new("Transfer(address indexed from, address indexed to, uint256 value)")
                .unwrap();

        let raw = RawLog {
            block_number: 12345678,
            tx_hash: "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
                .to_string(),
            log_index: 0,
            contract: "0xdac17f958d2ee523a2206206994597c13d831ec7".to_string(),
            topics: vec![
                format!("0x{}", hex::encode(schema.selector().as_slice())),
                "0x000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48".to_string(),
                "0x000000000000000000000000b0c7891c6218b36c1d19d4a2e9eb0ce3606eb990".to_string(),
            ],
            data: hex::decode("0000000000000000000000000000000000000000000000000000000005f5e100")
                .unwrap(),
        };

        let decoded = decode_log(&schema, &raw).unwrap();
        assert_eq!(decoded.block_number, 12345678);
        assert_eq!(decoded.params.len(), 3);
        assert_eq!(decoded.params[0].0, "from");
        assert_eq!(
            decoded.params[0].1,
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        );
        assert_eq!(decoded.params[1].0, "to");
        assert_eq!(decoded.params[2].0, "value");
        assert_eq!(decoded.params[2].1, "100000000");
    }
}
