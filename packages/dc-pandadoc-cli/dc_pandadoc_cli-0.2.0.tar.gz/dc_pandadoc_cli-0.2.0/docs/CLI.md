# PandaDoc CLI Specification

## Overview

| Property         | Value                                                 |
| ---------------- | ----------------------------------------------------- |
| **Name**         | `pandadoc`                                            |
| **One-liner**    | Manage PandaDoc documents with Copper CRM integration |
| **Primary User** | Both humans and scripts                               |
| **Version**      | 0.1.0                                                 |

## USAGE

```
pandadoc [global-flags] <command> [subcommand] [args]
```

## Command Tree

```
pandadoc
├── doc                      # Document management
│   ├── list                 # List documents
│   ├── get <id>             # Get document details
│   ├── create               # Create from template
│   ├── duplicate <id>       # Duplicate existing document
│   ├── update <id>          # Update document fields
│   ├── delete <id>          # Delete document
│   ├── send <id>            # Send for signature
│   ├── remind <id>          # Send reminder
│   ├── void <id>            # Void sent document
│   ├── download <id>        # Download document file
│   ├── link <id>            # Get shareable link
│   └── status <id>          # Get document status
├── contact                  # Contact management
│   ├── list                 # List contacts
│   ├── get <id>             # Get contact details
│   ├── create               # Create contact
│   ├── update <id>          # Update contact
│   └── delete <id>          # Delete contact
├── copper                   # Copper CRM integration
│   ├── pull <opp-id>        # Create doc from opportunity
│   ├── sync <doc-id>        # Push status to Copper
│   ├── attach <doc> <opp>   # Link document to opportunity
│   ├── detach <doc-id>      # Unlink document
│   ├── fields               # List available Copper fields
│   └── mapping              # Field mapping management
│       ├── show             # Show current mappings
│       ├── set <mapping>    # Set a mapping
│       └── unset <field>    # Remove a mapping
└── config                   # Configuration management
    ├── init                 # Interactive setup
    ├── show                 # Display configuration
    ├── set <key> <value>    # Set config value
    └── unset <key>          # Remove config value
```

---

## Global Flags

| Flag         | Short | Type | Default | Description                      |
| ------------ | ----- | ---- | ------- | -------------------------------- |
| `--help`     | `-h`  | bool | false   | Show help and exit               |
| `--version`  |       | bool | false   | Show version and exit            |
| `--quiet`    | `-q`  | bool | false   | Suppress non-error output        |
| `--verbose`  | `-v`  | bool | false   | Enable debug logging (to stderr) |
| `--json`     |       | bool | false   | Output as JSON                   |
| `--plain`    |       | bool | false   | Output as tab-separated values   |
| `--no-input` |       | bool | false   | Disable interactive prompts      |
| `--no-color` |       | bool | false   | Disable colored output           |

---

## I/O Contract

### stdout

- Primary data output (document lists, details, IDs, links)
- JSON output when `--json` is set
- Plain/TSV output when `--plain` is set
- Success messages (unless `--quiet`)

### stderr

- Error messages (always, even with `--quiet`)
- Warning messages
- Debug/verbose logging (when `--verbose`)

### TTY Detection

- Rich tables and colors only when stdout is a TTY
- Confirmation prompts only when stdin is a TTY
- Respects `NO_COLOR` environment variable
- Respects `TERM=dumb`
- `--no-input` disables prompts; commands requiring confirmation exit with code 2 unless `--force` is provided

---

## Exit Codes

| Code | Meaning         | When                                                         |
| ---- | --------------- | ------------------------------------------------------------ |
| `0`  | Success         | Command completed successfully                               |
| `1`  | Generic failure | API error, network failure, unexpected error                 |
| `2`  | Invalid usage   | Missing required argument, invalid format, parse error       |
| `4`  | Not found       | Document, contact, or opportunity doesn't exist              |
| `5`  | Conflict        | Resource in wrong state for operation (e.g., send non-draft) |
| `10` | Copper error    | Copper CRM API failure                                       |

---

## Environment Variables

| Variable            | Required              | Description                        |
| ------------------- | --------------------- | ---------------------------------- |
| `PANDADOC_API_KEY`  | For doc operations    | PandaDoc API key                   |
| `COPPER_API_KEY`    | For Copper operations | Copper CRM API key                 |
| `COPPER_USER_EMAIL` | For Copper operations | Copper user email                  |
| `NO_COLOR`          | No                    | Disable colored output (any value) |

---

## Configuration

### Precedence (highest wins)

1. Command-line flags
2. Environment variables
3. Project config (`.pandadoc.toml` in current directory)
4. User config (`~/.config/pandadoc/config.toml` or `~/.pandadoc.toml`)
5. System config (`/etc/pandadoc/config.toml`)

### Config File Format (TOML)

```toml
[pandadoc]
api_key = "your-key"

[copper]
api_key = "your-key"
user_email = "user@example.com"

[mapping]
"Client Name" = "opportunity.name"
"Company" = "opportunity.company_name"
"Contact Email" = "primary_contact.email"
```

---

## Installation

```bash
cd pandadoc-cli
uv sync
```

Or install globally:

```bash
uv build
pip install dist/pandadoc_cli-*.whl
```

### Shell Completion

```bash
# Bash
pandadoc --install-completion bash

# Zsh
pandadoc --install-completion zsh

# Fish
pandadoc --install-completion fish
```

---

## Command Reference

### `pandadoc config`

Manage configuration.

#### `pandadoc config init [--force]`

Interactive configuration setup. Prompts for PandaDoc API key and optionally Copper CRM credentials.

| Flag      | Short | Description               |
| --------- | ----- | ------------------------- |
| `--force` | `-f`  | Overwrite existing config |

```bash
pandadoc config init
pandadoc config init --force
```

Non-interactive setup:

```bash
pandadoc config set pandadoc.api_key "your-key"
pandadoc config set copper.api_key "your-key"
pandadoc config set copper.user_email "user@example.com"
```

#### `pandadoc config show`

Display current configuration (API keys masked).

```bash
pandadoc config show
pandadoc config show --json
```

#### `pandadoc config set <key> <value>`

Set a configuration value.

Valid keys: `pandadoc.api_key`, `copper.api_key`, `copper.user_email`, `mapping.<field>`

```bash
pandadoc config set pandadoc.api_key "your-key"
pandadoc config set copper.user_email "you@company.com"
pandadoc config set mapping."Client Name" "opportunity.name"
```

#### `pandadoc config unset <key>`

Remove a configuration value.

```bash
pandadoc config unset mapping."Client Name"
```

---

### `pandadoc doc`

Manage documents.

#### `pandadoc doc list [--status STATUS] [--template ID]`

List documents with optional filtering.

| Flag         | Short | Type   | Description                                                       |
| ------------ | ----- | ------ | ----------------------------------------------------------------- |
| `--status`   | `-s`  | string | Filter: draft, sent, viewed, completed, voided, declined, expired |
| `--template` | `-t`  | string | Filter by template ID                                             |

```bash
pandadoc doc list
pandadoc doc list --status draft
pandadoc doc list --status completed --json
pandadoc doc list --template abc123
```

#### `pandadoc doc get <id>`

Get document details.

```bash
pandadoc doc get abc123
pandadoc doc get abc123 --json
```

#### `pandadoc doc create --template ID [options]`

Create a document from a template.

| Flag          | Short | Type     | Description                       |
| ------------- | ----- | -------- | --------------------------------- |
| `--template`  | `-t`  | string   | **Required.** Template ID         |
| `--name`      | `-n`  | string   | Document name                     |
| `--recipient` | `-r`  | string[] | Recipient email (repeatable)      |
| `--field`     | `-f`  | string[] | Field as `key=value` (repeatable) |
| `--dry-run`   |       | bool     | Preview without creating          |

```bash
pandadoc doc create --template abc123
pandadoc doc create --template abc123 --name "Q1 Proposal"
pandadoc doc create --template abc123 --recipient buyer@acme.com
pandadoc doc create --template abc123 --field "Discount=15%"
pandadoc doc create --template abc123 --dry-run
```

#### `pandadoc doc duplicate <id> [--name NAME]`

Duplicate an existing document.

| Flag     | Short | Type   | Description       |
| -------- | ----- | ------ | ----------------- |
| `--name` | `-n`  | string | New document name |

```bash
pandadoc doc duplicate abc123
pandadoc doc duplicate abc123 --name "Copy of Proposal"
```

#### `pandadoc doc update <id> --field KEY=VALUE [...]`

Update document fields (draft documents only).

| Flag      | Short | Type     | Description                                     |
| --------- | ----- | -------- | ----------------------------------------------- |
| `--field` | `-f`  | string[] | **Required.** Field as `key=value` (repeatable) |

```bash
pandadoc doc update abc123 --field "Discount=20%"
pandadoc doc update abc123 --field "Term=12 months" --field "Price=5000"
```

#### `pandadoc doc delete <id> [--force]`

Delete a document. **Destructive operation.**

| Flag      | Short | Type | Description              |
| --------- | ----- | ---- | ------------------------ |
| `--force` | `-f`  | bool | Skip confirmation prompt |

```bash
pandadoc doc delete abc123
pandadoc doc delete abc123 --force
```

#### `pandadoc doc send <id> [options]`

Send document for signature.

| Flag        | Short | Type   | Description                     |
| ----------- | ----- | ------ | ------------------------------- |
| `--subject` | `-s`  | string | Email subject                   |
| `--message` | `-m`  | string | Email message                   |
| `--silent`  |       | bool   | Send without email notification |
| `--dry-run` |       | bool   | Preview without sending         |

```bash
pandadoc doc send abc123
pandadoc doc send abc123 --subject "Your proposal"
pandadoc doc send abc123 --message "Please review and sign"
pandadoc doc send abc123 --silent
pandadoc doc send abc123 --dry-run
```

#### `pandadoc doc remind <id> [--message MSG]`

Send a reminder for a sent document.

| Flag        | Short | Type   | Description      |
| ----------- | ----- | ------ | ---------------- |
| `--message` | `-m`  | string | Reminder message |

```bash
pandadoc doc remind abc123
pandadoc doc remind abc123 --message "Friendly reminder"
```

#### `pandadoc doc void <id> [options]`

Void a sent document. **Destructive operation (irreversible).**

| Flag        | Short | Type   | Description              |
| ----------- | ----- | ------ | ------------------------ |
| `--reason`  | `-r`  | string | Reason for voiding       |
| `--force`   | `-f`  | bool   | Skip confirmation prompt |
| `--dry-run` |       | bool   | Preview without voiding  |

```bash
pandadoc doc void abc123
pandadoc doc void abc123 --reason "Deal cancelled"
pandadoc doc void abc123 --force
pandadoc doc void abc123 --dry-run
```

#### `pandadoc doc download <id> [options]`

Download a document.

| Flag       | Short | Type   | Default    | Description           |
| ---------- | ----- | ------ | ---------- | --------------------- |
| `--output` | `-o`  | path   | `<id>.pdf` | Output file path      |
| `--format` | `-f`  | string | `pdf`      | Format: `pdf`, `docx` |

```bash
pandadoc doc download abc123
pandadoc doc download abc123 --output ./proposal.pdf
pandadoc doc download abc123 --format docx
```

#### `pandadoc doc link <id>`

Get a shareable link for a document. Outputs URL to stdout (pipe-friendly).

```bash
pandadoc doc link abc123
```

#### `pandadoc doc status <id>`

Get document status. Outputs status string to stdout.

```bash
pandadoc doc status abc123
pandadoc doc status abc123 --json
```

---

### `pandadoc contact`

Manage contacts.

#### `pandadoc contact list [--email EMAIL]`

List contacts with optional filtering.

| Flag      | Short | Type   | Description     |
| --------- | ----- | ------ | --------------- |
| `--email` | `-e`  | string | Filter by email |

```bash
pandadoc contact list
pandadoc contact list --email buyer@acme.com
pandadoc contact list --json
```

#### `pandadoc contact get <id>`

Get contact details.

```bash
pandadoc contact get abc123
```

#### `pandadoc contact create --email EMAIL [options]`

Create a contact.

| Flag        | Short | Type   | Description                      |
| ----------- | ----- | ------ | -------------------------------- |
| `--email`   | `-e`  | string | **Required.** Email address      |
| `--name`    | `-n`  | string | Full name (parsed as first/last) |
| `--company` | `-c`  | string | Company name                     |

```bash
pandadoc contact create --email buyer@acme.com
pandadoc contact create --email buyer@acme.com --name "John Doe"
pandadoc contact create --email buyer@acme.com --company "Acme Corp"
```

#### `pandadoc contact update <id> [options]`

Update a contact.

| Flag        | Short | Type   | Description       |
| ----------- | ----- | ------ | ----------------- |
| `--email`   | `-e`  | string | New email address |
| `--name`    | `-n`  | string | New full name     |
| `--company` | `-c`  | string | New company name  |

```bash
pandadoc contact update abc123 --email newemail@acme.com
pandadoc contact update abc123 --name "Jane Doe"
```

#### `pandadoc contact delete <id> [--force]`

Delete a contact. **Destructive operation.**

| Flag      | Short | Type | Description              |
| --------- | ----- | ---- | ------------------------ |
| `--force` | `-f`  | bool | Skip confirmation prompt |

```bash
pandadoc contact delete abc123
pandadoc contact delete abc123 --force
```

---

### `pandadoc copper`

Copper CRM integration.

> Links created via `pull` or `attach` are persisted in config under internal `_link_<doc-id>` keys so `sync` works across CLI runs.

#### `pandadoc copper pull <opp-id> --template ID [options]`

Create a PandaDoc document from Copper opportunity data.

| Flag         | Short | Type   | Description                               |
| ------------ | ----- | ------ | ----------------------------------------- |
| `--template` | `-t`  | string | **Required.** Template ID                 |
| `--name`     | `-n`  | string | Document name (default: from opportunity) |
| `--dry-run`  |       | bool   | Preview without creating                  |

**Behavior:**

- Pulls opportunity data from Copper
- Applies field mapping to populate document fields
- Gets recipient email from primary contact
- Auto-attaches document to opportunity

```bash
pandadoc copper pull 12345678 --template abc123
pandadoc copper pull 12345678 --template abc123 --name "Custom Name"
pandadoc copper pull 12345678 --template abc123 --dry-run
```

#### `pandadoc copper sync <doc-id> [--dry-run]`

Push document status to linked Copper opportunity.

| Flag        | Short | Type | Description             |
| ----------- | ----- | ---- | ----------------------- |
| `--dry-run` |       | bool | Preview without syncing |

**Behavior:**

- Updates opportunity custom field with document status
- Creates activity log entry in Copper

```bash
pandadoc copper sync abc123
pandadoc copper sync abc123 --dry-run
```

#### `pandadoc copper attach <doc-id> <opp-id>`

Link a document to a Copper opportunity.

```bash
pandadoc copper attach abc123 12345678
```

#### `pandadoc copper detach <doc-id>`

Remove link between document and Copper opportunity.

```bash
pandadoc copper detach abc123
```

#### `pandadoc copper fields`

List available Copper field paths for mapping.

```bash
pandadoc copper fields
```

Example output:

```
company.email_domain
company.name
opportunity.close_date
opportunity.monetary_value
opportunity.name
primary_contact.email
primary_contact.name
```

#### `pandadoc copper mapping show`

Show current field mappings.

```bash
pandadoc copper mapping show
```

#### `pandadoc copper mapping set <mapping>`

Set a field mapping. Format: `"PandaDoc Field=copper.path"`

```bash
pandadoc copper mapping set "Client Name=opportunity.name"
pandadoc copper mapping set "Company=opportunity.company_name"
pandadoc copper mapping set "Contact Email=primary_contact.email"
```

#### `pandadoc copper mapping unset <field>`

Remove a field mapping.

```bash
pandadoc copper mapping unset "Client Name"
```

---

## Safety Rules

### Destructive Operations

Commands that modify or delete data require confirmation:

- `doc delete` - Deletes document
- `doc void` - Voids sent document (irreversible)
- `contact delete` - Deletes contact

These commands:

1. Prompt for confirmation interactively (when stdin is TTY)
2. Require `--force` flag for non-interactive use
3. Support `--dry-run` for preview (where applicable)

### API Key Security

- API keys are never logged or printed in full
- `config show` masks keys (`xxxx...yyyy`)
- Prefer environment variables over config files for CI/CD
- Never pass secrets via command-line flags

### Rate Limiting

Built-in delays between API requests to respect rate limits:

- PandaDoc: 0.6s between requests
- Copper: 0.2s between requests

---

## Examples

### First-Time Setup

```bash
# Interactive setup
pandadoc config init

# Or set via environment
export PANDADOC_API_KEY="your-key"
export COPPER_API_KEY="your-copper-key"
export COPPER_USER_EMAIL="you@company.com"
```

### Configure Field Mappings

```bash
# See available Copper fields
pandadoc copper fields

# Set up mappings
pandadoc copper mapping set "Client Name=opportunity.name"
pandadoc copper mapping set "Company=opportunity.company_name"
pandadoc copper mapping set "Contact Email=primary_contact.email"
pandadoc copper mapping set "Deal Value=opportunity.monetary_value"

# Verify mappings
pandadoc copper mapping show
```

### Main Workflow (Copper → PandaDoc → Copper)

```bash
# Create document from Copper opportunity
pandadoc copper pull 12345678 --template "Sales Proposal"
# → Created document: abc123
# → Linked to opportunity: 12345678

# Send for signature
pandadoc doc send abc123 --subject "Your proposal from Acme"

# Check status
pandadoc doc status abc123

# Sync status back to Copper
pandadoc copper sync abc123

# Send reminder if needed
pandadoc doc remind abc123

# Download signed copy
pandadoc doc download abc123 --output ./signed-proposal.pdf
```

### Scripting Examples

```bash
# List all draft documents as JSON
pandadoc doc list --status draft --json | jq '.[].id'

# Get document ID for piping
DOC_ID=$(pandadoc doc create --template abc123 --json | jq -r '.id')

# Check status in scripts
STATUS=$(pandadoc doc status abc123)
if [ "$STATUS" = "completed" ]; then
  pandadoc doc download abc123
fi

# Batch sync all completed docs
pandadoc doc list --status completed --plain | cut -f1 | \
  xargs -I{} pandadoc copper sync {}

# Plain output for parsing
pandadoc doc list --plain | cut -f1  # Get IDs only
```

### Pure PandaDoc (No Copper)

```bash
# Create document directly
pandadoc doc create --template "NDA" \
  --name "NDA - Acme Corp" \
  --recipient legal@acme.com \
  --field "Company=Acme Corp"

# Send it
pandadoc doc send <doc-id>
```

### Silent/Batch Operations

```bash
# Delete without confirmation
pandadoc doc delete abc123 --force

# Quiet mode (only errors)
pandadoc --quiet doc send abc123

# Void without prompts in CI
pandadoc doc void abc123 --force --reason "Automated cleanup"
```

---

## Error Messages

Errors include what went wrong and suggested fixes:

```
✗ Document not found: abc123
  Use 'pandadoc doc list' to see available documents.

✗ Cannot send: document is not in draft status
  Current status: completed

✗ Missing required option: --template
  Usage: pandadoc doc create --template ID [options]

✗ Invalid format. Use: 'PandaDoc Field=copper.path'
```

---

## Changelog

### 0.1.0

- Initial release
- Document management (list, get, create, duplicate, update, delete, send, remind, void, download, link, status)
- Contact CRUD operations
- Copper CRM integration with field mapping
- Configuration management with TOML files
- JSON/plain output modes for scripting
- Shell completion support
