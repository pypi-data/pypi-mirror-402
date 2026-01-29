# PandaDoc CLI

CLI for managing PandaDoc documents with Copper CRM integration.

## Installation

```bash
uv sync
```

## Usage

```bash
# First-time setup
pandadoc config init

# Configure field mappings
pandadoc copper fields
pandadoc copper mapping set "Client Name=opportunity.name"

# Create doc from Copper opportunity
pandadoc copper pull 12345678 --template "Sales Proposal"

# Send for signature
pandadoc doc send <doc-id> --subject "Your proposal"

# Sync status back to Copper
pandadoc copper sync <doc-id>
```

## Commands

- `pandadoc doc` - Document CRUD and lifecycle
- `pandadoc contact` - Contact management
- `pandadoc copper` - Copper CRM integration
- `pandadoc config` - Configuration management
