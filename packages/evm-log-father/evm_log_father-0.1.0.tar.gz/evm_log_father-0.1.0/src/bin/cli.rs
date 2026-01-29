// Copyright (c) 2026 Bilinear Labs
// SPDX-License-Identifier: MIT

//! CLI for evm-log-father.
//!
//! Decode EVM logs from parquet files.

use clap::{Parser, Subcommand};
use evm_log_father::{EventSchema, decode_parquet, decode_parquet_parallel};
use std::fs::File;
use std::io::{self, Write};
use std::path::PathBuf;
use std::time::Instant;

#[derive(Parser)]
#[command(name = "evm-log-father")]
#[command(author = "Bilinear Labs")]
#[command(version)]
#[command(about = "Fast EVM log decoder", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Decode logs from a parquet file
    Decode {
        /// Path to input parquet file
        #[arg(short, long)]
        parquet: PathBuf,

        /// Event signature (e.g., "Transfer(address indexed from, address indexed to, uint256 value)")
        #[arg(short, long)]
        event: String,

        /// Output file path (stdout if not specified)
        #[arg(short, long)]
        output: Option<PathBuf>,

        /// Enable parallel decoding
        #[arg(long, default_value = "false")]
        parallel: bool,

        /// Limit number of rows to decode
        #[arg(short, long)]
        limit: Option<usize>,

        /// Print timing information
        #[arg(long, default_value = "false")]
        timing: bool,
    },

    /// Show information about an event signature
    Info {
        /// Event signature
        #[arg(short, long)]
        event: String,
    },
}

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Decode {
            parquet,
            event,
            output,
            parallel,
            limit,
            timing,
        } => {
            let start = Instant::now();

            let schema = EventSchema::new(&event)?;

            let decode_start = Instant::now();
            let mut decoded = if parallel {
                decode_parquet_parallel(&parquet, &schema)?
            } else {
                decode_parquet(&parquet, &schema)?
            };
            let decode_time = decode_start.elapsed();

            if let Some(n) = limit {
                decoded.truncate(n);
            }

            let json = serde_json::to_string_pretty(&decoded)?;

            match output {
                Some(path) => {
                    let mut file = File::create(&path)?;
                    file.write_all(json.as_bytes())?;
                    eprintln!("Wrote {} logs to {}", decoded.len(), path.display());
                }
                None => {
                    io::stdout().write_all(json.as_bytes())?;
                    io::stdout().write_all(b"\n")?;
                }
            }

            if timing {
                let total_time = start.elapsed();
                eprintln!("Decoded {} logs", decoded.len());
                eprintln!("Decode time: {:.3}s", decode_time.as_secs_f64());
                eprintln!("Total time: {:.3}s", total_time.as_secs_f64());
                if !decoded.is_empty() {
                    eprintln!(
                        "Throughput: {:.0} logs/s",
                        decoded.len() as f64 / decode_time.as_secs_f64()
                    );
                }
            }
        }

        Commands::Info { event } => {
            let schema = EventSchema::new(&event)?;
            println!("Event: {}", schema.name());
            println!("Signature: {}", schema.signature());
            println!("Selector: 0x{}", hex::encode(schema.selector().as_slice()));
            println!("Parameters:");
            for (i, name) in schema.param_names().iter().enumerate() {
                let indexed = if i < schema.indexed_count() {
                    " (indexed)"
                } else {
                    ""
                };
                println!("  {}: {}{}", i, name, indexed);
            }
        }
    }

    Ok(())
}
