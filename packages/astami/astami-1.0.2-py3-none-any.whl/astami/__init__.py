"""
Astami - Modern Asterisk Manager Interface (AMI) Client

A Python 3.10+ library for interacting with Asterisk PBX via the
Asterisk Manager Interface (AMI). Provides both async and sync clients.

Basic usage (sync):

    from astami import AMIClient

    with AMIClient("localhost", 5038, "admin", "secret") as ami:
        response = ami.command("core show version")
        print(response.output)

Basic usage (async):

    from astami import AsyncAMIClient

    async with AsyncAMIClient("localhost", 5038, "admin", "secret") as ami:
        response = await ami.command("core show version")
        print(response.output)
"""

from astami.client import (
    AMIClient,
    AMIError,
    AMIResponse,
    AsyncAMIClient,
)

__all__ = [
    "AMIClient",
    "AsyncAMIClient",
    "AMIError",
    "AMIResponse",
]

__version__ = "1.0.0"
