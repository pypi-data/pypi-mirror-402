# genome-cli

A CLI tool to analyze dbt manifest.json files.

## Installation

This package is distributed as a Rust binary. 

### Quick Install (macOS/Linux)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && source ~/.cargo/env && cargo install genome-cli
```

### Step by Step

1. Install Rust (if you don't have it):

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

2. Restart your terminal or run:

```bash
source ~/.cargo/env
```

3. Install genome-cli:

```bash
cargo install genome-cli
```

### Windows

1. Download and run the Rust installer: https://win.rustup.rs
2. Open a new terminal and run:

```bash
cargo install genome-cli
```

## Usage

```bash
# Analyze manifest (default: manifest.json)
genome sequence

# Specify a custom path
genome sequence --manifest path/to/manifest.json

# Output as JSON
genome sequence --json
```

## Why Rust?

Performance. The genome CLI is built in Rust for fast analysis of large dbt projects.

## License

Proprietary - All rights reserved.
