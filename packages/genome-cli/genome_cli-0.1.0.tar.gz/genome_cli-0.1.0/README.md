# genome-cli

A CLI tool to analyze dbt manifest.json files.

## Installation

```bash
pip install genome-cli
```

## Usage

### Count nodes in a manifest

```bash
# Using default path (target/manifest.json)
genome sequence

# Specify a custom path
genome sequence path/to/manifest.json
```

## Development

```bash
# Install in development mode
pip install -e .

# Run the CLI
genome --help
genome sequence --help
```

## License

Proprietary - All rights reserved.
