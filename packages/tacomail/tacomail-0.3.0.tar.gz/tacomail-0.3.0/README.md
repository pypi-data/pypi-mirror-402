# Tacomail Python Client

An unofficial Python client library for [Tacomail](https://tacomail.de/), a disposable email service. This library provides both synchronous and asynchronous interfaces to interact with the Tacomail API.

## Features

- 🔄 Both synchronous and asynchronous clients
- 📧 Generate random email addresses
- 📥 Fetch and manage temporary inboxes
- 📎 Handle email attachments
- ⏱️ Wait for specific emails with filtering capabilities
- 🔍 Full type hints and dataclass models

## Installation

### Standard Installation
```bash
pip install tacomail
```

### Using uvx (Recommended)
```bash
# Install and run CLI without affecting system Python
uvx tacomail create
```

## CLI Commands

The tacomail CLI provides comprehensive command-line interface for Tacomail disposable email service. All commands support both sync and async modes via the `--async` flag.

### Available Commands

**Email Generation & Domains**:
- `tacomail create` - Generate random email address
- `tacomail create-with-session` - Generate email and create session in one command (RECOMMENDED)
- `tacomail new` - Short alias for 'create-with-session' (RECOMMENDED)
- `tacomail list-domains` - List all available Tacomail domains

**Session Management**:
- `tacomail create-session <email>` - Create API session for receiving emails
- `tacomail delete-session <email>` - Delete API session

**Inbox Operations**:
- `tacomail list <email>` - List recent emails in inbox
- `tacomail get <email> <id>` - Get specific email details
- `tacomail delete <email> <id>` - Delete specific email
- `tacomail clear <email>` - Delete all emails from inbox

**Email Waiting**:
- `tacomail wait <email>` - Wait for new email to arrive
  - `--timeout <seconds>` - Maximum wait time (default: 30)
  - `--interval <seconds>` - Check interval (default: 2)
  - `--filter <pattern>` - Filter by subject/sender (regex)

### Global Options

- `--output`, `-o` - Output format: `rich` (default), `plain`, or `json`
- `--async` - Use async client instead of sync
- `--verbose` - Enable verbose/debug output
- `--help` - Show help message

### Output Formats

The CLI supports three output formats via the `--output` option:

**Rich (default)**: Beautiful formatted output with colors and panels
```bash
tacomail create
# ╭────────────── ✨ Success ──────────────╮
# │ Generated Email:                       │
# │ x7k9m2@tacomail.de                     │
# ╰────────────────────────────────────────╯
```

**Plain**: Simple key=value format for shell scripting
```bash
tacomail --output plain create
# email=x7k9m2@tacomail.de

tacomail -o plain list user@tacomail.de
# id123	sender@example.com	Subject Line	2026-01-15 10:30
```

**JSON**: Machine-readable JSON output
```bash
tacomail --output json create
# {"email": "x7k9m2@tacomail.de"}

tacomail -o json list user@tacomail.de
# [{"id": "id123", "from": "sender@example.com", "subject": "Subject Line", "date": "2026-01-15 10:30"}]
```

### Help for Specific Commands

Each command has its own help:
```bash
tacomail create --help
tacomail wait --help
tacomail list --help
# etc.
```

## Quick Start for Receiving Emails

### Recommended Workflow (Single Command)

**Quick Start**: Create email and session in one step
```bash
tacomail create-with-session
# Or use the short alias:
tacomail new
# Output: Email address and session information with expiration time
# Example:
# ╭────────────────────────── ✨ Email & Session Ready ──────────────────────────╮
# │ Email Address:                                                               │
# │ x7k9m2@tacomail.de                                                          │
# │                                                                              │
# │ Session Created                                                              │
# │                                                                              │
# │ Expires: 2026-01-15 23:59:59                                                 │
# │ Username: x7k9m2                                                             │
# │ Domain: tacomail.de                                                         │
# ╰──────────────────────────────────────────────────────────────────────────────╯
```

**With options**:
```bash
# Use specific domain
tacomail create-with-session --domain tacomail.de
# Or with the alias:
tacomail new --domain tacomail.de

# Use specific username and domain
tacomail create-with-session --username myuser --domain tacomail.de
# Or with the alias:
tacomail new -u myuser -d tacomail.de

# Short options
tacomail create-with-session -d tacomail.de -u myuser
# Or with the alias:
tacomail new -d tacomail.de -u myuser
```

**Using with async mode**:
```bash
tacomail --async create-with-session
# Or with the alias:
tacomail --async new
```

**Wait for emails**:
```bash
# After creating with session, wait for incoming email
EMAIL="x7k9m2@tacomail.de"  # Replace with your generated email
tacomail wait $EMAIL
# Monitors inbox and waits for incoming email
# Displays: From, Subject, Body when email arrives
```

### Alternative: Two-Step Workflow

**Step 1**: Generate email address
```bash
tacomail create
# Output: x7k9m2@tacomail.de
```

**Step 2**: Create session (REQUIRED for receiving emails)
```bash
tacomail create-session x7k9m2@tacomail.de
# Output: Session created, expires at [timestamp]
```

**Step 3**: Wait for emails
```bash
tacomail wait x7k9m2@tacomail.de
# Monitors inbox and waits for incoming email
# Displays: From, Subject, Body when email arrives
```

### Complete Workflow Example

```bash
# Generate email and create session (using plain output for easy parsing)
EMAIL=$(tacomail -o plain new | grep '^email=' | cut -d'=' -f2)

# Monitor inbox for incoming emails
tacomail wait $EMAIL --timeout 60
```

### Commands Needed for Receiving Emails

To receive emails, you can use either approach:

#### Quick Method (Recommended)
1. ✅ `tacomail create-with-session` - Generate email AND create session in one command (or use `tacomail new` - short alias)
2. ✅ `tacomail wait <email>` - Monitor inbox for incoming emails

#### Step-by-Step Method
1. ✅ `tacomail create` - Generate email address
2. ✅ `tacomail create-session <email>` - Create session (REQUIRED)
3. ✅ `tacomail wait <email>` - Monitor inbox for incoming emails

### Common Workflows

**Workflow 1: Quick setup for testing**
```bash
# Create and start receiving emails immediately
tacomail new  # or: tacomail create-with-session
tacomail wait <generated-email>
```

**Workflow 2: Automated script**
```bash
#!/bin/bash
# Get email and session using plain output (easy to parse)
EMAIL=$(tacomail -o plain new | grep '^email=' | cut -d'=' -f2)
echo "Created: $EMAIL"

# Or using JSON output with jq
EMAIL=$(tacomail -o json new | jq -r '.email')
echo "Created: $EMAIL"

# Monitor for emails (timeout 60s)
tacomail wait $EMAIL --timeout 60
```

**Workflow 3: Specific domain for testing**
```bash
# Use a specific domain if your service requires it
tacomail new --domain tacomail.de  # or: tacomail create-with-session --domain tacomail.de
tacomail list <generated-email>
```

### Optional: Check Inbox

You can check your inbox before waiting:
```bash
tacomail list x7k9m2@tacomail.de
# Shows all emails already in inbox
```

## Quick Start

### Synchronous Usage

```python
from tacomail import TacomailClient

with TacomailClient() as client:
    # Get a random email address
    username = client.get_random_username()
    domains = client.get_domains()
    email_address = f"{username}@{domains[0]}"
    
    # Create a session to receive emails (required for API v2)
    session = client.create_session(username, domains[0])
    print(f"Session expires at: {session.expires}")
    
    # Wait for an email to arrive
    email = client.wait_for_email(email_address, timeout=30)
    if email:
        print(f"From: {email.from_.address}")
        print(f"Subject: {email.subject}")
        print(f"Body: {email.body.text}")
```

### Asynchronous Usage

```python
import asyncio
from tacomail import AsyncTacomailClient

async def main():
    async with AsyncTacomailClient() as client:
        # Get a random email address
        username = await client.get_random_username()
        domains = await client.get_domains()
        email_address = f"{username}@{domains[0]}"
        
        # Create a session to receive emails (required for API v2)
        session = await client.create_session(username, domains[0])
        
        # Wait for an email with specific subject
        def filter_email(email):
            return email.subject == "Welcome!"
            
        email = await client.wait_for_email_filtered(
            email_address,
            filter_fn=filter_email,
            timeout=30
        )
        
        if email:
            print(f"Found email: {email.subject}")

asyncio.run(main())
```

## API Reference

### Main Classes

- `TacomailClient`: Synchronous client for Tacomail API
- `AsyncTacomailClient`: Asynchronous client for Tacomail API
- `Email`: Dataclass representing an email message
- `EmailAddress`: Dataclass for email addresses
- `EmailBody`: Dataclass for email content
- `Attachment`: Dataclass for email attachments
- `Session`: Dataclass for inbox session information

### Common Methods

Both sync and async clients provide these methods:

- `create_session(username, domain)`: Create an inbox session to receive emails
- `delete_session(username, domain)`: Delete an inbox session
- `get_random_username()`: Generate a random username
- `get_domains()`: Get list of available domains
- `get_random_address()`: Get a complete random email address
- `get_inbox(address, limit=None)`: Get recent emails
- `get_email(address, mail_id)`: Get a specific email
- `get_attachments(address, mail_id)`: Get email attachments
- `download_attachment(address, mail_id, attachment_id)`: Download an attachment
- `delete_email(address, mail_id)`: Delete a specific email
- `delete_inbox(address)`: Delete all emails in an inbox
- `wait_for_email(address, timeout=30, interval=2)`: Wait for new email
- `wait_for_email_filtered(address, filter_fn, timeout=30, interval=2)`: Wait for email matching criteria

## Requirements

- Python ≥ 3.12
- httpx ≥ 0.28.0

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

The test suite uses [Postmark](https://postmarkapp.com/) to send real test emails to the Tacomail addresses. This ensures the library works with actual email delivery.

1. Sign up for a Postmark account
2. Create a `.env` file in the project root with your credentials:

```bash
# .env
POSTMARK_API_KEY=your_postmark_api_key_here
SENDER_EMAIL=your_email_address_here  # The verified sender email in Postmark
```

Then run the tests:

```bash
pytest

# Run linter
ruff check .
```

## Credits

- Tacomail Service: [https://tacomail.de/](https://tacomail.de/)
- Tacomail Repository: [oskar2517/tacomail](https://github.com/oskar2517/tacomail)
- Tacomail API Documentation: [API.md](https://github.com/oskar2517/tacomail/blob/main/docs/API.md)
