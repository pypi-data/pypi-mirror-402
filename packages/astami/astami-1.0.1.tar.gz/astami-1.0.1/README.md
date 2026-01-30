# Astami

A modern, async-first Python client for the Asterisk Manager Interface (AMI).

[![PyPI version](https://badge.fury.io/py/astami.svg)](https://badge.fury.io/py/astami)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Modern Python**: Built for Python 3.10+ with full type hints
- **Async & Sync**: Both `AsyncAMIClient` and `AMIClient` (sync wrapper) available
- **Context Managers**: Automatic connection handling and cleanup
- **No Dependencies**: Pure Python, no external dependencies
- **Fully Typed**: Complete type annotations for IDE support
- **Convenience Methods**: High-level methods for common operations

## Installation

```bash
pip install astami
```

## Quick Start

### Synchronous Usage

```python
from astami import AMIClient

with AMIClient("localhost", 5038, "admin", "secret") as ami:
    # Execute CLI commands
    response = ami.command("core show version")
    print(response.output)

    # Reload configuration
    ami.reload("pjsip")
```

### Asynchronous Usage

```python
import asyncio
from astami import AsyncAMIClient

async def main():
    async with AsyncAMIClient("localhost", 5038, "admin", "secret") as ami:
        # Execute CLI commands
        response = await ami.command("core show version")
        print(response.output)

        # Reload configuration
        await ami.reload("pjsip")

asyncio.run(main())
```

## API Reference

### Client Classes

#### `AsyncAMIClient`

The async client for use in asyncio applications.

```python
AsyncAMIClient(
    host: str = "127.0.0.1",
    port: int = 5038,
    username: str = "",
    secret: str = "",
    timeout: float = 10.0,
)
```

#### `AMIClient`

Synchronous wrapper for use in threaded applications, Celery tasks, etc.

```python
AMIClient(
    host: str = "127.0.0.1",
    port: int = 5038,
    username: str = "",
    secret: str = "",
    timeout: float = 10.0,
)
```

### Response Object

All methods return an `AMIResponse` object:

```python
@dataclass
class AMIResponse:
    raw: str              # Raw response string
    action_id: str        # ActionID from the request
    response: str         # Response status (Success, Error, etc.)
    message: str          # Message from Asterisk
    data: dict[str, str]  # All key-value pairs
    output: list[str]     # Output lines (for Command actions)

    @property
    def success(self) -> bool:
        """True if response indicates success"""
```

### Available Methods

#### CLI Commands

```python
# Execute any CLI command
response = ami.command("sip show peers")
for line in response.output:
    print(line)
```

#### Asterisk Database (AstDB)

```python
# Store a value
ami.database_put("family", "key", "value")

# Retrieve a value
response = ami.database_get("family", "key")

# Delete a key
ami.database_del("family", "key")

# Delete entire family
ami.database_deltree("family")
```

#### Call Origination

```python
# Originate to dialplan
ami.originate(
    channel="PJSIP/1000",
    context="default",
    exten="1001",
    priority=1,
    caller_id="Test Call <1234>",
    variables={"VAR1": "value1", "VAR2": "value2"},
)

# Originate to application
ami.originate(
    channel="PJSIP/1000",
    application="Playback",
    data="hello-world",
)
```

#### Channel Operations

```python
# Hangup a channel
ami.hangup("PJSIP/1000-00000001")

# Redirect a channel
ami.redirect(
    channel="PJSIP/1000-00000001",
    context="default",
    exten="1002",
    priority=1,
)

# Get channel variable
response = ami.get_var("PJSIP/1000-00000001", "CALLERID(num)")

# Set channel variable
ami.set_var("PJSIP/1000-00000001", "MY_VAR", "my_value")
```

#### Configuration Reload

```python
# Reload specific module
ami.reload("pjsip")
ami.reload("dialplan")

# Reload all
ami.reload()
```

#### Raw Actions

For actions not covered by convenience methods:

```python
response = ami.send_action({
    "Action": "QueueStatus",
    "Queue": "support",
})
```

### Error Handling

```python
from astami import AMIClient, AMIError

try:
    with AMIClient("localhost", 5038, "admin", "wrong_password") as ami:
        ami.command("core show version")
except AMIError as e:
    print(f"AMI Error: {e}")
    if e.response:
        print(f"Response: {e.response.message}")
```

## Use Cases

### Celery Tasks

```python
from celery import shared_task
from astami import AMIClient, AMIError

@shared_task
def reload_dialplan(server_host: str) -> bool:
    try:
        with AMIClient(server_host, 5038, "admin", "secret") as ami:
            response = ami.command("dialplan reload")
            return response.success
    except AMIError as e:
        logger.error(f"AMI error: {e}")
        return False
```

### Django Management Command

```python
from django.core.management.base import BaseCommand
from astami import AMIClient

class Command(BaseCommand):
    help = "Show Asterisk version"

    def handle(self, *args, **options):
        with AMIClient("localhost", 5038, "admin", "secret") as ami:
            response = ami.command("core show version")
            self.stdout.write(self.style.SUCCESS(response.output[0]))
```

### Async Web Application (FastAPI)

```python
from fastapi import FastAPI
from astami import AsyncAMIClient

app = FastAPI()

@app.get("/asterisk/version")
async def get_version():
    async with AsyncAMIClient("localhost", 5038, "admin", "secret") as ami:
        response = await ami.command("core show version")
        return {"version": response.output[0] if response.output else "Unknown"}
```

## Configuration

### Asterisk manager.conf

Ensure your Asterisk server has AMI enabled in `/etc/asterisk/manager.conf`:

```ini
[general]
enabled = yes
port = 5038
bindaddr = 0.0.0.0

[admin]
secret = your_secret_here
read = all
write = all
```

After changes, reload the manager module:

```bash
asterisk -rx "manager reload"
```

## Why Astami?

- **Python 3.10+**: Uses modern Python features like `match` statements, union types with `|`, and proper async/await patterns
- **No Deprecated APIs**: Doesn't use deprecated asyncio patterns that break in Python 3.10+
- **Lightweight**: No dependencies beyond the Python standard library
- **Type Safe**: Full type hints for better IDE support and fewer bugs
- **Well Tested**: Comprehensive test suite

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Developed by [Real World Technology Solutions](https://rwts.com.au).
