# Barie AML Watcher MCP

A Model Context Protocol (MCP) server for performing real-time sanctions and PEP (Politically Exposed Persons) screening using AML Watcher. This package provides comprehensive KYC/AML compliance screening capabilities.

## Installation

Install via `uvx`:

```bash
uvx barie-aml-watcher-mcp
```

Or install via pip:

```bash
pip install barie-aml-watcher-mcp
```

## Usage

Run the MCP server:

```bash
barie-aml-watcher-mcp --api-key <your-aml-watcher-api-key>
```

### Required Arguments

- `--api-key`: Your AML Watcher API key

## Features

The server provides the following tool:

- **AML Watcher Search**: Perform comprehensive sanctions and PEP screening for any entity type
  - Supports screening of Persons, Companies, Organizations, Vessels, Aircraft, and Crypto Wallets
  - Searches across multiple categories: Sanctions, PEP (all levels), Adverse Media, Warnings and Regulatory Enforcement, Business, Businessperson, Fitness and Probity, Insolvency, SIE, and SIP
  - Optional filtering by entity type, countries, categories, birth/incorporation date, or unique identifiers
  - Uses fuzzy matching to identify close name variations and spelling differences

## Use Cases

- Financial institutions conducting KYC/AML checks
- Fintech platforms screening users or transactions
- Compliance teams monitoring high-risk customers or partners
- Maritime industry screening vessels
- Aviation industry screening aircraft
- Crypto exchanges screening wallet addresses

## Requirements

- Python 3.9+
- AML Watcher API key

## Development

For build and publish instructions, see [BUILD.md](BUILD.md).

## License

MIT
