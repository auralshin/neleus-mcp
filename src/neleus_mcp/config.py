"""
Credential and environment configuration for neleus-mcp.

Reads from environment variables. No file I/O — users set credentials
in their shell or MCP server config, not in files inside this package.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    private_key: str | None
    account_address: str | None
    testnet: bool

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            private_key=os.environ.get("HYPERLIQUID_SIGNER_PRIVATE_KEY"),
            account_address=os.environ.get("HYPERLIQUID_ACCOUNT_ADDRESS"),
            testnet=os.environ.get("HYPERLIQUID_TESTNET", "false").lower() in ("1", "true", "yes"),
        )

    @property
    def has_credentials(self) -> bool:
        return bool(self.private_key and self.account_address)
